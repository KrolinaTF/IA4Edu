import json
import os
from crewai import Agent, Task, Crew
from langchain_community.chat_models import ChatLiteLLM
from typing import List, Dict, Any
from pydantic import BaseModel

def load_student_profiles() -> str:
    """Carga los perfiles de estudiantes"""
    try:
        with open("data/perfiles_4_primaria.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error cargando perfiles: {str(e)}"

def load_activity_library() -> str:
    """Carga la biblioteca de actividades desde archivos .md"""
    try:
        import glob
        activities = []
        
        # Buscar todos los archivos k_*.md en la carpeta data
        activity_files = glob.glob("data/k_*.md")
        
        for file_path in activity_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extraer el nombre de la actividad del nombre del archivo
                activity_name = file_path.split("/")[-1].replace("k_", "").replace(".md", "").replace("_", " ").title()
                
                activities.append({
                    "nombre": activity_name,
                    "archivo": file_path,
                    "contenido": content[:500] + "..." if len(content) > 500 else content  # Resumen para el contexto inicial
                })
        
        # Formatear como texto legible
        result = "BIBLIOTECA DE ACTIVIDADES DISPONIBLES:\n\n"
        for i, activity in enumerate(activities, 1):
            result += f"{i}. {activity['nombre']}\n"
            result += f"   Archivo: {activity['archivo']}\n"
            result += f"   Resumen: {activity['contenido'][:200]}...\n\n"
        
        return result
    except Exception as e:
        return f"Error cargando biblioteca: {str(e)}"

def load_full_activity(file_path: str) -> str:
    """Carga el contenido completo de una actividad específica"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error cargando actividad {file_path}: {str(e)}"

class AnalystAgent:
    def __init__(self):
        # Gemini para análisis básico usando litellm
        self.llm = ChatLiteLLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY"),
            temperature=0.7
        )
        self.agent = Agent(
            role='Analista Educativo',
            goal='Analizar la solicitud del profesor y el contexto del aula para entender las necesidades específicas de aprendizaje',
            backstory="""Eres un experto en pedagogía inclusiva y neuroeducación. Tu especialidad es analizar las necesidades 
            educativas de grupos diversos de estudiantes y identificar los elementos clave para diseñar actividades inclusivas 
            desde el paradigma de adaptación de terreno.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_analysis_task(self, user_request: str) -> Task:
        student_profiles = load_student_profiles()
        return Task(
            description=f"""Analiza la siguiente solicitud del profesor: "{user_request}"
            
            Aquí están los perfiles de los 8 estudiantes del aula:
            {student_profiles}
            
            Tu trabajo es:
            1. Identificar el tema, materia y nivel educativo solicitado
            2. Analizar las necesidades específicas de cada neurotipo presente en el aula
            3. Identificar los desafíos potenciales y oportunidades de colaboración
            4. Determinar los principios de diseño universal que se deben aplicar
            
            Entrega un análisis detallado que incluya:
            - Resumen de la solicitud
            - Perfil del aula (neurotipos presentes y sus características)
            - Consideraciones pedagógicas clave
            - Recomendaciones para el diseño de la actividad""",
            agent=self.agent,
            expected_output="Análisis completo del contexto educativo y recomendaciones para el diseño de la actividad"
        )

class ResearcherAgent:
    def __init__(self):
        # Gemini para búsqueda en biblioteca usando litellm
        self.llm = ChatLiteLLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.agent = Agent(
            role='Investigador de Actividades',
            goal='Buscar en la biblioteca de actividades ejemplos relevantes que sirvan de inspiración para el diseño. Crear soluciones ingeniosas orientadas a cada aula con toda su diversidad',
            backstory="""Eres un investigador educativo especializado en metodologías de aprendizaje en múltiples contextos educativos. 
            Tienes acceso a una biblioteca de actividades exitosas, además de una gran inventiva y experiencia a la hora de crear contextos adaptados
            gracias a ello, puedes identificar patrones y estrategias 
            que funcionan bien para diferentes neurotipos.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_research_task(self, analysis_result: str) -> Task:
        activity_library = load_activity_library()
        
        # Cargar 2-3 actividades completas más relevantes basándose en palabras clave
        relevant_activities = ""
        keywords = ["matemáticas", "fracciones", "colaborativo", "parejas", "ciencias", "lengua"]
        loaded_count = 0
        
        import glob
        for file_path in glob.glob("data/k_*.md"):
            if loaded_count >= 1:
                break
            with open(file_path, "r", encoding="utf-8") as f:
                preview = f.read()[:200].lower()
                if any(keyword in preview for keyword in keywords):
                    relevant_activities += f"\n\n--- ACTIVIDAD COMPLETA: {file_path} ---\n"
                    relevant_activities += load_full_activity(file_path)
                    loaded_count += 1
        
        return Task(
            description=f"""Basándote en el análisis previo: {analysis_result}
            
            Aquí está la biblioteca de actividades disponible:
            {activity_library}
            
            Y aquí están algunas actividades completas relevantes para inspiración:
            {relevant_activities}
            
            Tu trabajo es:
            1. Identificar actividades similares o relacionadas con el tema solicitado
            2. Analizar las estrategias de adaptación que han funcionado bien en los ejemplos
            3. Extraer patrones exitosos de agrupación de estudiantes 
            4. Identificar materiales y recursos efectivos usados
            5. Observar cómo se estructuran las actividades por fases/días
            
            Entrega:
            - Lista de actividades relevantes que sirvan de inspiración
            - Estrategias de adaptación exitosas por neurotipo encontradas
            - Patrones de agrupación recomendados basados en los ejemplos
            - Materiales y recursos sugeridos
            - Estructura temporal y fases recomendadas""",
            agent=self.agent,
            expected_output="Investigación completa de actividades relevantes y estrategias exitosas",
            context=[analysis_result] if isinstance(analysis_result, Task) else []
        )

class DesignerAgent:
    def __init__(self):
        # Gemini para diseño complejo usando litellm
        self.llm = ChatLiteLLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.agent = Agent(
            role='Diseñador de Actividades Inclusivas',
            goal='Crear una actividad completa siguiendo el template, con adaptaciones específicas para cada estudiante',
            backstory="""Eres un diseñador educativo experto en crear actividades de pedagógicas inclusivas en cualquier contexto educativo. 
            Has de definir muy bien la actividad de una manera comprensible para el/la docente, de manera que pueda explicar con claridad a 
            los estudiantes qué van a hacer.
            Tu especialidad es aplicar el paradigma de adaptación de terreno, diseñando desde el inicio para acomodar 
            todos los neurotipos siempre que sea posible y crear las adaptaciones individuales solo cuando no exista forma de adaptar la propia actividad.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_design_task(self, analysis_result: str, research_result: str) -> Task:
        student_profiles = load_student_profiles()
        return Task(
            description=f"""Usando el análisis: {analysis_result} y la investigación: {research_result}
            
            Perfiles de estudiantes para adaptar la actividad:
            {student_profiles}
            
            Diseña una actividad completa que incluya:
            
            1. INFORMACIÓN GENERAL:
            - Título atractivo y descriptivo
            - Descripción general de la actividad
            - Materia, tema y nivel educativo
            - Duración total estimada
            - Tipo de actividad (investigación, creativo, manipulativo, etc.)
            
            2. OBJETIVOS:
            - Objetivos de aprendizaje específicos
            - Objetivos de inclusión
            - Competencias clave a desarrollar
            - Elige una organización que optimice las tareas de los/as estudiantes y haz un reparto de las tareas para cada estudiante, grupo o pareja 
            según corresponda. Justifica la elección.
            - Crea ejemplos para cada fase y, si es necesario, para cada grupo en cada fase, orientados a que el/la docente 
            tenga claro qué se va a hacer en cada fase y qué va a hacer cada estudiante en cada fase.
            
            3. FASES DE LA ACTIVIDAD:
            Para cada fase incluir:
            - Nombre y descripción
            - Objetivo específico
            - Duración estimada
            - Lista de tareas con instrucciones paso a paso
            - Adaptaciones específicas por neurotipo
            
            4. ASIGNACIÓN DE ESTUDIANTES:
            - Dependiendo del tipo de actividad, decidir si es individual, en parejas o grupos.
            - Formar grupos/parejas considerando los perfiles de los 8 estudiantes
            - Repartir las tareas específicas que realizará cada estudiante, o grupo/pareja de estudiantes en cada una de las fases.
            - Si la actividad lo requiere, asignar roles específicos que aprovechen las fortalezas de cada uno
            - Justificar las decisiones de agrupación
            
            5. MATERIALES Y RECURSOS:
            - Materiales base para todos
            - Materiales específicos por neurotipo
            - Recursos digitales si aplica
            
            6. EVALUACIÓN:
            - Criterios generales
            - Adaptaciones de evaluación por neurotipo
            - Rúbrica inclusiva
            
            IMPORTANTE: Aplica el paradigma de adaptación de terreno diseñando desde el inicio para todos los neurotipos.
            Crea adaptaciones ESPECÍFICAS para cada uno de los 8 estudiantes usando sus perfiles individuales. Esto significa tareas concretas en la actividad, 
            no adaptaciones genéricas. Tienes que responderte a esta pregunta: para la adaptación que necesita esta persona ¿qué tarea puede realizar específicamente en esta actividad concreta?
            Da ejemplos de esas tareas específicas y orientaciones de como llevarlas a cabo. 
            El/la docente ha de conocer qué va a hacer exactamente cada estudiante en cada fase de la actividad.
            
            FORMATO DE SALIDA: Genera la actividad en formato Markdown estructurado y bien formateado, usando:
            - # para el título principal
            - ## para secciones principales
            - ### para subsecciones
            - Listas con - o * para elementos
            - **Negrita** para resaltar elementos importantes
            - Tablas markdown cuando sea apropiado para organizar información
            
            La estructura debe ser clara y fácil de leer.""",
            agent=self.agent,
            expected_output="Documento Markdown completo y bien estructurado con la actividad y todas las adaptaciones específicas para cada estudiante",
            context=[analysis_result, research_result] if isinstance(analysis_result, Task) else []
        )

class RefinementAgent:
    def __init__(self):
        # Gemini para refinamiento usando litellm
        self.llm = ChatLiteLLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.agent = Agent(
            role='Especialista en Refinamiento',
            goal='Revisar y mejorar la actividad basándose en feedback del profesor',
            backstory="""Eres un especialista en mejora continua de diseños educativos. Tu trabajo es tomar el feedback 
            del profesor y transformarlo en mejoras concretas de la actividad, manteniendo siempre el enfoque inclusivo 
            y el paradigma de adaptación de terreno. Para ello, tendrás en cuenta las necesidades del aula y los perfiles de los estudiantes""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_refinement_task(self, activity_design: str, teacher_feedback: str) -> Task:
        student_profiles = load_student_profiles()
        return Task(
            description=f"""Tienes la actividad diseñada: {activity_design}
            
            Y el feedback del profesor: {teacher_feedback}
            
            Perfiles de estudiantes (para referencia en las mejoras):
            {student_profiles}
            
            Tu trabajo es:
            1. Analizar el feedback del profesor identificando áreas específicas de mejora
            2. Revisar la actividad existente manteniendo los elementos que funcionan. Es decir, a no ser que se diga lo contrario, se mantiene la información de la actividad que se ha generado hasta ahora.
            3. Implementar las mejoras solicitadas sin perder el enfoque inclusivo
            4. Asegurar que las adaptaciones para cada neurotipo siguen siendo efectivas
            5. Verificar que la actividad mantiene coherencia pedagógica
            
            Entrega:
            - Actividad revisada con las mejoras implementadas
            - Explicación de los cambios realizados
            - Justificación de cómo los cambios mantienen o mejoran la inclusividad
            - Recomendaciones adicionales si las hay
            
            FORMATO DE SALIDA: Genera la actividad refinada en formato Markdown estructurado,
            manteniendo el mismo formato claro y organizado que la actividad original.""",
            agent=self.agent,
            expected_output="Documento Markdown completo con la actividad educativa refinada y mejorada",
            context=[activity_design] if isinstance(activity_design, Task) else []
        )

class IA4EDUCrew:
    def __init__(self, gemini_api_key: str):
        # Configurar variable de entorno para que los agentes la usen
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        
        # Inicializar agentes (cada uno con Gemini)
        self.analyst = AnalystAgent()
        self.researcher = ResearcherAgent()
        self.designer = DesignerAgent()
        self.refinement = RefinementAgent()
    
    def design_activity(self, user_request: str) -> str:
        """Ejecuta el flujo completo de diseño de actividad"""
        
        # Crear tareas
        analysis_task = self.analyst.create_analysis_task(user_request)
        research_task = self.researcher.create_research_task(analysis_task)
        design_task = self.designer.create_design_task(analysis_task, research_task)
        
        # Crear crew
        crew = Crew(
            agents=[
                self.analyst.agent,
                self.researcher.agent,
                self.designer.agent
            ],
            tasks=[
                analysis_task,
                research_task,
                design_task
            ],
            verbose=True
        )
        
        # Ejecutar crew
        result = crew.kickoff()
        return result
    
    def refine_activity(self, activity_design: str, teacher_feedback: str) -> str:
        """Refina la actividad basándose en feedback del profesor"""
        
        refinement_task = self.refinement.create_refinement_task(activity_design, teacher_feedback)
        
        crew = Crew(
            agents=[self.refinement.agent],
            tasks=[refinement_task],
            verbose=True
        )
        
        result = crew.kickoff()
        return result