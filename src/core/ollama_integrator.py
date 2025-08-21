"""
Integrador simplificado con APIs de LLM (Ollama local y Groq).
"""

import logging
import requests
import os
from typing import Dict, Any, Optional

# Importar configuración centralizada
from config import OLLAMA_CONFIG

logger = logging.getLogger("SistemaAgentesABP.OllamaIntegrator")

class OllamaIntegrator:
    """Integrador unificado para APIs de LLM (Ollama local y Groq)"""
    
    def __init__(self, host: str = None, port: int = None, model: str = None, 
                 embedding_model: str = None, timeout: int = None):
        """
        Inicializa el integrador con configuración flexible
        
        Args:
            host: Host donde se ejecuta Ollama (usa config si no se especifica)
            port: Puerto de Ollama (usa config si no se especifica)  
            model: Modelo principal para generación de texto (usa config si no se especifica)
            embedding_model: Modelo específico para embeddings (usa config si no se especifica)
            timeout: Timeout para requests (usa config si no se especifica)
        """
        # Inicializar variables de estado
        self.llm_disponible = False
        self.ollama_disponible = False
        
        # Configuración del provider
        self.provider = OLLAMA_CONFIG.get("provider", "ollama")
        
        # Configuración para Groq
        if self.provider == "groq":
            self.groq_api_key = OLLAMA_CONFIG.get("groq_api_key")
            self.groq_model = OLLAMA_CONFIG.get("groq_model", "mixtral-8x7b-32768")
            self.groq_base_url = OLLAMA_CONFIG.get("groq_base_url", "https://api.groq.com/openai/v1")
            
            if not self.groq_api_key:
                logger.error("❌ GROQ_API_KEY no encontrada en variables de entorno")
                self.llm_disponible = False
        
        # Configuración para Ollama (siempre para embeddings)
        self.host = host or OLLAMA_CONFIG["host"]
        self.port = port or OLLAMA_CONFIG["port"]
        self.embedding_model = embedding_model or OLLAMA_CONFIG["embedding_model"]
        self.timeout = timeout or OLLAMA_CONFIG.get("timeout", 60)
        self.ollama_base_url = f"http://{self.host}:{self.port}"
        self.base_url = self.ollama_base_url  # Para compatibilidad
        
        # Para compatibilidad
        self.model = model or (OLLAMA_CONFIG.get("groq_model") if self.provider == "groq" else OLLAMA_CONFIG.get("model", "mistral"))
        
        # Crear sesión HTTP
        self.session = requests.Session()
        
        # Configurar headers para Groq
        if self.provider == "groq":
            self.session.headers.update({
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            })
        
        # Probar conexiones
        self._test_connections()
            
    def generar_respuesta(self, prompt: str, max_tokens: int = 500, temperatura: float = 0.7, 
                          stop_tokens: Optional[list] = None) -> str:
        """
        Genera respuesta usando el provider configurado (Groq u Ollama)
        
        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo de tokens a generar
            temperatura: Temperatura para generación (0.0-1.0)
            stop_tokens: Lista de tokens de parada (opcional)
            
        Returns:
            Respuesta generada
        """
        if self.provider == "groq" and self.llm_disponible:
            return self._generar_respuesta_groq(prompt, max_tokens, temperatura, stop_tokens)
        elif self.provider == "ollama" and self.ollama_disponible:
            return self._generar_respuesta_ollama(prompt, max_tokens, temperatura, stop_tokens)
        else:
            logger.warning(f"⚠️ Provider {self.provider} no disponible, usando respuesta fallback")
            return self._respuesta_fallback()
    
    def _respuesta_fallback(self) -> str:
        """Genera una respuesta de fallback cuando Ollama no está disponible"""
        return """
        TAREA 1: Investigación básica
        DESCRIPCIÓN: Buscar información sobre el tema asignado
        HABILIDADES: investigación, lectura
        COMPLEJIDAD: 2
        TIPO: individual
        
        TAREA 2: Presentación grupal
        DESCRIPCIÓN: Preparar presentación con la información encontrada
        HABILIDADES: comunicación, colaboración
        COMPLEJIDAD: 3
        TIPO: colaborativa
        """
    
    def generar_asignaciones(self, tareas_json: str, perfiles_json: str, adaptaciones_especiales: str = "") -> str:
        """
        Genera asignaciones estudiante-tarea usando el LLM
        
        Args:
            tareas_json: JSON con las tareas disponibles
            perfiles_json: JSON con los perfiles de estudiantes
            adaptaciones_especiales: Adaptaciones específicas requeridas
            
        Returns:
            JSON con las asignaciones generadas
        """
        prompt = f"""
        INSTRUCCIONES: Asigna cada tarea del proyecto a estudiantes específicos, considerando sus perfiles y necesidades.
        
        TAREAS DISPONIBLES:
        {tareas_json}
        
        PERFILES DE ESTUDIANTES:
        {perfiles_json}
        
        ADAPTACIONES ESPECIALES:
        {adaptaciones_especiales}
        
        GENERA asignaciones en formato JSON:
        {{
            "estudiante_001": {{
                "tareas": ["tarea_01", "tarea_03"],
                "rol": "investigador",
                "justificacion": "Su perfil visual se adapta bien a estas tareas de investigación."
            }},
            "estudiante_002": {{
                "tareas": ["tarea_02"],
                "rol": "diseñador",
                "justificacion": "Su creatividad visual es perfecta para esta tarea."
            }}
        }}
        """
        
        return self.generar_respuesta(prompt, max_tokens=800, temperatura=0.5)
    
    def _test_connections(self) -> None:
        """Prueba las conexiones según el provider configurado"""
        try:
            if self.provider == "groq":
                # Test Groq API
                if not self.groq_api_key:
                    logger.error("❌ GROQ_API_KEY no configurada")
                    self.llm_disponible = False
                    return
                    
                test_payload = {
                    "model": self.groq_model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                
                response = self.session.post(
                    f"{self.groq_base_url}/chat/completions",
                    json=test_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("✅ Conexión a Groq API exitosa")
                    self.llm_disponible = True
                else:
                    logger.error(f"❌ Error conectando a Groq: {response.status_code} - {response.text}")
                    self.llm_disponible = False
            
            # Test Ollama para embeddings (siempre necesario)
            try:
                response = self.session.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Conexión a Ollama exitosa (embeddings)")
                    self.ollama_disponible = True
                else:
                    logger.warning("⚠️ Ollama no disponible, usando embeddings fallback")
                    self.ollama_disponible = False
            except Exception as e:
                logger.warning(f"⚠️ No se pudo conectar a Ollama: {e}")
                self.ollama_disponible = False
                
        except Exception as e:
            logger.error(f"❌ Error en test de conexiones: {e}")
            if self.provider == "groq":
                self.llm_disponible = False
            self.ollama_disponible = False
    
    def _generar_respuesta_groq(self, prompt: str, max_tokens: int, temperatura: float, 
                                stop_tokens: Optional[list]) -> str:
        """Genera respuesta usando Groq API"""
        try:
            payload = {
                "model": self.groq_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperatura,
                "stop": stop_tokens or None
            }
            
            response = self.session.post(
                f"{self.groq_base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                respuesta = result["choices"][0]["message"]["content"].strip()
                
                if respuesta:
                    logger.debug(f"✅ Respuesta Groq generada ({len(respuesta)} chars)")
                    return respuesta
                else:
                    logger.warning("⚠️ Respuesta vacía de Groq")
                    return self._respuesta_fallback()
            else:
                logger.error(f"❌ Error en API de Groq: {response.status_code} - {response.text}")
                return self._respuesta_fallback()
                
        except Exception as e:
            logger.error(f"❌ Error generando respuesta Groq: {e}")
            return self._respuesta_fallback()
    
    def _generar_respuesta_ollama(self, prompt: str, max_tokens: int, temperatura: float, 
                                  stop_tokens: Optional[list]) -> str:
        """Genera respuesta usando Ollama local"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperatura,
                    "num_predict": max_tokens,
                    "stop": stop_tokens or []
                }
            }
            
            response = self.session.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                respuesta = result.get("response", "").strip()
                
                if respuesta:
                    logger.debug(f"✅ Respuesta Ollama generada ({len(respuesta)} chars)")
                    return respuesta
                else:
                    logger.warning("⚠️ Respuesta vacía de Ollama")
                    return self._respuesta_fallback()
            else:
                logger.error(f"❌ Error en API de Ollama: {response.status_code}")
                return self._respuesta_fallback()
                
        except Exception as e:
            logger.error(f"❌ Error generando respuesta Ollama: {e}")
            return self._respuesta_fallback()
    
    def listar_modelos(self) -> list:
        """
        Lista los modelos disponibles según el provider
        
        Returns:
            Lista de modelos disponibles
        """
        if self.provider == "groq":
            return ["mixtral-8x7b-32768", "llama3-70b-8192", "llama3-8b-8192"]
        elif self.ollama_disponible:
            try:
                response = self.session.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    models = [model.get('name') for model in result.get('models', [])]
                    return models
                else:
                    logger.error(f"❌ Error obteniendo modelos: {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"❌ Error listando modelos: {e}")
                return []
        else:
            return ["llama3.2", "llama3", "mistral"] # Modelos simulados
    
    def verificar_disponibilidad(self) -> bool:
        """
        Verifica si el provider está disponible
        
        Returns:
            True si el provider está disponible, False en caso contrario
        """
        if self.provider == "groq":
            return self.llm_disponible
        else:
            try:
                response = self.session.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                return response.status_code == 200
            except:
                return False
    
    def cambiar_modelo(self, nuevo_modelo: str) -> bool:
        """
        Cambia el modelo a utilizar
        
        Args:
            nuevo_modelo: Nombre del nuevo modelo
            
        Returns:
            True si se cambió el modelo correctamente, False en caso contrario
        """
        modelos_disponibles = self.listar_modelos()
        
        if nuevo_modelo in modelos_disponibles:
            self.model = nuevo_modelo
            logger.info(f"✅ Modelo cambiado a: {nuevo_modelo}")
            return True
        else:
            logger.error(f"❌ Modelo no disponible: {nuevo_modelo}")
            return False
    
    def generar_embedding(self, texto: str) -> list:
        """
        Genera embedding usando Ollama API
        
        Args:
            texto: Texto para generar embedding
            
        Returns:
            Lista con el vector embedding o lista vacía en caso de error
        """
        if not self.ollama_disponible:
            logger.warning("⚠️ Ollama no disponible, usando embedding fallback")
            return self._embedding_fallback(texto)
            
        try:
            payload = {
                "model": self.embedding_model,
                "input": texto
            }
            
            response = self.session.post(
                f"{self.ollama_base_url}/api/embed",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embeddings", [])
                # Si es una lista de embeddings, tomar el primero
                if isinstance(embedding, list) and len(embedding) > 0:
                    embedding = embedding[0] if isinstance(embedding[0], list) else embedding
                
                if embedding and len(embedding) > 0:
                    logger.debug(f"✅ Embedding generado ({len(embedding)} dims)")
                    return embedding
                else:
                    logger.warning("⚠️ Embedding vacío de Ollama")
                    return self._embedding_fallback(texto)
            else:
                logger.error(f"❌ Error en API de embedding: {response.status_code}")
                return self._embedding_fallback(texto)
                
        except Exception as e:
            logger.error(f"❌ Error generando embedding: {e}")
            return self._embedding_fallback(texto)
    
    def _embedding_fallback(self, texto: str) -> list:
        """Genera un embedding simple como fallback"""
        # Embedding básico basado en hash del texto
        import hashlib
        hash_obj = hashlib.sha256(texto.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generar vector de 128 dimensiones a partir del hash
        embedding = []
        for i in range(128):
            embedding.append((hash_int >> i) & 1)
        
        # Normalizar a floats entre -1 y 1
        embedding = [(x - 0.5) * 2 for x in embedding]
        
        logger.debug(f"🔄 Embedding fallback generado ({len(embedding)} dims)")
        return embedding