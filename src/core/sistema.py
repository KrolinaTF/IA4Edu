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
from typing import Dict, List, Any, Optional

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
    
    
    def ejecutar_flujo(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """
        Ejecuta el flujo completo usando el coordinador simplificado
        """
        # Extraer descripción de la actividad
        descripcion = actividad_seleccionada.get('descripcion', 
                    actividad_seleccionada.get('titulo', 'Actividad educativa'))
        
        # Usar el nuevo flujo único del coordinador
        proyecto_final = self.coordinador.ejecutar_flujo_completo(descripcion, info_adicional)
        
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
    
    def guardar_como_ejemplo_k(self, proyecto: Dict = None, nombre_base: str = None) -> Optional[str]:
        """
        Guarda una actividad generada como nuevo ejemplo k_ para futuros few-shot
        
        Args:
            proyecto: Proyecto a guardar (opcional, usará el proyecto actual)
            nombre_base: Nombre base para el archivo k_ (opcional)
            
        Returns:
            Ruta del archivo k_ guardado o None si hubo error
        """
        if proyecto is None:
            proyecto = self.proyecto_actual
            
        if not proyecto or not isinstance(proyecto, dict):
            logger.warning("⚠️ No hay proyecto válido para guardar como ejemplo k_")
            return None
        
        # Extraer actividad generada del proyecto
        actividad_generada = None
        if 'actividad_generada' in proyecto:
            actividad_generada = proyecto['actividad_generada']
        elif 'actividad_personalizada' in proyecto:
            # Compatibilidad con formato anterior
            actividad_generada = proyecto['actividad_personalizada']
        
        if not actividad_generada:
            logger.warning("⚠️ No se encontró actividad válida en el proyecto")
            return None
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if nombre_base:
            nombre_archivo = f"k_{nombre_base}_{timestamp}.json"
        else:
            # Generar nombre basado en el título
            titulo = actividad_generada.get('titulo', 'actividad_generada')
            nombre_limpio = ''.join(c.lower() if c.isalnum() else '_' for c in titulo)[:20]
            nombre_archivo = f"k_{nombre_limpio}_{timestamp}.json"
        
        # Ruta de destino en el directorio de actividades
        ruta_destino = f"data/actividades/json_actividades/{nombre_archivo}"
        
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            
            # Limpiar actividad para formato k_ (eliminar metadatos internos)
            actividad_k = self._limpiar_para_formato_k(actividad_generada)
            
            with open(ruta_destino, 'w', encoding='utf-8') as f:
                json.dump(actividad_k, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📚 Actividad guardada como ejemplo k_: {ruta_destino}")
            return ruta_destino
            
        except Exception as e:
            logger.error(f"❌ Error guardando actividad como ejemplo k_: {e}")
            return None
    
    def _limpiar_para_formato_k(self, actividad: Dict) -> Dict:
        """Limpia una actividad generada para que coincida con el formato k_ estándar"""
        actividad_limpia = {
            'id': actividad.get('id', 'ACT_GENERADA'),
            'titulo': actividad.get('titulo', 'Actividad Generada'),
            'objetivo': actividad.get('objetivo', 'Objetivo pedagógico'),
            'nivel_educativo': actividad.get('nivel_educativo', '4º de Primaria'),
            'duracion_minutos': actividad.get('duracion_minutos', '45 minutos'),
            'recursos': actividad.get('recursos', []),
            'etapas': actividad.get('etapas', [])
        }
        
        # Añadir observaciones si la actividad tiene adaptaciones
        observaciones = []
        for etapa in actividad_limpia.get('etapas', []):
            for tarea in etapa.get('tareas', []):
                if 'estrategias_adaptacion' in tarea:
                    observaciones.append("La actividad incluye adaptaciones para necesidades educativas especiales.")
                    break
            if observaciones:
                break
        
        if observaciones:
            actividad_limpia['observaciones'] = ' '.join(observaciones)
        
        return actividad_limpia
