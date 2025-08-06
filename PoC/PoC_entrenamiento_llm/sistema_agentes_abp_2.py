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
from dataclasses import dataclass, asdict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SistemaAgentesABP")

def serialize(obj):
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def parse_json_seguro(texto: str) -> Optional[dict]:
    try:
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()
        if not texto_limpio:
            raise ValueError("Respuesta vacía")
        return json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON del LLM: {e}")
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
    adaptaciones: List[str] = None

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
    """Agente Coordinador Principal (Master Agent) - REFRACTORIZADO DINÁMICO"""
    

    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.historial_prompts = []
        self.ejemplos_k = self._cargar_ejemplos_k() # Aún podemos usar esto para inspirar, no para copiar
    
    def _cargar_ejemplos_k(self) -> Dict[str, str]:
        """Carga ejemplos k_ para few-shot learning"""
        ejemplos = {}
        # Rutas relativas desde poc/poc_entrenamiento_llm (donde se ejecuta)
        base_path = "actividades_generadas/"
        archivos_k = [
            f"{base_path}k_feria_acertijos.txt",
            f"{base_path}k_sonnet_supermercado.txt", 
            f"{base_path}k_celula.txt",
            f"{base_path}k_piratas.txt",
            f"{base_path}k_sonnet7_fabrica_fracciones.txt"
        ]
        
        for archivo in archivos_k:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    nombre_ejemplo = archivo.split('/')[-1].replace('.txt', '').replace('k_', '')
                    ejemplos[nombre_ejemplo] = contenido[:800]  # Primeros 800 caracteres
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
    
    def _crear_prompt_dinamico(self, prompt_profesor: str) -> str:
        """
        Crea un prompt dinámico y a medida basado en el análisis del prompt del profesor.
        """
        
        # --- FASE 1: ANÁLISIS DEL PROMPT DEL PROFESOR ---
        prompt_analisis = f"""
        Eres un experto en el análisis de prompts educativos.
        Extrae la siguiente información del prompt del profesor, sin añadir texto adicional.

        PROMPT DEL PROFESOR: "{prompt_profesor}"

        Formato de salida (solo JSON):
        {{
        "tema": "[tema principal extraído, ej. 'obra artística']",
        "restricciones": ["[lista de restricciones, ej. 'sin narrativa']"],
        "formato_arte": "[formato de la obra de arte, ej. 'indefinido', 'pintura', 'escultura']",
        "objetivo": "[objetivo educativo, ej. 'aprender los tiempos verbales']",
        "duracion": "[duración solicitada, ej. 'una semana']"
        }}
        """
        
        # Simulación de llamada al LLM para el análisis
        try:
            analisis_json_str = self.ollama.generar_respuesta(prompt_analisis, max_tokens=200)
            # El LLM a veces devuelve el JSON dentro de bloques de código, así que los eliminamos
            analisis_json_str = analisis_json_str.replace("```json", "").replace("```", "").strip()
            analisis = json.loads(analisis_json_str)
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.warning(f"❌ Fallo al analizar el prompt. Usando valores por defecto. Error: {e}")
            analisis = {
                "tema": "actividad artística",
                "restricciones": ["sin narrativa"],
                "formato_arte": "indefinido",
                "objetivo": "tiempos verbales",
                "duracion": "una semana"
            }
        analisis = self._crear_fallback_analisis(prompt_profesor)

        # --- FASE 2: CONSTRUCCIÓN DINÁMICA DEL PROMPT DE GENERACIÓN ---
        # Ahora construimos un nuevo prompt con el análisis, enfocándonos en la creatividad
        
        tema = analisis.get("tema", "una actividad creativa")
        restricciones = " ".join(analisis.get("restricciones", ["sin restricciones específicas"]))
        formato_arte = analisis.get("formato_arte", "cualquier tipo de arte")
        objetivo = analisis.get("objetivo", "un objetivo educativo")
        duracion = analisis.get("duracion", "una semana")
        
        prompt_generacion = f"""
        Eres un experto en diseño de actividades educativas innovadoras.
        Genera 3 ideas de proyectos de ABP para 4º de Primaria que cumplan con las siguientes condiciones:
        
        1. **Tema y Formato:** La actividad debe ser {tema}, enfocada en {formato_arte}.
        2. **Objetivo:** El propósito principal es trabajar {objetivo}.
        3. **Restricciones:** La actividad debe cumplir con la siguiente condición: {restricciones}.
        4. **Duración:** La actividad debe poder completarse en {duracion}.
        5. **Flexibilidad de Tareas:** Desglosa la actividad en 3-5 tareas que puedan realizarse de manera simultánea, individualmente o en pequeños grupos, y que no dependan de una secuencia rígida.
        
        FORMATO DE SALIDA:
        IDEA 1:
        Título: [título creativo y no narrativo]
        Descripción: [descripción que explica el concepto, el objetivo y la duración]
        Nivel: 4º Primaria
        Objetivo de aprendizaje: [lista de objetivos claros]
        Tareas principales: [lista de 3-5 tareas simultáneas]
        Duración: [tiempo realista]

        IDEA 2:
        [mismo formato...]

        IDEA 3:
        [mismo formato...]
        """
        return prompt_generacion
        
    def generar_ideas_actividades(self, prompt_profesor: str) -> List[Dict]:
        """Genera 3 ideas de actividades basadas en el prompt del profesor"""
        self.historial_prompts.append({
            "tipo": "prompt_inicial",
            "contenido": prompt_profesor,
            "timestamp": datetime.now().isoformat()
        })
        
        # Usar el prompt dinámico
        prompt_ideas = self._crear_prompt_dinamico(prompt_profesor)
        
        respuesta = self.ollama.generar_respuesta(prompt_ideas, max_tokens=600)
        return self._parsear_ideas(respuesta)
    
    def _seleccionar_ejemplo_relevante(self, prompt_profesor: str) -> str:
        """Selecciona el ejemplo k_ más relevante según el prompt"""
        prompt_lower = prompt_profesor.lower()
        
        # Mapeo de palabras clave a ejemplos
        mapeo_ejemplos = {
            'supermercado': 'sonnet_supermercado',
            'dinero': 'sonnet_supermercado',
            'comprar': 'sonnet_supermercado',
            'fracciones': 'sonnet7_fabrica_fracciones',
            'fraccion': 'sonnet7_fabrica_fracciones',
            'juego': 'feria_acertijos',
            'juegos': 'feria_acertijos',
            'manipulativ': 'feria_acertijos',
            'resolver': 'feria_acertijos',
            'celula': 'celula',
            'ciencias': 'celula',
            'piratas': 'piratas',
            'tesoro': 'piratas'
        }
        
        # Buscar coincidencias
        for palabra_clave, ejemplo in mapeo_ejemplos.items():
            if palabra_clave in prompt_lower and ejemplo in self.ejemplos_k:
                return self.ejemplos_k[ejemplo]
        
        # Fallback al primer ejemplo disponible
        if self.ejemplos_k:
            return list(self.ejemplos_k.values())[0]
        
        # Fallback si no hay ejemplos cargados
        return """
EJEMPLO FALLBACK:
ACTIVIDAD: Feria Matemática de Resolución de Problemas
OBJETIVOS: Desarrollar competencias matemáticas mediante resolución colaborativa de problemas
DESCRIPCIÓN: Los estudiantes participan en estaciones rotativas resolviendo desafíos matemáticos
ROL PROFESOR: Observación activa y guía discreta
ADAPTACIONES: Apoyo visual para TEA, movimiento para TDAH, retos adicionales para altas capacidades
MATERIALES: Fichas de problemas, material manipulativo, cronómetros
"""
    
    def generar_ideas_actividades(self, prompt_profesor: str) -> List[Dict]:
        """Genera 3 ideas de actividades basadas en el prompt del profesor"""
        self.historial_prompts.append({
            "tipo": "prompt_inicial",
            "contenido": prompt_profesor,
            "timestamp": datetime.now().isoformat()
        })
        
        # Usar el prompt dinámico
        prompt_ideas = self._crear_prompt_dinamico(prompt_profesor)
        
        respuesta = self.ollama.generar_respuesta(prompt_ideas, max_tokens=600)
        return self._parsear_ideas(respuesta)
    
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
        
        return ideas[:3]  # Asegurar máximo 3 ideas
    
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

=== ESTRUCTURA RECOMENDADA === adaptar a la especificación del profesor
1. PREPARACIÓN (1-2 tareas): Contextualización y organización
2. DESARROLLO (3-5 tareas): Núcleo de la actividad con rotaciones
3. REFLEXIÓN (1-2 tareas): Metacognición y cierre

Identifica entre 6-8 subtareas específicas siguiendo esta estructura. Para cada subtarea proporciona:
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
    """Agente Perfilador de Estudiantes (Student Profiler Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.perfiles_base = self._cargar_perfiles_piloto()
    
    def _cargar_perfiles_piloto(self) -> List[Estudiante]:
        """Carga perfiles de estudiantes del dataset piloto"""
        perfiles = [
            Estudiante("001", "ALEX M.", ["pensamiento lógico", "trabajo autónomo"], ["necesita tiempo extra"], 8, ["investigador"], ["instrucciones claras"]),
            Estudiante("002", "MARÍA L.", ["comunicación oral", "trabajo en equipo"], ["dificultades escritura"], 7, ["presentadora"], ["apoyo escritura"]),
            Estudiante("003", "ELENA R.", ["creatividad", "arte visual"], ["TEA nivel 1"], 6, ["diseñadora"], ["rutinas claras", "espacio tranquilo"]),
            Estudiante("004", "PABLO S.", ["liderazgo", "organización"], ["TDAH"], 8, ["coordinador"], ["descansos frecuentes"]),
            Estudiante("005", "ANA G.", ["matemáticas", "análisis"], ["timidez extrema"], 7, ["analista"], ["trabajo individual inicial"]),
            Estudiante("006", "LUIS C.", ["tecnología", "innovación"], ["dislexia"], 7, ["técnico"], ["herramientas digitales"]),
            Estudiante("007", "SARA M.", ["empatía", "mediación"], ["alta sensibilidad"], 6, ["mediadora"], ["ambiente relajado"]),
            Estudiante("008", "DIEGO P.", ["experimentos", "ciencias"], ["necesidades motrices"], 8, ["científico"], ["adaptación material"])
        ]
        return perfiles
    
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
Rol_sugerido: [rol en el proyecto]

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
    
    def __init__(self, ollama_integrator: OllamaIntegrator, perfiles_estudiantes: List[Estudiante]):
        self.ollama = ollama_integrator
        self.perfiles = {e.id: e for e in perfiles_estudiantes}

    def optimizar_asignaciones(self, tareas: List[Tarea], analisis_estudiantes: Dict) -> Dict:
        """Optimiza las asignaciones de tareas basándose en el análisis de perfiles."""
        
        # Convertir la lista de objetos Tarea a una lista de diccionarios para que sea serializable
        tareas_dict_list = [asdict(tarea) for tarea in tareas] 
        
        # Prepara el prompt para el LLM
        prompt_optimizacion = f"""
        Eres un experto en asignación de tareas educativas. Tu misión es tomar la lista de tareas y los perfiles de los estudiantes para crear una asignación optimizada. El objetivo es equilibrar la carga de trabajo y asignar tareas en función de los perfiles para maximizar el aprendizaje y la colaboración.
        
        Tareas: {json.dumps(tareas_dict_list, indent=2, ensure_ascii=False)}
        
        Perfiles de estudiantes: {json.dumps(analisis_estudiantes, indent=2, ensure_ascii=False)}
        
        Considera los perfiles y el tiempo estimado de cada tarea. No asignes a un mismo estudiante más de 3 tareas en total.
        
        Formato de salida (solo JSON):
        {{
        "asignaciones": {{
            "estudiante_001": ["id_tarea_1", "id_tarea_2"],
            "estudiante_002": ["id_tarea_3"],
            ...
        }}
        }}
        """
        
        try:
            # Llamada al LLM y limpieza de la respuesta
            respuesta_llm = self.ollama.generar_respuesta(prompt_optimizacion, max_tokens=500)
            respuesta_llm = respuesta_llm.replace("```json", "").replace("```", "").strip()
            asignaciones = json.loads(respuesta_llm)
            logger.info(f"✅ Asignaciones parseadas correctamente.")
            return asignaciones.get('asignaciones', {})
        
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ Error al parsear JSON del LLM: {e}")
            logger.info("⚠️ Usando lógica de fallback para las asignaciones.")
            # Lógica de fallback simple: distribuir tareas de manera equitativa
            asignaciones_fallback = {}
            
            # Asegurar que haya estudiantes antes de realizar la operación de módulo
            num_estudiantes = len(analisis_estudiantes)
            if num_estudiantes == 0:
                logger.warning("No hay perfiles de estudiantes para asignar tareas. Devolviendo asignaciones vacías.")
                return {} # Devolver un diccionario vacío si no hay estudiantes
            
            # Lógica de asignación equitativa
            for i, tarea in enumerate(tareas):
                estudiante_id_base = list(analisis_estudiantes.keys())[i % num_estudiantes]
                asignaciones_fallback.setdefault(estudiante_id_base, []).append(tarea.id)
            
            
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
        
        # Preparamos el prompt para solicitar los recursos de manera estructurada.
        prompt_recursos = f"""
        Eres un experto en educación y recursos didácticos. Genera una lista completa de recursos para el siguiente proyecto de ABP, en formato JSON. Incluye materiales físicos, recursos analógicos y herramientas digitales.
        
        Proyecto: {json.dumps(proyecto_base, indent=2, ensure_ascii=False)}
        Tareas: {json.dumps([asdict(t) for t in tareas], indent=2, ensure_ascii=False)}
        
        Formato de salida (solo JSON):
        {{
          "recursos_materiales": [
            "Material 1: descripción",
            "Material 2: descripción",
            ...
          ],
          "recursos_analogicos": [
            "Recurso analógico 1: descripción",
            "Recurso analógico 2: descripción",
            ...
          ],
          "recursos_digitales": [
            "Herramienta digital 1: descripción",
            "Herramienta digital 2: descripción",
            ...
          ]
        }}
        """
        
        try:
            # Enviamos la solicitud al LLM y limpiamos la respuesta de cualquier texto extra.
            respuesta_llm = self.ollama.generar_respuesta(prompt_recursos, max_tokens=500)
            respuesta_llm = respuesta_llm.replace("```json", "").replace("```", "").strip()
            recursos = json.loads(respuesta_llm)
            logger.info(f"✅ Recursos parseados correctamente.")
            return recursos
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ Error al parsear JSON de recursos: {e}")
            logger.info("⚠️ Usando lógica de fallback para los recursos.")
            # Lógica de fallback para evitar errores si el LLM falla
            return {
                "recursos_materiales": ["Papel", "Lápices", "Marcadores", "Pintura"],
                "recursos_analogicos": ["Regletas de Cuisenaire", "Bloques lógicos"],
                "recursos_digitales": ["Editor de texto", "Buscador de imágenes"]
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
        
        # El optimizador ahora necesita los perfiles para su lógica interna
        self.optimizador = AgenteOptimizadorAsignaciones(self.ollama, self.perfilador.perfiles_base)
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
                print(f"   0: Generar nuevas ideas con un prompt diferente")
                
                # La opción -1 solo se muestra si ya hay una actividad seleccionada
                if actividad_seleccionada:
                    print(f"   -1: Añadir más detalles a la idea '{actividad_seleccionada.get('titulo', 'Sin título')}'")
                
                seleccion = int(input(f"\n🎯 Su elección: "))
                
                if seleccion == 0:
                    # Lógica para generar nuevas ideas
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
                    print(f"❌ Selección inválida. Por favor, elija un número entre 1 y {len(ideas)}, 0 para nuevas ideas.")
                    if actividad_seleccionada:
                         print(f"   Si desea añadir más detalles, puede usar la opción -1.")
                    
            except ValueError:
                print("❌ Ingrese un número válido")
        
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
        asignaciones = self.optimizador.optimizar_asignaciones(tareas, analisis_estudiantes)
        
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
                "sistema": "AgentesABP_v1.0",
                "historial_prompts": self.coordinador.historial_prompts,
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
                "tareas": [t.id for t in tareas if "investigar" in t.descripcion.lower() or "planificar" in t.descripcion.lower()][:3]
            },
            {
                "nombre": "Fase 2: Desarrollo y Creación",
                "duracion": "5-6 días", 
                # Corrección: Acceder a t.tipo
                "tareas": [t.id for t in tareas if t.tipo in ["colaborativa", "creativa"]][:4]
            },
            {
                "nombre": "Fase 3: Presentación y Evaluación",
                "duracion": "2-3 días",
                # Corrección: Acceder a t.id
                "tareas": [t.id for t in tareas if "presentar" in t.descripcion.lower() or "evaluar" in t.descripcion.lower()][:2]
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
        print(f"   Competencias: {', '.join(proyecto['proyecto']['competencias_objetivo'][:3])}...")
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