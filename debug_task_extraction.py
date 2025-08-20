#!/usr/bin/env python3
"""
Script de depuración para extraer tareas de actividades JSON
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Solo cargar manualmente los componentes necesarios para debug
import logging
from typing import Dict, List

def debug_json_structure():
    """Debug de la estructura JSON de k_feria_acertijos"""
    print("🔍 DEBUGEANDO ESTRUCTURA JSON")
    print("=" * 50)
    
    # Cargar el JSON directamente
    json_path = "data/actividades/json_actividades/k_feria_acertijos.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            actividad_data = json.load(f)
        
        print(f"📁 Archivo: {json_path}")
        print(f"🔑 Claves principales: {list(actividad_data.keys())}")
        
        if 'etapas' in actividad_data:
            print(f"📋 Número de etapas: {len(actividad_data['etapas'])}")
            
            for i, etapa in enumerate(actividad_data['etapas']):
                print(f"\n📌 Etapa {i+1}: {etapa.get('nombre', 'Sin nombre')}")
                print(f"   🔑 Claves: {list(etapa.keys())}")
                
                if 'tareas' in etapa:
                    print(f"   📝 Número de tareas: {len(etapa['tareas'])}")
                    
                    for j, tarea in enumerate(etapa['tareas']):
                        print(f"      🎯 Tarea {j+1}: {tarea.get('nombre', 'Sin nombre')}")
                        print(f"          📄 Descripción: {tarea.get('descripcion', 'Sin descripción')[:60]}...")
                        print(f"          🔑 Claves: {list(tarea.keys())}")
                else:
                    print(f"   ❌ No tiene clave 'tareas'")
        else:
            print("❌ No tiene clave 'etapas'")
            
    except Exception as e:
        print(f"❌ Error cargando JSON: {e}")

def debug_task_extraction():
    """Debug del método de extracción de tareas - versión simplificada"""
    print("\n\n🔧 DEBUGEANDO EXTRACCIÓN DE TAREAS (SIMPLIFICADO)")
    print("=" * 50)
    
    try:
        # Cargar actividad directamente
        json_path = "data/actividades/json_actividades/k_feria_acertijos.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            actividad_data = json.load(f)
        
        print(f"📥 Actividad cargada: {actividad_data.get('titulo', 'Sin título')}")
        
        # Simular extracción de tareas manualmente
        tareas_encontradas = []
        contador = 1
        
        for etapa in actividad_data.get('etapas', []):
            if not isinstance(etapa, dict):
                continue
                
            nombre_etapa = etapa.get('nombre', f'Etapa {contador}')
            print(f"   📌 Procesando etapa: {nombre_etapa}")
            
            for tarea_data in etapa.get('tareas', []):
                if not isinstance(tarea_data, dict):
                    continue
                
                nombre_tarea = tarea_data.get('nombre', f'Tarea {contador}')
                descripcion = tarea_data.get('descripcion', 'Sin descripción')
                formato = tarea_data.get('formato_asignacion', 'colaborativa')
                
                tareas_encontradas.append({
                    'id': f"tarea_{contador:02d}",
                    'nombre': nombre_tarea,
                    'descripcion': descripcion[:80] + "..." if len(descripcion) > 80 else descripcion,
                    'formato': formato
                })
                
                print(f"      ✅ Tarea {contador}: {nombre_tarea}")
                contador += 1
        
        print(f"\n📊 Total tareas encontradas: {len(tareas_encontradas)}")
        
        for tarea in tareas_encontradas:
            print(f"   • {tarea['id']}: {tarea['nombre']}")
            print(f"     📄 {tarea['descripcion']}")
            print(f"     🎯 Formato: {tarea['formato']}")
            print()
            
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        import traceback
        traceback.print_exc()

def debug_activity_structure_validation():
    """Debug de la validación de estructura JSON - versión simplificada"""
    print("\n\n✅ DEBUGEANDO VALIDACIÓN DE ESTRUCTURA")
    print("=" * 50)
    
    try:
        # Cargar actividad
        json_path = "data/actividades/json_actividades/k_feria_acertijos.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            actividad_data = json.load(f)
        
        # Debug paso a paso manual
        tiene_etapas = 'etapas' in actividad_data and isinstance(actividad_data['etapas'], list)
        print(f"   📌 ¿Tiene etapas?: {tiene_etapas}")
        
        if tiene_etapas:
            etapas_con_tareas = 0
            total_tareas = 0
            
            for i, etapa in enumerate(actividad_data['etapas']):
                tiene_tareas = isinstance(etapa, dict) and 'tareas' in etapa
                print(f"   📋 Etapa {i+1}: ¿Tiene tareas? {tiene_tareas}")
                
                if tiene_tareas:
                    etapas_con_tareas += 1
                    num_tareas = len(etapa['tareas']) if isinstance(etapa['tareas'], list) else 0
                    total_tareas += num_tareas
                    print(f"      📝 Número de tareas: {num_tareas}")
            
            print(f"   📊 Etapas con tareas: {etapas_con_tareas}/{len(actividad_data['etapas'])}")
            print(f"   📊 Total tareas en todas las etapas: {total_tareas}")
            
            # Validación final
            es_valida = tiene_etapas and etapas_con_tareas > 0 and total_tareas > 0
            print(f"   ✅ ¿Estructura válida?: {es_valida}")
        
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_json_structure()
    debug_task_extraction()
    debug_activity_structure_validation()
    
    print("\n✅ DEBUG COMPLETADO")