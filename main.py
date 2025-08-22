#!/usr/bin/env python3
"""
IA4EDU - Asistente de IA para crear actividades de aprendizaje por proyectos inclusivas
"""

import os
import sys
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.markdown import Markdown
import typer
from typing import Optional

# Cargar variables de entorno
load_dotenv()

# Importar agentes
import sys
sys.path.append('.')
from agents.crew_agents import IA4EDUCrew

app = typer.Typer(
    name="ia4edu",
    help="🎓 Asistente de IA para crear actividades de aprendizaje por proyectos inclusivas",
    add_completion=False
)

console = Console()

class IA4EDUInterface:
    def __init__(self):
        self.console = Console()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.crew = None
        
        if not self.gemini_api_key:
            self.console.print("❌ [red]Error: No se encontró GEMINI_API_KEY en las variables de entorno[/red]")
            self.console.print("💡 [yellow]Configura tu clave API de Gemini:[/yellow]")
            self.console.print("   export GEMINI_API_KEY='tu_clave_aqui'")
            sys.exit(1)
        
        try:
            self.crew = IA4EDUCrew(self.gemini_api_key)
        except Exception as e:
            self.console.print(f"❌ [red]Error inicializando IA4EDU: {str(e)}[/red]")
            sys.exit(1)
    
    def show_welcome(self):
        """Muestra la pantalla de bienvenida"""
        welcome_text = """
# 🎓 IA4EDU - Asistente para Actividades Inclusivas

**Bienvenido/a al asistente de IA para crear actividades de aprendizaje por proyectos inclusivas**

## ✨ Características principales:
- 🧠 **Paradigma de adaptación de terreno**: Diseñamos desde el inicio para todos los neurotipos
- 👥 **8 perfiles de estudiantes**: TEA, TDAH, Altas Capacidades y perfiles típicos
- 🔄 **Human-in-the-loop**: Refinamiento iterativo basado en tu feedback
- 📚 **Biblioteca de actividades**: Inspiración de proyectos exitosos

## 🚀 ¿Listo para empezar?
"""
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🎓 IA4EDU",
            border_style="cyan"
        ))
    
    def get_user_request(self) -> str:
        """Obtiene la solicitud inicial del usuario"""
        self.console.print("\n" + "="*60)
        self.console.print("📝 [bold cyan]PASO 1: Describe tu actividad[/bold cyan]")
        self.console.print("="*60)
        
        examples = """
💡 **Ejemplos de solicitudes:**
- "Crea una actividad de matemáticas sobre fracciones para 4º de primaria, para trabajar en parejas"
- "Necesito un proyecto de ciencias sobre ecosistemas para 5º primaria, en grupos de 3-4 estudiantes"
- "Diseña una actividad de lengua sobre escritura creativa para 3º primaria"
"""
        
        self.console.print(Markdown(examples))
        self.console.print()
        
        user_request = Prompt.ask(
            "[bold yellow]🎯 Describe la actividad que quieres crear[/bold yellow]",
            default="Crea una actividad de matemáticas sobre fracciones para 4º de primaria, para trabajar en parejas"
        )
        
        return user_request
    
    def show_student_profiles(self):
        """Muestra información sobre los perfiles de estudiantes"""
        try:
            with open("data/perfiles_4_primaria.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.console.print("\n" + "="*60)
            self.console.print("👥 [bold cyan]PASO 2: Perfiles de tu aula (8 estudiantes)[/bold cyan]")
            self.console.print("="*60)
            
            profiles_summary = "## 🧠 Neurotipos en tu aula:\n\n"
            neurotipo_counts = {}
            
            for student in data["estudiantes"]:
                neurotipo = student["diagnostico_formal"]
                neurotipo_counts[neurotipo] = neurotipo_counts.get(neurotipo, 0) + 1
            
            for neurotipo, count in neurotipo_counts.items():
                profiles_summary += f"- **{neurotipo}**: {count} estudiante(s)\n"
            
            profiles_summary += "\n✅ *Los agentes de IA considerarán automáticamente todos estos perfiles para crear adaptaciones personalizadas.*"
            
            self.console.print(Markdown(profiles_summary))
            
        except Exception as e:
            self.console.print(f"❌ [red]Error cargando perfiles: {str(e)}[/red]")
    
    def design_activity(self, user_request: str) -> str:
        """Diseña la actividad usando los agentes de IA"""
        self.console.print("\n" + "="*60)
        self.console.print("🤖 [bold cyan]PASO 3: Los agentes están trabajando...[/bold cyan]")
        self.console.print("="*60)
        
        with self.console.status("🔍 Analizando solicitud y perfiles de estudiantes...", spinner="dots"):
            try:
                result = self.crew.design_activity(user_request)
                # Si result es un objeto CrewOutput, extraer el texto
                if hasattr(result, 'raw'):
                    return result.raw
                else:
                    return str(result)
            except Exception as e:
                self.console.print(f"❌ [red]Error durante el diseño: {str(e)}[/red]")
                return None
    
    def show_activity_result(self, activity_design: str):
        """Muestra el resultado de la actividad diseñada"""
        self.console.print("\n" + "="*60)
        self.console.print("🎉 [bold green]PASO 4: ¡Tu actividad está lista![/bold green]")
        self.console.print("="*60)
        
        # Mostrar la actividad en un panel
        self.console.print(Panel(
            activity_design,
            title="📋 Actividad Diseñada",
            border_style="green",
            padding=(1, 2)
        ))
    
    def get_feedback(self) -> Optional[str]:
        """Obtiene feedback del profesor para refinamiento"""
        self.console.print("\n" + "="*60)
        self.console.print("💬 [bold cyan]PASO 5: Human-in-the-loop - Tu feedback[/bold cyan]")
        self.console.print("="*60)
        
        satisfied = Confirm.ask("¿Estás satisfecho/a con esta actividad?")
        
        if satisfied:
            self.console.print("✅ [green]¡Perfecto! La actividad está completada.[/green]")
            return None
        
        feedback_examples = """
💡 **Ejemplos de feedback:**
- "No entiendo la tarea de la fase 2"
- "Necesito más tiempo para la actividad completa"
- "La adaptación para TDAH no me parece clara"
- "Prefiero grupos de 3 en lugar de parejas"
- "Falta material manipulativo para matemáticas"
"""
        
        self.console.print(Markdown(feedback_examples))
        
        feedback = Prompt.ask(
            "[bold yellow]🔧 ¿Qué te gustaría cambiar o mejorar?[/bold yellow]"
        )
        
        return feedback
    
    def refine_activity(self, activity_design: str, feedback: str) -> str:
        """Refina la actividad basándose en el feedback"""
        self.console.print("\n🔄 [yellow]Refinando la actividad basándose en tu feedback...[/yellow]")
        
        with self.console.status("🛠️ El agente de refinamiento está trabajando...", spinner="dots"):
            try:
                refined_result = self.crew.refine_activity(activity_design, feedback)
                # Si result es un objeto CrewOutput, extraer el texto
                if hasattr(refined_result, 'raw'):
                    return refined_result.raw
                else:
                    return str(refined_result)
            except Exception as e:
                self.console.print(f"❌ [red]Error durante el refinamiento: {str(e)}[/red]")
                return activity_design  # Devolver la versión original si hay error
    
    def save_activity(self, activity_design: str, user_request: str):
        """Guarda la actividad final"""
        save = Confirm.ask("\n💾 ¿Quieres guardar esta actividad en un archivo?")
        
        if save:
            # Crear directorio de salida si no existe
            os.makedirs("output", exist_ok=True)
            
            # Generar nombre de archivo basado en la solicitud
            import re
            filename = re.sub(r'[^\w\s-]', '', user_request.lower())
            filename = re.sub(r'[-\s]+', '_', filename)[:50]
            filename = f"output/actividad_{filename}.md"
            
            try:
                import datetime
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# Actividad Generada por IA4EDU\n\n")
                    f.write(f"**Solicitud original:** {user_request}\n\n")
                    f.write(f"**Fecha:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(activity_design)
                
                self.console.print(f"✅ [green]Actividad guardada en: {filename}[/green]")
            except Exception as e:
                self.console.print(f"❌ [red]Error guardando archivo: {str(e)}[/red]")
    
    def run_interactive_session(self):
        """Ejecuta una sesión interactiva completa"""
        # Pantalla de bienvenida
        self.show_welcome()
        
        # Obtener solicitud del usuario
        user_request = self.get_user_request()
        
        # Mostrar perfiles de estudiantes
        self.show_student_profiles()
        
        # Diseñar actividad
        activity_design = self.design_activity(user_request)
        
        if not activity_design:
            self.console.print("❌ [red]Error: No se pudo generar la actividad[/red]")
            return
        
        # Ciclo de refinamiento human-in-the-loop
        while True:
            # Mostrar resultado
            self.show_activity_result(activity_design)
            
            # Obtener feedback
            feedback = self.get_feedback()
            
            # Si no hay feedback, terminar
            if not feedback:
                break
            
            # Refinar actividad
            activity_design = self.refine_activity(activity_design, feedback)
        
        # Guardar actividad final
        self.save_activity(activity_design, user_request)
        
        # Mensaje final
        self.console.print("\n🎉 [bold green]¡Gracias por usar IA4EDU![/bold green]")
        self.console.print("📚 [cyan]Tu actividad inclusiva está lista para implementar.[/cyan]")

@app.command()
def main():
    """🎓 Iniciar el asistente interactivo de IA4EDU"""
    try:
        interface = IA4EDUInterface()
        interface.run_interactive_session()
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]¡Hasta pronto![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ [red]Error inesperado: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    app()