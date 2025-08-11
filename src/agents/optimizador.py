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

    def optimizar_asignaciones(self, tareas: List[Tarea], analisis_estudiantes: Dict, perfilador=None, **kwargs) -> Dict:
        """
        Optimiza las asignaciones de tareas basándose en el análisis de perfiles
        
        Args:
            tareas: Lista de tareas
            analisis_estudiantes: Análisis de compatibilidades entre estudiantes y tareas
            perfilador: Referencia al perfilador (opcional)
            **kwargs: Parámetros adicionales
            
        Returns:
            Diccionario con asignaciones optimizadas
        """
        # Actualizar perfiles si se proporciona perfilador
        if perfilador and hasattr(perfilador, 'perfiles_base'):
            self.perfiles = {e.id: e for e in perfilador.perfiles_base}
            self.logger.info(f"📋 Perfiles actualizados: {len(self.perfiles)} estudiantes")
        
        # Convertir la lista de objetos Tarea a una lista de diccionarios para que sea serializable
        tareas_dict_list = [asdict(tarea) for tarea in tareas] 
        
        # Prepara el prompt para el LLM con instrucciones claras
        prompt_optimizacion = f"""
Eres un experto en asignación de tareas educativas del AULA_A_4PRIM.

TAREAS DISPONIBLES:
{self._formatear_tareas_para_prompt(tareas)}

ANÁLISIS DE ESTUDIANTES:
{self._formatear_analisis_para_prompt(analisis_estudiantes)}

INSTRUCCIONES:
- Equilibra la carga de trabajo según disponibilidad y capacidades
- Asigna según fortalezas y necesidades específicas de cada estudiante
- Elena (003): TEA - rutinas estructuradas, tareas predecibles
- Luis (004): TDAH - tareas dinámicas, permite movimiento
- Ana (005): Altas capacidades - puede liderar y tomar más responsabilidad
- Considera tiempo estimado y complejidad de cada tarea
- Permite flexibilidad en número de tareas según el estudiante

RESPONDE ÚNICAMENTE CON ESTE JSON (sin texto adicional):
{{
  "asignaciones": {{
    "estudiante_001": ["tarea_01", "tarea_02"],
    "estudiante_002": ["tarea_03"],
    "estudiante_003": ["tarea_04"],
    "estudiante_004": ["tarea_05"],
    "estudiante_005": ["tarea_06"],
    "estudiante_006": ["tarea_07"],
    "estudiante_007": ["tarea_08"],
    "estudiante_008": ["tarea_09"]
  }}
}}"""
        
        self._log_processing_start(f"Optimizando asignaciones para {len(tareas)} tareas")
        
        try:
            # Llamada al LLM y parseo robusto
            respuesta_llm = self.ollama.generar_respuesta(prompt_optimizacion, max_tokens=500)
            asignaciones_dict = parse_json_seguro(respuesta_llm)
            
            if asignaciones_dict and 'asignaciones' in asignaciones_dict:
                self.logger.info(f"✅ Asignaciones parseadas correctamente")
                self._log_processing_end(f"Generadas asignaciones para {len(asignaciones_dict['asignaciones'])} estudiantes")
                return asignaciones_dict.get('asignaciones', {})
            else:
                raise ValueError("No se pudo parsear JSON de asignaciones o formato incorrecto")
        
        except Exception as e:
            self.logger.error(f"❌ Error al parsear asignaciones del LLM: {e}")
            self.logger.info("⚠️ Usando lógica de fallback para las asignaciones")
            
            # Generar asignaciones de fallback
            asignaciones_fallback = self._generar_asignaciones_fallback(tareas)
            self._log_processing_end(f"Generadas asignaciones fallback para {len(asignaciones_fallback)} estudiantes")
            return asignaciones_fallback
    
    def _formatear_tareas_para_prompt(self, tareas: List[Tarea]) -> str:
        """
        Formatea lista de tareas para el prompt
        
        Args:
            tareas: Lista de tareas
            
        Returns:
            Texto formateado
        """
        return "\n".join([
            f"- {t.id}: {t.descripcion} (Complejidad: {t.complejidad}, Tipo: {t.tipo}, Tiempo: {t.tiempo_estimado}min)"
            for t in tareas
        ])
    
    def _formatear_analisis_para_prompt(self, analisis: Dict) -> str:
        """
        Formatea análisis de estudiantes para el prompt
        
        Args:
            analisis: Análisis de compatibilidades
            
        Returns:
            Texto formateado
        """
        texto = ""
        for estudiante_id, datos in analisis.items():
            texto += f"- Estudiante {estudiante_id}:\n"
            texto += f"  * Tareas compatibles: {', '.join(datos.get('tareas_compatibles', []))}\n"
            texto += f"  * Rol sugerido: {datos.get('rol_sugerido', 'No especificado')}\n"
        return texto
    
    def _generar_asignaciones_fallback(self, tareas: List[Tarea]) -> Dict:
        """
        Genera asignaciones de fallback en caso de error
        
        Args:
            tareas: Lista de tareas
            
        Returns:
            Diccionario con asignaciones
        """
        asignaciones_fallback = {}
        
        # Usar perfiles reales para asignación de fallback
        if not self.perfiles:
            self.logger.warning("No hay perfiles de estudiantes cargados. Devolviendo asignaciones vacías.")
            return {}
        
        estudiantes_ids = list(self.perfiles.keys())
        num_estudiantes = len(estudiantes_ids)
        
        if num_estudiantes == 0:
            self.logger.warning("No hay estudiantes disponibles para asignación.")
            return {}
        
        # Distribución equitativa mejorada
        tareas_por_estudiante = len(tareas) // num_estudiantes
        tareas_extra = len(tareas) % num_estudiantes
        
        indice_tarea = 0
        
        for i, estudiante_id in enumerate(estudiantes_ids):
            # Calcular número de tareas para este estudiante
            num_tareas_estudiante = tareas_por_estudiante
            if i < tareas_extra:
                num_tareas_estudiante += 1
            
            # Sin límite artificial - distribuir según capacidad y disponibilidad
            # Ajustar por disponibilidad del estudiante (si está disponible)
            if estudiante_id in self.perfiles:
                disponibilidad = self.perfiles[estudiante_id].disponibilidad
                # Estudiantes con mayor disponibilidad pueden tomar más tareas
                if disponibilidad > 85:
                    num_tareas_estudiante = min(num_tareas_estudiante + 1, len(tareas))
                elif disponibilidad < 70:
                    num_tareas_estudiante = max(1, num_tareas_estudiante - 1)
            
            # Asignar tareas
            tareas_estudiante = []
            for _ in range(num_tareas_estudiante):
                if indice_tarea < len(tareas):
                    tareas_estudiante.append(tareas[indice_tarea].id)
                    indice_tarea += 1
            
            asignaciones_fallback[f"estudiante_{estudiante_id}"] = tareas_estudiante
        
        self.logger.info(f"✅ Asignaciones fallback creadas para {len(asignaciones_fallback)} estudiantes")
        return asignaciones_fallback
    
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