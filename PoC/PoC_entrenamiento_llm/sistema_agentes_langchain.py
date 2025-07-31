#!/usr/bin/env python3
"""
Sistema de Agentes Langchain JERÁRQUICO para Generación de Actividades Educativas
Versión con estructura jerárquica y coordinador general, migrado de CrewAI.
"""

from typing import List, Dict
from dataclasses import dataclass
import logging
import os
import json
from datetime import datetime
from functools import partial

# Langchain imports
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate # Import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama

# Configuración básica
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LANGCHAIN_JERARQUICO")

# Configurar entorno (si es necesario para Langchain, aunque menos crítico que para CrewAI)
# os.environ["LANGCHAIN_TRACING_V2"] = "true" # Opcional: para trazar con Langsmith
# os.environ["LANGCHAIN_API_KEY"] = "YOUR_LANGCHAIN_API_KEY" # Opcional: para Langsmith

@dataclass
class ActividadEducativa:
    """Estructura para actividades educativas"""
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

class SistemaJerarquicoLangchain:
    """Sistema con estructura jerárquica de agentes utilizando Langchain."""

    def __init__(self, ollama_host: str = "192.168.1.10"):
        self.ollama_host = ollama_host
        self.base_url = f"http://{self.ollama_host}:11434"

        # Instancias LLM directas a Ollama
        # Se usan diferentes modelos para simular la especialización de los agentes CrewAI
        self.llm_qwen3 = Ollama(model="qwen3", base_url=self.base_url, temperature=0.7)
        self.llm_qwen2 = Ollama(model="qwen2", base_url=self.base_url, temperature=0.7)
        self.llm_mistral = Ollama(model="mistral", base_url=self.base_url, temperature=0.7)

        self.tools = self._crear_herramientas_para_agentes()
        self.coordinador_agent_executor = self._crear_coordinador_general()
        logger.info("✅ Sistema jerárquico Langchain inicializado")

    def _crear_herramientas_para_agentes(self) -> List[tool]:
        """
        Crea las herramientas que el coordinador general utilizará para delegar tareas
        a los "sub-agentes" (que son cadenas LLM especializadas).
        """

        # --- Agente: Diseñador de Ambientes de Aprendizaje ---
        # Goal: Diseñar el ambiente óptimo para la actividad
        # Backstory: Especialista en psicología educativa...
        prompt_ambiente = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un Diseñador de Ambientes de Aprendizaje. Tu objetivo es diseñar el ambiente óptimo para una actividad educativa.
            Considera la psicología educativa y las mejores prácticas para crear un entorno propicio para el aprendizaje.
            Proporciona una descripción detallada del ambiente, incluyendo aspectos físicos, emocionales y sociales.
            """),
            ("user", "Diseña el ambiente para una actividad de {materia} sobre {tema}.")
        ])
        chain_ambiente = prompt_ambiente | self.llm_qwen2 | StrOutputParser()

        @tool
        def disenar_ambiente(materia: str, tema: str = "un tema general") -> str:
            """
            Diseña el ambiente óptimo para una actividad educativa.
            Requiere la materia y opcionalmente el tema.
            Devuelve una descripción detallada del ambiente.
            """
            logger.info(f"🛠️ Diseñador de Ambiente trabajando en {materia} - {tema}")
            return chain_ambiente.invoke({"materia": materia, "tema": tema})

        # --- Agente: Diseñador de Actividades Educativas ---
        # Goal: Crear actividades educativas efectivas
        # Backstory: Pedagogo especializado en experiencias de aprendizaje...
        prompt_actividad = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un Diseñador de Actividades Educativas. Tu objetivo es crear actividades educativas efectivas y colaborativas.
            Pedagogo especializado en experiencias de aprendizaje innovadoras.
            Proporciona una descripción completa de la actividad, incluyendo objetivos, pasos, recursos y evaluación.
            """),
            ("user", "Diseña una actividad colaborativa para {materia} sobre {tema}.")
        ])
        chain_actividad = prompt_actividad | self.llm_qwen3 | StrOutputParser()

        @tool
        def disenar_actividad(materia: str, tema: str = "un tema general") -> str:
            """
            Diseña una actividad educativa colaborativa.
            Requiere la materia y opcionalmente el tema.
            Devuelve una descripción completa de la actividad.
            """
            logger.info(f"🛠️ Diseñador de Actividades trabajando en {materia} - {tema}")
            return chain_actividad.invoke({"materia": materia, "tema": tema})

        # --- Agente: Especialista en Adaptaciones Educativas ---
        # Goal: Asegurar que las actividades sean inclusivas
        # Backstory: Experto en educación inclusiva...
        prompt_adaptaciones = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un Especialista en Adaptaciones Educativas. Tu objetivo es asegurar que las actividades sean inclusivas y accesibles para todos los estudiantes.
            Experto en educación inclusiva y necesidades educativas especiales.
            Proporciona una lista de adaptaciones específicas para la actividad dada.
            """),
            ("user", "Basado en la siguiente actividad: '{actividad_contenido}', sugiere adaptaciones para hacerla inclusiva.")
        ])
        chain_adaptaciones = prompt_adaptaciones | self.llm_mistral | StrOutputParser()

        @tool
        def sugerir_adaptaciones(actividad_contenido: str) -> str:
            """
            Sugiere adaptaciones para una actividad educativa para hacerla inclusiva.
            Requiere el contenido de la actividad.
            Devuelve una lista de adaptaciones.
            """
            logger.info("🛠️ Especialista en Adaptaciones sugiriendo adaptaciones.")
            return chain_adaptaciones.invoke({"actividad_contenido": actividad_contenido})

        # --- Agente: Planificador de Tareas Educativas ---
        # Goal: Descomponer actividades en tareas ejecutables
        # Backstory: Experto en análisis de tareas...
        prompt_desglose = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un Planificador de Tareas Educativas. Tu objetivo es descomponer actividades educativas complejas en tareas más pequeñas y ejecutables.
            Experto en análisis de tareas y gestión de proyectos educativos.
            Proporciona un desglose detallado de la actividad en pasos claros y concisos.
            """),
            ("user", "Descompón la siguiente actividad: '{actividad_contenido}' y sus adaptaciones: '{adaptaciones_contenido}' en tareas ejecutables.")
        ])
        chain_desglose = prompt_desglose | self.llm_qwen3 | StrOutputParser()

        @tool
        def desglosar_actividad(actividad_contenido: str, adaptaciones_contenido: str) -> str:
            """
            Descompone una actividad educativa en tareas ejecutables, considerando sus adaptaciones.
            Requiere el contenido de la actividad y el contenido de las adaptaciones.
            Devuelve un desglose detallado de las tareas.
            """
            logger.info("🛠️ Planificador de Tareas desglosando actividad.")
            return chain_desglose.invoke({
                "actividad_contenido": actividad_contenido,
                "adaptaciones_contenido": adaptaciones_contenido
            })

        # --- Agente: Asignador de Roles Educativos ---
        # Goal: Asignar roles a estudiantes según sus características
        # Backstory: Conocedor de las necesidades individuales...
        prompt_asignacion = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un Asignador de Roles Educativos. Tu objetivo es asignar roles a los estudiantes dentro de una actividad,
            considerando sus características y las tareas desglosadas.
            Conocedor de las necesidades individuales y dinámicas de grupo.
            Proporciona una asignación de roles personalizada para un grupo de estudiantes hipotéticos (e.g., Estudiante A, Estudiante B, etc.)
            basada en el desglose de tareas.
            """),
            ("user", "Dado el siguiente desglose de tareas: '{desglose_contenido}', asigna roles a un grupo de 8 estudiantes hipotéticos (Estudiante 1 a Estudiante 8).")
        ])
        chain_asignacion = prompt_asignacion | self.llm_mistral | StrOutputParser()

        @tool
        def asignar_roles(desglose_contenido: str) -> str:
            """
            Asigna roles a estudiantes hipotéticos basado en el desglose de tareas de una actividad.
            Requiere el contenido del desglose de tareas.
            Devuelve una asignación personalizada de roles.
            """
            logger.info("🛠️ Asignador de Roles asignando roles.")
            return chain_asignacion.invoke({"desglose_contenido": desglose_contenido})

        # Las tareas de "supervisión" del Director de Diseño Educativo y el Coordinador General
        # se manejarán principalmente a través del prompt del agente coordinador y la síntesis final.
        # No se crean herramientas separadas para ellas, ya que su rol es más de orquestación y validación.

        return [
            disenar_ambiente,
            disenar_actividad,
            sugerir_adaptaciones,
            desglosar_actividad,
            asignar_roles
        ]

    def _crear_coordinador_general(self) -> AgentExecutor:
        """
        Crea el agente coordinador general, que orquesta el trabajo de los sub-agentes
        utilizando las herramientas definidas.
        """
        # Role: Coordinador General Educativo
        # Goal: Supervisar y coordinar todo el proceso de diseño de actividades educativas
        # Backstory: Experto en pedagogía y gestión educativa...

        # Using PromptTemplate for the agent's main prompt to handle agent_scratchpad as a string
        # This can sometimes resolve type errors when create_react_agent's internal formatting
        # doesn't perfectly align with MessagesPlaceholder for agent_scratchpad.
        prompt_coordinador = PromptTemplate.from_template("""
            Eres el Coordinador General Educativo. Tu objetivo es supervisar y coordinar todo el proceso de diseño de actividades educativas.
            Eres un experto en pedagogía y gestión educativa.
            Tu tarea es orquestar a los especialistas para generar una actividad educativa completa, inclusiva y bien estructurada.
            Utiliza las herramientas disponibles para delegar tareas a los sub-agentes (diseñador de ambiente, diseñador de actividades,
            especialista en adaptaciones, planificador de tareas, asignador de roles).

            Sigue estos pasos:
            1. Primero, delega la creación del ambiente y la actividad principal.
            2. Luego, usa la actividad principal para solicitar adaptaciones.
            3. Con la actividad y las adaptaciones, pide el desglose de tareas.
            4. Finalmente, con el desglose, solicita la asignación de roles.
            5. Una vez que todas las partes estén completas, integra y sintetiza toda la información
               en una descripción coherente y completa de la actividad educativa.
               Asegúrate de que el resultado final sea una actividad educativa completa y validada,
               incluyendo ambiente, descripción de la actividad, adaptaciones, desglose de tareas y asignación de roles.
               Presenta el resultado de forma clara y estructurada.

            Estas son las herramientas disponibles: {tools}
            Puedes usar las siguientes herramientas: {tool_names}

            {chat_history} # This placeholder will now expect a string, or be handled by the agent's internal logic
            Question: {input}
            {agent_scratchpad} # This placeholder will now expect a string
            """)

        # Se utiliza create_react_agent para que el coordinador pueda razonar y usar herramientas.
        agent = create_react_agent(self.llm_qwen3, self.tools, prompt_coordinador)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True # Útil para depuración
        )
        return agent_executor

    def generar_actividad(self, materia: str, tema: str = None) -> ActividadEducativa:
        logger.info(f"🚀 Iniciando generación de actividad para {materia} sobre {tema or 'un tema general'}")

        try:
            # El coordinador general es el punto de entrada para el flujo jerárquico.
            # Le pasamos la instrucción inicial y él se encargará de delegar usando sus herramientas.
            instruccion_inicial = (
                f"Genera una actividad educativa completa para la materia de '{materia}' "
                f"sobre el tema '{tema or 'un tema general'}'. "
                "Asegura que incluya el diseño del ambiente, la descripción de la actividad, "
                "adaptaciones inclusivas, un desglose de tareas y una asignación de roles para 8 estudiantes hipotéticos."
            )

            # Invocar al agente coordinador.
            # With PromptTemplate, agent_scratchpad and chat_history are handled as strings by create_react_agent.
            # We don't need to explicitly pass an empty list here; the agent will manage it.
            resultado_bruto = self.coordinador_agent_executor.invoke({
                "input": instruccion_inicial,
                "chat_history": "" # Initialize chat_history as an empty string for PromptTemplate
            })
            contenido_final = resultado_bruto.get("output", str(resultado_bruto))

            # Intentar extraer información estructurada si el LLM la proporciona,
            # de lo contrario, usar el resultado completo como contenido.
            # Aquí asumimos que el LLM del coordinador sintetiza toda la información.
            # Podrías añadir un paso de parsing más robusto si el LLM siempre genera un formato específico.

            actividad = ActividadEducativa(
                id=f"langchain_{materia}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad de {materia} - {tema or 'tema general'}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_final,
                estudiantes_objetivo=[f"Estudiante {i+1}" for i in range(8)], # Based on the instruction for 8 students
                tipo="colaborativa_langchain_jerarquica",
                adaptaciones=["inclusiva", "diferenciada"], # This could be extracted from contenido_final if the LLM details it
                metadatos={
                    "sistema": "langchain_jerarquico",
                    "niveles": ["coordinacion", "delegacion_herramientas"],
                    "ollama_host": self.ollama_host
                },
                timestamp=datetime.now().isoformat()
            )
            return actividad

        except Exception as e:
            logger.error(f"Error generando actividad con Langchain: {e}", exc_info=True)
            return self._crear_actividad_fallback(materia, tema, str(e))

    def _crear_actividad_fallback(self, materia: str, tema: str, error: str) -> ActividadEducativa:
        """Crea una actividad de fallback en caso de error."""
        return ActividadEducativa(
            id=f"fallback_langchain_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=f"Actividad Básica de {materia} (Fallback)",
            materia=materia,
            tema=tema or "tema general",
            contenido=f"Error al generar la actividad con Langchain: {error}\n\nActividad básica de ejemplo generada como fallback.",
            estudiantes_objetivo=[],
            tipo="fallback",
            adaptaciones=[],
            metadatos={"error": error, "sistema": "langchain_fallback"},
            timestamp=datetime.now().isoformat()
        )

def main():
    print("="*60)
    print("🏫 SISTEMA JERÁRQUICO DE DISEÑO EDUCATIVO (Langchain)")
    print("="*60)
    try:
        # Asegúrate de que tu servidor Ollama esté corriendo en esta IP y puerto
        # Puedes cambiar '192.168.1.10' a 'localhost' si Ollama está en tu máquina local
        sistema = SistemaJerarquicoLangchain(ollama_host="localhost") # Cambia esto si tu Ollama no está en localhost

        while True:
            print("\nOpciones:")
            print("1. Generar actividad educativa")
            print("2. Salir")
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                materia = input("Materia (ej. matematicas/lengua/ciencias): ").lower()
                tema = input("Tema específico (opcional): ").strip() or None
                print("\nGenerando actividad, esto puede tomar un momento...")
                actividad = sistema.generar_actividad(materia, tema)

                print("\n" + "="*60)
                print(f"📜 ACTIVIDAD GENERADA - {actividad.titulo}")
                print("="*60)
                print(actividad.contenido)
                print("\nMetadata:", json.dumps(actividad.metadatos, indent=2))
            elif opcion == "2":
                print("👋 Hasta luego!")
                break
            else:
                print("❌ Opción no válida")
    except ImportError as ie:
        print(f"❌ Error de importación: {ie}. Asegúrate de tener 'langchain', 'langchain-community' y 'langchain-core' instalados.")
        print("Puedes instalarlos con: pip install langchain langchain-community langchain-core")
    except Exception as e:
        print(f"❌ Un error inesperado ocurrió: {e}")
        print("Asegúrate de que Ollama esté corriendo y los modelos 'qwen3', 'qwen2', 'mistral' estén descargados.")
        print("Comprueba la IP del host de Ollama en el código.")


if __name__ == "__main__":
    main()
