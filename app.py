import streamlit as st
import json
from pathlib import Path
from agents.crew_agents import IA4EDUCrew
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv('LLM_API_KEY') or os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    st.error("⚠️ No se ha configurado la API key de Gemini. Por favor, configura LLM_API_KEY o GEMINI_API_KEY en el archivo .env")

st.set_page_config(
    page_title="IA4EDU - Asistente de Actividades Inclusivas",
    page_icon="🎓",
    layout="wide"
)

@st.cache_data
def load_student_profiles():
    with open("data/perfiles_4_primaria.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get('estudiantes', [])

def save_markdown_activity(content: str, output_dir: str = "output") -> str:
    """Guarda una actividad en formato Markdown."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"actividad_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(filename)

def main():
    st.title("🎓 IA4EDU - Asistente de Actividades Inclusivas")
    st.markdown("Sistema de IA para crear actividades educativas adaptadas a la neurodiversidad")
    
    profiles = load_student_profiles()
    
    # Initialize session state
    if 'activity_history' not in st.session_state:
        st.session_state.activity_history = []
    if 'current_version' not in st.session_state:
        st.session_state.current_version = -1
    
    with st.sidebar:
        st.header("📚 Información del Sistema")
        st.markdown("""
        Este asistente te ayudará a crear actividades educativas inclusivas para aulas neurodiversas.
        
        **Perfiles disponibles:**
        """)
        for profile in profiles:
            st.markdown(f"- {profile['nombre']} ({profile.get('diagnostico_formal', 'N/A')})")
        
        st.markdown("---")
        st.markdown("### 🔧 Configuración")
        show_debug = st.checkbox("Mostrar información de depuración", value=False)
        
        # History controls if there are activities
        if st.session_state.activity_history:
            st.markdown("---")
            st.markdown("### 📜 Historial de Versiones")
            st.write(f"Versiones disponibles: {len(st.session_state.activity_history)}")
            
            if st.button("🗑️ Limpiar historial y empezar de cero"):
                st.session_state.activity_history = []
                st.session_state.current_version = -1
                st.session_state.pop('refine_mode', None)
                st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["🆕 Nueva Actividad", "📄 Actividades Guardadas", "👥 Perfiles de Estudiantes"])
    
    with tab1:
        # Show version selector if there are multiple versions
        if len(st.session_state.activity_history) > 1:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                version_idx = st.selectbox(
                    "📌 Ver versión:",
                    range(len(st.session_state.activity_history)),
                    format_func=lambda x: f"Versión {x+1} - {'Original' if x == 0 else f'Refinamiento {x}'}",
                    index=st.session_state.current_version if st.session_state.current_version >= 0 else len(st.session_state.activity_history)-1
                )
                st.session_state.current_version = version_idx
            with col2:
                if st.button("⬅️ Volver a esta versión"):
                    # Keep only versions up to the selected one
                    st.session_state.activity_history = st.session_state.activity_history[:version_idx+1]
                    st.session_state.current_version = version_idx
                    st.success(f"Volviste a la versión {version_idx+1}")
                    st.rerun()
            with col3:
                if st.button("🔄 Comparar versiones"):
                    st.session_state['compare_mode'] = True
                    st.rerun()
        
        # Comparison mode
        if st.session_state.get('compare_mode', False) and len(st.session_state.activity_history) > 1:
            st.header("📊 Comparación de Versiones")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Versión Original")
                with st.container():
                    st.markdown(st.session_state.activity_history[0])
            
            with col2:
                st.subheader(f"Versión {len(st.session_state.activity_history)} (Última)")
                with st.container():
                    st.markdown(st.session_state.activity_history[-1])
            
            if st.button("❌ Cerrar comparación"):
                st.session_state['compare_mode'] = False
                st.rerun()
        
        # Normal mode - show current activity or creation form
        elif st.session_state.activity_history and not st.session_state.get('create_new', False):
            # Display current version
            current_activity = st.session_state.activity_history[st.session_state.current_version]
            
            st.header(f"📝 Actividad - Versión {st.session_state.current_version + 1}")
            
            # Activity display
            with st.container():
                st.markdown(current_activity)
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("💾 Guardar esta versión"):
                    filename = save_markdown_activity(current_activity, "output")
                    st.success(f"Actividad guardada en: {filename}")
            
            with col2:
                if st.button("✏️ Refinar actividad"):
                    st.session_state['refine_mode'] = True
                    st.rerun()
            
            with col3:
                if st.button("🆕 Crear nueva actividad"):
                    st.session_state['create_new'] = True
                    st.rerun()
            
            with col4:
                if show_debug:
                    with st.expander("🔍 Debug (Markdown)"):
                        st.code(current_activity, language="markdown")
            
            # Refinement interface
            if st.session_state.get('refine_mode', False):
                st.markdown("---")
                st.header("🔄 Refinar Actividad")
                
                st.info("💡 La actividad actual se mantendrá. El refinamiento creará una nueva versión que podrás comparar con la original.")
                
                feedback = st.text_area(
                    "¿Qué aspectos te gustaría mejorar?",
                    placeholder="Por ejemplo: Añadir más trabajo en grupo, simplificar instrucciones para TEA, aumentar el desafío para altas capacidades...",
                    height=100
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Aplicar Mejoras", type="primary", disabled=not feedback):
                        with st.spinner("Refinando actividad..."):
                            try:
                                crew = IA4EDUCrew(GEMINI_API_KEY)
                                refined_result = crew.refine_activity(
                                    current_activity,
                                    feedback
                                )
                                # Convert CrewOutput to string
                                refined_result_str = str(refined_result)
                                
                                # Add refined version to history
                                st.session_state.activity_history.append(refined_result_str)
                                st.session_state.current_version = len(st.session_state.activity_history) - 1
                                st.session_state['refine_mode'] = False
                                st.success("✅ Actividad refinada exitosamente - Nueva versión creada")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al refinar: {str(e)}")
                
                with col2:
                    if st.button("❌ Cancelar refinamiento"):
                        st.session_state['refine_mode'] = False
                        st.rerun()
        
        # Creation form
        else:
            st.header("Crear Nueva Actividad")
            
            if st.session_state.get('create_new', False) and st.session_state.activity_history:
                if st.button("⬅️ Volver a la actividad anterior"):
                    st.session_state['create_new'] = False
                    st.rerun()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                request = st.text_area(
                    "Describe la actividad que quieres crear:",
                    placeholder="Ejemplo: Quiero crear una actividad de matemáticas sobre fracciones para 4º de primaria...",
                    height=150
                )
                
                if st.button("🚀 Generar Actividad", type="primary", disabled=not request):
                    with st.spinner("Generando actividad inclusiva..."):
                        try:
                            crew = IA4EDUCrew(GEMINI_API_KEY)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            status_text.text("Analizando solicitud...")
                            progress_bar.progress(25)
                            
                            result = crew.design_activity(request)
                            
                            status_text.text("Diseñando adaptaciones...")
                            progress_bar.progress(75)
                            
                            if result:
                                status_text.text("¡Actividad generada con éxito!")
                                progress_bar.progress(100)
                                
                                # Convert CrewOutput to string
                                result_str = str(result)
                                
                                # Store in history
                                st.session_state.activity_history = [result_str]
                                st.session_state.current_version = 0
                                st.session_state['create_new'] = False
                                st.success("✅ Actividad generada exitosamente")
                                st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error al generar la actividad: {str(e)}")
                            if show_debug:
                                st.exception(e)
            
            with col2:
                st.info("""
                **💡 Consejos para mejores resultados:**
                - Especifica la materia y el tema
                - Indica el nivel educativo
                - Menciona objetivos específicos
                - Describe el contexto si es relevante
                """)
    
    with tab2:
        st.header("Actividades Guardadas")
        
        output_path = Path("output")
        if output_path.exists():
            activities = list(output_path.glob("*.md"))
            
            if activities:
                selected_activity = st.selectbox(
                    "Selecciona una actividad:",
                    activities,
                    format_func=lambda x: x.stem.replace("_", " ").title()
                )
                
                if selected_activity:
                    with open(selected_activity, "r", encoding="utf-8") as f:
                        content = f.read()
                        st.markdown(content)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Cargar para refinar"):
                            st.session_state.activity_history = [content]
                            st.session_state.current_version = 0
                            st.session_state['create_new'] = False
                            st.success("Actividad cargada - Ve a la pestaña 'Nueva Actividad' para refinarla")
                    
                    with col2:
                        if st.button("🗑️ Eliminar Actividad"):
                            selected_activity.unlink()
                            st.success("Actividad eliminada")
                            st.rerun()
            else:
                st.info("No hay actividades guardadas aún.")
        else:
            st.info("No hay actividades guardadas aún.")
    
    with tab3:
        st.header("Perfiles de Estudiantes")
        
        for i, profile in enumerate(profiles):
            with st.expander(f"{profile['nombre']} - {profile.get('diagnostico_formal', 'N/A')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Información General:**")
                    st.write(f"- **ID:** {profile.get('id', 'N/A')}")
                    st.write(f"- **Diagnóstico:** {profile.get('diagnostico_formal', 'N/A')}")
                    st.write(f"- **Nivel de apoyo:** {profile.get('nivel_apoyo', 'N/A')}")
                    st.write(f"- **Estilo de aprendizaje:** {', '.join(profile.get('estilo_aprendizaje', []))}")
                    st.write(f"- **Canal preferido:** {profile.get('canal_preferido', 'N/A')}")
                
                with col2:
                    st.markdown("**Características:**")
                    st.write(f"- **Temperamento:** {profile.get('temperamento', 'N/A')}")
                    st.write(f"- **Tolerancia a la frustración:** {profile.get('tolerancia_frustracion', 'N/A')}")
                    st.write(f"- **Intereses:** {', '.join(profile.get('intereses', []))}")
                
                st.markdown("**Competencias por materia:**")
                # Recopilar todas las competencias de diferentes materias
                competencias = {}
                if 'matematicas' in profile:
                    for k, v in profile['matematicas'].items():
                        competencias[f'Mat: {k}'] = v
                if 'lengua' in profile:
                    for k, v in profile['lengua'].items():
                        competencias[f'Len: {k}'] = v
                if 'ciencias' in profile:
                    for k, v in profile['ciencias'].items():
                        competencias[f'Cie: {k}'] = v
                
                if competencias:
                    cols = st.columns(min(4, len(competencias)))
                    for j, (subject, level) in enumerate(competencias.items()):
                        cols[j % len(cols)].write(f"**{subject}:** {level}")

if __name__ == "__main__":
    main()