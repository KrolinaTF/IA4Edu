#!/usr/bin/env python3
"""
Corrector de Edades Incoherentes - ProyectIA
Corrige edades incoherentes creando repetidores y adelantados realistas
"""

import json
import random
import os

def identificar_casos_incoherentes(perfiles):
    """Identifica casos con edades incoherentes para su curso"""
    
    # Rangos esperados por curso
    rangos_esperados = {
        '1_primaria': (6, 7),
        '2_primaria': (7, 8), 
        '3_primaria': (8, 9),
        '4_primaria': (9, 10),
        '5_primaria': (10, 11),
        '6_primaria': (11, 12)
    }
    
    casos_incoherentes = []
    
    for i, perfil in enumerate(perfiles):
        edad = perfil.get('identificacion', {}).get('edad')
        curso = perfil.get('identificacion', {}).get('curso')
        
        if edad and curso and curso in rangos_esperados:
            rango_min, rango_max = rangos_esperados[curso]
            
            if not (rango_min <= edad <= rango_max):
                # Calcular desviación
                if edad < rango_min:
                    desviacion = rango_min - edad
                    tipo_problema = 'adelantado'
                else:
                    desviacion = edad - rango_max
                    tipo_problema = 'repetidor'
                
                casos_incoherentes.append({
                    'indice': i,
                    'perfil': perfil,
                    'edad': edad,
                    'curso': curso,
                    'tipo_problema': tipo_problema,
                    'desviacion': desviacion
                })
    
    return casos_incoherentes

def evaluar_si_justifica_excepcion(perfil, tipo_problema):
    """Evalúa si un perfil justifica ser excepción (repetidor/adelantado)"""
    
    ci = perfil.get('perfil_cognitivo', {}).get('ci_estimado', 100)
    matematicas = perfil.get('perfil_academico', {}).get('matematicas', 3)
    lectura = perfil.get('perfil_academico', {}).get('lectura', 3)
    escritura = perfil.get('perfil_academico', {}).get('escritura', 3)
    
    rendimiento_promedio = (matematicas + lectura + escritura) / 3
    
    fuente = perfil.get('metadatos', {}).get('fuente_datos', '')
    
    # Criterios para adelantado (AC excepcional)
    if tipo_problema == 'adelantado':
        justifica = (
            ci >= 135 and  # CI muy alto
            rendimiento_promedio >= 4.0 and  # Rendimiento excelente
            ('altas_capacidades' in fuente.lower() or 'osf' in fuente.lower() or '2e' in fuente.lower())
        )
        return justifica, "AC_excepcional"
    
    # Criterios para repetidor
    elif tipo_problema == 'repetidor':
        # ADHD con bajo rendimiento
        if 'adhd' in fuente.lower() and rendimiento_promedio <= 2.5:
            return True, "ADHD_bajo_rendimiento"
        
        # Típico con dificultades
        elif rendimiento_promedio <= 2.0:
            return True, "dificultades_aprendizaje"
        
        # Otros casos
        elif ci <= 85:
            return True, "capacidad_limitada"
    
    return False, "sin_justificacion"

def reasignar_edad_coherente(perfil, curso_objetivo=None):
    """Reasigna edad coherente para el perfil"""
    
    # Rangos por curso
    rangos_coherentes = {
        '1_primaria': [6, 7],
        '2_primaria': [7, 8], 
        '3_primaria': [8, 9],
        '4_primaria': [9, 10],
        '5_primaria': [10, 11],
        '6_primaria': [11, 12]
    }
    
    curso_actual = perfil.get('identificacion', {}).get('curso')
    curso_para_edad = curso_objetivo or curso_actual
    
    if curso_para_edad in rangos_coherentes:
        # Elegir edad aleatoria dentro del rango
        edades_posibles = rangos_coherentes[curso_para_edad]
        nueva_edad = random.choice(edades_posibles)
        return nueva_edad
    
    return perfil.get('identificacion', {}).get('edad')  # Mantener original si no se puede corregir

def encontrar_curso_apropiado_para_edad(edad):
    """Encuentra el curso más apropiado para una edad dada"""
    
    cursos_por_edad = {
        6: '1_primaria',
        7: ['1_primaria', '2_primaria'],  # Puede estar en cualquiera
        8: ['2_primaria', '3_primaria'],
        9: ['3_primaria', '4_primaria'],
        10: ['4_primaria', '5_primaria'],
        11: ['5_primaria', '6_primaria'],
        12: '6_primaria'
    }
    
    opciones = cursos_por_edad.get(edad, [])
    
    if isinstance(opciones, list):
        return random.choice(opciones)  # Elegir aleatoriamente si hay opciones
    else:
        return opciones  # Curso único

def corregir_edades_incoherentes():
    """Función principal para corregir edades incoherentes"""
    
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
    
    # Identificar casos incoherentes
    print(f"\n🔍 IDENTIFICANDO CASOS INCOHERENTES...")
    casos_incoherentes = identificar_casos_incoherentes(perfiles)
    
    print(f"📊 Casos incoherentes encontrados: {len(casos_incoherentes)}")
    
    if not casos_incoherentes:
        print("✅ No hay casos incoherentes para corregir")
        return True
    
    # Mostrar casos encontrados
    print(f"\n📋 CASOS IDENTIFICADOS:")
    for caso in casos_incoherentes:
        print(f"  Perfil {caso['indice']}: {caso['edad']} años en {caso['curso']} ({caso['tipo_problema']}, desviación: {caso['desviacion']})")
    
    # Fijar semilla para reproducibilidad
    random.seed(42)
    
    # Procesar casos
    print(f"\n🔧 PROCESANDO CORRECCIONES...")
    
    excepciones_mantenidas = 0
    edades_corregidas = 0
    cursos_reasignados = 0
    
    for caso in casos_incoherentes:
        perfil = caso['perfil']
        indice = caso['indice']
        
        # Evaluar si justifica ser excepción
        justifica, razon = evaluar_si_justifica_excepcion(perfil, caso['tipo_problema'])
        
        if justifica and caso['desviacion'] <= 2:  # Solo excepciones menores (máximo 2 años)
            # Mantener como excepción
            print(f"  ✅ Perfil {indice}: Mantenido como {caso['tipo_problema']} ({razon})")
            excepciones_mantenidas += 1
            
            # Ajustar diagnóstico para reflejar la situación
            if caso['tipo_problema'] == 'adelantado':
                perfil['identificacion']['diagnostico_oficial'] = f"{perfil.get('identificacion', {}).get('diagnostico_oficial', 'altas_capacidades')}_aceleracion_curricular"
            elif caso['tipo_problema'] == 'repetidor':
                diagnostico_actual = perfil.get('identificacion', {}).get('diagnostico_oficial')
                if diagnostico_actual:
                    perfil['identificacion']['diagnostico_oficial'] = f"{diagnostico_actual}_repetidor"
                else:
                    perfil['identificacion']['diagnostico_oficial'] = f"{razon}_repetidor"
            
        else:
            # Corregir la incoherencia
            if caso['desviacion'] <= 1:
                # Desviación pequeña: corregir edad
                nueva_edad = reasignar_edad_coherente(perfil)
                perfil['identificacion']['edad'] = nueva_edad
                print(f"  🔧 Perfil {indice}: Edad corregida {caso['edad']} → {nueva_edad}")
                edades_corregidas += 1
            else:
                # Desviación grande: reasignar curso
                nuevo_curso = encontrar_curso_apropiado_para_edad(caso['edad'])
                perfil['identificacion']['curso'] = nuevo_curso
                print(f"  📚 Perfil {indice}: Curso reasignado {caso['curso']} → {nuevo_curso}")
                cursos_reasignados += 1
    
    print(f"\n📊 RESUMEN DE CORRECCIONES:")
    print(f"  - Excepciones mantenidas: {excepciones_mantenidas}")
    print(f"  - Edades corregidas: {edades_corregidas}")
    print(f"  - Cursos reasignados: {cursos_reasignados}")
    print(f"  - Total procesados: {len(casos_incoherentes)}")
    
    # Verificar resultado
    print(f"\n🔍 VERIFICACIÓN POST-CORRECCIÓN...")
    casos_restantes = identificar_casos_incoherentes(perfiles)
    
    print(f"📊 Casos incoherentes restantes: {len(casos_restantes)}")
    
    if casos_restantes:
        print("⚠️ Casos que siguen siendo incoherentes (excepciones justificadas):")
        for caso in casos_restantes:
            diagnostico = caso['perfil'].get('identificacion', {}).get('diagnostico_oficial', 'sin_diagnostico')
            print(f"  Perfil {caso['indice']}: {caso['edad']} años en {caso['curso']} - {diagnostico}")
    
    # Guardar dataset corregido
    print(f"\n💾 Guardando dataset corregido...")
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Dataset guardado correctamente")
    
    return True

def main():
    """Función principal"""
    print("📅 CORRECTOR DE EDADES INCOHERENTES")
    print("Corrigiendo edades incoherentes con excepciones realistas")
    print("=" * 60)
    
    exito = corregir_edades_incoherentes()
    
    if exito:
        print(f"\n🎉 CORRECCIÓN COMPLETADA")
        print("✅ Edades incoherentes corregidas")
        print("✅ Excepciones realistas mantenidas")
        print("✅ Dataset listo para regeneración de archivos por curso")
    else:
        print(f"\n❌ ERROR EN LA CORRECCIÓN")
        print("🔧 Revisa los mensajes de error anteriores")

if __name__ == "__main__":
    main()