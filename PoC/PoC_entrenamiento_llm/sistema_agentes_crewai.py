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

# Configurar variables de entorno para LiteLLM/CrewAI (localhost)
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"
os.environ["LITELLM_LOG"] = "DEBUG"  # Para debug

# Configuración para forzar Ollama sin LiteLLM
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder
os.environ["OPENAI_MODEL_NAME"] = "llama3:latest"
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
    
    def __init__(self, ollama_host: str = "localhost", ollama_model: str = "llama3:latest"):
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
    
    def __init__(self, ollama_host: str = "localhost", ollama_model: str = "llama3:latest", **kwargs):
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
                 ollama_host: str = "localhost", 
                 perfiles_model: str = "llama3:latest",      # Modelo para análisis de perfiles
                 disenador_model: str = "llama3:latest",     # Modelo para diseño de actividades
                 ambiente_model: str = "llama3:latest",  # Modelo para coordinación colaborativa
                 evaluador_model: str = "llama3:latest",     # Modelo para evaluación
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
        self.perfiles_model = perfiles_model
        self.disenador_model = disenador_model
        self.ambiente_model = ambiente_model
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
            modelos_unicos = set([self.perfiles_model, self.disenador_model, self.ambiente_model, self.evaluador_model])
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
            
            self.perfiles_llm = Ollama(
                model=f"ollama/{self.perfiles_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=f"ollama/{self.disenador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.ambiente_llm = Ollama(
                model=f"ollama/{self.ambiente_model}",
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
        logger.info(f"   Perfiles: {self.perfiles_model}")
        logger.info(f"   Diseñador: {self.disenador_model}")
        logger.info(f"   ambiente: {self.ambiente_model}")
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
            backstory="""Eres un experto en pedagogía colaborativa y gestión de la diversidad en el aula. Sabes reconocer perfectamente
            cuando el momento en el que los estudiantes están listos para continuar el aprendizaje y cuando necesitan asentar conocimientos. 
            Además, reconoces en las características de cada estudiante y cada aula, las necesidades de gestión emocional que precisan, 
            ayudando a dar los apoyos o permitir que se hagan responsables de una manera equilibrada en cada situación. Por ejemplo, en este aula
            siempre lideran las dos mismas personas y hay otras que están preparadas para ejercer liderazgo pero no han tenido la oportunidad. 
            El grupo tiene un gran interés por gestionar de manera autónoma así que les plantearemos actividades en las que han de resolver ciertos asuntos 
            por si mismos, de manera que tengan que pensar, probar, y autoevaluarse. 
            También según el horario en que se vayan a realizar las actividades. Por ejemplo, si hacemos la actividad después de una clase de 
            gimnasia o deportiva, quizás necesiten un tiempo de relajación antes de poder concentrarse. Si la clase de al lado está haciendo música, 
            quizás es un buen momento para hacer una actividad que no requiera estar muy concentrados y podamos hacer una charla común o cosas así. 
            Se buscará favorecer la colaboración entre el aula lo máximo posible (ya sea con todo el aula, en parejas o grupos) pero teniendo en cuenta que las 
            tareas individuales también son importantes. 
            Una de las claves para mantener un clima adecuado en un aula es que todo el mundo tenga un rol y una responsabilidad en cada momento de la actividad. 
            En este sentido eres como el jardinero que prepara el terreno para que las plantas tengan todo lo suficiente para crecer 
            y desarrollarse, pero sin interferir en su crecimiento natural.

            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas. Todos los roles, responsabilidades y estrategias deben estar en español.""",
            tools=[],  # Sin herramientas - usar solo LLM principal
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
            La actividad ha de estar diseñada para trabajar lo que se desea trabajar en el contexto del aula que tenemos. Se ha de diseñar 
            detallando las tareas que se han de realizar y que estas sean acordes a lo que cada estudiante necesita trabajar. 
            Tratarás de fomentar el pensamiento abstracto, el pensamiento crítico, la comprensión de los conceptos antes de trabajarlos, 
            la creatividad, la colaboración y el aprendizaje autónomo. Siempre que sea posible NO se usarán elementos tecnológicos, para comprender
            conceptos tecnológicos nos iremso a las opciones analógicas y de comprensión de las bases de la tecnología y no de su uso. 
            Es mejor para aprender como funciona la tecnología que aprendan secuencias lógicas y desarrollen su pensamiento abstracto a que 
            sepan usar una pantalla y pedirle al ordenador que les devuelva la respuesta correcta. NO ESTAS A FAVOR DEL USO DE LA TECNOLOGÍA en primaria
            Prefieres construir las cosas con las manos, hacer experimentos, juegos de rol, actividades prácticas y creativas que fomenten el aprendizaje significativo.
            La actividad tiene que estar detallada en sus tareas y el reparto de las mismas para cada estudiante de manera que estos siempre tengan cosas que hacer, 
            y, en lo menos posible, que dependan de otros para poder avanzar. La posibilidad de trabajar de manera simultánea es una gran habilidad 
            cuando se trabaja con grupos y tu la dominas a la perfección.
            
            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas. Todos los nombres, descripciones y contenidos deben estar en español.""",
            tools=[],  # Sin herramientas - usar solo LLM principal
            llm=self.disenador_llm,  # Modelo específico para diseño de actividades
            verbose=True,
            allow_delegation=False  # Desactivar delegación para evitar errores
        )
        # Agente Analizador de Perfiles
        self.agente_perfiles = Agent(
            role="Especialista en Análisis de Perfiles Educativos",
            goal="Analizar perfiles de estudiantes y identificar necesidades específicas para actividades educativas",
            backstory="""Eres un psicopedagogo experto con 15 años de experiencia en educación inclusiva. 
            Tu especialidad es analizar perfiles de estudiantes con diversas necesidades educativas (TEA, TDAH, 
            altas capacidades) y determinar las mejores estrategias de adaptación para cada caso. Puedes adaptar cualquier actividad que te proponga
            a cualquier grupo gracias a una capacidad innata para solucionar problemas complejos y encontrar soluciones creativas. ¿Como puedo conseguir que este 
            estudiante que tiene parálisis cerebral y no puede mover las manos consiga despegar una pegatina? Ok! puedo dejarle la pegatina ya un pelín despegada y poner 
            la hoja en un atril rígido para que pueda llevarla hasta ahí. 
            Una de tus grandes especialidades es que eres capaz de hacer las adaptaciones sin que ni siquiera se note que estás adaptando nada. Por ejemplo, tengo una niña TEA que necesita apoyo
            visual para una actividad, pues la actividad tendrá unas instrucciones para llevarse a cabo que precisamente realizará esta niña. Así, puede construirse su propio apoyo visual 
            mientras repasa todo el proceso y le ayuda a reducir la ansiedad que le genera no saber qué hacer. Este apoyo servirá para toda la clase y podremos
            observar también si otras personas lo precisan y no contábamos con ello.
            La inclusividad de la actividad ha de estar en la base de la misma y no aparecer como parches añadidos para que parezca que se está adaptando nada. 
            Tu capacidad de adaptación reside en tu experiencia y creatividad para dar solución a cada situación. 
            
            Conoces perfectamente a estos 8 estudiantes del AULA_A_4PRIM y puedes analizar su diversidad sin necesidad de herramientas externas.
            
            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas.""",
            tools=[],  # Sin herramientas por ahora, información directa
            llm=self.perfiles_llm,  # Modelo específico para análisis de perfiles
            verbose=True,
            allow_delegation=False
        )
        
        
        # Agente Evaluador de Calidad
        self.agente_evaluador = Agent(
            role="Evaluador de Calidad Educativa",
            goal="Revisar y mejorar las actividades generadas asegurando que cumplan con estándares pedagógicos",
            backstory="""Eres un supervisor educativo con amplia experiencia en evaluación de materiales 
            didácticos. Tu rol es asegurar que las actividades cumplan con los objetivos curriculares, 
            sean inclusivas, apropiadas para la edad y nivel, y respeten las adaptaciones necesarias. 
            Tienes conocimiento profundo del currículo de 4º de Primaria.
            
            IMPORTANTE: Siempre responde en ESPAÑOL. Nunca uses inglés en tus respuestas. Todas las evaluaciones y recomendaciones deben estar en español.""",
            tools=[],  # Sin herramientas de archivo por ahora
            llm=self.evaluador_llm,  # Modelo específico para evaluación
            verbose=True,
            allow_delegation=False
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
            agent=self.agente_perfiles,
            expected_output="Análisis detallado de la diversidad del aula con estrategias específicas"
        )
        
        tarea_diseno_base = Task(
            description=f"""Basándote en el análisis de diversidad, diseña la estructura base de una actividad de {materia} {f'sobre {tema}' if tema else ''} que:
            1. Sea apropiada para 4º de Primaria
            2. Permita trabajo ambiente
            3. Incluya múltiples canales de aprendizaje (visual, auditivo, kinestésico)
            4. Tenga flexibilidad para adaptaciones
            5. Genere un producto final significativo
            
            Diseña:
            - Título y objetivos pedagógicos
            - Descripción general de la actividad
            - Proceso paso a paso
            - Materiales necesarios
            - Criterios de evaluación
            - Duración estimada
            
            IMPORTANTE: 
            - Enfocate en la estructura y contenido pedagógico, no en roles específicos (eso lo hará otro agente)
            - Responde únicamente en ESPAÑOL. No uses palabras en inglés
            - Todos los títulos, descripciones y materiales deben estar en español""",
            agent=self.agente_disenador,
            expected_output="Diseño estructural de actividad educativa lista para coordinación colaborativa"
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
                        agent=self.agente_ambiente,
            expected_output="Coordinación colaborativa con roles específicos y estrategias de inclusión"
        )
        
        tarea_revision_colaborativa = Task(
            description="""Revisa la actividad colaborativa y verifica que:
            1. Todos los estudiantes tienen roles significativos y apropiados
            2. Las adaptaciones para necesidades especiales están incluidas
            3. La interdependencia es auténtica (no artificial)
            4. El producto final justifica la colaboración
            5. Los objetivos curriculares se cumplen
            6. La evaluación es justa para todos
            
            Proporciona recomendaciones específicas para optimizar la colaboración.
            
            IMPORTANTE: Responde únicamente en ESPAÑOL. Todas las evaluaciones y recomendaciones deben estar en español.""",
            agent=self.agente_evaluador,
            expected_output="Evaluación y optimización de la actividad colaborativa"
        )
        
        # Crear y ejecutar el crew ambiente con los 4 agentes
        crew = Crew(
            agents=[self.agente_ambiente, self.agente_disenador, self.agente_perfiles, self.agente_evaluador],
            tasks=[tarea_analisis_aula, tarea_diseno_base, tarea_coordinacion_colaborativa, tarea_revision_colaborativa],
            process=Process.sequential,
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
                
                contenido_completo += "=== EVALUACIÓN Y OPTIMIZACIÓN ===\n"
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
        OLLAMA_HOST = "localhost"  # Ollama local
        PERFILES_MODEL = "llama3:latest"     # Modelo para análisis de perfiles
        DISENADOR_MODEL = "llama3:latest"    # Modelo para diseño de actividades  
        ambiente_MODEL = "llama3:latest" # Modelo para coordinación colaborativa
        EVALUADOR_MODEL = "llama3:latest"    # Modelo para evaluación
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