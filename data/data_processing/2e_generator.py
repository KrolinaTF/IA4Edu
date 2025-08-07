#!/usr/bin/env python3
"""
Generador de Perfiles Doble Excepcionalidad (2e) - ProyectIA
Basado en escala TTESS y estructura JSON Goldilocks
Distribuye 25 perfiles: 10 AC+ADHD, 8 AC+Dislexia, 4 AC+TEA, 3 AC+Otros
GUARDA EN: data/processed/perfiles_doble_excepcionalidad_2e.json
"""

import json
import random
import os
from datetime import datetime

def generar_perfiles_2e():
    """Genera 25 perfiles de doble excepcionalidad para primaria"""
    
    perfiles = []
    
    # =================================
    # GRUPO 1: AC + ADHD (10 perfiles)
    # =================================
    for i in range(1, 11):
        perfil = {
            "identificacion": {
                "id_perfil": f"2e_ac_adhd_{i:03d}",
                "edad": random.choice([7, 8, 9, 10, 11]),
                "genero": random.choice(["masculino", "femenino"]),
                "nivel_educativo": "primaria",
                "curso": random.choice(["2_primaria", "3_primaria", "4_primaria", "5_primaria", "6_primaria"]),
                "tipo_estudiante": "doble_excepcionalidad"
            },
            
            "perfil_academico": {
                "rendimiento_general": random.randint(3, 4),  # Variable por compensación
                "matematicas": random.randint(4, 5),  # Fortaleza típica AC
                "lengua_castellana": random.randint(2, 4),  # Afectada por ADHD
                "ciencias_naturales": random.randint(4, 5),  # Fortaleza típica AC
                "ciencias_sociales": random.randint(3, 4),  # Variable
                "educacion_artistica": random.randint(3, 5),  # Puede ser fortaleza
                "educacion_fisica": random.randint(2, 4),  # Afectada por ADHD
                "segunda_lengua": random.randint(2, 4),  # Variable
                "competencia_digital": random.randint(4, 5),  # Fortaleza típica
                "altas_capacidades_identificadas": True,
                "area_talento_principal": random.choice(["matematicas", "ciencias", "tecnologia"]),
                "dificultades_aprendizaje": True,
                "tipo_dificultad": "ADHD"
            },
            
            "perfil_cognitivo": {
                "atencion_concentracion": random.randint(1, 2),  # Déficit ADHD
                "memoria_trabajo": random.randint(2, 3),  # Afectada por ADHD
                "velocidad_procesamiento": random.randint(2, 3),  # Variable ADHD
                "razonamiento_logico": random.randint(4, 5),  # Fortaleza AC
                "creatividad": random.randint(4, 5),  # Fortaleza AC+ADHD
                "resolucion_problemas": random.randint(4, 5),  # Fortaleza AC
                "planificacion_organizacion": random.randint(1, 2),  # Déficit ADHD
                "flexibilidad_cognitiva": random.randint(3, 4),  # Variable
                "metacognicion": random.randint(3, 4)  # Puede desarrollarse
            },
            
            "perfil_conductual": {
                "atencion_sostenida": random.randint(1, 2),  # Déficit ADHD
                "hiperactividad": random.randint(4, 5),  # Síntoma ADHD
                "impulsividad": random.randint(4, 5),  # Síntoma ADHD
                "autorregulacion": random.randint(1, 2),  # Déficit ADHD
                "habilidades_sociales": random.randint(2, 4),  # Variable
                "tolerancia_frustracion": random.randint(1, 3),  # Baja típica 2e
                "motivacion_intrinseca": random.randint(3, 5),  # Alta en áreas interés
                "perseverancia": random.randint(2, 4),  # Variable según interés
                "autonomia": random.randint(2, 3)  # Afectada por desorganización
            },
            
            "estilo_aprendizaje": {
                "canal_preferente": random.choice(["visual", "kinestesico"]),
                "ritmo_aprendizaje": random.choice(["rapido", "variable"]),
                "tipo_agrupamiento": random.choice(["individual", "pequeno_grupo"]),
                "nivel_autonomia": random.choice(["media", "necesita_estructura"]),
                "motivacion_principal": random.choice(["novedad", "reto", "creatividad"])
            },
            
            "adaptaciones": {
                "necesita_apoyo_atencion": 5,  # Crítico ADHD
                "requiere_descansos_frecuentes": 5,  # Crítico ADHD
                "necesita_estimulacion_cognitiva": 5,  # Crítico AC
                "requiere_flexibilidad_curricular": 4,  # Importante 2e
                "necesita_colaboracion_familia": 5,  # Factor TTESS
                "requiere_gestion_comportamiento": 4,  # Factor TTESS
                "necesita_engagement_especial": 5,  # Factor TTESS
                "requiere_estrategias_adaptadas": 5,  # Factor TTESS
                "necesita_medicacion": random.choice([True, False]),
                "requiere_evaluacion_adaptada": True
            },
            
            "contexto": {
                "apoyo_familiar": random.randint(3, 5),
                "recursos_disponibles": random.randint(2, 4),
                "estabilidad_emocional": random.randint(2, 4),
                "motivacion_estudiante": random.randint(3, 5),
                "expectativas_familia": random.randint(4, 5)
            },
            
            "observaciones_libres": f"Estudiante con altas capacidades en {random.choice(['matemáticas', 'ciencias', 'tecnología'])} y ADHD. Muestra gran creatividad pero dificultades de atención y organización. Requiere estrategias que combinen enriquecimiento cognitivo con apoyo ejecutivo.",
            
            "metadatos": {
                "fecha_creacion": datetime.now().isoformat(),
                "fuente_datos": "generado_2e_ttess",
                "confianza_perfil": 4,  # Basado en literatura científica
                "campos_imputados": ["algunos_valores_especificos"],
                "requiere_validacion": True,
                "version_estructura": "goldilocks_v1"
            }
        }
        perfiles.append(perfil)
    
    # ===================================
    # GRUPO 2: AC + DISLEXIA (8 perfiles)
    # ===================================
    for i in range(1, 9):
        perfil = {
            "identificacion": {
                "id_perfil": f"2e_ac_dislexia_{i:03d}",
                "edad": random.choice([8, 9, 10, 11, 12]),
                "genero": random.choice(["masculino", "femenino"]),
                "nivel_educativo": "primaria",
                "curso": random.choice(["3_primaria", "4_primaria", "5_primaria", "6_primaria"]),
                "tipo_estudiante": "doble_excepcionalidad"
            },
            
            "perfil_academico": {
                "rendimiento_general": random.randint(3, 4),
                "matematicas": random.randint(4, 5),  # Fortaleza AC
                "lengua_castellana": random.randint(1, 3),  # Afectada por dislexia
                "ciencias_naturales": random.randint(4, 5),  # Fortaleza AC
                "ciencias_sociales": random.randint(3, 4),  # Depende de lectura
                "educacion_artistica": random.randint(4, 5),  # Fortaleza típica
                "educacion_fisica": random.randint(3, 5),  # Normal/fortaleza
                "segunda_lengua": random.randint(1, 3),  # Afectada por dislexia
                "competencia_digital": random.randint(4, 5),  # Fortaleza
                "altas_capacidades_identificadas": True,
                "area_talento_principal": random.choice(["matematicas", "artes", "ciencias"]),
                "dificultades_aprendizaje": True,
                "tipo_dificultad": "dislexia"
            },
            
            "perfil_cognitivo": {
                "atencion_concentracion": random.randint(3, 4),  # Normal/buena
                "memoria_trabajo": random.randint(3, 4),  # Variable
                "velocidad_procesamiento": random.randint(2, 3),  # Afectada dislexia
                "razonamiento_logico": random.randint(4, 5),  # Fortaleza AC
                "creatividad": random.randint(4, 5),  # Fortaleza AC
                "resolucion_problemas": random.randint(4, 5),  # Fortaleza AC
                "planificacion_organizacion": random.randint(3, 4),  # Normal
                "flexibilidad_cognitiva": random.randint(4, 5),  # Fortaleza
                "metacognicion": random.randint(3, 4)  # Desarrollable
            },
            
            "perfil_conductual": {
                "atencion_sostenida": random.randint(3, 4),  # Normal/buena
                "hiperactividad": random.randint(1, 2),  # Baja
                "impulsividad": random.randint(2, 3),  # Normal
                "autorregulacion": random.randint(3, 4),  # Normal/buena
                "habilidades_sociales": random.randint(3, 5),  # Variable
                "tolerancia_frustracion": random.randint(2, 3),  # Frustración por lectura
                "motivacion_intrinseca": random.randint(4, 5),  # Alta en fortalezas
                "perseverancia": random.randint(3, 4),  # Buena
                "autonomia": random.randint(3, 4)  # Buena
            },
            
            "estilo_aprendizaje": {
                "canal_preferente": random.choice(["visual", "auditivo"]),
                "ritmo_aprendizaje": "rapido",
                "tipo_agrupamiento": random.choice(["individual", "pequeno_grupo"]),
                "nivel_autonomia": "alta",
                "motivacion_principal": random.choice(["reto", "creatividad", "reconocimiento"])
            },
            
            "adaptaciones": {
                "necesita_apoyo_lectoescritura": 5,  # Crítico dislexia
                "requiere_material_adaptado": 5,  # Crítico dislexia
                "necesita_estimulacion_cognitiva": 5,  # Crítico AC
                "requiere_flexibilidad_curricular": 4,  # Importante 2e
                "necesita_colaboracion_familia": 4,  # Factor TTESS
                "requiere_gestion_comportamiento": 2,  # Menor que ADHD
                "necesita_engagement_especial": 4,  # Factor TTESS
                "requiere_estrategias_adaptadas": 5,  # Factor TTESS
                "necesita_tecnologia_asistiva": True,
                "requiere_evaluacion_adaptada": True
            },
            
            "contexto": {
                "apoyo_familiar": random.randint(3, 5),
                "recursos_disponibles": random.randint(2, 4),
                "estabilidad_emocional": random.randint(3, 4),
                "motivacion_estudiante": random.randint(4, 5),
                "expectativas_familia": random.randint(4, 5)
            },
            
            "observaciones_libres": f"Estudiante con altas capacidades en {random.choice(['matemáticas', 'ciencias', 'artes'])} y dislexia. Excelente razonamiento pero dificultades significativas en lectoescritura. Requiere adaptaciones en acceso al currículo manteniendo alta exigencia cognitiva.",
            
            "metadatos": {
                "fecha_creacion": datetime.now().isoformat(),
                "fuente_datos": "generado_2e_ttess",
                "confianza_perfil": 4,
                "campos_imputados": ["algunos_valores_especificos"],
                "requiere_validacion": True,
                "version_estructura": "goldilocks_v1"
            }
        }
        perfiles.append(perfil)
    
    # ==============================
    # GRUPO 3: AC + TEA (4 perfiles)
    # ==============================
    for i in range(1, 5):
        perfil = {
            "identificacion": {
                "id_perfil": f"2e_ac_tea_{i:03d}",
                "edad": random.choice([7, 8, 9, 10, 11]),
                "genero": random.choice(["masculino", "femenino"]),
                "nivel_educativo": "primaria",
                "curso": random.choice(["2_primaria", "3_primaria", "4_primaria", "5_primaria"]),
                "tipo_estudiante": "doble_excepcionalidad"
            },
            
            "perfil_academico": {
                "rendimiento_general": random.randint(3, 5),  # Muy variable
                "matematicas": random.randint(4, 5),  # Fortaleza típica
                "lengua_castellana": random.randint(2, 4),  # Variable TEA
                "ciencias_naturales": random.randint(4, 5),  # Fortaleza típica
                "ciencias_sociales": random.randint(2, 4),  # Dificultad social
                "educacion_artistica": random.randint(3, 5),  # Variable
                "educacion_fisica": random.randint(2, 3),  # Dificultades motrices
                "segunda_lengua": random.randint(2, 4),  # Variable
                "competencia_digital": random.randint(4, 5),  # Fortaleza típica
                "altas_capacidades_identificadas": True,
                "area_talento_principal": random.choice(["matematicas", "ciencias", "tecnologia", "musica"]),
                "dificultades_aprendizaje": True,
                "tipo_dificultad": "TEA_leve"
            },
            
            "perfil_cognitivo": {
                "atencion_concentracion": random.randint(3, 5),  # Muy alta en intereses
                "memoria_trabajo": random.randint(3, 4),  # Buena
                "velocidad_procesamiento": random.randint(2, 4),  # Variable
                "razonamiento_logico": random.randint(4, 5),  # Fortaleza AC
                "creatividad": random.randint(3, 5),  # Variable TEA
                "resolucion_problemas": random.randint(4, 5),  # Fortaleza
                "planificacion_organizacion": random.randint(2, 4),  # Dificultad TEA
                "flexibilidad_cognitiva": random.randint(2, 3),  # Dificultad TEA
                "metacognicion": random.randint(2, 4)  # Variable
            },
            
            "perfil_conductual": {
                "atencion_sostenida": random.randint(4, 5),  # Muy alta en intereses
                "hiperactividad": random.randint(1, 2),  # Baja típica TEA
                "impulsividad": random.randint(2, 3),  # Variable
                "autorregulacion": random.randint(2, 3),  # Dificultad TEA
                "habilidades_sociales": random.randint(1, 2),  # Déficit TEA
                "tolerancia_frustracion": random.randint(1, 2),  # Baja TEA
                "motivacion_intrinseca": random.randint(4, 5),  # Muy alta en intereses
                "perseverancia": random.randint(4, 5),  # Muy alta
                "autonomia": random.randint(2, 3)  # Necesita estructura
            },
            
            "estilo_aprendizaje": {
                "canal_preferente": "visual",
                "ritmo_aprendizaje": random.choice(["rapido", "variable"]),
                "tipo_agrupamiento": "individual",
                "nivel_autonomia": "necesita_estructura",
                "motivacion_principal": "interes_especifico"
            },
            
            "adaptaciones": {
                "necesita_apoyo_social": 5,  # Crítico TEA
                "requiere_estructura_predecible": 5,  # Crítico TEA
                "necesita_estimulacion_cognitiva": 5,  # Crítico AC
                "requiere_flexibilidad_curricular": 4,  # Importante 2e
                "necesita_colaboracion_familia": 5,  # Factor TTESS
                "requiere_gestion_comportamiento": 4,  # Factor TTESS
                "necesita_engagement_especial": 5,  # Factor TTESS
                "requiere_estrategias_adaptadas": 5,  # Factor TTESS
                "necesita_anticipacion_cambios": True,
                "requiere_evaluacion_adaptada": True
            },
            
            "contexto": {
                "apoyo_familiar": random.randint(4, 5),  # Crucial en TEA
                "recursos_disponibles": random.randint(3, 4),
                "estabilidad_emocional": random.randint(2, 3),  # Variable TEA
                "motivacion_estudiante": random.randint(4, 5),  # Alta en intereses
                "expectativas_familia": random.randint(3, 5)
            },
            
            "observaciones_libres": f"Estudiante con altas capacidades en {random.choice(['matemáticas', 'ciencias', 'tecnología', 'música'])} y TEA leve. Excelente en áreas de interés pero dificultades sociales y de flexibilidad. Requiere estructura predecible y enriquecimiento en área de talento.",
            
            "metadatos": {
                "fecha_creacion": datetime.now().isoformat(),
                "fuente_datos": "generado_2e_ttess",
                "confianza_perfil": 4,
                "campos_imputados": ["algunos_valores_especificos"],
                "requiere_validacion": True,
                "version_estructura": "goldilocks_v1"
            }
        }
        perfiles.append(perfil)
    
    # ===================================
    # GRUPO 4: AC + OTROS (3 perfiles)
    # ===================================
    otros_tipos = ["discalculia", "disgrafia", "dificultades_motrices"]
    
    for i, tipo_dificultad in enumerate(otros_tipos, 1):
        perfil = {
            "identificacion": {
                "id_perfil": f"2e_ac_otros_{i:03d}",
                "edad": random.choice([8, 9, 10, 11]),
                "genero": random.choice(["masculino", "femenino"]),
                "nivel_educativo": "primaria",
                "curso": random.choice(["3_primaria", "4_primaria", "5_primaria", "6_primaria"]),
                "tipo_estudiante": "doble_excepcionalidad"
            },
            
            "perfil_academico": {
                "rendimiento_general": random.randint(3, 4),
                "matematicas": 2 if tipo_dificultad == "discalculia" else random.randint(4, 5),
                "lengua_castellana": 2 if tipo_dificultad == "disgrafia" else random.randint(4, 5),
                "ciencias_naturales": random.randint(4, 5),
                "ciencias_sociales": random.randint(3, 4),
                "educacion_artistica": 2 if tipo_dificultad == "dificultades_motrices" else random.randint(4, 5),
                "educacion_fisica": 2 if tipo_dificultad == "dificultades_motrices" else random.randint(3, 4),
                "segunda_lengua": random.randint(3, 4),
                "competencia_digital": random.randint(4, 5),
                "altas_capacidades_identificadas": True,
                "area_talento_principal": "verbal" if tipo_dificultad == "discalculia" else "matematicas",
                "dificultades_aprendizaje": True,
                "tipo_dificultad": tipo_dificultad
            },
            
            "perfil_cognitivo": {
                "atencion_concentracion": random.randint(3, 4),
                "memoria_trabajo": random.randint(3, 4),
                "velocidad_procesamiento": random.randint(3, 4),
                "razonamiento_logico": random.randint(4, 5),
                "creatividad": random.randint(4, 5),
                "resolucion_problemas": random.randint(4, 5),
                "planificacion_organizacion": random.randint(3, 4),
                "flexibilidad_cognitiva": random.randint(4, 5),
                "metacognicion": random.randint(3, 4)
            },
            
            "perfil_conductual": {
                "atencion_sostenida": random.randint(3, 4),
                "hiperactividad": random.randint(1, 2),
                "impulsividad": random.randint(2, 3),
                "autorregulacion": random.randint(3, 4),
                "habilidades_sociales": random.randint(3, 4),
                "tolerancia_frustracion": random.randint(2, 3),
                "motivacion_intrinseca": random.randint(4, 5),
                "perseverancia": random.randint(3, 4),
                "autonomia": random.randint(3, 4)
            },
            
            "estilo_aprendizaje": {
                "canal_preferente": random.choice(["visual", "auditivo", "kinestesico"]),
                "ritmo_aprendizaje": "rapido",
                "tipo_agrupamiento": random.choice(["individual", "pequeno_grupo"]),
                "nivel_autonomia": "alta",
                "motivacion_principal": random.choice(["reto", "creatividad"])
            },
            
            "adaptaciones": {
                "necesita_apoyo_especifico": 5,  # Según dificultad
                "requiere_material_adaptado": 4,
                "necesita_estimulacion_cognitiva": 5,  # Crítico AC
                "requiere_flexibilidad_curricular": 4,
                "necesita_colaboracion_familia": 4,  # Factor TTESS
                "requiere_gestion_comportamiento": 2,
                "necesita_engagement_especial": 4,  # Factor TTESS
                "requiere_estrategias_adaptadas": 5,  # Factor TTESS
                "necesita_tecnologia_asistiva": True,
                "requiere_evaluacion_adaptada": True
            },
            
            "contexto": {
                "apoyo_familiar": random.randint(3, 5),
                "recursos_disponibles": random.randint(3, 4),
                "estabilidad_emocional": random.randint(3, 4),
                "motivacion_estudiante": random.randint(4, 5),
                "expectativas_familia": random.randint(4, 5)
            },
            
            "observaciones_libres": f"Estudiante con altas capacidades y {tipo_dificultad}. Requiere adaptaciones específicas en área de dificultad manteniendo alto nivel de exigencia cognitiva en fortalezas.",
            
            "metadatos": {
                "fecha_creacion": datetime.now().isoformat(),
                "fuente_datos": "generado_2e_ttess",
                "confianza_perfil": 4,
                "campos_imputados": ["algunos_valores_especificos"],
                "requiere_validacion": True,
                "version_estructura": "goldilocks_v1"
            }
        }
        perfiles.append(perfil)
    
    return perfiles

def guardar_perfiles_2e():
    """Genera y guarda los 25 perfiles de doble excepcionalidad"""
    
    perfiles = generar_perfiles_2e()
    
    # Verificar que tenemos exactamente 25 perfiles
    assert len(perfiles) == 25, f"Error: Se generaron {len(perfiles)} perfiles en lugar de 25"
    
    # Contar por tipo
    tipos = {}
    for perfil in perfiles:
        tipo = perfil['perfil_academico']['tipo_dificultad']
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    print("📊 PERFILES 2e GENERADOS:")
    print(f"├── AC + ADHD: {tipos.get('ADHD', 0)} perfiles")
    print(f"├── AC + Dislexia: {tipos.get('dislexia', 0)} perfiles")
    print(f"├── AC + TEA: {tipos.get('TEA_leve', 0)} perfiles")
    print(f"└── AC + Otros: {tipos.get('discalculia', 0) + tipos.get('disgrafia', 0) + tipos.get('dificultades_motrices', 0)} perfiles")
    print(f"📈 TOTAL: {len(perfiles)} perfiles")
    
    # Guardar archivo JSON
    output_data = {
        "metadata": {
            "descripcion": "Perfiles de Doble Excepcionalidad para ProyectIA",
            "total_perfiles": len(perfiles),
            "distribucion": tipos,
            "fuente": "Generados basados en escala TTESS y literatura científica",
            "fecha_generacion": datetime.now().isoformat(),
            "version": "1.0"
        },
        "perfiles": perfiles
    }
    
    # Crear directorio data/processed si no existe
    os.makedirs('data/processed', exist_ok=True)
    
    filename = "data/processed/perfiles_doble_excepcionalidad_2e.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ ARCHIVO GUARDADO: {filename}")
    print(f"💾 Tamaño: {len(json.dumps(output_data, ensure_ascii=False))} caracteres")
    
    return perfiles, filename

# Ejecutar generación
if __name__ == "__main__":
    print("🧠 GENERANDO PERFILES DOBLE EXCEPCIONALIDAD (2e) - ProyectIA")
    print("=" * 60)
    
    perfiles, archivo = guardar_perfiles_2e()
    
    print("\n🎯 INTEGRACIÓN CON DATASET PRINCIPAL:")
    print("├── 116 perfiles ADHD")
    print("├── 149 perfiles AYEZ")  
    print("├── 104 perfiles Altas Capacidades")
    print("└── 25 perfiles Doble Excepcionalidad")
    print("=" * 30)
    print("📊 TOTAL DATASET: 394 perfiles")
    
    print("\n🚀 SIGUIENTE PASO: Combinar todos los datasets en archivo unificado")
    print("📋 LISTO PARA: Algoritmo de matching perfil→actividad")