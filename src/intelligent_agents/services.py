#!/usr/bin/env python3
"""
Servicios del Sistema de Agentes Inteligente
- Cargador de ejemplos k_
- Motor de detección de paralelismo
- Detector de contexto
- Analizador de materiales
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("AgentesInteligente")

@dataclass
class ActividadEducativa:
    """Estructura de datos para actividad educativa completa"""
    id: str
    titulo: str
    materia: str
    tema: str
    clima: str  # simple, juego, narrativa, complejo
    modalidad_trabajo: str  # individual, grupal, mixta
    contenido_completo: str
    tareas_estudiantes: Dict[str, str]
    materiales: List[str]
    duracion: str
    fases: List[str]
    metadatos: Dict
    timestamp: str

class CargadorEjemplosK:
    """Carga ejemplos k_ reales como few-shot estratégico"""
    
    def __init__(self, directorio_ejemplos: str = "."):
        self.directorio = directorio_ejemplos
        self.ejemplos_k = {}
        self.metadatos_ejemplos = {}
        self._cargar_ejemplos_k()
    
    def _cargar_ejemplos_k(self):
        """Carga ejemplos k_ desde archivos reales"""
        from config import DEFAULT_K_FILES
        
        for archivo in DEFAULT_K_FILES:
            ruta_completa = os.path.join(self.directorio, archivo)
            if os.path.exists(ruta_completa):
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        
                        # Extraer metadatos del ejemplo
                        self.metadatos_ejemplos[nombre_ejemplo] = self._extraer_metadatos(contenido)
                        logger.info(f"✅ Cargado ejemplo k_: {nombre_ejemplo}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {archivo}: {e}")
        
        if not self.ejemplos_k:
            logger.warning("⚠️ No se encontraron ejemplos k_. Usando ejemplo básico.")
            self._crear_ejemplo_fallback()
    
    def _extraer_metadatos(self, contenido: str) -> Dict[str, Any]:
        """Extrae metadatos de un ejemplo k_"""
        metadatos = {
            "materia": "general",
            "modalidad": "mixta", 
            "complejidad": "media",
            "tiene_narrativa": False,
            "tipo_actividad": "colaborativa"
        }
        
        contenido_lower = contenido.lower()
        
        # Detectar materia
        if any(palabra in contenido_lower for palabra in ['matemáticas', 'mates', 'números', 'fracciones']):
            metadatos["materia"] = "matematicas"
        elif any(palabra in contenido_lower for palabra in ['lengua', 'literatura', 'lectura', 'escritura']):
            metadatos["materia"] = "lengua"
        elif any(palabra in contenido_lower for palabra in ['ciencias', 'naturales', 'célula', 'cuerpo', 'experimento']):
            metadatos["materia"] = "ciencias"
        
        # Detectar narrativa
        if any(palabra in contenido_lower for palabra in ['historia', 'aventura', 'personaje', 'cuento']):
            metadatos["tiene_narrativa"] = True
        
        # Detectar modalidad
        grupos_mencionados = len(re.findall(r'grupo|equipo|pareja', contenido_lower))
        if grupos_mencionados >= 3:
            metadatos["modalidad"] = "grupal"
        elif grupos_mencionados >= 1:
            metadatos["modalidad"] = "mixta"
        else:
            metadatos["modalidad"] = "individual"
            
        return metadatos
    
    def _crear_ejemplo_fallback(self):
        """Crea ejemplo básico si no hay archivos k_"""
        ejemplo_basico = """
        ACTIVIDAD BÁSICA DE EJEMPLO
        Título: Actividad colaborativa simple
        Materia: General
        Duración: 45 minutos
        Estudiantes trabajan en grupos pequeños...
        """
        self.ejemplos_k["ejemplo_basico"] = ejemplo_basico
        self.metadatos_ejemplos["ejemplo_basico"] = {
            "materia": "general",
            "modalidad": "grupal",
            "complejidad": "baja"
        }
    
    def seleccionar_ejemplo_estrategico(self, materia_objetivo: str, tema_objetivo: str, modalidad_objetivo: str) -> str:
        """Selecciona el ejemplo k_ más apropiado según contexto"""
        
        mejor_ejemplo = "ejemplo_basico"
        mejor_puntuacion = 0
        
        for nombre, metadatos in self.metadatos_ejemplos.items():
            puntuacion = 0
            
            # Bonus por materia coincidente  
            if metadatos.get("materia", "").lower() == materia_objetivo.lower():
                puntuacion += 3
            
            # Bonus por modalidad coincidente
            if metadatos.get("modalidad", "").lower() == modalidad_objetivo.lower():
                puntuacion += 2
            
            # Bonus por tener narrativa si es apropiado
            if "narrativa" in tema_objetivo.lower() and metadatos.get("tiene_narrativa"):
                puntuacion += 2
                
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_ejemplo = nombre
        
        logger.info(f"🎯 Ejemplo k_ seleccionado: {mejor_ejemplo} (puntuación: {mejor_puntuacion})")
        return self.ejemplos_k.get(mejor_ejemplo, self.ejemplos_k.get("ejemplo_basico", ""))

class MotorParalelismo:
    """Motor de detección y optimización de paralelismo inteligente"""
    
    def __init__(self, agente_coordinador):
        self.agente_coordinador = agente_coordinador
        self.ejemplos_k = {}  # Se inyectará desde el workflow principal
    
    def detectar_oportunidades_naturales(self, contenido_estructura: str) -> bool:
        """Usa IA para detectar automáticamente oportunidades naturales de trabajo paralelo"""
        
        from crewai import Task, Crew, Process
        
        tarea_deteccion_paralelismo = Task(
            description=f"""
Analiza esta estructura educativa para detectar si tiene potencial NATURAL para trabajo paralelo/simultáneo.

ESTRUCTURA A ANALIZAR:
{contenido_estructura}

CRITERIOS DE EVALUACIÓN:
1. **TAREAS DIVISIBLES**: ¿Hay tareas que naturalmente se pueden dividir entre grupos?
2. **TRABAJO SIMULTÁNEO**: ¿Pueden varios estudiantes/grupos trabajar al mismo tiempo en diferentes aspectos?
3. **CONSTRUCCIÓN COLABORATIVA**: ¿Se está construyendo algo que permite trabajo en paralelo? (ej: maqueta, presentación, experimento)
4. **ROLES COMPLEMENTARIOS**: ¿Hay roles diferentes que pueden ejecutarse simultáneamente?
5. **ESTACIONES/ÁREAS**: ¿La actividad sugiere diferentes "lugares" o "momentos" de trabajo?

EJEMPLOS DE PARALELISMO NATURAL:
✅ "Construir maqueta del sistema solar" → Grupo A: planetas internos, Grupo B: externos, Grupo C: órbitas, Grupo D: información
✅ "Investigar animales del bosque" → Equipos por especies trabajando simultáneamente
✅ "Preparar obra de teatro" → Actores, escenografía, vestuario, música trabajando en paralelo
✅ "Experimento de plantas" → Diferentes grupos con diferentes condiciones experimentales

EJEMPLOS SIN PARALELISMO NATURAL:
❌ "Leer cuento individual y escribir resumen"
❌ "Resolver ejercicios de matemáticas" 
❌ "Examen o evaluación individual"

RESPONDE SOLO:
TIENE_POTENCIAL_PARALELO: SÍ/NO
JUSTIFICACIÓN: [1-2 líneas explicando por qué]
            """,
            agent=self.agente_coordinador,
            expected_output="Análisis de potencial paralelo con justificación"
        )
        
        crew_deteccion = Crew(
            agents=[self.agente_coordinador],
            tasks=[tarea_deteccion_paralelismo],
            process=Process.sequential,
            verbose=False  # Silencioso para no saturar
        )
        
        try:
            resultado_analisis = crew_deteccion.kickoff()
            
            # Parsear la respuesta
            resultado_str = str(resultado_analisis).lower()
            tiene_potencial = "sí" in resultado_str and "tiene_potencial_paralelo" in resultado_str
            
            logger.info(f"🔍 IA detectó paralelismo potencial: {tiene_potencial}")
            logger.info(f"📋 Análisis: {resultado_str[:200]}...")
            
            return tiene_potencial
            
        except Exception as e:
            logger.warning(f"⚠️ Error en detección IA de paralelismo: {e}")
            
            # Fallback: detección básica por palabras clave
            indicadores_basicos = ["grupo", "equipo", "construir", "crear", "diseñar", "investigar"]
            tiene_indicadores = sum(1 for ind in indicadores_basicos if ind in contenido_estructura.lower()) >= 2
            
            logger.info(f"🔄 Fallback: detección básica → {tiene_indicadores}")
            return tiene_indicadores
    
    def optimizar_coordinacion(self, estructura_original, contexto_analisis: str):
        """Optimiza la estructura para incluir coordinación paralela real y adaptativa"""
        
        from crewai import Task, Crew, Process
        
        # Obtener el ejemplo k_ de la fábrica de fracciones como referencia de paralelismo
        ejemplo_k_paralelo = self.ejemplos_k.get('k_sonnet7_fabrica_fracciones', 'Ejemplo no disponible')
        
        tarea_optimizacion = Task(
            description=f"""
Transforma esta actividad educativa para incluir TRABAJO PARALELO AUTÉNTICO sin forzar interdependencias artificiales.

ESTRUCTURA ORIGINAL:
{estructura_original}

CONTEXTO Y PREFERENCIAS DEL PROFESOR:
{contexto_analisis}

REFERENCIA DE PARALELISMO EXITOSO:
{ejemplo_k_paralelo[:800]}...

PRINCIPIOS DE OPTIMIZACIÓN:
1. **DETECTA DIVISIONES NATURALES**: ¿Qué aspectos de la actividad pueden separarse lógicamente?
2. **IDENTIFICA CONSTRUCCIÓN COLABORATIVA**: ¿Se está creando algo que permite trabajo simultáneo?
3. **RESPETA EL FLUJO ORIGINAL**: No cambies la esencia de la actividad, solo organizala mejor
4. **CREA CONVERGENCIA**: Los trabajos paralelos deben unirse en un resultado integrado

ESTRATEGIAS DE PARALELISMO SEGÚN TIPO DE ACTIVIDAD:

**SI ES INVESTIGACIÓN/ESTUDIO:**
- Diferentes grupos investigan aspectos complementarios
- Ejemplo: Sistema solar → Grupo A: planetas internos, Grupo B: externos, Grupo C: lunas, Grupo D: comparaciones

**SI ES CONSTRUCCIÓN/CREACIÓN:**
- Diferentes componentes se construyen simultáneamente  
- Ejemplo: Maqueta → Grupo A: estructura, Grupo B: detalles, Grupo C: información, Grupo D: presentación

**SI ES EXPERIMENTO/PRÁCTICA:**
- Diferentes variables o condiciones simultáneas
- Ejemplo: Plantas → Grupo A: con luz, Grupo B: sin luz, Grupo C: registro, Grupo D: hipótesis

**SI ES NARRATIVA/TEATRO:**
- Diferentes elementos simultáneos
- Ejemplo: Obra → Grupo A: actuación, Grupo B: escenografía, Grupo C: música, Grupo D: vestuario

ADAPTACIONES AUTOMÁTICAS POR ESTUDIANTE:
- Elena (TEA): Estación visual con instrucciones paso a paso
- Luis (TDAH): Estación kinestésica con cambios frecuentes
- Ana (altas capacidades): Rol de coordinación/supervisión entre estaciones
- Resto: Distribución equilibrada según habilidades

ESTRUCTURA DE RESPUESTA:
=== ACTIVIDAD OPTIMIZADA CON PARALELISMO NATURAL ===

**TÍTULO ACTUALIZADO:** [Título que refleje el trabajo paralelo]

**ORGANIZACIÓN TEMPORAL:**
- Preparación: [X minutos] - Organización de estaciones
- Trabajo paralelo: [X minutos] - Estaciones operando simultáneamente  
- Integración: [X minutos] - Unir resultados de todas las estaciones
- Presentación: [X minutos] - Resultado final conjunto

**ESTACIONES DE TRABAJO PARALELO:**
🔨 ESTACIÓN 1: [Descripción] - Estudiantes asignados
🎨 ESTACIÓN 2: [Descripción] - Estudiantes asignados  
📊 ESTACIÓN 3: [Descripción] - Estudiantes asignados
[🔄 ESTACIÓN 4: Si es necesaria]

**COORDINACIÓN ENTRE ESTACIONES:**
- Punto de sincronización 1: [Cuándo y cómo]
- Punto de sincronización 2: [Cuándo y cómo]
- Momento de integración: [Cómo se unen los resultados]

**PRODUCTO FINAL INTEGRADO:**
[Descripción de cómo se combinan todos los trabajos paralelos]

**SISTEMA DE ROTACIONES (si aplica):**
[Solo si es beneficioso - no forzar]
            """,
            agent=self.agente_coordinador,
            expected_output="Estructura educativa con paralelismo natural y organizativo"
        )
        
        crew_optimizacion = Crew(
            agents=[self.agente_coordinador],
            tasks=[tarea_optimizacion],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            estructura_optimizada = crew_optimizacion.kickoff()
            return estructura_optimizada
        except Exception as e:
            logger.error(f"Error optimizando paralelismo: {e}")
            print(f"⚠️ No pude optimizar el paralelismo, mantengo estructura original")
            return estructura_original

class AnalizadorMateriales:
    """Analizador de materiales educativos"""
    
    @staticmethod
    def extraer_materiales_de_actividad(contenido: str) -> List[str]:
        """Extrae lista de materiales de una actividad generada"""
        
        materiales = []
        
        # Buscar secciones de materiales
        patrones_materiales = [
            r"materiales?\s*necesarios?\s*:?(.+?)(?:\n\n|\*\*|$)",
            r"recursos?\s*:?(.+?)(?:\n\n|\*\*|$)",
            r"lo que necesitas?\s*:?(.+?)(?:\n\n|\*\*|$)"
        ]
        
        for patron in patrones_materiales:
            coincidencias = re.findall(patron, contenido, re.IGNORECASE | re.DOTALL)
            for coincidencia in coincidencias:
                # Limpiar y separar materiales
                lineas = coincidencia.strip().split('\n')
                for linea in lineas:
                    linea_limpia = re.sub(r'^[-•*]\s*', '', linea.strip())
                    if linea_limpia and len(linea_limpia) > 3:
                        materiales.append(linea_limpia)
        
        # Si no encuentra materiales específicos, usar lista genérica
        if not materiales:
            materiales = ["Materiales según actividad generada", "Recursos de consulta"]
        
        return materiales