#!/usr/bin/env python3
"""
Sistema de Agentes con Estructuras Adaptativas por Complejidad
============================================================

Sistema optimizado que incluye:
- Una sola llamada LLM principal (sin clasificación semántica en tiempo real)
- Plantillas de estructura según complejidad/características
- Configuración simplificada sin conflictos LiteLLM
- Estructuras obligatorias adaptativas (no solo nivel pedagógico)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Configuración de entorno (exacta como archivos que funcionan)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"
os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SISTEMA_ESTRUCTURADO")

try:
    from crewai import Agent, Task, Crew, Process
    from langchain_community.llms import Ollama
    from quantum_enhancer import QuantumEnhancer, QISKIT_CONFIG
    logger.info("✅ Dependencias importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    raise

# =============================================================================
# ENUMS Y ESTRUCTURAS
# =============================================================================

class TipoComplejidad(Enum):
    PRACTICA = "practica"
    NARRATIVA = "narrativa" 
    EXPLORATORIA = "exploratoria"
    ANALITICA = "analitica"

class NivelDificultad(Enum):
    BASICA = "basica"
    INTERMEDIA = "intermedia"
    AVANZADA = "avanzada"
    EXPERTA = "experta"

@dataclass
class PerfilActividad:
    """Define cómo debe estructurarse una actividad según complejidad y nivel"""
    tipo_complejidad: TipoComplejidad
    nivel_dificultad: NivelDificultad
    estructura_obligatoria: List[str]
    elementos_prohibidos: List[str]
    duracion_recomendada: str
    enfoque_principal: str
    formato_tareas: str

@dataclass
class ContextoEstructurado:
    """Contexto con estructura predefinida"""
    prompt_inicial: str
    materia: str
    tema: Optional[str]
    perfil_actividad: PerfilActividad
    estudiantes: List[Dict]
    ejemplos_k: Dict[str, str]
    quantum_insights: str

@dataclass
class ActividadEducativa:
    """Actividad educativa completa"""
    id: str
    titulo: str
    materia: str
    tema: str
    tipo_complejidad: str
    nivel_dificultad: str
    contenido: str
    estudiantes_objetivo: List[str]
    metadatos: Dict
    timestamp: str

# =============================================================================
# PLANTILLAS DE ESTRUCTURA POR COMPLEJIDAD
# =============================================================================

class PlantillasEstructura:
    """Define estructuras obligatorias según tipo de complejidad"""
    
    @staticmethod
    def get_perfil_actividad(tipo_complejidad: TipoComplejidad, nivel_dificultad: NivelDificultad) -> PerfilActividad:
        """Retorna el perfil de actividad según complejidad y nivel"""
        
        perfiles = {
            # ===============================================
            # ACTIVIDADES PRÁCTICAS
            # ===============================================
            (TipoComplejidad.PRACTICA, NivelDificultad.BASICA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.PRACTICA,
                nivel_dificultad=NivelDificultad.BASICA,
                estructura_obligatoria=[
                    "OBJETIVO CLARO Y SIMPLE",
                    "MATERIALES BÁSICOS NECESARIOS", 
                    "INSTRUCCIONES PASO A PASO",
                    "TAREAS ESPECÍFICAS POR ESTUDIANTE",
                    "EJEMPLO PRÁCTICO CONCRETO",
                    "EVALUACIÓN DIRECTA"
                ],
                elementos_prohibidos=[
                    "historias elaboradas", "narrativas complejas", "personajes ficticios",
                    "metáforas abstractas", "acertijos", "misterios", "elementos dramáticos"
                ],
                duracion_recomendada="1-2 sesiones de 45 minutos",
                enfoque_principal="Aplicación directa de conceptos con ejercicios concretos",
                formato_tareas="Lista numerada de tareas específicas y medibles"
            ),
            
            (TipoComplejidad.PRACTICA, NivelDificultad.INTERMEDIA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.PRACTICA,
                nivel_dificultad=NivelDificultad.INTERMEDIA,
                estructura_obligatoria=[
                    "OBJETIVO CON APLICACIÓN REAL",
                    "MATERIALES Y RECURSOS VARIADOS",
                    "METODOLOGÍA PRÁCTICA CLARA", 
                    "TAREAS DIFERENCIADAS POR GRUPO",
                    "PROBLEMAS REALES A RESOLVER",
                    "AUTOEVALUACIÓN Y REFLEXIÓN"
                ],
                elementos_prohibidos=[
                    "narrativas extensas", "elementos fantásticos", "complejidad innecesaria"
                ],
                duracion_recomendada="2-3 sesiones de 45 minutos",
                enfoque_principal="Resolución de problemas reales con aplicación práctica",
                formato_tareas="Proyectos cortos con entregables concretos"
            ),
            
            (TipoComplejidad.PRACTICA, NivelDificultad.AVANZADA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.PRACTICA,
                nivel_dificultad=NivelDificultad.AVANZADA,
                estructura_obligatoria=[
                    "OBJETIVO COMPLEJO CON MÚLTIPLES APLICACIONES",
                    "RECURSOS ESPECIALIZADOS Y TÉCNICOS",
                    "METODOLOGÍA AVANZADA",
                    "PROYECTOS INTERDISCIPLINARIOS",
                    "PROBLEMAS COMPLEJOS REALES",
                    "EVALUACIÓN MULTIDIMENSIONAL"
                ],
                elementos_prohibidos=[
                    "simplicidad excesiva", "tareas repetitivas", "elementos decorativos"
                ],
                duracion_recomendada="3-5 sesiones de 45 minutos",
                enfoque_principal="Aplicación avanzada con resolución de problemas complejos",
                formato_tareas="Proyectos complejos con múltiples entregables"
            ),
            
            # ===============================================
            # ACTIVIDADES NARRATIVAS
            # ===============================================
            (TipoComplejidad.NARRATIVA, NivelDificultad.BASICA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.NARRATIVA,
                nivel_dificultad=NivelDificultad.BASICA,
                estructura_obligatoria=[
                    "HISTORIA SIMPLE Y CLARA",
                    "PERSONAJES IDENTIFICABLES",
                    "SITUACIÓN PROBLEMA SENCILLA",
                    "ROLES ESPECÍFICOS POR ESTUDIANTE",
                    "DESARROLLO NARRATIVO GUIADO",
                    "RESOLUCIÓN COLABORATIVA"
                ],
                elementos_prohibidos=[
                    "tramas complejas", "múltiples subhistorias", "conceptos abstractos", "elementos confusos"
                ],
                duracion_recomendada="2-3 sesiones de 45 minutos",
                enfoque_principal="Aprendizaje a través de historia envolvente pero simple",
                formato_tareas="Secuencia narrativa con participación activa"
            ),
            
            (TipoComplejidad.NARRATIVA, NivelDificultad.INTERMEDIA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.NARRATIVA,
                nivel_dificultad=NivelDificultad.INTERMEDIA,
                estructura_obligatoria=[
                    "NARRATIVA CON DESARROLLO",
                    "PERSONAJES CON MOTIVACIONES",
                    "CONFLICTOS Y RESOLUCIONES",
                    "ROLES DINÁMICOS",
                    "DECISIONES COLABORATIVAS",
                    "ANÁLISIS NARRATIVO"
                ],
                elementos_prohibidos=[
                    "simplicidad excesiva", "personajes planos", "resoluciones obvias"
                ],
                duracion_recomendada="3-4 sesiones de 45 minutos",
                enfoque_principal="Inmersión narrativa con desarrollo de personajes",
                formato_tareas="Historia colaborativa con decisiones"
            ),
            
            (TipoComplejidad.NARRATIVA, NivelDificultad.AVANZADA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.NARRATIVA,
                nivel_dificultad=NivelDificultad.AVANZADA,
                estructura_obligatoria=[
                    "NARRATIVA MULTICAPA",
                    "PERSONAJES CON TRASFONDO COMPLEJO",
                    "MÚLTIPLES PERSPECTIVAS",
                    "ROLES COMPLEJOS Y DINÁMICOS",
                    "DECISIONES CON CONSECUENCIAS",
                    "ANÁLISIS NARRATIVO PROFUNDO"
                ],
                elementos_prohibidos=[
                    "simplicidad excesiva", "soluciones obvias", "desarrollo lineal"
                ],
                duracion_recomendada="1 semana (5 sesiones)",
                enfoque_principal="Inmersión narrativa con análisis crítico",
                formato_tareas="Desarrollo de historia colaborativa compleja"
            ),
            
            # ===============================================
            # ACTIVIDADES EXPLORATORIAS
            # ===============================================
            (TipoComplejidad.EXPLORATORIA, NivelDificultad.BASICA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.EXPLORATORIA,
                nivel_dificultad=NivelDificultad.BASICA,
                estructura_obligatoria=[
                    "PREGUNTA SIMPLE DE INVESTIGACIÓN",
                    "RECURSOS BÁSICOS PROPORCIONADOS",
                    "GUÍA DE EXPLORACIÓN CLARA",
                    "EQUIPOS CON ROLES SIMPLES",
                    "DESCUBRIMIENTOS GUIADOS",
                    "PRESENTACIÓN SENCILLA"
                ],
                elementos_prohibidos=[
                    "investigación compleja", "fuentes múltiples", "análisis profundo"
                ],
                duracion_recomendada="2-3 sesiones de 45 minutos",
                enfoque_principal="Exploración guiada con descubrimientos dirigidos",
                formato_tareas="Investigación simple estructurada"
            ),
            
            (TipoComplejidad.EXPLORATORIA, NivelDificultad.INTERMEDIA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.EXPLORATORIA,
                nivel_dificultad=NivelDificultad.INTERMEDIA,
                estructura_obligatoria=[
                    "PREGUNTA DE INVESTIGACIÓN",
                    "METODOLOGÍA DE EXPLORACIÓN",
                    "RECURSOS Y FUENTES VARIADAS",
                    "EQUIPOS DE INVESTIGACIÓN",
                    "PROCESO DE DESCUBRIMIENTO",
                    "PRESENTACIÓN DE HALLAZGOS"
                ],
                elementos_prohibidos=[
                    "respuestas predeterminadas", "caminos únicos de solución", "simplicidad excesiva"
                ],
                duracion_recomendada="3-4 sesiones de 45 minutos",
                enfoque_principal="Descubrimiento guiado con investigación activa",
                formato_tareas="Proyectos de investigación estructurada"
            ),
            
            # ===============================================
            # ACTIVIDADES ANALÍTICAS
            # ===============================================
            (TipoComplejidad.ANALITICA, NivelDificultad.INTERMEDIA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.ANALITICA,
                nivel_dificultad=NivelDificultad.INTERMEDIA,
                estructura_obligatoria=[
                    "CASO A ANALIZAR",
                    "METODOLOGÍA DE ANÁLISIS BÁSICA",
                    "HERRAMIENTAS DE ANÁLISIS",
                    "EQUIPOS ANALÍTICOS",
                    "DISCUSIÓN ESTRUCTURADA",
                    "CONCLUSIONES JUSTIFICADAS"
                ],
                elementos_prohibidos=[
                    "análisis superficial", "opiniones sin fundamento", "elementos narrativos"
                ],
                duracion_recomendada="3-4 sesiones de 45 minutos",
                enfoque_principal="Análisis estructurado con justificación",
                formato_tareas="Casos de estudio con análisis guiado"
            ),
            
            (TipoComplejidad.ANALITICA, NivelDificultad.AVANZADA): PerfilActividad(
                tipo_complejidad=TipoComplejidad.ANALITICA,
                nivel_dificultad=NivelDificultad.AVANZADA,
                estructura_obligatoria=[
                    "CASO COMPLEJO A ANALIZAR",
                    "METODOLOGÍA DE ANÁLISIS AVANZADA",
                    "HERRAMIENTAS ANALÍTICAS MÚLTIPLES",
                    "EQUIPOS ESPECIALIZADOS",
                    "DEBATE Y ARGUMENTACIÓN",
                    "CONCLUSIONES FUNDAMENTADAS"
                ],
                elementos_prohibidos=[
                    "análisis superficial", "conclusiones simplistas", "elementos narrativos", "simplicidad"
                ],
                duracion_recomendada="1 semana (5 sesiones)",
                enfoque_principal="Análisis crítico profundo con argumentación",
                formato_tareas="Estudios de caso con análisis exhaustivo"
            )
        }
        
        # Si no encuentra el perfil exacto, usar defaults inteligentes
        if (tipo_complejidad, nivel_dificultad) not in perfiles:
            return PerfilActividad(
                tipo_complejidad=tipo_complejidad,
                nivel_dificultad=nivel_dificultad,
                estructura_obligatoria=[
                    "OBJETIVO CLARO",
                    "METODOLOGÍA APROPIADA", 
                    "TAREAS ESPECÍFICAS",
                    "EVALUACIÓN"
                ],
                elementos_prohibidos=["elementos inapropiados para el nivel"],
                duracion_recomendada="2-3 sesiones",
                enfoque_principal="Enfoque equilibrado según tipo y nivel",
                formato_tareas="Tareas estructuradas apropiadas"
            )
        
        return perfiles[(tipo_complejidad, nivel_dificultad)]

# =============================================================================
# SISTEMA PRINCIPAL
# =============================================================================

class SistemaAgentesEstructurado:
    """Sistema de agentes con estructuras adaptativas"""
    
    def __init__(self,
                 ollama_host: str = "192.168.1.10",
                 modelo_base: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.modelo_base = modelo_base
        self.perfiles_path = perfiles_path
        
        self._configurar_llm()
        self._cargar_recursos()
        self._crear_agente_unificado()
        self._crear_quantum_enhancer()
        
        logger.info("✅ Sistema de Agentes Estructurado inicializado")
        logger.info(f"   🤖 Modelo: {self.modelo_base}")
        logger.info(f"   👥 Estudiantes: {len(self.estudiantes)}")
    
    def _configurar_llm(self):
        """Configura LLM sin conflictos (igual que archivos que funcionan)"""
        try:
            import litellm
            
            litellm.model_cost[f"ollama/{self.modelo_base}"] = {
                "input_cost_per_token": 0,
                "output_cost_per_token": 0,
                "max_tokens": 4096
            }
            
            self.llm = Ollama(
                model=f"ollama/{self.modelo_base}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info(f"✅ LLM configurado: {self.modelo_base}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLM: {e}")
            raise e
    
    def _cargar_recursos(self):
        """Carga recursos y perfiles"""
        
        # Cargar perfiles de estudiantes
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            perfiles_path = os.path.join(script_dir, self.perfiles_path)
            
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.estudiantes = data.get('estudiantes', self._crear_perfiles_default())
        except Exception as e:
            logger.warning(f"⚠️ Error cargando perfiles: {e}")
            self.estudiantes = self._crear_perfiles_default()
        
        # Cargar ejemplos K
        self._cargar_ejemplos_k()
    
    def _crear_perfiles_default(self) -> List[Dict]:
        """Perfiles por defecto"""
        return [
            {"id": "001", "nombre": "ALEX M.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 102},
            {"id": "002", "nombre": "MARÍA L.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno"},
            {"id": "003", "nombre": "ELENA R.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "TEA_nivel_1", "ci_base": 118},
            {"id": "004", "nombre": "LUIS T.", "temperamento": "impulsivo", "canal_preferido": "kinestésico", "diagnostico_formal": "TDAH_combinado", "ci_base": 102},
            {"id": "005", "nombre": "ANA V.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "altas_capacidades", "ci_base": 141},
            {"id": "006", "nombre": "SARA M.", "temperamento": "equilibrado", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno", "ci_base": 115},
            {"id": "007", "nombre": "EMMA K.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 132},
            {"id": "008", "nombre": "HUGO P.", "temperamento": "equilibrado", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 114}
        ]
    
    def _cargar_ejemplos_k(self):
        """Carga ejemplos K de referencia"""
        self.ejemplos_k = {}
        
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_sonnet_supermercado.txt", 
            "actividades_generadas/k_feria_acertijos.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                archivo_path = os.path.join(script_dir, archivo)
                
                if os.path.exists(archivo_path):
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido[:800]  # Truncar para contexto
                        logger.info(f"📖 Cargado: {nombre_ejemplo}")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando {archivo}: {e}")
        
        logger.info(f"✅ Cargados {len(self.ejemplos_k)} ejemplos K")
    
    def _crear_agente_unificado(self):
        """Crea agente unificado optimizado"""
        self.agente_unificado = Agent(
            role="Diseñador Educativo Estructurado",
            goal="Crear actividades educativas siguiendo estructuras específicas según complejidad y nivel",
            backstory="""Soy un diseñador educativo especializado en crear actividades estructuradas. 
            Adapto la estructura, formato y enfoque según el tipo de complejidad solicitada.
            Sigo plantillas específicas y evito elementos no deseados según el perfil elegido.
            Creo actividades prácticas cuando se solicita práctica, narrativas cuando se solicita narrativa, etc.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=1
        )
        
        logger.info("✅ Agente unificado creado")
    
    def _crear_quantum_enhancer(self):
        """Inicializa quantum enhancer"""
        try:
            self.quantum_enhancer = QuantumEnhancer(QISKIT_CONFIG)
            logger.info("✅ Quantum Enhancer inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Quantum Enhancer no disponible: {e}")
            self.quantum_enhancer = None
    
    def _detectar_materia_y_tema(self, prompt: str) -> tuple[str, Optional[str]]:
        """Detecta materia y tema del prompt"""
        prompt_lower = prompt.lower()
        
        # Detectar materia
        materias = {
            'matematicas': ['matemáticas', 'mates', 'números', 'cálculo', 'geometría', 'fracciones', 'suma', 'resta'],
            'lengua': ['lengua', 'idioma', 'escritura', 'lectura', 'gramática', 'literatura', 'texto', 'palabras', 'verbos', 'tiempos'],
            'ciencias': ['ciencias', 'biología', 'física', 'química', 'naturales', 'científico', 'células', 'animales', 'plantas']
        }
        
        materia_detectada = None
        for materia, keywords in materias.items():
            if any(keyword in prompt_lower for keyword in keywords):
                materia_detectada = materia
                break
        
        # Detectar tema
        import re
        tema_patterns = [
            r'sobre[:\s]*([^.,\n]+)',
            r'tema[:\s]*([^.,\n]+)', 
            r'acerca de[:\s]*([^.,\n]+)',
            r'de[:\s]+([^.,\n]+)'
        ]
        
        tema_detectado = None
        for pattern in tema_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                tema_detectado = match.group(1).strip()
                break
        
        return materia_detectada, tema_detectado
    
    def _solicitar_configuracion(self) -> tuple[TipoComplejidad, NivelDificultad]:
        """Solicita tipo de complejidad y nivel de dificultad"""
        
        print(f"\n" + "="*70)
        print(f"🎯 CONFIGURACIÓN DE ACTIVIDAD ESTRUCTURADA")
        print("="*70)
        
        # Seleccionar tipo de complejidad
        print("\n1️⃣ TIPO DE COMPLEJIDAD (estructura de la actividad):")
        print("1. 🔧 PRÁCTICA - Ejercicios directos, sin narrativas, enfoque aplicado")
        print("2. 📖 NARRATIVA - Historia envolvente, personajes, desarrollo narrativo")  
        print("3. 🔍 EXPLORATORIA - Investigación, descubrimiento, exploración guiada")
        print("4. 🧠 ANALÍTICA - Análisis profundo, casos complejos, argumentación")
        
        tipos = {
            "1": TipoComplejidad.PRACTICA,
            "2": TipoComplejidad.NARRATIVA, 
            "3": TipoComplejidad.EXPLORATORIA,
            "4": TipoComplejidad.ANALITICA
        }
        
        while True:
            try:
                opcion_tipo = input("\n👉 Selecciona tipo (1-4): ").strip()
                if opcion_tipo in tipos:
                    tipo_seleccionado = tipos[opcion_tipo]
                    break
                print("❌ Selecciona una opción válida (1-4)")
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado")
                return TipoComplejidad.PRACTICA, NivelDificultad.INTERMEDIA
        
        # Seleccionar nivel de dificultad
        print(f"\n2️⃣ NIVEL DE DIFICULTAD (complejidad pedagógica):")
        print("1. 🟢 BÁSICA - Conceptos fundamentales, actividades simples")
        print("2. 🟡 INTERMEDIA - Aplicación práctica, complejidad moderada")
        print("3. 🔴 AVANZADA - Conceptos complejos, pensamiento crítico")
        print("4. 🏆 EXPERTA - Máxima complejidad, análisis profundo")
        
        niveles = {
            "1": NivelDificultad.BASICA,
            "2": NivelDificultad.INTERMEDIA,
            "3": NivelDificultad.AVANZADA, 
            "4": NivelDificultad.EXPERTA
        }
        
        while True:
            try:
                opcion_nivel = input("\n👉 Selecciona nivel (1-4): ").strip()
                if opcion_nivel in niveles:
                    nivel_seleccionado = niveles[opcion_nivel]
                    break
                print("❌ Selecciona una opción válida (1-4)")
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado")
                return tipo_seleccionado, NivelDificultad.INTERMEDIA
        
        return tipo_seleccionado, nivel_seleccionado
    
    def _construir_contexto_estructurado(self, 
                                       prompt_inicial: str,
                                       materia: str,
                                       tema: str,
                                       perfil_actividad: PerfilActividad,
                                       quantum_insights: str = "") -> ContextoEstructurado:
        """Construye contexto con estructura predefinida"""
        
        return ContextoEstructurado(
            prompt_inicial=prompt_inicial,
            materia=materia,
            tema=tema,
            perfil_actividad=perfil_actividad,
            estudiantes=self.estudiantes,
            ejemplos_k=self.ejemplos_k,
            quantum_insights=quantum_insights
        )
    
    def _crear_prompt_estructurado(self, contexto: ContextoEstructurado) -> str:
        """Crea prompt con estructura obligatoria específica"""
        
        perfil = contexto.perfil_actividad
        
        prompt = f"""
════════════════════════════════════════════════════════════════════════════════
DISEÑO DE ACTIVIDAD EDUCATIVA ESTRUCTURADA
════════════════════════════════════════════════════════════════════════════════

SOLICITUD DEL USUARIO:
{contexto.prompt_inicial}

CONFIGURACIÓN OBLIGATORIA:
- Materia: {contexto.materia}
- Tema: {contexto.tema}
- Tipo de Complejidad: {perfil.tipo_complejidad.value.upper()}
- Nivel de Dificultad: {perfil.nivel_dificultad.value.upper()}

PERFIL DE ACTIVIDAD REQUERIDO:
- Duración: {perfil.duracion_recomendada}
- Enfoque Principal: {perfil.enfoque_principal}
- Formato de Tareas: {perfil.formato_tareas}

ESTRUCTURA OBLIGATORIA (DEBES INCLUIR TODOS):
"""
        
        for i, elemento in enumerate(perfil.estructura_obligatoria, 1):
            prompt += f"\n{i}. {elemento}"
        
        prompt += f"""

ELEMENTOS PROHIBIDOS (NO INCLUIR BAJO NINGÚN CONCEPTO):
"""
        for elemento in perfil.elementos_prohibidos:
            prompt += f"\n❌ {elemento}"
        
        prompt += f"""

ESTUDIANTES DISPONIBLES (USAR EXACTAMENTE ESTOS):
"""
        for estudiante in contexto.estudiantes:
            prompt += f"\n- {estudiante['id']} {estudiante['nombre']}: {estudiante['temperamento']}, {estudiante['canal_preferido']}"
            if estudiante.get('diagnostico_formal', 'ninguno') != 'ninguno':
                prompt += f", {estudiante['diagnostico_formal']}"
        
        if contexto.quantum_insights:
            prompt += f"""

INSIGHTS CUÁNTICOS PRE-PROCESADOS:
{contexto.quantum_insights}
"""
        
        if contexto.ejemplos_k:
            prompt += f"""

EJEMPLOS DE REFERENCIA:
"""
            for nombre, contenido in contexto.ejemplos_k.items():
                prompt += f"\n--- {nombre.upper()} ---\n{contenido[:300]}...\n"
        
        prompt += f"""

════════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES CRÍTICAS:

1. SIGUE EXACTAMENTE la estructura obligatoria del perfil {perfil.tipo_complejidad.value.upper()}
2. EVITA completamente los elementos prohibidos listados arriba
3. USA todos los 8 estudiantes con roles específicos y diferenciados
4. ADAPTA el vocabulario y conceptos al nivel {perfil.nivel_dificultad.value.upper()}
5. RESPETA la duración recomendada: {perfil.duracion_recomendada}
6. ENFÓCATE en: {perfil.enfoque_principal}
7. FORMATO: {perfil.formato_tareas}
8. CREA contenido apropiado para 4º Primaria

IMPORTANTE: Si el tipo es PRÁCTICA, NO incluyas historias ni narrativas.
Si el tipo es NARRATIVA, SÍ incluye historia envolvente con personajes.
Si el tipo es EXPLORATORIA, enfócate en investigación y descubrimiento.
Si el tipo es ANALÍTICA, enfócate en análisis y argumentación.

GENERA una actividad educativa completa que cumpla estrictamente con este perfil.
════════════════════════════════════════════════════════════════════════════════
"""
        
        return prompt
    
    def generar_actividad_estructurada(self, prompt_inicial: str) -> ActividadEducativa:
        """Genera actividad con estructura adaptativa (método principal)"""
        
        logger.info("🚀 Iniciando generación estructurada")
        
        # 1. Detectar materia y tema
        materia, tema = self._detectar_materia_y_tema(prompt_inicial)
        
        if not materia:
            materia = input("📚 ¿Qué materia? (matematicas/lengua/ciencias): ").strip().lower()
        
        if not tema:
            tema = "tema general"
        
        print(f"\n📚 Materia: {materia}")
        print(f"📝 Tema: {tema}")
        
        # 2. Configurar complejidad y nivel
        tipo_complejidad, nivel_dificultad = self._solicitar_configuracion()
        
        # 3. Obtener perfil de actividad
        perfil_actividad = PlantillasEstructura.get_perfil_actividad(tipo_complejidad, nivel_dificultad)
        
        print(f"\n✅ Configuración seleccionada:")
        print(f"   🎯 Tipo: {tipo_complejidad.value.upper()}")
        print(f"   🎚️ Nivel: {nivel_dificultad.value.upper()}")
        print(f"   ⏱️ Duración: {perfil_actividad.duracion_recomendada}")
        print(f"   🎯 Enfoque: {perfil_actividad.enfoque_principal}")
        
        try:
            # 4. Preprocesado cuántico
            quantum_insights = ""
            if self.quantum_enhancer:
                quantum_insights = self.quantum_enhancer.analizar_dificultad_cuantica(
                    materia, tema, ""
                )
                logger.info(f"✨ Insights cuánticos: {quantum_insights}")
            
            # 5. Construir contexto estructurado
            contexto = self._construir_contexto_estructurado(
                prompt_inicial, materia, tema, perfil_actividad, quantum_insights
            )
            
            # 6. Crear prompt estructurado
            prompt_estructurado = self._crear_prompt_estructurado(contexto)
            
            # 7. UNA SOLA LLAMADA LLM PRINCIPAL
            print(f"\n🤖 Generando actividad con estructura {tipo_complejidad.value}...")
            
            tarea_estructurada = Task(
                description=prompt_estructurado,
                agent=self.agente_unificado,
                expected_output=f"Actividad educativa completa siguiendo estructura {tipo_complejidad.value} nivel {nivel_dificultad.value}"
            )
            
            crew = Crew(
                agents=[self.agente_unificado],
                tasks=[tarea_estructurada],
                process=Process.sequential,
                verbose=False
            )
            
            resultado = crew.kickoff()
            actividad_generada = str(resultado)
            
            # 8. Validación cuántica
            validacion_final = None
            if self.quantum_enhancer:
                puntuacion, feedback_cuantico = self.quantum_enhancer.validar_actividad_cuanticamente(
                    actividad_generada, materia, tema
                )
                print(f"\n🔬 Validación cuántica: {puntuacion:.2f}")
                print(f"📝 {feedback_cuantico}")
                
                validacion_final = {
                    "puntuacion": puntuacion,
                    "feedback": feedback_cuantico,
                    "aprobado": puntuacion >= self.quantum_enhancer.UMBRAL_VALIDACION_CUANTICA
                }
            
            # 9. Crear actividad educativa final
            actividad_id = f"estructurada_{tipo_complejidad.value}_{nivel_dificultad.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            contenido_final = self._construir_contenido_final(
                actividad_generada, perfil_actividad, quantum_insights, validacion_final
            )
            
            return ActividadEducativa(
                id=actividad_id,
                titulo=f"Actividad {tipo_complejidad.value.title()} - {materia.title()}",
                materia=materia,
                tema=tema,
                tipo_complejidad=tipo_complejidad.value,
                nivel_dificultad=nivel_dificultad.value,
                contenido=contenido_final,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                metadatos={
                    "perfil_actividad": {
                        "tipo_complejidad": tipo_complejidad.value,
                        "nivel_dificultad": nivel_dificultad.value,
                        "duracion_recomendada": perfil_actividad.duracion_recomendada,
                        "enfoque_principal": perfil_actividad.enfoque_principal,
                        "estructura_obligatoria": perfil_actividad.estructura_obligatoria,
                        "elementos_prohibidos": perfil_actividad.elementos_prohibidos
                    },
                    "quantum_insights": quantum_insights,
                    "validacion_cuantica": validacion_final,
                    "modelo_usado": self.modelo_base,
                    "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                    "version": "sistema_estructurado_1.0"
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Error generando actividad: {e}")
            return ActividadEducativa(
                id=f"error_estructurada_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error - {materia}",
                materia=materia,
                tema=tema,
                tipo_complejidad="error",
                nivel_dificultad="error",
                contenido=f"Error generando actividad estructurada: {e}",
                estudiantes_objetivo=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _construir_contenido_final(self, actividad: str, perfil: PerfilActividad, quantum_insights: str, validacion: Optional[Dict]) -> str:
        """Construye contenido final estructurado"""
        
        contenido = "=" * 100 + "\n"
        contenido += "ACTIVIDAD EDUCATIVA ESTRUCTURADA\n"
        contenido += f"Tipo: {perfil.tipo_complejidad.value.upper()} | Nivel: {perfil.nivel_dificultad.value.upper()}\n"
        contenido += "=" * 100 + "\n\n"
        
        if quantum_insights:
            contenido += f"🔬 INSIGHTS CUÁNTICOS APLICADOS:\n"
            contenido += f"{quantum_insights}\n\n"
        
        contenido += f"📋 PERFIL DE ACTIVIDAD:\n"
        contenido += f"- Tipo de Complejidad: {perfil.tipo_complejidad.value.upper()}\n"
        contenido += f"- Nivel de Dificultad: {perfil.nivel_dificultad.value.upper()}\n"
        contenido += f"- Duración: {perfil.duracion_recomendada}\n"
        contenido += f"- Enfoque: {perfil.enfoque_principal}\n"
        contenido += f"- Formato: {perfil.formato_tareas}\n\n"
        
        contenido += f"📐 ESTRUCTURA APLICADA:\n"
        for i, elemento in enumerate(perfil.estructura_obligatoria, 1):
            contenido += f"{i}. {elemento}\n"
        contenido += "\n"
        
        if perfil.elementos_prohibidos:
            contenido += f"🚫 ELEMENTOS EVITADOS:\n"
            for elemento in perfil.elementos_prohibidos:
                contenido += f"❌ {elemento}\n"
            contenido += "\n"
        
        if validacion:
            contenido += f"🔬 VALIDACIÓN CUÁNTICA:\n"
            contenido += f"- Puntuación: {validacion['puntuacion']:.2f}\n"
            contenido += f"- Estado: {'✅ Aprobado' if validacion['aprobado'] else '❌ Rechazado'}\n"
            contenido += f"- Feedback: {validacion['feedback']}\n\n"
        
        contenido += f"🎯 ACTIVIDAD GENERADA:\n"
        contenido += "=" * 60 + "\n"
        contenido += actividad + "\n\n"
        
        contenido += f"📊 METADATOS:\n"
        contenido += f"- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        contenido += f"- Sistema: Agentes Estructurado v1.0\n"
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa) -> str:
        """Guarda la actividad generada"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "actividades_estructuradas")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write(f"ACTIVIDAD EDUCATIVA ESTRUCTURADA\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo Complejidad: {actividad.tipo_complejidad}\n")
            f.write(f"Nivel Dificultad: {actividad.nivel_dificultad}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 80 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\n")
            f.write("-" * 80 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("METADATOS:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad guardada: {filepath}")
        return filepath

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal del sistema"""
    
    print("=" * 100)
    print("🎓 SISTEMA DE AGENTES EDUCATIVO ESTRUCTURADO")
    print("Estructuras Adaptativas por Complejidad y Nivel")
    print("=" * 100)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        MODELO_BASE = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        print(f"\n🔧 Inicializando Sistema:")
        print(f" Host Ollama: {OLLAMA_HOST}")
        print(f" Modelo base: {MODELO_BASE}")
        print(f" Características:")
        print(f"   ✅ Estructuras adaptativas por complejidad")
        print(f"   ✅ Una sola llamada LLM optimizada")
        print(f"   ✅ Plantillas obligatorias específicas")
        print(f"   ✅ Validación cuántica integrada")
        
        # Inicializar sistema
        sistema = SistemaAgentesEstructurado(
            ollama_host=OLLAMA_HOST,
            modelo_base=MODELO_BASE,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema inicializado correctamente!")
        
        while True:
            print("\n" + "="*80)
            print("🎓 GENERACIÓN DE ACTIVIDADES ESTRUCTURADAS")
            print("1. 🚀 Generar actividad con estructura adaptativa")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona (1-2): ").strip()
            
            if opcion == "1":
                print("\n📝 Describe tu actividad ideal:")
                print("Ejemplo: 'Actividad de lengua sobre tiempos verbales para 4º primaria'")
                prompt_inicial = input("\n✨ Tu prompt: ").strip()
                
                if not prompt_inicial:
                    print("❌ Por favor, proporciona un prompt")
                    continue
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_estructurada(prompt_inicial)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n🎉 ACTIVIDAD GENERADA EN {duration:.1f}s:")
                print(f" 📄 ID: {actividad.id}")
                print(f" 📁 Archivo: {archivo}")
                print(f" 🎯 Tipo: {actividad.tipo_complejidad.upper()}")
                print(f" 🎚️ Nivel: {actividad.nivel_dificultad.upper()}")
                
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error en sistema: {e}")
        logger.error(f"Error en main: {e}")

if __name__ == "__main__":
    main()