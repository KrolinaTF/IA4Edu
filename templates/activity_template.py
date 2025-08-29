"""
Templates de datos para actividades educativas inclusivas.
Este archivo contiene las estructuras de datos y constantes utilizadas
para el diseño de actividades adaptadas a la neurodiversidad.
"""

from pydantic import BaseModel
from typing import List, Dict, Optional

# Modelos de datos para estructurar la información (opcional, para validación futura)
class AdaptacionEstudiante(BaseModel):
    estudiante_id: str
    neurotipo: str
    estrategias_especificas: List[str]
    materiales_adicionales: List[str]
    rol_en_grupo: str
    tiempo_estimado: str
    apoyo_necesario: str

class Tarea(BaseModel):
    nombre: str
    descripcion: str
    objetivo: str
    duracion_estimada: str
    materiales: List[str]
    instrucciones_paso_a_paso: List[str]
    adaptaciones_por_estudiante: List[AdaptacionEstudiante]
    criterios_evaluacion: List[str]

class Fase(BaseModel):
    nombre: str
    descripcion: str
    objetivo: str
    duracion_total: str
    tareas: List[Tarea]
    preguntas_clave_adaptacion: List[str]
    estrategias_adaptacion: Dict[str, str]  # neurotipo -> estrategia

class AsignacionGrupo(BaseModel):
    grupo_id: str
    estudiantes: List[str]
    tipo_agrupacion: str  # "parejas", "grupos_3", "grupos_4", "individual"
    justificacion_agrupacion: str
    roles_asignados: Dict[str, str]  # estudiante_id -> rol

# Preguntas clave para adaptaciones (constantes)
PREGUNTAS_CLAVE_ADAPTACION = [
    "¿Cómo puede este estudiante acceder a la información de manera efectiva?",
    "¿Qué tipo de instrucciones funcionan mejor para este perfil?",
    "¿Cómo puede demostrar su comprensión de manera auténtica?",
    "¿Qué rol en el grupo maximiza sus fortalezas?",
    "¿Qué apoyos ambientales necesita?",
    "¿Cómo mantener su motivación y engagement?",
    "¿Qué adaptaciones de tiempo o ritmo son necesarias?",
    "¿Cómo facilitar su interacción social positiva?"
]

# Neurotipos y sus características clave
NEUROTIPOS_INFO = {
    "TEA": {
        "fortalezas_comunes": ["atención al detalle", "pensamiento sistemático", "memoria específica"],
        "desafios_comunes": ["comunicación social", "flexibilidad", "procesamiento sensorial"],
        "estrategias_base": ["estructura clara", "instrucciones visuales", "tiempo de procesamiento"]
    },
    "TDAH": {
        "fortalezas_comunes": ["creatividad", "energía", "pensamiento divergente"],
        "desafios_comunes": ["atención sostenida", "organización", "autorregulación"],
        "estrategias_base": ["movimiento", "descansos", "estímulos multisensoriales"]
    },
    "Altas_Capacidades": {
        "fortalezas_comunes": ["razonamiento abstracto", "aprendizaje rápido", "creatividad"],
        "desafios_comunes": ["perfeccionismo", "motivación con tareas rutinarias", "intensidad emocional"],
        "estrategias_base": ["complejidad adicional", "autonomía", "proyectos independientes"]
    },
    "Típico": {
        "fortalezas_comunes": ["adaptabilidad", "trabajo colaborativo", "seguimiento de instrucciones"],
        "desafios_comunes": ["confianza", "liderazgo", "pensamiento crítico avanzado"],
        "estrategias_base": ["colaboración", "retroalimentación", "ejemplos concretos"]
    }
}