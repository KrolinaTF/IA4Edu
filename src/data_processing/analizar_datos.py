#!/usr/bin/env python3
"""
Analizador de Datos ProyectIA
Evalúa la consistencia y realismo de los datos generados
"""

import json
import os
from collections import defaultdict, Counter

def cargar_todos_los_perfiles():
    """Carga todos los perfiles de todos los cursos"""
    perfiles_totales = []
    archivos = []
    
    curso_dir = 'data/processed/por_curso/'
    if not os.path.exists(curso_dir):
        print(f"❌ No existe el directorio {curso_dir}")
        return [], []
    
    for archivo in os.listdir(curso_dir):
        if archivo.endswith('.json') and 'perfiles_' in archivo:
            ruta = os.path.join(curso_dir, archivo)
            archivos.append(archivo)
            
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                perfiles = data.get('perfiles', [])
                for perfil in perfiles:
                    perfil['_archivo_origen'] = archivo
                perfiles_totales.extend(perfiles)
    
    return perfiles_totales, archivos

def analizar_edad_curso(perfiles):
    """Analiza la consistencia entre edad y curso"""
    print("🔍 ANÁLISIS EDAD-CURSO")
    print("=" * 50)
    
    # Rangos esperados por curso
    rangos_esperados = {
        '1_primaria': (6, 7),
        '2_primaria': (7, 8), 
        '3_primaria': (8, 9),
        '4_primaria': (9, 10),
        '5_primaria': (10, 11),
        '6_primaria': (11, 12)
    }
    
    inconsistencias = []
    estadisticas_curso = defaultdict(list)
    
    for perfil in perfiles:
        edad = perfil.get('identificacion', {}).get('edad')
        curso = perfil.get('identificacion', {}).get('curso')
        archivo = perfil.get('_archivo_origen', 'desconocido')
        
        if edad and curso:
            estadisticas_curso[curso].append(edad)
            
            rango_min, rango_max = rangos_esperados.get(curso, (0, 20))
            
            if not (rango_min <= edad <= rango_max):
                inconsistencias.append({
                    'tipo': 'edad_curso',
                    'edad': edad,
                    'curso': curso,
                    'archivo': archivo,
                    'esperado': f"{rango_min}-{rango_max} años",
                    'severidad': 'alta' if abs(edad - rango_max) > 2 else 'media'
                })
    
    # Mostrar estadísticas por curso
    for curso, edades in estadisticas_curso.items():
        promedio = sum(edades) / len(edades)
        min_edad, max_edad = min(edades), max(edades)
        rango_esperado = rangos_esperados.get(curso, (0, 0))
        
        print(f"{curso}: {len(edades)} estudiantes")
        print(f"  Edades: {min_edad}-{max_edad} años (promedio: {promedio:.1f})")
        print(f"  Esperado: {rango_esperado[0]}-{rango_esperado[1]} años")
        print(f"  Atípicos: {len([e for e in edades if not (rango_esperado[0] <= e <= rango_esperado[1])])}")
        print()
    
    return inconsistencias

def analizar_ci_vs_necesidades(perfiles):
    """Analiza coherencia entre CI y necesidades de apoyo"""
    print("🧠 ANÁLISIS CI vs NECESIDADES DE APOYO")
    print("=" * 50)
    
    inconsistencias = []
    casos_interesantes = []
    
    for perfil in perfiles:
        ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado')
        adaptaciones = perfil.get('adaptaciones', {})
        tipo_estudiante = perfil.get('identificacion', {}).get('tipo_estudiante', 'tipico')
        diagnostico = perfil.get('identificacion', {}).get('diagnostico_oficial', 'ninguno')
        
        if ci:
            # CI muy alto con muchas adaptaciones (posible 2e)
            num_adaptaciones = sum(len(v) if isinstance(v, list) else 0 
                                 for v in adaptaciones.values())
            
            if ci >= 130 and num_adaptaciones > 5:
                if tipo_estudiante != 'doble_excepcionalidad':
                    inconsistencias.append({
                        'tipo': 'ci_alto_muchas_adaptaciones',
                        'ci': ci,
                        'adaptaciones': num_adaptaciones,
                        'tipo_estudiante': tipo_estudiante,
                        'diagnostico': diagnostico,
                        'severidad': 'media',
                        'posible_causa': 'Podría ser 2e no identificada'
                    })
                else:
                    casos_interesantes.append({
                        'tipo': '2e_identificada',
                        'ci': ci,
                        'adaptaciones': num_adaptaciones,
                        'diagnostico': diagnostico
                    })
            
            # CI bajo con pocas adaptaciones
            elif ci < 85 and num_adaptaciones < 2:
                inconsistencias.append({
                    'tipo': 'ci_bajo_pocas_adaptaciones',
                    'ci': ci,
                    'adaptaciones': num_adaptaciones,
                    'severidad': 'alta',
                    'posible_causa': 'Necesita más apoyo'
                })
    
    print(f"Total casos CI alto + muchas adaptaciones: {len([i for i in inconsistencias if i['tipo'] == 'ci_alto_muchas_adaptaciones'])}")
    print(f"Total casos 2e bien identificados: {len(casos_interesantes)}")
    print(f"Total casos CI bajo sin apoyo suficiente: {len([i for i in inconsistencias if i['tipo'] == 'ci_bajo_pocas_adaptaciones'])}")
    print()
    
    return inconsistencias

def analizar_tipos_estudiantes(perfiles):
    """Analiza distribución de tipos de estudiantes por curso"""
    print("📊 ANÁLISIS TIPOS DE ESTUDIANTES")
    print("=" * 50)
    
    distribucion = defaultdict(lambda: defaultdict(int))
    total_por_curso = defaultdict(int)
    
    for perfil in perfiles:
        curso = perfil.get('identificacion', {}).get('curso', 'desconocido')
        tipo = perfil.get('identificacion', {}).get('tipo_estudiante', 'tipico')
        
        distribucion[curso][tipo] += 1
        total_por_curso[curso] += 1
    
    # Mostrar distribución y evaluar realismo
    for curso in sorted(distribucion.keys()):
        print(f"{curso} ({total_por_curso[curso]} estudiantes):")
        
        for tipo, cantidad in distribucion[curso].items():
            porcentaje = (cantidad / total_por_curso[curso]) * 100
            print(f"  {tipo}: {cantidad} ({porcentaje:.1f}%)")
        print()
    
    # Evaluar realismo (porcentajes esperados en aulas reales)
    porcentajes_esperados = {
        'tipico': (80, 90),  # 80-90% estudiantes típicos
        'adhd': (3, 8),      # 3-8% ADHD
        'altas_capacidades': (2, 5),  # 2-5% AC
        'doble_excepcionalidad': (0.5, 2)  # 0.5-2% 2e
    }
    
    return distribucion, porcentajes_esperados

def analizar_campos_innecesarios(perfiles):
    """Identifica campos que se pueden eliminar"""
    print("🗑️ ANÁLISIS CAMPOS INNECESARIOS")
    print("=" * 50)
    
    campos_encontrados = defaultdict(int)
    campos_siempre_null = defaultdict(int)
    campos_siempre_igual = defaultdict(set)
    
    for perfil in perfiles:
        # Revisar metadatos
        metadatos = perfil.get('metadatos', {})
        for campo, valor in metadatos.items():
            campos_encontrados[f"metadatos.{campo}"] += 1
            if valor is None:
                campos_siempre_null[f"metadatos.{campo}"] += 1
            campos_siempre_igual[f"metadatos.{campo}"].add(str(valor))
        
        # Revisar contexto
        contexto = perfil.get('contexto', {})
        for campo, valor in contexto.items():
            campos_encontrados[f"contexto.{campo}"] += 1
            if valor is None:
                campos_siempre_null[f"contexto.{campo}"] += 1
            campos_siempre_igual[f"contexto.{campo}"].add(str(valor))
    
    total_perfiles = len(perfiles)
    
    # Campos siempre null
    print("Campos siempre NULL (candidatos a eliminar):")
    for campo, count in campos_siempre_null.items():
        if count == total_perfiles:
            print(f"  ✗ {campo}: NULL en 100% de casos")
        elif count > total_perfiles * 0.8:
            print(f"  ⚠ {campo}: NULL en {(count/total_perfiles)*100:.1f}% de casos")
    
    print("\nCampos con valor único (candidatos a eliminar):")
    for campo, valores in campos_siempre_igual.items():
        if len(valores) == 1:
            valor = list(valores)[0]
            print(f"  ✗ {campo}: siempre '{valor}'")
    
    print()

def generar_reporte_completo(perfiles, archivos):
    """Genera reporte completo de inconsistencias"""
    print("\n" + "=" * 70)
    print("📋 REPORTE COMPLETO DE ANÁLISIS DE DATOS")
    print("=" * 70)
    
    print(f"📊 RESUMEN GENERAL:")
    print(f"  Total perfiles analizados: {len(perfiles)}")
    print(f"  Archivos procesados: {len(archivos)}")
    print(f"  Archivos: {', '.join(archivos)}")
    print()
    
    # Análisis individuales
    inconsistencias_edad = analizar_edad_curso(perfiles)
    inconsistencias_ci = analizar_ci_vs_necesidades(perfiles)
    distribucion, esperados = analizar_tipos_estudiantes(perfiles)
    analizar_campos_innecesarios(perfiles)
    
    # Resumen de inconsistencias
    print("🚨 RESUMEN DE INCONSISTENCIAS ENCONTRADAS:")
    print(f"  Problemas edad-curso: {len(inconsistencias_edad)}")
    print(f"  Problemas CI-necesidades: {len(inconsistencias_ci)}")
    
    # Casos más severos
    casos_severos = [i for i in inconsistencias_edad + inconsistencias_ci 
                    if i.get('severidad') == 'alta']
    
    print(f"\n🔥 CASOS SEVEROS A CORREGIR: {len(casos_severos)}")
    for caso in casos_severos[:5]:  # Mostrar solo primeros 5
        print(f"  - {caso['tipo']}: {caso}")
    
    if len(casos_severos) > 5:
        print(f"  ... y {len(casos_severos) - 5} más")
    
    return {
        'inconsistencias_edad': inconsistencias_edad,
        'inconsistencias_ci': inconsistencias_ci,
        'distribucion_tipos': distribucion,
        'casos_severos': casos_severos
    }

def main():
    print("🔍 ANALIZADOR DE DATOS PROYECTIA")
    print("Evaluando consistencia y realismo de datos generados")
    print("=" * 70)
    
    # Cargar todos los perfiles
    perfiles, archivos = cargar_todos_los_perfiles()
    
    if not perfiles:
        print("❌ No se encontraron perfiles para analizar")
        return
    
    # Generar reporte completo
    reporte = generar_reporte_completo(perfiles, archivos)
    
    print("\n✅ ANÁLISIS COMPLETADO")
    print("💡 Revisa los resultados y decide qué inconsistencias corregir")

if __name__ == "__main__":
    main()