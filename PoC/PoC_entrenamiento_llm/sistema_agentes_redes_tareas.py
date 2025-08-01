#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI especializado en Redes de Tareas Interdependientes
Sistema completamente nuevo que diseña actividades como redes de tareas paralelas e interconectadas
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
logger = logging.getLogger("CREWAI_REDES_TAREAS")

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


class SistemaAgentesRedesTareas:
    """Sistema principal de agentes especializado en redes de tareas interdependientes"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 generador_ideas_model: str = "qwen3:latest",
                 narrador_model: str = "qwen3:latest",
                 desglosador_model: str = "qwen3:latest", 
                 analista_dependencias_model: str = "qwen2:latest",
                 asignador_estrategico_model: str = "mistral:latest",
                 validador_flujo_model: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema de agentes especializado en redes de tareas
        """
        self.ollama_host = ollama_host
        self.generador_ideas_model = generador_ideas_model
        self.narrador_model = narrador_model
        self.desglosador_model = desglosador_model
        self.analista_dependencias_model = analista_dependencias_model
        self.asignador_estrategico_model = asignador_estrategico_model
        self.validador_flujo_model = validador_flujo_model
        self.perfiles_path = perfiles_path
        
        # Cargar TODOS los ejemplos k_ para few-shot learning
        self._cargar_todos_ejemplos_k()
        
        # Crear LLMs específicos para cada agente
        logger.info("🔧 Configurando LLMs específicos para cada agente...")
        
        try:
            # Configurar LiteLLM correctamente para Ollama
            import litellm
            
            # Configuraciones específicas para Ollama local
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            # Mapear todos los modelos para LiteLLM CON PREFIJO CORRECTO
            modelos_unicos = set([self.generador_ideas_model, self.narrador_model, self.desglosador_model, self.analista_dependencias_model, 
                                 self.asignador_estrategico_model, self.validador_flujo_model])
            for modelo in modelos_unicos:
                # IMPORTANTE: Usar prefijo ollama/ para LiteLLM
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Configurar variables específicas para LiteLLM + Ollama
            os.environ["OLLAMA_API_BASE"] = f"http://{ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{ollama_host}:11434"
            
            # Crear LLMs específicos para cada agente CON PREFIJO CORRECTO
            self.generador_ideas_llm = Ollama(
                model=f"ollama/{self.generador_ideas_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.narrador_llm = Ollama(
                model=f"ollama/{self.narrador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.desglosador_llm = Ollama(
                model=f"ollama/{self.desglosador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.analista_llm = Ollama(
                model=f"ollama/{self.analista_dependencias_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.asignador_llm = Ollama(
                model=f"ollama/{self.asignador_estrategico_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.validador_llm = Ollama(
                model=f"ollama/{self.validador_flujo_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            logger.info(f"✅ LLMs configurados exitosamente con prefijos ollama/")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            logger.error("🚨 No se pudieron configurar LLMs para CrewAI.")
            raise e
        
        # Cargar perfiles directamente para usar en las descripciones de tareas
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes especializados en redes de tareas
        self._crear_agentes_redes_tareas()
        
        logger.info(f"✅ Sistema de redes de tareas inicializado con modelos:")
        logger.info(f"   💡 Generador Ideas: {self.generador_ideas_model}")
        logger.info(f"   📖 Narrador: {self.narrador_model}")
        logger.info(f"   🧩 Desglosador: {self.desglosador_model}")
        logger.info(f"   🔗 Analista Dependencias: {self.analista_dependencias_model}")  
        logger.info(f"   🎯 Asignador Estratégico: {self.asignador_estrategico_model}")
        logger.info(f"   ✅ Validador Flujo: {self.validador_flujo_model}")
    
    def _cargar_todos_ejemplos_k(self):
        """Cargar TODOS los ejemplos de actividades k_ válidos para few-shot learning"""
        self.ejemplos_k = {}
        
        # Buscar todos los archivos k_ disponibles
        script_dir = os.path.dirname(os.path.abspath(__file__))
        actividades_dir = os.path.join(script_dir, "actividades_generadas")
        
        if not os.path.exists(actividades_dir):
            logger.warning(f"⚠️ Directorio no existe: {actividades_dir}")
            return
        
        # Obtener todos los archivos k_
        archivos_k = []
        for archivo in os.listdir(actividades_dir):
            if archivo.startswith("k_") and archivo.endswith(".txt"):
                archivos_k.append(os.path.join(actividades_dir, archivo))
        
        logger.info(f"🔍 Encontrados {len(archivos_k)} archivos k_ potenciales")
        
        for archivo_path in archivos_k:
            try:
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    contenido = f.read().strip()
                    
                    # Filtrar archivos vacíos o muy cortos (menos de 500 caracteres)
                    if len(contenido) < 500:
                        logger.warning(f"⚠️ Archivo muy corto, omitiendo: {os.path.basename(archivo_path)}")
                        continue
                    
                    # Filtrar archivos que parecen incompletos o erróneos
                    if "error" in contenido.lower()[:100] or "test" in contenido.lower()[:100]:
                        logger.warning(f"⚠️ Archivo parece de prueba/error, omitiendo: {os.path.basename(archivo_path)}")
                        continue
                    
                    nombre_ejemplo = os.path.basename(archivo_path).replace('.txt', '')
                    self.ejemplos_k[nombre_ejemplo] = contenido
                    logger.info(f"📖 Cargado ejemplo válido: {nombre_ejemplo} ({len(contenido)} chars)")
                    
            except Exception as e:
                logger.error(f"❌ Error cargando {archivo_path}: {e}")
        
        logger.info(f"✅ Cargados {len(self.ejemplos_k)} ejemplos k_ válidos para few-shot learning")
        
        # Log de ejemplos cargados para debug
        for nombre in self.ejemplos_k.keys():
            logger.info(f"   📚 {nombre}")
    
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
    
    def _crear_agentes_redes_tareas(self):
        """Crea agentes especializados en diseño de redes de tareas interdependientes"""
        
        # AGENTE 1: GENERADOR DE IDEAS CREATIVAS (sin sesgo de ejemplos)
        self.agente_generador_ideas = Agent(
            role="Generador Creativo de Ideas Educativas",
            goal="Generar múltiples ideas completamente originales y creativas para cualquier materia educativa, sin limitarse a patrones previos",
            backstory="Eres pura creatividad educativa sin restricciones. Tu trabajo es generar 5-7 ideas completamente diferentes y originales para cualquier tema educativo. No te limites a patrones previos como 'supermercados' o 'tiendas' - usa tu imaginación ilimitada para crear conceptos únicos, narrativas frescas, y contextos innovadores. Cada idea debe ser distinta y emocionante para niños de 9-10 años. Respondes siempre en español.",
            tools=[],
            llm=self.generador_ideas_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: NARRADOR DE EXPERIENCIAS (estructura la mejor idea)
        self.agente_narrador = Agent(
            role="Narrador de Experiencias Educativas Auténticas",
            goal="Crear narrativas educativas envolventes que generen contextos auténticos donde las tareas específicas emergen naturalmente",
            backstory="Eres un maestro storyteller que diseña experiencias educativas como historias vividas. Tu especialidad es crear contextos donde los estudiantes NECESITAN hacer cosas específicas para resolver problemas reales. No inventas tareas artificiales, sino que diseñas situaciones donde las tareas educativas son la solución natural al problema planteado. Respondes siempre en español.",
            tools=[],
            llm=self.narrador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: DESGLOSADOR DE TAREAS ESPECÍFICAS
        self.agente_desglosador = Agent(
            role="Desglosador de Tareas Específicas y Concretas",
            goal="Identificar todas las tareas específicas necesarias para la experiencia, definiendo exactamente qué hace cada persona y qué produce",
            backstory="Eres un ingeniero de procesos educativos que descompone experiencias complejas en tareas específicas y realizables. Tu trabajo es identificar EXACTAMENTE qué tiene que hacer cada persona, qué materiales necesita, qué produce como resultado, y en qué momento lo hace. No creas roles vagos sino tareas concretas y medibles. Respondes siempre en español.",
            tools=[],
            llm=self.desglosador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: ANALISTA DE DEPENDENCIAS E INTERCONEXIONES
        self.agente_analista_dependencias = Agent(
            role="Analista de Dependencias e Interconexiones entre Tareas",
            goal="Mapear las interdependencias reales entre tareas para crear una red de trabajo colaborativo auténtico",
            backstory="Eres un especialista en sistemas que analiza cómo las tareas se conectan e interactúan entre sí. Tu trabajo es identificar qué tarea necesita el resultado de cuál otra, cuáles pueden ejecutarse en paralelo, y dónde están los puntos críticos de interdependencia. Creas redes de tareas, no secuencias lineales. Respondes siempre en español.",
            tools=[],
            llm=self.analista_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 5: ASIGNADOR ESTRATÉGICO (perfil-tarea matching)
        self.agente_asignador_estrategico = Agent(
            role="Asignador Estratégico de Tareas por Perfil de Estudiante",
            goal="Emparejar cada tarea específica con el estudiante que mejor pueda ejecutarla considerando sus fortalezas, necesidades y zona de desarrollo próximo",
            backstory="Eres un psicopedagogo especializado en matching perfecto entre estudiantes y tareas. Conoces a cada estudiante específico del aula y sabes exactamente qué tipo de tarea le permitirá brillar mientras aprende. Tu trabajo es asegurar que cada tarea tenga el ejecutor ideal. Respondes siempre en español.",
            tools=[],
            llm=self.asignador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 5: VALIDADOR DE FLUJO OPERATIVO
        self.agente_validador_flujo = Agent(
            role="Validador de Flujo Operativo y Viabilidad Práctica",
            goal="Verificar que el sistema de tareas funcione operativamente en un aula real con estudiantes reales",
            backstory="Eres un maestro experimentado que sabe exactamente qué funciona y qué no en un aula real. Tu trabajo es revisar todo el sistema de tareas y verificar que sea ejecutable, que el profesor sepa qué hacer en cada momento, que los estudiantes estén realmente ocupados con tareas significativas, y que la actividad fluya naturalmente. Respondes siempre en español.",
            tools=[],
            llm=self.validador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes de redes de tareas creados exitosamente")
    
    def _generar_contexto_ejemplos_k(self, materia: str, tema: str = None) -> str:
        """Genera contexto de ejemplos k_ para few-shot learning"""
        contexto_ejemplos = "\n=== EJEMPLOS DE ACTIVIDADES EXITOSAS PARA ESTUDIAR ===\n"
        
        # Incluir TODOS los ejemplos k_ cargados
        for nombre, contenido in self.ejemplos_k.items():
            # Limitar cada ejemplo a primeros 2000 caracteres para no exceder límites
            contexto_ejemplos += f"\n--- EJEMPLO EXITOSO: {nombre.upper().replace('_', ' ')} ---\n"
            contexto_ejemplos += contenido[:2000]
            if len(contenido) > 2000:
                contexto_ejemplos += "...\n"
            contexto_ejemplos += "\n"
        
        return contexto_ejemplos
    
    def generar_actividad_red_tareas(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera una actividad como red de tareas interdependientes"""
        
        logger.info(f"🕸️ Generando actividad de red de tareas para {materia}")
        
        try:
            # Obtener contexto de ejemplos k_
            contexto_ejemplos = self._generar_contexto_ejemplos_k(materia, tema)
            
            #TAREA 0: GENERADOR DE IDEAS - Crear ideas originales
            tarea_generador_ideas = Task(
                description=f"""Genera 5-7 ideas completamente originales y creativas para una actividad educativa en {materia} {f'sobre {tema}' if tema else ''}. No te limites a patrones previos como 'supermercados' o 'tiendas' - usa tu imaginación ilimitada para crear conceptos únicos, narrativas frescas, y contextos innovadores. Cada idea debe ser distinta y emocionante para niños de 9-10 años."""
                agent=self.agente_generador_ideas,
                expected_output="Ideas originales para desarrollar actividades relacionadas con la materia y el tema específico"
            )

            # TAREA 1: NARRADOR - Crear experiencia auténtica
            tarea_narracion = Task(
                description=f"""Estudia los ejemplos de actividades exitosas y crea una experiencia educativa auténtica para {materia} {f'sobre {tema}' if tema else ''}.

{contexto_ejemplos}

CARACTERÍSTICAS CLAVE que debes emular de estos ejemplos:
✨ CONTEXTO AUTÉNTICO: Situación real donde las tareas matemáticas/educativas son necesarias para resolver el problema
🎭 NARRATIVA ENVOLVENTE: Historia que motiva desde el inicio y se mantiene durante toda la actividad  
🔧 TAREAS ESPECÍFICAS: No roles vagos sino tareas concretas que producen resultados específicos
🌐 INTERDEPENDENCIA REAL: Unos necesitan los resultados de otros para avanzar
⚡ FLEXIBILIDAD NATURAL: Los estudiantes pueden elegir cómo abordar su tarea específica

GRUPO OBJETIVO: 8 estudiantes de 4º Primaria (9-10 años)
- 001 ALEX M.: reflexivo, visual, CI 102, apoyo bajo
- 002 MARÍA L.: reflexivo, auditivo, apoyo medio
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118, apoyo alto  
- 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102, apoyo alto
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141, apoyo bajo
- 006 SARA M.: equilibrado, auditivo, CI 115, apoyo medio
- 007 EMMA K.: reflexivo, visual, CI 132, apoyo medio
- 008 HUGO P.: equilibrado, visual, CI 114, apoyo bajo

RESTRICCIONES DE REALIDAD PRÁCTICA (MUY IMPORTANTE):
🏫 ESPACIO: Solo aula estándar (30m²), no espacios externos fantásticos
📚 MATERIALES: Solo lo disponible en cualquier aula (papel, lápices, objetos básicos, NO tecnología compleja)
⏰ TIEMPO: Actividad de 45-60 minutos máximo, tareas de 10-15 minutos para esta edad
👶 EDAD REAL: Niños de 9-10 años, no adolescentes - conceptos apropiados para su desarrollo cognitivo
👨‍🏫 PROFESOR: Un solo adulto gestionando 8 niños diversos, debe ser viable operativamente

CREA UNA EXPERIENCIA que sea REALISTA y EJECUTABLE:

RESPONDE EN ESTE FORMATO:
=== EXPERIENCIA EDUCATIVA AUTÉNTICA ===
NOMBRE: [Título que capture la esencia de la experiencia]
CONTEXTO PROBLEMÁTICO: [Situación REAL que requiere solución en aula]
NARRATIVA INICIAL: [Cómo se presenta el desafío - apropiado para 9-10 años]
OBJETIVO COLECTIVO: [Qué deben lograr juntos - alcanzable en 45-60 min]
COMPETENCIAS INTEGRADAS: [Qué aprenden - apropiado para 4º Primaria]
PRODUCTO FINAL: [Resultado tangible - viable en aula]

IMPORTANTE: La experiencia debe ser EJECUTABLE con materiales simples en aula estándar.""",
                agent=self.agente_narrador,
                expected_output="Experiencia educativa auténtica con contexto problemático real"
            )
            
            # TAREA 2: DESGLOSADOR - Identificar tareas específicas
            tarea_desglose = Task(
                description=f"""Desglosa la experiencia educativa en TAREAS ESPECÍFICAS Y CONCRETAS que deben ejecutarse.

RESTRICCIONES CRÍTICAS DE REALIDAD (CUMPLE OBLIGATORIAMENTE):
🏫 AULA ESTÁNDAR: Solo 30m², mesas normales, sin espacios especiales
📚 MATERIALES BÁSICOS: Solo papel, lápices, objetos del aula, NO tecnología
⏰ 4º PRIMARIA REAL: Niños 9-10 años, atención máxima 15 minutos por tarea
👶 APROPIADO PARA EDAD: Conceptos simples, instrucciones claras
🎯 EJECUTABLE: Un profesor puede supervisar 8 niños haciendo esto

Para cada tarea específica que identifiques, define:

=== INVENTARIO DE TAREAS ESPECÍFICAS ===

TAREA [número]: [Nombre específico de la tarea]
- QUÉ SE HACE EXACTAMENTE: [Acción concreta que un niño de 9 años puede hacer]
- MATERIALES NECESARIOS: [Solo cosas disponibles en aula normal]
- TIEMPO ESTIMADO: [Máximo 15 minutos para esta edad]
- RESULTADO/PRODUCTO: [Qué se genera - tangible y simple]
- HABILIDADES REQUERIDAS: [Apropiadas para 4º Primaria]
- DIFICULTAD: [Realista para 9-10 años: básico/medio]

EJEMPLO DE ESPECIFICIDAD APROPIADA:
❌ MAL: "Diseñar base lunar con software" (muy complejo, no hay tecnología)
✅ BIEN: "Contar cuántos lápices necesitamos si cada niño usa 3 lápices" (simple, factible)

❌ MAL: "Calcular presupuesto de 60€ por estudiante" (dinero demasiado alto)
✅ BIEN: "Contar cuántas hojas necesitamos si cada grupo usa 5 hojas" (realista)

IDENTIFICA 6-8 TAREAS ESPECÍFICAS máximo (no más, para edad apropiada).

IMPORTANTE: 
- Cada tarea debe poder explicarse en 20 segundos a un niño de 9 años
- Solo materiales que cualquier aula tiene
- Tiempos realistas para su capacidad de atención
- Un adulto debe poder supervisar las 8 tareas simultáneamente""",
                agent=self.agente_desglosador,
                context=[tarea_narracion],
                expected_output="Lista detallada de tareas específicas y concretas con todos los detalles operativos"
            )
            
            # TAREA 3: ANALISTA - Mapear interdependencias
            tarea_analisis_dependencias = Task(
                description=f"""Analiza las tareas específicas y mapea sus INTERDEPENDENCIAS REALES para crear una red de trabajo colaborativo.

Para cada tarea del inventario, analiza:

=== MAPA DE INTERDEPENDENCIAS ===

TAREA [nombre]: 
- REQUIERE COMO INPUT: [Qué resultados de otras tareas necesita para empezar]
- PRODUCE COMO OUTPUT: [Qué genera que otras tareas necesitan]
- PUEDE EJECUTARSE EN PARALELO CON: [Qué otras tareas pueden hacerse simultáneamente]
- PUNTOS DE SINCRONIZACIÓN: [Momentos donde debe coordinarse con otros]
- DEPENDENCIAS CRÍTICAS: [Sin qué tareas específicas no puede funcionar]

EJEMPLO DE INTERDEPENDENCIA REAL:
"TAREA Cajero-Tienda1" REQUIERE que "TAREA Supervisor-Preparar-Productos" esté completa
"TAREA Cliente-Comprar" REQUIERE que "TAREA Supervisor-Dictar-Lista" le haya dado su lista específica
"TAREA Verificar-Dinero-Final" REQUIERE que TODAS las compras estén completas

=== RED DE TRABAJO COLABORATIVO ===
- FASE 1 (Preparación): [Qué tareas deben completarse primero]
- FASE 2 (Ejecución paralela): [Qué tareas pueden hacerse simultáneamente]  
- FASE 3 (Convergencia): [Qué tareas requieren resultados de varias anteriores]
- PUNTOS DE CONTROL: [Momentos donde el grupo debe sincronizarse]

IMPORTANTE: Busca crear INTERDEPENDENCIA REAL, no artificial. Los estudiantes deben NECESITAR realmente el trabajo de otros.""",
                agent=self.agente_analista_dependencias,
                context=[tarea_desglose],
                expected_output="Mapa detallado de interdependencias con red de trabajo colaborativo"
            )
            
            # TAREA 4: ASIGNADOR - Emparejar estudiantes con tareas
            tarea_asignacion_estrategica = Task(
                description=f"""Asigna cada tarea específica al estudiante que mejor pueda ejecutarla, considerando fortalezas, necesidades y ZDP.

ESTUDIANTES DISPONIBLES (USAR NOMBRES ESPECÍFICOS):
- 001 ALEX M.: reflexivo, visual, CI 102, apoyo bajo
- 002 MARÍA L.: reflexivo, auditivo, apoyo medio
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118, apoyo alto
- 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102, apoyo alto
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141, apoyo bajo
- 006 SARA M.: equilibrado, auditivo, CI 115, apoyo medio
- 007 EMMA K.: reflexivo, visual, CI 132, apoyo medio
- 008 HUGO P.: equilibrado, visual, CI 114, apoyo bajo

DIRECTRICES DE ASIGNACIÓN REALISTA:
✅ Elena (TEA): Tareas visuales, estructuradas, sin presión temporal
✅ Luis (TDAH): Tareas kinestésicas, movimiento, retroalimentación frecuente
✅ Ana (Altas capacidades): Tareas complejas, mentoría a otros
✅ Resto: Tareas acordes a su canal preferido y temperamento

Para cada asignación, justifica:

=== ASIGNACIÓN ESTRATÉGICA DE TAREAS ===

**001 ALEX M.**: TAREA ASIGNADA [nombre específico]
- POR QUÉ ESTA TAREA: [Aprovecha su canal visual y temperamento reflexivo]
- ADAPTACIONES NECESARIAS: [Apoyo bajo específico]
- NIVEL DE DESAFÍO: [Apropiado para CI 102]
- PRODUCTOS QUE GENERA: [Qué entrega específicamente]
- INTERACCIONES CLAVE: [Con quién debe coordinarse y cómo]

**002 MARÍA L.**: TAREA ASIGNADA [nombre específico]
- POR QUÉ ESTA TAREA: [Aprovecha su canal auditivo y temperamento reflexivo]
- ADAPTACIONES NECESARIAS: [Apoyo medio específico]
- PRODUCTOS QUE GENERA: [Qué entrega específicamente]  
- INTERACCIONES CLAVE: [Con quién debe coordinarse y cómo]

**003 ELENA R.**: TAREA ASIGNADA [nombre específico]
- POR QUÉ ESTA TAREA: [Aprovecha su canal visual, considera TEA nivel 1]
- ADAPTACIONES TEA: [Estructura visual, pausas, regulación específica]
- PRODUCTOS QUE GENERA: [Qué entrega específicamente]
- INTERACCIONES CLAVE: [Con quién debe coordinarse - limitadas y claras]

**004 LUIS T.**: TAREA ASIGNADA [nombre específico]
- POR QUÉ ESTA TAREA: [Aprovecha su canal kinestésico y temperamento impulsivo]
- ADAPTACIONES TDAH: [Movimiento, retroalimentación frecuente, tareas dinámicas]
- PRODUCTOS QUE GENERA: [Qué entrega específicamente]
- INTERACCIONES CLAVE: [Con quién debe coordinarse y cómo]

**005 ANA V.**: TAREA ASIGNADA [nombre específico]
- POR QUÉ ESTA TAREA: [Aprovecha altas capacidades y canal auditivo]
- DESAFÍOS ADICIONALES: [Complejidad extra, liderazgo, mentoría]
- PRODUCTOS QUE GENERA: [Qué entrega específicamente]
- INTERACCIONES CLAVE: [Con quién debe coordinarse y cómo]

**006 SARA M.**: TAREA ASIGNADA [nombre específico]
**007 EMMA K.**: TAREA ASIGNADA [nombre específico]  
**008 HUGO P.**: TAREA ASIGNADA [nombre específico]

VERIFICACIÓN DE COBERTURA:
- ¿Todos los 8 estudiantes tienen tarea específica? [Sí/No]
- ¿Todas las tareas tienen ejecutor asignado? [Sí/No]
- ¿Las interdependencias funcionan con esta asignación? [Sí/No]

IMPORTANTE: USA LOS NOMBRES ESPECÍFICOS, no [NOMBRE]. Cada estudiante UNA TAREA PRINCIPAL.""",
                agent=self.agente_asignador_estrategico,
                context=[tarea_analisis_dependencias],
                expected_output="Asignación específica de cada tarea a cada estudiante con justificación pedagógica"
            )
            
            # TAREA 5: VALIDADOR - Verificar viabilidad operativa
            tarea_validacion_flujo = Task(
                description=f"""Valida que todo el sistema de tareas sea operativamente viable en un aula real de 4º Primaria.

CRITERIOS DE VALIDACIÓN OPERATIVA (SÉ MUY CRÍTICO):

✅ CLARIDAD DOCENTE:
- ¿El profesor sabe exactamente qué hacer minuto a minuto?
- ¿Las instrucciones son claras para preparar en aula estándar?
- ¿Están definidos los momentos exactos de intervención?

✅ VIABILIDAD PRÁCTICA REAL:
- ¿Los materiales existen en aula normal? (papel, lápices, objetos básicos)
- ¿El espacio de 30m² es suficiente para 8 niños?
- ¿Los tiempos de 10-15 min son realistas para niños de 9-10 años?
- ¿Un solo profesor puede supervisar 8 tareas simultáneas?

✅ OCUPACIÓN ESTUDIANTIL REAL:
- ¿Los 8 estudiantes están ocupados TODO el tiempo?
- ¿Hay plan específico para quien termine antes?
- ¿Las tareas son apropiadas para desarrollo cognitivo de 9-10 años?
- ¿Elena (TEA) y Luis (TDAH) pueden realmente ejecutar sus tareas?

✅ INTERDEPENDENCIA FUNCIONAL:
- ¿Las conexiones son REALMENTE necesarias (no artificiales)?
- ¿Si falta una tarea, el sistema colapsa genuinamente?
- ¿Los puntos de sincronización son claros y manejables?

✅ APRENDIZAJE AUTÉNTICO:
- ¿Los objetivos curriculares emergen naturalmente?
- ¿La evaluación es observable y medible?
- ¿Los niños aprenden haciendo, no simulando?

PARA CADA CRITERIO, sé BRUTALMENTE HONESTO:
- EVALUACIÓN: [Cumple/No cumple/Parcialmente]
- EVIDENCIA ESPECÍFICA: [Detalles concretos de por qué sí o no]
- MEJORAS OBLIGATORIAS: [Cambios específicos que DEBES hacer]

SI ENCUENTRAS PROBLEMAS GRAVES:
🚨 REDISEÑA aspectos problemáticos y propón alternativas específicas
🚨 NO te conformes con "parcialmente" - arréglalo hasta que funcione
🚨 Piensa en un aula REAL con 8 niños reales y 1 profesor real

PUNTUACIÓN FINAL: __/10 (comparado con ejemplos k_ exitosos)

ENTREGA FINAL OBLIGATORIA:
- Si 8+/10: Sistema validado con evidencia específica
- Si menos: REDISEÑA los aspectos problemáticos hasta alcanzar 8+/10

IMPORTANTE: No entregues nada que no funcione al 100% en aula real.""",
                agent=self.agente_validador_flujo,
                context=[tarea_asignacion_estrategica],
                expected_output="Validación completa de viabilidad operativa con mejoras específicas si son necesarias"
            )

            # Crear y ejecutar crew
            crew = Crew(
                agents=[self.agente_narrador, self.agente_desglosador, self.agente_analista_dependencias, 
                       self.agente_asignador_estrategico, self.agente_validador_flujo],
                tasks=[tarea_generador_ideas, tarea_narracion, tarea_desglose, tarea_analisis_dependencias, 
                      tarea_asignacion_estrategica, tarea_validacion_flujo],
                process=Process.sequential,
                verbose=True
            )
            
            logger.info("🚀 Ejecutando workflow de redes de tareas...")
            resultado = crew.kickoff()
            
            # Procesar resultados
            contenido_completo = self._procesar_resultados(resultado)
            
            return ActividadEducativa(
                id=f"redtareas_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Red de Tareas - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_red_tareas",
                adaptaciones=["tareas_especificas", "interdependencias_reales", "asignacion_estrategica"],
                metadatos={
                    "total_estudiantes": 8,
                    "flujo_pedagogico": ["narracion", "desglose", "analisis_dependencias", "asignacion_estrategica", "validacion_flujo"],
                    "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                    "total_ejemplos_k": len(self.ejemplos_k),
                    "modelos_usados": {
                        "narrador": self.narrador_model,
                        "desglosador": self.desglosador_model,
                        "analista_dependencias": self.analista_dependencias_model,
                        "asignador_estrategico": self.asignador_estrategico_model,
                        "validador_flujo": self.validador_flujo_model
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad de red de tareas: {e}")
            # Retornar actividad básica
            return ActividadEducativa(
                id=f"error_redtareas_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Error - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error generando actividad de red de tareas: {e}",
                estudiantes_objetivo=[],
                tipo="error_red_tareas",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _procesar_resultados(self, resultado) -> str:
        """Procesa y estructura los resultados del crew"""
        contenido = ""
        
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido += "=== EXPERIENCIA EDUCATIVA AUTÉNTICA ===\n"
                contenido += str(resultado.tasks_output[0]) + "\n\n"
                
                contenido += "=== INVENTARIO DE TAREAS ESPECÍFICAS ===\n"
                contenido += str(resultado.tasks_output[1]) + "\n\n"
                
                contenido += "=== MAPA DE INTERDEPENDENCIAS ===\n"
                contenido += str(resultado.tasks_output[2]) + "\n\n"
                
                contenido += "=== ASIGNACIÓN ESTRATÉGICA DE TAREAS ===\n"
                contenido += str(resultado.tasks_output[3]) + "\n\n"
                
                contenido += "=== VALIDACIÓN DE VIABILIDAD OPERATIVA ===\n"
                contenido += str(resultado.tasks_output[4]) + "\n\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados individuales: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_redtareas") -> str:
        """Guarda una actividad en un archivo"""
        
        # Asegurar que se guarde en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA RED DE TAREAS CrewAI + Ollama\n")
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
            f.write("METADATOS DEL SISTEMA RED DE TAREAS:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad red de tareas guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema de redes de tareas"""
    
    print("="*70)
    print("🕸️ SISTEMA DE AGENTES CREWAI RED DE TAREAS PARA EDUCACIÓN")
    print("="*70)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        NARRADOR_MODEL = "qwen3:latest"
        DESGLOSADOR_MODEL = "qwen3:latest"
        ANALISTA_MODEL = "qwen2:latest"
        ASIGNADOR_MODEL = "mistral:latest"
        VALIDADOR_MODEL = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        # Inicializar sistema
        print(f"\n🔧 Inicializando sistema de redes de tareas:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Modelos especializados por agente:")
        print(f"     📖 Narrador: {NARRADOR_MODEL}")
        print(f"     🧩 Desglosador: {DESGLOSADOR_MODEL}")
        print(f"     🔗 Analista Dependencias: {ANALISTA_MODEL}")
        print(f"     🎯 Asignador Estratégico: {ASIGNADOR_MODEL}")
        print(f"     ✅ Validador Flujo: {VALIDADOR_MODEL}")
        
        sistema = SistemaAgentesRedesTareas(
            ollama_host=OLLAMA_HOST,
            narrador_model=NARRADOR_MODEL,
            desglosador_model=DESGLOSADOR_MODEL,
            analista_dependencias_model=ANALISTA_MODEL,
            asignador_estrategico_model=ASIGNADOR_MODEL,
            validador_flujo_model=VALIDADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema de redes de tareas inicializado correctamente!")
        print(f"📖 Ejemplos k_ cargados: {len(sistema.ejemplos_k)}")
        for nombre in sistema.ejemplos_k.keys():
            print(f"   📚 {nombre}")
        
        # Menú
        while True:
            print("\n" + "="*50)
            print("🕸️ GENERACIÓN RED DE TAREAS")
            print("1. 🎯 Generar actividad como red de tareas interdependientes")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                print(f"\n⏳ Generando red de tareas para {materia}...")
                print("   (Esto puede tomar varios minutos con todos los ejemplos k_)")
                
                actividad = sistema.generar_actividad_red_tareas(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad red de tareas generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🕸️ Sistema: Red de tareas interdependientes")
                print(f"   📖 Ejemplos k_ utilizados: {len(actividad.metadatos.get('ejemplos_k_usados', []))}")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema de redes de tareas: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")
        print("   4. Los archivos k_ estén en actividades_generadas/")


if __name__ == "__main__":
    main()