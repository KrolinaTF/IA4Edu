#!/usr/bin/env python3
"""
Sistema de Agentes Híbrido Optimizado
Combina lo mejor de todos los sistemas anteriores:
- Feedback semántico automático (q_sistema_agentes_2)
- Validación cuántica con retry (sistema_agentes_fewshot)  
- Modularidad y tools (sistema_agentes_optimizado)
- Validación incorporada ligera (sistema_agentes_hibrido)
- Agentes dóciles + contexto rico separado
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from difflib import SequenceMatcher

# Configuración de entorno (EXACTAMENTE igual que q_sistema_agentes_2.py)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

os.environ["HTTPX_TIMEOUT"] = "120"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HIBRIDO_OPTIMIZADO")

# Importaciones
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from langchain_community.llms import Ollama
    from quantum_enhancer import QuantumEnhancer, QISKIT_CONFIG
    logger.info("✅ Dependencias importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    raise ImportError("Instala dependencias: pip install crewai crewai-tools langchain-community")

# =============================================================================
# DATA CLASSES Y ENUMS
# =============================================================================

class AgenteSemantico(Enum):
    INSPIRADOR = "inspirador"
    PEDAGOGO = "pedagogo" 
    ARQUITECTO = "arquitecto"
    DIFERENCIADOR = "diferenciador"
    GENERAL = "general"

class NivelComplejidad(Enum):
    BASICA = "basica"
    INTERMEDIA = "intermedia"
    AVANZADA = "avanzada"
    EXPERTA = "experta"

@dataclass
class FeedbackInteligente:
    """Feedback procesado automáticamente con IA"""
    prompt_usuario: str
    agente_objetivo: str
    intencion_detectada: str
    confianza: float
    instrucciones_procesadas: str
    timestamp: str

@dataclass
class RequisitosComplejidad:
    """Define requisitos específicos según nivel de complejidad"""
    nivel: NivelComplejidad
    descripcion: str
    elementos_obligatorios: List[str]
    elementos_prohibidos: List[str]
    duracion_recomendada: str
    enfoque_pedagogico: str
    nivel_vocabulario: str
    criterios_evaluacion: List[str]

@dataclass
class ContextoRico:
    """Contexto separado del prompt para agentes dóciles"""
    prompt_inicial: str
    materia: str
    tema: Optional[str]
    complejidad: str
    requisitos_complejidad: Optional[RequisitosComplejidad]
    ejemplos_k: Dict[str, str]
    perfiles_estudiantes: List[Dict]
    feedback_acumulado: List[FeedbackInteligente]
    fase_anterior: Optional[str]
    objetivo_fase: str
    quantum_insights: str

@dataclass
class ResultadoValidacion:
    """Resultado de validación cuántica"""
    puntuacion: float
    feedback_cuantico: str
    aprobado: bool
    intento: int

@dataclass
class ActividadEducativa:
    """Actividad educativa completa"""
    id: str
    titulo: str
    materia: str
    tema: str
    contenido: str
    estudiantes_objetivo: List[str]
    tipo: str
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str

# =============================================================================
# TOOLS ESPECIALIZADAS
# =============================================================================

class ValidadorCoherenciaTool(BaseTool):
    """Tool para validación de coherencia interna"""
    name: str = "validador_coherencia"
    description: str = "Valida coherencia narrativa y pedagógica de una actividad"
    
    def _run(self, actividad: str) -> str:
        problemas = []
        
        # Validación básica de coherencia
        if len(actividad) < 200:
            problemas.append("Actividad demasiado corta, falta profundidad")
        
        # Validación de estudiantes
        estudiantes_esperados = ["ALEX M.", "MARÍA L.", "ELENA R.", "LUIS T.", "ANA V.", "SARA M.", "EMMA K.", "HUGO P."]
        estudiantes_encontrados = sum(1 for est in estudiantes_esperados if est in actividad)
        
        if estudiantes_encontrados < 4:
            problemas.append(f"Solo se mencionan {estudiantes_encontrados}/8 estudiantes reales")
        
        # Validación de roles específicos
        if "roles específicos" not in actividad.lower() and "roles asignados" not in actividad.lower():
            problemas.append("Faltan roles específicos para los estudiantes")
        
        if problemas:
            return f"❌ PROBLEMAS DE COHERENCIA: {'; '.join(problemas)}"
        return "✅ Coherencia validada correctamente"

class EjemplosKTool(BaseTool):
    """Tool para cargar ejemplos K de referencia"""
    name: str = "ejemplos_k"
    description: str = "Carga ejemplos de actividades exitosas como referencia"
    
    def _run(self, materia: str) -> str:
        ejemplos_map = {
            'matematicas': 'k_sonnet_supermercado',
            'lengua': 'k_piratas', 
            'ciencias': 'k_celula'
        }
        
        ejemplo_key = ejemplos_map.get(materia.lower(), 'k_piratas')
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            archivo_path = os.path.join(script_dir, 'actividades_generadas', f'{ejemplo_key}.txt')
            
            if os.path.exists(archivo_path):
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()[:800]  # Primeros 800 caracteres
                return f"📖 EJEMPLO DE CALIDAD:\n{contenido}"
            else:
                return "📖 Ejemplo genérico: Actividad colaborativa con roles específicos, narrativa envolvente y adaptaciones personalizadas"
        except Exception as e:
            return f"📖 Error cargando ejemplo: {e}"

# =============================================================================
# SISTEMA PRINCIPAL
# =============================================================================

class SistemaAgentesHibridoOptimizado:
    """
    Sistema híbrido que combina lo mejor de todos los enfoques anteriores
    """
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10",
                 modelo_base: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.modelo_base = modelo_base
        self.perfiles_path = perfiles_path
        
        # Inicialización de componentes
        self._verificar_modelo_disponible()
        self._configurar_llm()
        self._cargar_recursos()
        self._crear_clasificador_semantico()
        self._crear_agentes_dociles()
        self._crear_quantum_enhancer()
        
        logger.info("✅ Sistema Híbrido Optimizado inicializado")
        logger.info(f"   🤖 Modelo: {self.modelo_base}")
        logger.info(f"   📖 Ejemplos K: {len(self.ejemplos_k)}")
        logger.info(f"   👥 Estudiantes: {len(self.perfiles_data)}")
    
    def _verificar_modelo_disponible(self):
        """Verifica que el modelo esté disponible en Ollama"""
        try:
            import requests
            
            # Verificar conexión con Ollama
            url = f"http://{self.ollama_host}:11434/api/tags"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                modelos_data = response.json()
                modelos_disponibles = [model['name'] for model in modelos_data.get('models', [])]
                
                logger.info(f"📋 Modelos disponibles en Ollama: {modelos_disponibles}")
                
                # Verificar si nuestro modelo está disponible
                if self.modelo_base not in modelos_disponibles:
                    logger.warning(f"⚠️ Modelo '{self.modelo_base}' no encontrado.")
                    logger.warning(f"💡 Modelos disponibles: {modelos_disponibles}")
                    
                    # Sugerir alternativas comunes (basadas en tus modelos disponibles)
                    alternativas = ['qwen3:latest', 'qwen2:latest', 'llama3:latest', 'llama3.2:latest', 'mistral:latest', 'gemma3:latest']
                    disponibles = [alt for alt in alternativas if alt in modelos_disponibles]
                    
                    if disponibles:
                        sugerencia = disponibles[0]
                        logger.info(f"💡 Sugerencia: Usar '{sugerencia}' como alternativa")
                        respuesta = input(f"¿Quieres usar '{sugerencia}' en lugar de '{self.modelo_base}'? (s/n): ")
                        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                            self.modelo_base = sugerencia
                            os.environ["OPENAI_MODEL_NAME"] = sugerencia
                            logger.info(f"✅ Modelo cambiado a: {sugerencia}")
                    else:
                        logger.error(f"❌ No hay alternativas obvias disponibles")
                        raise Exception(f"Modelo '{self.modelo_base}' no disponible")
                else:
                    logger.info(f"✅ Modelo '{self.modelo_base}' verificado y disponible")
            
            else:
                logger.warning(f"⚠️ No se pudo conectar a Ollama en {self.ollama_host}:11434")
                logger.warning(f"   Código de estado: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Error verificando modelos en Ollama: {e}")
            logger.warning(f"   Continuando sin verificación...")
        except Exception as e:
            logger.error(f"❌ Error en verificación de modelo: {e}")
            raise e
    
    def _configurar_llm(self):
        """Configura LLM compartido como q_sistema_agentes_2.py"""
        try:
            import litellm
            
            # Configurar litellm para costos
            litellm.model_cost[f"ollama/{self.modelo_base}"] = {
                "input_cost_per_token": 0,
                "output_cost_per_token": 0,
                "max_tokens": 4096
            }
            
            # Crear LLM (EXACTAMENTE igual que q_sistema_agentes_2.py línea 157-160)
            self.llm = Ollama(
                model=f"ollama/{self.modelo_base}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info(f"✅ LLM configurado: {self.modelo_base}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLM: {e}")
            raise e
    
    def _cargar_recursos(self):
        """Carga ejemplos K y perfiles de estudiantes"""
        # Cargar ejemplos K
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
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        logger.info(f"📖 Cargado: {nombre_ejemplo}")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando {archivo}: {e}")
        
        # Cargar perfiles de estudiantes
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            perfiles_path = os.path.join(script_dir, self.perfiles_path)
            
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.perfiles_data = data.get('estudiantes', self._crear_perfiles_default())
        except Exception as e:
            logger.warning(f"⚠️ Error cargando perfiles: {e}")
            self.perfiles_data = self._crear_perfiles_default()
    
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
    
    def _crear_clasificador_semantico(self):
        """Sistema de clasificación semántica usando LLM como clasificador inteligente"""
        
        # Definiciones conceptuales generales (no frases específicas)
        self.dominios_conceptuales = {
            "INSPIRADOR": {
                "descripcion": "Maneja creatividad, narrativa, estilo, ambiente, historia y conceptos inspiradores",
                "ejemplos": ["cambiar la historia", "más creativo", "menos fantasioso", "ambiente diferente", "narrativa más realista"]
            },
            "PEDAGOGO": {
                "descripcion": "Maneja objetivos educativos, metodología, evaluación, competencias y estructura pedagógica",
                "ejemplos": ["objetivos más claros", "cambiar metodología", "más riguroso", "competencias específicas", "evaluación diferente"]
            },
            "ARQUITECTO": {
                "descripcion": "Maneja organización, estructura temporal, flujo de tareas, logística, distribución de trabajo y asignación específica de roles",
                "ejemplos": ["organizar mejor", "estructurar tareas", "menos tiempo", "quién hace qué", "más organizado", "tareas específicas", "asignación de roles", "tareas adaptadas", "distribución del trabajo"]
            },
            "DIFERENCIADOR": {
                "descripcion": "Maneja adaptaciones, personalización, inclusión y necesidades específicas de estudiantes",
                "ejemplos": ["adaptar para TEA", "más inclusivo", "personalizar", "necesidades especiales", "accesibilidad"]
            }
        }
        
        logger.info("✅ Clasificador semántico inteligente configurado (basado en LLM)")
    
    def _crear_agentes_dociles(self):
        """Crea agentes con prompts minimalistas pero efectivos"""
        
        # Tools compartidas
        self.tools = [
            ValidadorCoherenciaTool(),
            EjemplosKTool()
        ]
        
        # Agente Inspirador - Prompts dóciles (igual que q_sistema_agentes_2.py)
        self.agente_inspirador = Agent(
            role="Creador de Semillas Creativas",
            goal="Crear una semilla creativa inspiradora basándome en el contexto rico proporcionado",
            backstory="Soy un especialista en narrativas educativas. Adapto ideas según feedback específico y creo propuestas originales.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Agente Pedagogo
        self.agente_pedagogo = Agent(
            role="Estructurador Pedagógico",
            goal="Transformar la semilla creativa en estructura pedagógica sólida, incorporando feedback específico",
            backstory="Soy un experto curricular. Ajusto metodologías según indicaciones precisas manteniendo rigor académico.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Agente Arquitecto
        self.agente_arquitecto = Agent(
            role="Diseñador de Experiencias",
            goal="Crear el flujo temporal y arquitectura de la experiencia educativa según feedback recibido",
            backstory="Soy un especialista en diseño de experiencias. Modifico estructuras según feedback específico.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Agente Diferenciador
        self.agente_diferenciador = Agent(
            role="Personalizador Educativo",
            goal="Adaptar la experiencia a cada estudiante según perfiles y feedback de inclusión",
            backstory="Soy un psicopedagogo. Personalizo según perfiles específicos y feedback de inclusión.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        logger.info("✅ Agentes dóciles creados")
    
    def _crear_quantum_enhancer(self):
        """Inicializa el quantum enhancer para validación"""
        try:
            self.quantum_enhancer = QuantumEnhancer(QISKIT_CONFIG)
            logger.info("✅ Quantum Enhancer inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando Quantum Enhancer: {e}")
            self.quantum_enhancer = None
    
    def _analizar_feedback_semantico(self, prompt_feedback: str) -> FeedbackInteligente:
        """Analiza feedback usando LLM como clasificador inteligente"""
        
        try:
            # TEMPORAL: Deshabilitar LLM para clasificación hasta que funcionen los agentes principales
            # Usar solo clasificación fallback
            return self._clasificacion_fallback(prompt_feedback, "LLM temporalmente deshabilitado para debugging")
            
            # Crear prompt para clasificación inteligente (DESHABILITADO TEMPORALMENTE)
            prompt_clasificador_disabled = f"""
Analiza este feedback de usuario y determina qué agente educativo debería recibirlo.

FEEDBACK DEL USUARIO: "{prompt_feedback}"

AGENTES DISPONIBLES:

INSPIRADOR: {self.dominios_conceptuales["INSPIRADOR"]["descripcion"]}
Ejemplos: {", ".join(self.dominios_conceptuales["INSPIRADOR"]["ejemplos"])}

PEDAGOGO: {self.dominios_conceptuales["PEDAGOGO"]["descripcion"]}
Ejemplos: {", ".join(self.dominios_conceptuales["PEDAGOGO"]["ejemplos"])}

ARQUITECTO: {self.dominios_conceptuales["ARQUITECTO"]["descripcion"]}
Ejemplos: {", ".join(self.dominios_conceptuales["ARQUITECTO"]["ejemplos"])}

DIFERENCIADOR: {self.dominios_conceptuales["DIFERENCIADOR"]["descripcion"]}
Ejemplos: {", ".join(self.dominios_conceptuales["DIFERENCIADOR"]["ejemplos"])}

INSTRUCCIONES:
1. Analiza el feedback del usuario
2. Determina qué agente es más apropiado basándote en el contenido semántico
3. Si el feedback abarca múltiples áreas, elige el área PRINCIPAL
4. Responde SOLO con una de estas opciones: INSPIRADOR, PEDAGOGO, ARQUITECTO, DIFERENCIADOR

RESPUESTA:"""
            
            # Usar LLM compartido para clasificar
            respuesta_llm = self.llm.invoke(prompt_clasificador).strip().upper()
            
            # Validar respuesta
            agentes_validos = ["INSPIRADOR", "PEDAGOGO", "ARQUITECTO", "DIFERENCIADOR"]
            if respuesta_llm not in agentes_validos:
                logger.warning(f"⚠️ Respuesta LLM inválida: {respuesta_llm}. Usando GENERAL")
                agente_objetivo = "general"
                confianza = 0.3
            else:
                agente_objetivo = respuesta_llm.lower()
                confianza = 0.8  # Alta confianza en LLM
            
            # Generar análisis de intención más detallado
            intencion_detectada = self._generar_analisis_intencion(prompt_feedback, agente_objetivo)
            
            # Generar instrucciones específicas
            agente_enum = AgenteSemantico(agente_objetivo) if agente_objetivo != "general" else AgenteSemantico.GENERAL
            instrucciones = self._generar_instrucciones_especificas(prompt_feedback, agente_enum)
            
            return FeedbackInteligente(
                prompt_usuario=prompt_feedback,
                agente_objetivo=agente_objetivo,
                intencion_detectada=intencion_detectada,
                confianza=confianza,
                instrucciones_procesadas=instrucciones,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Error en análisis semántico con LLM: {e}")
            
            # Fallback a clasificación simple basada en keywords
            return self._clasificacion_fallback(prompt_feedback, str(e))
    
    def _clasificacion_fallback(self, feedback: str, error: str) -> FeedbackInteligente:
        """Clasificación fallback simple cuando LLM falla"""
        
        feedback_lower = feedback.lower()
        
        # Keywords simples para clasificación básica
        if any(word in feedback_lower for word in ["tareas", "organizar", "estructura", "quien", "asignar", "roles"]):
            agente_objetivo = "arquitecto"
            confianza = 0.6
        elif any(word in feedback_lower for word in ["historia", "narrativa", "creativo", "artístico", "misterio"]):
            agente_objetivo = "inspirador" 
            confianza = 0.6
        elif any(word in feedback_lower for word in ["objetivos", "pedagógico", "metodología", "evaluación"]):
            agente_objetivo = "pedagogo"
            confianza = 0.6
        elif any(word in feedback_lower for word in ["adaptar", "TEA", "TDAH", "personalizar", "inclusivo"]):
            agente_objetivo = "diferenciador"
            confianza = 0.6
        else:
            agente_objetivo = "general"
            confianza = 0.3
        
        return FeedbackInteligente(
            prompt_usuario=feedback,
            agente_objetivo=agente_objetivo,
            intencion_detectada=f"Clasificación fallback: {agente_objetivo} (LLM no disponible)",
            confianza=confianza,
            instrucciones_procesadas=f"""
🔧 FEEDBACK DEL USUARIO (MODO FALLBACK):
"{feedback}"

INSTRUCCIONES:
- El LLM no está disponible, usando clasificación básica
- Interpreta este feedback según tu área de expertise
- Error LLM: {error}
""",
            timestamp=datetime.now().isoformat()
        )
    
    def _generar_analisis_intencion(self, feedback: str, agente_objetivo: str) -> str:
        """Genera análisis de intención más detallado usando LLM"""
        
        try:
            prompt_intencion = f"""
Analiza la intención específica de este feedback educativo:

FEEDBACK: "{feedback}"
AGENTE ASIGNADO: {agente_objetivo.upper()}

Genera un resumen breve (1 línea) de qué quiere cambiar o mejorar el usuario específicamente.

FORMATO: "El usuario quiere [acción específica] para [objetivo]"

RESPUESTA:"""
            
            # Usar LLM compartido para análisis de intención
            respuesta = self.llm.invoke(prompt_intencion).strip()
            return respuesta if respuesta else f"Modificar {agente_objetivo} según feedback del usuario"
            
        except Exception as e:
            logger.warning(f"⚠️ Error generando análisis de intención: {e}")
            return f"Modificar {agente_objetivo} - análisis automático"
    
    def _generar_instrucciones_especificas(self, prompt: str, agente: AgenteSemantico) -> str:
        """Genera instrucciones específicas por agente"""
        
        plantillas = {
            AgenteSemantico.INSPIRADOR: f"""
🎭 FEEDBACK DEL USUARIO PARA CREATIVIDAD E INSPIRACIÓN:
"{prompt}"

INSTRUCCIONES:
- Interpreta este feedback y aplícalo a los aspectos creativos, narrativos o inspiradores
- Mantén coherencia general pero prioriza la solicitud del usuario
- Adapta según el contexto específico de la actividad
""",
            AgenteSemantico.PEDAGOGO: f"""
📚 FEEDBACK DEL USUARIO PARA PEDAGOGÍA:
"{prompt}"

INSTRUCCIONES:
- Interpreta este feedback y aplícalo a los aspectos pedagógicos y metodológicos
- Ajusta según las necesidades educativas mencionadas
- Mantén rigor académico apropiado para el nivel
""",
            AgenteSemantico.ARQUITECTO: f"""
🏗️ FEEDBACK DEL USUARIO PARA ORGANIZACIÓN:
"{prompt}"

INSTRUCCIONES:
- Interpreta este feedback y aplícalo a la organización, estructura y flujo de tareas
- Reorganiza según las necesidades de timing y logística mencionadas
- Mantén coherencia en la experiencia general
""",
            AgenteSemantico.DIFERENCIADOR: f"""
🎯 FEEDBACK DEL USUARIO PARA PERSONALIZACIÓN:
"{prompt}"

INSTRUCCIONES:
- Interpreta este feedback y aplícalo a las adaptaciones y personalización
- Ajusta según las necesidades de inclusión o diferenciación mencionadas
- Mantén accesibilidad para todos los estudiantes
""",
            AgenteSemantico.GENERAL: f"""
🔧 FEEDBACK GENERAL DEL USUARIO:
"{prompt}"

INSTRUCCIONES:
- Interpreta este feedback según tu área de expertise específica
- Aplica los cambios de manera apropiada para tu rol
- Mantén coherencia con el objetivo general de la actividad
"""
        }
        
        return plantillas.get(agente, plantillas[AgenteSemantico.GENERAL])
    
    def _construir_contexto_rico(self, 
                                prompt_inicial: str,
                                materia: str,
                                tema: Optional[str],
                                complejidad: str,
                                requisitos_complejidad: Optional[RequisitosComplejidad],
                                fase_anterior: Optional[str],
                                objetivo_fase: str,
                                feedback_acumulado: List[FeedbackInteligente],
                                quantum_insights: str = "") -> ContextoRico:
        """Construye contexto rico separado para compensar prompts minimalistas"""
        
        # Seleccionar ejemplos K relevantes
        ejemplos_relevantes = {}
        if materia.lower() in ['matematicas', 'mates']:
            for key in ['k_sonnet_supermercado', 'k_feria_acertijos']:
                if key in self.ejemplos_k:
                    ejemplos_relevantes[key] = self.ejemplos_k[key][:1000]
        elif materia.lower() in ['ciencias', 'naturales']:
            if 'k_celula' in self.ejemplos_k:
                ejemplos_relevantes['k_celula'] = self.ejemplos_k['k_celula'][:1000]
        elif materia.lower() in ['lengua', 'lenguaje']:
            if 'k_piratas' in self.ejemplos_k:
                ejemplos_relevantes['k_piratas'] = self.ejemplos_k['k_piratas'][:1000]
        
        # Si no hay ejemplos específicos, usar uno genérico
        if not ejemplos_relevantes and 'k_piratas' in self.ejemplos_k:
            ejemplos_relevantes['k_piratas'] = self.ejemplos_k['k_piratas'][:1000]
        
        return ContextoRico(
            prompt_inicial=prompt_inicial,
            materia=materia,
            tema=tema,
            complejidad=complejidad,
            requisitos_complejidad=requisitos_complejidad,
            ejemplos_k=ejemplos_relevantes,
            perfiles_estudiantes=self.perfiles_data,
            feedback_acumulado=feedback_acumulado,
            fase_anterior=fase_anterior,
            objetivo_fase=objetivo_fase,
            quantum_insights=quantum_insights
        )
    
    def _crear_contexto_texto(self, contexto_rico: ContextoRico) -> str:
        """Convierte ContextoRico en texto estructurado para el LLM"""
        
        contexto_texto = f"""
════════════════════════════════════════════════════════════════════════════════
CONTEXTO RICO PARA AGENTE DÓCIL
════════════════════════════════════════════════════════════════════════════════

PROMPT INICIAL DEL USUARIO:
{contexto_rico.prompt_inicial}

INFORMACIÓN BÁSICA:
- Materia: {contexto_rico.materia}
- Tema: {contexto_rico.tema or 'General'}
- Complejidad solicitada: {contexto_rico.complejidad}
- Objetivo de esta fase: {contexto_rico.objetivo_fase}

REQUISITOS DE COMPLEJIDAD {contexto_rico.requisitos_complejidad.nivel.value.upper() if contexto_rico.requisitos_complejidad else 'NO ESPECIFICADO'}:
{f"- Duración: {contexto_rico.requisitos_complejidad.duracion_recomendada}" if contexto_rico.requisitos_complejidad else ""}
{f"- Enfoque pedagógico: {contexto_rico.requisitos_complejidad.enfoque_pedagogico}" if contexto_rico.requisitos_complejidad else ""}
{f"- Nivel de vocabulario: {contexto_rico.requisitos_complejidad.nivel_vocabulario}" if contexto_rico.requisitos_complejidad else ""}

ELEMENTOS OBLIGATORIOS PARA ESTE NIVEL:
{chr(10).join([f"✅ {elem}" for elem in contexto_rico.requisitos_complejidad.elementos_obligatorios]) if contexto_rico.requisitos_complejidad else "No especificado"}

ELEMENTOS PROHIBIDOS PARA ESTE NIVEL:
{chr(10).join([f"❌ {elem}" for elem in contexto_rico.requisitos_complejidad.elementos_prohibidos]) if contexto_rico.requisitos_complejidad else "No especificado"}

CRITERIOS DE EVALUACIÓN ESPERADOS:
{chr(10).join([f"🎯 {crit}" for crit in contexto_rico.requisitos_complejidad.criterios_evaluacion]) if contexto_rico.requisitos_complejidad else "No especificado"}

{f"INSIGHTS CUÁNTICOS PRE-PROCESADOS:{chr(10)}{contexto_rico.quantum_insights}" if contexto_rico.quantum_insights else ""}

EJEMPLOS DE CALIDAD K_ PARA INSPIRACIÓN:
"""
        
        for nombre, contenido in contexto_rico.ejemplos_k.items():
            contexto_texto += f"\n--- {nombre.upper()} ---\n{contenido}\n"
        
        contexto_texto += f"""
ESTUDIANTES REALES DEL AULA (USAR EXACTAMENTE ESTOS):
"""
        for estudiante in contexto_rico.perfiles_estudiantes:
            contexto_texto += f"- {estudiante['id']} {estudiante['nombre']}: {estudiante.get('temperamento', 'N/A')}, {estudiante.get('canal_preferido', 'N/A')}"
            if estudiante.get('diagnostico_formal', 'ninguno') != 'ninguno':
                contexto_texto += f", {estudiante['diagnostico_formal']}"
            contexto_texto += "\n"
        
        if contexto_rico.fase_anterior:
            contexto_texto += f"\nFASE ANTERIOR COMPLETADA: {contexto_rico.fase_anterior}"
        
        # Feedback acumulado
        if contexto_rico.feedback_acumulado:
            contexto_texto += f"\n\nFEEDBACK ACUMULADO DEL USUARIO:\n"
            for i, feedback in enumerate(contexto_rico.feedback_acumulado, 1):
                contexto_texto += f"{i}. [{feedback.agente_objetivo.upper()}] {feedback.prompt_usuario}\n"
                contexto_texto += f"   Instrucciones: {feedback.instrucciones_procesadas}\n"
        
        contexto_texto += f"""
════════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES FINALES:
- Usa EXACTAMENTE los 8 estudiantes listados arriba
- Inspírate en los ejemplos K_ pero crea algo NUEVO
- Si hay feedback del usuario, es PRIORIDAD MÁXIMA
- Mantén coherencia con el prompt inicial
- Crea contenido apropiado para 4º Primaria
- ADAPTA LA COMPLEJIDAD según el nivel solicitado: {contexto_rico.complejidad}
- Ajusta vocabulario, conceptos y actividades al nivel de complejidad indicado
════════════════════════════════════════════════════════════════════════════════
"""
        
        return contexto_texto
    
    def _validar_con_quantum_enhancer(self, actividad: str, materia: str, tema: str, intento: int) -> ResultadoValidacion:
        """Valida actividad usando quantum enhancer"""
        if not self.quantum_enhancer:
            return ResultadoValidacion(0.8, "Validación cuántica no disponible", True, intento)
        
        try:
            puntuacion, feedback = self.quantum_enhancer.validar_actividad_cuanticamente(
                actividad, materia, tema
            )
            
            aprobado = puntuacion >= self.quantum_enhancer.UMBRAL_VALIDACION_CUANTICA
            
            return ResultadoValidacion(puntuacion, feedback, aprobado, intento)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en validación cuántica: {e}")
            return ResultadoValidacion(0.8, f"Error en validación: {e}", True, intento)
    
    def _solicitar_feedback_inteligente(self, fase: str, contenido_previo: str) -> List[FeedbackInteligente]:
        """Solicita feedback usando sistema semántico inteligente"""
        
        print(f"\n" + "="*70)
        print(f"🧠 FEEDBACK SEMÁNTICO INTELIGENTE - {fase.upper()}")
        print("="*70)
        
        # Mostrar resumen del contenido
        lineas = contenido_previo.split('\n')[:6]
        for linea in lineas:
            if linea.strip():
                print(f"📄 {linea[:65]}{'...' if len(linea) > 65 else ''}")
        
        print(f"\n❓ ¿Qué quieres cambiar o mejorar de esta {fase}?")
        print("💡 Puedes escribir en lenguaje natural:")
        print("   • 'Hazlo más dinámico y corto'")
        print("   • 'Adapta mejor para estudiantes con TEA'") 
        print("   • 'Cambia la historia por algo más realista'")
        print("   • 'Reorganiza las fases temporales'")
        print("\n1. ✅ Perfecto, continúa sin cambios")
        print("2. 💬 Dar feedback en lenguaje natural")
        
        while True:
            try:
                opcion = input("\n👉 Selecciona (1-2): ").strip()
                
                if opcion == "1":
                    print("✅ Continuando sin cambios...")
                    return []
                elif opcion == "2":
                    break
                else:
                    print("❌ Por favor, selecciona 1 o 2")
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado")
                return []
        
        feedback_list = []
        
        while True:
            print(f"\n💬 Escribe tu feedback (o 'fin' para terminar):")
            try:
                prompt_feedback = input("🗣️ Tu feedback: ").strip()
                
                if prompt_feedback.lower() in ['fin', 'terminar', 'listo', 'ya']:
                    break
                
                if not prompt_feedback:
                    print("❌ Por favor, escribe algo o 'fin' para terminar")
                    continue
                
                # Análisis semántico automático
                feedback_analizado = self._analizar_feedback_semantico(prompt_feedback)
                
                # Mostrar análisis
                print(f"\n🧠 ANÁLISIS AUTOMÁTICO:")
                print(f"   🎯 Agente objetivo: {feedback_analizado.agente_objetivo}")
                print(f"   🎯 Confianza: {feedback_analizado.confianza:.1%}")
                print(f"   🎯 Intención: {feedback_analizado.intencion_detectada}")
                
                # Confirmar
                confirmar = input(f"\n¿Es correcto? (s/n): ").strip().lower()
                if confirmar in ['s', 'si', 'sí', 'yes', 'y', '']:
                    feedback_list.append(feedback_analizado)
                    print(f"✅ Feedback agregado para {feedback_analizado.agente_objetivo}")
                else:
                    print("❌ Feedback descartado. Puedes intentar con otras palabras.")
                
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado")
                break
            except Exception as e:
                print(f"❌ Error procesando feedback: {e}")
                continue
        
        if feedback_list:
            print(f"\n✅ {len(feedback_list)} feedback(s) procesado(s)")
        
        return feedback_list
    
    def _aplicar_feedback_a_agente(self, feedback_list: List[FeedbackInteligente], agente_actual: str) -> str:
        """Aplica feedback relevante al agente actual"""
        
        if not feedback_list:
            return ""
        
        # Filtrar feedback relevante
        feedback_relevante = [f for f in feedback_list 
                             if f.agente_objetivo == agente_actual or f.agente_objetivo == "general"]
        
        # Propagación crítica: feedback de arquitectura a todos
        feedback_arquitectura = [f for f in feedback_list if f.agente_objetivo == "arquitecto"]
        if feedback_arquitectura and agente_actual != "arquitecto":
            for fb in feedback_arquitectura:
                if any(keyword in fb.prompt_usuario.lower() 
                       for keyword in ["semana", "día", "duración", "tiempo", "organizar"]):
                    feedback_relevante.append(fb)
        
        if not feedback_relevante:
            return ""
        
        instrucciones = "\n🎯 FEEDBACK ESPECÍFICO DEL USUARIO (PRIORIDAD MÁXIMA):\n"
        for i, feedback in enumerate(feedback_relevante, 1):
            if feedback.agente_objetivo == "arquitecto" and agente_actual != "arquitecto":
                instrucciones += f"\n{i}. 🕐 DURACIÓN/TIEMPO CRÍTICO: {feedback.prompt_usuario}\n"
                instrucciones += f"   → APLICA esta consideración temporal en tu sección\n"
            else:
                instrucciones += f"\n{i}. {feedback.instrucciones_procesadas}\n"
        
        instrucciones += "\n⚠️ ESTAS INSTRUCCIONES TIENEN PRIORIDAD ABSOLUTA.\n"
        
        return instrucciones
    
    def _detectar_materia_y_tema(self, prompt: str) -> Tuple[str, Optional[str]]:
        """Detecta automáticamente materia y tema del prompt"""
        
        prompt_lower = prompt.lower()
        
        # Detectar materia
        materias = {
            'matematicas': ['matemáticas', 'mates', 'números', 'cálculo', 'geometría', 'fracciones', 'suma', 'resta'],
            'lengua': ['lengua', 'idioma', 'escritura', 'lectura', 'gramática', 'literatura', 'texto', 'palabras'],
            'ciencias': ['ciencias', 'biología', 'física', 'química', 'naturales', 'científico', 'células', 'animales', 'plantas']
        }
        
        materia_detectada = None
        for materia, keywords in materias.items():
            if any(keyword in prompt_lower for keyword in keywords):
                materia_detectada = materia
                break
        
        # Detectar tema
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
    
    def _obtener_requisitos_complejidad(self, nivel: str) -> RequisitosComplejidad:
        """Obtiene requisitos específicos según nivel de complejidad"""
        
        requisitos_por_nivel = {
            "básica": RequisitosComplejidad(
                nivel=NivelComplejidad.BASICA,
                descripcion="Conceptos fundamentales con actividades simples y directas",
                elementos_obligatorios=[
                    "Vocabulario simple y claro apropiado para 4º primaria",
                    "Instrucciones paso a paso muy detalladas",
                    "Ejemplos concretos y familiares",
                    "Actividades con objetivos claros y medibles",
                    "Roles simples y bien definidos para cada estudiante",
                    "Evaluación directa y observable"
                ],
                elementos_prohibidos=[
                    "Conceptos abstractos complejos",
                    "Vocabulario técnico sin explicación",
                    "Tareas abiertas sin guía",
                    "Múltiples objetivos simultáneos",
                    "Análisis profundo o reflexión compleja"
                ],
                duracion_recomendada="1-2 sesiones de 45 minutos",
                enfoque_pedagogico="Aprendizaje directo con práctica guiada",
                nivel_vocabulario="Básico de 4º primaria con explicaciones claras",
                criterios_evaluacion=[
                    "Comprensión de conceptos básicos",
                    "Participación activa en actividades",
                    "Completitud de tareas asignadas"
                ]
            ),
            
            "intermedia": RequisitosComplejidad(
                nivel=NivelComplejidad.INTERMEDIA,
                descripcion="Conceptos con aplicación práctica y actividades moderadamente complejas",
                elementos_obligatorios=[
                    "Vocabulario apropiado con algunos términos nuevos explicados",
                    "Combinación de trabajo individual y colaborativo",
                    "Aplicación práctica de conceptos",
                    "Conexiones entre ideas y conocimiento previo",
                    "Roles diferenciados y rotativos",
                    "Evaluación formativa y sumativa"
                ],
                elementos_prohibidos=[
                    "Simplificación excesiva",
                    "Conceptos demasiado abstractos",
                    "Tareas repetitivas sin desafío",
                    "Evaluación únicamente memorística"
                ],
                duracion_recomendada="2-3 sesiones de 45 minutos",
                enfoque_pedagogico="Aprendizaje constructivo con aplicación práctica",
                nivel_vocabulario="Intermedio con introducción de términos técnicos",
                criterios_evaluacion=[
                    "Aplicación correcta de conceptos",
                    "Colaboración efectiva en grupo",
                    "Transferencia de aprendizaje a nuevas situaciones"
                ]
            ),
            
            "avanzada": RequisitosComplejidad(
                nivel=NivelComplejidad.AVANZADA,
                descripcion="Conceptos complejos con actividades desafiantes que requieren pensamiento crítico",
                elementos_obligatorios=[
                    "Vocabulario técnico apropiado con definiciones",
                    "Análisis y síntesis de información",
                    "Resolución de problemas complejos",
                    "Argumentación y justificación de ideas",
                    "Roles especializados y liderazgo rotativo",
                    "Autoevaluación y evaluación entre pares"
                ],
                elementos_prohibidos=[
                    "Instrucciones demasiado directivas",
                    "Respuestas únicas o cerradas",
                    "Falta de desafío intelectual",
                    "Simplificación excesiva de conceptos"
                ],
                duracion_recomendada="3-4 sesiones de 45 minutos",
                enfoque_pedagogico="Aprendizaje por indagación con pensamiento crítico",
                nivel_vocabulario="Avanzado con terminología especializada",
                criterios_evaluacion=[
                    "Análisis crítico de información",
                    "Argumentación fundamentada",
                    "Innovación en soluciones propuestas",
                    "Liderazgo en trabajo colaborativo"
                ]
            ),
            
            "experta": RequisitosComplejidad(
                nivel=NivelComplejidad.EXPERTA,
                descripcion="Máxima complejidad con actividades muy desafiantes y análisis profundo",
                elementos_obligatorios=[
                    "Vocabulario especializado y técnico",
                    "Investigación independiente y dirigida",
                    "Síntesis de múltiples fuentes de información",
                    "Creación de productos originales",
                    "Metacognición y reflexión profunda",
                    "Evaluación multidimensional y autónoma"
                ],
                elementos_prohibidos=[
                    "Actividades rutinarias o mecánicas",
                    "Instrucciones excesivamente guiadas",
                    "Falta de oportunidades para innovación",
                    "Evaluación superficial"
                ],
                duracion_recomendada="1 semana (4-5 sesiones)",
                enfoque_pedagogico="Aprendizaje autónomo con mentoría especializada",
                nivel_vocabulario="Experto con terminología académica",
                criterios_evaluacion=[
                    "Originalidad en enfoques y soluciones",
                    "Profundidad de análisis y reflexión",
                    "Capacidad de síntesis interdisciplinaria",
                    "Liderazgo intelectual y creatividad"
                ]
            )
        }
        
        return requisitos_por_nivel.get(nivel, requisitos_por_nivel["intermedia"])
    
    def _solicitar_complejidad(self) -> tuple[str, RequisitosComplejidad]:
        """Solicita el nivel de complejidad de la actividad"""
        
        print(f"\n" + "="*60)
        print(f"🎚️ SELECCIÓN DE COMPLEJIDAD DE LA ACTIVIDAD")
        print("="*60)
        
        print("Selecciona el nivel de complejidad para la actividad:")
        print("1. 🟢 BÁSICA - Conceptos fundamentales, actividades simples")
        print("2. 🟡 INTERMEDIA - Conceptos con aplicación, actividades moderadas")  
        print("3. 🔴 AVANZADA - Conceptos complejos, actividades desafiantes")
        print("4. 🏆 EXPERTA - Máxima complejidad, actividades muy desafiantes")
        
        complejidades = {
            "1": ("básica", "Conceptos fundamentales con actividades simples y directas"),
            "2": ("intermedia", "Conceptos con aplicación práctica y actividades moderadamente complejas"),
            "3": ("avanzada", "Conceptos complejos con actividades desafiantes que requieren pensamiento crítico"),
            "4": ("experta", "Máxima complejidad con actividades muy desafiantes y análisis profundo")
        }
        
        while True:
            try:
                opcion = input("\n👉 Selecciona complejidad (1-4): ").strip()
                
                if opcion in complejidades:
                    nivel, descripcion = complejidades[opcion]
                    requisitos = self._obtener_requisitos_complejidad(nivel)
                    
                    print(f"✅ Complejidad seleccionada: {nivel.upper()}")
                    print(f"📝 {descripcion}")
                    print(f"⏱️ Duración: {requisitos.duracion_recomendada}")
                    print(f"🎯 Enfoque: {requisitos.enfoque_pedagogico}")
                    
                    return f"{nivel} - {descripcion}", requisitos
                else:
                    print("❌ Por favor, selecciona una opción válida (1-4)")
                    
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado. Usando complejidad intermedia por defecto.")
                requisitos_default = self._obtener_requisitos_complejidad("intermedia")
                return "intermedia - Conceptos con aplicación práctica y actividades moderadamente complejas", requisitos_default
            except Exception as e:
                print(f"❌ Error en selección: {e}")
                continue
    
    def generar_actividad_hibrida_optimizada(self, prompt_inicial: str) -> ActividadEducativa:
        """
        Método principal que genera actividad usando el sistema híbrido optimizado
        """
        
        logger.info("🚀 Iniciando generación híbrida optimizada")
        
        # 1. DETECCIÓN AUTOMÁTICA
        materia, tema = self._detectar_materia_y_tema(prompt_inicial)
        
        if not materia:
            materia = input("📚 ¿Qué materia? (matematicas/lengua/ciencias): ").strip().lower()
        
        print(f"\n🎯 Materia detectada: {materia}")
        print(f"🎯 Tema detectado: {tema or 'General'}")
        
        # 2. SELECCIÓN DE COMPLEJIDAD
        complejidad, requisitos_complejidad = self._solicitar_complejidad()
        
        try:
            feedback_acumulado = []
            resultados = {}
            
            # 2. PREPROCESADO CUÁNTICO (si está disponible)
            quantum_insights = ""
            if self.quantum_enhancer:
                quantum_insights = self.quantum_enhancer.analizar_dificultad_cuantica(
                    materia, tema, ""
                )
                logger.info(f"✨ Insights cuánticos: {quantum_insights}")
            
            # ========================================================
            # FASE 1: INSPIRACIÓN
            # ========================================================
            print(f"\n🎭 FASE 1: INSPIRACIÓN")
            
            contexto_inspiracion = self._construir_contexto_rico(
                prompt_inicial, materia, tema, complejidad, requisitos_complejidad, None,
                "Crear semilla creativa inspiradora", feedback_acumulado, quantum_insights
            )
            
            # Retry con validación cuántica para inspiración
            for intento in range(3):
                print(f"   🔄 Intento {intento + 1}/3")
                
                tarea_inspiracion = Task(
                    description=f"""
{self._crear_contexto_texto(contexto_inspiracion)}

TAREA ESPECÍFICA:
Como Creador de Semillas Creativas, genera una semilla creativa inspiradora para esta actividad educativa.
Utiliza el contexto rico proporcionado para crear una propuesta original y motivadora.
Inspírate en los ejemplos K_ pero crea algo NUEVO basado en el prompt inicial del usuario.
                    """,
                    agent=self.agente_inspirador,
                    expected_output="Semilla creativa inspiradora para la actividad educativa"
                )
                
                crew_inspiracion = Crew(
                    agents=[self.agente_inspirador],
                    tasks=[tarea_inspiracion],
                    process=Process.sequential,
                    verbose=False
                )
                
                resultado_inspiracion = crew_inspiracion.kickoff()
                
                # Validación cuántica
                validacion = self._validar_con_quantum_enhancer(
                    str(resultado_inspiracion), materia, tema or "general", intento + 1
                )
                
                if validacion.aprobado:
                    print(f"   ✅ Validación cuántica aprobada (puntuación: {validacion.puntuacion:.2f})")
                    break
                else:
                    print(f"   ❌ Validación fallida (puntuación: {validacion.puntuacion:.2f})")
                    if intento < 2:
                        print(f"   🔄 Reintentando con feedback cuántico...")
                        # Agregar feedback cuántico al contexto
                        contexto_inspiracion.quantum_insights += f"\n\nFEEDBACK CUÁNTICO: {validacion.feedback_cuantico}"
            
            resultados['inspiracion'] = str(resultado_inspiracion)
            
            # Solicitar feedback humano
            feedback_inspiracion = self._solicitar_feedback_inteligente("inspiración", str(resultado_inspiracion))
            feedback_acumulado.extend(feedback_inspiracion)
            
            # ========================================================
            # FASE 2: PEDAGOGÍA
            # ========================================================
            print(f"\n📚 FASE 2: PEDAGOGÍA")
            
            contexto_pedagogia = self._construir_contexto_rico(
                prompt_inicial, materia, tema, complejidad, requisitos_complejidad, "inspiración",
                "Estructurar pedagógicamente la semilla creativa", feedback_acumulado, quantum_insights
            )
            
            contexto_pedagogia_texto = f"""
RESULTADO DE LA FASE ANTERIOR (INSPIRACIÓN):
{str(resultado_inspiracion)}

{self._crear_contexto_texto(contexto_pedagogia)}
"""
            
            tarea_pedagogia = Task(
                description=f"""
{contexto_pedagogia_texto}

{self._aplicar_feedback_a_agente(feedback_acumulado, "pedagogo")}

TAREA ESPECÍFICA:
Como Estructurador Pedagógico, toma la semilla creativa anterior y desarróllala en una estructura pedagógica sólida.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
NO repitas el contenido anterior, sino que MEJORA y ESTRUCTURA la propuesta.
                """,
                agent=self.agente_pedagogo,
                expected_output="Estructura pedagógica mejorada basada en la semilla creativa anterior"
            )
            
            crew_pedagogia = Crew(
                agents=[self.agente_pedagogo],
                tasks=[tarea_pedagogia],
                process=Process.sequential,
                verbose=False
            )
            
            resultado_pedagogia = crew_pedagogia.kickoff()
            resultados['pedagogia'] = str(resultado_pedagogia)
            
            # Feedback humano
            feedback_pedagogia = self._solicitar_feedback_inteligente("estructura pedagógica", str(resultado_pedagogia))
            feedback_acumulado.extend(feedback_pedagogia)
            
            # ========================================================
            # FASE 3: ARQUITECTURA
            # ========================================================
            print(f"\n🏗️ FASE 3: ARQUITECTURA")
            
            contexto_arquitectura = self._construir_contexto_rico(
                prompt_inicial, materia, tema, complejidad, requisitos_complejidad, "pedagogía",
                "Diseñar arquitectura temporal y experiencial", feedback_acumulado, quantum_insights
            )
            
            contexto_arquitectura_texto = f"""
RESULTADO DE LA FASE ANTERIOR (PEDAGOGÍA):
{str(resultado_pedagogia)}

{self._crear_contexto_texto(contexto_arquitectura)}
"""
            
            tarea_arquitectura = Task(
                description=f"""
{contexto_arquitectura_texto}

{self._aplicar_feedback_a_agente(feedback_acumulado, "arquitecto")}

TAREA ESPECÍFICA:
Como Diseñador de Experiencias, toma la estructura pedagógica anterior y crea el flujo temporal y arquitectura de la experiencia.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
NO repitas el contenido anterior, sino que DISEÑA la experiencia temporal y logística.
                """,
                agent=self.agente_arquitecto,
                expected_output="Diseño de experiencia temporal basado en la estructura pedagógica anterior"
            )
            
            crew_arquitectura = Crew(
                agents=[self.agente_arquitecto],
                tasks=[tarea_arquitectura],
                process=Process.sequential,
                verbose=False
            )
            
            resultado_arquitectura = crew_arquitectura.kickoff()
            resultados['arquitectura'] = str(resultado_arquitectura)
            
            # Feedback humano
            feedback_arquitectura = self._solicitar_feedback_inteligente("arquitectura", str(resultado_arquitectura))
            feedback_acumulado.extend(feedback_arquitectura)
            
            # ========================================================
            # FASE 4: DIFERENCIACIÓN (FINAL)
            # ========================================================
            print(f"\n🎯 FASE 4: DIFERENCIACIÓN")
            
            contexto_diferenciacion = self._construir_contexto_rico(
                prompt_inicial, materia, tema, complejidad, requisitos_complejidad, "arquitectura",
                "Personalizar para cada estudiante específico", feedback_acumulado, quantum_insights
            )
            
            contexto_diferenciacion_texto = f"""
RESULTADO DE LA FASE ANTERIOR (ARQUITECTURA):
{str(resultado_arquitectura)}

{self._crear_contexto_texto(contexto_diferenciacion)}
"""
            
            tarea_diferenciacion = Task(
                description=f"""
{contexto_diferenciacion_texto}

{self._aplicar_feedback_a_agente(feedback_acumulado, "diferenciador")}

TAREA ESPECÍFICA:
Como Personalizador Educativo, toma la arquitectura de experiencia anterior y personalízala para cada estudiante específico.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
NO repitas el contenido anterior, sino que PERSONALIZA la experiencia para cada estudiante del aula.
                """,
                agent=self.agente_diferenciador,
                expected_output="Actividad personalizada para cada estudiante basada en la arquitectura anterior"
            )
            
            crew_diferenciacion = Crew(
                agents=[self.agente_diferenciador],
                tasks=[tarea_diferenciacion],
                process=Process.sequential,
                verbose=False
            )
            
            resultado_diferenciacion = crew_diferenciacion.kickoff()
            resultados['diferenciacion'] = str(resultado_diferenciacion)
            
            # ========================================================
            # VALIDACIÓN FINAL Y CONSTRUCCIÓN
            # ========================================================
            
            # Validación cuántica final
            contenido_completo = self._construir_contenido_final(resultados, feedback_acumulado, quantum_insights)
            
            validacion_final = self._validar_con_quantum_enhancer(
                contenido_completo, materia, tema or "general", 1
            )
            
            print(f"\n✅ VALIDACIÓN FINAL: {validacion_final.puntuacion:.2f}")
            print(f"📝 {validacion_final.feedback_cuantico}")
            
            return ActividadEducativa(
                id=f"hibrido_opt_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Híbrida Optimizada - {materia.title()}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="hibrido_optimizado",
                adaptaciones=["feedback_semantico", "validacion_cuantica", "contexto_rico", "agentes_dociles"],
                metadatos={
                    "total_estudiantes": 8,
                    "complejidad": complejidad,
                    "feedback_aplicado": len(feedback_acumulado),
                    "feedback_detalles": [
                        {
                            "agente": f.agente_objetivo,
                            "prompt": f.prompt_usuario,
                            "confianza": f.confianza,
                            "intencion": f.intencion_detectada
                        } for f in feedback_acumulado
                    ],
                    "quantum_insights": quantum_insights,
                    "validacion_final": {
                        "puntuacion": validacion_final.puntuacion,
                        "feedback": validacion_final.feedback_cuantico,
                        "aprobado": validacion_final.aprobado
                    },
                    "modelo_usado": self.modelo_base,
                    "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                    "version": "hibrido_optimizado_1.0"
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"❌ Error generando actividad híbrida: {e}")
            return ActividadEducativa(
                id=f"error_hibrido_{materia.lower() if materia else 'unknown'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error Híbrido - {materia or 'Unknown'}",
                materia=materia or "unknown",
                tema=tema or "tema general",
                contenido=f"Error generando actividad híbrida: {e}",
                estudiantes_objetivo=[],
                tipo="error_hibrido",
                adaptaciones=[],
                metadatos={"error": str(e), "version": "hibrido_optimizado_1.0"},
                timestamp=datetime.now().isoformat()
            )
    
    def _construir_contenido_final(self, resultados: Dict[str, str], feedback_acumulado: List[FeedbackInteligente], quantum_insights: str) -> str:
        """Construye el contenido final estructurado"""
        
        contenido = "=" * 100 + "\n"
        contenido += "ACTIVIDAD GENERADA CON SISTEMA HÍBRIDO OPTIMIZADO\n"
        contenido += "Combina: Feedback Semántico + Validación Cuántica + Contexto Rico + Agentes Dóciles\n"
        contenido += "=" * 100 + "\n\n"
        
        # Información del procesamiento
        if quantum_insights:
            contenido += "🔬 INSIGHTS CUÁNTICOS APLICADOS:\n"
            contenido += "-" * 50 + "\n"
            contenido += quantum_insights + "\n\n"
        
        # Feedback aplicado
        if feedback_acumulado:
            contenido += "🎯 FEEDBACK SEMÁNTICO APLICADO:\n"
            contenido += "-" * 50 + "\n"
            for i, feedback in enumerate(feedback_acumulado, 1):
                contenido += f"{i}. AGENTE: {feedback.agente_objetivo.upper()}\n"
                contenido += f"   Usuario: {feedback.prompt_usuario}\n"
                contenido += f"   Confianza: {feedback.confianza:.1%} | Intención: {feedback.intencion_detectada}\n\n"
        
        # Fases de desarrollo
        fases = {
            'inspiracion': '🎭 SEMILLA CREATIVA E INSPIRACIÓN',
            'pedagogia': '📚 ESTRUCTURA PEDAGÓGICA',
            'arquitectura': '🏗️ ARQUITECTURA DE LA EXPERIENCIA',
            'diferenciacion': '🎯 DIFERENCIACIÓN PERSONALIZADA'
        }
        
        for fase_key, fase_titulo in fases.items():
            if fase_key in resultados:
                contenido += f"\n{fase_titulo}\n"
                contenido += "=" * len(fase_titulo) + "\n"
                contenido += resultados[fase_key] + "\n\n"
        
        contenido += "\n" + "=" * 100 + "\n"
        contenido += "SISTEMA HÍBRIDO OPTIMIZADO - Versión 1.0\n"
        contenido += f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        contenido += "=" * 100 + "\n"
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_hibrido_optimizado") -> str:
        """Guarda la actividad generada"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write(f"ACTIVIDAD HÍBRIDA OPTIMIZADA\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo: {actividad.tipo}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 80 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\n")
            f.write("-" * 80 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("METADATOS DEL SISTEMA HÍBRIDO OPTIMIZADO:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad híbrida guardada en: {filepath}")
        return filepath

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal del sistema híbrido optimizado"""
    
    print("=" * 100)
    print("🚀 SISTEMA DE AGENTES HÍBRIDO OPTIMIZADO")
    print("Combina lo mejor de todos los sistemas anteriores")
    print("=" * 100)

    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        MODELO_BASE = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"

        print(f"\n🔧 Inicializando Sistema Híbrido:")
        print(f" Host Ollama: {OLLAMA_HOST}")
        print(f" Modelo base: {MODELO_BASE}")
        print(f" Características:")
        print(f"   ✅ Feedback semántico automático")
        print(f"   ✅ Validación cuántica con retry")
        print(f"   ✅ Contexto rico separado")
        print(f"   ✅ Agentes dóciles (prompts cortos)")
        print(f"   ✅ Human-in-the-loop inteligente")

        # Inicializar sistema
        sistema = SistemaAgentesHibridoOptimizado(
            ollama_host=OLLAMA_HOST,
            modelo_base=MODELO_BASE,
            perfiles_path=PERFILES_PATH
        )

        print("\n✅ Sistema Híbrido Optimizado inicializado correctamente!")
        print(f"📖 Ejemplos K cargados: {len(sistema.ejemplos_k)}")
        print(f"🔬 Quantum Enhancer: {'✅ Activo' if sistema.quantum_enhancer else '❌ No disponible'}")

        while True:
            print("\n" + "="*80)
            print("🎓 GENERACIÓN HÍBRIDA OPTIMIZADA")
            print("1. 🚀 Generar actividad con sistema híbrido completo")
            print("2. ❌ Salir")

            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                print("\n📝 Describe tu actividad ideal:")
                print("Ejemplo: 'Actividad colaborativa de matemáticas sobre fracciones")
                print("         para estudiantes de 4º primaria, inclusiva para TEA'")
                prompt_inicial = input("\n✨ Tu prompt: ").strip()
                
                if not prompt_inicial:
                    print("❌ Por favor, proporciona un prompt")
                    continue
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_hibrida_optimizada(prompt_inicial)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n🎉 ACTIVIDAD HÍBRIDA GENERADA EXITOSAMENTE!")
                print(f"⏱️  Tiempo: {duration:.1f}s")
                print(f"📄 ID: {actividad.id}")
                print(f"📁 Archivo: {archivo}")
                print(f"🎯 Feedback aplicado: {actividad.metadatos.get('feedback_aplicado', 0)} elementos")
                
                if 'validacion_final' in actividad.metadatos:
                    val = actividad.metadatos['validacion_final']
                    print(f"🔬 Validación cuántica: {val['puntuacion']:.2f} ({'✅ Aprobado' if val['aprobado'] else '❌ Rechazado'})")
                
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")

    except Exception as e:
        print(f"\n❌ Error inicializando sistema híbrido: {e}")
        print("\n💡 Verifica que:")
        print(" 1. Ollama esté ejecutándose en el host especificado")
        print(" 2. El modelo especificado esté disponible")
        print(" 3. El archivo quantum_enhancer.py esté disponible")
        print(" 4. Los archivos de perfiles y ejemplos K estén en sus rutas")
        print(" 5. Las dependencias estén instaladas (crewai, langchain-community)")

if __name__ == "__main__":
    main()