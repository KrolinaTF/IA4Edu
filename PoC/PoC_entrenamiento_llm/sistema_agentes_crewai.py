#!/usr/bin/env python3
"""
Sistema de Agentes con CrewAI y Ollama para Generación de Actividades Educativas
Un sistema multi-agente especializado en la creación de actividades educativas adaptadas
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
logger = logging.getLogger("CREWAI_EDUCATION_SYSTEM")

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


class DirectOllamaLLM(LLM):
    """LLM completamente personalizado que bypassa LiteLLM"""
    
    def __init__(self, ollama_host: str = "192.168.1.10", ollama_model: str = "qwen3:latest"):
        super().__init__()
        
        # Separar host y puerto si viene junto
        if ":" in ollama_host:
            host_only = ollama_host.split(":")[0]
        else:
            host_only = ollama_host
            
        # Crear generador de Ollama
        self.ollama_generator = OllamaAPIEducationGenerator(
            host=host_only, 
            model_name=ollama_model
        )
        self.model_name = ollama_model
        self.host = host_only
    
    @property
    def _llm_type(self) -> str:
        return "direct_ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Llamada principal al LLM - usa nuestro OllamaAPIEducationGenerator"""
        try:
            result = self.ollama_generator.generar_texto(
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', 800),
                temperature=kwargs.get('temperature', 0.7)
            )
            return result
        except Exception as e:
            logger.error(f"Error en DirectOllamaLLM: {e}")
            return f"Error generando respuesta con Ollama local: {str(e)}"
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Parámetros que identifican este LLM"""
        return {
            "llm_type": "direct_ollama",
            "model_name": self.model_name,
            "host": self.host
        }


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


class OllamaIntegrationTool(BaseTool):
    """Herramienta personalizada para integrar Ollama con CrewAI"""
    name: str = "ollama_generator"
    description: str = "Genera texto educativo usando modelos locales de Ollama"
    
    # Declarar campos para Pydantic v2
    ollama_generator: Optional[object] = None
    
    def __init__(self, ollama_host: str = "192.168.1.10", ollama_model: str = "qwen3:latest", **kwargs):
        # Separar host y puerto si viene junto
        if ":" in ollama_host:
            host_only = ollama_host.split(":")[0]
        else:
            host_only = ollama_host
            
        # Crear generador antes de llamar super()
        ollama_gen = OllamaAPIEducationGenerator(
            host=host_only, 
            model_name=ollama_model
        )
        
        # Inicializar con los datos
        super().__init__(ollama_generator=ollama_gen, **kwargs)
    
    def _run(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Ejecuta la generación de texto con Ollama"""
        return self.ollama_generator.generar_texto(prompt, max_tokens, temperature)


class SistemaAgentesEducativos:
    """Sistema principal de agentes para generación de actividades educativas"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 perfiles_model: str = "qwen3:latest",      # Modelo para análisis de perfiles
                 disenador_model: str = "qwen3:latest",     # Modelo para diseño de actividades
                 ambiente_model: str = "qwen2:latest",  # Modelo para coordinación colaborativa
                 evaluador_model: str = "mistral:latest",     # Modelo para evaluación
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema de agentes
        
        Args:
            ollama_host: Host del servidor Ollama
            perfiles_model: Modelo para el agente de análisis de perfiles
            disenador_model: Modelo para el agente diseñador de actividades
            ambiente_model: Modelo para el agente de coordinación colaborativa
            evaluador_model: Modelo para el agente evaluador
            perfiles_path: Ruta al archivo de perfiles de estudiantes
        """
        self.ollama_host = ollama_host
        self.ambiente_model = ambiente_model
        self.disenador_model = disenador_model
        self.perfiles_model = perfiles_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Modelo general para compatibilidad (usar el primero como base)
        self.ollama_model = perfiles_model
        
        # Crear LLMs específicos para cada agente
        logger.info("🔧 Configurando LLMs específicos para cada agente...")
        
        try:
            # Configurar LiteLLM correctamente para Ollama
            import litellm
            
            # Configuraciones específicas para Ollama local
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            # Mapear todos los modelos para LiteLLM
            modelos_unicos = set([self.ambiente_model, self.disenador_model, self.perfiles_model, self.evaluador_model])
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
            logger.info(f"🔄 Creando LLMs específicos:")
            logger.info(f"   📊 Perfiles: {self.perfiles_model}")
            logger.info(f"   🎨 Diseñador: {self.disenador_model}")
            logger.info(f"   🤝 ambiente: {self.ambiente_model}")
            logger.info(f"   ✅ Evaluador: {self.evaluador_model}")
            
            self.ambiente_llm = Ollama(
                model=f"ollama/{self.ambiente_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=f"ollama/{self.disenador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.perfiles_llm = Ollama(
                model=f"ollama/{self.perfiles_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.evaluador_llm = Ollama(
                model=f"ollama/{self.evaluador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            # Test básico con el primer LLM
            logger.info(f"🧪 Probando conexión con {self.perfiles_model}...")
            try:
                test_response = self.perfiles_llm.invoke("Hello")
                logger.info(f"✅ LLMs configurados exitosamente")
            except Exception as test_error:
                logger.warning(f"⚠️ Test inicial falló pero continuando: {test_error}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            logger.error("🚨 No se pudieron configurar LLMs para CrewAI.")
            raise e
        
        # Cargar perfiles directamente para usar en las descripciones de tareas
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes especializados
        self._crear_agentes()
        
        logger.info(f"🤖 Sistema de agentes inicializado con modelos:")
        logger.info(f"   ambiente: {self.ambiente_model}")
        logger.info(f"   Diseñador: {self.disenador_model}")
        logger.info(f"   Perfiles: {self.perfiles_model}")
        logger.info(f"   Evaluador: {self.evaluador_model}")
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        """Cargar perfiles de estudiantes desde archivo JSON"""
        try:
            import json
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('estudiantes', [])
        except Exception as e:
            logger.error(f"Error cargando perfiles: {e}")
            return []
    
    def _crear_agentes(self):
        """Crea los agentes especializados del sistema"""
        
        # Agente Coordinador ambiente
        self.agente_ambiente = Agent(
            role="Especialista en crear ambientes adecuados para que el aprendizaje emerga de forma natural",
            goal="Crear el ambiente que mejor se ajuste al momento vital del alumnado de manera que el aprendizaje emerja de forma natural",
            backstory="""Eres un experto en pedagogía colaborativa y gestión de la diversidad en el aula. Eres experto en comprender qué tipo de actividad
            necesita un grupo en un momento dado. Eres como el jardinero que sabe en qué momento exacto ha de regar, en qué momento hay que podar y en
            qué momento hay que dejar que las plantas crezcan. Tu objetivo es crear un ambiente que favorezca que el aprendizaje emerja de forma natural. 
            Tienes que ver el grupo como una unidad y encontrar el clima que favorezca el máximo al grupo. 
            Tienes que responderte a preguntas del tipo: ¿qué nivel de agitación necesita este grupo en este momento? 

            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas. Todos los roles, responsabilidades y estrategias deben estar en español.""",
            tools=[],  
            llm=self.ambiente_llm,  # Modelo específico para coordinación del ambiente adecuado
            verbose=True,
            allow_delegation=False  # Desactivar delegación para evitar errores
        )
        # Agente Diseñador de Actividades
        self.agente_disenador = Agent(
            role="Diseñador de Actividades Educativas Adaptadas",
            goal="Crear actividades educativas innovadoras y adaptadas a las necesidades específicas de cada estudiante",
            backstory="""Eres un docente innovador especializado en metodologías activas y educación personalizada. 
            Tu experiencia incluye trabajo con aulas diversas, DUA (Diseño Universal para el Aprendizaje). 
            La actividad se ha de diseñar teniendo en cuenta las especificaciones y luego reconocer qué tareas precisa para que se lleve a cabo. Es muy importante
            tener en cuenta que las tareas pueden ocurrir de manera secuencial o en paralelo, pero cada estudiante tiene que tener tarea (o tareas) a lo largo de todo el 
            proceso de la actividad. La actividad tiene que estar diseñada para que todo el mundo vaya trabajando en unas cosas u otras y poco a poco compongan el aprendizaje colaborativo. 
            Tu especialidad es diseñar actividades que fomenten la colaboración, la creatividad y el aprendizaje significativo.
            El muy importante que reconozcas el tiempo que hay y el numero de estudiantes que van a llevar a cabo la actividad de manera que tengas en cuenta que todos
            han de estar ocupados durante todo el tiempo que dure la actividad. 
            
            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas. Todos los nombres, descripciones y contenidos deben estar en español.""",
            tools=[],  # Sin herramientas - usar solo LLM principal
            llm=self.disenador_llm,  # Modelo específico para diseño de actividades
            verbose=True,
            allow_delegation=False  # Desactivar delegación para evitar errores
        )
        # Agente Analizador de Perfiles
        self.agente_perfiles = Agent(
            role="Especialista en repartir Perfiles Educativos",
            goal="Analizar perfiles de estudiantes y identificar necesidades específicas para actividades educativas",
            backstory="""Eres un psicopedagogo experto con 15 años de experiencia en educación inclusiva. 
            Tu especialidad es analizar perfiles de estudiantes con diversas necesidades educativas (TEA, TDAH, 
            altas capacidades) y determinar las mejores estrategias de adaptación para cada caso. Eres capaz de adaptar cualquier actividad a las necesidades de
            cada estudiante. Tienes la capacidad de coger un grupo de tareas y repartirlas de manera equilibrada según sus capacidades a un grup de alumnos 
            de manera que todos hagan la tarea que mejor les compete. 
            
            Conoces perfectamente a estos 8 estudiantes del AULA_A_4PRIM y puedes analizar su diversidad sin necesidad de herramientas externas.
            
            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas.""",
            tools=[],  # Sin herramientas por ahora, información directa
            llm=self.perfiles_llm,  # Modelo específico para análisis de perfiles
            verbose=True,
            allow_delegation=False
        )
        
        
        # Agente Evaluador de Calidad (SUPERVISOR JERÁRQUICO)
        self.agente_evaluador = Agent(
            role="Supervisor Educativo y Coordinador del Equipo",
            goal="Supervisar el trabajo de todos los agentes, coordinar tareas y garantizar que se cumplan todos los estándares pedagógicos y de calidad",
            backstory="""Eres un SUPERVISOR EDUCATIVO con 20 años de experiencia en evaluación pedagógica.
            Tu rol es revisar, validar que todas las premisas se cumplen. Si una premisa no se esta cumpliendo, has de devolver a los agentes la tarea 
            para que la revisen. 
            Tienes que asegurarte de que una actividad es:
            - Relevante al tema que se está tratando
            - Realizable en un aula estandar. 
            - Que todos los estudiantes tienen tareas a lo largo de todo el proceso, nadie tiene momentos en los que está sin hacer nada.
            - Que se cumplen los principios del DUA (Diseño Universal para el Aprendizaje)
            - Que se cumplen los objetivos curriculares según la edad del grupo

            IMPORTANTE: Siempre responde en ESPAÑOL y actúa como un supervisor constructivo.""",
            tools=[],
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=False  # Sin delegación en proceso secuencial
        )
    
    def generar_actividad_colaborativa(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera una actividad colaborativa para toda el aula usando el sistema de agentes"""
        
        logger.info(f"👥 Generando actividad colaborativa para {materia}")
        
        # Crear tareas para actividad colaborativa
        tarea_analisis_aula = Task(
            description=f"""Analiza la diversidad del AULA_A_4PRIM (8 estudiantes de 4º de Primaria) para {materia}:

ESTUDIANTES CONOCIDOS:
- 001 ALEX M.: 9 años, reflexivo, visual, CI 102, nivel apoyo bajo, ningún diagnóstico
- 002 MARÍA L.: 9 años, reflexivo, auditivo, nivel apoyo medio, ningún diagnóstico  
- 003 ELENA R.: 9 años, reflexivo, visual, CI 118, nivel apoyo alto, TEA nivel 1
- 004 LUIS T.: 9 años, impulsivo, kinestésico, CI 102, nivel apoyo alto, TDAH combinado
- 005 ANA V.: 8 años, reflexivo, auditivo, CI 141, nivel apoyo bajo, altas capacidades
- 006 SARA M.: 9 años, equilibrado, auditivo, CI 115, nivel apoyo medio, ningún diagnóstico
- 007 EMMA K.: 9 años, reflexivo, visual, CI 132, nivel apoyo medio, ningún diagnóstico
- 008 HUGO P.: 9 años, equilibrado, visual, CI 114, nivel apoyo bajo, ningún diagnóstico

PROPORCIONA (TODO EN ESPAÑOL):
1. Mapa de diversidad (diagnósticos, estilos, niveles de apoyo)
2. Fortalezas grupales aprovechables
3. Desafíos de inclusión a considerar
4. Oportunidades de colaboración e interdependencia
5. Recomendaciones para agrupamiento efectivo

IMPORTANTE: Responde únicamente en ESPAÑOL. No uses palabras en inglés.""",
            agent=self.agente_ambiente,
            expected_output="Análisis detallado de la diversidad del aula con estrategias específicas"
        )
        
        tarea_diseno_base = Task(
            description=f"""Basándote en el analisis de la diversidad de los perfiles, diseña la estructura base de una actividad de {materia} {f'sobre {tema}' if tema else ''} que:
            1. Debe ser adecuada para el nivel del grupo que va a trabajar.
            2. Debe definir sus tareas de manera que cada estudiante esté ocupado en una u otra tarea a lo largo de toda la actividad.
            3. Estas tareas han de pensarse específicamente para el grupo en su conjunto y los estudiantes de forma individual, pudiendo agregar o quitar 
            tareas que nos interesen para el aprendizaje. 
            4. Siempre que se pueda incorporará otros aspectos curriculares relevantes en el momento en el que está el grupo. 
            5. Debe tener en cuenta los principios del DUA (Diseño Universal para el Aprendizaje).
            6. Debe ser viable en un aula estandar.

            
            Diseña:
            - Título y objetivos pedagógicos
            - Descripción general de la actividad
            - Proceso paso a paso
            - Materiales necesarios
            - Criterios de evaluación
            - Duración estimada
            
            Este es un ejemplo: ACTIVIDAD: Supermercado de Números
OBJETIVO_PRINCIPAL: Trabajar matemáticas aplicadas con dinero real
DURACIÓN_FLEXIBLE: 1-1.5 horas (termina cuando todos los clientes completan sus listas)
PARTICIPANTES: 8 estudiantes de 4º Primaria (AULA_A)
COMPETENCIAS_CURRICULARES: Números decimales, operaciones básicas, dinero, comunicación oral, escritura, medidas (peso/volumen), expresión, trabajo colaborativo

=== CONTEXTO PEDAGÓGICO ===

MOMENTO_CURSO: Semana 1 del curso - Repaso y evaluación inicial
NIVEL_GRUPO: 4º_primaria_evaluación_inicial
- Productos: Precios variados 6€-25€ (enteros) y algunos con decimales simples (.50€)
- Operaciones: Sumas de múltiples dígitos con llevadas, algunos decimales .50
- Presupuesto: 60€ por cliente (deben gestionar y que les sobre dinero)
- Cambio: variado según compras (práctica realista)
- Presión temporal: media-baja
- Interacción social: normal, cortés

MODALIDAD: preparación_integrada + ejecución_simultánea
INSTALACIONES: Aula habitual convertida en centro comercial con 3 tiendas temáticas
MATERIALES_GENERALES: Productos etiquetados, dinero real, cajas registradoras simuladas, materiales de decoración, papel, rotuladores, tijeras, lápices

=== TIENDAS TEMÁTICAS ===

TIENDA 1 - "MATERIAL ESCOLAR" (Cajero: Alex)
Productos: Mochila 25€, Estuche 12€, Diccionario 18€, Set rotuladores 9€, Agenda 15€, Compás 11€
Contexto: "Valorar cuánto gastan las familias en material escolar"

TIENDA 2 - "SOUVENIRS DE VIAJE" (Cajero: Elena)  
Productos: Camiseta 16€, Llavero 7€, Imán nevera 4€, Gorra 13€, Postal 2€, Taza 8€
Contexto: "Compras de recuerdos para familiares"

TIENDA 3 - "HOBBIES Y TIEMPO LIBRE" (Cajero: Emma)
Productos: Libro 14€, Juego mesa 22€, Pelota 10€, Puzzle 17€, Cartas 6€, Kit manualidades 19€
Contexto: "Actividades para el tiempo libre"

=== GESTIÓN DOCENTE ===

ROL_PROFESOR:
1. **Explicación inicial** (5 min): Presentar actividad general a todos
2. **Reuniones individuales** (durante preparación):
   - Ana (Supervisor): Coordinar organización espacial y flujo de actividad
   - Elena (Cajero TEA): Revisar secuencias, protocolo de interacción, uso de apoyos
   - Luis (Cliente TDAH): Momento de centrado, revisar plan, estrategias de organización
3. **Supervisión general**: Circular por aula, resolver dudas, gestionar tiempos
4. **Apoyo en dictados**: Colaborar y supervisar en dictados individualizados
5. **Registro de observaciones**: Documentar uso de adaptaciones y efectividad

CRITERIO_FINALIZACIÓN:
La actividad termina cuando todos los clientes han completado sus listas de compra, sin presión temporal. Se estima 1-1.5 horas incluyendo preparación.

=== TAREAS IDENTIFICADAS ===

1. CAJERO (3 estudiantes)
   - Función: Cobrar productos, dar cambio, atender con cortesía, crear listados de precios (dictado)
   - Competencias: Matemáticas dinero, atención sostenida, comunicación, medidas
   - Interacciones: Clientes individuales, supervisor
   - Preparación: Organizar caja, revisar dinero, preparar tickets, decorar puesto
   - Entrega de cuentas: Reporte final de ventas y caja

2. SUPERVISOR/REPONEDOR (1 estudiante)
   - Función: Coordinar actividad, reponer productos, resolver problemas, realizar dictados
   - Competencias: Liderazgo, organización, matemáticas básicas, comunicación, lectura
   - Interacciones: Todos los roles, cajeros (consultas), clientes (dictados y problemas)
   - Preparación: Organizar productos, crear señalización, preparar listas para dictado
   - Informe de gestión: Síntesis de incidencias y coordinación

3. CLIENTE (4 estudiantes)
   - Función: Comprar productos según lista dictada, interactuar con cajeros
   - Competencias: Escritura (dictado), planificación, cálculo presupuesto, comunicación
   - Interacciones: Cajeros, supervisor (dictado), otros clientes (cola)
   - Preparación: Escribir lista por dictado, calcular presupuesto aproximado, organizar compra por tiendas
   - Compras:
		- Sara: mochila (25), llavero (7), libro (14) y gorra (13) = 59 
		- Luis: estuche (12), kit de manualidades (19), puzzle (17) y postal (2) = 50
		- María: diccionario (18), iman de nevera (4), taza (8) y pelota (10) = 40
		- Hugo: camiseta (16), juegos de mesa (22), cartas (6), set de rotuladores (9) = 52

=== PARÁMETROS CONFIGURABLES POR TAREA ===

COMPLEJIDAD_CÁLCULO:
- básica: números enteros, operaciones simples
- media: decimales básicos, operaciones combinadas
- alta: decimales complejos, descuentos, estimaciones

PRESIÓN_TEMPORAL:
- baja: ritmo pausado, tiempo para reflexionar
- media: ritmo normal, cierta urgencia
- alta: ritmo acelerado, decisiones rápidas

APOYO_DISPONIBLE:

- visual: tablas, secuencias, guías, ábacos
- manipulativo: dedos, pegatinas, objetos para contar
- social: compañero para consultas
- material: cascos reducción ruido, información estructurada, estrategias TDAH, cuerda delimitadora

INTERACCIÓN_SOCIAL:
- mínima: tareas individuales, comunicación básica
- normal: comunicación estándar, cortesía
- intensa: negociación, resolución conflictos, liderazgo

=== BANCO DE RECURSOS DISPONIBLES ===

ZONA_AUTOSELECCIÓN (disponible para quien la necesite):
- Ábacos y manipulativos para cálculo
- Pegatinas organizativas (productos, cantidades)
- Folios con cuadrantes para organizar listas por tienda
- Tablas de apoyo visual para operaciones
- Cascos de reducción de ruido
- Cuerdas delimitadoras para "cerrar tienda" temporalmente
- Leyendas visuales de procedimientos
- Carteles con precios únicos para todos

DIFERENCIACIÓN_CONTROLADA:
- Complejidad matemática gestionada desde dictados personalizados
- Todos los cajeros manejan los mismos precios (simplifica gestión)
- Adaptación por perfil mediante listas de compra individualizadas

CONTROL_FINANCIERO_TOTAL:
- 3 cajeros empiezan con 30€ cada uno = 90€ (cambio inicial)
- 4 clientes empiezan con 60€ cada uno = 240€
- TOTAL EN CIRCULACIÓN: 330€

VERIFICACIÓN_FINAL (la magia de las matemáticas):
- Suma dinero final de 3 cajeros + dinero final de 4 clientes = 330€
- Cada cajero declara: 30€ inicial + ventas realizadas - dinero final = beneficio obtenido
- Suma de beneficios de 3 cajeros = total gastado por 4 clientes
- Si todo cuadra: ¡Las matemáticas funcionan!

Este es otro ejemplo: 

Sumas Con Llevadas

¿Qué significa "me llevo 1"?

Descripción de la actividad:

Realizaremos sumas conjuntas. 
Colocaremos 6 mesas, dos a dos, separadas para poder moverse entre ellas y enfrentadas entre si. 
6 estudiantes se colocarán a cada lado, mirándose. Cada pareja que se mira será, respectivamente, las unidades, las decenas y las centenas. 

Daremos dos números, por ejemplo: 145 + 168 

Cada estudiante recibe en su lado de la mesa su cantidad correspondiente, en unidades o en paquetes (bolsas de 10, cajitas de 100). 
La clave es que ninguno puede tener más de 9 en sus mesas conjuntas. 
Al crear una bolsa o un paquete, han de pasarlo a sus compañeros y el resultado de cada pareja ha de quedar en el centro de la mesa.

Finalmente, reconocemos el número de resultado debería reflejar 313. 

Mientras, las 2 personas que no están en las mesas, han hecho las cuentas individualmente (en pizarra, cuadernos, como quieran). Si tenemos suficientes paquetes, pueden ponerse a realizar estas sumas de manera individual con ellos.

Finalmente, todxs deberíamos tener el mismo resultado. 

Hacemos rotaciones y vamos haciendo cuentas. Quizás la cosa fluya a que cada uno quiere hacer cuentas individualmente o por parejas o equipos. Se permite la exploración. 


Materiales:
Lentejas, garbanzos, cuentas, fichas, bolsas, cajitas.

Preparación:

Luis y Emma pueden preparar las mesas. 

El resto pueden ir haciendo paquetes de 10. Teniendo unos cuantos de 10 e individuales ya podemos dar las cantidades de salida. 
Quizás para Elena (o para cualqier otro) esta pueda ser una tarea estimulante, si se hacen bastantes nos da más flexibilidad para trastear. 
Cuando creamos que tenemos suficientes, podemos empezar. 
Si el material se elige con cierta conciencia, puede servir de estrategia metodológica, puede ser muy reutilizable para múltiples tareas y como estrategia cognitiva del aula para realizar cuentas. 
Por ejemplo, usar lentejas potencia la concentración, la motricidad fina. Se pueden guardar en bolsitas herméticas de 10 que ocupan poco espaci. Los paquetes 100 pueden ser cajitas o bolsas más grandes, pero es accesible de guardar en un aula. 

Versión para peques:

Imprimimos folios con 10 (circulos, estrellas..) tamaño pegatina y que ponga 1 en cada dibujito y 10 en grande como título del folio. Tenemos que tener pegatinas o se pueden colorear con pintura de dedos, rotus de punta gorda...
Cada vez que completamos el folio lo pasamos al otro lado. Cuando tengamos 10 folios, lo metemos en un portafolio con un cartel que ponga 10. Al final tenemos un resultado, reconocemos el numero y lo escribimos. 

Versión más compleja: 

A las bolsas de 10 les podemos ahora cambiar el nombre a 1, y al resto de forma correspondiente. De este modo, podemos trabajar con decimales. ¿0.5 = 1/2?. Podemos representarlo. 

Este es otro ejemplo: Mejoren las habilidades de orientación espacial y reconstrucción de mapas.

Además, la actividad incorpora aspectos curriculares transversales como:

Ciencias Naturales: Propiedades del agua (volumen), la forma de los objetos.

Lengua Castellana: Vocabulario geométrico, descripción de procesos de resolución, comunicación oral.

Habilidades del Siglo XXI: Pensamiento crítico, resolución de problemas, colaboración.

Descripción de la Actividad
La actividad se llevará a lo largo de la semana que culminará el viernes en una Feria Matemática. 

Rol del Profesor
El docente irá presentando las actividades sin hacer referencia a que vayan a ser utilizadas más adelante. Simplemente permitiendo que se despierte o no su curiosidad y estas cosas son las que iremos viendo del desarrollo del aula. 

Gestión del Aula durante la Actividad:
Observación Activa y Guía Discreta: Circulará por las estaciones, observando las dinámicas de las parejas y los desafíos individuales. Proporcionará pistas indirectas a través de preguntas abiertas ("¿Habéis probado a...? ¿Qué pasaría si...?"), en lugar de dar soluciones.

Gestión del Clima Emocional: Monitoreará la frustración y el aburrimiento. Recordará la importancia del tono tranquilo y respetuoso entre los compañeros, y el valor del esfuerzo. Puede sugerir pequeños "descansos cerebrales" si percibe altos niveles de ansiedad, especialmente para Elena y Luis.

Fomento de la Autonomía: Evitará la sobreintervención. Su objetivo es que los estudiantes encuentren sus propias soluciones y estrategias.

Gestión del Tiempo: Aunque la actividad es flexible, el docente puede dar avisos de tiempo para que las parejas avancen y no se queden atascadas demasiado tiempo en un reto.

Registro de Observaciones: Anotará qué estrategias utiliza cada pareja, qué desafíos surgen, y cómo colaboran, para la evaluación formativa posterior.

Planteamiento de la Actividad:
Narrativa Inmersiva: Presentará la actividad con una historia de piratas y tesoros, enfatizando que el verdadero tesoro es el conocimiento y la capacidad de resolver misterios.

Preparación de Estaciones: Asegurará que cada estación esté perfectamente preparada con los materiales adecuados y las instrucciones visuales/auditivas necesarias.


Agrupamientos y Tareas/Roles Específicos por Pareja
Las parejas se han formado buscando un equilibrio entre niveles de apoyo, canales preferentes y temperamentos, fomentando la ayuda mutua y el desafío óptimo para ambos miembros. Los roles dentro de cada pareja serán flexibles, permitiendo a los estudiantes decidir cómo se dividen el trabajo.
 
Preparación de la actividad: 

Durante la semana iremos preparando los materiales que vamos a necesitar.
Se pedirá que traigan botellas durante la semana y el jueves las trabajaremos.  

Lunes: Taller formas geométricas. 1.Recortables y montables. Hacer etiquetas con los nombres y guardarlas en un bote, carpeta... 2. Encontrar objetos en el aula (se puede favorecer por ejemplo, con dados de varias caras), categorizarlos, creandos dos tarjetas por objeto: nombre y forma geométrica. Y se guardan las tarjetas en otro bote o carpeta. 

Martes: Haremos una dinámica de cómo calcular áreas con diferentes materiales, con cuerdas para círculos y rectas, con bloques de dominó, imanix, la idea es jugar con diferentes formas de calcular cuánto ocupan las cosas. Una superficie puede ocupar un folio y 5 imanix. Dentro de esta actividad, dejaremos hechas, como 3 por estudiante, tarjetas con nombres de objetos del aula que podríamos medir con cualquier cosa. Por ejemplo puede haber tarjetas en las que ponga, "el libro de ciencias" o "el respaldo de las sillas", se deja libertad. Estas tarjetas también se guardan en un bote o carpetita.  Así mismo, se crearán tarjetas con los objetos que puedan servir de unidades de medida (los imanix, dominó, cuerda) que también se guardan. 

Miércoles:
Dinámica de lógica: 
Sacaremos diferentes actividades típicas de:
estrella+estrella=16

estrella+luna=25

luna−sol=10

sol×estrella+luna=?

Se puede hacer una actividad grupal de ir haciéndo varias en la pizarra entre todos primero. Y luego se les pide que traten de crear una ellos. Se deja el tiempo necesario hasta que todos han hecho por lo menos, una. Si en ese tiempo alguien hace más, se incluirán en su respectivo bote o carpeta. Todos los ejercicios han de ser validados antes de incluirlos. Dependiendo del ritmo se pueden hacer más. 

Jueves:
Botellas y revelación. 
Durante la semana habremos ido recopilando botellas en algún espacio del aula. Hoy las vamos a contar y catalogar. 
La idea es tener varias garrafas por ejemplo de 6 y 8 litros. Las dejaremos aparte y crearemos tarjetas de cantidades que podrían entrar (por ejemplo, 4,75L, 5,5L, 7,60L) bote totales
Todas las que sean como de 1,5L (aprox) para abajo, las iremos cogiendo una a una y escribiremos un cartelito por cada una con el volumen en decimales y fracciones, por ejemplo 0,5L y 1/2L. Y esos cartelitos se guardan también en un bote o carpeta. bote cálculos
 
Una vez cerrado el material, se revela la actividad: !Haremos una Feria Matemática!

Se explican los puestos brevemente. 

Garrafas. 
Se sacará una tarjeta del bote cantidades y dos tarjetas de las botellas. Cada equipo tendrá que elegir una garrafa y usar las dos botellas pequeñas que correspondan a sus tarjetas para rellenar la garrafa. 

Geometría.
Se descolocan las figuras geométricas. 
Cada equipo tendrá que colocar cada figura geométrica con su nombre correspondiente. Además, sacará 5 tarjetas de nombre de objeto y tendrá a disposición otra tanda de nombes de formas donde elegir. 

Lógica:
Cada equipo sacará 2 (o 3, dependiendo de cuántas se crearan) de las actividades que diseñaron ellos mismos y tendrán que resolverlas. 

Áreas:
Cogerán una tarjeta de objeto de aula y dos tarjetas de unidades de medida. Tendrán que encontrar la manera de describir en términos de las unidades que les hayan salido, cuánto ocupa el objeto. 

Repartiremos un puesto por grupo: 

Alex y María: equipo equilibrado, pareja bastante parecida a nivel funcional. 

Elena y Emma: tarea que puede generar tensión a Elena y Emma es muy tranquila. 

Ana y Hugo: ambos van a incurrir en conversación para llegar a una lógica. Buenos argumentando. 

Sara y Luis: Sara ayudará con buena argumentación y Luis creará opciones creativas. 

Cada equipo elige un puesto o coge una tarjetita aleatoria y el resto del día lo dedicaremos a organizar la feria. Primeramente cada equipo tendrá que crear un panel informativo de en qué consiste el puesto. Evaluaremos como van integrando la información. Ayudaremos a que cada uno tenga claro, al menos, su puesto. Así podrán crear las tarjetas con sentido. Después seguiremos decorando y colocando: dejar las garrafas preparadas, las carpetas o botes de cada puesto, hacer dibujos, etc. 

Viernes:

Ya tenemos todo preparado y debería haber al menos algo de expectación. 

Cada equipo puede coger una tarjeta de puesto, o coger un número y será el orden para elegir. 
La idea es incluir muchos aspectos de probabilidad y aleatoriedad en la dinámica. 
Cada equipo empieza en un puesto y luego rotan en un sentido o otro. En este momento hay que dar cierta libertad al juego, pero tratando de mantener un volumen adecuado. Aquí el profesor tendrá que ir validando la realización de cada prueba. Los grupos tendrán que esperar a que el/la profe esté disponible para ir a revisar y mientras deberán repasar sus resultados. 

Al acabar cada ronda, reciben por ejemplo, un trozo de frase de algún matemático famoso o referente a la magia de las matemáticas. Una vez que tienen todos sus trozos construyen su frase. 
O al acabar todas las pruebas cada equipo recibe un trozo de acertijo que tienen que resolver entre todo el aula. 



Adaptaciones: 

Elena siempre debería tener a disposición sus cascos y estrategias de regulación (por ejemplo, llevar un trozo de plastilina en la mano). 
El aula debe disponer de diferentes materiales que les sirvan de estrategia de organización, cuadernos, lápices, cuentas, etc. 
Para Luis es una actividad movida, motivante y estructurada. 
Para Ana es un reto donde además, juega el papel de la aleatoriedad. 


Proporcionar múltiples medios de representación (El "Qué" del Aprendizaje): tienen las garrafas y tienen las tarjetas, o los simbolos y las cuentas, las formas geométricas estrictas y las del "mundo", junto con nombres escritos. Numerosos materiales con los que medir áreas... 

Todos: La propia acción de verter agua, mover fichas, colocar carteles facilita la comprensión concreta.

Proporcionar múltiples medios de acción y expresión (El "Cómo" del Aprendizaje):

Expresión Oral: Discusión de estrategias en pareja, justificación de respuestas al profesor, explicación de conceptos.

Expresión Escrita/Dibujo: Registro de cálculos, diagramas, esquemas, listas de fracciones, dibujos de las soluciones de área.

Manipulación: Solución física de los problemas (llenar garrafas, cubrir áreas).

Autoregulación:

Gestión del tiempo: Reloj en el aula. 

Estrategias de afrontamiento: Se recordarán herramientas para la frustración (pausas, respiración, pedir ayuda). En los momentos entre ronda y ronda, se pueden hacer pausas estratégicas, parales un poco, antes de seguir. 

Elección: Dentro de cada reto, las parejas podrán decidir cómo se organizan el trabajo.

Proporcionar múltiples medios de implicación (El "Por qué" del Aprendizaje):

Colaboración y Pertenencia: El trabajo en pareja y la posterior resolución conjunta.

Novedad y Curiosidad: toda la actividad está diseñada para despertar curiosidad y puesta en conciencia.

Retroalimentación Inmediata y Formativa: La validación del profesor en cada reto ofrece retroalimentación instantánea, y la incapacidad de avanzar sin una respuesta correcta fomenta la auto-corrección.





Si hay opción de incorporar material nuevo al aula. Puede haber un premio de la feria que sea nuevo un libro para el aula, de curiosidades matemáticas, con datos interesantes y acertijos nuevos.

Los premios pueden ser "tesoros de conocimiento". Al acabar la última ronda, cada equipo recibe un "dato mágico" o una pregunta sobre una curiosidad que cuestionarse. 

"El número Pi (π) es un número infinito que nos ayuda a calcular la circunferencia de cualquier círculo. Se usa desde la construcción de las pirámides hasta los viajes al espacio." (Con un número largo de Pi escrito)

"¿Sabías que un rayo puede contener tanta energía como 100 bombillas encendidas durante un día? La electricidad es una forma de energía que se mide con números muy grandes y muy pequeños." (Con un dibujo de un rayo y una bombilla).

"Las abejas construyen sus panales con hexágonos perfectos. Esta forma geométrica es la más eficiente para guardar miel, ¡porque ocupa el mínimo espacio y usa el mínimo material!" (Con una imagen de un panal y un hexágono).

"Nuestro cerebro pesa solo un 2% de nuestro cuerpo, ¡pero consume un 20% de toda la energía que usamos! Es una máquina increíble para resolver problemas, como los que habéis resuelto hoy."

Conexión con Intereses: Si es posible, se puede intentar que el dato final conecte con un interés general del grupo (ciencia, naturaleza, el cuerpo humano, etc.).

Capacidad de reflexión y de pensamiento abstracto. Durante la semana, si empiezan a ver que algo se cuece, y al organizar la actividad el jueves, van recreando posibles opciones que les pueden tocar, conocen los materiales, y las posibilidades. 

La Curiosidad como Motor

Autonomía en la Resolución: El docente no da las soluciones, lo que empodera a los estudiantes a confiar en sus propias capacidades para encontrar las respuestas.

            IMPORTANTE: 
            - Enfocate el/la profesor/a en estos ejemplos, sabe exactamente qué hace cada uno en cada momento. Sabe si puede realizar las cuentas o las 
            tareas que se les asigna o no. 
            - Las tareas estan repartidas, no se dejan como "libres" o "a elección", sino que cada uno tiene una tarea concreta y definida.
            - Responde únicamente en ESPAÑOL. No uses palabras en inglés
            - Todos los títulos, descripciones y materiales deben estar en español""",
            agent=self.agente_disenador,
            context=[tarea_analisis_aula],
            expected_output="Diseño estructural de actividad educativa lista y detallada para coordinación colaborativa"
        )

        tarea_coordinacion_colaborativa = Task(
            description=f"""Toma la actividad diseñada y conviértela en una experiencia colaborativa asignando roles específicos a cada estudiante:

ESTUDIANTES DEL AULA:
- 001 ALEX M.: reflexivo, visual, CI 102, apoyo bajo
- 002 MARÍA L.: reflexivo, auditivo, apoyo medio  
- 003 ELENA R.: reflexivo, visual, CI 118, apoyo alto, TEA nivel 1
- 004 LUIS T.: impulsivo, kinestésico, CI 102, apoyo alto, TDAH combinado
- 005 ANA V.: reflexivo, auditivo, CI 141, apoyo bajo, altas capacidades
- 006 SARA M.: equilibrado, auditivo, CI 115, apoyo medio
- 007 EMMA K.: reflexivo, visual, CI 132, apoyo medio
- 008 HUGO P.: equilibrado, visual, CI 114, apoyo bajo

ASIGNA:
1. ROL ESPECÍFICO para cada estudiante (por nombre/ID)
2. Responsabilidades particulares que aprovechen sus fortalezas
3. Interdependencia positiva (todos necesarios para el éxito)
4. Adaptaciones específicas para TEA, TDAH y altas capacidades
5. Estrategias de apoyo e inclusión
6. Dinámicas de interacción y comunicación

IMPORTANTE: Responde únicamente en ESPAÑOL. Todos los roles, responsabilidades y estrategias deben estar en español.""",
                        agent=self.agente_perfiles,
            context=[tarea_diseno_base],
            expected_output="Coordinación colaborativa con roles específicos y estrategias de inclusión"
        )
        
        tarea_supervision_final = Task(
            description="""Como SUPERVISOR FINAL, revisa y valida todo el trabajo realizado por el equipo:
            
            REVISIÓN Y VALIDACIÓN COMPLETA:
            1. EVALÚA el análisis de perfiles del especialista en diversidad
            2. VALIDA el diseño pedagógico del diseñador de actividades  
            3. SUPERVISA la propuesta colaborativa del especialista en ambiente
            4. INTEGRA todas las fases en una propuesta coherente y optimizada
            
            CRITERIOS DE SUPERVISIÓN:
            ✅ Todos los estudiantes tienen roles significativos y apropiados
            ✅ Las adaptaciones para TEA, TDAH y altas capacidades son efectivas
            ✅ La interdependencia es auténtica y pedagogicamente justificada
            ✅ Los objetivos curriculares de 4º Primaria se cumplen completamente
            ✅ La evaluación es equitativa y adaptada a cada perfil
            ✅ La actividad es viable y realista para el aula
            ✅ Se respetan los principios del DUA
            
            ENTREGA FINAL:
            - Actividad completamente validada y optimizada
            - Justificación pedagógica de todas las decisiones
            - Plan de implementación claro para el docente
            - Criterios de éxito específicos y medibles
            
            IMPORTANTE: Como supervisor, tienes la responsabilidad final de la calidad. Responde únicamente en ESPAÑOL.""",
            agent=self.agente_evaluador,

            expected_output="Actividad colaborativa completamente supervisada, validada y optimizada con plan de implementación"
        )
        
        # Crear y ejecutar el crew con proceso secuencial supervisado

        crew = Crew(
            agents=[self.agente_perfiles, self.agente_disenador, self.agente_ambiente, self.agente_evaluador],
            tasks=[tarea_analisis_aula, tarea_diseno_base, tarea_coordinacion_colaborativa, tarea_supervision_final],
            process=Process.sequential,  # Cambiar a secuencial para evitar problemas de delegación
            verbose=True
        )
        
        resultado = crew.kickoff()
        
        # Capturar resultados de todas las tareas
        contenido_completo = ""
        
        # Intentar acceder a los resultados individuales de las tareas
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido_completo += "=== ANÁLISIS DE DIVERSIDAD DEL AULA ===\n"
                contenido_completo += str(resultado.tasks_output[0]) + "\n\n"
                
                contenido_completo += "=== DISEÑO BASE DE LA ACTIVIDAD ===\n"
                contenido_completo += str(resultado.tasks_output[1]) + "\n\n"
                
                contenido_completo += "=== COORDINACIÓN COLABORATIVA ===\n"
                contenido_completo += str(resultado.tasks_output[2]) + "\n\n"
                
                contenido_completo += "=== SUPERVISIÓN Y VALIDACIÓN FINAL ===\n"
                contenido_completo += str(resultado.tasks_output[3]) + "\n\n"
            else:
                # Fallback al resultado principal
                contenido_completo = str(resultado)
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados individuales: {e}")
            contenido_completo = str(resultado)
        
        # Crear estructura de actividad colaborativa
        actividad = ActividadEducativa(
            id=f"colaborativa_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad Colaborativa - {materia}",
            materia=materia,
            tema=tema or "Tema ambiente",
            contenido=contenido_completo,
            estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
            tipo="colaborativa",
            adaptaciones=["roles_diferenciados", "multiple_canales", "interdependencia_positiva"],
            metadatos={
                "total_estudiantes": 8,
                "modelos_usados": {
                    "perfiles": self.perfiles_model,
                    "disenador": self.disenador_model,
                    "ambiente": self.ambiente_model,
                    "evaluador": self.evaluador_model
                },
                "agentes_participantes": ["perfiles", "disenador", "ambiente", "evaluador"]
            },
            timestamp=datetime.now().isoformat()
        )
        
        return actividad
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_crewai") -> str:
        """Guarda una actividad en un archivo"""
        
        # Asegurar que se guarde en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON CREWAI + OLLAMA\n")
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
            f.write("METADATOS:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad guardada en: {filepath}")
        return filepath
    
    def ejecutar_workflow_completo(self, materia: str, tema: str = None) -> Dict:
        """Ejecuta un workflow simplificado generando solo actividades colaborativas"""
        
        logger.info(f"🚀 Iniciando workflow ambiente para {materia}")
        
        resultados = {
            "materia": materia,
            "tema": tema,
            "timestamp": datetime.now().isoformat(),
            "actividades_generadas": [],
            "archivos_creados": []
        }
        
        try:
            # Generar únicamente actividad colaborativa
            logger.info("🤝 Generando actividad colaborativa...")
            actividad_colaborativa = self.generar_actividad_colaborativa(materia, tema)
            archivo_colaborativa = self.guardar_actividad(actividad_colaborativa)
            
            resultados["actividades_generadas"].append({
                "tipo": "colaborativa",
                "id": actividad_colaborativa.id,
                "archivo": archivo_colaborativa
            })
            resultados["archivos_creados"].append(archivo_colaborativa)
            
            logger.info(f"✅ Workflow ambiente terminado. 1 actividad generada.")
            
        except Exception as e:
            logger.error(f"❌ Error en workflow ambiente: {e}")
            resultados["error"] = str(e)
        
        return resultados


def main():
    """Función principal de demostración del sistema de agentes"""
    
    print("="*60)
    print("🤖 SISTEMA DE AGENTES CREWAI + OLLAMA PARA EDUCACIÓN")
    print("="*60)
    
    try:
        # Configuración (ajusta según tu setup)
        OLLAMA_HOST = "192.168.1.10"  # Ollama local
        PERFILES_MODEL = "qwen3:latest"     # Modelo para análisis de perfiles
        DISENADOR_MODEL = "qwen3:latest"    # Modelo para diseño de actividades  
        ambiente_MODEL = "qwen3:latest" # Modelo para coordinación colaborativa
        EVALUADOR_MODEL = "qwen3:latest"    # Modelo para evaluación
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        # Inicializar sistema
        print(f"\n🔧 Inicializando sistema con:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Modelo Perfiles: {PERFILES_MODEL}")
        print(f"   Modelo Diseñador: {DISENADOR_MODEL}")
        print(f"   Modelo ambiente: {ambiente_MODEL}")
        print(f"   Modelo Evaluador: {EVALUADOR_MODEL}")
        print(f"   Perfiles: {PERFILES_PATH}")
        
        sistema = SistemaAgentesEducativos(
            ollama_host=OLLAMA_HOST,
            perfiles_model=PERFILES_MODEL,
            disenador_model=DISENADOR_MODEL,
            ambiente_model=ambiente_MODEL,
            evaluador_model=EVALUADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema inicializado correctamente!")
        
        # Menú simplificado - Solo actividades colaborativas
        while True:
            print("\n" + "="*50)
            print("🎯 SISTEMA DE ACTIVIDADES COLABORATIVAS")
            print("1. 🤝 Generar actividad colaborativa")
            print("2. 🚀 Ejecutar workflow ambiente")
            print("3. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-3): ").strip()
            
            if opcion == "1":
                print("\n🤝 GENERACIÓN DE ACTIVIDAD COLABORATIVA")
                materia = input("📚 Materia (Matemáticas/Lengua/Ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                actividad = sistema.generar_actividad_colaborativa(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                
                print(f"\n✅ Actividad colaborativa generada:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   👥 Estudiantes: {len(actividad.estudiantes_objetivo)}")
            
            elif opcion == "2":
                print("\n🚀 WORKFLOW ambiente")
                materia = input("📚 Materia (Matemáticas/Lengua/Ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                print(f"\n⏳ Ejecutando workflow ambiente para {materia}...")
                print("   (Esto puede tomar varios minutos)")
                
                resultados = sistema.ejecutar_workflow_completo(materia, tema)
                
                if "error" not in resultados:
                    print(f"\n🎉 ¡Workflow ambiente completado exitosamente!")
                    print(f"   📊 Total actividades: {len(resultados['actividades_generadas'])}")
                    print(f"   📁 Archivos creados: {len(resultados['archivos_creados'])}")
                    print("\n📋 Resumen:")
                    for act in resultados['actividades_generadas']:
                        print(f"   • {act['tipo'].capitalize()}: {act['id']}")
                else:
                    print(f"\n❌ Error en workflow: {resultados['error']}")
            
            elif opcion == "3":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-3.")
    
    except ImportError as e:
        print(f"\n❌ Error de importación: {e}")
        print("\n💡 Para usar este sistema necesitas instalar:")
        print("   pip install crewai crewai-tools")
        print("   pip install requests  # para Ollama")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. El modelo especificado esté disponible")
        print("   3. El archivo de perfiles exista")


if __name__ == "__main__":
    main()