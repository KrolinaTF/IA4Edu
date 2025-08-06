#!/usr/bin/env python3
"""
Configuración del Sistema de Agentes Inteligente
- Variables de entorno para Ollama
- Configuración de modelos LLM
- Logging
"""

import os
import logging
from typing import Dict

# ================================================================================
# CONFIGURACIÓN CRÍTICA DE OLLAMA + CREWAI (DEBE IR ANTES DE LOS IMPORTS)
# ================================================================================

def configure_environment(ollama_host: str = "192.168.1.10"):
    """Configura variables de entorno para evitar errores con CrewAI"""
    
    os.environ["OLLAMA_BASE_URL"] = f"http://{ollama_host}:11434"
    os.environ["OLLAMA_HOST"] = f"http://{ollama_host}:11434"  
    os.environ["OLLAMA_API_BASE"] = f"http://{ollama_host}:11434"
    os.environ["LITELLM_LOG"] = "DEBUG"
    os.environ["LITELLM_PROVIDER"] = "ollama"  # CRÍTICO: Definir provider
    os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder requerido
    os.environ["OPENAI_MODEL_NAME"] = "ollama/qwen3:latest"  # Con prefijo
    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
    os.environ["HTTPX_TIMEOUT"] = "120"

def setup_logging():
    """Configura logging para el sistema"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("AgentesInteligente")

# Configuración de modelos por defecto
DEFAULT_MODELS = {
    "detector": "qwen3:latest",
    "clima": "qwen3:latest", 
    "estructurador": "qwen2:latest",
    "tareas": "mistral:latest",
    "repartidor": "qwen3:latest",
    "validador": "qwen2:latest",
    "paralelismo": "qwen2:latest"
}

# Configuración de archivos k_ por defecto
DEFAULT_K_FILES = [
    "actividades_generadas/k_celula.txt",
    "actividades_generadas/k_feria_acertijos.txt", 
    "actividades_generadas/k_sonnet_supermercado.txt",
    "actividades_generadas/k_sonnet7_fabrica_fracciones.txt",
    "actividades_generadas/k_piratas.txt"
]

def validate_dependencies():
    """Valida que las dependencias necesarias estén disponibles"""
    try:
        from crewai import Agent, Task, Crew, Process
        from langchain_community.llms import Ollama
        import litellm
        
        logger = logging.getLogger("AgentesInteligente")
        logger.info("✅ CrewAI y dependencias importadas correctamente")
        return True
        
    except ImportError as e:
        logger = logging.getLogger("AgentesInteligente")
        logger.error(f"❌ Error importando dependencias: {e}")
        logger.error("💡 Instala: pip install crewai langchain-community")
        raise ImportError("Dependencias de CrewAI no disponibles")

def create_llm_config(ollama_host: str, models: Dict[str, str] = None) -> Dict[str, str]:
    """Crea configuración de LLMs para todos los agentes"""
    
    if models is None:
        models = DEFAULT_MODELS.copy()
    
    # Configurar LiteLLM para cada modelo
    try:
        import litellm
        
        for modelo in models.values():
            litellm.model_cost[f"ollama/{modelo}"] = {
                "input_cost_per_token": 0,
                "output_cost_per_token": 0,
                "max_tokens": 4096
            }
    except ImportError:
        pass  # LiteLLM es opcional
    
    return {
        agent_name: f"ollama/{model_name}"
        for agent_name, model_name in models.items()
    }