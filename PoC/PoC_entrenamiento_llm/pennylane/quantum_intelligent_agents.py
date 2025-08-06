#!/usr/bin/env python3
"""
Sistema de Agentes Inteligente con Integración Cuántica
Combina el sistema de agentes CrewAI con optimización cuántica de prompts
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import re

# Importar el optimizador cuántico
from quantum_educational_optimizer import QuantumEducationalOptimizer

# Las funciones están implementadas como métodos de la clase

# ================================================================================
# CONFIGURACIÓN CRÍTICA DE OLLAMA + CREWAI (DEBE IR ANTES DE LOS IMPORTS)
# ================================================================================

# Configurar variables de entorno para evitar errores con CrewAI
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"  
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"
os.environ["LITELLM_PROVIDER"] = "ollama"  # CRÍTICO: Definir provider
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder requerido
os.environ["OPENAI_MODEL_NAME"] = "ollama/qwen3:latest"  # Con prefijo
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuantumIntelligentAgents")

try:
    from crewai import Agent, Task, Crew, Process
    from langchain_community.llms import Ollama
    import litellm
    logger.info("✅ CrewAI y dependencias importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando dependencias: {e}")
    logger.error("💡 Instala: pip install crewai langchain-community")
    raise


@dataclass
class QuantumActividadEducativa:
    """Estructura de datos para actividad educativa con mejora cuántica"""
    id: str
    titulo: str
    materia: str
    tema: str
    clima: str
    modalidad_trabajo: str
    contenido_completo: str
    tareas_estudiantes: Dict[str, str]
    materiales: List[str]
    duracion: str
    fases: List[str]
    metadatos: Dict
    timestamp: str
    # Nuevos campos cuánticos
    parametros_cuanticos: Dict
    prompt_mejorado: str
    historial_optimizacion: List[float]


class CargadorEjemplosK:
    """Carga ejemplos k_ reales como few-shot estratégico"""
    
    def __init__(self, directorio_ejemplos: str = None):
        # Establecer directorio relativo al archivo actual
        if directorio_ejemplos is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.directorio = os.path.join(current_dir, "..")  # Directorio padre
        else:
            self.directorio = directorio_ejemplos
        self.ejemplos_k = {}
        self.metadatos_ejemplos = {}
        self._cargar_ejemplos_k()
    
    def _cargar_ejemplos_k(self):
        """Carga ejemplos k_ desde archivos reales"""
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_feria_acertijos.txt", 
            "actividades_generadas/k_sonnet_supermercado.txt",
            "actividades_generadas/k_piratas.txt",
            "actividades_generadas/k_sonnet7_fabrica_fracciones.txt",
            "actividades_generadas/k_llevadas.txt"  # Agregar este que también existe
        ]
        
        logger.info(f"🔍 Buscando ejemplos k_ en directorio: {self.directorio}")
        
        for archivo in archivos_k:
            ruta_completa = os.path.join(self.directorio, archivo)
            logger.debug(f"Verificando ruta: {ruta_completa}")
            
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
            else:
                logger.warning(f"⚠️ No encontrado: {ruta_completa}")
        
        if not self.ejemplos_k:
            logger.warning("⚠️ No se encontraron ejemplos k_. Usando ejemplo básico.")
            self._crear_ejemplo_fallback()
        else:
            logger.info(f"✅ Cargados {len(self.ejemplos_k)} ejemplos k_: {list(self.ejemplos_k.keys())}")
    
    def _extraer_metadatos(self, contenido: str) -> Dict[str, Any]:
        """Extrae metadatos pedagógicos del ejemplo k_"""
        metadatos = {
            "materia_detectada": "general",
            "modalidad_detectada": "mixta",
            "tipo_actividad": "práctica",
            "estudiantes_mencionados": [],
            "interdependencia": False,
            "materiales_fisicos": []
        }
        
        contenido_lower = contenido.lower()
        
        # Detectar materia
        if any(palabra in contenido_lower for palabra in ["matemática", "número", "fracción", "área", "volumen"]):
            metadatos["materia_detectada"] = "matematicas"
        elif any(palabra in contenido_lower for palabra in ["célula", "ciencia", "biología", "orgánulo"]):
            metadatos["materia_detectada"] = "ciencias"
        elif any(palabra in contenido_lower for palabra in ["cuento", "historia", "narrativa", "lengua"]):
            metadatos["materia_detectada"] = "lengua"
        
        # Detectar modalidad
        if "grupo" in contenido_lower or "equipo" in contenido_lower:
            metadatos["modalidad_detectada"] = "grupal"
        elif "individual" in contenido_lower or "cada uno" in contenido_lower:
            metadatos["modalidad_detectada"] = "individual"
        
        # Detectar estudiantes mencionados
        estudiantes = re.findall(r'(Alex|Elena|Luis|Ana|Sara|Hugo|Emma|María)', contenido, re.IGNORECASE)
        metadatos["estudiantes_mencionados"] = list(set(estudiantes))
        
        # Detectar interdependencia
        if any(palabra in contenido_lower for palabra in ["necesita", "usa", "verifica", "depende", "entre todos"]):
            metadatos["interdependencia"] = True
        
        # Detectar materiales físicos
        materiales = re.findall(r'(regla|papel|bloques|tijeras|pegamento|pinturas|cartón|objetos)', contenido_lower)
        metadatos["materiales_fisicos"] = list(set(materiales))
        
        return metadatos
    
    def _crear_ejemplo_fallback(self):
        """Crea ejemplo básico si no hay ejemplos k_"""
        self.ejemplos_k["k_basico"] = """
Actividad Básica Colaborativa:
- Alex: Organizar materiales en mesa por categorías
- Elena: Medir objetos usando regla y anotar medidas
- Luis: Construir estructura con bloques según medidas de Elena
- Ana: Verificar que medidas de Elena coinciden con construcción de Luis
- Sara: Documentar proceso completo en papel
- Hugo: Preparar presentación de resultados grupales
Interdependencia: Ana necesita medidas de Elena, Luis usa medidas de Elena, Sara documenta trabajo de todos.
        """
        self.metadatos_ejemplos["k_basico"] = {
            "materia_detectada": "general",
            "modalidad_detectada": "grupal", 
            "tipo_actividad": "práctica",
            "estudiantes_mencionados": ["Alex", "Elena", "Luis", "Ana", "Sara", "Hugo"],
            "interdependencia": True,
            "materiales_fisicos": ["regla", "papel", "bloques"]
        }
    
    def seleccionar_ejemplo_estrategico(self, materia: str, tema: str, modalidad: str = "mixta") -> str:
        """Selecciona ejemplo k_ más relevante estratégicamente"""
        mejor_ejemplo = None
        mejor_puntuacion = 0
        
        for nombre, metadatos in self.metadatos_ejemplos.items():
            puntuacion = 0
            
            # Puntuación por materia
            if metadatos["materia_detectada"] == materia.lower():
                puntuacion += 5
            elif metadatos["materia_detectada"] == "general":
                puntuacion += 1
            
            # Puntuación por modalidad
            if metadatos["modalidad_detectada"] == modalidad:
                puntuacion += 3
            elif metadatos["modalidad_detectada"] == "mixta":
                puntuacion += 1
            
            # Puntuación por interdependencia (siempre deseable)
            if metadatos["interdependencia"]:
                puntuacion += 2
            
            # Puntuación por materiales físicos
            if len(metadatos["materiales_fisicos"]) > 2:
                puntuacion += 2
            
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_ejemplo = nombre
        
        ejemplo_seleccionado = mejor_ejemplo or list(self.ejemplos_k.keys())[0]
        logger.info(f"📋 Ejemplo k_ seleccionado: {ejemplo_seleccionado} (puntuación: {mejor_puntuacion})")
        
        return self.ejemplos_k[ejemplo_seleccionado]


class QuantumIntelligentAgentsSystem:
    """Sistema principal con CrewAI + Ollama + PennyLane + Few-shot estratégico"""
    
    def __init__(self, ollama_host: str = "192.168.1.10"):
        self.ollama_host = ollama_host
        self.cargador_ejemplos = CargadorEjemplosK()
        
        # Inicializar optimizador cuántico
        self.quantum_optimizer = QuantumEducationalOptimizer()
        logger.info("🌟 Optimizador cuántico inicializado")
        
        # Configurar LiteLLM para Ollama
        self._configurar_litellm()
        
        # Crear LLMs específicos para cada agente
        self._crear_llms_especificos()
        
        # Crear agentes especializados
        self._crear_agentes()
        
        logger.info("✅ Sistema de Agentes Inteligente con Cuántica inicializado")
    
    def _configurar_litellm(self):
        """Configura LiteLLM usando el patrón EXACTO que funciona"""
        try:
            import litellm
            
            logger.info("🔧 Configurando LiteLLM para Ollama local...")
            
            # Configurar variables específicas para LiteLLM + Ollama (patrón exitoso)
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            logger.info("✅ LiteLLM configurado con patrón exitoso")
        except Exception as e:
            logger.warning(f"⚠️ Advertencia configurando LiteLLM: {e}")
    
    def _crear_llms_especificos(self):
        """Crea LLMs específicos para cada agente usando patrón exitoso"""
        try:
            # Usar el patrón EXACTO que funciona en sistema_agentes_inteligente.py
            modelos = ["qwen3:latest", "qwen2:latest", "mistral:latest"]
            
            # Mapear modelos para LiteLLM (patrón que funciona)
            for modelo in modelos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Crear LLMs con patrón exitoso: ollama/{modelo} + base_url
            logger.info("🔄 Creando LLMs con patrón exitoso:")
            
            self.llm_clima = Ollama(
                model=f"ollama/qwen3:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_estructurador = Ollama(
                model=f"ollama/qwen2:latest", 
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_tareas = Ollama(
                model=f"ollama/mistral:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.llm_repartidor = Ollama(
                model=f"ollama/qwen3:latest",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info("✅ LLMs específicos creados con patrón exitoso")
        except Exception as e:
            logger.error(f"❌ Error creando LLMs: {e}")
            raise
    
    def _crear_agentes(self):
        """Crea los agentes especializados con detector inteligente y validador final"""
        
        # DETECTOR INTELIGENTE CON CONCIENCIA CUÁNTICA
        self.agente_detector = Agent(
            role="Detector Inteligente de Contexto Pedagógico Cuántico",
            goal="Analizar prompts educativos y extraer parámetros para optimización cuántica",
            backstory="""Eres un experto en análisis curricular con conocimiento de optimización cuántica. 
            Identificas materias, temas, modalidades, perfiles estudiantiles y parámetros que pueden ser 
            optimizados cuánticamente para crear prompts educativos más efectivos. Tu análisis alimenta 
            directamente el sistema de optimización cuántica.""",
            llm=self.llm_clima,
            verbose=True,
            allow_delegation=False
        )
        
        # VALIDADOR FINAL CON CRITERIOS CUÁNTICOS
        self.agente_validador = Agent(
            role="Validador de Calidad Pedagógica Cuántica",
            goal="Garantizar que las actividades optimizadas cuánticamente mantienen coherencia pedagógica",
            backstory="""Eres un validador pedagógico que comprende tanto principios educativos tradicionales 
            como los efectos de la optimización cuántica en prompts. Verificas que las mejoras cuánticas 
            se traduzcan en actividades prácticas y efectivas, manteniendo estándares k_ de calidad.""",
            llm=self.llm_estructurador,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTES ESPECIALISTAS MEJORADOS
        self.agente_clima = Agent(
            role="Especialista en Clima Pedagógico Cuántico",
            goal="Determinar climas pedagógicos optimizados usando parámetros cuánticos",
            backstory="""Eres un experto en psicopedagogía que utiliza optimización cuántica para 
            determinar el clima pedagógico óptimo. Analizas los parámetros cuánticos de energía, 
            estructura y colaboración para crear ambientes de aprendizaje perfectamente calibrados.""",
            llm=self.llm_clima,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_estructurador = Agent(
            role="Arquitecto de Experiencias Educativas Cuánticas", 
            goal="Diseñar estructuras educativas usando prompts optimizados cuánticamente",
            backstory="""Eres un diseñador de experiencias educativas que incorpora mejoras cuánticas 
            en la estructura de las actividades. Utilizas prompts optimizados cuánticamente para crear 
            experiencias más equilibradas y adaptadas a los perfiles específicos de estudiantes.""",
            llm=self.llm_estructurador,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_tareas = Agent(
            role="Especialista en Desglose Pedagógico Cuántico",
            goal="Crear tareas específicas usando adaptaciones cuánticas para diferentes perfiles",
            backstory="""Eres un experto en crear tareas educativas que incorporan adaptaciones 
            cuánticas específicas. Utilizas los parámetros optimizados para TEA, TDAH y otros 
            perfiles para crear tareas perfectamente calibradas para cada tipo de estudiante.""",
            llm=self.llm_tareas,
            verbose=True,
            allow_delegation=False
        )
        
        self.agente_repartidor = Agent(
            role="Especialista en Inclusión y Adaptación Cuántica",
            goal="Asignar tareas usando parámetros cuánticos de adaptación personalizada", 
            backstory="""Eres un especialista en educación inclusiva que utiliza optimización cuántica 
            para crear asignaciones de tareas perfectamente adaptadas. Los parámetros cuánticos te 
            permiten calibrar con precisión las adaptaciones para TEA, TDAH, altas capacidades y 
            otros perfiles específicos.""",
            llm=self.llm_repartidor,
            verbose=True,
            allow_delegation=False
        )
        
        # COORDINADOR DE PARALELISMO
        self.agente_coordinador_paralelismo = Agent(
            role="Coordinador de Paralelismo Cuántico",
            goal="Detectar oportunidades de paralelización y coordinar tareas simultáneas optimizadas cuánticamente",
            backstory="""Eres un experto en optimización de procesos educativos que utiliza principios 
            cuánticos para detectar cuando las tareas pueden ejecutarse en paralelo. Analizas las 
            interdependencias entre actividades y coordinas la ejecución simultánea manteniendo 
            coherencia pedagógica.""",
            llm=self.llm_clima,
            verbose=True,
            allow_delegation=False
        )
    
    def generar_actividad_cuantica_desde_prompt(self, prompt_profesor: str) -> QuantumActividadEducativa:
        """Genera actividad con flujo completo por fases + optimización cuántica integrada"""
        
        print("\n🌟 INICIANDO FLUJO COMPLETO CON OPTIMIZACIÓN CUÁNTICA")
        print("="*70)
        
        # TRACKING DE INTERACCIONES HUMANAS
        interacciones_humanas = []
        modelos_utilizados = []
        
        # FASE 0: DETECCIÓN MULTIDIMENSIONAL + ANÁLISIS CUÁNTICO
        print("\n🔍 FASE 0: ANÁLISIS MULTIDIMENSIONAL Y CUÁNTICO...")
        contexto_detectado = self.detectar_contexto_multidimensional(prompt_profesor)
        modelos_utilizados.append({
            "fase": "Detección de contexto",
            "agente": "Detector Inteligente",
            "modelo": "ollama/qwen3:latest",
            "proposito": "Análisis multidimensional del prompt"
        })
        
        # OPTIMIZACIÓN CUÁNTICA (nueva funcionalidad integrada)
        print("\n⚛️ INTEGRACIÓN CUÁNTICA: Optimizando parámetros pedagógicos...")
        contexto_cuantico = self.detectar_contexto_para_cuantica(prompt_profesor)
        prompt_optimizado, parametros_cuanticos, historial = self.optimizar_prompt_cuanticamente(
            prompt_profesor, contexto_cuantico
        )
        
        print(f"\n✨ PROMPT OPTIMIZADO CUÁNTICAMENTE:")
        print("-" * 50)
        print(prompt_optimizado[:300] + "..." if len(prompt_optimizado) > 300 else prompt_optimizado)
        
        # VALIDACIÓN PREVIA: Contexto general y recomendación cuántica
        contexto_aprobado = self._validar_contexto_general_cuantico(contexto_detectado, parametros_cuanticos)
        respuesta_contexto = input(f"🗣️ ¿Continuar con análisis cuántico? (sí/no): ").strip().lower()
        interacciones_humanas.append({
            "fase": "Validación contexto cuántico",
            "pregunta": "¿Continuar con análisis cuántico?",
            "respuesta": respuesta_contexto,
            "prompt_usado": prompt_optimizado if respuesta_contexto in ['s', 'sí', 'si', 'vale', 'ok'] else prompt_profesor
        })
        
        if respuesta_contexto not in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            print("🔄 Usando prompt original y flujo clásico...")
            prompt_optimizado = prompt_profesor
            parametros_cuanticos = {"mensaje": "usuario_prefiere_clasico"}
            historial = []
        
        # FASE 1: OPCIONES DINÁMICAS (con parámetros cuánticos si se aceptaron)
        opciones_decididas = self._fase_opciones_dinamicas_cuantica(contexto_aprobado, parametros_cuanticos)
        modelos_utilizados.append({
            "fase": "Opciones dinámicas",
            "agente": "Detector Inteligente", 
            "modelo": "ollama/qwen3:latest",
            "proposito": "Generar opciones específicas por contexto"
        })
        
        # VALIDACIÓN 1: Después de decidir opciones específicas
        if not self._validacion_humana_intermedia("opciones específicas", opciones_decididas):
            opciones_decididas = self._refinar_opciones_cuanticas(contexto_aprobado, opciones_decididas, interacciones_humanas)
        
        # FASE 2: ESTRUCTURA + ORGANIZACIÓN (con prompt optimizado)
        estructura_completa = self._fase_estructura_libre_cuantica(opciones_decididas, contexto_detectado, prompt_optimizado)
        modelos_utilizados.append({
            "fase": "Estructuración",
            "agente": "Arquitecto de Experiencias Educativas Cuánticas",
            "modelo": "ollama/qwen2:latest", 
            "proposito": "Crear estructura usando prompt optimizado cuánticamente"
        })
        
        # VALIDACIÓN 2: Después de estructura completa
        if not self._validacion_humana_intermedia("estructura y organización", estructura_completa):
            estructura_completa = self._refinar_estructura_cuantica(contexto_detectado, estructura_completa, interacciones_humanas)
        
        # DETECCIÓN DE PARALELISMO (restaurada)
        if self._detectar_oportunidades_paralelismo_natural(str(estructura_completa.get("estructura_completa", ""))):
            print(f"\n🔄 Detecté oportunidades de trabajo simultáneo entre estudiantes.")
            optimizar_paralelismo = input(f"¿Quieres que coordine el trabajo paralelo? (sí/no): ").strip().lower()
            interacciones_humanas.append({
                "fase": "Optimización paralelismo",
                "pregunta": "¿Coordinar trabajo paralelo?",
                "respuesta": optimizar_paralelismo
            })
            
            if optimizar_paralelismo in ['s', 'sí', 'si', 'vale', 'ok']:
                print(f"\n⚡ Optimizando coordinación paralela...")
                estructura_completa = self._optimizar_coordinacion_paralela_cuantica(estructura_completa, contexto_detectado)
                modelos_utilizados.append({
                    "fase": "Optimización paralelismo",
                    "agente": "Coordinador de Trabajo Paralelo",
                    "modelo": "ollama/qwen2:latest",
                    "proposito": "Optimizar trabajo simultáneo entre estudiantes"
                })
        
        # FASE 3: ACTIVIDAD FINAL CON ITERACIÓN (restaurada)
        actividad_cuantica = self._crear_actividad_final_iterativa_cuantica(
            estructura_completa, contexto_detectado, interacciones_humanas, modelos_utilizados,
            parametros_cuanticos, prompt_optimizado, historial, prompt_profesor
        )
        
        return actividad_cuantica
    
    def detectar_contexto_multidimensional(self, prompt_profesor: str) -> Dict[str, Any]:
        """Detector libre que analiza múltiples dimensiones y genera opciones dinámicas"""
        
        tarea_deteccion = Task(
            description=f"""
Analiza este prompt educativo desde múltiples dimensiones y genera opciones contextuales:

PROMPT DEL PROFESOR: "{prompt_profesor}"

ANÁLISIS MULTIDIMENSIONAL:
1. CONTENIDO: ¿Qué materia, tema, nivel de complejidad conceptual?
2. NARRATIVA: ¿Qué nivel narrativo necesita? (historia envolvente, contexto simple, sin narrativa)
3. METODOLOGÍA: ¿Qué tipo de actividades? (talleres, debates, experimentos, creación, etc.)
4. ESTRUCTURA TEMPORAL: ¿Cómo organizar el tiempo? (sesión única, varios días, por bloques)
5. MODALIDAD SOCIAL: ¿Cómo trabajar? (individual, parejas, grupos pequeños, clase completa, mixto)
6. PRODUCTOS: ¿Qué debe generar? (contenido real como guiones, organizaciones, ambos)
7. ADAPTACIONES: ¿Qué necesidades específicas detectas?

GENERA OPCIONES DINÁMICAS específicas para ESTA actividad:
Basándote en el análisis, propón 2-3 preguntas clave que el profesor necesita decidir.

FORMATO DE RESPUESTA:
```json
{{
    "contexto_base": {{
        "materia": "detectado",
        "tema": "detectado",
        "complejidad_conceptual": "alta/media/baja"
    }},
    "dimensiones": {{
        "narrativa": {{"nivel": "alta/media/baja/ninguna", "tipo": "descripción"}},
        "metodologia": {{"principal": "tipo_principal", "secundarias": ["tipo1", "tipo2"]}},
        "estructura_temporal": {{"tipo": "sesion_unica/varios_dias/bloques", "flexibilidad": "alta/media/baja"}},
        "modalidad_social": {{"principal": "grupal/individual/mixta", "variaciones": ["detalles"]}},
        "productos_esperados": ["producto1", "producto2"],
        "adaptaciones_detectadas": ["necesidad1", "necesidad2"]
    }},
    "opciones_dinamicas": [
        "Pregunta específica 1 para esta actividad",
        "Pregunta específica 2 para esta actividad",
        "Pregunta específica 3 si es necesaria"
    ],
    "recomendacion_ia": "Mi recomendación basada en el análisis completo"
}}
```

Genera opciones ESPECÍFICAS para este contexto, no preguntas genéricas.
            """,
            agent=self.agente_detector,
            expected_output="JSON con análisis multidimensional y opciones dinámicas"
        )
        
        crew_detector = Crew(
            agents=[self.agente_detector],
            tasks=[tarea_deteccion],
            process=Process.sequential,
            verbose=True
        )
        
        contexto_detectado = crew_detector.kickoff()
        logger.info(f"🔍 Contexto detectado: {str(contexto_detectado)[:200]}...")
        
        # Convertir CrewOutput a string para procesamiento
        if hasattr(contexto_detectado, 'raw'):
            return str(contexto_detectado.raw)
        else:
            return str(contexto_detectado)
    
    def detectar_contexto_para_cuantica(self, prompt_profesor: str) -> Dict[str, Any]:
        """Detecta contexto específicamente para alimentar la optimización cuántica"""
        
        tarea_deteccion = Task(
            description=f"""
Analiza este prompt educativo para extraer parámetros que serán optimizados cuánticamente:

PROMPT DEL PROFESOR: "{prompt_profesor}"

EXTRAE PARÁMETROS CUÁNTICOS:
1. MATERIA CURRICULAR: ¿Qué área? (mathematics/matematicas, language/lengua, science/ciencias, arts/arte, physical_education)
2. PERFILES ESTUDIANTILES: ¿Qué necesidades especiales detectas?
   - TEA (Trastorno Espectro Autista): ¿Hay indicios? (0.0 a 1.0)
   - TDAH (Déficit Atención): ¿Hay indicios? (0.0 a 1.0)
   - Altas Capacidades: ¿Se menciona? (0.0 a 1.0)
3. AMBIENTE DESEADO:
   - Energía: ¿Alto/medio/bajo dinamismo? (0.0 a 1.0)
   - Estructura: ¿Muy estructurado/flexible? (0.0 a 1.0)  
   - Colaboración: ¿Individual/grupal/mixto? (0.0 a 1.0)

FORMATO DE RESPUESTA:
```json
{{
    "area_curricular": "mathematics|language|science|arts|physical_education|matematicas|lengua|ciencias|arte",
    "perfiles_estudiantiles": {{
        "tea": 0.0,
        "tdah": 0.0,
        "altas_capacidades": 0.0
    }},
    "ambiente_deseado": {{
        "energia": 0.5,
        "estructura": 0.5,
        "colaboracion": 0.5
    }},
    "tema_especifico": "descripción breve del tema",
    "duracion_estimada": "estimación en minutos",
    "contexto_adicional": "cualquier información relevante"
}}
```

IMPORTANTE: Los valores deben ser números entre 0.0 y 1.0 para la optimización cuántica.
            """,
            agent=self.agente_detector,
            expected_output="JSON con parámetros para optimización cuántica"
        )
        
        crew_detector = Crew(
            agents=[self.agente_detector],
            tasks=[tarea_deteccion],
            process=Process.sequential,
            verbose=True
        )
        
        resultado = crew_detector.kickoff()
        logger.info(f"🔍 Contexto detectado para cuántica: {str(resultado)[:200]}...")
        
        # Parsear resultado JSON
        try:
            import json
            import re
            
            resultado_str = str(resultado).encode('utf-8', errors='ignore').decode('utf-8')
            json_match = re.search(r'```json\s*({.*?})\s*```', resultado_str, re.DOTALL | re.MULTILINE)
            
            if json_match:
                contexto = json.loads(json_match.group(1))
                logger.info("✅ Contexto JSON parseado correctamente")
                return contexto
            else:
                logger.warning("⚠️ No se encontró JSON válido, usando valores por defecto")
                return self._contexto_por_defecto()
                
        except Exception as e:
            logger.error(f"❌ Error parseando contexto: {e}")
            return self._contexto_por_defecto()
    
    def _contexto_por_defecto(self) -> Dict[str, Any]:
        """Contexto por defecto para casos de error"""
        return {
            "area_curricular": "mathematics",
            "perfiles_estudiantiles": {"tea": 0.1, "tdah": 0.1, "altas_capacidades": 0.0},
            "ambiente_deseado": {"energia": 0.5, "estructura": 0.5, "colaboracion": 0.7},
            "tema_especifico": "actividad educativa",
            "duracion_estimada": "45 minutos",
            "contexto_adicional": "contexto no detectado automáticamente"
        }
    
    def optimizar_prompt_cuanticamente(self, prompt_original: str, contexto: Dict) -> tuple:
        """Optimiza el prompt usando el sistema cuántico"""
        
        logger.info("⚛️ Iniciando optimización cuántica del prompt...")
        
        # Extraer parámetros del contexto
        area_curricular = contexto.get("area_curricular", "mathematics")
        perfiles = contexto.get("perfiles_estudiantiles", {})
        
        # Usar el optimizador cuántico
        try:
            prompt_optimizado, parametros, historial = self.quantum_optimizer.quantum_enhanced_educational_prompt(
                prompt_original, area_curricular, perfiles
            )
            
            logger.info("✅ Optimización cuántica completada")
            return prompt_optimizado, parametros, historial
            
        except Exception as e:
            logger.error(f"❌ Error en optimización cuántica: {e}")
            # Fallback: devolver prompt original con metadatos de error
            return prompt_original, {"error": str(e)}, []
    
    def generar_con_agentes(self, prompt_optimizado: str, contexto: Dict) -> Dict[str, Any]:
        """Genera actividad usando los agentes con el prompt optimizado cuánticamente"""
        
        # Usar el agente estructurador para crear la actividad completa
        tarea_generacion = Task(
            description=f"""
Usando este PROMPT OPTIMIZADO CUÁNTICAMENTE, crea una actividad educativa completa para fracciones:

PROMPT OPTIMIZADO: {prompt_optimizado}

CONTEXTO ORIGINAL: {contexto}

ESTRUCTURA REQUERIDA:
**TÍTULO:** [Título específico de la actividad]

**OBJETIVOS:**
- [Objetivo 1]
- [Objetivo 2]

**MATERIALES:**
- [Material 1]
- [Material 2]
- [etc.]

**DURACIÓN:** [X minutos]

**DESARROLLO DE LA ACTIVIDAD:**
[Descripción detallada paso a paso]

**TAREAS POR ESTUDIANTE:**
- ALEX M. (001): [tarea específica]
- MARÍA L. (002): [tarea específica]  
- ELENA R. (003) [TEA]: [tarea adaptada con apoyo visual]
- LUIS T. (004) [TDAH]: [tarea kinestésica]
- ANA V. (005) [Altas capacidades]: [tarea con reto adicional]
- SARA M. (006): [tarea específica]
- EMMA K. (007): [tarea específica]
- HUGO P. (008): [tarea específica]

**EVALUACIÓN:**
[Cómo evaluar la actividad]

IMPORTANTE: Usa EXACTAMENTE el formato anterior con los nombres y códigos especificados.
            """,
            agent=self.agente_estructurador,
            expected_output="Actividad educativa completa estructurada según formato requerido"
        )
        
        crew_generacion = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_generacion],
            process=Process.sequential,
            verbose=True
        )
        
        actividad_resultado = crew_generacion.kickoff()
        
        # Procesar el resultado con mejor extracción
        contenido_str = str(actividad_resultado)
        
        resultado_procesado = {
            "titulo": self._extraer_titulo(contenido_str),
            "materia": contexto.get("area_curricular", "matematicas"),
            "tema": contexto.get("tema_especifico", "fracciones"),
            "clima": "cuántico-optimizado",
            "modalidad_trabajo": "adaptativa-cuántica", 
            "contenido_completo": contenido_str,
            "tareas_estudiantes": self._extraer_tareas_mejorado(contenido_str),
            "materiales": self._extraer_materiales_mejorado(contenido_str),
            "duracion": self._extraer_duracion(contenido_str),
            "fases": self._extraer_fases(contenido_str)
        }
        
        return resultado_procesado
    
    def _extraer_titulo(self, contenido: str) -> str:
        """Extrae el título de la actividad"""
        import re
        match = re.search(r'\*\*TÍTULO:\*\*\s*([^\n]+)', contenido, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: buscar líneas que parezcan títulos
        lines = contenido.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*') and len(line) < 80:
                if any(word in line.lower() for word in ['actividad', 'fracciones', 'matemáticas']):
                    return line
        
        return "Actividad de Fracciones Optimizada Cuánticamente"
    
    def _extraer_tareas_mejorado(self, contenido: str) -> Dict[str, str]:
        """Extrae tareas específicas con mejor parsing"""
        import re
        
        tareas = {}
        
        # Buscar sección de tareas por estudiante
        tareas_section = re.search(r'\*\*TAREAS POR ESTUDIANTE:\*\*(.*?)(?:\*\*|$)', contenido, re.DOTALL | re.IGNORECASE)
        
        if tareas_section:
            tareas_text = tareas_section.group(1)
            
            # Buscar patrones específicos con códigos
            patterns = [
                r'ALEX M\.\s*\(001\):\s*([^\n]+)',
                r'MARÍA L\.\s*\(002\):\s*([^\n]+)',
                r'ELENA R\.\s*\(003\).*?:\s*([^\n]+)',
                r'LUIS T\.\s*\(004\).*?:\s*([^\n]+)',
                r'ANA V\.\s*\(005\).*?:\s*([^\n]+)',
                r'SARA M\.\s*\(006\):\s*([^\n]+)',
                r'EMMA K\.\s*\(007\):\s*([^\n]+)',
                r'HUGO P\.\s*\(008\):\s*([^\n]+)'
            ]
            
            codigos = ["001", "002", "003", "004", "005", "006", "007", "008"]
            
            for i, pattern in enumerate(patterns):
                match = re.search(pattern, tareas_text, re.IGNORECASE)
                if match:
                    tareas[codigos[i]] = match.group(1).strip()
        
        # Si no encontramos suficientes tareas, buscar patrones alternativos
        if len(tareas) < 4:
            # Buscar líneas que empiecen con "-" y contengan nombres
            lines = contenido.split('\n')
            nombres_codigos = {
                'alex': '001', 'maría': '002', 'maria': '002', 'elena': '003',
                'luis': '004', 'ana': '005', 'sara': '006', 'emma': '007', 'hugo': '008'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    for nombre, codigo in nombres_codigos.items():
                        if nombre in line.lower():
                            # Extraer la tarea después del ":"
                            if ':' in line:
                                tarea = line.split(':', 1)[1].strip()
                                if tarea and len(tarea) > 10:  # Filtrar tareas muy cortas
                                    tareas[codigo] = tarea
                            break
        
        # Fallback con tareas específicas de fracciones
        if len(tareas) < 8:
            fallback_tareas = {
                "001": "Recortar círculos de papel en mitades y cuartos",
                "002": "Explicar oralmente qué representa cada fracción",
                "003": "Usar apoyo visual: dibujar fracciones en papel cuadriculado",
                "004": "Manipular bloques físicos para construir fracciones",
                "005": "Resolver problemas avanzados: convertir fracciones a decimales",
                "006": "Ayudar a compañeros con dificultades en fracciones",
                "007": "Documentar el proceso en una tabla de equivalencias",
                "008": "Presentar los resultados finales al grupo"
            }
            
            for codigo in ["001", "002", "003", "004", "005", "006", "007", "008"]:
                if codigo not in tareas:
                    tareas[codigo] = fallback_tareas[codigo]
        
        return tareas
    
    def _extraer_materiales_mejorado(self, contenido: str) -> List[str]:
        """Extrae materiales con mejor parsing"""
        import re
        
        materiales = []
        
        # Buscar sección de materiales
        materiales_section = re.search(r'\*\*MATERIALES:\*\*(.*?)(?:\*\*|$)', contenido, re.DOTALL | re.IGNORECASE)
        
        if materiales_section:
            materiales_text = materiales_section.group(1)
            lines = materiales_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    material = line[1:].strip()
                    if material and len(material) > 2:
                        materiales.append(material)
        
        # Si no encontramos materiales en formato estructurado, buscar palabras clave
        if not materiales:
            contenido_lower = contenido.lower()
            materiales_detectados = []
            
            if "papel" in contenido_lower:
                materiales_detectados.append("Papel")
            if "círculo" in contenido_lower or "figuras" in contenido_lower:
                materiales_detectados.append("Figuras geométricas de papel")
            if "bloque" in contenido_lower or "manipulativ" in contenido_lower:
                materiales_detectados.append("Bloques manipulativos")
            if "lápic" in contenido_lower or "lapiz" in contenido_lower:
                materiales_detectados.append("Lápices")
            if "cuadrícula" in contenido_lower or "cuaderno" in contenido_lower:
                materiales_detectados.append("Papel cuadriculado")
            if "tijera" in contenido_lower:
                materiales_detectados.append("Tijeras")
            if "pegamento" in contenido_lower:
                materiales_detectados.append("Pegamento")
            
            materiales = materiales_detectados if materiales_detectados else ["Papel", "Lápices", "Bloques de fracciones"]
        
        return materiales
    
    def _extraer_duracion(self, contenido: str) -> str:
        """Extrae la duración de la actividad"""
        import re
        
        match = re.search(r'\*\*DURACIÓN:\*\*\s*([^\n]+)', contenido, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Buscar patrones de tiempo en el texto
        time_patterns = [
            r'(\d+)\s*minutos',
            r'(\d+)\s*min',
            r'(\d+)-(\d+)\s*minutos'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, contenido, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "30-45 minutos"
    
    def _extraer_fases(self, contenido: str) -> List[str]:
        """Extrae las fases de la actividad"""
        import re
        
        fases = []
        
        # Buscar sección de desarrollo
        desarrollo_section = re.search(r'\*\*DESARROLLO.*?:\*\*(.*?)(?:\*\*|$)', contenido, re.DOTALL | re.IGNORECASE)
        
        if desarrollo_section:
            desarrollo_text = desarrollo_section.group(1)
            
            # Buscar fases numeradas o con bullets
            phase_patterns = [
                r'(\d+\.\s*[^\n]+)',
                r'(Fase\s*\d+[^\n]*)',
                r'(-\s*[^\n]{20,})'  # Líneas con guiones que sean suficientemente largas
            ]
            
            for pattern in phase_patterns:
                matches = re.findall(pattern, desarrollo_text, re.IGNORECASE)
                for match in matches:
                    fase = match.strip()
                    if len(fase) > 15:  # Filtrar fases muy cortas
                        fases.append(fase)
                
                if len(fases) >= 3:  # Suficientes fases encontradas
                    break
        
        # Fallback: fases genéricas pero específicas para fracciones
        if len(fases) < 3:
            fases = [
                "Introducción y explicación de fracciones (10 min)",
                "Trabajo manipulativo con materiales (20 min)",
                "Presentación y evaluación (10 min)"
            ]
        
        return fases[:5]  # Máximo 5 fases
    
    # =================== MÉTODOS RESTAURADOS DEL SISTEMA ORIGINAL ===================
    
    def _validar_contexto_general_cuantico(self, contexto_detectado, parametros_cuanticos) -> Dict[str, Any]:
        """Validación previa: mostrar recomendación general con parámetros cuánticos"""
        
        print(f"\n✅ VALIDACIÓN PREVIA: CONTEXTO GENERAL + CUÁNTICO")
        print("=" * 60)
        
        # Extraer análisis del detector (igual que en sistema original)
        try:
            contexto_str = str(contexto_detectado).encode('utf-8', errors='ignore').decode('utf-8')
            json_match = re.search(r'```json\s*({.*?})\s*```', contexto_str, re.DOTALL | re.MULTILINE)
            
            if json_match:
                analisis = json.loads(json_match.group(1))
            else:
                print(f"📝 Contexto recibido: {contexto_str[:500]}...")
                analisis = {
                    "contexto_base": {"materia": "detectado", "tema": "detectado"},
                    "recomendacion_ia": "Basado en tu descripción, recomiendo una actividad práctica."
                }
                
        except Exception as e:
            print(f"⚠️ Error procesando contexto: {e}")
            analisis = {
                "contexto_base": {"materia": "error", "tema": "error"},
                "recomendacion_ia": "Hubo un error analizando tu descripción."
            }
        
        # Mostrar contexto detectado
        print(f"\n📋 CONTEXTO DETECTADO:")
        if "contexto_base" in analisis:
            base = analisis["contexto_base"]
            print(f"   📚 Materia: {base.get('materia', 'no detectado')}")
            print(f"   🎯 Tema: {base.get('tema', 'no detectado')}")
            print(f"   📈 Complejidad: {base.get('complejidad_conceptual', 'no detectado')}")
        
        # Mostrar parámetros cuánticos si están disponibles
        if isinstance(parametros_cuanticos, dict) and "ambiente" in parametros_cuanticos:
            print(f"\n⚛️ PARÁMETROS CUÁNTICOS OPTIMIZADOS:")
            ambiente = parametros_cuanticos["ambiente"]
            print(f"   🔋 Energía: {ambiente.get('energia', 0):.2f}")
            print(f"   🏗️ Estructura: {ambiente.get('estructura', 0):.2f}")
            print(f"   🤝 Colaboración: {ambiente.get('colaboracion', 0):.2f}")
        
        # Mostrar recomendación de la IA
        if "recomendacion_ia" in analisis:
            print(f"\n🤖 RECOMENDACIÓN GENERAL: {analisis['recomendacion_ia']}")
        
        return analisis
    
    def _fase_opciones_dinamicas_cuantica(self, contexto_aprobado, parametros_cuanticos) -> Dict[str, Any]:
        """Fase 1: Preguntas específicas sobre actividad con información cuántica"""
        
        print(f"\n🧠 FASE 1: OPCIONES ESPECÍFICAS (CON CUÁNTICA)")
        print("-" * 50)
        
        # Extraer análisis del detector
        try:
            contexto_str = str(contexto_aprobado)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', contexto_str, re.DOTALL | re.MULTILINE)
            if json_match:
                analisis = json.loads(json_match.group(1))
            else:
                print(f"📝 Contexto recibido: {contexto_str[:500]}...")
                analisis = {
                    "contexto_base": {"materia": "detectado", "tema": "detectado"},
                    "opciones_dinamicas": ["¿Qué tipo de actividad prefieres?"],
                    "recomendacion_ia": "Basado en tu descripción, recomiendo una actividad práctica."
                }
                
        except Exception as e:
            print(f"⚠️ Error procesando contexto: {e}")
            analisis = {
                "contexto_base": {"materia": "error", "tema": "error"},
                "opciones_dinamicas": ["¿Cómo te gustaría enfocar esta actividad?"],
                "recomendacion_ia": "Hubo un error analizando tu descripción, pero puedo ayudarte."
            }
        
        print(f"\n🎯 Opciones específicas para tu actividad:")
        
        # Hacer preguntas dinámicas
        decisiones = {}
        opciones_dinamicas = analisis.get("opciones_dinamicas", [])
        
        for i, pregunta in enumerate(opciones_dinamicas, 1):
            print(f"\n🤔 PREGUNTA {i}: {pregunta}")
            respuesta = input(f"🗣️ Tu respuesta: ").strip()
            decisiones[f"decision_{i}"] = respuesta
        
        # Si no hay opciones dinámicas, hacer una pregunta genérica
        if not opciones_dinamicas:
            print(f"\n🤔 ¿Cómo te gustaría enfocar esta actividad?")
            respuesta = input(f"🗣️ Tu respuesta: ").strip()
            decisiones["enfoque_general"] = respuesta
        
        return {
            "analisis_detector": analisis,
            "decisiones_profesor": decisiones,
            "parametros_cuanticos": parametros_cuanticos
        }
    
    def _validacion_humana_intermedia(self, fase: str, contenido: Any) -> bool:
        """Validación humana intermedia más natural"""
        
        print(f"\n✅ VALIDACIÓN: {fase.upper()}")
        print("-" * 40)
        print(f"¿Te parece bien el enfoque hasta ahora?")
        
        respuesta = input(f"🗣️ (sí/no/cambiar): ").strip().lower()
        
        if respuesta in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            return True
        elif respuesta in ['no', 'cambiar', 'modificar']:
            return False
        else:
            print("⚠️ No entendí tu respuesta, asumiré que está bien.")
            return True
    
    def _refinar_opciones_cuanticas(self, contexto_original: Dict, opciones_actuales: Dict, interacciones_humanas: List) -> Dict:
        """Refina opciones basándose en feedback del profesor con tracking"""
        
        print(f"\n🔄 REFINANDO OPCIONES...")
        feedback = input(f"🗣️ ¿Qué te gustaría cambiar?: ").strip()
        
        # Registrar interacción
        interacciones_humanas.append({
            "fase": "Refinamiento opciones",
            "pregunta": "¿Qué te gustaría cambiar?",
            "respuesta": feedback
        })
        
        # Re-analizar con el feedback
        contexto_refinado = self.detectar_contexto_multidimensional(
            f"Contexto original: {contexto_original}\nFeedback del profesor: {feedback}"
        )
        
        # Aplicar feedback directamente, no volver a preguntar
        return {
            "analisis_detector": contexto_refinado,
            "decisiones_profesor": {
                "feedback_aplicado": feedback,
                "contexto_refinado": "El profesor quiere cambiar el enfoque según su feedback"
            },
            "parametros_cuanticos": opciones_actuales.get("parametros_cuanticos", {})
        }
    
    def _fase_estructura_libre_cuantica(self, opciones_decididas: Dict, contexto_detectado: Dict, prompt_optimizado: str) -> Dict[str, Any]:
        """Fase 2: Genera estructura completa basada en decisiones del profesor con prompt cuántico"""
        
        print(f"\n🏠 FASE 2: CREANDO ESTRUCTURA COMPLETA (CON CUÁNTICA)")
        print("-" * 50)
        
        # Crear prompt inteligente basado en las decisiones y optimización cuántica
        decisiones_texto = "\n".join([f"- {k}: {v}" for k, v in opciones_decididas.get("decisiones_profesor", {}).items()])
        analisis_texto = str(opciones_decididas.get("analisis_detector", {}))
        
        tarea_estructura = Task(
            description=f"""
Crea una estructura completa para la actividad usando PROMPT OPTIMIZADO CUÁNTICAMENTE:

PROMPT OPTIMIZADO CUÁNTICAMENTE:
{prompt_optimizado}

DECISIONES DEL PROFESOR:
{decisiones_texto}

ANÁLISIS ORIGINAL:
{analisis_texto}

CREA:
1. Si el profesor pide un GUIÓN → genera el guión teatral completo
2. Si pide ORGANIZACIÓN → estructura por días/grupos como "Lunes: X, Y, Z hacen A mientras P, Q hacen B"
3. Si pide AMBOS → guión + organización

IMPORTANTE:
- Genera CONTENIDO REAL, no solo descripciones
- Si es teatro → diálogos completos entre personajes
- Si es organización → reparto práctico por días y grupos
- Adapta para Elena (TEA), Luis (TDAH), Ana (altas capacidades), etc.
- USA las mejoras cuánticas del prompt optimizado

FORMATO:
- Título atractivo
- Duración realista
- Materiales específicos
- Contenido/Guión si se pide
- Organización temporal si se pide
- Adaptaciones incluidas naturalmente
            """,
            agent=self.agente_estructurador,
            expected_output="Estructura completa con contenido real generado usando optimización cuántica"
        )
        
        crew_estructura = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_estructura],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_resultado = crew_estructura.kickoff()
        
        print(f"\n🏠 ESTRUCTURA GENERADA CON CUÁNTICA:")
        print(str(estructura_resultado))
        
        # Obtener ejemplo_k si es necesario para metadatos
        ejemplo_k_usado = "cuantico_optimizado"
        
        return {
            "estructura_completa": estructura_resultado,
            "opciones_base": opciones_decididas,
            "ejemplo_k_usado": ejemplo_k_usado,
            "prompt_cuantico_usado": prompt_optimizado
        }
    
    def _refinar_estructura_cuantica(self, contexto_original: Dict, estructura_actual: Dict, interacciones_humanas: List) -> Dict:
        """Refina estructura basándose en feedback del profesor con tracking"""
        
        print(f"\n🔄 REFINANDO ESTRUCTURA...")
        feedback = input(f"🗣️ ¿Qué te gustaría cambiar en la estructura?: ").strip()
        
        # Registrar interacción
        interacciones_humanas.append({
            "fase": "Refinamiento estructura",
            "pregunta": "¿Qué te gustaría cambiar en la estructura?",
            "respuesta": feedback
        })
        
        # Crear tarea de refinamiento
        tarea_refinamiento = Task(
            description=f"""
ESTRUCTURA ACTUAL:
{estructura_actual.get('estructura_completa', '')}

FEEDBACK DEL PROFESOR:
"{feedback}"

REFINA la estructura según el feedback:
- Mantén lo que funciona
- Cambia lo que el profesor pide
- Genera contenido real si se solicita
- Adapta organización si es necesario
- Mantén las optimizaciones cuánticas si están presentes
            """,
            agent=self.agente_estructurador,
            expected_output="Estructura refinada según feedback del profesor"
        )
        
        crew_refinamiento = Crew(
            agents=[self.agente_estructurador],
            tasks=[tarea_refinamiento],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_refinada = crew_refinamiento.kickoff()
        
        return {
            "estructura_completa": estructura_refinada,
            "opciones_base": estructura_actual.get("opciones_base", {}),
            "refinado": True
        }
    
    def _detectar_oportunidades_paralelismo_natural(self, contenido_estructura: str) -> bool:
        """Usa IA para detectar automáticamente oportunidades naturales de trabajo paralelo"""
        
        tarea_deteccion_paralelismo = Task(
            description=f"""
Analiza esta estructura educativa para detectar si tiene potencial NATURAL para trabajo paralelo/simultáneo.

ESTRUCTURA A ANALIZAR:
{contenido_estructura}

CRITERIOS DE EVALUACIÓN:
1. **TAREAS DIVISIBLES**: ¿Hay tareas que naturalmente se pueden dividir entre grupos?
2. **TRABAJO SIMULTÁNEO**: ¿Pueden varios estudiantes/grupos trabajar al mismo tiempo en diferentes aspectos?
3. **CONSTRUCCIÓN COLABORATIVA**: ¿Se está construyendo algo que permite trabajo en paralelo?
4. **ROLES COMPLEMENTARIOS**: ¿Hay roles diferentes que pueden ejecutarse simultáneamente?
5. **ESTACIONES/ÁREAS**: ¿La actividad sugiere diferentes "lugares" o "momentos" de trabajo?

RESPONDE SOLO:
TIENE_POTENCIAL_PARALELO: SÍ/NO
JUSTIFICACIÓN: [1-2 líneas explicando por qué]
            """,
            agent=self.agente_coordinador_paralelismo,
            expected_output="Análisis de potencial paralelo con justificación"
        )
        
        crew_deteccion = Crew(
            agents=[self.agente_coordinador_paralelismo],
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
            return tiene_potencial
            
        except Exception as e:
            logger.warning(f"⚠️ Error en detección IA de paralelismo: {e}")
            
            # Fallback: detección básica por palabras clave
            indicadores_basicos = ["grupo", "equipo", "construir", "crear", "diseñar", "investigar"]
            tiene_indicadores = sum(1 for ind in indicadores_basicos if ind in contenido_estructura.lower()) >= 2
            
            logger.info(f"🔄 Fallback: detección básica → {tiene_indicadores}")
            return tiene_indicadores
    
    def _optimizar_coordinacion_paralela_cuantica(self, estructura_original, contexto_analisis: str):
        """Optimiza la estructura para incluir coordinación paralela real y adaptativa con cuántica"""
        
        # Primero, obtener el ejemplo k_ de la fábrica de fracciones como referencia de paralelismo
        ejemplo_k_paralelo = self.cargador_ejemplos.ejemplos_k.get('k_sonnet7_fabrica_fracciones', 'Ejemplo no disponible')
        
        tarea_optimizacion = Task(
            description=f"""
Transforma esta actividad educativa para incluir TRABAJO PARALELO AUTÉNTICO usando optimización cuántica.

ESTRUCTURA ORIGINAL:
{estructura_original}

CONTEXTO Y PREFERENCIAS DEL PROFESOR:
{contexto_analisis}

REFERENCIA DE PARALELISMO EXITOSO:
{ejemplo_k_paralelo[:800]}...

PRINCIPIOS DE OPTIMIZACIÓN CUÁNTICA:
1. **DETECTA DIVISIONES NATURALES**: ¿Qué aspectos de la actividad pueden separarse lógicamente?
2. **IDENTIFICA CONSTRUCCIÓN COLABORATIVA**: ¿Se está creando algo que permite trabajo simultáneo?
3. **RESPETA EL FLUJO ORIGINAL**: No cambies la esencia de la actividad, solo organizala mejor
4. **CREA CONVERGENCIA**: Los trabajos paralelos deben unirse en un resultado integrado
5. **APLICA OPTIMIZACIÓN CUÁNTICA**: Usa los parámetros cuánticos para calibrar la colaboración

ADAPTACIONES AUTOMÁTICAS POR ESTUDIANTE (CUÁNTICAS):
- Elena (TEA): Estación visual con instrucciones paso a paso
- Luis (TDAH): Estación kinestésica con cambios frecuentes
- Ana (altas capacidades): Rol de coordinación/supervisión entre estaciones
- Resto: Distribución equilibrada según habilidades

=== ACTIVIDAD OPTIMIZADA CON PARALELISMO CUÁNTICO ===
            """,
            agent=self.agente_coordinador_paralelismo,
            expected_output="Estructura educativa con paralelismo natural cuántico"
        )
        
        crew_optimizacion = Crew(
            agents=[self.agente_coordinador_paralelismo],
            tasks=[tarea_optimizacion],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            estructura_optimizada = crew_optimizacion.kickoff()
            return estructura_optimizada
        except Exception as e:
            logger.error(f"Error optimizando paralelismo cuántico: {e}")
            print(f"⚠️ No pude optimizar el paralelismo, mantengo estructura original")
            return estructura_original
    
    def _crear_actividad_final_iterativa_cuantica(self, estructura_completa: Dict, contexto_detectado: Dict, 
                                                interacciones_humanas: List, modelos_utilizados: List,
                                                parametros_cuanticos: Dict, prompt_optimizado: str, 
                                                historial: List, prompt_profesor: str):
        """Fase 3: Crea actividad final con iteración hasta que el profesor esté satisfecho + tracking completo"""
        
        print(f"\n✨ FASE 3: CREANDO ACTIVIDAD FINAL (CON ITERACIÓN)")
        print("-" * 50)
        
        # Extraer contexto real para la actividad final
        try:
            # Buscar contexto real en los datos pasados
            if isinstance(contexto_detectado, dict):
                ctx_base = contexto_detectado.get("contexto_base", {})
                ctx_dims = contexto_detectado.get("dimensiones", {})
            else:
                # Intentar extraer de string si es necesario
                import json, re
                contexto_str = str(contexto_detectado)
                json_match = re.search(r'```json\s*({.*?})\s*```', contexto_str, re.DOTALL)
                if json_match:
                    ctx_data = json.loads(json_match.group(1))
                    ctx_base = ctx_data.get("contexto_base", {})
                    ctx_dims = ctx_data.get("dimensiones", {})
                else:
                    ctx_base = {"materia": "detectado", "tema": "detectado"}
                    ctx_dims = {"narrativa": {"nivel": "detectado"}}
        except:
            ctx_base = {"materia": "detectado", "tema": "detectado"}
            ctx_dims = {"narrativa": {"nivel": "detectado"}}
        
        # Crear actividad con tracking completo
        actividad = QuantumActividadEducativa(
            id=f"quantum_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad Cuántica: {ctx_base.get('tema', 'Tema Detectado').title()}",
            materia=ctx_base.get("materia", "interdisciplinar"),
            tema=ctx_base.get("tema", "proyecto colaborativo cuántico"),
            clima=ctx_dims.get("narrativa", {}).get("nivel", "cuántico-optimizado"),
            modalidad_trabajo=ctx_dims.get("modalidad_social", {}).get("principal", "cuántica-adaptativa"),
            contenido_completo=str(estructura_completa.get("estructura_completa", "")),
            tareas_estudiantes=self._extraer_tareas_mejorado(str(estructura_completa.get("estructura_completa", ""))),
            materiales=self._extraer_materiales_mejorado(str(estructura_completa.get("estructura_completa", ""))),
            duracion=self._extraer_duracion(str(estructura_completa.get("estructura_completa", ""))),
            fases=self._extraer_fases(str(estructura_completa.get("estructura_completa", ""))),
            metadatos={
                "contexto_detectado": str(contexto_detectado),
                "estructura_completa": str(estructura_completa),
                "ejemplo_k_usado": [estructura_completa.get("ejemplo_k_usado", "cuantico")],
                "sistema_cuantico": True,
                "interacciones_humanas": interacciones_humanas,
                "modelos_utilizados": modelos_utilizados,
                "prompt_original": prompt_profesor,
                "sistema_version": "quantum_v2.0_completo"
            },
            timestamp=datetime.now().isoformat(),
            # Campos cuánticos específicos
            parametros_cuanticos=parametros_cuanticos,
            prompt_mejorado=prompt_optimizado,
            historial_optimizacion=historial
        )
        
        # Iteración hasta satisfacción (como en sistema original)
        max_iteraciones = 3
        for iteracion in range(1, max_iteraciones + 1):
            print(f"\n🔄 ITERACIÓN {iteracion}/{max_iteraciones}")
            
            # Mostrar actividad
            self.mostrar_actividad_cuantica(actividad)
            
            # Validación final
            print(f"\n✅ VALIDACIÓN FINAL:")
            satisfecho = input(f"🗣️ ¿Estás satisfecho con la actividad? (sí/no): ").strip().lower()
            
            # Registrar interacción final
            interacciones_humanas.append({
                "fase": f"Validación final iteración {iteracion}",
                "pregunta": "¿Estás satisfecho con la actividad?",
                "respuesta": satisfecho
            })
            
            if satisfecho in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
                print(f"\n✨ ¡ACTIVIDAD CUÁNTICA COMPLETADA!")
                break
            elif iteracion < max_iteraciones:
                feedback_final = input(f"🗣️ ¿Qué quieres cambiar?: ").strip()
                
                # Registrar feedback
                interacciones_humanas.append({
                    "fase": f"Feedback iteración {iteracion}",
                    "pregunta": "¿Qué quieres cambiar?",
                    "respuesta": feedback_final
                })
                
                # Refinar actividad completa
                nueva_estructura = self._refinar_estructura_cuantica(contexto_detectado, estructura_completa, interacciones_humanas)
                actividad.contenido_completo = str(nueva_estructura.get("estructura_completa", ""))
                actividad.metadatos["iteraciones"] = iteracion
                actividad.metadatos["interacciones_humanas"] = interacciones_humanas
                
                # Agregar modelo usado en refinamiento
                modelos_utilizados.append({
                    "fase": f"Refinamiento iteración {iteracion}",
                    "agente": "Arquitecto de Experiencias Educativas Cuánticas",
                    "modelo": "ollama/qwen2:latest",
                    "proposito": f"Refinar actividad según feedback: {feedback_final[:50]}..."
                })
            else:
                print(f"\n⚠️ Se alcanzó el máximo de iteraciones. Finalizando.")
        
        # Actualizar metadatos finales
        actividad.metadatos["interacciones_humanas"] = interacciones_humanas
        actividad.metadatos["modelos_utilizados"] = modelos_utilizados
        
        return actividad
    
    # =================== FIN MÉTODOS RESTAURADOS ===================
    
    def mostrar_actividad_cuantica(self, actividad: QuantumActividadEducativa):
        """Muestra actividad cuántica de forma clara"""
        print("\n" + "="*80)
        print(f"⚛️ {actividad.titulo}")
        print("="*80)
        print(f"📖 Materia: {actividad.materia} | Tema: {actividad.tema}")
        print(f"🎭 Clima: {actividad.clima} | Modalidad: {actividad.modalidad_trabajo}")
        print(f"⏱️ Duración: {actividad.duracion}")
        
        print(f"\n🔬 PARÁMETROS CUÁNTICOS:")
        if isinstance(actividad.parametros_cuanticos, dict) and "ambiente" in actividad.parametros_cuanticos:
            ambiente = actividad.parametros_cuanticos["ambiente"]
            print(f"  • Energía: {ambiente.get('energia', 0):.2f}")
            print(f"  • Estructura: {ambiente.get('estructura', 0):.2f}")
            print(f"  • Colaboración: {ambiente.get('colaboracion', 0):.2f}")
        
        print(f"\n📋 FASES DE LA ACTIVIDAD:")
        for i, fase in enumerate(actividad.fases, 1):
            print(f"  {i}. {fase}")
        
        print(f"\n📦 MATERIALES:")
        for material in actividad.materiales:
            print(f"  • {material}")
        
        print(f"\n👥 TAREAS POR ESTUDIANTE:")
        perfiles = {
            "001": "ALEX M.", "002": "MARÍA L.", "003": "ELENA R. [TEA]", "004": "LUIS T. [TDAH]",
            "005": "ANA V. [Altas Cap.]", "006": "SARA M.", "007": "EMMA K.", "008": "HUGO P."
        }
        
        for codigo, tarea in actividad.tareas_estudiantes.items():
            nombre = perfiles.get(codigo, f"Estudiante {codigo}")
            print(f"  {codigo} {nombre}: {tarea}")
        
        print(f"\n📄 CONTENIDO COMPLETO GENERADO:")
        print("-" * 50)
        # Mostrar solo los primeros 800 caracteres del contenido completo
        contenido_preview = actividad.contenido_completo[:800]
        if len(actividad.contenido_completo) > 800:
            contenido_preview += "... [contenido truncado]"
        print(contenido_preview)
        print("-" * 50)
        
        print(f"\n🌟 GENERADO POR: Sistema Cuántico de Agentes Inteligentes")
        print(f"📊 Optimización cuántica: {len(actividad.historial_optimizacion)} pasos")
        if actividad.historial_optimizacion:
            print(f"📈 Costo final: {actividad.historial_optimizacion[-1]:.4f}")
        
        # Agregar opción para ver contenido completo
        ver_completo = input(f"\n❓ ¿Ver contenido completo generado por el LLM? (s/n): ").strip().lower()
        if ver_completo in ['s', 'sí', 'si', 'yes', 'y']:
            print(f"\n📄 CONTENIDO COMPLETO:")
            print("="*80)
            print(actividad.contenido_completo)
            print("="*80)


def main():
    """Función principal con interfaz para sistema cuántico"""
    print("⚛️ Sistema de Agentes Inteligente con Optimización Cuántica")
    print("CrewAI + Ollama + PennyLane + Few-shot estratégico")
    print("="*70)
    
    # Inicializar sistema
    try:
        sistema = QuantumIntelligentAgentsSystem()
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        print("💡 Verifica que Ollama esté ejecutándose y PennyLane instalado")
        return
    
    # Solicitar prompt del profesor
    print("\n💬 Describe la actividad que quieres crear:")
    print("   El sistema optimizará tu prompt usando computación cuántica")
    print("   Ejemplo: 'Necesito trabajar fracciones con estudiantes de 4º primaria,")
    print("            Elena tiene TEA y Luis TDAH, disponemos de 45 minutos'")
    
    prompt_profesor = input("🗣️ Tu descripción: ").strip()
    
    if not prompt_profesor:
        print("⚠️ Necesito una descripción para generar la actividad")
        return
    
    # Generar actividad con optimización cuántica
    print(f"\n🌟 Generando actividad con optimización cuántica...")
    
    try:
        actividad_cuantica = sistema.generar_actividad_cuantica_desde_prompt(prompt_profesor)
        
        # Mostrar resultado
        sistema.mostrar_actividad_cuantica(actividad_cuantica)
        
        # Guardar actividad con tracking completo para análisis posterior
        filename = f"actividad_cuantica_{actividad_cuantica.id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            # Convertir a dict para JSON con tracking completo
            actividad_dict = {
                "id": actividad_cuantica.id,
                "titulo": actividad_cuantica.titulo,
                "materia": actividad_cuantica.materia,
                "tema": actividad_cuantica.tema,
                "clima": actividad_cuantica.clima,
                "modalidad_trabajo": actividad_cuantica.modalidad_trabajo,
                "contenido_completo": actividad_cuantica.contenido_completo,
                "tareas_estudiantes": actividad_cuantica.tareas_estudiantes,
                "materiales": actividad_cuantica.materiales,
                "duracion": actividad_cuantica.duracion,
                "fases": actividad_cuantica.fases,
                "metadatos": actividad_cuantica.metadatos,
                "timestamp": actividad_cuantica.timestamp,
                
                # Datos cuánticos específicos
                "parametros_cuanticos": actividad_cuantica.parametros_cuanticos,
                "prompt_mejorado": actividad_cuantica.prompt_mejorado,
                "historial_optimizacion": actividad_cuantica.historial_optimizacion,
                
                # Tracking para análisis y comparación
                "tracking_completo": {
                    "interacciones_humanas": actividad_cuantica.metadatos.get("interacciones_humanas", []),
                    "modelos_utilizados": actividad_cuantica.metadatos.get("modelos_utilizados", []),
                    "prompt_original": actividad_cuantica.metadatos.get("prompt_original", ""),
                    "sistema_version": actividad_cuantica.metadatos.get("sistema_version", "quantum_v2.0"),
                    "total_interacciones": len(actividad_cuantica.metadatos.get("interacciones_humanas", [])),
                    "total_modelos": len(actividad_cuantica.metadatos.get("modelos_utilizados", [])),
                    "iteraciones_realizadas": actividad_cuantica.metadatos.get("iteraciones", 1),
                    "optimizacion_cuantica_aplicada": True if actividad_cuantica.historial_optimizacion else False,
                    "pasos_optimizacion": len(actividad_cuantica.historial_optimizacion),
                    "costo_final_cuantico": actividad_cuantica.historial_optimizacion[-1] if actividad_cuantica.historial_optimizacion else None
                }
            }
            json.dump(actividad_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Actividad cuántica guardada: {filename}")
        
        # Mostrar resumen de tracking para el usuario
        if actividad_cuantica.metadatos.get("interacciones_humanas"):
            total_interacciones = len(actividad_cuantica.metadatos["interacciones_humanas"])
            print(f"📊 Interacciones humanas registradas: {total_interacciones}")
        
        if actividad_cuantica.metadatos.get("modelos_utilizados"):
            total_modelos = len(actividad_cuantica.metadatos["modelos_utilizados"])
            modelos_unicos = list(set([m["modelo"] for m in actividad_cuantica.metadatos["modelos_utilizados"]]))
            print(f"🤖 Modelos utilizados: {total_modelos} tareas en {len(modelos_unicos)} modelos diferentes")
        
        if actividad_cuantica.historial_optimizacion:
            print(f"⚛️ Optimización cuántica: {len(actividad_cuantica.historial_optimizacion)} pasos")
        
        print("🌟 ¡Actividad generada con sistema cuántico completo!")
        
    except Exception as e:
        print(f"❌ Error generando actividad cuántica: {e}")
        logger.error(f"Error en generación cuántica: {e}")


if __name__ == "__main__":
    main()