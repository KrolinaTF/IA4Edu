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
from core.validador_coherencia import ValidadorCoherencia

from agents.analizador import AgenteAnalizadorTareas
from agents.perfilador import AgentePerfiladorEstudiantes
from agents.optimizador import AgenteOptimizadorAsignaciones

from models.proyecto import Tarea

logger = logging.getLogger("SistemaAgentesABP.AgenteCoordinador")

class AgenteCoordinador:
    """Agente Coordinador Principal (Master Agent) - CON CONTEXTO HÍBRIDO AUTO-DETECTADO"""
    
    def __init__(self, ollama_integrator=None, analizador_tareas=None, perfilador=None, 
                 optimizador=None):
        """
        Inicializa el coordinador con agentes inyectados o valores por defecto
        
        Args:
            ollama_integrator: Integrador Ollama (opcional)
            analizador_tareas: Agente analizador de tareas (opcional)
            perfilador: Agente perfilador de estudiantes (opcional)
            optimizador: Agente optimizador de asignaciones (opcional)
        """
        # Inicializar integrador Ollama
        self.ollama = ollama_integrator or OllamaIntegrator()
        
        self.historial_prompts = []
        self.ejemplos_k = self._cargar_ejemplos_k()
        self.contexto_hibrido = ContextoHibrido()
        self.validador = ValidadorCoherencia()

        # Inicializar componentes de coordinación
        # self.estado_global ahora es self.contexto_hibrido que maneja todo
        self.comunicador = ComunicadorAgentes()
        
        # Inicializar agentes especializados (con inyección de dependencias)
        self.analizador_tareas = analizador_tareas or AgenteAnalizadorTareas(self.ollama)
        self.perfilador = perfilador or AgentePerfiladorEstudiantes(self.ollama)
        self.optimizador = optimizador or AgenteOptimizadorAsignaciones(self.ollama)
        
        # Registrar agentes en el comunicador y diccionario
        self.agentes_especializados = {}
        agentes_a_registrar = {
            'analizador_tareas': self.analizador_tareas,
            'perfilador_estudiantes': self.perfilador,
            'optimizador_asignaciones': self.optimizador
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
    
    def generar_ideas_actividades_hibrido(self, prompt_usuario: str, contexto_hibrido: ContextoHibrido) -> List[Dict]:
        """
        Genera 3 ideas de actividades usando contexto híbrido auto-detectado
        
        Args:
            prompt_usuario: Prompt del usuario
            contexto_hibrido: Contexto híbrido
            
        Returns:
            Lista de ideas generadas
        """
        
        # Crear prompt enriquecido con contexto híbrido
        prompt_completo = self._crear_prompt_hibrido(prompt_usuario, contexto_hibrido)
        
        # Generar ideas
        respuesta = self.ollama.generar_respuesta(prompt_completo, max_tokens=600)
        ideas = self._parsear_ideas(respuesta)
        
        # PROCESAR RESPUESTA CON CONTEXTO HÍBRIDO
        contexto_hibrido.procesar_respuesta_llm(respuesta, prompt_usuario)
        
        logger.info(f"📊 Contexto actualizado: {list(contexto_hibrido.metadatos.keys())}")
        
        return ideas
    
    def matizar_idea_especifica(self, idea_base: Dict, matizaciones: str, contexto_hibrido: ContextoHibrido) -> List[Dict]:
        """
        Matiza una idea específica aplicando las modificaciones solicitadas
        
        Args:
            idea_base: Idea base a matizar
            matizaciones: Matizaciones específicas solicitadas
            contexto_hibrido: Contexto híbrido
            
        Returns:
            Lista de ideas matizadas (generalmente 1-2 variantes)
        """
        
        # Crear prompt específico para matización
        prompt_matizacion = f"""Eres un experto en diseño de actividades educativas para 4º de Primaria.

IDEA BASE A MATIZAR:
Título: {idea_base.get('titulo', '')}
Descripción: {idea_base.get('descripcion', '')}
Nivel: {idea_base.get('nivel', '4º Primaria')}
Duración: {idea_base.get('duracion', '')}
Competencias: {idea_base.get('competencias', '')}

MATIZACIONES SOLICITADAS:
{matizaciones}

INSTRUCCIONES:
Toma la IDEA BASE y aplica EXACTAMENTE las matizaciones solicitadas.
Mantén la esencia de la actividad pero incorpora ESPECÍFICAMENTE los cambios pedidos.
Genera 1-2 variantes de la idea matizada.

FORMATO OBLIGATORIO:
1. [Título de la idea matizada]
   Descripción: [Descripción detallada incorporando las matizaciones]
   Nivel: 4º Primaria
   Duración: [duración apropiada]
   Competencias: [competencias desarrolladas]

RESPONDE SOLO CON LAS IDEAS MATIZADAS, SIN EXPLICACIONES ADICIONALES."""
        
        # Generar respuesta matizada
        respuesta = self.ollama.generar_respuesta(prompt_matizacion, max_tokens=500)
        ideas_matizadas = self._parsear_ideas(respuesta)
        
        # Procesar respuesta con contexto híbrido y registrar decisión
        contexto_hibrido.procesar_respuesta_llm(respuesta, f"Matizar: {matizaciones}")
        contexto_hibrido.registrar_decision("AgenteCoordinador", f"Matización aplicada: {matizaciones[:50]}...", {
            'matizaciones_originales': matizaciones,
            'ideas_generadas': len(ideas_matizadas),
            'idea_base_titulo': idea_base.get('titulo', 'Sin título')
        })
        
        logger.info(f"✅ Ideas matizadas: {len(ideas_matizadas)} variantes generadas")
        
        return ideas_matizadas if ideas_matizadas else [idea_base]  # Fallback a idea original
    
    def _crear_prompt_hibrido(self, prompt_usuario: str, contexto_hibrido: ContextoHibrido) -> str:
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
{prompt_usuario}

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
        self.contexto_hibrido.metadatos['prompt_usuario'] = prompt_profesor
        if perfiles_estudiantes:
            self.contexto_hibrido.perfiles_estudiantes = perfiles_estudiantes
        if recursos_disponibles:
            self.contexto_hibrido.recursos_disponibles = recursos_disponibles
        if restricciones:
            self.contexto_hibrido.restricciones = restricciones
            
        self.contexto_hibrido.actualizar_estado("informacion_recopilada", "AgenteCoordinador")
        
        # Usar contexto híbrido existente en lugar de crear uno temporal
        ideas = self.generar_ideas_actividades_hibrido(prompt_profesor, self.contexto_hibrido)
        
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
        
        # Definir flujo optimizado de ejecución (3 agentes - Fase 1)
        flujo = [
            {
                'agente': 'analizador_tareas',
                'metodo': 'seleccionar_y_adaptar_actividad',  # NUEVO método con embeddings
                'prioridad': 1,
                'descripcion': 'Seleccionar actividad con embeddings y adaptar'
            },
            {
                'agente': 'perfilador_estudiantes',
                'metodo': 'analizar_perfiles',
                'prioridad': 2,
                'descripcion': 'Analizar perfiles de estudiantes reales'
            },
            {
                'agente': 'optimizador_asignaciones',
                'metodo': 'optimizar_asignaciones',
                'prioridad': 3,
                'descripcion': 'Optimizar asignaciones estudiante-tarea'
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
                    
                    # Llamada especial para analizador con nuevo método de embeddings
                    if paso['agente'] == 'analizador_tareas' and paso['metodo'] == 'seleccionar_y_adaptar_actividad':
                        prompt = datos.get('prompt', proyecto_base.get('descripcion', ''))
                        resultado = self.analizador_tareas.seleccionar_y_adaptar_actividad(prompt)
                        
                        # NUEVO: Extraer tareas usando método híbrido
                        if resultado and 'actividad' in resultado:
                            actividad_seleccionada = resultado['actividad']
                            tareas_extraidas = self.analizador_tareas.extraer_tareas_hibrido(
                                actividad_seleccionada, 
                                prompt
                            )
                            # Añadir tareas al resultado
                            resultado['tareas_extraidas'] = tareas_extraidas
                            logger.info(f"✅ Extraídas {len(tareas_extraidas)} tareas con método híbrido")
                    else:
                        # Llamada estándar vía comunicador
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
    
    def _preparar_datos_para_agente(self, agente_nombre, proyecto_base, resultados):
        """Método corregido en coordinador.py"""
        
        if agente_nombre == 'optimizador_asignaciones':
            # Usar tareas extraídas del nuevo método híbrido
            tareas_data = resultados.get('analizador_tareas', {})
            
            # PRIORIDAD 1: Usar tareas ya extraídas con método híbrido
            if isinstance(tareas_data, dict) and 'tareas_extraidas' in tareas_data:
                tareas_extraidas = tareas_data['tareas_extraidas']
                logger.info(f"🎯 Usando {len(tareas_extraidas)} tareas del método híbrido")
                
            # PRIORIDAD 2: Extraer desde actividad si no hay tareas híbridas
            elif isinstance(tareas_data, dict) and 'actividad' in tareas_data:
                logger.warning("⚠️ Extrayendo tareas con método legacy")
                actividad = tareas_data['actividad']
                tareas_extraidas = self._extraer_tareas_de_actividad(actividad)
                
            # FALLBACK: Lista vacía
            else:
                logger.error("❌ No se encontraron tareas, usando fallback vacío")
                tareas_extraidas = []
                
            return {
                'tareas_input': tareas_extraidas,  # Nombre correcto del parámetro
                'analisis_estudiantes': resultados.get('perfilador_estudiantes', {}),
                'perfilador': self.perfilador  # Referencia al perfilador
            }
        
        return {'proyecto_base': proyecto_base, 'resultados_previos': resultados}
    
    def _extraer_tareas_de_actividad(self, actividad: Dict) -> List[Dict]:
        """
        Extrae tareas de una estructura de actividad JSON
        
        Args:
            actividad: Diccionario con estructura de actividad
            
        Returns:
            Lista de tareas normalizadas
        """
        if not isinstance(actividad, dict):
            logger.error(f"❌ Actividad no es un diccionario: {type(actividad)}")
            return []
        
        tareas_extraidas = []
        contador_tareas = 1
        
        etapas = actividad.get('etapas', [])
        
        if not etapas:
            logger.warning("⚠️ No se encontraron etapas en la actividad")
            # Crear una tarea básica desde la actividad completa
            return [{
                'id': 'tarea_01',
                'nombre': actividad.get('titulo', 'Actividad'),
                'descripcion': actividad.get('objetivo', 'Realizar la actividad propuesta'),
                'etapa': 'Principal',
                'formato_asignacion': 'grupos',
                'complejidad': 3,
                'tipo': 'colaborativa',
                'tiempo_estimado': 60,
                'competencias_requeridas': ['transversales'],
                'adaptaciones': {}
            }]
        
        for i, etapa in enumerate(etapas):
            if not isinstance(etapa, dict):
                logger.warning(f"⚠️ Etapa {i} no es un diccionario válido")
                continue
                
            nombre_etapa = etapa.get('nombre', f'Etapa {i+1}')
            tareas_etapa = etapa.get('tareas', [])
            
            if not isinstance(tareas_etapa, list):
                logger.warning(f"⚠️ Tareas de etapa '{nombre_etapa}' no es una lista")
                continue
            
            for j, tarea_data in enumerate(tareas_etapa):
                if not isinstance(tarea_data, dict):
                    logger.warning(f"⚠️ Tarea {j} en etapa '{nombre_etapa}' no es un diccionario")
                    continue
                    
                tarea_normalizada = {
                    'id': f'tarea_{contador_tareas:02d}',
                    'nombre': tarea_data.get('nombre', f'Tarea {contador_tareas}'),
                    'descripcion': tarea_data.get('descripcion', 'Tarea sin descripción'),
                    'etapa': nombre_etapa,
                    'formato_asignacion': tarea_data.get('formato_asignacion', 'grupos'),
                    'complejidad': self._estimar_complejidad_tarea(tarea_data),
                    'tipo': self._determinar_tipo_tarea(tarea_data),
                    'tiempo_estimado': self._estimar_tiempo_tarea(tarea_data),
                    'competencias_requeridas': self._extraer_competencias_tarea(tarea_data),
                    'adaptaciones': tarea_data.get('estrategias_adaptacion', {})
                }
                
                tareas_extraidas.append(tarea_normalizada)
                contador_tareas += 1
        
        if not tareas_extraidas:
            logger.warning("⚠️ No se pudieron extraer tareas válidas, creando tarea por defecto")
            return [{
                'id': 'tarea_01',
                'nombre': 'Actividad Principal',
                'descripcion': actividad.get('objetivo', 'Realizar la actividad propuesta'),
                'etapa': 'Principal',
                'formato_asignacion': 'grupos',
                'complejidad': 3,
                'tipo': 'colaborativa',
                'tiempo_estimado': 60,
                'competencias_requeridas': ['transversales'],
                'adaptaciones': {}
            }]
        
        logger.debug(f"📝 Extraídas {len(tareas_extraidas)} tareas de la actividad")
        return tareas_extraidas
    
    def _estimar_complejidad_tarea(self, tarea_data: dict) -> int:
        """Estima complejidad de 1-5 basada en descripción"""
        descripcion = tarea_data.get('descripcion', '').lower()
        
        # Palabras que indican alta complejidad
        palabras_complejas = ['análisis', 'evaluar', 'crear', 'diseñar', 'investigar', 'planificar']
        # Palabras que indican baja complejidad  
        palabras_simples = ['listar', 'copiar', 'leer', 'observar', 'identificar']
        
        for palabra in palabras_complejas:
            if palabra in descripcion:
                return 4
        
        for palabra in palabras_simples:
            if palabra in descripcion:
                return 2
                
        return 3  # Complejidad media por defecto
    
    def _determinar_tipo_tarea(self, tarea_data: dict) -> str:
        """Determina si la tarea es individual, colaborativa o creativa"""
        formato = tarea_data.get('formato_asignacion', 'grupos')
        descripcion = tarea_data.get('descripcion', '').lower()
        
        if 'grupos' in formato or 'colaborat' in descripcion or 'equipo' in descripcion:
            return 'colaborativa'
        elif 'individual' in formato or 'personal' in descripcion or 'autónomo' in descripcion:
            return 'individual'
        elif 'crear' in descripcion or 'diseñar' in descripcion or 'arte' in descripcion:
            return 'creativa'
        else:
            return 'colaborativa'  # Por defecto
    
    def _estimar_tiempo_tarea(self, tarea_data: dict) -> int:
        """Estima tiempo en minutos basado en complejidad y tipo"""
        complejidad = self._estimar_complejidad_tarea(tarea_data)
        tipo = self._determinar_tipo_tarea(tarea_data)
        
        # Base de tiempo según complejidad
        tiempo_base = complejidad * 15
        
        # Ajustar según tipo
        if tipo == 'colaborativa':
            tiempo_base += 15  # Más tiempo para coordinación
        elif tipo == 'creativa':
            tiempo_base += 30  # Más tiempo para creatividad
            
        return min(120, max(15, tiempo_base))  # Entre 15 y 120 minutos
    
    def _extraer_competencias_tarea(self, tarea_data: dict) -> list:
        """Extrae competencias requeridas de la descripción de la tarea"""
        descripcion = tarea_data.get('descripcion', '').lower()
        competencias = []
        
        # Mapeo de palabras clave a competencias
        mapeo_competencias = {
            'matemática': ['cálculo', 'números', 'operaciones', 'fracciones', 'suma', 'resta'],
            'lingüística': ['escritura', 'lectura', 'textos', 'comunicación', 'presentar'],
            'científica': ['experimento', 'observar', 'investigar', 'ciencias', 'método'],
            'digital': ['tecnología', 'ordenador', 'internet', 'digital'],
            'artística': ['crear', 'diseñar', 'dibujar', 'arte', 'creativo'],
            'social': ['grupos', 'equipo', 'colaborar', 'compartir', 'ayudar']
        }
        
        for competencia, palabras_clave in mapeo_competencias.items():
            if any(palabra in descripcion for palabra in palabras_clave):
                competencias.append(competencia)
        
        return competencias if competencias else ['transversales']
    
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
        
        # Estructuración de todos los resultados en formato unificado (Fase 1 - 3 agentes)
        proyecto_consolidado = {
            'proyecto_base': proyecto_base,
            'resultados_agentes': {
                'analizador_tareas': resultados.get('analizador_tareas', {}),
                'perfilador_estudiantes': resultados.get('perfilador_estudiantes', {}),
                'optimizador_asignaciones': resultados.get('optimizador_asignaciones', {})
                },
            'coherencia': coherencia_final,
            'estadisticas': estadisticas,
            'metadatos': {
                'timestamp_inicio': self.contexto_hibrido.metadatos.get('timestamp_inicio'),
                'timestamp_fin': datetime.now().isoformat(),
                'version_sistema': '1.1.0-fase1',  # Actualizada para Fase 1
                'arquitectura': '3_agentes_embeddings',
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
    
    def ejecutar_flujo_optimizado_fase2(self, prompt_usuario: str, perfiles_estudiantes: list = None) -> dict:
        """
        Flujo optimizado de 3 pasos para Fase 2
        
        Args:
            prompt_usuario: Descripción de la actividad deseada
            perfiles_estudiantes: Lista de perfiles (opcional, usa los predefinidos)
            
        Returns:
            Proyecto completo optimizado
        """
        logger.info("🚀 Iniciando flujo optimizado Fase 2 (3 pasos esenciales)")
        
        inicio_tiempo = datetime.now()
        self.contexto_hibrido.actualizar_estado("iniciando_flujo_fase2", "AgenteCoordinador")
        
        try:
            # =================== PASO 1: SELECCIÓN INTELIGENTE DE ACTIVIDAD ===================
            logger.info("🎯 PASO 1/3: Selección inteligente de actividad con embeddings")
            
            resultado_seleccion = self.analizador_tareas.seleccionar_y_adaptar_actividad(prompt_usuario)
            
            if not resultado_seleccion or not resultado_seleccion.get('actividad'):
                raise Exception("No se pudo seleccionar actividad adecuada")
            
            actividad_seleccionada = resultado_seleccion['actividad']
            
            # NUEVO: Extraer tareas con método híbrido
            logger.info("🎯 PASO 1b/3: Extracción híbrida de tareas")
            tareas_extraidas = self.analizador_tareas.extraer_tareas_hibrido(
                actividad_seleccionada, 
                prompt_usuario
            )
            resultado_seleccion['tareas_extraidas'] = tareas_extraidas
            
            logger.info(f"✅ Actividad seleccionada: {actividad_seleccionada.get('titulo', 'Sin título')}")
            logger.info(f"   • Estrategia: {resultado_seleccion.get('estrategia', 'N/A')}")
            logger.info(f"   • Similitud: {resultado_seleccion.get('similitud', 0):.3f}")
            logger.info(f"   • Tareas extraídas: {len(tareas_extraidas)}")
            
            # =================== PASO 2: USO DIRECTO DE PERFILES REALES ===================
            logger.info("👥 PASO 2/3: Uso directo de perfiles de estudiantes reales")
            
            # Usar perfiles existentes directamente sin procesamiento LLM
            perfiles_utilizados = perfiles_estudiantes or self.perfilador.perfiles_base
            
            perfiles_estructurados = {
                'estudiantes': {},
                'estadisticas': {
                    'total': len(perfiles_utilizados),
                    'con_necesidades_especiales': 0,
                    'sin_necesidades_especiales': 0
                },
                'resumen_capacidades': self._generar_resumen_capacidades(perfiles_utilizados)
            }
            
            for estudiante in perfiles_utilizados:
                perfil_id = estudiante.id if hasattr(estudiante, 'id') else str(estudiante.get('id', 'unknown'))
                
                perfiles_estructurados['estudiantes'][perfil_id] = {
                    'id': perfil_id,
                    'nombre': estudiante.nombre if hasattr(estudiante, 'nombre') else estudiante.get('nombre', 'N/A'),
                    'fortalezas': estudiante.fortalezas if hasattr(estudiante, 'fortalezas') else estudiante.get('fortalezas', []),
                    'necesidades_apoyo': estudiante.necesidades_apoyo if hasattr(estudiante, 'necesidades_apoyo') else estudiante.get('necesidades_apoyo', []),
                    'adaptaciones': estudiante.adaptaciones if hasattr(estudiante, 'adaptaciones') else estudiante.get('adaptaciones', []),
                    'disponibilidad': estudiante.disponibilidad if hasattr(estudiante, 'disponibilidad') else estudiante.get('disponibilidad', 85)
                }
                
                # Actualizar estadísticas
                if perfiles_estructurados['estudiantes'][perfil_id]['adaptaciones']:
                    perfiles_estructurados['estadisticas']['con_necesidades_especiales'] += 1
                else:
                    perfiles_estructurados['estadisticas']['sin_necesidades_especiales'] += 1
            
            logger.info(f"✅ Perfiles procesados: {len(perfiles_estructurados['estudiantes'])} estudiantes")
            logger.info(f"   • Con necesidades especiales: {perfiles_estructurados['estadisticas']['con_necesidades_especiales']}")
            logger.info(f"   • Neurotipos diversos: {len([e for e in perfiles_estructurados['estudiantes'].values() if e['adaptaciones']])}")
            
            # =================== PASO 3: ASIGNACIONES OPTIMIZADAS ===================
            logger.info("⚡ PASO 3/3: Generación de asignaciones optimizadas")
            
            # Preparar datos para optimizador
            datos_optimizacion = {
                'actividad': actividad_seleccionada,
                'perfiles': perfiles_estructurados,
                'contexto_global': {
                    'prompt_usuario': prompt_usuario,
                    'timestamp': inicio_tiempo.isoformat(),
                    'metodo_seleccion': resultado_seleccion.get('estrategia', 'unknown')
                }
            }
            
            # Ejecutar optimización con argumentos correctos
            resultado_optimizacion = self.optimizador.optimizar_asignaciones(
                tareas_input=tareas_extraidas,  # Primer argumento requerido
                analisis_estudiantes=perfiles_estructurados,  # Segundo argumento
                perfilador=self.perfilador  # Tercer argumento opcional
            )
            
            logger.info(f"✅ Asignaciones generadas exitosamente")
            
            # =================== CONSOLIDACIÓN FINAL ===================
            fin_tiempo = datetime.now()
            duracion = (fin_tiempo - inicio_tiempo).total_seconds()
            
            proyecto_final = {
                'actividad_base': actividad_seleccionada,
                'seleccion_info': {
                    'estrategia': resultado_seleccion.get('estrategia'),
                    'similitud': resultado_seleccion.get('similitud'),
                    'fuente': resultado_seleccion.get('actividad_fuente'),
                    'adaptaciones_aplicadas': resultado_seleccion.get('adaptaciones_aplicadas', [])
                },
                'perfiles_estudiantes': perfiles_estructurados,
                'asignaciones': resultado_optimizacion,
                'metadatos': {
                    'version': '2.0.0-fase2',
                    'arquitectura': '3_pasos_optimizados',
                    'timestamp_inicio': inicio_tiempo.isoformat(),
                    'timestamp_fin': fin_tiempo.isoformat(),
                    'duracion_segundos': duracion,
                    'prompt_usuario': prompt_usuario,
                    'estudiantes_procesados': len(perfiles_estructurados['estudiantes']),
                    'flujo': 'optimizado_fase2'
                },
                'coherencia': self.validador.validar_coherencia_rapida(
                    actividad_seleccionada, 
                    perfiles_estructurados
                ),
                'coherencia_completa': self.validador.validar_proyecto_completo(
                    actividad_seleccionada,
                    perfiles_estructurados, 
                    resultado_optimizacion
                )
            }
            
            # Actualizar contexto híbrido
            self.contexto_hibrido.actualizar_estado("completado_fase2", "AgenteCoordinador")
            self.contexto_hibrido.finalizar_proyecto(proyecto_final)
            
            logger.info(f"🎉 Flujo optimizado completado en {duracion:.2f} segundos")
            logger.info(f"📊 Coherencia del proyecto: {proyecto_final['coherencia']['puntuacion']:.2f}/1.0")
            logger.info(f"🔍 Validación completa: {proyecto_final['coherencia_completa']['nivel_coherencia']}")
            
            return proyecto_final
            
        except Exception as e:
            logger.error(f"❌ Error en flujo optimizado Fase 2: {e}")
            
            # Crear respuesta de error estructurada
            error_response = {
                'error': True,
                'mensaje': str(e),
                'flujo': 'optimizado_fase2',
                'timestamp': datetime.now().isoformat(),
                'metadatos': {
                    'version': '2.0.0-fase2',
                    'estado': 'error',
                    'prompt_usuario': prompt_usuario
                }
            }
            
            self.contexto_hibrido.registrar_error("AgenteCoordinador", str(e), {"flujo": "fase2"})
            return error_response
    
    def _generar_resumen_capacidades(self, perfiles: list) -> dict:
        """
        Genera resumen de capacidades del grupo
        
        Args:
            perfiles: Lista de perfiles de estudiantes
            
        Returns:
            Diccionario con resumen de capacidades
        """
        resumen = {
            'fortalezas_mas_comunes': {},
            'necesidades_apoyo_frecuentes': {},
            'diversidad_neurotipos': [],
            'nivel_colaboracion_potencial': 'medio'
        }
        
        try:
            # Contar fortalezas
            todas_fortalezas = []
            todas_necesidades = []
            neurotipos_detectados = set()
            
            for estudiante in perfiles:
                # Extraer fortalezas
                fortalezas = estudiante.fortalezas if hasattr(estudiante, 'fortalezas') else estudiante.get('fortalezas', [])
                todas_fortalezas.extend(fortalezas)
                
                # Extraer necesidades de apoyo
                necesidades = estudiante.necesidades_apoyo if hasattr(estudiante, 'necesidades_apoyo') else estudiante.get('necesidades_apoyo', [])
                todas_necesidades.extend(necesidades)
                
                # Detectar neurotipos
                adaptaciones = estudiante.adaptaciones if hasattr(estudiante, 'adaptaciones') else estudiante.get('adaptaciones', [])
                for adaptacion in adaptaciones:
                    if 'TEA' in adaptacion or 'autismo' in adaptacion.lower():
                        neurotipos_detectados.add('TEA')
                    elif 'TDAH' in adaptacion or 'hiperactividad' in adaptacion.lower():
                        neurotipos_detectados.add('TDAH')
                    elif 'altas capacidades' in adaptacion.lower():
                        neurotipos_detectados.add('Altas Capacidades')
            
            # Generar estadísticas de fortalezas
            from collections import Counter
            contador_fortalezas = Counter(todas_fortalezas)
            resumen['fortalezas_mas_comunes'] = dict(contador_fortalezas.most_common(5))
            
            contador_necesidades = Counter(todas_necesidades)
            resumen['necesidades_apoyo_frecuentes'] = dict(contador_necesidades.most_common(5))
            
            resumen['diversidad_neurotipos'] = list(neurotipos_detectados)
            
            # Calcular potencial de colaboración
            if len(resumen['fortalezas_mas_comunes']) > 3:
                resumen['nivel_colaboracion_potencial'] = 'alto'
            elif len(neurotipos_detectados) > 2:
                resumen['nivel_colaboracion_potencial'] = 'medio-alto'  # Diversidad enriquece
            
        except Exception as e:
            logger.warning(f"⚠️ Error generando resumen de capacidades: {e}")
        
        return resumen
    
    def _validar_coherencia_rapida(self, actividad: dict, perfiles: dict, asignaciones: dict) -> dict:
        """
        Validación rápida de coherencia para flujo optimizado
        
        Args:
            actividad: Datos de la actividad seleccionada
            perfiles: Perfiles de estudiantes
            asignaciones: Asignaciones generadas
            
        Returns:
            Diccionario con validación de coherencia
        """
        coherencia = {
            'valida': True,
            'puntuacion': 1.0,
            'aspectos_validados': [],
            'alertas': []
        }
        
        try:
            # Validar que la actividad tenga estructura básica
            elementos_requeridos = ['titulo', 'objetivo', 'etapas']
            for elemento in elementos_requeridos:
                if not actividad.get(elemento):
                    coherencia['alertas'].append(f"Actividad sin {elemento}")
                    coherencia['puntuacion'] -= 0.1
                else:
                    coherencia['aspectos_validados'].append(f"actividad_con_{elemento}")
            
            # Validar cobertura de estudiantes
            estudiantes_con_perfil = len(perfiles.get('estudiantes', {}))
            if estudiantes_con_perfil > 0:
                coherencia['aspectos_validados'].append(f"perfiles_{estudiantes_con_perfil}_estudiantes")
            else:
                coherencia['alertas'].append("Sin perfiles de estudiantes")
                coherencia['puntuacion'] -= 0.3
            
            # Validar asignaciones si existen
            if asignaciones and isinstance(asignaciones, dict):
                if asignaciones.get('asignaciones') or asignaciones.get('grupos'):
                    coherencia['aspectos_validados'].append("asignaciones_generadas")
                else:
                    coherencia['alertas'].append("Asignaciones vacías")
                    coherencia['puntuacion'] -= 0.2
            
            # Ajustar validez final
            coherencia['valida'] = coherencia['puntuacion'] > 0.6
            coherencia['puntuacion'] = max(0.0, coherencia['puntuacion'])
            
        except Exception as e:
            logger.warning(f"⚠️ Error en validación rápida: {e}")
            coherencia['valida'] = False
            coherencia['puntuacion'] = 0.0
            coherencia['alertas'].append(f"Error en validación: {str(e)}")
        
        return coherencia
    
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
            
            # Recursos ya incluidos en actividades JSON (no generados por separado)
            
            # Generar resumen
            estadisticas['resumen'] = {
                'total_elementos_procesados': (
                    estadisticas['tareas_analizadas'] + 
                    estadisticas['estudiantes_perfilados'] + 
                    estadisticas['asignaciones_generadas']
                    # recursos_generados eliminado - incluidos en JSON
                ),
                'tasa_exito': 1.0 - (estadisticas['errores_encontrados'] / max(1, estadisticas['agentes_ejecutados'])),
                'agentes_completados': estadisticas['agentes_ejecutados'] - estadisticas['errores_encontrados'],
                'arquitectura': '3_agentes_optimizada'
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
    
    # =================== NUEVO FLUJO MEJORADO CON MVP ===================
    def ejecutar_flujo_mejorado_mvp(self, descripcion_actividad: str, duracion_minutos: int = 45) -> Dict:
        """
        NUEVO MÉTODO: Flujo mejorado que usa las mejoras integradas del MVP
        Análisis profundo + Asignación neurotipos usando agentes existentes mejorados
        CON SISTEMA DE RETRY Y VALIDACIÓN AUTOMÁTICA
        
        Args:
            descripcion_actividad: Descripción de la actividad
            duracion_minutos: Duración total en minutos
            
        Returns:
            Dict: Proyecto completo con mejoras del MVP integradas
        """
        self._log_processing_start(f"🧠 FLUJO MEJORADO MVP CON RETRY: '{descripcion_actividad}'")
        
        # IMPLEMENTAR SISTEMA DE RETRY CON VALIDACIÓN
        max_intentos = self.flujo_config.get('max_iteraciones', 3)
        validacion_automatica = self.flujo_config.get('validacion_automatica', True)
        
        for intento in range(1, max_intentos + 1):
            logger.info(f"🔄 INTENTO {intento}/{max_intentos} del flujo MVP")
            
            try:
                proyecto_resultado = self._ejecutar_flujo_mvp_interno(descripcion_actividad, duracion_minutos)
                
                # VALIDACIÓN AUTOMÁTICA SI ESTÁ HABILITADA
                if validacion_automatica:
                    validacion = self._validar_proyecto_resultado(proyecto_resultado)
                    
                    if validacion['valido']:
                        logger.info(f"✅ ÉXITO en intento {intento}: Proyecto válido (puntuación: {validacion['puntuacion']:.2f})")
                        proyecto_resultado['intentos_realizados'] = intento
                        proyecto_resultado['validacion_final'] = validacion
                        return proyecto_resultado
                    else:
                        logger.warning(f"⚠️ RETRY necesario en intento {intento}: {validacion['problemas']}")
                        if intento < max_intentos:
                            self._ajustar_contexto_para_retry(proyecto_resultado, validacion)
                        continue
                else:
                    # Sin validación automática, retornar resultado
                    logger.info(f"✅ Flujo completado en intento {intento} (sin validación automática)")
                    proyecto_resultado['intentos_realizados'] = intento
                    return proyecto_resultado
                    
            except Exception as e:
                logger.error(f"❌ Error en intento {intento}: {e}")
                if intento == max_intentos:
                    raise
                continue
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"❌ FALLO TOTAL: {max_intentos} intentos agotados")
        raise Exception(f"Flujo MVP falló después de {max_intentos} intentos")
    
    def _ejecutar_flujo_mvp_interno(self, descripcion_actividad: str, duracion_minutos: int = 45) -> Dict:
        """
        Ejecuta la lógica interna del flujo MVP (sin retry)
        """
        # REINICIALIZAR CONTADOR DE TAREAS para IDs consistentes
        self._tarea_counter = 0
        
        # PASO 1: Crear estructura base coherente con formato k_*.json
        # Obtener metadatos del contexto híbrido para enriquecer la estructura
        metadatos_contexto = self.contexto_hibrido.metadatos
        
        # NUEVO: Aplicar metadatos estructurados si están disponibles
        duracion_final = self._aplicar_metadatos_estructurados(metadatos_contexto, duracion_minutos)
        
        # Generar ID único para la actividad
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        actividad_base_estructurada = {
            'id': f'ACT_GEN_{timestamp}',
            'titulo': self._extraer_titulo_inteligente_con_estructura(descripcion_actividad, metadatos_contexto),
            'objetivo': self._generar_objetivo_especifico(descripcion_actividad, metadatos_contexto),
            'nivel_educativo': '4º Primaria',
            'duracion_minutos': f'{duracion_final} minutos',
            'recursos': [],  # Se generarán durante el análisis
            'etapas': [],   # Se generarán con tareas agrupadas
            'tipo_generacion': 'mvp_integrado'
        }
        
        # Cargar perfiles al contexto híbrido si no están ya cargados
        if not self.contexto_hibrido.perfiles_estudiantes:
            self.contexto_hibrido.perfiles_estudiantes = self.perfilador.perfiles_base
            logger.info(f"👥 Perfiles cargados al contexto híbrido: {len(self.perfilador.perfiles_base)} estudiantes")
        
        # Registrar inicio de flujo MVP en el contexto
        self.contexto_hibrido.registrar_decision("AgenteCoordinador", f"Iniciando flujo MVP para: {descripcion_actividad[:50]}...", {
            'tipo_flujo': 'flujo_mvp_integrado',
            'duracion_minutos': duracion_minutos,
            'descripcion_completa': descripcion_actividad
        })
        
        # PASO 2: Usar analizador mejorado con análisis profundo + contexto híbrido
        tareas_profundas = self.analizador_tareas.extraer_tareas_hibrido(
            actividad_data=actividad_base_estructurada, 
            prompt_usuario=descripcion_actividad,  # Esto activa el análisis profundo
            contexto_hibrido=self.contexto_hibrido  # 🆕 Pasar contexto híbrido
        )
        logger.info(f"✅ PASO 2: Análisis profundo completado - {len(tareas_profundas)} tareas específicas")
        
        # Registrar resultados del análisis en contexto
        self.contexto_hibrido.registrar_decision("AgenteAnalizador", f"Analisis completado: {len(tareas_profundas)} tareas identificadas", {
            'tareas_identificadas': len(tareas_profundas),
            'tipo_analisis': 'analisis_profundo'
        })
        
        # PASO 3: Usar perfilador existente + contexto híbrido
        perfiles_procesados = self.perfilador.analizar_perfiles({
            'estudiantes': self.perfilador.perfiles_base
        }, contexto_hibrido=self.contexto_hibrido)  # 🆕 Pasar contexto híbrido
        logger.info(f"✅ PASO 3: Perfiles procesados - {len(self.perfilador.perfiles_base)} estudiantes")
        
        # Registrar procesamiento de perfiles
        self.contexto_hibrido.registrar_decision("AgentePerfilador", f"Perfiles procesados: {len(self.perfilador.perfiles_base)} estudiantes", {
            'estudiantes_procesados': len(self.perfilador.perfiles_base)
        })
        
        # PASO 4: Usar optimizador mejorado con criterios neurotípicos + contexto híbrido
        asignaciones_neurotipos = self.optimizador.optimizar_asignaciones(
            tareas_input=tareas_profundas,
            analisis_estudiantes=perfiles_procesados,
            perfilador=self.perfilador,
            contexto_hibrido=self.contexto_hibrido  # 🆕 Pasar contexto híbrido
        )
        logger.info(f"✅ PASO 4: Asignaciones neurotípicas completadas")
        
        # PASO 5: Construir actividad coherente con formato k_*.json
        # Organizar tareas en etapas lógicas CON modalidades específicas por fase
        actividad_estructurada = self._organizar_tareas_en_etapas_con_modalidades(
            actividad_base_estructurada, 
            tareas_profundas, 
            metadatos_contexto
        )
        
        # Generar recursos basados en las tareas y contexto
        actividad_estructurada['recursos'] = self._inferir_recursos_necesarios(
            tareas_profundas, 
            metadatos_contexto
        )
        
        # PASO 6: Construir proyecto final con estructura unificada
        proyecto_mejorado = {
            'tipo': 'flujo_mvp_integrado_v3',
            'actividad_generada': actividad_estructurada,  # ← NUEVA estructura coherente
            'asignaciones_neurotipos': asignaciones_neurotipos,
            'perfiles_estudiantes': perfiles_procesados,
            'metadatos': {
                'version': '3.0.0-estructura-unificada',
                'formato_coherente': 'k_actividades_json',
                'mejoras_aplicadas': [
                    'analisis_profundo_especifico',
                    'criterios_neurotipos_tea_tdah_ac', 
                    'estructura_coherente_k_json',
                    'organizacion_etapas_logicas'
                ],
                'agentes_utilizados': ['analizador_mejorado', 'perfilador', 'optimizador_neurotipos']
            }
        }
        
        # Registrar finalización exitosa del flujo
        self.contexto_hibrido.registrar_decision("AgenteOptimizador", "Asignaciones neurotípicas completadas", {
            'total_asignaciones': len(asignaciones_neurotipos.get('asignaciones', {})),
            'criterios_aplicados': asignaciones_neurotipos.get('metadatos', {}).get('criterios_aplicados', [])
        })
        
        # Actualizar contexto híbrido con estado final
        self.contexto_hibrido.actualizar_estado("flujo_mvp_completado", "AgenteCoordinador")
        self.contexto_hibrido.finalizar_proyecto(proyecto_mejorado)
        
        logger.info("🎉 FLUJO MEJORADO MVP COMPLETADO")
        logger.info(f"   📊 Tareas específicas: {len(tareas_profundas)}")
        logger.info(f"   👥 Estudiantes: {len(self.perfilador.perfiles_base)}")
        logger.info(f"   🧠 Criterios neurotípicos aplicados: {asignaciones_neurotipos.get('metadatos', {}).get('criterios_aplicados', [])}")
        
        return proyecto_mejorado
    
    def _extraer_titulo_inteligente(self, descripcion: str) -> str:
        """Extrae un título inteligente de la descripción"""
        # Limpiar y obtener las primeras palabras significativas
        palabras = descripcion.split()[:8]  # Primeras 8 palabras
        titulo_base = ' '.join(palabras)
        
        # Capitalizar correctamente
        titulo_limpio = ' '.join(word.capitalize() for word in titulo_base.split())
        
        # Asegurar que no sea demasiado largo
        if len(titulo_limpio) > 60:
            titulo_limpio = titulo_limpio[:57] + '...'
            
        return titulo_limpio
    
    def _generar_objetivo_especifico(self, descripcion: str, metadatos: Dict) -> str:
        """Genera un objetivo pedagógico específico"""
        # Base del objetivo según la materia detectada
        materia = metadatos.get('materia', 'general')
        
        objetivos_base = {
            'matematicas': 'Desarrollar competencias matemáticas mediante',
            'lengua': 'Mejorar competencias lingüísticas a través de',
            'ciencias': 'Fomentar el pensamiento científico mediante',
            'creatividad': 'Estimular la creatividad y expresión a través de',
            'general': 'Desarrollar competencias transversales mediante'
        }
        
        objetivo_base = objetivos_base.get(materia, objetivos_base['general'])
        return f"{objetivo_base} {descripcion.lower()}, fomentando el trabajo colaborativo y la inclusión educativa."
    
    def _organizar_tareas_en_etapas(self, actividad_base: Dict, tareas: List, metadatos: Dict) -> Dict:
        """Organiza las tareas en etapas lógicas siguiendo el formato k_*.json"""
        from dataclasses import asdict
        
        # Convertir tareas a diccionarios si son objetos
        tareas_dict = []
        for tarea in tareas:
            if hasattr(tarea, '__dataclass_fields__'):
                tarea_dict = asdict(tarea)
            elif hasattr(tarea, '__dict__'):
                tarea_dict = tarea.__dict__
            else:
                tarea_dict = tarea
            tareas_dict.append(tarea_dict)
        
        # Lógica de agrupación de tareas en etapas
        if len(tareas_dict) <= 2:
            # Actividad simple: una sola etapa
            etapas = [{
                'nombre': 'Desarrollo de la Actividad',
                'descripcion': f'Los estudiantes realizan {actividad_base["titulo"].lower()}',
                'tareas': self._convertir_tareas_a_formato_k(tareas_dict)
            }]
        elif len(tareas_dict) <= 4:
            # Actividad media: dos etapas
            medio = len(tareas_dict) // 2
            etapas = [
                {
                    'nombre': 'Fase 1: Preparación y Exploración',
                    'descripcion': 'Los estudiantes se preparan y exploran los conceptos básicos',
                    'tareas': self._convertir_tareas_a_formato_k(tareas_dict[:medio])
                },
                {
                    'nombre': 'Fase 2: Desarrollo y Síntesis',
                    'descripcion': 'Los estudiantes desarrollan la actividad y sintetizan los aprendizajes',
                    'tareas': self._convertir_tareas_a_formato_k(tareas_dict[medio:])
                }
            ]
        else:
            # Actividad compleja: tres etapas
            tercio = len(tareas_dict) // 3
            etapas = [
                {
                    'nombre': 'Fase 1: Introducción y Preparación',
                    'descripcion': 'Los estudiantes se familiarizan con los conceptos y materiales',
                    'tareas': self._convertir_tareas_a_formato_k(tareas_dict[:tercio])
                },
                {
                    'nombre': 'Fase 2: Desarrollo y Práctica',
                    'descripcion': 'Los estudiantes practican y desarrollan las competencias principales',
                    'tareas': self._convertir_tareas_a_formato_k(tareas_dict[tercio:tercio*2])
                },
                {
                    'nombre': 'Fase 3: Aplicación y Evaluación',
                    'descripcion': 'Los estudiantes aplican lo aprendido y evalúan sus resultados',
                    'tareas': self._convertir_tareas_a_formato_k(tareas_dict[tercio*2:])
                }
            ]
        
        # Actualizar actividad base con las etapas
        actividad_base['etapas'] = etapas
        return actividad_base
    
    def _convertir_tareas_a_formato_k(self, tareas: List[Dict]) -> List[Dict]:
        """Convierte tareas del formato interno al formato k_*.json"""
        tareas_formato_k = []
        
        # Contador global para IDs consistentes
        if not hasattr(self, '_tarea_counter'):
            self._tarea_counter = 0
        
        for tarea in tareas:
            self._tarea_counter += 1
            
            # Mapear tipo a formato_asignacion
            tipo_mapping = {
                'individual': 'individual',
                'colaborativa': 'grupos', 
                'creativa': 'grupos',
                'parejas': 'parejas'
            }
            
            formato_asignacion = tipo_mapping.get(tarea.get('tipo', 'colaborativa'), 'grupos')
            
            tarea_k = {
                'id': f'tarea_profunda_{self._tarea_counter:02d}',  # ← ID CONSISTENTE
                'nombre': tarea.get('descripcion', 'Tarea sin nombre')[:50],  # Usar descripción como nombre
                'descripcion': tarea.get('descripcion', 'Descripción de la tarea'),
                'formato_asignacion': formato_asignacion
            }
            
            # Añadir estrategias de adaptación si hay estudiantes especiales detectados
            if self.contexto_hibrido.metadatos.get('estudiantes_especiales'):
                tarea_k['estrategias_adaptacion'] = self._generar_adaptaciones_neurotipos(tarea)
            
            tareas_formato_k.append(tarea_k)
        
        return tareas_formato_k
    
    def _generar_adaptaciones_neurotipos(self, tarea: Dict) -> Dict:
        """Genera adaptaciones específicas para neurotipos basadas en la tarea"""
        adaptaciones = {}
        
        # Adaptaciones para Elena (TEA)
        adaptaciones['para_elena'] = f"Proporcionar estructura clara y rutina predecible para {tarea.get('descripcion', 'la tarea')[:30]}. Usar apoyos visuales."
        
        # Adaptaciones para Luis (TDAH)
        adaptaciones['para_luis'] = f"Permitir movimiento y descansos durante {tarea.get('descripcion', 'la tarea')[:30]}. Fragmentar en pasos pequeños."
        
        # Adaptaciones para Ana (Altas capacidades)
        adaptaciones['para_ana'] = f"Proporcionar retos adicionales y roles de liderazgo en {tarea.get('descripcion', 'la tarea')[:30]}."
        
        return adaptaciones
    
    def _validar_proyecto_resultado(self, proyecto: Dict) -> Dict:
        """
        Valida el proyecto resultado usando el ValidadorCoherencia
        CON SIMULACIÓN DE FALLAS PARA TESTING
        
        Args:
            proyecto: Proyecto a validar
            
        Returns:
            Dict con información de validación
        """
        try:
            actividad = proyecto.get('actividad_generada', {})
            perfiles = proyecto.get('perfiles_estudiantes', {})
            asignaciones = proyecto.get('asignaciones_neurotipos', {})
            
            # Usar validación rápida primero
            validacion_rapida = self.validador.validar_coherencia_rapida(actividad, perfiles)
            
            # Si pasa validación rápida, hacer validación completa
            if validacion_rapida.get('valida', False):
                validacion_completa = self.validador.validar_proyecto_completo(actividad, perfiles, asignaciones)
                
                return {
                    'valido': validacion_completa.get('valido_globalmente', False),
                    'puntuacion': validacion_completa.get('puntuacion_global', 0.0),
                    'nivel': validacion_completa.get('nivel_coherencia', 'insuficiente'),
                    'problemas': validacion_completa.get('aspectos_fallidos', []),
                    'recomendaciones': validacion_completa.get('recomendaciones_consolidadas', []),
                    'validacion_rapida': validacion_rapida,
                    'validacion_completa': validacion_completa
                }
            else:
                return {
                    'valido': False,
                    'puntuacion': validacion_rapida.get('puntuacion', 0.0),
                    'nivel': 'fallo_rapido',
                    'problemas': validacion_rapida.get('alertas', []),
                    'recomendaciones': ['Revisar estructura básica del proyecto'],
                    'validacion_rapida': validacion_rapida
                }
                
        except Exception as e:
            logger.error(f"❌ Error en validación: {e}")
            return {
                'valido': False,
                'puntuacion': 0.0,
                'nivel': 'error_validacion',
                'problemas': [f'Error de validación: {e}'],
                'recomendaciones': ['Revisar estructura del proyecto']
            }
    
    def _ajustar_contexto_para_retry(self, proyecto_fallido: Dict, validacion: Dict):
        """
        Ajusta el contexto híbrido basado en los problemas detectados para mejorar el siguiente intento
        
        Args:
            proyecto_fallido: Proyecto que falló validación
            validacion: Información de validación
        """
        logger.info("🔧 Ajustando contexto para retry...")
        
        problemas = validacion.get('problemas', [])
        recomendaciones = validacion.get('recomendaciones', [])
        
        # Registrar problemas en el contexto híbrido
        self.contexto_hibrido.actualizar_estado("retry_necesario", "ValidadorCoherencia")
        
        # Ajustes específicos basados en problemas detectados
        if 'estructura_actividad' in problemas:
            self.contexto_hibrido.actualizar_estado("mejorar_estructura", "ValidadorCoherencia")
            
        if 'coherencia_actividad_perfiles' in problemas:
            self.contexto_hibrido.actualizar_estado("ajustar_complejidad", "ValidadorCoherencia")
            
        if 'asignaciones_capacidades' in problemas:
            self.contexto_hibrido.actualizar_estado("redistribuir_asignaciones", "ValidadorCoherencia")
            
        if 'inclusion_dua' in problemas:
            self.contexto_hibrido.actualizar_estado("reforzar_adaptaciones", "ValidadorCoherencia")
        
        # Agregar recomendaciones al contexto para el siguiente intento
        for recomendacion in recomendaciones[:3]:  # Máximo 3 recomendaciones
            self.contexto_hibrido.actualizar_estado(f"recomendacion: {recomendacion}", "ValidadorCoherencia")
        
        logger.info(f"🔧 Contexto ajustado con {len(problemas)} problemas y {len(recomendaciones)} recomendaciones")
    
    
    def _inferir_recursos_necesarios(self, tareas: List, metadatos: Dict) -> List[str]:
        """Infiere recursos necesarios basados en tareas y metadatos"""
        recursos = set()  # Usar set para evitar duplicados
        
        # Recursos base por materia
        materia = metadatos.get('materia', 'general')
        recursos_base = {
            'matematicas': ['Material manipulativo', 'Calculadoras', 'Papel y lápices'],
            'lengua': ['Tarjetas de palabras', 'Papel y lápices', 'Diccionarios'],
            'ciencias': ['Material de laboratorio básico', 'Lupas', 'Cuaderno de observaciones'],
            'general': ['Papel y lápices', 'Materiales de manualidades básicos']
        }
        
        recursos.update(recursos_base.get(materia, recursos_base['general']))
        
        # Recursos detectados en metadatos
        if 'materiales' in metadatos:
            recursos.update(metadatos['materiales'])
        
        # Recursos inferidos de las descripciones de tareas
        for tarea in tareas:
            descripcion = str(tarea.get('descripcion', '')).lower() if hasattr(tarea, 'get') else str(tarea).lower()
            
            if 'tarjetas' in descripcion or 'cartas' in descripcion:
                recursos.add('Tarjetas o cartas didácticas')
            if 'dinero' in descripcion or 'euros' in descripcion:
                recursos.add('Dinero de juguete')
            if 'digital' in descripcion or 'ordenador' in descripcion:
                recursos.add('Dispositivos digitales (tablets/ordenadores)')
            if 'dibujar' in descripcion or 'pintar' in descripcion:
                recursos.add('Materiales de dibujo y pintura')
        
        return list(recursos)
    
    def formatear_proyecto_mejorado_para_profesor(self, proyecto: Dict) -> str:
        """
        Formatea el proyecto mejorado con MVP para el profesor
        
        Args:
            proyecto: Proyecto con mejoras del MVP integradas
            
        Returns:
            String formateado para el profesor
        """
        descripcion = proyecto.get('descripcion_actividad', 'Actividad Educativa')
        tareas = proyecto.get('tareas_especificas', [])
        asignaciones = proyecto.get('asignaciones_neurotipos', {})
        metadatos = proyecto.get('metadatos', {})
        
        output = f"""
🧠 PROYECTO EDUCATIVO MEJORADO CON MVP
{'='*80}
📝 Actividad: {descripcion}
⏱️ Duración: {proyecto.get('duracion_minutos', 45)} minutos
🤖 Sistema: Agentes con mejoras del MVP integradas
📊 Versión: {metadatos.get('version', 'N/A')}

🎯 MEJORAS APLICADAS:
{chr(10).join(f"   ✅ {mejora.replace('_', ' ').title()}" for mejora in metadatos.get('mejoras_aplicadas', []))}

📋 TAREAS ESPECÍFICAS IDENTIFICADAS ({len(tareas)}):
"""
        
        for i, tarea in enumerate(tareas[:6], 1):
            if isinstance(tarea, dict):
                descripcion_tarea = tarea.get('descripcion', 'Sin descripción')
                complejidad = tarea.get('complejidad', 3)
                tipo = tarea.get('tipo', 'colaborativa')
                output += f"   {i}. {descripcion_tarea} (Complejidad: {complejidad}, Tipo: {tipo})\n"
        
        # Mostrar asignaciones neurotípicas si están disponibles
        if isinstance(asignaciones, dict) and 'justificaciones' in asignaciones:
            output += f"""

👥 ASIGNACIONES NEUROTÍPICAS:
{'='*50}"""
            
            justificaciones = asignaciones.get('justificaciones', {})
            for estudiante_id, info in justificaciones.items():
                neurotipo = info.get('neurotipo', 'tipico')
                emoji = {'TEA': '🧩', 'TDAH': '⚡', 'altas_capacidades': '🌟', 'tipico': '👤'}.get(neurotipo, '👤')
                
                output += f"""
{emoji} Estudiante {estudiante_id} ({neurotipo}):
   💡 {info.get('justificacion', 'Sin justificación')}
   📋 Tareas asignadas: {info.get('num_tareas', 0)}
   🎯 Criterios: {', '.join(info.get('criterios_aplicados', []))}
"""
        
        # Estadísticas neurotípicas
        if isinstance(asignaciones, dict) and 'estadisticas_neurotipos' in asignaciones:
            stats = asignaciones['estadisticas_neurotipos']
            output += f"""

📊 DISTRIBUCIÓN NEUROTÍPICA:
"""
            for neurotipo, cantidad in stats.items():
                emoji = {'TEA': '🧩', 'TDAH': '⚡', 'altas_capacidades': '🌟', 'tipico': '👤'}.get(neurotipo, '👤')
                output += f"   {emoji} {neurotipo}: {cantidad} estudiantes\n"
        
        output += f"""

🎯 RESUMEN DE MEJORAS INTEGRADAS:
   🧠 Análisis profundo: Tareas específicas por tipo de actividad
   ⚖️ Criterios neurotípicos: Asignación TEA, TDAH, altas capacidades
   💡 Justificaciones: Decisiones pedagógicamente fundamentadas
   🛡️ Fallbacks inteligentes: Sistema robusto ante fallos
   🔄 Compatibilidad: Funciona con el flujo existente
"""
        
        return output
    
    def _log_processing_start(self, description: str):
        """Log del inicio del procesamiento"""
        logger.info(f"🚀 COORDINADOR: {description}")
    
    def _log_processing_end(self, description: str):
        """Log del fin del procesamiento"""
        logger.info(f"✅ COORDINADOR: {description}")
    
    def _aplicar_metadatos_estructurados(self, metadatos: Dict, duracion_default: int) -> int:
        """
        Aplica metadatos estructurados del input a la generación de actividades
        
        Args:
            metadatos: Metadatos del contexto híbrido
            duracion_default: Duración por defecto
            
        Returns:
            Duración final a usar
        """
        # Aplicar duración objetivo si está disponible
        duracion_objetivo = metadatos.get('duracion_objetivo')
        if duracion_objetivo and isinstance(duracion_objetivo, int):
            logger.info(f"📅 Aplicando duración estructurada: {duracion_objetivo} minutos")
            return duracion_objetivo
        
        # Registrar otras preferencias estructuradas
        modalidades = metadatos.get('modalidades_preferidas', [])
        if modalidades:
            logger.info(f"👥 Modalidades preferidas registradas: {', '.join(modalidades)}")
            
        estructura = metadatos.get('estructura_preferida', '')
        if estructura and estructura != 'libre':
            logger.info(f"🔄 Estructura preferida registrada: {estructura}")
            
        materia = metadatos.get('materia', '')
        if materia:
            logger.info(f"📚 Materia específica registrada: {materia}")
            
        tema = metadatos.get('tema', '')
        if tema:
            logger.info(f"🎯 Tema específico registrado: {tema}")
        
        return duracion_default
    
    def _extraer_titulo_inteligente_con_estructura(self, descripcion: str, metadatos: Dict) -> str:
        """
        Extrae título inteligente considerando metadatos estructurados
        
        Args:
            descripcion: Descripción de la actividad
            metadatos: Metadatos estructurados
            
        Returns:
            Título mejorado
        """
        # Usar título base
        titulo_base = self._extraer_titulo_inteligente(descripcion)
        
        # Enriquecer con metadatos estructurados
        materia = metadatos.get('materia', '')
        tema = metadatos.get('tema', '')
        
        # Si hay tema específico, usar como título principal
        if tema and len(tema.strip()) > 3:
            # Capitalizar correctamente el tema
            tema_capitalizado = ' '.join(word.capitalize() for word in tema.split())
            
            # Si hay materia, crear título compuesto
            if materia and materia != 'Interdisciplinar':
                return f"{tema_capitalizado}: Actividad de {materia}"
            else:
                return f"Explorando {tema_capitalizado}"
        
        # Si hay materia pero no tema específico, enriquecer título base
        elif materia and materia != 'Interdisciplinar':
            if titulo_base != "Actividad Educativa":
                return f"{titulo_base} - {materia}"
            else:
                return f"Actividad de {materia}"
        
        # Fallback al título base
        return titulo_base
    
    def _organizar_tareas_en_etapas_con_modalidades(self, actividad_base: Dict, tareas: List, metadatos: Dict) -> Dict:
        """
        Organiza las tareas en etapas lógicas CON modalidades específicas por fase
        
        Args:
            actividad_base: Estructura base de la actividad
            tareas: Lista de tareas extraídas
            metadatos: Metadatos del contexto híbrido
            
        Returns:
            Actividad con etapas y modalidades organizadas
        """
        from dataclasses import asdict
        
        # Convertir dataclass objects a diccionarios si es necesario
        tareas_dict = []
        for tarea in tareas:
            if hasattr(tarea, '__dict__'):
                # Es un dataclass
                tarea_dict = asdict(tarea)
            elif isinstance(tarea, dict):
                # Ya es un diccionario
                tarea_dict = tarea
            else:
                # Fallback
                tarea_dict = {'descripcion': str(tarea), 'tipo': 'colaborativa'}
                
            tareas_dict.append(tarea_dict)
        
        # Verificar si hay fases detalladas con modalidades específicas
        fases_detalladas = metadatos.get('fases_detalladas', [])
        
        if fases_detalladas:
            # USAR FASES ESTRUCTURADAS CON MODALIDADES ESPECÍFICAS
            etapas = self._crear_etapas_desde_fases_detalladas(tareas_dict, fases_detalladas)
        else:
            # FALLBACK: Usar organización estándar
            etapas = self._crear_etapas_estandar(tareas_dict)
        
        # Actualizar actividad base con las etapas
        actividad_base['etapas'] = etapas
        
        logger.info(f"🔄 Etapas organizadas: {len(etapas)} etapas con modalidades específicas")
        return actividad_base
    
    def _crear_etapas_desde_fases_detalladas(self, tareas: List[Dict], fases_detalladas: List[Dict]) -> List[Dict]:
        """
        Crea etapas basadas en las fases detalladas con modalidades específicas
        
        Args:
            tareas: Lista de tareas a distribuir
            fases_detalladas: Lista de fases con modalidades
            
        Returns:
            Lista de etapas con modalidades aplicadas
        """
        etapas = []
        num_fases = len(fases_detalladas)
        
        # Distribuir tareas entre las fases
        tareas_por_fase = len(tareas) // num_fases
        resto = len(tareas) % num_fases
        
        indice_tarea = 0
        
        for i, fase_detalle in enumerate(fases_detalladas):
            # Calcular cuántas tareas para esta fase
            tareas_en_fase = tareas_por_fase + (1 if i < resto else 0)
            
            # Obtener tareas para esta fase
            tareas_fase = tareas[indice_tarea:indice_tarea + tareas_en_fase]
            indice_tarea += tareas_en_fase
            
            # Aplicar modalidad específica a todas las tareas de esta fase
            modalidad_fase = fase_detalle.get('modalidad', 'grupos_pequeños')
            formato_asignacion = self._convertir_modalidad_a_formato(modalidad_fase)
            
            # Convertir tareas aplicando la modalidad específica
            tareas_formato_k = []
            for tarea in tareas_fase:
                tarea_k = self._convertir_tarea_individual_con_modalidad(tarea, formato_asignacion)
                tareas_formato_k.append(tarea_k)
            
            # Crear etapa con modalidad específica
            etapa = {
                'nombre': fase_detalle.get('nombre', f'Fase {i+1}'),
                'descripcion': self._generar_descripcion_fase(fase_detalle, modalidad_fase),
                'tareas': tareas_formato_k,
                'modalidad_predominante': modalidad_fase
            }
            
            etapas.append(etapa)
            
            logger.debug(f"🔸 Fase '{fase_detalle.get('nombre')}': {len(tareas_fase)} tareas, modalidad: {modalidad_fase}")
        
        return etapas
    
    def _crear_etapas_estandar(self, tareas: List[Dict]) -> List[Dict]:
        """
        Crea etapas usando el método estándar (fallback)
        
        Args:
            tareas: Lista de tareas
            
        Returns:
            Lista de etapas estándar
        """
        # Usar el método existente como fallback
        if len(tareas) <= 2:
            # Actividad simple: una etapa
            etapas = [{
                'nombre': 'Fase Principal',
                'descripcion': 'Los estudiantes desarrollan la actividad completa',
                'tareas': self._convertir_tareas_a_formato_k(tareas)
            }]
        elif len(tareas) <= 4:
            # Actividad media: dos etapas
            medio = len(tareas) // 2
            etapas = [
                {
                    'nombre': 'Fase 1: Preparación y Exploración',
                    'descripcion': 'Los estudiantes se preparan y exploran los conceptos básicos',
                    'tareas': self._convertir_tareas_a_formato_k(tareas[:medio])
                },
                {
                    'nombre': 'Fase 2: Desarrollo y Síntesis',
                    'descripcion': 'Los estudiantes desarrollan la actividad y sintetizan los aprendizajes',
                    'tareas': self._convertir_tareas_a_formato_k(tareas[medio:])
                }
            ]
        else:
            # Actividad compleja: tres etapas
            tercio = len(tareas) // 3
            etapas = [
                {
                    'nombre': 'Fase 1: Introducción y Preparación',
                    'descripcion': 'Los estudiantes se familiarizan con los conceptos y materiales',
                    'tareas': self._convertir_tareas_a_formato_k(tareas[:tercio])
                },
                {
                    'nombre': 'Fase 2: Desarrollo y Práctica', 
                    'descripcion': 'Los estudiantes practican y desarrollan las competencias principales',
                    'tareas': self._convertir_tareas_a_formato_k(tareas[tercio:tercio*2])
                },
                {
                    'nombre': 'Fase 3: Aplicación y Evaluación',
                    'descripcion': 'Los estudiantes aplican lo aprendido y evalúan sus resultados',
                    'tareas': self._convertir_tareas_a_formato_k(tareas[tercio*2:])
                }
            ]
        
        return etapas
    
    def _convertir_modalidad_a_formato(self, modalidad: str) -> str:
        """
        Convierte modalidad del input a formato de asignación
        
        Args:
            modalidad: Modalidad de trabajo
            
        Returns:
            Formato de asignación compatible
        """
        mapeo_modalidades = {
            'individual': 'individual',
            'parejas': 'parejas',
            'grupos_pequeños': 'grupos',
            'grupos_grandes': 'grupos',
            'clase_completa': 'grupos'  # Grupos grandes para toda la clase
        }
        
        return mapeo_modalidades.get(modalidad, 'grupos')
    
    def _convertir_tarea_individual_con_modalidad(self, tarea: Dict, formato_asignacion: str) -> Dict:
        """
        Convierte una tarea individual aplicando modalidad específica
        
        Args:
            tarea: Tarea a convertir
            formato_asignacion: Formato de asignación específico
            
        Returns:
            Tarea en formato k_ con modalidad aplicada
        """
        self._tarea_counter += 1
        
        tarea_k = {
            'id': f'tarea_profunda_{self._tarea_counter:02d}',
            'nombre': tarea.get('descripcion', 'Tarea sin nombre')[:50],
            'descripcion': tarea.get('descripcion', 'Descripción de la tarea'),
            'formato_asignacion': formato_asignacion
        }
        
        # Añadir estrategias de adaptación si hay estudiantes especiales detectados
        if self.contexto_hibrido.metadatos.get('estudiantes_especiales'):
            tarea_k['estrategias_adaptacion'] = self._generar_adaptaciones_neurotipos(tarea)
        
        return tarea_k
    
    def _generar_descripcion_fase(self, fase_detalle: Dict, modalidad: str) -> str:
        """
        Genera descripción pedagógica para una fase con modalidad específica
        
        Args:
            fase_detalle: Detalles de la fase
            modalidad: Modalidad de trabajo
            
        Returns:
            Descripción pedagógica de la fase
        """
        nombre_fase = fase_detalle.get('nombre', 'Fase')
        
        descripciones_modalidad = {
            'individual': 'Los estudiantes trabajan de manera autónoma',
            'parejas': 'Los estudiantes colaboran en parejas',
            'grupos_pequeños': 'Los estudiantes trabajan en grupos pequeños de 3-4 personas',
            'grupos_grandes': 'Los estudiantes se organizan en grupos grandes de 5-6 personas',
            'clase_completa': 'Toda la clase trabaja junta como un gran equipo'
        }
        
        descripcion_base = descripciones_modalidad.get(modalidad, 'Los estudiantes trabajan colaborativamente')
        
        if 'preparación' in nombre_fase.lower() or 'introducción' in nombre_fase.lower():
            return f"{descripcion_base} para familiarizarse con los conceptos y preparar la actividad"
        elif 'desarrollo' in nombre_fase.lower() or 'ejecución' in nombre_fase.lower():
            return f"{descripcion_base} para desarrollar las competencias principales de la actividad"
        elif 'presentación' in nombre_fase.lower() or 'exhibición' in nombre_fase.lower():
            return f"{descripcion_base} para presentar y compartir sus resultados"
        elif 'evaluación' in nombre_fase.lower() or 'reflexión' in nombre_fase.lower():
            return f"{descripcion_base} para evaluar y reflexionar sobre los aprendizajes"
        else:
            return f"{descripcion_base} para completar las tareas de esta fase"