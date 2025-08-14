"""
Definición de modelos relacionados con proyectos y tareas.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass  
class Tarea:
    """Estructura de la tarea"""
    id: str
    descripcion: str
    competencias_requeridas: List[str]
    complejidad: int  # 1-5
    tipo: str  # "individual", "colaborativa", "creativa"
    dependencias: List[str]
    tiempo_estimado: int

@dataclass
class TareaEspecifica:
    """Una tarea concreta de la actividad con análisis profundo del MVP"""
    id: str
    nombre: str
    descripcion: str
    habilidades_requeridas: List[str]
    materiales_especificos: List[str]
    duracion_estimada: int
    complejidad: str  # "baja", "media", "alta"
    tipo_interaccion: str  # "individual", "parejas", "grupo"
    
    @classmethod
    def from_tarea(cls, tarea: Tarea) -> 'TareaEspecifica':
        """Convierte una Tarea básica a TareaEspecifica"""
        complejidad_map = {1: "baja", 2: "baja", 3: "media", 4: "alta", 5: "alta"}
        tipo_map = {"individual": "individual", "colaborativa": "grupo", "creativa": "grupo"}
        
        return cls(
            id=tarea.id,
            nombre=tarea.descripcion[:50] + "..." if len(tarea.descripcion) > 50 else tarea.descripcion,
            descripcion=tarea.descripcion,
            habilidades_requeridas=tarea.competencias_requeridas,
            materiales_especificos=[],  # Se llenarían con análisis LLM
            duracion_estimada=tarea.tiempo_estimado,
            complejidad=complejidad_map.get(tarea.complejidad, "media"),
            tipo_interaccion=tipo_map.get(tarea.tipo, "grupo")
        )

@dataclass
class AnalisisActividad:
    """Análisis completo de una actividad específica del MVP"""
    titulo: str
    objetivos_especificos: List[str]
    pasos_detallados: List[str]
    tareas_identificadas: List[TareaEspecifica]
    materiales_completos: List[str]
    conceptos_clave: List[str]
    retos_potenciales: List[str]

@dataclass
class EstudianteFaseInteligente:
    """Estudiante con tareas específicas reales del MVP"""
    id: str
    nombre: str
    neurotipo: str
    tareas_asignadas: List[TareaEspecifica]
    rol_coordinado: str
    justificacion_detallada: str
    apoyos_especificos: List[str]
    tiempo_total: int

@dataclass
class FaseInteligente:
    """Fase con tareas reales coordinadas del MVP"""
    numero: int
    nombre: str
    objetivo_fase: str
    minuto_inicio: int
    minuto_fin: int
    estudiantes: List[EstudianteFaseInteligente]
    tareas_paralelas: List[str]
    puntos_sincronizacion: List[str]
    materiales_fase: List[str]

@dataclass
class ActividadInteligente:
    """Actividad completamente analizada y coordinada del MVP"""
    analisis: AnalisisActividad
    fases: List[FaseInteligente]
    duracion_total: int
    preparacion_detallada: List[str]
    evaluacion_sugerida: List[str]
    extension_posible: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tarea':
        """
        Crea una instancia de Tarea a partir de un diccionario
        
        Args:
            data: Diccionario con datos de la tarea
            
        Returns:
            Instancia de Tarea
        """
        # Procesar competencias
        if 'competencias_requeridas' in data:
            competencias = data['competencias_requeridas']
            if isinstance(competencias, str):
                competencias = [c.strip() for c in competencias.split(',')]
        else:
            competencias = []
            
        # Procesar dependencias
        if 'dependencias' in data:
            dependencias = data['dependencias']
            if isinstance(dependencias, str):
                dependencias = [d.strip() for d in dependencias.split(',')]
        else:
            dependencias = []
            
        return cls(
            id=data.get('id', ''),
            descripcion=data.get('descripcion', ''),
            competencias_requeridas=competencias,
            complejidad=data.get('complejidad', 3),
            tipo=data.get('tipo', 'individual'),
            dependencias=dependencias,
            tiempo_estimado=data.get('tiempo_estimado', 30)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la tarea a un diccionario
        
        Returns:
            Diccionario con los datos de la tarea
        """
        return asdict(self)

@dataclass
class Fase:
    """Estructura de una fase del proyecto"""
    nombre: str
    duracion: str
    tareas: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fase':
        """
        Crea una instancia de Fase a partir de un diccionario
        
        Args:
            data: Diccionario con datos de la fase
            
        Returns:
            Instancia de Fase
        """
        return cls(
            nombre=data.get('nombre', ''),
            duracion=data.get('duracion', ''),
            tareas=data.get('tareas', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la fase a un diccionario
        
        Returns:
            Diccionario con los datos de la fase
        """
        return asdict(self)

@dataclass
class ProyectoABP:
    """Estructura del proyecto completo de ABP"""
    titulo: str
    descripcion: str
    duracion: str
    competencias_objetivo: List[str]
    fases: List[Dict]
    asignaciones: List[Dict]
    recursos: Dict
    evaluacion: Dict
    metadatos: Dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProyectoABP':
        """
        Crea una instancia de ProyectoABP a partir de un diccionario
        
        Args:
            data: Diccionario con datos del proyecto
            
        Returns:
            Instancia de ProyectoABP
        """
        # Extraer datos del proyecto base si existe
        if 'proyecto_base' in data:
            proyecto_base = data['proyecto_base']
            titulo = proyecto_base.get('titulo', '')
            descripcion = proyecto_base.get('descripcion', '')
            duracion = proyecto_base.get('duracion_base', '')
            competencias = proyecto_base.get('competencias_base', [])
        else:
            # Intentar extraer de la raíz
            titulo = data.get('titulo', '')
            descripcion = data.get('descripcion', '')
            duracion = data.get('duracion', '')
            competencias = data.get('competencias_objetivo', [])
        
        return cls(
            titulo=titulo,
            descripcion=descripcion,
            duracion=duracion,
            competencias_objetivo=competencias,
            fases=data.get('fases', []),
            asignaciones=data.get('asignaciones', []),
            recursos=data.get('recursos', {}),
            evaluacion=data.get('evaluacion', {}),
            metadatos=data.get('metadatos', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el proyecto a un diccionario
        
        Returns:
            Diccionario con los datos del proyecto
        """
        return asdict(self)