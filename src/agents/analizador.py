"""
Agente Analizador de Tareas (Task Analyzer Agent).
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator
from core.embeddings_manager import EmbeddingsManager
from agents.base_agent import BaseAgent
from models.proyecto import Tarea

class AgenteAnalizadorTareas(BaseAgent):
    """Agente Analizador de Tareas (Task Analyzer Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator, embeddings_manager: EmbeddingsManager = None):
        """
        Inicializa el Agente Analizador de Tareas
        
        Args:
            ollama_integrator: Integrador de LLM
            embeddings_manager: Gestor de embeddings (opcional, se inicializa automáticamente)
        """
        super().__init__(ollama_integrator)
        
        # Inicializar EmbeddingsManager si no se proporciona
        if embeddings_manager is None:
            import os
            # Ruta base a las actividades JSON
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            proyecto_root = os.path.dirname(base_dir)
            actividades_base_path = os.path.join(proyecto_root, "data", "actividades")
            
            self.embeddings_manager = EmbeddingsManager(actividades_base_path, ollama_integrator)
        else:
            self.embeddings_manager = embeddings_manager
    
    def _detectar_tipo_actividad(self, prompt: str) -> Dict:
        """
        Detecta el tipo de actividad solicitada basándose en palabras clave
        
        Args:
            prompt: Descripción de la actividad solicitada
            
        Returns:
            Diccionario con tipo detectado, confianza y palabras clave encontradas
            {"tipo": "gymnkana", "confianza": 0.85, "palabras_clave": [...]}
        """
        # Definir tipos de actividad y sus palabras clave características
        tipos_actividad = {
            'gymnkana': {
                'palabras_clave': ['gymnkana', 'feria', 'puestos', 'rotación', 'circuito', 'pruebas', 'estaciones', 'retos'],
                'peso': 1.0
            },
            'proyecto': {
                'palabras_clave': ['proyecto', 'construir', 'crear', 'modelo', 'producto final', 'diseñar', 'elaborar'],
                'peso': 1.0
            },
            'taller': {
                'palabras_clave': ['taller', 'fábrica', 'laboratorio', 'exploración', 'materiales', 'experimento', 'manipular'],
                'peso': 1.0
            },
            'investigacion': {
                'palabras_clave': ['investigar', 'investigación', 'estudiar', 'analizar', 'buscar información', 'documentar'],
                'peso': 0.9
            },
            'presentacion': {
                'palabras_clave': ['presentar', 'exponer', 'mostrar', 'comunicar', 'compartir resultados'],
                'peso': 0.8
            }
        }
        
        prompt_lower = prompt.lower()
        resultados = {}
        
        # Calcular puntuación para cada tipo
        for tipo, config in tipos_actividad.items():
            palabras_encontradas = []
            puntuacion = 0
            
            for palabra in config['palabras_clave']:
                if palabra in prompt_lower:
                    palabras_encontradas.append(palabra)
                    puntuacion += config['peso']
            
            # Normalizar puntuación por número de palabras clave posibles
            max_puntuacion = len(config['palabras_clave']) * config['peso']
            confianza = min(1.0, puntuacion / max_puntuacion) if max_puntuacion > 0 else 0
            
            if palabras_encontradas:  # Solo incluir si encontró alguna palabra
                resultados[tipo] = {
                    'confianza': confianza,
                    'palabras_encontradas': palabras_encontradas,
                    'puntuacion_raw': puntuacion
                }
        
        # Determinar el tipo con mayor confianza
        if resultados:
            tipo_principal = max(resultados.keys(), key=lambda k: resultados[k]['confianza'])
            
            return {
                'tipo': tipo_principal,
                'confianza': resultados[tipo_principal]['confianza'],
                'palabras_clave': resultados[tipo_principal]['palabras_encontradas'],
                'tipos_detectados': {k: v['confianza'] for k, v in resultados.items()}
            }
        else:
            # Fallback si no se detecta ningún tipo específico
            return {
                'tipo': 'general',
                'confianza': 0.5,
                'palabras_clave': [],
                'tipos_detectados': {}
            }
    
    def _extraer_elementos_reutilizables(self, actividades: List) -> Dict:
        """
        Extrae elementos específicos reutilizables de múltiples actividades
        
        Args:
            actividades: Lista de actividades (dict o objetos Activity)
            
        Returns:
            Diccionario con elementos organizados por categoría:
            {
                "puestos": [...],
                "materiales": [...], 
                "adaptaciones": [...],
                "metodologias": [...]
            }
        """
        elementos = {
            'puestos': set(),
            'materiales': set(),
            'adaptaciones': set(),
            'metodologias': set(),
            'competencias': set(),
            'recursos_digitales': set()
        }
        
        # Patrones para identificar elementos específicos
        patrones_extraccion = {
            'puestos': [
                r'puesto\s+\d+[:\-]?\s*([^\.]+)',
                r'estación\s+\d+[:\-]?\s*([^\.]+)',
                r'reto\s+\d+[:\-]?\s*([^\.]+)',
                r'actividad\s+\d+[:\-]?\s*([^\.]+)'
            ],
            'materiales': [
                r'material(?:es)?[:\-]?\s*([^\.]+)',
                r'necesario[s]?[:\-]?\s*([^\.]+)',
                r'recursos[:\-]?\s*([^\.]+)'
            ],
            'adaptaciones': [
                r'(?:para|adaptación)\s+(?:TEA|TDAH|altas capacidades)[:\-]?\s*([^\.]+)',
                r'estudiantes?\s+con\s+[^\.]+[:\-]?\s*([^\.]+)',
                r'apoyo\s+visual[:\-]?\s*([^\.]+)'
            ]
        }
        
        for actividad in actividades:
            # Convertir a diccionario si es necesario
            if hasattr(actividad, '__dict__'):
                actividad_dict = actividad.__dict__
            elif hasattr(actividad, 'to_dict'):
                actividad_dict = actividad.to_dict()
            else:
                actividad_dict = actividad
            
            # Extraer texto completo de la actividad
            texto_completo = self._extraer_texto_completo_actividad(actividad_dict)
            
            # Aplicar patrones de extracción
            for categoria, patrones in patrones_extraccion.items():
                for patron in patrones:
                    matches = re.findall(patron, texto_completo, re.IGNORECASE)
                    for match in matches:
                        elemento_limpio = match.strip().strip(',.:;')
                        if len(elemento_limpio) > 3:  # Filtrar elementos muy cortos
                            elementos[categoria].add(elemento_limpio)
            
            # Extraer competencias específicas
            competencias = actividad_dict.get('competencias', '')
            if isinstance(competencias, str):
                comp_list = [c.strip() for c in competencias.split(',')]
                elementos['competencias'].update(comp_list)
            elif isinstance(competencias, list):
                elementos['competencias'].update(competencias)
            
            # Extraer metodologías de las etapas
            etapas = actividad_dict.get('etapas', [])
            for etapa in etapas:
                if isinstance(etapa, dict):
                    nombre_etapa = etapa.get('nombre', '')
                    if 'metodología' in nombre_etapa.lower() or 'método' in nombre_etapa.lower():
                        elementos['metodologias'].add(nombre_etapa)
        
        # Convertir sets a listas ordenadas y filtrar elementos duplicados similares
        resultado = {}
        for categoria, conjunto in elementos.items():
            lista_filtrada = self._filtrar_elementos_similares(list(conjunto))
            resultado[categoria] = sorted(lista_filtrada)
        
        return resultado
    
    def _extraer_texto_completo_actividad(self, actividad_dict: Dict) -> str:
        """
        Extrae todo el texto relevante de una actividad para análisis
        
        Args:
            actividad_dict: Diccionario con datos de actividad
            
        Returns:
            String con todo el texto concatenado
        """
        textos = []
        
        # Campos principales de texto
        campos_texto = ['titulo', 'objetivo', 'descripcion', 'observaciones']
        for campo in campos_texto:
            valor = actividad_dict.get(campo, '')
            if valor:
                textos.append(str(valor))
        
        # Extraer texto de etapas y tareas
        etapas = actividad_dict.get('etapas', [])
        for etapa in etapas:
            if isinstance(etapa, dict):
                textos.append(etapa.get('nombre', ''))
                textos.append(etapa.get('descripcion', ''))
                
                tareas = etapa.get('tareas', [])
                for tarea in tareas:
                    if isinstance(tarea, dict):
                        textos.append(tarea.get('nombre', ''))
                        textos.append(tarea.get('descripcion', ''))
        
        return ' '.join(filter(None, textos))
    
    def _filtrar_elementos_similares(self, elementos: List[str]) -> List[str]:
        """
        Filtra elementos muy similares para evitar duplicación
        
        Args:
            elementos: Lista de elementos a filtrar
            
        Returns:
            Lista filtrada sin duplicados similares
        """
        if not elementos:
            return []
        
        elementos_filtrados = []
        
        for elemento in elementos:
            es_similar = False
            elemento_lower = elemento.lower()
            
            # Verificar si es muy similar a alguno ya incluido
            for incluido in elementos_filtrados:
                incluido_lower = incluido.lower()
                
                # Verificar similitud por substring (uno contiene al otro)
                if (len(elemento_lower) > 10 and elemento_lower in incluido_lower) or \
                   (len(incluido_lower) > 10 and incluido_lower in elemento_lower):
                    es_similar = True
                    break
                
                # Verificar similitud por palabras comunes
                palabras_elemento = set(elemento_lower.split())
                palabras_incluido = set(incluido_lower.split())
                if len(palabras_elemento) > 1 and len(palabras_incluido) > 1:
                    interseccion = palabras_elemento & palabras_incluido
                    union = palabras_elemento | palabras_incluido
                    similitud = len(interseccion) / len(union) if union else 0
                    if similitud > 0.7:  # 70% de similitud
                        es_similar = True
                        break
            
            if not es_similar:
                elementos_filtrados.append(elemento)
        
        return elementos_filtrados
    
    def analizar_actividad_completa(self, prompt: str, incluir_elementos_reutilizables: bool = True) -> Dict:
        """
        Método público para análisis completo de actividad que integra todas las mejoras
        
        Args:
            prompt: Descripción de la actividad solicitada
            incluir_elementos_reutilizables: Si incluir extracción de elementos reutilizables
            
        Returns:
            Diccionario completo con tipo detectado, actividad seleccionada y elementos
        """
        self._log_processing_start(f"Análisis completo para: '{prompt[:50]}...'")
        
        # 1. Detectar tipo de actividad
        tipo_detectado = self._detectar_tipo_actividad(prompt)
        
        # 2. Seleccionar y adaptar actividad
        resultado_actividad = self.seleccionar_y_adaptar_actividad(prompt)
        
        # 3. Extraer tareas usando el método híbrido existente
        actividad = resultado_actividad.get('actividad', {})
        tareas_extraidas = self.extraer_tareas_hibrido(actividad, prompt)
        
        # 4. Compilar resultado completo
        resultado_completo = {
            'tipo_detectado': tipo_detectado,
            'actividad_seleccionada': resultado_actividad,
            'tareas_extraidas': [
                {
                    'id': tarea.id,
                    'descripcion': tarea.descripcion,
                    'competencias_requeridas': tarea.competencias_requeridas,
                    'complejidad': tarea.complejidad,
                    'tipo': tarea.tipo,
                    'tiempo_estimado': tarea.tiempo_estimado
                } for tarea in tareas_extraidas
            ],
            'num_tareas': len(tareas_extraidas)
        }
        
        # 5. Añadir elementos reutilizables si se solicita
        if incluir_elementos_reutilizables and 'elementos_reutilizables' in resultado_actividad:
            resultado_completo['elementos_reutilizables'] = resultado_actividad['elementos_reutilizables']
        
        self._log_processing_end(f"Análisis completo: {tipo_detectado['tipo']}, {len(tareas_extraidas)} tareas")
        return resultado_completo

    def extraer_tareas_hibrido(self, actividad_data: Dict, prompt_usuario: str = "", contexto_hibrido=None) -> List[Tarea]:
        """
       Extrae tareas usando la mejor estrategia disponible. Las tareas son actividades concretas que los estudiantes deben realizar 
       (recortar una plantilla, resolver un problema que le damos concreto, etc) Debemos definir las tareas que cada alumno deberá realizar, en ocasiones
       los estudiantes pueden hacer las mismas tareas, y en otras ocasiones pueden diferenciarse las tareas entre cada uno de los estudiantes.

       Análisis profundo específico de cada actividad
        
        Args:
            actividad_data: Datos de la actividad (JSON o dict)
            prompt_usuario: Prompt del usuario (opcional)
            contexto_hibrido: Contexto híbrido compartido (opcional)
            
        Returns:
            Lista de objetos Tarea garantizada
        """
        self._log_processing_start(f"Extracción híbrida de tareas mejorada")
        
        # Usar información del contexto híbrido si está disponible
        if contexto_hibrido:
            # Registrar uso del contexto en el análisis
            contexto_hibrido.registrar_decision("AgenteAnalizador", "Iniciando análisis de tareas con contexto híbrido", {
                'tiene_perfiles': len(contexto_hibrido.perfiles_estudiantes) > 0,
                'metadatos_disponibles': list(contexto_hibrido.metadatos.keys()),
                'prompt_usuario': prompt_usuario[:50] + '...' if prompt_usuario else 'No disponible'
            })
            self.logger.info(f"🔄 Usando contexto híbrido con {len(contexto_hibrido.perfiles_estudiantes)} perfiles")
        
        # ESTRATEGIA 1: ANÁLISIS PROFUNDO CON LLM 
        if prompt_usuario:
            self.logger.info("🧠 Estrategia 1: Análisis profundo específico (MVP)")
            tareas = self._analizar_actividad_profundo(prompt_usuario, actividad_data)
            if tareas:
                self._log_processing_end(f"✅ Análisis profundo: {len(tareas)} tareas específicas")
                
                # Registrar éxito en contexto híbrido si está disponible
                if contexto_hibrido:
                    contexto_hibrido.registrar_decision("AgenteAnalizador", f"Análisis profundo exitoso: {len(tareas)} tareas generadas", {
                        'metodo_usado': 'analisis_profundo_especifico',
                        'tareas_generadas': len(tareas),
                        'actividad_personalizada': actividad_data.get('tipo') == 'actividad_personalizada'
                    })
                
                # Si tenemos actividad personalizada, usarla como información base
                if actividad_data.get('tipo') == 'actividad_personalizada':
                    self.logger.info("📋 Usando actividad personalizada del prompt")
                    return tareas
                else:
                    return tareas
        
        # ESTRATEGIA 2: Extraer directamente desde JSON (PRIORIDAD ALTA)
        if self._tiene_estructura_json_valida(actividad_data):
            self.logger.info("🎯 Estrategia 2: Extracción directa desde JSON ADAPTATIVA")
            # Extraer contexto dinámico del contexto híbrido
            contexto_dinamico = self._extraer_contexto_dinamico(contexto_hibrido)
            tareas = self._extraer_tareas_desde_json(actividad_data, contexto_dinamico)
            if tareas:
                self._log_processing_end(f"✅ Extraídas {len(tareas)} tareas desde JSON adaptativo")
                return tareas
        else:
            self.logger.warning(f"⚠️ Actividad no tiene estructura JSON válida. Claves disponibles: {list(actividad_data.keys()) if isinstance(actividad_data, dict) else type(actividad_data)}")
        
        # ESTRATEGIA 3: Usar plantilla estructurada con LLM
        self.logger.info("🎯 Estrategia 3: Plantilla estructurada con LLM")
        tareas = self._generar_tareas_con_plantilla(actividad_data, prompt_usuario)
        if tareas:
            self._log_processing_end(f"✅ Generadas {len(tareas)} tareas con plantilla")
            return tareas
        
        # ESTRATEGIA 4: Prompt minimalista (FALLBACK)
        self.logger.warning("🎯 Estrategia 4: Prompt minimalista de emergencia")
        tareas = self._generar_tareas_prompt_simple(actividad_data)
        if tareas:
            self._log_processing_end(f"⚠️ Generadas {len(tareas)} tareas con prompt simple")
            return tareas
        
        # ÚLTIMO RECURSO: Tareas hardcodeadas
        self.logger.error("❌ Todas las estrategias fallaron, usando tareas de emergencia")
        return self._crear_tareas_fallback()
    
    def _analizar_actividad_profundo(self, descripcion_actividad: str, actividad_data: Dict) -> List[Tarea]:
        """
        Análisis profundo específico de cada actividad 
        
        Args:
            descripcion_actividad: Descripción específica de la actividad
            actividad_data: Datos adicionales de contexto
            
        Returns:
            Lista de tareas específicas analizadas profundamente
        """
        prompt_analisis = f"""Eres un experto pedagogo especializado en diseño de actividades educativas para 4º de Primaria.

ACTIVIDAD A ANALIZAR: "{descripcion_actividad}"

Tienes que responder estas preguntas: ¿Qué tareas concretas deben realizar los estudiantes? ¿Cómo se pueden dividir las tareas para que cada estudiante tenga una actividad específica y diferenciada?
En cada fase de la actividad, ¿qué tareas deben realizar los estudiantes? ¿Cómo se pueden adaptar las tareas a diferentes perfiles de estudiantes?

Analiza esta actividad y genera tareas concretas siguiendo EXACTAMENTE este formato:

TAREA 1: [nombre corto]
DESCRIPCIÓN: [qué hacer exactamente - máximo 100 caracteres]
HABILIDADES: [matemáticas/lengua/ciencias/creatividad/colaboración]
COMPLEJIDAD: [1-5]
TIPO: [individual/colaborativa/creativa]

TAREA 2: [nombre corto]
DESCRIPCIÓN: [qué hacer exactamente - máximo 100 caracteres]
HABILIDADES: [matemáticas/lengua/ciencias/creatividad/colaboración]
COMPLEJIDAD: [1-5]
TIPO: [individual/colaborativa/creativa]

TAREA 3: [nombre corto]
DESCRIPCIÓN: [qué hacer exactamente - máximo 100 caracteres]
HABILIDADES: [matemáticas/lengua/ciencias/creatividad/colaboración]
COMPLEJIDAD: [1-5]
TIPO: [individual/colaborativa/creativa]

REGLAS OBLIGATORIAS:
- Descripciones máximo 100 caracteres
- Habilidades solo de la lista: matemáticas, lengua, ciencias, creatividad, colaboración
- Complejidad solo números 1-5
- Tipo solo: individual, colaborativa, creativa
- NO añadir texto extra fuera del formato

ANÁLISIS:"""

        try:
            respuesta = self.ollama.generar_respuesta(prompt_analisis, max_tokens=800)
            
            # DEBUG: Log de la respuesta completa del LLM
            self.logger.info(f"🧠 RESPUESTA LLM ANÁLISIS PROFUNDO:\n{respuesta}")
            
            return self._parsear_tareas_del_analisis_profundo(respuesta, descripcion_actividad)
        except Exception as e:
            self.logger.error(f"Error en análisis profundo: {e}")
            return []
    
    def _parsear_tareas_del_analisis_profundo(self, respuesta: str, descripcion: str) -> List[Tarea]:
        """Parsea tareas del análisis profundo específico - MEJORADO PARA FLEXIBILIDAD"""
        tareas = []
        lineas = respuesta.split('\n')
        tarea_id = 1
        
        # DEBUG: Log de las líneas parseadas
        self.logger.info(f"🔍 DEBUG PARSING - Líneas a procesar: {len(lineas)}")
        
        for i, linea in enumerate(lineas):
            linea_clean = linea.strip()
            if not linea_clean:
                continue
                
            # MÉTODO MEJORADO: Buscar múltiples patrones
            es_tarea = any([
                'TAREA:' in linea.upper(),
                'TAREA ' in linea.upper() and ':' in linea,
                linea_clean.startswith(('1.', '2.', '3.', '4.', '5.')),
                'DESCRIPCIÓN:' in linea.upper() and 'TAREA' in lineas[max(0, i-1)].upper()
            ])
            
            if es_tarea:
                try:
                    self.logger.info(f"🎯 PARSEANDO LÍNEA {i+1}: {linea_clean[:100]}...")
                    
                    # PARSING FLEXIBLE
                    nombre = self._extraer_nombre_tarea(linea_clean)
                    descripcion_tarea = self._extraer_descripcion_tarea(linea_clean, descripcion)
                    habilidades = self._extraer_habilidades(linea_clean)
                    complejidad = self._extraer_complejidad(linea_clean, descripcion)
                    tipo = self._extraer_tipo_tarea(linea_clean)
                    
                    # Log de extracción
                    self.logger.info(f"📝 Tarea extraída: '{descripcion_tarea[:50]}...'")
                    
                    # Estimar tiempo basado en complejidad
                    tiempo_estimado = max(15, complejidad * 12)
                    
                    tarea = Tarea(
                        id=f"tarea_profunda_{tarea_id:02d}",
                        descripcion=descripcion_tarea,
                        competencias_requeridas=habilidades,
                        complejidad=complejidad,
                        tipo=tipo,
                        dependencias=[],
                        tiempo_estimado=tiempo_estimado
                    )
                    
                    tareas.append(tarea)
                    tarea_id += 1
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error parseando línea: {e}")
                    continue
        
        # DEBUG: Resultado del parsing
        self.logger.info(f"🎯 RESULTADO PARSING: {len(tareas)} tareas extraídas")
        
        # Si no se parseó nada, generar tareas básicas específicas
        if not tareas:
            self.logger.warning("🔄 Parsing falló, usando fallback específico")
            tareas = self._generar_tareas_especificas_basicas(descripcion)
        
        return tareas[:6]  # Máximo 6 tareas
    
    def _extraer_nombre_tarea(self, linea: str) -> str:
        """Extrae nombre de tarea de manera flexible"""
        if 'TAREA:' in linea.upper():
            return linea.split(':', 1)[1].split('-')[0].strip()
        elif ':' in linea:
            return linea.split(':', 1)[1].split('-')[0].strip()
        else:
            return "Tarea específica"
    
    def _extraer_descripcion_tarea(self, linea: str, contexto: str) -> str:
        """Extrae descripción específica basada en contexto"""
        # Buscar descripción explícita
        if 'DESCRIPCIÓN:' in linea.upper():
            desc = linea.split('DESCRIPCIÓN:', 1)[1].split('-')[0].strip()
        elif 'DESCRIPCION:' in linea.upper():
            desc = linea.split('DESCRIPCION:', 1)[1].split('-')[0].strip()
        elif ':' in linea:
            # Usar todo después de : como descripción
            desc = linea.split(':', 1)[1].strip()
            if not desc or desc.startswith('['):
                desc = self._generar_descripcion_contextual(contexto)
        else:
            # Fallback inteligente basado en contexto
            desc = self._generar_descripcion_contextual(contexto)
        
        # LIMPIAR FORMATO EXTRAÑO: quitar comillas y asteriscos
        desc = desc.strip('"').strip("'").strip('*').strip()
        
        # NUEVO: Limpiar metadatos del LLM incluidos en la descripción
        desc = self._limpiar_metadatos_llm(desc)
        
        # NUEVO: Limitar longitud máxima
        if len(desc) > 150:
            desc = desc[:147] + "..."
        
        return desc
    
    def _generar_descripcion_contextual(self, descripcion: str) -> str:
        """Genera descripción contextual específica"""
        desc_lower = descripcion.lower()
        
        if 'terrario' in desc_lower:
            return "Construir y monitorear terrario experimental"
        elif 'slime' in desc_lower:
            return "Experimentar con mezclas y propiedades químicas"
        elif 'robot' in desc_lower:
            return "Diseñar y programar robot funcional"
        elif 'matemáticas' in desc_lower or 'fracciones' in desc_lower:
            return "Resolver problemas matemáticos aplicados"
        elif 'célula' in desc_lower:
            return "Explorar estructura y función celular"
        else:
            return f"Desarrollar actividad específica: {descripcion[:30]}..."
    
    def _limpiar_metadatos_llm(self, desc: str) -> str:
        """Limpia metadatos incluidos por el LLM en las descripciones"""
        import re
        
        # Eliminar patrones comunes de metadatos del LLM
        patrones_metadatos = [
            r'\(HABILIDADES:.*?\)',
            r'\(COMPLEJIDAD:.*?\)', 
            r'\(TIPO:.*?\)',
            r'- HABILIDADES:.*?-',
            r'- COMPLEJIDAD:.*?-',
            r'- TIPO:.*?(?=-|$)',
            r'HABILIDADES:.*?(?=COMPLEJIDAD|TIPO|$)',
            r'COMPLEJIDAD:.*?(?=TIPO|$)',
            r'TIPO:.*$'
        ]
        
        for patron in patrones_metadatos:
            desc = re.sub(patron, '', desc, flags=re.IGNORECASE)
        
        # Limpiar espacios múltiples y puntuación residual
        desc = re.sub(r'\s+', ' ', desc)
        desc = desc.strip(' -.,;:')
        
        return desc
    
    def _extraer_habilidades(self, linea: str) -> List[str]:
        """Extrae habilidades con lista normalizada de competencias estándar"""
        # COMPETENCIAS ESTÁNDAR DE 4º PRIMARIA
        COMPETENCIAS_ESTANDAR = {
            'matemáticas': ['calcul', 'número', 'medic', 'proporc', 'fracción', 'suma', 'resta'],
            'lengua': ['lectura', 'escritura', 'gramática', 'comunicación', 'texto', 'palabras', 'oraciones'],
            'ciencias': ['observ', 'experim', 'investig', 'analiz', 'ciencia', 'natural', 'célula'],
            'creatividad': ['diseñ', 'crea', 'innov', 'art', 'imaginación', 'inventar'],
            'colaboración': ['grupo', 'equipo', 'colabor', 'comparti', 'ayudar', 'juntos']
        }
        
        # Extraer habilidades mencionadas explícitamente
        if 'HABILIDADES:' in linea.upper():
            hab_texto = linea.split('HABILIDADES:', 1)[1].split('-')[0].strip()
            habs_extraidas = [h.strip() for h in hab_texto.split(',')]
            # Normalizar contra competencias estándar
            return self._normalizar_competencias(habs_extraidas, COMPETENCIAS_ESTANDAR)
        
        # Inferir habilidades del contenido
        linea_lower = linea.lower()
        habilidades_detectadas = []
        
        for competencia, palabras in COMPETENCIAS_ESTANDAR.items():
            if any(palabra in linea_lower for palabra in palabras):
                habilidades_detectadas.append(competencia)
        
        # Fallback inteligente por contexto
        if not habilidades_detectadas:
            if any(word in linea_lower for word in ['digital', 'google', 'powerpoint', 'interactiv']):
                habilidades_detectadas = ['creatividad']
            elif any(word in linea_lower for word in ['tarjetas', 'palabras', 'oraciones']):
                habilidades_detectadas = ['lengua']
            else:
                habilidades_detectadas = ['colaboración']  # Fallback más específico
        
        return habilidades_detectadas
    
    def _normalizar_competencias(self, competencias_raw: List[str], estandar: Dict) -> List[str]:
        """Normaliza competencias contra lista estándar"""
        competencias_normalizadas = []
        
        for comp_raw in competencias_raw:
            comp_lower = comp_raw.lower().strip()
            
            # Buscar mapeo directo
            if comp_lower in estandar.keys():
                competencias_normalizadas.append(comp_lower)
                continue
            
            # Buscar por similitud de palabras clave
            for comp_estandar, palabras_clave in estandar.items():
                if any(palabra in comp_lower for palabra in palabras_clave):
                    competencias_normalizadas.append(comp_estandar)
                    break
            else:
                # Si no coincide con ninguna, mapear a colaboración por defecto
                competencias_normalizadas.append('colaboración')
        
        return list(set(competencias_normalizadas))  # Eliminar duplicados
    
    def _extraer_complejidad(self, linea: str, contexto: str) -> int:
        """Extrae complejidad de manera flexible"""
        if 'COMPLEJIDAD:' in linea.upper():
            try:
                comp_texto = linea.split('COMPLEJIDAD:', 1)[1].split('-')[0].strip()
                return min(5, max(1, int(comp_texto)))
            except:
                pass
        
        # Inferir complejidad del contenido
        linea_lower = linea.lower()
        contexto_lower = contexto.lower()
        
        palabras_complejas = ['analizar', 'evaluar', 'diseñar', 'planificar', 'coordinar']
        palabras_simples = ['identificar', 'listar', 'copiar', 'observar']
        
        if any(palabra in linea_lower or palabra in contexto_lower for palabra in palabras_complejas):
            return 4
        elif any(palabra in linea_lower or palabra in contexto_lower for palabra in palabras_simples):
            return 2
        else:
            return 3
    
    def _extraer_tipo_tarea(self, linea: str) -> str:
        """Extrae tipo de tarea de manera flexible"""
        if 'TIPO:' in linea.upper():
            tipo = linea.split('TIPO:', 1)[1].strip().lower()
            if 'individual' in tipo:
                return 'individual'
            elif 'creativ' in tipo:
                return 'creativa'
            else:
                return 'colaborativa'
        
        # Inferir tipo del contenido
        linea_lower = linea.lower()
        if any(palabra in linea_lower for palabra in ['individual', 'personal', 'propio']):
            return 'individual'
        elif any(palabra in linea_lower for palabra in ['crear', 'diseñar', 'inventar', 'arte']):
            return 'creativa'
        else:
            return 'colaborativa'
    
    def _generar_tareas_especificas_basicas(self, descripcion: str) -> List[Tarea]:
        """Genera tareas básicas específicas según la descripción"""
        desc_lower = descripcion.lower()
        
        # Tareas específicas según el tipo de actividad
        if 'terrario' in desc_lower:
            return [
                Tarea("prep_terrario", "Preparar recipiente y sistema de drenaje", ["organización", "precisión"], 2, "individual", [], 20),
                Tarea("plant_terrario", "Plantar especies seleccionadas", ["cuidado", "biología"], 3, "colaborativa", ["prep_terrario"], 25),
                Tarea("obs_terrario", "Observar y registrar ciclo del agua", ["observación", "registro"], 4, "individual", ["plant_terrario"], 30)
            ]
        elif 'slime' in desc_lower:
            return [
                Tarea("prep_slime", "Medir ingredientes según proporciones", ["matemáticas", "precisión"], 3, "individual", [], 15),
                Tarea("mezcla_slime", "Mezclar componentes químicos", ["química", "experimentación"], 4, "colaborativa", ["prep_slime"], 20),
                Tarea("test_slime", "Probar propiedades magnéticas", ["investigación", "análisis"], 4, "colaborativa", ["mezcla_slime"], 25)
            ]
        elif 'robot' in desc_lower:
            return [
                Tarea("diseño_robot", "Diseñar estructura del robot", ["creatividad", "ingeniería"], 4, "individual", [], 30),
                Tarea("construir_robot", "Ensamblar robot con materiales", ["construcción", "precisión"], 3, "colaborativa", ["diseño_robot"], 35),
                Tarea("program_robot", "Programar movimientos básicos", ["lógica", "tecnología"], 5, "individual", ["construir_robot"], 25)
            ]
        else:
            # Tareas genéricas mejoradas
            return self._crear_tareas_fallback()
    
    def _tiene_estructura_json_valida(self, actividad: Dict) -> bool:
        """Verifica si la actividad tiene estructura JSON válida"""
        return (
            isinstance(actividad, dict) and 
            'etapas' in actividad and 
            isinstance(actividad['etapas'], list) and
            len(actividad['etapas']) > 0 and
            any(isinstance(etapa, dict) and 'tareas' in etapa for etapa in actividad['etapas'])
        )
    
    def _extraer_tareas_desde_json(self, actividad: Dict, contexto_dinamico: Dict = None) -> List[Tarea]:
        """Extrae tareas directamente desde estructura JSON adaptándose al contexto dinámico del usuario"""
        tareas = []
        contador = 1
        
        # Obtener contexto dinámico de modalidades de trabajo
        modalidades_por_fase = self._extraer_modalidades_contexto(contexto_dinamico)
        self.logger.info(f"🎯 Modalidades detectadas por fase: {modalidades_por_fase}")
        
        for etapa in actividad.get('etapas', []):
            if not isinstance(etapa, dict):
                continue
                
            nombre_etapa = etapa.get('nombre', f'Etapa {contador}')
            modalidad_fase = self._determinar_modalidad_para_etapa(nombre_etapa, modalidades_por_fase)
            
            for tarea_data in etapa.get('tareas', []):
                if not isinstance(tarea_data, dict):
                    continue
                
                # MEJORA: Extraer también asignaciones específicas si existen
                asignaciones_especificas = tarea_data.get('asignaciones_especificas', {})
                
                # Verificar si hay asignaciones individuales
                if 'asignaciones_individuales' in asignaciones_especificas:
                    # Extraer tareas específicas por estudiante ADAPTADAS al contexto
                    tareas_especificas = self._extraer_tareas_especificas_por_estudiante(
                        asignaciones_especificas['asignaciones_individuales'], 
                        nombre_etapa, 
                        contador,
                        modalidad_fase  # NUEVO: Pasar modalidad dinámica
                    )
                    tareas.extend(tareas_especificas)
                    contador += len(tareas_especificas)
                    
                elif 'asignacion_puestos' in asignaciones_especificas:
                    # Extraer tareas específicas por puesto ADAPTADAS al contexto
                    tareas_puestos = self._extraer_tareas_especificas_por_puesto(
                        asignaciones_especificas['asignacion_puestos'], 
                        nombre_etapa, 
                        contador,
                        modalidad_fase  # NUEVO: Pasar modalidad dinámica
                    )
                    tareas.extend(tareas_puestos)
                    contador += len(tareas_puestos)
                    
                else:
                    # Tarea general adaptada al contexto
                    descripcion_completa = f"{tarea_data.get('nombre', '')} {tarea_data.get('descripcion', '')}"
                    
                    tarea = Tarea(
                        id=f"tarea_{contador:02d}",
                        descripcion=tarea_data.get('descripcion', tarea_data.get('nombre', f'Tarea {contador}')),
                        competencias_requeridas=self._extraer_habilidades(descripcion_completa),
                        complejidad=self._extraer_complejidad(descripcion_completa, actividad.get('objetivo', '')),
                        tipo=self._adaptar_tipo_a_modalidad(modalidad_fase),  # NUEVO: Adaptativo
                        dependencias=[],  # Se calculan después si es necesario
                        tiempo_estimado=self._calcular_tiempo_desde_json(tarea_data, actividad)
                    )
                    
                    tareas.append(tarea)
                    contador += 1
                    
                    self.logger.debug(f"📝 Extraída tarea JSON general: {tarea.descripcion[:50]}...")
        
        self.logger.info(f"✅ Total tareas extraídas desde JSON: {len(tareas)}")
        return tareas
    
    def _extraer_tareas_especificas_por_estudiante(self, asignaciones_individuales: List[Dict], nombre_etapa: str, contador_base: int, modalidad_fase: str = 'individual') -> List[Tarea]:
        """Extrae tareas específicas por estudiante desde asignaciones individuales"""
        tareas = []
        contador = contador_base
        
        for asignacion in asignaciones_individuales:
            if not isinstance(asignacion, dict):
                continue
                
            alumno = asignacion.get('alumno', f'Estudiante {contador}')
            comunidades = asignacion.get('comunidades_asignadas', [])
            adaptaciones = asignacion.get('adaptaciones', [])
            tiempo = asignacion.get('tiempo_estimado', '20 minutos')
            
            # Crear descripción específica para este estudiante
            if comunidades:
                descripcion = f"{alumno}: Trabajar con {', '.join(comunidades)}"
            else:
                descripcion = f"{alumno}: {asignacion.get('criterio_asignacion', 'Tarea específica')}"
            
            # Extraer competencias de las adaptaciones y criterio
            criterio_completo = f"{asignacion.get('criterio_asignacion', '')} {' '.join(adaptaciones)}"
            
            # ADAPTATIVO: Ajustar descripción y tipo según modalidad del usuario
            descripcion_adaptada, tipo_adaptado = self._adaptar_tarea_a_modalidad(
                descripcion, alumno, modalidad_fase, asignaciones_individuales, contador
            )
            
            tarea = Tarea(
                id=f"tarea_{contador:02d}_{alumno.replace(' ', '_').replace('.', '').lower()}",
                descripcion=descripcion_adaptada,
                competencias_requeridas=self._extraer_habilidades(criterio_completo),
                complejidad=self._calcular_complejidad_desde_asignacion(asignacion),
                tipo=tipo_adaptado,  # DINÁMICO: Basado en contexto del usuario
                dependencias=[],
                tiempo_estimado=self._parsear_tiempo_estimado(tiempo)
            )
            
            tareas.append(tarea)
            contador += 1
            
            self.logger.debug(f"📝 Extraída tarea específica: {alumno} -> {descripcion[:50]}...")
        
        return tareas
    
    def _extraer_tareas_especificas_por_puesto(self, asignacion_puestos: List[Dict], nombre_etapa: str, contador_base: int, modalidad_fase: str = 'colaborativa') -> List[Tarea]:
        """Extrae tareas específicas por puesto desde asignaciones de puestos"""
        tareas = []
        contador = contador_base
        
        for puesto_data in asignacion_puestos:
            if not isinstance(puesto_data, dict):
                continue
                
            puesto = puesto_data.get('puesto', f'Puesto {contador}')
            pareja = puesto_data.get('pareja', [])
            tareas_especificas = puesto_data.get('tareas_especificas', [])
            
            # Crear una tarea para cada tarea específica del puesto
            for i, tarea_especifica in enumerate(tareas_especificas):
                if isinstance(pareja, list) and len(pareja) >= 2:
                    descripcion = f"Pareja {pareja[0]}-{pareja[1]} en {puesto}: {tarea_especifica}"
                else:
                    descripcion = f"Equipo {puesto}: {tarea_especifica}"
                
                # ADAPTATIVO: Ajustar descripción según modalidad del usuario
                descripcion_adaptada = self._adaptar_descripcion_puesto_a_modalidad(
                    descripcion, puesto, pareja, modalidad_fase
                )
                
                tarea = Tarea(
                    id=f"tarea_{contador:02d}_{puesto.replace(' ', '_').lower()}_{i+1}",
                    descripcion=descripcion_adaptada,
                    competencias_requeridas=self._extraer_habilidades(f"{puesto} {tarea_especifica}"),
                    complejidad=self._calcular_complejidad_desde_puesto(puesto_data),
                    tipo=self._adaptar_tipo_a_modalidad(modalidad_fase),  # DINÁMICO
                    dependencias=[],
                    tiempo_estimado=15  # Tiempo estimado por tarea específica
                )
                
                tareas.append(tarea)
                contador += 1
                
                self.logger.debug(f"📝 Extraída tarea de puesto: {puesto} -> {tarea_especifica[:50]}...")
        
        return tareas
    
    def _calcular_complejidad_desde_asignacion(self, asignacion: Dict) -> int:
        """Calcula complejidad basada en la asignación individual"""
        # Buscar pistas de complejidad en el criterio y adaptaciones
        criterio = asignacion.get('criterio_asignacion', '').lower()
        adaptaciones = ' '.join(asignacion.get('adaptaciones', [])).lower()
        justificacion = asignacion.get('justificacion', '').lower()
        
        texto_completo = f"{criterio} {adaptaciones} {justificacion}"
        
        if any(term in texto_completo for term in ['altas capacidades', 'mayor complejidad', 'superado']):
            return 4
        elif any(term in texto_completo for term in ['tea', 'tdah', 'apoyo', 'estructura']):
            return 2
        elif any(term in texto_completo for term in ['medio', 'sencillo', 'definido']):
            return 3
        else:
            return 3  # Complejidad por defecto
    
    def _calcular_complejidad_desde_puesto(self, puesto_data: Dict) -> int:
        """Calcula complejidad basada en el puesto de trabajo"""
        puesto = puesto_data.get('puesto', '').lower()
        tareas_especificas = puesto_data.get('tareas_especificas', [])
        
        # Determinar complejidad por tipo de puesto
        if 'geometría' in puesto or 'matemática' in puesto:
            return 4
        elif 'organizar' in ' '.join(tareas_especificas).lower():
            return 3
        elif 'decorar' in ' '.join(tareas_especificas).lower():
            return 2
        else:
            return 3
    
    def _parsear_tiempo_estimado(self, tiempo_str: str) -> int:
        """Parsea tiempo estimado desde string a minutos"""
        if not tiempo_str:
            return 20
            
        import re
        # Buscar números en el string
        numeros = re.findall(r'\d+', str(tiempo_str))
        if numeros:
            return int(numeros[0])
        else:
            return 20  # Por defecto
    
    # =================== MÉTODOS ADAPTATIVOS AL CONTEXTO DINÁMICO ===================
    
    def _extraer_contexto_dinamico(self, contexto_hibrido) -> Dict:
        """Extrae contexto dinámico del contexto híbrido"""
        if not contexto_hibrido:
            return {}
        
        # Buscar en metadatos del contexto híbrido
        metadatos = contexto_hibrido.metadatos if hasattr(contexto_hibrido, 'metadatos') else {}
        
        # Buscar estructura_fases en diferentes ubicaciones
        contexto = {}
        
        # Opción 1: Directamente en metadatos
        if 'estructura_fases' in metadatos:
            contexto['estructura_fases'] = metadatos['estructura_fases']
        
        # Opción 2: En input_estructurado
        if 'input_estructurado' in metadatos:
            input_data = metadatos['input_estructurado']
            if isinstance(input_data, dict) and 'estructura_fases' in input_data:
                contexto['estructura_fases'] = input_data['estructura_fases']
        
        # Opción 3: Buscar en todo el contexto híbrido si tiene to_dict
        if hasattr(contexto_hibrido, 'to_dict'):
            datos_completos = contexto_hibrido.to_dict()
            for key, value in datos_completos.items():
                if isinstance(value, dict) and 'estructura_fases' in value:
                    contexto['estructura_fases'] = value['estructura_fases']
                    break
        
        self.logger.debug(f"🔍 Contexto dinámico extraído: {list(contexto.keys())}")
        return contexto
    
    def _extraer_modalidades_contexto(self, contexto_dinamico: Dict) -> Dict[str, str]:
        """Extrae modalidades de trabajo por fase desde el contexto dinámico"""
        modalidades = {}
        
        if not contexto_dinamico:
            return {'default': 'colaborativa'}
        
        # Buscar en estructura_fases.fases_detalladas
        estructura = contexto_dinamico.get('estructura_fases', {})
        fases_detalladas = estructura.get('fases_detalladas', [])
        
        for fase in fases_detalladas:
            nombre = fase.get('nombre', '').lower()
            modalidad = fase.get('modalidad', 'colaborativa')
            modalidades[nombre] = modalidad
            
        # Si no hay fases detalladas, usar modalidad general
        if not modalidades:
            modalidades_generales = contexto_dinamico.get('modalidades', [])
            if modalidades_generales:
                modalidades['default'] = modalidades_generales[0] if modalidades_generales else 'colaborativa'
            else:
                modalidades['default'] = 'colaborativa'
        
        return modalidades
    
    def _determinar_modalidad_para_etapa(self, nombre_etapa: str, modalidades_por_fase: Dict[str, str]) -> str:
        """Determina la modalidad de trabajo para una etapa específica"""
        nombre_lower = nombre_etapa.lower()
        
        # Buscar coincidencia exacta o parcial
        for fase, modalidad in modalidades_por_fase.items():
            if fase in nombre_lower or any(word in nombre_lower for word in fase.split()):
                return modalidad
        
        # Mapeo por palabras clave de la etapa
        if 'preparación' in nombre_lower or 'introducción' in nombre_lower:
            return modalidades_por_fase.get('preparacion', modalidades_por_fase.get('default', 'colaborativa'))
        elif 'ejecución' in nombre_lower or 'principal' in nombre_lower:
            return modalidades_por_fase.get('ejecucion', modalidades_por_fase.get('default', 'colaborativa'))
        elif 'reflexión' in nombre_lower or 'evaluación' in nombre_lower:
            return modalidades_por_fase.get('reflexion', modalidades_por_fase.get('default', 'colaborativa'))
        
        # Fallback a modalidad por defecto
        return modalidades_por_fase.get('default', 'colaborativa')
    
    def _adaptar_tipo_a_modalidad(self, modalidad: str) -> str:
        """Convierte modalidad del usuario a tipo de tarea"""
        modalidad_map = {
            'individual': 'individual',
            'parejas': 'colaborativa',
            'grupos_pequeños': 'colaborativa', 
            'grupos_grandes': 'colaborativa',
            'toda_la_clase': 'colaborativa',
            'colaborativa': 'colaborativa'
        }
        return modalidad_map.get(modalidad, 'colaborativa')
    
    def _adaptar_tarea_a_modalidad(self, descripcion_base: str, alumno: str, modalidad_fase: str, 
                                 todas_asignaciones: List[Dict], contador: int) -> tuple[str, str]:
        """Adapta una tarea individual al contexto de modalidad del usuario"""
        
        if modalidad_fase == 'parejas':
            # Buscar pareja para este alumno
            pareja = self._encontrar_pareja_para_alumno(alumno, todas_asignaciones, contador)
            if pareja:
                descripcion_adaptada = f"Pareja {alumno}-{pareja}: {descripcion_base.replace(f'{alumno}: ', '')}"
                return descripcion_adaptada, 'colaborativa'
            else:
                # Si no hay pareja, mantener individual pero indicar que debería tener pareja
                descripcion_adaptada = f"{alumno} (buscar pareja): {descripcion_base.replace(f'{alumno}: ', '')}"
                return descripcion_adaptada, 'individual'
                
        elif modalidad_fase == 'grupos_pequeños':
            # Crear grupo de 3-4 estudiantes
            grupo = self._crear_grupo_pequeño_para_alumno(alumno, todas_asignaciones, contador)
            descripcion_adaptada = f"Grupo {'-'.join(grupo)}: {descripcion_base.replace(f'{alumno}: ', '')}"
            return descripcion_adaptada, 'colaborativa'
            
        elif modalidad_fase == 'individual':
            # Mantener como está
            return descripcion_base, 'individual'
            
        else:  # toda_la_clase, grupos_grandes, etc.
            descripcion_adaptada = f"Clase completa - {alumno} responsable de: {descripcion_base.replace(f'{alumno}: ', '')}"
            return descripcion_adaptada, 'colaborativa'
    
    def _adaptar_descripcion_puesto_a_modalidad(self, descripcion_base: str, puesto: str, 
                                              pareja: List, modalidad_fase: str) -> str:
        """Adapta descripción de puesto a la modalidad especificada por el usuario"""
        
        # Extraer la tarea específica
        if ': ' in descripcion_base:
            tarea_especifica = descripcion_base.split(': ', 1)[1]
        else:
            tarea_especifica = descripcion_base
        
        if modalidad_fase == 'individual':
            # Convertir a asignación individual
            if isinstance(pareja, list) and len(pareja) > 0:
                return f"{pareja[0]} (individual) en {puesto}: {tarea_especifica}"
            else:
                return f"Estudiante individual en {puesto}: {tarea_especifica}"
                
        elif modalidad_fase == 'parejas':
            # Mantener como pareja
            if isinstance(pareja, list) and len(pareja) >= 2:
                return f"Pareja {pareja[0]}-{pareja[1]} en {puesto}: {tarea_especifica}"
            else:
                return f"Pareja en {puesto}: {tarea_especifica}"
                
        elif modalidad_fase in ['grupos_pequeños', 'grupos_grandes']:
            # Expandir a grupo más grande
            return f"Grupo en {puesto}: {tarea_especifica}"
            
        else:  # toda_la_clase
            return f"Clase completa - puesto {puesto}: {tarea_especifica}"
    
    def _encontrar_pareja_para_alumno(self, alumno: str, asignaciones: List[Dict], contador: int) -> str:
        """Encuentra pareja para un alumno basándose en las asignaciones disponibles"""
        # Buscar el siguiente alumno en la lista para formar pareja
        alumno_index = None
        for i, asignacion in enumerate(asignaciones):
            if asignacion.get('alumno') == alumno:
                alumno_index = i
                break
        
        if alumno_index is not None and alumno_index + 1 < len(asignaciones):
            return asignaciones[alumno_index + 1].get('alumno', f'Compañero_{contador+1}')
        
        return None
    
    def _crear_grupo_pequeño_para_alumno(self, alumno: str, asignaciones: List[Dict], contador: int) -> List[str]:
        """Crea un grupo pequeño (3-4 estudiantes) para un alumno"""
        grupo = [alumno]
        
        # Encontrar índice del alumno actual
        alumno_index = None
        for i, asignacion in enumerate(asignaciones):
            if asignacion.get('alumno') == alumno:
                alumno_index = i
                break
        
        if alumno_index is not None:
            # Añadir 2-3 compañeros más
            for i in range(1, 4):  # Intentar añadir hasta 3 más
                if alumno_index + i < len(asignaciones):
                    siguiente_alumno = asignaciones[alumno_index + i].get('alumno')
                    if siguiente_alumno:
                        grupo.append(siguiente_alumno)
        
        return grupo
    
    def _generar_tareas_con_plantilla(self, actividad: Dict, prompt_usuario: str) -> List[Tarea]:
        """Genera tareas usando plantilla JSON estructurada"""
        
        plantilla = {
            "tareas": [
                {
                    "id": "tarea_01",
                    "descripcion": "",
                    "competencias": [],
                    "complejidad": 3,
                    "tipo": "colaborativa",
                    "tiempo_minutos": 45,
                    "adaptaciones": {}
                }
            ]
        }
        
        titulo = actividad.get('titulo', 'Actividad educativa')
        objetivo = actividad.get('objetivo', prompt_usuario)
        
        prompt = f"""Completa esta plantilla JSON con 3-5 tareas específicas para la actividad educativa.

ACTIVIDAD: {titulo}
OBJETIVO: {objetivo}

PLANTILLA A COMPLETAR:
{json.dumps(plantilla, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
1. Genera entre 3-5 tareas concretas y realizables
2. Cada tarea debe tener descripción específica
3. Competencias: matemáticas, lengua, ciencias, creatividad, social
4. Complejidad: 1-5 (1=fácil, 5=difícil)
5. Tipo: individual, colaborativa, creativa
6. Tiempo en minutos: 15-90

RESPONDE SOLO CON EL JSON COMPLETADO, SIN EXPLICACIONES.
"""
        
        respuesta = self.ollama.generar_respuesta(prompt, max_tokens=600)
        return self._parse_json_tareas(respuesta)
    
    def _generar_tareas_prompt_simple(self, actividad: Dict) -> List[Tarea]:
        """Genera tareas con prompt minimalista"""
        
        titulo = actividad.get('titulo', 'Actividad')
        objetivo = actividad.get('objetivo', 'Realizar actividad educativa')
        
        prompt = f"""Descompón esta actividad en 4 tareas específicas:

ACTIVIDAD: {titulo}
OBJETIVO: {objetivo}

Formato obligatorio (usa EXACTAMENTE este formato):
TAREA 1: [descripción concreta de máximo 100 caracteres]
TAREA 2: [descripción concreta de máximo 100 caracteres]
TAREA 3: [descripción concreta de máximo 100 caracteres]
TAREA 4: [descripción concreta de máximo 100 caracteres]

Solo tareas concretas y realizables. Sin explicaciones adicionales."""
        
        respuesta = self.ollama.generar_respuesta(prompt, max_tokens=300)
        return self._parsear_tareas_simple(respuesta)
    
    def _inferir_competencias_desde_json(self, tarea_data: Dict, actividad: Dict) -> List[str]:
        """Infiere competencias desde datos JSON"""
        competencias = []
        
        # Analizar descripción de tarea y actividad
        texto = f"{tarea_data.get('descripcion', '')} {actividad.get('titulo', '')} {actividad.get('objetivo', '')}".lower()
        
        mapeo = {
            'matemáticas': ['número', 'suma', 'resta', 'fracción', 'cálculo', 'matemática'],
            'lengua': ['lectura', 'escritura', 'texto', 'comunicación', 'presentar'],
            'ciencias': ['experimento', 'observar', 'investigar', 'célula', 'ciencia'],
            'creatividad': ['crear', 'diseñar', 'arte', 'dibujar', 'inventar'],
            'social': ['grupo', 'equipo', 'colaborar', 'compartir', 'ayudar']
        }
        
        for competencia, palabras in mapeo.items():
            if any(palabra in texto for palabra in palabras):
                competencias.append(competencia)
        
        return competencias if competencias else ['transversales']
    
    def _inferir_complejidad_desde_json(self, tarea_data: Dict) -> int:
        """Infiere complejidad desde datos JSON"""
        descripcion = tarea_data.get('descripcion', '').lower()
        
        palabras_complejas = ['analizar', 'evaluar', 'crear', 'diseñar', 'investigar', 'planificar']
        palabras_simples = ['listar', 'copiar', 'leer', 'observar', 'identificar']
        
        for palabra in palabras_complejas:
            if palabra in descripcion:
                return 4
        
        for palabra in palabras_simples:
            if palabra in descripcion:
                return 2
                
        return 3  # Complejidad media por defecto
    
    def _normalizar_tipo_desde_json(self, formato: str) -> str:
        """Normaliza tipo de tarea desde JSON"""
        formato_lower = formato.lower()
        
        if 'grupo' in formato_lower or 'colabor' in formato_lower:
            return 'colaborativa'
        elif 'individual' in formato_lower:
            return 'individual'
        else:
            return 'colaborativa'  # Por defecto
    
    def _calcular_tiempo_desde_json(self, tarea_data: Dict, actividad: Dict) -> int:
        """Calcula tiempo estimado desde datos JSON"""
        # Intentar extraer duración de la actividad
        duracion = actividad.get('duracion_minutos', '')
        
        if isinstance(duracion, str) and 'sesion' in duracion.lower():
            return 45  # Una sesión estándar
        elif isinstance(duracion, str) and any(num in duracion for num in ['2', '3']):
            return 30  # División entre múltiples sesiones
        
        # Por defecto basado en complejidad usando método existente
        descripcion_completa = f"{tarea_data.get('nombre', '')} {tarea_data.get('descripcion', '')}"
        complejidad = self._extraer_complejidad(descripcion_completa, actividad.get('objetivo', ''))
        return min(60, max(15, complejidad * 12))  # 15-60 minutos
    
    def _parse_json_tareas(self, respuesta: str) -> List[Tarea]:
        """Parsea respuesta JSON del LLM"""
        try:
            # Limpiar respuesta
            respuesta_limpia = respuesta.strip()
            if respuesta_limpia.startswith('```json'):
                respuesta_limpia = respuesta_limpia[7:-3]
            elif respuesta_limpia.startswith('```'):
                respuesta_limpia = respuesta_limpia[3:-3]
            
            # Parsear JSON
            import json
            datos = json.loads(respuesta_limpia)
            
            tareas = []
            for i, tarea_data in enumerate(datos.get('tareas', [])):
                tarea = Tarea(
                    id=tarea_data.get('id', f'tarea_{i+1:02d}'),
                    descripcion=tarea_data.get('descripcion', f'Tarea {i+1}'),
                    competencias_requeridas=tarea_data.get('competencias', ['transversales']),
                    complejidad=tarea_data.get('complejidad', 3),
                    tipo=tarea_data.get('tipo', 'colaborativa'),
                    dependencias=[],
                    tiempo_estimado=tarea_data.get('tiempo_minutos', 45)
                )
                tareas.append(tarea)
            
            return tareas
            
        except Exception as e:
            self.logger.error(f"❌ Error parseando JSON: {e}")
            return []
    
    def _parsear_tareas_simple(self, respuesta: str) -> List[Tarea]:
        """Parsea respuesta de prompt simple"""
        tareas = []
        lineas = respuesta.split('\n')
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if linea.startswith('TAREA') and ':' in linea:
                descripcion = linea.split(':', 1)[1].strip()
                if descripcion:
                    tarea = Tarea(
                        id=f'tarea_{i+1:02d}',
                        descripcion=descripcion,
                        competencias_requeridas=['transversales'],
                        complejidad=3,
                        tipo='colaborativa',
                        dependencias=[],
                        tiempo_estimado=45
                    )
                    tareas.append(tarea)
        
        return tareas
    
    def seleccionar_y_adaptar_actividad(self, prompt: str) -> Dict[str, Any]:
        """
        Selecciona la actividad más adecuada usando embeddings y la adapta mínimamente
        
        Args:
            prompt: Prompt del usuario describiendo la actividad deseada
            
        Returns:
            Diccionario con la actividad seleccionada y adaptaciones
        """
        self._log_processing_start(f"Seleccionando actividad para: '{prompt[:50]}...'")
        
        try:
            # 1. NUEVO: Detectar tipo de actividad solicitada
            tipo_detectado = self._detectar_tipo_actividad(prompt)
            self.logger.info(f"🔍 Tipo detectado: {tipo_detectado['tipo']} (confianza: {tipo_detectado['confianza']:.2f})")
            
            # 2. Buscar actividades similares usando embeddings
            actividades_candidatas = self.embeddings_manager.encontrar_actividad_similar(prompt, top_k=3)
            
            if not actividades_candidatas:
                self.logger.warning("❌ No se encontraron actividades candidatas, usando fallback")
                return self._crear_actividad_fallback(prompt)
            
            # 2. Analizar similitud de la mejor candidata
            mejor_actividad_id, mejor_similitud, mejor_actividad_data = actividades_candidatas[0]
            
            self.logger.info(f"🎯 Mejor match: {mejor_actividad_id} (similitud: {mejor_similitud:.3f})")
            
            # 3. Decidir estrategia basada en similitud
            if mejor_similitud > 0.7:
                # Alta similitud: usar actividad completa con adaptaciones mínimas
                resultado = self._adaptar_actividad_existente(mejor_actividad_data, prompt)
                resultado['estrategia'] = 'adaptacion_minima'
                resultado['similitud'] = mejor_similitud
                
            elif mejor_similitud > 0.4:
                # Similitud media: usar como inspiración y adaptar más
                resultado = self._inspirar_en_actividad(mejor_actividad_data, prompt, actividades_candidatas)
                resultado['estrategia'] = 'inspiracion_adaptada'
                resultado['similitud'] = mejor_similitud
                
            else:
                # Similitud baja: crear nueva usando estructura base
                resultado = self._crear_actividad_nueva(prompt, mejor_actividad_data)
                resultado['estrategia'] = 'creacion_nueva'
                resultado['similitud'] = mejor_similitud
            
            resultado['actividad_fuente'] = mejor_actividad_id
            
            # 4. NUEVO: Extraer elementos reutilizables de actividades candidatas
            actividades_para_extraccion = [data for _, _, data in actividades_candidatas]
            elementos_reutilizables = self._extraer_elementos_reutilizables(actividades_para_extraccion)
            
            # 5. Enriquecer resultado con información detectada
            resultado['tipo_detectado'] = tipo_detectado
            resultado['elementos_reutilizables'] = elementos_reutilizables
            resultado['actividades_analizadas'] = len(actividades_candidatas)
            
            self.logger.info(f"🔧 Elementos extraídos: {sum(len(v) for v in elementos_reutilizables.values())} total")
            self._log_processing_end(f"Actividad seleccionada: {resultado['estrategia']}")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Error en selección de actividad: {e}")
            return self._crear_actividad_fallback(prompt)
    
    def _adaptar_actividad_existente(self, actividad_data: dict, prompt: str) -> Dict[str, Any]:
        """
        Adapta mínimamente una actividad existente de alta similitud
        
        Args:
            actividad_data: Datos de la actividad base
            prompt: Prompt original del usuario
            
        Returns:
            Actividad con adaptaciones mínimas
        """
        # Copiar actividad base
        actividad_adaptada = actividad_data.copy()
        
        # Lista de adaptaciones menores aplicadas
        adaptaciones = []
        
        # Adaptar título si el prompt menciona contexto específico
        titulo_original = actividad_data.get('titulo', '')
        if 'fracciones' in prompt.lower() and 'fracciones' not in titulo_original.lower():
            actividad_adaptada['titulo'] = titulo_original + ' - Enfoque en Fracciones'
            adaptaciones.append('titulo_especializado')
        
        # Adaptar duración si se especifica
        if 'sesión' in prompt.lower() or 'clase' in prompt.lower():
            actividad_adaptada['duracion_minutos'] = '50 minutos (1 sesión)'
            adaptaciones.append('duracion_ajustada')
        
        return {
            'actividad': actividad_adaptada,
            'adaptaciones_aplicadas': adaptaciones,
            'tipo_adaptacion': 'minima',
            'actividad_original_preservada': True
        }
    
    def _inspirar_en_actividad(self, actividad_data: dict, prompt: str, candidatas: list) -> Dict[str, Any]:
        """
        Usa una actividad como inspiración y adapta significativamente
        
        Args:
            actividad_data: Actividad base de inspiración
            prompt: Prompt original
            candidatas: Lista de actividades candidatas
            
        Returns:
            Actividad inspirada con adaptaciones significativas
        """
        # Generar nueva actividad usando LLM con la estructura base
        prompt_adaptacion = f"""
Basándote en esta actividad exitosa como INSPIRACIÓN (NO copia exacta):

ACTIVIDAD BASE: {actividad_data.get('titulo', '')}
OBJETIVO BASE: {actividad_data.get('objetivo', '')}
ESTRUCTURA BASE: {len(actividad_data.get('etapas', []))} etapas

NUEVA SOLICITUD DEL USUARIO: {prompt}

Crea una actividad NUEVA que:
1. Use la ESTRUCTURA pedagógica de la actividad base
2. Adapte el CONTENIDO completamente al nuevo tema solicitado  
3. Mantenga el FORMATO JSON de etapas y tareas
4. Incluya adaptaciones DUA específicas

Responde SOLO con la actividad adaptada, NO explicaciones adicionales.
"""
        
        respuesta = self.ollama.generar_respuesta(prompt_adaptacion, max_tokens=600)
        
        try:
            # Intentar parsear respuesta como JSON o texto estructurado
            actividad_inspirada = self._parsear_actividad_adaptada(respuesta, actividad_data)
        except Exception as e:
            self.logger.warning(f"⚠️ Error parseando actividad inspirada: {e}")
            actividad_inspirada = actividad_data.copy()  # Fallback a original
        
        return {
            'actividad': actividad_inspirada,
            'adaptaciones_aplicadas': ['estructura_mantenida', 'contenido_adaptado'],
            'tipo_adaptacion': 'inspiracion',
            'actividad_original_preservada': False
        }
    
    def _crear_actividad_nueva(self, prompt: str, referencia_data: dict) -> Dict[str, Any]:
        """
        Crea una actividad completamente nueva usando estructura de referencia
        
        Args:
            prompt: Prompt del usuario
            referencia_data: Actividad de referencia para estructura
            
        Returns:
            Actividad nueva creada
        """
        # Usar el método existente de descomposición como base
        proyecto_base = {
            'titulo': 'Actividad Personalizada',
            'descripcion': prompt,
            'nivel': '4º Primaria',
            'duracion_base': '2-3 sesiones',
            'info_adicional': 'Basada en solicitud específica del usuario'
        }
        
        tareas = self.descomponer_actividad(proyecto_base)
        
        # Convertir tareas a estructura de actividad JSON
        actividad_nueva = {
            'id': 'ACT_NUEVA',
            'titulo': f'Actividad: {prompt[:50]}...',
            'objetivo': f'Desarrollar competencias mediante: {prompt}',
            'nivel_educativo': '4º Primaria',
            'duracion_minutos': '2-3 sesiones',
            'etapas': self._convertir_tareas_a_etapas(tareas),
            'recursos': ['Materiales básicos del aula', 'Recursos específicos según necesidades'],
            'observaciones': 'Actividad creada automáticamente. Revisar adaptaciones específicas.'
        }
        
        return {
            'actividad': actividad_nueva,
            'adaptaciones_aplicadas': ['creacion_completa'],
            'tipo_adaptacion': 'nueva',
            'actividad_original_preservada': False
        }
    
    def _convertir_tareas_a_etapas(self, tareas: List[Tarea]) -> List[dict]:
        """
        Convierte lista de Tareas a estructura de etapas JSON
        
        Args:
            tareas: Lista de objetos Tarea
            
        Returns:
            Lista de etapas en formato JSON
        """
        etapas = []
        etapa_actual = None
        tareas_etapa = []
        
        for tarea in tareas:
            # Agrupar tareas en etapas según dependencias
            if not tarea.dependencias or etapa_actual is None:
                # Nueva etapa
                if etapa_actual is not None:
                    etapas.append({
                        'nombre': etapa_actual,
                        'descripcion': f'Etapa {len(etapas) + 1} de la actividad',
                        'tareas': tareas_etapa
                    })
                
                etapa_actual = f'Etapa {len(etapas) + 1}'
                tareas_etapa = []
            
            # Añadir tarea a la etapa actual
            tareas_etapa.append({
                'nombre': tarea.id,
                'descripcion': tarea.descripcion,
                'formato_asignacion': 'grupos' if tarea.tipo == 'colaborativa' else 'individual'
            })
        
        # Añadir última etapa
        if etapa_actual and tareas_etapa:
            etapas.append({
                'nombre': etapa_actual,
                'descripcion': f'Etapa {len(etapas) + 1} de la actividad',
                'tareas': tareas_etapa
            })
        
        return etapas
    
    def _parsear_actividad_adaptada(self, respuesta: str, base_data: dict) -> dict:
        """
        Parsea respuesta del LLM para actividad adaptada
        
        Args:
            respuesta: Respuesta cruda del LLM
            base_data: Datos base como fallback
            
        Returns:
            Diccionario con actividad parseada
        """
        try:
            import json
            # Intentar parsear como JSON directo
            if respuesta.strip().startswith('{'):
                return json.loads(respuesta)
        except:
            pass
        
        # Fallback: extraer campos clave y usar estructura base
        actividad = base_data.copy()
        
        # Extraer título
        titulo_match = re.search(r'título[:\s]*([^\n]+)', respuesta, re.IGNORECASE)
        if titulo_match:
            actividad['titulo'] = titulo_match.group(1).strip()
        
        # Extraer objetivo
        objetivo_match = re.search(r'objetivo[:\s]*([^\n]+)', respuesta, re.IGNORECASE)
        if objetivo_match:
            actividad['objetivo'] = objetivo_match.group(1).strip()
        
        return actividad
    
    def _crear_actividad_fallback(self, prompt: str) -> Dict[str, Any]:
        """
        Crea actividad fallback cuando todo falla
        
        Args:
            prompt: Prompt original
            
        Returns:
            Actividad fallback básica
        """
        actividad_fallback = {
            'id': 'ACT_FALLBACK',
            'titulo': f'Actividad Personalizada: {prompt[:30]}...',
            'objetivo': 'Desarrollar competencias mediante trabajo colaborativo',
            'nivel_educativo': '4º Primaria',
            'duracion_minutos': '2 sesiones',
            'etapas': [
                {
                    'nombre': 'Preparación',
                    'descripcion': 'Introducción y organización de la actividad',
                    'tareas': [{'nombre': 'Contextualización', 'descripcion': 'Presentar la actividad al alumnado'}]
                },
                {
                    'nombre': 'Desarrollo',
                    'descripcion': 'Desarrollo principal de la actividad',
                    'tareas': [{'nombre': 'Trabajo colaborativo', 'descripcion': 'Realizar la actividad en grupos'}]
                },
                {
                    'nombre': 'Cierre',
                    'descripcion': 'Presentación y reflexión final',
                    'tareas': [{'nombre': 'Presentación', 'descripcion': 'Presentar resultados y reflexionar'}]
                }
            ],
            'recursos': ['Materiales básicos del aula'],
            'observaciones': 'Actividad generada automáticamente como fallback'
        }
        
        return {
            'actividad': actividad_fallback,
            'adaptaciones_aplicadas': ['fallback_generado'],
            'tipo_adaptacion': 'fallback',
            'actividad_original_preservada': False,
            'similitud': 0.0
        }
    
    
    def process(self, proyecto_base: Dict) -> List[Tarea]:
        """
        Implementa el método abstracto process de BaseAgent
        
        Args:
            proyecto_base: Diccionario con información del proyecto
            
        Returns:
            Lista de objetos Tarea
        """
        return self.extraer_tareas_hibrido(proyecto_base, proyecto_base.get('descripcion', ''))
    
    def _parse_response(self, response: str) -> List[Dict]:
        """
        Implementa el método abstracto requerido por BaseAgent
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Lista de diccionarios con tareas parseadas
        """
        # Para compatibilidad con BaseAgent, convertimos List[Tarea] a List[Dict]
        tareas_objeto = self._parsear_tareas_simple(response)
        
        # Convertir objetos Tarea a diccionarios
        tareas_dict = []
        for tarea in tareas_objeto:
            tarea_dict = {
                'id': tarea.id,
                'descripcion': tarea.descripcion,
                'competencias_requeridas': tarea.competencias_requeridas,
                'complejidad': tarea.complejidad,
                'tipo': tarea.tipo,
                'dependencias': tarea.dependencias,
                'tiempo_estimado': tarea.tiempo_estimado
            }
            tareas_dict.append(tarea_dict)
        
        return tareas_dict
    
    def _crear_tareas_fallback(self) -> List[Tarea]:
        """
        Crea tareas genéricas como fallback
        
        Returns:
            Lista de objetos Tarea
        """
        return [
            Tarea(
                id="tarea_01",
                descripcion="Preparación y contextualización de la actividad",
                competencias_requeridas=["organizativas"],
                complejidad=2,
                tipo="individual",
                dependencias=[],
                tiempo_estimado=30
            ),
            Tarea(
                id="tarea_02",
                descripcion="Desarrollo principal de la actividad",
                competencias_requeridas=["específicas del proyecto"],
                complejidad=3,
                tipo="colaborativa", 
                dependencias=["tarea_01"],
                tiempo_estimado=60
            ),
            Tarea(
                id="tarea_03",
                descripcion="Reflexión y cierre de la actividad",
                competencias_requeridas=["metacognitivas"],
                complejidad=2,
                tipo="individual",
                dependencias=["tarea_02"],
                tiempo_estimado=20
            )
        ]
    
    # =================== MÉTODOS DE DEBATE ENTRE AGENTES ===================
    
    def generar_propuesta_debate(self, tema: str, contexto: Dict) -> Dict:
        """
        Genera propuesta inicial para debates entre agentes
        
        Args:
            tema: Tema del debate (tipo_actividad, combinacion_elementos, etc.)
            contexto: Contexto de la decisión crítica
            
        Returns:
            Propuesta estructurada para el debate
        """
        self.logger.info(f"🎯 Analizador generando propuesta para debate: {tema}")
        
        if tema == "tipo_actividad":
            return self._propuesta_tipo_actividad(contexto)
        elif tema == "combinacion_elementos":
            return self._propuesta_combinacion_elementos(contexto)
        else:
            return self._propuesta_generica(contexto)
    
    def _propuesta_tipo_actividad(self, contexto: Dict) -> Dict:
        """Propuesta específica para determinar tipo de actividad"""
        prompt_usuario = contexto.get('prompt_usuario', '')
        
        # Usar detector existente
        tipo_detectado = self._detectar_tipo_actividad(prompt_usuario)
        
        # Buscar actividades similares
        actividades_candidatas = self.embeddings_manager.encontrar_actividad_similar(prompt_usuario, top_k=3)
        
        # Convertir formato de actividades candidatas (Tuple[str, float, dict] -> dict)
        candidatas_formateadas = []
        for actividad_id, similitud, actividad_data in actividades_candidatas:
            candidatas_formateadas.append({
                'id': actividad_id,
                'titulo': actividad_data.get('titulo', 'Sin título'),
                'similitud': similitud
            })
        
        propuesta = {
            'tipo_propuesto': tipo_detectado['tipo'],
            'confianza': tipo_detectado['confianza'],
            'justificacion': f"Detectado '{tipo_detectado['tipo']}' por palabras clave: {tipo_detectado['palabras_clave']}",
            'actividades_candidatas': candidatas_formateadas,
            'estructura_sugerida': self._sugerir_estructura_por_tipo(tipo_detectado['tipo'])
        }
        
        return propuesta
    
    def _propuesta_combinacion_elementos(self, contexto: Dict) -> Dict:
        """Propuesta para combinar elementos de múltiples actividades"""
        actividades_seleccionadas = contexto.get('actividades_seleccionadas', [])
        prompt_usuario = contexto.get('prompt_usuario', '')
        
        # Extraer elementos reutilizables de cada actividad
        elementos_combinables = self._extraer_elementos_reutilizables(actividades_seleccionadas)
        
        propuesta = {
            'elementos_propuestos': elementos_combinables,
            'estrategia_combinacion': 'hibridacion_inteligente',
            'justificacion': f"Combinando {len(actividades_seleccionadas)} actividades para personalizar según prompt",
            'estructura_hibrida': self._diseñar_estructura_hibrida(elementos_combinables, prompt_usuario)
        }
        
        return propuesta
    
    def _propuesta_generica(self, contexto: Dict) -> Dict:
        """Propuesta genérica para otros tipos de debate"""
        return {
            'propuesta': 'análisis_requerido',
            'justificacion': 'Requiere análisis específico del contexto proporcionado',
            'recomendacion': 'Solicitar información adicional para propuesta específica'
        }
    
    def _sugerir_estructura_por_tipo(self, tipo: str) -> Dict:
        """Sugiere estructura básica según el tipo de actividad detectado"""
        estructuras = {
            'gymnkana': {
                'fases': ['preparacion', 'rotacion_puestos', 'evaluacion'],
                'organizacion': 'parejas_rotativas',
                'duracion_sugerida': '60-90 minutos'
            },
            'proyecto': {
                'fases': ['planificacion', 'desarrollo', 'presentacion'],
                'organizacion': 'grupos_pequenos',
                'duracion_sugerida': '2-3 sesiones'
            },
            'taller': {
                'fases': ['introduccion', 'experimentacion', 'reflexion'],
                'organizacion': 'individual_con_apoyo',
                'duracion_sugerida': '45-60 minutos'
            }
        }
        
        return estructuras.get(tipo, estructuras['taller'])  # taller como fallback
    
    def _diseñar_estructura_hibrida(self, elementos: Dict, prompt: str) -> Dict:
        """Diseña estructura híbrida combinando elementos de múltiples actividades"""
        return {
            'tipo_hibrido': 'actividad_personalizada',
            'elementos_clave': list(elementos.keys()),
            'adaptacion_prompt': f"Personalizada para: {prompt[:50]}...",
            'complejidad_resultante': 'media-alta'
        }