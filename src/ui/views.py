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
        LEGACY: Solicita el prompt inicial al usuario (formato libre)
        
        Returns:
            Prompt ingresado por el usuario
        """
        print("\n📝 GENERACIÓN DE IDEAS (FORMATO LIBRE)")
        print("-" * 40)
        return input("Describa la actividad educativa que desea generar: ")
    
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
        input_basico['prompt_especifico'] = CLIViews._solicitar_idea_previa()
        
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
        
        return {
            'incluir': True,
            'modalidad': modalidad,
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
        
        return {
            'incluir': True,
            'aspectos': aspectos_seleccionados,
            'modalidad': modalidad,
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
        
        return {
            'incluir': True,
            'modalidad': modalidad,
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
    def solicitar_input_estructurado() -> Dict:
        """
        LEGACY: Mantener compatibilidad con el sistema anterior
        """
        print("\n📋 GENERACIÓN ESTRUCTURADA DE ACTIVIDAD (MODO LEGACY)")
        print("=" * 50)
        print("Complete los siguientes campos para generar su actividad ABP:")
        
        input_estructurado = {}
        
        # 1. MATERIA
        print(f"\n📚 MATERIA/ÁREA:")
        print("   1. Matemáticas")
        print("   2. Lengua Castellana y Literatura") 
        print("   3. Ciencias Naturales")
        print("   4. Ciencias Sociales/Geografía")
        print("   5. Educación Artística")
        print("   6. Educación Física")
        print("   7. Interdisciplinar")
        print("   8. Otra (especificar)")
        
        while True:
            try:
                opcion_materia = input("Seleccione materia (1-8): ").strip()
                materias_map = {
                    '1': 'Matemáticas',
                    '2': 'Lengua Castellana y Literatura',
                    '3': 'Ciencias Naturales', 
                    '4': 'Ciencias Sociales',
                    '5': 'Educación Artística',
                    '6': 'Educación Física',
                    '7': 'Interdisciplinar',
                    '8': 'Otra'
                }
                
                if opcion_materia in materias_map:
                    if opcion_materia == '8':
                        input_estructurado['materia'] = input("Especifique la materia: ").strip()
                    else:
                        input_estructurado['materia'] = materias_map[opcion_materia]
                    break
                else:
                    print("❌ Opción inválida. Seleccione 1-8.")
            except:
                print("❌ Entrada inválida. Intente de nuevo.")
        
        # 2. TEMA/CONTENIDO
        print(f"\n🎯 TEMA O CONTENIDO ESPECÍFICO:")
        input_estructurado['tema'] = input("Ej: 'Fracciones equivalentes', 'El cuerpo humano', 'Comunidades autónomas':\n> ").strip()
        
        # 3. DURACIÓN
        print(f"\n⏱️ DURACIÓN:")
        print("   1. Una sesión (45-60 min)")
        print("   2. Dos sesiones")
        print("   3. Una semana (5 sesiones)")
        print("   4. Proyecto largo (2-3 semanas)")
        print("   5. Personalizada")
        
        while True:
            try:
                opcion_duracion = input("Seleccione duración (1-5): ").strip()
                duraciones_map = {
                    '1': {'valor': 45, 'descripcion': 'Una sesión (45 minutos)'},
                    '2': {'valor': 90, 'descripcion': 'Dos sesiones (90 minutos)'},
                    '3': {'valor': 225, 'descripcion': 'Una semana (5 sesiones)'},
                    '4': {'valor': 450, 'descripcion': 'Proyecto largo (2-3 semanas)'},
                    '5': {'valor': 'custom', 'descripcion': 'Personalizada'}
                }
                
                if opcion_duracion in duraciones_map:
                    if opcion_duracion == '5':
                        while True:
                            try:
                                minutos_custom = int(input("Duración en minutos: "))
                                input_estructurado['duracion'] = {
                                    'valor': minutos_custom,
                                    'descripcion': f'{minutos_custom} minutos personalizados'
                                }
                                break
                            except ValueError:
                                print("❌ Ingrese un número válido de minutos.")
                    else:
                        input_estructurado['duracion'] = duraciones_map[opcion_duracion]
                    break
                else:
                    print("❌ Opción inválida. Seleccione 1-5.")
            except:
                print("❌ Entrada inválida. Intente de nuevo.")
        
        # 4. MODALIDADES DE TRABAJO
        print(f"\n👥 MODALIDADES DE TRABAJO (puede seleccionar varias):")
        print("   1. Individual")
        print("   2. Parejas") 
        print("   3. Grupos pequeños (3-4 estudiantes)")
        print("   4. Grupos grandes (5-6 estudiantes)")
        print("   5. Toda la clase")
        
        modalidades_seleccionadas = []
        modalidades_map = {
            '1': 'individual',
            '2': 'parejas',
            '3': 'grupos_pequeños',
            '4': 'grupos_grandes', 
            '5': 'clase_completa'
        }
        
        while True:
            seleccion = input("Seleccione modalidades (ej: '1,3,5' o presione Enter para terminar): ").strip()
            if not seleccion:
                break
                
            try:
                opciones = [op.strip() for op in seleccion.split(',')]
                modalidades_validas = []
                
                for opcion in opciones:
                    if opcion in modalidades_map:
                        modalidad = modalidades_map[opcion]
                        if modalidad not in modalidades_seleccionadas:
                            modalidades_seleccionadas.append(modalidad)
                            modalidades_validas.append(f"{opcion}={modalidad}")
                    else:
                        print(f"❌ Opción '{opcion}' inválida.")
                
                if modalidades_validas:
                    print(f"✅ Añadidas: {', '.join(modalidades_validas)}")
                    
            except:
                print("❌ Formato inválido. Use números separados por comas (ej: 1,3,5)")
                
        input_estructurado['modalidades'] = modalidades_seleccionadas if modalidades_seleccionadas else ['grupos_pequeños']
        
        # 5. ESTRUCTURA DE FASES CON MODALIDADES ESPECÍFICAS
        print(f"\n🔄 ESTRUCTURA DE FASES:")
        print("   1. Simple (Introducción → Desarrollo → Cierre)")
        print("   2. Investigación (Pregunta → Investigación → Presentación)")
        print("   3. Creativa (Inspiración → Creación → Exhibición)")
        print("   4. Experimental (Hipótesis → Experimento → Análisis)")
        print("   5. Personalizada (definir fases propias)")
        print("   6. Libre (que el sistema decida)")
        
        while True:
            try:
                opcion_fases = input("Seleccione estructura (1-6): ").strip()
                
                if opcion_fases == '1':
                    fases_base = ['Introducción y Preparación', 'Desarrollo y Práctica', 'Aplicación y Cierre']
                    input_estructurado['estructura_fases'] = CLIViews._configurar_modalidades_por_fase(fases_base, 'simple')
                    break
                elif opcion_fases == '2':
                    fases_base = ['Planteamiento del Problema', 'Investigación y Recogida de Datos', 'Presentación de Resultados']
                    input_estructurado['estructura_fases'] = CLIViews._configurar_modalidades_por_fase(fases_base, 'investigacion')
                    break
                elif opcion_fases == '3':
                    fases_base = ['Inspiración y Lluvia de Ideas', 'Proceso Creativo', 'Exhibición y Reflexión']
                    input_estructurado['estructura_fases'] = CLIViews._configurar_modalidades_por_fase(fases_base, 'creativa')
                    break
                elif opcion_fases == '4':
                    fases_base = ['Formulación de Hipótesis', 'Experimentación', 'Análisis y Conclusiones']
                    input_estructurado['estructura_fases'] = CLIViews._configurar_modalidades_por_fase(fases_base, 'experimental')
                    break
                elif opcion_fases == '5':
                    # Fases personalizadas
                    input_estructurado['estructura_fases'] = CLIViews._configurar_fases_personalizadas()
                    break
                elif opcion_fases == '6':
                    input_estructurado['estructura_fases'] = {'tipo': 'libre', 'fases': []}
                    break
                else:
                    print("❌ Opción inválida. Seleccione 1-6.")
            except:
                print("❌ Entrada inválida. Intente de nuevo.")
        
        # 6. CONTEXTO ADICIONAL (OPCIONAL)
        print(f"\n💡 CONTEXTO ADICIONAL (opcional):")
        contexto = input("Añada cualquier detalle específico, recursos disponibles, o adaptaciones necesarias:\n> ").strip()
        if contexto:
            input_estructurado['contexto_adicional'] = contexto
            
        # MOSTRAR RESUMEN
        CLIViews._mostrar_resumen_input_estructurado(input_estructurado)
        
        # CONFIRMACIÓN
        confirmacion = input("\n¿Confirma estos datos para generar la actividad? (s/n): ").strip().lower()
        if not confirmacion.startswith('s'):
            print("❌ Generación cancelada. Volviendo al menú principal.")
            return None
            
        return input_estructurado
    
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
            modalidades_texto = ', '.join(modalidades).replace('_', ' ')
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
    def solicitar_modo_generacion() -> str:
        """
        Solicita al usuario que elija el modo de generación
        
        Returns:
            'estructurado' o 'libre'
        """
        print("\n🚀 MODO DE GENERACIÓN DE ACTIVIDAD")
        print("=" * 40)
        print("Elija cómo desea crear su actividad:")
        print()
        print("📋 1. MODO ESTRUCTURADO (Recomendado)")
        print("     • Formulario guiado paso a paso")
        print("     • Campos específicos (materia, duración, modalidades)")
        print("     • Mayor precisión en los resultados")
        print()
        print("✏️  2. MODO LIBRE (Tradicional)")
        print("     • Descripción libre de la actividad") 
        print("     • Más flexibilidad en la expresión")
        print("     • Sistema interpreta automáticamente")
        print()
        
        while True:
            opcion = input("Seleccione modo (1 o 2): ").strip()
            if opcion == '1':
                return 'estructurado'
            elif opcion == '2':
                return 'libre' 
            else:
                print("❌ Opción inválida. Seleccione 1 o 2.")
    
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