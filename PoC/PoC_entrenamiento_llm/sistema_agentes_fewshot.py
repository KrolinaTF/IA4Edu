# sistema_agentes_fewshot.py

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from crewai import Agent, Task, Crew, Process
from quantum_enhancer import QuantumEnhancer  # Importa del otro archivo

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("CREWAI_FEWSHOT")

@dataclass
class ActividadEducativa:
    id: str
    titulo: str
    materia: str
    tema: Optional[str]
    contenido: str
    estudiantes_objetivo: List[str]
    tipo: str
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str

# Configuración de Qiskit (debes mantener los detalles aquí SOLO para pasar al QuantumEnhancer)
QISKIT_CONFIG = {
    "backend": "aer_simulator",
    "num_qubits_max": 10,
    "shots": 1024,
    "umbral_validacion": 0.8
}

class SistemaAgentesFewShot:
    def __init__(self,
                 ollama_host: str = "192.168.1.10",
                 inspirador_model: str = "qwen3:latest",
                 pedagogo_model: str = "qwen3:latest",
                 arquitecto_model: str = "qwen2:latest",
                 diferenciador_model: str = "mistral:latest",
                 validador_model: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):

        self.agente_inspirador = Agent(role="Inspirador", goal="Crear ideas", backstory="...")
        self.agente_pedagogo = Agent(role="Pedagogo", goal="Diseñar la pedagogía", backstory="...")
        self.agente_arquitecto = Agent(role="Arquitecto", goal="Estructurar", backstory="...")
        self.agente_diferenciador = Agent(role="Diferenciador", goal="Adaptar", backstory="...")
        self.agente_validador = Agent(role="Validador", goal="Validar calidad", backstory="...")

        self.inspirador_model = inspirador_model
        self.pedagogo_model = pedagogo_model
        self.arquitecto_model = arquitecto_model
        self.diferenciador_model = diferenciador_model
        self.validador_model = validador_model

        self.ejemplos_k = {
            "ejemplo_celula": "Contenido de ejemplo sobre la célula...",
            "ejemplo_energia": "Contenido de ejemplo sobre la energía..."
        }
        self.quantum_enhancer = QuantumEnhancer(qiskit_config=QISKIT_CONFIG)
        logger.info("✅ QuantumEnhancer inicializado para pre-procesamiento y validación.")

    def _obtener_ejemplos_relevantes(self, materia: str, tema: Optional[str]) -> str:
        return "\n".join([f"### Ejemplo ID: {k}\n{v}" for k, v in self.ejemplos_k.items()])

    def _procesar_resultados(self, crew_result: str) -> str:
        return crew_result

    def generar_actividad_colaborativa(self, materia: str, tema: str = None) -> ActividadEducativa:
        logger.info(f"👥 Generando actividad few-shot para {materia}")

        MAX_INTENTOS_VALIDACION = 3
        intento_actual = 0
        solucion_final_validada = None
        retroalimentacion_para_llm = ""

        while intento_actual < MAX_INTENTOS_VALIDACION and solucion_final_validada is None:
            logger.info(f"🔄 Intento de generación de actividad: {intento_actual + 1}")
            try:
                quantum_insights_pre = self.quantum_enhancer.analizar_dificultad_cuantica(
                    materia, tema, retroalimentacion_para_llm
                )
                logger.info(f"✨ Insights cuánticos (pre-procesamiento): {quantum_insights_pre}")
            except Exception as e:
                logger.warning(f"⚠️ Error en pre-procesamiento cuántico: {e}.")
                quantum_insights_pre = ""

            ejemplos_relevantes = self._obtener_ejemplos_relevantes(materia, tema)
            tarea_inspiracion_description = f"""Estudia estos EJEMPLOS DE ACTIVIDADES EXITOSAS y crea una nueva idea inspiradora para {materia} {f'sobre {tema}' if tema else ''}.
{ejemplos_relevantes}
--- INSIGHTS CUÁNTICOS ---
{quantum_insights_pre if quantum_insights_pre else "No se proporcionaron insights cuánticos."}
--- FIN DE INSIGHTS ---
- Narrativa envolvente y atractiva
- Conexión emocional
- Semilla creativa clara
"""
            tarea_inspiracion = Task(
                description=tarea_inspiracion_description,
                agent=self.agente_inspirador,
                expected_output="Semilla creativa inspiradora con narrativa envolvente"
            )

            tarea_pedagogica = Task(
                description="...",
                agent=self.agente_pedagogo,
                context=[tarea_inspiracion],
                expected_output="Estructura pedagógica detallada"
            )
            tarea_arquitectura = Task(
                description="...",
                agent=self.agente_arquitecto,
                context=[tarea_pedagogica],
                expected_output="Arquitectura detallada"
            )
            tarea_diferenciacion = Task(
                description="...",
                agent=self.agente_diferenciador,
                context=[tarea_arquitectura],
                expected_output="Actividad diferenciada"
            )
            tarea_validacion_crew = Task(
                description="...",
                agent=self.agente_validador,
                context=[tarea_diferenciacion],
                expected_output="Actividad validada"
            )

            crew = Crew(
                agents=[self.agente_inspirador, self.agente_pedagogo, self.agente_arquitecto,
                        self.agente_diferenciador, self.agente_validador],
                tasks=[tarea_inspiracion, tarea_pedagogica, tarea_arquitectura,
                       tarea_diferenciacion, tarea_validacion_crew],
                process=Process.sequential,
                verbose=True
            )
            logger.info("🚀 Ejecutando workflow few-shot del LLM...")
            resultado_crew = crew.kickoff()
            contenido_completo_llm = self._procesar_resultados(resultado_crew)

            logger.info("⚡ FASE CUÁNTICA: Validando la actividad generada por el LLM...")
            puntuacion_validacion_cuantica = 0.0
            feedback_cuantico = ""
            try:
                puntuacion_validacion_cuantica, feedback_cuantico = \
                    self.quantum_enhancer.validar_actividad_cuanticamente(
                        contenido_completo_llm, materia, tema
                    )
                logger.info(f"✅ Validación cuántica: Puntuación={puntuacion_validacion_cuantica:.2f}, Feedback='{feedback_cuantico}'")

                if puntuacion_validacion_cuantica >= self.quantum_enhancer.UMBRAL_VALIDACION_CUANTICA:
                    solucion_final_validada = ActividadEducativa(
                        id=f"fewshot_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        titulo=f"Actividad Few-Shot - {materia}",
                        materia=materia,
                        tema=tema or "tema general",
                        contenido=contenido_completo_llm,
                        estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                        tipo="colaborativa_fewshot_quant_validated",
                        adaptaciones=["narrativa_envolvente", "construccion_progresiva", "flexibilidad_estructurada"],
                        metadatos={
                            "total_estudiantes": 8,
                            "flujo_pedagogico": ["inspiracion", "pedagogia", "arquitectura", "diferenciacion", "validacion_llm", "validacion_cuantica"],
                            "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                            "modelos_usados": {
                                "inspirador": self.inspirador_model,
                                "pedagogo": self.pedagogo_model,
                                "arquitecto": self.arquitecto_model,
                                "diferenciador": self.diferenciador_model,
                                "validador": self.validador_model
                            },
                            "puntuacion_validacion_cuantica": puntuacion_validacion_cuantica,
                            "feedback_cuantico_final": feedback_cuantico
                        },
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    retroalimentacion_para_llm = feedback_cuantico
                    logger.warning(f"❌ Validación cuántica fallida. Retroalimentando al LLM para reintento.")
            except Exception as e:
                logger.error(f"❌ Error en la validación cuántica: {e}.")
                retroalimentacion_para_llm = f"Error en la validación profunda: {e}. Por favor, revisa la consistencia lógica y la optimización de tu plan."
            intento_actual += 1

        if solucion_final_validada:
            return solucion_final_validada
        else:
            logger.error(f"❌ No se pudo generar una actividad validada cuánticamente.")
            return ActividadEducativa(
                id=f"failed_quant_val_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad (Validación Cuántica Fallida) - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo_llm if 'contenido_completo_llm' in locals() else "No se pudo generar una actividad.",
                estudiantes_objetivo=[],
                tipo="colaborativa_quant_failed",
                adaptaciones=[],
                metadatos={"error": "Validación cuántica fallida", "ultimo_feedback_cuantico": retroalimentacion_para_llm},
                timestamp=datetime.now().isoformat()
            )
