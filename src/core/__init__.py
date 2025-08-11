"""
Módulo Core - Componentes centrales del sistema
"""

from .contexto import ContextoHibrido
from .comunicador import ComunicadorAgentes
from .ollama_integrator import OllamaIntegrator

__all__ = [
    'ContextoHibrido',
    'ComunicadorAgentes', 
    'OllamaIntegrator'
]