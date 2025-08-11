"""
Clase base para todos los agentes especializados del sistema ABP.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator

class BaseAgent(ABC):
    """
    Clase base para todos los agentes especializados del sistema ABP
    
    Proporciona funcionalidad común y establece la interfaz estándar que
    todos los agentes deben seguir, eliminando duplicación de código.
    """
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """
        Inicializa el agente base con integrador LLM
        
        Args:
            ollama_integrator: Integrador de LLM
        """
        self.ollama = ollama_integrator
        self.agent_name = self.__class__.__name__
        
        # Logger específico para cada agente
        self.logger = logging.getLogger(f"SistemaAgentesABP.{self.agent_name}")
        self.logger.info(f"🤖 {self.agent_name} inicializado")
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Método principal de procesamiento - debe ser implementado por cada agente
        
        Args:
            *args, **kwargs: Argumentos específicos de cada agente
            
        Returns:
            Any: Resultado del procesamiento específico del agente
        """
        pass
    
    @abstractmethod 
    def _parse_response(self, response: str) -> Any:
        """
        Parsea respuesta del LLM - implementación específica por agente
        
        Args:
            response: Respuesta cruda del LLM
            
        Returns:
            Any: Datos estructurados específicos del agente
        """
        pass
    
    # ===== MÉTODOS COMUNES DE EXTRACCIÓN DE TEXTO =====
    
    def _extraer_campo(self, texto: str, campo: str, default: str = "No especificado") -> str:
        """
        Extrae un campo específico del texto
        
        Args:
            texto: Texto donde buscar
            campo: Campo a extraer
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor del campo
        """
        if not texto or not campo:
            return default
            
        lines = texto.split('\n')
        for line in lines:
            if campo.lower() in line.lower():
                # Extraer después del campo
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
                # Alternativa: extraer después del campo sin ':'
                return line.replace(campo, '').strip()
        return default
    
    def _extraer_lista(self, texto: str, campo: str) -> List[str]:
        """
        Extrae una lista separada por comas del texto
        
        Args:
            texto: Texto donde buscar
            campo: Campo a extraer
            
        Returns:
            Lista de elementos
        """
        valor = self._extraer_campo(texto, campo, "")
        if valor and valor != "No especificado":
            # Limpiar y dividir por comas
            items = [item.strip().strip('•-*') for item in valor.split(',')]
            return [item for item in items if item]  # Filtrar vacíos
        return []
    
    def _extraer_numero(self, texto: str, campo: str, default: int = 1) -> int:
        """
        Extrae un número del texto
        
        Args:
            texto: Texto donde buscar
            campo: Campo a extraer
            default: Valor por defecto si no se encuentra
            
        Returns:
            Número extraído
        """
        valor = self._extraer_campo(texto, campo, "")
        if valor:
            # Buscar primer número en el valor
            numeros = re.findall(r'\d+', valor)
            if numeros:
                return int(numeros[0])
        return default
    
    def _extraer_duracion(self, texto: str) -> int:
        """
        Extrae duración en minutos del texto
        
        Args:
            texto: Texto donde buscar
            
        Returns:
            Duración en minutos
        """
        # Buscar patrones como "30 min", "1 hora", "1.5 horas"
        duracion_match = re.search(r'(\d+(?:\.\d+)?)\s*(min|minuto|hora|sesion|session)', texto.lower())
        if duracion_match:
            cantidad = float(duracion_match.group(1))
            unidad = duracion_match.group(2)
            
            if 'hora' in unidad:
                return int(cantidad * 60)  # Convertir a minutos
            elif 'min' in unidad:
                return int(cantidad)
            elif 'sesion' in unidad:
                return int(cantidad * 45)  # Asumimos 45 min por sesión
        
        return 45  # Default: 45 minutos
    
    # ===== MÉTODOS COMUNES DE INTERACCIÓN CON LLM =====
    
    def _call_llm_with_fallback(self, prompt: str, max_tokens: int, fallback_data: Any, 
                               fallback_name: str = "fallback") -> Any:
        """
        Llama al LLM con manejo robusto de errores y fallback
        
        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo tokens de respuesta
            fallback_data: Datos a usar si falla el LLM
            fallback_name: Nombre del fallback para logging
            
        Returns:
            Datos parseados del LLM o fallback
        """
        try:
            self.logger.info(f"🔄 {self.agent_name} llamando al LLM...")
            response = self.ollama.generar_respuesta(prompt, max_tokens=max_tokens)
            
            if not response or not response.strip():
                raise ValueError("Respuesta vacía del LLM")
            
            parsed = self._parse_response(response)
            if parsed is not None:
                self.logger.info(f"✅ {self.agent_name} - Respuesta LLM procesada exitosamente")
                return parsed
            else:
                raise ValueError("Falló el parseo de la respuesta LLM")
                
        except Exception as e:
            self.logger.error(f"❌ {self.agent_name} - Error en llamada LLM: {e}")
            self.logger.info(f"⚠️  {self.agent_name} - Usando {fallback_name}")
            return fallback_data
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Parsea respuesta JSON con manejo robusto de errores
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Diccionario con JSON parseado o None si no se pudo parsear
        """
        from utils.json_parser import parse_json_seguro
        return parse_json_seguro(response)
    
    def _crear_prompt_estructurado(self, template: str, **kwargs) -> str:
        """
        Crea un prompt estructurado reemplazando placeholders
        
        Args:
            template: Template del prompt con placeholders {variable}
            **kwargs: Variables para reemplazar en el template
            
        Returns:
            Prompt con variables reemplazadas
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"❌ {self.agent_name} - Variable faltante en prompt: {e}")
            return template
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    def _log_processing_start(self, input_description: str):
        """
        Log del inicio del procesamiento
        
        Args:
            input_description: Descripción de la entrada
        """
        self.logger.info(f"🚀 {self.agent_name} - Iniciando procesamiento: {input_description}")
    
    def _log_processing_end(self, result_description: str):
        """
        Log del fin del procesamiento
        
        Args:
            result_description: Descripción del resultado
        """  
        self.logger.info(f"🎯 {self.agent_name} - Procesamiento completado: {result_description}")
    
    def _validate_required_params(self, params: Dict[str, Any], required: List[str]) -> bool:
        """
        Valida que los parámetros requeridos estén presentes
        
        Args:
            params: Diccionario de parámetros
            required: Lista de parámetros requeridos
            
        Returns:
            True si todos los parámetros requeridos están presentes, False en caso contrario
        """
        missing = [param for param in required if param not in params or params[param] is None]
        if missing:
            self.logger.error(f"❌ {self.agent_name} - Parámetros faltantes: {missing}")
            return False
        return True