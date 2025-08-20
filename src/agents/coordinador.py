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
from core.embeddings_manager import EmbeddingsManager

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
        
        # Accedemos a los embeddings
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        proyecto_root = os.path.dirname(base_dir)
        actividades_path = os.path.join(proyecto_root, "data", "actividades")
        self.embeddings_manager = EmbeddingsManager(actividades_path, self.ollama)
        
        self.historial_prompts = []
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
        actividades_similares = self.embeddings_manager.encontrar_actividad_similar(prompt_usuario, top_k=1)
        ejemplo_seleccionado = ""
        if actividades_similares:
            ejemplo_seleccionado = self.embeddings_manager.get_texto_enriquecido(actividades_similares[0][0])
        
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
            'geografía': 'Competencia en ciencias naturales y geografía',
            'geográficos': 'Competencia en ciencias naturales y geografía',
            'accidentes geográficos': 'Competencia en ciencias naturales y geografía',
            'lugares': 'Competencia en ciencias naturales y geografía',
            'viaje': 'Competencia social y cultural',
            'turistas': 'Competencia social y cultural',
            'investigación': 'Competencia científica',
            'ciencias naturales': 'Competencia en ciencias naturales',
            'comunicación': 'Competencia lingüística',
            'trabajo en equipo': 'Competencia social',
            'creatividad': 'Competencia artística',
            'tecnología': 'Competencia digital'
        }
        
        texto_lower = texto.lower()
        for keyword, competencia in keywords.items():
            if keyword in texto_lower and competencia not in competencias_encontradas:
                competencias_encontradas.append(competencia)
        
        return ', '.join(competencias_encontradas) if competencias_encontradas else "Competencia transversal, trabajo colaborativo"
    
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
    def ejecutar_flujo_completo(self, descripcion_actividad: str, info_adicional: str = "") -> Dict:
        """
        FLUJO COMPLETO CON DEBATES - Usa sistema de debate para decisiones críticas
        
        Args:
            descripcion_actividad: Descripción de la actividad educativa deseada
            info_adicional: Información adicional opcional
            
        Returns:
            Proyecto ABP completo con actividad, perfiles y asignaciones
        """
        logger.info(f"🚀 Ejecutando flujo completo para: {descripcion_actividad[:50]}...")
        logger.info(f"🔍 DEBUG - Usando flujo con debates (arquitectura: debate_consenso)")
        
        # PASO 1: DEBATE sobre tipo de actividad y estrategia
        logger.info("🗣️ Iniciando debate sobre tipo de actividad...")
        contexto_debate = {
            'prompt_usuario': descripcion_actividad,
            'info_adicional': info_adicional,
            'tiempo_disponible': '45 minutos',  # Por defecto, se puede extraer del contexto
            'recursos_disponibles': 'estándar'
        }
        
        decision_actividad = self.comunicador.iniciar_debate(
            tema="tipo_actividad",
            decision_critica=contexto_debate,
            agentes_participantes=['analizador_tareas', 'perfilador_estudiantes', 'optimizador_asignaciones'],
            coordinador='coordinador'
        )
        
        # PASO 2: Aplicar la decisión del debate para generar actividad
        logger.info(f"🎯 Aplicando decisión del debate: {decision_actividad.get('tipo', 'consenso')}")
        resultado_actividad = self._aplicar_decision_debate_actividad(decision_actividad, descripcion_actividad)
        
        # PASO 3: Analizar perfiles de estudiantes
        perfiles = self.perfilador.analizar_perfiles()
        
        # PASO 4: Optimizar asignaciones con información del debate
        asignaciones = self.optimizador.optimizar_asignaciones(
            resultado_actividad,  
            perfiles,
            perfilador=self.perfilador
            # NO pasar decision_actividad como contexto_hibrido ya que es un dict, no ContextoHibrido
        )
        
        # PASO 5: Consolidar resultado final - PRESERVAR TAREAS EXTRAÍDAS
        tareas_extraidas = resultado_actividad.get('tareas_extraidas', [])
        proyecto_final = {
            'actividad_personalizada': resultado_actividad.get('actividad', {}),
            'tareas_especificas': tareas_extraidas,
            'perfiles_estudiantes': perfiles,
            'asignaciones_neurotipos': asignaciones,
            'metadatos': {
                'timestamp': datetime.now().isoformat(),
                'descripcion_original': descripcion_actividad,
                'info_adicional': info_adicional,
                'arquitectura': 'debate_consenso',
                'decision_debate': decision_actividad
            }
        }
        
        logger.info("✅ Flujo completo ejecutado exitosamente")
        return proyecto_final
    
    def _aplicar_decision_debate_actividad(self, decision_debate: Dict, descripcion_actividad: str) -> Dict:
        """
        Aplica la decisión del debate para generar la actividad final
        
        Args:
            decision_debate: Resultado del debate entre agentes
            descripcion_actividad: Descripción original del usuario
            
        Returns:
            Actividad generada basada en el consenso del debate
        """
        logger.info("🎯 Aplicando decisión de debate para generar actividad...")
        
        if decision_debate.get('tipo') == 'consenso':
            # Consenso alcanzado - usar propuesta base con adaptaciones
            propuesta_base = decision_debate.get('propuesta_base', {})
            adaptaciones = decision_debate.get('adaptaciones_pedagogicas', {})
            modificaciones = decision_debate.get('modificaciones_viabilidad', {})
            
            # Crear actividad híbrida combinando las decisiones
            resultado = self._crear_actividad_hibrida(propuesta_base, adaptaciones, modificaciones, descripcion_actividad)
            
        elif decision_debate.get('tipo') == 'modificacion_pedagogica':
            # Priorizar criterios pedagógicos
            logger.info("📚 Priorizando criterios pedagógicos del debate")
            adaptaciones = decision_debate.get('adaptaciones_pedagogicas', {})
            resultado = self._crear_actividad_pedagogica_adaptada(adaptaciones, descripcion_actividad)
            
        else:
            # Fallback - usar método original
            logger.warning(f"⚠️ Usando fallback para tipo de decisión: {decision_debate.get('tipo')}")
            resultado = self.analizador_tareas.seleccionar_y_adaptar_actividad(descripcion_actividad)
        
        return resultado
    
    def _crear_actividad_hibrida(self, propuesta_base: Dict, adaptaciones: Dict, modificaciones: Dict, descripcion_actividad: str) -> Dict:
        """
        Crea actividad híbrida combinando elementos de múltiples fuentes según el debate
        
        Args:
            propuesta_base: Propuesta inicial del analizador
            adaptaciones: Adaptaciones pedagógicas del perfilador  
            modificaciones: Modificaciones de viabilidad del optimizador
            descripcion_actividad: Descripción original
            
        Returns:
            Actividad híbrida resultante
        """
        logger.info("🔧 Creando actividad híbrida basada en consenso del debate...")
        
        # Obtener actividades candidatas de la propuesta
        candidatas = propuesta_base.get('actividades_candidatas', [])
        tipo_sugerido = propuesta_base.get('tipo_propuesto', 'taller')
        
        # Seleccionar múltiples actividades para combinar (no solo una)
        actividades_a_combinar = candidatas[:3] if len(candidatas) >= 3 else candidatas
        
        if not actividades_a_combinar:
            # Fallback si no hay candidatas
            return self.analizador_tareas.seleccionar_y_adaptar_actividad(descripcion_actividad)
        
        logger.info(f"🎨 Combinando elementos de {len(actividades_a_combinar)} actividades:")
        for act in actividades_a_combinar:
            logger.info(f"   • {act.get('id', 'unknown')}: {act.get('titulo', 'Sin título')}")
        
        # Crear actividad híbrida
        actividad_hibrida = {
            'id': f"hibrida_{len(actividades_a_combinar)}_fuentes",
            'titulo': f"Actividad Personalizada: {descripcion_actividad[:50]}...",
            'objetivo': f"Actividad híbrida adaptada para: {descripcion_actividad}",
            'tipo_fuente': 'hibrida',
            'fuentes_combinadas': [act.get('id') for act in actividades_a_combinar],
            'estrategia_debate': 'consenso_multiagente'
        }
        
        # CREAR ACTIVIDAD INSPIRADA EN EJEMPLOS (no extraer tareas literalmente)
        ejemplos_inspiracion = []
        
        # Obtener las actividades completas como ejemplos de inspiración
        for candidata in actividades_a_combinar:
            actividad_id = candidata.get('id')
            if actividad_id:
                # Buscar la actividad en el embeddings manager
                actividades_similares = self.embeddings_manager.encontrar_actividad_similar(actividad_id, top_k=1)
                if actividades_similares:
                    # actividades_similares es List[Tuple[str, float, dict]]
                    _, _, actividad_completa = actividades_similares[0]
                    ejemplos_inspiracion.append(actividad_completa)
        
        # GENERAR NUEVA ACTIVIDAD USANDO LLM CON EJEMPLOS COMO INSPIRACIÓN
        tareas_combinadas = self._generar_actividad_con_llm_inspiracion(
            descripcion_actividad, 
            ejemplos_inspiracion, 
            adaptaciones, 
            modificaciones
        )
        
        # Aplicar adaptaciones pedagógicas
        if adaptaciones and isinstance(adaptaciones, dict):
            aprobacion = adaptaciones.get('aprobacion_pedagogica', {})
            if aprobacion.get('estado') in ['APROBADO', 'APROBADO_CON_ADAPTACIONES']:
                logger.info(f"✅ Aplicando adaptaciones pedagógicas: {aprobacion.get('mensaje')}")
        
        # Aplicar modificaciones de viabilidad
        if modificaciones and isinstance(modificaciones, dict):
            aprobacion_practica = modificaciones.get('aprobacion_practica', {})
            if aprobacion_practica.get('estado') in ['VIABLE', 'VIABLE_CON_MODIFICACIONES']:
                logger.info(f"⚙️ Aplicando modificaciones de viabilidad: {aprobacion_practica.get('mensaje')}")
        
        resultado = {
            'actividad': actividad_hibrida,
            'tareas_extraidas': tareas_combinadas,
            'estrategia': 'hibridacion_debate',
            'num_fuentes': len(actividades_a_combinar),
            'adaptaciones_aplicadas': bool(adaptaciones),
            'modificaciones_aplicadas': bool(modificaciones)
        }
        
        logger.info(f"✅ Actividad híbrida creada con {len(tareas_combinadas)} tareas de {len(actividades_a_combinar)} fuentes")
        return resultado
    
    def _extraer_contexto_para_tareas(self) -> Dict:
        """Extrae contexto dinámico para extracción de tareas adaptativa"""
        # Buscar en el contexto híbrido las modalidades especificadas por el usuario
        if hasattr(self, 'contexto_hibrido') and self.contexto_hibrido:
            metadatos = self.contexto_hibrido.metadatos if hasattr(self.contexto_hibrido, 'metadatos') else {}
            
            # DEBUG: Mostrar contenido de metadatos para diagnóstico
            logger.info(f"🔍 DEBUG - Metadatos disponibles: {list(metadatos.keys())}")
            
            # Buscar fases_configuradas en metadatos (formato del controller)
            if 'fases_configuradas' in metadatos:
                fases_configuradas = metadatos['fases_configuradas']
                logger.info(f"🔍 DEBUG - Encontradas fases_configuradas: {fases_configuradas}")
                
                # Convertir fases_configuradas a fases_detalladas
                fases_detalladas = []
                
                for fase_nombre, fase_config in fases_configuradas.items():
                    if isinstance(fase_config, dict) and fase_config.get('incluir', False):
                        fase_detallada = {
                            'nombre': fase_config.get('nombre', fase_nombre.title()),
                            'modalidad': fase_config.get('modalidad', 'colaborativa'),
                            'repartir_tareas': fase_config.get('repartir_tareas', True),
                            'aspectos': fase_config.get('aspectos', [])
                        }
                        fases_detalladas.append(fase_detallada)
                        logger.info(f"🎯 Fase convertida: {fase_detallada['nombre']} (modalidad: {fase_detallada['modalidad']})")
                
                logger.info(f"✅ Convertidas {len(fases_detalladas)} fases de fases_configuradas")
                return {'estructura_fases': {'fases_detalladas': fases_detalladas}}
            
            # Buscar estructura_aplicada en metadatos (formato posterior - JSON final)
            if 'estructura_aplicada' in metadatos:
                estructura_aplicada = metadatos['estructura_aplicada']
                logger.info(f"🔍 DEBUG - Encontrada estructura_aplicada: {estructura_aplicada}")
                
                # Convertir estructura_aplicada a fases_detalladas
                fases_detalladas = []
                
                for fase_nombre, fase_config in estructura_aplicada.items():
                    if isinstance(fase_config, dict) and fase_config.get('incluir', False):
                        fase_detallada = {
                            'nombre': fase_config.get('nombre', fase_nombre.title()),
                            'modalidad': fase_config.get('modalidad', 'colaborativa'),
                            'repartir_tareas': fase_config.get('repartir_tareas', True),
                            'aspectos': fase_config.get('aspectos', [])
                        }
                        fases_detalladas.append(fase_detallada)
                
                logger.info(f"✅ Convertidas {len(fases_detalladas)} fases de estructura_aplicada")
                return {'estructura_fases': {'fases_detalladas': fases_detalladas}}
            
            # Buscar estructura_fases en metadatos (formato antiguo)  
            if 'input_estructurado' in metadatos:
                input_data = metadatos['input_estructurado']
                if isinstance(input_data, dict) and 'estructura_fases' in input_data:
                    return {'estructura_fases': input_data['estructura_fases']}
        
        # Fallback: retornar estructura vacía
        logger.warning("⚠️ No se encontró contexto dinámico, usando modalidades por defecto")
        return {'estructura_fases': {'fases_detalladas': []}}
    
    def _generar_actividad_con_llm_inspiracion(self, descripcion_actividad: str, ejemplos_inspiracion: List[Dict], adaptaciones: Dict, modificaciones: Dict) -> List[Dict]:
        """
        Genera una actividad completamente nueva usando LLM con ejemplos como inspiración
        
        Args:
            descripcion_actividad: Descripción de la actividad solicitada por el usuario
            ejemplos_inspiracion: Actividades ejemplo para inspirarse (NO copiar)
            adaptaciones: Adaptaciones pedagógicas necesarias
            modificaciones: Modificaciones de viabilidad
            
        Returns:
            Lista de tareas y etapas generadas para la nueva actividad
        """
        logger.info(f"🎨 Generando actividad nueva con LLM usando {len(ejemplos_inspiracion)} ejemplos como inspiración...")
        
        # Extraer estructura de fases del usuario
        contexto_dinamico = self._extraer_contexto_para_tareas()
        estructura_fases = contexto_dinamico.get('estructura_fases', {})
        fases_detalladas = estructura_fases.get('fases_detalladas', [])
        
        # Crear prompt estructurado para el LLM
        prompt = self._crear_prompt_generacion_actividad(
            descripcion_actividad, 
            ejemplos_inspiracion, 
            fases_detalladas,
            adaptaciones, 
            modificaciones
        )
        
        try:
            logger.info("🤖 Enviando prompt al LLM para generar actividad completamente nueva...")
            respuesta_llm = self.ollama.generar_respuesta(prompt)
            
            # DEBUG: Mostrar respuesta completa del LLM para diagnóstico
            logger.info(f"🔍 DEBUG - Respuesta completa del LLM (primeros 1000 chars):")
            logger.info(respuesta_llm[:1000] if len(respuesta_llm) > 1000 else respuesta_llm)
            logger.info(f"🔍 DEBUG - Longitud total de respuesta: {len(respuesta_llm)} chars")
            
            # Parsear respuesta del LLM
            actividad_generada = self._parsear_respuesta_actividad_llm(respuesta_llm)
            
            logger.info(f"✅ Actividad generada con {len(actividad_generada.get('etapas', []))} etapas y {sum(len(etapa.get('tareas', [])) for etapa in actividad_generada.get('etapas', []))} tareas")
            
            # Retornar tareas en formato plano para compatibilidad
            return self._extraer_tareas_de_actividad_generada(actividad_generada)
            
        except Exception as e:
            logger.error(f"❌ Error generando actividad con LLM: {e}")
            # Fallback: crear actividad básica
            return self._crear_actividad_fallback(descripcion_actividad, fases_detalladas)
    
    def _crear_prompt_generacion_actividad(self, descripcion_actividad: str, ejemplos_inspiracion: List[Dict], fases_detalladas: List[Dict], adaptaciones: Dict, modificaciones: Dict) -> str:
        """
        Crea prompt estructurado para que el LLM genere una actividad nueva inspirándose en ejemplos y usando plantilla guiada
        """
        
        # Cargar plantilla guiada
        plantilla_guiada = self._cargar_plantilla_guiada()
        
        # Extraer información de adaptaciones
        neurotipos_detectados = []
        adaptaciones_requeridas = {}
        if adaptaciones and 'adaptaciones_pedagogicas' in adaptaciones:
            adap_ped = adaptaciones['adaptaciones_pedagogicas']
            neurotipos_detectados = adap_ped.get('compatibilidad_perfiles', {}).get('neurotipos_detectados', [])
            adaptaciones_requeridas = adap_ped.get('adaptaciones_requeridas', {})
        
        # Crear resumen de las fases solicitadas por el usuario
        fases_usuario = []
        for fase in fases_detalladas:
            nombre = fase.get('nombre', 'Sin nombre')
            modalidad = fase.get('modalidad', 'colaborativa')
            fases_usuario.append(f"- {nombre} (modalidad: {modalidad})")
        
        fases_texto = '\n'.join(fases_usuario) if fases_usuario else "- El usuario no especificó fases concretas"
        
        # Extraer ejemplos de estructura de los JSONs
        estructuras_ejemplo = []
        for i, ejemplo in enumerate(ejemplos_inspiracion[:2], 1):  # Máximo 2 ejemplos
            titulo = ejemplo.get('titulo', 'Sin título')
            etapas = ejemplo.get('etapas', [])
            estructura_ejemplo = f"\n**EJEMPLO {i} - {titulo}**\n"
            estructura_ejemplo += f"Número de etapas: {len(etapas)}\n"
            
            for j, etapa in enumerate(etapas[:3], 1):  # Máximo 3 etapas por ejemplo
                nombre_etapa = etapa.get('nombre', f'Etapa {j}')
                num_tareas = len(etapa.get('tareas', []))
                estructura_ejemplo += f"  • {nombre_etapa} ({num_tareas} tareas)\n"
                
                # Mostrar una tarea de ejemplo para ver el formato COMPLETO
                tareas = etapa.get('tareas', [])
                if tareas:
                    tarea_ejemplo = tareas[0]
                    estructura_ejemplo += f"    - Ejemplo tarea: {tarea_ejemplo.get('nombre', 'Sin nombre')}\n"
                    estructura_ejemplo += f"      Formato: {tarea_ejemplo.get('formato_asignacion', 'sin especificar')}\n"
                    
                    # MOSTRAR ESTRUCTURA COMPLETA DE ASIGNACIONES
                    if 'asignaciones_especificas' in tarea_ejemplo:
                        asig = tarea_ejemplo['asignaciones_especificas']
                        estructura_ejemplo += f"      Asignaciones específicas:\n"
                        
                        # Si tiene grupos
                        if 'grupos' in asig and isinstance(asig['grupos'], list):
                            estructura_ejemplo += f"        - {len(asig['grupos'])} grupos definidos\n"
                            for grupo in asig['grupos'][:2]:  # Mostrar max 2 grupos como ejemplo
                                estructura_ejemplo += f"          • {grupo.get('nombre', 'Grupo')}: {grupo.get('miembros', [])}\n"
                                estructura_ejemplo += f"            Tarea: {grupo.get('tarea_especifica', 'Sin especificar')[:50]}...\n"
                        
                        # Si tiene asignaciones individuales
                        elif 'asignaciones_individuales' in asig:
                            estructura_ejemplo += f"        - Asignaciones individuales para cada alumno\n"
                            asigs_ind = asig['asignaciones_individuales']
                            if isinstance(asigs_ind, list) and asigs_ind:
                                estructura_ejemplo += f"          Ejemplo: {asigs_ind[0].get('alumno', 'Alumno')} - {asigs_ind[0].get('tarea_especifica', '')[:50]}...\n"
            
            estructuras_ejemplo.append(estructura_ejemplo)
        
        ejemplos_texto = '\n'.join(estructuras_ejemplo)
        
        prompt = f"""Eres un experto español en crear actividades educativas ABP (Aprendizaje Basado en Proyectos) para 4º de Primaria.

RESPONDE ÚNICAMENTE EN ESPAÑOL. NO uses etiquetas <think> ni texto en inglés.

**SOLICITUD DEL USUARIO:**
{descripcion_actividad}

**FASES SOLICITADAS POR EL USUARIO:**
{fases_texto}

**NEUROTIPOS EN EL AULA:**
{', '.join(neurotipos_detectados) if neurotipos_detectados else 'Aula típica'}

**ADAPTACIONES NECESARIAS:**
{adaptaciones_requeridas if adaptaciones_requeridas else 'Adaptaciones estándar'}

**EJEMPLOS PARA INSPIRARTE (NO COPIAR - SOLO VER LA CALIDAD Y ESTRUCTURA):**
{ejemplos_texto}

**PLANTILLA GUIADA - USA ESTO COMO INSTRUCCIONES DIRECTAS:**
{plantilla_guiada}

**INTERPRETACIÓN DE LA PLANTILLA:**
- Los textos entre [ ] son INSTRUCCIONES que debes seguir
- Reemplaza cada "[CREAR: ...]" con contenido específico para el tema del usuario  
- Reemplaza cada "[USAR: ...]" con la información que te proporciono
- Reemplaza cada "[RESPONDER: ...]" con respuestas concretas y específicas
- NO incluyas los corchetes [ ] ni las instrucciones en tu respuesta final

**INSTRUCCIONES:**
1. SIGUE LA PLANTILLA GUIADA completamente - es tu guía principal
2. Crea una actividad COMPLETAMENTE NUEVA que responda exactamente a la solicitud del usuario
3. USA los ejemplos solo para inspirarte en la calidad y formato - NO copies contenido
4. RESPONDE A TODAS las preguntas de "[RESPONDER: ...]" de la plantilla con soluciones concretas
5. La actividad DEBE estar relacionada con el tema solicitado por el usuario
6. Estructura usando las fases que pidió el usuario (disponibles en la sección anterior)
7. **CRÍTICO**: Crear asignaciones específicas para todos los 8 estudiantes en cada fase
8. **CRÍTICO**: Responder todas las preguntas de adaptaciones con estrategias específicas y concretas
9. **PROHIBIDO INVENTAR**: Si no tienes información específica para un campo, déjalo vacío o pon "No especificado"
10. **PROHIBIDO**: NO inventes materiales específicos, duraciones exactas, datos o información que no puedas derivar directamente del tema
11. **REGLA DE ORO**: Es mejor un campo vacío que información incorrecta o inventada

RESPONDE SOLO CON EL JSON COMPLETO EN ESPAÑOL siguiendo la estructura de la plantilla guiada - NO agregues explicaciones ni comentarios.

IMPORTANTE: Tu respuesta debe ser un JSON válido que siga exactamente la estructura de la plantilla guiada, pero con todo el contenido entre [ ] reemplazado por contenido real y específico para el tema solicitado.

**RECORDATORIO FINAL**: No rellenes campos con información sin sentido solo por completar. Si no hay información disponible, usa "No especificado" o deja el campo vacío.
Genera la actividad ahora:"""
        
        return prompt
    
    def _cargar_plantilla_guiada(self) -> str:
        """
        Carga la plantilla guiada con instrucciones embebidas
        
        Returns:
            String con la plantilla JSON guiada
        """
        try:
            # Construir ruta a la plantilla
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            proyecto_root = os.path.dirname(base_dir)
            plantilla_path = os.path.join(proyecto_root, "data", "actividades", "plantilla_guiada.json")
            
            # Cargar plantilla
            with open(plantilla_path, 'r', encoding='utf-8') as f:
                plantilla_content = f.read()
                
            logger.debug(f"✅ Plantilla guiada cargada desde: {plantilla_path}")
            return plantilla_content
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando plantilla guiada: {e}")
            # Fallback a plantilla básica embebida
            return '''
{
  "titulo": "[CREAR: Título relacionado con el tema solicitado]",
  "objetivo": "[CREAR: Objetivo específico para el tema y materia solicitados]",
  "etapas": [
    {
      "nombre": "[USAR: Fase configurada por el usuario]",
      "tareas": [
        {
          "asignaciones_especificas": {
            "detalles": "[IMPORTANTE: Crear asignaciones específicas para cada uno de los 8 estudiantes]"
          }
        }
      ]
    }
  ]
}'''
    
    def _parsear_respuesta_actividad_llm(self, respuesta_llm: str) -> Dict:
        """
        Parsea la respuesta del LLM que contiene la actividad generada
        """
        import json
        
        try:
            # Buscar JSON en la respuesta (puede haber texto antes y después)
            inicio_json = respuesta_llm.find('{')
            fin_json = respuesta_llm.rfind('}') + 1
            
            if inicio_json != -1 and fin_json > inicio_json:
                json_texto = respuesta_llm[inicio_json:fin_json]
                
                # Intentar parsing directo primero
                try:
                    actividad_parseada = json.loads(json_texto)
                    if actividad_parseada and isinstance(actividad_parseada, dict):
                        logger.info("✅ Actividad parseada correctamente con JSON nativo")
                        return actividad_parseada
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ JSON nativo falló: {e}")
                    
                # Intentar con parser seguro como fallback
                from utils.json_parser import parse_json_seguro
                actividad_parseada = parse_json_seguro(json_texto)
                
                if actividad_parseada and isinstance(actividad_parseada, dict):
                    logger.info("✅ Actividad parseada correctamente con parser seguro")
                    return actividad_parseada
                else:
                    logger.warning("⚠️ Parser seguro también falló")
            
            # Si no se pudo parsear como JSON, extraer info de texto plano
            logger.warning("⚠️ No se pudo parsear JSON, extrayendo información del texto")
            return self._extraer_actividad_desde_texto_plano(respuesta_llm)
            
        except Exception as e:
            logger.error(f"❌ Error parseando respuesta del LLM: {e}")
            return self._crear_estructura_basica_desde_respuesta(respuesta_llm)
    
    def _extraer_actividad_desde_texto_plano(self, respuesta_llm: str) -> Dict:
        """
        Extrae información de actividad desde texto plano cuando falla el parsing JSON
        """
        import re
        
        # Extraer título
        titulo_match = re.search(r'"titulo":\s*"([^"]+)"', respuesta_llm)
        titulo = titulo_match.group(1) if titulo_match else "Actividad de Accidentes Geográficos"
        
        # Extraer objetivo
        objetivo_match = re.search(r'"objetivo":\s*"([^"]+)"', respuesta_llm)
        objetivo = objetivo_match.group(1) if objetivo_match else "Aprender sobre accidentes geográficos mundiales"
        
        # Buscar etapas mencionadas en el texto
        etapas_encontradas = []
        
        # DEBUG: Verificar si hay etapas válidas primero
        logger.info("🔍 DEBUG - Buscando etapas en la respuesta del LLM...")
        
        # Patrones comunes de etapas
        patrones_etapas = [
            r'"nombre":\s*"([^"]*[Pp]reparación[^"]*)"',
            r'"nombre":\s*"([^"]*[Ee]jecución[^"]*)"',
            r'"nombre":\s*"([^"]*[Rr]eflexión[^"]*)"',
            r'"nombre":\s*"([^"]*[Dd]esarrollo[^"]*)"',
            r'"nombre":\s*"([^"]*[Pp]resentación[^"]*)"'
        ]
        
        for patron in patrones_etapas:
            matches = re.findall(patron, respuesta_llm)
            logger.info(f"🔍 DEBUG - Patrón {patron} encontró: {matches}")
            for match in matches:
                if match not in [e.get('nombre') for e in etapas_encontradas]:
                    etapas_encontradas.append({
                        'nombre': match,
                        'descripcion': f'Etapa de {match.lower()}',
                        'tareas': [{
                            'nombre': f'Actividad de {match}',
                            'descripcion': f'Los estudiantes realizan actividades de {match.lower()} sobre el tema solicitado',
                            'formato_asignacion': 'parejas',
                            'etapa': match
                        }]
                    })
        
        logger.info(f"🔍 DEBUG - Total etapas encontradas con regex: {len(etapas_encontradas)}")
        
        # Si no encontramos TODAS las etapas esperadas, crear etapas usando el contexto del usuario
        contexto_dinamico = self._extraer_contexto_para_tareas()
        estructura_fases = contexto_dinamico.get('estructura_fases', {})
        fases_detalladas = estructura_fases.get('fases_detalladas', [])
        
        if len(etapas_encontradas) < len(fases_detalladas):
            logger.info(f"🔍 DEBUG - Solo {len(etapas_encontradas)} etapas encontradas, pero usuario configuró {len(fases_detalladas)} fases")
            logger.info("🎯 Usando configuración del usuario para generar todas las etapas...")
            # Limpiar etapas parciales y generar completas desde configuración
            etapas_encontradas = []
            
            if fases_detalladas:
                # Crear etapas basadas en la configuración del usuario
                logger.info(f"🎯 Creando etapas basadas en {len(fases_detalladas)} fases configuradas por el usuario")
                for i, fase in enumerate(fases_detalladas):
                    logger.info(f"🔍 DEBUG - Procesando fase {i+1}: {fase}")
                for fase in fases_detalladas:
                    nombre_fase = fase.get('nombre', 'Fase sin nombre')
                    modalidad = fase.get('modalidad', 'parejas')
                    
                    # Detectar tipo de actividad según el tema
                    # Obtener descripción desde contexto híbrido
                    descripcion_actividad = self.contexto_hibrido.metadatos.get('prompt_usuario', 'actividad educativa')
                    
                    if 'preparación' in nombre_fase.lower():
                        tarea_especifica = self._crear_tarea_preparacion_geografica(descripcion_actividad, modalidad)
                    elif 'ejecución' in nombre_fase.lower() or 'desarrollo' in nombre_fase.lower():
                        tarea_especifica = self._crear_tarea_ejecucion_geografica(descripcion_actividad, modalidad)
                    elif 'reflexión' in nombre_fase.lower():
                        tarea_especifica = self._crear_tarea_reflexion_geografica(descripcion_actividad, modalidad)
                    else:
                        tarea_especifica = self._crear_tarea_generica_geografica(descripcion_actividad, modalidad, nombre_fase)
                    
                    etapas_encontradas.append({
                        'nombre': nombre_fase,
                        'descripcion': f'Los estudiantes trabajan en {modalidad} para {tarea_especifica["descripcion"].lower()}',
                        'tareas': [tarea_especifica]
                    })
            else:
                # Fallback si no hay configuración del usuario
                etapas_encontradas = [
                {
                    'nombre': 'Preparación: Investigación de Destinos',
                    'descripcion': 'Las parejas seleccionan y investigan accidentes geográficos',
                    'tareas': [{
                        'nombre': 'Selección de accidentes geográficos',
                        'descripcion': 'Cada pareja elige un accidente geográfico (Gran Cañón, Cataratas Victoria, etc.) para investigar',
                        'formato_asignacion': 'parejas',
                        'etapa': 'Preparación: Investigación de Destinos'
                    }]
                },
                {
                    'nombre': 'Ejecución: Creación de Cuaderno de Viaje',
                    'descripcion': 'Las parejas desarrollan su cuaderno de viaje con información recopilada',
                    'tareas': [{
                        'nombre': 'Desarrollo del cuaderno de viaje',
                        'descripcion': 'Crear páginas con información, ilustraciones y datos sobre el accidente geográfico elegido',
                        'formato_asignacion': 'parejas',
                        'etapa': 'Ejecución: Creación de Cuaderno de Viaje'
                    }]
                },
                {
                    'nombre': 'Reflexión: Presentación de Viajes',
                    'descripcion': 'Las parejas comparten sus viajes y reflexionan sobre lo aprendido',
                    'tareas': [{
                        'nombre': 'Presentación de cuadernos de viaje',
                        'descripcion': 'Cada pareja presenta su accidente geográfico y comparte experiencias del "viaje"',
                        'formato_asignacion': 'parejas',
                        'etapa': 'Reflexión: Presentación de Viajes'
                    }]
                }
            ]
        
        logger.info(f"✅ Actividad extraída desde texto plano con {len(etapas_encontradas)} etapas")
        
        return {
            "titulo": titulo,
            "objetivo": objetivo,
            "nivel_educativo": "4º de Primaria",
            "duracion_minutos": "120 minutos",
            "etapas": etapas_encontradas
        }
    
    def _crear_estructura_basica_desde_respuesta(self, respuesta_llm: str) -> Dict:
        """
        Crea estructura básica si el parsing JSON falla
        MEJORADO: No inventar información, solo crear estructura mínima válida
        """
        # Validar si la respuesta parece coherente
        respuesta_validada = self._validar_respuesta_llm(respuesta_llm)
        
        if respuesta_validada:
            descripcion_tarea = respuesta_validada
        else:
            # Si la respuesta no tiene sentido, usar descripción genérica
            logger.warning("⚠️ Respuesta del LLM incoherente, usando descripción genérica")
            descripcion_tarea = "Actividad educativa sobre el tema solicitado"
        
        return {
            "titulo": "Actividad Educativa",
            "objetivo": "Desarrollar competencias según el tema solicitado",
            "nivel_educativo": "4º de Primaria", 
            "duracion_minutos": "90-120 minutos",
            "etapas": [
                {
                    "nombre": "Desarrollo de la Actividad",
                    "descripcion": "Los estudiantes trabajan en el tema propuesto",
                    "tareas": [
                        {
                            "nombre": "Actividad Principal",
                            "descripcion": descripcion_tarea,
                            "formato_asignacion": "parejas",
                            "etapa": "Desarrollo de la Actividad"
                        }
                    ]
                }
            ]
        }
    
    def _validar_respuesta_llm(self, respuesta: str) -> Optional[str]:
        """
        Valida si la respuesta del LLM tiene sentido o es incoherente
        
        Returns:
            String válido si la respuesta tiene sentido, None si es incoherente
        """
        if not respuesta or len(respuesta.strip()) < 20:
            return None
            
        respuesta_clean = respuesta.strip()
        
        # Detectar respuestas incoherentes comunes
        indicadores_incoherentes = [
            'First, I need to',
            'I should create',
            'For each variation',
            'Let me check',
            'Make sure',
            'I need to ensure'
        ]
        
        for indicador in indicadores_incoherentes:
            if indicador in respuesta_clean[:100]:  # Verificar primeros 100 chars
                logger.debug(f"🚫 Respuesta incoherente detectada: contiene '{indicador}'")
                return None
        
        # Si pasa las validaciones, tomar máximo 200 caracteres
        return respuesta_clean[:200] + "..." if len(respuesta_clean) > 200 else respuesta_clean
    
    def _extraer_tareas_de_actividad_generada(self, actividad_generada: Dict) -> List[Dict]:
        """
        Extrae tareas en formato plano de la actividad generada por LLM
        """
        tareas_extraidas = []
        contador = 1
        
        etapas = actividad_generada.get('etapas', [])
        for etapa in etapas:
            nombre_etapa = etapa.get('nombre', 'Etapa Principal')
            tareas_etapa = etapa.get('tareas', [])
            
            for tarea in tareas_etapa:
                tarea_normalizada = {
                    'id': f'tarea_{contador:02d}',
                    'nombre': tarea.get('nombre', f'Tarea {contador}'),
                    'descripcion': tarea.get('descripcion', 'Actividad a realizar'),
                    'etapa': nombre_etapa,  # CRÍTICO: Asignar etapa correctamente
                    'formato_asignacion': tarea.get('formato_asignacion', 'parejas'),
                    'complejidad': 3,
                    'tipo': 'colaborativa',
                    'tiempo_estimado': 30,
                    'competencias_requeridas': ['transversales'],
                    'asignaciones_especificas': tarea.get('asignaciones_especificas', {}),
                    'dependencias': []
                }
                tareas_extraidas.append(tarea_normalizada)
                contador += 1
        
        logger.info(f"✅ Extraídas {len(tareas_extraidas)} tareas de actividad generada con etapas asignadas")
        return tareas_extraidas
    
    def _crear_actividad_fallback(self, descripcion_actividad: str, fases_detalladas: List[Dict]) -> List[Dict]:
        """
        Crea actividad básica como fallback si falla la generación con LLM
        """
        logger.warning("⚠️ Creando actividad fallback básica")
        
        # Crear etapas básicas basadas en las fases del usuario
        if not fases_detalladas:
            fases_detalladas = [
                {'nombre': 'Preparación', 'modalidad': 'parejas'},
                {'nombre': 'Desarrollo', 'modalidad': 'parejas'},
                {'nombre': 'Presentación', 'modalidad': 'clase_completa'}
            ]
        
        tareas_fallback = []
        contador = 1
        
        for fase in fases_detalladas:
            nombre_fase = fase.get('nombre', f'Fase {contador}')
            modalidad = fase.get('modalidad', 'parejas')
            
            tarea_fallback = {
                'id': f'tarea_{contador:02d}',
                'nombre': f'{nombre_fase}: Trabajo sobre {descripcion_actividad[:50]}...',
                'descripcion': f'Los estudiantes trabajan en {modalidad} desarrollando actividades relacionadas con: {descripcion_actividad}',
                'etapa': nombre_fase,  # CRÍTICO: Asignar etapa
                'formato_asignacion': modalidad,
                'complejidad': 3,
                'tipo': 'colaborativa',
                'tiempo_estimado': 30,
                'competencias_requeridas': ['transversales'],
                'dependencias': []
            }
            tareas_fallback.append(tarea_fallback)
            contador += 1
        
        return tareas_fallback
    
    def _crear_tarea_preparacion_geografica(self, descripcion_actividad: str, modalidad: str) -> Dict:
        """Crea tarea específica para fase de preparación adaptada al tema del usuario"""
        # Extraer palabras clave del tema para adaptar la tarea
        if 'geográfic' in descripcion_actividad.lower() or 'viaj' in descripcion_actividad.lower():
            nombre = 'Selección y asignación de rutas temáticas'
            descripcion = f'Cada pareja selecciona elementos relacionados con {descripcion_actividad} y se asigna roles específicos para su investigación y desarrollo'
        elif 'matemátic' in descripcion_actividad.lower() or 'número' in descripcion_actividad.lower():
            nombre = 'Preparación de materiales y conceptos matemáticos'
            descripcion = f'Cada pareja prepara materiales y revisa conceptos necesarios para {descripcion_actividad}'
        elif 'histori' in descripcion_actividad.lower() or 'época' in descripcion_actividad.lower():
            nombre = 'Investigación de contexto histórico'
            descripcion = f'Cada pareja investiga el contexto y antecedentes necesarios para {descripcion_actividad}'
        else:
            nombre = 'Preparación temática colaborativa'
            descripcion = f'Cada pareja se prepara y organiza para desarrollar actividades relacionadas con {descripcion_actividad}'
            
        # Crear asignaciones específicas según modalidad
        asignaciones_especificas = self._crear_asignaciones_por_modalidad(modalidad, descripcion_actividad, 'preparacion')
        
        return {
            'nombre': nombre,
            'descripcion': descripcion,
            'formato_asignacion': modalidad,
            'etapa': 'Preparación con reparto específico de tareas (trabajo parejas)',
            'asignaciones_especificas': asignaciones_especificas
        }
    
    def _crear_asignaciones_por_modalidad(self, modalidad: str, descripcion_actividad: str, fase: str) -> Dict:
        """
        Crea asignaciones específicas para los 8 estudiantes según la modalidad
        
        Args:
            modalidad: parejas, grupos_pequeños, clase_completa, etc.
            descripcion_actividad: Descripción de la actividad para contexto
            fase: preparacion, ejecucion, reflexion
            
        Returns:
            Dict con estructura de asignaciones específicas
        """
        if modalidad == 'parejas':
            return {
                'modalidad': 'parejas',
                'grupos': [
                    {
                        'nombre': 'Pareja 1',
                        'miembros': ['Elena', 'Ana'],
                        'tarea_especifica': f'Investigar con apoyo visual estructurado para Elena (TEA)',
                        'justificacion': 'Ana (altas capacidades) puede apoyar a Elena con estructura clara'
                    },
                    {
                        'nombre': 'Pareja 2',
                        'miembros': ['Luis', 'Hugo'],
                        'tarea_especifica': f'Desarrollar actividad con componentes dinámicos para Luis (TDAH)',
                        'justificacion': 'Hugo puede ayudar a canalizar la energía de Luis productivamente'
                    },
                    {
                        'nombre': 'Pareja 3',
                        'miembros': ['María', 'Emma'],
                        'tarea_especifica': f'Trabajar de manera equilibrada en la actividad',
                        'justificacion': 'Pareja con habilidades complementarias'
                    },
                    {
                        'nombre': 'Pareja 4',
                        'miembros': ['Alex', 'Sara'],
                        'tarea_especifica': f'Desarrollar aspectos analíticos de la actividad',
                        'justificacion': 'Ambos con buenas capacidades analíticas'
                    }
                ]
            }
        elif modalidad == 'clase_completa' or modalidad == 'clase completa':
            return {
                'modalidad': 'clase_completa',
                'organizacion': 'Presentación por turnos',
                'orden_participacion': [
                    {'estudiante': 'Elena', 'rol': 'Presentadora con apoyo visual', 'tiempo': '3 min'},
                    {'estudiante': 'Luis', 'rol': 'Dinamizador de actividad', 'tiempo': '3 min'},
                    {'estudiante': 'Ana', 'rol': 'Coordinadora general', 'tiempo': '5 min'},
                    {'estudiante': 'María', 'rol': 'Secretaria', 'tiempo': '3 min'},
                    {'estudiante': 'Emma', 'rol': 'Apoyo visual', 'tiempo': '3 min'},
                    {'estudiante': 'Hugo', 'rol': 'Presentador', 'tiempo': '3 min'},
                    {'estudiante': 'Alex', 'rol': 'Analista', 'tiempo': '3 min'},
                    {'estudiante': 'Sara', 'rol': 'Sintetizadora', 'tiempo': '3 min'}
                ]
            }
        else:  # grupos pequeños u otras modalidades
            return {
                'modalidad': 'grupos',
                'grupos': [
                    {
                        'nombre': 'Grupo A',
                        'miembros': ['Elena', 'Ana', 'María', 'Emma'],
                        'tarea_especifica': 'Desarrollo con estructura y apoyo visual',
                        'justificacion': 'Ana lidera, Elena tiene apoyo múltiple'
                    },
                    {
                        'nombre': 'Grupo B',
                        'miembros': ['Luis', 'Hugo', 'Alex', 'Sara'],
                        'tarea_especifica': 'Desarrollo dinámico y analítico',
                        'justificacion': 'Balance entre energía de Luis y análisis del resto'
                    }
                ]
            }
    
    def _crear_tarea_ejecucion_geografica(self, descripcion_actividad: str, modalidad: str) -> Dict:
        """Crea tarea específica para fase de ejecución adaptada al tema del usuario"""
        # Adaptar según el tema
        if 'geográfic' in descripcion_actividad.lower() or 'viaj' in descripcion_actividad.lower():
            nombre = 'Desarrollo del proyecto temático principal'
            descripcion = f'Las parejas desarrollan el proyecto principal sobre {descripcion_actividad}, creando materiales, investigando y preparando presentaciones según sus roles asignados'
        elif 'matemátic' in descripcion_actividad.lower():
            nombre = 'Resolución y creación de problemas matemáticos'
            descripcion = f'Las parejas trabajan resolviendo y creando ejercicios relacionados con {descripcion_actividad}'
        elif 'cienci' in descripcion_actividad.lower():
            nombre = 'Experimentación y análisis científico'
            descripcion = f'Las parejas realizan experimentos y análisis sobre {descripcion_actividad}'
        else:
            nombre = 'Desarrollo del proyecto colaborativo'
            descripcion = f'Las parejas desarrollan colaborativamente el proyecto sobre {descripcion_actividad}'
            
        return {
            'nombre': nombre,
            'descripcion': descripcion,
            'formato_asignacion': modalidad,
            'etapa': 'Ejecución principal con investigación, creatividad, presentación, construcción/creación'
        }
    
    def _crear_tarea_reflexion_geografica(self, descripcion_actividad: str, modalidad: str) -> Dict:
        """Crea tarea específica para fase de reflexión adaptada al tema del usuario"""
        return {
            'nombre': 'Presentación y reflexión grupal',
            'descripcion': f'Los estudiantes presentan sus trabajos sobre {descripcion_actividad} y reflexionan grupalmente sobre lo aprendido, compartiendo experiencias y conclusiones',
            'formato_asignacion': modalidad,
            'etapa': 'Reflexión con reparto específico de tareas (trabajo clase completa)'
        }
    
    def _crear_tarea_generica_geografica(self, descripcion_actividad: str, modalidad: str, nombre_fase: str) -> Dict:
        """Crea tarea genérica adaptada al tema del usuario"""
        return {
            'nombre': f'Actividades de {nombre_fase}',
            'descripcion': f'Los estudiantes trabajan en {modalidad} desarrollando actividades relacionadas con {descripcion_actividad}',
            'formato_asignacion': modalidad,
            'etapa': nombre_fase
        }
    
    def _crear_actividad_pedagogica_adaptada(self, adaptaciones: Dict, descripcion_actividad: str) -> Dict:
        """
        Crea actividad priorizando adaptaciones pedagógicas específicas
        
        Args:
            adaptaciones: Adaptaciones pedagógicas requeridas
            descripcion_actividad: Descripción original
            
        Returns:
            Actividad adaptada pedagógicamente
        """
        logger.info("📚 Creando actividad con prioridad pedagógica...")
        
        # Por ahora, usar el método original pero marcar que se aplicaron adaptaciones
        resultado = self.analizador_tareas.seleccionar_y_adaptar_actividad(descripcion_actividad)
        
        # Marcar las adaptaciones que se aplicaron
        resultado['adaptaciones_pedagogicas'] = adaptaciones
        resultado['estrategia'] = 'adaptacion_pedagogica_priorizada'
        
        return resultado

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
   🎯 Criterios: {', '.join(str(c) for c in info.get('criterios_aplicados', []))}
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
            # Convertir modalidades a strings si son diccionarios
            modalidades_str = []
            for mod in modalidades:
                if isinstance(mod, dict):
                    modalidades_str.append(mod.get('nombre', str(mod)))
                else:
                    modalidades_str.append(str(mod))
            logger.info(f"👥 Modalidades preferidas registradas: {', '.join(modalidades_str)}")
            
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