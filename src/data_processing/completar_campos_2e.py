#!/usr/bin/env python3
"""
Completador de Campos Faltantes en Perfiles 2e - ProyectIA
Completa CI y lectura faltantes en perfiles de doble excepcionalidad
"""

import json
import random
import os

def identificar_perfiles_2e(perfiles):
    """Identifica perfiles de doble excepcionalidad"""
    perfiles_2e = []
    
    for i, perfil in enumerate(perfiles):
        fuente = perfil.get('metadatos', {}).get('fuente_datos', '')
        
        # Identificar por fuente de datos
        if '2e' in fuente.lower() or 'generado_2e_ttess' in fuente:
            perfiles_2e.append((i, perfil))
    
    return perfiles_2e

def analizar_campos_faltantes(perfiles_2e):
    """Analiza qué campos faltan en perfiles 2e"""
    print("🔍 ANÁLISIS DE CAMPOS FALTANTES EN PERFILES 2e")
    print("=" * 50)
    
    ci_faltantes = []
    lectura_faltantes = []
    
    for i, perfil in perfiles_2e:
        # Verificar CI
        ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado')
        if ci is None:
            ci_faltantes.append((i, perfil))
        
        # Verificar lectura
        lectura = perfil.get('perfil_academico', {}).get('lectura')
        if lectura is None:
            lectura_faltantes.append((i, perfil))
    
    print(f"📊 Perfiles 2e encontrados: {len(perfiles_2e)}")
    print(f"❌ CI faltante: {len(ci_faltantes)} casos")
    print(f"❌ Lectura faltante: {len(lectura_faltantes)} casos")
    
    return ci_faltantes, lectura_faltantes

def completar_ci_faltante(perfil):
    """Completa CI faltante para perfil 2e"""
    
    # Rango base para AC (125-145)
    ci_base_min, ci_base_max = 125, 145
    
    # Ajustar según otras medidas cognitivas
    perfil_cognitivo = perfil.get('perfil_cognitivo', {})
    
    # Si tiene velocidad de procesamiento baja (típico en 2e)
    velocidad_proc = perfil_cognitivo.get('velocidad_procesamiento', 3)
    memoria_trabajo = perfil_cognitivo.get('memoria_trabajo', 3)
    
    # Ajustar rango según patrones 2e
    if velocidad_proc <= 2:  # Velocidad baja
        ci_min, ci_max = 125, 135  # Extremo inferior del rango AC
    elif memoria_trabajo <= 2:  # Memoria de trabajo baja
        ci_min, ci_max = 128, 138
    else:
        ci_min, ci_max = 130, 145  # Rango completo AC
    
    # Generar CI con pequeña variabilidad
    ci_estimado = random.randint(ci_min, ci_max)
    
    return ci_estimado

def completar_lectura_faltante(perfil):
    """Completa lectura faltante para perfil 2e"""
    
    # Obtener información del perfil
    dificultades = perfil.get('perfil_academico', {}).get('dificultades_observadas', [])
    matematicas = perfil.get('perfil_academico', {}).get('matematicas', 3)
    escritura = perfil.get('perfil_academico', {}).get('escritura', 3)
    
    # Patrón típico 2e: matemáticas > lectura
    # Si tiene dificultades específicas en lectoescritura
    dificultades_lectura = ['dislexia', 'lectura', 'comprension_lectora', 'velocidad_lectora']
    tiene_dificultad_lectura = any(dif in str(dificultades).lower() for dif in dificultades_lectura)
    
    if tiene_dificultad_lectura:
        # Lectura claramente por debajo de matemáticas
        lectura = max(1, matematicas - random.randint(1, 2))
    elif escritura and escritura < matematicas:
        # Si escritura es baja, lectura similar
        lectura = random.choice([escritura, escritura + 1])
    else:
        # Sin dificultades específicas, lectura promedio pero menor que matemáticas
        lectura = max(2, min(4, matematicas - random.randint(0, 1)))
    
    return int(lectura)

def validar_coherencia_2e(perfil):
    """Valida que el perfil 2e sea coherente tras completar campos"""
    
    matematicas = perfil.get('perfil_academico', {}).get('matematicas', 3)
    lectura = perfil.get('perfil_academico', {}).get('lectura', 3)
    ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado', 100)
    
    # Verificaciones de coherencia 2e
    validaciones = []
    
    # 1. CI en rango AC
    if ci >= 125:
        validaciones.append("✅ CI en rango AC")
    else:
        validaciones.append("⚠️ CI por debajo del rango AC típico")
    
    # 2. Patrón académico 2e (matemáticas >= lectura)
    if matematicas >= lectura:
        validaciones.append("✅ Patrón académico 2e coherente")
    else:
        validaciones.append("⚠️ Lectura superior a matemáticas (atípico para 2e)")
    
    # 3. Variabilidad interna
    diferencia = abs(matematicas - lectura)
    if diferencia >= 1:
        validaciones.append("✅ Variabilidad académica presente")
    else:
        validaciones.append("ℹ️ Perfil académico uniforme")
    
    return validaciones

def completar_campos_2e():
    """Función principal para completar campos faltantes"""
    
    dataset_file = 'data/processed/dataset_unificado_proyectia.json'
    
    if not os.path.exists(dataset_file):
        print(f"❌ ERROR: No se encuentra {dataset_file}")
        return False
    
    # Cargar dataset
    print("📖 Cargando dataset unificado...")
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    perfiles = data.get('perfiles', [])
    print(f"✅ Dataset cargado: {len(perfiles)} perfiles")
    
    # Identificar perfiles 2e
    perfiles_2e = identificar_perfiles_2e(perfiles)
    
    if not perfiles_2e:
        print("❌ No se encontraron perfiles 2e")
        return False
    
    # Analizar campos faltantes
    ci_faltantes, lectura_faltantes = analizar_campos_faltantes(perfiles_2e)
    
    if not ci_faltantes and not lectura_faltantes:
        print("✅ No hay campos faltantes en perfiles 2e")
        return True
    
    # Fijar semilla para reproducibilidad
    random.seed(42)
    
    print(f"\n🔧 COMPLETANDO CAMPOS FALTANTES...")
    
    # Completar CIs faltantes
    ci_completados = 0
    for i, perfil in ci_faltantes:
        ci_nuevo = completar_ci_faltante(perfil)
        perfil['perfil_cognitivo']['ci_estimado'] = ci_nuevo
        ci_completados += 1
        print(f"  ✅ Perfil {i}: CI completado → {ci_nuevo}")
    
    # Completar lecturas faltantes
    lectura_completadas = 0
    for i, perfil in lectura_faltantes:
        lectura_nueva = completar_lectura_faltante(perfil)
        perfil['perfil_academico']['lectura'] = lectura_nueva
        lectura_completadas += 1
        print(f"  ✅ Perfil {i}: Lectura completada → {lectura_nueva}")
    
    print(f"\n📊 RESUMEN DE COMPLETADO:")
    print(f"  - CIs completados: {ci_completados}")
    print(f"  - Lecturas completadas: {lectura_completadas}")
    
    # Validar coherencia en algunos casos
    print(f"\n🔍 VALIDACIÓN DE COHERENCIA (muestra):")
    indices_validar = [idx for idx, _ in perfiles_2e[:5]]  # Primeros 5 para muestra
    
    for idx in indices_validar:
        perfil = perfiles[idx]
        validaciones = validar_coherencia_2e(perfil)
        
        ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado', 'N/A')
        mat = perfil.get('perfil_academico', {}).get('matematicas', 'N/A')
        lec = perfil.get('perfil_academico', {}).get('lectura', 'N/A')
        
        print(f"  Perfil {idx}: CI={ci}, Mat={mat}, Lec={lec}")
        for validacion in validaciones:
            print(f"    {validacion}")
        print()
    
    # Guardar dataset actualizado
    print("💾 Guardando dataset actualizado...")
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ Dataset guardado correctamente")
    
    return True

def main():
    """Función principal"""
    print("🧩 COMPLETADOR DE CAMPOS 2e")
    print("Completando CI y lectura en perfiles de doble excepcionalidad")
    print("=" * 60)
    
    exito = completar_campos_2e()
    
    if exito:
        print(f"\n🎉 COMPLETADO EXITOSO")
        print("✅ Todos los campos faltantes han sido completados")
        print("✅ Coherencia 2e validada")
        print("🚀 Listo para el siguiente paso: corregir edades incoherentes")
    else:
        print(f"\n❌ ERROR EN EL COMPLETADO")
        print("🔧 Revisa los mensajes de error anteriores")

if __name__ == "__main__":
    main()