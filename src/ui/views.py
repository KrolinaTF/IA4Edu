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
        validacion = proyecto_final.get('validacion', {})
        if not isinstance(validacion, dict):
            validacion = {}
            
        estadisticas = validacion.get('estadisticas', {})
        if not isinstance(estadisticas, dict):
            estadisticas = {}
            
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
        
        proyecto_base = proyecto_final.get('proyecto_base', {})
        if not isinstance(proyecto_base, dict):
            proyecto_base = {}
            
        resultados = proyecto_final.get('resultados_agentes', {})
        if not isinstance(resultados, dict):
            resultados = {}
        
        print(f"Título: {proyecto_base.get('titulo', 'N/A')}")
        print(f"Descripción: {proyecto_base.get('descripcion', 'N/A')}")
        
        # Acceso seguro a resultados anidados
        tareas_info = resultados.get('tareas', {})
        if isinstance(tareas_info, list):
            tareas_list = tareas_info
        else:
            tareas_list = tareas_info.get('tareas', []) if isinstance(tareas_info, dict) else []
        print(f"Tareas generadas: {len(tareas_list)}")
        
        # Validación manual
        return input("\n✅ ¿Aprueba el proyecto generado? (s/n): ").lower().startswith('s')