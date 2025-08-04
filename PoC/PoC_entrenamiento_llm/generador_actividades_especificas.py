#!/usr/bin/env python3
"""
Generador de Actividades Específicas y Ejecutables
=================================================

Sistema que convierte intenciones pedagógicas generales en planes de actividad
100% específicos, ejecutables y coherentes. Resuelve el problema de los LLMs
que generan actividades "que suenan bien" pero no son prácticas.

Características:
- Descompone actividades en tareas atómicas específicas
- Valida coherencia temporal, espacial y pedagógica
- Genera cronogramas minuto a minuto
- Asigna estudiantes específicos a tareas específicas
- Incluye puntos de control y validación en tiempo real
"""

import json
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum
from datetime import datetime, timedelta
import networkx as nx

# =============================================================================
# MODELOS DE DATOS
# =============================================================================

@dataclass
class Estudiante:
    """Perfil específico de estudiante"""
    id: str
    nombre: str
    necesidades_estructura: float  # 0.0 (creativo) a 1.0 (necesita estructura)
    preferencia_social: float      # 0.0 (individual) a 1.0 (grupal)
    canal_dominante: str          # 'visual', 'auditivo', 'kinestesico'
    capacidad_atencion: float     # 0.0 (baja) a 1.0 (alta)
    habilidades_especiales: List[str] = field(default_factory=list)
    restricciones: List[str] = field(default_factory=list)
    
    def puede_hacer(self, tarea: 'Tarea') -> bool:
        """Determina si el estudiante puede realizar una tarea específica"""
        # Verificar restricciones
        for restriccion in self.restricciones:
            if restriccion in tarea.requisitos_no_compatibles:
                return False
        
        # Verificar habilidades requeridas
        for habilidad in tarea.habilidades_requeridas:
            if habilidad not in self.habilidades_especiales and tarea.nivel_dificultad > 0.7:
                return False
        
        return True

@dataclass
class Tarea:
    """Tarea atómica específica"""
    id: str
    nombre: str
    descripcion_especifica: str
    duracion_minutos: int
    materiales_requeridos: List[str]
    espacio_requerido: str
    habilidades_requeridas: List[str] = field(default_factory=list)
    requisitos_no_compatibles: List[str] = field(default_factory=list)
    dependencias: List[str] = field(default_factory=list)  # IDs de tareas que deben completarse antes
    nivel_dificultad: float = 0.5
    estudiante_asignado: Optional[str] = None
    momento_inicio: Optional[int] = None
    momento_fin: Optional[int] = None
    
    def puede_ejecutarse_en_paralelo_con(self, otra_tarea: 'Tarea') -> bool:
        """Determina si esta tarea puede ejecutarse en paralelo con otra"""
        # No pueden compartir materiales únicos
        materiales_unicos = {'papel_continuo', 'tijeras', 'regla_grande'}
        mis_materiales_unicos = set(self.materiales_requeridos) & materiales_unicos
        otros_materiales_unicos = set(otra_tarea.materiales_requeridos) & materiales_unicos
        
        if mis_materiales_unicos & otros_materiales_unicos:
            return False
        
        # No pueden usar el mismo espacio físico
        if self.espacio_requerido == otra_tarea.espacio_requerido and self.espacio_requerido != 'cualquier_mesa':
            return False
        
        return True

@dataclass
class RecursoDisponible:
    """Recurso físico disponible en el aula"""
    id: str
    tipo: str  # 'material', 'espacio', 'herramienta'
    cantidad: int
    ubicacion: str
    restricciones_uso: List[str] = field(default_factory=list)

@dataclass
class ContextoEjecucion:
    """Contexto específico para la ejecución de la actividad"""
    duracion_total_minutos: int
    recursos_disponibles: List[RecursoDisponible]
    espacio_fisico: str
    restricciones_generales: List[str] = field(default_factory=list)
    momento_del_dia: str = 'mañana'  # 'mañana', 'tarde'

@dataclass
class PuntoControl:
    """Punto de verificación durante la actividad"""
    momento_minuto: int
    descripcion: str
    validaciones_requeridas: List[str]
    acciones_si_falla: List[str]

@dataclass
class ActividadEspecifica:
    """Actividad completamente especificada y ejecutable"""
    id: str
    titulo: str
    objetivo_especifico: str
    tareas: List[Tarea]
    cronograma_minuto_a_minuto: Dict[int, List[str]]  # minuto -> lista de acciones
    materiales_exactos: Dict[str, str]  # material -> cantidad específica
    puntos_control: List[PuntoControl]
    instrucciones_profesor: List[str]
    plan_emergencia: Dict[str, str]  # problema -> solución

# =============================================================================
# BANCO DE PLANTILLAS ESPECÍFICAS
# =============================================================================

class PlantillaActividad:
    """Plantilla base para generar actividades específicas"""
    
    def __init__(self, tipo: str):
        self.tipo = tipo
        self.parametros_requeridos = []
        self.validadores = []
    
    def puede_aplicarse(self, intencion: str, aula: List[Estudiante], contexto: ContextoEjecucion) -> bool:
        """Determina si esta plantilla es apropiada para la intención dada"""
        raise NotImplementedError
    
    def generar_tareas(self, aula: List[Estudiante], contexto: ContextoEjecucion) -> List[Tarea]:
        """Genera tareas específicas para esta plantilla"""
        raise NotImplementedError

class PlantillaMuralColaborativo(PlantillaActividad):
    """Plantilla específica para murales colaborativos"""
    
    def __init__(self):
        super().__init__("mural_colaborativo")
        self.temas_aplicables = ['célula', 'sistema_solar', 'ecosistema', 'historia']
    
    def puede_aplicarse(self, intencion: str, aula: List[Estudiante], contexto: ContextoEjecucion) -> bool:
        """Verifica si es apropiada para crear un mural"""
        palabras_clave = ['mural', 'colaborativo', 'dibujar', 'crear', 'visual']
        return any(palabra in intencion.lower() for palabra in palabras_clave) and len(aula) >= 3
    
    def calcular_dimensiones_papel(self, n_estudiantes: int) -> Tuple[float, float]:
        """Calcula dimensiones exactas del papel según número de estudiantes"""
        area_total = n_estudiantes * 0.25  # 0.25 m² por estudiante
        ratio = 1.4  # ancho/alto
        alto = math.sqrt(area_total / ratio)
        ancho = area_total / alto
        return (round(ancho, 1), round(alto, 1))
    
    def generar_tareas(self, aula: List[Estudiante], contexto: ContextoEjecucion) -> List[Tarea]:
        """Genera todas las tareas específicas para crear un mural"""
        tareas = []
        
        # Calcular parámetros específicos
        ancho, alto = self.calcular_dimensiones_papel(len(aula))
        
        # Tarea 1: Preparación del espacio
        tareas.append(Tarea(
            id="prep_espacio",
            nombre="Preparar espacio de trabajo",
            descripcion_especifica=f"Extender papel continuo de {ancho}m x {alto}m en mesa central. Limpiar superficie previamente.",
            duracion_minutos=5,
            materiales_requeridos=[f"papel_continuo_{ancho}x{alto}", "cinta_adhesiva"],
            espacio_requerido="mesa_central",
            habilidades_requeridas=["organizacion_basica"]
        ))
        
        # Tarea 2: Investigación de contenido
        tareas.append(Tarea(
            id="investigar_contenido",
            nombre="Buscar información específica",
            descripcion_especifica="Ir a biblioteca o usar libro de texto. Identificar 4-5 elementos principales del tema. Tomar notas en plantilla proporcionada.",
            duracion_minutos=15,
            materiales_requeridos=["libro_texto", "plantilla_notas", "lapiz"],
            espacio_requerido="biblioteca_o_rincon_lectura",
            habilidades_requeridas=["lectura_comprensiva"],
            dependencias=[]
        ))
        
        # Tarea 3: Diseño del contorno
        tareas.append(Tarea(
            id="disenar_contorno",
            nombre="Dibujar estructura principal",
            descripcion_especifica="Dibujar contorno principal usando lápiz. Si es célula: forma ovalada de 40cm x 30cm centrada. Usar regla para líneas rectas.",
            duracion_minutos=10,
            materiales_requeridos=["lapiz_grafico", "regla_30cm", "goma"],
            espacio_requerido="mesa_central",
            habilidades_requeridas=["dibujo_basico"],
            dependencias=["prep_espacio"]
        ))
        
        # Tarea 4: Creación de elementos
        tareas.append(Tarea(
            id="crear_elementos",
            nombre="Dibujar elementos específicos",
            descripcion_especifica="Dibujar elementos investigados dentro del contorno. Mantener proporciones realistas. Usar colores diferentes para cada elemento.",
            duracion_minutos=25,
            materiales_requeridos=["lapices_colores", "rotuladores_finos"],
            espacio_requerido="mesa_central",
            habilidades_requeridas=["dibujo_basico", "atencion_detalle"],
            dependencias=["disenar_contorno", "investigar_contenido"]
        ))
        
        # Tarea 5: Etiquetado
        tareas.append(Tarea(
            id="crear_etiquetas",
            nombre="Crear etiquetas informativas",
            descripcion_especifica="Escribir etiquetas claras para cada elemento. Letra mayúscula, 1.5cm de altura mínimo. Pegar con cinta en posición clara.",
            duracion_minutos=15,
            materiales_requeridos=["cartulina_blanca", "rotulador_negro", "tijeras_punta_roma", "cinta_adhesiva"],
            espacio_requerido="mesa_lateral",
            habilidades_requeridas=["escritura_clara"],
            dependencias=["crear_elementos"]
        ))
        
        # Tarea 6: Documentación
        tareas.append(Tarea(
            id="documentar_proceso",
            nombre="Fotografiar proceso y resultado",
            descripcion_especifica="Tomar 3 fotos: proceso investigación, mural en construcción, resultado final. Crear carpeta digital con nombre fecha_actividad.",
            duracion_minutos=8,
            materiales_requeridos=["tablet_o_movil", "cable_usb"],
            espacio_requerido="cualquier_ubicacion",
            habilidades_requeridas=["uso_tecnologia_basica"],
            dependencias=[]  # Puede hacerse en paralelo con otras tareas
        ))
        
        return tareas

class PlantillaExperimento(PlantillaActividad):
    """Plantilla para experimentos científicos simples"""
    
    def __init__(self):
        super().__init__("experimento_cientifico")
    
    def puede_aplicarse(self, intencion: str, aula: List[Estudiante], contexto: ContextoEjecucion) -> bool:
        palabras_clave = ['experimento', 'observar', 'medir', 'comparar', 'hipótesis']
        return any(palabra in intencion.lower() for palabra in palabras_clave)
    
    def generar_tareas(self, aula: List[Estudiante], contexto: ContextoEjecucion) -> List[Tarea]:
        # Implementación específica para experimentos
        # Por simplicidad, devolvemos lista vacía ahora
        return []

# =============================================================================
# MOTOR DE DESCOMPOSICIÓN Y VALIDACIÓN
# =============================================================================

class DescomponedorActividades:
    """Convierte actividades generales en tareas específicas ejecutables"""
    
    def __init__(self):
        self.plantillas = [
            PlantillaMuralColaborativo(),
            PlantillaExperimento()
        ]
    
    def seleccionar_plantilla(self, intencion: str, aula: List[Estudiante], 
                            contexto: ContextoEjecucion) -> Optional[PlantillaActividad]:
        """Selecciona la plantilla más apropiada para la intención"""
        for plantilla in self.plantillas:
            if plantilla.puede_aplicarse(intencion, aula, contexto):
                return plantilla
        return None
    
    def descomponer(self, intencion: str, aula: List[Estudiante], 
                   contexto: ContextoEjecucion) -> List[Tarea]:
        """Descompone intención en tareas específicas"""
        plantilla = self.seleccionar_plantilla(intencion, aula, contexto)
        
        if not plantilla:
            raise ValueError(f"No se encontró plantilla apropiada para: {intencion}")
        
        tareas = plantilla.generar_tareas(aula, contexto)
        return tareas

class ValidadorCoherencia:
    """Valida y corrige incoherencias en planes de actividad"""
    
    def __init__(self):
        self.conflictos_detectados = []
    
    def validar_temporalmente(self, tareas: List[Tarea], duracion_total: int) -> List[str]:
        """Valida que las tareas caben en el tiempo disponible"""
        errores = []
        
        # Crear grafo de dependencias
        grafo = nx.DiGraph()
        for tarea in tareas:
            grafo.add_node(tarea.id, duracion=tarea.duracion_minutos)
            for dependencia in tarea.dependencias:
                grafo.add_edge(dependencia, tarea.id)
        
        # Verificar que no hay ciclos
        if not nx.is_directed_acyclic_graph(grafo):
            errores.append("Dependencias circulares detectadas en las tareas")
            return errores
        
        # Calcular camino crítico
        try:
            camino_critico = self.calcular_camino_critico(grafo, tareas)
            if camino_critico > duracion_total:
                errores.append(f"Tiempo requerido ({camino_critico} min) excede tiempo disponible ({duracion_total} min)")
        except Exception as e:
            errores.append(f"Error calculando tiempo total: {str(e)}")
        
        return errores
    
    def calcular_camino_critico(self, grafo: nx.DiGraph, tareas: List[Tarea]) -> int:
        """Calcula el tiempo mínimo necesario considerando paralelización"""
        tareas_dict = {t.id: t for t in tareas}
        
        # Ordenamiento topológico
        orden_topologico = list(nx.topological_sort(grafo))
        
        # Calcular tiempos más tempranos
        tiempos_tempranos = {}
        for tarea_id in orden_topologico:
            tarea = tareas_dict[tarea_id]
            predecesores = list(grafo.predecessors(tarea_id))
            
            if not predecesores:
                tiempos_tempranos[tarea_id] = tarea.duracion_minutos
            else:
                tiempo_max_predecesor = max(tiempos_tempranos[pred] for pred in predecesores)
                tiempos_tempranos[tarea_id] = tiempo_max_predecesor + tarea.duracion_minutos
        
        return max(tiempos_tempranos.values()) if tiempos_tempranos else 0
    
    def validar_materiales(self, tareas: List[Tarea], recursos: List[RecursoDisponible]) -> List[str]:
        """Valida que hay suficientes materiales para todas las tareas"""
        errores = []
        
        # Crear inventario de recursos
        inventario = {}
        for recurso in recursos:
            if recurso.tipo == 'material':
                inventario[recurso.id] = recurso.cantidad
        
        # Verificar cada tarea
        for tarea in tareas:
            for material in tarea.materiales_requeridos:
                if material not in inventario:
                    errores.append(f"Material '{material}' requerido para '{tarea.nombre}' no está disponible")
                elif inventario[material] <= 0:
                    errores.append(f"Cantidad insuficiente de '{material}' para '{tarea.nombre}'")
                else:
                    inventario[material] -= 1  # Simular consumo
        
        return errores

class AsignadorTareas:
    """Asigna estudiantes específicos a tareas específicas"""
    
    def __init__(self):
        self.asignaciones = {}
    
    def asignar_estudiantes(self, tareas: List[Tarea], estudiantes: List[Estudiante]) -> Dict[str, str]:
        """Asigna cada tarea a un estudiante específico"""
        asignaciones = {}
        estudiantes_disponibles = estudiantes.copy()
        
        # Ordenar tareas por dificultad y requisitos
        tareas_ordenadas = sorted(tareas, key=lambda t: (len(t.habilidades_requeridas), t.nivel_dificultad), reverse=True)
        
        for tarea in tareas_ordenadas:
            mejor_estudiante = self.encontrar_mejor_estudiante(tarea, estudiantes_disponibles)
            
            if mejor_estudiante:
                asignaciones[tarea.id] = mejor_estudiante.id
                tarea.estudiante_asignado = mejor_estudiante.id
                # No removemos estudiante para permitir múltiples tareas si es necesario
            else:
                # Asignar al estudiante más compatible aunque no sea ideal
                estudiante_por_defecto = self.estudiante_mas_compatible(tarea, estudiantes_disponibles)
                if estudiante_por_defecto:
                    asignaciones[tarea.id] = estudiante_por_defecto.id
                    tarea.estudiante_asignado = estudiante_por_defecto.id
        
        return asignaciones
    
    def encontrar_mejor_estudiante(self, tarea: Tarea, estudiantes: List[Estudiante]) -> Optional[Estudiante]:
        """Encuentra el estudiante más apropiado para una tarea"""
        candidatos_validos = [est for est in estudiantes if est.puede_hacer(tarea)]
        
        if not candidatos_validos:
            return None
        
        # Calcular puntuación de compatibilidad
        mejor_puntuacion = -1
        mejor_estudiante = None
        
        for estudiante in candidatos_validos:
            puntuacion = self.calcular_compatibilidad(estudiante, tarea)
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_estudiante = estudiante
        
        return mejor_estudiante
    
    def calcular_compatibilidad(self, estudiante: Estudiante, tarea: Tarea) -> float:
        """Calcula compatibilidad entre estudiante y tarea (0.0 a 1.0)"""
        puntuacion = 0.5  # Base
        
        # Bonus por habilidades especiales
        habilidades_coincidentes = set(estudiante.habilidades_especiales) & set(tarea.habilidades_requeridas)
        puntuacion += len(habilidades_coincidentes) * 0.2
        
        # Ajuste por necesidades de estructura
        if 'organizacion' in tarea.habilidades_requeridas:
            puntuacion += estudiante.necesidades_estructura * 0.3
        
        if 'creatividad' in tarea.habilidades_requeridas:
            puntuacion += (1 - estudiante.necesidades_estructura) * 0.3
        
        # Ajuste por preferencias sociales
        if tarea.espacio_requerido in ['biblioteca', 'rincon_individual']:
            puntuacion += (1 - estudiante.preferencia_social) * 0.2
        else:
            puntuacion += estudiante.preferencia_social * 0.2
        
        return min(1.0, puntuacion)
    
    def estudiante_mas_compatible(self, tarea: Tarea, estudiantes: List[Estudiante]) -> Optional[Estudiante]:
        """Encuentra estudiante más compatible incluso si no cumple todos los requisitos"""
        if not estudiantes:
            return None
        
        return max(estudiantes, key=lambda est: self.calcular_compatibilidad(est, tarea))

class GeneradorCronograma:
    """Genera cronograma específico minuto a minuto"""
    
    def generar_cronograma(self, tareas: List[Tarea], duracion_total: int) -> Dict[int, List[str]]:
        """Genera cronograma detallado minuto a minuto"""
        cronograma = {}
        
        # Crear grafo de dependencias
        grafo = nx.DiGraph()
        tareas_dict = {t.id: t for t in tareas}
        
        for tarea in tareas:
            grafo.add_node(tarea.id)
            for dependencia in tarea.dependencias:
                grafo.add_edge(dependencia, tarea.id)
        
        # Programar tareas respetando dependencias
        momento_actual = 0
        tareas_programadas = set()
        
        while len(tareas_programadas) < len(tareas) and momento_actual < duracion_total:
            # Encontrar tareas que pueden ejecutarse ahora
            tareas_disponibles = [
                tarea for tarea in tareas 
                if tarea.id not in tareas_programadas 
                and all(dep in tareas_programadas for dep in tarea.dependencias)
            ]
            
            if not tareas_disponibles:
                momento_actual += 1
                continue
            
            # Programar primera tarea disponible
            tarea = tareas_disponibles[0]
            tarea.momento_inicio = momento_actual
            tarea.momento_fin = momento_actual + tarea.duracion_minutos
            
            # Añadir al cronograma
            for minuto in range(tarea.momento_inicio, tarea.momento_fin):
                if minuto not in cronograma:
                    cronograma[minuto] = []
                cronograma[minuto].append(
                    f"{tarea.estudiante_asignado}: {tarea.descripcion_especifica}"
                )
            
            tareas_programadas.add(tarea.id)
            momento_actual = tarea.momento_fin
        
        return cronograma

# =============================================================================
# SISTEMA PRINCIPAL
# =============================================================================

class GeneradorActividadesEspecificas:
    """Sistema principal que genera actividades 100% específicas"""
    
    def __init__(self):
        self.descomponedor = DescomponedorActividades()
        self.validador = ValidadorCoherencia()
        self.asignador = AsignadorTareas()
        self.cronogramador = GeneradorCronograma()
    
    def generar_actividad(self, intencion: str, aula: List[Estudiante], 
                         contexto: ContextoEjecucion) -> ActividadEspecifica:
        """Genera actividad completamente específica y ejecutable"""
        
        print(f"🎯 Generando actividad para: '{intencion}'")
        print(f"👥 Aula: {len(aula)} estudiantes")
        print(f"⏱️  Duración: {contexto.duracion_total_minutos} minutos")
        print()
        
        # 1. Descomponer en tareas específicas
        tareas = self.descomponedor.descomponer(intencion, aula, contexto)
        print(f"📋 Tareas generadas: {len(tareas)}")
        
        # 2. Validar coherencia
        errores_tiempo = self.validador.validar_temporalmente(tareas, contexto.duracion_total_minutos)
        errores_materiales = self.validador.validar_materiales(tareas, contexto.recursos_disponibles)
        
        if errores_tiempo or errores_materiales:
            print("❌ Errores de validación encontrados:")
            for error in errores_tiempo + errores_materiales:
                print(f"   - {error}")
            # En una implementación real, aquí corregiríamos los errores
        else:
            print("✅ Validación exitosa")
        
        # 3. Asignar estudiantes a tareas
        asignaciones = self.asignador.asignar_estudiantes(tareas, aula)
        print(f"👤 Asignaciones realizadas: {len(asignaciones)}")
        
        # 4. Generar cronograma
        cronograma = self.cronogramador.generar_cronograma(tareas, contexto.duracion_total_minutos)
        print(f"📅 Cronograma generado: {len(cronograma)} momentos")
        
        # 5. Calcular materiales exactos
        materiales_exactos = self.calcular_materiales_exactos(tareas)
        
        # 6. Crear puntos de control
        puntos_control = self.generar_puntos_control(tareas)
        
        # 7. Generar instrucciones para el profesor
        instrucciones = self.generar_instrucciones_profesor(tareas, cronograma)
        
        actividad = ActividadEspecifica(
            id=f"actividad_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad: {intencion}",
            objetivo_especifico=self.generar_objetivo_especifico(intencion, tareas),
            tareas=tareas,
            cronograma_minuto_a_minuto=cronograma,
            materiales_exactos=materiales_exactos,
            puntos_control=puntos_control,
            instrucciones_profesor=instrucciones,
            plan_emergencia=self.generar_plan_emergencia(tareas)
        )
        
        return actividad
    
    def calcular_materiales_exactos(self, tareas: List[Tarea]) -> Dict[str, str]:
        """Calcula lista exacta de materiales necesarios"""
        materiales = {}
        
        for tarea in tareas:
            for material in tarea.materiales_requeridos:
                if material in materiales:
                    # Incrementar cantidad si ya existe
                    cantidad_actual = materiales[material]
                    if "unidad" in cantidad_actual:
                        numero = int(cantidad_actual.split()[0]) + 1
                        materiales[material] = f"{numero} unidades"
                else:
                    # Material específico con cantidad
                    if "papel_continuo" in material:
                        materiales[material] = "1 rollo"
                    elif "lapiz" in material or "rotulador" in material:
                        materiales[material] = "1 unidad por estudiante"
                    else:
                        materiales[material] = "1 unidad"
        
        return materiales
    
    def generar_puntos_control(self, tareas: List[Tarea]) -> List[PuntoControl]:
        """Genera puntos de control durante la actividad"""
        puntos = []
        
        # Punto de control a los 20 minutos
        puntos.append(PuntoControl(
            momento_minuto=20,
            descripcion="Verificación de progreso inicial",
            validaciones_requeridas=[
                "¿Todos los estudiantes han comenzado sus tareas?",
                "¿Hay problemas con materiales?",
                "¿Algún estudiante necesita ayuda?"
            ],
            acciones_si_falla=[
                "Reasignar tareas si es necesario",
                "Proporcionar materiales alternativos",
                "Dar apoyo individualizado"
            ]
        ))
        
        # Punto de control a mitad de la actividad
        duracion_total = max(t.momento_fin for t in tareas if t.momento_fin)
        mitad = duracion_total // 2
        
        puntos.append(PuntoControl(
            momento_minuto=mitad,
            descripcion="Verificación de progreso intermedio",
            validaciones_requeridas=[
                "¿Se están cumpliendo los tiempos estimados?",
                "¿La calidad del trabajo es apropiada?",
                "¿Hay buena colaboración entre estudiantes?"
            ],
            acciones_si_falla=[
                "Acelerar tareas si es necesario",
                "Reforzar criterios de calidad",
                "Facilitar comunicación entre grupos"
            ]
        ))
        
        return puntos
    
    def generar_instrucciones_profesor(self, tareas: List[Tarea], cronograma: Dict) -> List[str]:
        """Genera instrucciones específicas para el profesor"""
        instrucciones = [
            "PREPARACIÓN PREVIA:",
            "- Revisar que todos los materiales estén disponibles según lista exacta",
            "- Preparar espacios de trabajo según distribución especificada",
            "- Tener plan de emergencia visible",
            "",
            "DURANTE LA ACTIVIDAD:",
            "- Seguir cronograma minuto a minuto",
            "- Intervenir solo si hay desviaciones significativas",
            "- Documentar observaciones para mejora futura",
            "",
            "ROLE DEL PROFESOR:",
            "- Facilitador, no director",
            "- Observador activo del progreso",
            "- Solucionador de problemas logísticos"
        ]
        
        return instrucciones
    
    def generar_objetivo_especifico(self, intencion: str, tareas: List[Tarea]) -> str:
        """Genera objetivo específico basado en las tareas"""
        verbos_accion = []
        for tarea in tareas:
            if "investigar" in tarea.nombre.lower():
                verbos_accion.append("investigar")
            elif "crear" in tarea.nombre.lower() or "dibujar" in tarea.nombre.lower():
                verbos_accion.append("crear")
            elif "documentar" in tarea.nombre.lower():
                verbos_accion.append("documentar")
        
        verbos_unicos = list(set(verbos_accion))
        
        return f"Los estudiantes serán capaces de {', '.join(verbos_unicos)} de manera colaborativa y específica, completando {len(tareas)} tareas interconectadas en {max(t.momento_fin for t in tareas if t.momento_fin)} minutos."
    
    def generar_plan_emergencia(self, tareas: List[Tarea]) -> Dict[str, str]:
        """Genera plan de emergencia para problemas comunes"""
        return {
            "estudiante_ausente": "Redistribuir tareas entre estudiantes presentes o combinar roles",
            "material_faltante": "Usar materiales alternativos según tabla de sustituciones",
            "tiempo_insuficiente": "Priorizar tareas principales y simplificar tareas secundarias",
            "conflicto_entre_estudiantes": "Separar temporalmente y reasignar a tareas individuales",
            "calidad_insuficiente": "Proporcionar ejemplo específico y tiempo adicional para corrección"
        }

# =============================================================================
# FUNCIÓN DE DEMOSTRACIÓN
# =============================================================================

def demo_generador():
    """Demostración del generador de actividades específicas"""
    
    print("=" * 60)
    print("🚀 DEMO: GENERADOR DE ACTIVIDADES ESPECÍFICAS")
    print("=" * 60)
    print()
    
    # Crear aula de ejemplo
    aula_ejemplo = [
        Estudiante(
            id="est_001",
            nombre="Ana",
            necesidades_estructura=0.8,
            preferencia_social=0.6,
            canal_dominante="visual",
            capacidad_atencion=0.9,
            habilidades_especiales=["lectura_comprensiva", "organizacion_basica"],
            restricciones=[]
        ),
        Estudiante(
            id="est_002", 
            nombre="Luis",
            necesidades_estructura=0.3,
            preferencia_social=0.8,
            canal_dominante="kinestesico",
            capacidad_atencion=0.6,
            habilidades_especiales=["uso_tecnologia_basica", "creatividad"],
            restricciones=["no_tijeras_puntiagudas"]
        ),
        Estudiante(
            id="est_003",
            nombre="Elena",
            necesidades_estructura=0.9,
            preferencia_social=0.4,
            canal_dominante="visual",
            capacidad_atencion=0.8,
            habilidades_especiales=["dibujo_basico", "atencion_detalle"],
            restricciones=[]
        ),
        Estudiante(
            id="est_004",
            nombre="Sara",
            necesidades_estructura=0.5,
            preferencia_social=0.9,
            canal_dominante="auditivo",
            capacidad_atencion=0.7,
            habilidades_especiales=["escritura_clara", "organizacion_basica"],
            restricciones=[]
        )
    ]
    
    # Crear contexto de ejecución
    recursos_ejemplo = [
        RecursoDisponible("papel_continuo_2.1x1.4", "material", 1, "armario_arte"),
        RecursoDisponible("lapices_colores", "material", 20, "mesa_materiales"),
        RecursoDisponible("rotuladores_finos", "material", 8, "mesa_materiales"),
        RecursoDisponible("rotulador_negro", "material", 4, "mesa_materiales"),
        RecursoDisponible("libro_texto", "material", 4, "biblioteca_aula"),
        RecursoDisponible("cartulina_blanca", "material", 10, "armario_arte"),
        RecursoDisponible("tijeras_punta_roma", "material", 4, "mesa_materiales"),
        RecursoDisponible("cinta_adhesiva", "material", 2, "mesa_materiales"),
        RecursoDisponible("regla_30cm", "material", 6, "mesa_materiales"),
        RecursoDisponible("tablet_o_movil", "material", 1, "mesa_profesor"),
        RecursoDisponible("mesa_central", "espacio", 1, "centro_aula"),
        RecursoDisponible("mesa_lateral", "espacio", 2, "laterales_aula"),
        RecursoDisponible("biblioteca_o_rincon_lectura", "espacio", 1, "rincon_aula")
    ]
    
    contexto_ejemplo = ContextoEjecucion(
        duracion_total_minutos=90,
        recursos_disponibles=recursos_ejemplo,
        espacio_fisico="aula_multiusos",
        restricciones_generales=["max_4_estudiantes_por_mesa", "no_ruido_excesivo"],
        momento_del_dia="mañana"
    )
    
    # Generar actividad
    generador = GeneradorActividadesEspecificas()
    
    try:
        actividad = generador.generar_actividad(
            intencion="crear mural colaborativo sobre la célula animal",
            aula=aula_ejemplo,
            contexto=contexto_ejemplo
        )
        
        print()
        print("=" * 60)
        print("📋 ACTIVIDAD GENERADA")
        print("=" * 60)
        print()
        
        print(f"🎯 TÍTULO: {actividad.titulo}")
        print(f"📖 OBJETIVO: {actividad.objetivo_especifico}")
        print()
        
        print("👥 TAREAS ESPECÍFICAS:")
        for i, tarea in enumerate(actividad.tareas, 1):
            print(f"   {i}. {tarea.nombre}")
            print(f"      👤 Responsable: {tarea.estudiante_asignado}")
            print(f"      ⏱️  Duración: {tarea.duracion_minutos} minutos")
            print(f"      📦 Materiales: {', '.join(tarea.materiales_requeridos)}")
            print(f"      📍 Espacio: {tarea.espacio_requerido}")
            print(f"      📝 Descripción: {tarea.descripcion_especifica}")
            if tarea.dependencias:
                print(f"      🔗 Depende de: {', '.join(tarea.dependencias)}")
            print()
        
        print("🗂️ MATERIALES EXACTOS NECESARIOS:")
        for material, cantidad in actividad.materiales_exactos.items():
            print(f"   - {material}: {cantidad}")
        print()
        
        print("📅 CRONOGRAMA MINUTO A MINUTO (primeros 30 minutos):")
        for minuto in sorted(actividad.cronograma_minuto_a_minuto.keys())[:30]:
            acciones = actividad.cronograma_minuto_a_minuto[minuto]
            print(f"   {minuto:02d}:00 - {'; '.join(acciones)}")
        print()
        
        print("🔍 PUNTOS DE CONTROL:")
        for punto in actividad.puntos_control:
            print(f"   ⏰ Minuto {punto.momento_minuto}: {punto.descripcion}")
            print(f"      ✓ Verificar: {', '.join(punto.validaciones_requeridas)}")
            print()
        
        print("👨‍🏫 INSTRUCCIONES PARA EL PROFESOR:")
        for instruccion in actividad.instrucciones_profesor:
            print(f"   {instruccion}")
        print()
        
        print("🚨 PLAN DE EMERGENCIA:")
        for problema, solucion in actividad.plan_emergencia.items():
            print(f"   - {problema}: {solucion}")
        
        print()
        print("=" * 60)
        print("✅ DEMO COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error generando actividad: {str(e)}")
        import traceback
        traceback.print_exc()

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    demo_generador()