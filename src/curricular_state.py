#!/usr/bin/env python3
"""
Generador Estado Curricular por Cursos - ProyectIA
Toma los 394 perfiles unificados y añade estado curricular específico
Divide en archivos JSON separados por curso (1º-6º primaria)
"""

import json
import random
import os
from datetime import datetime
from collections import defaultdict

# =============================================================================
# DEFINICIÓN CURRÍCULOS POR CURSO (BASADO EN CURRÍCULO ESPAÑOL PRIMARIA)
# =============================================================================

CURRICULOS = {
    "1_primaria": {
        "matematicas": {
            "numeros_0_10": "Reconocer y escribir números del 0 al 10",
            "contar_objetos": "Contar objetos hasta 10",
            "sumas_sin_llevada": "Sumas básicas sin llevada (hasta 10)",
            "restas_sin_llevada": "Restas básicas sin llevada (hasta 10)",
            "formas_geometricas": "Reconocer círculo, cuadrado, triángulo",
            "mayor_menor": "Comparar números usando >, <, =",
            "series_numericas": "Completar series numéricas sencillas",
            "problemas_suma": "Resolver problemas simples de suma"
        },
        "lengua": {
            "reconocer_letras": "Reconocer todas las letras del abecedario",
            "sonidos_letras": "Asociar letras con sus sonidos",
            "escribir_nombre": "Escribir su nombre correctamente",
            "leer_palabras": "Leer palabras de 3-4 letras",
            "escribir_palabras": "Escribir palabras sencillas",
            "leer_frases": "Leer frases de 3-5 palabras",
            "comprension_basica": "Entender instrucciones simples escritas",
            "vocabulario_basico": "Conocer 200-300 palabras básicas"
        },
        "ciencias": {
            "partes_cuerpo": "Identificar partes básicas del cuerpo",
            "sentidos": "Reconocer los 5 sentidos",
            "animales_plantas": "Distinguir entre animales y plantas",
            "tiempo_atmosferico": "Reconocer sol, lluvia, nube, viento",
            "dia_noche": "Entender diferencia día/noche",
            "materiales": "Identificar materiales básicos (madera, metal, plástico)"
        }
    },
    
    "2_primaria": {
        "matematicas": {
            "numeros_0_100": "Leer y escribir números hasta 100",
            "decenas_unidades": "Entender decenas y unidades",
            "sumas_llevada": "Sumas con llevada hasta 100",
            "restas_llevada": "Restas con llevada hasta 100",
            "tabla_2": "Tabla de multiplicar del 2",
            "tabla_5": "Tabla de multiplicar del 5",
            "tabla_10": "Tabla de multiplicar del 10",
            "problemas_dos_operaciones": "Problemas con 2 operaciones",
            "medidas_tiempo": "Leer reloj (horas en punto)",
            "euros_centimos": "Reconocer monedas y billetes básicos"
        },
        "lengua": {
            "leer_textos_cortos": "Leer textos de 4-6 líneas",
            "escribir_frases": "Escribir frases completas",
            "ortografia_basica": "Uso básico de mayúsculas y punto",
            "comprension_lectora": "Responder preguntas sobre texto leído",
            "vocabulario_amplio": "Conocer 500-700 palabras",
            "describir_imagenes": "Describir lo que ve en una imagen",
            "narrar_experiencias": "Contar experiencias personales",
            "uso_diccionario": "Buscar palabras en diccionario infantil"
        },
        "ciencias": {
            "ciclo_agua": "Entender evaporación y lluvia básica",
            "habitats": "Conocer donde viven diferentes animales",
            "alimentacion": "Clasificar alimentos básicos",
            "estaciones": "Reconocer las 4 estaciones",
            "plantas_crecimiento": "Entender qué necesitan las plantas",
            "cuidado_ambiente": "Conceptos básicos de reciclaje"
        }
    },
    
    "3_primaria": {
        "matematicas": {
            "numeros_1000": "Números hasta 1.000",
            "todas_tablas": "Tablas de multiplicar completas (1-10)",
            "divisiones_exactas": "Divisiones exactas básicas",
            "fracciones_mitad": "Concepto de mitad, tercio, cuarto",
            "problemas_complejos": "Problemas con 3 operaciones",
            "geometria_perimetro": "Calcular perímetro de figuras",
            "medidas_longitud": "Metro, centímetro, kilómetro",
            "medidas_peso": "Kilo, gramo básico",
            "graficos_barras": "Interpretar gráficos de barras simples"
        },
        "lengua": {
            "textos_largos": "Leer textos de 1-2 párrafos",
            "resumir": "Hacer resúmenes de 2-3 líneas",
            "ortografia_avanzada": "Acentos en palabras agudas",
            "tipos_palabras": "Sustantivos, adjetivos, verbos",
            "escribir_cuentos": "Escribir historias de 6-8 líneas",
            "comprension_avanzada": "Inferir información no explícita",
            "vocabulario_rico": "Conocer 800-1000 palabras",
            "expresion_oral": "Expresar opiniones oralmente"
        },
        "ciencias": {
            "sistema_solar": "Planetas básicos del sistema solar",
            "ecosistemas": "Bosque, desierto, océano",
            "cadena_alimenticia": "Entender quién come a quién",
            "estados_materia": "Sólido, líquido, gas",
            "energia": "Conceptos básicos de energía",
            "maquinas_simples": "Palanca, polea, plano inclinado"
        }
    },
    
    "4_primaria": {
        "matematicas": {
            "numeros_grandes": "Números hasta 10.000",
            "operaciones_complejas": "Operaciones combinadas con paréntesis",
            "divisiones_resto": "Divisiones con resto",
            "fracciones_operaciones": "Sumar y restar fracciones simples",
            "decimales": "Números decimales hasta centésimas",
            "area_rectangulo": "Calcular área de rectángulos",
            "unidades_medida": "Conversiones básicas de medidas",
            "porcentajes": "Porcentajes básicos (25%, 50%, 75%)",
            "probabilidad": "Conceptos de posible/imposible"
        },
        "lengua": {
            "analisis_sintactico": "Sujeto y predicado",
            "tiempos_verbales": "Presente, pasado, futuro",
            "ortografia_completa": "Acentuación completa",
            "textos_informativos": "Leer y escribir textos informativos",
            "argumentar": "Dar razones de sus opiniones",
            "teatro": "Representar pequeñas obras",
            "investigar": "Buscar información en diferentes fuentes",
            "vocabulario_tecnico": "Términos específicos de materias"
        },
        "ciencias": {
            "cuerpo_humano": "Sistemas básicos (digestivo, respiratorio)",
            "reproduccion": "Ciclos de vida básicos",
            "rocas_minerales": "Tipos básicos de rocas",
            "fuerzas": "Empujar, tirar, gravedad",
            "electricidad": "Circuitos eléctricos simples",
            "investigacion": "Método científico básico"
        }
    },
    
    "5_primaria": {
        "matematicas": {
            "numeros_millones": "Números hasta millones",
            "potencias": "Potencias de 10",
            "fracciones_decimales": "Relación fracciones-decimales",
            "porcentajes_calculo": "Calcular porcentajes",
            "proporcionalidad": "Regla de tres simple",
            "geometria_angulos": "Tipos de ángulos",
            "volumen": "Concepto de volumen",
            "estadistica": "Media aritmética, moda",
            "coordenadas": "Sistema de coordenadas básico"
        },
        "lengua": {
            "analisis_morfologico": "Análisis completo de palabras",
            "literatura": "Géneros literarios básicos",
            "texto_argumentativo": "Escribir textos argumentativos",
            "registro_linguistico": "Formal e informal",
            "sinonimos_antonimos": "Uso avanzado",
            "metrica": "Conceptos básicos de métrica",
            "presentaciones": "Presentar trabajos oralmente",
            "debate": "Participar en debates simples"
        },
        "ciencias": {
            "celulas": "Estructura celular básica",
            "clasificacion_seres": "Reino animal y vegetal",
            "nutricion": "Cadenas tróficas complejas",
            "clima": "Factores climáticos",
            "tecnologia": "Avances tecnológicos",
            "sostenibilidad": "Desarrollo sostenible básico"
        }
    },
    
    "6_primaria": {
        "matematicas": {
            "enteros": "Números enteros y negativos",
            "algebra_basica": "Ecuaciones de primer grado simples",
            "geometria_completa": "Área y perímetro de figuras complejas",
            "estadistica_avanzada": "Gráficos complejos, probabilidad",
            "proporcionalidad_compuesta": "Regla de tres compuesta",
            "raices": "Raíz cuadrada",
            "notacion_cientifica": "Notación científica básica",
            "problemas_reales": "Problemas de la vida real complejos"
        },
        "lengua": {
            "sintaxis_compleja": "Oraciones compuestas",
            "literatura_analisis": "Análisis de textos literarios",
            "ensayo": "Escribir ensayos cortos",
            "investigacion_avanzada": "Proyectos de investigación",
            "comunicacion_digital": "Normas comunicación online",
            "creatividad_literaria": "Crear textos creativos complejos",
            "critica_literaria": "Opinar sobre obras leídas",
            "preparacion_eso": "Preparación para secundaria"
        },
        "ciencias": {
            "evolucion": "Conceptos básicos de evolución",
            "universo": "Galaxias, estrellas avanzado",
            "quimica_basica": "Elementos y compuestos",
            "energia_renovable": "Tipos de energía renovable",
            "biotecnologia": "Aplicaciones básicas",
            "investigacion_cientifica": "Proyectos científicos complejos"
        }
    }
}

# Estados posibles para cada ítem curricular
ESTADOS_CURRICULO = [
    "no_iniciado",      # 0 - No ha empezado
    "iniciado",         # 1 - Ha empezado pero muy básico
    "en_proceso",       # 2 - Progresando, necesita práctica
    "conseguido",       # 3 - Dominado para su nivel
    "superado"          # 4 - Por encima del nivel esperado
]

def generar_estado_curricular_realista(perfil, curso):
    """
    Genera estado curricular realista basado en el perfil académico existente
    """
    
    estado_curricular = {}
    curriculo_curso = CURRICULOS.get(curso, {})
    
    # Obtener rendimientos académicos del perfil
    rendimiento_mat = perfil.get('perfil_academico', {}).get('matematicas', 3)
    rendimiento_lengua = perfil.get('perfil_academico', {}).get('lengua_castellana', 3)
    rendimiento_ciencias = perfil.get('perfil_academico', {}).get('ciencias_naturales', 3)
    
    # Factores del estudiante
    tipo_estudiante = perfil.get('identificacion', {}).get('tipo_estudiante', 'tipico')
    dificultades = perfil.get('perfil_academico', {}).get('dificultades_aprendizaje', False)
    altas_capacidades = perfil.get('perfil_academico', {}).get('altas_capacidades_identificadas', False)
    
    for materia, items in curriculo_curso.items():
        estado_curricular[materia] = {}
        
        # Determinar rendimiento base según materia
        if materia == "matematicas":
            rendimiento_base = rendimiento_mat
        elif materia == "lengua":
            rendimiento_base = rendimiento_lengua
        else:  # ciencias
            rendimiento_base = rendimiento_ciencias
        
        # Ajustar según tipo de estudiante
        if tipo_estudiante == "doble_excepcionalidad":
            # 2e: Alta variabilidad según fortalezas/debilidades
            area_talento = perfil.get('perfil_academico', {}).get('area_talento_principal', '')
            tipo_dificultad = perfil.get('perfil_academico', {}).get('tipo_dificultad', '')
            
            if materia == "matematicas" and area_talento in ["matematicas", "ciencias"]:
                rendimiento_ajustado = min(5, rendimiento_base + random.randint(1, 2))
            elif materia == "lengua" and tipo_dificultad in ["dislexia", "disgrafia"]:
                rendimiento_ajustado = max(1, rendimiento_base - random.randint(1, 2))
            else:
                rendimiento_ajustado = rendimiento_base + random.randint(-1, 1)
                
        elif tipo_estudiante == "altas_capacidades" or altas_capacidades:
            # AC: Generalmente por encima en la mayoría de áreas
            rendimiento_ajustado = min(5, rendimiento_base + random.randint(0, 1))
            
        elif tipo_estudiante == "adhd":
            # ADHD: Más variabilidad, especialmente en organización
            variabilidad = random.randint(-1, 1)
            rendimiento_ajustado = max(1, min(5, rendimiento_base + variabilidad))
            
        else:
            # Estudiante típico: Pequeña variabilidad
            rendimiento_ajustado = max(1, min(5, rendimiento_base + random.randint(-1, 1)))
        
        # Generar estado para cada ítem del currículo
        for item, descripcion in items.items():
            # Añadir variabilidad por ítem individual
            variacion_item = random.randint(-1, 1)
            estado_item = max(0, min(4, rendimiento_ajustado + variacion_item))
            
            # Ajustes específicos por tipo de ítem
            if tipo_estudiante == "adhd" and any(word in item for word in ["problemas", "complejos", "organizacion"]):
                estado_item = max(0, estado_item - 1)  # ADHD lucha con tareas complejas
                
            if dificultades and materia == "lengua" and any(word in item for word in ["leer", "escribir", "ortografia"]):
                estado_item = max(0, estado_item - 1)  # Dificultades lectoescritura
            
            estado_curricular[materia][item] = {
                "estado": ESTADOS_CURRICULO[estado_item],
                "nivel_numerico": estado_item,
                "descripcion": descripcion,
                "necesita_refuerzo": estado_item < 2,
                "puede_avanzar": estado_item >= 3
            }
    
    return estado_curricular

def dividir_perfiles_por_curso(dataset_unificado):
    """
    Divide los perfiles por curso y añade estado curricular
    """
    
    perfiles_por_curso = defaultdict(list)
    estadisticas = defaultdict(lambda: defaultdict(int))
    
    total_perfiles = len(dataset_unificado['perfiles'])
    
    print(f"🔄 PROCESANDO {total_perfiles} PERFILES...")
    print("=" * 50)
    
    for i, perfil in enumerate(dataset_unificado['perfiles']):
        try:
            # Obtener curso del perfil
            curso = perfil.get('identificacion', {}).get('curso', 'desconocido')
            
            if curso == 'desconocido' or curso not in CURRICULOS:
                print(f"⚠️  Perfil {i}: Curso '{curso}' no válido, asignando curso aleatorio")
                curso = random.choice(list(CURRICULOS.keys()))
                perfil['identificacion']['curso'] = curso
            
            # Generar estado curricular
            estado_curricular = generar_estado_curricular_realista(perfil, curso)
            
            # Añadir estado curricular al perfil
            perfil['estado_curricular'] = estado_curricular
            
            # Añadir metadatos del estado curricular
            perfil['metadatos']['tiene_estado_curricular'] = True
            perfil['metadatos']['fecha_estado_curricular'] = datetime.now().isoformat()
            perfil['metadatos']['version_curriculo'] = 'primaria_espana_v1'
            
            # Agregar a lista por curso
            perfiles_por_curso[curso].append(perfil)
            
            # Estadísticas
            tipo_estudiante = perfil.get('identificacion', {}).get('tipo_estudiante', 'tipico')
            estadisticas[curso]['total'] += 1
            estadisticas[curso][tipo_estudiante] += 1
            
            if (i + 1) % 50 == 0:
                print(f"📊 Procesados: {i + 1}/{total_perfiles}")
                
        except Exception as e:
            print(f"❌ Error procesando perfil {i}: {e}")
    
    print(f"\n✅ PROCESAMIENTO COMPLETADO")
    print(f"📊 Total perfiles procesados: {sum(stats['total'] for stats in estadisticas.values())}")
    
    return dict(perfiles_por_curso), dict(estadisticas)

def guardar_archivos_por_curso(perfiles_por_curso, estadisticas):
    """
    Guarda un archivo JSON por cada curso
    """
    
    # Crear directorio si no existe
    os.makedirs('data/processed/por_curso', exist_ok=True)
    
    archivos_creados = []
    
    print("\n💾 GUARDANDO ARCHIVOS POR CURSO:")
    print("=" * 50)
    
    for curso, perfiles in perfiles_por_curso.items():
        # Calcular estadísticas del estado curricular
        items_conseguidos = 0
        items_totales = 0
        
        for perfil in perfiles:
            estado_curr = perfil.get('estado_curricular', {})
            for materia, items in estado_curr.items():
                for item, datos in items.items():
                    items_totales += 1
                    if datos['estado'] in ['conseguido', 'superado']:
                        items_conseguidos += 1
        
        progreso_medio = (items_conseguidos / items_totales * 100) if items_totales > 0 else 0
        
        # Crear estructura del archivo
        archivo_curso = {
            "metadata": {
                "curso": curso,
                "total_perfiles": len(perfiles),
                "distribucion_tipos": {k: v for k, v in estadisticas[curso].items() if k != 'total'},
                "curriculo_aplicado": list(CURRICULOS[curso].keys()),
                "items_curriculares_total": sum(len(items) for items in CURRICULOS[curso].values()),
                "progreso_medio_curso": round(progreso_medio, 1),
                "fecha_generacion": datetime.now().isoformat(),
                "version": "1.0"
            },
            "curriculo_referencia": CURRICULOS[curso],
            "perfiles": perfiles
        }
        
        # Guardar archivo
        filename = f"data/processed/por_curso/perfiles_{curso}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(archivo_curso, f, ensure_ascii=False, indent=2)
        
        archivos_creados.append(filename)
        
        # Estadísticas por curso
        print(f"✅ {curso}: {len(perfiles)} perfiles")
        print(f"   📊 Progreso medio: {progreso_medio:.1f}%")
        print(f"   📁 Archivo: {filename}")
        
        # Mostrar distribución por tipos
        tipos = {k: v for k, v in estadisticas[curso].items() if k != 'total'}
        for tipo, cantidad in tipos.items():
            porcentaje = (cantidad / len(perfiles)) * 100
            print(f"   ├── {tipo}: {cantidad} ({porcentaje:.1f}%)")
        
        print()
    
    return archivos_creados

def crear_resumen_curricular_global(perfiles_por_curso, estadisticas):
    """
    Crea resumen ejecutivo del estado curricular
    """
    
    total_perfiles = sum(len(perfiles) for perfiles in perfiles_por_curso.values())
    
    resumen = f"""
# 📚 ESTADO CURRICULAR PROYECTIA - RESUMEN EJECUTIVO

## 🎯 TRANSFORMACIÓN COMPLETADA
✅ **{total_perfiles} perfiles** enriquecidos con estado curricular específico
✅ **6 cursos** de primaria con currículos completos  
✅ **División por curso** para matching preciso
✅ **Estados sintéticos** realistas basados en perfiles académicos

## 📊 DISTRIBUCIÓN POR CURSO
"""
    
    for curso, perfiles in perfiles_por_curso.items():
        curso_num = curso.replace('_primaria', '').replace('_', '')
        resumen += f"- **{curso_num}º Primaria**: {len(perfiles)} estudiantes\n"
    
    resumen += f"""
## 🧠 PRECISIÓN CURRICULAR LOGRADA

### Antes (genérico):
❌ "Matemáticas nivel 4" → Actividad genérica

### Ahora (específico):  
✅ "Sumas con llevada: conseguido, Divisiones: en proceso" → Actividad exacta

## 📚 CURRÍCULO IMPLEMENTADO
- **Matemáticas**: Desde números 0-10 hasta álgebra básica
- **Lengua**: Desde reconocer letras hasta análisis sintáctico  
- **Ciencias**: Desde partes del cuerpo hasta investigación científica
- **Estados**: no_iniciado → iniciado → en_proceso → conseguido → superado

## 🎯 MATCHING PRECISO POSIBLE
1. **Detectar** exactamente qué necesita cada estudiante
2. **Recomendar** actividades específicas para su nivel
3. **Progresar** siguiendo secuencia curricular lógica
4. **Adaptar** según tipo de estudiante (ADHD, AC, 2e, típico)

## 📁 ARCHIVOS GENERADOS
"""
    
    for curso in sorted(perfiles_por_curso.keys()):
        resumen += f"- `data/processed/por_curso/perfiles_{curso}.json`\n"
    
    resumen += f"""
## 🚀 IMPACTO EDUCATIVO
- **Personalización real** basada en currículo oficial
- **Profesores** ven valor inmediato y concreto
- **Estudiantes** reciben exactamente lo que necesitan
- **Escalabilidad** mantenida con precisión pedagógica

---
**ProyectIA - Personalización Curricular Precisa con IA**
*Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""
    
    with open('data/processed/resumen_estado_curricular.md', 'w', encoding='utf-8') as f:
        f.write(resumen)
    
    print(resumen)
    return resumen

def main():
    """Función principal"""
    
    print("📚 GENERADOR ESTADO CURRICULAR + DIVISIÓN POR CURSOS")
    print("🎯 Objetivo: Enriquecer 394 perfiles con estado curricular específico")
    print("=" * 70)
    
    # Cargar dataset unificado
    dataset_file = 'data/processed/dataset_unificado_proyectia.json'
    
    if not os.path.exists(dataset_file):
        print(f"❌ ERROR: No se encuentra {dataset_file}")
        print("🔧 Ejecuta primero el script unificador de datasets")
        return
    
    print(f"📖 Cargando dataset unificado: {dataset_file}")
    
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset_unificado = json.load(f)
        
        total_perfiles = len(dataset_unificado['perfiles'])
        print(f"✅ Dataset cargado: {total_perfiles} perfiles")
        
    except Exception as e:
        print(f"❌ Error cargando dataset: {e}")
        return
    
    # Dividir por curso y añadir estado curricular
    perfiles_por_curso, estadisticas = dividir_perfiles_por_curso(dataset_unificado)
    
    # Guardar archivos por curso
    archivos_creados = guardar_archivos_por_curso(perfiles_por_curso, estadisticas)
    
    # Crear resumen
    crear_resumen_curricular_global(perfiles_por_curso, estadisticas)
    
    print("\n🎉 ESTADO CURRICULAR COMPLETADO")
    print("=" * 50)
    print(f"✅ {len(archivos_creados)} archivos por curso creados")
    print(f"✅ Estado curricular añadido a {sum(len(p) for p in perfiles_por_curso.values())} perfiles")
    print(f"✅ Listo para matching curricular específico")
    print("\n🚀 SIGUIENTE FASE: Algoritmo de matching perfil→actividad curricular")

if __name__ == "__main__":
    main()