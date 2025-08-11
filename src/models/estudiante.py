"""
Definición de modelos relacionados con estudiantes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class Estudiante:
    """Estructura del estudiante"""
    id: str
    nombre: str
    fortalezas: List[str]
    necesidades_apoyo: List[str]
    disponibilidad: int
    historial_roles: List[str]
    adaptaciones: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Estudiante':
        """
        Crea una instancia de Estudiante a partir de un diccionario
        
        Args:
            data: Diccionario con datos del estudiante
            
        Returns:
            Instancia de Estudiante
        """
        return cls(
            id=data.get('id', ''),
            nombre=data.get('nombre', ''),
            fortalezas=data.get('fortalezas', []),
            necesidades_apoyo=data.get('necesidades_apoyo', []),
            disponibilidad=data.get('disponibilidad', 85),
            historial_roles=data.get('historial_roles', []),
            adaptaciones=data.get('adaptaciones', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el estudiante a un diccionario
        
        Returns:
            Diccionario con los datos del estudiante
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'fortalezas': self.fortalezas,
            'necesidades_apoyo': self.necesidades_apoyo,
            'disponibilidad': self.disponibilidad,
            'historial_roles': self.historial_roles,
            'adaptaciones': self.adaptaciones
        }

@dataclass
class PerfilEstudiante:
    """Perfil detallado de un estudiante con información académica y de comportamiento"""
    id: str
    nombre: str
    diagnostico_formal: str
    nivel_apoyo: str
    estilo_aprendizaje: List[str]
    canal_preferido: str
    temperamento: str
    tolerancia_frustracion: str
    intereses: List[str]
    matematicas: Dict[str, str]
    lengua: Dict[str, str]
    ciencias: Dict[str, str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerfilEstudiante':
        """
        Crea una instancia de PerfilEstudiante a partir de un diccionario
        
        Args:
            data: Diccionario con datos del perfil
            
        Returns:
            Instancia de PerfilEstudiante
        """
        return cls(
            id=data.get('id', ''),
            nombre=data.get('nombre', ''),
            diagnostico_formal=data.get('diagnostico_formal', 'ninguno'),
            nivel_apoyo=data.get('nivel_apoyo', 'medio'),
            estilo_aprendizaje=data.get('estilo_aprendizaje', []),
            canal_preferido=data.get('canal_preferido', 'visual'),
            temperamento=data.get('temperamento', 'equilibrado'),
            tolerancia_frustracion=data.get('tolerancia_frustracion', 'media'),
            intereses=data.get('intereses', []),
            matematicas=data.get('matematicas', {}),
            lengua=data.get('lengua', {}),
            ciencias=data.get('ciencias', {})
        )
    
    def get_fortalezas(self) -> List[str]:
        """
        Extrae fortalezas basándose en competencias conseguidas e intereses
        
        Returns:
            Lista de fortalezas identificadas
        """
        fortalezas = []
        
        # Basado en competencias matemáticas
        if self.matematicas.get("numeros_10000") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("matemáticas_números")
        if self.matematicas.get("operaciones_complejas") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("operaciones_matemáticas")
            
        # Basado en competencias lingüísticas
        if self.lengua.get("tiempos_verbales") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("gramática")
        if self.lengua.get("textos_informativos") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("comunicación_escrita")
            
        # Basado en competencias científicas
        if self.ciencias.get("metodo_cientifico") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("investigación")
            
        # Basado en intereses
        for interes in self.intereses:
            if interes == "ciencias":
                fortalezas.append("curiosidad_científica")
            elif interes == "experimentos":
                fortalezas.append("experimentación")
            elif interes == "trabajo_en_grupo":
                fortalezas.append("colaboración")
            elif interes == "lectura":
                fortalezas.append("comprensión_lectora")
        
        # Basado en características específicas
        if self.temperamento == "reflexivo":
            fortalezas.append("pensamiento_analítico")
        if self.tolerancia_frustracion == "alta":
            fortalezas.append("perseverancia")
            
        return fortalezas
        
    def get_necesidades_apoyo(self) -> List[str]:
        """
        Extrae necesidades de apoyo basándose en el perfil completo
        
        Returns:
            Lista de necesidades de apoyo identificadas
        """
        necesidades = []
        
        # Basado en nivel de apoyo
        if self.nivel_apoyo == "alto":
            necesidades.append("supervisión_continua")
        elif self.nivel_apoyo == "medio":
            necesidades.append("check_ins_regulares")
        
        # Basado en tolerancia a la frustración
        if self.tolerancia_frustracion == "baja":
            necesidades.append("apoyo_emocional")
            necesidades.append("tareas_graduadas")
        
        # Basado en canal preferido
        if self.canal_preferido == "visual":
            necesidades.append("apoyos_visuales")
        elif self.canal_preferido == "auditivo":
            necesidades.append("explicaciones_verbales")
        elif self.canal_preferido == "kinestésico":
            necesidades.append("actividades_manipulativas")
        
        # Basado en diagnóstico formal
        if "TEA" in self.diagnostico_formal:
            necesidades.extend(["rutinas_estructuradas", "ambiente_predecible"])
        elif "TDAH" in self.diagnostico_formal:
            necesidades.extend(["instrucciones_claras", "descansos_frecuentes"])
        elif "altas_capacidades" in self.diagnostico_formal:
            necesidades.extend(["retos_adicionales", "proyectos_autonomos"])
        
        return necesidades