#!/usr/bin/env python3
"""
Unificador de Formatos de Curso - ProyectIA
Convierte todos los formatos "Xº Primaria" a "X_primaria"
"""

import json
import os

def unificar_formatos_curso():
    """Unifica todos los formatos de curso al estándar X_primaria"""
    
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
    
    # Mapeo de conversión
    conversion_map = {
        '1º Primaria': '1_primaria',
        '2º Primaria': '2_primaria', 
        '3º Primaria': '3_primaria',
        '4º Primaria': '4_primaria',
        '5º Primaria': '5_primaria',
        '6º Primaria': '6_primaria'
    }
    
    # Contar formatos antes de conversión
    print("\n🔍 ANTES DE LA CONVERSIÓN:")
    formatos_antes = {}
    for perfil in perfiles:
        curso = perfil.get('identificacion', {}).get('curso', 'desconocido')
        formatos_antes[curso] = formatos_antes.get(curso, 0) + 1
    
    for formato, cantidad in sorted(formatos_antes.items()):
        print(f"  {formato}: {cantidad} perfiles")
    
    # Realizar conversión
    print(f"\n🔄 REALIZANDO CONVERSIÓN...")
    conversiones_realizadas = 0
    
    for perfil in perfiles:
        curso_original = perfil.get('identificacion', {}).get('curso')
        
        if curso_original in conversion_map:
            curso_nuevo = conversion_map[curso_original]
            perfil['identificacion']['curso'] = curso_nuevo
            conversiones_realizadas += 1
    
    print(f"✅ Conversiones realizadas: {conversiones_realizadas}")
    
    # Verificar resultado
    print(f"\n✅ DESPUÉS DE LA CONVERSIÓN:")
    formatos_despues = {}
    for perfil in perfiles:
        curso = perfil.get('identificacion', {}).get('curso', 'desconocido')
        formatos_despues[curso] = formatos_despues.get(curso, 0) + 1
    
    for formato, cantidad in sorted(formatos_despues.items()):
        print(f"  {formato}: {cantidad} perfiles")
    
    # Verificar que no queden formatos antiguos
    formatos_problematicos = [f for f in formatos_despues.keys() if 'º' in f]
    
    if formatos_problematicos:
        print(f"\n❌ ERROR: Quedan formatos sin convertir: {formatos_problematicos}")
        return False
    
    # Guardar dataset corregido
    print(f"\n💾 Guardando dataset corregido...")
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Dataset guardado correctamente")
    
    # Mostrar resumen final
    print(f"\n📊 RESUMEN DE LA CORRECCIÓN:")
    print(f"  - Perfiles procesados: {len(perfiles)}")
    print(f"  - Conversiones realizadas: {conversiones_realizadas}")
    print(f"  - Formatos únicos después: {len(formatos_despues)}")
    print(f"  - ✅ Todos los formatos ahora son consistentes")
    
    return True

def main():
    """Función principal"""
    print("🔧 UNIFICADOR DE FORMATOS DE CURSO")
    print("Convirtiendo 'Xº Primaria' → 'X_primaria'")
    print("=" * 50)
    
    exito = unificar_formatos_curso()
    
    if exito:
        print(f"\n🎉 UNIFICACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Todos los cursos ahora tienen formato consistente")
        print("🚀 Listo para el siguiente paso: completar campos faltantes")
    else:
        print(f"\n❌ ERROR EN LA UNIFICACIÓN")
        print("🔧 Revisa los mensajes de error anteriores")

if __name__ == "__main__":
    main()