"""
Definición de modelos relacionados con actividades educativas.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class Actividad:
    """Estructura de la actividad educativa"""
    descripcion: str
    nivel_educativo: str
    competencias_objetivo: List[str]
    duracion_estimada: int
    tipo_producto: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Actividad':
        """
        Crea una instancia de Actividad a partir de un diccionario
        
        Args:
            data: Diccionario con datos de la actividad
            
        Returns:
            Instancia de Actividad
        """
        competencias = data.get('competencias', '')
        if isinstance(competencias, str):
            competencias_lista = [c.strip() for c in competencias.split(',')]
        elif isinstance(competencias, list):
            competencias_lista = competencias
        else:
            competencias_lista = []
            
        # Extraer duración en formato numérico
        duracion_texto = data.get('duracion', '60')
        import re
        duracion_match = re.search(r'(\d+)', str(duracion_texto))
        duracion = int(duracion_match.group(1)) if duracion_match else 60
        
        return cls(
            descripcion=data.get('descripcion', 'No disponible'),
            nivel_educativo=data.get('nivel', '4º Primaria'),
            competencias_objetivo=competencias_lista,
            duracion_estimada=duracion,
            tipo_producto=data.get('tipo_producto', 'proyecto colaborativo')
        )

@dataclass
class Idea:
    """Estructura de una idea de actividad"""
    id: str
    titulo: str
    descripcion: str
    nivel: str
    competencias: str
    duracion: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], idx: int = 0) -> 'Idea':
        """
        Crea una instancia de Idea a partir de un diccionario
        
        Args:
            data: Diccionario con datos de la idea
            idx: Índice para generar ID si no existe
            
        Returns:
            Instancia de Idea
        """
        return cls(
            id=data.get('id', f"idea_{idx+1}"),
            titulo=data.get('titulo', 'Sin título'),
            descripcion=data.get('descripcion', 'No disponible'),
            nivel=data.get('nivel', '4º Primaria'),
            competencias=data.get('competencias', 'No especificadas'),
            duracion=data.get('duracion', '2-3 sesiones')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la idea a un diccionario
        
        Returns:
            Diccionario con los datos de la idea
        """
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'nivel': self.nivel,
            'competencias': self.competencias,
            'duracion': self.duracion
        }