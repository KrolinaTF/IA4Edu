"""
Módulo de Utilidades
"""

from .json_parser import parse_json_seguro
from .logger import configurar_logging

__all__ = [
    'parse_json_seguro',
    'configurar_logging'
]