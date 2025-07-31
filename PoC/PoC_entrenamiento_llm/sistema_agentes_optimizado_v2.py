#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI OPTIMIZADO para Generación de Actividades Educativas
Versión basada en el archivo funcional con nuevo flujo: Ambiente → Diseño → Desglose → Asignación
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
logger = logging.getLogger("CREWAI_OPTIMIZADO")

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


class SistemaAgentesOptimizado:
    """Sistema principal de agentes optimizado con nuevo flujo pedagógico"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 perfiles_model: str = "qwen3:latest",
                 disenador_model: str = "qwen3:latest", 
                 ambiente_model: str = "qwen2:latest",
                 evaluador_model: str = "mistral:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema de agentes optimizado con nuevo flujo
        """
        self.ollama_host = ollama_host
        self.perfiles_model = perfiles_model
        self.disenador_model = disenador_model
        self.ambiente_model = ambiente_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Modelo general para compatibilidad
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
            logger.info(f"   🤝 Ambiente: {self.ambiente_model}")
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
        
        # Crear agentes optimizados con nuevo flujo
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
    
    def _crear_agentes_optimizados(self):
        """Crea agentes con nuevo flujo: Ambiente → Diseño → Desglose → Asignación"""
        
        # AGENTE 1: DISEÑADOR DE AMBIENTE DE APRENDIZAJE (NUEVO)
        self.agente_ambiente = Agent(
            role="Diseñador de Ambiente de Aprendizaje",
            goal="Establecer el tono y características generales óptimas para la actividad educativa",
            backstory="Especialista en ambientes de aprendizaje. Analizas las características del grupo y defines si la actividad debe ser lúdica, investigativa, creativa o de concentración. Respondes siempre en español.",
            tools=[],
            llm=self.ambiente_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: DISEÑADOR DE ACTIVIDADES ESTRUCTURADAS (MODIFICADO)
        self.agente_disenador = Agent(
            role="Diseñador de Actividades Estructuradas",
            goal="Crear actividades específicas basadas en la base ambiental establecida",
            backstory="Docente experto en diseño curricular. Tomas la base ambiental y creas actividades estructuradas específicas por materia. Respondes siempre en español.",
            tools=[],
            llm=self.disenador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: DESGLOSADOR DE TAREAS (NUEVO)
        self.agente_desglosador = Agent(
            role="Desglosador de Tareas Específicas",
            goal="Descomponer actividades en tareas micro-específicas con requerimientos detallados",
            backstory="Especialista en análisis de tareas educativas. Descompones actividades complejas en tareas individuales específicas, analizando habilidades requeridas y dependencias. Respondes siempre en español.",
            tools=[],
            llm=self.perfiles_llm,  # Reutilizar modelo de perfiles
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: ASIGNADOR DE ROLES PERSONALIZADO (NUEVO)
        self.agente_asignador = Agent(
            role="Asignador de Roles Personalizado",
            goal="Emparejar tareas específicas con estudiantes según su Zona de Desarrollo Próximo",
            backstory="Psicopedagogo especializado en ZDP y personalización. Asignas tareas específicas a estudiantes considerando sus fortalezas, desafíos y zona de desarrollo próximo. Respondes siempre en español.",
            tools=[],
            llm=self.evaluador_llm,  # Reutilizar modelo evaluador
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes optimizados creados con nuevo flujo pedagógico")
    
    def generar_actividad_colaborativa(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera una actividad colaborativa usando el sistema optimizado"""
        
        logger.info(f"👥 Generando actividad colaborativa optimizada para {materia}")
        
        try:
            # Crear tareas con nuevo flujo para actividades completas y precisas
            tarea_ambiente = Task(
                description=f"""Diseña una ACTIVIDAD COMPLETA tipo simulación para {materia} {f'sobre {tema}' if tema else ''}.

GRUPO: 8 estudiantes de 4º Primaria
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

Propón una actividad tipo "Supermercado de Números", "Laboratorio de Ciencias", "Banco de Palabras", etc.

RESPONDE EN ESTE FORMATO:

ACTIVIDAD: [Nombre atractivo]
OBJETIVO_PRINCIPAL: [Qué se aprende]
DURACIÓN: [1-1.5 horas]
NARRATIVA: [Historia/contexto que motiva la actividad]
INSTALACIONES: [Cómo se organiza el aula]
ROLES_NECESARIOS: [3-4 roles principales, ej: cajeros, clientes, supervisor]

La actividad debe permitir que todos trabajen simultáneamente con roles complementarios.""",
                agent=self.agente_ambiente,
                expected_output="Propuesta de actividad completa con narrativa"
            )
            
            tarea_diseno = Task(
                description=f"""Desarrolla completamente la actividad propuesta con TODOS los detalles operativos.

INCLUYE:

=== CONTEXTO PEDAGÓGICO ===
- Competencias curriculares específicas
- Nivel de complejidad matemática/lingüística
- Materiales necesarios exactos

=== ESTRUCTURA DE ROLES ===
Para cada rol especifica:
- Función exacta durante la actividad
- Responsabilidades específicas
- Competencias que desarrolla
- Interacciones con otros roles
- Preparación que necesita
- Entrega final/reporte

=== FUNCIONAMIENTO OPERATIVO ===
- Preparación inicial (primeros 10-15 min)
- Desarrollo principal (1 hora)
- Cierre y verificación (15 min)
- Criterio de finalización
- Control de calidad

=== MATERIALES ESPECÍFICOS ===
- Lista exhaustiva de materiales
- Organización del espacio
- Recursos por rol

Ejemplo: Si hay cajeros, especifica exactamente qué productos, qué precios, cuánto dinero inicial, etc.""",
                agent=self.agente_disenador,
                context=[tarea_ambiente],
                expected_output="Actividad completamente desarrollada con detalles operativos"
            )
            
            tarea_desglose = Task(
                description="""Crea el SISTEMA DE CONTROL MATEMÁTICO Y PEDAGÓGICO de la actividad.

DESARROLLA:

=== CÁLCULOS EXACTOS ===
- Si hay dinero: presupuestos, cambios, totales que cuadren
- Si hay medidas: cantidades exactas, equivalencias
- Si hay problemas: ejercicios graduados por dificultad
- Verificación final matemática (todo debe cuadrar)

=== DIFERENCIACIÓN CONTROLADA ===
- Adaptación automática por niveles
- Complejidad graduada según capacidades
- Materiales de apoyo específicos
- Recursos de autorregulación disponibles

=== GESTIÓN DOCENTE ===
- Rol específico del profesor
- Momentos de intervención individual
- Supervisión general
- Registro de observaciones
- Apoyo en tareas específicas

=== BANCO DE RECURSOS ===
- Zona de autoselección de materiales
- Apoyos visuales, auditivos, kinestésicos
- Materiales de regulación (cascos, plastilina, etc.)
- Estrategias para diferentes perfiles

Todo debe ser matemáticamente exacto y pedagógicamente diferenciado.""",
                agent=self.agente_desglosador,
                context=[tarea_diseno],
                expected_output="Sistema de control matemático y pedagógico completo"
            )
            
            tarea_asignacion = Task(
                description="""Asigna ROL ESPECÍFICO a cada estudiante con ADAPTACIONES EXACTAS.

ESTUDIANTES:
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

PARA CADA ESTUDIANTE ESPECIFICA:

**NOMBRE**: ROL ASIGNADO
- Función específica: [qué hace exactamente]
- Adaptaciones: [apoyos específicos que necesita]
- Complejidad asignada: [nivel matemático/lingüístico]
- Interacciones: [con quién trabaja principalmente]
- Ejemplo concreto: [si es cliente, qué compra exactamente; si es cajero, qué tienda maneja]

EJEMPLO:
**ELENA R.**: CAJERO Tienda 2
- Función específica: Cobrar productos, dar cambio, atender clientes de souvenirs
- Adaptaciones: Cascos disponibles, protocolo visual de interacción, pausas permitidas
- Complejidad asignada: Precios enteros simples, operaciones básicas
- Interacciones: Clientes individuales, supervisor para consultas
- Productos que maneja: Camiseta 16€, Llavero 7€, Imán 4€, Gorra 13€, Postal 2€, Taza 8€

INCLUYE cálculos exactos si es necesario (presupuestos, listas de compra, etc.).""",
                agent=self.agente_asignador,
                context=[tarea_desglose],
                expected_output="Asignación exacta de roles con adaptaciones específicas"
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
                adaptaciones=["ambiente_optimizado", "tareas_micro_especificas", "asignacion_zdp"],
                metadatos={
                    "total_estudiantes": 8,
                    "flujo_pedagogico": ["ambiente", "diseno", "desglose", "asignacion"],
                    "modelos_usados": {
                        "ambiente": self.ambiente_model,
                        "disenador": self.disenador_model,
                        "desglosador": self.perfiles_model,
                        "asignador": self.evaluador_model
                    }
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
                
                contenido += "=== ASIGNACIÓN PERSONALIZADA DE ROLES ===\n"
                contenido += str(resultado.tasks_output[3]) + "\n\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados individuales: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_optimizadas") -> str:
        """Guarda una actividad en un archivo"""
        
        # Asegurar que se guarde en el directorio del script
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


def main():
    """Función principal del sistema optimizado"""
    
    print("="*70)
    print("🚀 SISTEMA DE AGENTES CREWAI OPTIMIZADO PARA EDUCACIÓN")
    print("="*70)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        PERFILES_MODEL = "qwen3:latest"
        DISENADOR_MODEL = "qwen3:latest"
        AMBIENTE_MODEL = "qwen2:latest"
        EVALUADOR_MODEL = "mistral:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        # Inicializar sistema
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
        
        # Menú
        while True:
            print("\n" + "="*50)
            print("🚀 GENERACIÓN OPTIMIZADA")
            print("1. 🎯 Generar actividad con flujo optimizado")
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
                
                print(f"\n✅ Actividad optimizada generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🎯 Sistema: Optimizado con tools integradas")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema optimizado: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")
        print("   4. Los módulos prompt_manager.py y educational_tools.py estén disponibles")


if __name__ == "__main__":
    main()