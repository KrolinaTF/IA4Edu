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
    patron_actividad = r'ACTIVIDAD\s+\d+:\s*"([^"]+)"'
    actividades = re.split(patron_actividad, contenido)
    
    proyectos = []
    
    for i in range(1, len(actividades), 2):
        if i + 1 < len(actividades):
            titulo = actividades[i].strip()
            contenido_actividad = actividades[i + 1].strip()
            
            proyecto_data = extraer_datos_proyecto(titulo, contenido_actividad)
            proyectos.append(proyecto_data)
    
    return proyectos

def extraer_objetivos(contenido):
    """Extrae objetivos/competencias del contenido"""
    objetivos = []
    
    # Buscar líneas que empiecen con "Competencias:"
    lineas = contenido.split('\n')
    for linea in lineas:
        if linea.strip().startswith('Competencias:'):
            competencia = linea.split(':', 1)[1].strip()
            objetivos.append(competencia)
    
    return '\n'.join(objetivos) if objetivos else "Objetivos por definir"

def extraer_datos_proyecto(titulo, contenido):
    """Extrae datos específicos de cada proyecto"""
    
    # Extraer duración
    duracion_match = re.search(r'Duración:\s*(\d+)', contenido)
    duracion = int(duracion_match.group(1)) if duracion_match else 1
    
    # Extraer áreas
    areas_match = re.search(r'Áreas integradas:\s*([^\n]+)', contenido)
    areas = areas_match.group(1).strip() if areas_match else ""
    
    # Extraer objetivos/competencias
    objetivos = extraer_objetivos(contenido)
    
    # Extraer adaptaciones
    adaptaciones = extraer_adaptaciones(contenido)
    
    return {
        'titulo': titulo,
        'duracion_sesiones': duracion,
        'areas_curriculares': areas,
        'objetivos': objetivos,
        'descripcion_breve': f"Proyecto: {titulo}",
        'contenido_completo': {'texto_completo': contenido},
        'adaptaciones_tea': adaptaciones.get('tea', ''),
        'adaptaciones_tdah': adaptaciones.get('tdah', ''),
        'adaptaciones_aacc': adaptaciones.get('aacc', ''),
    }

def extraer_adaptaciones(contenido):
    """Extrae adaptaciones específicas por tipo"""
    adaptaciones = {'tea': '', 'tdah': '', 'aacc': ''}
    
    lineas = contenido.split('\n')
    
    for linea in lineas:
        if 'TEA' in linea and ':' in linea:
            adaptaciones['tea'] = linea.split(':', 1)[1].strip()
        elif 'TDAH' in linea and ':' in linea:
            adaptaciones['tdah'] = linea.split(':', 1)[1].strip()
        elif 'AACC' in linea and ':' in linea:
            adaptaciones['aacc'] = linea.split(':', 1)[1].strip()
    
    return adaptaciones

def guardar_proyectos(proyectos):
    """Guarda o actualiza proyectos en la base de datos"""
    contador_nuevos = 0
    contador_actualizados = 0
    
    for proyecto_data in proyectos:
        titulo = proyecto_data['titulo']
        
        # VERIFICAR SI YA EXISTE
        proyecto_existente = Proyecto.objects.filter(titulo=titulo).first()
        
        if proyecto_existente:
            # ACTUALIZAR CAMPOS EXISTENTES
            campos_actualizados = []
            
            # Comparar y actualizar cada campo
            if proyecto_existente.duracion_sesiones != proyecto_data['duracion_sesiones']:
                proyecto_existente.duracion_sesiones = proyecto_data['duracion_sesiones']
                campos_actualizados.append('duración')
            
            if proyecto_existente.areas_curriculares != proyecto_data['areas_curriculares']:
                proyecto_existente.areas_curriculares = proyecto_data['areas_curriculares']
                campos_actualizados.append('áreas')
            
            if proyecto_existente.objetivos != proyecto_data['objetivos']:
                proyecto_existente.objetivos = proyecto_data['objetivos']
                campos_actualizados.append('objetivos')
            
            if proyecto_existente.adaptaciones_tea != proyecto_data['adaptaciones_tea']:
                proyecto_existente.adaptaciones_tea = proyecto_data['adaptaciones_tea']
                campos_actualizados.append('TEA')
            
            if proyecto_existente.adaptaciones_tdah != proyecto_data['adaptaciones_tdah']:
                proyecto_existente.adaptaciones_tdah = proyecto_data['adaptaciones_tdah']
                campos_actualizados.append('TDAH')
            
            if proyecto_existente.adaptaciones_aacc != proyecto_data['adaptaciones_aacc']:
                proyecto_existente.adaptaciones_aacc = proyecto_data['adaptaciones_aacc']
                campos_actualizados.append('AACC')
            
            # Siempre actualizar contenido completo
            proyecto_existente.contenido_completo = proyecto_data['contenido_completo']
            campos_actualizados.append('contenido')
            
            if campos_actualizados:
                proyecto_existente.save()
                print(f"🔄 Actualizado: {titulo} ({', '.join(campos_actualizados)})")
                contador_actualizados += 1
            else:
                print(f"✓ Sin cambios: {titulo}")
                
        else:
            # CREAR NUEVO
            proyecto = Proyecto(**proyecto_data)
            proyecto.save()
            contador_nuevos += 1
            print(f"✅ Nuevo: {titulo}")
    
    print(f"\n🎉 Nuevos creados: {contador_nuevos}")
    print(f"🔄 Actualizados: {contador_actualizados}")

def main():
    ruta_archivo = 'activities_and_projects.txt'
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as file:
            contenido = file.read()
        
        print("📖 Leyendo archivo...")
        proyectos = extraer_actividades(contenido)
        
        print(f"🔍 Encontradas {len(proyectos)} actividades en el archivo")
        
        # Mostrar preview
        if proyectos:
            print(f"\n📋 Ejemplo: {proyectos[0]['titulo']}")
            print(f"⏱️ Duración: {proyectos[0]['duracion_sesiones']} sesiones")
            print(f"📚 Áreas: {proyectos[0]['areas_curriculares']}")
            print(f"🎯 Objetivos: {proyectos[0]['objetivos'][:100]}...")
        
        # Guardar (con verificación de duplicados)
        respuesta = input("\n¿Procesar y guardar/actualizar proyectos? (s/n): ")
        if respuesta.lower() == 's':
            guardar_proyectos(proyectos)
        
    except FileNotFoundError:
        print(f"❌ No encontré el archivo: {ruta_archivo}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()