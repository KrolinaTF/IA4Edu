"""
Controlador de UI para el sistema de agentes ABP.
Actúa como intermediario entre la interfaz de usuario y la lógica de negocio.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

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
        Genera ideas basadas en el prompt libre llamando directamente al coordinador
        """
        logger.info(f"🎮 Solicitando generación de ideas para prompt: {prompt[:50]}...")
        
        # Llamar directamente al coordinador
        info_inicial = self.coordinador.recoger_informacion_inicial(prompt_profesor=prompt)
        return info_inicial.get('ideas_generadas', [])
    
    def generar_ideas_desde_input_estructurado(self, input_estructurado: Dict) -> List[Dict]:
        """
        NUEVO: Genera ideas basadas en input estructurado del profesor
        
        Args:
            input_estructurado: Diccionario con campos estructurados
            
        Returns:
            Lista de ideas generadas
        """
        logger.info(f"🎮 Generando ideas desde input estructurado")
        logger.info(f"   📚 Materia: {input_estructurado.get('materia', 'N/A')}")
        logger.info(f"   🎯 Tema: {input_estructurado.get('tema', 'N/A')}")
        logger.info(f"   ⏱️ Duración: {input_estructurado.get('duracion', {}).get('descripcion', 'N/A')}")
        
        # Convertir input estructurado a prompt enriquecido
        prompt_enriquecido = self._convertir_input_estructurado_a_prompt(input_estructurado)
        
        # Registrar metadatos estructurados en el contexto
        self._registrar_metadatos_estructurados(input_estructurado)
        
        # Usar la capa de abstracción del sistema con prompt enriquecido
        info_inicial = self.coordinador.recoger_informacion_inicial(prompt_profesor=prompt_enriquecido)
        
        # Enriquecer ideas con metadatos estructurados
        ideas_enriquecidas = self._enriquecer_ideas_con_estructura(
            info_inicial.get('ideas_generadas', []), 
            input_estructurado
        )
        
        return ideas_enriquecidas
    
    def _convertir_input_estructurado_a_prompt(self, input_data: Dict) -> str:
        """
        Convierte input estructurado a prompt enriquecido para el sistema
        
        Args:
            input_data: Datos estructurados del input
            
        Returns:
            Prompt enriquecido para el sistema
        """
        elementos_prompt = []
        
        # Materia y tema
        materia = input_data.get('materia', '')
        tema = input_data.get('tema', '')
        
        if materia and tema:
            elementos_prompt.append(f"Crear una actividad de {materia} sobre {tema}")
        elif tema:
            elementos_prompt.append(f"Crear una actividad educativa sobre {tema}")
        elif materia:
            elementos_prompt.append(f"Crear una actividad de {materia}")
        else:
            elementos_prompt.append("Crear una actividad educativa")
        
        # Duración
        duracion = input_data.get('duracion', {})
        if duracion.get('descripcion'):
            elementos_prompt.append(f"con duración de {duracion['descripcion']}")
        
        # Modalidades de trabajo
        modalidades = input_data.get('modalidades', [])
        if modalidades:
            modalidades_texto = self._formatear_modalidades(modalidades)
            elementos_prompt.append(f"usando modalidades de trabajo: {modalidades_texto}")
        
        # Estructura de fases con modalidades específicas
        estructura = input_data.get('estructura_fases', {})
        if estructura.get('tipo') and estructura['tipo'] != 'libre':
            elementos_prompt.append(f"con estructura {estructura['tipo']}")
            
            # Incluir fases detalladas con modalidades
            fases_detalladas = estructura.get('fases_detalladas', [])
            if fases_detalladas:
                fases_con_modalidades = []
                for fase in fases_detalladas:
                    nombre = fase.get('nombre', 'Fase')
                    modalidad = fase.get('modalidad', 'grupos_pequeños').replace('_', ' ')
                    fases_con_modalidades.append(f"{nombre} (trabajo {modalidad})")
                
                fases_texto = ' → '.join(fases_con_modalidades)
                elementos_prompt.append(f"siguiendo las fases: {fases_texto}")
            else:
                # Fallback a fases simples
                fases = estructura.get('fases', [])
                if fases:
                    fases_texto = ' → '.join(fases)
                    elementos_prompt.append(f"siguiendo las fases: {fases_texto}")
        
        # Contexto adicional
        contexto = input_data.get('contexto_adicional', '')
        if contexto:
            elementos_prompt.append(f"Consideraciones adicionales: {contexto}")
        
        # Información sobre neurotipos (siempre incluir)
        elementos_prompt.append("La actividad debe incluir adaptaciones para estudiantes con TEA, TDAH y altas capacidades")
        
        prompt_final = '. '.join(elementos_prompt) + '.'
        
        logger.debug(f"📝 Prompt generado: {prompt_final}")
        return prompt_final
    
    def _formatear_modalidades(self, modalidades: List[str]) -> str:
        """Formatea lista de modalidades para inclusión en prompt"""
        modalidades_formateadas = []
        
        mapeo_modalidades = {
            'individual': 'trabajo individual',
            'parejas': 'trabajo en parejas',
            'grupos_pequeños': 'grupos pequeños (3-4 estudiantes)',
            'grupos_grandes': 'grupos grandes (5-6 estudiantes)',
            'clase_completa': 'toda la clase'
        }
        
        for modalidad in modalidades:
            if modalidad in mapeo_modalidades:
                modalidades_formateadas.append(mapeo_modalidades[modalidad])
            else:
                modalidades_formateadas.append(modalidad.replace('_', ' '))
        
        return ', '.join(modalidades_formateadas)
    
    def _registrar_metadatos_estructurados(self, input_data: Dict):
        """
        Registra metadatos estructurados en el contexto híbrido del coordinador
        
        Args:
            input_data: Datos estructurados del input
        """
        if not self.coordinador:
            return
            
        # Actualizar contexto híbrido con metadatos estructurados
        self.coordinador.contexto_hibrido.actualizar_estado("input_estructurado_recibido", "UIController")
        
        # Registrar metadatos específicos
        estructura_fases = input_data.get('estructura_fases', {})
        metadatos_educativos = {
            'materia': input_data.get('materia', ''),
            'tema': input_data.get('tema', ''),
            'duracion_objetivo': input_data.get('duracion', {}).get('valor', 45),
            'modalidades_preferidas': input_data.get('modalidades', []),
            'estructura_preferida': estructura_fases.get('tipo', 'libre'),
            'fases_especificas': estructura_fases.get('fases', []),
            'fases_detalladas': estructura_fases.get('fases_detalladas', []),
            'contexto_adicional': input_data.get('contexto_adicional', '')
        }
        
        # Actualizar metadatos del contexto híbrido
        self.coordinador.contexto_hibrido.metadatos.update(metadatos_educativos)
        
        logger.info(f"📊 Metadatos estructurados registrados en contexto híbrido")
    
    def _enriquecer_ideas_con_estructura(self, ideas: List[Dict], input_data: Dict) -> List[Dict]:
        """
        Enriquece las ideas generadas con información de la estructura solicitada
        
        Args:
            ideas: Ideas generadas por el sistema
            input_data: Datos estructurados del input
            
        Returns:
            Ideas enriquecidas con metadatos estructurados
        """
        ideas_enriquecidas = []
        
        for idea in ideas:
            idea_enriquecida = idea.copy()
            
            # Añadir metadatos estructurados
            idea_enriquecida['metadatos_estructura'] = {
                'materia_solicitada': input_data.get('materia', ''),
                'tema_solicitado': input_data.get('tema', ''),
                'duracion_solicitada': input_data.get('duracion', {}).get('descripcion', ''),
                'modalidades_solicitadas': input_data.get('modalidades', []),
                'estructura_solicitada': input_data.get('estructura_fases', {}).get('tipo', 'libre')
            }
            
            # Actualizar duración si es específica
            duracion_valor = input_data.get('duracion', {}).get('valor')
            if duracion_valor and isinstance(duracion_valor, int):
                idea_enriquecida['duracion'] = f"{duracion_valor} minutos"
            
            # Añadir información de modalidades
            modalidades = input_data.get('modalidades', [])
            if modalidades:
                modalidades_texto = self._formatear_modalidades(modalidades)
                idea_enriquecida['modalidades_trabajo'] = modalidades_texto
            
            # Añadir etiqueta de origen
            idea_enriquecida['origen_generacion'] = 'input_estructurado'
            
            ideas_enriquecidas.append(idea_enriquecida)
        
        logger.debug(f"💎 Enriquecidas {len(ideas_enriquecidas)} ideas con estructura")
        return ideas_enriquecidas
    
    def generar_ideas_desde_input_progresivo(self, input_basico: Dict) -> List[Dict]:
        """
        NUEVO: Genera ideas desde input progresivo (materia/tema/duración)
        
        Args:
            input_basico: Input básico capturado en los primeros pasos
            
        Returns:
            Lista de ideas generadas
        """
        logger.info(f"🎮 Generando ideas desde input progresivo")
        logger.info(f"   📚 Materia: {input_basico.get('materia', 'N/A')}")
        logger.info(f"   🎯 Tema: {input_basico.get('tema', 'N/A')}")
        
        # Construir prompt base desde los datos básicos
        prompt_base = self._construir_prompt_basico(input_basico)
        
        # Registrar metadatos básicos en contexto
        self._registrar_metadatos_basicos(input_basico)
        
        # Generar ideas usando el sistema existente
        info_inicial = self.coordinador.recoger_informacion_inicial(prompt_profesor=prompt_base)
        ideas_base = info_inicial.get('ideas_generadas', [])
        
        # Enriquecer ideas con información básica
        ideas_enriquecidas = self._enriquecer_ideas_con_basicos(ideas_base, input_basico)
        
        return ideas_enriquecidas
    
    def aplicar_estructura_post_seleccion(self, actividad_seleccionada: Dict, estructura_detallada: Dict) -> Dict:
        """
        Aplica estructura detallada DESPUÉS de seleccionar la actividad
        
        Args:
            actividad_seleccionada: Actividad elegida por el profesor
            estructura_detallada: Estructura de fases configurada
            
        Returns:
            Proyecto final estructurado
        """
        logger.info(f"🔧 Aplicando estructura detallada a: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Construir prompt enriquecido con estructura
        prompt_estructurado = self._construir_prompt_con_estructura(actividad_seleccionada, estructura_detallada)
        
        # Registrar estructura en contexto híbrido
        self._registrar_estructura_detallada(estructura_detallada)
        
        # Ejecutar flujo MVP con prompt enriquecido
        logger.info("🚀 Ejecutando flujo MVP con estructura aplicada")
        proyecto_final = self.sistema.ejecutar_flujo({'descripcion': prompt_estructurado}, "")
        
        # Añadir metadatos de estructura al proyecto
        if 'metadatos' not in proyecto_final:
            proyecto_final['metadatos'] = {}
        
        proyecto_final['metadatos']['estructura_aplicada'] = estructura_detallada
        proyecto_final['metadatos']['flujo_utilizado'] = 'progresivo'
        proyecto_final['metadatos']['actividad_base_seleccionada'] = actividad_seleccionada
        
        return proyecto_final
    
    def _construir_prompt_basico(self, input_basico: Dict) -> str:
        """Construye prompt básico para generar ideas iniciales"""
        elementos = []
        
        # Materia y tema
        materia = input_basico.get('materia', '')
        tema = input_basico.get('tema', '')
        
        if materia and tema:
            elementos.append(f"Crear una actividad de {materia} sobre {tema}")
        elif tema:
            elementos.append(f"Crear una actividad educativa sobre {tema}")
        elif materia:
            elementos.append(f"Crear una actividad de {materia}")
        else:
            elementos.append("Crear una actividad educativa")
        
        # Duración
        duracion = input_basico.get('duracion', {})
        if duracion.get('descripcion'):
            elementos.append(f"con duración de {duracion['descripcion']}")
        
        # Idea específica si la hay
        prompt_usuario = input_basico.get('prompt_usuario', '')
        if prompt_usuario:
            elementos.append(f"Idea específica del profesor: {prompt_usuario}")
        
        # Contexto ABP
        elementos.append("La actividad debe seguir metodología ABP (Aprendizaje Basado en Proyectos)")
        elementos.append("Incluir adaptaciones para estudiantes con TEA, TDAH y altas capacidades")
        
        return '. '.join(elementos) + '.'
    
    def _construir_prompt_con_estructura(self, actividad: Dict, estructura: Dict) -> str:
        """Construye prompt enriquecido con estructura detallada"""
        elementos = []
        
        # Base de la actividad seleccionada
        titulo = actividad.get('titulo', '')
        descripcion = actividad.get('descripcion', '')
        
        if titulo:
            elementos.append(f"Desarrollar la actividad '{titulo}'")
        if descripcion:
            elementos.append(f"Descripción: {descripcion}")
        
        # Estructura de fases
        fases_incluidas = []
        
        # Preparación
        if estructura.get('preparacion', {}).get('incluir'):
            prep = estructura['preparacion']
            modalidad = prep.get('modalidad', 'grupos_pequeños').replace('_', ' ')
            if prep.get('repartir_tareas'):
                fases_incluidas.append(f"Preparación con reparto específico de tareas (trabajo {modalidad})")
            else:
                fases_incluidas.append(f"Preparación e Introducción (trabajo {modalidad})")
        
        # Ejecución (siempre incluida)
        ejecucion = estructura.get('ejecucion', {})
        aspectos = ejecucion.get('aspectos', ['colaboración'])
        modalidad_ej = ejecucion.get('modalidad', 'grupos_pequeños').replace('_', ' ')
        aspectos_texto = ', '.join(aspectos)
        if ejecucion.get('repartir_tareas'):
            fases_incluidas.append(f"Ejecución principal con {aspectos_texto} y reparto específico de tareas (trabajo {modalidad_ej})")
        else:
            fases_incluidas.append(f"Ejecución principal con {aspectos_texto} (trabajo {modalidad_ej})")
        
        # Reflexión
        if estructura.get('reflexion', {}).get('incluir'):
            refl = estructura['reflexion']
            modalidad = refl.get('modalidad', 'grupos_pequeños').replace('_', ' ')
            if refl.get('repartir_tareas'):
                fases_incluidas.append(f"Reflexión con reparto específico de tareas (trabajo {modalidad})")
            else:
                fases_incluidas.append(f"Reflexión y Evaluación (trabajo {modalidad})")
        
        # Recogida
        if estructura.get('recogida', {}).get('incluir'):
            rec = estructura['recogida']
            modalidad = rec.get('modalidad', 'grupos_pequeños').replace('_', ' ')
            if rec.get('repartir_tareas'):
                fases_incluidas.append(f"Recogida con reparto específico de tareas (trabajo {modalidad})")
            else:
                fases_incluidas.append(f"Recogida y Organización (trabajo {modalidad})")
        
        if fases_incluidas:
            elementos.append(f"Estructurar en las siguientes fases: {' → '.join(fases_incluidas)}")
        
        # Contexto ABP
        elementos.append("Seguir metodología ABP con adaptaciones para neurotipos diversos")
        
        return '. '.join(elementos) + '.'
    
    def _registrar_metadatos_basicos(self, input_basico: Dict):
        """Registra metadatos básicos en el contexto híbrido"""
        if not self.coordinador:
            return
        
        metadatos_basicos = {
            'materia': input_basico.get('materia', ''),
            'tema': input_basico.get('tema', ''),
            'duracion_objetivo': input_basico.get('duracion', {}).get('valor', 45),
            'sesiones_objetivo': input_basico.get('duracion', {}).get('sesiones', 1),
            'prompt_usuario': input_basico.get('prompt_usuario', ''),
            'flujo_tipo': 'progresivo'
        }
        
        self.coordinador.contexto_hibrido.actualizar_estado("input_progresivo_recibido", "UIController")
        self.coordinador.contexto_hibrido.metadatos.update(metadatos_basicos)
        
        logger.info(f"📊 Metadatos básicos registrados en contexto híbrido")
    
    def _registrar_estructura_detallada(self, estructura: Dict):
        """Registra estructura detallada en el contexto híbrido"""
        if not self.coordinador:
            return
        
        metadatos_estructura = {
            'estructura_detallada_aplicada': True,
            'fases_configuradas': estructura,
            'preparacion_incluida': estructura.get('preparacion', {}).get('incluir', False),
            'preparacion_reparto_tareas': estructura.get('preparacion', {}).get('repartir_tareas', False),
            'ejecucion_reparto_tareas': estructura.get('ejecucion', {}).get('repartir_tareas', False),
            'reflexion_incluida': estructura.get('reflexion', {}).get('incluir', False),
            'reflexion_reparto_tareas': estructura.get('reflexion', {}).get('repartir_tareas', False),
            'recogida_incluida': estructura.get('recogida', {}).get('incluir', False),
            'recogida_reparto_tareas': estructura.get('recogida', {}).get('repartir_tareas', False),
            'aspectos_ejecucion': estructura.get('ejecucion', {}).get('aspectos', [])
        }
        
        self.coordinador.contexto_hibrido.actualizar_estado("estructura_detallada_aplicada", "UIController")
        self.coordinador.contexto_hibrido.metadatos.update(metadatos_estructura)
        
        logger.info(f"🔧 Estructura detallada registrada en contexto híbrido")
    
    def _enriquecer_ideas_con_basicos(self, ideas: List[Dict], input_basico: Dict) -> List[Dict]:
        """Enriquece ideas con metadatos básicos"""
        ideas_enriquecidas = []
        
        for idea in ideas:
            idea_enriquecida = idea.copy()
            
            # Añadir metadatos básicos
            idea_enriquecida['metadatos_basicos'] = {
                'materia_solicitada': input_basico.get('materia', ''),
                'tema_solicitado': input_basico.get('tema', ''),
                'duracion_solicitada': input_basico.get('duracion', {}).get('descripcion', ''),
                'prompt_usuario': input_basico.get('prompt_usuario', '')
            }
            
            # Actualizar duración específica
            duracion_valor = input_basico.get('duracion', {}).get('valor')
            if duracion_valor:
                idea_enriquecida['duracion'] = input_basico['duracion']['descripcion']
            
            # Etiqueta de origen
            idea_enriquecida['origen_generacion'] = 'progresivo'
            
            ideas_enriquecidas.append(idea_enriquecida)
        
        return ideas_enriquecidas
    
    def matizar_idea(self, ideas: List[Dict], idea_idx: int, matizaciones: str) -> List[Dict]:
        """
        Solicita al coordinador matizar una idea seleccionada
        """
        if not (0 <= idea_idx < len(ideas)):
            logger.error(f"🎮 Índice de idea inválido: {idea_idx}")
            return ideas
            
        idea_seleccionada = ideas[idea_idx]
        logger.info(f"🎮 Solicitando matización de idea: {idea_seleccionada.get('titulo', '')}...")
        
        # Llamar directamente al coordinador
        return self.coordinador.matizar_idea_especifica(
            idea_seleccionada, 
            matizaciones, 
            self.coordinador.contexto_hibrido
        )
    
    def generar_nuevas_ideas(self, nuevo_prompt: str) -> List[Dict]:
        """
        Solicita al coordinador generar nuevas ideas con un prompt diferente
        """
        logger.info(f"🎮 Solicitando nuevas ideas con prompt: {nuevo_prompt[:50]}...")
        
        # Llamar directamente al coordinador
        return self.coordinador.generar_ideas_actividades_hibrido(
            nuevo_prompt, 
            self.coordinador.contexto_hibrido
        )
    
    def registrar_detalles_adicionales(self, actividad: Dict, detalles: str):
        """
        Registra detalles adicionales para una actividad seleccionada
        """
        logger.info(f"🎮 Registrando detalles adicionales para: {actividad.get('titulo', 'Sin título')}")
        
        # Registrar directamente en el coordinador
        if detalles.strip():
            from datetime import datetime
            self.coordinador.historial_prompts.append({
                "tipo": "detalles_actividad_seleccionada",
                "actividad_id": actividad.get('id'),
                "actividad_titulo": actividad.get('titulo'),
                "detalles_adicionales": detalles,
                "timestamp": datetime.now().isoformat()
            })
    
    def ejecutar_flujo_completo(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """
        Solicita al sistema ejecutar el flujo completo (usando MVP mejorado)
        
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