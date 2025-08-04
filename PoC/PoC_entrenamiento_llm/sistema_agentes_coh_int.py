import os
import json
import requests
import traceback
import logging

# ================================================================================
# CONFIGURACIÓN CRÍTICA DE OLLAMA + CREWAI (DEBE IR ANTES DE LOS IMPORTS)
# ================================================================================

# Variables de entorno necesarias para CrewAI + Ollama
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"  
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"
os.environ["LITELLM_PROVIDER"] = "ollama"
os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "ollama/llama3:latest"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["HTTPX_TIMEOUT"] = "120"

from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from requests.exceptions import ConnectionError, Timeout

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("COH_INT_SYSTEM")

OLLAMA_SERVER_URL = "http://192.168.1.10:11434"

# Configuración del LLM con patrón exitoso
try:
    ollama_llm = Ollama(
        model="ollama/llama3:latest",
        base_url="http://192.168.1.10:11434"
    )
    logger.info("✅ LLM Ollama configurado correctamente")
except Exception as e:
    logger.error(f"❌ Error configurando LLM: {e}")
    raise

# Rutas a los archivos de datos
PERFIL_AULA_FILE = "perfiles_4_primaria.json"
ACTIVIDADES_EJEMPLO_DIR = "actividades_generadas"

def test_ollama_connection():
    """
    Verifica si el servidor de Ollama está accesible con un timeout.
    Si la conexión falla o el tiempo de espera expira, el script se detendrá.
    """
    try:
        print(f"Intentando conectar con el servidor de Ollama en {OLLAMA_SERVER_URL}...")
        response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=5) # Timeout de 5 segundos
        response.raise_for_status() # Lanza un error para códigos de estado HTTP malos
        print("Conexión con el servidor de Ollama exitosa. El modelo está disponible.")
    except ConnectionError as e:
        print("\n--- ¡ERROR DE CONEXIÓN! ---")
        print(f"No se pudo conectar al servidor de Ollama en {OLLAMA_SERVER_URL}.")
        print("Asegúrate de que el servidor de Ollama esté en ejecución y sea accesible desde tu red local.")
        print("Saliendo del script...")
        exit()
    except Timeout:
        print("\n--- ¡ERROR DE TIEMPO DE ESPERA! ---")
        print(f"La conexión con el servidor de Ollama en {OLLAMA_SERVER_URL} expiró.")
        print("Esto puede deberse a un cortafuegos que bloquea la conexión o a una configuración de red incorrecta.")
        print("Saliendo del script...")
        exit()
    except requests.exceptions.RequestException as e:
        print(f"Ocurrió un error al verificar el servidor de Ollama: {e}")
        print("💡 Asegúrate de tener llama3:latest disponible ejecutando:")
        print("   ollama pull llama3:latest")
        print("Saliendo del script...")
        exit()

def cargar_perfil_aula(file_path):
    """Carga los datos del perfil del aula desde un archivo JSON."""
    if not os.path.exists(file_path):
        print(f"Error: No se encontró el archivo de perfil del aula en {file_path}")
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_actividades_ejemplo(dir_path):
    """Carga actividades de ejemplo para few-shot learning desde un directorio."""
    if not os.path.exists(dir_path):
        return []
    examples = []
    for filename in os.listdir(dir_path):
        if filename.startswith("k_") and filename.endswith(".txt"):
            filepath = os.path.join(dir_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                examples.append(f.read())
    return examples

# Cargar los datos necesarios
perfil_aula_data = cargar_perfil_aula(PERFIL_AULA_FILE)
if not perfil_aula_data:
    exit()

actividades_ejemplo = cargar_actividades_ejemplo(ACTIVIDADES_EJEMPLO_DIR)
few_shot_prompt_part = ""
if actividades_ejemplo:
    few_shot_prompt_part = (
        "Ten en cuenta estos ejemplos de actividades exitosas para replicar su estilo, "
        "coherencia interna y especificidad. Aquí hay un ejemplo:\n"
        f"```json\n{actividades_ejemplo[0]}\n```"
    )
    print(f"Se cargaron {len(actividades_ejemplo)} actividades de ejemplo para few-shot learning.")
else:
    print("No se encontraron actividades de ejemplo. El few-shot learning no será aplicado.")

# --- DEFINICIÓN DE AGENTES ---

contexto_analyst = Agent(
    role="Analista de Contexto Pedagógico",
    goal="Evaluar el perfil del aula y el prompt del profesor para establecer el 'clima' y las condiciones iniciales óptimas para una actividad.",
    backstory=(
        f"Eres un experto en pedagogía y diseño curricular. Analizas el 'estado probabilístico' del aula "
        f"(basado en el perfil: {perfil_aula_data}) y el prompt del profesor para definir el 'Hamiltoniano' "
        "pedagógico de la actividad. Tu objetivo es determinar el tipo de actividad (exploratoria, narrativa, "
        "colaborativa, etc.) y su complejidad, para maximizar el potencial de aprendizaje del grupo."
    ),
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False
)

activity_designer = Agent(
    role="Diseñador de Actividades Detalladas",
    goal="Crear una estructura de actividad coherente, con tareas específicas, basándose en el clima y los objetivos.",
    backstory=(
        f"Eres un planificador de lecciones meticuloso. Basándote en el clima general definido y en los objetivos, "
        f"diseñas la actividad paso a paso. {few_shot_prompt_part} "
        "Tu tarea es crear un plan detallado en formato JSON, definiendo el título, "
        "los objetivos, la duración y la estructura en fases y tareas específicas."
    ),
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False
)

adaptation_agent = Agent(
    role="Consultor de Adaptaciones y Modalidades",
    goal="Sugerir adaptaciones concretas para las tareas y definir la modalidad de trabajo (individual, parejas, grupos) más adecuada para cada una, sin asignar nombres específicos.",
    backstory=(
        "Eres un especialista en pedagogía inclusiva. Analizas cada tarea de la actividad y, sin etiquetar a los "
        "alumnos, propones adaptaciones que surjan del 'terreno' (el perfil del aula). "
        "Tu objetivo es asegurar que la actividad pueda ser abordada de manera óptima por la diversidad "
        "de estudiantes, sugiriendo diferentes rutas y modalidades de trabajo."
    ),
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False
)

# --- DEFINICIÓN DE TAREAS ---

test_ollama_connection()

teacher_prompt = input("¡Hola, profesor/a! ¿Qué actividad quieres diseñar? Describe los objetivos, el tema y cualquier idea que tengas: \n")

clima_task = Task(
    description=(
        f"Analiza este prompt del profesor: '{teacher_prompt}' y el siguiente perfil del aula:\n"
        f"```json\n{json.dumps(perfil_aula_data, indent=2, ensure_ascii=False)}\n```\n"
        "Genera una descripción del 'clima' de la actividad, incluyendo si será simple/compleja, "
        "si tendrá una narrativa, si será exploratoria, y qué tipo de metodologías "
        "serían más adecuadas para este grupo."
    ),
    agent=contexto_analyst,
    expected_output="Una descripción de alto nivel del 'clima' de la actividad, especificando su tipo (ej. narrativa, exploratoria), complejidad y metodologías adecuadas."
)

design_task = Task(
    description=(
        "Usando el clima de la actividad generado, crea una actividad completa. "
        "Define un título, duración, objetivos específicos y una estructura en fases. "
        "Para cada fase, describe las tareas concretas y los recursos sugeridos. "
        "El resultado debe ser un JSON bien formateado y coherente, similar a los ejemplos de few-shot."
    ),
    agent=activity_designer,
    context=[clima_task],
    expected_output="Un objeto JSON completo y bien formateado que describe la actividad pedagógica detallada, incluyendo fases, tareas, duración y objetivos."
)

adaptation_task = Task(
    description=(
        "Toma la actividad detallada del agente Diseñador. Para cada 'fase' y 'tarea' de la actividad, "
        "propón adaptaciones y modalidades de trabajo (individual, parejas, grupos, aula completa). "
        "Justifica brevemente por qué estas adaptaciones son óptimas para la diversidad del aula "
        "sin mencionar estudiantes específicos. El output debe ser una lista de sugerencias."
    ),
    agent=adaptation_agent,
    context=[design_task],
    expected_output="Una lista detallada de sugerencias de adaptaciones y modalidades de trabajo, fase por fase, para la actividad generada."
)

# --- CONSTRUCCIÓN DE LA CREW INICIAL ---

crew = Crew(
    agents=[contexto_analyst, activity_designer, adaptation_agent],
    tasks=[clima_task, design_task, adaptation_task],
    process=Process.sequential,
    verbose=True,
    # Se pasa la misma instancia del LLM al manager para evitar inconsistencias
    manager_llm=ollama_llm
)

# --- EJECUCIÓN DEL FLUJO Y HUMAN IN THE LOOP ---

print("--- Iniciando el diseño de la actividad con la Crew... ---")
user_accepted = False
current_proposal = None

try:
    initial_result = crew.kickoff()
    current_proposal = initial_result
    
    while not user_accepted:
        print("\n\n--- PROPUESTA COMPLETA DE ACTIVIDAD ---")
        print("---------------------------------------")

        # Se añaden comprobaciones para evitar imprimir un output no generado
        if design_task.output.raw:
            print("\n--- Plan de la actividad ---")
            print(design_task.output.raw)
        else:
            print("\n--- Plan de la actividad ---")
            print("El agente de diseño no pudo generar un plan. Revisa los logs.")

        if adaptation_task.output.raw:
            print("\n--- Adaptaciones sugeridas ---")
            print(adaptation_task.output.raw)
        else:
            print("\n--- Adaptaciones sugeridas ---")
            print("El agente de adaptación no pudo generar sugerencias. Revisa los logs.")

        print("\n---------------------------------------")

        print("\n\n--- FASE DE VALIDACIÓN: HUMAN IN THE LOOP ---")
        print("Profesor/a, la Crew ha terminado de diseñar la actividad.")

        user_feedback = input("\n¿Aceptas la propuesta? (sí/no) [Si dices 'no', se te pedirá feedback para refinarla]: ")

        if user_feedback.lower() in ['s', 'sí']:
            user_accepted = True
            print("\n¡Genial! La actividad ha sido validada y está lista para ser implementada en tu aula.")
        else:
            user_refinement_prompt = input("Por favor, describe los cambios o mejoras que te gustaría ver en la actividad: \n")

            refinement_task = Task(
                description=(
                    f"Revisa la siguiente propuesta de actividad y el feedback del profesor. "
                    f"Incorpora los cambios solicitados para mejorar la actividad. "
                    f"Feedback del profesor: '{user_refinement_prompt}'\n\n"
                    f"Propuesta original:\n{design_task.output.raw}"
                ),
                agent=activity_designer,
                context=[clima_task],
                expected_output="Un objeto JSON actualizado de la actividad pedagógica, incorporando el feedback del profesor."
            )

            print("\n--- Analizando tus comentarios y refinando la actividad... ---")
            refinement_crew = Crew(
                agents=[activity_designer],
                tasks=[refinement_task],
                process=Process.sequential,
                verbose=True,
                manager_llm=ollama_llm
            )
            
            refined_result = refinement_crew.kickoff()
            current_proposal = refined_result
            print("\n--- ¡La actividad ha sido refinada! ---")

except KeyboardInterrupt:
    print("\n--- EJECUCIÓN DETENIDA ---")
    print("El proceso fue detenido manualmente. Intenta dejar que se ejecute por completo para ver la respuesta del LLM.")
except Exception as e:
    print("\n--- ¡ERROR CRÍTICO DURANTE LA EJECUCIÓN DE LA CREW! ---")
    print("Parece que hubo un problema al intentar generar el contenido con Ollama.")
    print("Posibles causas:")
    print("- El modelo 'llama3:latest' no está disponible. Ejecuta: ollama pull llama3:latest")
    print("- Problema de configuración LLM con CrewAI.")
    print("- El LLM se detuvo inesperadamente o devolvió un error.")
    print("\nDetalles del error:")
    print(traceback.format_exc())
    print("Saliendo del script...")

print("\nEntendido. Usa esta propuesta como base y haz los ajustes necesarios. ¡Feliz enseñanza!")
