#!/usr/bin/env python3
"""
Sistema de Agentes para ABP (Aprendizaje Basado en Proyectos) - Estructura Sencilla
Arquitectura modular con 5 agentes especializados y validación iterativa
"""

import json
import os
import re
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
        if texto_limpio.startswith("A continuación") or texto_limpio.startswith("Aquí"):
            # El LLM respondió en texto plano, extraer JSON si existe
            import re
            json_match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
            if json_match:
                texto_limpio = json_match.group()
            else:
                logger.warning("No se encontró JSON en la respuesta de texto plano")
                return None
                
        if not texto_limpio:
            raise ValueError("Respuesta vacía")
            
        # Estrategia 2: Buscar el primer { hasta el último }
        start_idx = texto_limpio.find('{')
        end_idx = texto_limpio.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            texto_limpio = texto_limpio[start_idx:end_idx+1]
            
        return json.loads(texto_limpio)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON del LLM: {e}")
        logger.error(f"🔍 Texto recibido (primeros 200 chars): {texto[:200]}...")
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
        temas_especificos = ['fracciones', 'multiplicación', 'división', 'geometría', 'ortografía', 'lectura', 'escritura']
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
            'proyecto colaborativo': ['proyecto', 'colaborar', 'equipo', 'grupo']
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
    
    def extraer_informacion_prompt_legacy(self, prompt: str) -> Dict:
        """MÉTODO OBSOLETO - Solo para compatibilidad hacia atrás"""
        # Este método se mantiene por compatibilidad pero ya no se usa
        # La auto-detección se hace en autodetectar_metadatos()
        return {}
    
    def actualizar_contexto_legacy(self, prompt: str, accion: str) -> List[str]:
        """MÉTODO OBSOLETO - El contexto ahora se actualiza automáticamente"""
        # Este método ya no se usa - el contexto se actualiza en procesar_respuesta_llm()
        logger.warning("⚠️ Método obsoleto actualizar_contexto_legacy() llamado")
        return []
    
    def registrar_idea_rechazada_legacy(self, idea: Dict, razon: str = "No especificada"):
        """MÉTODO OBSOLETO - Las ideas rechazadas se manejan automáticamente en ContextoHibrido"""
        logger.info(f"❌ Idea rechazada (legacy): {idea.get('titulo', 'Sin título')} - {razon}")
    
    def obtener_contexto_completo_legacy(self) -> str:
        """MÉTODO OBSOLETO - El contexto se maneja ahora en ContextoHibrido"""
        return "Contexto legacy no disponible - usar ContextoHibrido"
        
        return descripcion
    
    def obtener_json_contexto_legacy(self) -> Dict:
        """MÉTODO OBSOLETO - Usar ContextoHibrido en su lugar"""
        return {}  # El contexto ahora está en ContextoHibrido

# ===== INTEGRACIÓN OLLAMA =====
# (Mantiene el mismo integrador de Ollama, no necesita cambios)
class OllamaIntegrator:
    """Integrador simplificado con Ollama API"""
    
    def __init__(self, host: str = "192.168.1.10", port: int = 11434, model: str = "llama3.2"):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        
        try:
            from ollama_api_integrator import OllamaAPIEducationGenerator
            self.ollama = OllamaAPIEducationGenerator(host=host, port=port, model_name=model)
            logger.info("✅ Ollama integrado correctamente")
        except ImportError:
            logger.error("❌ No se pudo importar OllamaAPIEducationGenerator, usando simulador")
            self.ollama = None
            
    def generar_respuesta(self, prompt: str, max_tokens: int = 500) -> str:
        """Genera respuesta usando Ollama"""
        if self.ollama:
            return self.ollama.generar_texto(prompt, max_tokens=max_tokens, temperature=0.7)
        else:
            # Simulador para desarrollo
            return f"""
            [SIMULADO JSON]
            {{
                "estudiante_001": {{
                    "tareas": ["tarea_01", "tarea_03"],
                    "rol": "coordinador",
                    "justificacion": "Basado en su fortaleza de liderazgo."
                }},
                "estudiante_002": {{
                    "tareas": ["tarea_02"],
                    "rol": "diseñador",
                    "justificacion": "Su creatividad visual es perfecta para esta tarea."
                }}
            }}
            """

# ===== AGENTES ESPECIALIZADOS (Refactorizados) =====

class AgenteCoordinador:
    """Agente Coordinador Principal (Master Agent) - CON CONTEXTO HÍBRIDO AUTO-DETECTADO"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.historial_prompts = []  # Mantener por compatibilidad
        self.ejemplos_k = self._cargar_ejemplos_k()
    
    def _cargar_ejemplos_k(self) -> Dict[str, str]:
        """Carga ejemplos k_ para few-shot learning"""
        ejemplos = {}
        # Rutas correctas para los archivos k_
        archivos_k = [
            "actividades_generadas/k_feria_acertijos.txt",
            "actividades_generadas/k_sonnet_supermercado.txt", 
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_piratas.txt",
            "actividades_generadas/k_sonnet7_fabrica_fracciones.txt"
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
    
    def generar_ideas_actividades(self, prompt_profesor: str) -> List[Dict]:
        """MÉTODO LEGACY - Usar generar_ideas_actividades_hibrido() en su lugar"""
        logger.warning("⚠️ Método legacy generar_ideas_actividades() llamado")
        # Fallback al método híbrido con contexto temporal
        contexto_temporal = ContextoHibrido()
        return self.generar_ideas_actividades_hibrido(prompt_profesor, contexto_temporal)
    
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
    
    def _crear_prompt_con_contexto_legacy(self) -> str:
        """MÉTODO LEGACY - Mantener por compatibilidad"""
        logger.warning("⚠️ Método legacy _crear_prompt_con_contexto() llamado")
        # Método original conservado pero no usado
        return "Prompt legacy no disponible"
        
        # Método legacy - conservado para compatibilidad
        if ejemplo_seleccionado:
            seccion_ejemplo = f"""
=== EJEMPLO DE ACTIVIDAD EXITOSA ===
{ejemplo_seleccionado}

=== PATRONES A SEGUIR ===
• NARRATIVA INMERSIVA: Contextualizar con historias atractivas
• OBJETIVOS CLAROS: Competencias específicas del tema + habilidades transversales
• ROL DOCENTE: Observación activa, guía discreta, gestión emocional
• ADAPTACIONES: Específicas para TEA, TDAH, altas capacidades
• MATERIALES CONCRETOS: Manipulativos, reales, accesibles"""
        else:
            seccion_ejemplo = f"""
=== PRINCIPIOS PEDAGÓGICOS ===
• CENTRADO EN EL ESTUDIANTE: Actividades que partan de sus intereses y necesidades
• APRENDIZAJE SIGNIFICATIVO: Conectar con experiencias reales y contextos auténticos
• INCLUSIÓN: Adaptaciones para TEA (Elena), TDAH (Luis), altas capacidades (Ana)
• COLABORACIÓN: Fomentar trabajo en equipo y comunicación
• CREATIVIDAD: Permitir múltiples formas de expresión y solución"""

        prompt_fewshot = f"""
Eres un experto en diseño de actividades educativas para 4º de Primaria. 

{contexto_completo}
{seccion_ejemplo}

=== INSTRUCCIONES ===
Basándote ÚNICAMENTE en el CONTEXTO ACUMULATIVO proporcionado, genera exactamente 3 ideas de actividades educativas diferentes que:

1. Sean coherentes con el tema y enfoque ya establecido
2. Eviten repetir las ideas rechazadas anteriormente
3. Incorporen las preferencias del profesor
4. Respeten las restricciones mencionadas
5. NO agregues elementos que no estén en el contexto del profesor

FORMATO EXACTO:
IDEA 1:
Título: [título contextualizado]
Descripción: [descripción que respete exactamente el contexto proporcionado]
Nivel: 4º Primaria
Competencias: [competencias relevantes al tema específico]
Duración: [tiempo realista según contexto]

IDEA 2:
[mismo formato...]

IDEA 3:
[mismo formato...]
"""
        return prompt_fewshot
    
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
    
    def _extraer_campo(self, texto: str, campo: str) -> str:
        """Extrae un campo específico del texto"""
        lines = texto.split('\n')
        for line in lines:
            if campo in line:
                return line.replace(campo, '').strip()
        return "No especificado"
    
    def _extraer_titulo_inteligente(self, texto: str) -> str:
        """Extrae título usando múltiples patrones"""
        # Patrones en orden de prioridad
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
                # Limpiar caracteres no deseados
                titulo = re.sub(r'^[\d\s.*:-]+', '', titulo).strip()
                if len(titulo) > 5:  # Título mínimo razonable
                    return titulo
        
        return "Actividad Educativa"
    
    def _extraer_descripcion_inteligente(self, texto: str) -> str:
        """Extrae descripción usando múltiples patrones"""
        # Buscar descripción explícita
        desc_match = re.search(r'Descripción:\s*([^\n]+(?:\n[^\n:]+)*)', texto, re.IGNORECASE)
        if desc_match:
            return desc_match.group(1).strip()
        
        # Buscar párrafos descriptivos (líneas largas sin ":")
        lines = texto.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 50 and ':' not in line and not line.startswith(('Nivel', 'Duración', 'Competencias')):
                return line
        
        return "Actividad práctica para desarrollar competencias matemáticas"
    
    def _extraer_nivel_inteligente(self, texto: str) -> str:
        """Extrae nivel educativo usando múltiples patrones"""
        # Buscar nivel explícito
        nivel_match = re.search(r'Nivel:\s*([^\n]+)', texto, re.IGNORECASE)
        if nivel_match:
            return nivel_match.group(1).strip()
        
        # Buscar palabras clave de nivel
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
        
        return "4º Primaria"  # Por defecto
    
    def _extraer_competencias_inteligente(self, texto: str) -> str:
        """Extrae competencias usando múltiples patrones"""
        # Buscar competencias explícitas
        comp_match = re.search(r'Competencias:\s*([^\n]+)', texto, re.IGNORECASE)
        if comp_match:
            return comp_match.group(1).strip()
        
        # Buscar palabras clave de competencias
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
        # Buscar duración explícita
        dur_match = re.search(r'Duración:\s*([^\n]+)', texto, re.IGNORECASE)
        if dur_match:
            return dur_match.group(1).strip()
        
        # Buscar patrones de tiempo
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
        
        return "2-3 sesiones"  # Por defecto
    
    def coordinar_proceso(self, actividad_seleccionada: Dict, info_adicional: str = "") -> Dict:
        """Coordina todo el proceso de creación del proyecto ABP"""
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
            "competencias_base": actividad_seleccionada.get("competencias", "").split(", "),
            "duracion_base": actividad_seleccionada.get("duracion", "2 semanas"),
            "info_adicional": info_adicional
        }
        
        return proyecto_base

class AgenteAnalizadorTareas:
    """Agente Analizador de Tareas (Task Analyzer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
    
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
    
    def _extraer_campo(self, texto: str, campo: str) -> str:
        """Extrae un campo específico del texto"""
        lines = texto.split('\n')
        for line in lines:
            if campo in line:
                return line.replace(campo, '').strip()
        return "No especificado"
    
    def _extraer_lista(self, texto: str, campo: str) -> List[str]:
        """Extrae una lista de elementos separados por comas"""
        valor = self._extraer_campo(texto, campo)
        if valor and valor != "No especificado":
            return [item.strip() for item in valor.split(",")]
        return []
    
    def _extraer_numero(self, texto: str, campo: str, default: int) -> int:
        """Extrae un número del texto"""
        valor = self._extraer_campo(texto, campo)
        try:
            return int(re.findall(r'\d+', valor)[0])
        except:
            return default

class AgentePerfiladorEstudiantes:
    """Agente Perfilador de Estudiantes - AULA_A_4PRIM"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.perfiles_base = self._cargar_perfiles_reales()
        logger.info(f"👥 Perfilador inicializado con {len(self.perfiles_base)} estudiantes del AULA_A_4PRIM")
    
    def _cargar_perfiles_reales(self) -> List[Estudiante]:
        """Carga los perfiles reales específicos del AULA_A_4PRIM desde el archivo JSON"""
        try:
            with open("perfiles_4_primaria.json", "r", encoding="utf-8") as f:
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
            logger.info(f"✅ AULA_A_4PRIM: Cargados {len(estudiantes)} perfiles reales:")
            for est in estudiantes:
                # Buscar el perfil original para obtener el diagnóstico
                perfil_original = next((p for p in data["estudiantes"] if p["id"] == est.id), {})
                diagnostico = self._obtener_diagnostico_legible(perfil_original.get("diagnostico_formal", "ninguno"))
                logger.info(f"   • {est.nombre} (ID: {est.id}) - {diagnostico}")
            
            return estudiantes
            
        except FileNotFoundError:
            logger.error("❌ CRÍTICO: No se encontró perfiles_4_primaria.json")
            logger.error("   El sistema requiere los perfiles reales de estudiantes")
            raise FileNotFoundError("Archivo perfiles_4_primaria.json requerido para el funcionamiento")
        except Exception as e:
            logger.error(f"❌ Error cargando perfiles reales: {e}")
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
                "adaptaciones": self._extraer_lista_simple(parte, "Adaptaciones:"),
                "rol_sugerido": self._extraer_campo_simple(parte, "Rol_sugerido:")
            }
        
        return analisis
    
    def _extraer_lista_ids(self, texto: str, campo: str) -> List[str]:
        """Extrae lista de IDs de tareas"""
        valor = self._extraer_campo_simple(texto, campo)
        if valor and valor != "No especificado":
            # Buscar patrones como tarea_01, tarea_02, etc.
            ids = re.findall(r'tarea_\d+', valor)
            return ids
        return []
    
    def _extraer_lista_simple(self, texto: str, campo: str) -> List[str]:
        """Extrae lista simple separada por comas"""
        valor = self._extraer_campo_simple(texto, campo)
        if valor and valor != "No especificado":
            return [item.strip() for item in valor.split(",")]
        return []
    
    def _extraer_campo_simple(self, texto: str, campo: str) -> str:
        """Extrae un campo específico del texto"""
        lines = texto.split('\n')
        for line in lines:
            if campo in line:
                return line.replace(campo, '').strip()
        return "No especificado"

class AgenteOptimizadorAsignaciones:
    """Agente Optimizador de Asignaciones (Assignment Optimizer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.perfiles = {}  # Se actualizará cuando reciba los perfiles

    def optimizar_asignaciones(self, tareas: List[Tarea], analisis_estudiantes: Dict, perfilador=None) -> Dict:
        """Optimiza las asignaciones de tareas basándose en el análisis de perfiles."""
        
        # Actualizar perfiles si se proporciona perfilador
        if perfilador and hasattr(perfilador, 'perfiles_base'):
            self.perfiles = {e.id: e for e in perfilador.perfiles_base}
            logger.info(f"📋 Perfiles actualizados: {len(self.perfiles)} estudiantes")
        
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
                logger.info(f"✅ Asignaciones parseadas correctamente.")
                return asignaciones_dict.get('asignaciones', {})
            else:
                raise ValueError("No se pudo parsear JSON de asignaciones")
        
        except Exception as e:
            logger.error(f"❌ Error al parsear asignaciones del LLM: {e}")
            logger.info("⚠️ Usando lógica de fallback para las asignaciones.")
            # Lógica de fallback simple: distribuir tareas de manera equitativa
            asignaciones_fallback = {}
            
            # Usar perfiles reales para asignación de fallback
            if not self.perfiles:
                logger.warning("No hay perfiles de estudiantes cargados. Devolviendo asignaciones vacías.")
                return {}
            
            estudiantes_ids = list(self.perfiles.keys())
            num_estudiantes = len(estudiantes_ids)
            
            if num_estudiantes == 0:
                logger.warning("No hay estudiantes disponibles para asignación.")
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
            
            logger.info(f"✅ Asignaciones fallback creadas para {len(asignaciones_fallback)} estudiantes usando perfiles reales.")
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
            logger.error(f"❌ Error al parsear JSON del LLM: {e}")
            logger.info("⚠️ Usando lógica de fallback para el parseo.")
            
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
            
# AÑADIMOS LA CLASE QUE FALTABA
class AgenteGeneradorRecursos:
    """Agente Generador de Recursos (Resource Generator Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
    
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
                logger.info(f"✅ Recursos parseados correctamente.")
                return recursos_dict
            else:
                raise ValueError("No se pudo parsear JSON de recursos")
                
        except Exception as e:
            logger.error(f"❌ Error al parsear recursos del LLM: {e}")
            logger.info("⚠️ Usando lógica de fallback para los recursos.")
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

# ===== SISTEMA PRINCIPAL =====

class SistemaAgentesABP:
    """Sistema de Agentes para Aprendizaje Basado en Proyectos (ABP) con Contexto Híbrido"""
    def __init__(self, host_ollama: str = "192.168.1.10", model: str = "llama3.2"):
        self.ollama = OllamaIntegrator(host=host_ollama, model=model)
        
        # CONTEXTO HÍBRIDO (reemplaza el contexto JSON rígido)
        self.contexto_hibrido = ContextoHibrido()
        
        # Inicializar agentes
        self.coordinador = AgenteCoordinador(self.ollama)
        self.analizador_tareas = AgenteAnalizadorTareas(self.ollama)
        self.perfilador = AgentePerfiladorEstudiantes(self.ollama)
        
        # El optimizador recibe referencia al perfilador
        self.optimizador = AgenteOptimizadorAsignaciones(self.ollama)
        self.generador_recursos = AgenteGeneradorRecursos(self.ollama)
        
        self.proyecto_actual = None
        self.validado = False
        
        logger.info("🚀 Sistema de Agentes ABP inicializado con contexto híbrido")
        
    def ejecutar_flujo_completo(self) -> Dict:
        """Ejecuta el flujo completo del sistema"""
        
        print("🎓 SISTEMA DE AGENTES PARA ABP - ESTRUCTURA SENCILLA")
        print("=" * 60)
        
        # PASO 1: Prompt inicial del profesor
        prompt_profesor = input("\n📝 Ingrese su prompt de actividad educativa: ")
        
        # PASO 2: Generar ideas de actividades con contexto híbrido
        print("\n🧠 Generando ideas de actividades...")
        ideas = self.coordinador.generar_ideas_actividades_hibrido(prompt_profesor, self.contexto_hibrido)
        
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
        
        # PASO 5: Coordinar proceso
        print("\n🎯 Coordinando proyecto...")
        proyecto_base = self.coordinador.coordinar_proceso(actividad_seleccionada, info_adicional)
        
        # PASO 6: Analizar tareas
        print("\n🔍 Analizando y descomponiendo tareas...")
        tareas = self.analizador_tareas.descomponer_actividad(proyecto_base)
        
        # PASO 7: Perfilar estudiantes
        print("\n👥 Analizando perfiles de estudiantes...")
        analisis_estudiantes = self.perfilador.analizar_perfiles(tareas)
        
        # PASO 8: Optimizando asignaciones
        print("\n⚖️ Optimizando asignaciones...")
        asignaciones = self.optimizador.optimizar_asignaciones(tareas, analisis_estudiantes, self.perfilador)
        
        # PASO 9: Generar recursos
        print("\n📚 Generando recursos necesarios...")
        recursos = self.generador_recursos.generar_recursos(proyecto_base, tareas, asignaciones)
        
        # PASO 10: Crear proyecto final
        proyecto_final = self._crear_proyecto_final(proyecto_base, tareas, asignaciones, recursos)
        
        # PASO 11: Validación
        self._ejecutar_validacion(proyecto_final)
        
        return proyecto_final
    
    def _crear_proyecto_final(self, proyecto_base: Dict, tareas: List[Tarea], 
                            asignaciones: Dict, recursos: Dict) -> Dict:
        """Crea la estructura final del proyecto"""
        
        # Organizar tareas por fases
        fases = self._organizar_fases(tareas)
        
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
        nombre_archivo = f"proyecto_abp_{timestamp}.json"
        
        try:
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
        # Inicializar sistema (configurar host de Ollama según tu setup)
        sistema = SistemaAgentesABP(host_ollama="192.168.1.10", model="llama3.2")
        
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