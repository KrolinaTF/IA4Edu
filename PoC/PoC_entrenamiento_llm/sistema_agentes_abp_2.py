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

# ===== CONTEXTO ACUMULATIVO =====

@dataclass
class IteracionPrompt:
    """Registro de una iteración de prompt"""
    numero: int
    prompt: str
    accion: str  # "INICIAR", "AMPLIAR", "REFINAR", "REEMPLAZAR"
    campos_modificados: List[str]
    timestamp: str

class ContextoActividad:
    """Gestiona el contexto acumulativo de la actividad"""
    
    def __init__(self):
        self.contexto = {
            "metadata_sesion": {
                "session_id": self._generar_session_id(),
                "timestamp_inicio": datetime.now().isoformat(),
                "prompts_realizados": 0,
                "estado_actual": "INICIO"
            },
            
            "contexto_actividad": {
                # INFORMACIÓN BÁSICA
                "tema_principal": None,
                "nivel_educativo": "4º Primaria",
                "duracion_estimada": None,
                
                # ESPECIFICACIONES PEDAGÓGICAS  
                "enfoque_metodologico": None,
                "competencias_objetivo": [],
                "materias_involucradas": [],
                
                # ESTRUCTURA DE LA ACTIVIDAD
                "estructura_actividad": {
                    "tipo_organizacion": None,
                    "fases_actividad": [],
                    "tareas_preliminares": [],
                    "roles_estudiantes": [],
                    "materiales_necesarios": []
                },
                
                # RESTRICCIONES Y PREFERENCIAS
                "restricciones": [],
                "preferencias_profesor": [],
                "ideas_rechazadas": [],
                
                # ADAPTACIONES
                "adaptaciones_necesarias": {
                    "TEA": False,
                    "TDAH": False, 
                    "altas_capacidades": False,
                    "especificas": []
                }
            },
            
            "historial_iteraciones": []
        }
        
        logger.info(f"🔄 Contexto acumulativo inicializado - Session: {self.contexto['metadata_sesion']['session_id']}")
    
    def _generar_session_id(self) -> str:
        """Genera un ID único para la sesión"""
        return f"abp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def analizar_continuidad_contexto(self, prompt_nuevo: str) -> str:
        """Analiza si el prompt continúa el tema o cambia completamente"""
        
        tema_actual = self.contexto["contexto_actividad"]["tema_principal"]
        enfoque_actual = self.contexto["contexto_actividad"]["enfoque_metodologico"]
        
        # Si no hay contexto previo, es el inicio
        if not tema_actual:
            return "INICIAR"
        
        prompt_lower = prompt_nuevo.lower()
        
        # Indicadores de cambio total de tema
        indicadores_cambio = [
            "quiero otra cosa", "cambiemos de tema", "mejor hagamos", 
            "prefiero algo diferente", "no, quiero", "mejor otra actividad"
        ]
        
        for indicador in indicadores_cambio:
            if indicador in prompt_lower:
                return "REEMPLAZAR"
        
        # Indicadores de refinamiento/ampliación
        indicadores_refinamiento = [
            "más", "también", "además", "pero que", "y que sea", 
            "añadir", "incluir", "que tenga", "con", "sin embargo"
        ]
        
        # Calcular similitud básica con tema actual
        palabras_tema = tema_actual.lower().split() if tema_actual else []
        palabras_prompt = prompt_lower.split()
        
        coincidencias = len(set(palabras_tema) & set(palabras_prompt))
        similitud = coincidencias / len(palabras_tema) if palabras_tema else 0
        
        # Lógica de decisión
        if any(indicador in prompt_lower for indicador in indicadores_refinamiento):
            return "AMPLIAR"
        elif similitud > 0.3:
            return "REFINAR"  
        else:
            return "REEMPLAZAR"
    
    def extraer_informacion_prompt(self, prompt: str) -> Dict:
        """Extrae información estructurada del prompt"""
        info = {
            "tema_principal": None,
            "enfoque_metodologico": None,
            "competencias": [],
            "restricciones": [],
            "preferencias": [],
            "nivel": None,
            "duracion": None
        }
        
        prompt_lower = prompt.lower()
        
        # Extraer tema principal
        temas_educativos = {
            "matemáticas": ["matemáticas", "mates", "números", "cálculo", "operaciones", "fracciones", "geometría"],
            "lengua": ["lengua", "lectura", "escritura", "texto", "redacción", "ortografía"],
            "ciencias": ["ciencias", "experimentos", "laboratorio", "naturaleza", "física", "química"],
            "geografía": ["geografía", "mapa", "comunidades", "países", "ciudades", "regiones", "españa"],
            "historia": ["historia", "época", "siglos", "acontecimientos", "pasado"],
            "educación física": ["deporte", "ejercicio", "actividad física", "juego", "competición"],
            "arte": ["arte", "pintura", "dibujo", "creatividad", "manualidades", "decoración"]
        }
        
        for tema, palabras_clave in temas_educativos.items():
            if any(palabra in prompt_lower for palabra in palabras_clave):
                info["tema_principal"] = tema
                break
        
        # Extraer enfoque metodológico
        enfoques = {
            "colaborativo": ["colaborativo", "en grupos", "entre todos", "juntos", "equipo"],
            "manipulativo": ["manipulativo", "material", "objetos", "tocar", "construir"],
            "juego": ["juego", "lúdico", "divertido", "entretenido", "gamificación"],
            "competitivo": ["competición", "ganar", "desafío", "reto", "concurso"],
            "creativo": ["creativo", "crear", "inventar", "imaginar", "original"]
        }
        
        for enfoque, palabras_clave in enfoques.items():
            if any(palabra in prompt_lower for palabra in palabras_clave):
                info["enfoque_metodologico"] = enfoque
                break
        
        # Extraer restricciones
        if any(palabra in prompt_lower for palabra in ["no quiero", "sin", "evitar", "no me gusta"]):
            palabras_restriccion = re.findall(r'(?:no quiero|sin|evitar|no me gusta)\s+([^,.\n]+)', prompt_lower)
            info["restricciones"].extend([r.strip() for r in palabras_restriccion])
        
        # Extraer preferencias
        if any(palabra in prompt_lower for palabra in ["quiero", "con", "que tenga", "incluir"]):
            palabras_preferencia = re.findall(r'(?:quiero|con|que tenga|incluir)\s+([^,.\n]+)', prompt_lower)
            info["preferencias"].extend([p.strip() for p in palabras_preferencia])
        
        return info
    
    def actualizar_contexto(self, prompt: str, accion: str) -> List[str]:
        """Actualiza el contexto según el prompt y acción determinada"""
        
        campos_modificados = []
        info_extraida = self.extraer_informacion_prompt(prompt)
        
        contexto_act = self.contexto["contexto_actividad"]
        
        if accion == "REEMPLAZAR":
            # Limpiar contexto y empezar de nuevo
            contexto_act["tema_principal"] = info_extraida["tema_principal"]
            contexto_act["enfoque_metodologico"] = info_extraida["enfoque_metodologico"] 
            contexto_act["competencias_objetivo"] = []
            contexto_act["restricciones"] = info_extraida["restricciones"]
            contexto_act["preferencias_profesor"] = info_extraida["preferencias"]
            contexto_act["ideas_rechazadas"] = []
            
            campos_modificados = ["tema_principal", "enfoque_metodologico", "restricciones", "preferencias_profesor"]
            
        elif accion in ["AMPLIAR", "REFINAR"]:
            # Actualizar/añadir información sin borrar
            if info_extraida["tema_principal"] and not contexto_act["tema_principal"]:
                contexto_act["tema_principal"] = info_extraida["tema_principal"]
                campos_modificados.append("tema_principal")
                
            if info_extraida["enfoque_metodologico"]:
                if contexto_act["enfoque_metodologico"] != info_extraida["enfoque_metodologico"]:
                    contexto_act["enfoque_metodologico"] = info_extraida["enfoque_metodologico"]
                    campos_modificados.append("enfoque_metodologico")
            
            # Añadir restricciones y preferencias sin duplicar
            for restriccion in info_extraida["restricciones"]:
                if restriccion not in contexto_act["restricciones"]:
                    contexto_act["restricciones"].append(restriccion)
                    if "restricciones" not in campos_modificados:
                        campos_modificados.append("restricciones")
            
            for preferencia in info_extraida["preferencias"]:
                if preferencia not in contexto_act["preferencias_profesor"]:
                    contexto_act["preferencias_profesor"].append(preferencia)
                    if "preferencias_profesor" not in campos_modificados:
                        campos_modificados.append("preferencias_profesor")
        
        elif accion == "INICIAR":
            # Primer prompt, establecer información base
            contexto_act["tema_principal"] = info_extraida["tema_principal"]
            contexto_act["enfoque_metodologico"] = info_extraida["enfoque_metodologico"]
            contexto_act["restricciones"] = info_extraida["restricciones"] 
            contexto_act["preferencias_profesor"] = info_extraida["preferencias"]
            
            campos_modificados = ["tema_principal", "enfoque_metodologico", "restricciones", "preferencias_profesor"]
        
        # Registrar iteración
        self.contexto["metadata_sesion"]["prompts_realizados"] += 1
        
        iteracion = IteracionPrompt(
            numero=self.contexto["metadata_sesion"]["prompts_realizados"],
            prompt=prompt,
            accion=accion,
            campos_modificados=campos_modificados,
            timestamp=datetime.now().isoformat()
        )
        
        self.contexto["historial_iteraciones"].append(asdict(iteracion))
        
        logger.info(f"🔄 Contexto actualizado - Acción: {accion} - Campos: {', '.join(campos_modificados)}")
        
        return campos_modificados
    
    def registrar_idea_rechazada(self, idea: Dict, razon: str = "No especificada"):
        """Registra una idea rechazada por el profesor"""
        idea_rechazada = {
            "titulo": idea.get("titulo", "Sin título"),
            "descripcion": idea.get("descripcion", "")[:100] + "...",
            "razon": razon,
            "timestamp": datetime.now().isoformat()
        }
        
        self.contexto["contexto_actividad"]["ideas_rechazadas"].append(idea_rechazada)
        logger.info(f"❌ Registrada idea rechazada: {idea_rechazada['titulo']}")
    
    def obtener_contexto_completo(self) -> str:
        """Genera descripción textual completa del contexto para usar en prompts"""
        ctx = self.contexto["contexto_actividad"]
        
        descripcion = f"CONTEXTO ACUMULATIVO DE LA ACTIVIDAD:\n"
        
        if ctx["tema_principal"]:
            descripcion += f"- Tema principal: {ctx['tema_principal']}\n"
            
        if ctx["enfoque_metodologico"]:
            descripcion += f"- Enfoque metodológico: {ctx['enfoque_metodologico']}\n"
            
        descripcion += f"- Nivel educativo: {ctx['nivel_educativo']}\n"
        
        if ctx["competencias_objetivo"]:
            descripcion += f"- Competencias objetivo: {', '.join(ctx['competencias_objetivo'])}\n"
            
        if ctx["preferencias_profesor"]:
            descripcion += f"- Preferencias del profesor: {', '.join(ctx['preferencias_profesor'])}\n"
            
        if ctx["restricciones"]:
            descripcion += f"- Restricciones: {', '.join(ctx['restricciones'])}\n"
            
        if ctx["ideas_rechazadas"]:
            descripcion += f"- Ideas rechazadas anteriormente: "
            titulos_rechazados = [idea["titulo"] for idea in ctx["ideas_rechazadas"]]
            descripcion += f"{', '.join(titulos_rechazados)}\n"
        
        return descripcion
    
    def obtener_json_contexto(self) -> Dict:
        """Devuelve el JSON completo del contexto"""
        return self.contexto.copy()

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
    """Agente Coordinador Principal (Master Agent) - CON CONTEXTO ACUMULATIVO"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.contexto_actividad = ContextoActividad()
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
    
    def generar_ideas_actividades(self, prompt_profesor: str) -> List[Dict]:
        """Genera 3 ideas de actividades usando contexto acumulativo"""
        
        # Analizar continuidad del contexto
        accion = self.contexto_actividad.analizar_continuidad_contexto(prompt_profesor)
        
        # Actualizar contexto acumulativo
        campos_modificados = self.contexto_actividad.actualizar_contexto(prompt_profesor, accion)
        
        # Mantener historial para compatibilidad
        self.historial_prompts.append({
            "tipo": "prompt_ideas",
            "contenido": prompt_profesor,
            "accion_contexto": accion,
            "campos_modificados": campos_modificados,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generar ideas usando contexto completo
        prompt_completo = self._crear_prompt_con_contexto()
        
        respuesta = self.ollama.generar_respuesta(prompt_completo, max_tokens=600)
        return self._parsear_ideas(respuesta)
    
    def _crear_prompt_con_contexto(self) -> str:
        """Crea prompt usando el contexto acumulativo completo"""
        
        # Obtener contexto actual
        contexto_completo = self.contexto_actividad.obtener_contexto_completo()
        
        # Seleccionar ejemplo k_ relevante (puede estar vacío)
        tema_principal = self.contexto_actividad.contexto["contexto_actividad"]["tema_principal"]
        ejemplo_seleccionado = self._seleccionar_ejemplo_relevante(tema_principal or "")
        
        # Construir prompt dinámicamente
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
            'aventura': 'piratas'
        }
        
        # Buscar coincidencias exactas
        for palabra_clave, ejemplo in mapeo_ejemplos.items():
            if palabra_clave in tema_lower and ejemplo in self.ejemplos_k:
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
    """Sistema de Agentes para Aprendizaje Basado en Proyectos (ABP)"""
    def __init__(self, host_ollama: str = "192.168.1.10", model: str = "llama3.2"):
        self.ollama = OllamaIntegrator(host=host_ollama, model=model)
        
        # Inicializar agentes
        self.coordinador = AgenteCoordinador(self.ollama)
        self.analizador_tareas = AgenteAnalizadorTareas(self.ollama)
        self.perfilador = AgentePerfiladorEstudiantes(self.ollama)
        
        # El optimizador recibe referencia al perfilador
        self.optimizador = AgenteOptimizadorAsignaciones(self.ollama)
        self.generador_recursos = AgenteGeneradorRecursos(self.ollama)
        
        self.proyecto_actual = None
        self.validado = False
        
        logger.info("🚀 Sistema de Agentes ABP inicializado")
        
    def ejecutar_flujo_completo(self) -> Dict:
        """Ejecuta el flujo completo del sistema"""
        
        print("🎓 SISTEMA DE AGENTES PARA ABP - ESTRUCTURA SENCILLA")
        print("=" * 60)
        
        # PASO 1: Prompt inicial del profesor
        prompt_profesor = input("\n📝 Ingrese su prompt de actividad educativa: ")
        
        # PASO 2: Generar ideas de actividades
        print("\n🧠 Generando ideas de actividades...")
        ideas = self.coordinador.generar_ideas_actividades(prompt_profesor)
        
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
                            
                            # Registrar las otras ideas como rechazadas (pero no la seleccionada)
                            for i, idea in enumerate(ideas):
                                if i != (idea_a_perfilar - 1):
                                    self.coordinador.contexto_actividad.registrar_idea_rechazada(idea, "Usuario prefirió otra opción para matizar")
                            
                            # Crear prompt para matizar la idea seleccionada
                            prompt_matizacion = f"Toma esta idea: '{idea_seleccionada.get('titulo', '')}' - {idea_seleccionada.get('descripcion', '')} y aplica estos cambios/matizaciones: {matizaciones}"
                            
                            print("\n🧠 Generando versiones matizadas...")
                            ideas = self.coordinador.generar_ideas_actividades(prompt_matizacion)
                            
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
                    # Registrar ideas actuales como rechazadas
                    for idea in ideas:
                        self.coordinador.contexto_actividad.registrar_idea_rechazada(idea, "Usuario solicitó nuevas ideas")
                    
                    # Lógica para generar nuevas ideas usando contexto acumulativo
                    nuevo_prompt = input("\n📝 Ingrese un nuevo prompt para generar diferentes ideas: ")
                    print("\n🧠 Generando nuevas ideas...")
                    ideas = self.coordinador.generar_ideas_actividades(nuevo_prompt)
                    
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
                "contexto_acumulativo": self.coordinador.contexto_actividad.obtener_json_contexto(),
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