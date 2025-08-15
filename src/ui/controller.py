"""
Controlador de UI para el sistema de agentes ABP.
Actúa como intermediario entre la interfaz de usuario y la lógica de negocio.
"""

import logging
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
        Solicita al sistema generar ideas basadas en el prompt
        
        Args:
            prompt: Prompt inicial del profesor
            
        Returns:
            Lista de ideas generadas
        """
        logger.info(f"🎮 Solicitando generación de ideas para prompt: {prompt[:50]}...")
        
        # Usar la capa de abstracción del sistema
        info_inicial = self.sistema.generar_ideas(prompt_profesor=prompt)
        return info_inicial.get('ideas_generadas', [])
    
    def matizar_idea(self, ideas: List[Dict], idea_idx: int, matizaciones: str) -> List[Dict]:
        """
        Solicita al sistema matizar una idea seleccionada
        
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
        
        # Usar la capa de abstracción del sistema
        return self.sistema.matizar_actividad(idea_seleccionada, matizaciones)
    
    def generar_nuevas_ideas(self, nuevo_prompt: str) -> List[Dict]:
        """
        Solicita al sistema generar nuevas ideas con un prompt diferente
        
        Args:
            nuevo_prompt: Nuevo prompt para generar ideas
            
        Returns:
            Lista de nuevas ideas generadas
        """
        logger.info(f"🎮 Solicitando nuevas ideas con prompt: {nuevo_prompt[:50]}...")
        
        # Usar la capa de abstracción del sistema
        return self.sistema.generar_nuevas_ideas(nuevo_prompt)
    
    def registrar_detalles_adicionales(self, actividad: Dict, detalles: str):
        """
        Registra detalles adicionales para una actividad seleccionada
        
        Args:
            actividad: Actividad seleccionada
            detalles: Detalles adicionales
        """
        logger.info(f"🎮 Registrando detalles adicionales para: {actividad.get('titulo', 'Sin título')}")
        
        # Usar la capa de abstracción del sistema
        self.sistema.registrar_detalles_adicionales(actividad, detalles)
    
    def ejecutar_flujo_orquestado(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """
        Solicita al sistema ejecutar el flujo completo
        
        Args:
            actividad_seleccionada: Actividad seleccionada para procesar
            info_adicional: Información adicional opcional
            
        Returns:
            Proyecto final generado
        """
        logger.info(f"🎮 Solicitando ejecución de flujo completo para: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Usar la capa de abstracción del sistema
        proyecto_final = self.sistema.ejecutar_flujo(actividad_seleccionada, info_adicional)
        
        # Validar automáticamente si el proyecto se completó correctamente
        if proyecto_final and isinstance(proyecto_final, dict):
            self.sistema.validar_proyecto(True)
        
        return proyecto_final
    
    def guardar_proyecto(self, proyecto: Dict = None, nombre_archivo: str = None) -> str:
        """
        Guarda el proyecto actual del sistema en un archivo JSON
        
        Args:
            proyecto: Proyecto a guardar (opcional, usará el proyecto actual del sistema)
            nombre_archivo: Nombre de archivo opcional
            
        Returns:
            Ruta del archivo guardado
        """
        logger.info(f"🎮 Solicitando guardado de proyecto")
        
        # Si no se especifica proyecto, usar el del sistema
        if proyecto is None:
            return self.sistema.guardar_proyecto(nombre_archivo)
        else:
            # Actualizar proyecto actual del sistema y luego guardarlo
            self.sistema.proyecto_actual = proyecto
            return self.sistema.guardar_proyecto(nombre_archivo)