"""
Configuración centralizada para el Sistema de Agentes ABP.
Contiene constantes, ajustes y parámetros configurables.
"""

import os
import logging
from typing import Dict, Any

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
EXAMPLES_DIR = os.path.join(DATA_DIR, "actividades")

# Configuración de Ollama
OLLAMA_CONFIG = {
    "host": "192.168.1.10",
    "port": 11434,
    "model": "llama3.2"
}

# Configuración de agentes
AGENTS_CONFIG = {
    "max_iteraciones": 3,
    "validacion_automatica": True,
    "reintentos_por_agente": 2,
    "timeout_por_agente": 60
}

# Patrones para detección de metadatos
MATERIA_PATRONES = {
    'matematicas': ['matemáticas', 'fracciones', 'números', 'operaciones', 'mercado de las fracciones', 'cálculo', 'geometría'],
    'lengua': ['escritura', 'lectura', 'texto', 'poesía', 'gramática', 'ortografía', 'redacción'],
    'ciencias': ['experimento', 'laboratorio', 'célula', 'planeta', 'científico', 'naturaleza', 'física', 'química'],
    'geografia': ['geografía', 'mapa', 'comunidades', 'países', 'ciudades', 'regiones', 'españa', 'andalucía', 'cataluña', 'valencia', 'viajes', 'turismo', 'autonomas'],
    'historia': ['historia', 'época', 'siglos', 'acontecimientos', 'pasado'],
    'arte': ['arte', 'pintura', 'dibujo', 'creatividad', 'manualidades']
}

# Mapeo de ejemplos para contexto híbrido
EJEMPLOS_MAPEO = {
    'supermercado': 'sonnet_supermercado',
    'dinero': 'sonnet_supermercado', 
    'comercio': 'sonnet_supermercado',
    'fracciones': 'sonnet7_fabrica_fracciones',
    'fábrica': 'sonnet7_fabrica_fracciones',
    'ciencias': 'celula',
    'células': 'celula',
    'biología': 'celula',
    'piratas': 'piratas',
    'tesoro': 'piratas',
    'aventura': 'piratas',
    'geografia': None,
    'españa': None,
    'comunidades': None,
    'viajes': None
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
}

# Perfiles de estudiantes predeterminados
ESTUDIANTES_AULA_A_4PRIM = """
- 001 ALEX M.: reflexivo, visual, CI 102
- 002 MARÍA L.: reflexivo, auditivo
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118 - Necesita apoyo visual y rutinas
- 004 LUIS T.: impulsivo, kinestetico, TDAH combinado, CI 102 - Necesita movimiento
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141 - Necesita desafíos extra
- 006 SARA M.: equilibrado, auditivo, CI 115
- 007 EMMA K.: reflexivo, visual, CI 132
- 008 HUGO P.: equilibrado, visual, CI 114
"""

# Crear directorios si no existen
def ensure_directories():
    """Asegura que los directorios necesarios existan"""
    for directory in [DATA_DIR, TEMP_DIR, EXAMPLES_DIR]:
        os.makedirs(directory, exist_ok=True)

# Función para cargar configuración desde archivo (opcional)
def load_config(config_file: str = None) -> Dict[str, Any]:
    """
    Carga configuración desde un archivo externo (si existe)
    
    Args:
        config_file: Ruta al archivo de configuración
    
    Returns:
        Diccionario con la configuración
    """
    config = {
        'ollama': OLLAMA_CONFIG,
        'agents': AGENTS_CONFIG,
        'logging': LOGGING_CONFIG,
        'dirs': {
            'base': BASE_DIR,
            'data': DATA_DIR,
            'temp': TEMP_DIR,
            'examples': EXAMPLES_DIR
        }
    }
    
    # Si se proporciona un archivo de configuración y existe, sobrescribir configuración
    if config_file and os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Actualizar configuración con los valores del usuario
            # (implementación simplificada, se podría hacer más sofisticada)
            for key, value in user_config.items():
                if key in config and isinstance(value, dict) and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
                    
        except Exception as e:
            logging.error(f"Error cargando configuración desde {config_file}: {e}")
    
    return config