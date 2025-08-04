#!/usr/bin/env python3
"""
Sistema Q-Agents v2 - Human-in-the-Loop con Feedback Estructurado
Arquitectura rediseñada que separa 'qué hacer' (feedback) de 'cómo hacerlo' (expertise)
Agentes dóciles + Contexto rico + Feedback estructurado
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import logging
from enum import Enum
import re
from difflib import SequenceMatcher

os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

os.environ["HTTPX_TIMEOUT"] = "120"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Q_AGENTS_V2")

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from crewai_tools import FileReadTool, DirectoryReadTool
    
    from langchain_community.llms import Ollama
    logger.info("✅ Usando langchain-community.llms.Ollama (compatible con CrewAI)")
        
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    logger.error("💡 Instala dependencias: pip install crewai crewai-tools langchain-community")
    raise ImportError("Dependencias no están disponibles")


# ==== ENUMS Y DATA CLASSES ====
@dataclass
class FeedbackFlexible:
    prompt_usuario: str
    agente_objetivo: str
    intencion_detectada: str
    confianza: float
    instrucciones_procesadas: str

class AgenteSemantico(Enum):
    INSPIRADOR = "inspirador"
    PEDAGOGO = "pedagogo" 
    ARQUITECTO = "arquitecto"
    DIFERENCIADOR = "diferenciador"
    GENERAL = "general"

@dataclass
class ContextoRico:
    prompt_inicial: str
    materia: str
    tema: Optional[str]
    ejemplos_k: Dict[str, str]
    perfiles_estudiantes: List[Dict]
    feedback_acumulado: List[FeedbackFlexible]
    fase_anterior: Optional[str]
    objetivo_fase: str

@dataclass
class ActividadEducativa:
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

# ==== SISTEMA PRINCIPAL ====
class SistemaQAgentsV2:
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 modelo_base: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.modelo_base = modelo_base
        self.perfiles_path = perfiles_path
        
        self._cargar_ejemplos_k()
        self._configurar_llm()
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        self._crear_agentes_dociles()
        
        logger.info(f"✅ Sistema Q-Agents v2 inicializado")
        logger.info(f"   🤖 Modelo base: {self.modelo_base}")
        logger.info(f"   📖 Ejemplos k_: {len(self.ejemplos_k)}")
        logger.info(f"   👥 Estudiantes: {len(self.perfiles_data)}")
    
    def _cargar_ejemplos_k(self):
        """Carga ejemplos k_ para contexto rico"""
        self.ejemplos_k = {}
        
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_sonnet_supermercado.txt", 
            "actividades_generadas/k_feria_acertijos.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            try:
                if not os.path.isabs(archivo):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    archivo_path = os.path.join(script_dir, archivo)
                else:
                    archivo_path = archivo
                
                if os.path.exists(archivo_path):
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        logger.info(f"📖 Cargado ejemplo: {nombre_ejemplo}")
                else:
                    logger.warning(f"⚠️ No se encontró archivo: {archivo_path}")
            except Exception as e:
                logger.error(f"❌ Error cargando {archivo}: {e}")
        
        logger.info(f"✅ Cargados {len(self.ejemplos_k)} ejemplos k_")
    
    def _configurar_llm(self):
        """Configura LLM único para todos los agentes"""
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
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        """Carga perfiles de estudiantes"""
        try:
            if not os.path.isabs(perfiles_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                perfiles_path = os.path.join(script_dir, perfiles_path)
            
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('estudiantes', [])
        except Exception as e:
            logger.error(f"Error cargando perfiles: {e}")
            return self._crear_perfiles_default()
    
    def _crear_perfiles_default(self) -> List[Dict]:
        """Perfiles por defecto si no se pueden cargar"""
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
    
    def _crear_agentes_dociles(self):
        """Crea agentes con prompts minimalistas pero expertise intacta"""
        
        # Agente dócil pero experto en inspiración
        self.agente_inspirador = Agent(
            role="Creador de Semillas Creativas",
            goal="Crear una semilla creativa que inspire una actividad educativa memorable basándome en el contexto rico proporcionado",
            backstory="Soy un especialista en narrativas educativas que adapta ideas según feedback específico.",
            tools=[], 
            llm=self.llm, 
            verbose=True, 
            allow_delegation=False
        )
        
        # Agente dócil pero experto en pedagogía
        self.agente_pedagogo = Agent(
            role="Estructurador Pedagógico",
            goal="Transformar la semilla creativa en estructura pedagógica sólida, incorporando feedback específico",
            backstory="Soy un experto curricular que ajusta metodologías según indicaciones precisas.",
            tools=[], 
            llm=self.llm, 
            verbose=True, 
            allow_delegation=False
        )
        
        # Agente dócil pero experto en experiencias
        self.agente_arquitecto = Agent(
            role="Diseñador de Experiencias",
            goal="Crear el flujo temporal y arquitectura de la experiencia educativa según feedback recibido",
            backstory="Soy un especialista en diseño de experiencias que modifica estructuras según feedback específico.",
            tools=[], 
            llm=self.llm, 
            verbose=True, 
            allow_delegation=False
        )
        
        # Agente dócil pero experto en diferenciación
        self.agente_diferenciador = Agent(
            role="Personalizador Educativo",
            goal="Adaptar la experiencia a cada estudiante según perfiles y feedback de inclusión",
            backstory="Soy un psicopedagogo que personaliza según perfiles específicos y feedback de inclusión.",
            tools=[], 
            llm=self.llm, 
            verbose=True, 
            allow_delegation=False
        )
        
        logger.info("✅ Agentes dóciles creados")
        
        # Crear sistema de clasificación semántica
        self._crear_clasificador_semantico()
    
    def _crear_clasificador_semantico(self):
        """Crea el sistema de clasificación semántica de feedback"""
        
        # Dominios semánticos por agente
        self.dominios_semanticos = {
            AgenteSemantico.INSPIRADOR: {
                "keywords": [
                    "historia", "narrativa", "contexto", "motivación", "gancho", "dramatismo",
                    "realismo", "fantasía", "creatividad", "inspiración", "semilla", "idea",
                    "tema", "concepto", "metáfora", "ambiente", "escenario", "situación"
                ],
                "patterns": [
                    r"más\s+(dramático|emocionante|creativo)",
                    r"menos\s+(fantasioso|abstracto)",
                    r"cambiar\s+(el\s+tema|la\s+historia|el\s+contexto)",
                    r"quiero\s+que\s+sea\s+más\s+(realista|fantástico)",
                    r"la\s+historia\s+(debería|debe)"
                ],
                "descripcion": "Creatividad, narrativa, contexto motivacional y conceptos inspiradores"
            },
            
            AgenteSemantico.PEDAGOGO: {
                "keywords": [
                    "objetivos", "competencias", "currículum", "evaluación", "aprendizaje",
                    "didáctica", "metodología", "contenidos", "estándares", "criterios",
                    "pedagógico", "educativo", "formativo", "cognitivo", "habilidades",
                    "conocimientos", "destrezas", "logros", "metas", "indicadores"
                ],
                "patterns": [
                    r"objetivos?\s+(más|menos)\s+(claros|específicos|medibles)",
                    r"cambiar\s+(la\s+metodología|el\s+enfoque\s+pedagógico)",
                    r"más\s+(riguroso|académico|estructurado)",
                    r"evaluación\s+(más|menos)\s+(exigente|flexible)",
                    r"competencias?\s+(curriculares|específicas)"
                ],
                "descripcion": "Estructura pedagógica, objetivos, competencias y metodología educativa"
            },
            
            AgenteSemantico.ARQUITECTO: {
                "keywords": [
                    "tiempo", "duración", "sesiones", "fases", "etapas", "secuencia",
                    "organización", "estructura", "flujo", "progresión", "timing",
                    "cronograma", "planificación", "logística", "espacios", "materiales",
                    "recursos", "preparación", "desarrollo", "cierre", "transiciones",
                    "semana", "semanas", "día", "días", "horas", "sencillo", "simple",
                    "tareas", "organizado", "organizarlo", "organizarla"
                ],
                "patterns": [
                    r"(más|menos)\s+(tiempo|duración|sesiones)",
                    r"cambiar\s+(el\s+orden|la\s+secuencia|las\s+fases)",
                    r"reorganizar\s+(las\s+actividades|el\s+flujo)",
                    r"(acortar|alargar|extender)\s+la\s+actividad",
                    r"dividir\s+en\s+(más|menos)\s+partes",
                    r"una\s+semana\s+(como\s+mucho|máximo)",
                    r"organizado\s+por\s+tareas",
                    r"a\s+lo\s+largo\s+de\s+la\s+semana",
                    r"algo\s+(sencillo|simple)"
                ],
                "descripcion": "Arquitectura temporal, flujo de experiencia, organización, logística, duración y estructura de tareas"
            },
            
            AgenteSemantico.DIFERENCIADOR: {
                "keywords": [
                    "estudiantes", "personalización", "adaptaciones", "inclusión", "diferenciación",
                    "TEA", "TDAH", "altas capacidades", "necesidades", "perfiles", "diversidad",
                    "accesibilidad", "apoyo", "ajustes", "modificaciones", "individual",
                    "específico", "particular", "único", "personalizado", "adaptado"
                ],
                "patterns": [
                    r"para\s+(estudiantes\s+con|alumnos\s+con)\s+(TEA|TDAH|altas\s+capacidades)",
                    r"más\s+(inclusivo|accesible|personalizado)",
                    r"adaptar\s+para\s+(cada|todos)\s+los?\s+estudiantes?",
                    r"diferenciación\s+(más|menos)\s+(específica|detallada)",
                    r"considerar\s+(las\s+necesidades|los\s+perfiles)"
                ],
                "descripcion": "Personalización, adaptaciones específicas e inclusión educativa"
            }
        }
        
        logger.info("✅ Clasificador semántico creado")
    
    def _analizar_intencion_feedback(self, prompt_feedback: str) -> FeedbackFlexible:
        """Analiza un prompt de feedback y determina el agente objetivo"""
        
        prompt_lower = prompt_feedback.lower()
        puntuaciones = {}
        
        # Calcular puntuación para cada agente
        for agente, dominio in self.dominios_semanticos.items():
            puntuacion = 0
            detalles_deteccion = []
            
            # Puntuación por keywords
            for keyword in dominio["keywords"]:
                if keyword in prompt_lower:
                    puntuacion += 2
                    detalles_deteccion.append(f"keyword:{keyword}")
            
            # Puntuación por patterns
            for pattern in dominio["patterns"]:
                matches = re.findall(pattern, prompt_lower)
                if matches:
                    puntuacion += 5  # Patterns valen más
                    detalles_deteccion.append(f"pattern:{pattern}")
            
            # Puntuación por similitud semántica
            similitud_descripcion = SequenceMatcher(None, prompt_lower, dominio["descripcion"].lower()).ratio()
            puntuacion += similitud_descripcion * 3
            
            puntuaciones[agente] = {
                "puntuacion": puntuacion,
                "detalles": detalles_deteccion
            }
        
        # Determinar agente con mayor puntuación
        agente_ganador = max(puntuaciones.keys(), key=lambda k: puntuaciones[k]["puntuacion"])
        puntuacion_maxima = puntuaciones[agente_ganador]["puntuacion"]
        
        # Calcular confianza (normalizada)
        confianza = min(puntuacion_maxima / 10.0, 1.0)  # Max confianza = 1.0
        
        # Si la confianza es muy baja, usar GENERAL
        if confianza < 0.3:
            agente_ganador = AgenteSemantico.GENERAL
            confianza = 0.5  # Confianza media para casos generales
            intencion_detectada = f"Modificar {agente_ganador.value} - feedback general"
        else:
            intencion_detectada = f"Modificar {agente_ganador.value} - {puntuaciones[agente_ganador]['detalles'][:3]}"
        
        # Procesar el feedback en instrucciones
        instrucciones = self._procesar_prompt_a_instrucciones(prompt_feedback, agente_ganador)
        
        return FeedbackFlexible(
            prompt_usuario=prompt_feedback,
            agente_objetivo=agente_ganador.value,
            intencion_detectada=intencion_detectada,
            confianza=confianza,
            instrucciones_procesadas=instrucciones
        )
    
    def _procesar_prompt_a_instrucciones(self, prompt: str, agente: AgenteSemantico) -> str:
        """Convierte un prompt de feedback en instrucciones específicas para el agente"""
        
        # Plantillas específicas por agente
        plantillas = {
            AgenteSemantico.INSPIRADOR: f"""
🎭 FEEDBACK ESPECÍFICO PARA INSPIRACIÓN:
Usuario solicita: "{prompt}"

INSTRUCCIONES PARA EL AGENTE INSPIRADOR:
- Ajusta la semilla creativa según esta solicitud específica
- Mantén la coherencia narrativa pero incorpora los cambios solicitados
- Prioriza esta modificación sobre otras consideraciones creativas
            """,
            
            AgenteSemantico.PEDAGOGO: f"""
📚 FEEDBACK ESPECÍFICO PARA PEDAGOGÍA:
Usuario solicita: "{prompt}"

INSTRUCCIONES PARA EL AGENTE PEDAGOGO:
- Modifica la estructura pedagógica según esta solicitud específica
- Ajusta objetivos, competencias o metodología según lo requerido
- Mantén el rigor académico mientras implementas los cambios
            """,
            
            AgenteSemantico.ARQUITECTO: f"""
🏗️ FEEDBACK ESPECÍFICO PARA ARQUITECTURA:
Usuario solicita: "{prompt}"

INSTRUCCIONES PARA EL AGENTE ARQUITECTO:
- Reorganiza el flujo temporal según esta solicitud específica
- Ajusta duración, secuencia o logística según lo requerido
- Mantén la coherencia experiencial mientras implementas los cambios
            """,
            
            AgenteSemantico.DIFERENCIADOR: f"""
🎯 FEEDBACK ESPECÍFICO PARA DIFERENCIACIÓN:
Usuario solicita: "{prompt}"

INSTRUCCIONES PARA EL AGENTE DIFERENCIADOR:
- Ajusta las adaptaciones específicas según esta solicitud
- Personaliza para las necesidades mencionadas
- Mantén la inclusión mientras implementas los cambios específicos
            """,
            
            AgenteSemantico.GENERAL: f"""
🔧 FEEDBACK GENERAL:
Usuario solicita: "{prompt}"

INSTRUCCIONES GENERALES:
- Implementa esta modificación en tu área de expertise
- Interpreta la solicitud según tu rol específico
- Mantén la calidad mientras implementas el cambio solicitado
            """
        }
        
        return plantillas.get(agente, plantillas[AgenteSemantico.GENERAL])
    
    def solicitar_feedback_flexible(self, fase: str, contenido_previo: str) -> List[FeedbackFlexible]:
        """Solicita feedback mediante prompts libres con clasificación automática"""
        print(f"\n" + "="*60)
        print(f"🧠 FEEDBACK SEMÁNTICO INTELIGENTE - {fase.upper()}")
        print("="*60)
        
        # Mostrar resumen del contenido previo
        lineas = contenido_previo.split('\n')[:8]
        for linea in lineas:
            if linea.strip():
                print(f"📄 {linea[:70]}{'...' if len(linea) > 70 else ''}")
        
        print(f"\n❓ ¿Qué quieres cambiar o mejorar de esta {fase}?")
        print("💡 Puedes escribir en lenguaje natural:")
        print("   • 'Hazlo más corto y dinámico'")
        print("   • 'Adapta mejor para estudiantes con TEA'") 
        print("   • 'Cambia la historia por algo más realista'")
        print("   • 'Añade más evaluación formativa'")
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
                print("\n❌ Proceso cancelado por el usuario")
                return []
            except Exception as e:
                print(f"❌ Error en input: {e}")
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
                
                # Analizar el feedback con clasificación semántica
                feedback_analizado = self._analizar_intencion_feedback(prompt_feedback)
                
                # Mostrar análisis al usuario
                print(f"\n🧠 ANÁLISIS AUTOMÁTICO:")
                print(f"   🎯 Agente objetivo: {feedback_analizado.agente_objetivo}")
                print(f"   🎯 Confianza: {feedback_analizado.confianza:.1%}")
                print(f"   🎯 Intención: {feedback_analizado.intencion_detectada}")
                
                # Confirmar con el usuario
                confirmar = input(f"\n¿Es correcto? (s/n): ").strip().lower()
                if confirmar in ['s', 'si', 'sí', 'yes', 'y', '']:
                    feedback_list.append(feedback_analizado)
                    print(f"✅ Feedback agregado para {feedback_analizado.agente_objetivo}")
                else:
                    print("❌ Feedback descartado. Puedes intentar con otras palabras.")
                
            except KeyboardInterrupt:
                print("\n❌ Proceso cancelado por el usuario")
                break
            except Exception as e:
                print(f"❌ Error procesando feedback: {e}")
                continue
        
        if feedback_list:
            print(f"\n✅ {len(feedback_list)} feedback(s) procesado(s) exitosamente")
        else:
            print("\n📝 No se agregó feedback")
        
        return feedback_list
    
    def _aplicar_feedback_flexible(self, feedback_list: List[FeedbackFlexible], agente_actual: str) -> str:
        """Aplica feedback flexible específico para el agente actual"""
        if not feedback_list:
            return ""
        
        # Filtrar feedback relevante para este agente
        feedback_relevante = [f for f in feedback_list if f.agente_objetivo == agente_actual or f.agente_objetivo == "general"]
        
        # PROPAGACIÓN CRÍTICA: Feedback de arquitectura debe aplicarse a todos los agentes
        feedback_arquitectura = [f for f in feedback_list if f.agente_objetivo == "arquitecto"]
        if feedback_arquitectura and agente_actual != "arquitecto":
            # Extraer info temporal crítica para otros agentes
            for fb in feedback_arquitectura:
                if any(keyword in fb.prompt_usuario.lower() for keyword in ["semana", "día", "duración", "tiempo"]):
                    feedback_relevante.append(fb)
        
        if not feedback_relevante:
            return ""
        
        instrucciones_combinadas = "\n🎯 FEEDBACK ESPECÍFICO DEL USUARIO:\n"
        for i, feedback in enumerate(feedback_relevante, 1):
            if feedback.agente_objetivo == "arquitecto" and agente_actual != "arquitecto":
                # Adaptar feedback de arquitectura para otros agentes
                instrucciones_combinadas += f"\n{i}. 🕐 DURACIÓN CRÍTICA: {feedback.prompt_usuario}\n"
                instrucciones_combinadas += f"   → APLICA esta duración temporal en tu sección específica\n"
            else:
                instrucciones_combinadas += f"\n{i}. {feedback.instrucciones_procesadas}\n"
        
        instrucciones_combinadas += "\n⚠️ ESTAS INSTRUCCIONES TIENEN PRIORIDAD MÁXIMA sobre cualquier otra consideración.\n"
        
        return instrucciones_combinadas
    
    
    def _construir_contexto_rico(self, 
                                prompt_inicial: str,
                                materia: str,
                                tema: Optional[str],
                                fase_anterior: Optional[str],
                                objetivo_fase: str,
                                feedback_acumulado: List[FeedbackFlexible]) -> ContextoRico:
        """Construye contexto rico para compensar prompts minimalistas"""
        
        # Seleccionar ejemplos k_ relevantes
        ejemplos_relevantes = {}
        if materia.lower() in ['matematicas', 'mates']:
            for key in ['k_sonnet_supermercado', 'k_feria_acertijos']:
                if key in self.ejemplos_k:
                    ejemplos_relevantes[key] = self.ejemplos_k[key][:1000]  # Primeros 1000 chars
        elif materia.lower() in ['ciencias', 'naturales']:
            if 'k_celula' in self.ejemplos_k:
                ejemplos_relevantes['k_celula'] = self.ejemplos_k['k_celula'][:1000]
        
        # Si no hay ejemplos específicos, usar uno genérico
        if not ejemplos_relevantes and 'k_piratas' in self.ejemplos_k:
            ejemplos_relevantes['k_piratas'] = self.ejemplos_k['k_piratas'][:1000]
        
        return ContextoRico(
            prompt_inicial=prompt_inicial,
            materia=materia,
            tema=tema,
            ejemplos_k=ejemplos_relevantes,
            perfiles_estudiantes=self.perfiles_data,
            feedback_acumulado=feedback_acumulado,
            fase_anterior=fase_anterior,
            objetivo_fase=objetivo_fase
        )
    
    
    def _crear_contexto_texto(self, contexto_rico: ContextoRico) -> str:
        """Convierte ContextoRico en texto estructurado"""
        contexto_texto = f"""
CONTEXTO RICO:

PROMPT INICIAL DEL USUARIO:
{contexto_rico.prompt_inicial}

MATERIA: {contexto_rico.materia}
TEMA: {contexto_rico.tema or 'General'}

EJEMPLOS DE CALIDAD K_ PARA INSPIRACIÓN:
"""
        
        for nombre, contenido in contexto_rico.ejemplos_k.items():
            contexto_texto += f"\n--- {nombre.upper()} ---\n{contenido}\n"
        
        contexto_texto += f"""
ESTUDIANTES DEL AULA:
"""
        for estudiante in contexto_rico.perfiles_estudiantes:
            contexto_texto += f"- {estudiante['id']} {estudiante['nombre']}: {estudiante.get('temperamento', 'N/A')}, {estudiante.get('canal_preferido', 'N/A')}"
            if estudiante.get('diagnostico_formal', 'ninguno') != 'ninguno':
                contexto_texto += f", {estudiante['diagnostico_formal']}"
            contexto_texto += "\n"
        
        if contexto_rico.fase_anterior:
            contexto_texto += f"\nFASE ANTERIOR: {contexto_rico.fase_anterior}"
        
        contexto_texto += f"\nOBJETIVO DE ESTA FASE: {contexto_rico.objetivo_fase}"
        
        return contexto_texto
    
    
    def generar_actividad_colaborativa(self, prompt_inicial: str) -> ActividadEducativa:
        """Genera actividad con nueva arquitectura de feedback estructurado"""
        
        # Análisis inicial básico del prompt
        materia = self._detectar_materia(prompt_inicial)
        tema = self._detectar_tema(prompt_inicial)
        
        if not materia:
            materia = input("📚 ¿Qué materia? (matematicas/lengua/ciencias): ").strip().lower()
        
        logger.info(f"🚀 Generando actividad Q-Agents v2 para {materia}")
        
        try:
            feedback_acumulado = []
            resultados = {}
            
            # === FASE 1: INSPIRACIÓN ===
            contexto_inspiracion = self._construir_contexto_rico(
                prompt_inicial, materia, tema, None, 
                "Crear semilla creativa inspiradora", feedback_acumulado
            )
            
            tarea_inspiracion = Task(
                description=f"""
{self._crear_contexto_texto(contexto_inspiracion)}

TAREA:
Como Creador de Semillas Creativas, genera una semilla creativa inspiradora para esta actividad educativa.
Utiliza el contexto rico proporcionado para crear una propuesta original y motivadora.
Mantén la calidad pedagógica inspirándote en los ejemplos k_.
Crea algo NUEVO basado en el prompt inicial del usuario.
                """,
                agent=self.agente_inspirador,
                expected_output="Semilla creativa inspiradora para la actividad educativa"
            )
            
            crew_inspiracion = Crew(
                agents=[self.agente_inspirador],
                tasks=[tarea_inspiracion],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_inspiracion = crew_inspiracion.kickoff()
            resultados['inspiracion'] = str(resultado_inspiracion)
            
            # Solicitar feedback flexible con NLP
            feedback_inspiracion = self.solicitar_feedback_flexible("inspiración", str(resultado_inspiracion))
            feedback_acumulado.extend(feedback_inspiracion)
            
            # === FASE 2: PEDAGOGÍA ===
            contexto_pedagogia = self._construir_contexto_rico(
                prompt_inicial, materia, tema, "inspiración", 
                "Estructurar pedagógicamente la semilla creativa", feedback_acumulado
            )
            
            # IMPORTANTE: Agregar resultado anterior al contexto
            contexto_pedagogia_texto = f"""
RESULTADO DE LA FASE ANTERIOR (INSPIRACIÓN):
{str(resultado_inspiracion)}

{self._crear_contexto_texto(contexto_pedagogia)}
"""
            
            tarea_pedagogia = Task(
                description=f"""
{contexto_pedagogia_texto}

{self._aplicar_feedback_flexible(feedback_inspiracion, "pedagogo")}

TAREA:
Como Estructurador Pedagógico, toma la semilla creativa anterior y desarróllala en una estructura pedagógica sólida.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
Mantén la calidad pedagógica inspirándote en los ejemplos k_.
NO repitas el contenido anterior, sino que MEJORA y ESTRUCTURA la propuesta.
                """,
                agent=self.agente_pedagogo,
                expected_output="Estructura pedagógica mejorada basada en la semilla creativa anterior"
            )
            
            crew_pedagogia = Crew(
                agents=[self.agente_pedagogo],
                tasks=[tarea_pedagogia],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_pedagogia = crew_pedagogia.kickoff()
            resultados['pedagogia'] = str(resultado_pedagogia)
            
            # Solicitar feedback flexible con NLP
            feedback_pedagogia = self.solicitar_feedback_flexible("estructura pedagógica", str(resultado_pedagogia))
            feedback_acumulado.extend(feedback_pedagogia)
            
            # === FASE 3: ARQUITECTURA ===
            contexto_arquitectura = self._construir_contexto_rico(
                prompt_inicial, materia, tema, "pedagogía", 
                "Diseñar arquitectura temporal y experiencial", feedback_acumulado
            )
            
            # IMPORTANTE: Agregar resultado anterior al contexto
            contexto_arquitectura_texto = f"""
RESULTADO DE LA FASE ANTERIOR (PEDAGOGÍA):
{str(resultado_pedagogia)}

{self._crear_contexto_texto(contexto_arquitectura)}
"""
            
            tarea_arquitectura = Task(
                description=f"""
{contexto_arquitectura_texto}

{self._aplicar_feedback_flexible(feedback_pedagogia, "arquitecto")}

TAREA:
Como Diseñador de Experiencias, toma la estructura pedagógica anterior y crea el flujo temporal y arquitectura de la experiencia.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
Mantén la calidad pedagógica inspirándote en los ejemplos k_.
NO repitas el contenido anterior, sino que DISEÑA la experiencia temporal y logística.
                """,
                agent=self.agente_arquitecto,
                expected_output="Diseño de experiencia temporal basado en la estructura pedagógica anterior"
            )
            
            crew_arquitectura = Crew(
                agents=[self.agente_arquitecto],
                tasks=[tarea_arquitectura],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_arquitectura = crew_arquitectura.kickoff()
            resultados['arquitectura'] = str(resultado_arquitectura)
            
            # Solicitar feedback flexible con NLP
            feedback_arquitectura = self.solicitar_feedback_flexible("arquitectura", str(resultado_arquitectura))
            feedback_acumulado.extend(feedback_arquitectura)
            
            # === FASE 4: DIFERENCIACIÓN (Final) ===
            contexto_diferenciacion = self._construir_contexto_rico(
                prompt_inicial, materia, tema, "arquitectura", 
                "Personalizar para cada estudiante específico", feedback_acumulado
            )
            
            # IMPORTANTE: Agregar resultado anterior al contexto
            contexto_diferenciacion_texto = f"""
RESULTADO DE LA FASE ANTERIOR (ARQUITECTURA):
{str(resultado_arquitectura)}

{self._crear_contexto_texto(contexto_diferenciacion)}
"""
            
            tarea_diferenciacion = Task(
                description=f"""
{contexto_diferenciacion_texto}

{self._aplicar_feedback_flexible(feedback_arquitectura, "diferenciador")}

TAREA:
Como Personalizador Educativo, toma la arquitectura de experiencia anterior y personalízala para cada estudiante específico.
Si hay instrucciones específicas del usuario, dales prioridad absoluta.
Mantén la calidad pedagógica inspirándote en los ejemplos k_.
NO repitas el contenido anterior, sino que PERSONALIZA la experiencia para cada estudiante del aula.
                """,
                agent=self.agente_diferenciador,
                expected_output="Actividad personalizada para cada estudiante basada en la arquitectura anterior"
            )
            
            crew_diferenciacion = Crew(
                agents=[self.agente_diferenciador],
                tasks=[tarea_diferenciacion],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_diferenciacion = crew_diferenciacion.kickoff()
            resultados['diferenciacion'] = str(resultado_diferenciacion)
            
            # Construir contenido final
            contenido_completo = self._construir_contenido_final(resultados, feedback_acumulado)
            
            return ActividadEducativa(
                id=f"q2_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Q-Agents v2 - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_q_agents_v2",
                adaptaciones=["feedback_estructurado", "contexto_rico", "agentes_dociles"],
                metadatos={
                    "total_estudiantes": 8,
                    "feedback_aplicado": len(feedback_acumulado),
                    "feedback_detalles": [{"agente": f.agente_objetivo, "prompt": f.prompt_usuario, "confianza": f.confianza, "intencion": f.intencion_detectada} for f in feedback_acumulado],
                    "modelo_usado": self.modelo_base,
                    "ejemplos_k_usados": list(self.ejemplos_k.keys()),
                    "version": "2.0_semantic_feedback"
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad Q-Agents v2: {e}")
            return ActividadEducativa(
                id=f"error_q2_{materia.lower() if materia else 'unknown'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Error - {materia or 'Unknown'}",
                materia=materia or "unknown",
                tema=tema or "tema general",
                contenido=f"Error generando actividad Q-Agents v2: {e}",
                estudiantes_objetivo=[],
                tipo="error_q_agents_v2",
                adaptaciones=[],
                metadatos={"error": str(e), "version": "2.0"},
                timestamp=datetime.now().isoformat()
            )
    
    def _detectar_materia(self, prompt: str) -> Optional[str]:
        """Detecta materia en el prompt"""
        prompt_lower = prompt.lower()
        
        materias = {
            'matematicas': ['matemáticas', 'mates', 'números', 'cálculo', 'geometría', 'álgebra', 'fracciones'],
            'lengua': ['lengua', 'idioma', 'escritura', 'lectura', 'gramática', 'literatura'],
            'ciencias': ['ciencias', 'biología', 'física', 'química', 'naturales', 'científico', 'células']
        }
        
        for materia, keywords in materias.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return materia
        return None
    
    def _detectar_tema(self, prompt: str) -> Optional[str]:
        """Detecta tema específico en el prompt"""
        import re
        
        tema_patterns = [
            r'sobre[:\s]*([^.,\n]+)',
            r'tema[:\s]*([^.,\n]+)',
            r'acerca de[:\s]*([^.,\n]+)'
        ]
        
        for pattern in tema_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return match.group(1).strip()
        return None
    
    def _construir_contenido_final(self, resultados: Dict[str, str], feedback_acumulado: List[FeedbackFlexible]) -> str:
        """Construye el contenido final de la actividad"""
        contenido = "=" * 80 + "\n"
        contenido += "ACTIVIDAD GENERADA CON Q-AGENTS V2\n"
        contenido += "Sistema con Feedback Estructurado y Contexto Rico\n"
        contenido += "=" * 80 + "\n\n"
        
        # Resumen de feedback aplicado
        if feedback_acumulado:
            contenido += "🎯 FEEDBACK APLICADO DEL USUARIO:\n"
            contenido += "-" * 40 + "\n"
            for i, feedback in enumerate(feedback_acumulado, 1):
                contenido += f"{i}. AGENTE: {feedback.agente_objetivo.upper()}\n"
                contenido += f"   Solicitud: {feedback.prompt_usuario}\n"
                contenido += f"   Confianza: {feedback.confianza:.1%}\n"
                contenido += f"   Intención: {feedback.intencion_detectada}\n\n"
        
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
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_q") -> str:
        """Guarda la actividad generada"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON Q-AGENTS V2\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo: {actividad.tipo}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 50 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\n")
            f.write("-" * 50 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("METADATOS DEL SISTEMA Q-AGENTS V2:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad Q-Agents v2 guardada en: {filepath}")
        return filepath


# -------------------------------
def main():
    print("=" * 70)
    print("🎓 SISTEMA Q-AGENTS V2 - HUMAN-IN-THE-LOOP AVANZADO")
    print("=" * 70)

    try:
        OLLAMA_HOST = "192.168.1.10"
        MODELO_BASE = "qwen3:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"

        print(f"\n🔧 Inicializando Q-Agents v2:")
        print(f" Host Ollama: {OLLAMA_HOST}")
        print(f" Modelo base: {MODELO_BASE}")
        print(f" Arquitectura: Agentes dóciles + Contexto rico + Feedback estructurado")

        sistema = SistemaQAgentsV2(
            ollama_host=OLLAMA_HOST,
            modelo_base=MODELO_BASE,
            perfiles_path=PERFILES_PATH
        )

        print("\n✅ Sistema Q-Agents v2 inicializado correctamente!")
        print(f"📖 Ejemplos k_ cargados: {len(sistema.ejemplos_k)}")

        while True:
            print("\n" + "="*50)
            print("🎓 GENERACIÓN Q-AGENTS V2")
            print("1. 🎯 Generar actividad con feedback estructurado")
            print("2. ❌ Salir")

            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            if opcion == "1":
                print("\n📝 Describe tu actividad ideal:")
                print("Ejemplo: 'Actividad colaborativa de matemáticas sobre fracciones")
                print("         para estudiantes de 4º primaria, inclusiva para TEA'")
                prompt_inicial = input("\n✨ Tu prompt: ").strip()
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_colaborativa(prompt_inicial)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad Q-Agents v2 generada en {duration:.1f}s:")
                print(f" 📄 ID: {actividad.id}")
                print(f" 📁 Archivo: {archivo}")
                print(f" 🎯 Sistema: Q-Agents v2 con feedback estructurado")
                print(f" 🔧 Feedback aplicado: {actividad.metadatos.get('feedback_aplicado', 0)} elementos")
                
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")

    except Exception as e:
        print(f"\n❌ Error inicializando sistema Q-Agents v2: {e}")
        print("\n💡 Verifica que:")
        print(" 1. Ollama esté ejecutándose")
        print(" 2. El modelo especificado esté disponible")
        print(" 3. El archivo de perfiles exista")
        print(" 4. Los archivos k_ estén en actividades_generadas/")

if __name__ == "__main__":
    main()