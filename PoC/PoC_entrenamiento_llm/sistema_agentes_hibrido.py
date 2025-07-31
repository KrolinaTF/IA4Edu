#!/usr/bin/env python3
"""
Sistema de Agentes CrewAI HÍBRIDO - Validación + Proceso Secuencial
Combina sistema v2 (funcional) + validación mejorada sin problemas jerárquicos
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# Configurar variables de entorno para LiteLLM/CrewAI (192.168.1.10)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"

# Configuración para forzar Ollama sin LiteLLM
os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CREWAI_HIBRIDO")

try:
    from crewai import Agent, Task, Crew, Process
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


class SistemaAgentesHibrido:
    """Sistema híbrido: v2 funcional + validación mejorada + proceso secuencial"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10", 
                 perfiles_model: str = "qwen3:latest",
                 disenador_model: str = "qwen3:latest", 
                 ambiente_model: str = "qwen2:latest",
                 evaluador_model: str = "mistral:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        """
        Inicializa el sistema híbrido
        """
        self.ollama_host = ollama_host
        self.perfiles_model = perfiles_model
        self.disenador_model = disenador_model
        self.ambiente_model = ambiente_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Crear LLMs específicos para cada agente (igual que v2 funcional)
        logger.info("🔧 Configurando LLMs específicos...")
        
        try:
            import litellm
            
            modelos_unicos = set([self.ambiente_model, self.disenador_model, self.perfiles_model, self.evaluador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            os.environ["OLLAMA_API_BASE"] = f"http://{ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{ollama_host}:11434"
            
            self.perfiles_llm = Ollama(
                model=f"ollama/{self.perfiles_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=f"ollama/{self.disenador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.ambiente_llm = Ollama(
                model=f"ollama/{self.ambiente_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            self.evaluador_llm = Ollama(
                model=f"ollama/{self.evaluador_model}",
                base_url=f"http://{ollama_host}:11434"
            )
            
            logger.info(f"✅ LLMs configurados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            raise e
        
        # Cargar perfiles
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes híbridos
        self._crear_agentes_hibridos()
        
        logger.info(f"✅ Sistema híbrido inicializado")
    
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
    
    def _crear_agentes_hibridos(self):
        """Crea agentes híbridos mejorados con validación incorporada"""
        
        # AGENTE 1: DISEÑADOR DE AMBIENTE (Con validación incorporada)
        self.agente_ambiente = Agent(
            role="Diseñador de Ambiente Validado",
            goal="Proponer actividades coherentes tipo 'Supermercado de Números' validando coherencia narrativa",
            backstory="""Especialista en ambientes educativos con EXPERIENCIA EN VALIDACIÓN.

ANTES de proponer cualquier actividad, VALIDAS:
1. ¿Es coherente la narrativa? (no mezclar supermercado + células sin lógica)
2. ¿Usas solo los 8 estudiantes reales?: ALEX M., MARÍA L., ELENA R., LUIS T., ANA V., SARA M., EMMA K., HUGO P.
3. ¿La actividad tiene sentido educativo para 4º Primaria?

Solo propones actividades como 'Supermercado de Números', 'Laboratorio de Células', 'Banco de Palabras' que sean:
- Narrativamente coherentes
- Con roles que conecten lógicamente
- Para exactamente 8 estudiantes específicos

Si detectas incoherencia durante tu diseño, la corriges ANTES de presentar la propuesta.
Respondes siempre en español.""",
            tools=[],
            llm=self.ambiente_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: DISEÑADOR ESTRUCTURAL (Con validación incorporada)
        self.agente_disenador = Agent(
            role="Diseñador Estructural Validado",
            goal="Desarrollar estructuras operativas validando viabilidad en aula real",
            backstory="""Docente experto con EXPERIENCIA EN AULAS REALES.

MIENTRAS desarrollas la estructura, VALIDAS continuamente:
1. ¿Los materiales son realistas para un aula normal? (no 30 computadoras)
2. ¿La duración es apropiada? (1-1.5 horas máximo)
3. ¿El espacio es realizable? (no "naves espaciales")
4. ¿Los roles funcionan simultáneamente para 8 estudiantes?

Te basas en actividades exitosas conocidas y ajustas todo para que sea:
- Realizable en aula estándar
- Con materiales disponibles
- Operativamente funcional
- Para exactamente 8 estudiantes

Si algo no es viable durante tu diseño, lo modificas para que sí lo sea.
Respondes siempre en español.""",
            tools=[],
            llm=self.disenador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: ESPECIALISTA EN CONTROL (Con validación matemática incorporada)
        self.agente_desglosador = Agent(
            role="Especialista en Control Matemático Validado",
            goal="Crear sistemas de control validando que todos los cálculos sean exactos para 8 estudiantes",
            backstory="""Especialista en matemáticas educativas con OBSESIÓN POR LA EXACTITUD.

DURANTE todo tu trabajo, VALIDAS:
1. ¿Todos los cálculos son para 8 estudiantes? (NUNCA 30)
2. ¿Los presupuestos son realistas? (no $3000 para actividad escolar)
3. ¿Las operaciones cuadran matemáticamente?
4. ¿Las adaptaciones son específicas para cada diagnóstico?

Creas:
- Cálculos exactos y verificables
- Diferenciación real por estudiante
- Recursos pedagógicos apropiados
- Sistemas que funcionan matemáticamente

Si encuentras un error matemático durante tu trabajo, lo corriges inmediatamente.
Solo presentas sistemas que cuadran perfectamente.
Respondes siempre en español.""",
            tools=[],
            llm=self.perfiles_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: ASIGNADOR PERSONALIZADO (Con validación de estudiantes incorporada)
        self.agente_asignador = Agent(
            role="Asignador de Roles Validado",
            goal="Asignar roles específicos validando que solo se usen los 8 estudiantes reales",
            backstory="""Psicopedagogo que CONOCE PERFECTAMENTE a los 8 estudiantes del aula.

DURANTE cada asignación, VALIDAS ESTRICTAMENTE:
1. ¿Solo usas estos nombres?: ALEX M., MARÍA L., ELENA R., LUIS T., ANA V., SARA M., EMMA K., HUGO P.
2. ¿NUNCA usas estos nombres falsos?: CAROLINA G., LUIS A., JUAN P., SARA G. (NO EXISTEN)
3. ¿Cada estudiante tiene rol específico y adaptaciones apropiadas?
4. ¿Las asignaciones consideran TEA (Elena), TDAH (Luis), altas capacidades (Ana)?

Solo asignas roles a estudiantes que EXISTEN realmente en el aula.
Si durante tu trabajo usas un nombre incorrecto, lo corriges inmediatamente.
Cada estudiante real debe tener función clara, adaptaciones específicas y ejemplos concretos.
Respondes siempre en español.""",
            tools=[],
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 5: VALIDADOR FINAL (Nuevo agente secuencial)
        self.agente_validador = Agent(
            role="Validador Final y Control de Calidad",
            goal="Revisar la actividad completa y asegurar que cumple todos los criterios de calidad educativa",
            backstory="""Supervisor educativo senior con 25 años de experiencia en 4º Primaria.

Realizas la VALIDACIÓN FINAL verificando:

1. COHERENCIA NARRATIVA TOTAL:
   - ¿La actividad tiene sentido completo?
   - ¿No hay conceptos mezclados sin lógica?
   - ¿Los roles conectan con la narrativa?

2. ESTUDIANTES CORRECTOS:
   - ¿Solo aparecen los 8 nombres reales?: ALEX M., MARÍA L., ELENA R., LUIS T., ANA V., SARA M., EMMA K., HUGO P.
   - ¿No aparecen nombres falsos?: CAROLINA G., LUIS A., JUAN P., SARA G.
   - ¿Todos tienen roles específicos?

3. MATEMÁTICA EXACTA:
   - ¿Todo calculado para 8 estudiantes, no 30?
   - ¿Presupuestos realistas?
   - ¿Operaciones que cuadran?

4. VIABILIDAD PRÁCTICA:
   - ¿Materiales disponibles en aula normal?
   - ¿Duración apropiada (1-1.5 horas)?
   - ¿Espacios realistas?

Si encuentras errores, los identificas específicamente y sugieres correcciones concretas.
Solo apruebas actividades PERFECTAMENTE coherentes y realizables.
Respondes siempre en español.""",
            tools=[],
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes híbridos creados (4 especialistas + 1 validador final)")
    
    def generar_actividad_hibrida(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera actividad usando proceso secuencial con validación incorporada"""
        
        logger.info(f"🔄 Generando actividad híbrida para {materia}")
        
        try:
            # EJEMPLO DE REFERENCIA (del k_sonnet_supermercado.txt)
            ejemplo_exitoso = """
EJEMPLO DE ACTIVIDAD EXITOSA - SUPERMERCADO DE NÚMEROS:

ACTIVIDAD: Supermercado de Números
OBJETIVO_PRINCIPAL: Trabajar matemáticas aplicadas con dinero real y fracciones
DURACIÓN: 1-1.5 horas (termina cuando todos completan sus listas)
PARTICIPANTES: Exactamente 8 estudiantes específicos

TIENDAS Y CAJEROS:
- TIENDA 1 "MATERIAL ESCOLAR" (Cajero: ALEX M.)
  Productos: Mochila 25€, Estuche 12€, Diccionario 18€, Set rotuladores 9€, Agenda 15€, Compás 11€

- TIENDA 2 "SOUVENIRS DE VIAJE" (Cajero: ELENA R. - adaptaciones: cascos disponibles)  
  Productos: Camiseta 16€, Llavero 7€, Imán nevera 4€, Gorra 13€, Postal 2€, Taza 8€

- TIENDA 3 "HOBBIES Y TIEMPO LIBRE" (Cajero: EMMA K.)
  Productos: Libro 14€, Juego mesa 22€, Pelota 10€, Puzzle 17€, Cartas 6€, Kit manualidades 19€

CLIENTES CON LISTAS EXACTAS:
- SARA M.: mochila (25€), llavero (7€), libro (14€), gorra (13€) = 59€ total
- LUIS T.: estuche (12€), kit manualidades (19€), puzzle (17€), postal (2€) = 50€ total  
- MARÍA L.: diccionario (18€), imán nevera (4€), taza (8€), pelota (10€) = 40€ total
- HUGO P.: camiseta (16€), juego mesa (22€), cartas (6€), set rotuladores (9€) = 53€ total

SUPERVISOR: ANA V. (altas capacidades) - verifica cálculos, ayuda con cambios complejos

CONTROL MATEMÁTICO EXACTO:
- 3 cajeros empiezan con 30€ cada uno = 90€ total cambio inicial
- 4 clientes + 1 supervisor empiezan con: 59€ + 50€ + 40€ + 53€ + presupuesto supervisor = total
- VERIFICACIÓN FINAL: Todo el dinero debe cuadrar exactamente

Esta actividad es COHERENTE, REALISTA y funciona perfectamente en aula.
            """
            
            # Crear tareas secuenciales con validación incorporada
            tarea_ambiente = Task(
                description=f"""Diseña una ACTIVIDAD COMPLETA para {materia} {f'sobre {tema}' if tema else ''} siguiendo el modelo exitoso.

ESTUDIANTES REALES (exactamente estos 8, no otros):
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118 (necesita cascos, protocolo visual)
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102 (necesita movimiento)
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141 (puede asumir más complejidad)
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

REFERENCIA DE ACTIVIDAD EXITOSA:
{ejemplo_exitoso}

ANTES de proponer, VALIDA INTERNAMENTE:
✓ ¿Es coherente la narrativa para {materia}?
✓ ¿Solo uso los 8 nombres reales listados arriba?
✓ ¿Los roles conectan lógicamente con la materia?
✓ ¿Es similar en calidad al Supermercado de Números?

FORMATO OBLIGATORIO:
ACTIVIDAD: [Nombre atractivo coherente]
OBJETIVO_PRINCIPAL: [Qué se aprende específicamente en {materia}]
DURACIÓN: [1-1.5 horas]
NARRATIVA: [Historia/contexto COHERENTE para {materia}]
INSTALACIONES: [Cómo se organiza el aula específicamente]
ROLES_NECESARIOS: [3-4 roles que funcionen simultáneamente]

Solo propón si pasa tu validación interna.""",
                agent=self.agente_ambiente,
                expected_output="Propuesta de actividad validada internamente por coherencia y estudiantes correctos"
            )
            
            tarea_estructura = Task(
                description="""Desarrolla COMPLETAMENTE la actividad con VALIDACIÓN INTERNA de viabilidad.

DURANTE tu desarrollo, VALIDA continuamente:
✓ ¿Los materiales son realistas para aula normal?
✓ ¿La duración es apropiada (1-1.5 horas)?
✓ ¿El espacio es realizable en aula estándar?
✓ ¿Los 8 estudiantes pueden trabajar simultáneamente?

DESARROLLA OBLIGATORIAMENTE:

=== CONTEXTO PEDAGÓGICO ===
- Competencias curriculares específicas
- Nivel de complejidad para 4º Primaria
- Materiales REALISTAS disponibles en aula normal

=== ESTRUCTURA DE ROLES ===
Para cada rol especifica:
- Función exacta durante toda la actividad
- Responsabilidades específicas
- Competencias que desarrolla
- Interacciones con otros roles
- Preparación necesaria antes de empezar
- Entrega final/reporte

=== FUNCIONAMIENTO OPERATIVO ===
- Preparación inicial (10-15 min) - paso a paso
- Desarrollo principal (1 hora) - fase por fase
- Cierre y verificación (15 min) - cómo termina
- Criterio claro de finalización
- Control de calidad continuo

=== MATERIALES ESPECÍFICOS ===
- Lista exhaustiva de materiales REALISTAS
- Organización del espacio en aula normal
- Recursos específicos por rol
- Todo disponible en colegio típico

Solo presenta si pasa tu validación interna de viabilidad.""",
                agent=self.agente_disenador,
                context=[tarea_ambiente],
                expected_output="Estructura operativa completa validada internamente por viabilidad práctica"
            )
            
            tarea_control = Task(
                description="""Crea el SISTEMA DE CONTROL MATEMÁTICO validando exactitud para 8 estudiantes.

DURANTE todo tu trabajo, VALIDA internamente:
✓ ¿Todos los cálculos son para exactamente 8 estudiantes (no 30)?
✓ ¿Los presupuestos son realistas (no miles de euros)?
✓ ¿Las operaciones cuadran matemáticamente?
✓ ¿Las adaptaciones son específicas por diagnóstico?

DESARROLLA OBLIGATORIAMENTE:

=== CÁLCULOS EXACTOS ===
- Si hay dinero: presupuestos exactos para 8 estudiantes
- Si hay medidas: cantidades precisas y realistas
- Si hay problemas: ejercicios graduados por dificultad individual
- Verificación final matemática (todo debe cuadrar)

=== DIFERENCIACIÓN CONTROLADA ===
- Adaptación específica por estudiante:
  * ELENA R. (TEA): cascos, protocolo visual, pausas
  * LUIS T. (TDAH): movimiento, tareas fraccionadas
  * ANA V. (altas capacidades): retos adicionales
- Complejidad graduada según CI y capacidades
- Materiales de apoyo específicos disponibles
- Recursos de autorregulación (cascos, plastilina, etc.)

=== GESTIÓN DOCENTE ===
- Rol específico del profesor durante cada fase
- Momentos exactos de intervención individual
- Supervisión general realista y factible
- Registro de observaciones concreto
- Apoyo específico por necesidades especiales

Todo calculado exactamente para 8 estudiantes reales.
Solo presenta si pasa tu validación matemática interna.""",
                agent=self.agente_desglosador,
                context=[tarea_estructura],
                expected_output="Sistema de control matemático exacto validado internamente para 8 estudiantes"
            )
            
            tarea_asignacion = Task(
                description="""Asigna ROL ESPECÍFICO a cada estudiante VALIDANDO nombres constantemente.

ESTUDIANTES REALES (solo estos, NUNCA otros):
- 001 ALEX M.: reflexivo, visual, ninguno, CI 102
- 002 MARÍA L.: reflexivo, auditivo, ninguno
- 003 ELENA R.: reflexivo, visual, TEA_nivel_1, CI 118 (cascos, protocolo visual)
- 004 LUIS T.: impulsivo, kinestésico, TDAH_combinado, CI 102 (movimiento)
- 005 ANA V.: reflexivo, auditivo, altas_capacidades, CI 141 (reto mayor)
- 006 SARA M.: equilibrado, auditivo, ninguno, CI 115
- 007 EMMA K.: reflexivo, visual, ninguno, CI 132
- 008 HUGO P.: equilibrado, visual, ninguno, CI 114

NOMBRES PROHIBIDOS (NO EXISTEN): CAROLINA G., LUIS A., JUAN P., SARA G.

DURANTE cada asignación, VALIDA internamente:
✓ ¿Solo uso los 8 nombres listados arriba?
✓ ¿No uso ningún nombre prohibido?
✓ ¿Cada estudiante tiene función clara?
✓ ¿Las adaptaciones son apropiadas para cada diagnóstico?

FORMATO OBLIGATORIO para cada estudiante:
**NOMBRE EXACTO DE LA LISTA**: ROL ASIGNADO
- Función específica: [qué hace durante toda la actividad]
- Adaptaciones: [apoyos específicos según diagnóstico]
- Complejidad: [nivel asignado según CI y capacidades]
- Interacciones: [con quién trabaja principalmente]
- Ejemplo concreto: [qué hace exactamente con detalles]

EJEMPLO CORRECTO:
**ELENA R.**: CAJERO Tienda 2
- Función específica: Cobrar productos, dar cambio, atender clientes
- Adaptaciones: Cascos disponibles, protocolo visual, pausas permitidas
- Complejidad: Precios enteros simples, operaciones básicas
- Interacciones: Clientes individuales, supervisor para consultas
- Ejemplo concreto: Maneja Camiseta 16€, Llavero 7€, da cambio de 3€ a cliente con 10€

Solo presenta si todos los nombres pasan tu validación interna.""",
                agent=self.agente_asignador,
                context=[tarea_control],
                expected_output="Asignación específica validada internamente con solo los 8 estudiantes reales"
            )
            
            tarea_validacion = Task(
                description="""Realiza VALIDACIÓN FINAL EXHAUSTIVA de toda la actividad completa.

Revisa SISTEMÁTICAMENTE cada aspecto:

1. COHERENCIA NARRATIVA:
   ¿La actividad completa tiene sentido educativo?
   ¿Los conceptos están conectados lógicamente?
   ¿Los roles encajan con la narrativa?
   ¿Es comparable en calidad al Supermercado de Números?

2. ESTUDIANTES CORRECTOS:
   ¿Solo aparecen estos 8?: ALEX M., MARÍA L., ELENA R., LUIS T., ANA V., SARA M., EMMA K., HUGO P.
   ¿NO aparecen estos falsos?: CAROLINA G., LUIS A., JUAN P., SARA G.
   ¿Todos tienen roles específicos y significativos?

3. MATEMÁTICA EXACTA:
   ¿Todo calculado para exactamente 8 estudiantes?
   ¿Presupuestos realistas para actividad escolar?
   ¿Las operaciones cuadran matemáticamente?

4. VIABILIDAD PRÁCTICA:
   ¿Materiales disponibles en aula normal?
   ¿Duración apropiada (1-1.5 horas)?
   ¿Espacios realistas en colegio típico?
   ¿Operativamente funcional?

FORMATO DE RESPUESTA:
=== VALIDACIÓN FINAL COMPLETA ===

COHERENCIA NARRATIVA: ✓ APROBADA / ❌ ERRORES: [especificar errores]
ESTUDIANTES CORRECTOS: ✓ APROBADA / ❌ ERRORES: [especificar errores]  
MATEMÁTICA EXACTA: ✓ APROBADA / ❌ ERRORES: [especificar errores]
VIABILIDAD PRÁCTICA: ✓ APROBADA / ❌ ERRORES: [especificar errores]

DICTAMEN FINAL: ✅ ACTIVIDAD APROBADA / ❌ REQUIERE CORRECCIÓN

Si hay errores, identifica específicamente qué corregir.
Solo aprueba actividades PERFECTAMENTE coherentes y realizables.""",
                agent=self.agente_validador,
                context=[tarea_asignacion],
                expected_output="Validación final exhaustiva con dictamen de aprobación o correcciones específicas"
            )
            
            # Crear crew SECUENCIAL (no jerárquico para evitar problemas de delegación)
            crew = Crew(
                agents=[
                    self.agente_ambiente,
                    self.agente_disenador, 
                    self.agente_desglosador,
                    self.agente_asignador,
                    self.agente_validador
                ],
                tasks=[tarea_ambiente, tarea_estructura, tarea_control, tarea_asignacion, tarea_validacion],
                process=Process.sequential,  # SECUENCIAL (funciona sin problemas)
                verbose=True
            )
            
            logger.info("🚀 Ejecutando proceso híbrido secuencial con validación...")
            resultado = crew.kickoff()
            
            # Procesar resultados
            contenido_completo = self._procesar_resultados(resultado)
            
            return ActividadEducativa(
                id=f"hibrido_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Híbrida Validada - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="colaborativa_hibrida_validada",
                adaptaciones=["validacion_incorporada", "control_matematico_exacto", "coherencia_narrativa"],
                metadatos={
                    "total_estudiantes": 8,
                    "flujo_hibrido": ["ambiente_validado", "estructura_validada", "control_validado", "asignacion_validada", "validacion_final"],
                    "proceso": "secuencial_con_validacion_incorporada",
                    "modelos_usados": {
                        "ambiente": self.ambiente_model,
                        "disenador": self.disenador_model,
                        "desglosador": self.perfiles_model,
                        "asignador": self.evaluador_model,
                        "validador": self.evaluador_model
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error en proceso híbrido: {e}")
            return ActividadEducativa(
                id=f"error_hibrido_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error Híbrido - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error en proceso híbrido: {e}",
                estudiantes_objetivo=[],
                tipo="error_hibrido",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _procesar_resultados(self, resultado) -> str:
        """Procesa y estructura los resultados del crew híbrido"""
        contenido = ""
        
        try:
            if hasattr(resultado, 'tasks_output') and resultado.tasks_output:
                contenido += "=== DISEÑO DE AMBIENTE VALIDADO ===\\n"
                contenido += str(resultado.tasks_output[0]) + "\\n\\n"
                
                contenido += "=== ESTRUCTURA OPERATIVA VALIDADA ===\\n"
                contenido += str(resultado.tasks_output[1]) + "\\n\\n"
                
                contenido += "=== SISTEMA DE CONTROL MATEMÁTICO VALIDADO ===\\n"
                contenido += str(resultado.tasks_output[2]) + "\\n\\n"
                
                contenido += "=== ASIGNACIÓN PERSONALIZADA VALIDADA ===\\n"
                contenido += str(resultado.tasks_output[3]) + "\\n\\n"
                
                contenido += "=== VALIDACIÓN FINAL EXHAUSTIVA ===\\n"
                contenido += str(resultado.tasks_output[4]) + "\\n\\n"
            else:
                contenido = str(resultado)
        except Exception as e:
            logger.warning(f"Error procesando resultados: {e}")
            contenido = str(resultado)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_hibridas") -> str:
        """Guarda una actividad híbrida"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA HÍBRIDO CrewAI + Ollama\\n")
            f.write("=" * 80 + "\\n\\n")
            f.write(f"ID: {actividad.id}\\n")
            f.write(f"Título: {actividad.titulo}\\n")
            f.write(f"Materia: {actividad.materia}\\n")
            f.write(f"Tema: {actividad.tema}\\n")
            f.write(f"Tipo: {actividad.tipo}\\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\\n")
            f.write(f"Timestamp: {actividad.timestamp}\\n")
            f.write("\\n" + "-" * 50 + "\\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\\n")
            f.write("-" * 50 + "\\n\\n")
            f.write(actividad.contenido)
            f.write("\\n\\n" + "=" * 80 + "\\n")
            f.write("METADATOS DEL SISTEMA HÍBRIDO:\\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\\n")
        
        logger.info(f"💾 Actividad híbrida guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema híbrido"""
    
    print("="*70)
    print("🔄 SISTEMA DE AGENTES CREWAI HÍBRIDO - Validación + Secuencial")
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
        print(f"\\n🔧 Inicializando sistema híbrido:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   Proceso: Secuencial con validación incorporada")
        print(f"   Modelos especializados:")
        print(f"     📊 Perfiles: {PERFILES_MODEL}")
        print(f"     🎨 Diseñador: {DISENADOR_MODEL}")
        print(f"     🤝 Ambiente: {AMBIENTE_MODEL}")
        print(f"     ✅ Validador: {EVALUADOR_MODEL}")
        
        sistema = SistemaAgentesHibrido(
            ollama_host=OLLAMA_HOST,
            perfiles_model=PERFILES_MODEL,
            disenador_model=DISENADOR_MODEL,
            ambiente_model=AMBIENTE_MODEL,
            evaluador_model=EVALUADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\\n✅ Sistema híbrido inicializado!")
        
        # Menú
        while True:
            print("\\n" + "="*50)
            print("🔄 GENERACIÓN HÍBRIDA CON VALIDACIÓN")
            print("1. 🎯 Generar actividad híbrida validada")
            print("2. ❌ Salir")
            
            opcion = input("\\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_hibrida(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\\n✅ Actividad híbrida generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🔄 Sistema: Híbrido secuencial con validación incorporada")
            
            elif opcion == "2":
                print("\\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\\n❌ Error inicializando sistema híbrido: {e}")
        print("\\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. El archivo de perfiles exista")


if __name__ == "__main__":
    main()