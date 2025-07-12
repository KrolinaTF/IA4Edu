import pandas as pd
import json
import numpy as np
from pathlib import Path
import random
from datetime import datetime

def load_adhd_dataset():
    """Cargar el dataset ADHD"""
    df = pd.read_csv('data/raw/ADHD_para_uso_no_comercial.csv')
    print(f"Dataset ADHD cargado: {len(df)} casos")
    return df

def filtrar_primaria(df):
    """Filtrar solo casos de edad de Primaria (6-12 años)"""
    df_primaria = df[(df['Age'] >= 6) & (df['Age'] <= 12)]
    print(f"Casos en edad de Primaria: {len(df_primaria)}")
    return df_primaria

def calcular_curso(edad):
    """Calcular curso aproximado según edad"""
    if edad < 7:
        return "1º Primaria"
    elif edad < 8:
        return "2º Primaria"  
    elif edad < 9:
        return "3º Primaria"
    elif edad < 10:
        return "4º Primaria"
    elif edad < 11:
        return "5º Primaria"
    else:
        return "6º Primaria"

def interpretar_diagnostico(dx):
    """Interpretar código de diagnóstico"""
    dx_map = {
        '0': None,  # Control
        '1': 'TDAH_inatento', 
        '2': 'TDAH_hiperactivo', 
        '3': 'TDAH_combinado'
    }
    return dx_map.get(str(dx), None)

def convertir_escala_atencion(valor):
    """Convertir escalas ADHD (10-90) a escala pedagógica (1-5)"""
    if pd.isna(valor) or str(valor) in ['-999', 'pending']:
        return None
    
    try:
        val = float(valor)
        if val <= 25:
            return 5  # Muy buena
        elif val <= 35:
            return 4  # Buena  
        elif val <= 50:
            return 3  # Media
        elif val <= 70:
            return 2  # Dificultades
        else:
            return 1  # Muchas dificultades
    except:
        return None

def generar_perfil_academico_sintetico(caso):
    """Generar perfil académico basado en CI y perfil ADHD"""
    ci_verbal = caso.get('Verbal IQ')
    ci_total = caso.get('Full4 IQ') 
    dx = str(caso.get('DX', '0'))
    
    # Base según CI
    if pd.notna(ci_verbal):
        if ci_verbal >= 120:
            base_academico = 4  # Alto
        elif ci_verbal >= 110:
            base_academico = 3  # Medio-alto
        elif ci_verbal >= 90:
            base_academico = 3  # Medio
        else:
            base_academico = 2  # Bajo
    else:
        base_academico = 3  # Default medio
    
    # Ajustes según perfil ADHD
    ajuste_atencion = 0
    if dx in ['1', '2', '3']:  # Tiene ADHD
        ajuste_atencion = -1  # Más dificultades en tareas que requieren atención
    
    return {
        "matematicas": max(1, min(5, base_academico + random.choice([-1, 0, 1]))),
        "lectura": max(1, min(5, base_academico + ajuste_atencion + random.choice([-1, 0, 1]))),
        "escritura": max(1, min(5, base_academico + ajuste_atencion + random.choice([-1, 0, 1]))),
        "ciencias": max(1, min(5, base_academico + random.choice([-1, 0, 1]))),
        "fortalezas_observadas": generar_fortalezas_sinteticas(caso),
        "dificultades_observadas": generar_dificultades_sinteticas(caso)
    }

def generar_fortalezas_sinteticas(caso):
    """Generar fortalezas basadas en perfil real"""
    ci_verbal = caso.get('Verbal IQ', 100)
    ci_total = caso.get('Full4 IQ', 100)
    dx = str(caso.get('DX', '0'))
    
    fortalezas = []
    
    # Basado en CI alto
    if ci_verbal >= 120:
        fortalezas.extend(["comprension_verbal", "vocabulario_rico"])
    if ci_total >= 120:
        fortalezas.extend(["razonamiento_logico", "resolucion_problemas"])
    
    # Fortalezas típicas ADHD (creatividad, energía)
    if dx in ['2', '3']:  # ADHD con componente hiperactivo
        fortalezas.extend(["creatividad", "energia_alta", "pensamiento_divergente"])
    
    # Control (sin ADHD) - fortalezas más académicas
    if dx == '0':
        fortalezas.extend(["atencion_sostenida", "organizacion"])
    
    return fortalezas[:4]  # Máximo 4 fortalezas

def generar_dificultades_sinteticas(caso):
    """Generar dificultades basadas en perfil real"""
    dx = str(caso.get('DX', '0'))
    inattentive = caso.get('Inattentive')
    hyperactive = caso.get('Hyper/Impulsive')
    
    dificultades = []
    
    # Basado en escalas ADHD reales
    if inattentive and str(inattentive) not in ['-999', 'pending']:
        if float(inattentive) > 50:
            dificultades.extend(["atencion_sostenida", "organizacion", "seguimiento_instrucciones"])
    
    if hyperactive and str(hyperactive) not in ['-999', 'pending']:
        if float(hyperactive) > 50:
            dificultades.extend(["control_impulsos", "permanecer_sentado", "esperar_turno"])
    
    # Si no hay ADHD, dificultades más leves
    if dx == '0':
        dificultades = random.sample(["velocidad_procesamiento", "memoria_trabajo"], 1)
    
    return dificultades[:3]  # Máximo 3 dificultades

def generar_perfil_conductual_sintetico(caso):
    """Generar perfil conductual basado en diagnóstico"""
    dx = str(caso.get('DX', '0'))
    hyperactive = caso.get('Hyper/Impulsive')
    
    # Regulación emocional
    if dx in ['1', '2', '3']:  # ADHD
        regulacion = random.choice([2, 3])  # Más dificultades
        tolerancia = random.choice([2, 3])
    else:
        regulacion = random.choice([3, 4])  # Mejor regulación
        tolerancia = random.choice([3, 4])
    
    # Impulsividad basada en escalas reales
    if hyperactive and str(hyperactive) not in ['-999', 'pending']:
        if float(hyperactive) > 50:
            impulsividad = random.choice([4, 5])  # Alta
        else:
            impulsividad = random.choice([2, 3])  # Media
    else:
        impulsividad = random.choice([1, 2])  # Baja
    
    return {
        "regulacion_emocional": regulacion,
        "tolerancia_frustracion": tolerancia,
        "habilidades_sociales": random.choice([3, 4]),  # Neutral-bueno
        "impulsividad": impulsividad,
        "nivel_actividad": 4 if dx in ['2', '3'] else random.choice([2, 3]),
        "triggers": generar_triggers_sinteticos(dx),
        "motivadores": generar_motivadores_sinteticos(dx)
    }

def generar_triggers_sinteticos(dx):
    """Generar triggers típicos según perfil"""
    if dx in ['1', '2', '3']:  # ADHD
        return random.sample([
            "critica_publica", "tareas_largas", "cambios_rutina", 
            "sobrecarga_sensorial", "esperar_mucho_tiempo"
        ], 3)
    else:
        return random.sample([
            "critica_publica", "cambios_rutina", "presion_tiempo"
        ], 2)

def generar_motivadores_sinteticos(dx):
    """Generar motivadores típicos según perfil"""
    if dx in ['1', '2', '3']:  # ADHD
        return random.sample([
            "novedad", "movimiento", "reconocimiento_inmediato", 
            "competicion", "variedad"
        ], 3)
    else:
        return random.sample([
            "reconocimiento", "autonomia", "logro_personal", "colaboracion"
        ], 3)

def generar_estilo_aprendizaje_sintetico(caso):
    """Generar estilo de aprendizaje basado en perfil"""
    dx = str(caso.get('DX', '0'))
    
    # Canal preferido según perfil típico
    if dx in ['2', '3']:  # ADHD hiperactivo
        canal = "kinestesico"
    elif dx == '1':  # ADHD inatento
        canal = random.choice(["visual", "auditivo"])
    else:
        canal = random.choice(["visual", "auditivo", "mixto"])
    
    return {
        "canal_preferido": canal,
        "ritmo_preferido": "rapido" if dx in ['2', '3'] else random.choice(["medio", "rapido"]),
        "agrupamiento_optimo": random.choice(["pequeño_grupo", "pareja"]),
        "estructura_necesaria": 4 if dx == '1' else random.choice([2, 3]),
        "necesita_movimiento": dx in ['2', '3'],
        "sensible_ruido": random.choice([True, False]),
        "aprende_mejor_con": generar_estrategias_aprendizaje(dx)
    }

def generar_estrategias_aprendizaje(dx):
    """Generar estrategias que funcionan según perfil"""
    if dx in ['1', '2', '3']:  # ADHD
        return random.sample([
            "instrucciones_cortas", "pausas_frecuentes", "ejemplos_concretos",
            "feedback_inmediato", "variedad_actividades"
        ], 3)
    else:
        return random.sample([
            "explicaciones_detalladas", "tiempo_reflexion", "ejemplos_visuales"
        ], 2)

def mapear_caso_completo(caso):
    """Mapear un caso del dataset al JSON Goldilocks completo"""
    
    edad = float(caso['Age'])
    dx = interpretar_diagnostico(caso['DX'])
    
    # Medicación
    med_map = {'1': False, '2': True}
    medicacion = med_map.get(str(caso.get('Med Status')), None)
    
    perfil = {
        "identificacion": {
            "edad": int(edad),
            "curso": calcular_curso(edad),
            "genero": "M" if int(caso['Gender']) == 0 else "F",
            "diagnostico_oficial": dx
        },
        
        "perfil_academico": generar_perfil_academico_sintetico(caso),
        
        "perfil_cognitivo": {
            "atencion_sostenida": convertir_escala_atencion(caso.get('Inattentive')),
            "atencion_selectiva": convertir_escala_atencion(caso.get('Inattentive')),  # Similar
            "memoria_trabajo": max(1, min(5, int(caso.get('Full4 IQ', 100)) // 20)) if pd.notna(caso.get('Full4 IQ')) else None,
            "velocidad_procesamiento": convertir_escala_atencion(caso.get('ADHD Index')),
            "control_inhibitorio": convertir_escala_atencion(caso.get('Hyper/Impulsive')),
            "flexibilidad_cognitiva": random.choice([2, 3, 4]) if dx else random.choice([3, 4]),
            "ci_estimado": int(caso['Full4 IQ']) if pd.notna(caso['Full4 IQ']) else None,
            "variabilidad_rendimiento": 4 if dx in ['TDAH_combinado', 'TDAH_hiperactivo'] else random.choice([1, 2, 3])
        },
        
        "perfil_conductual": generar_perfil_conductual_sintetico(caso),
        
        "estilo_aprendizaje": generar_estilo_aprendizaje_sintetico(caso),
        
        "adaptaciones": {
            "metodologicas": generar_estrategias_aprendizaje(str(caso.get('DX', '0'))),
            "organizativas": ["ubicacion_preferente"] if dx else [],
            "evaluativas": ["tiempo_extra"] if dx else [],
            "efectividad_reportada": {}  # Vacío - solo feedback real profesor
        },
        
        "contexto": {
            "nivel_apoyo_familiar": None,  # Imposible sintetizar
            "nivel_socioeconomico": None,  # Imposible sintetizar  
            "idioma_casa": "castellano",   # Asumimos por defecto
            "factores_estres": [],        # Solo datos reales
            "medicacion": medicacion,
            "servicios_apoyo": ["ninguno"] if not dx else ["orientador"]
        },
        
        "observaciones_libres": {
            "descripcion_general": None,     # Solo profesor real
            "estrategias_funcionan": None,   # Solo feedback real
            "estrategias_no_funcionan": None,
            "notas_profesor": None
        },
        
        "metadatos": {
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "fuente_datos": "dataset_ADHD",
            "caso_id": str(caso.get('ID')),
            "confianza_perfil": 0.7,  # Media - mix real/sintético
            "campos_imputados": [
                "perfil_academico", "perfil_conductual", 
                "estilo_aprendizaje", "adaptaciones"
            ],
            "requiere_validacion": True
        }
    }
    
    return perfil

def procesar_dataset_completo():
    """Procesar todo el dataset y guardar perfiles"""
    df = load_adhd_dataset()
    df_primaria = filtrar_primaria(df)
    
    perfiles_generados = []
    
    print("\nGenerando perfiles...")
    for i, (idx, caso) in enumerate(df_primaria.iterrows()):
        try:
            perfil = mapear_caso_completo(caso)
            perfiles_generados.append(perfil)
            
            if (i + 1) % 20 == 0:
                print(f"Procesados {i + 1}/{len(df_primaria)} casos")
                
        except Exception as e:
            print(f"Error en caso {idx}: {e}")
            continue
    
    # Crear directorio si no existe
    Path('data/processed').mkdir(exist_ok=True)
    
    # Guardar archivo con todos los perfiles
    output_file = 'data/processed/perfiles_adhd_primaria.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(perfiles_generados, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(perfiles_generados)} perfiles guardados en {output_file}")
    
    return perfiles_generados

if __name__ == "__main__":
    # Procesar dataset completo
    perfiles = procesar_dataset_completo()
    
    # Mostrar ejemplo del primer perfil
    print("\n=== EJEMPLO PERFIL GENERADO ===")
    print(json.dumps(perfiles[0], indent=2, ensure_ascii=False))