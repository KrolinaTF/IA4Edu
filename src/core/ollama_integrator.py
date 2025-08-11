"""
Integrador simplificado con Ollama API.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("SistemaAgentesABP.OllamaIntegrator")

class OllamaIntegrator:
    """Integrador simplificado con Ollama API"""
    
    def __init__(self, host: str = "192.168.1.10", port: int = 11434, model: str = "llama3.2"):
        """
        Inicializa el integrador con Ollama
        
        Args:
            host: Host donde se ejecuta Ollama
            port: Puerto de Ollama
            model: Modelo a utilizar
        """
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        
        # Conectar directamente con Ollama API usando requests
        self.session = requests.Session()
        
        # Probar conexión con Ollama
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Conectado exitosamente a Ollama en {self.base_url}")
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
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"❌ Error en API Ollama: {response.status_code}")
                    return self._respuesta_fallback()
                    
            except Exception as e:
                logger.error(f"❌ Error generando respuesta: {e}")
                return self._respuesta_fallback()
        else:
            return self._respuesta_fallback()
    
    def _respuesta_fallback(self) -> str:
        """
        Respuesta de fallback cuando Ollama no está disponible
        
        Returns:
            Texto con respuesta de fallback
        """
        return """
        [SIMULADO JSON]
        {
            "estudiante_001": {
                "tareas": ["tarea_01", "tarea_03"],
                "rol": "coordinador",
                "justificacion": "Basado en su fortaleza de liderazgo."
            },
            "estudiante_002": {
                "tareas": ["tarea_02"],
                "rol": "diseñador",
                "justificacion": "Su creatividad visual es perfecta para esta tarea."
            }
        }
        """
    
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