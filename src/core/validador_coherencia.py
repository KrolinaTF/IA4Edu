"""
Validador de Coherencia - Sistema avanzado para validar coherencia entre actividades y capacidades
Fase 2: Validaciones inteligentes sin dependencia excesiva de LLM
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger("SistemaAgentesABP.ValidadorCoherencia")

@dataclass
class ValidacionResult:
    """Resultado de una validación específica"""
    aspecto: str
    valido: bool
    puntuacion: float  # 0.0 - 1.0
    detalles: str
    recomendaciones: List[str]

class ValidadorCoherencia:
    """Sistema avanzado de validación de coherencia actividad-capacidades"""
    
    def __init__(self):
        """Inicializa el validador con reglas pedagógicas"""
        self.reglas_pedagogicas = self._cargar_reglas_pedagogicas()
        self.umbrales_validacion = {
            'coherencia_minima': 0.6,
            'coherencia_buena': 0.8,
            'coherencia_excelente': 0.95
        }
        logger.info("✅ ValidadorCoherencia inicializado")
    
    def validar_proyecto_completo(self, actividad: Dict[str, Any], 
                                perfiles: Dict[str, Any], 
                                asignaciones: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación completa de coherencia del proyecto
        
        Args:
            actividad: Datos de la actividad seleccionada
            perfiles: Perfiles de estudiantes 
            asignaciones: Asignaciones generadas
            
        Returns:
            Resultado completo de validación
        """
        logger.info("🔍 Iniciando validación completa de coherencia")
        
        validaciones = []
        
        # 1. Validar estructura básica de la actividad
        validacion_estructura = self._validar_estructura_actividad(actividad)
        validaciones.append(validacion_estructura)
        
        # 2. Validar coherencia actividad-perfiles
        validacion_perfiles = self._validar_coherencia_actividad_perfiles(actividad, perfiles)
        validaciones.append(validacion_perfiles)
        
        # 3. Validar asignaciones vs capacidades
        validacion_asignaciones = self._validar_asignaciones_capacidades(
            actividad, perfiles, asignaciones
        )
        validaciones.append(validacion_asignaciones)
        
        # 4. Validar inclusión y adaptaciones DUA
        validacion_inclusion = self._validar_inclusion_dua(actividad, perfiles)
        validaciones.append(validacion_inclusion)
        
        # 5. Validar carga de trabajo equilibrada
        validacion_carga = self._validar_equilibrio_carga(actividad, perfiles, asignaciones)
        validaciones.append(validacion_carga)
        
        # Consolidar resultados
        resultado_final = self._consolidar_validaciones(validaciones)
        
        logger.info(f"✅ Validación completada: {resultado_final['puntuacion_global']:.2f}/1.0")
        
        return resultado_final
    
    def validar_coherencia_rapida(self, actividad: Dict[str, Any], 
                                perfiles: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación rápida para flujo optimizado
        
        Args:
            actividad: Datos de la actividad
            perfiles: Perfiles de estudiantes
            
        Returns:
            Resultado de validación rápida
        """
        logger.info("⚡ Iniciando validación rápida de coherencia")
        
        puntuacion = 1.0
        alertas = []
        aspectos_validados = []
        
        # Validaciones críticas rápidas
        if not actividad.get('titulo'):
            alertas.append("Actividad sin título")
            puntuacion -= 0.2
        else:
            aspectos_validados.append("titulo_presente")
            
        if not actividad.get('objetivo'):
            alertas.append("Actividad sin objetivo claro")
            puntuacion -= 0.3
        else:
            aspectos_validados.append("objetivo_presente")
            
        if not actividad.get('etapas'):
            alertas.append("Actividad sin etapas estructuradas")
            puntuacion -= 0.4
        else:
            aspectos_validados.append(f"estructura_{len(actividad['etapas'])}_etapas")
        
        # Validar cobertura de estudiantes
        estudiantes_con_perfil = len(perfiles.get('estudiantes', {}))
        if estudiantes_con_perfil == 0:
            alertas.append("Sin perfiles de estudiantes")
            puntuacion -= 0.3
        else:
            aspectos_validados.append(f"perfiles_{estudiantes_con_perfil}_estudiantes")
        
        # Validar diversidad neurotipos
        neurotipos_detectados = set()
        for estudiante_data in perfiles.get('estudiantes', {}).values():
            for adaptacion in estudiante_data.get('adaptaciones', []):
                if 'TEA' in adaptacion:
                    neurotipos_detectados.add('TEA')
                elif 'TDAH' in adaptacion:
                    neurotipos_detectados.add('TDAH')
                elif 'altas capacidades' in adaptacion.lower():
                    neurotipos_detectados.add('Altas Capacidades')
        
        if neurotipos_detectados:
            aspectos_validados.append(f"diversidad_{len(neurotipos_detectados)}_neurotipos")
            # Bonus por diversidad bien gestionada
            puntuacion = min(1.0, puntuacion + 0.1)
        
        return {
            'puntuacion': max(0.0, puntuacion),
            'valida': puntuacion > self.umbrales_validacion['coherencia_minima'],
            'alertas': alertas,
            'aspectos_validados': aspectos_validados,
            'neurotipos_detectados': list(neurotipos_detectados),
            'tipo_validacion': 'rapida'
        }
    
    def _validar_estructura_actividad(self, actividad: Dict[str, Any]) -> ValidacionResult:
        """Valida la estructura básica de la actividad"""
        puntuacion = 1.0
        detalles = []
        recomendaciones = []
        
        # Elementos requeridos con pesos
        elementos_requeridos = {
            'titulo': 0.15,
            'objetivo': 0.25,
            'nivel_educativo': 0.1,
            'etapas': 0.3,
            'recursos': 0.1,
            'observaciones': 0.1
        }
        
        for elemento, peso in elementos_requeridos.items():
            if not actividad.get(elemento):
                puntuacion -= peso
                detalles.append(f"Falta elemento: {elemento}")
                recomendaciones.append(f"Añadir {elemento} a la actividad")
            else:
                detalles.append(f"✓ {elemento} presente")
        
        # Validaciones específicas
        if actividad.get('etapas'):
            num_etapas = len(actividad['etapas'])
            if num_etapas < 2:
                puntuacion -= 0.1
                recomendaciones.append("Considerar añadir más etapas para mejor estructura")
            elif num_etapas > 5:
                puntuacion -= 0.05
                recomendaciones.append("Considerar simplificar número de etapas")
            else:
                detalles.append(f"✓ Número apropiado de etapas: {num_etapas}")
        
        return ValidacionResult(
            aspecto="estructura_actividad",
            valido=puntuacion > 0.6,
            puntuacion=max(0.0, puntuacion),
            detalles="; ".join(detalles),
            recomendaciones=recomendaciones
        )
    
    def _validar_coherencia_actividad_perfiles(self, actividad: Dict[str, Any], 
                                             perfiles: Dict[str, Any]) -> ValidacionResult:
        """Valida coherencia entre actividad y perfiles de estudiantes"""
        puntuacion = 1.0
        detalles = []
        recomendaciones = []
        
        estudiantes = perfiles.get('estudiantes', {})
        if not estudiantes:
            return ValidacionResult(
                aspecto="coherencia_actividad_perfiles",
                valido=False,
                puntuacion=0.0,
                detalles="Sin estudiantes para validar",
                recomendaciones=["Proporcionar perfiles de estudiantes"]
            )
        
        # Analizar complejidad de la actividad
        complejidad_actividad = self._evaluar_complejidad_actividad(actividad)
        detalles.append(f"Complejidad detectada: {complejidad_actividad}")
        
        # Analizar capacidades del grupo
        capacidades_grupo = self._analizar_capacidades_grupo(estudiantes)
        
        # Validar alineación complejidad-capacidades
        if complejidad_actividad == "alta" and capacidades_grupo["nivel_promedio"] < 0.6:
            puntuacion -= 0.3
            recomendaciones.append("Actividad muy compleja para el nivel del grupo")
        elif complejidad_actividad == "baja" and capacidades_grupo["nivel_promedio"] > 0.8:
            puntuacion -= 0.2
            recomendaciones.append("Actividad poco desafiante para el nivel del grupo")
        else:
            detalles.append("✓ Complejidad alineada con capacidades del grupo")
        
        # Validar cobertura de fortalezas
        fortalezas_requeridas = self._extraer_fortalezas_requeridas(actividad)
        fortalezas_disponibles = capacidades_grupo["fortalezas_principales"]
        
        cobertura = len(set(fortalezas_requeridas) & set(fortalezas_disponibles))
        cobertura_porcentaje = cobertura / max(1, len(fortalezas_requeridas))
        
        if cobertura_porcentaje < 0.5:
            puntuacion -= 0.2
            recomendaciones.append("Pocas fortalezas del grupo alineadas con la actividad")
        else:
            detalles.append(f"✓ Cobertura de fortalezas: {cobertura_porcentaje:.1%}")
        
        return ValidacionResult(
            aspecto="coherencia_actividad_perfiles",
            valido=puntuacion > 0.6,
            puntuacion=max(0.0, puntuacion),
            detalles="; ".join(detalles),
            recomendaciones=recomendaciones
        )
    
    def _validar_asignaciones_capacidades(self, actividad: Dict[str, Any], 
                                        perfiles: Dict[str, Any], 
                                        asignaciones: Dict[str, Any]) -> ValidacionResult:
        """Valida que las asignaciones respeten las capacidades"""
        puntuacion = 1.0
        detalles = []
        recomendaciones = []
        
        if not asignaciones:
            return ValidacionResult(
                aspecto="asignaciones_capacidades",
                valido=False,
                puntuacion=0.0,
                detalles="Sin asignaciones para validar",
                recomendaciones=["Generar asignaciones de estudiantes"]
            )
        
        estudiantes = perfiles.get('estudiantes', {})
        
        # Validar asignaciones específicas (si existen)
        asignaciones_data = asignaciones.get('asignaciones', {})
        if asignaciones_data:
            for estudiante_id, asignacion in asignaciones_data.items():
                if estudiante_id in estudiantes:
                    estudiante = estudiantes[estudiante_id]
                    
                    # Validar rol asignado vs fortalezas
                    rol_asignado = asignacion.get('rol', '')
                    fortalezas_estudiante = estudiante.get('fortalezas', [])
                    
                    if self._validar_rol_fortalezas(rol_asignado, fortalezas_estudiante):
                        detalles.append(f"✓ {estudiante['nombre']}: rol alineado")
                    else:
                        puntuacion -= 0.1
                        detalles.append(f"⚠ {estudiante['nombre']}: rol no óptimo")
                        recomendaciones.append(f"Revisar rol de {estudiante['nombre']}")
        
        # Validar equilibrio de carga
        carga_promedio = self._calcular_carga_promedio(asignaciones, estudiantes)
        if carga_promedio > 0.8:
            puntuacion -= 0.15
            recomendaciones.append("Carga de trabajo muy alta, considerar redistribuir")
        elif carga_promedio < 0.4:
            puntuacion -= 0.1
            recomendaciones.append("Carga de trabajo baja, estudiantes podrían asumir más")
        else:
            detalles.append(f"✓ Carga equilibrada: {carga_promedio:.1%}")
        
        return ValidacionResult(
            aspecto="asignaciones_capacidades",
            valido=puntuacion > 0.6,
            puntuacion=max(0.0, puntuacion),
            detalles="; ".join(detalles),
            recomendaciones=recomendaciones
        )
    
    def _validar_inclusion_dua(self, actividad: Dict[str, Any], 
                             perfiles: Dict[str, Any]) -> ValidacionResult:
        """Valida inclusión y adaptaciones DUA"""
        puntuacion = 1.0
        detalles = []
        recomendaciones = []
        
        estudiantes = perfiles.get('estudiantes', {})
        estudiantes_con_necesidades = [
            e for e in estudiantes.values() 
            if e.get('adaptaciones', [])
        ]
        
        if not estudiantes_con_necesidades:
            detalles.append("✓ Grupo sin necesidades especiales detectadas")
            return ValidacionResult(
                aspecto="inclusion_dua",
                valido=True,
                puntuacion=1.0,
                detalles="; ".join(detalles),
                recomendaciones=[]
            )
        
        # Detectar neurotipos presentes
        neurotipos_presentes = set()
        for estudiante in estudiantes_con_necesidades:
            for adaptacion in estudiante['adaptaciones']:
                if 'TEA' in adaptacion:
                    neurotipos_presentes.add('TEA')
                elif 'TDAH' in adaptacion:
                    neurotipos_presentes.add('TDAH')
                elif 'altas capacidades' in adaptacion.lower():
                    neurotipos_presentes.add('Altas Capacidades')
        
        # Validar adaptaciones por neurotipo
        observaciones = actividad.get('observaciones', '').lower()
        
        for neurotipo in neurotipos_presentes:
            if neurotipo == 'TEA':
                if 'visual' in observaciones and 'estructura' in observaciones:
                    detalles.append("✓ Adaptaciones TEA presentes")
                else:
                    puntuacion -= 0.2
                    recomendaciones.append("Añadir adaptaciones visuales y estructurales para TEA")
                    
            elif neurotipo == 'TDAH':
                if 'movimiento' in observaciones or 'descanso' in observaciones:
                    detalles.append("✓ Adaptaciones TDAH presentes")
                else:
                    puntuacion -= 0.2
                    recomendaciones.append("Añadir adaptaciones de movimiento para TDAH")
                    
            elif neurotipo == 'Altas Capacidades':
                if 'desafío' in observaciones or 'enriquecimiento' in observaciones:
                    detalles.append("✓ Adaptaciones Altas Capacidades presentes")
                else:
                    puntuacion -= 0.15
                    recomendaciones.append("Añadir desafíos adicionales para Altas Capacidades")
        
        return ValidacionResult(
            aspecto="inclusion_dua",
            valido=puntuacion > 0.6,
            puntuacion=max(0.0, puntuacion),
            detalles="; ".join(detalles),
            recomendaciones=recomendaciones
        )
    
    def _validar_equilibrio_carga(self, actividad: Dict[str, Any], 
                                perfiles: Dict[str, Any], 
                                asignaciones: Dict[str, Any]) -> ValidacionResult:
        """Valida equilibrio de carga de trabajo"""
        puntuacion = 1.0
        detalles = []
        recomendaciones = []
        
        num_estudiantes = len(perfiles.get('estudiantes', {}))
        num_etapas = len(actividad.get('etapas', []))
        
        if num_estudiantes == 0:
            return ValidacionResult(
                aspecto="equilibrio_carga",
                valido=False,
                puntuacion=0.0,
                detalles="Sin estudiantes para evaluar carga",
                recomendaciones=[]
            )
        
        # Calcular tareas totales
        tareas_totales = 0
        for etapa in actividad.get('etapas', []):
            tareas_totales += len(etapa.get('tareas', []))
        
        # Ratio tareas/estudiantes
        if tareas_totales > 0:
            ratio_tareas = tareas_totales / num_estudiantes
            
            if ratio_tareas > 3:
                puntuacion -= 0.2
                recomendaciones.append("Muchas tareas por estudiante, considerar simplificar")
            elif ratio_tareas < 1:
                puntuacion -= 0.1
                recomendaciones.append("Pocas tareas, estudiantes podrían estar subutilizados")
            else:
                detalles.append(f"✓ Ratio tareas equilibrado: {ratio_tareas:.1f} por estudiante")
        
        # Validar duración vs capacidades
        duracion_str = actividad.get('duracion_minutos', '').lower()
        if 'sesion' in duracion_str or 'hora' in duracion_str:
            detalles.append("✓ Duración especificada apropiadamente")
        else:
            puntuacion -= 0.05
            recomendaciones.append("Especificar duración más claramente")
        
        return ValidacionResult(
            aspecto="equilibrio_carga",
            valido=puntuacion > 0.6,
            puntuacion=max(0.0, puntuacion),
            detalles="; ".join(detalles),
            recomendaciones=recomendaciones
        )
    
    def _consolidar_validaciones(self, validaciones: List[ValidacionResult]) -> Dict[str, Any]:
        """Consolida todas las validaciones en un resultado final"""
        puntuacion_global = sum(v.puntuacion for v in validaciones) / len(validaciones)
        
        todas_recomendaciones = []
        todos_detalles = []
        aspectos_validados = []
        aspectos_fallidos = []
        
        for validacion in validaciones:
            todos_detalles.append(f"{validacion.aspecto}: {validacion.detalles}")
            todas_recomendaciones.extend(validacion.recomendaciones)
            
            if validacion.valido:
                aspectos_validados.append(validacion.aspecto)
            else:
                aspectos_fallidos.append(validacion.aspecto)
        
        # Determinar nivel de coherencia
        if puntuacion_global >= self.umbrales_validacion['coherencia_excelente']:
            nivel = "excelente"
        elif puntuacion_global >= self.umbrales_validacion['coherencia_buena']:
            nivel = "buena"
        elif puntuacion_global >= self.umbrales_validacion['coherencia_minima']:
            nivel = "aceptable"
        else:
            nivel = "insuficiente"
        
        return {
            'puntuacion_global': puntuacion_global,
            'nivel_coherencia': nivel,
            'valido_globalmente': puntuacion_global >= self.umbrales_validacion['coherencia_minima'],
            'aspectos_validados': aspectos_validados,
            'aspectos_fallidos': aspectos_fallidos,
            'detalles_completos': todos_detalles,
            'recomendaciones_consolidadas': list(set(todas_recomendaciones)),  # Eliminar duplicados
            'validaciones_individuales': [
                {
                    'aspecto': v.aspecto,
                    'puntuacion': v.puntuacion,
                    'valido': v.valido,
                    'recomendaciones': v.recomendaciones
                } for v in validaciones
            ],
            'timestamp': self._get_timestamp(),
            'version_validador': '2.0.0'
        }
    
    # Métodos auxiliares
    
    def _cargar_reglas_pedagogicas(self) -> Dict[str, Any]:
        """Carga reglas pedagógicas predefinidas"""
        return {
            'complejidad_factores': ['num_etapas', 'num_tareas_por_etapa', 'dependencias'],
            'fortalezas_actividad_map': {
                'matemáticas': ['números', 'cálculo', 'operaciones', 'fracciones'],
                'comunicación': ['presentación', 'grupo', 'debate', 'escritura'],
                'experimentación': ['investigación', 'experimento', 'observación'],
                'creatividad': ['diseño', 'arte', 'mural', 'creativo']
            },
            'neurotipos_adaptaciones': {
                'TEA': ['visual', 'estructura', 'rutina', 'predictible'],
                'TDAH': ['movimiento', 'fragmentado', 'descanso', 'dinámico'],
                'Altas Capacidades': ['desafío', 'enriquecimiento', 'autonomía', 'liderazgo']
            }
        }
    
    def _evaluar_complejidad_actividad(self, actividad: Dict[str, Any]) -> str:
        """Evalúa complejidad de la actividad"""
        puntos_complejidad = 0
        
        # Factores de complejidad
        etapas = actividad.get('etapas', [])
        puntos_complejidad += len(etapas)
        
        for etapa in etapas:
            tareas = etapa.get('tareas', [])
            puntos_complejidad += len(tareas) * 0.5
            
            for tarea in tareas:
                if tarea.get('formato_asignacion') == 'grupos':
                    puntos_complejidad += 0.5  # Trabajo grupal añade complejidad
        
        if puntos_complejidad > 8:
            return "alta"
        elif puntos_complejidad > 4:
            return "media"
        else:
            return "baja"
    
    def _analizar_capacidades_grupo(self, estudiantes: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza capacidades del grupo"""
        todas_fortalezas = []
        disponibilidades = []
        
        for estudiante in estudiantes.values():
            fortalezas = estudiante.get('fortalezas', [])
            todas_fortalezas.extend(fortalezas)
            
            disponibilidad = estudiante.get('disponibilidad', 85)
            disponibilidades.append(disponibilidad)
        
        from collections import Counter
        contador_fortalezas = Counter(todas_fortalezas)
        
        return {
            'nivel_promedio': sum(disponibilidades) / max(1, len(disponibilidades)) / 100,
            'fortalezas_principales': [f for f, c in contador_fortalezas.most_common(5)],
            'diversidad_fortalezas': len(set(todas_fortalezas))
        }
    
    def _extraer_fortalezas_requeridas(self, actividad: Dict[str, Any]) -> List[str]:
        """Extrae fortalezas requeridas de la actividad"""
        texto_actividad = (
            f"{actividad.get('titulo', '')} {actividad.get('objetivo', '')}"
        ).lower()
        
        fortalezas_requeridas = []
        reglas = self.reglas_pedagogicas['fortalezas_actividad_map']
        
        for fortaleza, palabras_clave in reglas.items():
            if any(palabra in texto_actividad for palabra in palabras_clave):
                fortalezas_requeridas.append(fortaleza)
        
        return fortalezas_requeridas
    
    def _validar_rol_fortalezas(self, rol: str, fortalezas: List[str]) -> bool:
        """Valida si un rol es apropiado para las fortalezas del estudiante"""
        if not rol or not fortalezas:
            return False
        
        rol_lower = rol.lower()
        
        # Mapeo simplificado rol-fortalezas
        mapeo_roles = {
            'coordinador': ['liderazgo', 'comunicación_escrita', 'organización'],
            'investigador': ['curiosidad_científica', 'investigación', 'experimentación'],
            'comunicador': ['comunicación_escrita', 'presentación', 'colaboración'],
            'diseñador': ['creatividad', 'arte', 'diseño_visual'],
            'calculador': ['matemáticas_números', 'operaciones_matemáticas']
        }
        
        for tipo_rol, fortalezas_esperadas in mapeo_roles.items():
            if tipo_rol in rol_lower:
                return any(f in fortalezas for f in fortalezas_esperadas)
        
        return True  # Si no hay mapeo específico, asumimos válido
    
    def _calcular_carga_promedio(self, asignaciones: Dict[str, Any], 
                                estudiantes: Dict[str, Any]) -> float:
        """Calcula carga promedio de trabajo"""
        if not asignaciones or not estudiantes:
            return 0.5  # Carga neutra por defecto
        
        asignaciones_data = asignaciones.get('asignaciones', {})
        cargas_individuales = []
        
        for estudiante_id, asignacion in asignaciones_data.items():
            if estudiante_id in estudiantes:
                # Estimar carga basada en número de tareas y disponibilidad
                tareas = asignacion.get('tareas', [])
                disponibilidad = estudiantes[estudiante_id].get('disponibilidad', 85) / 100
                
                carga_estimada = min(1.0, len(tareas) * 0.3 / disponibilidad)
                cargas_individuales.append(carga_estimada)
        
        if cargas_individuales:
            return sum(cargas_individuales) / len(cargas_individuales)
        else:
            return 0.5
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()