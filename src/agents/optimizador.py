"""
Agente Optimizador de Asignaciones (Assignment Optimizer Agent).
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from core.ollama_integrator import OllamaIntegrator
from agents.base_agent import BaseAgent
from models.proyecto import Tarea
from utils.json_parser import parse_json_seguro

class AgenteOptimizadorAsignaciones(BaseAgent):
    """Agente Optimizador de Asignaciones (Assignment Optimizer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """
        Inicializa el Agente Optimizador de Asignaciones
        
        Args:
            ollama_integrator: Integrador de LLM
        """
        super().__init__(ollama_integrator)
        self.perfiles = {}  # Se actualizará cuando reciba los perfiles

    def optimizar_asignaciones(self, tareas_input, analisis_estudiantes: Dict, perfilador=None, **kwargs) -> Dict:
        """
        Optimiza las asignaciones de tareas basándose en el análisis de perfiles
        
        Args:
            tareas_input: Puede ser List[Tarea], Dict con actividad, o datos del analizador
            analisis_estudiantes: Análisis de compatibilidades entre estudiantes y tareas
            perfilador: Referencia al perfilador (opcional)
            **kwargs: Parámetros adicionales
            
        Returns:
            Diccionario con asignaciones optimizadas
        """
        self.logger.info("🎯 Iniciando optimización de asignaciones...")
        
        # =================== VALIDACIÓN Y NORMALIZACIÓN DE ENTRADA ===================
        
        # 1. Actualizar perfiles si se proporciona perfilador
        if perfilador and hasattr(perfilador, 'perfiles_base'):
            self.perfiles = {e.id: e for e in perfilador.perfiles_base}
            self.logger.info(f"📋 Perfiles actualizados: {len(self.perfiles)} estudiantes")
        
        # 2. Extraer y normalizar tareas desde diferentes tipos de entrada
        tareas_normalizadas = self._normalizar_tareas_entrada(tareas_input)
        
        if not tareas_normalizadas:
            self.logger.warning("❌ No se pudieron extraer tareas válidas de la entrada")
            return self._generar_asignaciones_fallback([])
        
        self.logger.info(f"✅ Tareas normalizadas: {len(tareas_normalizadas)} tareas")
        
        # 3. Validar que hay estudiantes para asignar
        if not self.perfiles:
            self.logger.warning("❌ No hay perfiles de estudiantes disponibles")
            return self._generar_asignaciones_fallback(tareas_normalizadas)
        
        # 3.1. Debug: Mostrar IDs de estudiantes disponibles
        estudiantes_disponibles = list(self.perfiles.keys())
        self.logger.info(f"📋 Estudiantes disponibles en sistema: {estudiantes_disponibles}")
        
        # =================== PREPARACIÓN DE DATOS PARA LLM ===================
        
        # 4. Preparar prompt optimizado para el LLM
        prompt_optimizacion = self._construir_prompt_optimizacion(
            tareas_normalizadas, 
            analisis_estudiantes
        )
        
        self.logger.info(f"🔄 Enviando prompt al LLM para {len(tareas_normalizadas)} tareas y {len(self.perfiles)} estudiantes")
        
        # =================== LLAMADA AL LLM Y PARSEO ===================
        
        try:
            # 5. Llamada al LLM con parámetros optimizados
            respuesta_llm = self.ollama.generar_respuesta(
                prompt_optimizacion, 
                max_tokens=800,
                temperatura=0.3  # Menos creatividad, más consistencia
            )
            
            self.logger.debug(f"📥 Respuesta del LLM recibida: {len(respuesta_llm)} caracteres")
            
            # 6. Parsear respuesta del LLM
            asignaciones_parseadas = self._parsear_respuesta_llm(respuesta_llm)
            
            if asignaciones_parseadas:
                # 7. Validar y completar asignaciones
                asignaciones_validadas = self._validar_y_completar_asignaciones(
                    asignaciones_parseadas, 
                    tareas_normalizadas
                )
                
                if asignaciones_validadas:
                    self.logger.info(f"✅ Asignaciones generadas exitosamente para {len(asignaciones_validadas)} estudiantes")
                    return asignaciones_validadas
            
            raise ValueError("Respuesta del LLM no válida o incompleta")
            
        except Exception as e:
            self.logger.error(f"❌ Error en optimización con LLM: {e}")
            self.logger.info("⚠️ Activando sistema de fallback inteligente...")
            
            # 8. Fallback inteligente basado en reglas
            asignaciones_fallback = self._generar_asignaciones_inteligentes(
                tareas_normalizadas, 
                analisis_estudiantes
            )
            
            self.logger.info(f"✅ Asignaciones fallback generadas para {len(asignaciones_fallback)} estudiantes")
            return asignaciones_fallback

    def _normalizar_tareas_entrada(self, tareas_input) -> List[Dict]:
        """
        Normaliza diferentes tipos de entrada a una lista uniforme de tareas
        
        Args:
            tareas_input: Entrada variable (List, Dict, objeto actividad, etc.)
            
        Returns:
            Lista normalizada de diccionarios de tareas
        """
        tareas_normalizadas = []
        
        try:
            # Caso 1: Lista de objetos Tarea (dataclass)
            if isinstance(tareas_input, list):
                for i, tarea in enumerate(tareas_input):
                    if hasattr(tarea, '__dataclass_fields__'):  # Es dataclass
                        from dataclasses import asdict
                        tareas_normalizadas.append(asdict(tarea))
                    elif hasattr(tarea, '__dict__'):  # Es objeto con atributos
                        tareas_normalizadas.append(tarea.__dict__)
                    elif isinstance(tarea, dict):  # Ya es diccionario
                        tareas_normalizadas.append(tarea)
                    else:
                        # Crear tarea básica desde string u otro tipo
                        tareas_normalizadas.append({
                            'id': f'tarea_{i+1:02d}',
                            'descripcion': str(tarea),
                            'complejidad': 3,
                            'tipo': 'colaborativa',
                            'tiempo_estimado': 30
                        })
            
            # Caso 2: Diccionario con estructura de actividad (del analizador)
            elif isinstance(tareas_input, dict):
                if 'actividad' in tareas_input:
                    # Extraer tareas de la actividad JSON
                    actividad = tareas_input['actividad']
                    tareas_normalizadas = self._extraer_tareas_de_actividad(actividad)
                elif 'etapas' in tareas_input:
                    # Es directamente una actividad
                    tareas_normalizadas = self._extraer_tareas_de_actividad(tareas_input)
                else:
                    # Asumir que es una sola tarea
                    tareas_normalizadas = [tareas_input]
            
            # Caso 3: Otros tipos, convertir a tarea básica
            else:
                tareas_normalizadas = [{
                    'id': 'tarea_01',
                    'descripcion': str(tareas_input),
                    'complejidad': 3,
                    'tipo': 'colaborativa',
                    'tiempo_estimado': 30
                }]
            
            self.logger.debug(f"📝 Normalizadas {len(tareas_normalizadas)} tareas desde entrada tipo {type(tareas_input)}")
            
        except Exception as e:
            self.logger.error(f"❌ Error normalizando tareas: {e}")
            tareas_normalizadas = []
        
        return tareas_normalizadas

    def _extraer_tareas_de_actividad(self, actividad: Dict) -> List[Dict]:
        """
        Extrae tareas de una estructura de actividad JSON
        
        Args:
            actividad: Diccionario con estructura de actividad
            
        Returns:
            Lista de tareas normalizadas
        """
        if not isinstance(actividad, dict):
            self.logger.error(f"❌ Actividad no es un diccionario: {type(actividad)}")
            return []
        
        tareas_extraidas = []
        contador_tareas = 1
        
        etapas = actividad.get('etapas', [])
        
        if not etapas:
            self.logger.warning("⚠️ No se encontraron etapas en la actividad")
            # Crear una tarea básica desde la actividad completa
            return [{
                'id': 'tarea_01',
                'nombre': actividad.get('titulo', 'Actividad'),
                'descripcion': actividad.get('objetivo', 'Realizar la actividad propuesta'),
                'etapa': 'Principal',
                'formato_asignacion': 'grupos',
                'complejidad': 3,
                'tipo': 'colaborativa',
                'tiempo_estimado': 60,
                'competencias_requeridas': ['transversales'],
                'adaptaciones': {}
            }]
        
        for i, etapa in enumerate(etapas):
            if not isinstance(etapa, dict):
                self.logger.warning(f"⚠️ Etapa {i} no es un diccionario válido")
                continue
                
            nombre_etapa = etapa.get('nombre', f'Etapa {i+1}')
            tareas_etapa = etapa.get('tareas', [])
            
            if not isinstance(tareas_etapa, list):
                self.logger.warning(f"⚠️ Tareas de etapa '{nombre_etapa}' no es una lista")
                continue
            
            for j, tarea_data in enumerate(tareas_etapa):
                if not isinstance(tarea_data, dict):
                    self.logger.warning(f"⚠️ Tarea {j} en etapa '{nombre_etapa}' no es un diccionario")
                    continue
                    
                tarea_normalizada = {
                    'id': f'tarea_{contador_tareas:02d}',
                    'nombre': tarea_data.get('nombre', f'Tarea {contador_tareas}'),
                    'descripcion': tarea_data.get('descripcion', 'Tarea sin descripción'),
                    'etapa': nombre_etapa,
                    'formato_asignacion': tarea_data.get('formato_asignacion', 'grupos'),
                    'complejidad': self._estimar_complejidad_tarea(tarea_data),
                    'tipo': self._determinar_tipo_tarea(tarea_data),
                    'tiempo_estimado': self._estimar_tiempo_tarea(tarea_data),
                    'competencias_requeridas': self._extraer_competencias(tarea_data),
                    'adaptaciones': tarea_data.get('estrategias_adaptacion', {})
                }
                
                tareas_extraidas.append(tarea_normalizada)
                contador_tareas += 1
        
        if not tareas_extraidas:
            self.logger.warning("⚠️ No se pudieron extraer tareas válidas, creando tarea por defecto")
            return [{
                'id': 'tarea_01',
                'nombre': 'Actividad Principal',
                'descripcion': actividad.get('objetivo', 'Realizar la actividad propuesta'),
                'etapa': 'Principal',
                'formato_asignacion': 'grupos',
                'complejidad': 3,
                'tipo': 'colaborativa',
                'tiempo_estimado': 60,
                'competencias_requeridas': ['transversales'],
                'adaptaciones': {}
            }]
        
        self.logger.debug(f"📝 Extraídas {len(tareas_extraidas)} tareas de la actividad")
        return tareas_extraidas


    def _construir_prompt_optimizacion(self, tareas: List[Dict], analisis_estudiantes: Dict) -> str:
        """
        Construye prompt optimizado para el LLM
        
        Args:
            tareas: Lista de tareas normalizadas
            analisis_estudiantes: Análisis de estudiantes
            
        Returns:
            Prompt estructurado para el LLM
        """
        # Información de estudiantes del aula
        estudiantes_info = self._formatear_estudiantes_para_prompt()
        
        # Información de tareas
        tareas_info = self._formatear_tareas_para_prompt(tareas)
        
        # Análisis específico (si está disponible)
        analisis_info = self._formatear_analisis_para_prompt(analisis_estudiantes)
        
        prompt = f"""Eres un experto pedagogo especializado en Aprendizaje Basado en Proyectos (ABP) y Diseño Universal para el Aprendizaje (DUA).

    Tu misión es asignar tareas de manera óptima considerando las características específicas de cada estudiante.

    === ESTUDIANTES DEL AULA ===
    {estudiantes_info}

    === TAREAS DISPONIBLES ===
    {tareas_info}

    === ANÁLISIS ESPECÍFICO ===
    {analisis_info}

    === CRITERIOS DE ASIGNACIÓN ===
    1. INCLUSIÓN DUA: Cada estudiante debe tener tareas alineadas con sus fortalezas
    2. EQUILIBRIO: Distribuir carga de trabajo de manera equitativa
    3. ADAPTACIONES: Considerar necesidades específicas (TEA, TDAH, altas capacidades)
    4. COLABORACIÓN: Promover trabajo en equipo complementario
    5. DESARROLLO: Asignar algunas tareas ligeramente desafiantes para crecimiento

    === INSTRUCCIONES ESPECÍFICAS ===
    - Elena (TEA): Tareas estructuradas, rutinas predecibles, menos cambios de contexto
    - Luis (TDAH): Tareas dinámicas, que permitan movimiento, variadas
    - Ana (Altas capacidades): Puede liderar, asumir mayor complejidad, mentoría
    - Alex/Sara: Balancear según fortalezas individuales
    - Cada estudiante debe tener 2-4 tareas según capacidad y disponibilidad

    RESPONDE ÚNICAMENTE CON ESTE JSON (sin texto adicional):
    {{
        "asignaciones": {{
            "001": ["tarea_01", "tarea_03"],
            "002": ["tarea_02", "tarea_04"],
            "003": ["tarea_05"],
            "004": ["tarea_06", "tarea_07"],
            "005": ["tarea_08", "tarea_01"],
            "006": ["tarea_02"],
            "007": ["tarea_03", "tarea_09"],
            "008": ["tarea_04", "tarea_10"]
        }},
        "explicacion": {{
            "criterio_principal": "Asignación basada en fortalezas y necesidades DUA",
            "adaptaciones_aplicadas": ["TEA_estructura", "TDAH_dinamismo", "AC_liderazgo"],
            "equilibrio_carga": "2-4 tareas por estudiante según capacidad"
        }}
    }}"""
        
        return prompt

    def _formatear_estudiantes_para_prompt(self) -> str:
        """Formatea información de estudiantes para el prompt"""
        info_estudiantes = []
        
        for estudiante_id, estudiante in self.perfiles.items():
            if hasattr(estudiante, 'nombre'):
                nombre = estudiante.nombre
                fortalezas = estudiante.fortalezas if hasattr(estudiante, 'fortalezas') else []
                necesidades = estudiante.necesidades_apoyo if hasattr(estudiante, 'necesidades_apoyo') else []
                disponibilidad = estudiante.disponibilidad if hasattr(estudiante, 'disponibilidad') else 85
            else:
                # Si es diccionario
                nombre = estudiante.get('nombre', f'Estudiante_{estudiante_id}')
                fortalezas = estudiante.get('fortalezas', [])
                necesidades = estudiante.get('necesidades_apoyo', [])
                disponibilidad = estudiante.get('disponibilidad', 85)
            
            info_estudiante = f"- {estudiante_id} ({nombre}):\n"
            info_estudiante += f"  * Fortalezas: {', '.join(fortalezas) if fortalezas else 'Generales'}\n"
            info_estudiante += f"  * Necesidades apoyo: {', '.join(necesidades) if necesidades else 'Ninguna específica'}\n"
            info_estudiante += f"  * Disponibilidad: {disponibilidad}%\n"
            
            info_estudiantes.append(info_estudiante)
        
        return "\n".join(info_estudiantes)

    def _formatear_tareas_para_prompt(self, tareas: List[Dict]) -> str:
        """Formatea tareas para el prompt del LLM"""
        info_tareas = []
        
        for tarea in tareas:
            tarea_id = tarea.get('id', 'sin_id')
            descripcion = tarea.get('descripcion', 'Sin descripción')
            complejidad = tarea.get('complejidad', 3)
            tipo = tarea.get('tipo', 'colaborativa')
            tiempo = tarea.get('tiempo_estimado', 30)
            etapa = tarea.get('etapa', 'General')
            
            info_tarea = f"- {tarea_id}: {descripcion}\n"
            info_tarea += f"  * Etapa: {etapa}\n"
            info_tarea += f"  * Complejidad: {complejidad}/5, Tipo: {tipo}, Tiempo: {tiempo}min\n"
            
            info_tareas.append(info_tarea)
        
        return "\n".join(info_tareas)

    def _formatear_analisis_para_prompt(self, analisis: Dict) -> str:
        """Formatea análisis de estudiantes para el prompt"""
        if not analisis or not isinstance(analisis, dict):
            return "Análisis específico no disponible - usar criterios generales DUA"
        
        info_analisis = []
        for estudiante_id, datos in analisis.items():
            if isinstance(datos, dict):
                info_analisis.append(f"- {estudiante_id}:")
                info_analisis.append(f"  * Tareas compatibles: {', '.join(datos.get('tareas_compatibles', []))}")
                info_analisis.append(f"  * Rol sugerido: {datos.get('rol_sugerido', 'Colaborador')}")
        
        return "\n".join(info_analisis) if info_analisis else "Análisis detallado no disponible"

    def _parsear_respuesta_llm(self, respuesta: str) -> Optional[Dict]:
        """
        Parsea la respuesta del LLM de manera robusta
        
        Args:
            respuesta: Respuesta cruda del LLM
            
        Returns:
            Diccionario con asignaciones o None si falla
        """
        if not respuesta or not isinstance(respuesta, str):
            self.logger.error("❌ Respuesta del LLM vacía o inválida")
            return None
        
        try:
            # Estrategia 1: Parseo JSON directo
            resultado = parse_json_seguro(respuesta)
            
            if resultado and isinstance(resultado, dict) and 'asignaciones' in resultado:
                self.logger.debug("✅ Parseo JSON directo exitoso")
                return resultado['asignaciones']
            
            # Estrategia 2: Buscar JSON embebido con regex más específico
            json_match = re.search(
                r'\{\s*"asignaciones"\s*:\s*\{[^}]*\}(?:\s*,\s*"[^"]*"\s*:\s*\{[^}]*\})?\s*\}', 
                respuesta, 
                re.DOTALL
            )
            
            if json_match:
                json_text = json_match.group()
                try:
                    parsed = json.loads(json_text)
                    if 'asignaciones' in parsed and isinstance(parsed['asignaciones'], dict):
                        self.logger.debug("✅ Parseo JSON embebido exitoso")
                        return parsed['asignaciones']
                except json.JSONDecodeError as e:
                    self.logger.warning(f"⚠️ Error en parseo JSON embebido: {e}")
            
            # Estrategia 3: Parseo línea por línea
            resultado_manual = self._parsear_respuesta_manual(respuesta)
            if resultado_manual:
                self.logger.debug("✅ Parseo manual exitoso")
                return resultado_manual
            
            self.logger.warning("⚠️ Todas las estrategias de parseo fallaron")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico parseando respuesta LLM: {e}")
            return None

    def _parsear_respuesta_manual(self, respuesta: str) -> Dict:
        """Parsea respuesta manualmente si JSON falla"""
        asignaciones = {}
        
        lines = respuesta.split('\n')
        for line in lines:
            # Buscar patrones como "001": ["tarea_01", "tarea_02"] o "estudiante_001": ["tarea_01", "tarea_02"]
            if ('estudiante_' in line or ('"00' in line and '"' in line)) and '[' in line:
                try:
                    parts = line.split(':')
                    estudiante_id = parts[0].strip().replace('"', '').replace(',', '')
                    
                    # Normalizar ID: quitar 'estudiante_' si está presente
                    if estudiante_id.startswith('estudiante_'):
                        estudiante_id = estudiante_id.replace('estudiante_', '')
                    
                    tareas_part = ':'.join(parts[1:]).strip()
                    
                    # Extraer tareas entre corchetes
                    import re
                    tareas_match = re.findall(r'"(tarea_\d+)"', tareas_part)
                    if tareas_match:
                        asignaciones[estudiante_id] = tareas_match
                except:
                    continue
        
        return asignaciones if asignaciones else None

    def _validar_y_completar_asignaciones(self, asignaciones: Dict, tareas: List[Dict]) -> Dict:
        """
        Valida y completa las asignaciones generadas
        
        Args:
            asignaciones: Asignaciones desde LLM
            tareas: Lista de tareas disponibles
            
        Returns:
            Asignaciones validadas y completadas
        """
        if not asignaciones:
            return {}
        
        tareas_ids_disponibles = {tarea['id'] for tarea in tareas}
        estudiantes_sistema = set(self.perfiles.keys())
        asignaciones_validadas = {}
        
        # Validar cada asignación
        for estudiante_id, tareas_asignadas in asignaciones.items():
            # Normalizar ID de estudiante
            estudiante_id_normalizado = estudiante_id
            if estudiante_id.startswith('estudiante_'):
                estudiante_id_normalizado = estudiante_id.replace('estudiante_', '')
            
            # Verificar que el estudiante existe
            if estudiante_id_normalizado not in estudiantes_sistema:
                self.logger.warning(f"⚠️ Estudiante {estudiante_id_normalizado} no existe en sistema")
                continue
            
            # Filtrar tareas válidas
            tareas_validas = [t for t in tareas_asignadas if t in tareas_ids_disponibles]
            
            if tareas_validas:
                asignaciones_validadas[estudiante_id_normalizado] = tareas_validas
            else:
                self.logger.warning(f"⚠️ No hay tareas válidas para {estudiante_id_normalizado}")
        
        # Completar estudiantes sin asignaciones
        estudiantes_sin_asignacion = estudiantes_sistema - set(asignaciones_validadas.keys())
        if estudiantes_sin_asignacion:
            self.logger.info(f"📝 Completando asignaciones para {len(estudiantes_sin_asignacion)} estudiantes")
            asignaciones_completadas = self._completar_asignaciones_faltantes(
                asignaciones_validadas, 
                estudiantes_sin_asignacion, 
                tareas
            )
            asignaciones_validadas.update(asignaciones_completadas)
        
        return asignaciones_validadas

    def _generar_asignaciones_inteligentes(self, tareas: List[Dict], analisis_estudiantes: Dict) -> Dict:
        """
        Genera asignaciones usando lógica basada en reglas (fallback inteligente)
        
        Args:
            tareas: Lista de tareas normalizadas
            analisis_estudiantes: Análisis de estudiantes
            
        Returns:
            Diccionario con asignaciones basadas en reglas
        """
        if not tareas or not self.perfiles:
            return {}
        
        self.logger.info("🧠 Generando asignaciones con lógica basada en reglas...")
        
        asignaciones = {}
        tareas_disponibles = tareas.copy()
        estudiantes_ids = list(self.perfiles.keys())
        
        # Distribuir tareas según capacidades y necesidades
        for i, estudiante_id in enumerate(estudiantes_ids):
            estudiante = self.perfiles[estudiante_id]
            
            # Determinar número de tareas según disponibilidad
            if hasattr(estudiante, 'disponibilidad'):
                disponibilidad = estudiante.disponibilidad
            else:
                disponibilidad = estudiante.get('disponibilidad', 85) if isinstance(estudiante, dict) else 85
            
            if disponibilidad > 85:
                num_tareas = min(4, len(tareas_disponibles))
            elif disponibilidad > 70:
                num_tareas = min(3, len(tareas_disponibles))
            else:
                num_tareas = min(2, len(tareas_disponibles))
            
            # Seleccionar tareas apropiadas
            tareas_estudiante = self._seleccionar_tareas_para_estudiante(
                estudiante, 
                tareas_disponibles, 
                num_tareas
            )
            
            if tareas_estudiante:
                asignaciones[estudiante_id] = [t['id'] for t in tareas_estudiante]
                # Remover tareas asignadas de disponibles
                for tarea in tareas_estudiante:
                    if tarea in tareas_disponibles:
                        tareas_disponibles.remove(tarea)
        
        return asignaciones
    def _generar_asignaciones_fallback(self, tareas: List[Dict]) -> Dict:
        """
        Genera asignaciones básicas de fallback cuando no hay perfiles
        
        Args:
            tareas: Lista de tareas disponibles
            
        Returns:
            Diccionario con asignaciones básicas
        """
        if not tareas:
            return {}
        
        # Crear estudiantes ficticios si no hay perfiles
        estudiantes_ficticios = [
            f"estudiante_{i+1:03d}" for i in range(8)  # 8 estudiantes por defecto
        ]
        
        asignaciones_basicas = {}
        num_estudiantes = len(estudiantes_ficticios)
        
        # Distribución equitativa
        tareas_por_estudiante = len(tareas) // num_estudiantes
        tareas_extra = len(tareas) % num_estudiantes
        
        indice_tarea = 0
        
        for i, estudiante_id in enumerate(estudiantes_ficticios):
            # Calcular número de tareas para este estudiante
            num_tareas_estudiante = tareas_por_estudiante
            if i < tareas_extra:
                num_tareas_estudiante += 1
            
            # Asignar tareas
            tareas_estudiante = []
            for _ in range(num_tareas_estudiante):
                if indice_tarea < len(tareas):
                    tareas_estudiante.append(tareas[indice_tarea]['id'])
                    indice_tarea += 1
            
            if tareas_estudiante:  # Solo asignar si hay tareas
                asignaciones_basicas[estudiante_id] = tareas_estudiante
        
        self.logger.info(f"✅ Asignaciones básicas fallback creadas para {len(asignaciones_basicas)} estudiantes")
        return asignaciones_basicas
    def _seleccionar_tareas_para_estudiante(self, estudiante, tareas_disponibles: List[Dict], num_tareas: int) -> List[Dict]:
        """Selecciona tareas apropiadas para un estudiante específico"""
        if not tareas_disponibles:
            return []
        
        # Obtener características del estudiante
        if hasattr(estudiante, 'fortalezas'):
            fortalezas = estudiante.fortalezas
            necesidades = estudiante.necesidades_apoyo
        else:
            fortalezas = estudiante.get('fortalezas', []) if isinstance(estudiante, dict) else []
            necesidades = estudiante.get('necesidades_apoyo', []) if isinstance(estudiante, dict) else []
        
        tareas_puntuadas = []
        
        for tarea in tareas_disponibles:
            puntuacion = 0
            
            # Puntuación base
            puntuacion += 1
            
            # Bonus por alineación con fortalezas
            if any(fortaleza in tarea.get('descripcion', '').lower() for fortaleza in fortalezas):
                puntuacion += 2
            
            # Ajuste por complejidad
            complejidad = tarea.get('complejidad', 3)
            if 'altas_capacidades' in necesidades and complejidad >= 4:
                puntuacion += 1
            elif 'apoyo_adicional' in necesidades and complejidad <= 2:
                puntuacion += 1
            
            # Penalización por inadecuación
            if 'TEA' in necesidades and tarea.get('tipo') == 'creativa':
                puntuacion -= 1
            if 'TDAH' in necesidades and complejidad >= 4:
                puntuacion -= 0.5
            
            tareas_puntuadas.append((tarea, puntuacion))
        
        # Ordenar por puntuación y seleccionar las mejores
        tareas_puntuadas.sort(key=lambda x: x[1], reverse=True)
        return [tarea for tarea, _ in tareas_puntuadas[:num_tareas]]

    # Métodos de utilidad adicionales
    def _estimar_complejidad_tarea(self, tarea_data: Dict) -> int:
        """Estima complejidad de tarea basada en descripción"""
        descripcion = tarea_data.get('descripcion', '').lower()
        
        if any(word in descripcion for word in ['analizar', 'evaluar', 'crear', 'diseñar']):
            return 4
        elif any(word in descripcion for word in ['comparar', 'explicar', 'aplicar']):
            return 3
        elif any(word in descripcion for word in ['identificar', 'listar', 'describir']):
            return 2
        else:
            return 3  # Por defecto

    def _determinar_tipo_tarea(self, tarea_data: Dict) -> str:
        """Determina tipo de tarea basado en formato de asignación"""
        formato = tarea_data.get('formato_asignacion', '').lower()
        
        if 'grupos' in formato or 'parejas' in formato:
            return 'colaborativa'
        elif 'individual' in formato:
            return 'individual'
        elif 'aula completa' in formato:
            return 'colaborativa'
        else:
            return 'colaborativa'  # Por defecto

    def _estimar_tiempo_tarea(self, tarea_data: Dict) -> int:
        """Estima tiempo de tarea en minutos"""
        descripcion = tarea_data.get('descripcion', '').lower()
        
        if any(word in descripcion for word in ['presentar', 'exposición', 'debate']):
            return 45
        elif any(word in descripcion for word in ['crear', 'construir', 'diseñar']):
            return 60
        elif any(word in descripcion for word in ['investigar', 'buscar', 'recopilar']):
            return 40
        else:
            return 30  # Por defecto

    def _extraer_competencias(self, tarea_data: Dict) -> List[str]:
        """Extrae competencias requeridas basadas en descripción de tarea"""
        descripcion = tarea_data.get('descripcion', '').lower()
        competencias = []
        
        if any(word in descripcion for word in ['matemáticas', 'números', 'cálculo']):
            competencias.append('matemáticas')
        if any(word in descripcion for word in ['lectura', 'escritura', 'texto']):
            competencias.append('lengua')
        if any(word in descripcion for word in ['ciencias', 'experimento', 'investigación']):
            competencias.append('ciencias')
        if any(word in descripcion for word in ['arte', 'diseño', 'creativo']):
            competencias.append('creatividad')
        if any(word in descripcion for word in ['presentar', 'exponer', 'comunicar']):
            competencias.append('comunicación')
        
        return competencias if competencias else ['transversales']

    def _completar_asignaciones_faltantes(self, asignaciones_actuales: Dict, estudiantes_faltantes: set, tareas: List[Dict]) -> Dict:
        """Completa asignaciones para estudiantes que no recibieron tareas"""
        asignaciones_completadas = {}
        tareas_no_asignadas = []
        
        # Identificar tareas no asignadas
        tareas_asignadas = set()
        for tareas_est in asignaciones_actuales.values():
            tareas_asignadas.update(tareas_est)
        
        for tarea in tareas:
            if tarea['id'] not in tareas_asignadas:
                tareas_no_asignadas.append(tarea)
        
        # Asignar tareas restantes
        estudiantes_faltantes_list = list(estudiantes_faltantes)
        for i, estudiante_id in enumerate(estudiantes_faltantes_list):
            if i < len(tareas_no_asignadas):
                asignaciones_completadas[estudiante_id] = [tareas_no_asignadas[i]['id']]
            else:
                # Si no hay más tareas, asignar una básica
                asignaciones_completadas[estudiante_id] = ['tarea_01']  # Fallback
        
        return asignaciones_completadas
    
    # Implementación de métodos abstractos de BaseAgent
    def process(self, tareas: List[Tarea], analisis_estudiantes: Dict, **kwargs) -> Dict:
        """
        Implementa el método abstracto process de BaseAgent
        
        Args:
            tareas: Lista de tareas
            analisis_estudiantes: Análisis de compatibilidades
            **kwargs: Parámetros adicionales
            
        Returns:
            Diccionario con asignaciones optimizadas
        """
        return self.optimizar_asignaciones(tareas, analisis_estudiantes, **kwargs)
    
    def _parse_response(self, response: str) -> Dict:
        """
        Parsea respuesta del LLM para asignaciones
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Diccionario con asignaciones
        """
        json_data = parse_json_seguro(response)
        if json_data and 'asignaciones' in json_data:
            return json_data['asignaciones']
        return {}