#!/usr/bin/env python3
"""
Agentes y Tareas del Sistema de Agentes Inteligente
- Definición de todos los agentes CrewAI
- Templates de tareas específicas
- Configuración de LLMs
"""

import logging
from typing import Dict, Any
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama

logger = logging.getLogger("AgentesInteligente")

class AgentesCrewAI:
    """Gestor de agentes CrewAI especializados"""
    
    def __init__(self, ollama_host: str = "192.168.1.10"):
        self.ollama_host = ollama_host
        self._crear_llms_especificos()
        self._crear_agentes()
        logger.info("✅ Agentes CrewAI inicializados")
    
    def _crear_llms_especificos(self):
        """Crea LLMs específicos para cada agente usando patrón exitoso"""
        try:
            import litellm
            
            # Usar el patrón EXACTO que funciona
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

class TemplatesTareas:
    """Templates de tareas especializadas para cada agente"""
    
    @staticmethod
    def crear_tarea_deteccion_contexto(prompt_profesor: str, agente_detector) -> Task:
        """Crea tarea para detectar contexto multidimensional"""
        
        return Task(
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
        "productos": {{"tipo": "concreto/abstracto", "ejemplos": ["producto1", "producto2"]}},
        "adaptaciones": {{"necesarias": ["tipo1", "tipo2"], "opcionales": ["tipo3"]}}
    }},
    "opciones_dinamicas": [
        "¿Pregunta específica 1?",
        "¿Pregunta específica 2?",
        "¿Pregunta específica 3?"
    ],
    "recomendacion_ia": "Tu recomendación específica basada en el análisis"
}}
```
            """,
            agent=agente_detector,
            expected_output="Análisis JSON multidimensional con opciones dinámicas"
        )
    
    @staticmethod
    def crear_tarea_clima(clima_context: str, agente_clima) -> Task:
        """Crea tarea para definir clima pedagógico"""
        
        return Task(
            description=f"""
Analiza el contexto y propón 3 opciones de CLIMA pedagógico diferentes:

CONTEXTO APROBADO: {clima_context}

Las opciones deben ser:
1. **SIMPLE**: Actividad directa, sin narrativa compleja
2. **JUEGO**: Con elementos lúdicos y competitivos
3. **NARRATIVA**: Con historia envolvente y personajes
4. **COMPLEJO**: Multi-fase con varios componentes

Para CADA opción, incluye:
- Justificación de por qué funcionaría
- Duración estimada
- Tipo de materiales necesarios
- Nivel de engagement esperado

RECOMENDACIÓN FINAL: Indica cuál recomiendas y por qué.
            """,
            agent=agente_clima,
            expected_output="3 opciones de clima con justificación y recomendación"
        )
    
    @staticmethod
    def crear_tarea_estructura(clima_aprobado: str, contexto_detectado: Dict, ejemplo_k: str, agente_estructurador) -> Task:
        """Crea tarea para estructurar la actividad"""
        
        return Task(
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
            agent=agente_estructurador,
            expected_output="Estructura detallada de la actividad"
        )
    
    @staticmethod
    def crear_tarea_desglose_tareas(estructura_completa: str, agente_tareas) -> Task:
        """Crea tarea para desglosar en tareas específicas"""
        
        return Task(
            description=f"""
ESTRUCTURA COMPLETA DE LA ACTIVIDAD:
{estructura_completa}

DESGLOSA en tareas específicas y concretas:

REQUISITOS:
- Cada tarea debe ser ESPECÍFICA (no genérica)
- Incluir verbo de acción concreto
- Especificar materiales exactos necesarios
- Definir resultado esperado medible
- Duración estimada realista

EVITA roles abstractos como "coordinador" o "investigador general".
PREFIERE tareas concretas como "medir 3 objetos con regla" o "recortar 5 figuras geométricas".

FORMATO:
TAREA 1: [Descripción específica] - Materiales: [lista] - Resultado: [medible] - Tiempo: [minutos]
TAREA 2: [Descripción específica] - Materiales: [lista] - Resultado: [medible] - Tiempo: [minutos]
...
            """,
            agent=agente_tareas,
            expected_output="Lista detallada de tareas específicas y concretas"
        )
    
    @staticmethod
    def crear_tarea_asignacion_estudiantes(tareas_desglosadas: str, agente_repartidor) -> Task:
        """Crea tarea para asignar tareas a estudiantes específicos"""
        
        return Task(
            description=f"""  
TAREAS DESGLOSADAS:
{tareas_desglosadas}

PERFILES DE ESTUDIANTES (4º PRIMARIA):
- 001 ALEX M. (ninguno, visual, apoyo bajo, reflexivo)
- 002 MARÍA L. (ninguno, auditivo, apoyo medio, reflexivo)  
- 003 ELENA R. (TEA_nivel_1, visual, apoyo alto, reflexivo)
- 004 LUIS T. (TDAH_combinado, kinestésico, apoyo alto, impulsivo)
- 005 ANA V. (altas_capacidades, auditivo, apoyo bajo, equilibrado)
- 006 SARA M. (ninguno, auditivo, apoyo medio, reflexivo)
- 007 EMMA K. (ninguno, visual, apoyo medio, equilibrado)
- 008 HUGO P. (ninguno, visual, apoyo bajo, reflexivo)

ASIGNA cada tarea considerando:
- Canal de aprendizaje preferido (visual/auditivo/kinestésico)
- Nivel de apoyo necesario
- Temperamento (reflexivo/impulsivo/equilibrado)
- Diagnósticos específicos (TEA, TDAH, altas capacidades)

ADAPTACIONES ESPECÍFICAS:
- Elena (TEA): Instrucciones visuales claras, pasos estructurados
- Luis (TDAH): Tareas kinestésicas, cambios frecuentes
- Ana (altas capacidades): Desafíos adicionales, rol de ayuda

FORMATO:
001 ALEX M.: [Tarea específica asignada con justificación]
002 MARÍA L.: [Tarea específica asignada con justificación]
...
            """,
            agent=agente_repartidor,
            expected_output="Asignación específica de tareas por estudiante con adaptaciones"
        )