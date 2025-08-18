"""
EmbeddingsManager - Gestor de embeddings para selección inteligente de actividades.
Utiliza las actividades JSON existentes como plantillas expertas.
"""

import os
import json
import logging
import numpy as np
import hashlib
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("SistemaAgentesABP.EmbeddingsManager")

class EmbeddingsManager:
    """Gestor de embeddings para selección inteligente de actividades JSON y TXT"""
    
    def __init__(self, actividades_base_path: str, ollama_integrator):
        """
        Inicializa el gestor de embeddings con cache persistente
        
        Args:
            actividades_base_path: Ruta base al directorio de actividades (buscará JSON y TXT)
            ollama_integrator: Instancia del integrador Ollama
        """
        self.actividades_base_path = actividades_base_path
        self.ollama = ollama_integrator
        self.actividades = {}
        self.embeddings_cache = {}
        self.textos_enriquecidos = {}
        self.cache_file = os.path.join(actividades_base_path, "embeddings_cache.json")
        self.cache_persistente = True  # Activar cache persistente por defecto
        
        # Cargar actividades JSON y TXT
        self._cargar_actividades_json_y_txt()
        
        # Cargar embeddings desde cache o generar nuevos
        self._cargar_o_generar_embeddings()
        
        logger.info(f"✅ EmbeddingsManager inicializado con {len(self.actividades)} actividades")
    
    def _cargar_actividades_json_y_txt(self) -> None:
        """Carga actividades JSON y TXT del directorio base"""
        try:
            # Buscar archivos JSON en subdirectorio json_actividades
            json_path = os.path.join(self.actividades_base_path, "json_actividades")
            if os.path.exists(json_path):
                self._cargar_actividades_json_desde_directorio(json_path)
            
            # Buscar archivos TXT en el directorio base
            self._cargar_actividades_txt_desde_directorio(self.actividades_base_path)
            
            logger.info(f"✅ Cargadas {len(self.actividades)} actividades (JSON + TXT)")
            
        except Exception as e:
            logger.error(f"❌ Error en carga de actividades: {e}")
    
    def _cargar_actividades_json_desde_directorio(self, directorio: str) -> None:
        """Carga actividades JSON de un directorio específico"""
        try:
            archivos_json = [f for f in os.listdir(directorio) if f.endswith('.json')]
            
            for archivo in archivos_json:
                ruta_completa = os.path.join(directorio, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        actividad_data = json.load(f)
                        actividad_id = os.path.splitext(archivo)[0]  # nombre sin extensión
                        actividad_data['_tipo_fuente'] = 'json'
                        actividad_data['_archivo_origen'] = archivo
                        self.actividades[actividad_id] = actividad_data
                        logger.info(f"📚 Cargada actividad JSON: {actividad_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error cargando JSON {archivo}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error listando directorio JSON {directorio}: {e}")
    
    def _cargar_actividades_txt_desde_directorio(self, directorio: str) -> None:
        """Carga actividades TXT de un directorio específico"""
        try:
            archivos_txt = [f for f in os.listdir(directorio) if f.startswith('k_') and f.endswith('.txt')]
            
            for archivo in archivos_txt:
                ruta_completa = os.path.join(directorio, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido_txt = f.read()
                        actividad_id = os.path.splitext(archivo)[0]  # nombre sin extensión
                        
                        # Solo cargar TXT si no existe ya una versión JSON del mismo
                        if actividad_id not in self.actividades:
                            # Crear estructura básica para TXT
                            actividad_data = self._parsear_actividad_txt(contenido_txt, actividad_id, archivo)
                            actividad_data['_tipo_fuente'] = 'txt'
                            actividad_data['_archivo_origen'] = archivo
                            self.actividades[actividad_id] = actividad_data
                            logger.info(f"📝 Cargada actividad TXT: {actividad_id}")
                        else:
                            # Agregar contenido TXT como enriquecimiento a la versión JSON
                            self.actividades[actividad_id]['_contenido_txt_complementario'] = contenido_txt
                            logger.info(f"🔗 Enriquecida actividad JSON con TXT: {actividad_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error cargando TXT {archivo}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error listando directorio TXT {directorio}: {e}")
    
    def _parsear_actividad_txt(self, contenido: str, actividad_id: str, archivo: str) -> dict:
        """Parsea contenido TXT para crear estructura básica de actividad"""
        lineas = contenido.split('\n')
        
        # Extraer título
        titulo = ""
        for linea in lineas[:10]:  # Buscar en las primeras 10 líneas
            if "título" in linea.lower() or "Título" in linea:
                titulo = linea.split(':', 1)[-1].strip(' "').strip()
                break
        
        if not titulo:
            titulo = f"Actividad {actividad_id.replace('k_', '').replace('_', ' ').title()}"
        
        # Extraer objetivo
        objetivo = ""
        for linea in lineas:
            if "objetivo" in linea.lower():
                objetivo = linea.split(':', 1)[-1].strip(' "').strip()
                break
        
        if not objetivo:
            objetivo = f"Actividad educativa basada en {actividad_id.replace('k_', '').replace('_', ' ')}"
        
        return {
            'id': actividad_id.upper(),
            'titulo': titulo,
            'objetivo': objetivo,
            'nivel_educativo': 'Primaria',
            'duracion_minutos': 'Variable',
            'contenido_completo': contenido,
            'etapas': [],
            'recursos': [],
            'observaciones': f'Actividad cargada desde archivo TXT: {archivo}'
        }
    
    def _generar_texto_enriquecido(self, actividad_id: str, actividad_data: dict) -> str:
        """
        Genera texto enriquecido para embedding combinando JSON + TXT si existe
        
        Args:
            actividad_id: ID de la actividad
            actividad_data: Datos de la actividad
            
        Returns:
            Texto enriquecido para generar embedding
        """
        texto_base = []
        
        # Información básica
        texto_base.append(f"TÍTULO: {actividad_data.get('titulo', '')}")
        texto_base.append(f"OBJETIVO: {actividad_data.get('objetivo', '')}")
        texto_base.append(f"NIVEL: {actividad_data.get('nivel_educativo', '')}")
        texto_base.append(f"DURACIÓN: {actividad_data.get('duracion_minutos', '')}")
        
        # Si es actividad TXT pura, usar contenido completo
        if actividad_data.get('_tipo_fuente') == 'txt':
            contenido_completo = actividad_data.get('contenido_completo', '')
            if contenido_completo:
                # Usar primeros 1000 caracteres del TXT completo
                texto_base.append(f"CONTENIDO COMPLETO: {contenido_completo[:1000]}")
        else:
            # Para actividades JSON, procesar estructura normal
            recursos = actividad_data.get('recursos', [])
            if recursos:
                texto_base.append(f"RECURSOS: {', '.join(recursos[:5])}")
            
            # Etapas y tareas
            etapas = actividad_data.get('etapas', [])
            for etapa in etapas[:3]:
                texto_base.append(f"ETAPA: {etapa.get('nombre', '')}")
                tareas = etapa.get('tareas', [])
                for tarea in tareas[:2]:
                    texto_base.append(f"TAREA: {tarea.get('descripcion', '')}")
            
            # Adaptaciones
            observaciones = actividad_data.get('observaciones', '')
            if observaciones:
                texto_base.append(f"ADAPTACIONES: {observaciones[:200]}")
        
        # Si hay contenido TXT complementario, añadirlo
        contenido_txt_complementario = actividad_data.get('_contenido_txt_complementario', '')
        if contenido_txt_complementario:
            texto_base.append(f"CONTEXTO PEDAGÓGICO EXTENDIDO: {contenido_txt_complementario[:500]}")
            logger.debug(f"📖 Añadido contexto TXT complementario para {actividad_id}")
        
        texto_final = "\n".join(texto_base)
        self.textos_enriquecidos[actividad_id] = texto_final
        
        return texto_final
    
    def _calcular_hash_archivo(self, archivo_path: str) -> str:
        """Calcula hash MD5 de un archivo para detectar cambios"""
        try:
            with open(archivo_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Error calculando hash de {archivo_path}: {e}")
            return ""
    
    def _cargar_cache_embeddings(self) -> Dict:
        """Carga cache de embeddings desde archivo JSON"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    logger.info(f"📥 Cache de embeddings cargado: {len(cache_data.get('embeddings', {}))} entradas")
                    return cache_data
        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache de embeddings: {e}")
        
        return {"embeddings": {}, "metadata": {}}
    
    def _guardar_cache_embeddings(self, cache_data: Dict) -> None:
        """Guarda cache de embeddings a archivo JSON"""
        try:
            # Convertir numpy arrays a listas para JSON
            cache_serializable = {
                "embeddings": {},
                "metadata": cache_data.get("metadata", {})
            }
            
            for actividad_id, embedding in cache_data.get("embeddings", {}).items():
                if isinstance(embedding, np.ndarray):
                    cache_serializable["embeddings"][actividad_id] = embedding.tolist()
                else:
                    cache_serializable["embeddings"][actividad_id] = embedding
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_serializable, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Cache de embeddings guardado: {len(cache_serializable['embeddings'])} entradas")
            
        except Exception as e:
            logger.error(f"❌ Error guardando cache de embeddings: {e}")
    
    def _cargar_o_generar_embeddings(self) -> None:
        """
        Carga embeddings existentes o genera nuevos con cache optimizado
        
        """
        try:
            cache_data = self._cargar_cache_embeddings()
            embeddings_cache = cache_data.get("embeddings", {})
            metadata_cache = cache_data.get("metadata", {})
            
            embeddings_reutilizados = 0
            embeddings_generados = 0
            embeddings_actualizados = {}
            metadata_actualizada = {}
            
            for actividad_id, actividad_data in self.actividades.items():
                try:
                    #Construir según el tipo de fuente
                    archivo_origen = actividad_data.get('_archivo_origen', '')
                    
                    if archivo_origen:
                        tipo_fuente = actividad_data.get('_tipo_fuente', 'unknown')
                        
                        if tipo_fuente == 'json':
                            # Los archivos JSON están en subdirectorio json_actividades
                            archivo_path = os.path.join(self.actividades_base_path, "json_actividades", archivo_origen)
                        else:
                            # Los archivos TXT están en directorio base
                            archivo_path = os.path.join(self.actividades_base_path, archivo_origen)
                        
                        hash_actual = self._calcular_hash_archivo(archivo_path)
                    else:
                        hash_actual = ""
                    
                    # Verificar si necesitamos regenerar
                    metadata_previa = metadata_cache.get(actividad_id, {})
                    hash_previo = metadata_previa.get('hash', '')
                    
                    if hash_actual == hash_previo and actividad_id in embeddings_cache:
                        # Reutilizar embedding existente
                        embedding_lista = embeddings_cache[actividad_id]
                        self.embeddings_cache[actividad_id] = np.array(embedding_lista)
                        embeddings_actualizados[actividad_id] = embedding_lista
                        metadata_actualizada[actividad_id] = metadata_previa
                        embeddings_reutilizados += 1
                        logger.debug(f"♻️ Embedding reutilizado para {actividad_id}")
                        
                    else:
                        # Generar nuevo embedding
                        texto_enriquecido = self._generar_texto_enriquecido(actividad_id, actividad_data)
                        embedding = self.ollama.generar_embedding(texto_enriquecido)
                        
                        if embedding and len(embedding) > 0:
                            self.embeddings_cache[actividad_id] = np.array(embedding)
                            embeddings_actualizados[actividad_id] = embedding
                            metadata_actualizada[actividad_id] = {
                                'hash': hash_actual,
                                'archivo': archivo_origen,
                                'tipo': actividad_data.get('_tipo_fuente', 'unknown')
                            }
                            embeddings_generados += 1
                            logger.debug(f"🔹 Embedding generado para {actividad_id} ({len(embedding)} dims)")
                        else:
                            logger.warning(f"⚠️ Embedding vacío para {actividad_id}, usando fallback")
                            embedding_fallback = np.random.normal(0, 1, 384)
                            embedding_fallback = embedding_fallback / np.linalg.norm(embedding_fallback)
                            self.embeddings_cache[actividad_id] = embedding_fallback
                            embeddings_actualizados[actividad_id] = embedding_fallback.tolist()
                            metadata_actualizada[actividad_id] = {
                                'hash': hash_actual,
                                'archivo': archivo_origen,
                                'tipo': 'fallback'
                            }
                            embeddings_generados += 1
                            
                except Exception as e:
                    logger.error(f"❌ Error procesando embedding para {actividad_id}: {e}")
                    # Fallback
                    embedding_fallback = np.random.normal(0, 1, 384)
                    embedding_fallback = embedding_fallback / np.linalg.norm(embedding_fallback)
                    self.embeddings_cache[actividad_id] = embedding_fallback
                    embeddings_actualizados[actividad_id] = embedding_fallback.tolist()
                    metadata_actualizada[actividad_id] = {'hash': '', 'archivo': archivo_origen, 'tipo': 'error'}
            
            # Guardar cache actualizado
            cache_actualizado = {
                "embeddings": embeddings_actualizados,
                "metadata": metadata_actualizada
            }
            self._guardar_cache_embeddings(cache_actualizado)
            
            logger.info(f"✅ Embeddings: {embeddings_reutilizados} reutilizados, {embeddings_generados} generados")
            
        except Exception as e:
            logger.error(f"❌ Error en carga/generación de embeddings: {e}")
    
    
    def crear_embedding_cached(self, texto: str) -> np.ndarray:
        """
        Crea embedding con cache persistente
        
        """
        # Calcular hash del texto SOLO para cache
        hash_texto = hashlib.md5(texto.encode('utf-8')).hexdigest()
        
        # Buscar en cache de memoria primero (por hash)
        if hash_texto in self.embeddings_cache:
            logger.debug(f"📊 Cache hit (memoria) para texto (hash: {hash_texto[:8]})")
            return self.embeddings_cache[hash_texto]
        
        # Buscar en cache persistente (por hash)
        cache_data = self._cargar_cache_embeddings()
        if hash_texto in cache_data.get("embeddings", {}):
            logger.debug(f"📊 Cache hit (persistente) para texto (hash: {hash_texto[:8]})")
            embedding_lista = cache_data["embeddings"][hash_texto]
            embedding_array = np.array(embedding_lista)
            # Cargar en cache de memoria para próxima vez
            self.embeddings_cache[hash_texto] = embedding_array
            return embedding_array
        
        # Generar nuevo embedding DEL TEXTO REAL
        logger.debug(f"🔄 Generando nuevo embedding para texto (hash: {hash_texto[:8]})")
        embedding = self.ollama.generar_embedding(texto)  # ← TEXTO REAL, no hash
        
        if embedding and len(embedding) > 0:
            embedding_array = np.array(embedding)
            # Guardar en cache de memoria (por hash)
            self.embeddings_cache[hash_texto] = embedding_array
            
            # Guardar en cache persistente si está habilitado
            if self.cache_persistente:
                self._actualizar_cache_persistente(hash_texto, embedding)
            
            return embedding_array
        else:
            # Fallback
            logger.warning(f"⚠️ Embedding vacío, usando fallback")
            embedding_fallback = np.random.normal(0, 1, 384)
            embedding_fallback = embedding_fallback / np.linalg.norm(embedding_fallback)
            self.embeddings_cache[hash_texto] = embedding_fallback
            return embedding_fallback
    
    def _actualizar_cache_persistente(self, hash_texto: str, embedding: List[float]) -> None:
        """
        Actualiza el cache persistente con un nuevo embedding
        
        Args:
            hash_texto: Hash del texto
            embedding: Embedding generado
        """
        try:
            # Cargar cache actual
            cache_data = self._cargar_cache_embeddings()
            
            # Añadir nuevo embedding
            cache_data["embeddings"][hash_texto] = embedding
            cache_data["metadata"][hash_texto] = {
                'timestamp': str(hash(hash_texto))[:8],
                'tipo': 'texto_usuario'
            }
            
            # Guardar cache actualizado
            self._guardar_cache_embeddings(cache_data)
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando cache persistente: {e}")
    
    def encontrar_actividad_similar(self, prompt: str, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """
        Encuentra las actividades más similares al prompt usando embeddings mejorados
        """
        if not self.embeddings_cache:
            logger.error("❌ No hay embeddings disponibles")
            return []

        try:
            # Enriquecer el prompt del usuario para mejor matching
            prompt_enriquecido = self._enriquecer_prompt_usuario(prompt)
            
            # Generar embedding del prompt enriquecido usando cache
            prompt_embedding = self.crear_embedding_cached(prompt_enriquecido)
            
            if prompt_embedding is None or len(prompt_embedding) == 0:
                logger.warning("⚠️ No se pudo generar embedding del prompt, usando selección por palabras clave")
                return self._seleccion_por_palabras_clave(prompt, top_k)
            
            # prompt_embedding ya es np.array desde crear_embedding_cached
            similitudes = []
            
            # CAMBIO CRÍTICO: Iterar solo sobre actividades conocidas, no sobre todo el cache
            for actividad_id, actividad_data in self.actividades.items():
                try:
                    # Verificar que existe embedding para esta actividad
                    if actividad_id in self.embeddings_cache:
                        embedding = self.embeddings_cache[actividad_id]
                        
                        # Calcular similitud
                        similitud_base = self._similitud_coseno(prompt_embedding, embedding)
                        
                        # Aplicar boost semántico basado en características del prompt
                        similitud_ponderada = self._aplicar_boost_semantico(
                            similitud_base, prompt, actividad_data
                        )
                        
                        similitudes.append((actividad_id, similitud_ponderada, actividad_data))
                    else:
                        logger.debug(f"⚠️ No hay embedding para actividad {actividad_id}")
                        similitudes.append((actividad_id, 0.0, actividad_data))
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error calculando similitud para {actividad_id}: {e}")
                    similitudes.append((actividad_id, 0.0, actividad_data))
            
            # Ordenar por similitud descendente y filtrar por umbral mínimo
            similitudes_filtradas = [s for s in similitudes if s[1] > 0.2]  # Umbral mínimo
            similitudes_ordenadas = sorted(similitudes_filtradas, key=lambda x: x[1], reverse=True)[:top_k]
            
            # Si no hay suficientes resultados, usar fallback híbrido
            if len(similitudes_ordenadas) < top_k:
                similitudes_adicionales = self._seleccion_por_palabras_clave(prompt, top_k - len(similitudes_ordenadas))
                similitudes_ordenadas.extend(similitudes_adicionales)
            
            # Log de resultados mejorado
            if similitudes_ordenadas:
                logger.info(f"🎯 Actividades seleccionadas para '{prompt[:50]}...':")
                for i, (act_id, sim, act_data) in enumerate(similitudes_ordenadas[:top_k]):
                    logger.info(f"   {i+1}. {act_id} - {act_data.get('titulo', 'Sin título')} (similitud: {sim:.3f})")
            else:
                logger.warning("⚠️ No se encontraron actividades similares")
            
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
    
    def limpiar_cache(self) -> bool:
        """
        Elimina el archivo de cache para forzar regeneración completa
        
        Returns:
            True si se eliminó correctamente
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("🗑️ Cache de embeddings eliminado")
                return True
            else:
                logger.info("ℹ️ No hay cache para eliminar")
                return True
        except Exception as e:
            logger.error(f"❌ Error eliminando cache: {e}")
            return False