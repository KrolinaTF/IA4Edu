#!/usr/bin/env python3
"""
Script Principal del Sistema Cuántico de Agentes Inteligentes
Punto de entrada principal para el sistema integrado PennyLane + CrewAI
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainQuantumSystem")

def verificar_dependencias():
    """Verifica que todas las dependencias estén disponibles"""
    dependencias_faltantes = []
    
    try:
        import pennylane as qml
        logger.info("✅ PennyLane disponible")
    except ImportError:
        dependencias_faltantes.append("pennylane")
    
    try:
        import numpy as np
        logger.info("✅ NumPy disponible")
    except ImportError:
        dependencias_faltantes.append("numpy")
    
    try:
        from crewai import Agent, Task, Crew
        logger.info("✅ CrewAI disponible")
    except ImportError:
        dependencias_faltantes.append("crewai")
    
    try:
        from langchain_community.llms import Ollama
        logger.info("✅ LangChain Community disponible")
    except ImportError:
        dependencias_faltantes.append("langchain-community")
    
    if dependencias_faltantes:
        print("❌ DEPENDENCIAS FALTANTES:")
        for dep in dependencias_faltantes:
            print(f"   - {dep}")
        print("\n💡 Instala las dependencias faltantes:")
        print("   pip install pennylane numpy crewai langchain-community")
        return False
    
    return True

def verificar_ollama():
    """Verifica que Ollama esté disponible"""
    try:
        import requests
        response = requests.get("http://192.168.1.10:11434/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Ollama disponible en 192.168.1.10:11434")
            return True
        else:
            logger.warning(f"⚠️ Ollama responde pero con código {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ollama no disponible: {e}")
        print("💡 Verifica que Ollama esté ejecutándose en 192.168.1.10:11434")
        return False

def mostrar_menu_principal():
    """Muestra el menú principal del sistema"""
    print("\n" + "="*70)
    print("⚛️  SISTEMA CUÁNTICO DE AGENTES INTELIGENTES")
    print("="*70)
    print("🔬 PennyLane + CrewAI + Ollama + Few-shot estratégico")
    print()
    print("OPCIONES DISPONIBLES:")
    print("1. 🌟 Generar Actividad con Optimización Cuántica")
    print("2. 🧪 Probar Solo el Optimizador Cuántico")
    print("3. 🤖 Probar Solo los Agentes (sin cuántica)")
    print("4. 📊 Ejecutar Tests del Sistema")
    print("5. ❓ Mostrar Información del Sistema")
    print("0. 🚪 Salir")
    print()

def ejecutar_sistema_completo():
    """Ejecuta el sistema completo con optimización cuántica"""
    try:
        from quantum_intelligent_agents import main
        print("\n🌟 Iniciando sistema completo con optimización cuántica...")
        main()
    except Exception as e:
        logger.error(f"Error ejecutando sistema completo: {e}")
        print(f"❌ Error: {e}")

def probar_solo_cuantica():
    """Prueba solo el optimizador cuántico"""
    try:
        from quantum_educational_optimizer import test_quantum_optimizer
        print("\n🧪 Probando solo el optimizador cuántico...")
        success = test_quantum_optimizer()
        if success:
            print("✅ Optimizador cuántico funcionando correctamente")
        else:
            print("❌ Problemas con el optimizador cuántico")
    except Exception as e:
        logger.error(f"Error probando cuántica: {e}")
        print(f"❌ Error: {e}")

def probar_solo_agentes():
    """Prueba solo los agentes sin cuántica"""
    try:
        # Importar y usar el sistema original de agentes
        print("\n🤖 Probando solo los agentes (sin optimización cuántica)...")
        print("💡 Esta funcionalidad requiere el sistema original de agentes")
        print("📝 Puedes usar ../sistema_agentes_inteligente.py para esto")
    except Exception as e:
        logger.error(f"Error probando agentes: {e}")
        print(f"❌ Error: {e}")

def ejecutar_tests():
    """Ejecuta todos los tests del sistema"""
    print("\n📊 Ejecutando tests del sistema...")
    
    # Test 1: Optimizador Cuántico
    print("\n🧪 TEST 1: Optimizador Cuántico")
    try:
        from quantum_educational_optimizer import test_quantum_optimizer
        if test_quantum_optimizer():
            print("✅ Test cuántico: PASADO")
        else:
            print("❌ Test cuántico: FALLADO")
    except Exception as e:
        print(f"❌ Test cuántico: ERROR - {e}")
    
    # Test 2: Conexión Ollama
    print("\n🔗 TEST 2: Conexión Ollama")
    if verificar_ollama():
        print("✅ Test Ollama: PASADO")
    else:
        print("❌ Test Ollama: FALLADO")
    
    # Test 3: Imports de Agentes
    print("\n🤖 TEST 3: Imports de Agentes")
    try:
        from quantum_intelligent_agents import QuantumIntelligentAgentsSystem
        sistema = QuantumIntelligentAgentsSystem()
        print("✅ Test agentes: PASADO")
    except Exception as e:
        print(f"❌ Test agentes: ERROR - {e}")
    
    print("\n📊 Tests completados")

def mostrar_info_sistema():
    """Muestra información detallada del sistema"""
    print("\n" + "="*70)
    print("📊 INFORMACIÓN DEL SISTEMA")
    print("="*70)
    
    print("\n🏗️ ARQUITECTURA:")
    print("   - quantum_educational_optimizer.py: Optimización cuántica con PennyLane")
    print("   - quantum_intelligent_agents.py: Sistema de agentes con integración cuántica")
    print("   - main_quantum_system.py: Script principal (este archivo)")
    
    print("\n🔬 COMPONENTES CUÁNTICOS:")
    print("   - 16 qubits para codificación de parámetros educativos")
    print("   - Hamiltoniano educativo para optimización")
    print("   - Entrelazamiento cuántico para interdependencias pedagógicas")
    
    print("\n🤖 AGENTES INTEGRADOS:")
    print("   - Detector de Contexto Pedagógico Cuántico")
    print("   - Especialista en Clima Pedagógico Cuántico") 
    print("   - Arquitecto de Experiencias Educativas Cuánticas")
    print("   - Especialista en Desglose Pedagógico Cuántico")
    print("   - Especialista en Inclusión y Adaptación Cuántica")
    print("   - Validador de Calidad Pedagógica Cuántica")
    
    print("\n⚙️ DEPENDENCIAS:")
    print("   - PennyLane: Computación cuántica")
    print("   - CrewAI: Sistema de agentes")
    print("   - Ollama: Modelos de lenguaje locales")
    print("   - LangChain: Integración con LLMs")
    
    print("\n🎯 ADAPTACIONES AUTOMÁTICAS:")
    print("   - TEA: Estructuración optimizada cuánticamente")
    print("   - TDAH: Balance energía-estructura cuántico")
    print("   - Altas Capacidades: Retos calibrados")
    
    print("\n🔍 ESTADO ACTUAL:")
    verificar_dependencias()
    verificar_ollama()

def main():
    """Función principal del sistema"""
    print("🚀 Iniciando Sistema Cuántico de Agentes Inteligentes...")
    
    # Verificaciones iniciales
    if not verificar_dependencias():
        return
    
    # Bucle principal
    while True:
        mostrar_menu_principal()
        
        try:
            opcion = input("🔢 Selecciona una opción (0-5): ").strip()
            
            if opcion == "0":
                print("\n👋 ¡Hasta luego! Gracias por usar el sistema cuántico.")
                break
            elif opcion == "1":
                ejecutar_sistema_completo()
            elif opcion == "2":
                probar_solo_cuantica()
            elif opcion == "3":
                probar_solo_agentes()
            elif opcion == "4":
                ejecutar_tests()
            elif opcion == "5":
                mostrar_info_sistema()
            else:
                print("⚠️ Opción no válida. Por favor, elige entre 0-5.")
            
            # Pausa antes de volver al menú
            if opcion != "0":
                input("\n⏸️ Presiona Enter para continuar...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Saliendo del sistema...")
            break
        except Exception as e:
            logger.error(f"Error en menú principal: {e}")
            print(f"❌ Error inesperado: {e}")
            input("\n⏸️ Presiona Enter para continuar...")

if __name__ == "__main__":
    main()