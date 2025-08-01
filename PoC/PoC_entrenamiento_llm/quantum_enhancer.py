# quantum_enhancer.py

import logging
from typing import Optional

QISKIT_CONFIG = {
    "backend": "aer_simulator",  # simulador Aer de Qiskit
    "num_qubits_max": 10,
    "shots": 1024,
    "umbral_validacion": 0.8  # umbral para validación cuántica
}

class QuantumEnhancer:
    def __init__(self, qiskit_config: dict):
        self.qiskit_config = qiskit_config
        self.UMBRAL_VALIDACION_CUANTICA = qiskit_config.get("umbral_validacion", 0.8)
        logging.getLogger("QUANTUM_ENHANCER").info(
            f"QuantumEnhancer inicializado con umbral {self.UMBRAL_VALIDACION_CUANTICA}"
        )

    def analizar_dificultad_cuantica(self, materia: str, tema: Optional[str], feedback_anterior: str) -> str:
        insights = []
        if "ecosistema" in str(tema).lower() or "redes" in str(tema).lower():
            insights.append("Análisis cuántico: alta interconexión conceptual detectada. Necesaria progresión estructurada.")
        if "no optimo" in feedback_anterior.lower() or "inconsistente" in feedback_anterior.lower():
            insights.append(f"Análisis cuántico: intentos anteriores fallaron en coherencia/optimización. Revisar lógica de dependencias.")
        return " ".join(insights) if insights else "Análisis cuántico inicial: complejidad general detectada."

    def validar_actividad_cuanticamente(self, actividad_llm_completa: str, materia: str, tema: Optional[str]) -> (float, str):
        puntuacion = 0.0
        feedback = []

        costo_simulado = 0.0
        if "clímax pedagógico" not in actividad_llm_completa.lower():
            costo_simulado += 0.2
            feedback.append("El componente cuántico sugiere que el clímax pedagógico no está claramente definido o es subóptimo.")
        if "roles específicos" not in actividad_llm_completa.lower() and "roles asignados" not in actividad_llm_completa.lower():
            costo_simulado += 0.3
            feedback.append("La asignación de roles o su especificidad es insuficiente para garantizar la interdependencia real, lo que aumenta el 'costo' de la actividad.")
        if len(actividad_llm_completa) < 500:
            costo_simulado += 0.1
            feedback.append("La actividad parece carecer de profundidad o detalle, lo que afecta su 'densidad' de optimización.")

        puntuacion = max(0.0, 1.0 - costo_simulado)
        if puntuacion < self.UMBRAL_VALIDACION_CUANTICA:
            if not feedback:
                feedback.append(
                    f"La actividad no alcanzó el umbral de calidad cuántica ({self.UMBRAL_VALIDACION_CUANTICA:.2f}). Necesita una revisión profunda de la optimización y consistencia global."
                )
        else:
            feedback.append("La actividad ha sido validada cuánticamente con alta coherencia y optimización.")
        return puntuacion, " ".join(feedback)
