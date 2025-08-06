#!/usr/bin/env python3
"""
Punto de entrada principal del Sistema de Agentes Inteligente
- CLI conversacional
- Manejo de errores
- Guardado de actividades
"""

import os
import json
import logging
from datetime import datetime

from workflows import SistemaAgentesInteligente

logger = logging.getLogger("AgentesInteligente")

def guardar_actividad(actividad, directorio_salida="actividades_inteligentes"):
    """Guarda la actividad generada en un archivo"""
    
    # Crear directorio si no existe
    os.makedirs(directorio_salida, exist_ok=True)
    
    # Crear nombre de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{actividad.id}.json"
    ruta_archivo = os.path.join(directorio_salida, nombre_archivo)
    
    # Convertir actividad a diccionario
    actividad_dict = {
        "id": actividad.id,
        "titulo": actividad.titulo,
        "materia": actividad.materia,
        "tema": actividad.tema,
        "clima": actividad.clima,
        "modalidad_trabajo": actividad.modalidad_trabajo,
        "contenido_completo": actividad.contenido_completo,
        "tareas_estudiantes": actividad.tareas_estudiantes,
        "materiales": actividad.materiales,
        "duracion": actividad.duracion,
        "fases": actividad.fases,
        "metadatos": actividad.metadatos,
        "timestamp": actividad.timestamp
    }
    
    # Guardar archivo
    try:
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(actividad_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Actividad guardada en: {ruta_archivo}")
        return ruta_archivo
        
    except Exception as e:
        logger.error(f"Error guardando actividad: {e}")
        print(f"❌ No pude guardar la actividad: {e}")
        return None

def main():
    """Función principal con interfaz conversacional"""
    
    print("🤖 Sistema de Agentes Inteligente")
    print("CrewAI + Ollama + Few-shot estratégico + Human-in-the-loop")
    print("="*70)
    print("💡 Describe qué actividad educativa quieres crear")
    print("   Ejemplos:")
    print("   • 'Quiero enseñar las fracciones de forma divertida'")
    print("   • 'Necesito una actividad sobre el sistema solar'")
    print("   • 'Ayúdame con comprensión lectora para 4º primaria'")
    print("-"*70)
    
    try:
        # Inicializar sistema
        sistema = SistemaAgentesInteligente()
        
        while True:
            # Obtener input del usuario
            print("\n📝 Describe tu actividad (o 'salir' para terminar):")
            prompt_usuario = input("🗣️ ").strip()
            
            if not prompt_usuario:
                print("⚠️ Por favor, describe qué actividad quieres crear.")
                continue
            
            if prompt_usuario.lower() in ['salir', 'exit', 'quit', 'q']:
                print("👋 ¡Hasta luego!")
                break
            
            # Generar actividad
            print(f"\n🚀 Generando actividad...")
            actividad = sistema.generar_actividad_completa(prompt_usuario)
            
            if actividad:
                # Preguntar si quiere guardar
                guardar = input(f"\n💾 ¿Quieres guardar esta actividad? (sí/no): ").strip().lower()
                
                if guardar in ['s', 'sí', 'si', 'vale', 'ok']:
                    guardar_actividad(actividad)
                
                # Preguntar si quiere crear otra
                continuar = input(f"\n🔄 ¿Quieres crear otra actividad? (sí/no): ").strip().lower()
                
                if continuar not in ['s', 'sí', 'si', 'vale', 'ok']:
                    print("👋 ¡Hasta luego!")
                    break
            else:
                print("❌ No se pudo generar la actividad. ¿Quieres intentar de nuevo?")
                continuar = input("🔄 (sí/no): ").strip().lower()
                
                if continuar not in ['s', 'sí', 'si', 'vale', 'ok']:
                    break
    
    except KeyboardInterrupt:
        print("\n👋 Proceso interrumpido por el usuario")
    
    except Exception as e:
        logger.error(f"Error en main: {e}")
        print(f"❌ Error inesperado: {e}")
        print("💡 Revisa la configuración de Ollama y las dependencias")

if __name__ == "__main__":
    main()