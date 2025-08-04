#!/usr/bin/env python3
"""
Sistema de Agentes Q-Agents con Human-in-the-Loop
Sistema avanzado que usa ejemplos de actividades k_ y feedback del usuario
para generar contenido pedagógico personalizado de alta calidad
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import re

os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

os.environ["HTTPX_TIMEOUT"] = "120"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Q_AGENTS_HITL")

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from crewai_tools import FileReadTool, DirectoryReadTool
    
    from langchain_community.llms import Ollama
    logger.info("✅ Usando langchain-community.llms.Ollama (compatible con CrewAI)")
        
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    logger.error("💡 Instala dependencias: pip install crewai crewai-tools langchain-community")
    raise ImportError("Dependencias no están disponibles")


# ==== DATA CLASSES Y SISTEMA PRINCIPAL ====
@dataclass
class ActividadEducativa:
    id: str
    titulo: str
    materia: str
    tema: str
    contenido: str
    estudiantes_objetivo: List[str]
    tipo: str
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str

@dataclass
class PromptAnalysis:
    materia: Optional[str] = None
    tema: Optional[str] = None
    objetivos: List[str] = None
    metodologia: Optional[str] = None
    duracion: Optional[str] = None
    nivel_detalle: Optional[str] = None
    enfoque_especial: List[str] = None
    missing_info: List[str] = None

class SistemaAgentesQAgents:
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 inspirador_model: str = "qwen3:latest",
                 pedagogo_model: str = "qwen3:latest", 
                 arquitecto_model: str = "qwen2:latest",
                 diferenciador_model: str = "mistral:latest",
                 validador_model: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.inspirador_model = inspirador_model
        self.pedagogo_model = pedagogo_model
        self.arquitecto_model = arquitecto_model
        self.diferenciador_model = diferenciador_model
        self.validador_model = validador_model
        self.perfiles_path = perfiles_path
        
        self._cargar_ejemplos_k()
        
        logger.info("🔧 Configurando LLMs específicos para cada agente...")
        
        try:
            import litellm
            
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            modelos_unicos = set([self.inspirador_model, self.pedagogo_model, self.arquitecto_model, 
                                 self.diferenciador_model, self.validador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            os.environ["OLLAMA_API_BASE"] = f"http://{ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{ollama_host}:11434"
            
            self.inspirador_llm = Ollama(
                model=f"ollama/{self.inspirador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.pedagogo_llm = Ollama(
                model=f"ollama/{self.pedagogo_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.arquitecto_llm = Ollama(
                model=f"ollama/{self.arquitecto_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.diferenciador_llm = Ollama(
                model=f"ollama/{self.diferenciador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.validador_llm = Ollama(
                model=f"ollama/{self.validador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            logger.info(f"✅ LLMs configurados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            logger.error("🚨 No se pudieron configurar LLMs para CrewAI.")
            raise e
        
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        self._crear_agentes_fewshot()
        
        logger.info(f"✅ Sistema few-shot inicializado con modelos:")
        logger.info(f"   🎭 Inspirador: {self.inspirador_model}")
        logger.info(f"   📚 Pedagogo: {self.pedagogo_model}")
        logger.info(f"   🏗️ Arquitecto: {self.arquitecto_model}")  
        logger.info(f"   🎯 Diferenciador: {self.diferenciador_model}")
        logger.info(f"   ✅ Validador: {self.validador_model}")
    
    def _cargar_ejemplos_k(self):
        self.ejemplos_k = {}
        
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_sonnet_supermercado.txt", 
            "actividades_generadas/k_feria_acertijos.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            try:
                if not os.path.isabs(archivo):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    archivo_path = os.path.join(script_dir, archivo)
                else:
                    archivo_path = archivo
                
                if os.path.exists(archivo_path):
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        logger.info(f"📖 Cargado ejemplo: {nombre_ejemplo}")
                else:
                    logger.warning(f"⚠️ No se encontró archivo: {archivo_path}")
            except Exception as e:
                logger.error(f"❌ Error cargando {archivo}: {e}")
        
        logger.info(f"✅ Cargados {len(self.ejemplos_k)} ejemplos k_ para few-shot learning")
    
    def _analizar_prompt_inicial(self, prompt_usuario: str) -> PromptAnalysis:
        """Analiza el prompt del usuario para extraer información ya proporcionada"""
        analysis = PromptAnalysis()
        analysis.missing_info = []
        
        prompt_lower = prompt_usuario.lower()
        
        # Detectar materia
        materias = {
            'matematicas': ['matemáticas', 'mates', 'números', 'cálculo', 'geometría', 'álgebra'],
            'lengua': ['lengua', 'idioma', 'escritura', 'lectura', 'gramática', 'literatura'],
            'ciencias': ['ciencias', 'biología', 'física', 'química', 'naturales', 'científico']
        }
        
        for materia, keywords in materias.items():
            if any(keyword in prompt_lower for keyword in keywords):
                analysis.materia = materia
                break
        
        # Detectar tema específico
        tema_patterns = [
            r'tema[:\s]*([^.,\n]+)',
            r'sobre[:\s]*([^.,\n]+)',
            r'acerca de[:\s]*([^.,\n]+)'
        ]
        for pattern in tema_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                analysis.tema = match.group(1).strip()
                break
        
        # Detectar objetivos
        objetivo_patterns = [
            r'objetivo[s]?[:\s]*([^.,\n]+)',
            r'meta[s]?[:\s]*([^.,\n]+)',
            r'pretende[:\s]*([^.,\n]+)'
        ]
        analysis.objetivos = []
        for pattern in objetivo_patterns:
            matches = re.findall(pattern, prompt_lower)
            analysis.objetivos.extend([match.strip() for match in matches])
        
        # Detectar metodología
        metodologias = ['colaborativa', 'individual', 'grupal', 'proyecto', 'gamificación', 'investigación']
        for metodologia in metodologias:
            if metodologia in prompt_lower:
                analysis.metodologia = metodologia
                break
        
        # Detectar duración
        duracion_patterns = [
            r'(\d+)\s*sesion[es]*',
            r'(\d+)\s*hora[s]*',
            r'(\d+)\s*minuto[s]*'
        ]
        for pattern in duracion_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                analysis.duracion = match.group(0)
                break
        
        # Detectar enfoque especial
        enfoques = ['inclusivo', 'diferenciado', 'personalizado', 'adaptado', 'tea', 'tdah', 'altas capacidades']
        analysis.enfoque_especial = []
        for enfoque in enfoques:
            if enfoque in prompt_lower:
                analysis.enfoque_especial.append(enfoque)
        
        # Identificar información faltante
        if not analysis.materia:
            analysis.missing_info.append('materia')
        if not analysis.tema:
            analysis.missing_info.append('tema_especifico')
        if not analysis.objetivos:
            analysis.missing_info.append('objetivos')
        if not analysis.metodologia:
            analysis.missing_info.append('metodologia_preferida')
        if not analysis.duracion:
            analysis.missing_info.append('duracion')
        
        return analysis
    
    def _solicitar_informacion_faltante(self, analysis: PromptAnalysis) -> Dict[str, str]:
        """Solicita al usuario la información que falta"""
        info_adicional = {}
        
        print("\n" + "="*60)
        print("🔍 ANÁLISIS DEL PROMPT INICIAL")
        print("="*60)
        
        if analysis.materia:
            print(f"✅ Materia detectada: {analysis.materia}")
        if analysis.tema:
            print(f"✅ Tema detectado: {analysis.tema}")
        if analysis.objetivos:
            print(f"✅ Objetivos detectados: {', '.join(analysis.objetivos)}")
        if analysis.metodologia:
            print(f"✅ Metodología detectada: {analysis.metodologia}")
        if analysis.duracion:
            print(f"✅ Duración detectada: {analysis.duracion}")
        if analysis.enfoque_especial:
            print(f"✅ Enfoque especial: {', '.join(analysis.enfoque_especial)}")
        
        if analysis.missing_info:
            print(f"\n❓ Información adicional necesaria:")
            
            for info in analysis.missing_info:
                if info == 'materia' and not analysis.materia:
                    while True:
                        materia = input("📚 ¿Qué materia? (matematicas/lengua/ciencias): ").strip().lower()
                        if materia in ['matematicas', 'lengua', 'ciencias']:
                            info_adicional['materia'] = materia
                            break
                        print("❌ Por favor, selecciona: matematicas, lengua o ciencias")
                
                elif info == 'tema_especifico':
                    tema = input("📝 ¿Tema específico? (opcional, Enter para omitir): ").strip()
                    if tema:
                        info_adicional['tema'] = tema
                
                elif info == 'objetivos':
                    objetivos = input("🎯 ¿Objetivos principales? (separados por comas): ").strip()
                    if objetivos:
                        info_adicional['objetivos'] = [obj.strip() for obj in objetivos.split(',')]
                
                elif info == 'metodologia_preferida':
                    metodologia = input("🔧 ¿Metodología preferida? (colaborativa/individual/proyecto/otra): ").strip()
                    if metodologia:
                        info_adicional['metodologia'] = metodologia
                
                elif info == 'duracion':
                    duracion = input("⏱️ ¿Duración estimada? (ej: 2 sesiones, 60 minutos): ").strip()
                    if duracion:
                        info_adicional['duracion'] = duracion
        
        return info_adicional
    
    def _solicitar_feedback_intermedio(self, fase: str, contenido_previo: str) -> str:
        """Solicita feedback del usuario en puntos clave del proceso"""
        print(f"\n" + "="*60)
        print(f"🔄 REVISIÓN INTERMEDIA - {fase.upper()}")
        print("="*60)
        
        # Mostrar resumen del contenido previo
        lineas = contenido_previo.split('\n')[:10]  # Primeras 10 líneas
        for linea in lineas:
            if linea.strip():
                print(f"📄 {linea[:80]}{'...' if len(linea) > 80 else ''}")
        
        print(f"\n❓ ¿Cómo te parece esta {fase}?")
        print("1. ✅ Perfecto, continúa")
        print("2. 📝 Añadir algunas indicaciones")
        print("3. 🔄 Necesita cambios importantes")
        
        while True:
            opcion = input("\n👉 Selecciona (1-3): ").strip()
            
            if opcion == "1":
                return ""
            elif opcion == "2":
                feedback = input("💭 ¿Qué te gustaría añadir o modificar? ")
                return f"FEEDBACK DEL USUARIO: {feedback}"
            elif opcion == "3":
                feedback = input("🔄 ¿Qué cambios importantes necesita? ")
                return f"CAMBIOS REQUERIDOS: {feedback}"
            else:
                print("❌ Por favor, selecciona 1, 2 o 3")
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        try:
            if not os.path.isabs(perfiles_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                perfiles_path = os.path.join(script_dir, perfiles_path)
            
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('estudiantes', [])
        except Exception as e:
            logger.error(f"Error cargando perfiles: {e}")
            return self._crear_perfiles_default()
    
    def _crear_perfiles_default(self) -> List[Dict]:
        return [
            {"id": "001", "nombre": "ALEX M.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 102},
            {"id": "002", "nombre": "MARÍA L.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno"},
            {"id": "003", "nombre": "ELENA R.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "TEA_nivel_1", "ci_base": 118},
            {"id": "004", "nombre": "LUIS T.", "temperamento": "impulsivo", "canal_preferido": "kinestésico", "diagnostico_formal": "TDAH_combinado", "ci_base": 102},
            {"id": "005", "nombre": "ANA V.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "altas_capacidades", "ci_base": 141},
            {"id": "006", "nombre": "SARA M.", "temperamento": "equilibrado", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno", "ci_base": 115},
            {"id": "007", "nombre": "EMMA K.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 132},
            {"id": "008", "nombre": "HUGO P.", "temperamento": "equilibrado", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 114}
        ]
    
    def _crear_agentes_fewshot(self):
        self.agente_inspirador = Agent(
            role="Inspirador de Experiencias Educativas",
            goal="Crear la semilla narrativa y conceptual de actividades memorables basándote en ejemplos exitosos",
            backstory="Eres un maestro creativo que diseña experiencias educativas memorables...",
            tools=[], llm=self.inspirador_llm, verbose=True, allow_delegation=False
        )
        
        self.agente_pedagogo = Agent(
            role="Pedagogo Curricular",
            goal="Transformar la idea inspiradora en estructura pedagógica sólida con objetivos y competencias claras",
            backstory="Eres un experto en currículum de primaria...",
            tools=[], llm=self.pedagogo_llm, verbose=True, allow_delegation=False
        )
        
        self.agente_arquitecto = Agent(
            role="Arquitecto de Experiencias de Aprendizaje",
            goal="Diseñar la progresión temporal y el flujo de la actividad",
            backstory="Eres un experto en diseño de experiencias...",
            tools=[], llm=self.arquitecto_llm, verbose=True, allow_delegation=False
        )
        
        self.agente_diferenciador = Agent(
            role="Especialista en Diferenciación Educativa",
            goal="Adaptar la experiencia a cada estudiante específico según sus necesidades, fortalezas y desafíos",
            backstory="Eres un psicopedagogo experto en personalización educativa...",
            tools=[], llm=self.diferenciador_llm, verbose=True, allow_delegation=False
        )
        
        self.agente_validador = Agent(
            role="Validador de Calidad Pedagógica",
            goal="Verificar que la actividad alcance los estándares de calidad de los ejemplos k_ exitosos",
            backstory="Eres un supervisor pedagógico experto...",
            tools=[], llm=self.validador_llm, verbose=True, allow_delegation=False
        )
        
        logger.info("✅ Agentes few-shot creados con nuevo flujo pedagógico")
    
    def _obtener_ejemplos_relevantes(self, materia: str, tema: str = None) -> str:
        ejemplos_texto = ""
        ejemplos_seleccionados = []
        
        if materia.lower() in ['matematicas', 'mates']:
            if 'k_sonnet_supermercado' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_sonnet_supermercado', self.ejemplos_k['k_sonnet_supermercado']))
            if 'k_feria_acertijos' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_feria_acertijos', self.ejemplos_k['k_feria_acertijos']))
        elif materia.lower() in ['ciencias', 'naturales']:
            if 'k_celula' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_celula', self.ejemplos_k['k_celula']))
        
        if not ejemplos_seleccionados:
            if 'k_piratas' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_piratas', self.ejemplos_k['k_piratas']))
            if 'k_sonnet_supermercado' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_sonnet_supermercado', self.ejemplos_k['k_sonnet_supermercado']))
        
        for nombre, contenido in ejemplos_seleccionados:
            ejemplos_texto += f"\n=== EJEMPLO EXITOSO: {nombre.upper()} ===\n"
            ejemplos_texto += contenido[:1500] + "...\n"
        
        return ejemplos_texto
    
    def generar_actividad_colaborativa(self, prompt_inicial: str = None, materia: str = None, tema: str = None) -> ActividadEducativa:
        """Genera una actividad colaborativa usando el sistema few-shot con human-in-the-loop"""
        
        # === HUMAN-IN-THE-LOOP: ANÁLISIS INICIAL ===
        info_adicional = {}
        if prompt_inicial:
            print(f"\n📝 PROMPT INICIAL RECIBIDO:")
            print(f"'{prompt_inicial}'")
            
            # Analizar el prompt
            analysis = self._analizar_prompt_inicial(prompt_inicial)
            
            # Solicitar información faltante
            info_adicional = self._solicitar_informacion_faltante(analysis)
            
            # Usar información del análisis y completar con parámetros
            materia = analysis.materia or info_adicional.get('materia') or materia
            tema = analysis.tema or info_adicional.get('tema') or tema
        
        if not materia:
            materia = input("📚 ¿Qué materia? (matematicas/lengua/ciencias): ").strip().lower()
        
        logger.info(f"👥 Generando actividad q-agents para {materia}")
        
        try:
            ejemplos_relevantes = self._obtener_ejemplos_relevantes(materia, tema)

            # -- TAREA 1: INSPIRADOR --
            contexto_adicional = ""
            if prompt_inicial:
                contexto_adicional += f"\n\nPROMPT INICIAL DEL USUARIO:\n{prompt_inicial}\n"
            if info_adicional:
                contexto_adicional += f"\nINFORMACIÓN ADICIONAL PROPORCIONADA:\n"
                for key, value in info_adicional.items():
                    contexto_adicional += f"- {key}: {value}\n"
            
            tarea_inspiracion = Task(
                description=f"""
            Estudia estos EJEMPLOS DE ACTIVIDADES EXITOSAS para {materia} {f'sobre {tema}' if tema else ''}.
            EJEMPLOS EXITOSOS A ESTUDIAR:
            {ejemplos_relevantes}
            
            {contexto_adicional}
            Crea una semilla creativa original que:
            - Enfoque la actividad con inclusividad real desde el principio, pensando en todo el aula, no solo ajustando a último momento las adaptaciones.
            - Promueva el pensamiento crítico y abstracto, evitando herramientas tecnológicas o atajos digitales. Favorece herramientas analógicas, debates, comparaciones y analogías para que comprendan desde fundamentos.
            - Diseñe la actividad como una experiencia colectiva donde la colaboración sea dividida, y el resultado final sea la suma coordinada de pequeñas contribuciones individuales, con sentido y coherencia pedagógica.
            - Plantee un "estado hamiltoniano" conceptual, es decir, una semilla que contenga todos los niveles y dimensiones que la actividad debe desarrollar y combinar con sentido.
            - Mantenga simplicidad pedagógica para resolver necesidades reales del aula de forma práctica y efectiva.

            

        CARACTERÍSTICAS CLAVE que debes emular de estos ejemplos:
        ✨ NARRATIVA ENVOLVENTE: Historia o contexto que motiva desde el inicio
        🏗️ CONSTRUCCIÓN PROGRESIVA: Preparación que construye hacia un clímax
        🎭 ROLES ESPECÍFICOS: Cada estudiante tiene función clara y necesaria
        🎯 INTEGRACIÓN CURRICULAR: Múltiples competencias trabajadas naturalmente
        ⚡ FLEXIBILIDAD ESTRUCTURADA: Libertad dentro de un marco claro

        GRUPO OBJETIVO: 8 estudiantes de 4º Primaria
        - 001 ALEX M.: reflexivo, visual, CI 102
        - 002 MARÍA L.: reflexivo, auditivo
        - 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118  
        - 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102
        - 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141
        - 006 SARA M.: equilibrado, auditivo, CI 115
        - 007 EMMA K.: reflexivo, visual, CI 132
        - 008 HUGO P.: equilibrado, visual, CI 114

        CREA UNA NUEVA ACTIVIDAD que tenga el mismo "alma pedagógica" que los ejemplos exitosos:

            === SEMILLA CREATIVA ===
            NOMBRE: [Título evocador]
            NARRATIVA: [Historia o contexto motivador y accesible]
            CONCEPTO CENTRAL: [La idea fundamental o metáfora que orienta la actividad]
            GANCHO INICIAL: [Cómo despertar curiosidad sin usar tecnología, con ejemplos analógicos o situaciones cotidianas]
            CLIMAX PEDAGÓGICO: [Momento culminante que consolida la comprensión abstracta]
            ABSTRACCIÓN Y PENSAMIENTO CRÍTICO: [Cómo se fomentan específicamente]
            COLABORACIÓN: [Breve descripción de cómo se reparte la participación y cómo las partes forman el todo]
            INCLUSIÓN: [Cómo se considera la inclusión desde el diseño, integrando a todos los estudiantes sin parches posteriores]
            INSTRUMENTOS ANALÓGICOS: [Qué herramientas/técnicas físicas, analógicas o discursivas se usarán para facilitar la comprensión profunda]
            INTEGRACIÓN CURRICULAR: [Qué competencias y aprendizajes se abordan de forma integrada]

            IMPORTANTE: Basándote en el estilo de los ejemplos, pero creando algo NUEVO y ORIGINAL.""",
                agent=self.agente_inspirador,
                expected_output="Semilla creativa inspiradora con narrativa envolvente"
            )

            # -- TAREA 2: PEDAGOGO --
            tarea_pedagogica = Task(
                description=f"""
            Toma la semilla creativa propuesta por el agente inspirador y desarrolla una propuesta pedagógica rigurosa que:
            - Diseñe la actividad considerando la inclusión “de terreno”: la actividad debe construirse desde la realidad del aula, contemplando todas las necesidades desde el principio, no como adaptaciones aisladas.
            - Promueva el desarrollo del pensamiento crítico y abstracto usando estrategias didácticas analógicas, discusiones guiadas, razonamientos y explicaciones fundamentadas.
            - Defina objetivos claros, medibles y ajustados al nivel de 4º primaria, conectando con competencias transversales y valores inclusivos.
            - Exponga cómo se manejará la colaboración distribuida para que el producto final sea resultado de la suma coherente y coordinada de las tareas individuales de los estudiantes.
            - Fundamente la elección de métodos y recursos analógicos que permitan el aprendizaje sin depender de tecnología.
            - Integre criterios de evaluación formativa que valoren la comprensión, la colaboración y la reflexión crítica.

            DESARROLLA:

        === MARCO PEDAGÓGICO ===
        - Objetivos de aprendizaje específicos y medibles
        - Competencias curriculares que se desarrollan
        - Nivel de complejidad apropiado para 4º Primaria
        - Criterios de evaluación formativa
        - Conexiones con otras materias

        === ESTRUCTURA EDUCATIVA ===
        - Metodología principal (colaborativa, por proyectos, etc.)
        - Principios DUA aplicados
        - Estrategias de motivación
        - Gestión de la diversidad del aula
        - Recursos pedagógicos necesarios

        === JUSTIFICACIÓN CURRICULAR ===
        - Por qué esta actividad es valiosa para este grupo
        - Qué necesidades educativas específicas atiende
        - Cómo se conecta con aprendizajes previos y futuros

        Mantén la magia de la semilla creativa pero añade el rigor pedagógico necesario.""",
                    agent=self.agente_pedagogo,
                    context=[tarea_inspiracion],
                    expected_output="Estructura pedagógica sólida con objetivos y metodología clara"
                )

            # -- TAREA 3: ARQUITECTO --
            tarea_arquitectura = Task(
                description=f"""
            Diseña el flujo completo y la arquitectura de la experiencia educativa basada en la propuesta pedagógica. Debe incluir:
            - Fases claras y progresivas (preparación, desarrollo, cierre) que promuevan la construcción y consolidación del aprendizaje.
            - Grabación detallada de roles distribuidos y responsabilidades específicas para cada estudiante, asegurando que todos tengan tareas significativas.
            - Descripción precisa de cómo las tareas individuales se integran para crear el producto o resultado final, tipo suma de contribuciones.
            - Estrategias para fomentar la colaboración coordinada y el acompañamiento mutuo, con espacios para reflexión y evaluación grupal.
            - Duración estimada realista y flexibilidad para adaptar al ritmo natural del aula.
            - Diseño de recursos analógicos específicos para cada fase, que ayuden a vivir y comprender el proceso desde lo concreto.

            Incluye también recomendaciones sobre la organización del aula, gestión del tiempo y dinámicas grupales que promuevan un ambiente inclusivo, motivador y respetuoso.
            DISEÑA:

            === ARQUITECTURA TEMPORAL ===
            - Fases de preparación (construcción progresiva)
            - Desarrollo principal (experiencia cumbre)
            - Cierre y consolidación
            - Duración realista y flexible

            === FLUJO DE PARTICIPACIÓN ===
            - Cómo se involucra progresivamente a los estudiantes
            - Momentos de trabajo individual vs. colaborativo
            - Transiciones entre actividades
            - Gestión de la energía y atención del grupo

            === ROLES Y RESPONSABILIDADES ===
            - 3-4 roles principales necesarios
            - Función específica de cada rol
            - Interacciones entre roles
            - Rotaciones o cambios durante la actividad

            === MATERIALES Y ESPACIOS ===
            - Organización física del aula
            - Materiales específicos necesarios
            - Preparación previa requerida
            - Recursos de apoyo disponibles

            Crea una experiencia que "fluya" naturalmente y mantenga a todos los estudiantes activamente involucrados.""",
                agent=self.agente_arquitecto,
                context=[tarea_pedagogica],
                expected_output="Diseño completo de experiencia con progresión temporal y roles específicos"
            )


            # -- TAREA 4: DIFERENCIADOR --
            tarea_diferenciacion = Task(
                description=f"""
            Personaliza la experiencia diseñada para atender las necesidades, fortalezas y desafíos de cada estudiante de forma integrada y coherente.

            **No se trata de aplicar adaptaciones aisladas al final, sino de desplegar un diseño en el que la inclusión esté imbricada en la experiencia desde el inicio.**

            Estudiantes y perfiles:

            - 001 ALEX M.: reflexivo, visual, CI 102
            - 002 MARÍA L.: reflexivo, auditivo
            - 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118
            - 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102
            - 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141
            - 006 SARA M.: equilibrado, auditivo, CI 115
            - 007 EMMA K.: reflexivo, visual, CI 132
            - 008 HUGO P.: equilibrado, visual, CI 114

            Para cada estudiante:

                            **NOMBRE**: ROL ASIGNADO
                - Función específica: [qué hace exactamente en la actividad]
                - Por qué este rol: [cómo aprovecha sus fortalezas]
                - Adaptaciones: [apoyos específicos que necesita]
                - Nivel de desafío: [apropiado para su ZDP]
                - Interacciones: [con quién colabora principalmente]
                - Productos/evidencias: [qué genera o presenta]

                ADAPTACIONES ESPECIALES:
                - Elena (TEA): Estrategias de regulación, estructura visual, pausas
                - Luis (TDAH): Movimiento, tareas dinámicas, retroalimentación frecuente  
                - Ana (Altas capacidades): Desafíos adicionales, liderazgo, mentoreo

                BANCO DE RECURSOS disponibles para autoselección.""",
                agent=self.agente_diferenciador,
                context=[tarea_arquitectura],
                expected_output="Asignación personalizada de roles con adaptaciones específicas para cada estudiante"
            )


            # -- TAREA 5: VALIDADOR --
            tarea_validacion = Task(
                description=f"""
            Valida rigurosamente que la actividad final desarrollada cumpla con los más altos estándares pedagógicos y de inclusión.

            CHECKLIST PEDAGÓGICO PROFUNDO:

            1. Inclusión “de terreno”:
            - La actividad promueve la participación activa y significativa de todos los estudiantes.
            - Las adaptaciones no son parches aislados, sino parte integral del diseño.
            - Hay sentido de pertenencia y equidad real entre roles.

            2. Fomento del pensamiento crítico y abstracto:
            - No se usan herramientas tecnológicas como atajos.
            - El diseño propone recursos y estrategias analógicas y discursivas para aproximarse a los fundamentos de los conceptos.
            - Se promueven debates, análisis, comparación y reflexión profunda.

            3. Colaboración distribuida:
            - La actividad está diseñada como suma integrada de tareas individuales para producir un resultado conjunto.
            - Los roles y tareas se complementan formando una estructura coherente y funcional.
            - Se evidencia flujo claro y coordinación entre estudiantes.

            4. Cobertura de niveles y estados conceptuales (“estado hamiltoniano”):
            - La actividad incluye desarrollo en múltiples niveles de abstracción y comprensión.
            - Se revisa que la entrega cubra todos estos niveles, sin lagunas significativas.
            - Se asegura la consistencia y coherencia global del diseño.

            5. Simplicidad pedagógica que resuelve necesidades reales:
            - La actividad es sencilla y práctica, sin complejidad innecesaria.
            - Resuelve efectivamente las necesidades detectadas en el aula.
            - Promueve la autonomía y motivación del grupo.

            Proporciona una valoración clara y crítica (mínimo / máximo 10 puntos) con justificaciones detalladas.

            Si hay áreas de mejora, identifica concretamente qué falta y cómo corregirlo.

            Entrega un informe final optimizado para implementación en el aula completa, con todos los aspectos de inclusión, pensamiento crítico, colaboración y estructura pedagógica correctamente abordados.
        
            CRITERIOS DE VALIDACIÓN (basados en ejemplos k_):

            ✅ NARRATIVA ENVOLVENTE:
            - ¿Tiene una historia/contexto que motiva desde el inicio?
            - ¿Genera curiosidad y expectativa?
            - ¿Se mantiene el hilo narrativo durante toda la actividad?

            ✅ CONSTRUCCIÓN PROGRESIVA:
            - ¿Hay preparación previa que construye hacia el clímax?
            - ¿Los estudiantes participan en la construcción de la experiencia?
            - ¿Existe anticipación y descubrimiento progresivo?

            ✅ FLEXIBILIDAD ESTRUCTURADA:
            - ¿Hay estructura clara pero permite autonomía?
            - ¿Los estudiantes pueden tomar decisiones dentro del marco?
            - ¿Se adapta a diferentes ritmos y estilos?

            ✅ INTEGRACIÓN CURRICULAR NATURAL:
            - ¿Se trabajan múltiples competencias de forma orgánica?
            - ¿Las conexiones curriculares surgen naturalmente?
            - ¿Es más que la suma de sus partes?

            ✅ ROLES ESPECÍFICOS Y NECESARIOS:
            - ¿Cada estudiante tiene función clara e importante?
            - ¿Hay interdependencia real entre roles?
            - ¿Todos están activos durante toda la actividad?

            PUNTUACIÓN: __/10 (comparado con ejemplos k_)

            Si la puntuación es menor a 8/10, identifica específicamente qué falta y cómo mejorarlo.

            ENTREGA FINAL VALIDADA con todos los elementos integrados.""",
                agent=self.agente_validador,
                context=[tarea_diferenciacion],
                expected_output="Actividad validada y optimizada que alcanza estándares de calidad k_"
            )

            crew = Crew(
                agents=[
                    self.agente_inspirador,
                    self.agente_pedagogo,
                    self.agente_arquitecto,
                    self.agente_diferenciador,
                    self.agente_validador
                ],
                tasks=[
                    tarea_inspiracion,
                    tarea_pedagogica,
                    tarea_arquitectura,
                    tarea_diferenciacion,
                    tarea_validacion
                ],
                process=Process.sequential,
                verbose=True # Corregido: de 2 a True
            )
            
            logger.info("🚀 Ejecutando workflow q-agents con human-in-the-loop...")
            
            # Ejecutar tareas con feedback intermedio
            resultados_intermedios = []
            
            # Ejecutar Inspirador
            crew_inspirador = Crew(
                agents=[self.agente_inspirador],
                tasks=[tarea_inspiracion],
                process=Process.sequential,
                verbose=True
            )
            resultado_inspirador = crew_inspirador.kickoff()
            resultados_intermedios.append(("INSPIRACIÓN", str(resultado_inspirador)))
            
            # Solicitar feedback del usuario
            feedback_inspiracion = self._solicitar_feedback_intermedio("inspiración", str(resultado_inspirador))
            if feedback_inspiracion:
                # Actualizar la tarea pedagógica con el feedback
                tarea_pedagogica.description += f"\n\nFEEDBACK SOBRE LA INSPIRACIÓN:\n{feedback_inspiracion}"
            
            # Ejecutar Pedagogo
            crew_pedagogo = Crew(
                agents=[self.agente_pedagogo],
                tasks=[tarea_pedagogica],
                process=Process.sequential,
                verbose=True
            )
            resultado_pedagogo = crew_pedagogo.kickoff()
            resultados_intermedios.append(("PEDAGOGÍA", str(resultado_pedagogo)))
            
            # Solicitar feedback del usuario
            feedback_pedagogia = self._solicitar_feedback_intermedio("estructura pedagógica", str(resultado_pedagogo))
            if feedback_pedagogia:
                tarea_arquitectura.description += f"\n\nFEEDBACK SOBRE LA PEDAGOGÍA:\n{feedback_pedagogia}"
            
            # Ejecutar Arquitecto
            crew_arquitecto = Crew(
                agents=[self.agente_arquitecto],
                tasks=[tarea_arquitectura],
                process=Process.sequential,
                verbose=True
            )
            resultado_arquitecto = crew_arquitecto.kickoff()
            resultados_intermedios.append(("ARQUITECTURA", str(resultado_arquitecto)))
            
            # Solicitar feedback del usuario
            feedback_arquitectura = self._solicitar_feedback_intermedio("arquitectura", str(resultado_arquitecto))
            if feedback_arquitectura:
                tarea_diferenciacion.description += f"\n\nFEEDBACK SOBRE LA ARQUITECTURA:\n{feedback_arquitectura}"
            
            # Ejecutar Diferenciador y Validador sin interrupciones (flujo final)
            crew_final = Crew(
                agents=[self.agente_diferenciador, self.agente_validador],
                tasks=[tarea_diferenciacion, tarea_validacion],
                process=Process.sequential,
                verbose=True
            )
            resultado_final = crew_final.kickoff()
            
            # Combinar todos los resultados
            class ResultadoCombinado:
                def __init__(self, resultados):
                    self.tasks_output = resultados
            
            resultado = ResultadoCombinado([
                resultado_inspirador,
                resultado_pedagogo, 
                resultado_arquitecto,
                resultado_final.tasks_output[0] if hasattr(resultado_final, 'tasks_output') else resultado_final,
                resultado_final.tasks_output[1] if hasattr(resultado_final, 'tasks_output') and len(resultado_final.tasks_output) > 1 else resultado_final
            ])
            
            contenido_completo = self._procesar_resultados(resultado)
            
            return ActividadEducativa(
                id=f"q_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Few-Shot - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_fewshot",
                adaptaciones=["narrativa_envolvente", "construccion_progresiva", "flexibilidad_estructurada"],
                metadatos={
                    "total_estudiantes": 8,
                    "flujo_pedagogico": ["inspiracion", "pedagogia", "arquitectura", "diferenciacion", "validacion"],
                    "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                    "modelos_usados": {
                        "inspirador": self.inspirador_model,
                        "pedagogo": self.pedagogo_model,
                        "arquitecto": self.arquitecto_model,
                        "diferenciador": self.diferenciador_model,
                        "validador": self.validador_model
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad few-shot: {e}")
            return ActividadEducativa(
                id=f"error_q_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Error - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error generando actividad few-shot: {e}",
                estudiantes_objetivo=[],
                tipo="error_fewshot",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

    def _procesar_resultados(self, resultado) -> str:
        contenido = ""
        
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido += "=== SEMILLA CREATIVA E INSPIRACIÓN ===\n"
                contenido += str(resultado.tasks_output[0]) + "\n\n"
                
                contenido += "=== ESTRUCTURA PEDAGÓGICA ===\n"
                contenido += str(resultado.tasks_output[1]) + "\n\n"
                
                contenido += "=== ARQUITECTURA DE LA EXPERIENCIA ===\n"
                contenido += str(resultado.tasks_output[2]) + "\n\n"
                
                contenido += "=== DIFERENCIACIÓN PERSONALIZADA ===\n"
                contenido += str(resultado.tasks_output[3]) + "\n\n"
                
                contenido += "=== VALIDACIÓN DE CALIDAD ===\n"
                contenido += str(resultado.tasks_output[4]) + "\n\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados individuales: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_q") -> str:
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA CUÁNTICO-AGENTES\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo: {actividad.tipo}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 50 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\n")
            f.write("-" * 50 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("METADATOS DEL SISTEMA CUÁNTICO-AGENTES:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad cuántica guardada en: {filepath}")
        return filepath

# -------------------------------

def main():
    print("=" * 70)
    print("🎓 SISTEMA Q-AGENTS CON HUMAN-IN-THE-LOOP PARA EDUCACIÓN")
    print("=" * 70)

    try:
        OLLAMA_HOST = "192.168.1.10"
        INSPIRADOR_MODEL = "qwen3:latest"
        PEDAGOGO_MODEL = "qwen3:latest"
        ARQUITECTO_MODEL = "qwen2:latest"
        DIFERENCIADOR_MODEL = "mistral:latest"
        VALIDADOR_MODEL = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"

        print(f"\n🔧 Inicializando sistema few-shot:")
        print(f" Host Ollama: {OLLAMA_HOST}")
        print(f" Modelos especializados por agente:")
        print(f" 🎭 Inspirador: {INSPIRADOR_MODEL}")
        print(f" 📚 Pedagogo: {PEDAGOGO_MODEL}")
        print(f" 🏗️ Arquitecto: {ARQUITECTO_MODEL}")
        print(f" 🎯 Diferenciador: {DIFERENCIADOR_MODEL}")
        print(f" ✅ Validador: {VALIDADOR_MODEL}")

        sistema = SistemaAgentesQAgents(
            ollama_host=OLLAMA_HOST,
            inspirador_model=INSPIRADOR_MODEL,
            pedagogo_model=PEDAGOGO_MODEL,
            arquitecto_model=ARQUITECTO_MODEL,
            diferenciador_model=DIFERENCIADOR_MODEL,
            validador_model=VALIDADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )

        print("\n✅ Sistema q-agents inicializado correctamente!")
        print(f"📖 Ejemplos k_ cargados: {len(sistema.ejemplos_k)}")

        while True:
            print("\n" + "="*50)
            print("🎓 GENERACIÓN Q-AGENTS CON HUMAN-IN-THE-LOOP")
            print("1. 🎯 Generar con prompt inicial personalizado")
            print("2. 🔧 Generar paso a paso (modo tradicional)")
            print("3. ❌ Salir")

            opcion = input("\n👉 Selecciona una opción (1-3): ").strip()
            if opcion == "1":
                print("\n📝 Describe tu actividad ideal:")
                print("Ejemplo: 'Quiero una actividad colaborativa de matemáticas sobre fracciones")
                print("         que dure 2 sesiones y sea inclusiva para estudiantes con TEA'")
                prompt_inicial = input("\n✨ Tu prompt: ").strip()
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_colaborativa(prompt_inicial=prompt_inicial)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"\n✅ Actividad q-agents generada en {duration:.1f}s:")
                print(f" 📄 ID: {actividad.id}")
                print(f" 📁 Archivo: {archivo}")
                print(f" 🎯 Sistema: Q-agents con human-in-the-loop")
                print(f" 📖 Ejemplos usados: {len(actividad.metadatos.get('ejemplos_k_usados', []))}")
            
            elif opcion == "2":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                start_time = datetime.now()
                actividad = sistema.generar_actividad_colaborativa(materia=materia, tema=tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"\n✅ Actividad q-agents generada en {duration:.1f}s:")
                print(f" 📄 ID: {actividad.id}")
                print(f" 📁 Archivo: {archivo}")
                print(f" 🎯 Sistema: Q-agents con human-in-the-loop")
                print(f" 📖 Ejemplos usados: {len(actividad.metadatos.get('ejemplos_k_usados', []))}")
            elif opcion == "3":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("\n❌ Opción no válida. Selecciona 1-3.")

    except Exception as e:
        print(f"\n❌ Error inicializando sistema q-agents: {e}")
        print("\n💡 Verifica que:")
        print(" 1. Ollama esté ejecutándose")
        print(" 2. Los modelos especificados estén disponibles")
        print(" 3. El archivo de perfiles exista")
        print(" 4. Los archivos k_ estén en actividades_generadas/")

if __name__ == "__main__":
    main()
