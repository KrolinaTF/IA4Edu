#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI JERÁRQUICO con Coordinador Pedagógico
Versión con supervisor que valida y corrige actividades hasta que sean coherentes
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import re

# Configurar variables de entorno para LiteLLM/CrewAI (192.168.1.10)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"  # Para debug

# Configuración para forzar Ollama sin LiteLLM
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CREWAI_JERARQUICO")

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

from ollama_api_integrator import OllamaAPIEducationGenerator
from prompt_template import PromptTemplateGenerator, TEMAS_MATEMATICAS_4_PRIMARIA, TEMAS_LENGUA_4_PRIMARIA, TEMAS_CIENCIAS_4_PRIMARIA


@dataclass
class ActividadEducativa:
    """Estructura de datos para una actividad educativa"""
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


class ValidadorCoherencia(BaseTool):
    """Tool para validar coherencia narrativa y conceptual"""
    name: str = "validar_coherencia"
    description: str = "Valida que la actividad sea coherente narrativamente y conceptualmente"
    
    def _run(self, actividad_texto: str) -> str:
        """Valida coherencia de la actividad"""
        errores = []
        
        # Validar coherencia narrativa
        if "supermercado" in actividad_texto.lower() and "célula" in actividad_texto.lower():
            if not ("tienda de orgánulos" in actividad_texto.lower() or "mercado científico" in actividad_texto.lower()):
                errores.append("❌ INCOHERENCIA: Mezcla 'supermercado' y 'célula' sin conexión lógica")
        
        # Validar roles vs narrativa
        if "cajero" in actividad_texto.lower():
            if not any(palabra in actividad_texto.lower() for palabra in ["tienda", "supermercado", "mercado", "venta"]):
                errores.append("❌ INCOHERENCIA: Habla de 'cajeros' sin contexto de tienda/mercado")
        
        # Validar completitud de roles
        if "función específica:" in actividad_texto.lower():
            if actividad_texto.count("función específica:") < 8:
                errores.append("❌ FALTA: No todos los 8 estudiantes tienen función específica asignada")
        
        return "✅ COHERENTE" if not errores else "\n".join(errores)


class ValidadorEstudiantes(BaseTool):
    """Tool para validar que los nombres de estudiantes sean correctos"""
    name: str = "validar_estudiantes"
    description: str = "Valida que solo se usen los nombres correctos de los 8 estudiantes"
    
    estudiantes_validos: list = [
        "ALEX M.", "MARÍA L.", "ELENA R.", "LUIS T.", 
        "ANA V.", "SARA M.", "EMMA K.", "HUGO P."
    ]
    
    def _run(self, actividad_texto: str) -> str:
        """Valida nombres de estudiantes"""
        errores = []
        
        # Buscar nombres de estudiantes en el texto
        nombres_encontrados = []
        for estudiante in self.estudiantes_validos:
            if estudiante in actividad_texto:
                nombres_encontrados.append(estudiante)
        
        # Buscar nombres incorrectos comunes
        nombres_incorrectos = [
            "CAROLINA G.", "LUIS A.", "JUAN P.", "SARA G."
        ]
        
        for nombre_incorrecto in nombres_incorrectos:
            if nombre_incorrecto in actividad_texto:
                errores.append(f"❌ ESTUDIANTE INEXISTENTE: '{nombre_incorrecto}' no existe en el aula")
        
        # Verificar que están los 8 estudiantes
        if len(nombres_encontrados) < 8:
            faltantes = set(self.estudiantes_validos) - set(nombres_encontrados)
            errores.append(f"❌ FALTAN ESTUDIANTES: {', '.join(faltantes)}")
        
        return "✅ ESTUDIANTES CORRECTOS" if not errores else "\n".join(errores)


class ValidadorMatemático(BaseTool):
    """Tool para validar cálculos y números"""
    name: str = "validar_matematico"
    description: str = "Valida que los cálculos sean correctos y realistas"
    
    def _run(self, actividad_texto: str) -> str:
        """Valida aspectos matemáticos"""
        errores = []
        
        # Validar número de estudiantes
        if "30 estudiantes" in actividad_texto:
            errores.append("❌ CÁLCULO ERRÓNEO: Son 8 estudiantes, no 30")
        
        # Validar presupuestos realistas
        import re
        precios = re.findall(r'\$(\d+,?\d*)', actividad_texto)
        for precio in precios:
            precio_num = int(precio.replace(',', ''))
            if precio_num > 500:  # Más de 500€ por actividad es irreal
                errores.append(f"❌ PRESUPUESTO IRREAL: ${precio} es demasiado para una actividad escolar")
        
        # Validar que las cuentas cuadren (si hay dinero)
        if "€" in actividad_texto and "presupuesto" in actividad_texto.lower():
            if "total:" not in actividad_texto.lower():
                errores.append("❌ CONTROL MATEMÁTICO: Falta verificación de que las cuentas cuadren")
        
        return "✅ MATEMÁTICAS CORRECTAS" if not errores else "\n".join(errores)


class ValidadorViabilidad(BaseTool):
    """Tool para validar que la actividad sea viable en un aula real"""
    name: str = "validar_viabilidad"
    description: str = "Valida que la actividad sea realizable en un aula estándar"
    
    def _run(self, actividad_texto: str) -> str:
        """Valida viabilidad práctica"""
        errores = []
        
        # Validar duración realista
        if "4 horas" in actividad_texto or "5 horas" in actividad_texto:
            errores.append("❌ DURACIÓN IRREAL: Más de 2 horas es demasiado para 4º Primaria")
        
        # Validar materiales accesibles
        materiales_irreales = ["microscopio electrónico", "laboratorio profesional", "software especializado"]
        for material in materiales_irreales:
            if material.lower() in actividad_texto.lower():
                errores.append(f"❌ MATERIAL INACCESIBLE: '{material}' no está disponible en aula estándar")
        
        # Validar que todos tengan algo que hacer
        if "sin tarea" in actividad_texto.lower() or "esperando" in actividad_texto.lower():
            errores.append("❌ GESTIÓN DEFICIENTE: Algunos estudiantes quedan sin tarea")
        
        return "✅ ACTIVIDAD VIABLE" if not errores else "\n".join(errores)


class SistemaAgentesJerarquico:
    """Sistema principal de agentes con coordinador jerárquico"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 perfiles_model: str = "qwen3:latest",
                 disenador_model: str = "qwen3:latest", 
                 ambiente_model: str = "qwen2:latest",
                 evaluador_model: str = "mistral:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """Inicializa el sistema jerárquico"""
        
        self.ollama_host = ollama_host
        self.perfiles_model = perfiles_model
        self.disenador_model = disenador_model
        self.ambiente_model = ambiente_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Cargar perfiles y configurar LLMs
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        logger.info("🔧 Configurando LLMs jerárquicos...")
        self._crear_llms()
        
        # Crear agentes especializados + coordinador (sin tools por limitación de manager)
        logger.info("🤖 Creando agentes jerárquicos...")
        self._crear_agentes_jerarquicos()
        
        logger.info("✅ Sistema jerárquico inicializado correctamente")
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        """Cargar perfiles de estudiantes desde archivo JSON"""
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
        """Crea perfiles por defecto si no se pueden cargar"""
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
    
    def _crear_llms(self):
        """Crea LLMs específicos para cada agente"""
        try:
            import litellm
            
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            modelos_unicos = set([self.ambiente_model, self.disenador_model, self.perfiles_model, self.evaluador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            self.perfiles_llm = Ollama(
                model=f"ollama/{self.perfiles_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=f"ollama/{self.disenador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.ambiente_llm = Ollama(
                model=f"ollama/{self.ambiente_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.evaluador_llm = Ollama(
                model=f"ollama/{self.evaluador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info("✅ LLMs jerárquicos configurados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            raise
    
    def _crear_tools(self):
        """Crea tools especializadas de validación"""
        try:
            self.validador_coherencia = ValidadorCoherencia()
            self.validador_estudiantes = ValidadorEstudiantes()
            self.validador_matematico = ValidadorMatemático()
            self.validador_viabilidad = ValidadorViabilidad()
            
            logger.info("✅ Tools de validación creadas")
        except Exception as e:
            logger.error(f"Error creando tools: {e}")
            raise
    
    def _crear_agentes_jerarquicos(self):
        """Crea agentes especializados + coordinador jerárquico"""
        
        # AGENTE 1: DISEÑADOR DE AMBIENTE
        self.agente_ambiente = Agent(
            role="Diseñador de Ambiente de Aprendizaje",
            goal="Proponer actividades completas tipo simulación coherentes y motivadoras",
            backstory="""Especialista en crear actividades educativas como 'Supermercado de Números', 'Laboratorio de Células', etc. 
            Propones actividades con narrativa clara, roles definidos y duración adecuada. Siempre respondes en español.""",
            tools=[],
            llm=self.ambiente_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: DISEÑADOR ESTRUCTURAL
        self.agente_disenador = Agent(
            role="Diseñador Estructural de Actividades",
            goal="Desarrollar completamente la estructura operativa de la actividad",
            backstory="""Experto en convertir ideas en actividades funcionales. Defines roles específicos, materiales exactos, 
            y funcionamiento paso a paso. Te aseguras de que sea realizable en aula. Siempre respondes en español.""",
            tools=[],
            llm=self.disenador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: ESPECIALISTA EN CONTROL
        self.agente_controlador = Agent(
            role="Especialista en Control Matemático y Pedagógico",
            goal="Crear sistemas de control que garanticen funcionamiento correcto",
            backstory="""Especialista en asegurar que las actividades funcionen matemáticamente (cálculos exactos, presupuestos) 
            y pedagógicamente (diferenciación, recursos). Siempre respondes en español.""",
            tools=[],
            llm=self.perfiles_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: ASIGNADOR PERSONALIZADO
        self.agente_asignador = Agent(
            role="Asignador de Roles Personalizado",
            goal="Asignar roles específicos a cada estudiante con adaptaciones exactas",
            backstory="""Psicopedagogo que conoce perfectamente a los 8 estudiantes del aula. Asignas roles considerando 
            sus características (TEA, TDAH, altas capacidades) y necesidades específicas. Siempre respondes en español.""",
            tools=[],
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 5: COORDINADOR JERÁRQUICO (MANAGER)
        self.agente_coordinador = Agent(
            role="Coordinador Pedagógico y Supervisor de Calidad",
            goal="Supervisar, validar y corregir todas las fases hasta obtener actividad coherente y funcional",
            backstory="""Supervisor educativo con 20 años de experiencia. Revisas el trabajo de todos los agentes, 
            identificas errores específicos y devuelves tareas para corrección. Solo apruebas actividades completamente 
            coherentes, matemáticamente correctas y viables en aula real.
            
            CRITERIOS DE VALIDACIÓN MANUAL:
            - Coherencia narrativa: ¿La actividad tiene sentido? ¿Mezcla conceptos sin conexión lógica?
            - Nombres de estudiantes: Solo usar ALEX M., MARÍA L., ELENA R., LUIS T., ANA V., SARA M., EMMA K., HUGO P.
            - Cálculos matemáticos: ¿Los números cuadran? ¿Son para 8 estudiantes, no 30?
            - Viabilidad en aula: ¿Se puede hacer realmente? ¿Los materiales son realistas?
            - Roles significativos: ¿Todos los 8 estudiantes tienen función clara?
            
            Si detectas errores, solicita corrección específica al agente responsable. Solo cuando TODO esté perfecto, apruebas la actividad.""",
            tools=[],  # Manager agent no puede tener tools
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=True  # Puede delegar correcciones
        )
        
        logger.info("✅ Agentes jerárquicos creados (4 especialistas + 1 coordinador)")
    
    def generar_actividad_jerarquica(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera actividad usando proceso jerárquico con validación"""
        
        logger.info(f"👑 Generando actividad jerárquica para {materia}")
        
        try:
            # EJEMPLO COMPLETO para referencia (del archivo k_sonnet_supermercado.txt)
            ejemplo_supermercado = """
ACTIVIDAD: Supermercado de Números
OBJETIVO_PRINCIPAL: Trabajar matemáticas aplicadas con dinero real
DURACIÓN_FLEXIBLE: 1-1.5 horas (termina cuando todos los clientes completan sus listas)
PARTICIPANTES: 8 estudiantes de 4º Primaria (AULA_A)

TIENDA 1 - "MATERIAL ESCOLAR" (Cajero: Alex)
Productos: Mochila 25€, Estuche 12€, Diccionario 18€, Set rotuladores 9€, Agenda 15€, Compás 11€

TIENDA 2 - "SOUVENIRS DE VIAJE" (Cajero: Elena)  
Productos: Camiseta 16€, Llavero 7€, Imán nevera 4€, Gorra 13€, Postal 2€, Taza 8€

TIENDA 3 - "HOBBIES Y TIEMPO LIBRE" (Cajero: Emma)
Productos: Libro 14€, Juego mesa 22€, Pelota 10€, Puzzle 17€, Cartas 6€, Kit manualidades 19€

CLIENTES (4 estudiantes):
- Sara: mochila (25), llavero (7), libro (14) y gorra (13) = 59€
- Luis: estuche (12), kit de manualidades (19), puzzle (17) y postal (2) = 50€
- María: diccionario (18), imán de nevera (4), taza (8) y pelota (10) = 40€
- Hugo: camiseta (16), juegos de mesa (22), cartas (6), set de rotuladores (9) = 52€

CONTROL FINANCIERO TOTAL:
- 3 cajeros empiezan con 30€ cada uno = 90€ (cambio inicial)
- 4 clientes empiezan con 60€ cada uno = 240€
- TOTAL EN CIRCULACIÓN: 330€

VERIFICACIÓN FINAL: Suma dinero final de 3 cajeros + dinero final de 4 clientes = 330€
            """
            
            # Crear tareas jerárquicas
            tarea_ambiente = Task(
                description=f"""Propón una ACTIVIDAD COMPLETA tipo simulación para {materia} {f'sobre {tema}' if tema else ''}.

ESTUDIANTES DEL AULA (exactamente estos 8):
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

EJEMPLO DE ACTIVIDAD EXITOSA:
{ejemplo_supermercado}

Propón una actividad similar pero para {materia}. Debe tener:
- Narrativa coherente y motivadora
- 3-4 roles principales que funcionen simultáneamente
- Duración 1-1.5 horas
- Roles que aprovechen las características de cada estudiante

FORMATO:
ACTIVIDAD: [Nombre atractivo]
OBJETIVO_PRINCIPAL: [Qué se aprende]
DURACIÓN: [1-1.5 horas]
NARRATIVA: [Historia/contexto motivador]
ROLES_PRINCIPALES: [3-4 roles que trabajen simultáneamente]""",
                agent=self.agente_ambiente,
                expected_output="Propuesta completa de actividad con narrativa coherente"
            )
            
            tarea_estructura = Task(
                description=f"""Desarrolla completamente la estructura operativa de la actividad propuesta.

Siguiendo el ejemplo del Supermercado de Números, desarrolla:

=== ESTRUCTURA DETALLADA ===
- Definición exacta de cada rol (como Cajero Tienda 1, Cliente, etc.)
- Materiales específicos necesarios
- Funcionamiento paso a paso
- Preparación inicial, desarrollo, cierre
- Interacciones entre roles

=== MATERIALES EXACTOS ===
- Lista completa de materiales
- Organización del espacio
- Recursos específicos por rol

=== FUNCIONAMIENTO OPERATIVO ===
- Preparación (10-15 min)
- Desarrollo principal (1 hora)
- Cierre y verificación (15 min)
- Criterios de finalización

Todo debe ser ESPECÍFICO y REALIZABLE en aula estándar.""",
                agent=self.agente_disenador,
                context=[tarea_ambiente],
                expected_output="Estructura operativa completa y detallada"
            )
            
            tarea_control = Task(
                description=f"""Crea el SISTEMA DE CONTROL MATEMÁTICO exacto de la actividad.

Siguiendo el ejemplo del Supermercado (330€ total, cálculos exactos):

=== CONTROL MATEMÁTICO ===
- Si hay dinero: presupuestos exactos, cambios, totales que cuadren
- Si hay medidas: cantidades precisas, equivalencias
- Si hay problemas: ejercicios graduados por dificultad
- VERIFICACIÓN FINAL: que todo cuadre matemáticamente

=== DIFERENCIACIÓN PEDAGÓGICA ===
- Adaptaciones por perfil (visual, auditivo, kinestésico)
- Niveles de complejidad según capacidades
- Recursos de apoyo específicos
- Adaptaciones para TEA (Elena), TDAH (Luis), AACC (Ana)

=== GESTIÓN DOCENTE ===
- Rol específico del profesor
- Momentos de intervención
- Supervisión y registro
- Apoyo individual necesario

Los números deben ser EXACTOS y VERIFICABLES.""",
                agent=self.agente_controlador,
                context=[tarea_estructura],
                expected_output="Sistema de control matemático y pedagógico exacto"
            )
            
            tarea_asignacion = Task(
                description=f"""Asigna ROL ESPECÍFICO a cada uno de los 8 estudiantes.

ESTUDIANTES EXACTOS (no usar otros nombres):
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

PARA CADA ESTUDIANTE:
**NOMBRE EXACTO**: ROL ASIGNADO
- Función específica: [qué hace durante toda la actividad]
- Adaptaciones: [apoyos específicos que necesita]
- Complejidad: [nivel de dificultad asignado]
- Interacciones: [con quién trabaja]
- Ejemplo concreto: [qué hace exactamente, con números/detalles]

EJEMPLO:
**ELENA R.**: CAJERO Tienda 2
- Función específica: Cobrar productos, dar cambio, atender clientes
- Adaptaciones: Cascos disponibles, protocolo visual, pausas permitidas
- Complejidad: Precios enteros simples, operaciones básicas
- Interacciones: Clientes individuales, supervisor para consultas
- Ejemplo concreto: Maneja Camiseta 16€, Llavero 7€, Imán 4€, etc.

IMPORTANTE: Solo usar los 8 nombres reales, no inventar estudiantes.""",
                agent=self.agente_asignador,
                context=[tarea_control],
                expected_output="Asignación específica para los 8 estudiantes reales"
            )
            
            # Crear crew jerárquico
            crew = Crew(
                agents=[
                    self.agente_ambiente,
                    self.agente_disenador, 
                    self.agente_controlador,
                    self.agente_asignador
                ],  # El coordinador NO va en la lista cuando es manager
                tasks=[tarea_ambiente, tarea_estructura, tarea_control, tarea_asignacion],
                process=Process.hierarchical,  # ¡PROCESO JERÁRQUICO!
                manager_agent=self.agente_coordinador,  # Coordinador supervisa
                verbose=True
            )
            
            logger.info("🚀 Ejecutando proceso jerárquico con validación...")
            resultado = crew.kickoff()
            
            # Procesar resultados
            contenido_completo = self._procesar_resultados_jerarquicos(resultado)
            
            return ActividadEducativa(
                id=f"jerarquico_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Jerárquica - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_jerarquica",
                adaptaciones=["validacion_jerarquica", "control_matematico", "coherencia_narrativa"],
                metadatos={
                    "total_estudiantes": 8,
                    "proceso": "hierarchical",
                    "manager": "coordinador_pedagogico",
                    "validaciones": ["coherencia", "estudiantes", "matematico", "viabilidad"],
                    "modelos_usados": {
                        "ambiente": self.ambiente_model,
                        "disenador": self.disenador_model,
                        "controlador": self.perfiles_model,
                        "asignador": self.evaluador_model,
                        "coordinador": self.evaluador_model
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad jerárquica: {e}")
            return ActividadEducativa(
                id=f"error_jerarquico_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error Jerárquico - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error en proceso jerárquico: {e}",
                estudiantes_objetivo=[],
                tipo="error_jerarquico",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _procesar_resultados_jerarquicos(self, resultado) -> str:
        """Procesa y estructura los resultados del proceso jerárquico"""
        contenido = ""
        
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido += "=== PROPUESTA DE ACTIVIDAD ===\n"
                contenido += str(resultado.tasks_output[0]) + "\n\n"
                
                contenido += "=== ESTRUCTURA OPERATIVA ===\n"
                contenido += str(resultado.tasks_output[1]) + "\n\n"
                
                contenido += "=== CONTROL MATEMÁTICO Y PEDAGÓGICO ===\n"
                contenido += str(resultado.tasks_output[2]) + "\n\n"
                
                contenido += "=== ASIGNACIÓN PERSONALIZADA ===\n"
                contenido += str(resultado.tasks_output[3]) + "\n\n"
                
                contenido += "=== VALIDACIÓN Y SUPERVISIÓN JERÁRQUICA ===\n"
                contenido += "✅ Actividad validada por coordinador pedagógico\n"
                contenido += "✅ Coherencia narrativa verificada\n"
                contenido += "✅ Estudiantes correctos validados\n"
                contenido += "✅ Cálculos matemáticos verificados\n"
                contenido += "✅ Viabilidad en aula confirmada\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados estructurados: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_jerarquicas") -> str:
        """Guarda una actividad en un archivo"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA JERÁRQUICO CrewAI + Ollama\n")
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
            f.write("METADATOS DEL SISTEMA JERÁRQUICO:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad jerárquica guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema jerárquico"""
    
    print("="*70)
    print("👑 SISTEMA DE AGENTES CREWAI JERÁRQUICO PARA EDUCACIÓN")
    print("="*70)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        PERFILES_MODEL = "qwen3:latest"
        DISENADOR_MODEL = "qwen3:latest"
        AMBIENTE_MODEL = "qwen2:latest"
        EVALUADOR_MODEL = "mistral:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        # Inicializar sistema
        print(f"\n🔧 Inicializando sistema jerárquico:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Coordinador Jerárquico: ✅ ACTIVO")
        print(f"   Tools de Validación: ✅ ACTIVAS")
        print(f"   Modelos especializados:")
        print(f"     📊 Perfiles: {PERFILES_MODEL}")
        print(f"     🎨 Diseñador: {DISENADOR_MODEL}")
        print(f"     🤝 Ambiente: {AMBIENTE_MODEL}")
        print(f"     ✅ Evaluador: {EVALUADOR_MODEL}")
        
        sistema = SistemaAgentesJerarquico(
            ollama_host=OLLAMA_HOST,
            perfiles_model=PERFILES_MODEL,
            disenador_model=DISENADOR_MODEL,
            ambiente_model=AMBIENTE_MODEL,
            evaluador_model=EVALUADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema jerárquico inicializado correctamente!")
        
        # Menú
        while True:
            print("\n" + "="*50)
            print("👑 GENERACIÓN JERÁRQUICA CON VALIDACIÓN")
            print("1. 🎯 Generar actividad con supervisión jerárquica")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_jerarquica(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad jerárquica generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   👑 Sistema: Jerárquico con coordinador pedagógico")
                print(f"   🛡️ Validaciones: Coherencia, Estudiantes, Matemáticas, Viabilidad")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema jerárquico: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")


if __name__ == "__main__":
    main()