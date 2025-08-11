#!/usr/bin/env python3
"""
Punto de entrada principal para el Sistema de Agentes ABP.
Inicializa componentes y ejecuta el flujo completo.
"""

import logging
import os
import sys

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("SistemaAgentesABP")

# Asegurar que podamos importar módulos desde el directorio actual
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes principales
from core.ollama_integrator import OllamaIntegrator
from agents.coordinador import AgenteCoordinador
from agents.analizador import AgenteAnalizadorTareas
from agents.perfilador import AgentePerfiladorEstudiantes
from agents.optimizador import AgenteOptimizadorAsignaciones
# from agents.generador import AgenteGeneradorRecursos  # ELIMINADO Fase 1
from core.sistema import SistemaAgentesABP
from ui.controller import UIController
from ui.cli import CLI

def main():
    """Función principal que inicializa y ejecuta el sistema"""
    try:
        logger.info("🚀 Iniciando Sistema de Agentes ABP")
        
        # Inicializar integrador Ollama
        ollama_config = {
            "host": "192.168.1.10",
            "port": 11434,
            "model": "llama3.2",
            "embedding_model": "nomic-embed-text"
        }
        ollama_integrator = OllamaIntegrator(**ollama_config)
        
        # Inicializar agentes (Fase 2 - Solo 3 agentes esenciales)
        analizador = AgenteAnalizadorTareas(ollama_integrator)
        perfilador = AgentePerfiladorEstudiantes(ollama_integrator)
        optimizador = AgenteOptimizadorAsignaciones(ollama_integrator)
        # generador eliminado en Fase 1
        
        # Inicializar coordinador con agentes
        coordinador = AgenteCoordinador(
            ollama_integrator=ollama_integrator,
            analizador_tareas=analizador,
            perfilador=perfilador,
            optimizador=optimizador
            # generador_recursos eliminado
        )
        
        # Inicializar sistema
        sistema = SistemaAgentesABP(coordinador=coordinador)
        
        # Inicializar controlador de UI y CLI
        controller = UIController(coordinador=coordinador, sistema=sistema)
        cli = CLI(controller)
        
        # Ejecutar CLI
        proyecto_final = cli.ejecutar()
        
        logger.info("✅ Proceso completado exitosamente")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Proceso interrumpido por el usuario")
        return 1
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())