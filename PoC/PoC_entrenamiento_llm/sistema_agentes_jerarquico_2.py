#!/usr/bin/env python3

"""
Sistema de Agentes CrewAI JERÁRQUICO para Generación de Actividades Educativas
Versión con estructura jerárquica y coordinador general
"""

from typing import List, Dict
from dataclasses import dataclass
import logging
import os
import json
from datetime import datetime

# Configuración básica
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CREWAI_JERARQUICO")

# Configurar entorno
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

try:
    from crewai import Agent, Task, Crew, Process
    from langchain_ollama.llms import OllamaLLM
except ImportError as e:
    logger.error(f"Error de importación: {e}")
    raise

@dataclass
class ActividadEducativa:
    """Estructura para actividades educativas"""
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

class SistemaJerarquico:
    """Sistema con estructura jerárquica de agentes"""
    def __init__(self, ollama_host: str = "192.168.1.10"):
        self.ollama_host = ollama_host
        self.base_url = f"http://{self.ollama_host}:11434"

        # Instancias LLM directas a Ollama usando la clase actual
        self.llm_qwen3 = OllamaLLM(model="ollama/qwen3", base_url=self.base_url, temperature=0.7)
        self.llm_qwen2 = OllamaLLM(model="ollama/qwen2", base_url=self.base_url, temperature=0.7)
        self.llm_mistral = OllamaLLM(model="ollama/mistral", base_url=self.base_url, temperature=0.7)

        self._crear_agentes_jerarquicos()
        # Crear directorio para actividades si no existe (ruta absoluta)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.directorio_actividades = os.path.join(script_dir, "actividades_jerarquicas")
        os.makedirs(self.directorio_actividades, exist_ok=True)
        
        logger.info("✅ Sistema jerárquico inicializado")

    def _crear_agentes_jerarquicos(self):
        """Crea la estructura jerárquica de agentes"""
        self.coordinador = Agent(
            role="Coordinador General Educativo",
            goal="Supervisar y coordinar todo el proceso de diseño de actividades educativas",
            backstory="""Experto en pedagogía y gestión educativa esperas de las actividades que estén perfectamente definidas, de manera que
            el docente tenga claro qué hace cada quien en cada momento y que el flujo de actividad discurre de manera fluida.
            Además, estas deberán estar correctamente ajustadas a los perfiles de los alumnos tanto en aspectos curriculares como adaptaciones""",
            llm=self.llm_qwen3,
            verbose=True,
            allow_delegation=True
        )

        self.director_diseno = Agent(
            role="Director de Diseño Educativo",
            goal="Supervisar el diseño completo de la actividad educativa",
            backstory="""Especialista en diseño curricular y pedagógico, encargado de asegurar que todas las actividades 
            estén alineadas con los objetivos educativos y las necesidades de los estudiantes""",
            llm=self.llm_qwen3,
            verbose=True,
            allow_delegation=True
        )

        self.disenador_ambiente = Agent(
            role="Diseñador de Ambientes de Aprendizaje",
            goal="Diseñar el ambiente óptimo para la actividad",
            backstory="""Especialista en psicología educativa perfectamente conocedor de que para que el aprendizaje emerja, el ambiente debe ser
            propicio. Sabes que el espacio físico, la distribución de grupos, los materiales disponibles y la atmósfera emocional
            son elementos fundamentales que condicionan el éxito de cualquier actividad educativa. Tu experiencia te permite diseñar
            ambientes que fomenten la colaboración, reduzcan la ansiedad y maximicen las oportunidades de aprendizaje para todos
            los estudiantes, independientemente de sus características individuales.""",
            llm=self.llm_qwen2,
            verbose=True
        )

        self.disenador_actividades = Agent(
            role="Diseñador de Actividades Educativas",
            goal="Crear actividades educativas efectivas",
            backstory="""Pedagogo especializado en experiencias de aprendizaje colaborativo con más de 15 años de experiencia diseñando actividades
            que integran teoría y práctica. Dominas las metodologías activas, el aprendizaje basado en proyectos y las estrategias
            de trabajo cooperativo. Tu enfoque se centra en crear experiencias significativas que conecten con los intereses de los
            estudiantes y promuevan el desarrollo de competencias tanto académicas como socioemocionales. Eres experto en graduar
            la dificultad y crear secuencias didácticas que mantengan la motivación y el engagement de todos los participantes.""",
            llm=self.llm_qwen3,
            verbose=True
        )

        self.especialista_adaptaciones = Agent(
            role="Especialista en Adaptaciones Educativas",
            goal="Asegurar que las actividades sean inclusivas",
            backstory="""Experto en educación inclusiva con profundo conocimiento del Diseño Universal para el Aprendizaje (DUA).
            Tu especialidad es identificar las barreras de aprendizaje y proponer adaptaciones específicas que permitan la
            participación efectiva de todos los estudiantes. Conoces las necesidades educativas especiales más comunes,
            las estrategias de diferenciación curricular y las tecnologías de apoyo. Tu objetivo es que ningún estudiante
            quede excluido del proceso de aprendizaje, garantizando múltiples formas de representación, expresión y
            participación según los principios del DUA.""",
            llm=self.llm_mistral,
            verbose=True
        )

        self.planificador_tareas = Agent(
            role="Planificador de Tareas Educativas",
            goal="Descomponer actividades en tareas ejecutables",
            backstory="""Experto en análisis de tareas educativas y secuenciación didáctica. Tu especialidad es descomponer actividades
            complejas en tareas específicas, concretas y ejecutables, estableciendo tiempos realistas, dependencias entre tareas
            y criterios de evaluación claros. Dominas las técnicas de scaffolding (andamiaje) para estructurar el apoyo que
            necesitan los estudiantes en cada fase del proceso. Tu enfoque metodológico asegura que cada tarea tenga un propósito
            claro, contribuya al objetivo global del aprendizaje y sea apropiada para el nivel de desarrollo de los estudiantes.""",
            llm=self.llm_qwen3,
            verbose=True
        )

        self.asignador_roles = Agent(
            role="Asignador de Roles Educativos",
            goal="Asignar roles a estudiantes según sus características",
            backstory="""Conocedor profundo de las necesidades individuales de los estudiantes y experto en asignación estratégica de roles.
            Tu experiencia te permite analizar los perfiles de cada estudiante (fortalezas, áreas de mejora, estilos de aprendizaje,
            motivaciones) para asignar roles que potencien sus capacidades y les ayuden a superar sus dificultades. Entiendes que
            los roles no son estáticos y pueden rotar para favorecer el desarrollo integral. Tu objetivo es crear equipos
            equilibrados donde cada estudiante se sienta valorado, tenga oportunidades de liderazgo y pueda aprender de sus
            compañeros a través de la interdependencia positiva.""",
            llm=self.llm_mistral,
            verbose=True
        )

        logger.info("✅ Estructura jerárquica de agentes creada")
    
    def _guardar_actividad(self, actividad: ActividadEducativa):
        """Guarda la actividad en un archivo de texto"""
        try:
            nombre_archivo = f"{actividad.id}.txt"
            ruta_archivo = os.path.join(self.directorio_actividades, nombre_archivo)
            
            # Debug: mostrar rutas
            logger.info(f"🔍 Directorio: {self.directorio_actividades}")
            logger.info(f"🔍 Archivo: {nombre_archivo}")
            logger.info(f"🔍 Ruta completa: {ruta_archivo}")
            logger.info(f"🔍 Directorio existe: {os.path.exists(self.directorio_actividades)}")
            
            # Asegurar que el directorio existe
            os.makedirs(self.directorio_actividades, exist_ok=True)
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"ACTIVIDAD EDUCATIVA JERÁRQUICA\n")
                f.write(f"="*50 + "\n\n")
                f.write(f"ID: {actividad.id}\n")
                f.write(f"Título: {actividad.titulo}\n")
                f.write(f"Materia: {actividad.materia}\n")
                f.write(f"Tema: {actividad.tema}\n")
                f.write(f"Tipo: {actividad.tipo}\n")
                f.write(f"Timestamp: {actividad.timestamp}\n")
                f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
                f.write(f"Adaptaciones: {', '.join(actividad.adaptaciones)}\n\n")
                f.write(f"CONTENIDO DE LA ACTIVIDAD:\n")
                f.write(f"="*50 + "\n")
                f.write(actividad.contenido)
                f.write(f"\n\n" + "="*50 + "\n")
                f.write(f"METADATOS:\n{json.dumps(actividad.metadatos, indent=2, ensure_ascii=False)}\n")
            
            logger.info(f"✅ Actividad guardada en: {ruta_archivo}")
            print(f"📁 Actividad guardada en: {ruta_archivo}")
            
        except Exception as e:
            logger.error(f"Error guardando actividad: {e}")
            print(f"❌ Error guardando actividad: {e}")

    def generar_actividad(self, materia: str, tema: str = None) -> ActividadEducativa:
        logger.info(f"🚀 Iniciando generación de actividad para {materia}")
        try:
            tarea_ambiente = Task(
                description=f"""Diseña el ambiente físico y emocional óptimo para una actividad colaborativa de {materia} sobre {tema or 'un tema general'}.
                Considera: 1) Distribución del espacio físico (agrupaciones, movilidad, zonas de trabajo), 2) Materiales y recursos necesarios,
                3) Condiciones ambientales (iluminación, ruido, temperatura), 4) Estrategias para crear un clima emocional seguro y motivador,
                5) Elementos que fomenten la participación de todos los estudiantes. El ambiente debe facilitar la colaboración,
                minimizar distracciones y ser accesible para estudiantes con diferentes necesidades.""",
                agent=self.disenador_ambiente,
                expected_output="Descripción detallada del ambiente con especificaciones físicas, materiales y estrategias emocionales"
            )

            tarea_actividad = Task(
                description=f"""Diseña una actividad colaborativa completa para {materia} sobre {tema or 'un tema general'} que integre:
                1) Objetivos de aprendizaje claros y específicos, 2) Metodología activa y participativa, 3) Secuencia didáctica estructurada,
                4) Estrategias de trabajo cooperativo, 5) Elementos de gamificación o motivación, 6) Conexión con situaciones reales,
                7) Oportunidades para el desarrollo de competencias transversales. La actividad debe ser significativa, desafiante
                pero alcanzable, y promover tanto el aprendizaje individual como el grupal. Incluye criterios de evaluación formativa.""",
                agent=self.disenador_actividades,
                expected_output="Actividad educativa completa con objetivos, metodología, secuencia didáctica y evaluación"
            )

            tarea_adaptaciones = Task(
                description="""Analiza la actividad propuesta y diseña adaptaciones específicas siguiendo los principios del DUA:
                1) Múltiples formas de representación (visual, auditiva, táctil), 2) Múltiples formas de expresión y participación,
                3) Múltiples formas de motivación y engagement. Considera adaptaciones para: estudiantes con dificultades de aprendizaje,
                altas capacidades, diversidad cultural y lingüística, necesidades sensoriales o motoras. Propón alternativas concretas
                para materiales, instrucciones, tiempos, productos finales y formas de participación. Asegura que las adaptaciones
                mantengan el rigor académico y permitan alcanzar los mismos objetivos de aprendizaje.""",
                agent=self.especialista_adaptaciones,
                expected_output="Lista detallada de adaptaciones organizadas por principios DUA con alternativas específicas",
                context=[tarea_actividad]
            )

            tarea_desglose = Task(
                description="""Descompone la actividad en tareas específicas, secuenciadas y ejecutables:
                1) Identifica las macro-tareas principales, 2) Subdivide cada macro-tarea en micro-tareas concretas,
                3) Establece tiempos estimados realistas, 4) Define dependencias entre tareas, 5) Especifica recursos necesarios,
                6) Determina puntos de control y retroalimentación, 7) Incluye momentos de reflexión y metacognición.
                Cada tarea debe tener: objetivo específico, instrucciones claras, criterios de éxito, duración estimada.
                Considera las adaptaciones propuestas para ajustar tiempos y apoyos adicionales donde sea necesario.""",
                agent=self.planificador_tareas,
                expected_output="Desglose cronológico detallado con tareas específicas, tiempos, recursos y puntos de control",
                context=[tarea_actividad, tarea_adaptaciones]
            )

            tarea_asignacion = Task(
                description="""Asigna roles específicos a cada estudiante basándote en sus perfiles individuales:
                1) Analiza fortalezas, intereses y áreas de mejora de cada estudiante, 2) Diseña roles complementarios que generen
                interdependencia positiva, 3) Asegura rotación de roles para desarrollo integral, 4) Define responsabilidades
                específicas para cada rol, 5) Establece mecanismos de apoyo mutuo, 6) Considera liderazgos distribuidos.
                Roles deben: potenciar fortalezas individuales, ofrecer desafíos apropiados, promover crecimiento en áreas débiles,
                fomentar la colaboración efectiva. Incluye estrategias para resolver conflictos y apoyar a estudiantes con dificultades.""",
                agent=self.asignador_roles,
                expected_output="Asignación personalizada de roles con justificación pedagógica y estrategias de apoyo",
                context=[tarea_desglose]
            )

            tarea_supervision_diseno = Task(
                description="""Supervisa y valida la coherencia del diseño educativo completo:
                1) Verifica alineación entre objetivos, metodología y evaluación, 2) Revisa la integración efectiva del ambiente,
                actividad y adaptaciones, 3) Asegura que el diseño responda a los principios pedagógicos actuales,
                4) Evalúa la viabilidad práctica en el contexto educativo, 5) Identifica posibles mejoras o ajustes necesarios,
                6) Confirma que todos los elementos contribuyen al aprendizaje significativo. Proporciona retroalimentación
                constructiva y recomendaciones específicas para optimizar el diseño antes de la implementación.""",
                agent=self.director_diseno,
                expected_output="Diseño educativo validado con retroalimentación específica y recomendaciones de mejora",
                context=[tarea_ambiente, tarea_actividad, tarea_adaptaciones]
            )

            tarea_supervision_implementacion = Task(
                description="""Supervisa y valida el plan de implementación práctica:
                1) Revisa la secuencia temporal y la viabilidad de los tiempos propuestos, 2) Evalúa la coherencia entre
                la asignación de roles y el desglose de tareas, 3) Identifica posibles obstáculos en la implementación,
                4) Verifica que todos los estudiantes tengan oportunidades equitativas de participación y aprendizaje,
                5) Asegura que existen mecanismos de seguimiento y ajuste durante la implementación, 6) Valida la factibilidad
                de los recursos y materiales necesarios. Proporciona un plan de contingencia para situaciones imprevistas.""",
                agent=self.director_diseno,
                expected_output="Plan de implementación validado con cronograma, seguimiento y contingencias",
                context=[tarea_desglose, tarea_asignacion]
            )

            tarea_coordinacion = Task(
                description="""Coordina y consolida todo el proceso de diseño educativo en una propuesta final:
                1) Integra todos los elementos en una actividad educativa coherente y completa, 2) Asegura que la propuesta
                final sea clara, práctica y directamente implementable por el docente, 3) Verifica que se mantenga el foco
                en los objetivos de aprendizaje y las necesidades de los estudiantes, 4) Consolida todas las adaptaciones
                y estrategias en un formato accesible, 5) Incluye orientaciones claras para el docente sobre implementación,
                seguimiento y evaluación, 6) Proporciona una visión global que permita entender el flujo completo de la actividad.
                La propuesta final debe ser autónoma, completa y lista para implementar en el aula.""",
                agent=self.coordinador,
                expected_output="Actividad educativa completa, integrada y lista para implementación con guía docente",
                context=[tarea_supervision_diseno, tarea_supervision_implementacion]
            )

            crew = Crew(
                agents=[
                    self.director_diseno,
                    self.disenador_ambiente,
                    self.disenador_actividades,
                    self.especialista_adaptaciones,
                    self.planificador_tareas,
                    self.asignador_roles
                ],
                tasks=[
                    tarea_ambiente,
                    tarea_actividad,
                    tarea_adaptaciones,
                    tarea_desglose,
                    tarea_asignacion,
                    tarea_supervision_diseno,
                    tarea_supervision_implementacion,
                    tarea_coordinacion
                ],
                process=Process.hierarchical,
                manager_agent=self.coordinador,
                verbose=True
            )

            logger.info("🏗️ Ejecutando flujo jerárquico...")
            resultado = crew.kickoff()

            actividad = ActividadEducativa(
                id=f"jerarquico_{materia}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad de {materia} - {tema or 'tema general'}",
                materia=materia,
                tema=tema or "tema general",
                contenido=str(resultado),
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_jerarquica",
                adaptaciones=["inclusiva", "diferenciada"],
                metadatos={
                    "sistema": "jerarquico",
                    "niveles": ["coordinacion", "direccion", "especialistas"]
                },
                timestamp=datetime.now().isoformat()
            )
            
            # Guardar actividad en archivo
            self._guardar_actividad(actividad)
            return actividad

        except Exception as e:
            logger.error(f"Error generando actividad: {e}")
            actividad_fallback = self._crear_actividad_fallback(materia, tema, str(e))
            self._guardar_actividad(actividad_fallback)
            return actividad_fallback

    def _crear_actividad_fallback(self, materia: str, tema: str, error: str) -> ActividadEducativa:
        return ActividadEducativa(
            id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad Básica de {materia}",
            materia=materia,
            tema=tema or "tema general",
            contenido=f"Error: {error}\n\nActividad básica de ejemplo.",
            estudiantes_objetivo=[],
            tipo="fallback",
            adaptaciones=[],
            metadatos={"error": error},
            timestamp=datetime.now().isoformat()
        )

def main():
    print("="*60)
    print("🏫 SISTEMA JERÁRQUICO DE DISEÑO EDUCATIVO")
    print("="*60)
    try:
        sistema = SistemaJerarquico()
        while True:
            print("\nOpciones:")
            print("1. Generar actividad educativa")
            print("2. Salir")
            opcion = input("Seleccione una opción: ").strip()
            if opcion == "1":
                materia = input("Materia (matematicas/lengua/ciencias): ").lower()
                tema = input("Tema específico (opcional): ").strip() or None
                actividad = sistema.generar_actividad(materia, tema)
                print("\n" + "="*60)
                print(f"📜 ACTIVIDAD GENERADA - {actividad.titulo}")
                print("="*60)
                print(f"📁 Archivo guardado: {actividad.id}.txt")
                print(f"📂 Directorio: actividades_jerarquicas/")
                print("\n📋 RESUMEN:")
                print(f"Materia: {actividad.materia}")
                print(f"Tema: {actividad.tema}")
                print(f"Tipo: {actividad.tipo}")
                print(f"Estudiantes: {len(actividad.estudiantes_objetivo)}")
                print("\n💡 Puedes encontrar el contenido completo en el archivo generado.")
            elif opcion == "2":
                print("👋 Hasta luego!")
                break
            else:
                print("❌ Opción no válida")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
