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
        
        # Sistema de debate extendido
        self.debates_activos = {}
        self.historial_debates = []
        
        logger.info("🔗 Comunicador de agentes inicializado con capacidades de debate")
        
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
    
    def iniciar_debate(self, tema: str, decision_critica: Dict, agentes_participantes: List[str], 
                      coordinador: str = "coordinador") -> Dict:
        """
        Inicia un debate entre agentes para tomar decisiones críticas
        
        Args:
            tema: Tema del debate (ej: "tipo_actividad", "combinacion_elementos")
            decision_critica: Datos sobre la decisión a tomar
            agentes_participantes: Lista de agentes que participan
            coordinador: Agente que actuará como moderador
            
        Returns:
            Resultado del debate con la decisión consensuada
        """
        debate_id = f"debate_{len(self.historial_debates) + 1}_{tema}"
        
        logger.info(f"🗣️ Iniciando debate: {debate_id}")
        logger.info(f"   👥 Participantes: {', '.join(agentes_participantes)}")
        logger.info(f"   ⚖️ Moderador: {coordinador}")
        
        debate = {
            'id': debate_id,
            'tema': tema,
            'moderador': coordinador,
            'participantes': agentes_participantes,
            'decision_critica': decision_critica,
            'rondas': [],
            'decision_final': None,
            'timestamp_inicio': datetime.now().isoformat(),
            'estado': 'en_curso'
        }
        
        self.debates_activos[debate_id] = debate
        
        try:
            # RONDA 1: Propuesta inicial (normalmente el Analizador)
            if 'analizador_tareas' in agentes_participantes:
                logger.info(f"🎯 Ronda 1: Propuesta inicial por analizador_tareas")
                propuesta = self.enviar_mensaje(
                    coordinador, 'analizador_tareas', 'generar_propuesta_debate', 
                    {'tema': tema, 'contexto': decision_critica}
                )
                debate['rondas'].append({
                    'numero': 1,
                    'agente': 'analizador',
                    'tipo': 'propuesta_inicial',
                    'contenido': propuesta
                })
            
            # RONDA 2: Evaluación pedagógica (Perfilador)
            if 'perfilador_estudiantes' in agentes_participantes:
                logger.info(f"👥 Ronda 2: Evaluación pedagógica por perfilador_estudiantes")
                evaluacion = self.enviar_mensaje(
                    coordinador, 'perfilador_estudiantes', 'evaluar_propuesta_debate',
                    {'propuesta': debate['rondas'][-1]['contenido'], 'contexto': decision_critica}
                )
                debate['rondas'].append({
                    'numero': 2,
                    'agente': 'perfilador',
                    'tipo': 'evaluacion_pedagogica',
                    'contenido': evaluacion
                })
            
            # RONDA 3: Viabilidad práctica (Optimizador)
            if 'optimizador_asignaciones' in agentes_participantes:
                logger.info(f"⚙️ Ronda 3: Viabilidad práctica por optimizador_asignaciones")
                viabilidad = self.enviar_mensaje(
                    coordinador, 'optimizador_asignaciones', 'evaluar_viabilidad_debate',
                    {'propuesta': debate['rondas'][0]['contenido'], 
                     'evaluacion': debate['rondas'][-1]['contenido'] if len(debate['rondas']) > 1 else None,
                     'contexto': decision_critica}
                )
                debate['rondas'].append({
                    'numero': 3,
                    'agente': 'optimizador',
                    'tipo': 'viabilidad_practica',
                    'contenido': viabilidad
                })
            
            # RONDA 4: Consenso o arbitraje (Coordinador)
            logger.info(f"⚖️ Ronda 4: Decisión final por coordinador")
            decision_final = self._arbitrar_debate(debate)
            
            debate['decision_final'] = decision_final
            debate['estado'] = 'completado'
            debate['timestamp_fin'] = datetime.now().isoformat()
            
            # Mover a historial
            self.historial_debates.append(debate)
            del self.debates_activos[debate_id]
            
            logger.info(f"✅ Debate {debate_id} completado con decisión: {decision_final.get('tipo', 'sin_tipo')}")
            return decision_final
            
        except Exception as e:
            debate['estado'] = 'error'
            debate['error'] = str(e)
            logger.error(f"❌ Debate {debate_id} falló: {e}")
            return {'error': str(e), 'decision': 'fallback'}
    
    def _arbitrar_debate(self, debate: Dict) -> Dict:
        """
        Arbitra el debate basándose en las rondas para tomar la decisión final
        
        Args:
            debate: Datos completos del debate
            
        Returns:
            Decisión final consensuada
        """
        logger.info(f"⚖️ Arbitrando debate: {debate['tema']}")
        
        # Extraer puntos clave de cada ronda
        propuesta_inicial = None
        evaluacion_pedagogica = None
        viabilidad_practica = None
        
        for ronda in debate['rondas']:
            if ronda['tipo'] == 'propuesta_inicial':
                propuesta_inicial = ronda['contenido']
            elif ronda['tipo'] == 'evaluacion_pedagogica':
                evaluacion_pedagogica = ronda['contenido']
            elif ronda['tipo'] == 'viabilidad_practica':
                viabilidad_practica = ronda['contenido']
        
        # Lógica de arbitraje simple basada en consenso
        decision = {
            'tipo': 'consenso',
            'propuesta_base': propuesta_inicial,
            'adaptaciones_pedagogicas': evaluacion_pedagogica,
            'modificaciones_viabilidad': viabilidad_practica,
            'decision_arbitrada': True,
            'justificacion': f"Consenso alcanzado en debate {debate['id']}"
        }
        
        # Si hay conflictos, priorizar viabilidad pedagógica
        if evaluacion_pedagogica and isinstance(evaluacion_pedagogica, dict):
            if evaluacion_pedagogica.get('rechazo') or evaluacion_pedagogica.get('conflicto'):
                decision['tipo'] = 'modificacion_pedagogica'
                decision['justificacion'] = "Propuesta modificada por criterios pedagógicos"
        
        return decision