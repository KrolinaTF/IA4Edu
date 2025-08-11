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
        
        Returns:
            Proyecto final generado
        """
        try:
            # Mostrar bienvenida
            self.views.mostrar_bienvenida()
            
            # Solicitar prompt inicial
            prompt_profesor = self.views.solicitar_prompt_inicial()
            
            # Generar ideas iniciales
            self.views.mostrar_mensaje_procesando()
            ideas = self.controller.generar_ideas_desde_prompt(prompt_profesor)
            
            # Mostrar ideas generadas
            self.views.mostrar_ideas(ideas)
            
            # Gestionar selección y matización de ideas
            actividad_seleccionada = self._gestionar_seleccion_ideas(ideas)
            
            if not actividad_seleccionada:
                self.views.mostrar_mensaje_error("No se seleccionó ninguna actividad")
                return {}
            
            # Solicitar información adicional opcional
            info_adicional = self.views.solicitar_detalles_adicionales(actividad_seleccionada.get('titulo', 'la actividad'))
            
            # Ejecutar flujo orquestado
            self.views.mostrar_mensaje_procesando()
            proyecto_final = self.controller.ejecutar_flujo_orquestado(actividad_seleccionada, info_adicional)
            
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