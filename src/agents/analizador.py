"""
Agente Analizador de Tareas (Task Analyzer Agent).
"""

import logging
import re
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator
from agents.base_agent import BaseAgent
from models.proyecto import Tarea

class AgenteAnalizadorTareas(BaseAgent):
    """Agente Analizador de Tareas (Task Analyzer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """
        Inicializa el Agente Analizador de Tareas
        
        Args:
            ollama_integrator: Integrador de LLM
        """
        super().__init__(ollama_integrator)
    
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