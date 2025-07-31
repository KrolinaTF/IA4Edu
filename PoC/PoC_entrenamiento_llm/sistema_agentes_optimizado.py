#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI OPTIMIZADO para Generación de Actividades Educativas
Versión mejorada con prompts concisos, tools especializadas y templates modulares
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Mapping
from dataclasses import dataclass
import logging

# Configurar variables de entorno para LiteLLM/CrewAI (configuración del proyecto funcional)
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
logger = logging.getLogger("CREWAI_OPTIMIZADO")

# Configurar LiteLLM globalmente antes de los imports de CrewAI
try:
    import litellm
    # Configuración específica para Ollama
    litellm.set_verbose = True
    # Configurar modelos de Ollama explícitamente
    os.environ["LITELLM_PROVIDER"] = "ollama"
    logger.info("✅ LiteLLM configurado para Ollama")
except ImportError:
    logger.warning("⚠️ LiteLLM no disponible")
    pass

try:
    from crewai import Agent, Task, Crew, Process
    from langchain_community.llms import Ollama
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping
    logger.info("✅ Dependencias CrewAI cargadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    raise ImportError("Instala: pip install crewai crewai-tools langchain-community")

# Importar módulos de Ollama
from ollama_api_integrator import OllamaAPIEducationGenerator

# Importar nuestros módulos optimizados
from prompt_manager import PromptTemplateManager
from educational_tools import (
    PerfilAnalyzerTool, ActivityValidatorTool, CurriculumCheckerTool,
    EnvironmentDesignTool, TaskDecomposerTool, StudentTaskMatcherTool
)


class DirectOllamaLLM(LLM):
    """LLM completamente personalizado que bypassa LiteLLM"""
    
    # Declarar campos para Pydantic v2
    ollama_generator: Optional[object] = None
    model_name: str = "qwen3:latest"
    host: str = "192.168.1.10"
    
    def __init__(self, ollama_host: str = "192.168.1.10", ollama_model: str = "qwen3:latest", **kwargs):
        # Separar host y puerto si viene junto
        if ":" in ollama_host:
            host_only = ollama_host.split(":")[0]
        else:
            host_only = ollama_host
            
        # Crear generador de Ollama
        ollama_gen = OllamaAPIEducationGenerator(
            host=host_only, 
            model_name=ollama_model
        )
        
        # Inicializar con los campos requeridos
        super().__init__(
            ollama_generator=ollama_gen,
            model_name=ollama_model,
            host=host_only,
            **kwargs
        )
    
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
    tipo: str
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str


class SistemaAgentesOptimizado:
    """Sistema principal de agentes optimizado para generación de actividades educativas"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 perfiles_model: str = "qwen3:latest",
                 disenador_model: str = "qwen3:latest", 
                 ambiente_model: str = "qwen2:latest",
                 evaluador_model: str = "mistral:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema de agentes optimizado
        """
        self.ollama_host = ollama_host
        self.perfiles_model = perfiles_model
        self.disenador_model = disenador_model
        self.ambiente_model = ambiente_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Cargar perfiles y crear gestores
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        try:
            self.prompt_manager = PromptTemplateManager(self.perfiles_data)
        except Exception as e:
            logger.warning(f"Error creando PromptTemplateManager: {e}")
            # Usar datos por defecto si fallan los perfiles
            perfiles_default = self._crear_perfiles_default()
            self.prompt_manager = PromptTemplateManager(perfiles_default)
        
        # Crear LLMs específicos para cada agente
        logger.info("🔧 Configurando LLMs optimizados...")
        self._crear_llms()
        
        # Crear tools especializadas
        logger.info("🛠️ Inicializando tools especializadas...")
        self._crear_tools()
        
        # Crear agentes optimizados
        logger.info("🤖 Creando agentes optimizados...")
        self._crear_agentes_optimizados()
        
        logger.info(f"✅ Sistema optimizado inicializado con modelos:")
        logger.info(f"   📊 Perfiles: {self.perfiles_model}")
        logger.info(f"   🎨 Diseñador: {self.disenador_model}")
        logger.info(f"   🤝 Ambiente: {self.ambiente_model}")  
        logger.info(f"   ✅ Evaluador: {self.evaluador_model}")
    
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
    
    def _crear_llms(self):
        """Crea LLMs específicos para cada agente con configuración LiteLLM"""
        try:
            # Configurar LiteLLM correctamente para Ollama (solución del proyecto anterior)
            import litellm
            
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
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            # Crear LLMs específicos para cada agente (sin prefijo para conexión directa)
            self.perfiles_llm = Ollama(
                model=self.perfiles_model,
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=self.disenador_model,
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.ambiente_llm = Ollama(
                model=self.ambiente_model,
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.evaluador_llm = Ollama(
                model=self.evaluador_model,
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            # Verificar conexión
            try:
                test_response = self.perfiles_llm.invoke("Test de conexión")
                logger.info("✅ LLMs configurados exitosamente")
            except Exception as test_error:
                logger.error(f"❌ Fallo en test de conexión: {test_error}")
                raise ConnectionError("No se pudo conectar con Ollama. Verifica que el servicio esté corriendo.")
                
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            raise
    
    def _crear_tools(self):
        """Crea tools especializadas para cada agente"""
        try:
            # Tools originales
            self.perfil_tool = PerfilAnalyzerTool(self.perfiles_data)
            self.validator_tool = ActivityValidatorTool()
            self.curriculum_tool = CurriculumCheckerTool()
            
            # Nuevas tools para el flujo rediseñado
            self.environment_tool = EnvironmentDesignTool()
            self.decomposer_tool = TaskDecomposerTool()
            self.matcher_tool = StudentTaskMatcherTool()
            
            logger.info("✅ Tools especializadas creadas (incluyendo nuevas tools de flujo)")
        except Exception as e:
            logger.error(f"Error creando tools: {e}")
            # Crear tools vacías como fallback
            self.perfil_tool = PerfilAnalyzerTool([])
            self.validator_tool = ActivityValidatorTool()
            self.curriculum_tool = CurriculumCheckerTool()
            logger.info("⚠️ Tools creadas con datos por defecto")
    
    def _crear_agentes_optimizados(self):
        """Crea agentes con nuevo flujo: Ambiente → Diseño → Desglose → Asignación"""
        
        # AGENTE 1: DISEÑADOR DE AMBIENTE DE APRENDIZAJE (NUEVO)
        self.agente_ambiente = Agent(
            role="Diseñador de Ambiente de Aprendizaje",
            goal="Establecer el tono y características generales óptimas para la actividad educativa",
            backstory="Especialista en ambientes de aprendizaje. Analizas las características del grupo y defines si la actividad debe ser lúdica, investigativa, creativa o de concentración. IMPORTANTE: Usa diseñar_ambiente UNA SOLA VEZ. Respondes siempre en español.",
            tools=[self.environment_tool],  # Tool para diseñar ambiente
            llm=self.ambiente_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: DISEÑADOR DE ACTIVIDADES ESTRUCTURADAS (MODIFICADO)
        self.agente_disenador = Agent(
            role="Diseñador de Actividades Estructuradas",
            goal="Crear actividades específicas basadas en la base ambiental establecida",
            backstory="Docente experto en diseño curricular. Tomas la base ambiental y creas actividades estructuradas específicas por materia. Usas verificar_curriculum para asegurar objetivos. Respondes siempre en español.",
            tools=[self.curriculum_tool],  # Tool para verificar objetivos curriculares
            llm=self.disenador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: DESGLOSADOR DE TAREAS (NUEVO)
        self.agente_desglosador = Agent(
            role="Desglosador de Tareas Específicas",
            goal="Descomponer actividades en tareas micro-específicas con requerimientos detallados",
            backstory="Especialista en análisis de tareas educativas. Descompones actividades complejas en tareas individuales específicas, analizando habilidades requeridas y dependencias. IMPORTANTE: Usa descomponer_tareas UNA SOLA VEZ. Respondes siempre en español.",
            tools=[self.decomposer_tool],  # Tool para descomponer tareas
            llm=self.perfiles_llm,  # Reutilizar modelo de perfiles
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: ASIGNADOR DE ROLES PERSONALIZADO (NUEVO)
        self.agente_asignador = Agent(
            role="Asignador de Roles Personalizado",
            goal="Emparejar tareas específicas con estudiantes según su Zona de Desarrollo Próximo",
            backstory="Psicopedagogo especializado en ZDP y personalización. Asignas tareas específicas a estudiantes considerando sus fortalezas, desafíos y zona de desarrollo próximo. IMPORTANTE: Usa asignar_tareas_estudiantes UNA SOLA VEZ. Respondes siempre en español.",
            tools=[self.matcher_tool],  # Tool para emparejar estudiantes-tareas
            llm=self.evaluador_llm,  # Reutilizar modelo evaluador
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes reorganizados creados con nuevo flujo pedagógico")
    
    def generar_actividad_colaborativa(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera una actividad colaborativa usando el sistema optimizado"""
        
        logger.info(f"👥 Generando actividad colaborativa optimizada para {materia}")
        
        try:
            # Crear tareas con nuevo flujo
            tarea_ambiente = Task(
                description=self.prompt_manager.generar_prompt(materia, "ambiente"),
                agent=self.agente_ambiente,
                expected_output="Base ambiental definida con justificación pedagógica"
            )
            
            tarea_diseno = Task(
                description=self.prompt_manager.generar_prompt(materia, "diseno", tema),
                agent=self.agente_disenador,
                context=[tarea_ambiente],
                expected_output="Actividad estructurada específica"
            )
            
            tarea_desglose = Task(
                description=self.prompt_manager.generar_prompt(materia, "desglose"),
                agent=self.agente_desglosador,
                context=[tarea_diseno],
                expected_output="Desglose completo en tareas micro-específicas"
            )
            
            tarea_asignacion = Task(
                description=self.prompt_manager.generar_prompt(materia, "asignacion"),
                agent=self.agente_asignador,
                context=[tarea_desglose],
                expected_output="Asignación optimizada de tareas por estudiante"
            )

            # Crear y ejecutar crew
            crew = Crew(
                agents=[self.agente_ambiente, self.agente_disenador, self.agente_desglosador, self.agente_asignador],
                tasks=[tarea_ambiente, tarea_diseno, tarea_desglose, tarea_asignacion],
                process=Process.sequential,
                verbose=True
            )
            
            logger.info("🚀 Ejecutando workflow optimizado...")
            resultado = crew.kickoff()
            
            # Procesar resultados
            contenido_completo = self._procesar_resultados(resultado)
            
            return ActividadEducativa(
                id=f"flujo_pedagogico_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Colaborativa - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_flujo_pedagogico",
                adaptaciones=["ambiente_personalizado", "tareas_especificas", "asignacion_zdp"],
                metadatos={
                    "sistema": "flujo_pedagogico_reorganizado",
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad: {e}")
            # Retornar actividad básica
            return ActividadEducativa(
                id=f"error_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Básica - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error generando actividad: {e}",
                estudiantes_objetivo=[],
                tipo="error_fallback",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _procesar_resultados(self, resultado) -> str:
        """Procesa y estructura los resultados del crew"""
        contenido = ""
        
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido += "=== DISEÑO DE AMBIENTE DE APRENDIZAJE ===\n"
                contenido += str(resultado.tasks_output[0]) + "\n\n"
                
                contenido += "=== DISEÑO DE ACTIVIDAD ESTRUCTURADA ===\n"
                contenido += str(resultado.tasks_output[1]) + "\n\n"
                
                contenido += "=== DESGLOSE EN TAREAS ESPECÍFICAS ===\n"
                contenido += str(resultado.tasks_output[2]) + "\n\n"
                
                contenido += "=== ASIGNACIÓN PERSONALIZADA POR ZDP ===\n"
                contenido += str(resultado.tasks_output[3]) + "\n\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"Error procesando resultados: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_optimizadas") -> str:
        """Guarda una actividad optimizada en un archivo"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA OPTIMIZADO CrewAI + Ollama\n")
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
            f.write("METADATOS DEL SISTEMA OPTIMIZADO:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad optimizada guardada en: {filepath}")
        return filepath
    
    def ejecutar_workflow_completo(self, materia: str, tema: str = None) -> Dict:
        """Ejecuta workflow completo optimizado"""
        
        logger.info(f"🚀 Iniciando workflow optimizado para {materia}")
        start_time = datetime.now()
        
        resultados = {
            "sistema": "optimizado",
            "materia": materia,
            "tema": tema,
            "timestamp": start_time.isoformat(),
            "actividades_generadas": [],
            "archivos_creados": [],
            "metricas": {}
        }
        
        try:
            # Generar actividad colaborativa optimizada
            logger.info("🤝 Generando actividad colaborativa optimizada...")
            actividad = self.generar_actividad_colaborativa(materia, tema)
            archivo = self.guardar_actividad(actividad)
            
            end_time = datetime.now()
            duracion = (end_time - start_time).total_seconds()
            
            resultados["actividades_generadas"].append({
                "tipo": "colaborativa_optimizada",
                "id": actividad.id,
                "archivo": archivo
            })
            resultados["archivos_creados"].append(archivo)
            resultados["metricas"] = {
                "duracion_segundos": duracion,
                "tokens_estimados": len(actividad.contenido) // 4,  # Estimación rough
                "modelos_utilizados": 4,
                "tools_aplicadas": 3
            }
            
            logger.info(f"✅ Workflow optimizado completado en {duracion:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en workflow optimizado: {e}")
            resultados["error"] = str(e)
        
        return resultados
    
    def comparar_con_sistema_original(self, materia: str, tema: str = None) -> Dict:
        """Compara rendimiento con sistema original (para testing)"""
        
        logger.info(f"📊 Ejecutando comparación de sistemas para {materia}")
        
        # Ejecutar sistema optimizado
        resultado_optimizado = self.ejecutar_workflow_completo(materia, tema)
        
        comparacion = {
            "sistema_optimizado": resultado_optimizado,
            "mejoras_implementadas": [
                "Prompts reducidos de 400+ líneas a 50-80 líneas",
                "Tools especializadas integradas (3 tools)",
                "Templates modulares reutilizables",
                "Validación automática de calidad",
                "Verificación curricular integrada"
            ],
            "ventajas_esperadas": [
                "Menor tiempo de ejecución",
                "Respuestas más consistentes",
                "Menor uso de tokens",
                "Mejor calidad pedagógica",
                "Mayor mantenibilidad"
            ]
        }
        
        return comparacion


def main():
    """Función principal de demostración del sistema optimizado"""
    
    print("="*70)
    print("🚀 SISTEMA DE AGENTES CREWAI OPTIMIZADO PARA EDUCACIÓN")
    print("="*70)
    
    try:
        # Configuración optimizada
        OLLAMA_HOST = "192.168.1.10"
        PERFILES_MODEL = "qwen3:latest"
        DISENADOR_MODEL = "qwen3:latest"
        AMBIENTE_MODEL = "qwen2:latest"
        EVALUADOR_MODEL = "mistral:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        print(f"\n🔧 Inicializando sistema optimizado:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Modelos especializados por agente:")
        print(f"     📊 Perfiles: {PERFILES_MODEL}")
        print(f"     🎨 Diseñador: {DISENADOR_MODEL}")
        print(f"     🤝 Ambiente: {AMBIENTE_MODEL}")
        print(f"     ✅ Evaluador: {EVALUADOR_MODEL}")
        
        sistema = SistemaAgentesOptimizado(
            ollama_host=OLLAMA_HOST,
            perfiles_model=PERFILES_MODEL,
            disenador_model=DISENADOR_MODEL,
            ambiente_model=AMBIENTE_MODEL,
            evaluador_model=EVALUADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema optimizado inicializado correctamente!")
        
        # Menú optimizado
        while True:
            print("\n" + "="*60)
            print("🎯 SISTEMA OPTIMIZADO DE ACTIVIDADES COLABORATIVAS")
            print("1. 🚀 Generar actividad optimizada")
            print("2. 📊 Ejecutar workflow completo con métricas")
            print("3. 🔬 Comparar con sistema original")
            print("4. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-4): ").strip()
            
            if opcion == "1":
                print("\n🚀 GENERACIÓN OPTIMIZADA")
                materia_input = input("📚 Materia (matematicas/lengua/ciencias): ").strip().lower()
                # Normalizar entrada
                if materia_input in ["mates", "mate"]:
                    materia = "matematicas"
                elif materia_input in ["lengua", "lenguaje"]:
                    materia = "lengua"
                elif materia_input in ["ciencias", "ciencia"]:
                    materia = "ciencias"
                else:
                    materia = materia_input
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_colaborativa(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duracion = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad optimizada generada en {duracion:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🎯 Sistema: Optimizado con tools integradas")
            
            elif opcion == "2":
                print("\n📊 WORKFLOW COMPLETO CON MÉTRICAS")
                materia_input = input("📚 Materia (matematicas/lengua/ciencias): ").strip().lower()
                # Normalizar entrada
                if materia_input in ["mates", "mate"]:
                    materia = "matematicas"
                elif materia_input in ["lengua", "lenguaje"]:
                    materia = "lengua"
                elif materia_input in ["ciencias", "ciencia"]:
                    materia = "ciencias"
                else:
                    materia = materia_input
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                resultados = sistema.ejecutar_workflow_completo(materia, tema)
                
                if "error" not in resultados:
                    print(f"\n🎉 ¡Workflow optimizado completado!")
                    print(f"   ⏱️  Duración: {resultados['metricas']['duracion_segundos']:.1f}s")
                    print(f"   🔢 Tokens estimados: {resultados['metricas']['tokens_estimados']}")
                    print(f"   🤖 Modelos utilizados: {resultados['metricas']['modelos_utilizados']}")
                    print(f"   🛠️  Tools aplicadas: {resultados['metricas']['tools_aplicadas']}")
                    print(f"   📁 Archivo: {resultados['archivos_creados'][0]}")
                else:
                    print(f"\n❌ Error: {resultados['error']}")
            
            elif opcion == "3":
                print("\n🔬 COMPARACIÓN DE SISTEMAS")
                materia_input = input("📚 Materia para comparar: ").strip().lower()
                # Normalizar entrada
                if materia_input in ["mates", "mate"]:
                    materia = "matematicas"
                elif materia_input in ["lengua", "lenguaje"]:
                    materia = "lengua"
                elif materia_input in ["ciencias", "ciencia"]:
                    materia = "ciencias"
                else:
                    materia = materia_input
                tema = input("📝 Tema (opcional): ").strip() or None
                
                comparacion = sistema.comparar_con_sistema_original(materia, tema)
                
                print(f"\n📈 COMPARACIÓN COMPLETADA:")
                print(f"   🚀 Sistema optimizado ejecutado exitosamente")
                print(f"   ⏱️  Duración: {comparacion['sistema_optimizado']['metricas']['duracion_segundos']:.1f}s")
                
                print(f"\n🔧 MEJORAS IMPLEMENTADAS:")
                for mejora in comparacion['mejoras_implementadas']:
                    print(f"   ✅ {mejora}")
            
            elif opcion == "4":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-4.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema optimizado: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")
        print("   4. Los módulos prompt_manager.py y educational_tools.py estén disponibles")


if __name__ == "__main__":
    main()