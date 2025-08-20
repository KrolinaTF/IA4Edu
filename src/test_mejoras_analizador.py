#!/usr/bin/env python3
"""
Script de prueba para las mejoras del AgenteAnalizadorTareas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.analizador import AgenteAnalizadorTareas
from core.ollama_integrator import OllamaIntegrator
from config import OLLAMA_CONFIG

def test_detector_tipos():
    """Prueba el detector de tipos de actividad"""
    print("🔍 PROBANDO DETECTOR DE TIPOS DE ACTIVIDAD")
    print("=" * 50)
    
    # Crear analizador (sin necesidad de conectar a Ollama para esta prueba)
    analizador = AgenteAnalizadorTareas(None)
    
    prompts_prueba = [
        "crear una gymnkana con diferentes puestos para matemáticas",
        "hacer un proyecto de construcción de un robot",
        "organizar un taller de ciencias con experimentos",
        "investigar sobre el sistema solar",
        "presentar los resultados del trabajo en equipo"
    ]
    
    for prompt in prompts_prueba:
        resultado = analizador._detectar_tipo_actividad(prompt)
        print(f"\n📝 Prompt: {prompt}")
        print(f"   🎯 Tipo: {resultado['tipo']}")
        print(f"   📊 Confianza: {resultado['confianza']:.2f}")
        print(f"   🔑 Palabras clave: {resultado['palabras_clave']}")

def test_extractor_elementos():
    """Prueba el extractor de elementos reutilizables"""
    print("\n\n🔧 PROBANDO EXTRACTOR DE ELEMENTOS REUTILIZABLES")
    print("=" * 50)
    
    analizador = AgenteAnalizadorTareas(None)
    
    # Actividades de ejemplo
    actividades_ejemplo = [
        {
            'titulo': 'Feria de Fracciones',
            'objetivo': 'Aprender fracciones mediante juegos',
            'etapas': [
                {
                    'nombre': 'Preparación',
                    'tareas': [
                        {'nombre': 'Puesto 1: Pizza de fracciones', 'descripcion': 'Dividir pizzas en fracciones'},
                        {'nombre': 'Puesto 2: Carrera de fracciones', 'descripcion': 'Competir ordenando fracciones'}
                    ]
                }
            ],
            'recursos': 'Materiales: cartón, tijeras, rotuladores. Necesario: calculadoras básicas.',
            'competencias': 'matemáticas, trabajo colaborativo'
        },
        {
            'titulo': 'Laboratorio de Células',
            'objetivo': 'Explorar la estructura celular',
            'etapas': [
                {
                    'nombre': 'Experimentación',
                    'tareas': [
                        {'nombre': 'Estación 1: Microscopio', 'descripcion': 'Observar células al microscopio'},
                        {'nombre': 'Estación 2: Modelos 3D', 'descripcion': 'Construir modelos de células'}
                    ]
                }
            ],
            'observaciones': 'Para TEA: proporcionar rutina clara. Para TDAH: permitir movimiento entre estaciones.'
        }
    ]
    
    elementos = analizador._extraer_elementos_reutilizables(actividades_ejemplo)
    
    for categoria, lista in elementos.items():
        if lista:
            print(f"\n📂 {categoria.upper()}:")
            for elemento in lista[:3]:  # Mostrar máximo 3 elementos
                print(f"   • {elemento}")

def test_analisis_completo():
    """Prueba el análisis completo (requiere conexión a Ollama)"""
    print("\n\n🎯 PROBANDO ANÁLISIS COMPLETO")
    print("=" * 50)
    
    try:
        # Intentar conectar a Ollama
        ollama = OllamaIntegrator(**OLLAMA_CONFIG)
        analizador = AgenteAnalizadorTareas(ollama)
        
        prompt_prueba = "crear una feria de matemáticas con diferentes puestos de fracciones"
        
        resultado = analizador.analizar_actividad_completa(prompt_prueba)
        
        print(f"📝 Prompt analizado: {prompt_prueba}")
        print(f"🎯 Tipo detectado: {resultado['tipo_detectado']['tipo']}")
        print(f"📊 Confianza: {resultado['tipo_detectado']['confianza']:.2f}")
        print(f"📋 Tareas extraídas: {resultado['num_tareas']}")
        print(f"🔧 Estrategia usada: {resultado['actividad_seleccionada']['estrategia']}")
        
        if 'elementos_reutilizables' in resultado:
            total_elementos = sum(len(v) for v in resultado['elementos_reutilizables'].values())
            print(f"🔗 Elementos reutilizables: {total_elementos} total")
        
    except Exception as e:
        print(f"❌ Error en análisis completo (probablemente Ollama no disponible): {e}")
        print("💡 Los métodos de detección y extracción funcionan independientemente de Ollama")

if __name__ == "__main__":
    print("🚀 PROBANDO MEJORAS DEL ANALIZADOR DE TAREAS")
    print("=" * 60)
    
    test_detector_tipos()
    test_extractor_elementos()
    test_analisis_completo()
    
    print("\n✅ PRUEBAS COMPLETADAS")