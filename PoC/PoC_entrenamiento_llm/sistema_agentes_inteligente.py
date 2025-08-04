#!/usr/bin/env python3
"""
Sistema de Agentes Inteligente con CrewAI + Ollama
- Few-shot estratégico con ejemplos k_
- Human-in-the-loop inteligente con análisis de contexto
- Flujo de 4 fases con LLMs reales
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import re

# ================================================================================
# CONFIGURACIÓN CRÍTICA DE OLLAMA + CREWAI (DEBE IR ANTES DE LOS IMPORTS)
# ================================================================================

# Configurar variables de entorno para evitar errores con CrewAI
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"  
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"
os.environ["LITELLM_PROVIDER"] = "ollama"  # CRÍTICO: Definir provider
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder requerido
os.environ["OPENAI_MODEL_NAME"] = "ollama/qwen3:latest"  # Con prefijo
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AgentesInteligente")

try:
    from crewai import Agent, Task, Crew, Process
    from langchain_community.llms import Ollama
    import litellm
    logger.info("✅ CrewAI y dependencias importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando dependencias: {e}")
    logger.error("💡 Instala: pip install crewai langchain-community")
    raise

# Sistema limpio usando solo langchain_community.llms.Ollama

@dataclass
class ActividadEducativa:
    """Estructura de datos para actividad educativa completa"""
    id: str
    titulo: str
    materia: str
    tema: str
    clima: str  # simple, juego, narrativa, complejo
    modalidad_trabajo: str  # individual, grupal, mixta
    contenido_completo: str
    tareas_estudiantes: Dict[str, str]
    materiales: List[str]
    duracion: str
    fases: List[str]
    metadatos: Dict
    timestamp: str

class CargadorEjemplosK:
    """Carga ejemplos k_ reales como few-shot estratégico"""
    
    def __init__(self, directorio_ejemplos: str = "."):
        self.directorio = directorio_ejemplos
        self.ejemplos_k = {}
        self.metadatos_ejemplos = {}
        self._cargar_ejemplos_k()
    
    def _cargar_ejemplos_k(self):
        """Carga ejemplos k_ desde archivos reales"""
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_feria_acertijos.txt", 
            "actividades_generadas/k_sonnet_supermercado.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            ruta_completa = os.path.join(self.directorio, archivo)
            if os.path.exists(ruta_completa):
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        
                        # Extraer metadatos del ejemplo
                        self.metadatos_ejemplos[nombre_ejemplo] = self._extraer_metadatos(contenido)
                        logger.info(f"✅ Cargado ejemplo k_: {nombre_ejemplo}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {archivo}: {e}")
        
        if not self.ejemplos_k:
            logger.warning("⚠️ No se encontraron ejemplos k_. Usando ejemplo básico.")
            self._crear_ejemplo_fallback()
    
    def _extraer_metadatos(self, contenido: str) -> Dict[str, Any]:
        """Extrae metadatos pedagógicos del ejemplo k_"""
        metadatos = {
            "materia_detectada": "general",
            "modalidad_detectada": "mixta",
            "tipo_actividad": "práctica",
            "estudiantes_mencionados": [],
            "interdependencia": False,
            "materiales_fisicos": []
        }
        
        contenido_lower = contenido.lower()
        
        # Detectar materia
        if any(palabra in contenido_lower for palabra in ["matemática", "número", "fracción", "área", "volumen"]):
            metadatos["materia_detectada"] = "matematicas"
        elif any(palabra in contenido_lower for palabra in ["célula", "ciencia", "biología", "orgánulo"]):
            metadatos["materia_detectada"] = "ciencias"
        elif any(palabra in contenido_lower for palabra in ["cuento", "historia", "narrativa", "lengua"]):
            metadatos["materia_detectada"] = "lengua"
        
        # Detectar modalidad
        if "grupo" in contenido_lower or "equipo" in contenido_lower:
            metadatos["modalidad_detectada"] = "grupal"
        elif "individual" in contenido_lower or "cada uno" in contenido_lower:
            metadatos["modalidad_detectada"] = "individual"
        
        # Detectar estudiantes mencionados
        estudiantes = re.findall(r'(Alex|Elena|Luis|Ana|Sara|Hugo|Emma|María)', contenido, re.IGNORECASE)
        metadatos["estudiantes_mencionados"] = list(set(estudiantes))
        
        # Detectar interdependencia
        if any(palabra in contenido_lower for palabra in ["necesita", "usa", "verifica", "depende", "entre todos"]):
            metadatos["interdependencia"] = True
        
        # Detectar materiales físicos
        materiales = re.findall(r'(regla|papel|bloques|tijeras|pegamento|pinturas|cartón|objetos)', contenido_lower)
        metadatos["materiales_fisicos"] = list(set(materiales))
        
        return metadatos
    
    def _crear_ejemplo_fallback(self):
        """Crea ejemplo básico si no hay ejemplos k_"""
        self.ejemplos_k["k_basico"] = """
Actividad Básica Colaborativa:
- Alex: Organizar materiales en mesa por categorías
- Elena: Medir objetos usando regla y anotar medidas
- Luis: Construir estructura con bloques según medidas de Elena
- Ana: Verificar que medidas de Elena coinciden con construcción de Luis
- Sara: Documentar proceso completo en papel
- Hugo: Preparar presentación de resultados grupales
Interdependencia: Ana necesita medidas de Elena, Luis usa medidas de Elena, Sara documenta trabajo de todos.
        """
        self.metadatos_ejemplos["k_basico"] = {
            "materia_detectada": "general",
            "modalidad_detectada": "grupal", 
            "tipo_actividad": "práctica",
            "estudiantes_mencionados": ["Alex", "Elena", "Luis", "Ana", "Sara", "Hugo"],
            "interdependencia": True,
            "materiales_fisicos": ["regla", "papel", "bloques"]
        }
    
    def seleccionar_ejemplo_estrategico(self, materia: str, tema: str, modalidad: str = "mixta") -> str:
        """Selecciona ejemplo k_ más relevante estratégicamente"""
        mejor_ejemplo = None
        mejor_puntuacion = 0
        
        for nombre, metadatos in self.metadatos_ejemplos.items():
            puntuacion = 0
            
            # Puntuación por materia
            if metadatos["materia_detectada"] == materia.lower():
                puntuacion += 5
            elif metadatos["materia_detectada"] == "general":
                puntuacion += 1
            
            # Puntuación por modalidad
            if metadatos["modalidad_detectada"] == modalidad:
                puntuacion += 3
            elif metadatos["modalidad_detectada"] == "mixta":
                puntuacion += 1
            
            # Puntuación por interdependencia (siempre deseable)
            if metadatos["interdependencia"]:
                puntuacion += 2
            
            # Puntuación por materiales físicos
            if len(metadatos["materiales_fisicos"]) > 2:
                puntuacion += 2
            
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_ejemplo = nombre
        
        ejemplo_seleccionado = mejor_ejemplo or list(self.ejemplos_k.keys())[0]
        logger.info(f"📋 Ejemplo k_ seleccionado: {ejemplo_seleccionado} (puntuación: {mejor_puntuacion})")
        
        return self.ejemplos_k[ejemplo_seleccionado]

class SistemaAgentesInteligente:
    """Sistema principal con CrewAI + Ollama + Few-shot estratégico + Human-in-the-loop"""
    
    def __init__(self, ollama_host: str = "192.168.1.10"):
        self.ollama_host = ollama_host
        self.cargador_ejemplos = CargadorEjemplosK()
        
        # Configurar LiteLLM para Ollama
        self._configurar_litellm()
        
        # Crear LLMs específicos para cada agente
        self._crear_llms_especificos()
        
        # Crear agentes especializados
        self._crear_agentes()
        
        logger.info("✅ Sistema de Agentes Inteligente inicializado")
    
    def _configurar_litellm(self):
        """Configura LiteLLM usando el patrón EXACTO que funciona"""
        try:
            import litellm
            
            logger.info("🔧 Configurando LiteLLM para Ollama local...")
            
            # Configurar variables específicas para LiteLLM + Ollama (patrón exitoso)
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            logger.info("✅ LiteLLM configurado con patrón exitoso")
        except Exception as e:
            logger.warning(f"⚠️ Advertencia configurando LiteLLM: {e}")
    
    def _crear_llms_especificos(self):
        """Crea LLMs específicos para cada agente usando patrón exitoso"""
        try:
            # Usar el patrón EXACTO que funciona en sistema_agentes_crewai.py
            modelos = ["qwen3:latest", "qwen2:latest", "mistral:latest"]
            
            # Mapear modelos para LiteLLM (patrón que funciona)
            for modelo in modelos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Crear LLMs con patrón exitoso: ollama/{modelo} + base_url
            logger.info("🔄 Creando LLMs con patrón exitoso:")
            
            self.llm_clima = Ollama(
                model=f"ollama/qwen3:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_estructurador = Ollama(
                model=f"ollama/qwen2:latest", 
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_tareas = Ollama(
                model=f"ollama/mistral:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_repartidor = Ollama(
                model=f"ollama/qwen3:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info("✅ LLMs específicos creados con patrón exitoso")
        except Exception as e:
            logger.error(f"❌ Error creando LLMs: {e}")
            raise
    
    def _crear_agentes(self):
        """Crea los agentes especializados con detector inteligente y validador final"""
        
        # DETECTOR INTELIGENTE (CENTRAL)
        self.agente_detector = Agent(
            role="Detector Inteligente de Contexto Pedagógico",
            goal="Analizar cualquier prompt educativo y extraer materia, tema, modalidad, limitaciones y preferencias pedagógicas",
            backstory="""Eres un experto en análisis curricular que puede interpretar cualquier descripción 
            educativa en lenguaje natural. Identificas materias (incluso con sinónimos como 'expresión plástica' = arte), 
            temas específicos, modalidades de trabajo, limitaciones de tiempo/materiales y preferencias pedagógicas. 
            Tu análisis guía a todos los demás agentes proporcionándoles contexto estructurado.""",
            llm=self.llm_clima,  # Usa el LLM más capaz para análisis
            verbose=True,
            allow_delegation=False
        )
        
        # VALIDADOR FINAL (GUARDIÁN DE CALIDAD)
        self.agente_validador = Agent(
            role="Validador de Calidad Pedagógica",
            goal="Garantizar que cada fase cumple estándares k_ de especificidad, coherencia y practicidad",
            backstory="""Eres un validador pedagógico experto que aplica estándares de calidad rigurosos. 
            Tu función es rechazar outputs genéricos, vagas o impracticables. Exiges tareas concretas 
            con verbos de acción específicos ('medir 3 objetos' NO 'investigar tema'), cantidades definidas 
            y resultados medibles. Comparas con ejemplos k_ para mantener calidad.""",
            llm=self.llm_estructurador,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTES ESPECIALISTAS (NIVEL OPERATIVO)
        self.agente_clima = Agent(
            role="Especialista en Clima Pedagógico",
            goal="Determinar el tipo de actividad (simple, juego, narrativa, complejo) más adecuado según contexto",
            backstory="""Eres un experto en psicopedagogía que analiza contextos educativos para determinar 
            qué tipo de actividad funcionará mejor. Consideras factores como tiempo disponible, 
            materiales, características de estudiantes y preferencias del docente. Reportas al Coordinador.""",
            llm=self.llm_clima,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_estructurador = Agent(
            role="Arquitecto de Experiencias Educativas", 
            goal="Diseñar la estructura específica de la actividad usando ejemplos k_ como referencia",
            backstory="""Eres un diseñador de experiencias educativas que crea actividades específicas 
            y detalladas. Usas ejemplos exitosos como inspiración pero adaptas todo al contexto específico. 
            Siempre incluyes materiales concretos, duración realista y objetivos claros. Tu trabajo debe 
            pasar la validación de coherencia y especificidad.""",
            llm=self.llm_estructurador,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_tareas = Agent(
            role="Especialista en Desglose Pedagógico",
            goal="Descomponer actividades en tareas específicas y concretas para cada estudiante",
            backstory="""Eres un experto en crear tareas educativas específicas y medibles. 
            Evitas roles abstractos como 'coordinador' y prefieres tareas concretas como 
            'medir 3 objetos con regla'. Cada tarea debe ser clara y ejecutable. El Validador rechazará 
            tu trabajo si es genérico.""",
            llm=self.llm_tareas,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_repartidor = Agent(
            role="Especialista en Inclusión y Adaptación",
            goal="Asignar tareas de forma equilibrada considerando perfiles individuales de estudiantes", 
            backstory="""Eres un especialista en educación inclusiva que conoce las necesidades específicas 
            de estudiantes con TEA, TDAH, altas capacidades, etc. Asignas tareas considerando estilos 
            de aprendizaje y necesidades individuales para maximizar participación y aprendizaje.""",
            llm=self.llm_repartidor,
            verbose=True,
            allow_delegation=False
        )
        
        # COORDINADOR DE PARALELISMO (OPCIONAL - solo se activa cuando detecta oportunidades)
        self.agente_coordinador_paralelismo = Agent(
            role="Coordinador de Trabajo Paralelo",
            goal="Identificar oportunidades naturales de trabajo simultáneo y coordinación entre estudiantes",
            backstory="""Eres un especialista en dinámicas de grupo que detecta cuándo las tareas pueden 
            ejecutarse simultáneamente sin forzar interdependencias artificiales. Solo intervienes cuando 
            identificas trabajo genuino en paralelo (como tu ejemplo de la fábrica de fracciones con 4 estaciones 
            simultáneas). Respetas el trabajo individual cuando es apropiado, pero optimizas la colaboración 
            cuando es natural y productiva.""",
            llm=self.llm_estructurador,  # Usar el mismo LLM que el estructurador
            verbose=True,
            allow_delegation=False
        )
    
    def detectar_contexto_multidimensional(self, prompt_profesor: str) -> Dict[str, Any]:
        """Detector libre que analiza múltiples dimensiones y genera opciones dinámicas"""
        
        tarea_deteccion = Task(
            description=f"""
Analiza este prompt educativo desde múltiples dimensiones y genera opciones contextuales:

PROMPT DEL PROFESOR: "{prompt_profesor}"

ANÁLISIS MULTIDIMENSIONAL:
1. CONTENIDO: ¿Qué materia, tema, nivel de complejidad conceptual?
2. NARRATIVA: ¿Qué nivel narrativo necesita? (historia envolvente, contexto simple, sin narrativa)
3. METODOLOGÍA: ¿Qué tipo de actividades? (talleres, debates, experimentos, creación, etc.)
4. ESTRUCTURA TEMPORAL: ¿Cómo organizar el tiempo? (sesión única, varios días, por bloques)
5. MODALIDAD SOCIAL: ¿Cómo trabajar? (individual, parejas, grupos pequeños, clase completa, mixto)
6. PRODUCTOS: ¿Qué debe generar? (contenido real como guiones, organizaciones, ambos)
7. ADAPTACIONES: ¿Qué necesidades específicas detectas?

GENERA OPCIONES DINÁMICAS específicas para ESTA actividad:
Basándote en el análisis, propón 2-3 preguntas clave que el profesor necesita decidir.

FORMATO DE RESPUESTA:
```json
{{
    "contexto_base": {{
        "materia": "detectado",
        "tema": "detectado",
        "complejidad_conceptual": "alta/media/baja"
    }},
    "dimensiones": {{
        "narrativa": {{"nivel": "alta/media/baja/ninguna", "tipo": "descripción"}},
        "metodologia": {{"principal": "tipo_principal", "secundarias": ["tipo1", "tipo2"]}},
        "estructura_temporal": {{"tipo": "sesion_unica/varios_dias/bloques", "flexibilidad": "alta/media/baja"}},
        "modalidad_social": {{"principal": "grupal/individual/mixta", "variaciones": ["detalles"]}},
        "productos_esperados": ["producto1", "producto2"],
        "adaptaciones_detectadas": ["necesidad1", "necesidad2"]
    }},
    "opciones_dinamicas": [
        "Pregunta específica 1 para esta actividad",
        "Pregunta específica 2 para esta actividad",
        "Pregunta específica 3 si es necesaria"
    ],
    "recomendacion_ia": "Mi recomendación basada en el análisis completo"
}}
```

Genera opciones ESPECÍFICAS para este contexto, no preguntas genéricas.
            """,
            agent=self.agente_detector,
            expected_output="JSON con análisis multidimensional y opciones dinámicas"
        )
        
        # Ejecutar detección
        resultado = Task(
            description=tarea_deteccion.description,
            agent=self.agente_detector,
            expected_output=tarea_deteccion.expected_output
        )
        
        crew_detector = Crew(
            agents=[self.agente_detector],
            tasks=[resultado],
            process=Process.sequential,
            verbose=True
        )
        
        contexto_detectado = crew_detector.kickoff()
        logger.info(f"🔍 Contexto detectado: {str(contexto_detectado)[:200]}...")
        
        # Convertir CrewOutput a string para procesamiento
        if hasattr(contexto_detectado, 'raw'):
            return str(contexto_detectado.raw)
        else:
            return str(contexto_detectado)

    def generar_actividad_desde_prompt(self, prompt_profesor: str) -> ActividadEducativa:
        """Genera actividad con flujo por fases y validación humana"""
        
        print("\n🎯 INICIANDO FLUJO POR FASES CON VALIDACIÓN HUMANA")
        print("="*60)
        
        # FASE 0: DETECCIÓN MULTIDIMENSIONAL
        print("\n🔍 FASE 0: ANALIZANDO TU DESCRIPCIÓN...")
        contexto_detectado = self.detectar_contexto_multidimensional(prompt_profesor)
        
        # VALIDACIÓN PREVIA: Contexto general y recomendación
        contexto_aprobado = self._validar_contexto_general(contexto_detectado)
        
        # FASE 1: OPCIONES DINÁMICAS (solo si contexto aprobado)
        opciones_decididas = self._fase_opciones_dinamicas(contexto_aprobado)
        
        # VALIDACIÓN 1: Después de decidir opciones específicas
        if not self._validacion_humana_intermedia("opciones específicas", opciones_decididas):
            opciones_decididas = self._refinar_opciones(contexto_aprobado, opciones_decididas)
        
        # FASE 2: ESTRUCTURA + ORGANIZACIÓN (SIN VALIDACIÓN INTERMEDIA)
        estructura_completa = self._fase_estructura_libre(opciones_decididas, contexto_detectado)
        
        # VALIDACIÓN 2: Después de estructura completa
        if not self._validacion_humana_intermedia("estructura y organización", estructura_completa):
            estructura_completa = self._refinar_estructura(contexto_detectado, estructura_completa)
        
        # FASE 3: ACTIVIDAD FINAL CON ITERACIÓN
        actividad_final = self._crear_actividad_final_iterativa(estructura_completa, contexto_detectado)
        
        return actividad_final
    
    def _validar_contexto_general(self, contexto_detectado) -> Dict[str, Any]:
        """Validación previa: mostrar recomendación general antes de preguntas específicas"""
        
        print(f"\n✅ VALIDACIÓN PREVIA: CONTEXTO GENERAL")
        print("=" * 60)
        
        # Extraer análisis del detector (igual que en _fase_opciones_dinamicas)
        try:
            import json
            import re
            
            contexto_str = str(contexto_detectado).encode('utf-8', errors='ignore').decode('utf-8')
            json_match = re.search(r'```json\s*({.*?})\s*```', contexto_str, re.DOTALL | re.MULTILINE)
            
            if json_match:
                analisis = json.loads(json_match.group(1))
            else:
                print(f"📝 Contexto recibido: {contexto_str[:500]}...")
                analisis = {
                    "contexto_base": {"materia": "detectado", "tema": "detectado"},
                    "recomendacion_ia": "Basado en tu descripción, recomiendo una actividad práctica."
                }
                
        except Exception as e:
            print(f"⚠️ Error procesando contexto: {e}")
            analisis = {
                "contexto_base": {"materia": "error", "tema": "error"},
                "recomendacion_ia": "Hubo un error analizando tu descripción."
            }
        
        # Mostrar contexto detectado
        print(f"\n📋 CONTEXTO DETECTADO:")
        if "contexto_base" in analisis:
            base = analisis["contexto_base"]
            print(f"   📚 Materia: {base.get('materia', 'no detectado')}")
            print(f"   🎯 Tema: {base.get('tema', 'no detectado')}")
            print(f"   📈 Complejidad: {base.get('complejidad_conceptual', 'no detectado')}")
        
        # Mostrar recomendación de la IA
        if "recomendacion_ia" in analisis:
            print(f"\n🤖 RECOMENDACIÓN GENERAL: {analisis['recomendacion_ia']}")
        
        # Validación del contexto general
        print(f"\n🤔 ¿Este enfoque general te parece correcto?")
        print(f"   (Si dices 'no', podré cambiar completamente el enfoque)")
        
        respuesta = input(f"🗣️ (sí/no): ").strip().lower()
        
        if respuesta in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            print(f"\n✅ ¡Perfecto! Continuemos con opciones específicas.")
            return analisis
        else:
            print(f"\n🔄 ¿Qué enfoque prefieres?")
            feedback_general = input(f"🗣️ Tu respuesta: ").strip()
            
            # Re-analizar SOLO con el feedback del usuario, no el contexto original
            contexto_refinado = self.detectar_contexto_multidimensional(feedback_general)
            
            # Mostrar el NUEVO contexto basado en el feedback
            print(f"\n✅ NUEVO CONTEXTO BASADO EN TU FEEDBACK:")
            print("=" * 60)
            
            # Procesar contexto refinado
            try:
                import json
                contexto_str = str(contexto_refinado).encode('utf-8', errors='ignore').decode('utf-8')
                json_match = re.search(r'```json\s*({.*?})\s*```', contexto_str, re.DOTALL | re.MULTILINE)
                
                if json_match:
                    analisis_refinado = json.loads(json_match.group(1))
                else:
                    analisis_refinado = {
                        "contexto_base": {"materia": "personalizado", "tema": feedback_general[:50]},
                        "recomendacion_ia": f"Basado en tu feedback: {feedback_general}"
                    }
            except:
                analisis_refinado = {
                    "contexto_base": {"materia": "personalizado", "tema": feedback_general[:50]},
                    "recomendacion_ia": f"Enfoque personalizado: {feedback_general}"
                }
            
            # Mostrar el nuevo análisis
            if "contexto_base" in analisis_refinado:
                base = analisis_refinado["contexto_base"]
                print(f"   📚 Materia: {base.get('materia', 'personalizado')}")
                print(f"   🎯 Tema: {base.get('tema', feedback_general[:50])}")
                print(f"   📈 Complejidad: {base.get('complejidad_conceptual', 'según tu enfoque')}")
            
            if "recomendacion_ia" in analisis_refinado:
                print(f"\n🤖 NUEVA RECOMENDACIÓN: {analisis_refinado['recomendacion_ia']}")
            
            # Confirmación del nuevo enfoque (sin recursión infinita)
            print(f"\n🤔 ¿Este nuevo enfoque refleja mejor lo que quieres?")
            confirmacion = input(f"🗣️ (sí/no): ").strip().lower()
            
            if confirmacion in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
                print(f"\n✅ ¡Perfecto! Continuemos con este enfoque personalizado.")
                return analisis_refinado
            else:
                print(f"\n⚠️ Volvamos al enfoque original entonces.")
                return analisis
    
    def _fase_opciones_dinamicas(self, contexto_aprobado) -> Dict[str, Any]:
        """Fase 1: Preguntas específicas sobre actividad (contexto ya validado)"""
        
        print(f"\n🧠 FASE 1: OPCIONES ESPECÍFICAS")
        print("-" * 50)
        
        # Extraer análisis del detector
        try:
            import json
            # Convertir contexto_aprobado a string si es necesario
            contexto_str = str(contexto_aprobado)
            if True:  # Siempre procesar como string
                # Buscar JSON en el string
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', contexto_str, re.DOTALL | re.MULTILINE)
                if json_match:
                    analisis = json.loads(json_match.group(1))
                else:
                    # Fallback si no encuentra JSON
                    print(f"📝 Contexto recibido: {contexto_str[:500]}...")
                    analisis = {
                        "contexto_base": {"materia": "detectado", "tema": "detectado"},
                        "opciones_dinamicas": ["¿Qué tipo de actividad prefieres?"],
                        "recomendacion_ia": "Basado en tu descripción, recomiendo una actividad práctica."
                    }
            else:
                analisis = {
                    "contexto_base": {"materia": "no detectado", "tema": "no detectado"},
                    "opciones_dinamicas": ["¿Cómo te gustaría enfocar esta actividad?"],
                    "recomendacion_ia": "No pude analizar tu descripción completamente."
                }
                
        except Exception as e:
            print(f"\u26a0\ufe0f Error procesando contexto: {e}")
            print(f"\ud83d\udcdd Contexto bruto: {str(contexto_detectado)[:300]}...")
            analisis = {
            "contexto_base": {"materia": "error", "tema": "error"},
            "opciones_dinamicas": ["¿Cómo te gustaría enfocar esta actividad?"],
            "recomendacion_ia": "Hubo un error analizando tu descripción, pero puedo ayudarte."
        }
        
        # El contexto ya fue mostrado y aprobado en la validación previa
        print(f"\n🎯 Ahora vamos con las opciones específicas:")
        
        # Hacer preguntas dinámicas
        decisiones = {}
        opciones_dinamicas = analisis.get("opciones_dinamicas", [])
        
        for i, pregunta in enumerate(opciones_dinamicas, 1):
            print(f"\n🤔 PREGUNTA {i}: {pregunta}")
            respuesta = input(f"🗣\ufe0f Tu respuesta: ").strip()
            decisiones[f"decision_{i}"] = respuesta
        
        # Si no hay opciones dinámicas, hacer una pregunta genérica
        if not opciones_dinamicas:
            print(f"\n🤔 ¿Cómo te gustaría enfocar esta actividad?")
            respuesta = input(f"🗣\ufe0f Tu respuesta: ").strip()
            decisiones["enfoque_general"] = respuesta
        
        return {
            "analisis_detector": analisis,
            "decisiones_profesor": decisiones
        }
    
    def _validacion_humana_intermedia(self, fase: str, contenido: Any) -> bool:
        """Validación humana intermedia más natural"""
        
        print(f"\n✅ VALIDACIÓN: {fase.upper()}")
        print("-" * 40)
        print(f"\u00bfTe parece bien el enfoque hasta ahora?")
        
        respuesta = input(f"🗣\ufe0f (sí/no/cambiar): ").strip().lower()
        
        if respuesta in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            return True
        elif respuesta in ['no', 'cambiar', 'modificar']:
            return False
        else:
            print("\u26a0\ufe0f No entendí tu respuesta, asumiré que está bien.")
            return True
    
    def _refinar_opciones(self, contexto_original: Dict, opciones_actuales: Dict) -> Dict:
        """Refina opciones basándose en feedback del profesor"""
        
        print(f"\n🔄 REFINANDO OPCIONES...")
        feedback = input(f"🗣\ufe0f ¿Qué te gustaría cambiar?: ").strip()
        
        # Re-analizar con el feedback
        contexto_refinado = self.detectar_contexto_multidimensional(
            f"Contexto original: {contexto_original}\nFeedback del profesor: {feedback}"
        )
        
        # Aplicar feedback directamente, no volver a preguntar
        return {
            "analisis_detector": contexto_refinado,
            "decisiones_profesor": {
                "feedback_aplicado": feedback,
                "contexto_refinado": "El profesor quiere cambiar el enfoque según su feedback"
            }
        }
    
    def _fase_estructura_libre(self, opciones_decididas: Dict, contexto_detectado: Dict) -> Dict[str, Any]:
        """Fase 2: Genera estructura completa basada en decisiones del profesor"""
        
        print(f"\n🏠 FASE 2: CREANDO ESTRUCTURA COMPLETA")
        print("-" * 50)
        
        # Crear prompt inteligente basado en las decisiones
        decisiones_texto = "\n".join([f"- {k}: {v}" for k, v in opciones_decididas.get("decisiones_profesor", {}).items()])
        analisis_texto = str(opciones_decididas.get("analisis_detector", {}))
        
        tarea_estructura = Task(
            description=f"""
Crea una estructura completa para la actividad basada en:

DECISIONES DEL PROFESOR:
{decisiones_texto}

ANÁLISIS ORIGINAL:
{analisis_texto}

CREA:
1. Si el profesor pide un GUIÓN → genera el guión teatral completo
2. Si pide ORGANIZACIÓN → estructura por días/grupos como "Lunes: X, Y, Z hacen A mientras P, Q hacen B"
3. Si pide AMBOS → guión + organización

IMPORTANTE:
- Genera CONTENIDO REAL, no solo descripciones
- Si es teatro → diálogos completos entre personajes
- Si es organización → reparto práctico por días y grupos
- Adapta para Elena (TEA), Luis (TDAH), Ana (altas capacidades), etc.

FORMATO:
- Título atractivo
- Duración realista
- Materiales específicos
- Contenido/Guión si se pide
- Organización temporal si se pide
- Adaptaciones incluidas naturalmente
            """,
            agent=self.agente_estructurador,
            expected_output="Estructura completa con contenido real generado"
        )
        
        crew_estructura = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_estructura],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_resultado = crew_estructura.kickoff()
        
        print(f"\n🏠 ESTRUCTURA GENERADA:")
        print(str(estructura_resultado))
        
        # NUEVA FUNCIONALIDAD: Detección automática de oportunidades de paralelismo
        if self._detectar_oportunidades_paralelismo_natural(str(estructura_resultado)):
            print(f"\n🔄 Detecté oportunidades de trabajo simultáneo entre estudiantes.")
            optimizar = input(f"¿Quieres que coordine el trabajo paralelo? (sí/no): ").strip().lower()
            
            if optimizar in ['s', 'sí', 'si', 'vale', 'ok']:
                print(f"\n⚡ Optimizando coordinación paralela...")
                estructura_resultado = self._optimizar_coordinacion_paralela(estructura_resultado, analisis_texto)
                print(f"\n🔄 ESTRUCTURA OPTIMIZADA PARA PARALELISMO:")
                print(str(estructura_resultado))
        
        # Obtener ejemplo_k si es necesario para metadatos
        ejemplo_k_usado = "ninguno"
        if "estructura_completa" in opciones_decididas:
            ejemplo_k_usado = "estructura_completa_generada"
        
        return {
            "estructura_completa": estructura_resultado,
            "opciones_base": opciones_decididas,
            "ejemplo_k_usado": ejemplo_k_usado
        }
    
    def _refinar_estructura(self, contexto_original: Dict, estructura_actual: Dict) -> Dict:
        """Refina estructura basándose en feedback del profesor"""
        
        print(f"\n🔄 REFINANDO ESTRUCTURA...")
        feedback = input(f"🗣\ufe0f ¿Qué te gustaría cambiar en la estructura?: ").strip()
        
        # Crear tarea de refinamiento
        tarea_refinamiento = Task(
            description=f"""
ESTRUCTURA ACTUAL:
{estructura_actual.get('estructura_completa', '')}

FEEDBACK DEL PROFESOR:
"{feedback}"

REFINA la estructura según el feedback:
- Mantén lo que funciona
- Cambia lo que el profesor pide
- Genera contenido real si se solicita
- Adapta organización si es necesario
            """,
            agent=self.agente_estructurador,
            expected_output="Estructura refinada según feedback del profesor"
        )
        
        crew_refinamiento = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_refinamiento],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_refinada = crew_refinamiento.kickoff()
        
        return {
            "estructura_completa": estructura_refinada,
            "opciones_base": estructura_actual.get("opciones_base", {})
        }
    
    def _crear_actividad_final_iterativa(self, estructura_completa: Dict, contexto_detectado: Dict) -> ActividadEducativa:
        """Fase 3: Crea actividad final con iteración hasta que el profesor esté satisfecho"""
        
        print(f"\n✨ FASE 3: CREANDO ACTIVIDAD FINAL")
        print("-" * 50)
        
        # Extraer contexto real para la actividad final
        try:
            # Buscar contexto real en los datos pasados
            if isinstance(contexto_detectado, dict):
                ctx_base = contexto_detectado.get("contexto_base", {})
                ctx_dims = contexto_detectado.get("dimensiones", {})
            else:
                # Intentar extraer de string si es necesario
                import json, re
                contexto_str = str(contexto_detectado)
                json_match = re.search(r'```json\s*({.*?})\s*```', contexto_str, re.DOTALL)
                if json_match:
                    ctx_data = json.loads(json_match.group(1))
                    ctx_base = ctx_data.get("contexto_base", {})
                    ctx_dims = ctx_data.get("dimensiones", {})
                else:
                    ctx_base = {"materia": "detectado", "tema": "detectado"}
                    ctx_dims = {"narrativa": {"nivel": "detectado"}}
        except:
            ctx_base = {"materia": "detectado", "tema": "detectado"}
            ctx_dims = {"narrativa": {"nivel": "detectado"}}
        
        # Crear actividad con contexto real
        actividad = ActividadEducativa(
            id=f"libre_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad de {ctx_base.get('tema', 'Tema Detectado').title()}",
            materia=ctx_base.get("materia", "interdisciplinar"),
            tema=ctx_base.get("tema", "proyecto colaborativo"),
            clima=ctx_dims.get("narrativa", {}).get("nivel", "detectado"),
            modalidad_trabajo=ctx_dims.get("modalidad_social", {}).get("principal", "mixta"),
            contenido_completo=str(estructura_completa.get("estructura_completa", "")),
            tareas_estudiantes=self._extraer_tareas_reales(estructura_completa),
            materiales=self._extraer_materiales_reales(estructura_completa),
            duracion="según estructura",
            fases=["Preparación", "Desarrollo", "Presentación"],
            metadatos={
                "contexto_detectado": str(contexto_detectado),
                "estructura_completa": str(estructura_completa),
                "ejemplo_k_usado": [estructura_completa.get("ejemplo_k_usado", "ninguno")],
                "sistema_libre": True
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Iteración hasta satisfacción
        max_iteraciones = 3
        for iteracion in range(1, max_iteraciones + 1):
            print(f"\n🔄 ITERACIÓN {iteracion}/{max_iteraciones}")
            
            # Mostrar actividad
            self.mostrar_actividad(actividad)
            
            # Validación final
            print(f"\n✅ VALIDACIÓN FINAL:")
            satisfecho = input(f"🗣\ufe0f ¿Estás satisfecho con la actividad? (sí/no): ").strip().lower()
            
            if satisfecho in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
                print(f"\n✨ ¡ACTIVIDAD COMPLETADA!")
                break
            elif iteracion < max_iteraciones:
                feedback_final = input(f"🗣\ufe0f ¿Qué quieres cambiar?: ").strip()
                
                # Refinar actividad completa
                nueva_estructura = self._refinar_estructura(contexto_detectado, estructura_completa)
                actividad.contenido_completo = str(nueva_estructura.get("estructura_completa", ""))
                actividad.metadatos["iteraciones"] = iteracion
            else:
                print(f"\n⚠\ufe0f Se alcanzó el máximo de iteraciones. Finalizando.")
        
        return actividad
    
    def _fase_clima_con_validacion(self, contexto_detectado) -> str:
        """Fase 1: Determinar clima con validación humana"""
        
        print(f"\n🎭 FASE 1: DETERMINANDO CLIMA PEDAGÓGICO")
        print("-" * 50)
        
        # Mostrar contexto detectado
        print(f"📋 Contexto detectado: {str(contexto_detectado)[:300]}...")
        
        tarea_clima = Task(
            description=f"""
Basándote en este contexto: {contexto_detectado}

Propón 3 opciones de CLIMA pedagógico con justificación:

1. SIMPLE: Actividad directa y práctica (20-30 min)
2. JUEGO: Dinámico con competencia/retos (30-45 min)  
3. NARRATIVA: Historia/contexto envolvente (45-60 min)
4. COMPLEJO: Proyecto investigativo (60+ min)

Para cada opción explica:
- Por qué encaja con el contexto
- Qué tipo de actividad sería
- Duración estimada

FORMATO:
Opción 1: [CLIMA] - [Justificación breve]
Opción 2: [CLIMA] - [Justificación breve]  
Opción 3: [CLIMA] - [Justificación breve]

RECOMENDACIÓN: [La mejor opción y por qué]
            """,
            agent=self.agente_clima,
            expected_output="3 opciones de clima con justificación y recomendación"
        )
        
        crew_clima = Crew(
            agents=[self.agente_clima],
            tasks=[tarea_clima],
            process=Process.sequential,
            verbose=True
        )
        
        opciones_clima = crew_clima.kickoff()
        
        # Mostrar opciones al profesor
        print(f"\n🎭 OPCIONES DE CLIMA PROPUESTAS:")
        print(str(opciones_clima))
        
        # Validación humana con opciones claras
        while True:
            print(f"\n🗣️ PROFESOR: ¿Qué decides sobre el clima?")
            print("   1️⃣ SEGUIR - Me gusta alguna de las opciones propuestas")
            print("   2️⃣ CAMBIAR - Quiero algo diferente")
            
            opcion = input(f"🔢 Tu elección (1/2): ").strip()
            
            if opcion == "1":
                eleccion = input(f"📝 ¿Cuál prefieres? (simple/juego/narrativa/complejo): ").strip().lower()
                print(f"✅ Clima elegido: {eleccion}")
                return eleccion
            elif opcion == "2":
                cambio_clima = input(f"\n📝 Describe el clima que prefieres: ").strip()
                
                if not cambio_clima:
                    print("⚠️ Necesito que describas qué tipo de clima quieres.")
                    continue
                
                # PROCESAR CON DETECTOR
                print(f"\n🔍 Analizando tu preferencia de clima...")
                contexto_clima = self.detectar_contexto_inteligente(f"Prefiero clima: {cambio_clima}")
                
                print(f"✅ Clima personalizado registrado: {cambio_clima}")
                return cambio_clima
            else:
                print("⚠️ Por favor, elige 1 o 2.")
    
    def _fase_estructura_con_validacion(self, clima_aprobado, contexto_detectado) -> str:
        """Fase 2: Estructurar actividad con validación humana"""
        
        print(f"\n🏗️ FASE 2: ESTRUCTURANDO ACTIVIDAD")
        print("-" * 50)
        
        # Extraer materia/tema del contexto para seleccionar ejemplo apropiado
        try:
            if isinstance(contexto_detectado, dict) and "contexto_base" in contexto_detectado:
                materia_real = contexto_detectado["contexto_base"].get("materia", "general")
                tema_real = contexto_detectado["contexto_base"].get("tema", "actividad")
            else:
                materia_real = "general"
                tema_real = "actividad"
        except:
            materia_real = "general"
            tema_real = "actividad"
        
        ejemplo_k = self.cargador_ejemplos.seleccionar_ejemplo_estrategico(materia_real, tema_real, "mixta")
        
        tarea_estructura = Task(
            description=f"""
CLIMA APROBADO: {clima_aprobado}
CONTEXTO ORIGINAL: {contexto_detectado}

EJEMPLO K_ DE REFERENCIA:
{ejemplo_k[:500]}...

Crea la ESTRUCTURA específica de la actividad:

INCLUYE:
- Título atractivo
- Duración total y por fases
- Materiales específicos necesarios
- Modalidad de trabajo (individual/grupal/mixta)
- Objetivos claros y medibles
- Fases temporales (ej: Fase 1: 15min intro, Fase 2: 20min desarrollo...)

SER ESPECÍFICO, NO GENÉRICO.
            """,
            agent=self.agente_estructurador,
            expected_output="Estructura detallada de la actividad"
        )
        
        crew_estructura = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_estructura],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_propuesta = crew_estructura.kickoff()
        
        # Mostrar al profesor
        print(f"\n🏗️ ESTRUCTURA PROPUESTA:")
        print(str(estructura_propuesta))
        
        # Validación humana con opciones claras
        while True:
            print(f"\n🗣️ PROFESOR: ¿Qué decides sobre esta estructura?")
            print("   1️⃣ SEGUIR - La estructura está bien")
            print("   2️⃣ CAMBIAR - Quiero modificarla")
            
            opcion = input(f"🔢 Tu elección (1/2): ").strip()
            
            if opcion == "1":
                print(f"✅ Estructura aprobada!")
                return str(estructura_propuesta)
            elif opcion == "2":
                cambio_estructura = input(f"\n📝 Describe cómo quieres la estructura: ").strip()
                
                if not cambio_estructura:
                    print("⚠️ Necesito que describas qué cambios quieres en la estructura.")
                    continue
                
                # PROCESAR CON DETECTOR Y REGENERAR
                print(f"\n🔍 Analizando cambios en estructura...")
                contexto_estructura = self.detectar_contexto_inteligente(f"Modificación estructura: {cambio_estructura}")
                
                print(f"🔄 Regenerando estructura según tus indicaciones...")
                
                tarea_regeneracion_estructura = Task(
                    description=f"""
CLIMA APROBADO: {clima_aprobado}
CONTEXTO ORIGINAL: {contexto_detectado}

FEEDBACK DEL PROFESOR: "{cambio_estructura}"
CONTEXTO ANALIZADO: {contexto_estructura}

REGENERA la estructura según las especificaciones del profesor:

INCLUYE:
- Título que refleje la visión del profesor
- Duración y fases según lo solicitado
- Materiales específicos necesarios
- Modalidad de trabajo apropiada  
- Objetivos claros
- Estructura temporal específica

SEGUIR EXACTAMENTE la visión del profesor.
                    """,
                    agent=self.agente_estructurador,
                    expected_output="Estructura regenerada según feedback del profesor"
                )
                
                crew_regeneracion_estructura = Crew(
                    agents=[self.agente_estructurador],
                    tasks=[tarea_regeneracion_estructura],
                    process=Process.sequential,
                    verbose=True
                )
                
                estructura_regenerada = crew_regeneracion_estructura.kickoff()
                
                print(f"\n🏗️ ESTRUCTURA REGENERADA:")
                print(str(estructura_regenerada))
                
                confirmacion = input(f"\n✅ ¿Ahora refleja mejor tu visión? (sí/no): ").strip().lower()
                
                if confirmacion in ['sí', 'si', 'vale', 'ok', 'bien']:
                    print(f"✅ Estructura finalmente aprobada!")
                    return str(estructura_regenerada)
                else:
                    print(f"🔄 Continuemos refinando...")
            else:
                print("⚠️ Por favor, elige 1 o 2.")
    
    def _fase_tareas_con_validacion(self, estructura_aprobada, contexto_detectado) -> str:
        """Fase 3: Desglosar tareas con validación humana"""
        
        print(f"\n📝 FASE 3: DESGLOSANDO EN TAREAS ESPECÍFICAS")
        print("-" * 50)
        
        tarea_desglose = Task(
            description=f"""
ESTRUCTURA APROBADA: {estructura_aprobada}

Desglosa en 8 TAREAS ESPECÍFICAS Y CONCRETAS:

REQUISITOS CRÍTICOS:
- Usar VERBOS DE ACCIÓN específicos (medir, cortar, escribir, explicar)
- Incluir CANTIDADES específicas (3 objetos, 2 minutos, 5 palabras)
- Evitar roles abstractos (NO "coordinador", "investigador")
- Crear INTERDEPENDENCIA real entre tareas

FORMATO:
1. [Verbo] [cantidad] [objeto] [resultado esperado]
2. [Verbo] [cantidad] [objeto] [resultado esperado]
...
8. [Verbo] [cantidad] [objeto] [resultado esperado]

EJEMPLO BUENO: "Medir 3 objetos del aula con regla y anotar medidas en tabla"
EJEMPLO MALO: "Investigar el tema asignado"
            """,
            agent=self.agente_tareas,
            expected_output="8 tareas específicas numeradas"
        )
        
        crew_tareas = Crew(
            agents=[self.agente_tareas],
            tasks=[tarea_desglose],
            process=Process.sequential,
            verbose=True
        )
        
        tareas_propuestas = crew_tareas.kickoff()
        
        print(f"\n📝 TAREAS PROPUESTAS:")
        print(str(tareas_propuestas))
        
        # Validación humana con opciones claras
        while True:
            print(f"\n🗣️ PROFESOR: ¿Qué decides sobre estas tareas?")
            print("   1️⃣ SEGUIR - Las tareas están bien, continuar")
            print("   2️⃣ CAMBIAR - Quiero modificar algo")
            
            opcion = input(f"🔢 Tu elección (1/2): ").strip()
            
            if opcion == "1":
                print(f"✅ Tareas aprobadas!")
                return str(tareas_propuestas)
            elif opcion == "2":
                # Pedir descripción del cambio
                cambio_deseado = input(f"\n📝 Describe cómo quieres que sean las tareas: ").strip()
                
                if not cambio_deseado:
                    print("⚠️ Necesito que describas qué cambios quieres.")
                    continue
                
                # PROCESAR CON DETECTOR
                print(f"\n🔍 Analizando tus modificaciones...")
                contexto_cambio = self.detectar_contexto_inteligente(f"Modificación de tareas: {cambio_deseado}")
                
                # REGENERAR TAREAS CON EL CONTEXTO MODIFICADO
                print(f"🔄 Regenerando tareas según tus indicaciones...")
                
                tarea_regeneracion = Task(
                    description=f"""
ESTRUCTURA ORIGINAL: {estructura_aprobada}

FEEDBACK DEL PROFESOR: "{cambio_deseado}"
CONTEXTO ANALIZADO: {contexto_cambio}

REGENERA las 8 tareas según las especificaciones del profesor:

REQUISITOS:
- Seguir EXACTAMENTE la visión del profesor
- Mantener especificidad (verbos + cantidades + objetos)
- Crear interdependencia real entre tareas
- Ser práctico y ejecutable

El resultado debe reflejar FIELMENTE lo que el profesor ha solicitado.
                    """,
                    agent=self.agente_tareas,
                    expected_output="8 tareas regeneradas según feedback del profesor"
                )
                
                crew_regeneracion = Crew(
                    agents=[self.agente_tareas],
                    tasks=[tarea_regeneracion],
                    process=Process.sequential,
                    verbose=True
                )
                
                tareas_regeneradas = crew_regeneracion.kickoff()
                
                print(f"\n📝 TAREAS REGENERADAS:")
                print(str(tareas_regeneradas))
                
                # Preguntar si ahora están bien
                confirmacion = input(f"\n✅ ¿Ahora reflejan mejor tu visión? (sí/no): ").strip().lower()
                
                if confirmacion in ['sí', 'si', 'vale', 'ok', 'bien']:
                    print(f"✅ Tareas finalmente aprobadas!")
                    return str(tareas_regeneradas)
                else:
                    print(f"🔄 Continuemos refinando...")
                    # El bucle continúa para permitir más ajustes
            else:
                print("⚠️ Por favor, elige 1 o 2.")
    
    def _fase_reparto_con_validacion(self, tareas_aprobadas, contexto_detectado) -> str:
        """Fase 4: Repartir tareas con validación humana"""
        
        print(f"\n👥 FASE 4: REPARTIENDO TAREAS POR ESTUDIANTE")
        print("-" * 50)
        
        perfiles = """
001 ALEX M. (reflexivo, visual) 
002 MARÍA L. (reflexivo, auditivo)
003 ELENA R. (reflexivo, visual, TEA_nivel_1) 
004 LUIS T. (impulsivo, kinestésico, TDAH_combinado)
005 ANA V. (reflexivo, auditivo, altas_capacidades)
006 SARA M. (equilibrado, auditivo)
007 EMMA K. (reflexivo, visual)
008 HUGO P. (equilibrado, visual)
        """
        
        tarea_reparto = Task(
            description=f"""
TAREAS APROBADAS: {tareas_aprobadas}

PERFILES DE ESTUDIANTES: {perfiles}

Asigna las 8 tareas considerando:
- Elena (TEA): Tareas estructuradas, visuales, claras
- Luis (TDAH): Tareas kinestésicas, cortas, con movimiento  
- Ana (altas capacidades): Tareas desafiantes, liderazgo
- Otros: Según su estilo (visual, auditivo, etc.)

FORMATO:
001 ALEX M.: [tarea específica adaptada a su perfil]
002 MARÍA L.: [tarea específica adaptada a su perfil]
...
008 HUGO P.: [tarea específica adaptada a su perfil]
            """,
            agent=self.agente_repartidor,
            expected_output="Asignación específica por estudiante"
        )
        
        crew_reparto = Crew(
            agents=[self.agente_repartidor],
            tasks=[tarea_reparto],
            process=Process.sequential,
            verbose=True
        )
        
        reparto_propuesto = crew_reparto.kickoff()
        
        print(f"\n👥 REPARTO PROPUESTO:")
        print(str(reparto_propuesto))
        
        # Validación humana con opciones claras
        while True:
            print(f"\n🗣️ PROFESOR: ¿Qué decides sobre este reparto?")
            print("   1️⃣ SEGUIR - El reparto está bien")
            print("   2️⃣ CAMBIAR - Quiero modificar asignaciones")
            
            opcion = input(f"🔢 Tu elección (1/2): ").strip()
            
            if opcion == "1":
                print(f"✅ Reparto aprobado!")
                return str(reparto_propuesto)
            elif opcion == "2":
                cambio_reparto = input(f"\n📝 Describe cómo quieres repartir las tareas: ").strip()
                
                if not cambio_reparto:
                    print("⚠️ Necesito que describas cómo quieres cambiar el reparto.")
                    continue
                
                # PROCESAR CON DETECTOR Y REGENERAR
                print(f"\n🔍 Analizando cambios en reparto...")
                contexto_reparto = self.detectar_contexto_inteligente(f"Modificación reparto: {cambio_reparto}")
                
                print(f"🔄 Regenerando reparto según tus indicaciones...")
                
                tarea_regeneracion_reparto = Task(
                    description=f"""
TAREAS ORIGINALES: {tareas_aprobadas}
PERFILES ESTUDIANTES: {perfiles}

FEEDBACK DEL PROFESOR: "{cambio_reparto}"
CONTEXTO ANALIZADO: {contexto_reparto}

REGENERA el reparto según las especificaciones del profesor:

CONSIDERA:
- La petición específica del profesor
- Necesidades de Elena (TEA), Luis (TDAH), Ana (altas capacidades)  
- Estilos de aprendizaje de cada estudiante
- Equilibrio en la carga de trabajo
- Adaptaciones necesarias

SEGUIR EXACTAMENTE las indicaciones del profesor sobre el reparto.

FORMATO:
001 ALEX M.: [tarea específica según nueva distribución]
002 MARÍA L.: [tarea específica según nueva distribución]
...
008 HUGO P.: [tarea específica según nueva distribución]
                    """,
                    agent=self.agente_repartidor,
                    expected_output="Reparto regenerado según feedback del profesor"
                )
                
                crew_regeneracion_reparto = Crew(
                    agents=[self.agente_repartidor],
                    tasks=[tarea_regeneracion_reparto],
                    process=Process.sequential,
                    verbose=True
                )
                
                reparto_regenerado = crew_regeneracion_reparto.kickoff()
                
                print(f"\n👥 REPARTO REGENERADO:")
                print(str(reparto_regenerado))
                
                confirmacion = input(f"\n✅ ¿Ahora el reparto refleja mejor tu visión? (sí/no): ").strip().lower()
                
                if confirmacion in ['sí', 'si', 'vale', 'ok', 'bien']:
                    print(f"✅ Reparto finalmente aprobado!")
                    return str(reparto_regenerado)
                else:
                    print(f"🔄 Continuemos refinando...")
            else:
                print("⚠️ Por favor, elige 1 o 2.")
    
    def _validacion_tecnica_final(self, reparto_aprobado, contexto_detectado) -> ActividadEducativa:
        """Fase 5: Validación técnica final por el validador"""
        
        print(f"\n✅ FASE 5: VALIDACIÓN TÉCNICA FINAL")
        print("-" * 50)
        
        tarea_validacion = Task(
            description=f"""
ACTIVIDAD COMPLETA A VALIDAR:
{reparto_aprobado}

CONTEXTO ORIGINAL:
{contexto_detectado}

EVALÚA SEGÚN CRITERIOS K_:
1. ¿Las tareas son ESPECÍFICAS y CONCRETAS?
2. ¿Hay COHERENCIA interna entre todas las partes?
3. ¿Es PRACTICABLE en un aula real?
4. ¿Considera ADAPTACIONES adecuadas?
5. ¿Alcanza CALIDAD de ejemplos k_?

RESPUESTA:
- APROBADA: Si cumple todos los criterios
- RECHAZADA: Si falta especificidad o coherencia

Justifica tu decisión con detalle.
            """,
            agent=self.agente_validador,
            expected_output="APROBADA/RECHAZADA con justificación"
        )
        
        crew_validacion = Crew(
            agents=[self.agente_validador],
            tasks=[tarea_validacion],
            process=Process.sequential,
            verbose=True
        )
        
        validacion_resultado = crew_validacion.kickoff()
        
        print(f"\n✅ VALIDACIÓN TÉCNICA:")
        print(str(validacion_resultado))
        
        # Crear actividad final (simplificado)
        actividad = ActividadEducativa(
            id=f"fases_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo="Actividad Generada por Fases",
            materia="interdisciplinar",
            tema="proyecto colaborativo",
            clima="narrativa",
            modalidad_trabajo="mixta",
            contenido_completo=str(reparto_aprobado),
            tareas_estudiantes={"001": "Tarea 1", "002": "Tarea 2"},  # Simplificado
            materiales=["materiales varios"],
            duracion="60 minutos",
            fases=["Fase 1", "Fase 2", "Fase 3"],
            metadatos={
                "contexto_detectado": str(contexto_detectado),
                "validacion_tecnica": str(validacion_resultado)
            },
            timestamp=datetime.now().isoformat()
        )
        
        return actividad
    
    def _extraer_tareas_reales(self, estructura_completa: Dict) -> Dict[str, str]:
        """Extrae tareas específicas del contenido generado"""
        contenido = str(estructura_completa.get("estructura_completa", ""))
        
        # Buscar patrones de asignación de estudiantes
        import re
        asignaciones = re.findall(r'(00[1-8])\s+([A-Z\s\.]+):\s*([^\n]+)', contenido)
        
        if asignaciones:
            return {codigo: tarea.strip() for codigo, nombre, tarea in asignaciones}
        
        # Buscar grupos/equipos
        grupos = re.findall(r'Grupo\s+([A-Z]).*?:\s*([^\n]+)', contenido, re.IGNORECASE)
        if grupos:
            estudiantes_base = ["001", "002", "003", "004", "005", "006", "007", "008"]
            reparto = {}
            for i, (grupo, tarea) in enumerate(grupos):
                # Asignar estudiantes a grupos de manera equilibrada
                inicio = i * 2
                fin = min(inicio + 2, len(estudiantes_base))
                for j in range(inicio, fin):
                    if j < len(estudiantes_base):
                        reparto[estudiantes_base[j]] = f"Grupo {grupo}: {tarea.strip()}"
            return reparto
        
        # Fallback: buscar actividades mencionadas
        if "quiz" in contenido.lower():
            return {
                "001": "Participar en quiz sobre sistemas del cuerpo humano",
                "002": "Buscar información en libros para responder preguntas", 
                "003": "Colaborar en equipo para obtener puntos",
                "004": "Participar en quiz sobre sistemas del cuerpo humano",
                "005": "Buscar información en libros para responder preguntas",
                "006": "Colaborar en equipo para obtener puntos",
                "007": "Participar en quiz sobre sistemas del cuerpo humano",
                "008": "Buscar información en libros para responder preguntas"
            }
        
        return {"todos": "Participar en actividad según estructura generada"}
    
    def _extraer_materiales_reales(self, estructura_completa: Dict) -> List[str]:
        """Extrae materiales específicos del contenido generado"""
        contenido = str(estructura_completa.get("estructura_completa", "")).lower()
        
        materiales = []
        
        # Buscar materiales mencionados
        if "libro" in contenido:
            materiales.append("Libros de consulta sobre anatomía")
        if "quiz" in contenido:
            materiales.append("Preguntas preparadas")
            materiales.append("Sistema de puntuación")
        if "papel" in contenido:
            materiales.append("Papel para respuestas")
        if "lápic" in contenido or "lapiz" in contenido:
            materiales.append("Lápices")
        if "pizarra" in contenido:
            materiales.append("Pizarra para puntuaciones")
        
        # Materiales por defecto si no encuentra nada
        if not materiales:
            materiales = ["Materiales según actividad generada", "Recursos de consulta"]
        
        return materiales

    def _detectar_oportunidades_paralelismo_natural(self, contenido_estructura: str) -> bool:
        """Usa IA para detectar automáticamente oportunidades naturales de trabajo paralelo"""
        
        tarea_deteccion_paralelismo = Task(
            description=f"""
Analiza esta estructura educativa para detectar si tiene potencial NATURAL para trabajo paralelo/simultáneo.

ESTRUCTURA A ANALIZAR:
{contenido_estructura}

CRITERIOS DE EVALUACIÓN:
1. **TAREAS DIVISIBLES**: ¿Hay tareas que naturalmente se pueden dividir entre grupos?
2. **TRABAJO SIMULTÁNEO**: ¿Pueden varios estudiantes/grupos trabajar al mismo tiempo en diferentes aspectos?
3. **CONSTRUCCIÓN COLABORATIVA**: ¿Se está construyendo algo que permite trabajo en paralelo? (ej: maqueta, presentación, experimento)
4. **ROLES COMPLEMENTARIOS**: ¿Hay roles diferentes que pueden ejecutarse simultáneamente?
5. **ESTACIONES/ÁREAS**: ¿La actividad sugiere diferentes "lugares" o "momentos" de trabajo?

EJEMPLOS DE PARALELISMO NATURAL:
✅ "Construir maqueta del sistema solar" → Grupo A: planetas internos, Grupo B: externos, Grupo C: órbitas, Grupo D: información
✅ "Investigar animales del bosque" → Equipos por especies trabajando simultáneamente
✅ "Preparar obra de teatro" → Actores, escenografía, vestuario, música trabajando en paralelo
✅ "Experimento de plantas" → Diferentes grupos con diferentes condiciones experimentales

EJEMPLOS SIN PARALELISMO NATURAL:
❌ "Leer cuento individual y escribir resumen"
❌ "Resolver ejercicios de matemáticas" 
❌ "Examen o evaluación individual"

RESPONDE SOLO:
TIENE_POTENCIAL_PARALELO: SÍ/NO
JUSTIFICACIÓN: [1-2 líneas explicando por qué]
            """,
            agent=self.agente_coordinador_paralelismo,
            expected_output="Análisis de potencial paralelo con justificación"
        )
        
        crew_deteccion = Crew(
            agents=[self.agente_coordinador_paralelismo],
            tasks=[tarea_deteccion_paralelismo],
            process=Process.sequential,
            verbose=False  # Silencioso para no saturar
        )
        
        try:
            resultado_analisis = crew_deteccion.kickoff()
            
            # Parsear la respuesta
            resultado_str = str(resultado_analisis).lower()
            tiene_potencial = "sí" in resultado_str and "tiene_potencial_paralelo" in resultado_str
            
            logger.info(f"🔍 IA detectó paralelismo potencial: {tiene_potencial}")
            logger.info(f"📋 Análisis: {resultado_str[:200]}...")
            
            return tiene_potencial
            
        except Exception as e:
            logger.warning(f"⚠️ Error en detección IA de paralelismo: {e}")
            
            # Fallback: detección básica por palabras clave
            indicadores_basicos = ["grupo", "equipo", "construir", "crear", "diseñar", "investigar"]
            tiene_indicadores = sum(1 for ind in indicadores_basicos if ind in contenido_estructura.lower()) >= 2
            
            logger.info(f"🔄 Fallback: detección básica → {tiene_indicadores}")
            return tiene_indicadores

    def _optimizar_coordinacion_paralela(self, estructura_original, contexto_analisis: str):
        """Optimiza la estructura para incluir coordinación paralela real y adaptativa"""
        
        # Primero, obtener el ejemplo k_ de la fábrica de fracciones como referencia de paralelismo
        ejemplo_k_paralelo = self.cargador_ejemplos.ejemplos_k.get('k_sonnet7_fabrica_fracciones', 'Ejemplo no disponible')
        
        tarea_optimizacion = Task(
            description=f"""
Transforma esta actividad educativa para incluir TRABAJO PARALELO AUTÉNTICO sin forzar interdependencias artificiales.

ESTRUCTURA ORIGINAL:
{estructura_original}

CONTEXTO Y PREFERENCIAS DEL PROFESOR:
{contexto_analisis}

REFERENCIA DE PARALELISMO EXITOSO:
{ejemplo_k_paralelo[:800]}...

PRINCIPIOS DE OPTIMIZACIÓN:
1. **DETECTA DIVISIONES NATURALES**: ¿Qué aspectos de la actividad pueden separarse lógicamente?
2. **IDENTIFICA CONSTRUCCIÓN COLABORATIVA**: ¿Se está creando algo que permite trabajo simultáneo?
3. **RESPETA EL FLUJO ORIGINAL**: No cambies la esencia de la actividad, solo organizala mejor
4. **CREA CONVERGENCIA**: Los trabajos paralelos deben unirse en un resultado integrado

ESTRATEGIAS DE PARALELISMO SEGÚN TIPO DE ACTIVIDAD:

**SI ES INVESTIGACIÓN/ESTUDIO:**
- Diferentes grupos investigan aspectos complementarios
- Ejemplo: Sistema solar → Grupo A: planetas internos, Grupo B: externos, Grupo C: lunas, Grupo D: comparaciones

**SI ES CONSTRUCCIÓN/CREACIÓN:**
- Diferentes componentes se construyen simultáneamente  
- Ejemplo: Maqueta → Grupo A: estructura, Grupo B: detalles, Grupo C: información, Grupo D: presentación

**SI ES EXPERIMENTO/PRÁCTICA:**
- Diferentes variables o condiciones simultáneas
- Ejemplo: Plantas → Grupo A: con luz, Grupo B: sin luz, Grupo C: registro, Grupo D: hipótesis

**SI ES NARRATIVA/TEATRO:**
- Diferentes elementos simultáneos
- Ejemplo: Obra → Grupo A: actuación, Grupo B: escenografía, Grupo C: música, Grupo D: vestuario

ADAPTACIONES AUTOMÁTICAS POR ESTUDIANTE:
- Elena (TEA): Estación visual con instrucciones paso a paso
- Luis (TDAH): Estación kinestésica con cambios frecuentes
- Ana (altas capacidades): Rol de coordinación/supervisión entre estaciones
- Resto: Distribución equilibrada según habilidades

ESTRUCTURA DE RESPUESTA:
=== ACTIVIDAD OPTIMIZADA CON PARALELISMO NATURAL ===

**TÍTULO ACTUALIZADO:** [Título que refleje el trabajo paralelo]

**ORGANIZACIÓN TEMPORAL:**
- Preparación: [X minutos] - Organización de estaciones
- Trabajo paralelo: [X minutos] - Estaciones operando simultáneamente  
- Integración: [X minutos] - Unir resultados de todas las estaciones
- Presentación: [X minutos] - Resultado final conjunto

**ESTACIONES DE TRABAJO PARALELO:**
🔨 ESTACIÓN 1: [Descripción] - Estudiantes asignados
🎨 ESTACIÓN 2: [Descripción] - Estudiantes asignados  
📊 ESTACIÓN 3: [Descripción] - Estudiantes asignados
[🔄 ESTACIÓN 4: Si es necesaria]

**COORDINACIÓN ENTRE ESTACIONES:**
- Punto de sincronización 1: [Cuándo y cómo]
- Punto de sincronización 2: [Cuándo y cómo]
- Momento de integración: [Cómo se unen los resultados]

**PRODUCTO FINAL INTEGRADO:**
[Descripción de cómo se combinan todos los trabajos paralelos]

**SISTEMA DE ROTACIONES (si aplica):**
[Solo si es beneficioso - no forzar]
            """,
            agent=self.agente_coordinador_paralelismo,
            expected_output="Estructura educativa con paralelismo natural y organizativo"
        )
        
        crew_optimizacion = Crew(
            agents=[self.agente_coordinador_paralelismo],
            tasks=[tarea_optimizacion],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            estructura_optimizada = crew_optimizacion.kickoff()
            return estructura_optimizada
        except Exception as e:
            logger.error(f"Error optimizando paralelismo: {e}")
            print(f"⚠️ No pude optimizar el paralelismo, mantengo estructura original")
            return estructura_original

    def mostrar_actividad(self, actividad: ActividadEducativa):
        """Muestra actividad de forma clara"""
        print("\n" + "="*80)
        print(f"🎯 {actividad.titulo}")
        print("="*80)
        print(f"📖 Materia: {actividad.materia} | Tema: {actividad.tema}")
        print(f"🎭 Clima: {actividad.clima} | Modalidad: {actividad.modalidad_trabajo}")
        print(f"⏱️ Duración: {actividad.duracion}")
        
        print(f"\n📦 MATERIALES:")
        for material in actividad.materiales:
            print(f"  • {material}")
        
        print(f"\n👥 TAREAS POR ESTUDIANTE:")
        perfiles = {
            "001": "ALEX M.", "002": "MARÍA L.", "003": "ELENA R.", "004": "LUIS T.",
            "005": "ANA V.", "006": "SARA M.", "007": "EMMA K.", "008": "HUGO P."
        }
        
        for codigo, tarea in actividad.tareas_estudiantes.items():
            nombre = perfiles.get(codigo, f"Estudiante {codigo}")
            print(f"  {codigo} {nombre}: {tarea}")
        
        print(f"\n🎯 GENERADO POR: Sistema de Agentes Inteligente")
        print(f"📅 Ejemplo k_ usado: {list(actividad.metadatos.get('ejemplo_k_usado', []))}")

def main():
    """Función principal con interfaz conversacional"""
    print("🤖 Sistema de Agentes Inteligente")
    print("CrewAI + Ollama + Few-shot estratégico + Human-in-the-loop")
    print("="*70)
    
    # Inicializar sistema
    try:
        sistema = SistemaAgentesInteligente()
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        print("💡 Verifica que Ollama esté ejecutándose en 192.168.1.10:11434")
        return
    
    # Opción de entrada: prompt libre o separado
    print("\n🔄 OPCIONES DE ENTRADA:")
    print("1. 📝 Prompt libre (describe tu actividad completa)")
    print("2. 📖 Entrada tradicional (materia + tema + contexto)")
    
    opcion = input("🔢 Elige opción (1-2): ").strip()
    
    if opcion == "1":
        # PROMPT LIBRE
        print("\n💬 Describe la actividad que quieres crear:")
        print("   Ejemplo: 'Quiero una actividad de fracciones para 30 minutos, trabajo grupal,")
        print("            Elena necesita apoyo visual, usar material manipulativo'")
        prompt_profesor = input("🗣️ Tu descripción: ").strip()
        
        # Generar desde prompt libre
        print(f"\n🚀 Generando actividad desde tu descripción...")
        print("   🔍 Analizando y extrayendo variables...")
        print("   📖 Detectando materia y tema...")
        print("   🎭 Determinando clima pedagógico...")
        print("   🏗️ Estructurando actividad...")
        print("   📝 Desglosando tareas...")
        print("   👥 Repartiendo equilibradamente...")
        
        try:
            actividad = sistema.generar_actividad_desde_prompt(prompt_profesor)
            print(f"\n✨ ¡ACTIVIDAD COMPLETADA CON SISTEMA LIBRE!")
        except Exception as e:
            print(f"❌ Error con prompt libre: {e}")
            print(f"📝 Detalles: {str(e)}")
            return
            
    else:
        # ENTRADA TRADICIONAL
        materia = input("📖 Materia: ").strip()
        tema = input("📋 Tema: ").strip()
        
        print("\n💬 Describe cualquier contexto adicional:")
        print("   Ejemplo: 'solo tengo 30 minutos, Elena necesita apoyo visual, trabajo grupal'")
        contexto = input("🗣️ Contexto: ").strip()
        
        # Generar actividad tradicional
        print(f"\n🚀 Generando actividad inteligente...")
        print("   📋 Analizando contexto...")
        print("   🎭 Determinando clima pedagógico...")
        print("   🏗️ Estructurando actividad...")
        print("   📝 Desglosando tareas...")
        print("   👥 Repartiendo equilibradamente...")
        
        print("❌ Funcionalidad tradicional no disponible en versión limpia")
        print("💡 Usa opción 1 (prompt libre) que funciona con el nuevo sistema")
        return
    
    # Mostrar actividad final
    sistema.mostrar_actividad(actividad)
    actividad_final = actividad
    
    # Guardar
    try:
        filename = f"actividad_{actividad_final.id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            # Convertir a dict para JSON
            actividad_dict = {
                "id": actividad_final.id,
                "titulo": actividad_final.titulo,
                "materia": actividad_final.materia,
                "tema": actividad_final.tema,
                "clima": actividad_final.clima,
                "modalidad_trabajo": actividad_final.modalidad_trabajo,
                "contenido_completo": actividad_final.contenido_completo,
                "tareas_estudiantes": actividad_final.tareas_estudiantes,
                "materiales": actividad_final.materiales,
                "duracion": actividad_final.duracion,
                "fases": actividad_final.fases,
                "metadatos": actividad_final.metadatos,
                "timestamp": actividad_final.timestamp
            }
            json.dump(actividad_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Actividad guardada: {filename}")
        print("🌟 ¡Actividad generada con agentes inteligentes!")
        
    except Exception as e:
        print(f"❌ Error guardando actividad: {e}")
        logger.error(f"Error guardando: {e}")

if __name__ == "__main__":
    main()