"""
Controlador de UI para el sistema de agentes ABP.
Actúa como intermediario entre la interfaz de usuario y la lógica de negocio.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SistemaAgentesABP.UIController")

class UIController:
    """Controlador de la interfaz de usuario que coordina interacciones con la lógica de negocio"""
    
    def __init__(self, coordinador=None, sistema=None):
        """
        Inicializa el controlador con referencias al coordinador y sistema
        
        Args:
            coordinador: Referencia al AgenteCoordinador
            sistema: Referencia al SistemaAgentesABP
        """
        self.coordinador = coordinador
        self.sistema = sistema
        logger.info("🎮 Controlador de UI inicializado")
    
    def generar_ideas_desde_prompt(self, prompt: str) -> List[Dict]:
        """
        Solicita al coordinador generar ideas basadas en el prompt
        
        Args:
            prompt: Prompt inicial del profesor
            
        Returns:
            Lista de ideas generadas
        """
        logger.info(f"🎮 Solicitando generación de ideas para prompt: {prompt[:50]}...")
        
        # Llamar al método correspondiente del coordinador
        info_inicial = self.coordinador.recoger_informacion_inicial(prompt_profesor=prompt)
        return info_inicial.get('ideas_generadas', [])
    
    def matizar_idea(self, ideas: List[Dict], idea_idx: int, matizaciones: str) -> List[Dict]:
        """
        Solicita al coordinador matizar una idea seleccionada
        
        Args:
            ideas: Lista de ideas actuales
            idea_idx: Índice de la idea a matizar (0-based)
            matizaciones: Texto con las matizaciones solicitadas
            
        Returns:
            Lista actualizada de ideas
        """
        if not (0 <= idea_idx < len(ideas)):
            logger.error(f"🎮 Índice de idea inválido: {idea_idx}")
            return ideas
            
        idea_seleccionada = ideas[idea_idx]
        logger.info(f"🎮 Solicitando matización de idea: {idea_seleccionada.get('titulo', '')}...")
        
        # Crear prompt para matizar la idea seleccionada
        prompt_matizacion = f"Toma esta idea: '{idea_seleccionada.get('titulo', '')}' - {idea_seleccionada.get('descripcion', '')} y aplica estos cambios/matizaciones: {matizaciones}"
        
        # Obtener contexto híbrido del coordinador
        contexto_hibrido = self.coordinador.contexto_hibrido
        
        # Generar ideas matizadas
        return self.coordinador.generar_ideas_actividades_hibrido(prompt_matizacion, contexto_hibrido)
    
    def generar_nuevas_ideas(self, nuevo_prompt: str) -> List[Dict]:
        """
        Solicita al coordinador generar nuevas ideas con un prompt diferente
        
        Args:
            nuevo_prompt: Nuevo prompt para generar ideas
            
        Returns:
            Lista de nuevas ideas generadas
        """
        logger.info(f"🎮 Solicitando nuevas ideas con prompt: {nuevo_prompt[:50]}...")
        
        # Obtener contexto híbrido del coordinador
        contexto_hibrido = self.coordinador.contexto_hibrido
        
        # Generar nuevas ideas
        return self.coordinador.generar_ideas_actividades_hibrido(nuevo_prompt, contexto_hibrido)
    
    def registrar_detalles_adicionales(self, actividad: Dict, detalles: str):
        """
        Registra detalles adicionales para una actividad seleccionada
        
        Args:
            actividad: Actividad seleccionada
            detalles: Detalles adicionales
        """
        if not detalles.strip():
            return
            
        logger.info(f"🎮 Registrando detalles adicionales para: {actividad.get('titulo', 'Sin título')}")
        
        # Registrar en el historial de prompts del coordinador
        self.coordinador.historial_prompts.append({
            "tipo": "detalles_actividad_seleccionada",
            "actividad_id": actividad.get('id'),
            "actividad_titulo": actividad.get('titulo'),
            "detalles_adicionales": detalles,
            "timestamp": datetime.now().isoformat()
        })
    
    def ejecutar_flujo_orquestado(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """
        Solicita al coordinador ejecutar el flujo orquestado completo
        
        Args:
            actividad_seleccionada: Actividad seleccionada para procesar
            info_adicional: Información adicional opcional
            
        Returns:
            Proyecto final generado
        """
        logger.info(f"🎮 Solicitando ejecución de flujo para: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Ejecutar flujo orquestado
        return self.coordinador.ejecutar_flujo_orquestado(actividad_seleccionada, info_adicional)
    
    def guardar_proyecto(self, proyecto: Dict, nombre_archivo: str = None) -> str:
        """
        Guarda el proyecto en un archivo JSON
        
        Args:
            proyecto: Proyecto a guardar
            nombre_archivo: Nombre de archivo opcional
            
        Returns:
            Ruta del archivo guardado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if nombre_archivo:
            nombre_archivo = f"{nombre_archivo}_{timestamp}.json"
        else:
            nombre_archivo = f"abp_{timestamp}.json"
            
        # Asegurar que la ruta incluya el directorio temp
        if not nombre_archivo.startswith("temp/"):
            nombre_archivo = f"temp/{nombre_archivo}"
        
        try:
            # Crear directorio temp si no existe
            os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
            
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                json.dump(proyecto, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Proyecto guardado en: {nombre_archivo}")
            return nombre_archivo
            
        except Exception as e:
            logger.error(f"❌ Error guardando proyecto: {e}")
            return None