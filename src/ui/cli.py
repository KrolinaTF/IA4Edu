"""
Interfaz de línea de comandos (CLI) para el sistema de agentes ABP.
Implementa un bucle de interacción con el usuario y coordina con el controlador.
"""

import logging
from typing import Dict, List, Any, Optional

from ui.views import CLIViews
from ui.controller import UIController

logger = logging.getLogger("SistemaAgentesABP.CLI")

class CLI:
    """Interfaz de línea de comandos para el sistema de agentes ABP"""
    
    def __init__(self, controller: UIController):
        """
        Inicializa la CLI con un controlador
        
        Args:
            controller: Controlador de UI
        """
        self.controller = controller
        self.views = CLIViews()
        logger.info("🖥️ CLI inicializada")
    
    def ejecutar(self) -> Dict:
        """
        Ejecuta el flujo completo de interacción con el usuario
        CON SOPORTE PARA INPUTS ESTRUCTURADOS
        
        Returns:
            Proyecto final generado
        """
        try:
            # Mostrar bienvenida
            self.views.mostrar_bienvenida()
             
            ideas, datos_contexto = self._flujo_progresivo()
                
            # Mostrar ideas generadas
            self.views.mostrar_ideas(ideas)
            
            # Gestionar selección y matización de ideas
            actividad_seleccionada = self._gestionar_seleccion_ideas(ideas)
            
            if not actividad_seleccionada:
                self.views.mostrar_mensaje_error("No se seleccionó ninguna actividad")
                return {}
            
            if datos_contexto:
                proyecto_final = self._aplicar_estructura_progresiva(actividad_seleccionada, datos_contexto)
            else:
                # Fallback si no hay contexto
                info_adicional = self.views.solicitar_detalles_adicionales(actividad_seleccionada.get('titulo', 'la actividad'))
                self.views.mostrar_mensaje_procesando()
                proyecto_final = self.controller.ejecutar_flujo_completo(actividad_seleccionada, info_adicional)
            
            # Mostrar resumen y validación
            self.views.mostrar_resumen_proceso(proyecto_final)
            validado = self.views.mostrar_validacion_final(proyecto_final)
            
            # Guardar proyecto si fue validado
            if validado:
                ruta_archivo = self.controller.guardar_proyecto(proyecto_final)
                if ruta_archivo:
                    self.views.mostrar_mensaje_exito(f"Proyecto guardado exitosamente en {ruta_archivo}")
                else:
                    self.views.mostrar_mensaje_error("No se pudo guardar el proyecto")
            
            return proyecto_final
            
        except KeyboardInterrupt:
            self.views.mostrar_mensaje_error("Proceso interrumpido por el usuario")
            return {}
        except Exception as e:
            logger.error(f"Error en CLI: {e}")
            self.views.mostrar_mensaje_error(f"Error inesperado: {e}")
            return {}
    
    def _gestionar_seleccion_ideas(self, ideas: List[Dict]) -> Optional[Dict]:
        """
        Gestiona el proceso de selección y matización de ideas
        
        Args:
            ideas: Lista de ideas generadas
            
        Returns:
            Actividad seleccionada o None si no se seleccionó ninguna
        """
        actividad_seleccionada = None
        
        while True:
            # Mostrar opciones disponibles
            self.views.mostrar_opciones_seleccion(ideas, actividad_seleccionada is not None)
            
            # Solicitar selección
            seleccion_input = self.views.solicitar_seleccion()
            
            # Procesar selección
            try:
                if seleccion_input.isdigit():
                    seleccion = int(seleccion_input)
                    
                    if 1 <= seleccion <= len(ideas):
                        # Seleccionar una idea
                        actividad_seleccionada = ideas[seleccion - 1]
                        self.views.mostrar_mensaje_exito(f"Ha seleccionado la actividad: {actividad_seleccionada.get('titulo', 'Sin título')}")
                        
                        # Solicitar detalles adicionales
                        detalle_extra = self.views.solicitar_detalles_adicionales(actividad_seleccionada.get('titulo', 'la actividad'))
                        if detalle_extra.strip():
                            self.controller.registrar_detalles_adicionales(actividad_seleccionada, detalle_extra)
                            self.views.mostrar_mensaje_exito("Detalles adicionales registrados")
                        
                        # Finalizar selección
                        break
                        
                    elif seleccion == 0:
                        # Generar nuevas ideas
                        nuevo_prompt = self.views.solicitar_nuevo_prompt()
                        self.views.mostrar_mensaje_procesando()
                        ideas = self.controller.generar_nuevas_ideas(nuevo_prompt)
                        self.views.mostrar_ideas(ideas)
                        actividad_seleccionada = None
                        continue
                        
                elif seleccion_input == 'M':
                    # Matizar idea
                    idea_idx = self.views.solicitar_indice_idea(len(ideas))
                    
                    if 1 <= idea_idx <= len(ideas):
                        matizaciones = self.views.solicitar_matizaciones()
                        self.views.mostrar_mensaje_procesando()
                        ideas_matizadas = self.controller.matizar_idea(ideas, idea_idx - 1, matizaciones)
                        
                        # Actualizar lista de ideas
                        ideas = ideas_matizadas
                        self.views.mostrar_ideas(ideas)
                        actividad_seleccionada = None
                        continue
                    else:
                        self.views.mostrar_mensaje_error(f"Selección inválida. Elige entre 1 y {len(ideas)}")
                        continue
                        
                elif seleccion_input == '-1' and actividad_seleccionada:
                    # Añadir más detalles a la actividad seleccionada
                    detalles = self.views.solicitar_detalles_adicionales(actividad_seleccionada.get('titulo', 'la actividad'))
                    if detalles.strip():
                        self.controller.registrar_detalles_adicionales(actividad_seleccionada, detalles)
                        self.views.mostrar_mensaje_exito("Detalles adicionales registrados")
                    break
                    
                else:
                    self.views.mostrar_mensaje_error("Selección inválida")
                    
            except Exception as e:
                logger.error(f"Error en selección: {e}")
                self.views.mostrar_mensaje_error(f"Error en selección: {e}")
        
        return actividad_seleccionada
     
    
    def _flujo_progresivo(self) -> tuple:
        """
        NUEVO: Flujo progresivo paso a paso
        
        Returns:
            Tupla (ideas, datos_contexto)
        """
        logger.info("🎓 Iniciando flujo progresivo paso a paso")
        
        # PASO 1-4: Captura básica (materia, tema, idea previa, duración)
        input_basico = self.views.solicitar_input_estructurado_progresivo()
        
        if not input_basico:
            logger.warning("⚠️ Input básico cancelado por el usuario")
            return [], None
        
        # GENERAR IDEAS desde input básico
        self.views.mostrar_mensaje_procesando()
        ideas = self.controller.generar_ideas_desde_input_progresivo(input_basico)
        
        if not ideas:
            logger.warning("⚠️ No se generaron ideas desde input progresivo")
            return [], None
        
        logger.info(f"✅ Generadas {len(ideas)} ideas desde input progresivo")
        return ideas, input_basico
    
    def _aplicar_estructura_progresiva(self, actividad_seleccionada: Dict, datos_contexto: Dict) -> Dict:
        """
        Aplica estructura detallada al modo progresivo
        
        Args:
            actividad_seleccionada: Actividad elegida por el profesor
            datos_contexto: Datos del contexto básico capturado
            
        Returns:
            Proyecto final con estructura aplicada
        """
        logger.info("🔧 Aplicando estructura progresiva detallada")
        
        # CAPTURAR ESTRUCTURA DETALLADA post-selección
        estructura_detallada = self.views.solicitar_estructura_post_seleccion(actividad_seleccionada)
        
        if not estructura_detallada:
            logger.warning("⚠️ Estructura detallada cancelada, usando flujo tradicional")
            # Fallback al flujo tradicional
            info_adicional = self.views.solicitar_detalles_adicionales(actividad_seleccionada.get('titulo', 'la actividad'))
            self.views.mostrar_mensaje_procesando()
            return self.controller.ejecutar_flujo_completo(actividad_seleccionada, info_adicional)
        
        # APLICAR ESTRUCTURA DETALLADA
        self.views.mostrar_mensaje_procesando()
        proyecto_final = self.controller.aplicar_estructura_post_seleccion(
            actividad_seleccionada, 
            estructura_detallada
        )
        
        logger.info("✅ Estructura progresiva aplicada exitosamente")
        return proyecto_final