"""
Sistema de Agentes Inteligente con CrewAI + Ollama
- Few-shot estratégico con ejemplos k_
- Human-in-the-loop inteligente con análisis de contexto  
- Flujo de 4 fases con LLMs reales
- Detección automática de paralelismo
"""

from workflows import SistemaAgentesInteligente
from services import ActividadEducativa, CargadorEjemplosK, MotorParalelismo
from config import configure_environment, setup_logging, validate_dependencies

__version__ = "1.0.0"
__author__ = "IA4EDU Team"