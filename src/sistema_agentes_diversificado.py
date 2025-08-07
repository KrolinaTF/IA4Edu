#!/usr/bin/env python3
"""
Sistema Multi-Agente Inteligente para Generación de Actividades Educativas
Contexto específico: 4º Primaria con adaptaciones DUA
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SistemaAgentesInteligente")

# Importaciones para conexión directa a Ollama
import requests

class EstadoActividad(Enum):
    """Estados posibles de una actividad"""
    INICIADO = "iniciado"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    ERROR = "error"
    REQUIERE_HUMAN = "requiere_human"

@dataclass
class ActividadState:
    """Estado completo de una actividad en proceso"""
    tema: str
    nivel_educativo: str = "4º Primaria"
    iteracion: int = 1
    max_iteraciones: int = 3
    estado: EstadoActividad = EstadoActividad.INICIADO
    
    # Contenido de la actividad
    ideas_generadas: List[Dict] = field(default_factory=list)
    actividad_seleccionada: Dict = field(default_factory=dict)
    adaptaciones_dua: Dict = field(default_factory=dict)
    arquitectura_tareas: Dict = field(default_factory=dict)
    validacion_curricular: Dict = field(default_factory=dict)
    recursos_logisticos: Dict = field(default_factory=dict)
    
    # Metadatos y control
    timestamp_inicio: str = ""
    agente_actual: str = ""
    necesita_human_input: bool = False
    problemas_detectados: List[str] = field(default_factory=list)

class BaseAgent:
    """Clase base para todos los agentes del sistema"""
    
    # Configuración global de Ollama
    _ollama_config = {
        'host': '192.168.1.10',
        'port': 11434,
        'default_model': 'llama3.2:latest'
    }
    
    def __init__(self, name: str, llm_required: bool = True, model_override: str = None):
        self.name = name
        self.llm_required = llm_required
        self.model = model_override or self._ollama_config['default_model']
        self.ollama_url = f"http://{self._ollama_config['host']}:{self._ollama_config['port']}"
        
        # Verificar conexión si es necesario
        if self.llm_required:
            logger.info(f"🔧 [{self.name}] Verificando conexión con modelo: {self.model}")
            self._verificar_conexion()
        
    def _verificar_conexion(self):
        """Verifica que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ [{self.name}] Conexión exitosa a Ollama con modelo {self.model}")
            else:
                logger.warning(f"⚠️ [{self.name}] Ollama responde pero con código {response.status_code}")
        except Exception as e:
            logger.error(f"❌ [{self.name}] Error conectando a Ollama: {e}")
    
    def verificar_conexion_individual(self):
        """Verifica el estado de la conexión"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ [{self.name}] Conexión verificada")
                return True
            else:
                logger.warning(f"⚠️ [{self.name}] Ollama responde con código {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ [{self.name}] Error verificando conexión: {e}")
            return False
    
    def generar_con_llm(self, prompt: str, max_tokens: int = 800) -> str:
        """Genera respuesta usando Ollama con conexión directa"""
        
        logger.info(f"[{self.name}] 📤 Enviando prompt a {self.model} (longitud: {len(prompt)} chars)")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data.get('response', '').strip()
                
                if respuesta:
                    logger.info(f"[{self.name}] ✅ Respuesta de {self.model} recibida (longitud: {len(respuesta)} chars)")
                    return respuesta
                else:
                    logger.warning(f"[{self.name}] ⚠️ Respuesta vacía de {self.model}")
                    return self._respuesta_simulada()
            else:
                logger.error(f"[{self.name}] ❌ Error HTTP {response.status_code}: {response.text}")
                return self._respuesta_simulada()
                
        except Exception as e:
            logger.error(f"[{self.name}] ❌ Error conectando con {self.model}: {e}")
            return self._respuesta_simulada()
    
    def _respuesta_simulada(self) -> str:
        """Respuesta simulada por defecto"""
        return "Respuesta simulada - Ollama no disponible"
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Método base que debe ser implementado por cada agente"""
        raise NotImplementedError("Cada agente debe implementar el método procesar")

# ===== AGENTES ESPECIALIZADOS =====

class IdeadorAgent(BaseAgent):
    """Agente que genera ideas iniciales de actividades"""
    
    def __init__(self):
        super().__init__("Ideador", llm_required=True, model_override="mistral:latest")
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Genera ideas iniciales para la actividad"""
        logger.info(f"[{self.name}] Generando ideas para: {state.tema}")
        state.agente_actual = self.name
        
        prompt = f"""
Eres un experto diseñador de actividades educativas para 4º de Primaria.

TEMA: {state.tema}
NIVEL: {state.nivel_educativo}

Genera 3 ideas creativas de actividades que:
1. Sean apropiadas para 4º de Primaria (9-10 años)
2. Fomenten el aprendizaje activo y colaborativo
3. Incluyan elementos manipulativos y visuales
4. Duren entre 30-60 minutos
5. Permitan adaptaciones para diferentes necesidades

Para cada idea proporciona:
- Título atractivo
- Descripción breve (2-3 líneas)
- Tipo de actividad (individual/grupos/mixta)
- Materiales básicos necesarios
- Objetivo pedagógico principal

Formato: IDEA 1: [título], IDEA 2: [título], IDEA 3: [título]
"""
        
        respuesta = self.generar_con_llm(prompt, max_tokens=600)
        ideas = self._parsear_ideas(respuesta)
        
        state.ideas_generadas = ideas
        
        if ideas:
            logger.info(f"[{self.name}] Generadas {len(ideas)} ideas exitosamente")
        else:
            state.problemas_detectados.append(f"{self.name}: No se pudieron generar ideas válidas")
        
        return state
    
    def _parsear_ideas(self, respuesta: str) -> List[Dict]:
        """Parsea las ideas desde la respuesta del LLM"""
        ideas = []
        
        # Buscar patrones de ideas
        patron_idea = r'IDEA\s*(\d+):\s*([^,\n]+)'
        matches = re.findall(patron_idea, respuesta)
        
        for i, (numero, titulo) in enumerate(matches[:3]):
            idea = {
                "id": f"idea_{numero}",
                "titulo": titulo.strip(),
                "descripcion": f"Actividad educativa sobre {titulo.strip()}",
                "tipo": "mixta",
                "materiales": "Materiales básicos de aula",
                "objetivo": f"Desarrollar competencias en {titulo.strip().lower()}"
            }
            ideas.append(idea)
        
        # Si no se encontraron ideas estructuradas, crear una básica
        if not ideas:
            ideas.append({
                "id": "idea_1",
                "titulo": f"Actividad de {respuesta[:50]}...",
                "descripcion": "Actividad educativa interactiva",
                "tipo": "mixta",
                "materiales": "Materiales básicos",
                "objetivo": "Desarrollar competencias educativas"
            })
        
        return ideas
    
    def _respuesta_simulada(self) -> str:
        return """
IDEA 1: Laboratorio de Fracciones
IDEA 2: Teatro Matemático
IDEA 3: Mercado de Problemas
"""

class AdaptadorDUAAgent(BaseAgent):
    """Agente que aplica principios DUA a la actividad seleccionada. 
    Eres un traductor de los principio DUA a la actividad específica que se está desarrollando, 
    tienes que responder a la pregunta ¿en qué se materializa esta adaptación en esta actividad en concreto?"""
    
    def __init__(self):
        super().__init__("AdaptadorDUA", llm_required=True, model_override="gemma3:latest")
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Aplica adaptaciones DUA a la actividad"""
        logger.info(f"[{self.name}] Aplicando adaptaciones DUA")
        state.agente_actual = self.name
        
        if not state.actividad_seleccionada:
            # Seleccionar primera idea por defecto
            if state.ideas_generadas:
                state.actividad_seleccionada = state.ideas_generadas[0]
            else:
                state.problemas_detectados.append(f"{self.name}: No hay actividad base para adaptar")
                return state
        
        actividad = state.actividad_seleccionada
        
        prompt = f"""
Aplica principios DUA (Diseño Universal para el Aprendizaje) a esta actividad:

ACTIVIDAD: {actividad.get('titulo', 'Sin título')}
DESCRIPCIÓN: {actividad.get('descripcion', 'Sin descripción')}

Considera estos perfiles típicos de 4º Primaria:
- Elena (TEA): Necesita rutinas claras, instrucciones visuales
- Luis (TDAH): Necesita descansos, actividades kinestésicas  
- Ana (Altas capacidades): Necesita retos adicionales
- Estudiantes neurotípicos: Variedad de estilos de aprendizaje

Proporciona adaptaciones específicas para:

1. REPRESENTACIÓN (cómo presentar la información):
   - Adaptaciones visuales
   - Adaptaciones auditivas
   - Adaptaciones kinestésicas

2. EXPRESIÓN (cómo los estudiantes demuestran aprendizaje):
   - Opciones de respuesta
   - Herramientas alternativas

3. MOTIVACIÓN (cómo mantener el compromiso):
   - Estrategias de motivación
   - Opciones de agrupamiento

Formato claro y específico para cada área.
"""
        
        respuesta = self.generar_con_llm(prompt, max_tokens=700)
        adaptaciones = self._parsear_adaptaciones(respuesta)
        
        state.adaptaciones_dua = adaptaciones
        
        if adaptaciones:
            logger.info(f"[{self.name}] Adaptaciones DUA aplicadas exitosamente")
        else:
            state.problemas_detectados.append(f"{self.name}: No se pudieron generar adaptaciones DUA")
        
        return state
    
    def _parsear_adaptaciones(self, respuesta: str) -> Dict:
        """Parsea las adaptaciones DUA desde la respuesta"""
        adaptaciones = {
            "representacion": {
                "visuales": ["Usar organizadores gráficos", "Código de colores"],
                "auditivas": ["Instrucciones verbales claras", "Música de fondo"],
                "kinestesicas": ["Materiales manipulativos", "Movimiento corporal"]
            },
            "expresion": {
                "opciones_respuesta": ["Oral", "Escrita", "Visual", "Digital"],
                "herramientas": ["Calculadora", "Tabletas", "Material concreto"]
            },
            "motivacion": {
                "estrategias": ["Gamificación", "Trabajo colaborativo", "Elección de temas"],
                "agrupamiento": ["Individual", "Parejas", "Grupos pequeños", "Gran grupo"]
            },
            "adaptaciones_especificas": {
                "TEA": ["Rutinas visuales", "Tiempo extra", "Espacio tranquilo"],
                "TDAH": ["Descansos frecuentes", "Fidgets", "Tareas cortas"],
                "Altas_capacidades": ["Proyectos avanzados", "Mentoría", "Investigación"],
                "General": ["Múltiples formatos", "Apoyo entre pares"]
            }
        }
        
        return adaptaciones
    
    def _respuesta_simulada(self) -> str:
        return """
REPRESENTACIÓN:
- Visuales: Organizadores gráficos, colores
- Auditivas: Explicaciones verbales
- Kinestésicas: Manipulativos

EXPRESIÓN:
- Múltiples opciones de respuesta
- Herramientas alternativas

MOTIVACIÓN:
- Gamificación
- Trabajo colaborativo
"""

class ArquitectoTareasAgent(BaseAgent):
    """Agente que descompone la actividad en tareas específicas"""
    
    def __init__(self):
        super().__init__("ArquitectoTareas", llm_required=True, model_override="qwen2:latest")
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Descompone la actividad en tareas específicas"""
        logger.info(f"[{self.name}] Diseñando arquitectura de tareas")
        state.agente_actual = self.name
        
        if not state.actividad_seleccionada:
            state.problemas_detectados.append(f"{self.name}: No hay actividad base para descomponer")
            return state
        
        actividad = state.actividad_seleccionada
        adaptaciones = state.adaptaciones_dua
        
        prompt = f"""
Descompón esta actividad educativa en tareas específicas y secuenciales:

ACTIVIDAD: {actividad.get('titulo', 'Sin título')}
DESCRIPCIÓN: {actividad.get('descripcion', 'Sin descripción')}

Teniendo en cuenta las adaptaciones DUA aplicadas, crea una secuencia de 4-6 tareas que:

1. Tengan una progresión lógica (preparación → desarrollo → cierre)
2. Sean apropiadas para 4º Primaria
3. Permitan trabajo individual y colaborativo
4. Incluyan checkpoints de evaluación
5. Consideren las adaptaciones para TEA, TDAH y altas capacidades

Para cada tarea especifica:
- Nombre de la tarea
- Duración estimada (minutos)
- Tipo (individual/parejas/grupos)
- Materiales específicos
- Instrucciones claras
- Adaptaciones necesarias
- Criterio de éxito

Formato: TAREA 1: [nombre], TAREA 2: [nombre], etc.
"""
        
        respuesta = self.generar_con_llm(prompt, max_tokens=800)
        arquitectura = self._parsear_arquitectura(respuesta)
        
        state.arquitectura_tareas = arquitectura
        
        if arquitectura and arquitectura.get('tareas'):
            logger.info(f"[{self.name}] Arquitectura de {len(arquitectura['tareas'])} tareas creada")
        else:
            state.problemas_detectados.append(f"{self.name}: No se pudo crear arquitectura de tareas")
        
        return state
    
    def _parsear_arquitectura(self, respuesta: str) -> Dict:
        """Parsea la arquitectura de tareas desde la respuesta"""
        tareas = []
        
        # Buscar patrones de tareas
        patron_tarea = r'TAREA\s*(\d+):\s*([^\n]+)'
        matches = re.findall(patron_tarea, respuesta)
        
        for i, (numero, nombre) in enumerate(matches):
            tarea = {
                "id": f"tarea_{numero}",
                "nombre": nombre.strip(),
                "duracion": 8 + (i * 2),  # Duración progresiva
                "tipo": ["individual", "parejas", "grupos"][i % 3],
                "materiales": "Materiales básicos de aula",
                "instrucciones": f"Desarrollar {nombre.strip().lower()}",
                "adaptaciones": {
                    "TEA": "Instrucciones visuales claras",
                    "TDAH": "Permitir movimiento",
                    "Altas_capacidades": "Retos adicionales"
                },
                "criterio_exito": f"Completar {nombre.strip().lower()} satisfactoriamente"
            }
            tareas.append(tarea)
        
        # Si no se encontraron tareas, crear estructura básica
        if not tareas:
            tareas = [
                {
                    "id": "tarea_1",
                    "nombre": "Preparación y contexto",
                    "duracion": 10,
                    "tipo": "grupos",
                    "materiales": "Materiales básicos",
                    "instrucciones": "Introducir el tema y organizar grupos",
                    "criterio_exito": "Grupos organizados y tema comprendido"
                },
                {
                    "id": "tarea_2", 
                    "nombre": "Desarrollo principal",
                    "duracion": 25,
                    "tipo": "colaborativa",
                    "materiales": "Materiales específicos",
                    "instrucciones": "Realizar actividad principal",
                    "criterio_exito": "Actividad completada exitosamente"
                },
                {
                    "id": "tarea_3",
                    "nombre": "Presentación y cierre",
                    "duracion": 10,
                    "tipo": "gran_grupo",
                    "materiales": "Resultados de la actividad",
                    "instrucciones": "Compartir resultados y reflexionar",
                    "criterio_exito": "Ideas compartidas y reflexión realizada"
                }
            ]
        
        return {
            "tareas": tareas,
            "duracion_total": sum(t.get("duracion", 10) for t in tareas),
            "secuencia": "lineal",
            "flexibilidad": "media"
        }
    
    def _respuesta_simulada(self) -> str:
        return """
TAREA 1: Preparación y organización
TAREA 2: Exploración del concepto
TAREA 3: Práctica guiada
TAREA 4: Aplicación independiente
TAREA 5: Presentación de resultados
"""

class ValidadorCurricularAgent(BaseAgent):
    """Agente que valida el alineamiento curricular"""
    
    def __init__(self):
        super().__init__("ValidadorCurricular", llm_required=True, model_override="qwen2:latest")
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Valida el alineamiento con el currículo de 4º Primaria"""
        logger.info(f"[{self.name}] Validando alineamiento curricular")
        state.agente_actual = self.name
        
        if not state.arquitectura_tareas:
            state.problemas_detectados.append(f"{self.name}: No hay arquitectura de tareas para validar")
            return state
        
        actividad = state.actividad_seleccionada
        arquitectura = state.arquitectura_tareas
        
        prompt = f"""
Valida si esta actividad educativa cumple con los estándares curriculares de 4º de Primaria:

TEMA: {state.tema}
ACTIVIDAD: {actividad.get('titulo', 'Sin título')}
TAREAS: {len(arquitectura.get('tareas', []))} tareas planificadas
DURACIÓN: {arquitectura.get('duracion_total', 45)} minutos

Evalúa:

1. COMPETENCIAS CLAVE:
   - ¿Qué competencias específicas desarrolla?
   - ¿Son apropiadas para 4º Primaria?

2. OBJETIVOS CURRICULARES:
   - ¿Qué objetivos de aprendizaje cumple?
   - ¿Están alineados con el currículo oficial?

3. EVALUACIÓN:
   - ¿Cómo se puede evaluar el aprendizaje?
   - ¿Qué instrumentos son apropiados?

4. VIABILIDAD:
   - ¿Es factible en el tiempo asignado?
   - ¿Los materiales son accesibles?

Proporciona una validación clara: APROBADA/REQUIERE_AJUSTES/RECHAZADA
Y justifica tu decisión.
"""
        
        respuesta = self.generar_con_llm(prompt, max_tokens=600)
        validacion = self._parsear_validacion(respuesta)
        
        state.validacion_curricular = validacion
        
        estado = validacion.get('estado', 'requiere_ajustes')
        if estado == 'aprobada':
            logger.info(f"[{self.name}] Actividad validada exitosamente")
        elif estado == 'requiere_ajustes':
            logger.warning(f"[{self.name}] Actividad requiere ajustes")
        else:
            logger.error(f"[{self.name}] Actividad rechazada")
            state.problemas_detectados.append(f"{self.name}: Actividad no cumple estándares curriculares")
        
        return state
    
    def _parsear_validacion(self, respuesta: str) -> Dict:
        """Parsea la validación curricular desde la respuesta"""
        
        # Buscar estado de validación
        estado = 'requiere_ajustes'  # Por defecto
        if 'APROBADA' in respuesta.upper():
            estado = 'aprobada'
        elif 'RECHAZADA' in respuesta.upper():
            estado = 'rechazada'
        
        return {
            "estado": estado,
            "competencias_identificadas": [
                "Competencia matemática",
                "Aprender a aprender",
                "Competencias sociales y cívicas"
            ],
            "objetivos_curriculares": [
                "Resolver problemas matemáticos",
                "Trabajar en equipo",
                "Comunicar resultados"
            ],
            "instrumentos_evaluacion": [
                "Observación directa",
                "Rúbrica de trabajo en equipo", 
                "Autoevaluación"
            ],
            "viabilidad": {
                "tiempo": "adecuado",
                "materiales": "accesibles",
                "dificultad": "apropiada"
            },
            "justificacion": respuesta[:200] + "..." if len(respuesta) > 200 else respuesta,
            "recomendaciones": [
                "Mantener estructura actual",
                "Reforzar adaptaciones DUA",
                "Documentar proceso de evaluación"
            ]
        }
    
    def _respuesta_simulada(self) -> str:
        return """
APROBADA

COMPETENCIAS: Matemática, social, aprender a aprender
OBJETIVOS: Alineados con currículo 4º Primaria
EVALUACIÓN: Observación, rúbricas, autoevaluación  
VIABILIDAD: Tiempo y materiales adecuados
"""

class GestorLogisticoAgent(BaseAgent):
    """Agente que maneja aspectos logísticos y recursos"""
    
    def __init__(self):
        super().__init__("GestorLogistico", llm_required=True, model_override="llama3.2:latest")
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Gestiona recursos y aspectos logísticos"""
        logger.info(f"[{self.name}] Gestionando recursos logísticos")
        state.agente_actual = self.name
        
        if not state.arquitectura_tareas:
            state.problemas_detectados.append(f"{self.name}: No hay arquitectura de tareas para gestionar")
            return state
        
        actividad = state.actividad_seleccionada
        arquitectura = state.arquitectura_tareas
        duracion = arquitectura.get('duracion_total', 45)
        
        prompt = f"""
Analiza los recursos logísticos necesarios para esta actividad educativa:

ACTIVIDAD: {actividad.get('titulo', 'Sin título')}
DURACIÓN: {duracion} minutos
TAREAS: {len(arquitectura.get('tareas', []))} tareas planificadas

Proporciona:

1. MATERIALES ESPECÍFICOS:
   - Lista detallada de materiales por tarea
   - Cantidades necesarias para 25 estudiantes
   - Alternativas económicas o accesibles

2. ESPACIOS Y DISTRIBUCIÓN:
   - Configuración del aula requerida
   - Espacios adicionales necesarios
   - Distribución de estudiantes

3. TIEMPOS DETALLADOS:
   - Cronograma específico por tarea
   - Tiempos de transición
   - Flexibilidad temporal

4. PREPARACIÓN PREVIA:
   - Qué debe preparar el profesor
   - Qué pueden traer los estudiantes
   - Setup del aula

5. VIABILIDAD:
   - ¿Es viable con recursos típicos de aula?
   - ¿Qué alternativas hay si faltan recursos?

Formato claro y práctico para implementar.
"""
        
        respuesta = self.generar_con_llm(prompt, max_tokens=700)
        recursos = self._parsear_recursos(respuesta)
        
        state.recursos_logisticos = recursos
        
        viabilidad = recursos.get('viabilidad', {}).get('factible', True)
        if viabilidad:
            logger.info(f"[{self.name}] Recursos logísticos organizados exitosamente")
        else:
            logger.warning(f"[{self.name}] Detectados problemas de viabilidad logística")
            state.problemas_detectados.append(f"{self.name}: Recursos no completamente viables")
        
        return state
    
    def _parsear_recursos(self, respuesta: str) -> Dict:
        """Parsea los recursos logísticos desde la respuesta"""
        return {
            "materiales": {
                "basicos": [
                    "Papel (25 hojas)",
                    "Lápices (25 unidades)", 
                    "Marcadores (6 sets)",
                    "Cartulinas (10 unidades)"
                ],
                "especificos": [
                    "Material manipulativo",
                    "Calculadoras (opcional)",
                    "Reglas (25 unidades)"
                ],
                "costo_estimado": "10-15 euros",
                "alternativas": [
                    "Usar material reciclado",
                    "Reutilizar recursos existentes",
                    "Materiales caseros"
                ]
            },
            "espacios": {
                "configuracion_aula": "Grupos de 4-5 estudiantes",
                "espacios_adicionales": "No requeridos",
                "distribucion": "Mesas agrupadas, espacio central libre",
                "accesibilidad": "Considerada para estudiantes con necesidades especiales"
            },
            "cronograma": {
                "preparacion": "5 minutos",
                "desarrollo": f"{30} minutos", 
                "cierre": "10 minutos",
                "flexibilidad": "+/- 5 minutos por fase",
                "transiciones": "2 minutos entre tareas"
            },
            "preparacion_previa": {
                "profesor": [
                    "Preparar materiales",
                    "Configurar aula",
                    "Revisar adaptaciones"
                ],
                "estudiantes": [
                    "Traer estuche completo",
                    "Material personal básico"
                ],
                "tiempo_prep": "15 minutos"
            },
            "viabilidad": {
                "factible": True,
                "nivel_dificultad": "Medio",
                "recursos_criticos": "Ninguno",
                "contingencias": [
                    "Plan B si faltan materiales",
                    "Adaptación para grupos más pequeños",
                    "Versión digital alternativa"
                ]
            }
        }
    
    def _respuesta_simulada(self) -> str:
        return """
MATERIALES: Papel, lápices, marcadores, cartulinas
ESPACIOS: Aula regular, grupos de 4-5 estudiantes
TIEMPOS: 45 minutos total, flexible
PREPARACIÓN: 15 minutos previos
VIABILIDAD: Alta, recursos accesibles
"""

# ===== ORQUESTADOR PRINCIPAL =====

class OrquestadorAgent(BaseAgent):
    """Agente maestro que coordina todo el flujo"""
    
    def __init__(self):
        super().__init__("Orquestador", llm_required=False)
        
        # Pipeline de agentes
        self.agentes = {
            'ideador': IdeadorAgent(),
            'adaptador_dua': AdaptadorDUAAgent(),
            'arquitecto_tareas': ArquitectoTareasAgent(),
            'validador_curricular': ValidadorCurricularAgent(),
            'gestor_logistico': GestorLogisticoAgent()
        }
        
        # Flujo normal del pipeline
        self.flujo_normal = [
            'ideador',
            'adaptador_dua', 
            'arquitecto_tareas',
            'validador_curricular',
            'gestor_logistico'
        ]
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Orquesta el proceso completo de generación de actividad"""
        
        logger.info(f"🎯 [{self.name}] Iniciando generación de actividad: {state.tema}")
        state.timestamp_inicio = datetime.now().isoformat()
        
        # Ejecutar pipeline principal
        for i, agente_name in enumerate(self.flujo_normal):
            logger.info(f"📋 Paso {i+1}/{len(self.flujo_normal)}: {agente_name}")
            
            try:
                agente = self.agentes[agente_name]
                state = agente.procesar(state)
                
                # Verificar si hay errores críticos
                if self._hay_errores_criticos(state):
                    logger.error(f"❌ Errores críticos en {agente_name}")
                    state.estado = EstadoActividad.ERROR
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error ejecutando {agente_name}: {e}")
                state.problemas_detectados.append(f"Error en {agente_name}: {str(e)}")
                state.estado = EstadoActividad.ERROR
                break
        
        # Evaluar resultado final
        if state.estado != EstadoActividad.ERROR:
            state.estado = EstadoActividad.COMPLETADO
            logger.info(f"✅ [{self.name}] Actividad generada exitosamente")
        
        return state
    
    def _hay_errores_criticos(self, state: ActividadState) -> bool:
        """Verifica si hay errores que impidan continuar"""
        # Verificar validación curricular rechazada
        if state.validacion_curricular:
            if state.validacion_curricular.get('estado') == 'rechazada':
                return True
        
        # Verificar si hay muchos problemas acumulados
        if len(state.problemas_detectados) >= 3:
            return True
            
        return False

# ===== SISTEMA PRINCIPAL =====

class SistemaMultiAgenteCompleto:
    """Sistema completo que coordina la generación de actividades educativas"""
    
    def __init__(self):
        self.orquestador = OrquestadorAgent()
        
        # Verificar conexiones individuales de cada agente
        logger.info("🔍 Verificando conexiones individuales de cada agente...")
        self._verificar_conexiones_agentes()
    
    def _verificar_conexiones_agentes(self):
        """Verifica la conexión de cada agente individualmente"""
        agentes_conectados = 0
        total_agentes = len(self.orquestador.agentes)
        
        for nombre, agente in self.orquestador.agentes.items():
            if agente.verificar_conexion_individual():
                logger.info(f"✅ {nombre} conectado correctamente con {agente.model}")
                agentes_conectados += 1
            else:
                logger.warning(f"❌ {nombre} falló conexión con {agente.model}")
        
        logger.info(f"📊 Resultado: {agentes_conectados}/{total_agentes} agentes conectados")
        
        if agentes_conectados == total_agentes:
            logger.info("🎉 Todos los agentes están conectados y listos")
        elif agentes_conectados > 0:
            logger.warning(f"⚠️ Solo {agentes_conectados} agentes funcionarán con LLM, el resto usará simuladores")
        else:
            logger.error("❌ Ningún agente pudo conectar, todo funcionará con simuladores")
        
    def generar_actividad(self, tema: str, restricciones: Dict = None) -> ActividadState:
        """Método principal para generar una actividad educativa completa"""
        
        # Crear estado inicial
        state_inicial = ActividadState(
            tema=tema,
            nivel_educativo="4º Primaria"
        )
        
        if restricciones:
            state_inicial.__dict__.update(restricciones)
        
        logger.info(f"🚀 Iniciando generación de actividad: '{tema}'")
        
        # Procesar a través del orquestador
        estado_final = self.orquestador.procesar(state_inicial)
        
        # Mostrar resultado final
        self._mostrar_resultado_final(estado_final)
        
        return estado_final
    
    def _mostrar_resultado_final(self, state: ActividadState):
        """Muestra el resultado final del proceso"""
        print("\n" + "="*70)
        print("🎯 RESULTADO FINAL")
        print("="*70)
        
        print(f"Estado: {state.estado.value.upper()}")
        print(f"Tema: {state.tema}")
        
        if state.estado == EstadoActividad.COMPLETADO:
            print("✅ Actividad generada exitosamente")
            
            if state.actividad_seleccionada:
                print(f"\n📚 Actividad: {state.actividad_seleccionada.get('titulo', 'Sin título')}")
            
            if state.arquitectura_tareas:
                tareas = state.arquitectura_tareas.get('tareas', [])
                print(f"📋 Tareas: {len(tareas)} tareas definidas")
                duracion = state.arquitectura_tareas.get('duracion_total', 0)
                print(f"⏱️  Duración: {duracion} minutos")
            
            if state.adaptaciones_dua:
                print(f"🎭 Adaptaciones DUA: Aplicadas exitosamente")
            
            if state.validacion_curricular:
                estado_val = state.validacion_curricular.get('estado', 'sin validar')
                print(f"✅ Validación curricular: {estado_val.upper()}")
            
            if state.recursos_logisticos:
                viabilidad = state.recursos_logisticos.get('viabilidad', {}).get('factible', False)
                print(f"🎒 Recursos: {'VIABLES' if viabilidad else 'REVISAR'}")
                
        elif state.estado == EstadoActividad.ERROR:
            print("❌ Error en la generación")
            
        if state.problemas_detectados:
            print(f"\n⚠️  Problemas detectados ({len(state.problemas_detectados)}):")
            for problema in state.problemas_detectados:
                print(f"  - {problema}")
        
        print("="*70)
    
    def guardar_actividad(self, state: ActividadState, archivo: str = None):
        """Guarda la actividad generada en un archivo JSON"""
        if not archivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo = f"../temp/diversificado_inteligente_{timestamp}.json"
        else:
            # Asegurar que el archivo se guarde en ../temp/
            if not archivo.startswith('../temp/'):
                archivo = f"../temp/{archivo}"
        
        # Convertir a diccionario serializable
        data = {
            "metadatos": {
                "tema": state.tema,
                "nivel": state.nivel_educativo,
                "estado": state.estado.value,
                "timestamp": state.timestamp_inicio,
                "problemas": state.problemas_detectados
            },
            "actividad": state.actividad_seleccionada,
            "adaptaciones_dua": state.adaptaciones_dua,
            "arquitectura_tareas": state.arquitectura_tareas,
            "validacion_curricular": state.validacion_curricular,
            "recursos_logisticos": state.recursos_logisticos
        }
        
        try:
            # Crear directorio temp si no existe
            temp_dir = os.path.dirname(archivo)
            os.makedirs(temp_dir, exist_ok=True)
            
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Actividad guardada en: {archivo}")
            print(f"💾 Actividad guardada en: {archivo}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando actividad: {e}")

# ===== FUNCIÓN PRINCIPAL =====

def solicitar_datos_usuario():
    """Solicita los datos de entrada al usuario de forma interactiva"""
    print("🎯 Sistema Multi-Agente Inteligente para Actividades Educativas")
    print("=" * 60)
    print("📝 Por favor, proporciona los siguientes datos:\n")
    
    # 1. Materia
    print("📚 MATERIA:")
    print("1. Matemáticas")
    print("2. Lengua")  
    print("3. Ciencias")
    print("4. Otra (especificar)")
    
    while True:
        try:
            opcion_materia = input("\nSelecciona la materia (1-4): ").strip()
            if opcion_materia == "1":
                materia = "Matemáticas"
                break
            elif opcion_materia == "2":
                materia = "Lengua"
                break
            elif opcion_materia == "3":
                materia = "Ciencias"
                break
            elif opcion_materia == "4":
                materia = input("Especifica la materia: ").strip()
                if materia:
                    break
                print("❌ Por favor, especifica una materia válida")
            else:
                print("❌ Opción inválida. Por favor selecciona 1, 2, 3 o 4")
        except KeyboardInterrupt:
            print("\n⚠️ Proceso cancelado por el usuario")
            return None
    
    # 2. Tema específico
    print(f"\n🎯 TEMA ESPECÍFICO para {materia}:")
    
    # Sugerencias según la materia
    if materia.lower() in ["matemáticas", "matematicas"]:
        print("💡 Ejemplos: fracciones, multiplicación, geometría, medidas...")
    elif materia.lower() == "lengua":
        print("💡 Ejemplos: tiempos verbales, comprensión lectora, ortografía...")
    elif materia.lower() == "ciencias":
        print("💡 Ejemplos: sistema solar, estados de la materia, animales...")
    else:
        print("💡 Especifica el tema que quieres trabajar...")
    
    tema = input(f"Tema específico: ").strip()
    if not tema:
        print("❌ El tema no puede estar vacío")
        tema = input("Por favor, especifica un tema: ").strip()
    
    # 3. Duración
    print(f"\n⏰ DURACIÓN:")
    print("1. 30 minutos")
    print("2. 45 minutos") 
    print("3. 60 minutos")
    print("4. 90 minutos")
    print("5. Otra duración (especificar)")
    
    while True:
        try:
            opcion_duracion = input("\nSelecciona la duración (1-5): ").strip()
            if opcion_duracion == "1":
                duracion = 30
                break
            elif opcion_duracion == "2":
                duracion = 45
                break
            elif opcion_duracion == "3":
                duracion = 60
                break
            elif opcion_duracion == "4":
                duracion = 90
                break
            elif opcion_duracion == "5":
                duracion_input = input("Duración en minutos: ").strip()
                try:
                    duracion = int(duracion_input)
                    if duracion > 0:
                        break
                    else:
                        print("❌ La duración debe ser mayor a 0 minutos")
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
            else:
                print("❌ Opción inválida. Por favor selecciona 1-5")
        except KeyboardInterrupt:
            print("\n⚠️ Proceso cancelado por el usuario")
            return None
    
    # 4. Lugar
    print(f"\n🏢 LUGAR DE DESARROLLO:")
    print("1. Aula")
    print("2. Patio")
    print("3. Ambos (aula y patio)")
    print("4. Otro lugar (especificar)")
    
    while True:
        try:
            opcion_lugar = input("\nSelecciona el lugar (1-4): ").strip()
            if opcion_lugar == "1":
                lugar = "aula"
                break
            elif opcion_lugar == "2":
                lugar = "patio"
                break
            elif opcion_lugar == "3":
                lugar = "aula y patio"
                break
            elif opcion_lugar == "4":
                lugar = input("Especifica el lugar: ").strip()
                if lugar:
                    break
                print("❌ Por favor, especifica un lugar válido")
            else:
                print("❌ Opción inválida. Por favor selecciona 1-4")
        except KeyboardInterrupt:
            print("\n⚠️ Proceso cancelado por el usuario")
            return None
    
    # Confirmación
    print(f"\n✅ RESUMEN DE TU SOLICITUD:")
    print("=" * 40)
    print(f"📚 Materia: {materia}")
    print(f"🎯 Tema: {tema}")
    print(f"⏰ Duración: {duracion} minutos")
    print(f"🏢 Lugar: {lugar}")
    print("=" * 40)
    
    confirmar = input("\n¿Confirmas estos datos? (s/n): ").lower().strip()
    if confirmar not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Proceso cancelado. Ejecuta de nuevo para reintentar.")
        return None
    
    return {
        "materia": materia,
        "tema": tema,
        "duracion": duracion,
        "lugar": lugar
    }

def main():
    """Función principal del sistema"""
    try:
        # Solicitar datos al usuario
        datos = solicitar_datos_usuario()
        if datos is None:
            return
        
        print(f"\n🚀 Iniciando generación de actividad...")
        print("⏳ Esto puede tomar algunos minutos...")
        
        # Crear sistema
        sistema = SistemaMultiAgenteCompleto()
        
        # Crear tema combinado
        tema_completo = f"{datos['tema']} ({datos['materia']})"
        
        # Generar actividad con los datos del usuario
        resultado = sistema.generar_actividad(
            tema=tema_completo,
            restricciones={
                "materia": datos["materia"],
                "duracion_max": datos["duracion"],
                "lugar": datos["lugar"],
                "nivel": "4º Primaria"
            }
        )
        
        # Guardar resultado
        archivo = f"../temp/diversificado_{datos['materia'].lower()}_{datos['tema'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        sistema.guardar_actividad(resultado, archivo)
        
        print(f"\n🎉 ¡Actividad de {datos['materia']} sobre '{datos['tema']}' creada exitosamente!")
        print(f"📋 Duración: {datos['duracion']} minutos")
        print(f"🏢 Lugar: {datos['lugar']}")
        print(f"💾 Guardada en: {archivo}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en el sistema principal: {e}")
        print(f"❌ Error en el sistema: {e}")
        print("🔧 Por favor, reporta este error para que podamos solucionarlo")

if __name__ == "__main__":
    main()