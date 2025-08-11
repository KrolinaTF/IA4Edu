"""
Sistema principal de Agentes para Aprendizaje Basado en Proyectos (ABP).
Coordina los diferentes componentes y provee la lógica central.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import json

from agents.coordinador import AgenteCoordinador
from core.ollama_integrator import OllamaIntegrator

logger = logging.getLogger("SistemaAgentesABP.Sistema")

class SistemaAgentesABP:
    """Sistema de Agentes para Aprendizaje Basado en Proyectos (ABP) con Contexto Híbrido"""
    def __init__(self, coordinador=None):
        """
        Inicializa el sistema, opcionalmente con un coordinador específico
        
        Args:
            coordinador: AgenteCoordinador personalizado (opcional)
        """
        # Permitir inyección de un coordinador o crear uno nuevo
        self.coordinador = coordinador or AgenteCoordinador()
        
        # Estado del sistema
        self.proyecto_actual = None
        self.validado = False
        
        logger.info("🚀 Sistema de Agentes ABP inicializado")
    
    def generar_ideas(self, prompt_profesor: str) -> Dict:
        """
        Genera ideas a partir del prompt del profesor
        
        Args:
            prompt_profesor: Prompt inicial del profesor
            
        Returns:
            Diccionario con información inicial e ideas generadas
        """
        logger.info(f"💡 Generando ideas para prompt: {prompt_profesor[:50]}...")
        
        # Recolectar información inicial y generar ideas
        info_inicial = self.coordinador.recoger_informacion_inicial(
            prompt_profesor=prompt_profesor
        )
        
        return info_inicial
    
    def ejecutar_flujo(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """
        Ejecuta el flujo completo de procesamiento para una actividad seleccionada
        
        Args:
            actividad_seleccionada: Actividad seleccionada para procesar
            info_adicional: Información adicional opcional
            
        Returns:
            Proyecto final generado
        """
        logger.info(f"🚀 Ejecutando flujo para: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Ejecutar flujo orquestado
        proyecto_final = self.coordinador.ejecutar_flujo_orquestado(actividad_seleccionada, info_adicional)
        
        # Guardar proyecto actual para referencia futura
        self.proyecto_actual = proyecto_final
        
        return proyecto_final
    
    def validar_proyecto(self, validado: bool = True) -> None:
        """
        Establece el estado de validación del proyecto
        
        Args:
            validado: Estado de validación
        """
        self.validado = validado
        
        if self.proyecto_actual and isinstance(self.proyecto_actual, dict):
            # Actualizar metadatos del proyecto
            if 'metadatos' in self.proyecto_actual:
                self.proyecto_actual['metadatos']['validado'] = validado
            
            logger.info(f"✅ Proyecto {'validado' if validado else 'invalidado'}")
        else:
            logger.warning("⚠️ No hay proyecto actual para validar")
    
    def guardar_proyecto(self, nombre_archivo: str = None) -> Optional[str]:
        """
        Guarda el proyecto actual en un archivo JSON
        
        Args:
            nombre_archivo: Nombre base del archivo (opcional)
            
        Returns:
            Ruta del archivo guardado o None si hubo error
        """
        if not self.proyecto_actual:
            logger.warning("⚠️ No hay proyecto para guardar")
            return None
        
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
                json.dump(self.proyecto_actual, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Proyecto guardado en: {nombre_archivo}")
            return nombre_archivo
            
        except Exception as e:
            logger.error(f"❌ Error guardando proyecto: {e}")
            return None
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del proyecto actual
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.proyecto_actual:
            return {
                'hay_proyecto': False,
                'mensaje': 'No hay proyecto actual',
                'timestamp': datetime.now().isoformat()
            }
        
        # Extrae estadísticas del proyecto actual de forma segura
        validacion = self.proyecto_actual.get('validacion', {})
        if not isinstance(validacion, dict):
            validacion = {}
            
        estadisticas = validacion.get('estadisticas', {})
        if not isinstance(estadisticas, dict):
            estadisticas = {}
        
        # Añadir información adicional
        estadisticas.update({
            'hay_proyecto': True,
            'proyecto_validado': self.validado,
            'timestamp_consulta': datetime.now().isoformat()
        })
        
        return estadisticas