#!/usr/bin/env python3
"""
Script de prueba para el Sistema de Agentes Inteligente modular
"""

import sys
import os

# Añadir ruta del PoC para acceder a ejemplos k_
sys.path.append(os.path.join(os.path.dirname(__file__), '../PoC/PoC_entrenamiento_llm'))

def test_imports():
    """Prueba que todos los imports funcionen correctamente"""
    
    print("🧪 Probando imports del sistema modular...")
    
    try:
        from intelligent_agents import SistemaAgentesInteligente, ActividadEducativa
        from intelligent_agents.config import configure_environment, validate_dependencies
        from intelligent_agents.services import CargadorEjemplosK
        from intelligent_agents.agents_and_tasks import AgentesCrewAI
        
        print("✅ Todos los imports principales funcionan")
        return True
        
    except ImportError as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_basic_functionality():
    """Prueba funcionalidad básica sin llamadas a LLM"""
    
    print("🧪 Probando funcionalidad básica...")
    
    try:
        # Cambiar al directorio del PoC para encontrar ejemplos k_
        os.chdir('../PoC/PoC_entrenamiento_llm')
        
        from intelligent_agents.services import CargadorEjemplosK
        
        # Probar carga de ejemplos k_
        cargador = CargadorEjemplosK(".")
        print(f"✅ Ejemplos k_ cargados: {len(cargador.ejemplos_k)}")
        print(f"   Ejemplos disponibles: {list(cargador.ejemplos_k.keys())}")
        
        # Probar selección estratégica
        ejemplo = cargador.seleccionar_ejemplo_estrategico("matematicas", "fracciones", "grupal")
        print(f"✅ Selección estratégica funciona: {len(ejemplo)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad básica: {e}")
        return False

def test_system_initialization():
    """Prueba inicialización del sistema completo"""
    
    print("🧪 Probando inicialización del sistema...")
    
    try:
        # Configurar entorno
        from intelligent_agents.config import configure_environment
        configure_environment("192.168.1.10")
        print("✅ Entorno configurado")
        
        # NO inicializar el sistema completo para evitar conexiones a Ollama
        # solo verificar que la clase esté disponible
        from intelligent_agents import SistemaAgentesInteligente
        print("✅ Clase SistemaAgentesInteligente disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    
    print("🚀 Iniciando pruebas del sistema modular")
    print("="*50)
    
    pruebas_exitosas = 0
    pruebas_totales = 3
    
    # Prueba 1: Imports
    if test_imports():
        pruebas_exitosas += 1
    
    print()
    
    # Prueba 2: Funcionalidad básica
    if test_basic_functionality():
        pruebas_exitosas += 1
    
    print()
    
    # Prueba 3: Inicialización
    if test_system_initialization():
        pruebas_exitosas += 1
    
    print()
    print("="*50)
    print(f"📊 Resultado: {pruebas_exitosas}/{pruebas_totales} pruebas exitosas")
    
    if pruebas_exitosas == pruebas_totales:
        print("🎉 ¡Todas las pruebas pasaron! El sistema modular está listo.")
        print("💡 Para probar con Ollama, ejecuta: python -m intelligent_agents.main")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return pruebas_exitosas == pruebas_totales

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)