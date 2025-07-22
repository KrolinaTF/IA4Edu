#!/usr/bin/env python3
"""
Script de prueba simple para verificar que el generador funciona sin problemas JSON
"""

from generador_actividades_main import GeneradorActividadesEducativas

def test_actividad_simple():
    """Prueba simple de generación de actividad"""
    try:
        # Inicializar generador
        print("Inicializando generador...")
        generador = GeneradorActividadesEducativas()
        
        # Generar una actividad simple
        print("Generando actividad para estudiante 001...")
        resultado = generador.generar_actividad_individual("001", "Matemáticas")
        
        if resultado.get("success"):
            print("OK Actividad generada exitosamente")
            print(f"Estudiante: {resultado['metadatos']['estudiante']['nombre']}")
            print(f"Tema: {resultado['metadatos']['actividad']['tema']}")
            print(f"Actividad: {resultado['actividad'][:200]}...")
        else:
            print(f"ERROR: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_actividad_simple()