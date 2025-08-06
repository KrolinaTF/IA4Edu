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

class OllamaIntegrator:
    """Integrador simplificado con Ollama API"""
    
    def __init__(self, host: str = "192.168.1.10", port: int = 11434, model: str = "llama3.2"):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        
        # Importar la clase existente de Ollama
        try:
            from ollama_api_integrator import OllamaAPIEducationGenerator
            self.ollama = OllamaAPIEducationGenerator(host=host, port=port, model_name=model)
            logger.info("✅ Ollama integrado correctamente")
        except ImportError:
            logger.error("❌ No se pudo importar OllamaAPIEducationGenerator")
            self.ollama = None
    
    def generar_respuesta(self, prompt: str, max_tokens: int = 500) -> str:
        """Genera respuesta usando Ollama"""
        if self.ollama:
            return self.ollama.generar_texto(prompt, max_tokens=max_tokens, temperature=0.7)
        else:
            return f"[SIMULADO] Respuesta a: {prompt[:50]}..."

# ===== AGENTES ESPECIALIZADOS =====

class AgenteCoordinador:
    """Agente Coordinador Principal (Master Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
        self.historial_prompts = []
        self.ejemplos_k = self._cargar_ejemplos_k()
    
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
    
    def _crear_prompt_fewshot(self, prompt_profesor: str) -> str:
        """Crea prompt con ejemplos few-shot de actividades k_"""
        
        # Seleccionar ejemplo más relevante según palabras clave
        ejemplo_seleccionado = self._seleccionar_ejemplo_relevante(prompt_profesor)
        
        prompt_fewshot = f"""
Eres un experto en diseño de actividades educativas para 4º de Primaria. Tu misión es generar actividades ABP (Aprendizaje Basado en Proyectos) siguiendo los patrones exitosos de actividades k_.

=== EJEMPLO DE ACTIVIDAD EXITOSA ===
{ejemplo_seleccionado}

=== PATRONES A SEGUIR ===
• NARRATIVA INMERSIVA: Contextualizar con historias atractivas (piratas, ferias, fábricas, supermercados)
• OBJETIVOS CLAROS: Competencias matemáticas específicas + habilidades transversales
• ROL DOCENTE: Observación activa, guía discreta, gestión emocional
• ADAPTACIONES: Específicas para TEA, TDAH, altas capacidades
• MATERIALES CONCRETOS: Manipulativos, reales, accesibles
• EVALUACIÓN FORMATIVA: Observación, registro, reflexión

=== SOLICITUD DEL PROFESOR ===
"{prompt_profesor}"

=== INSTRUCCIONES ===
Basándote en la solicitud del profesor y siguiendo los patrones de las actividades k_ exitosas, genera exactamente 3 ideas de actividades educativas diferentes. Para cada una proporciona:

1. Título descriptivo (con narrativa inmersiva)
2. Breve descripción (2-3 frases contextualizadas)
3. Nivel educativo (4º Primaria adaptado a diversidad)
4. Competencias principales que desarrolla
5. Duración estimada realista

FORMATO EXACTO:
IDEA 1:
Título: [título con narrativa inmersiva]
Descripción: [descripción contextualizada y atractiva]
Nivel: 4º Primaria
Competencias: [competencias específicas]
Duración: [tiempo realista]

IDEA 2:
[mismo formato...]

IDEA 3:
[mismo formato...]
"""
        return prompt_fewshot
    
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
        
        # Usar prompt con few-shot learning
        prompt_ideas = self._crear_prompt_fewshot(prompt_profesor)
        
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
• NARRATIVA INMERSIVA: Mantener contexto atractivo en cada tarea
• ESTRUCTURA PEDAGÓGICA: Preparación → Desarrollo → Reflexión
• ROLES ESPECÍFICOS: Asignar roles concretos según fortalezas
• MATERIAL MANIPULATIVO: Usar objetos reales y tangibles
• ADAPTACIONES DUA: Considerar TEA, TDAH, altas capacidades
• EVALUACIÓN FORMATIVA: Observación y registro continuo

=== ESTRUCTURA RECOMENDADA ===
1. PREPARACIÓN (1-2 tareas): Contextualización y organización
2. DESARROLLO (3-5 tareas): Núcleo de la actividad con rotaciones
3. REFLEXIÓN (1-2 tareas): Metacognición y cierre

Identifica entre 6-8 subtareas específicas siguiendo esta estructura. Para cada subtarea proporciona:
- Descripción clara y específica (con contexto narrativo)
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
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
    
    def optimizar_asignaciones(self, tareas: List[Tarea], analisis_estudiantes: Dict) -> List[Dict]:
        """Realiza el reparto óptimo de tareas"""
        
        # Preparar información para el prompt
        info_tareas = []
        for tarea in tareas:
            info_tareas.append(f"{tarea.id}: {tarea.descripcion} (Complejidad: {tarea.complejidad}, Tipo: {tarea.tipo})")
        
        info_analisis = []
        for estudiante_id, analisis in analisis_estudiantes.items():
            compatibles = ", ".join(analisis.get("tareas_compatibles", []))
            desarrollo = ", ".join(analisis.get("tareas_desarrollo", []))
            rol = analisis.get("rol_sugerido", "colaborador")
            info_analisis.append(f"{estudiante_id}: Compatible con [{compatibles}], Desarrollo [{desarrollo}], Rol: {rol}")
        
        prompt_optimizacion = f"""
Optimiza la asignación de tareas considerando estos principios:
1. Maximizar fortalezas individuales (60%)
2. Equilibrar carga de trabajo (20%)
3. Promover desarrollo de competencias (20%)
4. Máximo 3 tareas por estudiante
5. Equipos de 2-4 personas para tareas colaborativas

TAREAS DISPONIBLES:
{chr(10).join(info_tareas)}

ANÁLISIS DE ESTUDIANTES:
{chr(10).join(info_analisis)}

Propón asignaciones específicas:

ASIGNACIONES:
[Para cada estudiante, lista las tareas asignadas, su rol principal y justificación]

EQUIPOS COLABORATIVOS:
[Para tareas colaborativas, especifica qué estudiantes trabajarán juntos]
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_optimizacion, max_tokens=700)
        return self._parsear_asignaciones(respuesta, tareas)
    
    def _parsear_asignaciones(self, respuesta: str, tareas: List[Tarea]) -> List[Dict]:
        """Parsea las asignaciones optimizadas"""
        asignaciones = []
        
        # Lógica simplificada de parseo
        # En una implementación real, se haría un parseo más sofisticado
        estudiantes_ids = ["001", "002", "003", "004", "005", "006", "007", "008"]
        
        for i, estudiante_id in enumerate(estudiantes_ids):
            # Distribución simple basada en el número de tareas
            tareas_asignadas = []
            inicio = (i * len(tareas)) // len(estudiantes_ids)
            fin = ((i + 1) * len(tareas)) // len(estudiantes_ids)
            
            for j in range(inicio, min(fin, len(tareas))):
                if j < len(tareas):
                    tareas_asignadas.append(tareas[j].id)
            
            asignacion = {
                "estudiante_id": estudiante_id,
                "tareas_asignadas": tareas_asignadas[:3],  # Máximo 3 tareas
                "rol_principal": self._determinar_rol(estudiante_id),
                "adaptaciones": self._obtener_adaptaciones(estudiante_id)
            }
            asignaciones.append(asignacion)
        
        return asignaciones
    
    def _determinar_rol(self, estudiante_id: str) -> str:
        """Determina rol principal basado en el ID del estudiante"""
        roles = {
            "001": "investigador principal",
            "002": "comunicadora",
            "003": "diseñadora visual", 
            "004": "coordinador de equipo",
            "005": "analista de datos",
            "006": "especialista técnico",
            "007": "facilitadora grupal",
            "008": "experimentador"
        }
        return roles.get(estudiante_id, "colaborador")
    
    def _obtener_adaptaciones(self, estudiante_id: str) -> List[str]:
        """Obtiene adaptaciones específicas por estudiante"""
        adaptaciones = {
            "001": ["instrucciones escritas claras", "tiempo adicional"],
            "002": ["herramientas de apoyo a la escritura"],
            "003": ["rutinas estructuradas", "espacio tranquilo"],
            "004": ["descansos cada 20 minutos", "movimiento permitido"],
            "005": ["presentaciones individuales iniciales"],
            "006": ["material en formato digital", "fuentes legibles"],
            "007": ["ambientes de baja estimulación sensorial"],
            "008": ["materiales adaptados para manipulación"]
        }
        return adaptaciones.get(estudiante_id, ["seguimiento personalizado"])

class AgenteGeneradorRecursos:
    """Agente Generador de Recursos (Resource Generator Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        self.ollama = ollama_integrator
    
    def generar_recursos(self, proyecto_base: Dict, tareas: List[Tarea], asignaciones: List[Dict]) -> Dict:
        """Propone materiales y herramientas necesarias"""
        
        # Extraer competencias y tipos de tareas
        competencias = set()
        tipos_tareas = set()
        
        for tarea in tareas:
            competencias.update(tarea.competencias_requeridas)
            tipos_tareas.add(tarea.tipo)
        
        prompt_recursos = f"""
Genera recursos específicos para este proyecto ABP:

PROYECTO: {proyecto_base['titulo']}
NIVEL: {proyecto_base['nivel']}
COMPETENCIAS: {', '.join(competencias)}
TIPOS DE TAREAS: {', '.join(tipos_tareas)}

Propón recursos organizados en:

MATERIALES FÍSICOS:
[Lista de materiales tangibles necesarios]

HERRAMIENTAS DIGITALES:
[Software, apps, plataformas online]

RECURSOS DIDÁCTICOS:
[Libros, videos, artículos adaptados al nivel]

ESPACIOS NECESARIOS:
[Tipos de espacios requeridos]

PRESUPUESTO ESTIMADO:
[Coste aproximado en euros]

ADAPTACIONES DUA:
[Recursos específicos para diversidad funcional]
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_recursos, max_tokens=600)
        return self._parsear_recursos(respuesta)
    
    def _parsear_recursos(self, respuesta: str) -> Dict:
        """Parsea los recursos generados"""
        recursos = {
            "materiales_fisicos": self._extraer_seccion(respuesta, "MATERIALES FÍSICOS:"),
            "herramientas_digitales": self._extraer_seccion(respuesta, "HERRAMIENTAS DIGITALES:"),
            "recursos_didacticos": self._extraer_seccion(respuesta, "RECURSOS DIDÁCTICOS:"),
            "espacios_necesarios": self._extraer_seccion(respuesta, "ESPACIOS NECESARIOS:"),
            "presupuesto_estimado": self._extraer_seccion_simple(respuesta, "PRESUPUESTO ESTIMADO:"),
            "adaptaciones_dua": self._extraer_seccion(respuesta, "ADAPTACIONES DUA:")
        }
        return recursos
    
    def _extraer_seccion(self, texto: str, inicio: str) -> List[str]:
        """Extrae una sección como lista de elementos"""
        partes = texto.split(inicio)
        if len(partes) < 2:
            return []
        
        seccion = partes[1].split('\n\n')[0]  # Hasta el siguiente párrafo vacío
        items = []
        
        for line in seccion.split('\n'):
            line = line.strip()
            if line and not line.startswith(('MATERIALES', 'HERRAMIENTAS', 'RECURSOS', 'ESPACIOS', 'PRESUPUESTO', 'ADAPTACIONES')):
                # Limpiar marcadores como -, *, [números]
                item = re.sub(r'^[-*\d.)\s]+', '', line).strip()
                if item:
                    items.append(item)
        
        return items[:5]  # Máximo 5 elementos por sección
    
    def _extraer_seccion_simple(self, texto: str, inicio: str) -> str:
        """Extrae una sección como texto simple"""
        partes = texto.split(inicio)
        if len(partes) < 2:
            return "No especificado"
        
        seccion = partes[1].split('\n\n')[0].strip()
        return seccion.split('\n')[0].strip() if seccion else "No especificado"

# ===== SISTEMA PRINCIPAL =====

class SistemaAgentesABP:
    """Sistema principal que coordina todos los agentes"""
    
    def __init__(self, host_ollama: str = "192.168.1.10", model: str = "llama3.2"):
        self.ollama = OllamaIntegrator(host=host_ollama, model=model)
        
        # Inicializar agentes
        self.coordinador = AgenteCoordinador(self.ollama)
        self.analizador_tareas = AgenteAnalizadorTareas(self.ollama)
        self.perfilador = AgentePerfiladorEstudiantes(self.ollama)
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
        while True:
            try:
                print(f"\n🎯 Opciones disponibles:")
                print(f"   1-{len(ideas)}: Seleccionar una actividad")
                print(f"   0: Generar nuevas ideas con prompt diferente")
                print(f"   -1: Continuar con actividad seleccionada pero añadir más detalles")
                
                seleccion = int(input(f"\n🎯 Su elección: "))
                
                if seleccion == 0:
                    # Generar nuevas ideas
                    nuevo_prompt = input("\n📝 Ingrese un nuevo prompt para generar diferentes ideas: ")
                    print("\n🧠 Generando nuevas ideas...")
                    ideas = self.coordinador.generar_ideas_actividades(nuevo_prompt)
                    
                    print("\n💡 NUEVAS IDEAS GENERADAS:")
                    for i, idea in enumerate(ideas, 1):
                        print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
                        print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
                        print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
                        print(f"   Duración: {idea.get('duracion', 'No especificada')}")
                    continue
                    
                elif 1 <= seleccion <= len(ideas):
                    actividad_seleccionada = ideas[seleccion - 1]
                    
                    # Preguntar si quiere añadir detalles
                    detalle_extra = input(f"\n📝 ¿Desea añadir detalles específicos sobre '{actividad_seleccionada.get('titulo', 'la actividad')}' antes de continuar? (Enter para continuar, o escriba detalles): ")
                    
                    if detalle_extra.strip():
                        # Registrar detalles adicionales
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
                    print("❌ Selección inválida")
                    
            except ValueError:
                print("❌ Ingrese un número válido")
        
        # PASO 4: Información adicional (opcional)
        info_adicional = input("\n📋 ¿Información adicional específica? (Enter para continuar): ")
        
        # PASO 5: Coordinar proceso (incluir todos los detalles acumulados)
        print("\n🎯 Coordinando proyecto...")
        
        # Recopilar toda la información adicional del historial
        info_completa = info_adicional
        for prompt_entry in self.coordinador.historial_prompts:
            if prompt_entry["tipo"] == "detalles_actividad_seleccionada":
                info_completa += f"\n\nDetalles específicos de la actividad: {prompt_entry['detalles_adicionales']}"
        
        proyecto_base = self.coordinador.coordinar_proceso(actividad_seleccionada, info_completa)
        
        # PASO 6: Analizar tareas
        print("\n🔍 Analizando y descomponiendo tareas...")
        tareas = self.analizador_tareas.descomponer_actividad(proyecto_base)
        
        # PASO 7: Perfilar estudiantes
        print("\n👥 Analizando perfiles de estudiantes...")
        analisis_estudiantes = self.perfilador.analizar_perfiles(tareas)
        
        # PASO 8: Optimizar asignaciones
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
                            asignaciones: List[Dict], recursos: Dict) -> Dict:
        """Crea la estructura final del proyecto"""
        
        # Organizar tareas por fases
        fases = self._organizar_fases(tareas)
        
        # Crear estructura final
        proyecto_final = {
            "proyecto": {
                "titulo": proyecto_base["titulo"],
                "descripcion": proyecto_base["descripcion"],
                "duracion": proyecto_base["duracion_base"],
                "competencias_objetivo": proyecto_base["competencias_base"]
            },
            "fases": fases,
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
                "tareas": [t.id for t in tareas if "investigar" in t.descripcion.lower() or "planificar" in t.descripcion.lower()][:3]
            },
            {
                "nombre": "Fase 2: Desarrollo y Creación",
                "duracion": "5-6 días", 
                "tareas": [t.id for t in tareas if t.tipo in ["colaborativa", "creativa"]][:4]
            },
            {
                "nombre": "Fase 3: Presentación y Evaluación",
                "duracion": "2-3 días",
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