import os
import sys
import django
import re

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_generator.settings')
django.setup()

from core.models import Proyecto

def extraer_actividades(contenido):
    """Extrae actividades del texto usando patrones"""
    # Patrón para detectar inicio de actividad
    patron_actividad = r'ACTIVIDAD\s+\d+:\s*"([^"]+)"'
    
    # Dividir por actividades
    actividades = re.split(patron_actividad, contenido)
    
    proyectos = []
    
    # Procesar pares (título, contenido)
    for i in range(1, len(actividades), 2):
        if i + 1 < len(actividades):
            titulo = actividades[i].strip()
            contenido_actividad = actividades[i + 1].strip()
            
            # Extraer datos básicos
            proyecto_data = extraer_datos_proyecto(titulo, contenido_actividad)
            proyectos.append(proyecto_data)
    
    return proyectos

def extraer_datos_proyecto(titulo, contenido):
    """Extrae datos específicos de cada proyecto"""
    
    # Extraer duración
    duracion_match = re.search(r'Duración:\s*(\d+)', contenido)
    duracion = int(duracion_match.group(1)) if duracion_match else 1
    
    # Extraer áreas
    areas_match = re.search(r'Áreas integradas:\s*([^\n]+)', contenido)
    areas = areas_match.group(1).strip() if areas_match else ""
    
    # Extraer adaptaciones
    adaptaciones = extraer_adaptaciones(contenido)
    
    return {
        'titulo': titulo,
        'duracion_sesiones': duracion,
        'areas_curriculares': areas,
        'descripcion_breve': f"Proyecto: {titulo}",
        'contenido_completo': {'texto_completo': contenido},
        'adaptaciones_tea': adaptaciones.get('tea', ''),
        'adaptaciones_tdah': adaptaciones.get('tdah', ''),
        'adaptaciones_aacc': adaptaciones.get('aacc', ''),
    }


def extraer_adaptaciones(contenido):
    """Extrae adaptaciones específicas por tipo"""
    adaptaciones = {'tea': '', 'tdah': '', 'aacc': ''}
    
    # Buscar líneas que contengan adaptaciones específicas
    lineas = contenido.split('\n')
    
    for linea in lineas:
        # Buscar TEA
        if 'TEA' in linea and ':' in linea:
            adaptaciones['tea'] = linea.split(':', 1)[1].strip()
        
        # Buscar TDAH
        elif 'TDAH' in linea and ':' in linea:
            adaptaciones['tdah'] = linea.split(':', 1)[1].strip()
        
        # Buscar AACC
        elif 'AACC' in linea and ':' in linea:
            adaptaciones['aacc'] = linea.split(':', 1)[1].strip()
    
    return adaptaciones

def guardar_proyectos(proyectos):
    """Guarda proyectos en la base de datos"""
    contador = 0
    
    for proyecto_data in proyectos:
        proyecto = Proyecto(**proyecto_data)
        proyecto.save()
        contador += 1
        print(f"✅ Guardado: {proyecto.titulo}")
    
    print(f"\n🎉 Total guardados: {contador} proyectos")

def main():
    # Leer archivo
    ruta_archivo = 'activities_and_projects.txt'  # Ajusta la ruta
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as file:
            contenido = file.read()
        
        print("📖 Leyendo archivo...")
        proyectos = extraer_actividades(contenido)
        
        print(f"🔍 Encontradas {len(proyectos)} actividades")
        
        # Mostrar primera para verificar
        if proyectos:
            print(f"\n📋 Ejemplo: {proyectos[0]['titulo']}")
            print(f"⏱️ Duración: {proyectos[0]['duracion_sesiones']} sesiones")
            print(f"📚 Áreas: {proyectos[0]['areas_curriculares']}")
        
        # Guardar en BD
        respuesta = input("\n¿Guardar en base de datos? (s/n): ")
        if respuesta.lower() == 's':
            guardar_proyectos(proyectos)
        
    except FileNotFoundError:
        print(f"❌ No encontré el archivo: {ruta_archivo}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()