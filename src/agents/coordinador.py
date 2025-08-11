"""
Agente Coordinador Principal (Master Agent) del sistema ABP.
"""

import logging
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from core.contexto import ContextoHibrido
from core.comunicador import ComunicadorAgentes
from core.ollama_integrator import OllamaIntegrator

from agents.analizador import AgenteAnalizadorTareas
from agents.perfilador import AgentePerfiladorEstudiantes
from agents.optimizador import AgenteOptimizadorAsignaciones
from agents.generador import AgenteGeneradorRecursos

from models.proyecto import Tarea

logger = logging.getLogger("SistemaAgentesABP.AgenteCoordinador")

class AgenteCoordinador:
    """Agente Coordinador Principal (Master Agent) - CON CONTEXTO HÍBRIDO AUTO-DETECTADO"""
    
    def __init__(self, ollama_integrator=None, analizador_tareas=None, perfilador=None, 
                 optimizador=None, generador_recursos=None):
        """
        Inicializa el coordinador con agentes inyectados o valores por defecto
        
        Args:
            ollama_integrator: Integrador Ollama (opcional)
            analizador_tareas: Agente analizador de tareas (opcional)
            perfilador: Agente perfilador de estudiantes (opcional)
            optimizador: Agente optimizador de asignaciones (opcional)
            generador_recursos: Agente generador de recursos (opcional)
        """
        # Inicializar integrador Ollama
        self.ollama = ollama_integrator or OllamaIntegrator()
        
        self.historial_prompts = []
        self.ejemplos_k = self._cargar_ejemplos_k()
        self.contexto_hibrido = ContextoHibrido()

        # Inicializar componentes de coordinación
        # self.estado_global ahora es self.contexto_hibrido que maneja todo
        self.comunicador = ComunicadorAgentes()
        
        # Inicializar agentes especializados (con inyección de dependencias)
        self.analizador_tareas = analizador_tareas or AgenteAnalizadorTareas(self.ollama)
        self.perfilador = perfilador or AgentePerfiladorEstudiantes(self.ollama)
        self.optimizador = optimizador or AgenteOptimizadorAsignaciones(self.ollama)
        self.generador_recursos = generador_recursos or AgenteGeneradorRecursos(self.ollama)
        
        # Registrar agentes en el comunicador y diccionario
        self.agentes_especializados = {}
        agentes_a_registrar = {
            'analizador_tareas': self.analizador_tareas,
            'perfilador_estudiantes': self.perfilador,
            'optimizador_asignaciones': self.optimizador,
            'generador_recursos': self.generador_recursos
        }
        
        for nombre, agente in agentes_a_registrar.items():
            self.comunicador.registrar_agente(nombre, agente)
            self.agentes_especializados[nombre] = agente
    
        # Configuración de flujo
        self.flujo_config = {
            'max_iteraciones': 3,
            'validacion_automatica': True,
            'reintentos_por_agente': 2,
            'timeout_por_agente': 60
        }
        
        logger.info(f"🚀 AgenteCoordinador inicializado con {len(self.agentes_especializados)} agentes especializados")
    
    def _cargar_ejemplos_k(self) -> Dict[str, str]:
        """
        Carga ejemplos k_ para few-shot learning
        
        Returns:
            Diccionario con ejemplos k_
        """
        ejemplos = {}
        
        # Obtener directorio base del proyecto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # Subir un nivel desde /agents
        
        # Rutas absolutas para los archivos k_
        archivos_k = [
            os.path.join(base_dir, "data", "actividades", "k_feria_acertijos.txt"),
            os.path.join(base_dir, "data", "actividades", "k_sonnet_supermercado.txt"), 
            os.path.join(base_dir, "data", "actividades", "k_celula.txt"),
            os.path.join(base_dir, "data", "actividades", "k_piratas.txt"),
            os.path.join(base_dir, "data", "actividades", "k_sonnet7_fabrica_fracciones.txt")
        ]
        
        # Crear directorio si no existe
        os.makedirs(os.path.join(base_dir, "data", "actividades"), exist_ok=True)
        
        for archivo in archivos_k:
            try:
                # Si el archivo no existe, crear un ejemplo mínimo
                if not os.path.exists(archivo):
                    self._crear_ejemplo_k_minimo(archivo)
                
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    nombre_ejemplo = os.path.basename(archivo).replace('.txt', '').replace('k_', '')
                    ejemplos[nombre_ejemplo] = contenido  # Contenido completo del ejemplo
                    logger.info(f"✅ Cargado ejemplo k_: {nombre_ejemplo}")
            except FileNotFoundError:
                logger.warning(f"❌ No se encontró el archivo: {archivo}")
                continue
            except Exception as e:
                logger.error(f"❌ Error cargando ejemplo {archivo}: {e}")
                continue
        
        if ejemplos:
            logger.info(f"📚 Cargados {len(ejemplos)} ejemplos k_ para few-shot learning")
        else:
            logger.warning("⚠️ No se cargaron ejemplos k_, usando fallback")
            
        return ejemplos
    
    def _crear_ejemplo_k_minimo(self, ruta_archivo: str) -> None:
        """
        Crea un archivo de ejemplo k_ mínimo
        
        Args:
            ruta_archivo: Ruta donde crear el archivo
        """
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
        
        # Determinar tipo de ejemplo basado en nombre de archivo
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # Contenido genérico basado en tipo
        contenido = "ACTIVIDAD DE EJEMPLO: Mercado de fracciones\n\n"
        contenido += "DESCRIPCIÓN: Los estudiantes crean un mercado donde intercambian productos usando fracciones como moneda.\n\n"
        contenido += "COMPETENCIAS: Matemáticas (fracciones), trabajo en equipo, resolución de problemas\n\n"
        contenido += "ADAPTACIONES:\n"
        contenido += "- TEA: Usar tarjetas visuales con pasos claros\n"
        contenido += "- TDAH: Asignar rol de cajero que requiere movimiento\n"
        contenido += "- Altas capacidades: Retos con fracciones más complejas\n\n"
        contenido += "DESARROLLO: Preparación de materiales, explicación de reglas, desarrollo del mercado, reflexión final\n"
        
        # Guardar archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
            
        logger.info(f"✅ Creado archivo de ejemplo k_ mínimo: {ruta_archivo}")
    
    def generar_ideas_actividades_hibrido(self, prompt_profesor: str, contexto_hibrido: ContextoHibrido) -> List[Dict]:
        """
        Genera 3 ideas de actividades usando contexto híbrido auto-detectado
        
        Args:
            prompt_profesor: Prompt del profesor
            contexto_hibrido: Contexto híbrido
            
        Returns:
            Lista de ideas generadas
        """
        
        # Crear prompt enriquecido con contexto híbrido
        prompt_completo = self._crear_prompt_hibrido(prompt_profesor, contexto_hibrido)
        
        # Generar ideas
        respuesta = self.ollama.generar_respuesta(prompt_completo, max_tokens=600)
        ideas = self._parsear_ideas(respuesta)
        
        # PROCESAR RESPUESTA CON CONTEXTO HÍBRIDO
        contexto_hibrido.procesar_respuesta_llm(respuesta, prompt_profesor)
        
        logger.info(f"📊 Contexto actualizado: {list(contexto_hibrido.metadatos.keys())}")
        
        return ideas
    
    def _crear_prompt_hibrido(self, prompt_profesor: str, contexto_hibrido: ContextoHibrido) -> str:
        """
        Crea prompt usando contexto híbrido auto-detectado
        
        Args:
            prompt_profesor: Prompt del profesor
            contexto_hibrido: Contexto híbrido
            
        Returns:
            Prompt enriquecido
        """
        
        # Obtener contexto enriquecido del sistema híbrido
        contexto_str = contexto_hibrido.get_contexto_para_llm()
        
        # Seleccionar ejemplo k_ relevante basado en metadatos detectados
        tema_detectado = contexto_hibrido.metadatos.get('materia', '') + ' ' + contexto_hibrido.metadatos.get('tema', '')
        ejemplo_seleccionado = self._seleccionar_ejemplo_relevante(tema_detectado.strip())
        
        # Construir prompt híbrido
        prompt_hibrido = f"""
Eres un experto en diseño de actividades educativas para 4º de Primaria.

{contexto_str}

=== NUEVA PETICIÓN DEL USUARIO ===
{prompt_profesor}

=== ESTUDIANTES ESPECÍFICOS (AULA_A_4PRIM) ===
- 001 ALEX M.: reflexivo, visual, CI 102
- 002 MARÍA L.: reflexivo, auditivo
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118 - Necesita apoyo visual y rutinas
- 004 LUIS T.: impulsivo, kinestetico, TDAH combinado, CI 102 - Necesita movimiento
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141 - Necesita desafíos extra
- 006 SARA M.: equilibrado, auditivo, CI 115
- 007 EMMA K.: reflexivo, visual, CI 132
- 008 HUGO P.: equilibrado, visual, CI 114"""
        
        if ejemplo_seleccionado:
            prompt_hibrido += f"""

=== EJEMPLO DE ACTIVIDAD EXITOSA ===
{ejemplo_seleccionado}

=== PATRONES A SEGUIR ===
• NARRATIVA INMERSIVA: Contextualizar con historias atractivas
• OBJETIVOS CLAROS: Competencias específicas del tema + habilidades transversales
• ROL DOCENTE: Observación activa, guía discreta, gestión emocional
• ADAPTACIONES: Específicas para TEA, TDAH, altas capacidades
• MATERIALES CONCRETOS: Manipulativos, reales, accesibles"""
        else:
            prompt_hibrido += f"""

=== PRINCIPIOS PEDAGÓGICOS ===
• CENTRADO EN EL ESTUDIANTE: Actividades que partan de sus intereses y necesidades
• APRENDIZAJE SIGNIFICATIVO: Conectar con experiencias reales y contextos auténticos
• INCLUSIÓN: Adaptaciones para TEA (Elena), TDAH (Luis), altas capacidades (Ana)
• COLABORACIÓN: Fomentar trabajo en equipo y comunicación
• CREATIVIDAD: Permitir múltiples formas de expresión y solución"""
        
        prompt_hibrido += f"""

=== INSTRUCCIONES CRÍTICAS ===
IMPORTANTE: Lee atentamente la petición del usuario y céntrate EXCLUSIVAMENTE en el tema que solicita.

Genera exactamente 3 ideas de actividades educativas que:
1. RESPONDAN DIRECTAMENTE al tema específico solicitado por el usuario
2. MANTENGAN COHERENCIA TEMÁTICA en las 3 ideas (no mezclar materias diferentes)
3. Sean apropiadas para el tema detectado en el contexto: {contexto_hibrido.metadatos.get('materia', 'tema solicitado')}
4. Incluyan adaptaciones para Elena (TEA), Luis (TDAH) y Ana (altas capacidades)
5. Sean completamente ejecutables en 4º Primaria

SI el usuario pidió geografía → las 3 ideas deben ser de geografía
SI el usuario pidió ciencias → las 3 ideas deben ser de ciencias
SI el usuario pidió matemáticas → las 3 ideas deben ser de matemáticas

NO desvíes del tema principal solicitado por el usuario.

FORMATO EXACTO:
IDEA 1:
Título: [título del tema específico solicitado]
Descripción: [descripción detallada del tema solicitado]
Nivel: 4º Primaria
Competencias: [competencias del tema específico]
Duración: [tiempo realista]

IDEA 2:
[mismo formato, mismo tema...]

IDEA 3:
[mismo formato, mismo tema...]

Céntrate en el tema solicitado y proporciona 3 variaciones creativas del MISMO tema.
"""
        
        return prompt_hibrido
    
    def _seleccionar_ejemplo_relevante(self, tema: str) -> str:
        """
        Selecciona el ejemplo k_ más relevante según el tema del contexto JSON
        
        Args:
            tema: Tema detectado
            
        Returns:
            Ejemplo k_ seleccionado
        """
        if not tema:
            return ""  # Sin tema, sin ejemplo específico
            
        tema_lower = tema.lower()
        
        # Mapeo dinámico basado en el contexto real
        mapeo_ejemplos = {
            'supermercado': 'sonnet_supermercado',
            'dinero': 'sonnet_supermercado', 
            'comercio': 'sonnet_supermercado',
            'fracciones': 'sonnet7_fabrica_fracciones',
            'fábrica': 'sonnet7_fabrica_fracciones',
            'ciencias': 'celula',
            'células': 'celula',
            'biología': 'celula',
            'piratas': 'piratas',
            'tesoro': 'piratas',
            'aventura': 'piratas',
            # NO HAY EJEMPLOS DE GEOGRAFÍA - Devolver vacío para máxima creatividad
            'geografia': None,
            'españa': None,
            'comunidades': None,
            'viajes': None
        }
        
        # Buscar coincidencias exactas
        for palabra_clave, ejemplo in mapeo_ejemplos.items():
            if palabra_clave in tema_lower:
                if ejemplo is None:
                    # Intencionalmente sin ejemplo para máxima creatividad
                    return ""
                elif ejemplo in self.ejemplos_k:
                    return self.ejemplos_k[ejemplo]
        
        # Si no hay coincidencias, devolver vacío para que el LLM sea más creativo
        return ""
    
    def _parsear_ideas(self, respuesta: str) -> List[Dict]:
        """
        Parsea la respuesta para extraer las 3 ideas con múltiples patrones
        
        Args:
            respuesta: Respuesta del LLM
            
        Returns:
            Lista de ideas
        """
        ideas = []
        
        # Intentar múltiples patrones de división
        patrones_division = ["IDEA ", "**IDEA ", "# IDEA ", "\n\n"]
        partes = None
        
        for patron in patrones_division:
            temp_partes = respuesta.split(patron)
            if len(temp_partes) > 1:
                partes = temp_partes
                break
        
        if not partes:
            # Si no hay divisiones claras, tratar toda la respuesta como una idea
            partes = ["", respuesta]
        
        # Procesar cada parte encontrada
        for i, parte in enumerate(partes[1:]):  # Saltar primera parte vacía
            if not parte.strip() or i >= 3:  # Máximo 3 ideas
                continue
                
            idea = {
                "id": f"idea_{i+1}",
                "titulo": self._extraer_titulo_inteligente(parte),
                "descripcion": self._extraer_descripcion_inteligente(parte),
                "nivel": self._extraer_nivel_inteligente(parte),
                "competencias": self._extraer_competencias_inteligente(parte),
                "duracion": self._extraer_duracion_inteligente(parte)
            }
            ideas.append(idea)
        
        # Si no se encontraron ideas estructuradas, crear una única idea general
        if not ideas:
            ideas.append({
                "id": "idea_1",
                "titulo": self._extraer_titulo_inteligente(respuesta),
                "descripcion": respuesta[:200] + "..." if len(respuesta) > 200 else respuesta,
                "nivel": "4º Primaria",
                "competencias": "Matemáticas, trabajo en equipo",
                "duracion": "2-3 sesiones"
            })
        
        return ideas  # Devolver todas las ideas generadas
    
    def _extraer_titulo_inteligente(self, texto: str) -> str:
        """
        Extrae título usando múltiples patrones
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Título extraído
        """
        patrones = [
            r'Título:\s*([^\n]+)',
            r'\*\*([^*]+)\*\*',
            r'"([^"]+)"',
            r'\d+[.:)]\s*([^\n]+)',
            r'^([^\n.!?]+)[.!?]?'
        ]
        
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                titulo = match.group(1).strip()
                titulo = re.sub(r'^[\d\s.*:-]+', '', titulo).strip()
                if len(titulo) > 5:
                    return titulo
        
        return "Actividad Educativa"
    
    def _extraer_descripcion_inteligente(self, texto: str) -> str:
        """
        Extrae descripción usando múltiples patrones
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Descripción extraída
        """
        desc_match = re.search(r'Descripción:\s*([^\n]+(?:\n[^\n:]+)*)', texto, re.IGNORECASE)
        if desc_match:
            return desc_match.group(1).strip()
        
        lines = texto.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 50 and ':' not in line and not line.startswith(('Nivel', 'Duración', 'Competencias')):
                return line
        
        return "Actividad práctica para desarrollar competencias matemáticas"
    
    def _extraer_nivel_inteligente(self, texto: str) -> str:
        """
        Extrae nivel educativo usando múltiples patrones
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Nivel extraído
        """
        nivel_match = re.search(r'Nivel:\s*([^\n]+)', texto, re.IGNORECASE)
        if nivel_match:
            return nivel_match.group(1).strip()
        
        keywords = {
            'primaria': '4º Primaria',
            'cuarto': '4º Primaria', 
            'secundaria': 'Secundaria',
            'infantil': 'Educación Infantil'
        }
        
        texto_lower = texto.lower()
        for keyword, nivel in keywords.items():
            if keyword in texto_lower:
                return nivel
        
        return "4º Primaria"
    
    def _extraer_competencias_inteligente(self, texto: str) -> str:
        """
        Extrae competencias usando múltiples patrones
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Competencias extraídas
        """
        comp_match = re.search(r'Competencias:\s*([^\n]+)', texto, re.IGNORECASE)
        if comp_match:
            return comp_match.group(1).strip()
        
        competencias_encontradas = []
        keywords = {
            'matemáticas': 'Competencia matemática',
            'fracciones': 'Competencia matemática',
            'sumas': 'Competencia matemática',
            'decimales': 'Competencia matemática',
            'comunicación': 'Competencia lingüística',
            'trabajo en equipo': 'Competencia social',
            'creatividad': 'Competencia artística',
            'tecnología': 'Competencia digital'
        }
        
        texto_lower = texto.lower()
        for keyword, competencia in keywords.items():
            if keyword in texto_lower and competencia not in competencias_encontradas:
                competencias_encontradas.append(competencia)
        
        return ', '.join(competencias_encontradas) if competencias_encontradas else "Competencia matemática, trabajo colaborativo"
    
    def _extraer_duracion_inteligente(self, texto: str) -> str:
        """
        Extrae duración usando múltiples patrones
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Duración extraída
        """
        dur_match = re.search(r'Duración:\s*([^\n]+)', texto, re.IGNORECASE)
        if dur_match:
            return dur_match.group(1).strip()
        
        tiempo_patterns = [
            r'(\d+)\s*sesiones?',
            r'(\d+)\s*horas?',
            r'(\d+)\s*días?',
            r'(\d+)\s*semanas?'
        ]
        
        for pattern in tiempo_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "2-3 sesiones"
    
    def recoger_informacion_inicial(self, prompt_profesor: str, perfiles_estudiantes: list = None, 
                                  recursos_disponibles: list = None, restricciones: dict = None) -> dict:
        """
        Recoge y estructura toda la información inicial del proyecto
        
        Args:
            prompt_profesor: Prompt del profesor
            perfiles_estudiantes: Lista de perfiles de estudiantes (opcional)
            recursos_disponibles: Lista de recursos disponibles (opcional)
            restricciones: Diccionario con restricciones (opcional)
            
        Returns:
            Diccionario con información inicial
        """
        logger.info("📋 Recogiendo información inicial del proyecto")
        
        # Actualizar contexto hibrido con información inicial
        self.contexto_hibrido.metadatos['prompt_original'] = prompt_profesor
        if perfiles_estudiantes:
            self.contexto_hibrido.perfiles_estudiantes = perfiles_estudiantes
        if recursos_disponibles:
            self.contexto_hibrido.recursos_disponibles = recursos_disponibles
        if restricciones:
            self.contexto_hibrido.restricciones = restricciones
            
        self.contexto_hibrido.actualizar_estado("informacion_recopilada", "AgenteCoordinador")
        
        # Generar ideas base usando el método existente
        contexto_temporal = ContextoHibrido()
        ideas = self.generar_ideas_actividades_hibrido(prompt_profesor, contexto_temporal)
        
        return {
            'ideas_generadas': ideas,
            'estado': self.contexto_hibrido,
            'timestamp': datetime.now().isoformat()
        }
    
    def ejecutar_flujo_orquestado(self, idea_seleccionada: dict, informacion_adicional: str = "") -> dict:
        """
        Ejecuta el flujo completo orquestado con validaciones y manejo de errores
        
        Args:
            idea_seleccionada: Idea seleccionada para desarrollar
            informacion_adicional: Información adicional (opcional)
            
        Returns:
            Proyecto final generado
        """
        logger.info("🚀 Iniciando flujo orquestado mejorado")
        
        # Actualizar estado global con idea seleccionada
        self.contexto_hibrido.metadatos.update(idea_seleccionada)
        self.contexto_hibrido.metadatos['informacion_adicional'] = informacion_adicional
        self.contexto_hibrido.actualizar_estado("ejecutando_flujo", "AgenteCoordinador")
        
        # Definir flujo de ejecución
        flujo = [
            {
                'agente': 'analizador_tareas',
                'metodo': 'descomponer_actividad',
                'prioridad': 1,
                'descripcion': 'Descomponer actividad en tareas específicas'
            },
            {
                'agente': 'perfilador_estudiantes',
                'metodo': 'analizar_perfiles',
                'prioridad': 2,
                'descripcion': 'Analizar perfiles de estudiantes'
            },
            {
                'agente': 'optimizador_asignaciones',
                'metodo': 'optimizar_asignaciones',
                'prioridad': 3,
                'descripcion': 'Optimizar asignaciones estudiante-tarea'
            },
            {
                'agente': 'generador_recursos',
                'metodo': 'generar_recursos',
                'prioridad': 4,
                'descripcion': 'Generar recursos educativos'
            }
        ]
        
        # Ejecutar cada paso del flujo
        resultados = {}
        proyecto_base = self._crear_proyecto_base(idea_seleccionada, informacion_adicional)
        
        for i, paso in enumerate(flujo):
            try:
                logger.info(f"⚙️ Paso {i+1}/{len(flujo)}: {paso['descripcion']}")
                
                # Ejecutar agente usando el comunicador si está disponible
                if paso['agente'] in self.agentes_especializados:
                    datos = self._preparar_datos_para_agente(paso['agente'], proyecto_base, resultados)
                    resultado = self.comunicador.enviar_mensaje(
                        remitente="AgenteCoordinador",
                        destinatario=paso['agente'],
                        metodo=paso['metodo'],
                        datos=datos
                    )
                    resultados[paso['agente']] = resultado
                    
                    # Validación intermedia
                    coherencia = self.contexto_hibrido.validar_coherencia()
                    if coherencia['sugerencias']:
                        logger.info(f"💡 Sugerencias: {coherencia['sugerencias']}")
                        
                    logger.info(f"✅ Paso {i+1} completado exitosamente")
                else:
                    logger.warning(f"⚠️ Agente {paso['agente']} no disponible, saltando paso")
                    
            except Exception as e:
                logger.error(f"❌ Error en paso {i+1} ({paso['agente']}): {e}")
                self.contexto_hibrido.errores.append({
                    'paso': i+1,
                    'agente': paso['agente'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Continuar con el siguiente paso en caso de error
                continue
                
        # Consolidación final
        return self._consolidar_resultados_mejorado(proyecto_base, resultados)
    
    def _preparar_datos_para_agente(self, agente_nombre: str, proyecto_base: dict, resultados: dict) -> dict:
        """
        Prepara los datos necesarios para cada agente de forma genérica
        
        Args:
            agente_nombre: Nombre del agente
            proyecto_base: Datos del proyecto base
            resultados: Resultados de agentes anteriores
            
        Returns:
            Diccionario con datos preparados para el agente
        """
        # Datos comunes para todos los agentes
        datos_base = {
            'contexto_global': self.contexto_hibrido.metadatos,
            'timestamp': datetime.now().isoformat()
        }
        
        # Mapa simplificado de datos necesarios por agente
        mapa_datos = {
            'analizador_tareas': {'proyecto_base': proyecto_base},
            'perfilador_estudiantes': {'tareas': resultados.get('analizador_tareas', {})},
            'optimizador_asignaciones': {
                'tareas': resultados.get('analizador_tareas', {}),
                'analisis_estudiantes': resultados.get('perfilador_estudiantes', {}),
                'perfilador': self.perfilador
            },
            'generador_recursos': {
                'proyecto_base': proyecto_base,
                'tareas': resultados.get('analizador_tareas', {}),
                'asignaciones': resultados.get('optimizador_asignaciones', {})
            }
        }
        
        # Añadir datos específicos del agente si existen
        if agente_nombre in mapa_datos:
            datos_base.update(mapa_datos[agente_nombre])
        
        return datos_base
    
    def _consolidar_resultados_mejorado(self, proyecto_base: dict, resultados: dict) -> dict:
        """
        Consolida todos los resultados en un proyecto coherente mejorado
        
        Args:
            proyecto_base: Datos del proyecto base
            resultados: Resultados de los agentes
            
        Returns:
            Proyecto final consolidado
        """
        logger.info("🔄 Consolidando resultados finales con validación avanzada")
        
        self.contexto_hibrido.actualizar_estado("consolidando", "AgenteCoordinador")
        
        # Validación final de coherencia
        coherencia_final = self._validar_coherencia_global(proyecto_base, resultados)
        
        # Recopilación de estadísticas del proceso
        estadisticas = self._generar_estadisticas_proceso(resultados)
        
        # Estructuración de todos los resultados en formato unificado
        proyecto_consolidado = {
            'proyecto_base': proyecto_base,
            'resultados_agentes': {
                'analizador_tareas': resultados.get('analizador_tareas', {}),
                'perfilador_estudiantes': resultados.get('perfilador_estudiantes', {}),
                'optimizador_asignaciones': resultados.get('optimizador_asignaciones', {}),
                'generador_recursos': resultados.get('generador_recursos', {})
            },
            'coherencia': coherencia_final,
            'estadisticas': estadisticas,
            'metadatos': {
                'timestamp_inicio': self.contexto_hibrido.metadatos.get('timestamp_inicio'),
                'timestamp_fin': datetime.now().isoformat(),
                'version_sistema': '1.0.0',
                'estado_final': 'completado'
            }
        }
        
        # Actualizar estado global a completado
        self.contexto_hibrido.actualizar_estado("completado", "AgenteCoordinador")
        self.contexto_hibrido.finalizar_proyecto(proyecto_consolidado)
        
        logger.info("✅ Consolidación de resultados completada exitosamente")
        logger.info(f"📊 Estadísticas: {estadisticas['resumen']}")
        
        # Retornar el proyecto consolidado
        return proyecto_consolidado
    
    def _validar_coherencia_global(self, proyecto_base: dict, resultados: dict) -> dict:
        """
        Valida la coherencia entre el proyecto base y los resultados de todos los agentes
        
        Args:
            proyecto_base: Datos del proyecto base
            resultados: Resultados de todos los agentes
            
        Returns:
            Diccionario con información de coherencia
        """
        coherencia = {
            'validacion_exitosa': True,
            'puntuacion_coherencia': 0.0,
            'inconsistencias': [],
            'recomendaciones': []
        }
        
        try:
            # Validar coherencia entre tareas analizadas y asignaciones
            tareas = resultados.get('analizador_tareas', {})
            asignaciones = resultados.get('optimizador_asignaciones', {})
            
            # Normalizar tareas si es una lista
            if isinstance(tareas, list):
                tareas = {'tareas': {f'tarea_{i}': tarea for i, tarea in enumerate(tareas)}}
            
            # Normalizar asignaciones si es una lista
            if isinstance(asignaciones, list):
                asignaciones = {'asignaciones': {f'grupo_{i}': item for i, item in enumerate(asignaciones)}}
            
            if tareas and asignaciones and isinstance(tareas, dict) and isinstance(asignaciones, dict):
                tareas_ids = set(tareas.get('tareas', {}).keys()) if isinstance(tareas.get('tareas'), dict) else set()
                asignaciones_ids = set()
                
                if isinstance(asignaciones.get('asignaciones'), dict):
                    for grupo in asignaciones['asignaciones'].values():
                        if isinstance(grupo, dict) and 'tareas' in grupo:
                            asignaciones_ids.update(grupo['tareas'])
                
                # Verificar que todas las tareas tengan asignaciones
                tareas_sin_asignacion = tareas_ids - asignaciones_ids
                if tareas_sin_asignacion:
                    coherencia['inconsistencias'].append(f"Tareas sin asignación: {tareas_sin_asignacion}")
                    coherencia['puntuacion_coherencia'] -= 0.2
            
            # Validar coherencia entre perfiles y asignaciones
            perfiles = resultados.get('perfilador_estudiantes', {})
            if perfiles and asignaciones:
                estudiantes_perfilados = set(perfiles.get('estudiantes', {}).keys()) if isinstance(perfiles.get('estudiantes'), dict) else set()
                estudiantes_asignados = set(asignaciones.get('asignaciones', {}).keys()) if isinstance(asignaciones.get('asignaciones'), dict) else set()
                
                estudiantes_sin_perfil = estudiantes_asignados - estudiantes_perfilados
                if estudiantes_sin_perfil:
                    coherencia['inconsistencias'].append(f"Estudiantes asignados sin perfil: {estudiantes_sin_perfil}")
                    coherencia['puntuacion_coherencia'] -= 0.15
            
            # Calcular puntuación final
            coherencia['puntuacion_coherencia'] = max(0.0, 1.0 + coherencia['puntuacion_coherencia'])
            
            if coherencia['puntuacion_coherencia'] >= 0.8:
                coherencia['recomendaciones'].append("Alta coherencia del proyecto")
            elif coherencia['puntuacion_coherencia'] >= 0.6:
                coherencia['recomendaciones'].append("Coherencia aceptable, revisar inconsistencias menores")
            else:
                coherencia['validacion_exitosa'] = False
                coherencia['recomendaciones'].append("Baja coherencia, revisar inconsistencias críticas")
                
        except Exception as e:
            logger.error(f"Error en validación de coherencia: {e}")
            coherencia['validacion_exitosa'] = False
            coherencia['inconsistencias'].append(f"Error de validación: {str(e)}")
        
        return coherencia
    
    def _generar_estadisticas_proceso(self, resultados: dict) -> dict:
        """
        Genera estadísticas del proceso de ejecución
        
        Args:
            resultados: Resultados de todos los agentes
            
        Returns:
            Diccionario con estadísticas del proceso
        """
        estadisticas = {
            'agentes_ejecutados': len([k for k, v in resultados.items() if v]),
            'tareas_analizadas': 0,
            'estudiantes_perfilados': 0,
            'asignaciones_generadas': 0,
            'recursos_generados': 0,
            'errores_encontrados': sum(1 for v in resultados.values() if isinstance(v, dict) and 'error' in v),
            'tiempo_total_estimado': None,
            'resumen': {}
        }
        
        try:
            # Contar tareas analizadas
            if 'analizador_tareas' in resultados and resultados['analizador_tareas']:
                tareas_data = resultados['analizador_tareas']
                if isinstance(tareas_data, list):
                    estadisticas['tareas_analizadas'] = len(tareas_data)
                elif isinstance(tareas_data, dict):
                    tareas = tareas_data.get('tareas', {})
                    estadisticas['tareas_analizadas'] = len(tareas) if isinstance(tareas, (dict, list)) else 0
            
            # Contar estudiantes perfilados
            if 'perfilador_estudiantes' in resultados and resultados['perfilador_estudiantes']:
                perfiles_data = resultados['perfilador_estudiantes']
                if isinstance(perfiles_data, list):
                    estadisticas['estudiantes_perfilados'] = len(perfiles_data)
                elif isinstance(perfiles_data, dict):
                    estudiantes = perfiles_data.get('estudiantes', {})
                    estadisticas['estudiantes_perfilados'] = len(estudiantes) if isinstance(estudiantes, (dict, list)) else 0
            
            # Contar asignaciones generadas
            if 'optimizador_asignaciones' in resultados and resultados['optimizador_asignaciones']:
                asignaciones_data = resultados['optimizador_asignaciones']
                if isinstance(asignaciones_data, list):
                    estadisticas['asignaciones_generadas'] = len(asignaciones_data)
                elif isinstance(asignaciones_data, dict):
                    asignaciones = asignaciones_data.get('asignaciones', {})
                    estadisticas['asignaciones_generadas'] = len(asignaciones) if isinstance(asignaciones, (dict, list)) else 0
            
            # Contar recursos generados
            if 'generador_recursos' in resultados and resultados['generador_recursos']:
                recursos_data = resultados['generador_recursos']
                if isinstance(recursos_data, list):
                    estadisticas['recursos_generados'] = len(recursos_data)
                elif isinstance(recursos_data, dict):
                    recursos = recursos_data.get('recursos', {})
                    estadisticas['recursos_generados'] = len(recursos) if isinstance(recursos, (dict, list)) else 0
            
            # Generar resumen
            estadisticas['resumen'] = {
                'total_elementos_procesados': (
                    estadisticas['tareas_analizadas'] + 
                    estadisticas['estudiantes_perfilados'] + 
                    estadisticas['asignaciones_generadas'] + 
                    estadisticas['recursos_generados']
                ),
                'tasa_exito': 1.0 - (estadisticas['errores_encontrados'] / max(1, estadisticas['agentes_ejecutados'])),
                'agentes_completados': estadisticas['agentes_ejecutados'] - estadisticas['errores_encontrados']
            }
            
        except Exception as e:
            logger.error(f"Error generando estadísticas: {e}")
            estadisticas['error_estadisticas'] = str(e)
        
        return estadisticas
    
    def _crear_proyecto_base(self, actividad_seleccionada: dict, info_adicional: str = "") -> dict:
        """
        Crea la estructura base del proyecto ABP
        
        Args:
            actividad_seleccionada: Actividad seleccionada
            info_adicional: Información adicional opcional
            
        Returns:
            Estructura base del proyecto
        """
        if info_adicional:
            self.historial_prompts.append({
                "tipo": "info_adicional",
                "contenido": info_adicional,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"🎯 Creando estructura base del proyecto: {actividad_seleccionada.get('titulo', 'Sin título')}")
        
        # Crear estructura base del proyecto
        proyecto_base = {
            "titulo": actividad_seleccionada.get("titulo", "Proyecto ABP"),
            "descripcion": actividad_seleccionada.get("descripcion", ""),
            "nivel": actividad_seleccionada.get("nivel", "4º Primaria"),
            "competencias_base": actividad_seleccionada.get("competencias", "").split(", ") if actividad_seleccionada.get("competencias") else [],
            "duracion_base": actividad_seleccionada.get("duracion", "2 semanas"),
            "info_adicional": info_adicional
        }
        
        # Registrar en contexto hibrido
        self.contexto_hibrido.metadatos.update(proyecto_base)
        self.contexto_hibrido.actualizar_estado("estructura_base_creada", "AgenteCoordinador")
        
        return proyecto_base