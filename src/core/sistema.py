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
        
        # Ejecutar flujo MVP mejorado (en lugar del legacy orquestado)
        descripcion_actividad = actividad_seleccionada.get('descripcion', actividad_seleccionada.get('titulo', ''))
        if info_adicional:
            descripcion_actividad += f" {info_adicional}"
            
        proyecto_final = self.coordinador.ejecutar_flujo_mejorado_mvp(descripcion_actividad)
        
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
    
    def ejecutar_flujo_mvp(self, descripcion_actividad: str) -> Dict:
        """
        Ejecuta el flujo MVP mejorado específicamente
        
        Args:
            descripcion_actividad: Descripción completa de la actividad
            
        Returns:
            Proyecto final generado
        """
        logger.info(f"🚀 Ejecutando flujo MVP para actividad")
        
        # Ejecutar flujo MVP mejorado
        proyecto_final = self.coordinador.ejecutar_flujo_mejorado_mvp(descripcion_actividad)
        
        # Guardar proyecto actual para referencia futura
        self.proyecto_actual = proyecto_final
        
        return proyecto_final
    
    def matizar_actividad(self, idea_base: Dict, matizaciones: str) -> List[Dict]:
        """
        Matiza una idea específica con refinamientos del usuario
        
        Args:
            idea_base: Idea base a matizar
            matizaciones: Matizaciones solicitadas por el usuario
            
        Returns:
            Lista de ideas matizadas
        """
        logger.info(f"💡 Matizando idea: {idea_base.get('titulo', 'Sin título')}")
        
        # Usar el contexto híbrido del coordinador
        contexto_hibrido = self.coordinador.contexto_hibrido
        
        # Ejecutar matización específica
        return self.coordinador.matizar_idea_especifica(idea_base, matizaciones, contexto_hibrido)
    
    def generar_nuevas_ideas(self, prompt: str) -> List[Dict]:
        """
        Genera nuevas ideas con contexto híbrido
        
        Args:
            prompt: Prompt para generar nuevas ideas
            
        Returns:
            Lista de nuevas ideas generadas
        """
        logger.info(f"💡 Generando nuevas ideas con contexto híbrido")
        
        # Obtener contexto híbrido del coordinador
        contexto_hibrido = self.coordinador.contexto_hibrido
        
        # Generar ideas con contexto
        return self.coordinador.generar_ideas_actividades_hibrido(prompt, contexto_hibrido)
    
    def registrar_detalles_adicionales(self, actividad: Dict, detalles: str):
        """
        Registra detalles adicionales en el historial del coordinador
        
        Args:
            actividad: Actividad seleccionada
            detalles: Detalles adicionales
        """
        if not detalles.strip():
            return
            
        logger.info(f"📝 Registrando detalles adicionales para: {actividad.get('titulo', 'Sin título')}")
        
        # Registrar en el historial de prompts del coordinador
        from datetime import datetime
        self.coordinador.historial_prompts.append({
            "tipo": "detalles_actividad_seleccionada",
            "actividad_id": actividad.get('id'),
            "actividad_titulo": actividad.get('titulo'),
            "detalles_adicionales": detalles,
            "timestamp": datetime.now().isoformat()
        })