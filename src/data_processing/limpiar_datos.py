#!/usr/bin/env python3
"""
Limpiador Automático de Datos ProyectIA
Corrige edades, tipos de estudiantes y elimina campos innecesarios
Mantiene coherencia CI-adaptaciones
"""

import json
import os
import random
from collections import defaultdict

# Configuración de correcciones
RANGOS_EDAD_CURSO = {
    '1_primaria': (6, 7),
    '2_primaria': (7, 8), 
    '3_primaria': (8, 9),
    '4_primaria': (9, 10),
    '5_primaria': (10, 11),
    '6_primaria': (11, 12)
}

# Distribución realista de tipos de estudiantes por curso
DISTRIBUCION_TIPOS = {
    '1_primaria': {'tipico': 95, 'adhd': 2, 'altas_capacidades': 2, 'doble_excepcionalidad': 1},
    '2_primaria': {'tipico': 90, 'adhd': 4, 'altas_capacidades': 3, 'doble_excepcionalidad': 3},
    '3_primaria': {'tipico': 85, 'adhd': 6, 'altas_capacidades': 4, 'doble_excepcionalidad': 5},
    '4_primaria': {'tipico': 82, 'adhd': 8, 'altas_capacidades': 5, 'doble_excepcionalidad': 5},
    '5_primaria': {'tipico': 80, 'adhd': 8, 'altas_capacidades': 6, 'doble_excepcionalidad': 6},
    '6_primaria': {'tipico': 78, 'adhd': 8, 'altas_capacidades': 7, 'doble_excepcionalidad': 7}
}

# Campos a eliminar
CAMPOS_ELIMINAR = {
    'metadatos': ['requiere_validacion', 'tiene_estado_curricular', 'version_curriculo'],
    'contexto': ['nivel_apoyo_familiar', 'nivel_socioeconomico', 'idioma_casa', 'factores_estres']
}

def corregir_edad(perfil, curso, tipo_estudiante):
    """Corrige la edad según el curso y tipo de estudiante"""
    rango_min, rango_max = RANGOS_EDAD_CURSO[curso]
    
    # Casos especiales
    if tipo_estudiante == 'altas_capacidades' and random.random() < 0.3:
        # 30% de AC son adelantados (1 año menor)
        nueva_edad = rango_min - 1
        perfil['identificacion']['diagnostico_oficial'] = 'altas_capacidades_aceleracion_curricular'
    elif tipo_estudiante in ['adhd', 'doble_excepcionalidad'] and random.random() < 0.2:
        # 20% de ADHD/2e son repetidores (1 año mayor)
        nueva_edad = rango_max + 1
        diagnostico_base = 'TDAH_combinado' if tipo_estudiante == 'adhd' else 'doble_excepcionalidad_AC_TDAH'
        perfil['identificacion']['diagnostico_oficial'] = f"{diagnostico_base}_repetidor"
    else:
        # Edad normal para el curso
        nueva_edad = random.randint(rango_min, rango_max)
    
    # Límites absolutos de seguridad
    nueva_edad = max(5, min(13, nueva_edad))
    perfil['identificacion']['edad'] = nueva_edad
    return perfil

def asignar_tipo_estudiante(perfiles, curso):
    """Asigna tipos de estudiantes según distribución realista"""
    
    total_perfiles = len(perfiles)
    distribucion = DISTRIBUCION_TIPOS[curso]
    
    # Calcular cantidades por tipo
    cantidades = {}
    restante = total_perfiles
    
    for tipo, porcentaje in distribucion.items():
        if tipo == 'tipico':  # El típico se ajusta al final
            continue
        cantidad = max(1, round(total_perfiles * porcentaje / 100))
        cantidades[tipo] = min(cantidad, restante - 1)  # Dejar al menos 1 para típicos
        restante -= cantidades[tipo]
    
    cantidades['tipico'] = restante
    
    # Asignar tipos aleatoriamente
    indices = list(range(total_perfiles))
    random.shuffle(indices)
    
    idx = 0
    for tipo, cantidad in cantidades.items():
        for _ in range(cantidad):
            if idx < len(indices):
                perfil = perfiles[indices[idx]]
                perfil['_tipo_asignado'] = tipo
                idx += 1
    
    return cantidades

def ajustar_perfil_segun_tipo(perfil, tipo):
    """Ajusta el perfil según el tipo de estudiante"""
    
    if tipo == 'tipico':
        perfil['identificacion']['diagnostico_oficial'] = None
        # Mantener CI en rango típico
        if perfil['perfil_cognitivo']['ci_estimado'] > 125:
            perfil['perfil_cognitivo']['ci_estimado'] = random.randint(90, 115)
    
    elif tipo == 'adhd':
        perfil['identificacion']['diagnostico_oficial'] = random.choice([
            'TDAH_combinado', 'TDAH_inatento', 'TDAH_hiperactivo_impulsivo'
        ])
        # Ajustar perfil cognitivo para ADHD
        perfil['perfil_cognitivo']['atencion_sostenida'] = random.randint(1, 3)
        perfil['perfil_cognitivo']['control_inhibitorio'] = random.randint(1, 3)
        perfil['perfil_cognitivo']['variabilidad_rendimiento'] = random.randint(3, 5)
        
        # Ajustar perfil conductual
        perfil['perfil_conductual']['impulsividad'] = random.randint(3, 5)
        perfil['perfil_conductual']['nivel_actividad'] = random.randint(3, 5)
        
        # Añadir dificultades típicas
        dificultades = perfil['perfil_academico'].get('dificultades_observadas', [])
        dificultades_adhd = ['atencion_sostenida', 'organizacion', 'seguir_instrucciones']
        for dif in dificultades_adhd:
            if dif not in dificultades:
                dificultades.append(dif)
        perfil['perfil_academico']['dificultades_observadas'] = dificultades[:3]  # Max 3
    
    elif tipo == 'altas_capacidades':
        perfil['identificacion']['diagnostico_oficial'] = 'altas_capacidades_identificadas'
        # CI alto para AC
        perfil['perfil_cognitivo']['ci_estimado'] = random.randint(130, 150)
        
        # Fortalezas típicas de AC
        fortalezas = perfil['perfil_academico'].get('fortalezas_observadas', [])
        fortalezas_ac = ['razonamiento_logico', 'comprension_verbal', 'creatividad', 'resolucion_problemas']
        for fort in fortalezas_ac:
            if fort not in fortalezas:
                fortalezas.append(fort)
        perfil['perfil_academico']['fortalezas_observadas'] = fortalezas[:4]  # Max 4
    
    elif tipo == 'doble_excepcionalidad':
        perfil['identificacion']['diagnostico_oficial'] = 'doble_excepcionalidad_AC_TDAH'
        # CI alto pero con dificultades ADHD
        perfil['perfil_cognitivo']['ci_estimado'] = random.randint(125, 145)
        perfil['perfil_cognitivo']['atencion_sostenida'] = random.randint(1, 3)
        perfil['perfil_cognitivo']['variabilidad_rendimiento'] = random.randint(4, 5)
        
        # Combinar fortalezas y dificultades
        fortalezas = ['razonamiento_logico', 'creatividad']
        dificultades = ['atencion_sostenida', 'organizacion']
        perfil['perfil_academico']['fortalezas_observadas'] = fortalezas
        perfil['perfil_academico']['dificultades_observadas'] = dificultades

def ajustar_coherencia_ci_adaptaciones(perfil):
    """Ajusta coherencia entre CI y adaptaciones"""
    ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado')
    
    # Si CI es None o inválido, asignar uno típico
    if ci is None or not isinstance(ci, (int, float)):
        ci = random.randint(90, 115)
        perfil['perfil_cognitivo']['ci_estimado'] = ci
    
    adaptaciones = perfil.get('adaptaciones', {})
    
    # Contar adaptaciones totales
    total_adaptaciones = sum(len(v) if isinstance(v, list) else 0 for v in adaptaciones.values())
    
    # CI muy alto con muchas adaptaciones sin justificación
    if ci >= 130 and total_adaptaciones > 6:
        diagnostico = perfil['identificacion'].get('diagnostico_oficial', '')
        if 'doble_excepcionalidad' not in diagnostico and 'discapacidad' not in diagnostico:
            # Reducir adaptaciones o añadir justificación
            if random.random() < 0.8:  # 80% reduce adaptaciones
                for categoria in adaptaciones:
                    if isinstance(adaptaciones[categoria], list) and len(adaptaciones[categoria]) > 2:
                        adaptaciones[categoria] = adaptaciones[categoria][:2]
            else:  # 20% añade justificación de discapacidad física
                perfil['identificacion']['diagnostico_oficial'] = 'altas_capacidades_discapacidad_motora'
    
    # CI bajo sin suficientes adaptaciones
    elif ci < 85 and total_adaptaciones < 2:
        # Añadir adaptaciones básicas
        if 'metodologicas' not in adaptaciones:
            adaptaciones['metodologicas'] = []
        adaptaciones['metodologicas'].extend(['explicaciones_detalladas', 'tiempo_extra'])
        adaptaciones['metodologicas'] = list(set(adaptaciones['metodologicas']))[:3]

def eliminar_campos_innecesarios(perfil):
    """Elimina campos innecesarios del perfil"""
    
    # Eliminar de metadatos
    metadatos = perfil.get('metadatos', {})
    for campo in CAMPOS_ELIMINAR['metadatos']:
        metadatos.pop(campo, None)
    
    # Eliminar de contexto
    contexto = perfil.get('contexto', {})
    for campo in CAMPOS_ELIMINAR['contexto']:
        contexto.pop(campo, None)
    
    # Eliminar campo temporal
    perfil.pop('_tipo_asignado', None)

def procesar_archivo_curso(archivo_path):
    """Procesa un archivo de curso completo"""
    
    print(f"\n🔄 Procesando: {os.path.basename(archivo_path)}")
    
    # Cargar archivo
    with open(archivo_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    curso = data['metadata']['curso']
    perfiles = data['perfiles']
    
    print(f"   📊 {len(perfiles)} perfiles en {curso}")
    
    # 1. Asignar tipos de estudiantes
    cantidades_tipos = asignar_tipo_estudiante(perfiles, curso)
    print(f"   🎯 Tipos asignados: {cantidades_tipos}")
    
    # 2. Procesar cada perfil
    for perfil in perfiles:
        tipo_asignado = perfil.get('_tipo_asignado', 'tipico')
        
        # Corregir edad según tipo
        corregir_edad(perfil, curso, tipo_asignado)
        
        # Ajustar perfil según tipo
        ajustar_perfil_segun_tipo(perfil, tipo_asignado)
        
        # Ajustar coherencia CI-adaptaciones
        ajustar_coherencia_ci_adaptaciones(perfil)
        
        # Eliminar campos innecesarios
        eliminar_campos_innecesarios(perfil)
    
    # 3. Actualizar metadatos
    data['metadata']['distribucion_tipos'] = cantidades_tipos
    
    # 4. Guardar archivo corregido
    with open(archivo_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ {os.path.basename(archivo_path)} corregido")
    
    return cantidades_tipos

def main():
    """Función principal"""
    print("🧹 LIMPIADOR AUTOMÁTICO DE DATOS PROYECTIA")
    print("=" * 60)
    
    # Buscar archivos por curso
    curso_dir = 'data/processed/por_curso/'
    archivos = []
    
    for archivo in os.listdir(curso_dir):
        if archivo.endswith('.json') and 'perfiles_' in archivo:
            archivos.append(os.path.join(curso_dir, archivo))
    
    archivos.sort()
    
    print(f"📁 Encontrados {len(archivos)} archivos para procesar")
    
    # Procesar cada archivo
    resumen_total = defaultdict(int)
    
    for archivo_path in archivos:
        try:
            cantidades = procesar_archivo_curso(archivo_path)
            
            # Acumular estadísticas
            for tipo, cantidad in cantidades.items():
                resumen_total[tipo] += cantidad
                
        except Exception as e:
            print(f"❌ Error procesando {archivo_path}: {e}")
    
    # Resumen final
    print(f"\n📋 RESUMEN FINAL:")
    print("=" * 40)
    total_perfiles = sum(resumen_total.values())
    print(f"Total perfiles procesados: {total_perfiles}")
    
    for tipo, cantidad in resumen_total.items():
        porcentaje = (cantidad / total_perfiles) * 100
        print(f"  {tipo}: {cantidad} ({porcentaje:.1f}%)")
    
    print(f"\n✅ LIMPIEZA AUTOMÁTICA COMPLETADA")
    print("🔧 Listo para ajustes manuales de casos especiales")

if __name__ == "__main__":
    # Fijar semilla para reproducibilidad durante desarrollo
    random.seed(42)
    main()