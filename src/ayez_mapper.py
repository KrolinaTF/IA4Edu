import pandas as pd
import json
from pathlib import Path

def load_ayez_dataset():
    """Cargar el dataset AYEZ"""
    df = pd.read_csv('data/raw/AYEZ_trials.csv')
    print(f"Dataset AYEZ cargado: {len(df)} trials")
    print(f"Columnas: {list(df.columns)}")
    return df

def analizar_estructura_ayez(df):
    """Analizar la estructura del dataset AYEZ"""
    print(f"\n=== ANÁLISIS ESTRUCTURA AYEZ ===")
    print(f"Total trials: {len(df)}")
    
    # Ver participantes únicos
    if 'id' in df.columns:
        participantes = df['id'].nunique()
        print(f"Participantes únicos: {participantes}")
        print(f"IDs ejemplo: {sorted([x for x in df['id'].unique() if pd.notna(x)])[:10]}")
    
    # Ver columnas disponibles
    print(f"\nColumnas disponibles:")
    for col in df.columns:
        valores_unicos = df[col].nunique()
        print(f"  {col}: {valores_unicos} valores únicos")
        
        # Mostrar ejemplos de valores (sin errores de tipo)
        try:
            valores = [x for x in df[col].unique() if pd.notna(x)]
            if len(valores) < 20:
                print(f"    Valores: {valores}")
            else:
                print(f"    Ejemplo valores: {valores[:5]}...")
        except Exception as e:
            print(f"    (Error mostrando valores: {e})")

def analizar_metricas_participante(df, participante_id):
    """Analizar métricas cognitivas de un participante"""
    data = df[df['id'] == participante_id]
    
    # Solo trials de test (no practice)
    test_trials = data[data['trial_mode'] == 'test']
    
    print(f"\n=== MÉTRICAS PARTICIPANTE {participante_id} ===")
    print(f"Trials totales: {len(data)}")
    print(f"Trials de test: {len(test_trials)}")
    
    if len(test_trials) > 0:
        # Precisión (ACC = accuracy)
        precision = test_trials['ACC'].mean()
        print(f"Precisión media: {precision:.3f}")
        
        # Tiempo de reacción (RT = reaction time)
        rt_medio = test_trials['RT'].mean()
        print(f"Tiempo reacción medio: {rt_medio:.0f}ms")
        
        # Análisis congruencia (local vs global)
        if 'congruence' in test_trials.columns:
            for cong in test_trials['congruence'].unique():
                if pd.notna(cong):
                    subset = test_trials[test_trials['congruence'] == cong]
                    precision_cong = subset['ACC'].mean()
                    rt_cong = subset['RT'].mean()
                    print(f"  {cong}: Precisión={precision_cong:.3f}, RT={rt_cong:.0f}ms")
    
    return test_trials

def calcular_metricas_cognitivas(df, participante_id):
    """Extraer métricas cognitivas relevantes para perfil educativo"""
    data = df[df['id'] == participante_id]
    test_trials = data[data['trial_mode'] == 'test']
    
    if len(test_trials) == 0:
        return None
    
    # Métricas básicas
    precision_total = test_trials['ACC'].mean()
    rt_medio = test_trials['RT'].mean()
    
    # Métricas por congruencia
    congruente = test_trials[test_trials['congruence'] == 'con']
    incongruente = test_trials[test_trials['congruence'] == 'inc']
    
    precision_con = congruente['ACC'].mean() if len(congruente) > 0 else 0
    precision_inc = incongruente['ACC'].mean() if len(incongruente) > 0 else 0
    rt_con = congruente['RT'].mean() if len(congruente) > 0 else 0
    rt_inc = incongruente['RT'].mean() if len(incongruente) > 0 else 0
    
    # Interferencia (marcador clave según abstract)
    interferencia_precision = precision_con - precision_inc
    interferencia_rt = rt_inc - rt_con
    
    # Métricas por nivel (local vs global)
    local = test_trials[test_trials['level'] == 'loc']
    global_trials = test_trials[test_trials['level'] == 'glo']
    
    precision_local = local['ACC'].mean() if len(local) > 0 else 0
    precision_global = global_trials['ACC'].mean() if len(global_trials) > 0 else 0
    sesgo_local_global = precision_local - precision_global
    
    # Variabilidad (indicador de consistencia atencional)
    variabilidad_rt = test_trials['RT'].std()
    
    return {
        'id': participante_id,
        'precision_total': precision_total,
        'rt_medio': rt_medio,
        'interferencia_precision': interferencia_precision,
        'interferencia_rt': interferencia_rt,
        'sesgo_local_global': sesgo_local_global,
        'variabilidad_rt': variabilidad_rt,
        'trials_completados': len(test_trials)
    }

def clasificar_perfil_cognitivo(metricas):
    """Clasificar perfil cognitivo basado en métricas Navon"""
    if not metricas:
        return "sin_datos"
    
    # Según el abstract: Mayor interferencia local-global en TEA/Ansiedad/TOC
    interferencia_rt = metricas['interferencia_rt']
    sesgo_local = metricas['sesgo_local_global']
    variabilidad = metricas['variabilidad_rt']
    
    # Clasificación heurística basada en literatura
    if interferencia_rt > 100:  # Alta interferencia
        if sesgo_local > 0.05:  # Ventaja local (típico TEA)
            return "perfil_detalle_TEA"
        else:
            return "perfil_interferencia_alta"
    elif interferencia_rt < 30:  # Baja interferencia
        return "perfil_flexible"
    else:
        return "perfil_tipico"

def analizar_todos_participantes(df):
    """Analizar métricas de todos los participantes"""
    participantes = df['id'].unique()
    resultados = []
    
    print(f"\nAnalizando {len(participantes)} participantes...")
    
    for i, pid in enumerate(participantes):
        if pd.notna(pid):
            metricas = calcular_metricas_cognitivas(df, pid)
            if metricas:
                perfil = clasificar_perfil_cognitivo(metricas)
                metricas['perfil_cognitivo'] = perfil
                resultados.append(metricas)
        
        if (i + 1) % 50 == 0:
            print(f"Procesados {i + 1}/{len(participantes)}")
    
    # Mostrar distribución de perfiles
    perfiles = [r['perfil_cognitivo'] for r in resultados]
    from collections import Counter
    distribucion = Counter(perfiles)
    
    print(f"\n=== DISTRIBUCIÓN PERFILES COGNITIVOS ===")
    for perfil, count in distribucion.items():
        print(f"{perfil}: {count} participantes ({count/len(resultados)*100:.1f}%)")
    
    return resultados

def mapear_ayez_a_perfil_educativo(metricas):
    """Mapear métricas cognitivas AYEZ al JSON Goldilocks"""
    
    # Generar demografía sintética para Primaria
    edad_sintetica = random.randint(7, 12)
    genero_sintetico = random.choice(["M", "F"])
    
    # Interpretación educativa de métricas cognitivas
    perfil_cog = metricas['perfil_cognitivo']
    
    # Mapear a escalas pedagógicas (1-5)
    if metricas['precision_total'] >= 0.95:
        atencion_base = 5
    elif metricas['precision_total'] >= 0.90:
        atencion_base = 4
    elif metricas['precision_total'] >= 0.80:
        atencion_base = 3
    elif metricas['precision_total'] >= 0.70:
        atencion_base = 2
    else:
        atencion_base = 1
    
    # Ajustar según perfil específico
    if perfil_cog == "perfil_detalle_TEA":
        # TEA: Muy bueno en detalles, puede tener dificultades sociales
        atencion_selectiva = min(5, atencion_base + 1)  # Muy bueno en detalles
        flexibilidad_cognitiva = max(1, atencion_base - 2)  # Rigidez cognitiva
        sensible_ruido = True
        necesita_rutinas = True
        canal_preferido = "visual"
    elif perfil_cog == "perfil_interferencia_alta":
        # Posible ansiedad/dificultades atencionales
        atencion_sostenida = max(1, atencion_base - 1)
        control_inhibitorio = max(1, atencion_base - 1) 
        regulacion_emocional = 2
        sensible_ruido = True
        canal_preferido = random.choice(["visual", "auditivo"])
    elif perfil_cog == "perfil_flexible":
        # Muy buenos procesadores
        atencion_sostenida = min(5, atencion_base + 1)
        flexibilidad_cognitiva = 5
        regulacion_emocional = 4
        sensible_ruido = False
        canal_preferido = "mixto"
    else:  # perfil_tipico
        # Perfiles normales
        atencion_sostenida = atencion_base
        flexibilidad_cognitiva = random.choice([3, 4])
        regulacion_emocional = random.choice([3, 4])
        sensible_ruido = random.choice([True, False])
        canal_preferido = random.choice(["visual", "auditivo", "kinestesico"])
    
    # Construir JSON completo
    perfil = {
        "identificacion": {
            "edad": edad_sintetica,
            "curso": calcular_curso_edad(edad_sintetica),
            "genero": genero_sintetico,
            "diagnostico_oficial": "TEA_nivel1" if perfil_cog == "perfil_detalle_TEA" else None
        },
        
        "perfil_academico": generar_academico_desde_cognitivo(metricas, perfil_cog),
        
        "perfil_cognitivo": {
            "atencion_sostenida": atencion_sostenida,
            "atencion_selectiva": min(5, atencion_base + 1) if perfil_cog == "perfil_detalle_TEA" else atencion_base,
            "memoria_trabajo": atencion_base,  # Correlación general
            "velocidad_procesamiento": convertir_rt_a_escala(metricas['rt_medio']),
            "control_inhibitorio": max(1, atencion_base - 1) if perfil_cog == "perfil_interferencia_alta" else atencion_base,
            "flexibilidad_cognitiva": locals().get('flexibilidad_cognitiva', 3),
            "ci_estimado": estimar_ci_desde_precision(metricas['precision_total']),
            "variabilidad_rendimiento": convertir_variabilidad_rt(metricas['variabilidad_rt'])
        },
        
        "perfil_conductual": {
            "regulacion_emocional": locals().get('regulacion_emocional', 3),
            "tolerancia_frustracion": 2 if perfil_cog in ["perfil_detalle_TEA", "perfil_interferencia_alta"] else random.choice([3, 4]),
            "habilidades_sociales": 2 if perfil_cog == "perfil_detalle_TEA" else random.choice([3, 4]),
            "impulsividad": random.choice([1, 2]),  # No medido en Navon
            "nivel_actividad": random.choice([2, 3, 4]),
            "triggers": generar_triggers_cognitivos(perfil_cog),
            "motivadores": generar_motivadores_cognitivos(perfil_cog)
        },
        
        "estilo_aprendizaje": {
            "canal_preferido": canal_preferido,
            "ritmo_preferido": "pausado" if perfil_cog == "perfil_detalle_TEA" else random.choice(["medio", "rapido"]),
            "agrupamiento_optimo": "individual" if perfil_cog == "perfil_detalle_TEA" else random.choice(["pequeño_grupo", "pareja"]),
            "estructura_necesaria": 5 if perfil_cog == "perfil_detalle_TEA" else random.choice([2, 3, 4]),
            "necesita_movimiento": False,  # Navon es tarea sedentaria
            "sensible_ruido": sensible_ruido,
            "aprende_mejor_con": generar_estrategias_cognitivas(perfil_cog)
        },
        
        "adaptaciones": {
            "metodologicas": generar_adaptaciones_cognitivas(perfil_cog),
            "organizativas": ["ambiente_tranquilo"] if sensible_ruido else [],
            "evaluativas": ["tiempo_extra"] if perfil_cog in ["perfil_detalle_TEA", "perfil_interferencia_alta"] else [],
            "efectividad_reportada": {}
        },
        
        "contexto": {
            "nivel_apoyo_familiar": None,
            "nivel_socioeconomico": None,
            "idioma_casa": "castellano",
            "factores_estres": [],
            "medicacion": False,  # Asumimos no, era muestra general
            "servicios_apoyo": ["orientador"] if perfil_cog == "perfil_detalle_TEA" else ["ninguno"]
        },
        
        "observaciones_libres": {
            "descripcion_general": None,
            "estrategias_funcionan": None, 
            "estrategias_no_funcionan": None,
            "notas_profesor": None
        },
        
        "metadatos": {
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "fuente_datos": "dataset_AYEZ_navon",
            "caso_id": f"ayez_{metricas['id']}",
            "confianza_perfil": 0.6,  # Menor que ADHD, más sintético
            "campos_imputados": [
                "identificacion.edad_genero", "perfil_academico", 
                "perfil_conductual", "contexto"
            ],
            "requiere_validacion": True,
            "metricas_originales": {
                "precision_total": metricas['precision_total'],
                "interferencia_rt": metricas['interferencia_rt'],
                "perfil_cognitivo": perfil_cog,
                "variabilidad_rt": metricas['variabilidad_rt']
            }
        }
    }
    
    return perfil

# Funciones auxiliares
def calcular_curso_edad(edad):
    if edad <= 7: return "2º Primaria"
    elif edad <= 8: return "3º Primaria" 
    elif edad <= 9: return "4º Primaria"
    elif edad <= 10: return "5º Primaria"
    elif edad <= 11: return "6º Primaria"
    else: return "6º Primaria"

def convertir_rt_a_escala(rt_ms):
    """Convertir tiempo reacción a escala velocidad procesamiento 1-5"""
    if rt_ms < 400: return 5    # Muy rápido
    elif rt_ms < 500: return 4  # Rápido
    elif rt_ms < 600: return 3  # Normal
    elif rt_ms < 700: return 2  # Lento
    else: return 1              # Muy lento

def estimar_ci_desde_precision(precision):
    """Estimar CI aproximado desde precisión en tarea cognitiva"""
    if precision >= 0.95: return random.randint(110, 125)
    elif precision >= 0.90: return random.randint(100, 115) 
    elif precision >= 0.80: return random.randint(90, 105)
    elif precision >= 0.70: return random.randint(80, 95)
    else: return random.randint(70, 85)

def convertir_variabilidad_rt(variabilidad_ms):
    """Convertir variabilidad RT a escala consistencia 1-5"""
    if variabilidad_ms < 100: return 1    # Muy consistente
    elif variabilidad_ms < 150: return 2  # Consistente
    elif variabilidad_ms < 200: return 3  # Normal
    elif variabilidad_ms < 250: return 4  # Variable
    else: return 5                        # Muy variable

def generar_academico_desde_cognitivo(metricas, perfil_cog):
    """Generar rendimiento académico basado en perfil cognitivo"""
    base = 3  # Media
    
    if metricas['precision_total'] >= 0.95:
        base = 4
    elif metricas['precision_total'] <= 0.80:
        base = 2
        
    if perfil_cog == "perfil_detalle_TEA":
        return {
            "matematicas": base + 1,  # Buenos en detalles/lógica
            "lectura": base,
            "escritura": max(1, base - 1),  # Dificultades expresivas
            "ciencias": base + 1,  # Buenos en sistemático
            "fortalezas_observadas": ["atencion_detalle", "memoria_hechos", "patron_reconocimiento"],
            "dificultades_observadas": ["expresion_escrita", "comprension_social", "flexibilidad"]
        }
    elif perfil_cog == "perfil_flexible":
        return {
            "matematicas": base + 1,
            "lectura": base + 1, 
            "escritura": base,
            "ciencias": base + 1,
            "fortalezas_observadas": ["adaptabilidad", "resolucion_problemas", "comprension_rapida"],
            "dificultades_observadas": []
        }
    else:
        return {
            "matematicas": base + random.choice([-1, 0, 1]),
            "lectura": base + random.choice([-1, 0, 1]),
            "escritura": base + random.choice([-1, 0, 1]), 
            "ciencias": base + random.choice([-1, 0, 1]),
            "fortalezas_observadas": random.sample(["memoria", "atencion", "logica"], 2),
            "dificultades_observadas": random.sample(["velocidad", "organizacion"], 1)
        }

def generar_triggers_cognitivos(perfil_cog):
    if perfil_cog == "perfil_detalle_TEA":
        return ["cambios_rutina", "sobrecarga_sensorial", "ambiguedad_instrucciones"]
    elif perfil_cog == "perfil_interferencia_alta":
        return ["presion_tiempo", "multitarea", "critica_publica"]
    else:
        return random.sample(["cambios_rutina", "presion_tiempo"], 1)

def generar_motivadores_cognitivos(perfil_cog):
    if perfil_cog == "perfil_detalle_TEA":
        return ["rutinas_claras", "objetivos_especificos", "reconocimiento_logros"]
    elif perfil_cog == "perfil_flexible":
        return ["variedad", "retos_nuevos", "autonomia"]
    else:
        return random.sample(["reconocimiento", "colaboracion", "logro"], 2)

def generar_estrategias_cognitivas(perfil_cog):
    if perfil_cog == "perfil_detalle_TEA":
        return ["instrucciones_paso_paso", "ejemplos_visuales", "tiempo_procesamiento"]
    elif perfil_cog == "perfil_flexible":
        return ["retos_complejos", "proyectos_abiertos", "autoevaluacion"]
    else:
        return random.sample(["feedback_frecuente", "organizadores_visuales"], 2)

def generar_adaptaciones_cognitivas(perfil_cog):
    if perfil_cog == "perfil_detalle_TEA":
        return ["rutinas_estructuradas", "anticipacion_cambios", "instrucciones_claras"]
    elif perfil_cog == "perfil_interferencia_alta":
        return ["reducir_distractores", "pausas_frecuentes", "un_estimulo_vez"]
    else:
        return ["feedback_positivo", "variedad_actividades"]

if __name__ == "__main__":
    import random
    from datetime import datetime
    
    print("=== PROCESANDO DATASET AYEZ ===")
    df = load_ayez_dataset()
    
    # Análisis de todos los participantes
    todos_resultados = analizar_todos_participantes(df)
    
    # Generar perfiles educativos
    print(f"\nGenerando perfiles educativos desde {len(todos_resultados)} participantes...")
    perfiles_generados = []
    
    for i, metricas in enumerate(todos_resultados):
        try:
            perfil = mapear_ayez_a_perfil_educativo(metricas)
            perfiles_generados.append(perfil)
            
            if (i + 1) % 30 == 0:
                print(f"Procesados {i + 1}/{len(todos_resultados)} perfiles")
                
        except Exception as e:
            print(f"Error en participante {metricas['id']}: {e}")
            continue
    
    # Crear directorio si no existe
    Path('data/processed').mkdir(exist_ok=True)
    
    # Guardar archivo con todos los perfiles AYEZ
    output_file = 'data/processed/perfiles_ayez_primaria.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(perfiles_generados, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(perfiles_generados)} perfiles AYEZ guardados en {output_file}")
    
    # Mostrar distribución final
    perfiles_tipo = {}
    for p in perfiles_generados:
        tipo = p['metadatos']['metricas_originales']['perfil_cognitivo']
        perfiles_tipo[tipo] = perfiles_tipo.get(tipo, 0) + 1
    
    print(f"\n=== DISTRIBUCIÓN PERFILES GENERADOS ===")
    for tipo, count in perfiles_tipo.items():
        print(f"{tipo}: {count} perfiles")
    
    # Mostrar ejemplo del primer perfil
    print(f"\n=== EJEMPLO PERFIL GENERADO ===")
    print(json.dumps(perfiles_generados[0], indent=2, ensure_ascii=False))