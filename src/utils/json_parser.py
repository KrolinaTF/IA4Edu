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

def convertir_a_json(datos: Any) -> str:
    """
    Convierte datos a formato JSON con manejo de dataclasses y tipos personalizados
    
    Args:
        datos: Datos a convertir
        
    Returns:
        String con datos en formato JSON
    """
    try:
        from dataclasses import is_dataclass, asdict
        
        def serializar(obj):
            """Función auxiliar para serializar tipos especiales"""
            if is_dataclass(obj):
                return asdict(obj)
            elif hasattr(obj, 'to_dict') and callable(obj.to_dict):
                return obj.to_dict()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        return json.dumps(datos, default=serializar, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error convirtiendo a JSON: {e}")
        return "{}"

def extraer_json_desde_texto(texto: str) -> Optional[dict]:
    """
    Extrae objetos JSON desde texto libre
    
    Args:
        texto: Texto que puede contener JSON
        
    Returns:
        Diccionario con JSON extraído o None si no se encontró
    """
    # Buscar texto JSON en el texto libre usando regex
    matches = re.findall(r'({[\s\S]*?})', texto)
    
    for match in matches:
        try:
            # Intentar parsear cada coincidencia
            json_obj = json.loads(match)
            
            # Si se pudo parsear y es un diccionario, devolverlo
            if isinstance(json_obj, dict):
                return json_obj
        except:
            # Si no se pudo parsear, continuar con la siguiente coincidencia
            continue
    
    # Si no se encontró JSON válido, intentar extraer usando regex más agresivo
    json_match = re.search(r'({.*})', texto, re.DOTALL)
    if json_match:
        try:
            json_str = json_match.group(1)
            # Intentar parsear con estrategia más robusta
            return parse_json_seguro(json_str)
        except:
            pass
            
    return None

def fusionar_diccionarios(dict1: dict, dict2: dict, sobrescribir: bool = True) -> dict:
    """
    Fusiona dos diccionarios de forma recursiva
    
    Args:
        dict1: Primer diccionario
        dict2: Segundo diccionario
        sobrescribir: Si True, dict2 sobrescribe valores de dict1
        
    Returns:
        Nuevo diccionario con la fusión
    """
    resultado = dict1.copy()
    
    for key, value in dict2.items():
        if key in resultado and isinstance(resultado[key], dict) and isinstance(value, dict):
            # Recursivamente fusionar subdicionarios
            resultado[key] = fusionar_diccionarios(resultado[key], value, sobrescribir)
        elif key not in resultado or sobrescribir:
            # Añadir o sobrescribir valor
            resultado[key] = value
            
    return resultado