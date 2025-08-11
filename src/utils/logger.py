"""
Configuración de logging para el sistema de agentes ABP.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

def configurar_logging(
    level: int = logging.INFO,
    formato: str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    log_file: Optional[str] = None,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    Configura el sistema de logging
    
    Args:
        level: Nivel de logging
        formato: Formato del mensaje de log
        log_file: Nombre del archivo de log (opcional)
        log_dir: Directorio para los logs
        
    Returns:
        Logger principal configurado
    """
    # Crear directorio de logs si no existe
    if log_file:
        os.makedirs(log_dir, exist_ok=True)
        
        # Generar nombre de archivo con timestamp si no se proporciona
        if log_file == True:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f"abp_{timestamp}.log"
            
        log_path = os.path.join(log_dir, log_file)
    else:
        log_path = None
    
    # Configurar logger principal
    logger = logging.getLogger("SistemaAgentesABP")
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Crear formato
    formatter = logging.Formatter(formato)
    
    # Configurar handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configurar handler de archivo si se especificó
    if log_path:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logs guardados en: {log_path}")
    
    return logger

class ColoredFormatter(logging.Formatter):
    """Formateador de logs con colores para la consola"""
    
    # Códigos ANSI para colores
    COLORS = {
        'DEBUG': '\033[94m',  # Azul
        'INFO': '\033[92m',   # Verde
        'WARNING': '\033[93m', # Amarillo
        'ERROR': '\033[91m',  # Rojo
        'CRITICAL': '\033[91m\033[1m', # Rojo brillante
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        """Formato con colores para los logs"""
        log_message = super().format(record)
        
        # Añadir color según el nivel
        level_name = record.levelname
        if level_name in self.COLORS:
            log_message = f"{self.COLORS[level_name]}{log_message}{self.COLORS['RESET']}"
            
        return log_message

def configurar_logging_colorido(
    level: int = logging.INFO,
    formato: str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    log_file: Optional[str] = None,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    Configura el sistema de logging con colores en la consola
    
    Args:
        level: Nivel de logging
        formato: Formato del mensaje de log
        log_file: Nombre del archivo de log (opcional)
        log_dir: Directorio para los logs
        
    Returns:
        Logger principal configurado
    """
    # Crear directorio de logs si no existe
    if log_file:
        os.makedirs(log_dir, exist_ok=True)
        
        # Generar nombre de archivo con timestamp si no se proporciona
        if log_file == True:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f"abp_{timestamp}.log"
            
        log_path = os.path.join(log_dir, log_file)
    else:
        log_path = None
    
    # Configurar logger principal
    logger = logging.getLogger("SistemaAgentesABP")
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Crear formatos
    console_formatter = ColoredFormatter(formato)
    file_formatter = logging.Formatter(formato)
    
    # Configurar handler de consola con colores
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Configurar handler de archivo si se especificó (sin colores)
    if log_path:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logs guardados en: {log_path}")
    
    return logger

def configurar_emoji_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    Configura el sistema de logging con emojis y colores
    
    Args:
        level: Nivel de logging
        log_file: Nombre del archivo de log (opcional)
        log_dir: Directorio para los logs
        
    Returns:
        Logger principal configurado
    """
    # Formato con emojis
    emoji_formato = '%(asctime)s - %(emoji)s %(levelname)s - %(name)s - %(message)s'
    
    # Clase personalizada para añadir emojis
    class EmojiAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            level = kwargs.get('levelno', self.logger.level)
            
            if level >= logging.CRITICAL:
                emoji = '🔥'
            elif level >= logging.ERROR:
                emoji = '❌'
            elif level >= logging.WARNING:
                emoji = '⚠️'
            elif level >= logging.INFO:
                emoji = '📝'
            else:  # DEBUG
                emoji = '🔍'
                
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['emoji'] = emoji
            return msg, kwargs
    
    # Usar el configurador de color existente
    base_logger = configurar_logging_colorido(level, emoji_formato, log_file, log_dir)
    
    # Envolver en el adaptador de emojis
    logger = EmojiAdapter(base_logger, {})
    
    return logger