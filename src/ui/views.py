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
    def solicitar_input_estructurado_progresivo() -> Dict:
        """
        NUEVO: Flujo progresivo para crear actividades paso a paso
        
        Returns:
            Diccionario con información básica para generar ideas
        """
        print("\n🎓 CREACIÓN PROGRESIVA DE ACTIVIDAD ABP")
        print("=" * 50)
        print("Vamos a crear su actividad paso a paso, de lo general a lo específico")
        
        input_basico = {}
        
        # PASO 1: MATERIA
        input_basico['materia'] = CLIViews._solicitar_materia()
        
        # PASO 2: TEMA
        input_basico['tema'] = CLIViews._solicitar_tema()
        
        # PASO 3: ¿TIENES ALGO EN MENTE?
        input_basico['prompt_usuario'] = CLIViews._solicitar_idea_previa()
        
        # PASO 4: DURACIÓN
        input_basico['duracion'] = CLIViews._solicitar_duracion_sesiones()
        
        return input_basico
    
    @staticmethod
    def solicitar_estructura_post_seleccion(actividad_seleccionada: Dict) -> Dict:
        """
        Solicita estructura detallada DESPUÉS de seleccionar/matizar la idea
        
        Args:
            actividad_seleccionada: Actividad que el profesor ha elegido
            
        Returns:
            Diccionario con estructura detallada de fases
        """
        print(f"\n🔧 ESTRUCTURA DETALLADA DE LA ACTIVIDAD")
        print("=" * 50)
        print(f"Actividad seleccionada: {actividad_seleccionada.get('titulo', 'Sin título')}")
        print("\nAhora vamos a definir cómo estructurar esta actividad específicamente:")
        
        estructura = {}
        
        # FASE 1: ¿PREPARACIÓN?
        estructura['preparacion'] = CLIViews._configurar_fase_preparacion()
        
        # FASE 2: EJECUCIÓN (obligatoria)
        estructura['ejecucion'] = CLIViews._configurar_fase_ejecucion()
        
        # FASE 3: ¿REFLEXIÓN?
        estructura['reflexion'] = CLIViews._configurar_fase_reflexion()
        
        # FASE 4: ¿RECOGIDA/LIMPIEZA?
        estructura['recogida'] = CLIViews._configurar_fase_recogida()
        
        return estructura
    
    # ========== MÉTODOS DE APOYO PARA EL FLUJO PROGRESIVO ==========
    
    @staticmethod
    def _solicitar_materia() -> str:
        """Solicita materia de forma simple"""
        print(f"\n📚 PASO 1: MATERIA/ÁREA")
        print("   1. Matemáticas")
        print("   2. Lengua Castellana") 
        print("   3. Ciencias Naturales")
        print("   4. Ciencias Sociales")
        print("   5. Educación Artística")
        print("   6. Educación Física")
        print("   7. Interdisciplinar")
        print("   8. Otra")
        
        materias_map = {
            '1': 'Matemáticas', '2': 'Lengua Castellana', '3': 'Ciencias Naturales',
            '4': 'Ciencias Sociales', '5': 'Educación Artística', '6': 'Educación Física',
            '7': 'Interdisciplinar', '8': 'Otra'
        }
        
        while True:
            opcion = input("Seleccione materia (1-8): ").strip()
            if opcion in materias_map:
                if opcion == '8':
                    return input("Especifique la materia: ").strip()
                else:
                    return materias_map[opcion]
            print("❌ Opción inválida. Seleccione 1-8.")
    
    @staticmethod
    def _solicitar_tema() -> str:
        """Solicita tema específico"""
        print(f"\n🎯 PASO 2: TEMA ESPECÍFICO")
        return input("¿Qué tema concreto quiere trabajar? (ej: 'Fracciones', 'El cuerpo humano'):\n> ").strip()
    
    @staticmethod
    def _solicitar_idea_previa() -> str:
        """Pregunta si tiene algo específico en mente"""
        print(f"\n💭 PASO 3: ¿TIENES ALGO ESPECÍFICO EN MENTE?")
        tiene_idea = input("¿Ya tienes una idea específica de actividad? (s/n): ").strip().lower()
        
        if tiene_idea.startswith('s'):
            return input("Describe tu idea:\n> ").strip()
        else:
            return ""
    
    @staticmethod
    def _solicitar_duracion_sesiones() -> Dict:
        """Solicita duración en sesiones"""
        print(f"\n⏱️ PASO 4: DURACIÓN")
        print("   1. Una sesión (45 min)")
        print("   2. Dos sesiones (90 min)")
        print("   3. Una semana (5 sesiones)")
        print("   4. Personalizada")
        
        while True:
            opcion = input("¿Cuánto tiempo tienes disponible? (1-4): ").strip()
            if opcion == '1':
                return {'valor': 45, 'descripcion': 'Una sesión', 'sesiones': 1}
            elif opcion == '2':
                return {'valor': 90, 'descripcion': 'Dos sesiones', 'sesiones': 2}
            elif opcion == '3':
                return {'valor': 225, 'descripcion': 'Una semana', 'sesiones': 5}
            elif opcion == '4':
                try:
                    sesiones = int(input("¿Cuántas sesiones? "))
                    minutos = sesiones * 45
                    return {'valor': minutos, 'descripcion': f'{sesiones} sesiones', 'sesiones': sesiones}
                except ValueError:
                    print("❌ Ingrese un número válido.")
            else:
                print("❌ Opción inválida. Seleccione 1-4.")
    
    @staticmethod
    def _configurar_fase_preparacion() -> Dict:
        """Configura la fase de preparación opcional"""
        print(f"\n🏗️ FASE DE PREPARACIÓN")
        incluir = input("¿Quieres incluir una fase de preparación/introducción? (s/n): ").strip().lower()
        
        if not incluir.startswith('s'):
            return {'incluir': False}
        
        print("¿Cómo trabajarán en la preparación?")
        modalidad = CLIViews._seleccionar_modalidad_simple()
        
        # Preguntar sobre reparto específico de tareas
        reparto = input("¿Quieres repartir tareas específicas de preparación entre estudiantes? (s/n): ").strip().lower()
        repartir_tareas = reparto.startswith('s')
        
        return {
            'incluir': True,
            'modalidad': modalidad,
            'repartir_tareas': repartir_tareas,
            'nombre': 'Preparación e Introducción'
        }
    
    @staticmethod
    def _configurar_fase_ejecucion() -> Dict:
        """Configura la fase de ejecución (obligatoria)"""
        print(f"\n🚀 FASE DE EJECUCIÓN (Principal)")
        print("¿Qué aspectos quieres incluir en la ejecución? (puedes elegir varios)")
        
        aspectos_disponibles = {
            '1': 'investigación',
            '2': 'creatividad', 
            '3': 'experimentación',
            '4': 'colaboración',
            '5': 'presentación',
            '6': 'análisis',
            '7': 'construcción/creación'
        }
        
        print("   1. Investigación  2. Creatividad  3. Experimentación")
        print("   4. Colaboración   5. Presentación  6. Análisis")
        print("   7. Construcción/Creación")
        
        aspectos_seleccionados = []
        while True:
            seleccion = input("Selecciona aspectos (ej: '1,3,5' o Enter para terminar): ").strip()
            if not seleccion:
                break
            
            try:
                opciones = [op.strip() for op in seleccion.split(',')]
                for opcion in opciones:
                    if opcion in aspectos_disponibles:
                        aspecto = aspectos_disponibles[opcion]
                        if aspecto not in aspectos_seleccionados:
                            aspectos_seleccionados.append(aspecto)
                            print(f"✅ Añadido: {aspecto}")
                break
            except:
                print("❌ Formato inválido. Usa números separados por comas.")
        
        if not aspectos_seleccionados:
            aspectos_seleccionados = ['colaboración']  # Default
        
        print("¿Cómo trabajarán en la ejecución?")
        modalidad = CLIViews._seleccionar_modalidad_simple()
        
        # Preguntar sobre reparto específico de tareas
        reparto = input("¿Quieres repartir tareas específicas de ejecución entre estudiantes? (s/n): ").strip().lower()
        repartir_tareas = reparto.startswith('s')
        
        return {
            'incluir': True,
            'aspectos': aspectos_seleccionados,
            'modalidad': modalidad,
            'repartir_tareas': repartir_tareas,
            'nombre': 'Ejecución de la Actividad'
        }
    
    @staticmethod
    def _configurar_fase_reflexion() -> Dict:
        """Configura la fase de reflexión opcional"""
        print(f"\n🤔 FASE DE REFLEXIÓN")
        incluir = input("¿Quieres incluir una fase de reflexión/evaluación? (s/n): ").strip().lower()
        
        if not incluir.startswith('s'):
            return {'incluir': False}
        
        print("¿Cómo trabajarán en la reflexión?")
        modalidad = CLIViews._seleccionar_modalidad_simple()
        
        # Preguntar sobre reparto específico de tareas
        reparto = input("¿Quieres repartir tareas específicas de reflexión entre estudiantes? (s/n): ").strip().lower()
        repartir_tareas = reparto.startswith('s')
        
        return {
            'incluir': True,
            'modalidad': modalidad,
            'repartir_tareas': repartir_tareas,
            'nombre': 'Reflexión y Evaluación'
        }
    
    @staticmethod
    def _configurar_fase_recogida() -> Dict:
        """Configura la fase de recogida/limpieza opcional"""
        print(f"\n🧹 FASE DE RECOGIDA Y ORGANIZACIÓN")
        incluir = input("¿Incluir fase de recogida de materiales y limpieza? (s/n): ").strip().lower()
        
        if not incluir.startswith('s'):
            return {'incluir': False}
        
        # Preguntar sobre reparto de tareas
        reparto = input("¿Quieres repartir tareas específicas de limpieza entre estudiantes? (s/n): ").strip().lower()
        repartir_tareas = reparto.startswith('s')
        
        modalidad = CLIViews._seleccionar_modalidad_simple()
        
        return {
            'incluir': True,
            'modalidad': modalidad,
            'repartir_tareas': repartir_tareas,
            'nombre': 'Recogida y Organización'
        }
    
    @staticmethod
    def _seleccionar_modalidad_simple() -> str:
        """Selector simple de modalidad"""
        print("   1. Individual  2. Parejas  3. Grupos pequeños  4. Grupos grandes  5. Toda la clase")
        
        modalidades_map = {
            '1': 'individual', '2': 'parejas', '3': 'grupos_pequeños',
            '4': 'grupos_grandes', '5': 'clase_completa'
        }
        
        while True:
            opcion = input("¿Cómo trabajan? (1-5): ").strip()
            if opcion in modalidades_map:
                modalidad = modalidades_map[opcion]
                print(f"✅ {modalidad.replace('_', ' ')}")
                return modalidad
            print("❌ Opción inválida. Seleccione 1-5.")
    
    @staticmethod
    def _mostrar_resumen_input_estructurado(input_data: Dict):
        """Muestra resumen del input estructurado"""
        print(f"\n📋 RESUMEN DE LA ACTIVIDAD A GENERAR:")
        print("=" * 50)
        print(f"📚 Materia: {input_data.get('materia', 'N/A')}")
        print(f"🎯 Tema: {input_data.get('tema', 'N/A')}")
        print(f"⏱️ Duración: {input_data.get('duracion', {}).get('descripcion', 'N/A')}")
        
        modalidades = input_data.get('modalidades', [])
        if modalidades:
            modalidades_texto = ', '.join(str(m) for m in modalidades).replace('_', ' ')
            print(f"👥 Modalidades: {modalidades_texto}")
        
        estructura = input_data.get('estructura_fases', {})
        if estructura.get('tipo') != 'libre':
            print(f"🔄 Estructura: {estructura.get('tipo', 'N/A').title()}")
            fases = estructura.get('fases', [])
            if fases:
                for i, fase in enumerate(fases, 1):
                    print(f"   {i}. {fase}")
        
        contexto = input_data.get('contexto_adicional', '')
        if contexto:
            print(f"💡 Contexto: {contexto[:100]}{'...' if len(contexto) > 100 else ''}")
        
        # Mostrar estructura detallada de fases si existe
        estructura = input_data.get('estructura_fases', {})
        if estructura.get('fases_detalladas'):
            print(f"\n🔄 FASES Y MODALIDADES DETALLADAS:")
            for i, fase in enumerate(estructura['fases_detalladas'], 1):
                modalidad = fase.get('modalidad', 'N/A').replace('_', ' ')
                print(f"   {i}. {fase.get('nombre', 'Sin nombre')} ({modalidad})")
    
    @staticmethod
    def _configurar_modalidades_por_fase(fases_base: List[str], tipo_estructura: str) -> Dict:
        """
        Configura modalidades específicas para cada fase
        
        Args:
            fases_base: Lista de nombres de fases
            tipo_estructura: Tipo de estructura seleccionada
            
        Returns:
            Diccionario con estructura completa
        """
        print(f"\n📋 CONFIGURACIÓN POR FASE:")
        print("Para cada fase, seleccione cómo trabajarán los estudiantes:")
        print("   1. Individual  2. Parejas  3. Grupos pequeños  4. Grupos grandes  5. Toda la clase")
        
        fases_detalladas = []
        modalidades_map = {
            '1': 'individual',
            '2': 'parejas', 
            '3': 'grupos_pequeños',
            '4': 'grupos_grandes',
            '5': 'clase_completa'
        }
        
        for i, fase_nombre in enumerate(fases_base, 1):
            print(f"\n🔸 FASE {i}: {fase_nombre}")
            
            while True:
                try:
                    modalidad_opcion = input(f"¿Cómo trabajan en esta fase? (1-5): ").strip()
                    
                    if modalidad_opcion in modalidades_map:
                        modalidad = modalidades_map[modalidad_opcion]
                        modalidad_texto = modalidad.replace('_', ' ')
                        
                        fases_detalladas.append({
                            'nombre': fase_nombre,
                            'modalidad': modalidad,
                            'orden': i
                        })
                        
                        print(f"✅ {fase_nombre} → {modalidad_texto}")
                        break
                    else:
                        print("❌ Opción inválida. Seleccione 1-5.")
                except:
                    print("❌ Entrada inválida. Intente de nuevo.")
        
        return {
            'tipo': tipo_estructura,
            'fases': [fase['nombre'] for fase in fases_detalladas],
            'fases_detalladas': fases_detalladas
        }
    
    @staticmethod
    def _configurar_fases_personalizadas() -> Dict:
        """
        Permite al usuario definir fases completamente personalizadas
        
        Returns:
            Diccionario con estructura personalizada
        """
        print(f"\n🛠️ FASES PERSONALIZADAS:")
        print("Defina sus propias fases (mínimo 2, máximo 5)")
        
        fases_detalladas = []
        modalidades_map = {
            '1': 'individual',
            '2': 'parejas',
            '3': 'grupos_pequeños', 
            '4': 'grupos_grandes',
            '5': 'clase_completa'
        }
        
        for i in range(1, 6):  # Máximo 5 fases
            print(f"\n📝 FASE {i}:")
            nombre_fase = input(f"Nombre de la fase {i} (o Enter para terminar): ").strip()
            
            if not nombre_fase:
                if i >= 3:  # Mínimo 2 fases
                    break
                else:
                    print("❌ Debe definir al menos 2 fases.")
                    continue
            
            print("Modalidad de trabajo:")
            print("   1. Individual  2. Parejas  3. Grupos pequeños  4. Grupos grandes  5. Toda la clase")
            
            while True:
                try:
                    modalidad_opcion = input(f"¿Cómo trabajan en '{nombre_fase}'? (1-5): ").strip()
                    
                    if modalidad_opcion in modalidades_map:
                        modalidad = modalidades_map[modalidad_opcion]
                        modalidad_texto = modalidad.replace('_', ' ')
                        
                        fases_detalladas.append({
                            'nombre': nombre_fase,
                            'modalidad': modalidad,
                            'orden': i
                        })
                        
                        print(f"✅ {nombre_fase} → {modalidad_texto}")
                        break
                    else:
                        print("❌ Opción inválida. Seleccione 1-5.")
                except:
                    print("❌ Entrada inválida. Intente de nuevo.")
        
        if len(fases_detalladas) < 2:
            print("❌ Se requieren al menos 2 fases. Usando estructura simple por defecto.")
            return CLIViews._configurar_modalidades_por_fase(
                ['Introducción y Preparación', 'Desarrollo y Práctica', 'Aplicación y Cierre'], 
                'simple'
            )
        
        return {
            'tipo': 'personalizada',
            'fases': [fase['nombre'] for fase in fases_detalladas],
            'fases_detalladas': fases_detalladas
        }
    
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
        
        # Opción 3: Calcular estadísticas reales basadas en la estructura actual
        if not estadisticas:
            # Detectar si hubo debate (estructura híbrida)
            metadatos = proyecto_final.get('metadatos', {})
            arquitectura = metadatos.get('arquitectura', '')
            
            if arquitectura == 'debate_consenso':
                # Estructura de debate: analizador, perfilador, optimizador + coordinador
                estadisticas = {
                    'total_agentes_ejecutados': 4,  # analizador, perfilador, optimizador, coordinador
                    'total_mensajes': 6,  # debate rounds + processing
                    'errores_encontrados': 0
                }
            else:
                # Estructura legacy
                resultados = proyecto_final.get('resultados_agentes', {})
                estadisticas = {
                    'total_agentes_ejecutados': len([k for k, v in resultados.items() if v]),
                    'total_mensajes': sum(1 for v in resultados.values() if v),
                    'errores_encontrados': 0
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
        """
        print("\n🔍 VALIDACIÓN FINAL:")
        
        # DETECTAR ESTRUCTURA CORRECTA PARA EL FLUJO ACTUAL
        if 'actividad_generada' in proyecto_final:
            # NUEVA ESTRUCTURA UNIFICADA (v3.0)
            proyecto_base = proyecto_final.get('actividad_generada', {})
            resultados = proyecto_final
            print(f"   DEBUG - ESTRUCTURA UNIFICADA V3 DETECTADA")
        elif 'actividad_personalizada' in proyecto_final:
            # ESTRUCTURA MVP ACTUAL - ESTE ES EL CASO QUE TENEMOS
            proyecto_base = proyecto_final.get('actividad_personalizada', {})
            resultados = proyecto_final
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
        print(f"Descripción: {proyecto_base.get('descripcion', proyecto_base.get('objetivo', 'N/A'))}")
        
        # ===== INFORMACIÓN DETALLADA DE TAREAS =====
        tareas_list = []
        actividad_info = {}
        
        # PRIORIDAD 1: Buscar en tareas_especificas (estructura debate híbrido) PRIMERO
        if 'tareas_especificas' in proyecto_final:
            tareas_list = proyecto_final['tareas_especificas']
            if not isinstance(tareas_list, list):
                tareas_list = []
            print(f"   DEBUG - Estructura DEBATE HÍBRIDO detectada: {len(tareas_list)} tareas")
            
        # PRIORIDAD 2: Buscar en estructura MVP actual
        elif 'actividad_personalizada' in proyecto_final:
            actividad_personalizada = proyecto_final['actividad_personalizada']
            actividad_info = actividad_personalizada
            
            # Extraer tareas de las etapas
            etapas = actividad_personalizada.get('etapas', [])
            for etapa in etapas:
                tareas_etapa = etapa.get('tareas', [])
                tareas_list.extend(tareas_etapa)
            
            print(f"   DEBUG - Estructura MVP actual: {len(tareas_list)} tareas, actividad: {actividad_info.get('titulo', 'Sin título')}")
        
        # PRIORIDAD 3: Buscar en estructura unificada v3.0
        elif 'actividad_generada' in resultados:
            actividad_generada = resultados['actividad_generada']
            
            # Extraer tareas de todas las etapas
            for etapa in actividad_generada.get('etapas', []):
                tareas_etapa = etapa.get('tareas', [])
                tareas_list.extend(tareas_etapa)
            
            actividad_info = actividad_generada
            print(f"   DEBUG - Estructura UNIFICADA V3 detectada: {len(tareas_list)} tareas")
            
        # FALLBACK: Buscar en estructura legacy
        else:
            tareas_info = resultados.get('tareas', {})
            if isinstance(tareas_info, list):
                tareas_list = tareas_info
            else:
                tareas_list = tareas_info.get('tareas', []) if isinstance(tareas_info, dict) else []
        
        print(f"Tareas generadas: {len(tareas_list)}")
        print(f"   DEBUG - Estructura de resultados: {list(proyecto_final.keys())}")
        
        # MOSTRAR ASIGNACIONES SI EXISTEN
        if 'asignaciones_neurotipos' in proyecto_final:
            asignaciones = proyecto_final['asignaciones_neurotipos']
            if isinstance(asignaciones, dict) and 'asignaciones' in asignaciones:
                num_asignaciones = len(asignaciones['asignaciones'])
                print(f"Asignaciones generadas: {num_asignaciones} estudiantes")
            else:
                print(f"Asignaciones generadas: Disponibles")
        
        # MOSTRAR DETALLES DE ETAPAS Y TAREAS
        if tareas_list:
            print(f"\n📋 ESTRUCTURA DE LA ACTIVIDAD:")
            if actividad_info:
                print(f"   Título: {actividad_info.get('titulo', 'Sin título')}")
                print(f"   Objetivo: {actividad_info.get('objetivo', 'Sin objetivo')[:100]}...")
                print(f"   Duración: {actividad_info.get('duracion_minutos', 'No especificada')}")
            
            # MOSTRAR ETAPAS ORGANIZADAS - ADAPTADO PARA DEBATE HÍBRIDO
            etapas = []
            
            # PRIORIDAD 1: Etapas desde actividad_personalizada (estructura MVP)
            if 'actividad_personalizada' in proyecto_final:
                etapas = proyecto_final['actividad_personalizada'].get('etapas', [])
            
            # PRIORIDAD 2: Si no hay etapas, crear desde tareas_especificas agrupándolas por etapa
            if not etapas and 'tareas_especificas' in proyecto_final:
                # Agrupar tareas por etapa
                tareas_por_etapa = {}
                for tarea in proyecto_final['tareas_especificas']:
                    if isinstance(tarea, dict):
                        nombre_etapa = tarea.get('etapa', 'Etapa Principal')
                        if nombre_etapa not in tareas_por_etapa:
                            tareas_por_etapa[nombre_etapa] = []
                        tareas_por_etapa[nombre_etapa].append(tarea)
                
                # Convertir a estructura de etapas
                etapas = []
                for nombre_etapa, tareas_etapa in tareas_por_etapa.items():
                    etapas.append({
                        'nombre': nombre_etapa,
                        'descripcion': f'Etapa con {len(tareas_etapa)} tareas asignadas',
                        'tareas': tareas_etapa
                    })
            
            # MOSTRAR LAS ETAPAS
            print(f"\n📄 ETAPAS DE LA ACTIVIDAD ({len(etapas)}):")
            
            for i, etapa in enumerate(etapas, 1):
                print(f"\n   🔸 ETAPA {i}: {etapa.get('nombre', 'Sin nombre')}")
                print(f"      {etapa.get('descripcion', 'Sin descripción')[:80]}...")
                
                tareas_etapa = etapa.get('tareas', [])
                if tareas_etapa:
                    print(f"      📋 Tareas ({len(tareas_etapa)}):")
                    for j, tarea in enumerate(tareas_etapa[:3], 1):  # Máximo 3 tareas por etapa
                        if isinstance(tarea, dict):
                            nombre = tarea.get('nombre', 'Sin nombre')[:40]
                            formato = tarea.get('formato_asignacion', 'N/A')
                            print(f"         {j}. {nombre} ({formato})")
                        else:
                            print(f"         {j}. Tarea {j}")
            
            # MOSTRAR DETALLES DE LAS TAREAS ESPECÍFICAS SI EXISTEN
            if 'tareas_especificas' in proyecto_final and len(proyecto_final['tareas_especificas']) > 0:
                print(f"\n🎯 ASIGNACIONES ESPECÍFICAS DE TAREAS:")
                for i, tarea in enumerate(proyecto_final['tareas_especificas'][:6], 1):  # Mostrar máximo 6 tareas
                    if isinstance(tarea, dict):
                        nombre = tarea.get('nombre', f'Tarea {i}')
                        descripcion = tarea.get('descripcion', 'Sin descripción')[:60]
                        formato = tarea.get('formato_asignacion', 'N/A')
                        etapa = tarea.get('etapa', 'Sin etapa')
                        print(f"   {i}. {nombre} ({formato})")
                        print(f"      • {descripcion}...")
                        print(f"      • Etapa: {etapa}")
                if len(proyecto_final['tareas_especificas']) > 6:
                    restantes = len(proyecto_final['tareas_especificas']) - 6
                    print(f"   ... y {restantes} tareas más")
        
        # Solicitar aprobación
        print(f"\n¿Aprueba este proyecto? (s/n): ", end="")
        respuesta = input().strip().lower()
        return respuesta.startswith('s')