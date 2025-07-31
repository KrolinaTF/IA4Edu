#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI con Few-Shot Learning
Sistema mejorado que usa ejemplos de actividades k_ para generar contenido de alta calidad pedagógica
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# Configurar variables de entorno para LiteLLM/CrewAI (192.168.1.10)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"  # Para debug

# Configuración para forzar Ollama sin LiteLLM
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
# Desactivar LiteLLM en CrewAI
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# Configuración de timeout
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CREWAI_FEWSHOT")

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from crewai_tools import FileReadTool, DirectoryReadTool
    
    # Forzar uso de langchain-community para compatibilidad con CrewAI
    from langchain_community.llms import Ollama
    logger.info("✅ Usando langchain-community.llms.Ollama (compatible con CrewAI)")
        
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    logger.error("💡 Instala dependencias: pip install crewai crewai-tools langchain-community")
    raise ImportError("Dependencias no están disponibles")

from ollama_api_integrator import OllamaAPIEducationGenerator
from prompt_template import PromptTemplateGenerator, TEMAS_MATEMATICAS_4_PRIMARIA, TEMAS_LENGUA_4_PRIMARIA, TEMAS_CIENCIAS_4_PRIMARIA


@dataclass
class ActividadEducativa:
    """Estructura de datos para una actividad educativa"""
    id: str
    titulo: str
    materia: str
    tema: str
    contenido: str
    estudiantes_objetivo: List[str]
    tipo: str  # "individual", "grupal", "colaborativa"
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str


class SistemaAgentesFewShot:
    """Sistema principal de agentes con few-shot learning basado en ejemplos k_"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 inspirador_model: str = "qwen3:latest",
                 pedagogo_model: str = "qwen3:latest", 
                 arquitecto_model: str = "qwen2:latest",
                 diferenciador_model: str = "mistral:latest",
                 validador_model: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema de agentes con few-shot learning
        """
        self.ollama_host = ollama_host
        self.inspirador_model = inspirador_model
        self.pedagogo_model = pedagogo_model
        self.arquitecto_model = arquitecto_model
        self.diferenciador_model = diferenciador_model
        self.validador_model = validador_model
        self.perfiles_path = perfiles_path
        
        # Cargar ejemplos k_ para few-shot learning
        self._cargar_ejemplos_k()
        
        # Crear LLMs específicos para cada agente
        logger.info("🔧 Configurando LLMs específicos para cada agente...")
        
        try:
            # Configurar LiteLLM correctamente para Ollama
            import litellm
            
            # Configuraciones específicas para Ollama local
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            # Mapear todos los modelos para LiteLLM
            modelos_unicos = set([self.inspirador_model, self.pedagogo_model, self.arquitecto_model, 
                                 self.diferenciador_model, self.validador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Configurar variables específicas para LiteLLM + Ollama
            os.environ["OLLAMA_API_BASE"] = f"http://{ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{ollama_host}:11434"
            
            # Crear LLMs específicos para cada agente
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
        
        # Cargar perfiles directamente para usar en las descripciones de tareas
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes con nuevo flujo
        self._crear_agentes_fewshot()
        
        logger.info(f"✅ Sistema few-shot inicializado con modelos:")
        logger.info(f"   🎭 Inspirador: {self.inspirador_model}")
        logger.info(f"   📚 Pedagogo: {self.pedagogo_model}")
        logger.info(f"   🏗️ Arquitecto: {self.arquitecto_model}")  
        logger.info(f"   🎯 Diferenciador: {self.diferenciador_model}")
        logger.info(f"   ✅ Validador: {self.validador_model}")
    
    def _cargar_ejemplos_k(self):
        """Cargar ejemplos de actividades k_ para few-shot learning"""
        self.ejemplos_k = {}
        
        # Rutas de archivos k_
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_sonnet_supermercado.txt", 
            "actividades_generadas/k_feria_acertijos.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            try:
                # Crear ruta absoluta si es relativa
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
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        """Cargar perfiles de estudiantes desde archivo JSON"""
        try:
            # Crear ruta absoluta si es relativa
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
        """Crea perfiles por defecto si no se pueden cargar"""
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
        """Crea agentes con nuevo flujo: Inspirador → Pedagogo → Arquitecto → Diferenciador → Validador"""
        
        # AGENTE 1: INSPIRADOR (con few-shot de ejemplos k_)
        self.agente_inspirador = Agent(
            role="Inspirador de Experiencias Educativas",
            goal="Crear la semilla narrativa y conceptual de actividades memorables basándote en ejemplos exitosos",
            backstory="Eres un maestro creativo que diseña experiencias educativas memorables. Te inspiras en actividades exitosas previas para crear nuevas narrativas envolventes. Sabes que una buena actividad empieza con una historia que motiva y contextualiza el aprendizaje. Respondes siempre en español.",
            tools=[],
            llm=self.inspirador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: PEDAGOGO (estructura curricular)
        self.agente_pedagogo = Agent(
            role="Pedagogo Curricular",
            goal="Transformar la idea inspiradora en estructura pedagógica sólida con objetivos y competencias claras",
            backstory="Eres un experto en currículum de primaria que toma ideas creativas y las estructura pedagógicamente. Defines objetivos de aprendizaje, competencias a desarrollar y criterios de evaluación. Tu trabajo garantiza que la actividad tenga rigor académico sin perder la magia inicial. Respondes siempre en español.",
            tools=[],
            llm=self.pedagogo_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: ARQUITECTO DE EXPERIENCIA (progresión y flujo)
        self.agente_arquitecto = Agent(
            role="Arquitecto de Experiencias de Aprendizaje",
            goal="Diseñar la progresión temporal y el flujo de la actividad para crear construcción progresiva del conocimiento",
            backstory="Eres un experto en diseño de experiencias que sabe cómo construir el aprendizaje paso a paso. Diseñas la progresión temporal, las fases de preparación, los momentos climáticos y los cierres satisfactorios. Tu especialidad es crear el 'arco narrativo' del aprendizaje. Respondes siempre en español.",
            tools=[],
            llm=self.arquitecto_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: DIFERENCIADOR (personalización)
        self.agente_diferenciador = Agent(
            role="Especialista en Diferenciación Educativa",
            goal="Adaptar la experiencia a cada estudiante específico según sus necesidades, fortalezas y desafíos",
            backstory="Eres un psicopedagogo experto en personalización educativa. Conoces a cada estudiante del aula y sabes cómo adaptar cualquier actividad para que todos puedan participar exitosamente. Tu trabajo es crucial para la inclusión real. Respondes siempre en español.",
            tools=[],
            llm=self.diferenciador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 5: VALIDADOR (calidad vs ejemplos k_)
        self.agente_validador = Agent(
            role="Validador de Calidad Pedagógica",
            goal="Verificar que la actividad alcance los estándares de calidad de los ejemplos k_ exitosos",
            backstory="Eres un supervisor pedagógico experto que conoce las características que hacen exitosa una actividad educativa. Comparas la propuesta final con los mejores ejemplos y garantizas que tenga narrativa envolvente, construcción progresiva, flexibilidad dentro de estructura, e integración curricular natural. Respondes siempre en español.",
            tools=[],
            llm=self.validador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes few-shot creados con nuevo flujo pedagógico")
    
    def _obtener_ejemplos_relevantes(self, materia: str, tema: str = None) -> str:
        """Obtiene ejemplos k_ relevantes para la materia y tema"""
        ejemplos_texto = ""
        
        # Seleccionar ejemplos más relevantes
        ejemplos_seleccionados = []
        
        if materia.lower() in ['matematicas', 'mates']:
            if 'k_sonnet_supermercado' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_sonnet_supermercado', self.ejemplos_k['k_sonnet_supermercado']))
            if 'k_feria_acertijos' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_feria_acertijos', self.ejemplos_k['k_feria_acertijos']))
        elif materia.lower() in ['ciencias', 'naturales']:
            if 'k_celula' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_celula', self.ejemplos_k['k_celula']))
        
        # Si no hay ejemplos específicos, usar los más generales
        if not ejemplos_seleccionados:
            if 'k_piratas' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_piratas', self.ejemplos_k['k_piratas']))
            if 'k_sonnet_supermercado' in self.ejemplos_k:
                ejemplos_seleccionados.append(('k_sonnet_supermercado', self.ejemplos_k['k_sonnet_supermercado']))
        
        # Crear texto de ejemplos (limitado a primeros 1000 caracteres de cada uno)
        for nombre, contenido in ejemplos_seleccionados:
            ejemplos_texto += f"\n=== EJEMPLO EXITOSO: {nombre.upper()} ===\n"
            ejemplos_texto += contenido[:1500] + "...\n"
        
        return ejemplos_texto
    
    def generar_actividad_colaborativa(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera una actividad colaborativa usando el sistema few-shot"""
        
        logger.info(f"👥 Generando actividad few-shot para {materia}")
        
        try:
            # Obtener ejemplos relevantes
            ejemplos_relevantes = self._obtener_ejemplos_relevantes(materia, tema)
            
            # TAREA 1: INSPIRADOR - Crear semilla narrativa
            tarea_inspiracion = Task(
                description=f"""Estudia estos EJEMPLOS DE ACTIVIDADES EXITOSAS y crea una nueva idea inspiradora para {materia} {f'sobre {tema}' if tema else ''}.

EJEMPLOS EXITOSOS A ESTUDIAR:
{ejemplos_relevantes}

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

RESPONDE EN ESTE FORMATO:
=== SEMILLA CREATIVA ===
NOMBRE: [Título atractivo y evocador]
NARRATIVA: [Historia/contexto que motiva la participación]
CONCEPTO CENTRAL: [La idea principal que hace especial esta actividad]
GANCHO INICIAL: [Cómo se presenta para despertar curiosidad]
CLIMAX PEDAGÓGICO: [El momento culminante de aprendizaje]
INTEGRACIÓN CURRICULAR: [Qué competencias se trabajan naturalmente]

IMPORTANTE: Basándote en el estilo de los ejemplos, pero creando algo NUEVO y ORIGINAL.""",
                agent=self.agente_inspirador,
                expected_output="Semilla creativa inspiradora con narrativa envolvente"
            )
            
            # TAREA 2: PEDAGOGO - Estructura curricular  
            tarea_pedagogica = Task(
                description=f"""Toma la semilla creativa y transfórmala en una propuesta pedagógica sólida para 4º Primaria.

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
            
            # TAREA 3: ARQUITECTO - Diseño de experiencia
            tarea_arquitectura = Task(
                description=f"""Diseña la EXPERIENCIA COMPLETA paso a paso, creando la progresión temporal y el flujo de aprendizaje.

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
            
            # TAREA 4: DIFERENCIADOR - Personalización
            tarea_diferenciacion = Task(
                description=f"""Personaliza la experiencia para cada estudiante específico del aula, asignando roles y adaptaciones.

ESTUDIANTES A PERSONALIZAR:
- 001 ALEX M.: reflexivo, visual, CI 102, apoyo bajo
- 002 MARÍA L.: reflexivo, auditivo, apoyo medio  
- 003 ELENA R.: reflexivo, visual, CI 118, apoyo alto, TEA nivel 1
- 004 LUIS T.: impulsivo, kinestésico, CI 102, apoyo alto, TDAH combinado
- 005 ANA V.: reflexivo, auditivo, CI 141, apoyo bajo, altas capacidades
- 006 SARA M.: equilibrado, auditivo, CI 115, apoyo medio
- 007 EMMA K.: reflexivo, visual, CI 132, apoyo medio
- 008 HUGO P.: equilibrado, visual, CI 114, apoyo bajo

PARA CADA ESTUDIANTE ESPECIFICA:

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
            
            # TAREA 5: VALIDADOR - Control de calidad
            tarea_validacion = Task(
                description=f"""Valida que la actividad final alcance los estándares de calidad de los ejemplos k_ exitosos.

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

            # Crear y ejecutar crew
            crew = Crew(
                agents=[self.agente_inspirador, self.agente_pedagogo, self.agente_arquitecto, 
                       self.agente_diferenciador, self.agente_validador],
                tasks=[tarea_inspiracion, tarea_pedagogica, tarea_arquitectura, 
                      tarea_diferenciacion, tarea_validacion],
                process=Process.sequential,
                verbose=True
            )
            
            logger.info("🚀 Ejecutando workflow few-shot...")
            resultado = crew.kickoff()
            
            # Procesar resultados
            contenido_completo = self._procesar_resultados(resultado)
            
            return ActividadEducativa(
                id=f"fewshot_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
            # Retornar actividad básica
            return ActividadEducativa(
                id=f"error_fewshot_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
        """Procesa y estructura los resultados del crew"""
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
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_fewshot") -> str:
        """Guarda una actividad en un archivo"""
        
        # Asegurar que se guarde en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA FEW-SHOT CrewAI + Ollama\n")
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
            f.write("METADATOS DEL SISTEMA FEW-SHOT:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad few-shot guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema few-shot"""
    
    print("="*70)
    print("🎓 SISTEMA DE AGENTES CREWAI FEW-SHOT PARA EDUCACIÓN")
    print("="*70)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        INSPIRADOR_MODEL = "qwen3:latest"
        PEDAGOGO_MODEL = "qwen3:latest"
        ARQUITECTO_MODEL = "qwen2:latest"
        DIFERENCIADOR_MODEL = "mistral:latest"
        VALIDADOR_MODEL = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        # Inicializar sistema
        print(f"\n🔧 Inicializando sistema few-shot:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Modelos especializados por agente:")
        print(f"     🎭 Inspirador: {INSPIRADOR_MODEL}")
        print(f"     📚 Pedagogo: {PEDAGOGO_MODEL}")
        print(f"     🏗️ Arquitecto: {ARQUITECTO_MODEL}")
        print(f"     🎯 Diferenciador: {DIFERENCIADOR_MODEL}")
        print(f"     ✅ Validador: {VALIDADOR_MODEL}")
        
        sistema = SistemaAgentesFewShot(
            ollama_host=OLLAMA_HOST,
            inspirador_model=INSPIRADOR_MODEL,
            pedagogo_model=PEDAGOGO_MODEL,
            arquitecto_model=ARQUITECTO_MODEL,
            diferenciador_model=DIFERENCIADOR_MODEL,
            validador_model=VALIDADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema few-shot inicializado correctamente!")
        print(f"📖 Ejemplos k_ cargados: {len(sistema.ejemplos_k)}")
        
        # Menú
        while True:
            print("\n" + "="*50)
            print("🎓 GENERACIÓN FEW-SHOT")
            print("1. 🎯 Generar actividad con few-shot learning")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_colaborativa(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad few-shot generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🎯 Sistema: Few-shot con ejemplos k_")
                print(f"   📖 Ejemplos usados: {len(actividad.metadatos.get('ejemplos_k_usados', []))}")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema few-shot: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")
        print("   4. Los archivos k_ estén en actividades_generadas/")


if __name__ == "__main__":
    main()