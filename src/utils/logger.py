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

