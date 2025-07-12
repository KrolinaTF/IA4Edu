#!/usr/bin/env python3
"""
Auditoría Completa del Dataset Unificado ProyectIA
Identifica y cataloga TODOS los problemas de formato, rangos e inconsistencias
"""

import json
import os
from collections import defaultdict, Counter

def cargar_dataset():
    """Carga el dataset unificado"""
    dataset_file = 'data/processed/dataset_unificado_proyectia.json'
    
    if not os.path.exists(dataset_file):
        print(f"❌ ERROR: No se encuentra {dataset_file}")
        return None
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def auditoria_formatos(perfiles):
    """Audita problemas de formato"""
    print("🔍 AUDITORÍA DE FORMATOS")
    print("=" * 50)
    
    problemas = []
    
    # 1. Formatos de curso inconsistentes
    formatos_curso = set()
    for perfil in perfiles:
        curso = perfil.get('identificacion', {}).get('curso')
        if curso:
            formatos_curso.add(curso)
    
    print("📚 FORMATOS DE CURSO ENCONTRADOS:")
    formatos_correctos = []
    formatos_incorrectos = []
    
    for formato in sorted(formatos_curso):
        if '_primaria' in formato:
            formatos_correctos.append(formato)
            print(f"  ✅ {formato}")
        else:
            formatos_incorrectos.append(formato)
            print(f"  ❌ {formato}")
    
    if formatos_incorrectos:
        problemas.append({
            'tipo': 'formato_curso_inconsistente',
            'descripcion': f'{len(formatos_incorrectos)} formatos incorrectos de curso',
            'detalles': formatos_incorrectos,
            'severidad': 'alta',
            'afecta_perfiles': len([p for p in perfiles if p.get('identificacion', {}).get('curso') in formatos_incorrectos])
        })
    
    # 2. Campos requeridos faltantes
    campos_requeridos = [
        ('identificacion', 'edad'),
        ('identificacion', 'curso'),
        ('identificacion', 'genero'),
        ('perfil_academico', 'matematicas'),
        ('perfil_academico', 'lectura'),
        ('perfil_cognitivo', 'ci_estimado')
    ]
    
    print(f"\n🔧 CAMPOS REQUERIDOS FALTANTES:")
    for seccion, campo in campos_requeridos:
        faltantes = 0
        nulos = 0
        
        for perfil in perfiles:
            valor = perfil.get(seccion, {}).get(campo)
            if valor is None:
                if seccion not in perfil:
                    faltantes += 1
                else:
                    nulos += 1
        
        if faltantes > 0 or nulos > 0:
            print(f"  ❌ {seccion}.{campo}: {faltantes} faltantes, {nulos} null")
            problemas.append({
                'tipo': 'campo_faltante',
                'descripcion': f'{seccion}.{campo} faltante o null',
                'detalles': {'faltantes': faltantes, 'nulos': nulos},
                'severidad': 'alta' if faltantes + nulos > 10 else 'media',
                'afecta_perfiles': faltantes + nulos
            })
        else:
            print(f"  ✅ {seccion}.{campo}: completo")
    
    return problemas

def auditoria_rangos(perfiles):
    """Audita rangos de valores fuera de lo esperado"""
    print(f"\n📊 AUDITORÍA DE RANGOS")
    print("=" * 50)
    
    problemas = []
    
    # 1. Distribución de edades
    edades = [p.get('identificacion', {}).get('edad') for p in perfiles if p.get('identificacion', {}).get('edad')]
    contador_edades = Counter(edades)
    
    print("👶 DISTRIBUCIÓN DE EDADES:")
    edades_problematicas = []
    
    for edad in sorted(contador_edades.keys()):
        cantidad = contador_edades[edad]
        porcentaje = (cantidad / len(perfiles)) * 100
        
        # Detectar edades problemáticas
        if edad < 6 or edad > 12:
            edades_problematicas.append(edad)
            print(f"  ❌ {edad} años: {cantidad} ({porcentaje:.1f}%) - FUERA DE RANGO")
        elif edad == 6 and cantidad == 0:
            print(f"  ⚠️  6 años: {cantidad} ({porcentaje:.1f}%) - FALTA PARA 1º PRIMARIA")
            edades_problematicas.append(6)
        else:
            print(f"  ✅ {edad} años: {cantidad} ({porcentaje:.1f}%)")
    
    if edades_problematicas:
        problemas.append({
            'tipo': 'rango_edad_problematico',
            'descripcion': f'Edades fuera de rango primaria',
            'detalles': edades_problematicas,
            'severidad': 'alta',
            'afecta_perfiles': sum(contador_edades.get(edad, 0) for edad in edades_problematicas)
        })
    
    # 2. CI fuera de rangos típicos
    cis = []
    for perfil in perfiles:
        ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado')
        if ci and isinstance(ci, (int, float)):
            cis.append(ci)
    
    print(f"\n🧠 DISTRIBUCIÓN DE CI:")
    ci_problematicos = []
    
    if cis:
        ci_min, ci_max = min(cis), max(cis)
        ci_promedio = sum(cis) / len(cis)
        
        print(f"  Rango: {ci_min} - {ci_max}")
        print(f"  Promedio: {ci_promedio:.1f}")
        
        # Detectar CIs extremos
        cis_muy_bajos = [ci for ci in cis if ci < 70]
        cis_muy_altos = [ci for ci in cis if ci > 160]
        
        if cis_muy_bajos:
            print(f"  ❌ CI < 70: {len(cis_muy_bajos)} casos")
            ci_problematicos.extend(cis_muy_bajos)
        
        if cis_muy_altos:
            print(f"  ❌ CI > 160: {len(cis_muy_altos)} casos")
            ci_problematicos.extend(cis_muy_altos)
        
        if ci_problematicos:
            problemas.append({
                'tipo': 'ci_extremo',
                'descripcion': f'CIs fuera de rangos típicos',
                'detalles': {'muy_bajos': len(cis_muy_bajos), 'muy_altos': len(cis_muy_altos)},
                'severidad': 'media',
                'afecta_perfiles': len(ci_problematicos)
            })
    
    return problemas

def auditoria_coherencia_edad_curso(perfiles):
    """Audita coherencia entre edad y curso"""
    print(f"\n👥 AUDITORÍA COHERENCIA EDAD-CURSO")
    print("=" * 50)
    
    problemas = []
    
    # Rangos esperados
    rangos_esperados = {
        '1_primaria': (6, 7), '1º Primaria': (6, 7),
        '2_primaria': (7, 8), '2º Primaria': (7, 8),
        '3_primaria': (8, 9), '3º Primaria': (8, 9),
        '4_primaria': (9, 10), '4º Primaria': (9, 10),
        '5_primaria': (10, 11), '5º Primaria': (10, 11),
        '6_primaria': (11, 12), '6º Primaria': (11, 12)
    }
    
    # Agrupar por curso
    por_curso = defaultdict(list)
    for perfil in perfiles:
        curso = perfil.get('identificacion', {}).get('curso')
        edad = perfil.get('identificacion', {}).get('edad')
        if curso and edad:
            por_curso[curso].append(edad)
    
    print("📚 COHERENCIA POR CURSO:")
    
    total_incoherentes = 0
    cursos_problematicos = []
    
    for curso, edades in por_curso.items():
        rango_esperado = rangos_esperados.get(curso, (0, 20))
        edades_incoherentes = [e for e in edades if not (rango_esperado[0] <= e <= rango_esperado[1])]
        
        print(f"  {curso}: {len(edades)} estudiantes")
        print(f"    Edades: {min(edades)}-{max(edades)} (esperado: {rango_esperado[0]}-{rango_esperado[1]})")
        
        if edades_incoherentes:
            print(f"    ❌ {len(edades_incoherentes)} edades incoherentes: {sorted(set(edades_incoherentes))}")
            total_incoherentes += len(edades_incoherentes)
            cursos_problematicos.append(curso)
        else:
            print(f"    ✅ Todas las edades coherentes")
        print()
    
    if total_incoherentes > 0:
        problemas.append({
            'tipo': 'incoherencia_edad_curso',
            'descripcion': f'Estudiantes con edad incoherente para su curso',
            'detalles': cursos_problematicos,
            'severidad': 'alta',
            'afecta_perfiles': total_incoherentes
        })
    
    return problemas

def auditoria_tipos_estudiantes(perfiles):
    """Audita distribución de tipos de estudiantes"""
    print(f"\n🎯 AUDITORÍA TIPOS DE ESTUDIANTES")
    print("=" * 50)
    
    problemas = []
    
    # Inferir tipos desde fuente_datos
    tipos_reales = defaultdict(int)
    tipos_declarados = defaultdict(int)
    
    for perfil in perfiles:
        # Tipo declarado
        tipo_declarado = perfil.get('identificacion', {}).get('tipo_estudiante')
        if tipo_declarado:
            tipos_declarados[tipo_declarado] += 1
        
        # Tipo inferido desde fuente
        fuente = perfil.get('metadatos', {}).get('fuente_datos', '')
        
        if 'adhd' in fuente.lower() or 'ADHD' in fuente:
            tipos_reales['adhd'] += 1
        elif 'altas_capacidades' in fuente.lower() or 'osf' in fuente.lower():
            tipos_reales['altas_capacidades'] += 1
        elif '2e' in fuente.lower() or 'doble' in fuente.lower():
            tipos_reales['doble_excepcionalidad'] += 1
        elif 'ayez' in fuente.lower():
            tipos_reales['tipico'] += 1
        else:
            tipos_reales['desconocido'] += 1
    
    print("🏷️  TIPOS DECLARADOS:")
    total_declarados = sum(tipos_declarados.values())
    for tipo, cantidad in tipos_declarados.items():
        porcentaje = (cantidad / len(perfiles)) * 100
        print(f"  {tipo}: {cantidad} ({porcentaje:.1f}%)")
    
    print(f"\n🔍 TIPOS INFERIDOS DESDE FUENTE:")
    for tipo, cantidad in tipos_reales.items():
        porcentaje = (cantidad / len(perfiles)) * 100
        print(f"  {tipo}: {cantidad} ({porcentaje:.1f}%)")
    
    # Detectar problemas de distribución
    porcentajes_reales = {tipo: (cantidad / len(perfiles)) * 100 for tipo, cantidad in tipos_reales.items()}
    
    # Rangos esperados en aulas reales
    rangos_esperados = {
        'tipico': (75, 90),
        'adhd': (3, 8),
        'altas_capacidades': (2, 5),
        'doble_excepcionalidad': (0.5, 2)
    }
    
    print(f"\n⚖️  EVALUACIÓN VS RANGOS REALES:")
    tipos_problematicos = []
    
    for tipo, (min_esp, max_esp) in rangos_esperados.items():
        porcentaje_actual = porcentajes_reales.get(tipo, 0)
        
        if porcentaje_actual < min_esp or porcentaje_actual > max_esp:
            print(f"  ❌ {tipo}: {porcentaje_actual:.1f}% (esperado: {min_esp}-{max_esp}%)")
            tipos_problematicos.append(tipo)
        else:
            print(f"  ✅ {tipo}: {porcentaje_actual:.1f}% (dentro de rango)")
    
    if tipos_problematicos:
        problemas.append({
            'tipo': 'distribucion_tipos_irreal',
            'descripcion': f'Distribución de tipos no realista',
            'detalles': {tipo: porcentajes_reales.get(tipo, 0) for tipo in tipos_problematicos},
            'severidad': 'alta',
            'afecta_perfiles': len(perfiles)  # Afecta la validez de todo el dataset
        })
    
    return problemas

def auditoria_campos_innecesarios(perfiles):
    """Audita campos que se pueden eliminar"""
    print(f"\n🗑️ AUDITORÍA CAMPOS INNECESARIOS")
    print("=" * 50)
    
    problemas = []
    
    # Campos que aparecen siempre con el mismo valor
    campos_constantes = {}
    campos_siempre_null = {}
    
    # Analizar metadatos
    if perfiles:
        primer_perfil = perfiles[0]
        
        # Revisar campos en metadatos
        for campo in primer_perfil.get('metadatos', {}):
            valores = set()
            nulos = 0
            
            for perfil in perfiles:
                valor = perfil.get('metadatos', {}).get(campo)
                if valor is None:
                    nulos += 1
                else:
                    valores.add(str(valor))
            
            if nulos == len(perfiles):
                campos_siempre_null[f'metadatos.{campo}'] = nulos
            elif len(valores) == 1:
                campos_constantes[f'metadatos.{campo}'] = list(valores)[0]
    
    print("🔄 CAMPOS SIEMPRE CONSTANTES (candidatos a eliminar):")
    for campo, valor in campos_constantes.items():
        print(f"  ❌ {campo}: siempre '{valor}'")
    
    print(f"\n❌ CAMPOS SIEMPRE NULL (candidatos a eliminar):")
    for campo, cantidad in campos_siempre_null.items():
        print(f"  ❌ {campo}: NULL en {cantidad} casos")
    
    if campos_constantes or campos_siempre_null:
        problemas.append({
            'tipo': 'campos_innecesarios',
            'descripcion': f'Campos constantes o siempre null',
            'detalles': {
                'constantes': list(campos_constantes.keys()),
                'siempre_null': list(campos_siempre_null.keys())
            },
            'severidad': 'baja',
            'afecta_perfiles': 0  # No afecta funcionalmente
        })
    
    return problemas

def generar_resumen_auditoria(todos_problemas, total_perfiles):
    """Genera resumen ejecutivo de la auditoría"""
    print(f"\n" + "=" * 70)
    print("📋 RESUMEN EJECUTIVO DE AUDITORÍA")
    print("=" * 70)
    
    # Clasificar por severidad
    alta_severidad = [p for p in todos_problemas if p['severidad'] == 'alta']
    media_severidad = [p for p in todos_problemas if p['severidad'] == 'media']
    baja_severidad = [p for p in todos_problemas if p['severidad'] == 'baja']
    
    print(f"📊 TOTAL PERFILES ANALIZADOS: {total_perfiles}")
    print(f"🚨 PROBLEMAS ENCONTRADOS: {len(todos_problemas)}")
    print()
    
    print(f"🔥 SEVERIDAD ALTA ({len(alta_severidad)} problemas):")
    for problema in alta_severidad:
        print(f"  ❌ {problema['descripcion']} - Afecta {problema['afecta_perfiles']} perfiles")
    print()
    
    print(f"⚠️  SEVERIDAD MEDIA ({len(media_severidad)} problemas):")
    for problema in media_severidad:
        print(f"  ⚠️  {problema['descripcion']} - Afecta {problema['afecta_perfiles']} perfiles")
    print()
    
    print(f"ℹ️  SEVERIDAD BAJA ({len(baja_severidad)} problemas):")
    for problema in baja_severidad:
        print(f"  ℹ️  {problema['descripcion']}")
    print()
    
    # Priorización de correcciones
    print("🎯 PRIORIDAD DE CORRECCIÓN:")
    print("1. 🔥 ALTA: Corregir inmediatamente (afectan funcionamiento)")
    for problema in alta_severidad:
        print(f"   - {problema['tipo']}")
    
    if media_severidad:
        print("2. ⚠️  MEDIA: Corregir antes de producción")
        for problema in media_severidad:
            print(f"   - {problema['tipo']}")
    
    if baja_severidad:
        print("3. ℹ️  BAJA: Opcional (limpieza)")
        for problema in baja_severidad:
            print(f"   - {problema['tipo']}")
    
    return {
        'total_problemas': len(todos_problemas),
        'alta_severidad': len(alta_severidad),
        'media_severidad': len(media_severidad),
        'baja_severidad': len(baja_severidad),
        'problemas': todos_problemas
    }

def main():
    """Función principal de auditoría"""
    print("🔍 AUDITORÍA COMPLETA DEL DATASET UNIFICADO")
    print("=" * 70)
    
    # Cargar dataset
    data = cargar_dataset()
    if not data:
        return
    
    perfiles = data.get('perfiles', [])
    print(f"📊 Dataset cargado: {len(perfiles)} perfiles")
    print()
    
    # Ejecutar auditorías
    todos_problemas = []
    
    # 1. Auditoría de formatos
    problemas_formato = auditoria_formatos(perfiles)
    todos_problemas.extend(problemas_formato)
    
    # 2. Auditoría de rangos
    problemas_rangos = auditoria_rangos(perfiles)
    todos_problemas.extend(problemas_rangos)
    
    # 3. Auditoría coherencia edad-curso
    problemas_coherencia = auditoria_coherencia_edad_curso(perfiles)
    todos_problemas.extend(problemas_coherencia)
    
    # 4. Auditoría tipos de estudiantes
    problemas_tipos = auditoria_tipos_estudiantes(perfiles)
    todos_problemas.extend(problemas_tipos)
    
    # 5. Auditoría campos innecesarios
    problemas_campos = auditoria_campos_innecesarios(perfiles)
    todos_problemas.extend(problemas_campos)
    
    # Generar resumen ejecutivo
    resumen = generar_resumen_auditoria(todos_problemas, len(perfiles))
    
    # Guardar reporte detallado
    reporte = {
        'fecha_auditoria': '2025-07-12',
        'total_perfiles': len(perfiles),
        'resumen': resumen,
        'problemas_detallados': todos_problemas
    }
    
    with open('data/processed/auditoria_dataset_reporte.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Reporte detallado guardado en: data/processed/auditoria_dataset_reporte.json")

if __name__ == "__main__":
    main()