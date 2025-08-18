"""
Integrador simplificado con Ollama API.
"""

import logging
import requests
from typing import Dict, Any, Optional

# Importar configuración centralizada
from config import OLLAMA_CONFIG

logger = logging.getLogger("SistemaAgentesABP.OllamaIntegrator")

class OllamaIntegrator:
    """Integrador simplificado con Ollama API"""
    
    def __init__(self, host: str = None, port: int = None, model: str = None, 
                 embedding_model: str = None, timeout: int = None):
        """
        Inicializa el integrador con Ollama
        
        Args:
            host: Host donde se ejecuta Ollama (usa config si no se especifica)
            port: Puerto de Ollama (usa config si no se especifica)
            model: Modelo principal para generación de texto (usa config si no se especifica)
            embedding_model: Modelo específico para embeddings (usa config si no se especifica)
            timeout: Timeout para requests (usa config si no se especifica)
        """
        # Usar configuración centralizada como fallback
        self.host = host or OLLAMA_CONFIG["host"]
        self.port = port or OLLAMA_CONFIG["port"]
        self.model = model or OLLAMA_CONFIG["model"]
        self.embedding_model = embedding_model or OLLAMA_CONFIG["embedding_model"]
        self.timeout = timeout or OLLAMA_CONFIG.get("timeout", 30)
        
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Conectar directamente con Ollama API usando requests
        self.session = requests.Session()
        
        # Probar conexión con Ollama
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Conectado exitosamente a Ollama en {self.base_url}")
                logger.info(f"📋 Modelo configurado: {self.model} | Embeddings: {self.embedding_model}")
                self.ollama_disponible = True
            else:
                logger.error(f"❌ Error conectando a Ollama: {response.status_code}")
                self.ollama_disponible = False
        except Exception as e:
            logger.error(f"❌ No se pudo conectar a Ollama en {self.base_url}: {e}")
            self.ollama_disponible = False
            
    def generar_respuesta(self, prompt: str, max_tokens: int = 500, temperatura: float = 0.7, 
                          stop_tokens: Optional[list] = None) -> str:
        """
        Genera respuesta usando Ollama
        
        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo de tokens a generar
            temperatura: Temperatura para generación (0.0-1.0)
            stop_tokens: Lista de tokens de parada (opcional)
            
        Returns:
            Respuesta generada
        """
        if self.ollama_disponible:
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
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    respuesta = result.get("response", "").strip()
                    
                    if respuesta:
                        logger.debug(f"✅ Respuesta generada ({len(respuesta)} chars)")
                        return respuesta
                    else:
                        logger.warning("⚠️ Respuesta vacía de Ollama")
                        return self._respuesta_fallback()
                else:
                    logger.error(f"❌ Error en API de Ollama: {response.status_code}")
                    return self._respuesta_fallback()
                    
            except Exception as e:
                logger.error(f"❌ Error generando respuesta: {e}")
                return self._respuesta_fallback()
        else:
            logger.warning("⚠️ Ollama no disponible, usando respuesta fallback")
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
    
    def listar_modelos(self) -> list:
        """
        Lista los modelos disponibles en Ollama
        
        Returns:
            Lista de modelos disponibles
        """
        if self.ollama_disponible:
            try:
                response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
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
        Verifica si Ollama está disponible
        
        Returns:
            True si Ollama está disponible, False en caso contrario
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
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
                f"{self.base_url}/api/embed",
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