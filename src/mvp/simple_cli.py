"""
CLI Simplificada para el sistema ABP MVP.
Interfaz mínima para probar el coordinador simplificado.
"""

import logging
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp.simplified_coordinator import SimplifiedCoordinator
from mvp.profile_manager import ProfileManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("SimplifiedABP.CLI")

def main():
    """Función principal de la CLI"""
    print("\n🚀 SISTEMA ABP SIMPLIFICADO - MVP")
    print("=" * 50)
    
    try:
        # Inicializar componentes
        print("📦 Inicializando sistema...")
        coordinator = SimplifiedCoordinator()
        profile_manager = ProfileManager()
        
        # Mostrar información del aula
        print(f"\n👥 AULA: {len(profile_manager.get_all_student_names())} estudiantes")
        print(f"📊 Neurotipos: {profile_manager.get_neurotipo_stats()}")
        
        # Bucle principal
        while True:
            print("\n" + "=" * 50)
            print("OPCIONES:")
            print("1. Generar actividad ABP (con feedback iterativo)")
            print("2. Ver perfiles de estudiantes")
            print("3. Ver parejas optimizadas")
            print("4. Salir")
            
            opcion = input("\nSelecciona una opción (1-4): ").strip()
            
            if opcion == "1":
                generar_actividad_personalizada(coordinator)
            elif opcion == "2":
                mostrar_perfiles(profile_manager)
            elif opcion == "3":
                mostrar_parejas(profile_manager)
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción no válida")
    
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Error en main: {e}")

def generar_actividad_personalizada(coordinator):
    """Genera actividad personalizada según input del usuario"""
    print("\n📝 GENERAR ACTIVIDAD ABP PERSONALIZADA")
    print("-" * 40)
    
    # Recoger input del usuario
    solicitud = input("Describe la actividad que quieres crear: ").strip()
    
    if not solicitud:
        print("❌ Debes describir la actividad")
        return
    
    detalles = input("Detalles adicionales (opcional): ").strip()
    
    print(f"\n🔄 Generando actividad para: '{solicitud}'...")
    
    try:
        # Generar actividad inicial
        activity = coordinator.generate_activity(solicitud, detalles)
        
        # Mostrar resultado inicial
        print("\n🎯 ACTIVIDAD INICIAL GENERADA:")
        print("=" * 50)
        mostrar_actividad(activity)
        
        # Sistema de feedback iterativo (sin guardar todavía)
        print("\n💡 Ahora puedes refinar la actividad con feedback...")
        activity_final = proceso_feedback_iterativo(coordinator, activity)
        
        # Mostrar resumen final
        if activity_final != activity:
            print("\n🎯 ACTIVIDAD FINAL (después de refinamientos):")
            print("=" * 50)
            mostrar_actividad(activity_final)
        
        # Opción de guardar LA VERSIÓN FINAL
        guardar = input("\n💾 ¿Guardar actividad final? (s/n): ").strip().lower()
        if guardar in ['s', 'si', 'sí', 'y', 'yes']:
            filepath = coordinator.save_activity(activity_final)
            if filepath:
                print(f"✅ Actividad final guardada en: {filepath}")
        else:
            print("📝 Actividad no guardada. Se ha perdido al salir.")
    
    except Exception as e:
        print(f"❌ Error generando actividad: {e}")
        logger.error(f"Error en generar_actividad_personalizada: {e}")

def proceso_feedback_iterativo(coordinator, activity):
    """Proceso iterativo de feedback y refinamiento"""
    current_activity = activity
    iteracion = 0
    max_iteraciones = 3
    
    while iteracion < max_iteraciones:
        print(f"\n🔄 REFINAMIENTO #{iteracion + 1}")
        print("-" * 30)
        print("¿Quieres dar feedback para mejorar la actividad?")
        print("Ejemplos de feedback:")
        print("• 'Añade más detalles sobre los materiales'")
        print("• 'Cambia la duración a 3 sesiones'")
        print("• 'Incluye más actividades para Luis (TDAH)'")
        print("• 'La tarea 2 es muy compleja, simplifícala'")
        print("• 'Los roles no están claros, especifícalos mejor'")
        print("• 'Falta material manipulativo para el TDAH'")
        
        quiere_feedback = input("\n¿Dar feedback? (s/n): ").strip().lower()
        
        if quiere_feedback not in ['s', 'si', 'sí', 'y', 'yes']:
            print("✅ Actividad finalizada sin más cambios")
            break
        
        feedback = input("\n📝 Tu feedback: ").strip()
        
        if not feedback:
            print("❌ No se proporcionó feedback")
            continue
        
        print(f"\n🔄 Aplicando feedback: '{feedback[:50]}...'")
        
        try:
            # Refinar actividad
            refined_activity = coordinator.refine_activity(current_activity, feedback)
            
            # Mostrar cambios
            print("\n🎯 ACTIVIDAD REFINADA:")
            print("=" * 50)
            mostrar_actividad(refined_activity)
            
            # Preguntar si acepta los cambios
            aceptar = input("\n✅ ¿Aceptar estos cambios? (s/n): ").strip().lower()
            
            if aceptar in ['s', 'si', 'sí', 'y', 'yes']:
                current_activity = refined_activity
                iteracion += 1
                print(f"✅ Cambios aplicados. Refinamiento #{iteracion} completado.")
            else:
                print("❌ Cambios rechazados. Manteniendo versión anterior.")
        
        except Exception as e:
            print(f"❌ Error en refinamiento: {e}")
            logger.error(f"Error en proceso_feedback_iterativo: {e}")
            break
    
    if iteracion >= max_iteraciones:
        print(f"\n⚠️ Máximo de {max_iteraciones} refinamientos alcanzado")
    
    return current_activity


def mostrar_actividad(activity):
    """Muestra la actividad generada de forma legible"""
    print("\n🎯 ACTIVIDAD GENERADA:")
    print("=" * 50)
    
    print(f"📋 Título: {activity.get('titulo', 'Sin título')}")
    print(f"🎯 Objetivo: {activity.get('objetivo', 'Sin objetivo')}")
    print(f"⏱️ Duración: {activity.get('duracion', 'No especificada')}")
    
    fases = activity.get('fases', [])
    for i, fase in enumerate(fases, 1):
        print(f"\n📌 FASE {i}: {fase.get('nombre', 'Sin nombre')}")
        print(f"   Descripción: {fase.get('descripcion', 'Sin descripción')}")
        
        tareas = fase.get('tareas', [])
        for j, tarea in enumerate(tareas, 1):
            print(f"\n   🔸 Tarea {j}: {tarea.get('nombre', 'Sin nombre')}")
            print(f"      📝 {tarea.get('descripcion', 'Sin descripción')}")
            
            parejas = tarea.get('parejas_asignadas', [])
            if parejas:
                print(f"      👥 Parejas: {', '.join(parejas)}")
            
            detalles = tarea.get('detalles_especificos', '')
            if detalles:
                print(f"      🔍 Detalles: {detalles}")
    
    adaptaciones = activity.get('adaptaciones', {})
    if adaptaciones:
        print(f"\n🔧 ADAPTACIONES:")
        for neurotipo, lista_adaptaciones in adaptaciones.items():
            if lista_adaptaciones:
                print(f"   {neurotipo}: {', '.join(lista_adaptaciones)}")

def mostrar_perfiles(profile_manager):
    """Muestra información de perfiles de estudiantes"""
    print("\n👥 PERFILES DE ESTUDIANTES")
    print("-" * 40)
    
    stats = profile_manager.get_neurotipo_stats()
    print(f"📊 Distribución de neurotipos:")
    for neurotipo, cantidad in stats.items():
        if cantidad > 0:
            estudiantes = profile_manager.neurotipo_map[neurotipo]
            print(f"   {neurotipo}: {cantidad} ({', '.join(estudiantes)})")
    
    print(f"\n📋 Resumen: {profile_manager.get_students_summary()}")
    
    print(f"\n🔧 Adaptaciones necesarias:")
    adaptaciones = profile_manager.get_adaptations_needed()
    for neurotipo, lista in adaptaciones.items():
        print(f"\n   {neurotipo.upper()}:")
        for adaptacion in lista:
            print(f"      • {adaptacion}")

def mostrar_parejas(profile_manager):
    """Muestra parejas optimizadas"""
    print("\n👫 PAREJAS OPTIMIZADAS")
    print("-" * 40)
    
    parejas = profile_manager.create_optimal_pairs()
    
    for i, pareja in enumerate(parejas, 1):
        if len(pareja) == 2:
            est1, est2 = pareja
            print(f"Pareja {i}: {est1} + {est2}")
        elif len(pareja) == 3:
            est1, est2, est3 = pareja
            print(f"Grupo {i}: {est1} + {est2} + {est3}")
    
    print(f"\n📊 Total: {len(parejas)} parejas/grupos formados")

if __name__ == "__main__":
    main()