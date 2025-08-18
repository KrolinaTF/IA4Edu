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

# Importar configuración centralizada
from config import OLLAMA_CONFIG, ensure_directories

# Importar componentes principales
from core.ollama_integrator import OllamaIntegrator
from agents.coordinador import AgenteCoordinador
from agents.analizador import AgenteAnalizadorTareas
from agents.perfilador import AgentePerfiladorEstudiantes
from agents.optimizador import AgenteOptimizadorAsignaciones
from core.sistema import SistemaAgentesABP
from ui.controller import UIController
from ui.cli import CLI

def main():
    """Función principal que inicializa y ejecuta el sistema"""
    try:
        logger.info("🚀 Iniciando Sistema de Agentes ABP")
        
        # Asegurar directorios necesarios
        ensure_directories()
        
        # Usar configuración centralizada de Ollama
        logger.info(f"📡 Conectando a Ollama en {OLLAMA_CONFIG['host']}:{OLLAMA_CONFIG['port']} con modelo {OLLAMA_CONFIG['model']}")
        
        ollama_integrator = OllamaIntegrator(**OLLAMA_CONFIG)
        
        # Inicializar agentes
        analizador = AgenteAnalizadorTareas(ollama_integrator)
        perfilador = AgentePerfiladorEstudiantes(ollama_integrator)
        optimizador = AgenteOptimizadorAsignaciones(ollama_integrator)
        
        
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