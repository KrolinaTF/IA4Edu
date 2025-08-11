"""
EmbeddingsManager - Gestor de embeddings para selección inteligente de actividades.
Utiliza las actividades JSON existentes como plantillas expertas.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("SistemaAgentesABP.EmbeddingsManager")

class EmbeddingsManager:
    """Gestor de embeddings para selección inteligente de actividades JSON"""
    
    def __init__(self, actividades_json_path: str, ollama_integrator):
        """
        Inicializa el gestor de embeddings
        
        Args:
            actividades_json_path: Ruta al directorio con actividades JSON
            ollama_integrator: Instancia del integrador Ollama
        """
        self.actividades_path = actividades_json_path
        self.ollama = ollama_integrator
        self.actividades = {}
        self.embeddings_cache = {}
        self.textos_enriquecidos = {}
        
        # Cargar actividades y generar embeddings
        self._cargar_actividades_json()
        self._generar_embeddings_actividades()
        
        logger.info(f"✅ EmbeddingsManager inicializado con {len(self.actividades)} actividades")
    
    def _cargar_actividades_json(self) -> None:
        """Carga todas las actividades JSON del directorio especificado"""
        try:
            if not os.path.exists(self.actividades_path):
                logger.error(f"❌ Directorio de actividades no encontrado: {self.actividades_path}")
                return
            
            archivos_json = [f for f in os.listdir(self.actividades_path) if f.endswith('.json')]
            
            for archivo in archivos_json:
                ruta_completa = os.path.join(self.actividades_path, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        actividad_data = json.load(f)
                        actividad_id = os.path.splitext(archivo)[0]  # nombre sin extensión
                        self.actividades[actividad_id] = actividad_data
                        logger.info(f"📚 Cargada actividad: {actividad_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error cargando {archivo}: {e}")
                    continue
            
            logger.info(f"✅ Cargadas {len(self.actividades)} actividades JSON")
            
        except Exception as e:
            logger.error(f"❌ Error en carga de actividades: {e}")
    
    def _generar_texto_enriquecido(self, actividad_id: str, actividad_data: dict) -> str:
        """
        Genera texto enriquecido para embedding combinando JSON + TXT si existe
        
        Args:
            actividad_id: ID de la actividad
            actividad_data: Datos JSON de la actividad
            
        Returns:
            Texto enriquecido para generar embedding
        """
        texto_base = []
        
        # Información básica del JSON
        texto_base.append(f"TÍTULO: {actividad_data.get('titulo', '')}")
        texto_base.append(f"OBJETIVO: {actividad_data.get('objetivo', '')}")
        texto_base.append(f"NIVEL: {actividad_data.get('nivel_educativo', '')}")
        texto_base.append(f"DURACIÓN: {actividad_data.get('duracion_minutos', '')}")
        
        # Recursos como contexto temático
        recursos = actividad_data.get('recursos', [])
        if recursos:
            texto_base.append(f"RECURSOS: {', '.join(recursos[:5])}")  # Primeros 5 recursos
        
        # Etapas y tareas como contenido pedagógico
        etapas = actividad_data.get('etapas', [])
        for etapa in etapas[:3]:  # Primeras 3 etapas
            texto_base.append(f"ETAPA: {etapa.get('nombre', '')}")
            tareas = etapa.get('tareas', [])
            for tarea in tareas[:2]:  # Primeras 2 tareas por etapa
                texto_base.append(f"TAREA: {tarea.get('descripcion', '')}")
        
        # Adaptaciones como contexto inclusivo
        observaciones = actividad_data.get('observaciones', '')
        if observaciones:
            texto_base.append(f"ADAPTACIONES: {observaciones[:200]}")  # Primeros 200 chars
        
        # Buscar archivo TXT complementario (ruta específica para tu estructura)
        # Convertir k_celula.json -> k_celula.txt
        base_name = actividad_id.replace('k_', '')
        txt_path = os.path.join(
            os.path.dirname(self.actividades_path), 
            f"k_{base_name}.txt"
        )
        
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    contenido_txt = f.read()[:500]  # Primeros 500 caracteres
                    texto_base.append(f"CONTEXTO PEDAGÓGICO: {contenido_txt}")
                    logger.debug(f"📖 Añadido contexto TXT para {actividad_id}")
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo TXT para {actividad_id}: {e}")
        
        texto_final = "\n".join(texto_base)
        self.textos_enriquecidos[actividad_id] = texto_final
        
        return texto_final
    
    def _generar_embeddings_actividades(self) -> None:
        """Genera embeddings para todas las actividades cargadas"""
        logger.info("🔄 Generando embeddings para actividades...")
        
        for actividad_id, actividad_data in self.actividades.items():
            try:
                # Generar texto enriquecido
                texto_enriquecido = self._generar_texto_enriquecido(actividad_id, actividad_data)
                
                # Generar embedding usando Ollama
                embedding = self.ollama.generar_embedding(texto_enriquecido)
                
                if embedding and len(embedding) > 0:
                    self.embeddings_cache[actividad_id] = np.array(embedding)
                    logger.debug(f"🔹 Embedding generado para {actividad_id} ({len(embedding)} dims)")
                else:
                    logger.warning(f"⚠️ Embedding vacío para {actividad_id}, usando fallback")
                    # Fallback: embedding aleatorio normalizado
                    self.embeddings_cache[actividad_id] = np.random.normal(0, 1, 384) / np.linalg.norm(np.random.normal(0, 1, 384))
                    
            except Exception as e:
                logger.error(f"❌ Error generando embedding para {actividad_id}: {e}")
                # Fallback para casos de error
                self.embeddings_cache[actividad_id] = np.random.normal(0, 1, 384) / np.linalg.norm(np.random.normal(0, 1, 384))
        
        logger.info(f"✅ Embeddings generados: {len(self.embeddings_cache)} actividades")
    
    def encontrar_actividad_similar(self, prompt: str, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """
        Encuentra las actividades más similares al prompt usando embeddings mejorados
        
        Args:
            prompt: Prompt del usuario
            top_k: Número de actividades a retornar
            
        Returns:
            Lista de tuplas (actividad_id, similitud, datos_actividad)
        """
        if not self.embeddings_cache:
            logger.error("❌ No hay embeddings disponibles")
            return []
        
        try:
            # Enriquecer el prompt del usuario para mejor matching
            prompt_enriquecido = self._enriquecer_prompt_usuario(prompt)
            
            # Generar embedding del prompt enriquecido
            prompt_embedding = self.ollama.generar_embedding(prompt_enriquecido)
            
            if not prompt_embedding or len(prompt_embedding) == 0:
                logger.warning("⚠️ No se pudo generar embedding del prompt, usando selección por palabras clave")
                return self._seleccion_por_palabras_clave(prompt, top_k)
            
            prompt_embedding = np.array(prompt_embedding)
            similitudes = []
            
            # Calcular similitudes coseno con ponderación inteligente
            for actividad_id, embedding in self.embeddings_cache.items():
                try:
                    similitud_base = self._similitud_coseno(prompt_embedding, embedding)
                    
                    # Aplicar boost semántico basado en características del prompt
                    similitud_ponderada = self._aplicar_boost_semantico(
                        similitud_base, prompt, self.actividades[actividad_id]
                    )
                    
                    similitudes.append((actividad_id, similitud_ponderada, self.actividades[actividad_id]))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error calculando similitud para {actividad_id}: {e}")
                    similitudes.append((actividad_id, 0.0, self.actividades[actividad_id]))
            
            # Ordenar por similitud descendente y filtrar por umbral mínimo
            similitudes_filtradas = [s for s in similitudes if s[1] > 0.2]  # Umbral mínimo
            similitudes_ordenadas = sorted(similitudes_filtradas, key=lambda x: x[1], reverse=True)[:top_k]
            
            # Si no hay suficientes resultados, usar fallback híbrido
            if len(similitudes_ordenadas) < top_k:
                similitudes_adicionales = self._seleccion_por_palabras_clave(prompt, top_k - len(similitudes_ordenadas))
                similitudes_ordenadas.extend(similitudes_adicionales)
            
            # Log de resultados mejorado
            logger.info(f"🎯 Actividades seleccionadas para '{prompt[:50]}...':")
            for i, (act_id, sim, act_data) in enumerate(similitudes_ordenadas[:top_k]):
                logger.info(f"   {i+1}. {act_id} - {act_data.get('titulo', 'Sin título')} (similitud: {sim:.3f})")
            
            return similitudes_ordenadas[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de similitud: {e}")
            return self._seleccion_por_palabras_clave(prompt, top_k)
    
    def _enriquecer_prompt_usuario(self, prompt: str) -> str:
        """
        Enriquece el prompt del usuario con contexto adicional para mejor matching
        
        Args:
            prompt: Prompt original del usuario
            
        Returns:
            Prompt enriquecido
        """
        prompt_lower = prompt.lower()
        enriquecimientos = []
        
        # Detectar materia y añadir contexto
        if any(term in prompt_lower for term in ['matemáticas', 'matemática', 'números', 'fracciones', 'sumas']):
            enriquecimientos.append('competencias matemáticas cálculo operaciones')
            
        if any(term in prompt_lower for term in ['ciencias', 'naturales', 'experimentos', 'células']):
            enriquecimientos.append('ciencias naturales investigación método científico')
            
        if any(term in prompt_lower for term in ['lengua', 'lectura', 'escritura', 'textos']):
            enriquecimientos.append('lengua castellana comunicación textual')
            
        if any(term in prompt_lower for term in ['geografía', 'españa', 'comunidades', 'mapas']):
            enriquecimientos.append('geografía territorio español localización')
        
        # Detectar modalidades de trabajo
        if any(term in prompt_lower for term in ['colaborativo', 'grupos', 'equipo', 'conjunto']):
            enriquecimientos.append('trabajo colaborativo grupos cooperativo')
            
        if any(term in prompt_lower for term in ['individual', 'personal', 'autónomo']):
            enriquecimientos.append('trabajo individual autónomo personal')
            
        if any(term in prompt_lower for term in ['creativo', 'arte', 'diseño', 'mural']):
            enriquecimientos.append('creatividad artística diseño visual')
        
        # Detectar contextos específicos
        if any(term in prompt_lower for term in ['supermercado', 'tienda', 'compras', 'dinero']):
            enriquecimientos.append('supermercado comercio dinero transacciones')
            
        if any(term in prompt_lower for term in ['piratas', 'tesoro', 'aventura']):
            enriquecimientos.append('piratas aventura tesoro narrativa')
        
        # Combinar prompt original con enriquecimientos
        prompt_final = prompt
        if enriquecimientos:
            prompt_final += f" {' '.join(enriquecimientos)}"
            
        return prompt_final
    
    def _aplicar_boost_semantico(self, similitud_base: float, prompt: str, actividad_data: dict) -> float:
        """
        Aplica boost semántico basado en características específicas
        
        Args:
            similitud_base: Similitud coseno base
            prompt: Prompt del usuario
            actividad_data: Datos de la actividad
            
        Returns:
            Similitud con boost aplicado
        """
        boost_total = 0.0
        prompt_lower = prompt.lower()
        
        # Boost por coincidencia directa de términos clave
        titulo = actividad_data.get('titulo', '').lower()
        objetivo = actividad_data.get('objetivo', '').lower()
        
        # Términos específicos con boost alto
        terminos_especificos = {
            'fracciones': 0.15,
            'células': 0.15, 
            'supermercado': 0.15,
            'piratas': 0.15,
            'mural': 0.10,
            'tienda': 0.10
        }
        
        for termino, boost in terminos_especificos.items():
            if termino in prompt_lower and termino in (titulo + objetivo):
                boost_total += boost
                logger.debug(f"🚀 Boost {boost:.2f} aplicado por término '{termino}'")
        
        # Boost por nivel educativo
        if '4º' in prompt_lower or 'cuarto' in prompt_lower:
            nivel = actividad_data.get('nivel_educativo', '').lower()
            if 'primaria' in nivel:
                boost_total += 0.05
        
        # Boost por modalidad de trabajo
        if 'colaborat' in prompt_lower or 'grupo' in prompt_lower:
            etapas = actividad_data.get('etapas', [])
            for etapa in etapas[:3]:  # Revisar primeras 3 etapas
                tareas = etapa.get('tareas', [])
                for tarea in tareas[:2]:  # Revisar primeras 2 tareas
                    if 'grupos' in tarea.get('formato_asignacion', ''):
                        boost_total += 0.05
                        break
        
        # Aplicar boost con límite máximo
        similitud_final = min(1.0, similitud_base + boost_total)
        
        if boost_total > 0:
            logger.debug(f"🎯 Boost total {boost_total:.3f} aplicado: {similitud_base:.3f} → {similitud_final:.3f}")
        
        return similitud_final
    
    def _seleccion_por_palabras_clave(self, prompt: str, top_k: int) -> List[Tuple[str, float, dict]]:
        """
        Selección fallback basada en palabras clave cuando embeddings fallan
        
        Args:
            prompt: Prompt del usuario
            top_k: Número de actividades a retornar
            
        Returns:
            Lista de actividades seleccionadas por palabras clave
        """
        logger.info("🔍 Usando selección por palabras clave como fallback")
        
        prompt_lower = prompt.lower()
        puntuaciones = []
        
        # Sistema de puntuación por palabras clave
        for actividad_id, actividad_data in self.actividades.items():
            puntuacion = 0.0
            
            # Texto completo de la actividad para búsqueda
            texto_actividad = (
                f"{actividad_data.get('titulo', '')} "
                f"{actividad_data.get('objetivo', '')} "
                f"{' '.join([etapa.get('nombre', '') for etapa in actividad_data.get('etapas', [])])}"
            ).lower()
            
            # Mapeo de términos con pesos
            terminos_clave = {
                'matemáticas': ['matemática', 'números', 'fracciones', 'sumas', 'cálculo'],
                'ciencias': ['ciencias', 'naturales', 'células', 'experimento', 'investigación'],
                'supermercado': ['supermercado', 'tienda', 'compras', 'dinero', 'comercio'],
                'geografía': ['geografía', 'españa', 'comunidades', 'mapas', 'territorio'],
                'piratas': ['piratas', 'tesoro', 'aventura', 'narrativa'],
                'colaborativo': ['colaborativo', 'grupos', 'equipo', 'conjunto', 'cooperativo']
            }
            
            # Calcular puntuación
            for categoria, terminos in terminos_clave.items():
                for termino in terminos:
                    if termino in prompt_lower and termino in texto_actividad:
                        puntuacion += 0.3 if termino == categoria else 0.1
            
            if puntuacion > 0:
                puntuaciones.append((actividad_id, puntuacion, actividad_data))
        
        # Ordenar por puntuación y normalizar a escala [0,1]
        puntuaciones_ordenadas = sorted(puntuaciones, key=lambda x: x[1], reverse=True)[:top_k]
        
        # Normalizar puntuaciones
        if puntuaciones_ordenadas:
            max_puntuacion = puntuaciones_ordenadas[0][1]
            if max_puntuacion > 0:
                puntuaciones_normalizadas = [
                    (act_id, min(0.8, punt / max_puntuacion * 0.8), act_data)  # Máximo 0.8 para fallback
                    for act_id, punt, act_data in puntuaciones_ordenadas
                ]
            else:
                puntuaciones_normalizadas = puntuaciones_ordenadas
        else:
            # Fallback final: actividades aleatorias
            actividades_aleatorias = list(self.actividades.items())[:top_k]
            puntuaciones_normalizadas = [(act_id, 0.3, act_data) for act_id, act_data in actividades_aleatorias]
        
        logger.info(f"🔍 Selección por palabras clave completada: {len(puntuaciones_normalizadas)} actividades")
        return puntuaciones_normalizadas
    
    def _similitud_coseno(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcula similitud coseno entre dos vectores
        
        Args:
            vec1: Vector 1
            vec2: Vector 2
            
        Returns:
            Similitud coseno (0-1)
        """
        try:
            # Asegurar que ambos vectores tienen la misma dimensión
            if len(vec1) != len(vec2):
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]
            
            # Calcular normas
            norma1 = np.linalg.norm(vec1)
            norma2 = np.linalg.norm(vec2)
            
            # Evitar división por cero
            if norma1 == 0 or norma2 == 0:
                return 0.0
            
            # Calcular similitud coseno
            similitud = np.dot(vec1, vec2) / (norma1 * norma2)
            
            # Convertir de [-1, 1] a [0, 1]
            similitud_normalizada = (similitud + 1) / 2
            
            return float(similitud_normalizada)
            
        except Exception as e:
            logger.error(f"❌ Error en cálculo de similitud coseno: {e}")
            return 0.0
    
    def get_actividad_por_id(self, actividad_id: str) -> Optional[dict]:
        """
        Obtiene una actividad específica por su ID
        
        Args:
            actividad_id: ID de la actividad
            
        Returns:
            Datos de la actividad o None si no se encuentra
        """
        return self.actividades.get(actividad_id)
    
    def get_estadisticas(self) -> dict:
        """
        Obtiene estadísticas del gestor de embeddings
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'actividades_cargadas': len(self.actividades),
            'embeddings_generados': len(self.embeddings_cache),
            'textos_enriquecidos': len(self.textos_enriquecidos),
            'actividades_disponibles': list(self.actividades.keys())
        }
    
    def get_texto_enriquecido(self, actividad_id: str) -> str:
        """
        Obtiene el texto enriquecido de una actividad específica
        
        Args:
            actividad_id: ID de la actividad
            
        Returns:
            Texto enriquecido o cadena vacía
        """
        return self.textos_enriquecidos.get(actividad_id, "")