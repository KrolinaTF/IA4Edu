"""
Agente Analizador de Tareas (Task Analyzer Agent).
"""

import logging
import re
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator
from core.embeddings_manager import EmbeddingsManager
from agents.base_agent import BaseAgent
from models.proyecto import Tarea

class AgenteAnalizadorTareas(BaseAgent):
    """Agente Analizador de Tareas (Task Analyzer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator, embeddings_manager: EmbeddingsManager = None):
        """
        Inicializa el Agente Analizador de Tareas
        
        Args:
            ollama_integrator: Integrador de LLM
            embeddings_manager: Gestor de embeddings (opcional, se inicializa automáticamente)
        """
        super().__init__(ollama_integrator)
        
        # Inicializar EmbeddingsManager si no se proporciona
        if embeddings_manager is None:
            import os
            # Ruta a las actividades JSON
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            actividades_path = os.path.join(base_dir, "..", "data", "actividades", "json_actividades")
            
            self.embeddings_manager = EmbeddingsManager(actividades_path, ollama_integrator)
        else:
            self.embeddings_manager = embeddings_manager
    
    def descomponer_actividad(self, proyecto_base: Dict, **kwargs) -> List[Tarea]:
        """
        Descompone la actividad en subtareas específicas
        
        Args:
            proyecto_base: Diccionario con información del proyecto
            **kwargs: Parámetros adicionales (no usados actualmente)
            
        Returns:
            Lista de objetos Tarea
        """
        
        prompt_tareas = f"""
Analiza este proyecto educativo siguiendo los patrones exitosos de actividades k_ y descomponlo en subtareas específicas:

PROYECTO: {proyecto_base['titulo']}
DESCRIPCIÓN: {proyecto_base['descripcion']}
NIVEL: {proyecto_base['nivel']}
DURACIÓN: {proyecto_base['duracion_base']}
INFORMACIÓN ADICIONAL: {proyecto_base.get('info_adicional', 'No disponible')}

=== PATRONES EXITOSOS K_ ===
• NARRATIVA INMERSIVA: Mantener contexto atractivo en cada tarea (ofrecer opciones con y sin narrativa)
• ESTRUCTURA PEDAGÓGICA: Preparación → Desarrollo → Reflexión (si el profesor solicita otra estructura, dar prioridad a la suya)
• ROLES ESPECÍFICOS: Asignar roles concretos según fortalezas (Si la actividad tiene roles, si no, repartir las tareas sin un rol concreto)
• MATERIAL MANIPULATIVO: Usar objetos reales y tangibles a ser posible, reciclados o accesibles NO tecnológicos. siempre analogicos
• ADAPTACIONES DUA: Considerar TEA, TDAH, altas capacidades. Expras en qué se traduce la adaptación en esta actividad concreta
• EVALUACIÓN FORMATIVA: Observación y registro continuo

=== ESTRUCTURA RECOMENDADA === adaptar completamente a la especificación del profesor
1. PREPARACIÓN: Contextualización y organización (tantas tareas como requiera la actividad)
2. DESARROLLO: Núcleo de la actividad (tantas tareas como requiera la complejidad del proyecto)
3. REFLEXIÓN: Metacognición y cierre (según necesidades de evaluación)

Identifica las subtareas necesarias para completar el proyecto (sin límite fijo, según la complejidad de la actividad). Para cada subtarea proporciona:
- Descripción clara y específica (con contexto narrativo si se solicita)
- Competencias requeridas (matemáticas, lengua, ciencias, creativas, digitales)
- Complejidad del 1 al 5 (1=muy fácil, 5=muy difícil)
- Tipo: individual, colaborativa, o creativa
- Tiempo estimado en horas
- Dependencias (qué tareas deben completarse antes)
- Adaptaciones sugeridas

Formato:
TAREA 1:
Descripción: [descripción específica con contexto narrativo]
Competencias: [competencias separadas por comas]
Complejidad: [1-5]
Tipo: [individual/colaborativa/creativa]
Tiempo: [horas]
Dependencias: [ninguna o nombre de tareas previas]
Adaptaciones: [adaptaciones específicas para diversidad]

[Repetir para todas las tareas siguiendo estructura Preparación-Desarrollo-Reflexión...]
"""
        
        self._log_processing_start(f"Descomponiendo actividad: {proyecto_base.get('titulo', 'Sin título')}")
        
        # Llamar al LLM con fallback
        respuesta = self.ollama.generar_respuesta(prompt_tareas, max_tokens=800)
        tareas = self._parsear_tareas(respuesta)
        
        if not tareas:
            self.logger.warning("❌ No se pudieron extraer tareas de la respuesta del LLM, usando fallback")
            tareas = self._crear_tareas_fallback()
        
        self._log_processing_end(f"Generadas {len(tareas)} tareas")
        return tareas
    
    def seleccionar_y_adaptar_actividad(self, prompt: str) -> Dict[str, Any]:
        """
        Selecciona la actividad más adecuada usando embeddings y la adapta mínimamente
        
        Args:
            prompt: Prompt del usuario describiendo la actividad deseada
            
        Returns:
            Diccionario con la actividad seleccionada y adaptaciones
        """
        self._log_processing_start(f"Seleccionando actividad para: '{prompt[:50]}...'")
        
        try:
            # 1. Buscar actividades similares usando embeddings
            actividades_candidatas = self.embeddings_manager.encontrar_actividad_similar(prompt, top_k=3)
            
            if not actividades_candidatas:
                self.logger.warning("❌ No se encontraron actividades candidatas, usando fallback")
                return self._crear_actividad_fallback(prompt)
            
            # 2. Analizar similitud de la mejor candidata
            mejor_actividad_id, mejor_similitud, mejor_actividad_data = actividades_candidatas[0]
            
            self.logger.info(f"🎯 Mejor match: {mejor_actividad_id} (similitud: {mejor_similitud:.3f})")
            
            # 3. Decidir estrategia basada en similitud
            if mejor_similitud > 0.7:
                # Alta similitud: usar actividad completa con adaptaciones mínimas
                resultado = self._adaptar_actividad_existente(mejor_actividad_data, prompt)
                resultado['estrategia'] = 'adaptacion_minima'
                resultado['similitud'] = mejor_similitud
                
            elif mejor_similitud > 0.4:
                # Similitud media: usar como inspiración y adaptar más
                resultado = self._inspirar_en_actividad(mejor_actividad_data, prompt, actividades_candidatas)
                resultado['estrategia'] = 'inspiracion_adaptada'
                resultado['similitud'] = mejor_similitud
                
            else:
                # Similitud baja: crear nueva usando estructura base
                resultado = self._crear_actividad_nueva(prompt, mejor_actividad_data)
                resultado['estrategia'] = 'creacion_nueva'
                resultado['similitud'] = mejor_similitud
            
            resultado['actividad_fuente'] = mejor_actividad_id
            
            self._log_processing_end(f"Actividad seleccionada: {resultado['estrategia']}")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Error en selección de actividad: {e}")
            return self._crear_actividad_fallback(prompt)
    
    def _adaptar_actividad_existente(self, actividad_data: dict, prompt: str) -> Dict[str, Any]:
        """
        Adapta mínimamente una actividad existente de alta similitud
        
        Args:
            actividad_data: Datos de la actividad base
            prompt: Prompt original del usuario
            
        Returns:
            Actividad con adaptaciones mínimas
        """
        # Copiar actividad base
        actividad_adaptada = actividad_data.copy()
        
        # Lista de adaptaciones menores aplicadas
        adaptaciones = []
        
        # Adaptar título si el prompt menciona contexto específico
        titulo_original = actividad_data.get('titulo', '')
        if 'fracciones' in prompt.lower() and 'fracciones' not in titulo_original.lower():
            actividad_adaptada['titulo'] = titulo_original + ' - Enfoque en Fracciones'
            adaptaciones.append('titulo_especializado')
        
        # Adaptar duración si se especifica
        if 'sesión' in prompt.lower() or 'clase' in prompt.lower():
            actividad_adaptada['duracion_minutos'] = '50 minutos (1 sesión)'
            adaptaciones.append('duracion_ajustada')
        
        return {
            'actividad': actividad_adaptada,
            'adaptaciones_aplicadas': adaptaciones,
            'tipo_adaptacion': 'minima',
            'actividad_original_preservada': True
        }
    
    def _inspirar_en_actividad(self, actividad_data: dict, prompt: str, candidatas: list) -> Dict[str, Any]:
        """
        Usa una actividad como inspiración y adapta significativamente
        
        Args:
            actividad_data: Actividad base de inspiración
            prompt: Prompt original
            candidatas: Lista de actividades candidatas
            
        Returns:
            Actividad inspirada con adaptaciones significativas
        """
        # Generar nueva actividad usando LLM con la estructura base
        prompt_adaptacion = f"""
Basándote en esta actividad exitosa como INSPIRACIÓN (NO copia exacta):

ACTIVIDAD BASE: {actividad_data.get('titulo', '')}
OBJETIVO BASE: {actividad_data.get('objetivo', '')}
ESTRUCTURA BASE: {len(actividad_data.get('etapas', []))} etapas

NUEVA SOLICITUD DEL USUARIO: {prompt}

Crea una actividad NUEVA que:
1. Use la ESTRUCTURA pedagógica de la actividad base
2. Adapte el CONTENIDO completamente al nuevo tema solicitado  
3. Mantenga el FORMATO JSON de etapas y tareas
4. Incluya adaptaciones DUA específicas

Responde SOLO con la actividad adaptada, NO explicaciones adicionales.
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_adaptacion, max_tokens=600)
        
        try:
            # Intentar parsear respuesta como JSON o texto estructurado
            actividad_inspirada = self._parsear_actividad_adaptada(respuesta, actividad_data)
        except Exception as e:
            self.logger.warning(f"⚠️ Error parseando actividad inspirada: {e}")
            actividad_inspirada = actividad_data.copy()  # Fallback a original
        
        return {
            'actividad': actividad_inspirada,
            'adaptaciones_aplicadas': ['estructura_mantenida', 'contenido_adaptado'],
            'tipo_adaptacion': 'inspiracion',
            'actividad_original_preservada': False
        }
    
    def _crear_actividad_nueva(self, prompt: str, referencia_data: dict) -> Dict[str, Any]:
        """
        Crea una actividad completamente nueva usando estructura de referencia
        
        Args:
            prompt: Prompt del usuario
            referencia_data: Actividad de referencia para estructura
            
        Returns:
            Actividad nueva creada
        """
        # Usar el método existente de descomposición como base
        proyecto_base = {
            'titulo': 'Actividad Personalizada',
            'descripcion': prompt,
            'nivel': '4º Primaria',
            'duracion_base': '2-3 sesiones',
            'info_adicional': 'Basada en solicitud específica del usuario'
        }
        
        tareas = self.descomponer_actividad(proyecto_base)
        
        # Convertir tareas a estructura de actividad JSON
        actividad_nueva = {
            'id': 'ACT_NUEVA',
            'titulo': f'Actividad: {prompt[:50]}...',
            'objetivo': f'Desarrollar competencias mediante: {prompt}',
            'nivel_educativo': '4º Primaria',
            'duracion_minutos': '2-3 sesiones',
            'etapas': self._convertir_tareas_a_etapas(tareas),
            'recursos': ['Materiales básicos del aula', 'Recursos específicos según necesidades'],
            'observaciones': 'Actividad creada automáticamente. Revisar adaptaciones específicas.'
        }
        
        return {
            'actividad': actividad_nueva,
            'adaptaciones_aplicadas': ['creacion_completa'],
            'tipo_adaptacion': 'nueva',
            'actividad_original_preservada': False
        }
    
    def _convertir_tareas_a_etapas(self, tareas: List[Tarea]) -> List[dict]:
        """
        Convierte lista de Tareas a estructura de etapas JSON
        
        Args:
            tareas: Lista de objetos Tarea
            
        Returns:
            Lista de etapas en formato JSON
        """
        etapas = []
        etapa_actual = None
        tareas_etapa = []
        
        for tarea in tareas:
            # Agrupar tareas en etapas según dependencias
            if not tarea.dependencias or etapa_actual is None:
                # Nueva etapa
                if etapa_actual is not None:
                    etapas.append({
                        'nombre': etapa_actual,
                        'descripcion': f'Etapa {len(etapas) + 1} de la actividad',
                        'tareas': tareas_etapa
                    })
                
                etapa_actual = f'Etapa {len(etapas) + 1}'
                tareas_etapa = []
            
            # Añadir tarea a la etapa actual
            tareas_etapa.append({
                'nombre': tarea.id,
                'descripcion': tarea.descripcion,
                'formato_asignacion': 'grupos' if tarea.tipo == 'colaborativa' else 'individual'
            })
        
        # Añadir última etapa
        if etapa_actual and tareas_etapa:
            etapas.append({
                'nombre': etapa_actual,
                'descripcion': f'Etapa {len(etapas) + 1} de la actividad',
                'tareas': tareas_etapa
            })
        
        return etapas
    
    def _parsear_actividad_adaptada(self, respuesta: str, base_data: dict) -> dict:
        """
        Parsea respuesta del LLM para actividad adaptada
        
        Args:
            respuesta: Respuesta cruda del LLM
            base_data: Datos base como fallback
            
        Returns:
            Diccionario con actividad parseada
        """
        try:
            import json
            # Intentar parsear como JSON directo
            if respuesta.strip().startswith('{'):
                return json.loads(respuesta)
        except:
            pass
        
        # Fallback: extraer campos clave y usar estructura base
        actividad = base_data.copy()
        
        # Extraer título
        titulo_match = re.search(r'título[:\s]*([^\n]+)', respuesta, re.IGNORECASE)
        if titulo_match:
            actividad['titulo'] = titulo_match.group(1).strip()
        
        # Extraer objetivo
        objetivo_match = re.search(r'objetivo[:\s]*([^\n]+)', respuesta, re.IGNORECASE)
        if objetivo_match:
            actividad['objetivo'] = objetivo_match.group(1).strip()
        
        return actividad
    
    def _crear_actividad_fallback(self, prompt: str) -> Dict[str, Any]:
        """
        Crea actividad fallback cuando todo falla
        
        Args:
            prompt: Prompt original
            
        Returns:
            Actividad fallback básica
        """
        actividad_fallback = {
            'id': 'ACT_FALLBACK',
            'titulo': f'Actividad Personalizada: {prompt[:30]}...',
            'objetivo': 'Desarrollar competencias mediante trabajo colaborativo',
            'nivel_educativo': '4º Primaria',
            'duracion_minutos': '2 sesiones',
            'etapas': [
                {
                    'nombre': 'Preparación',
                    'descripcion': 'Introducción y organización de la actividad',
                    'tareas': [{'nombre': 'Contextualización', 'descripcion': 'Presentar la actividad al alumnado'}]
                },
                {
                    'nombre': 'Desarrollo',
                    'descripcion': 'Desarrollo principal de la actividad',
                    'tareas': [{'nombre': 'Trabajo colaborativo', 'descripcion': 'Realizar la actividad en grupos'}]
                },
                {
                    'nombre': 'Cierre',
                    'descripcion': 'Presentación y reflexión final',
                    'tareas': [{'nombre': 'Presentación', 'descripcion': 'Presentar resultados y reflexionar'}]
                }
            ],
            'recursos': ['Materiales básicos del aula'],
            'observaciones': 'Actividad generada automáticamente como fallback'
        }
        
        return {
            'actividad': actividad_fallback,
            'adaptaciones_aplicadas': ['fallback_generado'],
            'tipo_adaptacion': 'fallback',
            'actividad_original_preservada': False,
            'similitud': 0.0
        }
    
    def _parsear_tareas(self, respuesta: str) -> List[Tarea]:
        """
        Parsea la respuesta para crear objetos Tarea
        
        Args:
            respuesta: Respuesta del LLM
            
        Returns:
            Lista de objetos Tarea
        """
        tareas = []
        partes = respuesta.split("TAREA ")
        
        for i, parte in enumerate(partes[1:]):  # Saltar el primer elemento vacío
            if not parte.strip():
                continue
                
            tarea = Tarea(
                id=f"tarea_{i+1:02d}",
                descripcion=self._extraer_campo(parte, "Descripción:"),
                competencias_requeridas=self._extraer_lista(parte, "Competencias:"),
                complejidad=self._extraer_numero(parte, "Complejidad:", 3),
                tipo=self._extraer_campo(parte, "Tipo:"),
                dependencias=self._extraer_lista(parte, "Dependencias:"),
                tiempo_estimado=self._extraer_numero(parte, "Tiempo:", 2)
            )
            tareas.append(tarea)
        
        return tareas
    
    def process(self, proyecto_base: Dict) -> List[Tarea]:
        """
        Implementa el método abstracto process de BaseAgent
        
        Args:
            proyecto_base: Diccionario con información del proyecto
            
        Returns:
            Lista de objetos Tarea
        """
        return self.descomponer_actividad(proyecto_base)
    
    def _parse_response(self, response: str) -> List[Dict]:
        """
        Parsea respuesta del LLM para tareas
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Lista de diccionarios con tareas
        """
        return self._parsear_tareas(response)
    
    def _crear_tareas_fallback(self) -> List[Tarea]:
        """
        Crea tareas genéricas como fallback
        
        Returns:
            Lista de objetos Tarea
        """
        return [
            Tarea(
                id="tarea_01",
                descripcion="Preparación y contextualización de la actividad",
                competencias_requeridas=["organizativas"],
                complejidad=2,
                tipo="individual",
                dependencias=[],
                tiempo_estimado=30
            ),
            Tarea(
                id="tarea_02",
                descripcion="Desarrollo principal de la actividad",
                competencias_requeridas=["específicas del proyecto"],
                complejidad=3,
                tipo="colaborativa", 
                dependencias=["tarea_01"],
                tiempo_estimado=60
            ),
            Tarea(
                id="tarea_03",
                descripcion="Reflexión y cierre de la actividad",
                competencias_requeridas=["metacognitivas"],
                complejidad=2,
                tipo="individual",
                dependencias=["tarea_02"],
                tiempo_estimado=20
            )
        ]