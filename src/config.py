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

# === CONFIGURACIÓN OLLAMA CENTRALIZADA ===
OLLAMA_CONFIG = {
    "host": "192.168.1.10",
    "port": 11434,
    "model": "mistral",  # PUNTO ÚNICO para cambiar modelo
    "embedding_model": "nomic-embed-text",
    "timeout": 60
}

# Configuración de agentes
AGENTS_CONFIG = {
    "max_iteraciones": 3,
    "validacion_automatica": True,
    "reintentos_por_agente": 2,
    "timeout_por_agente": 60
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
}



# === FUNCIONES NECESARIAS ===

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