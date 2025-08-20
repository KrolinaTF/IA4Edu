"""
MVP del Sistema ABP Simplificado.

Este módulo contiene una versión simplificada del sistema de agentes ABP
que elimina la complejidad innecesaria y se enfoca en generar actividades
específicas y útiles.

Componentes principales:
- SimplifiedCoordinator: Coordinador único que maneja toda la generación
- ProfileManager: Gestor simple de perfiles de estudiantes
- simple_cli: Interfaz de línea de comandos para pruebas
"""

from .simplified_coordinator import SimplifiedCoordinator
from .profile_manager import ProfileManager

__version__ = "1.0.0"
__author__ = "Sistema ABP Simplificado"

__all__ = [
    "SimplifiedCoordinator",
    "ProfileManager"
]