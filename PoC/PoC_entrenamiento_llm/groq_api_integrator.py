#!/usr/bin/env python3
"""
Integrador con Groq API para generar actividades educativas
API gratuita y rápida alternativa a HuggingFace
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GROQ_API")

# Cargar variables del archivo .env manualmente
def load_env_file():
    """
    Carga variables de entorno desde un archivo .env
    Busca el archivo en varias ubicaciones posibles
    """
    # Lista de posibles ubicaciones del archivo .env
    possible_paths = [
        '.env',  # Directorio actual
        os.path.join(os.path.dirname(__file__), '.env'),  # Directorio del script
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # Directorio padre
    ]
    
    # Buscar el archivo .env en las posibles ubicaciones
    for env_path in possible_paths:
        if os.path.exists(env_path):
            logger.info(f" Archivo .env encontrado en: {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        if key.strip() == 'GROQ_API_KEY':
                            logger.info(" GROQ_API_KEY configurado desde archivo .env")
            return True
            
    logger.info(" No se encontró archivo .env")
    return False

# Cargar variables del .env
load_env_file()

class GroqAPIEducationGenerator:
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.1-8b-instant"):
        """
        Inicializa el generador con Groq API
        
        Args:
            api_key: Token de la API de Groq (opcional, se busca en .env)
            model_name: Modelo a usar (por defecto llama-3.1-8b-instant)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.model_name = model_name
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            logger.error("ERROR No se encontró GROQ_API_KEY en variables de entorno")
            raise ValueError("Se requiere GROQ_API_KEY")
        
        logger.info(f" Groq API inicializada con modelo: {self.model_name}")
        logger.info(f" Token encontrado: {self.api_key[:10]}...")
    
    def generar_texto(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Genera texto usando Groq API
        
        Args:
            prompt: Texto de entrada para el modelo
            max_tokens: Máximo número de tokens a generar
            temperature: Creatividad del modelo (0.0 - 1.0)
            
        Returns:
            Texto generado por el modelo
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Sanitizar prompt para evitar problemas de encoding
        prompt_clean = prompt.encode('utf-8', 'ignore').decode('utf-8')
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt_clean
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            logger.info(f" Enviando solicitud a Groq API...")
            logger.info(f" Prompt: {prompt[:100]}...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f" Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                logger.info("OK Texto generado exitosamente")
                logger.info(f" Resultado: {generated_text[:100]}...")
                return generated_text
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(f"ERROR {error_msg}")
                return f"Error al generar texto: {error_msg}"
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout al conectar con Groq API"
            logger.error(f"TIMEOUT {error_msg}")
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Error de conexión con Groq API"
            logger.error(f"CONNECTION_ERROR {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"UNEXPECTED_ERROR {error_msg}")
            return error_msg

def test_groq_api():
    """
    Función de prueba para verificar que la API funciona
    """
    try:
        generator = GroqAPIEducationGenerator()
        
        # Prueba simple
        prompt = "Explica qué son las fracciones de manera simple para niños de 4º de primaria"
        result = generator.generar_texto(prompt, max_tokens=200)
        
        print("=" * 50)
        print("PRUEBA DE GROQ API")
        print("=" * 50)
        print(f"Prompt: {prompt}")
        print("-" * 50)
        print(f"Resultado: {result}")
        print("=" * 50)
        
    except Exception as e:
        print(f"ERROR Error en la prueba: {e}")

if __name__ == "__main__":
    test_groq_api()