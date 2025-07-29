#!/usr/bin/env python3
"""
Integrador con Ollama API para generar actividades educativas
Conexión a servidor Ollama local o remoto
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OLLAMA_API")

class OllamaAPIEducationGenerator:
    
    def __init__(self, host: str = "192.168.1.10", port: int = 11434, model_name: str = "llama3.2"):
        """
        Inicializa el generador con Ollama API
        
        Args:
            host: IP o hostname del servidor Ollama
            port: Puerto del servidor Ollama (por defecto 11434)
            model_name: Modelo a usar (debe estar instalado en Ollama)
        """
        self.host = host
        self.port = port
        self.model_name = model_name
        self.base_url = f"http://{host}:{port}"
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
        
        logger.info(f"🦙 Ollama API inicializada")
        logger.info(f"📍 Servidor: {self.base_url}")
        logger.info(f"🤖 Modelo: {self.model_name}")
        
        # Verificar conexión y modelo
        if not self._verificar_conexion():
            raise ConnectionError(f"No se puede conectar a Ollama en {self.base_url}")
        
        if not self._verificar_modelo():
            raise ValueError(f"Modelo '{self.model_name}' no disponible en Ollama")
    
    def _verificar_conexion(self) -> bool:
        """Verifica si el servidor Ollama está disponible"""
        try:
            response = requests.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ Conexión con Ollama establecida")
                return True
            else:
                logger.error(f"❌ Error de conexión: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ No se puede conectar a Ollama: {e}")
            return False
    
    def _verificar_modelo(self) -> bool:
        """Verifica si el modelo está disponible"""
        try:
            response = requests.get(self.tags_url)
            if response.status_code == 200:
                models = response.json()
                available_models = [model['name'] for model in models.get('models', [])]
                
                # Buscar el modelo (con o sin :latest)
                model_variations = [
                    self.model_name,
                    f"{self.model_name}:latest",
                    self.model_name.replace(":latest", "")
                ]
                
                for variation in model_variations:
                    if variation in available_models:
                        logger.info(f"✅ Modelo '{variation}' encontrado")
                        self.model_name = variation  # Actualizar con la versión exacta
                        return True
                
                logger.error(f"❌ Modelo '{self.model_name}' no encontrado")
                logger.info(f"📋 Modelos disponibles: {available_models}")
                return False
            else:
                logger.error("❌ No se pudo obtener lista de modelos")
                return False
        except Exception as e:
            logger.error(f"❌ Error verificando modelo: {e}")
            return False
    
    def listar_modelos(self) -> List[Dict]:
        """Lista todos los modelos disponibles en Ollama"""
        try:
            response = requests.get(self.tags_url)
            if response.status_code == 200:
                return response.json().get('models', [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []
    
    def generar_texto(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Genera texto usando Ollama API
        
        Args:
            prompt: Texto de entrada para el modelo
            max_tokens: Máximo número de tokens a generar (aproximado)
            temperature: Creatividad del modelo (0.0 - 1.0)
            
        Returns:
            Texto generado por el modelo
        """
        
        # Preparar payload para Ollama
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,  # Respuesta completa, no streaming
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens  # Parámetro de Ollama para max tokens
            }
        }
        
        try:
            logger.info(f"🚀 Enviando solicitud a Ollama...")
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            
            start_time = time.time()
            
            response = requests.post(
                self.generate_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=120  # Timeout más largo para modelos locales
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"⏱️ Tiempo de respuesta: {duration:.2f} segundos")
            logger.info(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                
                # Log adicional de estadísticas si están disponibles
                if 'eval_count' in result:
                    eval_count = result['eval_count']
                    eval_duration = result.get('eval_duration', 0) / 1e9  # Convertir a segundos
                    tokens_per_sec = eval_count / eval_duration if eval_duration > 0 else 0
                    logger.info(f"📈 Tokens generados: {eval_count}")
                    logger.info(f"⚡ Velocidad: {tokens_per_sec:.1f} tokens/segundo")
                
                logger.info("✅ Texto generado exitosamente")
                logger.info(f"📄 Resultado: {generated_text[:100]}...")
                return generated_text
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(f"❌ {error_msg}")
                return f"Error al generar texto: {error_msg}"
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout al conectar con Ollama"
            logger.error(f"⏰ {error_msg}")
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión con Ollama en {self.base_url}"
            logger.error(f"🔌 {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return error_msg
    
    def generar_texto_streaming(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7):
        """
        Genera texto usando streaming (para respuestas en tiempo real)
        
        Returns:
            Generator que yield cada chunk de texto
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                self.generate_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                stream=True,
                timeout=120
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            yield chunk['response']
                        if chunk.get('done', False):
                            break
            else:
                yield f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            yield f"Error en streaming: {str(e)}"

def test_ollama_api(host="192.168.1.146", model="llama3.2"):
    """
    Función de prueba para verificar que Ollama funciona
    """
    try:
        print("🦙 INICIANDO PRUEBA DE OLLAMA API")
        print("=" * 50)
        
        generator = OllamaAPIEducationGenerator(host=host, model_name=model)
        
        # Mostrar modelos disponibles
        print("\n📋 MODELOS DISPONIBLES:")
        modelos = generator.listar_modelos()
        for modelo in modelos:
            param_size = modelo.get('details', {}).get('parameter_size', 'N/A')
            print(f"  • {modelo['name']} ({param_size})")
        
        # Prueba simple
        prompt = "Explica qué son las fracciones de manera simple para niños de 4º de primaria"
        print(f"\n📝 PROMPT: {prompt}")
        print("-" * 50)
        
        result = generator.generar_texto(prompt, max_tokens=200)
        
        print(f"📄 RESULTADO:")
        print(result)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    # Prueba con tu servidor
    test_ollama_api("192.168.1.146", "llama3.2")