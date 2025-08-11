"""
Sistema de comunicación centralizada entre agentes.
"""

import logging
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("SistemaAgentesABP.ComunicadorAgentes")

class ComunicadorAgentes:
    """Sistema de comunicación centralizada entre agentes"""
    
    def __init__(self):
        self.mensajes = []
        self.agentes_registrados = {}
        self.interfaces_agentes = {}  # Registro de métodos y parámetros
        
        logger.info("🔗 Comunicador de agentes inicializado")
        
    def registrar_agente(self, nombre: str, agente):
        """
        Registra un agente en el sistema de comunicación
        
        Args:
            nombre: Identificador único del agente
            agente: Instancia del agente
        """
        self.agentes_registrados[nombre] = agente
        
        # Registrar métodos públicos del agente (no los que empiezan con _)
        self.interfaces_agentes[nombre] = {
            method_name: method 
            for method_name, method in inspect.getmembers(agente, inspect.ismethod)
            if not method_name.startswith('_') and method_name != 'process'
        }
        
        logger.info(f"🔗 Agente registrado: {nombre} con {len(self.interfaces_agentes[nombre])} métodos")
        
    def enviar_mensaje(self, remitente: str, destinatario: str, metodo: str, datos: dict) -> dict:
        """
        Envía un mensaje de un agente a otro y ejecuta el método correspondiente
        
        Args:
            remitente: Nombre del agente que envía el mensaje
            destinatario: Nombre del agente destinatario
            metodo: Nombre del método a ejecutar
            datos: Datos para el método
            
        Returns:
            Resultado de la ejecución del método
        """
        # Verificar existencia del destinatario
        if destinatario not in self.agentes_registrados:
            raise Exception(f"Agente destinatario no encontrado: {destinatario}")
            
        # Crear registro del mensaje
        mensaje = {
            'id': len(self.mensajes) + 1,
            'timestamp': datetime.now().isoformat(),
            'remitente': remitente,
            'destinatario': destinatario,
            'metodo': metodo,
            'datos': datos,
            'estado': 'enviado'
        }
        
        self.mensajes.append(mensaje)
        logger.info(f"📨 Mensaje {mensaje['id']}: {remitente} → {destinatario}.{metodo}")
        
        try:
            # Obtener el agente y el método
            agente = self.agentes_registrados[destinatario]
            
            # Verificar si el método existe
            if metodo not in self.interfaces_agentes[destinatario]:
                raise Exception(f"Método no encontrado: {metodo} en {destinatario}")
            
            metodo_func = self.interfaces_agentes[destinatario][metodo]
            
            # Ejecutar el método (utilizando process como interfaz estándar)
            if hasattr(agente, 'process') and metodo == 'process':
                resultado = agente.process(**datos)
            else:
                # Método específico del agente
                resultado = metodo_func(**datos)
                
            mensaje['estado'] = 'completado'
            mensaje['resultado'] = resultado
            
            logger.info(f"✅ Mensaje {mensaje['id']} completado exitosamente")
            return resultado
            
        except Exception as e:
            mensaje['estado'] = 'error'
            mensaje['error'] = str(e)
            logger.error(f"❌ Mensaje {mensaje['id']} falló: {e}")
            raise e
            
    def obtener_historial(self, filtro_agente: str = None) -> list:
        """
        Obtiene el historial de comunicación
        
        Args:
            filtro_agente: Filtrar por agente (opcional)
            
        Returns:
            Lista de mensajes
        """
        if filtro_agente:
            return [m for m in self.mensajes 
                   if m['remitente'] == filtro_agente or m['destinatario'] == filtro_agente]
        return self.mensajes
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de comunicación
        
        Returns:
            Diccionario con estadísticas
        """
        # Contar mensajes por estado
        estados = {}
        for m in self.mensajes:
            estado = m.get('estado', 'desconocido')
            estados[estado] = estados.get(estado, 0) + 1
        
        # Contar mensajes por agente
        agentes_actividad = {}
        for m in self.mensajes:
            remitente = m.get('remitente', 'desconocido')
            destinatario = m.get('destinatario', 'desconocido')
            
            agentes_actividad[remitente] = agentes_actividad.get(remitente, 0) + 1
            agentes_actividad[destinatario] = agentes_actividad.get(destinatario, 0) + 1
        
        return {
            'total_mensajes': len(self.mensajes),
            'mensajes_por_estado': estados,
            'agentes_actividad': agentes_actividad,
            'agentes_registrados': list(self.agentes_registrados.keys()),
            'timestamp': datetime.now().isoformat()
        }
    
    def resetear(self) -> None:
        """Resetea el historial de mensajes manteniendo los agentes registrados"""
        self.mensajes = []
        logger.info("🔄 Historial de mensajes reseteado")