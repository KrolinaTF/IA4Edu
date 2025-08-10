#!/usr/bin/env python3
"""
Sistema de Agentes para ABP (Aprendizaje Basado en Proyectos) - Estructura Sencilla
Arquitectura modular con 5 agentes especializados y validación iterativa
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, is_dataclass
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SistemaAgentesABP")

def serialize(obj):
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def parse_json_seguro(texto: str) -> Optional[dict]:
    """Parseo robusto de JSON con múltiples estrategias de limpieza"""
    try:
        # Estrategia 1: Limpieza básica
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()
        
        # Estrategia 2: Detectar respuestas en texto plano (incluyendo markdown)
        if (texto_limpio.startswith("A continuación") or 
            texto_limpio.startswith("Aquí") or 
            texto_limpio.startswith("**") or  # Markdown
            texto_limpio.startswith("#") or   # Headers
            not texto_limpio.startswith("{")):  # No empieza con JSON
            
            # El LLM respondió en texto plano, extraer JSON si existe
            json_match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
            if json_match:
                texto_limpio = json_match.group()
            else:
                logger.warning(f"❌ LLM respondió en texto plano sin JSON válido")
                logger.warning(f"🔍 Respuesta: {texto[:200]}...")
                return None
                
        if not texto_limpio:
            raise ValueError("Respuesta vacía")
            
        # Estrategia 3: Buscar el primer { hasta el último }
        start_idx = texto_limpio.find('{')
        end_idx = texto_limpio.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            texto_limpio = texto_limpio[start_idx:end_idx+1]
        else:
            logger.warning(f"❌ No se encontraron llaves válidas en: {texto_limpio[:100]}...")
            return None
            
        return json.loads(texto_limpio)
        
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  JSON malformado, intentando reparar: {e}")
        
        # Estrategia 4: Intentar reparar JSON común
        try:
            # Reparar comillas internas comunes
            texto_reparado = texto_limpio
            # Escapar comillas internas en valores
            texto_reparado = re.sub(r'"([^"]*)"([^"]*)"([^"]*)":', r'"\1\"\2\"\3":', texto_reparado)
            # Añadir comas faltantes antes de llaves
            texto_reparado = re.sub(r'"\s*\n\s*{', '",\n    {', texto_reparado)
            # Añadir comas faltantes entre objetos
            texto_reparado = re.sub(r'}\s*\n\s*{', '},\n    {', texto_reparado)
            
            return json.loads(texto_reparado)
            
        except json.JSONDecodeError:
            logger.error(f"❌ No se pudo reparar el JSON del LLM")
            logger.error(f"🔍 Texto recibido (primeros 400 chars): {texto[:400]}...")
            return None
    except Exception as e:
        logger.error(f"❌ Error inesperado en parseo JSON: {e}")
        return None
    
# ===== ESTRUCTURAS DE DATOS =====

@dataclass
class Actividad:
    """Estructura de la actividad educativa"""
    descripcion: str
    nivel_educativo: str
    competencias_objetivo: List[str]
    duracion_estimada: int
    tipo_producto: str

@dataclass
class Estudiante:
    """Estructura del estudiante"""
    id: str
    nombre: str
    fortalezas: List[str]
    necesidades_apoyo: List[str]
    disponibilidad: int
    historial_roles: List[str]
    adaptaciones: List[str]

@dataclass  
class Tarea:
    """Estructura de la tarea"""
    id: str
    descripcion: str
    competencias_requeridas: List[str]
    complejidad: int  # 1-5
    tipo: str  # "individual", "colaborativa", "creativa"
    dependencias: List[str]
    tiempo_estimado: int

@dataclass
class ProyectoABP:
    """Estructura del proyecto completo de ABP"""
    titulo: str
    descripcion: str
    duracion: str
    competencias_objetivo: List[str]
    fases: List[Dict]
    asignaciones: List[Dict]
    recursos: Dict
    evaluacion: Dict
    metadatos: Dict

# ===== CONTEXTO HÍBRIDO AUTO-DETECTADO =====

@dataclass
class IteracionPrompt:
    """Registro de una iteración de prompt"""
    numero: int
    prompt: str
    accion: str  # "INICIAR", "AMPLIAR", "REFINAR", "REEMPLAZAR"
    metadatos_detectados: Dict
    timestamp: str

class ContextoHibrido:
    """Gestiona contexto híbrido con auto-detección de metadatos"""
    
    def __init__(self):
        # Metadatos estructurados (auto-detectados)
        self.metadatos = {}
        
        # Contenido completo de la última respuesta
        self.texto_completo = ""
        
        # Historial de interacciones
        self.historial = []
        
        # Metadata de sesión
        self.session_id = self._generar_session_id()
        self.timestamp_inicio = datetime.now().isoformat()
        self.prompts_realizados = 0
        
        logger.info(f"🔄 Contexto híbrido inicializado - Session: {self.session_id}")
    
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
                    contexto_str += f"- {clave.replace('_', ' ').title()}: {', '.join(valor)}\n"
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
    
    
    
    
    

# ===== INTEGRACIÓN OLLAMA =====
# (Mantiene el mismo integrador de Ollama, no necesita cambios)
class OllamaIntegrator:
    """Integrador simplificado con Ollama API"""
    
    def __init__(self, host: str = "192.168.1.10", port: int = 11434, model: str = "llama3.2"):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        
        # Conectar directamente con Ollama API usando requests
        self.session = requests.Session()
        
        # Probar conexión con Ollama
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Conectado exitosamente a Ollama en {self.base_url}")
                self.ollama_disponible = True
            else:
                logger.error(f"❌ Error conectando a Ollama: {response.status_code}")
                self.ollama_disponible = False
        except Exception as e:
            logger.error(f"❌ No se pudo conectar a Ollama en {self.base_url}: {e}")
            self.ollama_disponible = False
            
    def generar_respuesta(self, prompt: str, max_tokens: int = 500) -> str:
        """Genera respuesta usando Ollama"""
        if self.ollama_disponible:
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens
                    }
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"❌ Error en API Ollama: {response.status_code}")
                    return self._respuesta_fallback()
                    
            except Exception as e:
                logger.error(f"❌ Error generando respuesta: {e}")
                return self._respuesta_fallback()
        else:
            return self._respuesta_fallback()
    
    def _respuesta_fallback(self) -> str:
        """Respuesta de fallback cuando Ollama no está disponible"""
        return """
        [SIMULADO JSON]
        {
            "estudiante_001": {
                "tareas": ["tarea_01", "tarea_03"],
                "rol": "coordinador",
                "justificacion": "Basado en su fortaleza de liderazgo."
            },
            "estudiante_002": {
                "tareas": ["tarea_02"],
                "rol": "diseñador",
                "justificacion": "Su creatividad visual es perfecta para esta tarea."
            }
        }
        """

# ===== ESTADO GLOBAL Y COORDINACIÓN MEJORADA =====

class EstadoGlobalProyecto:
    """Estado centralizado del proyecto en desarrollo"""
    
    def __init__(self):
        self.metadatos = {}
        self.perfiles_estudiantes = []
        self.recursos_disponibles = []
        self.restricciones = {}
        self.historial_decisiones = []
        self.version = 1
        self.timestamp_inicio = datetime.now().isoformat()
        self.estado_actual = "iniciado"
        self.errores = []
        self.validaciones = {}
        
    def actualizar_estado(self, nuevo_estado: str, agente: str = None):
        """Actualiza el estado del proyecto"""
        self.estado_actual = nuevo_estado
        self.historial_decisiones.append({
            'timestamp': datetime.now().isoformat(),
            'agente': agente,
            'estado': nuevo_estado
        })
        logger.info(f"🔄 Estado actualizado: {nuevo_estado} por {agente}")
        
    def registrar_decision(self, agente: str, decision: str, datos: dict = None):
        """Registra una decisión tomada por un agente"""
        self.historial_decisiones.append({
            'timestamp': datetime.now().isoformat(),
            'agente': agente,
            'decision': decision,
            'datos': datos or {}
        })
        
    def validar_coherencia(self) -> dict:
        """Valida la coherencia global del proyecto"""
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

class ComunicadorAgentes:
    """Sistema de comunicación centralizada entre agentes"""
    
    def __init__(self):
        self.mensajes = []
        self.agentes_registrados = {}
        
    def registrar_agente(self, nombre: str, agente):
        """Registra un agente en el sistema de comunicación"""
        self.agentes_registrados[nombre] = agente
        logger.info(f"🔗 Agente registrado: {nombre}")
        
    def enviar_mensaje(self, remitente: str, destinatario: str, metodo: str, datos: dict) -> dict:
        """Envía un mensaje de un agente a otro con trazabilidad"""
        if destinatario not in self.agentes_registrados:
            raise Exception(f"Agente destinatario no encontrado: {destinatario}")
            
        mensaje = {
            'id': len(self.mensajes) + 1,
            'timestamp': datetime.now().isoformat(),
            'remitente': remitente,
            'destinatario': destinatario,
            'metodo': metodo,
            'datos': datos,
            'estado': 'enviado'
        }
        
        self.mensajes.append(mensaje)
        logger.info(f"📨 Mensaje {mensaje['id']}: {remitente} → {destinatario}.{metodo}")
        
        try:
            # Ejecutar método en el agente destinatario
            agente = self.agentes_registrados[destinatario]
            metodo_func = getattr(agente, metodo, None)
            
            if not metodo_func:
                raise Exception(f"Método no encontrado: {metodo} en {destinatario}")
                
            # Determinar argumentos según el agente
            if destinatario == 'analizador_tareas' and metodo == 'descomponer_actividad':
                resultado = metodo_func(datos.get('proyecto_base', {}))
            elif destinatario == 'perfilador_estudiantes' and metodo == 'analizar_perfiles':
                resultado = metodo_func(datos.get('tareas', {}))
            elif destinatario == 'optimizador_asignaciones' and metodo == 'optimizar_asignaciones':
                resultado = metodo_func(
                    datos.get('tareas', {}),
                    datos.get('analisis_estudiantes', {}),
                    self.agentes_registrados.get('perfilador_estudiantes')
                )
            elif destinatario == 'generador_recursos' and metodo == 'generar_recursos':
                # Extraer tareas y asignaciones de todos_los_resultados
                todos_resultados = datos.get('todos_los_resultados', {})
                tareas_resultado = todos_resultados.get('analizador_tareas', {})
                asignaciones_resultado = todos_resultados.get('optimizador_asignaciones', {})
                
                # Extraer la lista de tareas si existe
                tareas = tareas_resultado.get('tareas', []) if isinstance(tareas_resultado, dict) else []
                asignaciones = asignaciones_resultado if isinstance(asignaciones_resultado, dict) else {}
                
                resultado = metodo_func(
                    datos.get('proyecto_base', {}),
                    tareas,
                    asignaciones
                )
            else:
                # Método genérico
                resultado = metodo_func(**datos)
                
            mensaje['estado'] = 'completado'
            mensaje['resultado'] = resultado
            
            logger.info(f"✅ Mensaje {mensaje['id']} completado exitosamente")
            return resultado
            
        except Exception as e:
            mensaje['estado'] = 'error'
            mensaje['error'] = str(e)
            logger.error(f"❌ Mensaje {mensaje['id']} falló: {e}")
            raise e
            
    def obtener_historial(self, filtro_agente: str = None) -> list:
        """Obtiene el historial de comunicación"""
        if filtro_agente:
            return [m for m in self.mensajes 
                   if m['remitente'] == filtro_agente or m['destinatario'] == filtro_agente]
        return self.mensajes

# ===== AGENTES ESPECIALIZADOS (Refactorizados) =====

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Clase base para todos los agentes especializados del sistema ABP
    
    Proporciona funcionalidad común y establece la interfaz estándar que
    todos los agentes deben seguir, eliminando duplicación de código.
    """
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """Inicializa el agente base con integrador LLM"""
        self.ollama = ollama_integrator
        self.agent_name = self.__class__.__name__
        
        # Logger específico para cada agente
        self.logger = logging.getLogger(f"SistemaAgentesABP.{self.agent_name}")
        self.logger.info(f"🤖 {self.agent_name} inicializado")
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Método principal de procesamiento - debe ser implementado por cada agente
        
        Args:
            *args, **kwargs: Argumentos específicos de cada agente
            
        Returns:
            Any: Resultado del procesamiento específico del agente
        """
        pass
    
    @abstractmethod 
    def _parse_response(self, response: str) -> Any:
        """
        Parsea respuesta del LLM - implementación específica por agente
        
        Args:
            response: Respuesta cruda del LLM
            
        Returns:
            Any: Datos estructurados específicos del agente
        """
        pass
    
    # ===== MÉTODOS COMUNES DE EXTRACCIÓN DE TEXTO =====
    
    def _extraer_campo(self, texto: str, campo: str, default: str = "No especificado") -> str:
        """Extrae un campo específico del texto"""
        if not texto or not campo:
            return default
            
        lines = texto.split('\n')
        for line in lines:
            if campo.lower() in line.lower():
                # Extraer después del campo
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
                # Alternativa: extraer después del campo sin ':'
                return line.replace(campo, '').strip()
        return default
    
    def _extraer_lista(self, texto: str, campo: str) -> List[str]:
        """Extrae una lista separada por comas del texto"""
        valor = self._extraer_campo(texto, campo, "")
        if valor and valor != "No especificado":
            # Limpiar y dividir por comas
            items = [item.strip().strip('•-*') for item in valor.split(',')]
            return [item for item in items if item]  # Filtrar vacíos
        return []
    
    def _extraer_numero(self, texto: str, campo: str, default: int = 1) -> int:
        """Extrae un número del texto"""
        valor = self._extraer_campo(texto, campo, "")
        if valor:
            # Buscar primer número en el valor
            numeros = re.findall(r'\d+', valor)
            if numeros:
                return int(numeros[0])
        return default
    
    def _extraer_duracion(self, texto: str) -> int:
        """Extrae duración en minutos del texto"""
        # Buscar patrones como "30 min", "1 hora", "1.5 horas"
        duracion_match = re.search(r'(\d+(?:\.\d+)?)\s*(min|minuto|hora|sesion|session)', texto.lower())
        if duracion_match:
            cantidad = float(duracion_match.group(1))
            unidad = duracion_match.group(2)
            
            if 'hora' in unidad:
                return int(cantidad * 60)  # Convertir a minutos
            elif 'min' in unidad:
                return int(cantidad)
            elif 'sesion' in unidad:
                return int(cantidad * 45)  # Asumimos 45 min por sesión
        
        return 45  # Default: 45 minutos
    
    # ===== MÉTODOS COMUNES DE INTERACCIÓN CON LLM =====
    
    def _call_llm_with_fallback(self, prompt: str, max_tokens: int, fallback_data: Any, 
                               fallback_name: str = "fallback") -> Any:
        """
        Llama al LLM con manejo robusto de errores y fallback
        
        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo tokens de respuesta
            fallback_data: Datos a usar si falla el LLM
            fallback_name: Nombre del fallback para logging
            
        Returns:
            Datos parseados del LLM o fallback
        """
        try:
            self.logger.info(f"🔄 {self.agent_name} llamando al LLM...")
            response = self.ollama.generar_respuesta(prompt, max_tokens=max_tokens)
            
            if not response or not response.strip():
                raise ValueError("Respuesta vacía del LLM")
            
            parsed = self._parse_response(response)
            if parsed is not None:
                self.logger.info(f"✅ {self.agent_name} - Respuesta LLM procesada exitosamente")
                return parsed
            else:
                raise ValueError("Falló el parseo de la respuesta LLM")
                
        except Exception as e:
            self.logger.error(f"❌ {self.agent_name} - Error en llamada LLM: {e}")
            self.logger.info(f"⚠️  {self.agent_name} - Usando {fallback_name}")
            return fallback_data
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parsea respuesta JSON con manejo robusto de errores"""
        return parse_json_seguro(response)
    
    def _crear_prompt_estructurado(self, template: str, **kwargs) -> str:
        """
        Crea un prompt estructurado reemplazando placeholders
        
        Args:
            template: Template del prompt con placeholders {variable}
            **kwargs: Variables para reemplazar en el template
            
        Returns:
            Prompt con variables reemplazadas
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"❌ {self.agent_name} - Variable faltante en prompt: {e}")
            return template
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    def _log_processing_start(self, input_description: str):
        """Log del inicio del procesamiento"""
        self.logger.info(f"🚀 {self.agent_name} - Iniciando procesamiento: {input_description}")
    
    def _log_processing_end(self, result_description: str):
        """Log del fin del procesamiento"""  
        self.logger.info(f"🎯 {self.agent_name} - Procesamiento completado: {result_description}")
    
    def _validate_required_params(self, params: Dict[str, Any], required: List[str]) -> bool:
        """Valida que los parámetros requeridos estén presentes"""
        missing = [param for param in required if param not in params or params[param] is None]
        if missing:
            self.logger.error(f"❌ {self.agent_name} - Parámetros faltantes: {missing}")
            return False
        return True

class AgenteCoordinador:
    """Agente Coordinador Principal (Master Agent) - CON CONTEXTO HÍBRIDO AUTO-DETECTADO"""
    
    def __init__(self):
        # Inicializar integrador Ollama propio
        self.ollama = OllamaIntegrator()
        
        self.historial_prompts = []  # Mantener por compatibilidad
        self.ejemplos_k = self._cargar_ejemplos_k()
        self.contexto_hibrido = ContextoHibrido()

        # Inicializar agentes especializados
        self.analizador_tareas = AgenteAnalizadorTareas(self.ollama)
        self.perfilador = AgentePerfiladorEstudiantes(self.ollama)
        self.optimizador = AgenteOptimizadorAsignaciones(self.ollama)
        self.generador_recursos = AgenteGeneradorRecursos(self.ollama)

        # Registro de agentes especializados (FIX: atributo faltante)
        self.agentes_especializados = {}

        # Nuevos componentes de coordinación
        self.estado_global = EstadoGlobalProyecto()
        self.comunicador = ComunicadorAgentes()
        
        # Registrar agentes en el comunicador y diccionario
        agentes_a_registrar = {
            'analizador_tareas': self.analizador_tareas,
            'perfilador_estudiantes': self.perfilador,
            'optimizador_asignaciones': self.optimizador,
            'generador_recursos': self.generador_recursos
        }
        
        for nombre, agente in agentes_a_registrar.items():
            self.comunicador.registrar_agente(nombre, agente)
            self.agentes_especializados[nombre] = agente
    
        # Configuración de flujo
        self.flujo_config = {
            'max_iteraciones': 3,
            'validacion_automatica': True,
            'reintentos_por_agente': 2,
            'timeout_por_agente': 60
        }
        
        logger.info(f"🚀 AgenteCoordinador inicializado con {len(self.agentes_especializados)} agentes especializados")
    
    def _cargar_ejemplos_k(self) -> Dict[str, str]:
        """Carga ejemplos k_ para few-shot learning"""
        ejemplos = {}
        
        # Obtener directorio base del proyecto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # Subir un nivel desde /src
        
        # Rutas absolutas para los archivos k_
        archivos_k = [
            os.path.join(base_dir, "data", "actividades", "k_feria_acertijos.txt"),
            os.path.join(base_dir, "data", "actividades", "k_sonnet_supermercado.txt"), 
            os.path.join(base_dir, "data", "actividades", "k_celula.txt"),
            os.path.join(base_dir, "data", "actividades", "k_piratas.txt"),
            os.path.join(base_dir, "data", "actividades", "k_sonnet7_fabrica_fracciones.txt")
        ]
        
        for archivo in archivos_k:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    nombre_ejemplo = archivo.split('/')[-1].replace('.txt', '').replace('k_', '')
                    ejemplos[nombre_ejemplo] = contenido  # Contenido completo del ejemplo
                    logger.info(f"✅ Cargado ejemplo k_: {nombre_ejemplo}")
            except FileNotFoundError:
                logger.warning(f"❌ No se encontró el archivo: {archivo}")
                continue
        
        if ejemplos:
            logger.info(f"📚 Cargados {len(ejemplos)} ejemplos k_ para few-shot learning")
        else:
            logger.warning("⚠️ No se cargaron ejemplos k_, usando fallback")
            
        return ejemplos
    
    def _crear_fallback_analisis(self, prompt_original: str):
        """Genera un diccionario de fallback basado en el prompt original."""
        
        # Aquí puedes usar tu lógica para extraer información del prompt
        # Por ejemplo, una simple búsqueda de palabras clave
        tema = "indefinido"
        if "arte" in prompt_original.lower():
            tema = "actividad artística"
        
        duracion = "una semana"
        if "un mes" in prompt_original.lower():
            duracion = "un mes"

        # Retorna un diccionario con los valores extraídos o por defecto
        return {
            "tema": tema,
            "restricciones": [], # Puedes dejar esto vacío o con un valor por defecto
            "formato_arte": "indefinido",
            "objetivo": "indefinido", # No siempre lo podemos extraer, es mejor un valor neutro
            "duracion": duracion
        }
    
    def generar_ideas_actividades_hibrido(self, prompt_profesor: str, contexto_hibrido: ContextoHibrido) -> List[Dict]:
        """Genera 3 ideas de actividades usando contexto híbrido auto-detectado"""
        
        # Crear prompt enriquecido con contexto híbrido
        prompt_completo = self._crear_prompt_hibrido(prompt_profesor, contexto_hibrido)
        
        # Generar ideas
        respuesta = self.ollama.generar_respuesta(prompt_completo, max_tokens=600)
        ideas = self._parsear_ideas(respuesta)
        
        # PROCESAR RESPUESTA CON CONTEXTO HÍBRIDO
        contexto_hibrido.procesar_respuesta_llm(respuesta, prompt_profesor)
        
        logger.info(f"📊 Contexto actualizado: {list(contexto_hibrido.metadatos.keys())}")
        
        return ideas
    
    
    def _crear_prompt_hibrido(self, prompt_profesor: str, contexto_hibrido: ContextoHibrido) -> str:
        """Crea prompt usando contexto híbrido auto-detectado"""
        
        # Obtener contexto enriquecido del sistema híbrido
        contexto_str = contexto_hibrido.get_contexto_para_llm()
        
        # Seleccionar ejemplo k_ relevante basado en metadatos detectados
        tema_detectado = contexto_hibrido.metadatos.get('materia', '') + ' ' + contexto_hibrido.metadatos.get('tema', '')
        ejemplo_seleccionado = self._seleccionar_ejemplo_relevante(tema_detectado.strip())
        
        # Construir prompt híbrido
        prompt_hibrido = f"""
Eres un experto en diseño de actividades educativas para 4º de Primaria.

{contexto_str}

=== NUEVA PETICIÓN DEL USUARIO ===
{prompt_profesor}

=== ESTUDIANTES ESPECÍFICOS (AULA_A_4PRIM) ===
- 001 ALEX M.: reflexivo, visual, CI 102
- 002 MARÍA L.: reflexivo, auditivo
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118 - Necesita apoyo visual y rutinas
- 004 LUIS T.: impulsivo, kinestetico, TDAH combinado, CI 102 - Necesita movimiento
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141 - Necesita desafíos extra
- 006 SARA M.: equilibrado, auditivo, CI 115
- 007 EMMA K.: reflexivo, visual, CI 132
- 008 HUGO P.: equilibrado, visual, CI 114"""
        
        if ejemplo_seleccionado:
            prompt_hibrido += f"""

=== EJEMPLO DE ACTIVIDAD EXITOSA ===
{ejemplo_seleccionado}

=== PATRONES A SEGUIR ===
• NARRATIVA INMERSIVA: Contextualizar con historias atractivas
• OBJETIVOS CLAROS: Competencias específicas del tema + habilidades transversales
• ROL DOCENTE: Observación activa, guía discreta, gestión emocional
• ADAPTACIONES: Específicas para TEA, TDAH, altas capacidades
• MATERIALES CONCRETOS: Manipulativos, reales, accesibles"""
        else:
            prompt_hibrido += f"""

=== PRINCIPIOS PEDAGÓGICOS ===
• CENTRADO EN EL ESTUDIANTE: Actividades que partan de sus intereses y necesidades
• APRENDIZAJE SIGNIFICATIVO: Conectar con experiencias reales y contextos auténticos
• INCLUSIÓN: Adaptaciones para TEA (Elena), TDAH (Luis), altas capacidades (Ana)
• COLABORACIÓN: Fomentar trabajo en equipo y comunicación
• CREATIVIDAD: Permitir múltiples formas de expresión y solución"""
        
        prompt_hibrido += f"""

=== INSTRUCCIONES CRÍTICAS ===
IMPORTANTE: Lee atentamente la petición del usuario y céntrate EXCLUSIVAMENTE en el tema que solicita.

Genera exactamente 3 ideas de actividades educativas que:
1. RESPONDAN DIRECTAMENTE al tema específico solicitado por el usuario
2. MANTENGAN COHERENCIA TEMÁTICA en las 3 ideas (no mezclar materias diferentes)
3. Sean apropiadas para el tema detectado en el contexto: {contexto_hibrido.metadatos.get('materia', 'tema solicitado')}
4. Incluyan adaptaciones para Elena (TEA), Luis (TDAH) y Ana (altas capacidades)
5. Sean completamente ejecutables en 4º Primaria

SI el usuario pidió geografía → las 3 ideas deben ser de geografía
SI el usuario pidió ciencias → las 3 ideas deben ser de ciencias
SI el usuario pidió matemáticas → las 3 ideas deben ser de matemáticas

NO desvíes del tema principal solicitado por el usuario.

FORMATO EXACTO:
IDEA 1:
Título: [título del tema específico solicitado]
Descripción: [descripción detallada del tema solicitado]
Nivel: 4º Primaria
Competencias: [competencias del tema específico]
Duración: [tiempo realista]

IDEA 2:
[mismo formato, mismo tema...]

IDEA 3:
[mismo formato, mismo tema...]

Céntrate en el tema solicitado y proporciona 3 variaciones creativas del MISMO tema.
"""
        
        return prompt_hibrido
    
    
    def _seleccionar_ejemplo_relevante(self, tema: str) -> str:
        """Selecciona el ejemplo k_ más relevante según el tema del contexto JSON"""
        if not tema:
            return ""  # Sin tema, sin ejemplo específico
            
        tema_lower = tema.lower()
        
        # Mapeo dinámico basado en el contexto real
        mapeo_ejemplos = {
            'supermercado': 'sonnet_supermercado',
            'dinero': 'sonnet_supermercado', 
            'comercio': 'sonnet_supermercado',
            'fracciones': 'sonnet7_fabrica_fracciones',
            'fábrica': 'sonnet7_fabrica_fracciones',
            'ciencias': 'celula',
            'células': 'celula',
            'biología': 'celula',
            'piratas': 'piratas',
            'tesoro': 'piratas',
            'aventura': 'piratas',
            # NO HAY EJEMPLOS DE GEOGRAFÍA - Devolver vacío para máxima creatividad
            'geografia': None,
            'españa': None,
            'comunidades': None,
            'viajes': None
        }
        
        # Buscar coincidencias exactas
        for palabra_clave, ejemplo in mapeo_ejemplos.items():
            if palabra_clave in tema_lower:
                if ejemplo is None:
                    # Intencionalmente sin ejemplo para máxima creatividad
                    return ""
                elif ejemplo in self.ejemplos_k:
                    return self.ejemplos_k[ejemplo]
        
        # Si no hay coincidencias, devolver vacío para que el LLM sea más creativo
        return ""
    
    def _get_ejemplo_fallback(self) -> str:
        """Ejemplo de fallback cuando no hay ejemplos k_ disponibles"""
        return """
EJEMPLO ACTIVIDAD ABP:
ACTIVIDAD: Feria Matemática Colaborativa
OBJETIVOS: Desarrollar competencias matemáticas mediante resolución colaborativa de problemas
DESCRIPCIÓN: Los estudiantes participan en estaciones rotativas resolviendo desafíos matemáticos
ROL PROFESOR: Observación activa y guía discreta
ADAPTACIONES: Apoyo visual para TEA, movimiento para TDAH, retos adicionales para altas capacidades
MATERIALES: Material manipulativo, fichas de problemas, cronómetros
"""
    
    def _parsear_ideas(self, respuesta: str) -> List[Dict]:
        """Parsea la respuesta para extraer las 3 ideas con múltiples patrones"""
        ideas = []
        
        # Intentar múltiples patrones de división
        patrones_division = ["IDEA ", "**IDEA ", "# IDEA ", "\n\n"]
        partes = None
        
        for patron in patrones_division:
            temp_partes = respuesta.split(patron)
            if len(temp_partes) > 1:
                partes = temp_partes
                break
        
        if not partes:
            # Si no hay divisiones claras, tratar toda la respuesta como una idea
            partes = ["", respuesta]
        
        # Procesar cada parte encontrada
        for i, parte in enumerate(partes[1:]):  # Saltar primera parte vacía
            if not parte.strip() or i >= 3:  # Máximo 3 ideas
                continue
                
            idea = {
                "id": f"idea_{i+1}",
                "titulo": self._extraer_titulo_inteligente(parte),
                "descripcion": self._extraer_descripcion_inteligente(parte),
                "nivel": self._extraer_nivel_inteligente(parte),
                "competencias": self._extraer_competencias_inteligente(parte),
                "duracion": self._extraer_duracion_inteligente(parte)
            }
            ideas.append(idea)
        
        # Si no se encontraron ideas estructuradas, crear una única idea general
        if not ideas:
            ideas.append({
                "id": "idea_1",
                "titulo": self._extraer_titulo_inteligente(respuesta),
                "descripcion": respuesta[:200] + "..." if len(respuesta) > 200 else respuesta,
                "nivel": "4º Primaria",
                "competencias": "Matemáticas, trabajo en equipo",
                "duracion": "2-3 sesiones"
            })
        
        return ideas  # Devolver todas las ideas generadas
    
    def _extraer_titulo_inteligente(self, texto: str) -> str:
        """Extrae título usando múltiples patrones"""
        patrones = [
            r'Título:\s*([^\n]+)',
            r'\*\*([^*]+)\*\*',
            r'"([^"]+)"',
            r'\d+[.:)]\s*([^\n]+)',
            r'^([^\n.!?]+)[.!?]?'
        ]
        
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                titulo = match.group(1).strip()
                titulo = re.sub(r'^[\d\s.*:-]+', '', titulo).strip()
                if len(titulo) > 5:
                    return titulo
        
        return "Actividad Educativa"
    
    def _extraer_descripcion_inteligente(self, texto: str) -> str:
        """Extrae descripción usando múltiples patrones"""
        desc_match = re.search(r'Descripción:\s*([^\n]+(?:\n[^\n:]+)*)', texto, re.IGNORECASE)
        if desc_match:
            return desc_match.group(1).strip()
        
        lines = texto.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 50 and ':' not in line and not line.startswith(('Nivel', 'Duración', 'Competencias')):
                return line
        
        return "Actividad práctica para desarrollar competencias matemáticas"
    
    def _extraer_nivel_inteligente(self, texto: str) -> str:
        """Extrae nivel educativo usando múltiples patrones"""
        nivel_match = re.search(r'Nivel:\s*([^\n]+)', texto, re.IGNORECASE)
        if nivel_match:
            return nivel_match.group(1).strip()
        
        keywords = {
            'primaria': '4º Primaria',
            'cuarto': '4º Primaria', 
            'secundaria': 'Secundaria',
            'infantil': 'Educación Infantil'
        }
        
        texto_lower = texto.lower()
        for keyword, nivel in keywords.items():
            if keyword in texto_lower:
                return nivel
        
        return "4º Primaria"
    
    def _extraer_competencias_inteligente(self, texto: str) -> str:
        """Extrae competencias usando múltiples patrones"""
        comp_match = re.search(r'Competencias:\s*([^\n]+)', texto, re.IGNORECASE)
        if comp_match:
            return comp_match.group(1).strip()
        
        competencias_encontradas = []
        keywords = {
            'matemáticas': 'Competencia matemática',
            'fracciones': 'Competencia matemática',
            'sumas': 'Competencia matemática',
            'decimales': 'Competencia matemática',
            'comunicación': 'Competencia lingüística',
            'trabajo en equipo': 'Competencia social',
            'creatividad': 'Competencia artística',
            'tecnología': 'Competencia digital'
        }
        
        texto_lower = texto.lower()
        for keyword, competencia in keywords.items():
            if keyword in texto_lower and competencia not in competencias_encontradas:
                competencias_encontradas.append(competencia)
        
        return ', '.join(competencias_encontradas) if competencias_encontradas else "Competencia matemática, trabajo colaborativo"
    
    def _extraer_duracion_inteligente(self, texto: str) -> str:
        """Extrae duración usando múltiples patrones"""
        dur_match = re.search(r'Duración:\s*([^\n]+)', texto, re.IGNORECASE)
        if dur_match:
            return dur_match.group(1).strip()
        
        tiempo_patterns = [
            r'(\d+)\s*sesiones?',
            r'(\d+)\s*horas?',
            r'(\d+)\s*días?',
            r'(\d+)\s*semanas?'
        ]
        
        for pattern in tiempo_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "2-3 sesiones"
    
    def recoger_informacion_inicial(self, prompt_profesor: str, perfiles_estudiantes: list = None, 
                                  recursos_disponibles: list = None, restricciones: dict = None) -> dict:
        """Recoge y estructura toda la información inicial del proyecto"""
        logger.info("📋 Recogiendo información inicial del proyecto")
        
        # Actualizar estado global con información inicial
        self.estado_global.metadatos['prompt_original'] = prompt_profesor
        if perfiles_estudiantes:
            self.estado_global.perfiles_estudiantes = perfiles_estudiantes
        if recursos_disponibles:
            self.estado_global.recursos_disponibles = recursos_disponibles
        if restricciones:
            self.estado_global.restricciones = restricciones
            
        self.estado_global.actualizar_estado("informacion_recopilada", "AgenteCoordinador")
        
        # Generar ideas base usando el método existente
        contexto_temporal = ContextoHibrido()
        ideas = self.generar_ideas_actividades_hibrido(prompt_profesor, contexto_temporal)
        
        return {
            'ideas_generadas': ideas,
            'estado': self.estado_global,
            'timestamp': datetime.now().isoformat()
        }
        
    def ejecutar_flujo_orquestado(self, idea_seleccionada: dict, informacion_adicional: str = "") -> dict:
        """Ejecuta el flujo completo orquestado con validaciones y manejo de errores"""
        logger.info("🚀 Iniciando flujo orquestado mejorado")
        
        # Actualizar estado global con idea seleccionada
        self.estado_global.metadatos.update(idea_seleccionada)
        self.estado_global.metadatos['informacion_adicional'] = informacion_adicional
        self.estado_global.actualizar_estado("ejecutando_flujo", "AgenteCoordinador")
        
        # Definir flujo de ejecución
        flujo = [
            {
                'agente': 'analizador_tareas',
                'metodo': 'descomponer_actividad',
                'prioridad': 1,
                'descripcion': 'Descomponer actividad en tareas específicas'
            },
            {
                'agente': 'perfilador_estudiantes',
                'metodo': 'analizar_perfiles',
                'prioridad': 2,
                'descripcion': 'Analizar perfiles de estudiantes'
            },
            {
                'agente': 'optimizador_asignaciones',
                'metodo': 'optimizar_asignaciones',
                'prioridad': 3,
                'descripcion': 'Optimizar asignaciones estudiante-tarea'
            },
            {
                'agente': 'generador_recursos',
                'metodo': 'generar_recursos',
                'prioridad': 4,
                'descripcion': 'Generar recursos educativos'
            }
        ]
        
        # Ejecutar cada paso del flujo
        resultados = {}
        proyecto_base = self.coordinar_proceso(idea_seleccionada, informacion_adicional)
        
        for i, paso in enumerate(flujo):
            try:
                logger.info(f"⚙️ Paso {i+1}/{len(flujo)}: {paso['descripcion']}")
                
                # Ejecutar agente usando el comunicador si está disponible
                if paso['agente'] in self.agentes_especializados:
                    datos = self._preparar_datos_para_agente(paso['agente'], proyecto_base, resultados)
                    resultado = self.comunicador.enviar_mensaje(
                        remitente="AgenteCoordinador",
                        destinatario=paso['agente'],
                        metodo=paso['metodo'],
                        datos=datos
                    )
                    resultados[paso['agente']] = resultado
                    
                    # Validación intermedia
                    coherencia = self.estado_global.validar_coherencia()
                    if coherencia['sugerencias']:
                        logger.info(f"💡 Sugerencias: {coherencia['sugerencias']}")
                        
                    logger.info(f"✅ Paso {i+1} completado exitosamente")
                else:
                    logger.warning(f"⚠️ Agente {paso['agente']} no disponible, saltando paso")
                    
            except Exception as e:
                logger.error(f"❌ Error en paso {i+1} ({paso['agente']}): {e}")
                self.estado_global.errores.append({
                    'paso': i+1,
                    'agente': paso['agente'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Continuar con el siguiente paso en caso de error
                continue
                
        # Consolidación final
        return self._consolidar_resultados_mejorado(proyecto_base, resultados)
        
    def _preparar_datos_para_agente(self, agente_nombre: str, proyecto_base: dict, resultados: dict) -> dict:
        """Prepara los datos necesarios para cada agente"""
        datos_base = {
            'contexto_global': self.estado_global.metadatos,
            'timestamp': datetime.now().isoformat()
        }
        
        if agente_nombre == 'analizador_tareas':
            datos_base['proyecto_base'] = proyecto_base
        elif agente_nombre == 'perfilador_estudiantes':
            datos_base['tareas'] = resultados.get('analizador_tareas', {})
        elif agente_nombre == 'optimizador_asignaciones':
            datos_base.update({
                'tareas': resultados.get('analizador_tareas', {}),
                'analisis_estudiantes': resultados.get('perfilador_estudiantes', {})
            })
        elif agente_nombre == 'generador_recursos':
            datos_base.update({
                'proyecto_base': proyecto_base,
                'todos_los_resultados': resultados
            })
            
        return datos_base
        
    def _consolidar_resultados_mejorado(self, proyecto_base: dict, resultados: dict) -> dict:
        """Consolida todos los resultados en un proyecto coherente mejorado"""
        logger.info("🔄 Consolidando resultados finales con validación avanzada")
        
        self.estado_global.actualizar_estado("consolidando", "AgenteCoordinador")
        
        # Validación final de coherencia
        coherencia_final = self.estado_global.validar_coherencia()
        
        # Estadísticas del proceso
        estadisticas = {
            'total_agentes_ejecutados': len(resultados),
            'total_mensajes': len(self.comunicador.mensajes),
            'errores_encontrados': len(self.estado_global.errores),
            'tiempo_total': datetime.now().isoformat()
        }
        
        proyecto_final = {
            'proyecto_base': proyecto_base,
            'resultados_agentes': {
                'tareas': resultados.get('analizador_tareas', {}),
                'perfiles': resultados.get('perfilador_estudiantes', {}),
                'asignaciones': resultados.get('optimizador_asignaciones', {}),
                'recursos': resultados.get('generador_recursos', {})
            },
            'estado_global': {
                'metadatos': self.estado_global.metadatos,
                'estado_final': self.estado_global.estado_actual,
                'historial_decisiones': self.estado_global.historial_decisiones,
                'errores': self.estado_global.errores
            },
            'validacion': {
                'coherencia_final': coherencia_final,
                'estadisticas': estadisticas
            },
            'comunicacion': {
                'historial_mensajes': self.comunicador.obtener_historial(),
                'total_comunicaciones': len(self.comunicador.mensajes)
            },
            'timestamp_finalizacion': datetime.now().isoformat()
        }
        
        self.estado_global.actualizar_estado("completado", "AgenteCoordinador")
        
        # Log de resumen final
        logger.info(f"✅ Proyecto completado: {estadisticas['total_agentes_ejecutados']} agentes, {estadisticas['total_mensajes']} mensajes")
        if isinstance(coherencia_final, dict) and coherencia_final.get('sugerencias'):
            logger.info(f"💡 Sugerencias finales: {coherencia_final['sugerencias']}")
        
        return proyecto_final
        
    def coordinar_proceso(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """Coordina todo el proceso de creación del proyecto ABP (Método original mantenido por compatibilidad)"""
        if info_adicional:
            self.historial_prompts.append({
                "tipo": "info_adicional",
                "contenido": info_adicional,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"🎯 Coordinando proyecto: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Crear estructura base del proyecto
        proyecto_base = {
            "titulo": actividad_seleccionada.get("titulo", "Proyecto ABP"),
            "descripcion": actividad_seleccionada.get("descripcion", ""),
            "nivel": actividad_seleccionada.get("nivel", "4º Primaria"),
            "competencias_base": actividad_seleccionada.get("competencias", "").split(", ") if actividad_seleccionada.get("competencias") else [],
            "duracion_base": actividad_seleccionada.get("duracion", "2 semanas"),
            "info_adicional": info_adicional
        }
        
        # Registrar en estado global si está disponible
        if hasattr(self, 'estado_global') and self.estado_global:
            self.estado_global.metadatos.update(proyecto_base)
            self.estado_global.actualizar_estado("estructura_base_creada", "AgenteCoordinador")
        
        return proyecto_base
        
    def crear_proyecto_final(self, proyecto_base: Dict, tareas: List[Tarea], 
                            asignaciones: Dict, recursos: Dict) -> Dict:
        """Crea la estructura final del proyecto"""
        
        # Organizar tareas por fases
        fases = self.organizar_fases_proyecto(tareas)
        
        # Crear diccionario completo de tareas con toda la información
        tareas_detalladas = {}
        for tarea in tareas:
            tareas_detalladas[tarea.id] = {
                "id": tarea.id,
                "descripcion": tarea.descripcion,
                "competencias_requeridas": tarea.competencias_requeridas,
                "complejidad": tarea.complejidad,
                "tipo": tarea.tipo,
                "dependencias": tarea.dependencias,
                "tiempo_estimado": tarea.tiempo_estimado
            }
        
        # Crear estructura final
        proyecto_final = {
            "proyecto": {
                "titulo": proyecto_base["titulo"],
                "descripcion": proyecto_base["descripcion"],
                "duracion": proyecto_base["duracion_base"],
                "competencias_objetivo": proyecto_base["competencias_base"],
                "recursos_materiales": len(recursos.get('recursos_materiales', [])) if recursos and isinstance(recursos, dict) else 0
            },
            "tareas": tareas_detalladas,
            "fases": fases,
            "asignaciones": asignaciones,
            "recursos": recursos,
            "evaluacion": {
                "criterios": ["Calidad del trabajo", "Colaboración", "Creatividad", "Competencias específicas"],
                "instrumentos": ["Rúbrica", "Autoevaluación", "Evaluación por pares", "Portfolio digital"]
            },
            "metadatos": {
                "timestamp": datetime.now().isoformat(),
                "sistema": "AgentesABP_v2.0_ContextoAcumulativo",
                "historial_prompts": self.historial_prompts,
                "contexto_hibrido": self.contexto_hibrido.get_resumen_sesion(),
                "validado": False
            }
        }
        
        return proyecto_final
    
    def organizar_fases_proyecto(self, tareas: List[Tarea]) -> List[Dict]:
        """Organiza las tareas en fases del proyecto"""
        fases = [
            {
                "nombre": "Fase 1: Investigación y Planificación",
                "duracion": "3-4 días",
                "tareas": [t.id for t in tareas if "investigar" in t.descripcion.lower() or "planificar" in t.descripcion.lower()]
            },
            {
                "nombre": "Fase 2: Desarrollo y Creación",
                "duracion": "5-6 días", 
                "tareas": [t.id for t in tareas if t.tipo in ["colaborativa", "creativa"]]
            },
            {
                "nombre": "Fase 3: Presentación y Evaluación",
                "duracion": "2-3 días",
                "tareas": [t.id for t in tareas if "presentar" in t.descripcion.lower() or "evaluar" in t.descripcion.lower()]
            }
        ]
        
        # Asegurar que todas las tareas estén asignadas a alguna fase
        tareas_asignadas = set()
        for fase in fases:
            tareas_asignadas.update(fase["tareas"])
        
        # Asignar tareas restantes a la fase de desarrollo
        for tarea in tareas:
            if tarea.id not in tareas_asignadas:
                fases[1]["tareas"].append(tarea.id)
        
        return fases
        
    def ejecutar_flujo_completo_con_ui(self, prompt_profesor: str) -> Dict:
        """Ejecuta todo el flujo de coordinación con interacción UI delegada"""
        logger.info("🎯 Iniciando flujo completo con coordinación centralizada")
        
        # Cargar perfiles de estudiantes
        perfiles_estudiantes = self.perfilador._cargar_perfiles_reales()
        
        # Recolectar información inicial y generar ideas
        info_inicial = self.recoger_informacion_inicial(
            prompt_profesor=prompt_profesor,
            perfiles_estudiantes=perfiles_estudiantes
        )
        
        ideas = info_inicial['ideas_generadas']
        
        # Manejar interacción y selección (aquí delego a UI pero mantengo lógica de negocio)
        actividad_seleccionada = self._manejar_seleccion_con_ui(ideas)
        
        # Ejecutar flujo orquestado completo
        proyecto_final = self.ejecutar_flujo_orquestado(actividad_seleccionada)
        
        return proyecto_final
    
    def _manejar_seleccion_con_ui(self, ideas: List[Dict]) -> Dict:
        """Maneja la selección de actividad con UI (simplificado por ahora)"""
        # Por ahora, mantener la lógica existente pero centralizada aquí
        # TODO: En futura iteración, separar completamente UI de lógica
        
        print("\n💡 IDEAS GENERADAS:")
        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
            print(f"   Descripción: {idea.get('descripción', 'No disponible')}")
            print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
            print(f"   Duración: {idea.get('duracion', 'No especificada')}")
        
        actividad_seleccionada = None
        
        while True:
            try:
                print(f"\n🎯 Opciones disponibles:")
                print(f"   1-{len(ideas)}: Seleccionar una de las ideas y continuar")
                print(f"   M: Me gusta alguna idea pero quiero matizarla/perfilarla")
                print(f"   0: Generar nuevas ideas con un prompt diferente")
                
                if actividad_seleccionada:
                    print(f"   -1: Añadir más detalles a la idea '{actividad_seleccionada.get('titulo', 'Sin título')}'")
                
                seleccion_input = input(f"\n🎯 Su elección: ").strip().upper()
                
                # Lógica de selección
                if seleccion_input.isdigit():
                    seleccion = int(seleccion_input)
                    if 1 <= seleccion <= len(ideas):
                        actividad_seleccionada = ideas[seleccion - 1]
                        logger.info(f"✅ Actividad seleccionada: {actividad_seleccionada.get('titulo', 'Sin título')}")
                        break
                    elif seleccion == 0:
                        # Generar nuevas ideas
                        nuevo_prompt = input("\n📝 Ingrese un nuevo prompt: ")
                        info_inicial = self.recoger_informacion_inicial(prompt_profesor=nuevo_prompt)
                        ideas = info_inicial['ideas_generadas']
                        continue
                    
                elif seleccion_input == 'M':
                    # Manejar matización
                    ideas = self._procesar_matizacion_ui(ideas)
                    continue
                    
                elif seleccion_input == '-1' and actividad_seleccionada:
                    # Añadir detalles
                    detalles = input("\n📋 Información adicional: ")
                    self._registrar_detalles_adicionales(actividad_seleccionada, detalles)
                    break
                else:
                    print("❌ Selección no válida")
                    
            except Exception as e:
                logger.error(f"Error en selección: {e}")
                print("❌ Error en la selección, intente nuevamente")
        
        return actividad_seleccionada
    
    def _procesar_matizacion_ui(self, ideas: List[Dict]) -> List[Dict]:
        """Procesa matización de ideas con UI"""
        try:
            idea_idx = int(input(f"¿Qué idea desea matizar? (1-{len(ideas)}): ")) - 1
            if not (0 <= idea_idx < len(ideas)):
                print("❌ Número de idea no válido")
                return ideas
                
            matizaciones = input("📝 ¿Cómo desea matizar/perfilar la idea?: ")
            
            # Procesar matización usando el contexto híbrido
            prompt_matizacion = f"""Matiza esta idea educativa con las siguientes especificaciones:

IDEA ORIGINAL:
{ideas[idea_idx]}

MATIZACIONES SOLICITADAS:
{matizaciones}

Genera 3 nuevas versiones matizadas manteniendo la esencia pero incorporando los cambios solicitados.

INSTRUCCIONES CRÍTICAS:
1. Responde SOLO con JSON válido, sin explicaciones
2. NO uses texto antes o después del JSON
3. Asegúrate de que todas las comas y llaves estén correctas
4. Duración máxima: 2 horas

FORMATO OBLIGATORIO:
{{
  "ideas": [
    {{
      "titulo": "Título corto y claro",
      "descripcion": "Descripción sin comillas internas",
      "nivel": "4º Primaria",
      "duracion": "2 horas máximo"
    }},
    {{
      "titulo": "Título corto y claro",
      "descripcion": "Descripción sin comillas internas",
      "nivel": "4º Primaria", 
      "duracion": "2 horas máximo"
    }},
    {{
      "titulo": "Título corto y claro",
      "descripcion": "Descripción sin comillas internas",
      "nivel": "4º Primaria",
      "duracion": "2 horas máximo"
    }}
  ]
}}"""

            respuesta_matizada = self.ollama.generar_respuesta(prompt_matizacion)
            ideas_matizadas = parse_json_seguro(respuesta_matizada)
            
            if ideas_matizadas and 'ideas' in ideas_matizadas:
                print("\n💡 IDEAS MATIZADAS:")
                for i, idea in enumerate(ideas_matizadas['ideas'], 1):
                    print(f"\n{i+len(ideas)}. {idea.get('titulo', 'Sin título')}")
                    print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
                
                ideas.extend(ideas_matizadas['ideas'])
            
        except Exception as e:
            logger.error(f"Error en matización: {e}")
            print("❌ Error al procesar matización")
            
        return ideas
    
    def _registrar_detalles_adicionales(self, actividad: Dict, detalles: str):
        """Registra detalles adicionales en el historial"""
        self.historial_prompts.append({
            "tipo": "detalles_adicionales",
            "actividad": actividad.get('titulo', 'Sin título'),
            "contenido": detalles,
            "timestamp": datetime.now().isoformat()
        })
        logger.info("📝 Detalles adicionales registrados")

class AgenteAnalizadorTareas(BaseAgent):
    """Agente Analizador de Tareas (Task Analyzer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        super().__init__(ollama_integrator)
    
    def descomponer_actividad(self, proyecto_base: Dict) -> List[Tarea]:
        """Descompone la actividad en subtareas específicas"""
        
        prompt_tareas = f"""
Analiza este proyecto educativo siguiendo los patrones exitosos de actividades k_ y descomponlo en subtareas específicas:

PROYECTO: {proyecto_base['titulo']}
DESCRIPCIÓN: {proyecto_base['descripcion']}
NIVEL: {proyecto_base['nivel']}
DURACIÓN: {proyecto_base['duracion_base']}
INFORMACIÓN ADICIONAL: {proyecto_base.get('info_adicional', 'No disponible')}

=== PATRONES EXITOSOS K_ ===
• NARRATIVA INMERSIVA: Mantener contexto atractivo en cada tarea (ofrecer opciones con y sin narrativa)
• ESTRUCTURA PEDAGÓGICA: Preparación → Desarrollo → Reflexión (si el profesor solicita otra estructura, dar prioridad a la suya)
• ROLES ESPECÍFICOS: Asignar roles concretos según fortalezas (Si la actividad tiene roles, si no, repartir las tareas sin un rol concreto)
• MATERIAL MANIPULATIVO: Usar objetos reales y tangibles a ser posible, reciclados o accesibles NO tecnológicos. siempre analogicos
• ADAPTACIONES DUA: Considerar TEA, TDAH, altas capacidades. Expras en qué se traduce la adaptación en esta actividad concreta
• EVALUACIÓN FORMATIVA: Observación y registro continuo

=== ESTRUCTURA RECOMENDADA === adaptar completamente a la especificación del profesor
1. PREPARACIÓN: Contextualización y organización (tantas tareas como requiera la actividad)
2. DESARROLLO: Núcleo de la actividad (tantas tareas como requiera la complejidad del proyecto)
3. REFLEXIÓN: Metacognición y cierre (según necesidades de evaluación)

Identifica las subtareas necesarias para completar el proyecto (sin límite fijo, según la complejidad de la actividad). Para cada subtarea proporciona:
- Descripción clara y específica (con contexto narrativo si se solicita)
- Competencias requeridas (matemáticas, lengua, ciencias, creativas, digitales)
- Complejidad del 1 al 5 (1=muy fácil, 5=muy difícil)
- Tipo: individual, colaborativa, o creativa
- Tiempo estimado en horas
- Dependencias (qué tareas deben completarse antes)
- Adaptaciones sugeridas

Formato:
TAREA 1:
Descripción: [descripción específica con contexto narrativo]
Competencias: [competencias separadas por comas]
Complejidad: [1-5]
Tipo: [individual/colaborativa/creativa]
Tiempo: [horas]
Dependencias: [ninguna o nombre de tareas previas]
Adaptaciones: [adaptaciones específicas para diversidad]

[Repetir para todas las tareas siguiendo estructura Preparación-Desarrollo-Reflexión...]
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_tareas, max_tokens=800)
        return self._parsear_tareas(respuesta)
    
    def _parsear_tareas(self, respuesta: str) -> List[Tarea]:
        """Parsea la respuesta para crear objetos Tarea"""
        tareas = []
        partes = respuesta.split("TAREA ")
        
        for i, parte in enumerate(partes[1:]):  # Saltar el primer elemento vacío
            if not parte.strip():
                continue
                
            tarea = Tarea(
                id=f"tarea_{i+1:02d}",
                descripcion=self._extraer_campo(parte, "Descripción:"),
                competencias_requeridas=self._extraer_lista(parte, "Competencias:"),
                complejidad=self._extraer_numero(parte, "Complejidad:", 3),
                tipo=self._extraer_campo(parte, "Tipo:"),
                dependencias=self._extraer_lista(parte, "Dependencias:"),
                tiempo_estimado=self._extraer_numero(parte, "Tiempo:", 2)
            )
            tareas.append(tarea)
        
        return tareas
    
    # Métodos heredados de BaseAgent: _extraer_campo, _extraer_lista, _extraer_numero
    
    def process(self, proyecto_base: Dict) -> List[Tarea]:
        """Implementa el método abstracto process de BaseAgent"""
        return self.descomponer_actividad(proyecto_base)
    
    def _parse_response(self, response: str) -> List[Dict]:
        """Parsea respuesta del LLM para tareas"""
        return self._parsear_tareas(response)
    
    def _crear_tareas_fallback(self) -> List[Tarea]:
        """Crea tareas genéricas como fallback"""
        return [
            Tarea(
                id="tarea_01",
                descripcion="Preparación y contextualización de la actividad",
                competencias_requeridas=["organizativas"],
                complejidad=2,
                tipo="individual",
                dependencias=[],
                tiempo_estimado=30
            ),
            Tarea(
                id="tarea_02",
                descripcion="Desarrollo principal de la actividad",
                competencias_requeridas=["específicas del proyecto"],
                complejidad=3,
                tipo="colaborativa", 
                dependencias=["tarea_01"],
                tiempo_estimado=60
            ),
            Tarea(
                id="tarea_03",
                descripcion="Reflexión y cierre de la actividad",
                competencias_requeridas=["metacognitivas"],
                complejidad=2,
                tipo="individual",
                dependencias=["tarea_02"],
                tiempo_estimado=20
            )
        ]

class AgentePerfiladorEstudiantes(BaseAgent):
    """Agente Perfilador de Estudiantes - AULA_A_4PRIM"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        super().__init__(ollama_integrator)
        self.perfiles_base = self._cargar_perfiles_reales()
        self.logger.info(f"👥 Perfilador inicializado con {len(self.perfiles_base)} estudiantes del AULA_A_4PRIM")
    
    def _cargar_perfiles_reales(self) -> List[Estudiante]:
        """Carga los perfiles reales específicos del AULA_A_4PRIM desde el archivo JSON"""
        try:
            # Obtener ruta absoluta al archivo de perfiles
            script_dir = os.path.dirname(os.path.abspath(__file__))
            perfiles_path = os.path.join(script_dir, "perfiles_4_primaria.json")
            
            with open(perfiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            estudiantes = []
            for perfil in data["estudiantes"]:
                # Extraer información rica del JSON
                fortalezas = self._extraer_fortalezas(perfil)
                necesidades_apoyo = self._extraer_necesidades_apoyo(perfil)
                adaptaciones = perfil.get("necesidades_especiales", [])
                historial_roles = self._generar_historial_roles(perfil)
                
                estudiante = Estudiante(
                    id=perfil["id"],
                    nombre=perfil["nombre"],
                    fortalezas=fortalezas,
                    necesidades_apoyo=necesidades_apoyo,
                    disponibilidad=self._calcular_disponibilidad(perfil),
                    historial_roles=historial_roles,
                    adaptaciones=adaptaciones
                )
                estudiantes.append(estudiante)
            
            # Log detallado de estudiantes cargados
            self.logger.info(f"✅ AULA_A_4PRIM: Cargados {len(estudiantes)} perfiles reales:")
            for est in estudiantes:
                # Buscar el perfil original para obtener el diagnóstico
                perfil_original = next((p for p in data["estudiantes"] if p["id"] == est.id), {})
                diagnostico = self._obtener_diagnostico_legible(perfil_original.get("diagnostico_formal", "ninguno"))
                self.logger.info(f"   • {est.nombre} (ID: {est.id}) - {diagnostico}")
            
            return estudiantes
            
        except FileNotFoundError:
            self.logger.error("❌ CRÍTICO: No se encontró perfiles_4_primaria.json")
            self.logger.error("   El sistema requiere los perfiles reales de estudiantes")
            raise FileNotFoundError("Archivo perfiles_4_primaria.json requerido para el funcionamiento")
        except Exception as e:
            self.logger.error(f"❌ Error cargando perfiles reales: {e}")
            raise
    
    def _extraer_fortalezas(self, perfil: dict) -> List[str]:
        """Extrae fortalezas basándose en competencias conseguidas y intereses"""
        fortalezas = []
        
        # Basado en competencias conseguidas/superadas
        if perfil["matematicas"].get("numeros_10000") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("matemáticas_números")
        if perfil["matematicas"].get("operaciones_complejas") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("operaciones_matemáticas")
        if perfil["lengua"].get("tiempos_verbales") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("gramática")
        if perfil["lengua"].get("textos_informativos") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("comunicación_escrita")
        if perfil["ciencias"].get("metodo_cientifico") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("investigación")
        
        # Basado en intereses
        for interes in perfil["intereses"]:
            if interes == "ciencias":
                fortalezas.append("curiosidad_científica")
            elif interes == "experimentos":
                fortalezas.append("experimentación")
            elif interes == "trabajo_en_grupo":
                fortalezas.append("colaboración")
            elif interes == "lectura":
                fortalezas.append("comprensión_lectora")
        
        # Basado en características específicas
        if perfil["temperamento"] == "reflexivo":
            fortalezas.append("pensamiento_analítico")
        if perfil["tolerancia_frustracion"] == "alta":
            fortalezas.append("perseverancia")
            
        return fortalezas  # Devolver todas las fortalezas identificadas
    
    def _extraer_necesidades_apoyo(self, perfil: dict) -> List[str]:
        """Extrae necesidades de apoyo basándose en el perfil completo"""
        necesidades = []
        
        # Basado en nivel de apoyo
        if perfil["nivel_apoyo"] == "alto":
            necesidades.append("supervisión_continua")
        elif perfil["nivel_apoyo"] == "medio":
            necesidades.append("check_ins_regulares")
        
        # Basado en tolerancia a la frustración
        if perfil["tolerancia_frustracion"] == "baja":
            necesidades.append("apoyo_emocional")
            necesidades.append("tareas_graduadas")
        
        # Basado en canal preferido
        if perfil["canal_preferido"] == "visual":
            necesidades.append("apoyos_visuales")
        elif perfil["canal_preferido"] == "auditivo":
            necesidades.append("explicaciones_verbales")
        elif perfil["canal_preferido"] == "kinestésico":
            necesidades.append("actividades_manipulativas")
        
        # Basado en diagnóstico formal
        diagnostico = perfil.get("diagnostico_formal", "ninguno")
        if "TEA" in diagnostico:
            necesidades.extend(["rutinas_estructuradas", "ambiente_predecible"])
        elif "TDAH" in diagnostico:
            necesidades.extend(["instrucciones_claras", "descansos_frecuentes"])
        elif "altas_capacidades" in diagnostico:
            necesidades.extend(["retos_adicionales", "proyectos_autonomos"])
        
        return necesidades
    
    def _calcular_disponibilidad(self, perfil: dict) -> int:
        """Calcula disponibilidad basada en múltiples factores"""
        disponibilidad = 85  # Base
        
        # Ajustar por nivel de apoyo
        if perfil["nivel_apoyo"] == "bajo":
            disponibilidad += 10
        elif perfil["nivel_apoyo"] == "alto":
            disponibilidad -= 15
        
        # Ajustar por tolerancia a frustración
        if perfil["tolerancia_frustracion"] == "alta":
            disponibilidad += 5
        elif perfil["tolerancia_frustracion"] == "baja":
            disponibilidad -= 10
        
        # Ajustar por temperamento
        if perfil["temperamento"] == "impulsivo":
            disponibilidad -= 5
        
        return max(60, min(100, disponibilidad))  # Entre 60-100
    
    def _generar_historial_roles(self, perfil: dict) -> List[str]:
        """Genera historial de roles basado en fortalezas y estilo de aprendizaje"""
        roles = []
        
        # Roles basados en estilo de aprendizaje
        if "visual" in perfil["estilo_aprendizaje"]:
            roles.append("diseñador_visual")
        if "auditivo" in perfil["estilo_aprendizaje"]:
            roles.append("comunicador")
        if "kinestésico" in perfil["estilo_aprendizaje"]:
            roles.append("experimentador")
        
        # Roles basados en intereses
        if "ciencias" in perfil["intereses"]:
            roles.append("investigador_científico")
        if "experimentos" in perfil["intereses"]:
            roles.append("experimentador")
        if "trabajo_colaborativo" in perfil["intereses"]:
            roles.append("facilitador_grupal")
        if "lectura" in perfil["intereses"]:
            roles.append("analista_información")
        
        # Roles específicos por diagnóstico
        diagnostico = perfil.get("diagnostico_formal", "ninguno")
        if "altas_capacidades" in diagnostico:
            roles.append("mentor_académico")
        
        return roles  # Devolver todos los roles identificados
    
    def _obtener_diagnostico_legible(self, diagnostico_formal: str) -> str:
        """Convierte el diagnóstico formal en texto legible"""
        if diagnostico_formal == "TEA_nivel_1":
            return "TEA nivel 1"
        elif diagnostico_formal == "TDAH_combinado":
            return "TDAH combinado"
        elif diagnostico_formal == "altas_capacidades":
            return "Altas capacidades"
        elif diagnostico_formal == "ninguno":
            return "Desarrollo típico"
        else:
            return diagnostico_formal
    
    def analizar_perfiles(self, tareas: List[Tarea]) -> Dict[str, Dict]:
        """Analiza perfiles de estudiantes en relación a las tareas"""
        
        # Crear un prompt con información de estudiantes y tareas
        info_estudiantes = "\n".join([
            f"- {e.id}: {e.nombre} - Fortalezas: {', '.join(e.fortalezas)} - Necesidades: {', '.join(e.necesidades_apoyo)}"
            for e in self.perfiles_base
        ])
        
        info_tareas = "\n".join([
            f"- {t.id}: {t.descripcion} - Competencias: {', '.join(t.competencias_requeridas)} - Tipo: {t.tipo}"
            for t in tareas
        ])
        
        prompt_analisis = f"""
Analiza estos estudiantes y tareas para identificar compatibilidades:

ESTUDIANTES:
{info_estudiantes}

TAREAS:
{info_tareas}

Para cada estudiante, identifica:
1. Qué tareas se adaptan mejor a sus fortalezas
2. Qué tareas podrían ayudarle a desarrollar nuevas competencias
3. Qué adaptaciones específicas necesita
4. Qué rol sería más apropiado en el proyecto

Formato:
ESTUDIANTE [ID]:
Tareas_compatibles: [lista de IDs de tareas]
Tareas_desarrollo: [tareas para crecer]
Adaptaciones: [adaptaciones específicas]

[Repetir para todos los estudiantes...]
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_analisis, max_tokens=900)
        return self._parsear_analisis(respuesta)
    
    def _parsear_analisis(self, respuesta: str) -> Dict[str, Dict]:
        """Parsea el análisis de compatibilidades"""
        analisis = {}
        partes = respuesta.split("ESTUDIANTE ")
        
        for parte in partes[1:]:
            if not parte.strip():
                continue
                
            # Extraer ID del estudiante
            lines = parte.split('\n')
            estudiante_id = lines[0].replace(':', '').strip()
            
            analisis[estudiante_id] = {
                "tareas_compatibles": self._extraer_lista_ids(parte, "Tareas_compatibles:"),
                "tareas_desarrollo": self._extraer_lista_ids(parte, "Tareas_desarrollo:"),
                "adaptaciones": self._extraer_lista(parte, "Adaptaciones:"),
                "rol_sugerido": self._extraer_campo(parte, "Rol_sugerido:")
            }
        
        return analisis
    
    def _extraer_lista_ids(self, texto: str, campo: str) -> List[str]:
        """Extrae lista de IDs de tareas usando método heredado"""
        valor = self._extraer_campo(texto, campo, "")
        if valor and valor != "No especificado":
            # Buscar patrones como tarea_01, tarea_02, etc.
            ids = re.findall(r'tarea_\d+', valor)
            return ids
        return []
    
    # Implementación de métodos abstractos de BaseAgent
    def process(self, *args, **kwargs) -> Dict:
        """Implementa el método abstracto process de BaseAgent"""
        return self.analizar_perfiles(*args, **kwargs)
    
    def _parse_response(self, response: str) -> Dict:
        """Parsea respuesta del LLM para análisis de estudiantes"""
        return self._parsear_analisis_estudiantes(response)

class AgenteOptimizadorAsignaciones(BaseAgent):
    """Agente Optimizador de Asignaciones (Assignment Optimizer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        super().__init__(ollama_integrator)
        self.perfiles = {}  # Se actualizará cuando reciba los perfiles

    def optimizar_asignaciones(self, tareas: List[Tarea], analisis_estudiantes: Dict, perfilador=None) -> Dict:
        """Optimiza las asignaciones de tareas basándose en el análisis de perfiles."""
        
        # Actualizar perfiles si se proporciona perfilador
        if perfilador and hasattr(perfilador, 'perfiles_base'):
            self.perfiles = {e.id: e for e in perfilador.perfiles_base}
            self.logger.info(f"📋 Perfiles actualizados: {len(self.perfiles)} estudiantes")
        
        # Convertir la lista de objetos Tarea a una lista de diccionarios para que sea serializable
        tareas_dict_list = [asdict(tarea) for tarea in tareas] 
        
        # Prepara el prompt para el LLM con instrucciones más claras
        prompt_optimizacion = f"""
Eres un experto en asignación de tareas educativas del AULA_A_4PRIM.

TAREAS DISPONIBLES:
{json.dumps(tareas_dict_list, indent=2, ensure_ascii=False)}

ANÁLISIS DE ESTUDIANTES:
{json.dumps(analisis_estudiantes, indent=2, ensure_ascii=False)}

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
        
        try:
            # Llamada al LLM y parseo robusto
            respuesta_llm = self.ollama.generar_respuesta(prompt_optimizacion, max_tokens=500)
            asignaciones_dict = parse_json_seguro(respuesta_llm)
            
            if asignaciones_dict:
                self.logger.info(f"✅ Asignaciones parseadas correctamente.")
                return asignaciones_dict.get('asignaciones', {})
            else:
                raise ValueError("No se pudo parsear JSON de asignaciones")
        
        except Exception as e:
            self.logger.error(f"❌ Error al parsear asignaciones del LLM: {e}")
            self.logger.info("⚠️ Usando lógica de fallback para las asignaciones.")
            # Lógica de fallback simple: distribuir tareas de manera equitativa
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
            
            self.logger.info(f"✅ Asignaciones fallback creadas para {len(asignaciones_fallback)} estudiantes usando perfiles reales.")
            return asignaciones_fallback
        

    def _parsear_asignaciones(self, respuesta: str, tareas: List[Tarea]) -> List[Dict]:
        """
        Parsea la respuesta del LLM. Intenta leer JSON primero y luego usa fallback.
        """
        try:
            # Intento de parseo de JSON
            json_str = respuesta.strip().replace("[SIMULADO JSON]\n", "")
            asignaciones_dict = json.loads(json_str)
            
            asignaciones_list = []
            for estudiante_id, data in asignaciones_dict.items():
                asignaciones_list.append({
                    "estudiante_id": estudiante_id.replace("estudiante_", ""),
                    "tareas_asignadas": data.get("tareas", []),
                    "rol_principal": data.get("rol", "colaborador"),
                    "justificacion": data.get("justificacion", "No especificado")
                })
            
            return asignaciones_list

        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Error al parsear JSON del LLM: {e}")
            self.logger.info("⚠️ Usando lógica de fallback para el parseo.")
            
            # Lógica de fallback (simple distribución como en el script original, pero con más info)
            asignaciones = []
            estudiantes_ids = list(self.perfiles.keys())
            
            for i, estudiante_id in enumerate(estudiantes_ids):
                tareas_asignadas = [t.id for t in tareas if i == int(t.id.split('_')[1]) % len(estudiantes_ids)]
                
                asignaciones.append({
                    "estudiante_id": estudiante_id,
                    "tareas_asignadas": tareas_asignadas,
                    "rol_principal": "colaborador", # Fallback
                    "justificacion": "Distribución por defecto debido a error de formato del LLM."
                })
                
            return asignaciones
    
    # Implementación de métodos abstractos de BaseAgent
    def process(self, *args, **kwargs) -> Dict:
        """Implementa el método abstracto process de BaseAgent"""
        return self.optimizar_asignaciones(*args, **kwargs)
    
    def _parse_response(self, response: str) -> Dict:
        """Parsea respuesta del LLM para asignaciones"""
        return parse_json_seguro(response)
            
# AÑADIMOS LA CLASE QUE FALTABA
class AgenteGeneradorRecursos(BaseAgent):
    """Agente Generador de Recursos (Resource Generator Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        super().__init__(ollama_integrator)
    
    def generar_recursos(self, proyecto_base: dict, tareas: list, asignaciones: dict) -> dict:
        """
        Genera una lista de recursos materiales, analógicos y digitales
        para el proyecto, en formato JSON.
        """
        
        # Prompt mejorado para recursos con contexto específico
        prompt_recursos = f"""
Eres un experto en recursos educativos para 4º de Primaria.

PROYECTO: {proyecto_base.get('titulo', 'Actividad educativa')}
DESCRIPCIÓN: {proyecto_base.get('descripcion', 'No disponible')}

TAREAS DEL PROYECTO:
{json.dumps([asdict(t) for t in tareas], indent=2, ensure_ascii=False)}

ESTUDIANTES ESPECIALES A CONSIDERAR:
- Elena (TEA): Necesita materiales estructurados y predecibles
- Luis (TDAH): Materiales que permitan movimiento y manipulación
- Ana (Altas capacidades): Recursos adicionales para profundizar

RESPONDE ÚNICAMENTE CON ESTE JSON (sin texto adicional):
{{
  "recursos_materiales": [
    "Recurso físico 1",
    "Recurso físico 2",
    "Recurso físico 3"
  ],
  "recursos_analogicos": [
    "Herramienta manipulativa 1",
    "Herramienta manipulativa 2"
  ],
  "recursos_digitales": [
    "Recurso digital 1",
    "Recurso digital 2"
  ]
}}"""
        
        try:
            # Llamada al LLM y parseo robusto
            respuesta_llm = self.ollama.generar_respuesta(prompt_recursos, max_tokens=500)
            recursos_dict = parse_json_seguro(respuesta_llm)
            
            if recursos_dict:
                self.logger.info(f"✅ Recursos parseados correctamente.")
                return recursos_dict
            else:
                raise ValueError("No se pudo parsear JSON de recursos")
                
        except Exception as e:
            self.logger.error(f"❌ Error al parsear recursos del LLM: {e}")
            self.logger.info("⚠️ Usando lógica de fallback para los recursos.")
            # Lógica de fallback expandida (materiales base + contextuales)
            return {
                "recursos_materiales": [
                    # Materiales educativos básicos
                    "Papel", "Lápices", "Marcadores", "Pintura", "Tijeras", "Pegamento",
                    "Cartulinas", "Rotuladores", "Reglas", "Gomas de borrar",
                    # Materiales específicos del contexto (si aplica)
                    "Guías de viaje", "Mapas físicos", "Atlas", "Material manipulativo"
                ],
                "recursos_analogicos": [
                    # Recursos manipulativos básicos
                    "Regletas de Cuisenaire", "Bloques lógicos", "Material de construcción",
                    "Juegos de mesa educativos", "Puzzles", "Dados",
                    # Recursos específicos del contexto (si aplica)
                    "Brújula", "Herramientas de medición", "Material de orientación"
                ],
                "recursos_digitales": [
                    # Herramientas digitales básicas
                    "Editor de texto", "Buscador de imágenes", "Calculadora", 
                    "Herramientas de presentación", "Apps educativas",
                    # Recursos específicos del contexto (si aplica)
                    "Recursos web temáticos", "Mapas digitales"
                ]
            }
        
    def _parsear_recursos(self, respuesta: str) -> Dict[str, List[str]]:
        """Parsea una respuesta en formato JSON para crear el diccionario de recursos."""
        
        try:
            # Intenta parsear directamente como JSON si es posible
            recursos = json.loads(respuesta)
            # Verifica que las claves esperadas existan y sean listas
            if not all(k in recursos and isinstance(recursos[k], list) for k in ["recursos_materiales", "recursos_analogicos", "recursos_digitales"]):
                raise ValueError("El JSON no tiene el formato esperado.")
            
            return recursos
        
        except json.JSONDecodeError as e:
            # En caso de que el LLM no devuelva un JSON perfecto, usamos regex como fallback
            print(f"⚠️ Error al parsear JSON. Usando lógica de fallback (regex). Error: {e}")
            
            recursos = {
                "recursos_materiales": [],
                "recursos_analogicos": [],
                "recursos_digitales": []
            }
            
            # Regex para recursos materiales
            materiales_match = re.search(r'"recursos_materiales":\s*\[([^]]*)\]', respuesta, re.DOTALL)
            if materiales_match:
                try:
                    # Usa json.loads para parsear la lista de forma segura
                    recursos['recursos_materiales'] = json.loads(f'[{materiales_match.group(1)}]')
                except json.JSONDecodeError:
                    # Si falla, se hace un parseo simple por comas
                    recursos['recursos_materiales'] = [item.strip().strip('"') for item in materiales_match.group(1).split(",") if item.strip()]

            # Regex para recursos analógicos
            analogicos_match = re.search(r'"recursos_analogicos":\s*\[([^]]*)\]', respuesta, re.DOTALL)
            if analogicos_match:
                try:
                    recursos['recursos_analogicos'] = json.loads(f'[{analogicos_match.group(1)}]')
                except json.JSONDecodeError:
                    recursos['recursos_analogicos'] = [item.strip().strip('"') for item in analogicos_match.group(1).split(",") if item.strip()]

            # Regex para recursos digitales
            digitales_match = re.search(r'"recursos_digitales":\s*\[([^]]*)\]', respuesta, re.DOTALL)
            if digitales_match:
                try:
                    recursos['recursos_digitales'] = json.loads(f'[{digitales_match.group(1)}]')
                except json.JSONDecodeError:
                    recursos['recursos_digitales'] = [item.strip().strip('"') for item in digitales_match.group(1).split(",") if item.strip()]

            return recursos
    
    # Implementación de métodos abstractos de BaseAgent
    def process(self, *args, **kwargs) -> Dict:
        """Implementa el método abstracto process de BaseAgent"""
        return self.generar_recursos(*args, **kwargs)
    
    def _parse_response(self, response: str) -> Dict:
        """Parsea respuesta del LLM para recursos"""
        return parse_json_seguro(response)

# ===== SISTEMA PRINCIPAL =====

class SistemaAgentesABP:
    """Sistema de Agentes para Aprendizaje Basado en Proyectos (ABP) con Contexto Híbrido"""
    def __init__(self):
        # Inicializar coordinador (ahora se auto-inicializa)
        self.coordinador = AgenteCoordinador()
        
        # Estado del sistema
        self.proyecto_actual = None
        self.validado = False
        
        logger.info("🚀 Sistema de Agentes ABP inicializado con coordinador mejorado")
        
    def ejecutar_flujo_completo(self) -> Dict:
        """Ejecuta el flujo completo del sistema - VERSION SIMPLIFICADA"""
        
        print("🎓 SISTEMA DE AGENTES PARA ABP - ESTRUCTURA SENCILLA")
        print("=" * 60)
        
        # UI: Obtener prompt inicial del profesor
        prompt_profesor = input("\n📝 Ingrese su prompt de actividad educativa: ")
        
        print("\n📋 Procesando con coordinador centralizado...")
        
        # COORDINACIÓN: Delegar todo el flujo al coordinador
        proyecto_final = self.coordinador.ejecutar_flujo_completo_con_ui(prompt_profesor)
        
        # Guardar el proyecto actual para persistencia
        self.proyecto_actual = proyecto_final
        
        # UI: Mostrar resultados finales
        self._mostrar_resumen_proceso(proyecto_final)
        self._ejecutar_validacion_mejorada(proyecto_final)
        
        return proyecto_final
        
        ideas = info_inicial['ideas_generadas']
        
        print("\n💡 IDEAS GENERADAS:")
        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
            print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
            print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
            print(f"   Duración: {idea.get('duracion', 'No especificada')}")
        
        # PASO 3: Selección de actividad con opciones adicionales
        actividad_seleccionada = None  # Inicializamos la variable fuera del bucle
        
        while True:
            try:
                print(f"\n🎯 Opciones disponibles:")
                print(f"   1-{len(ideas)}: Seleccionar una de las ideas y continuar")
                print(f"   M: Me gusta alguna idea pero quiero matizarla/perfilarla")
                print(f"   0: Generar nuevas ideas con un prompt diferente")
                
                # La opción -1 solo se muestra si ya hay una actividad seleccionada
                if actividad_seleccionada:
                    print(f"   -1: Añadir más detalles a la idea '{actividad_seleccionada.get('titulo', 'Sin título')}'")
                
                seleccion_input = input(f"\n🎯 Su elección: ").strip().upper()
                
                # Convertir a número si es posible, o mantener como string para M
                try:
                    seleccion = int(seleccion_input)
                except ValueError:
                    seleccion = seleccion_input
                
                if seleccion == "M":
                    # Opción para matizar/perfilar ideas existentes
                    print("\n🔧 MATIZAR/PERFILAR IDEAS")
                    print("¿Cuál de las ideas te parece más interesante para perfilar?")
                    
                    try:
                        idea_a_perfilar = int(input(f"Selecciona el número (1-{len(ideas)}): "))
                        if 1 <= idea_a_perfilar <= len(ideas):
                            idea_seleccionada = ideas[idea_a_perfilar - 1]
                            print(f"\n✏️ Has seleccionado: {idea_seleccionada.get('titulo', 'Sin título')}")
                            
                            # Solicitar matizaciones específicas
                            matizaciones = input("\n📝 ¿Qué aspectos te gustaría matizar/cambiar de esta idea?: ")
                            
                            # En el contexto híbrido, las ideas rechazadas se manejan automáticamente
                            logger.info(f"📋 Usuario seleccionó idea {idea_a_perfilar} para matizar")
                            
                            # Crear prompt para matizar la idea seleccionada
                            prompt_matizacion = f"Toma esta idea: '{idea_seleccionada.get('titulo', '')}' - {idea_seleccionada.get('descripcion', '')} y aplica estos cambios/matizaciones: {matizaciones}"
                            
                            print("\n🧠 Generando versiones matizadas...")
                            ideas = self.coordinador.generar_ideas_actividades_hibrido(prompt_matizacion, self.contexto_hibrido)
                            
                            print("\n💡 IDEAS MATIZADAS GENERADAS:")
                            for i, idea in enumerate(ideas, 1):
                                print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
                                print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
                                print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
                                print(f"   Duración: {idea.get('duracion', 'No especificada')}")
                            
                            # Reiniciar selección con nuevas ideas matizadas
                            actividad_seleccionada = None
                            continue
                        else:
                            print(f"❌ Selección inválida. Elige entre 1 y {len(ideas)}")
                            continue
                    except ValueError:
                        print("❌ Ingrese un número válido")
                        continue
                
                elif seleccion == 0:
                    # En el contexto híbrido, las ideas rechazadas se procesan automáticamente
                    logger.info("📋 Usuario solicitó nuevas ideas, context híbrido se actualizará")
                    
                    # Generar nuevas ideas usando contexto híbrido actualizado
                    nuevo_prompt = input("\n📝 Ingrese un nuevo prompt para generar diferentes ideas: ")
                    print("\n🧠 Generando nuevas ideas...")
                    ideas = self.coordinador.generar_ideas_actividades_hibrido(nuevo_prompt, self.contexto_hibrido)
                    
                    print("\n💡 NUEVAS IDEAS GENERADAS:")
                    for i, idea in enumerate(ideas, 1):
                        print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
                        print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
                        print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
                        print(f"   Duración: {idea.get('duracion', 'No especificada')}")
                    # Reiniciamos la selección
                    actividad_seleccionada = None
                    continue
                
                elif seleccion == -1 and actividad_seleccionada:
                    # Lógica para añadir detalles, solo si ya hay una actividad seleccionada
                    detalle_extra = input(f"\n📝 ¿Desea añadir detalles específicos sobre '{actividad_seleccionada.get('titulo', 'la actividad')}'? (Enter para continuar, o escriba detalles): ")
                    
                    if detalle_extra.strip():
                        self.coordinador.historial_prompts.append({
                            "tipo": "detalles_actividad_seleccionada",
                            "actividad_id": actividad_seleccionada.get('id'),
                            "actividad_titulo": actividad_seleccionada.get('titulo'),
                            "detalles_adicionales": detalle_extra,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"✅ Detalles adicionales registrados para la actividad")
                    
                    # Salimos del bucle para continuar con el flujo principal
                    break
                        
                elif 1 <= seleccion <= len(ideas):
                    # Seleccionamos una actividad y la guardamos
                    actividad_seleccionada = ideas[seleccion - 1]
                    print(f"✅ Ha seleccionado la actividad: {actividad_seleccionada.get('titulo', 'Sin título')}")
                    
                    # Preguntar si quiere añadir detalles después de la selección
                    detalle_extra = input(f"\n📝 ¿Desea añadir detalles específicos sobre '{actividad_seleccionada.get('titulo', 'la actividad')}' antes de continuar? (Enter para continuar, o escriba detalles): ")
                    
                    if detalle_extra.strip():
                        self.coordinador.historial_prompts.append({
                            "tipo": "detalles_actividad_seleccionada",
                            "actividad_id": actividad_seleccionada.get('id'),
                            "actividad_titulo": actividad_seleccionada.get('titulo'),
                            "detalles_adicionales": detalle_extra,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"✅ Detalles adicionales registrados para la actividad")
                    
                    break
                    
                else:
                    print(f"❌ Selección inválida. Opciones disponibles:")
                    print(f"   • Números 1-{len(ideas)}: Seleccionar idea")
                    print(f"   • M: Matizar/perfilar una idea")
                    print(f"   • 0: Generar nuevas ideas")
                    if actividad_seleccionada:
                        print(f"   • -1: Añadir detalles")
                    
            except ValueError:
                print("❌ Entrada inválida. Use números (1-{}, 0) o 'M' para matizar".format(len(ideas)))
        
        # PASO 4: Información adicional (opcional)
        info_adicional = input("\n📋 ¿Información adicional específica? (Enter para continuar): ")
        
        # PASO 5: Ejecutar flujo orquestado completo
        print(f"\n🚀 Ejecutando flujo orquestado para: {actividad_seleccionada.get('titulo', 'Sin título')}...")
        proyecto_final = self.coordinador.ejecutar_flujo_orquestado(actividad_seleccionada, info_adicional)
        
        # Mostrar resumen del proceso
        self._mostrar_resumen_proceso(proyecto_final)
        
        # Validación mejorada
        self._ejecutar_validacion_mejorada(proyecto_final)
        
        return proyecto_final
    
    def _mostrar_resumen_proceso(self, proyecto_final: dict):
        """Muestra un resumen detallado del proceso ejecutado"""
        validacion = proyecto_final.get('validacion', {})
        if not isinstance(validacion, dict):
            validacion = {}
            
        estadisticas = validacion.get('estadisticas', {})
        if not isinstance(estadisticas, dict):
            estadisticas = {}
            
        print(f"\n📏 RESUMEN DEL PROCESO:")
        print(f"   • Agentes ejecutados: {estadisticas.get('total_agentes_ejecutados', 'N/A')}")
        print(f"   • Mensajes intercambiados: {estadisticas.get('total_mensajes', 'N/A')}")
        print(f"   • Errores encontrados: {estadisticas.get('errores_encontrados', 'N/A')}")
        
        coherencia = validacion.get('coherencia_final', {})
        if not isinstance(coherencia, dict):
            coherencia = {}
            
        if coherencia.get('sugerencias'):
            print(f"\n💡 SUGERENCIAS:")
            for sugerencia in coherencia['sugerencias']:
                print(f"   • {sugerencia}")
        
        if coherencia.get('problemas'):
            print(f"\n⚠️ PROBLEMAS DETECTADOS:")
            for problema in coherencia['problemas']:
                print(f"   • {problema}")
                
    def _ejecutar_validacion_mejorada(self, proyecto_final: dict):
        """Ejecuta validación mejorada con información detallada"""
        print("\n🔍 VALIDACIÓN FINAL:")
        
        proyecto_base = proyecto_final.get('proyecto_base', {})
        if not isinstance(proyecto_base, dict):
            proyecto_base = {}
            
        resultados = proyecto_final.get('resultados_agentes', {})
        if not isinstance(resultados, dict):
            resultados = {}
        
        print(f"Título: {proyecto_base.get('titulo', 'N/A')}")
        print(f"Descripción: {proyecto_base.get('descripcion', 'N/A')}")
        
        # Acceso seguro a resultados anidados
        tareas_info = resultados.get('tareas', {})
        tareas_list = tareas_info.get('tareas', []) if isinstance(tareas_info, dict) else []
        print(f"Tareas generadas: {len(tareas_list)}")
        
        perfiles_info = resultados.get('perfiles', {})
        perfiles_list = perfiles_info.get('perfiles', []) if isinstance(perfiles_info, dict) else []
        print(f"Estudiantes analizados: {len(perfiles_list)}")
        
        asignaciones_info = resultados.get('asignaciones', {})
        asignaciones_list = asignaciones_info.get('asignaciones', []) if isinstance(asignaciones_info, dict) else []
        print(f"Asignaciones creadas: {len(asignaciones_list)}")
        
        recursos_info = resultados.get('recursos', {})
        recursos_list = recursos_info.get('recursos', []) if isinstance(recursos_info, dict) else []
        print(f"Recursos generados: {len(recursos_list)}")
        
        # Validación manual con información mejorada
        estado_global = proyecto_final.get('estado_global', {})
        if not isinstance(estado_global, dict):
            estado_global = {}
            
        estado_final = estado_global.get('estado_final', 'desconocido')
        
        if estado_final == "completado":
            validacion_manual = input("\n✅ ¿Aprueba el proyecto generado? (s/n): ").lower().startswith('s')
            
            if validacion_manual:
                print("✅ Proyecto aprobado y completado exitosamente")
                self.validado = True
            else:
                print("❌ Proyecto rechazado - Puede ejecutar nuevamente para mejoras")
                self.validado = False
        else:
            print(f"⚠️ Proyecto completado con estado: {estado_final}")
            self.validado = False

    def _crear_proyecto_final(self, proyecto_base: Dict, tareas: List[Tarea], 
                            asignaciones: Dict, recursos: Dict) -> Dict:
        """Crea la estructura final del proyecto"""
        
        # Organizar tareas por fases
        fases = self._organizar_fases(tareas)
        
        # Crear diccionario completo de tareas con toda la información
        tareas_detalladas = {}
        for tarea in tareas:
            tareas_detalladas[tarea.id] = {
                "id": tarea.id,
                "descripcion": tarea.descripcion,
                "competencias_requeridas": tarea.competencias_requeridas,
                "complejidad": tarea.complejidad,
                "tipo": tarea.tipo,
                "dependencias": tarea.dependencias,
                "tiempo_estimado": tarea.tiempo_estimado
            }
        
        # Crear estructura final
        proyecto_final = {
            "proyecto": {
                "titulo": proyecto_base["titulo"],
                "descripcion": proyecto_base["descripcion"],
                "duracion": proyecto_base["duracion_base"],
                "competencias_objetivo": proyecto_base["competencias_base"],
                # Corrección: Acceder a la clave 'recursos_materiales' de manera segura
                "recursos_materiales": len(recursos.get('recursos_materiales', [])) if recursos and isinstance(recursos, dict) else 0
            },
            "tareas": tareas_detalladas,  # ✅ AÑADIR TAREAS COMPLETAS
            "fases": fases,
            # Corrección: Las asignaciones ya vienen como un dict, no una lista
            "asignaciones": asignaciones,
            "recursos": recursos,
            "evaluacion": {
                "criterios": ["Calidad del trabajo", "Colaboración", "Creatividad", "Competencias específicas"],
                "instrumentos": ["Rúbrica", "Autoevaluación", "Evaluación por pares", "Portfolio digital"]
            },
            "metadatos": {
                "timestamp": datetime.now().isoformat(),
                "sistema": "AgentesABP_v2.0_ContextoAcumulativo",
                "historial_prompts": self.coordinador.historial_prompts,
                "contexto_hibrido": self.contexto_hibrido.get_resumen_sesion(),
                "validado": self.validado
            }
        }
        
        self.proyecto_actual = proyecto_final
        return proyecto_final
    
    def _organizar_fases(self, tareas: List[Tarea]) -> List[Dict]:
        """Organiza las tareas en fases del proyecto"""
        fases = [
            {
                "nombre": "Fase 1: Investigación y Planificación",
                "duracion": "3-4 días",
                # Corrección: Acceder a t.id
                "tareas": [t.id for t in tareas if "investigar" in t.descripcion.lower() or "planificar" in t.descripcion.lower()]
            },
            {
                "nombre": "Fase 2: Desarrollo y Creación",
                "duracion": "5-6 días", 
                # Corrección: Acceder a t.tipo
                "tareas": [t.id for t in tareas if t.tipo in ["colaborativa", "creativa"]]
            },
            {
                "nombre": "Fase 3: Presentación y Evaluación",
                "duracion": "2-3 días",
                # Corrección: Acceder a t.id
                "tareas": [t.id for t in tareas if "presentar" in t.descripcion.lower() or "evaluar" in t.descripcion.lower()]
            }
        ]
        
        # Asegurar que todas las tareas estén asignadas a alguna fase
        tareas_asignadas = set()
        for fase in fases:
            tareas_asignadas.update(fase["tareas"])
        
        # Asignar tareas restantes a la fase de desarrollo
        for tarea in tareas:
            if tarea.id not in tareas_asignadas:
                fases[1]["tareas"].append(tarea.id)
        
        return fases
    
    def _ejecutar_validacion(self, proyecto: Dict) -> bool:
        """Ejecuta el proceso de validación con posible iteración"""
        
        print("\n✅ VALIDACIÓN DEL PROYECTO")
        print("-" * 40)
        
        # Mostrar resumen del proyecto
        self._mostrar_resumen_proyecto(proyecto)
        
        while not self.validado:
            validacion = input("\n🔍 ¿Valida el proyecto? (s/n): ").lower().strip()
            
            if validacion == 's':
                self.validado = True
                proyecto["metadatos"]["validado"] = True
                print("✅ Proyecto validado correctamente")
                
                # Guardar proyecto
                self._guardar_proyecto(proyecto)
                break
                
            elif validacion == 'n':
                print("\n🔄 Proceso de iteración iniciado")
                cambios_solicitados = input("📝 ¿Qué cambios específicos desea realizar?: ")
                
                # Guardar feedback para iteración
                self.coordinador.historial_prompts.append({
                    "tipo": "feedback_iteracion",
                    "contenido": cambios_solicitados,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Aquí se implementaría la lógica de iteración
                print("🔄 Aplicando cambios solicitados...")
                # Por simplicidad, se muestra el mensaje y se vuelve a validar
                
            else:
                print("❌ Respuesta inválida. Use 's' para sí o 'n' para no")
        
        return self.validado
    
    def _mostrar_resumen_proyecto(self, proyecto: Dict):
        """Muestra un resumen del proyecto para validación"""
        print(f"\n📋 RESUMEN DEL PROYECTO:")
        print(f"   Título: {proyecto['proyecto']['titulo']}")
        print(f"   Duración: {proyecto['proyecto']['duracion']}")
        competencias_texto = ', '.join(proyecto['proyecto']['competencias_objetivo'])
        if len(competencias_texto) > 100:
            competencias_texto = competencias_texto[:100] + "..."
        print(f"   Competencias: {competencias_texto}")
        print(f"   Número de fases: {len(proyecto['fases'])}")
        print(f"   Estudiantes asignados: {len(proyecto['asignaciones'])}")
        print(f"   Recursos materiales: {len(proyecto['recursos'].get('materiales_fisicos', []))}")
    
    def _guardar_proyecto(self, proyecto: Dict):
        """Guarda el proyecto en un archivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"../../temp/sencillo_abp_{timestamp}.json"
        
        try:
            # Crear directorio temp si no existe
            temp_dir = os.path.dirname(nombre_archivo)
            os.makedirs(temp_dir, exist_ok=True)
            
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                json.dump(proyecto, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Proyecto guardado en: {nombre_archivo}")
            print(f"💾 Proyecto guardado en: {nombre_archivo}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando proyecto: {e}")
            print(f"❌ Error guardando proyecto: {e}")

# ===== FUNCIÓN PRINCIPAL =====

def main():
    """Función principal del sistema"""
    try:
        # Inicializar sistema (el coordinador maneja la configuración de Ollama)
        sistema = SistemaAgentesABP()
        
        # Ejecutar flujo completo
        proyecto = sistema.ejecutar_flujo_completo()
        
        print("\n🎉 PROCESO COMPLETADO")
        print("=" * 40)
        
        if sistema.validado:
            print("✅ Proyecto validado y guardado exitosamente")
        else:
            print("⚠️ Proyecto creado pero no validado")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en el sistema: {e}")
        print(f"❌ Error en el sistema: {e}")

if __name__ == "__main__":
    main()