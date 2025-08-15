"""
Utilidades para el parseo robusto de JSON.
"""

import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SistemaAgentesABP.JSONParser")

def parse_json_seguro(texto: str) -> Optional[dict]:
    """
    Parseo robusto de JSON con múltiples estrategias de limpieza
    
    Args:
        texto: Texto que contiene JSON a parsear
        
    Returns:
        Diccionario con JSON parseado o None si no se pudo parsear
    """
    try:
        # Estrategia 1: Limpieza básica
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()
        
        # Estrategia 2: Detectar respuestas en texto plano (incluyendo markdown)
        if (texto_limpio.startswith("A continuación") or 
            texto_limpio.startswith("Aquí") or 
            texto_limpio.startswith("**") or  # Markdown
            texto_limpio.startswith("#") or   # Headers
            not texto_limpio.startswith("{")):  # No empieza con JSON
            
            # El LLM respondió en texto plano, extraer JSON si existe
            json_match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
            if json_match:
                texto_limpio = json_match.group()
            else:
                logger.warning(f"❌ LLM respondió en texto plano sin JSON válido")
                logger.warning(f"🔍 Respuesta: {texto[:200]}...")
                return None
                
        if not texto_limpio:
            raise ValueError("Respuesta vacía")
            
        # Estrategia 3: Buscar el primer { hasta el último }
        start_idx = texto_limpio.find('{')
        end_idx = texto_limpio.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            texto_limpio = texto_limpio[start_idx:end_idx+1]
        else:
            logger.warning(f"❌ No se encontraron llaves válidas en: {texto_limpio[:100]}...")
            return None
            
        return json.loads(texto_limpio)
        
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  JSON malformado, intentando reparar: {e}")
        
        # Estrategia 4: Intentar reparar JSON común
        try:
            # Reparar comillas internas comunes
            texto_reparado = texto_limpio
            # Escapar comillas internas en valores
            texto_reparado = re.sub(r'"([^"]*)"([^"]*)"([^"]*)":', r'"\1\"\2\"\3":', texto_reparado)
            # Añadir comas faltantes antes de llaves
            texto_reparado = re.sub(r'"\s*\n\s*{', '",\n    {', texto_reparado)
            # Añadir comas faltantes entre objetos
            texto_reparado = re.sub(r'}\s*\n\s*{', '},\n    {', texto_reparado)
            
            return json.loads(texto_reparado)
            
        except json.JSONDecodeError:
            logger.error(f"❌ No se pudo reparar el JSON del LLM")
            logger.error(f"🔍 Texto recibido (primeros 400 chars): {texto[:400]}...")
            return None
    except Exception as e:
        logger.error(f"❌ Error inesperado en parseo JSON: {e}")
        return None

