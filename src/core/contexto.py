"""
Gestión de contexto híbrido y estado global para el sistema de agentes ABP.
Combina auto-detección de metadatos, gestión de estado global y coordinación entre agentes.
"""

import re
import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("SistemaAgentesABP.ContextoHibrido")

@dataclass
class IteracionPrompt:
    """Registro de una iteración de prompt"""
    numero: int
    prompt: str
    accion: str  # "INICIAR", "AMPLIAR", "REFINAR", "REEMPLAZAR"
    metadatos_detectados: Dict
    timestamp: str

class ContextoHibrido:
    """
    Gestiona contexto híbrido con auto-detección de metadatos y estado global del proyecto.
    Combina funcionalidades de contexto LLM y coordinación entre agentes.
    """
    
    def __init__(self):
        # === CONTEXTO LLM ===
        # Contenido completo de la última respuesta
        self.texto_completo = ""
        
        # Historial de interacciones LLM
        self.historial = []
        
        # === ESTADO GLOBAL DEL PROYECTO ===
        # Metadatos estructurados (fusiona auto-detección + estado global)
        self.metadatos = {}
        
        # Gestión de agentes y coordinación
        self.perfiles_estudiantes = []
        self.recursos_disponibles = []
        self.restricciones = {}
        self.historial_decisiones = []
        self.errores = []
        self.validaciones = {}
        
        # Estado del proyecto
        self.estado_actual = "iniciado"
        self.version = 1
        
        # Metadata de sesión
        self.session_id = self._generar_session_id()
        self.timestamp_inicio = datetime.now().isoformat()
        self.prompts_realizados = 0
        
        # === PERSISTENCIA ===
        self.archivo_persistencia = "contexto_historico.json"
        self.cargar_estado_previo()
        
        logger.info(f"🔄 ContextoHibrido inicializado - Session: {self.session_id}")
        logger.info(f"🔄 Estado global inicializado")
        logger.info(f"💾 Persistencia activada: {self.archivo_persistencia}")
    
    def _generar_session_id(self) -> str:
        """Genera un ID único para la sesión"""
        return f"abp_hibrido_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def procesar_respuesta_llm(self, respuesta: str, prompt_usuario: str = ""):
        """Procesa la respuesta del LLM y actualiza el contexto automáticamente"""
        # 1. Guardar texto completo
        self.texto_completo = respuesta
        
        # 2. Auto-detectar metadatos
        nuevos_metadatos = self.autodetectar_metadatos(respuesta)
        
        # 3. Actualizar metadatos existentes
        self.metadatos.update(nuevos_metadatos)
        
        # 4. Guardar en historial
        iteracion = IteracionPrompt(
            numero=len(self.historial) + 1,
            prompt=prompt_usuario,
            accion=self.determinar_accion(prompt_usuario),
            metadatos_detectados=nuevos_metadatos,
            timestamp=datetime.now().isoformat()
        )
        
        self.historial.append(iteracion)
        self.prompts_realizados += 1
        
        logger.info(f"📊 Metadatos detectados: {list(nuevos_metadatos.keys())}")
    
    def autodetectar_metadatos(self, texto: str) -> Dict:
        """Auto-detecta metadatos del texto de respuesta del LLM"""
        metadatos = {}
        texto_lower = texto.lower()
        
        # DETECCIÓN DE MATERIA
        materias_patron = {
            'matematicas': ['matemáticas', 'fracciones', 'números', 'operaciones', 'mercado de las fracciones', 'cálculo', 'geometría'],
            'lengua': ['escritura', 'lectura', 'texto', 'poesía', 'gramática', 'ortografía', 'redacción'],
            'ciencias': ['experimento', 'laboratorio', 'célula', 'planeta', 'científico', 'naturaleza', 'física', 'química'],
            'geografia': ['geografía', 'mapa', 'comunidades', 'países', 'ciudades', 'regiones', 'españa', 'andalucía', 'cataluña', 'valencia', 'viajes', 'turismo', 'autonomas'],
            'historia': ['historia', 'época', 'siglos', 'acontecimientos', 'pasado'],
            'arte': ['arte', 'pintura', 'dibujo', 'creatividad', 'manualidades']
        }
        
        for materia, palabras_clave in materias_patron.items():
            if any(palabra in texto_lower for palabra in palabras_clave):
                metadatos['materia'] = materia
                break
        
        # DETECCIÓN DE DURACIÓN
        patron_duracion = re.search(r'(\d+)\s*(minutos?|min|horas?)', texto_lower)
        if patron_duracion:
            numero = int(patron_duracion.group(1))
            unidad = patron_duracion.group(2)
            if 'hora' in unidad:
                numero *= 60
            metadatos['duracion'] = f"{numero} minutos"
        
        # DETECCIÓN DE TEMA ESPECÍFICO
        temas_especificos = ['fracciones', 'multiplicación', 'división', 'geometría', 'ortografía', 'lectura', 'escritura', 'tiempos verbales', 'área', 'volumen']
        for tema in temas_especificos:
            if tema in texto_lower:
                metadatos['tema'] = tema
                break
        
        # DETECCIÓN DE ESTUDIANTES ESPECIALES
        estudiantes_especiales = []
        if 'elena' in texto_lower:
            contextos_elena = ['tea', 'apoyo visual', 'no se sienta perdida', 'tarjetas', 'protocolo visual']
            if any(contexto in texto_lower for contexto in contextos_elena):
                estudiantes_especiales.append('Elena (TEA - apoyo visual)')
        
        if 'luis' in texto_lower:
            contextos_luis = ['tdah', 'moverse', 'movimiento', 'inspector', 'activo', 'cada 15']
            if any(contexto in texto_lower for contexto in contextos_luis):
                estudiantes_especiales.append('Luis (TDAH - necesita movimiento)')
        
        if 'ana' in texto_lower:
            contextos_ana = ['altas capacidades', 'problemas extra', 'auditora', 'desafíos', 'complejos']
            if any(contexto in texto_lower for contexto in contextos_ana):
                estudiantes_especiales.append('Ana (Altas capacidades - desafíos extra)')
        
        if estudiantes_especiales:
            metadatos['estudiantes_especiales'] = estudiantes_especiales
        
        # DETECCIÓN DE MATERIALES
        materiales_patron = ['productos', 'dinero', 'calculadoras', 'tarjetas', 'papel', 'lápices', 'cartulinas', 'tijeras', 'pegamento']
        materiales_detectados = []
        for material in materiales_patron:
            if material in texto_lower:
                materiales_detectados.append(material)
        
        if materiales_detectados:
            metadatos['materiales'] = materiales_detectados
        
        # DETECCIÓN DE TIPO DE ACTIVIDAD
        tipos_actividad = {
            'simulación de mercado': ['mercado', 'tienda', 'comprar', 'vender', 'cajero', 'cliente'],
            'laboratorio': ['experimento', 'laboratorio', 'investigar', 'hipótesis'],
            'juego de roles': ['rol', 'personaje', 'actuar', 'interpretar'],
            'proyecto colaborativo': ['proyecto', 'colaborar', 'equipo', 'grupo'],
            'actividad artística': ['arte', 'pintura', 'dibujo', 'manualidades', 'creatividad'],
            'actividad física': ['deporte', 'juego', 'actividad física', 'movimiento', 'ejercicio'],
            'actividad de escritura': ['escritura', 'redacción', 'ensayo', 'poesía', 'texto'],
        }
        
        for tipo, palabras in tipos_actividad.items():
            if any(palabra in texto_lower for palabra in palabras):
                metadatos['tipo_actividad'] = tipo
                break
        
        # DETECCIÓN DE ROLES ESPECÍFICOS
        roles_detectados = []
        roles_patron = ['cajero', 'cajera', 'inspector', 'inspectora', 'auditor', 'auditora', 'cliente', 'vendedor', 'contador', 'contable']
        for rol in roles_patron:
            if rol in texto_lower:
                roles_detectados.append(rol)
        
        if roles_detectados:
            metadatos['roles_detectados'] = list(set(roles_detectados))  # Eliminar duplicados
        
        # DETECCIÓN DE ESTRUCTURA TEMPORAL
        if any(palabra in texto_lower for palabra in ['preparación', 'desarrollo', 'cierre', 'fases', 'etapas']):
            metadatos['tiene_estructura_temporal'] = True
            
        # DETECCIÓN DE REPARTO ESPECÍFICO DE TAREAS
        if any(palabra in texto_lower for palabra in ['reparto específico', 'repartir tareas', 'asignación individual']):
            metadatos['requiere_reparto_especifico'] = True
        
        return metadatos
    
    def determinar_accion(self, prompt: str) -> str:
        """Determina qué tipo de acción realizar basándose en el prompt"""
        if not prompt:
            return "INICIAR"
            
        prompt_lower = prompt.lower()
        
        # Indicadores de cambio total
        if any(palabra in prompt_lower for palabra in ['otra cosa', 'diferente', 'cambiar', 'mejor otra', 'no quiero esto']):
            return "REEMPLAZAR"
        
        # Indicadores de refinamiento
        if any(palabra in prompt_lower for palabra in ['más', 'también', 'además', 'incluir', 'añadir']):
            return "AMPLIAR"
        
        # Si hay contexto previo, por defecto es refinar
        if self.metadatos:
            return "REFINAR"
        
        return "INICIAR"
    
    def get_contexto_para_llm(self) -> str:
        """Genera el contexto enriquecido para enviar al LLM"""
        contexto_str = "\n=== CONTEXTO DETECTADO ===\n"
        
        if not self.metadatos:
            contexto_str += "(Ningún contexto detectado aún)\n"
        else:
            for clave, valor in self.metadatos.items():
                if isinstance(valor, list):
                    contexto_str += f"- {clave.replace('_', ' ').title()}: {', '.join(str(v) for v in valor)}\n"
                else:
                    contexto_str += f"- {clave.replace('_', ' ').title()}: {valor}\n"
        
        if self.texto_completo:
            contexto_str += f"\n=== ACTIVIDAD ANTERIOR ===\n{self.texto_completo[-1500:]}\n"  # Últimos 1500 chars
        
        if len(self.historial) > 1:
            contexto_str += f"\n=== ITERACIONES REALIZADAS ===\n"
            for iteracion in self.historial[-3:]:  # Últimas 3 iteraciones
                contexto_str += f"- {iteracion.accion}: {iteracion.prompt[:100]}...\n"
        
        return contexto_str
    
    def get_resumen_sesion(self) -> Dict:
        """Obtiene un resumen de la sesión actual"""
        return {
            'session_id': self.session_id,
            'prompts_realizados': self.prompts_realizados,
            'metadatos_detectados': self.metadatos,
            'tiene_actividad': bool(self.texto_completo),
            'iteraciones': len(self.historial)
        }
    
    def analizar_continuidad_contexto(self, prompt_nuevo: str) -> str:
        """MÉTODO OBSOLETO - Usar determinar_accion() en su lugar"""
        return self.determinar_accion(prompt_nuevo)
    
    # ===== MÉTODOS DE ESTADO GLOBAL Y COORDINACIÓN =====
    
    def actualizar_estado(self, nuevo_estado: str, agente: str = None):
        """
        Actualiza el estado del proyecto
        
        Args:
            nuevo_estado: Nuevo estado
            agente: Agente que actualiza el estado
        """
        self.estado_actual = nuevo_estado
        self.historial_decisiones.append({
            'timestamp': datetime.now().isoformat(),
            'agente': agente,
            'estado': nuevo_estado
        })
        logger.info(f"🔄 Estado actualizado: {nuevo_estado} por {agente}")
        
    def registrar_decision(self, agente: str, decision: str, datos: dict = None):
        """
        Registra una decisión tomada por un agente
        
        Args:
            agente: Agente que toma la decisión
            decision: Descripción de la decisión
            datos: Datos asociados a la decisión
        """
        self.historial_decisiones.append({
            'timestamp': datetime.now().isoformat(),
            'agente': agente,
            'decision': decision,
            'datos': datos or {}
        })
        
        logger.info(f"📝 Decisión registrada: {decision} por {agente}")
        
    def validar_coherencia(self) -> dict:
        """
        Valida la coherencia global del proyecto
        
        Returns:
            Diccionario con resultados de validación
        """
        coherencia = {
            'valido': True,
            'problemas': [],
            'sugerencias': []
        }
        
        # Validar que hay contenido mínimo
        if not self.metadatos.get('titulo'):
            coherencia['valido'] = False
            coherencia['problemas'].append("Falta título del proyecto")
            
        if not self.perfiles_estudiantes:
            coherencia['sugerencias'].append("Recomendado cargar perfiles de estudiantes")
            
        # Validar coherencia temporal
        duracion_total = self.metadatos.get('duracion', 0)
        if isinstance(duracion_total, str):
            # Extraer número de duración si es string
            duracion_match = re.search(r'(\d+)', str(duracion_total))
            duracion_total = int(duracion_match.group(1)) if duracion_match else 0
            
        if duracion_total > 120:
            coherencia['sugerencias'].append("Duración muy larga, considerar dividir en sesiones")
            
        return coherencia
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado actual
        
        Returns:
            Diccionario con resumen del estado
        """
        return {
            'estado_actual': self.estado_actual,
            'metadatos': self.metadatos,
            'version': self.version,
            'num_estudiantes': len(self.perfiles_estudiantes),
            'num_recursos': len(self.recursos_disponibles),
            'num_decisiones': len(self.historial_decisiones),
            'num_errores': len(self.errores),
            'ultima_actualizacion': self.historial_decisiones[-1]['timestamp'] if self.historial_decisiones else self.timestamp_inicio,
            'session_id': self.session_id,
            'prompts_realizados': self.prompts_realizados,
            'tiene_actividad': bool(self.texto_completo),
            'iteraciones': len(self.historial)
        }
    
    def registrar_error(self, origen: str, mensaje: str, detalles: Any = None):
        """
        Registra un error ocurrido
        
        Args:
            origen: Componente donde ocurrió el error
            mensaje: Descripción del error
            detalles: Detalles adicionales (opcional)
        """
        error = {
            'timestamp': datetime.now().isoformat(),
            'origen': origen,
            'mensaje': mensaje,
            'detalles': detalles
        }
        
        self.errores.append(error)
        logger.error(f"❌ Error en {origen}: {mensaje}")
        
        # Actualizar estado si es crítico
        if detalles and detalles.get('critico', False):
            self.actualizar_estado("error_critico", origen)
    
    def reiniciar(self):
        """Reinicia el estado a valores iniciales conservando metadatos básicos"""
        # Guardar metadatos importantes
        metadatos_preservados = {
            k: v for k, v in self.metadatos.items() 
            if k in ['titulo', 'descripcion', 'nivel', 'materia']
        }
        
        # Incrementar versión
        version_anterior = self.version
        
        # Reiniciar estado
        self.__init__()
        
        # Restaurar metadatos preservados y actualizar versión
        self.metadatos.update(metadatos_preservados)
        self.version = version_anterior + 1
        
        # Registrar reinicio
        self.actualizar_estado("reiniciado", "ContextoHibrido")
    
    def finalizar_proyecto(self, proyecto_final: Dict[str, Any]):
        """
        Finaliza el proyecto guardando los resultados finales
        
        Args:
            proyecto_final: Proyecto consolidado final
        """
        self.metadatos['proyecto_final'] = proyecto_final
        self.metadatos['timestamp_finalizacion'] = datetime.now().isoformat()
        self.actualizar_estado("finalizado", "ContextoHibrido")
        
        # Guardar estado al finalizar
        self.guardar_estado()
        
        logger.info(f"🎯 Proyecto finalizado: {proyecto_final.get('proyecto_base', {}).get('titulo', 'Sin título')}")
    
    # ===== MÉTODOS DE PERSISTENCIA =====
    
    def guardar_estado(self) -> None:
        """
        Guarda el estado actual del contexto a archivo JSON
        """
        try:
            estado_serializable = {
                'session_id': self.session_id,
                'timestamp_inicio': self.timestamp_inicio,
                'metadatos': self.metadatos,
                'historial_decisiones': self.historial_decisiones[-10:],  # Últimas 10
                'estado_actual': self.estado_actual,
                'version': self.version,
                'prompts_realizados': self.prompts_realizados,
                'patrones_exitosos': self._extraer_patrones_exitosos(),
                'timestamp_guardado': datetime.now().isoformat()
            }
            
            with open(self.archivo_persistencia, 'w', encoding='utf-8') as f:
                json.dump(estado_serializable, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Estado guardado en {self.archivo_persistencia}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error guardando estado: {e}")
    
    def cargar_estado_previo(self) -> None:
        """
        Carga estado de sesiones anteriores si existe
        """
        try:
            if os.path.exists(self.archivo_persistencia):
                with open(self.archivo_persistencia, 'r', encoding='utf-8') as f:
                    estado_previo = json.load(f)
                
                # Integrar patrones exitosos del pasado
                patrones_previos = estado_previo.get('patrones_exitosos', [])
                if patrones_previos:
                    self.metadatos['patrones_historicos'] = patrones_previos
                    logger.info(f"📚 Cargados {len(patrones_previos)} patrones históricos")
                
                # Cargar metadatos útiles
                metadatos_previos = estado_previo.get('metadatos', {})
                materias_usadas = metadatos_previos.get('materias_trabajadas', [])
                if materias_usadas:
                    self.metadatos['materias_historicas'] = materias_usadas
                
                logger.info(f"🔄 Estado histórico cargado desde {self.archivo_persistencia}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando estado previo: {e}")
    
    def _extraer_patrones_exitosos(self) -> List[Dict]:
        """
        Extrae patrones de proyectos exitosos para reutilización futura
        
        Returns:
            Lista de patrones exitosos
        """
        patrones = []
        
        # Si el proyecto actual fue exitoso, extraer patrón
        if (self.estado_actual == "finalizado" and 
            self.metadatos.get('proyecto_final')):
            
            patron = {
                'materia': self.metadatos.get('materia', ''),
                'tema': self.metadatos.get('tema', ''),
                'duracion': self.metadatos.get('duracion', ''),
                'tipo_actividad': self.metadatos.get('tipo_actividad', ''),
                'modalidades_usadas': self.metadatos.get('modalidades_preferidas', []),
                'timestamp': datetime.now().isoformat(),
                'exito': True
            }
            
            patrones.append(patron)
        
        return patrones
    
    def recomendar_basado_en_historial(self, nueva_solicitud: Dict) -> List[str]:
        """
        Genera recomendaciones basadas en patrones históricos
        
        Args:
            nueva_solicitud: Nueva solicitud del usuario
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        patrones_historicos = self.metadatos.get('patrones_historicos', [])
        materias_historicas = self.metadatos.get('materias_historicas', [])
        
        # Recomendar basado en materia
        materia_nueva = nueva_solicitud.get('materia', '')
        if materia_nueva in materias_historicas:
            recomendaciones.append(f"He trabajado antes con {materia_nueva}, puedo sugerir actividades similares")
        
        # Recomendar basado en patrones exitosos
        for patron in patrones_historicos:
            if patron.get('materia') == materia_nueva:
                tipo_previo = patron.get('tipo_actividad', '')
                if tipo_previo:
                    recomendaciones.append(f"Actividades tipo '{tipo_previo}' funcionaron bien anteriormente")
        
        return recomendaciones
    
    # ===== MÉTODOS DE COMPATIBILIDAD =====
    
    def get_resumen_sesion(self) -> Dict:
        """MÉTODO LEGACY - Usar obtener_resumen() en su lugar"""
        return self.obtener_resumen()