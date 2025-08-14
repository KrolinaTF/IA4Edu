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
            # Ruta base a las actividades (JSON + TXT)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            actividades_base_path = os.path.join(base_dir, "..", "data", "actividades")
            
            self.embeddings_manager = EmbeddingsManager(actividades_base_path, ollama_integrator)
        else:
            self.embeddings_manager = embeddings_manager
    
    def extraer_tareas_hibrido(self, actividad_data: Dict, prompt_original: str = "") -> List[Tarea]:
        """
        NUEVA FUNCIÓN HÍBRIDA: Extrae tareas usando la mejor estrategia disponible
        MEJORADO CON MVP: Análisis profundo específico de cada actividad
        
        Args:
            actividad_data: Datos de la actividad (JSON o dict)
            prompt_original: Prompt original del usuario (opcional)
            
        Returns:
            Lista de objetos Tarea garantizada
        """
        self._log_processing_start(f"Extracción híbrida de tareas mejorada")
        
        # ESTRATEGIA 1: ANÁLISIS PROFUNDO CON LLM (NUEVA - DEL MVP)
        if prompt_original:
            self.logger.info("🧠 Estrategia 1: Análisis profundo específico (MVP)")
            tareas = self._analizar_actividad_profundo(prompt_original, actividad_data)
            if tareas:
                self._log_processing_end(f"✅ Análisis profundo: {len(tareas)} tareas específicas")
                
                # Si tenemos actividad personalizada, usarla como información base
                if actividad_data.get('tipo') == 'actividad_personalizada':
                    self.logger.info("📋 Usando actividad personalizada del prompt")
                    return tareas
                else:
                    return tareas
        
        # ESTRATEGIA 2: Extraer directamente desde JSON (PRIORIDAD ALTA)
        if self._tiene_estructura_json_valida(actividad_data):
            self.logger.info("🎯 Estrategia 2: Extracción directa desde JSON")
            tareas = self._extraer_tareas_desde_json(actividad_data)
            if tareas:
                self._log_processing_end(f"✅ Extraídas {len(tareas)} tareas desde JSON")
                return tareas
        
        # ESTRATEGIA 3: Usar plantilla estructurada con LLM
        self.logger.info("🎯 Estrategia 3: Plantilla estructurada con LLM")
        tareas = self._generar_tareas_con_plantilla(actividad_data, prompt_original)
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
        NUEVO: Análisis profundo específico de cada actividad (del MVP)
        
        Args:
            descripcion_actividad: Descripción específica de la actividad
            actividad_data: Datos adicionales de contexto
            
        Returns:
            Lista de tareas específicas analizadas profundamente
        """
        prompt_analisis = f"""Eres un experto pedagogo especializado en diseño de actividades educativas para 4º de Primaria.

ACTIVIDAD A ANALIZAR: "{descripcion_actividad}"

Analiza esta actividad específica en profundidad y genera tareas concretas:

1. OBJETIVO ESPECÍFICO: ¿Qué aprenderán exactamente los estudiantes?

2. TAREAS ESPECÍFICAS: ¿Qué tareas concretas hay que hacer?
   Formato: TAREA: [nombre] - DESCRIPCIÓN: [qué hacer exactamente] - HABILIDADES: [habilidades requeridas] - COMPLEJIDAD: [1-5] - TIPO: [individual/colaborativa/creativa]

3. MATERIALES ESPECÍFICOS: Lista de materiales concretos necesarios

Sé MUY ESPECÍFICO para esta actividad, no uses generalidades.

ANÁLISIS:"""

        try:
            respuesta = self.ollama.generar_respuesta(prompt_analisis, max_tokens=600)
            
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
    
    def _extraer_habilidades(self, linea: str) -> List[str]:
        """Extrae habilidades de manera flexible"""
        if 'HABILIDADES:' in linea.upper():
            hab_texto = linea.split('HABILIDADES:', 1)[1].split('-')[0].strip()
            return [h.strip() for h in hab_texto.split(',')]
        
        # Inferir habilidades del contenido
        linea_lower = linea.lower()
        habilidades = []
        
        mapeo_habilidades = {
            'matemáticas': ['calcul', 'número', 'medic', 'proporc'],
            'ciencias': ['observ', 'experim', 'investig', 'analiz'],
            'creatividad': ['diseñ', 'crea', 'innov', 'art'],
            'colaboración': ['grupo', 'equipo', 'colabor', 'comparti'],
            'comunicación': ['present', 'explic', 'comunicar']
        }
        
        for habilidad, palabras in mapeo_habilidades.items():
            if any(palabra in linea_lower for palabra in palabras):
                habilidades.append(habilidad)
        
        return habilidades if habilidades else ['transversales']
    
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
    
    def _extraer_tareas_desde_json(self, actividad: Dict) -> List[Tarea]:
        """Extrae tareas directamente desde estructura JSON"""
        tareas = []
        contador = 1
        
        for etapa in actividad.get('etapas', []):
            if not isinstance(etapa, dict):
                continue
                
            nombre_etapa = etapa.get('nombre', f'Etapa {contador}')
            
            for tarea_data in etapa.get('tareas', []):
                if not isinstance(tarea_data, dict):
                    continue
                
                tarea = Tarea(
                    id=f"tarea_{contador:02d}",
                    descripcion=tarea_data.get('descripcion', tarea_data.get('nombre', f'Tarea {contador}')),
                    competencias_requeridas=self._inferir_competencias_desde_json(tarea_data, actividad),
                    complejidad=self._inferir_complejidad_desde_json(tarea_data),
                    tipo=self._normalizar_tipo_desde_json(tarea_data.get('formato_asignacion', 'colaborativa')),
                    dependencias=[],  # Se calculan después si es necesario
                    tiempo_estimado=self._calcular_tiempo_desde_json(tarea_data, actividad)
                )
                
                tareas.append(tarea)
                contador += 1
                
                self.logger.debug(f"📝 Extraída tarea JSON: {tarea.descripcion[:50]}...")
        
        return tareas
    
    def _generar_tareas_con_plantilla(self, actividad: Dict, prompt_original: str) -> List[Tarea]:
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
        objetivo = actividad.get('objetivo', prompt_original)
        
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
        
        # Por defecto basado en complejidad
        complejidad = self._inferir_complejidad_desde_json(tarea_data)
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
            # 1. Buscar actividades similares usando embeddings
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