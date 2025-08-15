"""
Vistas para la interfaz de usuario del sistema de agentes ABP.
Se encarga de la presentación y captura de datos.
"""

import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("SistemaAgentesABP.UIViews")

class CLIViews:
    """Vistas para la interfaz de línea de comandos"""
    
    @staticmethod
    def mostrar_bienvenida():
        """Muestra mensaje de bienvenida"""
        print("\n🎓 SISTEMA DE AGENTES PARA ABP - ESTRUCTURA MEJORADA")
        print("=" * 60)
        print("Bienvenido al sistema de generación de actividades ABP para educación primaria")
        print("Este sistema le ayudará a crear actividades educativas adaptadas a las necesidades")
        print("específicas de estudiantes con distintos perfiles de aprendizaje.")
        print("=" * 60)
    
    @staticmethod
    def solicitar_prompt_inicial() -> str:
        """
        Solicita el prompt inicial al usuario
        
        Returns:
            Prompt ingresado por el usuario
        """
        print("\n📝 GENERACIÓN DE IDEAS")
        print("-" * 40)
        return input("Describa la actividad educativa que desea generar: ")
    
    @staticmethod
    def mostrar_ideas(ideas: List[Dict]):
        """
        Muestra las ideas generadas
        
        Args:
            ideas: Lista de ideas a mostrar
        """
        print("\n💡 IDEAS GENERADAS:")
        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. {idea.get('titulo', 'Sin título')}")
            print(f"   Descripción: {idea.get('descripcion', 'No disponible')}")
            print(f"   Nivel: {idea.get('nivel', 'No especificado')}")
            print(f"   Duración: {idea.get('duracion', 'No especificada')}")
            print(f"   Competencias: {idea.get('competencias', 'No especificadas')}")
    
    @staticmethod
    def mostrar_opciones_seleccion(ideas: List[Dict], hay_seleccion: bool = False):
        """
        Muestra las opciones disponibles para el usuario
        
        Args:
            ideas: Lista de ideas
            hay_seleccion: Indica si ya hay una selección activa
        """
        print(f"\n🎯 OPCIONES DISPONIBLES:")
        print(f"   1-{len(ideas)}: Seleccionar una de las ideas y continuar")
        print(f"   M: Me gusta alguna idea pero quiero matizarla/perfilarla")
        print(f"   0: Generar nuevas ideas con un prompt diferente")
        
        if hay_seleccion:
            print(f"   -1: Añadir más detalles a la idea seleccionada")
    
    @staticmethod
    def solicitar_seleccion() -> str:
        """
        Solicita selección al usuario
        
        Returns:
            Selección ingresada
        """
        return input(f"\n🎯 Su elección: ").strip().upper()
    
    @staticmethod
    def solicitar_indice_idea(max_ideas: int) -> int:
        """
        Solicita índice de idea a matizar
        
        Args:
            max_ideas: Número máximo de ideas
            
        Returns:
            Índice de idea seleccionada (1-based)
        """
        try:
            return int(input(f"¿Qué idea desea matizar? (1-{max_ideas}): "))
        except ValueError:
            return -1
    
    @staticmethod
    def solicitar_matizaciones() -> str:
        """
        Solicita matizaciones para una idea
        
        Returns:
            Texto con matizaciones
        """
        return input("📝 ¿Cómo desea matizar/perfilar la idea?: ")
    
    @staticmethod
    def solicitar_nuevo_prompt() -> str:
        """
        Solicita nuevo prompt para generar ideas
        
        Returns:
            Nuevo prompt
        """
        return input("\n📝 Ingrese un nuevo prompt para generar diferentes ideas: ")
    
    @staticmethod
    def solicitar_detalles_adicionales(titulo: str) -> str:
        """
        Solicita detalles adicionales para una actividad
        
        Args:
            titulo: Título de la actividad
            
        Returns:
            Detalles adicionales
        """
        return input(f"\n📝 ¿Desea añadir detalles específicos sobre '{titulo}'? (Enter para continuar, o escriba detalles): ")
    
    @staticmethod
    def mostrar_mensaje_procesando():
        """Muestra mensaje de procesamiento"""
        print("\n🚀 Procesando su solicitud, esto puede tomar unos momentos...")
    
    @staticmethod
    def mostrar_mensaje_exito(mensaje: str):
        """
        Muestra mensaje de éxito
        
        Args:
            mensaje: Mensaje a mostrar
        """
        print(f"✅ {mensaje}")
    
    @staticmethod
    def mostrar_mensaje_error(mensaje: str):
        """
        Muestra mensaje de error
        
        Args:
            mensaje: Mensaje a mostrar
        """
        print(f"❌ {mensaje}")
    
    @staticmethod
    def mostrar_resumen_proceso(proyecto_final: dict):
        """
        Muestra resumen del proceso ejecutado
        
        Args:
            proyecto_final: Proyecto final generado
        """
        # Buscar estadísticas en múltiples ubicaciones posibles
        estadisticas = {}
        
        # Opción 1: En validacion.estadisticas
        validacion = proyecto_final.get('validacion', {})
        if isinstance(validacion, dict):
            estadisticas = validacion.get('estadisticas', {})
        
        # Opción 2: Directamente en proyecto_final
        if not estadisticas:
            estadisticas = proyecto_final.get('estadisticas', {})
        
        # Opción 3: Calcular en tiempo real desde los datos disponibles
        if not estadisticas:
            resultados = proyecto_final.get('resultados_agentes', {})
            estadisticas = {
                'total_agentes_ejecutados': len([k for k, v in resultados.items() if v]),
                'total_mensajes': sum(1 for v in resultados.values() if v),
                'errores_encontrados': 0  # Podríamos detectar errores en los resultados
            }
            
        print(f"\n📏 RESUMEN DEL PROCESO:")
        print(f"   • Agentes ejecutados: {estadisticas.get('total_agentes_ejecutados', 'N/A')}")
        print(f"   • Mensajes intercambiados: {estadisticas.get('total_mensajes', 'N/A')}")
        print(f"   • Errores encontrados: {estadisticas.get('errores_encontrados', 'N/A')}")
        
        coherencia = validacion.get('coherencia_final', {})
        if not isinstance(coherencia, dict):
            coherencia = {}
            
        if coherencia.get('sugerencias'):
            print(f"\n💡 SUGERENCIAS:")
            for sugerencia in coherencia['sugerencias']:
                print(f"   • {sugerencia}")
        
        if coherencia.get('problemas'):
            print(f"\n⚠️ PROBLEMAS DETECTADOS:")
            for problema in coherencia['problemas']:
                print(f"   • {problema}")
    
    @staticmethod
    def mostrar_validacion_final(proyecto_final: dict) -> bool:
        """
        Muestra información de validación y solicita aprobación
        
        Args:
            proyecto_final: Proyecto final generado
            
        Returns:
            True si el usuario aprueba el proyecto, False en caso contrario
        """
        print("\n🔍 VALIDACIÓN FINAL:")
        
        # DETECTAR ESTRUCTURA: NUEVA UNIFICADA vs MVP vs LEGACY
        if 'actividad_generada' in proyecto_final:
            # NUEVA ESTRUCTURA UNIFICADA (v3.0)
            proyecto_base = proyecto_final.get('actividad_generada', {})
            resultados = proyecto_final
            print(f"   DEBUG - ESTRUCTURA UNIFICADA V3 DETECTADA")
        elif 'tipo' in proyecto_final and 'flujo_mvp_integrado' in str(proyecto_final['tipo']):
            # ESTRUCTURA MVP: El proyecto es directamente los resultados
            proyecto_base = proyecto_final.get('actividad_personalizada', {})
            resultados = proyecto_final  # El proyecto completo son los resultados
            print(f"   DEBUG - ESTRUCTURA MVP DETECTADA")
        else:
            # ESTRUCTURA LEGACY
            proyecto_base = proyecto_final.get('proyecto_base', {})
            if not isinstance(proyecto_base, dict):
                proyecto_base = {}
                
            resultados = proyecto_final.get('resultados_agentes', {})
            if not isinstance(resultados, dict):
                resultados = {}
            print(f"   DEBUG - ESTRUCTURA LEGACY DETECTADA")
        
        print(f"Título: {proyecto_base.get('titulo', 'N/A')}")
        print(f"Descripción: {proyecto_base.get('descripcion', proyecto_final.get('descripcion_actividad', 'N/A'))}")
        
        # ===== INFORMACIÓN DETALLADA DE TAREAS =====
        tareas_list = []
        actividad_info = {}
        
        # PRIORIDAD 1: Buscar en estructura unificada v3.0
        if 'actividad_generada' in resultados:
            # Nueva estructura unificada que sigue formato k_*.json
            actividad_generada = resultados['actividad_generada']
            
            # Extraer tareas de todas las etapas
            tareas_list = []
            for etapa in actividad_generada.get('etapas', []):
                tareas_etapa = etapa.get('tareas', [])
                tareas_list.extend(tareas_etapa)
            
            actividad_info = actividad_generada
            print(f"   DEBUG - Estructura UNIFICADA V3 detectada: {len(tareas_list)} tareas, actividad: {actividad_info.get('titulo', 'Sin título')}")
            
        # PRIORIDAD 2: Buscar en estructura del flujo MVP integrado
        elif 'tipo' in resultados and 'flujo_mvp_integrado' in str(resultados.get('tipo', '')):
            # Estructura del flujo MVP mejorado
            tareas_list = resultados.get('tareas_especificas', [])
            actividad_info = resultados.get('actividad_personalizada', {})
            print(f"   DEBUG - Estructura MVP detectada: {len(tareas_list)} tareas, actividad: {actividad_info.get('titulo', 'Sin título')}")
            
        # PRIORIDAD 3: Buscar en la estructura anterior: resultados_agentes -> analizador_tareas
        elif 'analizador_tareas' in resultados:
            analizador_data = resultados['analizador_tareas']
            if isinstance(analizador_data, list):
                tareas_list = analizador_data
            elif isinstance(analizador_data, dict):
                # Extraer información de actividad
                actividad_info = analizador_data.get('actividad', {})
                
                # Buscar tareas en diferentes ubicaciones
                tareas_list = (
                    analizador_data.get('tareas_extraidas', []) or
                    analizador_data.get('tareas', []) or
                    []
                )
        
        # Fallback: buscar en estructura antigua
        if not tareas_list:
            tareas_info = resultados.get('tareas', {})
            if isinstance(tareas_info, list):
                tareas_list = tareas_info
            else:
                tareas_list = tareas_info.get('tareas', []) if isinstance(tareas_info, dict) else []
        
        print(f"Tareas generadas: {len(tareas_list)}")
        print(f"   DEBUG - Estructura de resultados: {list(resultados.keys())}")
        print(f"   DEBUG - Tipo de resultados: {resultados.get('tipo', 'N/A')}")
        print(f"   DEBUG - Actividad info keys: {list(actividad_info.keys()) if actividad_info else 'Vacío'}")
        
        # ===== MOSTRAR LISTADO DE TAREAS =====
        if 'actividad_generada' in resultados:
            # MOSTRAR ETAPAS Y TAREAS ESTRUCTURADAS (FORMATO K_*.JSON)
            print(f"\n📋 ESTRUCTURA DE LA ACTIVIDAD:")
            actividad = resultados['actividad_generada']
            
            print(f"   Título: {actividad.get('titulo', 'Sin título')}")
            print(f"   Objetivo: {actividad.get('objetivo', 'Sin objetivo')[:100]}...")
            print(f"   Duración: {actividad.get('duracion_minutos', 'No especificada')}")
            
            # Mostrar recursos
            recursos = actividad.get('recursos', [])
            if recursos:
                print(f"\n🎨 RECURSOS NECESARIOS:")
                for recurso in recursos[:5]:  # Máximo 5 recursos
                    print(f"   • {recurso}")
            
            # Mostrar etapas y tareas
            etapas = actividad.get('etapas', [])
            print(f"\n🔄 ETAPAS DE LA ACTIVIDAD ({len(etapas)}):")
            
            for i, etapa in enumerate(etapas, 1):
                print(f"\n   🔸 ETAPA {i}: {etapa.get('nombre', 'Sin nombre')}")
                print(f"      {etapa.get('descripcion', 'Sin descripción')[:80]}...")
                
                tareas_etapa = etapa.get('tareas', [])
                if tareas_etapa:
                    print(f"      📋 Tareas ({len(tareas_etapa)}):")
                    for j, tarea in enumerate(tareas_etapa[:3], 1):  # Máximo 3 tareas por etapa
                        nombre = tarea.get('nombre', 'Sin nombre')[:40]
                        formato = tarea.get('formato_asignacion', 'N/A')
                        print(f"         {j}. {nombre} ({formato})")
                        
        elif tareas_list and len(tareas_list) > 0:
            # MOSTRAR TAREAS EN FORMATO ANTERIOR (COMPATIBILIDAD)
            print(f"\n📋 TAREAS ESPECÍFICAS:")
            print(f"   DEBUG - Tipo tareas_list: {type(tareas_list)}")
            print(f"   DEBUG - Primer elemento: {tareas_list[0] if tareas_list else 'Vacío'}")
            
            for i, tarea in enumerate(tareas_list[:5], 1):  # Mostrar máximo 5
                print(f"   DEBUG - Tarea {i} tipo: {type(tarea)}")
                
                if isinstance(tarea, dict):
                    # Es un diccionario
                    tarea_id = tarea.get('id', f'tarea_{i:02d}')
                    descripcion = tarea.get('descripcion', tarea.get('nombre', 'Sin descripción'))
                    complejidad = tarea.get('complejidad', 'N/A')
                elif hasattr(tarea, 'id') and hasattr(tarea, 'descripcion'):
                    # Es un objeto Tarea (dataclass)
                    tarea_id = tarea.id
                    descripcion = tarea.descripcion
                    complejidad = getattr(tarea, 'complejidad', 'N/A')
                else:
                    # Fallback
                    tarea_id = f'tarea_{i:02d}'
                    descripcion = str(tarea)[:50]
                    complejidad = 'N/A'
                
                print(f"   {i}. {descripcion} (Complejidad: {complejidad})")
            
            if len(tareas_list) > 5:
                print(f"   ... y {len(tareas_list) - 5} tareas más")
        
        # ===== MOSTRAR DETALLE DE LA ACTIVIDAD =====
        if actividad_info:
            print(f"\n📚 DETALLE DE LA ACTIVIDAD:")
            print(f"   • Objetivo: {actividad_info.get('objetivo', 'No especificado')}")
            print(f"   • Duración: {actividad_info.get('duracion_minutos', 'No especificada')}")
            print(f"   • Nivel: {actividad_info.get('nivel_educativo', '4º Primaria')}")
            
            # Mostrar etapas si existen
            etapas = actividad_info.get('etapas', [])
            if etapas:
                print(f"   • Etapas ({len(etapas)}):")
                for i, etapa in enumerate(etapas[:3], 1):  # Mostrar máximo 3
                    if isinstance(etapa, dict):
                        print(f"     {i}. {etapa.get('nombre', f'Etapa {i}')}")
        
        # ===== MOSTRAR ASIGNACIONES DE ESTUDIANTES =====
        asignaciones = None
        
        # PRIORIDAD 1: Buscar asignaciones en flujo MVP
        if 'asignaciones_neurotipos' in resultados:
            asignaciones = resultados['asignaciones_neurotipos']
        # PRIORIDAD 2: Buscar en estructura anterior
        elif 'optimizador_asignaciones' in resultados:
            asignaciones = resultados['optimizador_asignaciones']
        
        if asignaciones:
            if isinstance(asignaciones, dict) and asignaciones:
                print(f"\n👥 ASIGNACIONES POR ESTUDIANTE:")
                
                # Crear mapeo de ID de tarea -> descripción
                tarea_descripciones = {}
                print(f"   DEBUG - Creando mapeo de {len(tareas_list)} tareas")
                if isinstance(tareas_list, list):
                    for tarea in tareas_list:
                        print(f"   DEBUG - Tipo de tarea: {type(tarea)}")
                        
                        if isinstance(tarea, dict):
                            # Es un diccionario
                            tarea_id = tarea.get('id', '')
                            descripcion = tarea.get('descripcion', tarea.get('nombre', tarea_id))
                        elif hasattr(tarea, 'id') and hasattr(tarea, 'descripcion'):
                            # Es un objeto Tarea (dataclass)
                            tarea_id = tarea.id
                            descripcion = tarea.descripcion
                        else:
                            # Intentar convertir a string
                            tarea_id = f'tarea_unknown_{len(tarea_descripciones)+1}'
                            descripcion = str(tarea)[:50]
                        
                        # Limitar descripción a 40 caracteres para legibilidad
                        if len(descripcion) > 40:
                            descripcion = descripcion[:37] + "..."
                        
                        tarea_descripciones[tarea_id] = descripcion
                        print(f"   DEBUG - Mapeado: {tarea_id} -> {descripcion}")
                
                print(f"   DEBUG - Mapeo final: {tarea_descripciones}")
                
                for estudiante_id, tareas_asignadas in asignaciones.items():
                    if isinstance(tareas_asignadas, list) and tareas_asignadas:
                        # Convertir IDs a descripciones
                        descripciones_tareas = []
                        for tarea_id in tareas_asignadas[:2]:  # Mostrar máximo 2
                            descripcion = tarea_descripciones.get(tarea_id, tarea_id)
                            descripciones_tareas.append(descripcion)
                        
                        tareas_texto = ', '.join(descripciones_tareas)
                        if len(tareas_asignadas) > 2:
                            tareas_texto += '...'
                        
                        print(f"   • Estudiante {estudiante_id}: {len(tareas_asignadas)} tareas ({tareas_texto})")
        
        # Validación manual
        return input("\n✅ ¿Aprueba el proyecto generado? (s/n): ").lower().startswith('s')