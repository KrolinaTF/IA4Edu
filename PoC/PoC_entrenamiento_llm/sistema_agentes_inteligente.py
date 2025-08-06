print(f"⚠️  {total_problemas} problemas logísticos detectados")


class OrquestadorAgent(BaseAgent):
    """Agente maestro que coordina el flujo completo, maneja iteraciones y human-in-the-loop"""
    
    def __init__(self):
        super().__init__("Orquestador", llm_required=True)
        
        # Pipeline de agentes
        self.agentes = {
            'ideador': IdeadorAgent(),
            'adaptador_dua': AdaptadorDUAAgent(),
            'arquitecto_tareas': ArquitectoTareasAgent(),
            'validador_curricular': ValidadorCurricularAgent(),
            'gestor_logistico': GestorLogisticoAgent()
        }
        
        # Flujo normal del pipeline
        self.flujo_normal = [
            'ideador',
            'adaptador_dua', 
            'arquitecto_tareas',
            'validador_curricular',
            'gestor_logistico'
        ]
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Orquesta el proceso completo de generación de actividad"""
        
        print(f"\n🎯 [{self.name}] Iniciando generación de actividad")
        print(f"Tema: {state.tema}")
        print(f"Iteración: {state.iteracion}")
        
        # Ejecutar pipeline principal
        state = self._ejecutar_pipeline(state)
        
        # Evaluar resultado y decidir siguiente paso
        decision = self._evaluar_resultado(state)
        
        if decision['accion'] == 'completar':
            state.estado = EstadoActividad.COMPLETADO
            print(f"\n✅ [{self.name}] Actividad completada exitosamente")
            
        elif decision['accion'] == 'iterar':
            # Manejar iteración
            state = self._manejar_iteracion(state, decision)
            
        elif decision['accion'] == 'human_input':
            # Requiere intervención humana
            state = self._solicitar_intervencion_humana(state, decision)
        
        return state
    
    def _ejecutar_pipeline(self, state: ActividadState) -> ActividadState:
        """Ejecuta la secuencia de agentes"""
        
        for i, agente_name in enumerate(self.flujo_normal):
            # Mostrar progreso
            print(f"\n📋 Paso {i+1}/{len(self.flujo_normal)}: {agente_name}")
            
            # Ejecutar agente
            agente = self.agentes[agente_name]
            state = agente.procesar(state)
            
            # Verificar si hay problemas críticos que requieren parar
            if self._hay_problemas_criticos(state):
                print(f"⚠️  Problemas críticos detectados en {agente_name}")
                break
                
            # Checkpoint para posible human input
            if state.necesita_human_input:
                print(f"🔔 {agente_name} solicita intervención humana")
                break
        
        return state
    
    def _evaluar_resultado(self, state: ActividadState) -> Dict:
        """Evalúa el estado actual y decide la siguiente acción"""
        
        # Verificar completitud
        completitud = self._verificar_completitud(state)
        
        # Verificar calidad
        problemas = self._analizar_problemas(state)
        
        # Decidir acción
        if completitud['completo'] and not problemas['criticos']:
            return {'accion': 'completar', 'razon': 'Actividad completa y sin problemas críticos'}
        
        elif problemas['criticos']:
            return {
                'accion': 'iterar', 
                'razon': f"Problemas críticos: {', '.join(problemas['criticos'])}",
                'volver_a_agente': self._determinar_agente_responsable(problemas['criticos'])
            }
        
        elif state.necesita_human_input:
            return {
                'accion': 'human_input',
                'razon': 'Agente solicitó intervención humana',
                'contexto': problemas
            }
        
        else:
            return {
                'accion': 'iterar',
                'razon': 'Actividad incompleta',
                'volver_a_agente': self._encontrar_primer_agente_incompleto(completitud)
            }
    
    def _manejar_iteracion(self, state: ActividadState, decision: Dict) -> ActividadState:
        """Maneja el proceso de iteración cuando hay problemas"""
        
        print(f"\n🔄 [{self.name}] Iniciando iteración")
        print(f"Razón: {decision['razon']}")
        
        # Incrementar contador de iteración
        state.iteracion += 1
        state.estado = EstadoActividad.ITERANDO
        
        # Registrar en historial
        state.historial_cambios.append({
            'iteracion': state.iteracion,
            'razon': decision['razon'],
            'volver_a_agente': decision.get('volver_a_agente'),
            'timestamp': datetime.now().isoformat(),
            'problemas_detectados': state.problemas_detectados.copy()
        })
        
        # Determinar desde dónde reiniciar
        agente_inicio = decision.get('volver_a_agente', 'ideador')
        
        # Limpiar estado parcial si es necesario
        state = self._limpiar_estado_parcial(state, agente_inicio)
        
        # Ejecutar desde el agente indicado
        indice_inicio = self.flujo_normal.index(agente_inicio)
        flujo_iteracion = self.flujo_normal[indice_inicio:]
        
        for agente_name in flujo_iteracion:
            agente = self.agentes[agente_name]
            state = agente.procesar(state)
            
            if self._hay_problemas_criticos(state):
                break
        
        # Evaluar resultado de la iteración
        return self._evaluar_resultado_iteracion(state)
    
    def _solicitar_intervencion_humana(self, state: ActividadState, decision: Dict) -> ActividadState:
        """Solicita y maneja intervención humana"""
        
        print(f"\n👤 [{self.name}] Intervención humana requerida")
        print(f"Contexto: {decision['razon']}")
        
        # En una implementación real, aquí se pausaría para input del usuario
        # Por ahora, simularemos diferentes tipos de respuesta
        
        # Mostrar estado actual al usuario
        self._mostrar_resumen_para_usuario(state)
        
        # Solicitar input real del usuario
        respuesta_usuario = self._solicitar_input_usuario(state, decision)
        
        # Procesar respuesta del usuario
        state = self._procesar_respuesta_usuario(state, respuesta_usuario)
        
        return state
    
    def _verificar_completitud(self, state: ActividadState) -> Dict:
        """Verifica si la actividad está completa"""
        
        componentes = {
            'actividad_base': bool(state.actividad_base),
            'adaptaciones_dua': bool(state.adaptaciones_dua),
            'tareas_paralelas': bool(state.tareas_paralelas),
            'validacion_curricular': bool(state.validacion_curricular),
            'recursos_necesarios': bool(state.recursos_necesarios)
        }
        
        completo = all(componentes.values())
        
        return {
            'completo': completo,
            'componentes': componentes,
            'faltantes': [k for k, v in componentes.items() if not v]
        }
    
    def _analizar_problemas(self, state: ActividadState) -> Dict:
        """Analiza y categoriza problemas detectados"""
        
        todos_problemas = state.problemas_detectados
        
        # Categorizar problemas
        criticos = []
        menores = []
        
        for problema in todos_problemas:
            if any(keyword in problema.lower() for keyword in ['crítico', 'rechazada', 'no viable']):
                criticos.append(problema)
            else:
                menores.append(problema)
        
        return {
            'criticos': criticos,
            'menores': menores,
            'total': len(todos_problemas)
        }
    
    def _determinar_agente_responsable(self, problemas_criticos: List[str]) -> str:
        """Determina qué agente debe revisar basado en los problemas"""
        
        # Mapeo de tipos de problemas a agentes responsables
        mapeo_responsabilidad = {
            'curricular': 'ideador',  # Problemas de diseño base
            'dua': 'adaptador_dua',   # Problemas de adaptación
            'tareas': 'arquitecto_tareas',  # Problemas de asignación
            'pedagógico': 'validador_curricular',  # Problemas curriculares
            'tiempo': 'gestor_logistico',  # Problemas logísticos
            'materiales': 'gestor_logistico',
            'espacio': 'gestor_logistico'
        }
        
        # Analizar problemas y determinar responsable más frecuente
        contador_responsables = {}
        
        for problema in problemas_criticos:
            problema_lower = problema.lower()
            
            for tipo_problema, agente in mapeo_responsabilidad.items():
                if tipo_problema in problema_lower:
                    contador_responsables[agente] = contador_responsables.get(agente, 0) + 1
                    break
            else:
                # Si no se identifica, volver al ideador por defecto
                contador_responsables['ideador'] = contador_responsables.get('ideador', 0) + 1
        
        # Retornar el agente con más problemas asignados
        if contador_responsables:
            return max(contador_responsables, key=contador_responsables.get)
        else:
            return 'ideador'  # Default
    
    def _encontrar_primer_agente_incompleto(self, completitud: Dict) -> str:
        """Encuentra el primer agente que no completó su trabajo"""
        
        mapeo_componentes_agentes = {
            'actividad_base': 'ideador',
            'adaptaciones_dua': 'adaptador_dua',
            'tareas_paralelas': 'arquitecto_tareas',
            'validacion_curricular': 'validador_curricular',
            'recursos_necesarios': 'gestor_logistico'
        }
        
        for componente in completitud['faltantes']:
            if componente in mapeo_componentes_agentes:
                return mapeo_componentes_agentes[componente]
        
        return 'ideador'  # Default
    
    def _hay_problemas_criticos(self, state: ActividadState) -> bool:
        """Verifica si hay problemas que requieren parar el pipeline"""
        
        # Verificar validación curricular rechazada
        if state.validacion_curricular:
            if state.validacion_curricular.get('estado_aprobacion') == 'rechazada':
                return True
        
        # Verificar recursos no viables
        if state.recursos_necesarios:
            if not state.recursos_necesarios.get('viable', True):
                return True
        
        # Verificar problemas críticos generales
        if state.problemas_detectados:
            for problema in state.problemas_detectados:
                if 'crítico' in problema.lower() or 'rechazad' in problema.lower():
                    return True
        
        return False
    
    def _limpiar_estado_parcial(self, state: ActividadState, agente_inicio: str) -> ActividadState:
        """Limpia el estado parcial desde el agente de inicio hacia adelante"""
        
        # Mapeo de agentes a campos que deben limpiarse
        limpieza_por_agente = {
            'ideador': ['actividad_base', 'adaptaciones_dua', 'tareas_paralelas', 'validacion_curricular', 'recursos_necesarios'],
            'adaptador_dua': ['adaptaciones_dua', 'tareas_paralelas', 'validacion_curricular', 'recursos_necesarios'],
            'arquitecto_tareas': ['tareas_paralelas', 'validacion_curricular', 'recursos_necesarios'],
            'validador_curricular': ['validacion_curricular', 'recursos_necesarios'],
            'gestor_logistico': ['recursos_necesarios']
        }
        
        campos_a_limpiar = limpieza_por_agente.get(agente_inicio, [])
        
        for campo in campos_a_limpiar:
            if campo == 'actividad_base':
                state.actividad_base = {}
            elif campo == 'adaptaciones_dua':
                state.adaptaciones_dua = []
            elif campo == 'tareas_paralelas':
                state.tareas_paralelas = []
            elif campo == 'validacion_curricular':
                state.validacion_curricular = {}
            elif campo == 'recursos_necesarios':
                state.recursos_necesarios = {}
        
        # Limpiar problemas detectados previos
        state.problemas_detectados = []
        
        return state
    
    def _evaluar_resultado_iteracion(self, state: ActividadState) -> ActividadState:
        """Evalúa el resultado después de una iteración"""
        
        # Verificar si se resolvieron los problemas
        completitud = self._verificar_completitud(state)
        problemas = self._analizar_problemas(state)
        
        if completitud['completo'] and not problemas['criticos']:
            state.estado = EstadoActividad.COMPLETADO
            print(f"✅ Iteración {state.iteracion} exitosa - Actividad completada")
        
        elif state.iteracion >= 3:  # Máximo 3 iteraciones
            state.estado = EstadoActividad.RECHAZADO
            state.problemas_detectados.append("Máximo de iteraciones alcanzado - requiere intervención manual")
            print(f"❌ Máximo de iteraciones alcanzado - actividad marcada como rechazada")
        
        else:
            # Continuar iterando si aún hay problemas
            if problemas['criticos']:
                decision = {
                    'accion': 'iterar',
                    'razon': f"Iteración {state.iteracion} no resolvió problemas críticos",
                    'volver_a_agente': self._determinar_agente_responsable(problemas['criticos'])
                }
                return self._manejar_iteracion(state, decision)
        
        return state
    
    def _mostrar_resumen_para_usuario(self, state: ActividadState):
        """Muestra resumen del estado actual para el usuario"""
        print("\n" + "="*60)
        print("📋 RESUMEN DE ACTIVIDAD PARA REVISIÓN")
        print("="*60)
        
        if state.actividad_base:
            print(f"Título: {state.actividad_base.get('titulo', 'Sin título')}")
            print(f"Duración: {state.actividad_base.get('duracion', 'Sin especificar')}")
            print(f"Objetivo: {state.actividad_base.get('objetivo_pedagogico', 'Sin objetivo')}")
        
        if state.tareas_paralelas:
            print(f"\nTareas paralelas: {len(state.tareas_paralelas)}")
            for i, tarea in enumerate(state.tareas_paralelas[:3]):  # Mostrar solo primeras 3
                print(f"  {i+1}. {tarea.get('nombre', 'Sin nombre')}: {tarea.get('estudiantes', 'Sin asignar')}")
        
        if state.problemas_detectados:
            print(f"\n⚠️  Problemas detectados ({len(state.problemas_detectados)}):")
            for problema in state.problemas_detectados[:5]:  # Mostrar solo primeros 5
                print(f"  - {problema}")
        
        print("="*60)
    
    def _solicitar_input_usuario(self, state: ActividadState, decision: Dict) -> Dict:
        """Solicita input real del usuario"""
        
        print("\n🤔 ¿Qué deseas hacer?")
        print("1. Continuar con la actividad tal como está")
        print("2. Hacer cambios específicos") 
        print("3. Reiniciar desde otro punto")
        print("4. Aprobar actividad final")
        
        try:
            choice = input("Selecciona una opción (1-4): ").strip()
            
            if choice == "1":
                return {
                    'accion': 'continuar',
                    'feedback': 'Usuario decidió continuar'
                }
            elif choice == "2":
                return self._solicitar_cambios_especificos(state)
            elif choice == "3":
                return self._solicitar_reinicio(state)
            elif choice == "4":
                return {
                    'accion': 'aprobar',
                    'feedback': 'Usuario aprobó la actividad final'
                }
            else:
                print("❌ Opción no válida, continuando...")
                return {
                    'accion': 'continuar',
                    'feedback': 'Opción inválida, continuar por defecto'
                }
        except KeyboardInterrupt:
            print("\n❌ Proceso interrumpido por el usuario")
            return {
                'accion': 'aprobar',
                'feedback': 'Proceso interrumpido, aprobar estado actual'
            }
    
    def _solicitar_cambios_especificos(self, state: ActividadState) -> Dict:
        """Permite al usuario especificar cambios"""
        print("\n📝 ¿Qué tipo de cambios deseas hacer?")
        print("1. Cambiar duración (minutos)")
        print("2. Modificar materiales")
        print("3. Ajustar nivel de dificultad")
        print("4. Otros cambios")
        
        choice = input("Tipo de cambio (1-4): ").strip()
        
        if choice == "1":
            try:
                nueva_duracion = int(input("Nueva duración en minutos: "))
                return {
                    'accion': 'modificar_restricciones',
                    'cambios': {'duracion_max': nueva_duracion},
                    'feedback': f'Usuario cambió duración a {nueva_duracion} minutos'
                }
            except ValueError:
                print("❌ Duración inválida, manteniendo original")
        elif choice == "2":
            nuevos_materiales = input("Nuevos materiales disponibles: ").strip()
            if nuevos_materiales:
                return {
                    'accion': 'modificar_restricciones', 
                    'cambios': {'materiales': nuevos_materiales},
                    'feedback': f'Usuario cambió materiales: {nuevos_materiales}'
                }
        elif choice == "3":
            print("1. Más fácil  2. Más difícil  3. Mantener nivel")
            nivel = input("Ajuste de dificultad (1-3): ").strip()
            if nivel in ["1", "2"]:
                ajuste = "más_facil" if nivel == "1" else "más_dificil"
                return {
                    'accion': 'ajustar_dificultad',
                    'cambios': {'dificultad': ajuste},
                    'feedback': f'Usuario solicitó actividad {ajuste.replace("_", " ")}'
                }
        
        # Fallback
        return {
            'accion': 'continuar',
            'feedback': 'Usuario no especificó cambios válidos'
        }
    
    def _solicitar_reinicio(self, state: ActividadState) -> Dict:
        """Permite al usuario reiniciar desde un punto específico"""
        print("\n🔄 ¿Desde dónde deseas reiniciar?")
        print("1. Desde el diseño inicial")
        print("2. Desde adaptaciones DUA")
        print("3. Desde arquitectura de tareas")
        
        choice = input("Punto de reinicio (1-3): ").strip()
        
        puntos_reinicio = {
            "1": "ideador",
            "2": "adaptador_dua", 
            "3": "arquitecto_tareas"
        }
        
        agente = puntos_reinicio.get(choice, "ideador")
        
        return {
            'accion': 'reiniciar',
            'desde_agente': agente,
            'feedback': f'Usuario solicitó reiniciar desde {agente}'
        }
    
    def _procesar_respuesta_usuario(self, state: ActividadState, respuesta: Dict) -> ActividadState:
        """Procesa la respuesta del usuario y actualiza el estado"""
        
        accion = respuesta.get('accion', 'aprobar')
        
        if accion == 'aprobar':
            state.estado = EstadoActividad.COMPLETADO
            state.feedback_profesor.append(f"Usuario aprobó en iteración {state.iteracion}")
            
        elif accion == 'modificar_restricciones':
            # Actualizar restricciones según el feedback del usuario
            cambios = respuesta.get('cambios', {})
            state.restricciones.update(cambios)
            
            feedback = respuesta.get('feedback', 'Usuario solicitó cambios')
            state.feedback_profesor.append(feedback)
            
            # Marcar que necesita re-evaluar desde gestor logístico
            state = self._manejar_iteracion(state, {
                'accion': 'iterar',
                'razon': 'Usuario modificó restricciones',
                'volver_a_agente': 'gestor_logistico'
            })
            
        elif accion == 'continuar_con_cambios':
            # Continuar a pesar de problemas menores
            state.estado = EstadoActividad.COMPLETADO
            feedback = respuesta.get('feedback', 'Usuario aceptó con cambios menores')
            state.feedback_profesor.append(feedback)
        
        # Reset flag de necesita input
        state.necesita_human_input = False
        
        return state


class SistemaMultiAgenteCompleto:
    """Sistema completo que coordina la generación de actividades educativas"""
    
    def __init__(self):
        self.orquestador = OrquestadorAgent()
        
    def generar_actividad(self, tema: str, perfiles_estudiantes: Dict, restricciones: Dict = None) -> ActividadState:
        """Método principal para generar una actividad educativa completa"""
        
        # Crear estado inicial
        state_inicial = ActividadState(
            tema=tema,
            perfiles_estudiantes=perfiles_estudiantes,
            restricciones=restricciones or {}
        )
        
        print(f"\n🚀 Iniciando generación de actividad: '{tema}'")
        
        # Procesar a través del orquestador
        state_final = self.orquestador.procesar(state_inicial)
        
        # Mostrar resultado final
        self._mostrar_resultado_final(state_final)
        
        return state_final
    
    def _mostrar_resultado_final(self, state: ActividadState):
        """Muestra el resultado final del proceso"""
        print("\n" + "="*70)
        print("🎯 RESULTADO FINAL")
        print("="*70)
        
        print(f"Estado: {state.estado.value.upper()}")
        print(f"Iteraciones: {state.iteracion}")
        
        if state.estado == EstadoActividad.COMPLETADO:
            print("✅ Actividad generada exitosamente")
            
            if state.actividad_base:
                print(f"\n📚 Actividad: {state.actividad_base.get('titulo', 'Sin título')}")
                print(f"Duración: {state.actividad_base.get('duracion', 'Sin especificar')}")
            
            if state.tareas_paralelas:
                print(f"\n👥 Tareas paralelas: {len(state.tareas_paralelas)} definidas")
                
            if state.adaptaciones_dua:
                individuales = len([a for a in state.adaptaciones_dua if a.get('tipo') == 'individual'])
                print(f"🎭 Adaptaciones: {individuales} estudiantes con adaptaciones específicas")
            
        elif state.estado == EstadoActividad.RECHAZADO:
            print("❌ No se pudo generar actividad viable")
            if state.problemas_detectados:
                print(f"Problemas finales ({len(state.problemas_detectados)}):")
                for problema in state.problemas_detectados[-3:]:  # Mostrar últimos 3
                    print(f"  - {problema}")
        
        if state.feedback_profesor:
            print(f"\n💬 Feedback del profesor: {len(state.feedback_profesor)} intervenciones")
            
        print("="*70)


# Actualizar el main para usar el sistema completo
if __name__ == "__main__":
    # Test del sistema completo
    print("🎯 Sistema Multi-Agente para Actividades Educativas")
    print("=" * 50)
    
    # Perfiles de ejemplo completos
    perfiles_test = {
        "estudiantes": [
            {"nombre": "ALEX M.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "nivel_apoyo": "bajo", "temperamento": "reflexivo", "agrupamiento_optimo": "individual", "tolerancia_frustracion": "alta"},
            {"nombre": "ELENA R.", "diagnostico_formal": "TEA_nivel_1", "canal_preferido": "visual", "nivel_apoyo": "alto", "temperamento": "reflexivo", "agrupamiento_optimo": "individual", "tolerancia_frustracion": "baja", "necesidades_especiales": ["rutinas_claras", "instrucciones_visuales"]},
            {"nombre": "LUIS T.", "diagnostico_formal": "TDAH_combinado", "canal_preferido": "kinestésico", "nivel_apoyo": "alto", "temperamento": "impulsivo", "agrupamiento_optimo": "grupos", "tolerancia_frustracion": "baja", "necesidades_especiales": ["descansos_frecuentes", "actividades_físicas"]},
            {"nombre": "ANA V.", "diagnostico_formal": "altas_capacidades", "canal_preferido": "auditivo", "nivel_apoyo": "bajo", "temperamento": "reflexivo", "agrupamiento_optimo": "individual", "tolerancia_frustracion": "baja", "necesidades_especiales": ["retos_intelectuales"]},
            {"nombre": "MARÍA L.", "diagnostico_formal": "ninguno", "canal_preferido": "auditivo", "nivel_apoyo": "medio", "temperamento": "reflexivo", "agrupamiento_optimo": "grupos", "tolerancia_frustracion": "media"},
            {"nombre": "SARA M.", "diagnostico_formal": "ninguno", "canal_preferido": "auditivo", "nivel_apoyo": "medio", "temperamento": "equilibrado", "agrupamiento_optimo": "grupos", "tolerancia_frustracion": "media"},
            {"nombre": "EMMA K.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "nivel_apoyo": "medio", "temperamento": "reflexivo", "agrupamiento_optimo": "individual", "tolerancia_frustracion": "baja"},
            {"nombre": "HUGO P.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "nivel_apoyo": "bajo", "temperamento": "equilibrado", "agrupamiento_optimo": "individual", "tolerancia_frustracion": "alta"}
        ]
    }
    
    # Crear sistema
    sistema = SistemaMultiAgenteCompleto()
    
    # Generar actividad
    resultado = sistema.generar_actividad(
        tema="Fracciones equivalentes",
        perfiles_estudiantes=perfiles_test,
        restricciones={
            "duracion_max": 45,
            "materiales": "básicos",
            "espacio_amplio": False
        }
    )

#!/usr/bin/env python3
"""
Sistema Multi-Agente para Generación de Actividades Educativas Adaptadas
Implementación basada en el flujo pedagógico diseñado
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SistemaAgentesInteligente")

# Importar integrador de Ollama
try:
    from ollama_api_integrator import OllamaAPIEducationGenerator
    logger.info("✅ Ollama integrator importado correctamente")
except ImportError:
    logger.error("❌ No se pudo importar OllamaAPIEducationGenerator")
    OllamaAPIEducationGenerator = None

class EstadoActividad(Enum):
    INICIANDO = "iniciando"
    EN_PROCESO = "en_proceso"  
    VALIDANDO = "validando"
    ITERANDO = "iterando"
    COMPLETADO = "completado"
    RECHAZADO = "rechazado"

@dataclass
class ActividadState:
    """Estado compartido entre todos los agentes"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    iteracion: int = 1
    estado: EstadoActividad = EstadoActividad.INICIANDO
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Inputs iniciales
    tema: str = ""
    perfiles_estudiantes: Dict = field(default_factory=dict)
    restricciones: Dict = field(default_factory=dict)
    
    # Contenido generado por agentes
    actividad_base: Dict = field(default_factory=dict)
    adaptaciones_dua: List[Dict] = field(default_factory=list)
    tareas_paralelas: List[Dict] = field(default_factory=list)
    validacion_curricular: Dict = field(default_factory=dict)
    recursos_necesarios: Dict = field(default_factory=dict)
    
    # Feedback y control
    feedback_profesor: List[str] = field(default_factory=list)
    historial_cambios: List[Dict] = field(default_factory=list)
    problemas_detectados: List[str] = field(default_factory=list)
    
    # Control de flujo
    agente_actual: str = ""
    necesita_human_input: bool = False
    
class BaseAgent:
    """Clase base para todos los agentes del sistema"""
    
    # Configuración global de Ollama
    _ollama_instance = None
    _ollama_config = {
        'host': '192.168.1.10',
        'port': 11434,
        'model': 'llama3.2'
    }
    
    def __init__(self, name: str, llm_required: bool = True, model_override: str = None):
        self.name = name
        self.llm_required = llm_required
        self.model = model_override or self._ollama_config['model']
        
        # Inicializar conexión Ollama si es necesario
        if self.llm_required and BaseAgent._ollama_instance is None:
            self._init_ollama()
        
    @classmethod
    def _init_ollama(cls):
        """Inicializa la conexión con Ollama una sola vez"""
        if OllamaAPIEducationGenerator is None:
            logger.error("❌ OllamaAPIEducationGenerator no disponible")
            return
            
        try:
            cls._ollama_instance = OllamaAPIEducationGenerator(
                host=cls._ollama_config['host'],
                port=cls._ollama_config['port'],
                model_name=cls._ollama_config['model']
            )
            logger.info(f"✅ Conexión Ollama establecida: {cls._ollama_config['host']}:{cls._ollama_config['port']}")
        except Exception as e:
            logger.error(f"❌ Error conectando con Ollama: {e}")
            cls._ollama_instance = None
    
    def procesar(self, state: ActividadState) -> ActividadState:
        """Método principal que cada agente debe implementar"""
        raise NotImplementedError
        
    def validar_inputs(self, state: ActividadState) -> Tuple[bool, str]:
        """Valida que los inputs necesarios estén disponibles"""
        return True, ""
    
    def llamar_llm(self, prompt: str, **kwargs) -> str:
        """Llamada real a LLM usando Ollama"""
        print(f"\n🤖 [{self.name}] Consultando LLM...")
        print(f"PROMPT: {prompt[:200]}...")
        
        if BaseAgent._ollama_instance is None:
            logger.warning(f"⚠️ [{self.name}] Ollama no disponible, usando respuesta simulada")
            return self._get_fallback_response(prompt, **kwargs)
        
        try:
            # Configurar parámetros
            max_tokens = kwargs.get('max_tokens', 500)
            temperature = kwargs.get('temperature', 0.7)
            
            # Generar respuesta con Ollama
            respuesta = BaseAgent._ollama_instance.generar_texto(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"✅ [{self.name}] Respuesta LLM generada ({len(respuesta)} chars)")
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ [{self.name}] Error llamando LLM: {e}")
            return self._get_fallback_response(prompt, **kwargs)
    
    def _get_fallback_response(self, prompt: str, **kwargs) -> str:
        """Respuesta de fallback cuando Ollama no está disponible"""
        return f"[FALLBACK] Respuesta simulada para {self.name} - Ollama no disponible"

class IdeadorAgent(BaseAgent):
    """Agente que genera la idea principal de la actividad"""
    
    def __init__(self):
        super().__init__("Ideador", llm_required=True)
        
    def procesar(self, state: ActividadState) -> ActividadState:
        """Genera la actividad base siguiendo el proceso pedagógico del usuario"""
        
        # Actualizar estado
        state.agente_actual = self.name
        state.estado = EstadoActividad.EN_PROCESO
        
        # Construir prompt con el proceso pedagógico
        prompt = self._construir_prompt_ideador(state)
        
        # Llamar a LLM
        respuesta = self.llamar_llm(prompt, temperatura=0.8)
        
        # Parsear respuesta y actualizar estado
        actividad_generada = self._parsear_respuesta_ideador(respuesta)
        state.actividad_base = actividad_generada
        
        # Log del proceso
        self._log_proceso(state, respuesta)
        
        return state
    
    def _construir_prompt_ideador(self, state: ActividadState) -> str:
        """Construye el prompt siguiendo el proceso mental del usuario"""
        
        # Few-shot examples de las actividades exitosas del usuario
        ejemplos_exitosos = self._get_ejemplos_exitosos()
        
        # Análisis de perfiles para diseñar apropiadamente
        analisis_grupo = self._analizar_perfiles_grupo(state.perfiles_estudiantes)
        
        prompt = f"""
PROCESO_PEDAGOGICO_EXPERTO:

Tu tarea es generar una actividad educativa siguiendo este proceso mental de un pedagogo experto:

1. ANÁLISIS_CONCEPTO: ¿Qué hace difícil este concepto para estudiantes de 9-10 años?
2. ANÁLISIS_GRUPO: ¿Qué características tiene este grupo específico?
3. INSIGHT_PEDAGOGICO: ¿Cómo hacer este concepto tangible, considerando las necesidades del grupo?
4. DISEÑO_ACTIVIDAD: Crear actividad que permita trabajo paralelo y colaborativo
5. IDENTIFICACIÓN_TAREAS: ¿Qué subtareas pueden realizarse simultáneamente?

CONTEXTO:
- Tema: {state.tema}
- Estudiantes: 8 niños de 4º primaria (edad 9-10 años)
- Duración típica: 45-60 minutos

ANÁLISIS_DEL_GRUPO_ACTUAL:
{analisis_grupo}

EJEMPLOS_DE_ACTIVIDADES_EXITOSAS:
{ejemplos_exitosos}

RESTRICCIONES_ACTUALES:
{json.dumps(state.restricciones, indent=2) if state.restricciones else "Ninguna restricción específica"}

FEEDBACK_PREVIO_DEL_PROFESOR:
{chr(10).join(state.feedback_profesor) if state.feedback_profesor else "Sin feedback previo"}

RESPONDE EN ESTE FORMATO:

ANÁLISIS_CONCEPTO:
[¿Por qué es difícil este concepto? ¿Dónde suelen fallar los estudiantes?]

ANÁLISIS_GRUPO:
[¿Qué oportunidades y desafíos presenta este grupo específico?]

INSIGHT_PEDAGOGICO:
[¿Cómo hacer este concepto tangible considerando las características del grupo?]

ACTIVIDAD_PROPUESTA:
Título: [nombre atractivo]
Duración: [tiempo en minutos]
Descripción: [explicación clara de la actividad general, considerando las necesidades del grupo]

TAREAS_IDENTIFICADAS:
[Lista de 3-4 subtareas que pueden realizarse en paralelo, pensando en los perfiles disponibles]
1. Tarea A: [descripción] - Perfil ideal: [visual/auditivo/kinestésico, nivel de apoyo]
2. Tarea B: [descripción] - Perfil ideal: [visual/auditivo/kinestésico, nivel de apoyo]
3. Tarea C: [descripción] - Perfil ideal: [visual/auditivo/kinestésico, nivel de apoyo]

MATERIALES_BÁSICOS:
[Lista de materiales necesarios]

OBJETIVO_PEDAGOGICO:
[¿Qué van a aprender exactamente?]
"""
        
        return prompt
    
    def _analizar_perfiles_grupo(self, perfiles: Dict) -> str:
        """Analiza los perfiles de estudiantes para informar el diseño de la actividad"""
        if not perfiles or 'estudiantes' not in perfiles:
            return "Sin información de perfiles disponible"
            
        estudiantes = perfiles['estudiantes']
        
        # Contadores para análisis
        diagnosticos = {}
        canales = {}
        niveles_apoyo = {}
        temperamentos = {}
        agrupamientos = {}
        
        for est in estudiantes:
            # Contar diagnósticos
            diag = est.get('diagnostico_formal', 'ninguno')
            diagnosticos[diag] = diagnosticos.get(diag, 0) + 1
            
            # Contar canales preferidos
            canal = est.get('canal_preferido', 'no_especificado')
            canales[canal] = canales.get(canal, 0) + 1
            
            # Contar niveles de apoyo
            apoyo = est.get('nivel_apoyo', 'no_especificado')
            niveles_apoyo[apoyo] = niveles_apoyo.get(apoyo, 0) + 1
            
            # Contar temperamentos
            temp = est.get('temperamento', 'no_especificado')
            temperamentos[temp] = temperamentos.get(temp, 0) + 1
            
            # Contar preferencias de agrupamiento
            grup = est.get('agrupamiento_optimo', 'no_especificado')
            agrupamientos[grup] = agrupamientos.get(grup, 0) + 1
        
        analisis = f"""
COMPOSICIÓN DEL GRUPO ({len(estudiantes)} estudiantes):

Diagnósticos especiales:
{self._format_dict_counts(diagnosticos)}

Canales de aprendizaje preferidos:
{self._format_dict_counts(canales)}

Niveles de apoyo necesarios:
{self._format_dict_counts(niveles_apoyo)}

Temperamentos:
{self._format_dict_counts(temperamentos)}

Preferencias de agrupamiento:
{self._format_dict_counts(agrupamientos)}

IMPLICACIONES PARA EL DISEÑO:
- Diversidad de canales: Necesita actividad multi-sensorial
- Necesidades especiales: {self._get_necesidades_especiales_resumen(estudiantes)}
- Tolerancia frustración: {self._get_tolerancia_frustracion_resumen(estudiantes)}
- Agrupamiento: {self._get_estrategia_agrupamiento(agrupamientos)}
"""
        return analisis
    
    def _format_dict_counts(self, dict_counts: Dict) -> str:
        """Formatea un diccionario de conteos para el análisis"""
        return ", ".join([f"{k}: {v}" for k, v in dict_counts.items()])
    
    def _get_necesidades_especiales_resumen(self, estudiantes: List[Dict]) -> str:
        """Resume las necesidades especiales del grupo"""
        especiales = []
        for est in estudiantes:
            diag = est.get('diagnostico_formal', 'ninguno')
            if diag != 'ninguno':
                nombre = est.get('nombre', 'Estudiante')
                especiales.append(f"{nombre}({diag})")
        
        return ", ".join(especiales) if especiales else "Sin diagnósticos especiales"
    
    def _get_tolerancia_frustracion_resumen(self, estudiantes: List[Dict]) -> str:
        """Resume la tolerancia a la frustración del grupo"""
        bajas = sum(1 for est in estudiantes if est.get('tolerancia_frustracion') == 'baja')
        if bajas >= len(estudiantes) // 2:
            return "Mayoría con baja tolerancia - necesita éxito temprano y tareas cortas"
        elif bajas > 0:
            return f"{bajas} estudiantes con baja tolerancia - incluir opciones de diferente dificultad"
        else:
            return "Buena tolerancia general - permite retos más complejos"
    
    def _get_estrategia_agrupamiento(self, agrupamientos: Dict) -> str:
        """Sugiere estrategia de agrupamiento basada en preferencias"""
        individual = agrupamientos.get('individual', 0)
        grupos = agrupamientos.get('grupos', 0)
        
        if individual > grupos:
            return "Mayoría prefiere trabajo individual - diseñar tareas paralelas individuales"
        elif grupos > individual:
            return "Mayoría prefiere trabajo grupal - incluir colaboración y roles complementarios"
        else:
            return "Grupo mixto - combinar fases individuales y colaborativas"
    
    def _get_ejemplos_exitosos(self) -> str:
        """Devuelve los ejemplos exitosos del usuario como few-shot"""
        return """
EJEMPLO 1 - Sumas con llevadas:
- Concepto difícil: El abstracto "me llevo 1"
- Insight: Representación física con intercambio real
- Actividad: 6 estudiantes como dígitos, intercambian materiales físicos
- Tareas paralelas: Preparar mesas, hacer paquetes, calcular individual
- Resultado: Entendimiento físico del concepto

EJEMPLO 2 - Fábrica de fracciones:
- Concepto difícil: ¿Qué es una fracción? ¿Qué significa 1?
- Insight: Fraccionamiento como proceso físico
- Actividad: Estaciones de fraccionamiento con rotaciones
- Tareas paralelas: Elegir objetos, decidir fraccionamiento, ejecutar, clasificar
- Resultado: Comprensión vivencial de fracciones
"""
    
    def _parsear_respuesta_ideador(self, respuesta: str) -> Dict:
        """Extrae la información estructurada de la respuesta del LLM"""
        
        # Usar regex para extraer secciones
        secciones = {}
        
        patrones = {
            'analisis_concepto': r'ANÁLISIS_CONCEPTO:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'analisis_grupo': r'ANÁLISIS_GRUPO:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'insight_pedagogico': r'INSIGHT_PEDAGOGICO:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'titulo': r'Título:\s*(.*?)(?=\n|$)',
            'duracion': r'Duración:\s*(.*?)(?=\n|$)',
            'descripcion': r'Descripción:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'tareas': r'TAREAS_IDENTIFICADAS:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'materiales': r'MATERIALES_BÁSICOS:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)',
            'objetivo': r'OBJETIVO_PEDAGOGICO:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ_]+:|$)'
        }
        
        for key, patron in patrones.items():
            match = re.search(patron, respuesta, re.DOTALL | re.MULTILINE)
            if match:
                secciones[key] = match.group(1).strip()
            else:
                secciones[key] = ""
        
        return {
            'analisis_concepto': secciones['analisis_concepto'],
            'analisis_grupo': secciones['analisis_grupo'],
            'insight_pedagogico': secciones['insight_pedagogico'],
            'titulo': secciones['titulo'],
            'duracion': secciones['duracion'],
            'descripcion': secciones['descripcion'],
            'tareas_identificadas': secciones['tareas'],
            'materiales_basicos': secciones['materiales'],
            'objetivo_pedagogico': secciones['objetivo'],
            'respuesta_completa': respuesta
        }
    
    def _log_proceso(self, state: ActividadState, respuesta: str):
        """Registra el proceso para debugging"""
        print(f"\n✅ [{self.name}] Actividad base generada")
        print(f"Título: {state.actividad_base.get('titulo', 'Sin título')}")
        print(f"Duración: {state.actividad_base.get('duracion', 'Sin especificar')}")

class AdaptadorDUAAgent(BaseAgent):
    """Agente que convierte adaptaciones DUA genéricas en acciones específicas"""
    
    def __init__(self):
        super().__init__("AdaptadorDUA", llm_required=True)
        
    def procesar(self, state: ActividadState) -> ActividadState:
        """Traduce el DUA genérico a acciones concretas para esta actividad específica"""
        
        # Validar que tenemos la actividad base
        is_valid, msg = self.validar_inputs(state)
        if not is_valid:
            state.problemas_detectados.append(f"AdaptadorDUA: {msg}")
            return state
            
        # Actualizar estado
        state.agente_actual = self.name
        
        # Construir prompt específico para adaptaciones DUA
        prompt = self._construir_prompt_adaptaciones(state)
        
        # Llamar a LLM
        respuesta = self.llamar_llm(prompt, temperatura=0.7)
        
        # Parsear y actualizar adaptaciones
        adaptaciones_generadas = self._parsear_adaptaciones(respuesta)
        state.adaptaciones_dua = adaptaciones_generadas
        
        # Log del proceso
        self._log_proceso(state, len(adaptaciones_generadas))
        
        return state
    
    def validar_inputs(self, state: ActividadState) -> Tuple[bool, str]:
        """Valida que tenemos la actividad base para adaptar"""
        if not state.actividad_base:
            return False, "Se necesita actividad base del Ideador"
        
        if not state.perfiles_estudiantes:
            return False, "Se necesitan perfiles de estudiantes para adaptar"
            
        return True, ""
    
    def _construir_prompt_adaptaciones(self, state: ActividadState) -> str:
        """Construye prompt para convertir DUA genérico en acciones específicas"""
        
        # Extraer estudiantes con necesidades especiales
        estudiantes_especiales = self._identificar_necesidades_especiales(state.perfiles_estudiantes)
        
        # Extraer actividad actual
        actividad = state.actividad_base
        
        prompt = f"""
ESPECIALISTA_DUA_CONCRETO:

Tu función es TRADUCIR adaptaciones DUA genéricas en ACCIONES ESPECÍFICAS para esta actividad concreta.

NO digas "dar apoyo visual" → SÍ especifica "escribir los 3 pasos en la pizarra"
NO digas "permitir descansos" → SÍ especifica "rotación cada 15 min entre estaciones"

ACTIVIDAD_A_ADAPTAR:
Título: {actividad.get('titulo', '')}
Descripción: {actividad.get('descripcion', '')}
Tareas identificadas: {actividad.get('tareas_identificadas', '')}
Duración: {actividad.get('duracion', '')}

ESTUDIANTES_CON_NECESIDADES_ESPECÍFICAS:
{estudiantes_especiales}

EJEMPLOS_DE_ADAPTACIONES_CONCRETAS_EXITOSAS:
{self._get_ejemplos_adaptaciones_concretas()}

PRINCIPIOS_PARA_ADAPTACIONES_CONCRETAS:
- TEA: Secuencias visuales paso a paso, rutinas predecibles
- TDAH: Tareas cortas con movimiento, feedback inmediato
- Altas capacidades: Extensiones y retos adicionales
- Baja tolerancia frustración: Éxito temprano, pasos pequeños

RESPONDE EN ESTE FORMATO:

ADAPTACIONES_ESPECÍFICAS:

Para [NOMBRE_ESTUDIANTE] ([DIAGNÓSTICO]):
- Acción_concreta_1: [descripción específica de QUÉ hacer exactamente]
- Acción_concreta_2: [descripción específica de QUÉ hacer exactamente]
- Material_de_apoyo: [si necesita algo específico]

[Repite para cada estudiante con necesidades especiales]

ADAPTACIONES_GRUPALES:
- Modificación_1: [cambio específico en la actividad general]
- Modificación_2: [cambio específico en la actividad general]

SEÑALES_DE_ALERTA_A_OBSERVAR:
- [Qué observar en cada estudiante para saber si funciona]
"""
        
        return prompt
    
    def _identificar_necesidades_especiales(self, perfiles: Dict) -> str:
        """Identifica estudiantes con necesidades de adaptación específicas"""
        if not perfiles or 'estudiantes' not in perfiles:
            return "Sin información de perfiles"
            
        estudiantes_especiales = []
        
        for est in perfiles['estudiantes']:
            necesidades = []
            
            # Diagnósticos formales
            diag = est.get('diagnostico_formal', 'ninguno')
            if diag != 'ninguno':
                necesidades.append(f"Diagnóstico: {diag}")
            
            # Nivel de apoyo alto
            if est.get('nivel_apoyo') == 'alto':
                necesidades.append("Apoyo alto requerido")
                
            # Baja tolerancia a frustración
            if est.get('tolerancia_frustracion') == 'baja':
                necesidades.append("Baja tolerancia frustración")
                
            # Necesidades especiales explícitas
            if 'necesidades_especiales' in est:
                necesidades.extend(est['necesidades_especiales'])
            
            if necesidades:
                nombre = est.get('nombre', 'Estudiante')
                canal = est.get('canal_preferido', 'no especificado')
                temperamento = est.get('temperamento', 'no especificado')
                
                info = f"""
{nombre}:
- Canal preferido: {canal}
- Temperamento: {temperamento}
- Necesidades: {', '.join(necesidades)}
"""
                estudiantes_especiales.append(info)
        
        return '\n'.join(estudiantes_especiales) if estudiantes_especiales else "Sin necesidades especiales identificadas"
    
    def _get_ejemplos_adaptaciones_concretas(self) -> str:
        """Ejemplos reales de adaptaciones específicas exitosas"""
        return """
EJEMPLO_TEA (Elena):
❌ Genérico: "Dar apoyo visual"
✅ Específico: "Crear cartel con secuencia: 1)Tomar fracción 2)Buscar equivalente 3)Verificar con compañero 4)Pegar en mural"

EJEMPLO_TDAH (Luis):  
❌ Genérico: "Permitir movimiento"
✅ Específico: "Rol de coordinador: caminar entre estaciones cada 10min para recoger resultados y llevar a siguiente estación"

EJEMPLO_ALTAS_CAPACIDADES (Ana):
❌ Genérico: "Dar retos adicionales"  
✅ Específico: "Después de completar su estación, crear 3 fracciones equivalentes complejas (con números mayores a 20) para otros grupos"
"""
    
    def _parsear_adaptaciones(self, respuesta: str) -> List[Dict]:
        """Extrae las adaptaciones específicas de la respuesta"""
        adaptaciones = []
        
        # Buscar secciones de adaptaciones individuales
        patron_individual = r'Para ([^(]+)\(([^)]+)\):(.*?)(?=Para [^(]+\(|ADAPTACIONES_GRUPALES:|SEÑALES_DE_ALERTA|$)'
        matches_individuales = re.findall(patron_individual, respuesta, re.DOTALL)
        
        for nombre, diagnostico, contenido in matches_individuales:
            acciones = []
            # Extraer acciones específicas (líneas que empiezan con -)
            lineas_accion = re.findall(r'- ([^:]+): (.+)', contenido)
            
            for tipo_accion, descripcion in lineas_accion:
                acciones.append({
                    'tipo': tipo_accion.strip(),
                    'descripcion': descripcion.strip()
                })
            
            adaptaciones.append({
                'estudiante': nombre.strip(),
                'diagnostico': diagnostico.strip(),
                'acciones_especificas': acciones,
                'tipo': 'individual'
            })
        
        # Buscar adaptaciones grupales
        patron_grupal = r'ADAPTACIONES_GRUPALES:(.*?)(?=SEÑALES_DE_ALERTA|$)'
        match_grupal = re.search(patron_grupal, respuesta, re.DOTALL)
        
        if match_grupal:
            contenido_grupal = match_grupal.group(1)
            modificaciones = re.findall(r'- ([^:]+): (.+)', contenido_grupal)
            
            if modificaciones:
                adaptaciones.append({
                    'tipo': 'grupal',
                    'modificaciones': [
                        {'tipo': mod[0].strip(), 'descripcion': mod[1].strip()}
                        for mod in modificaciones
                    ]
                })
        
        return adaptaciones
    
    def _log_proceso(self, state: ActividadState, num_adaptaciones: int):
        """Log del proceso de adaptaciones"""
        print(f"\n✅ [{self.name}] Adaptaciones específicas generadas")
        print(f"Total adaptaciones: {num_adaptaciones}")
        
        # Mostrar resumen de adaptaciones individuales
        individuales = [a for a in state.adaptaciones_dua if a.get('tipo') == 'individual']
        if individuales:
            print("Estudiantes adaptados:")
            for adapt in individuales:
                print(f"  - {adapt['estudiante']}: {len(adapt.get('acciones_especificas', []))} acciones")


class ArquitectoTareasAgent(BaseAgent):
    """Agente que descompone la actividad en tareas paralelas y las asigna estratégicamente"""
    
    def __init__(self):
        super().__init__("ArquitectoTareas", llm_required=True)
        
    def procesar(self, state: ActividadState) -> ActividadState:
        """Crea arquitectura de tareas paralelas con asignaciones estratégicas"""
        
        # Validar inputs
        is_valid, msg = self.validar_inputs(state)
        if not is_valid:
            state.problemas_detectados.append(f"ArquitectoTareas: {msg}")
            return state
        
        # Actualizar estado
        state.agente_actual = self.name
        
        # Construir prompt para arquitectura de tareas
        prompt = self._construir_prompt_arquitectura(state)
        
        # Llamar a LLM
        respuesta = self.llamar_llm(prompt, temperatura=0.6)
        
        # Parsear y actualizar tareas
        tareas_generadas = self._parsear_tareas_paralelas(respuesta)
        state.tareas_paralelas = tareas_generadas
        
        # Log del proceso
        self._log_proceso(state, len(tareas_generadas))
        
        return state
    
    def validar_inputs(self, state: ActividadState) -> Tuple[bool, str]:
        """Valida que tenemos la información necesaria"""
        if not state.actividad_base:
            return False, "Se necesita actividad base del Ideador"
        
        if not state.perfiles_estudiantes:
            return False, "Se necesitan perfiles para asignar tareas"
            
        return True, ""
    
    def _construir_prompt_arquitectura(self, state: ActividadState) -> str:
        """Construye prompt para crear arquitectura de tareas paralelas"""
        
        # Información de estudiantes
        resumen_estudiantes = self._crear_resumen_estudiantes(state.perfiles_estudiantes)
        
        # Adaptaciones ya definidas
        adaptaciones_resumen = self._resumir_adaptaciones(state.adaptaciones_dua)
        
        prompt = f"""
ARQUITECTO_DE_TAREAS_PARALELAS:

Tu función es diseñar la ESTRUCTURA OPERATIVA de la actividad, dividiendo en tareas que pueden ejecutarse SIMULTÁNEAMENTE en el aula.

ACTIVIDAD_BASE:
{state.actividad_base.get('titulo', '')}
{state.actividad_base.get('descripcion', '')}

ESTUDIANTES_DISPONIBLES (8 total):
{resumen_estudiantes}

ADAPTACIONES_YA_DEFINIDAS:
{adaptaciones_resumen}

PRINCIPIOS_PARA_TAREAS_PARALELAS:
1. Máximo 2-3 estudiantes por tarea (permite supervisión)
2. Tareas interdependientes pero ejecutables en paralelo
3. Roles que aprovechan fortalezas individuales
4. Puntos de sincronización para compartir resultados
5. Cada tarea debe tener resultado tangible para el objetivo común

EJEMPLOS_DE_ARQUITECTURAS_EXITOSAS:
{self._get_ejemplos_arquitecturas()}

RESPONDE EN ESTE FORMATO:

ARQUITECTURA_DE_TAREAS:

FASE_PREPARACIÓN (15 min):
Tarea_1: [nombre_tarea]
- Estudiantes: [nombres específicos y por qué son ideales]
- Función: [qué hacen exactamente]
- Resultado: [qué entregan al grupo]
- Materiales: [qué necesitan]

Tarea_2: [nombre_tarea]
- Estudiantes: [nombres específicos y por qué son ideales]  
- Función: [qué hacen exactamente]
- Resultado: [qué entregan al grupo]
- Materiales: [qué necesitan]

FASE_EJECUCIÓN (20-25 min):
[Repetir estructura para fase principal]

FASE_INTEGRACIÓN (10 min):
[Cómo se juntan los resultados]

PUNTOS_DE_SINCRONIZACIÓN:
- Minuto 15: [qué comparten/verifican]
- Minuto 30: [qué comparten/verifican]
- Final: [presentación/síntesis]
"""
        
        return prompt
    
    def _crear_resumen_estudiantes(self, perfiles: Dict) -> str:
        """Crea resumen ejecutivo de estudiantes para asignación de tareas"""
        if not perfiles or 'estudiantes' not in perfiles:
            return "Sin información de estudiantes"
            
        resumen = []
        for est in perfiles['estudiantes']:
            nombre = est.get('nombre', 'Estudiante')
            canal = est.get('canal_preferido', 'no especificado')
            apoyo = est.get('nivel_apoyo', 'no especificado')
            diag = est.get('diagnostico_formal', 'ninguno')
            temp = est.get('temperamento', 'no especificado')
            grup = est.get('agrupamiento_optimo', 'no especificado')
            
            # Identificar fortalezas para asignación
            fortalezas = []
            if canal == 'visual':
                fortalezas.append("diseño/organización")
            elif canal == 'auditivo':
                fortalezas.append("comunicación/presentación")
            elif canal == 'kinestésico':
                fortalezas.append("manipulación/construcción")
                
            if temp == 'reflexivo':
                fortalezas.append("análisis/verificación")
            elif temp == 'impulsivo':
                fortalezas.append("acción/dinamismo")
                
            if diag == 'altas_capacidades':
                fortalezas.append("tareas complejas/coordinación")
                
            fortalezas_str = ", ".join(fortalezas) if fortalezas else "versátil"
            
            linea = f"{nombre}: {canal}/{apoyo} apoyo, {grup}, fortalezas: {fortalezas_str}"
            if diag != 'ninguno':
                linea += f" ({diag})"
                
            resumen.append(linea)
        
        return '\n'.join(resumen)
    
    def _resumir_adaptaciones(self, adaptaciones: List[Dict]) -> str:
        """Resume las adaptaciones para considerar en asignación de tareas"""
        if not adaptaciones:
            return "Sin adaptaciones específicas definidas"
            
        resumen = []
        for adapt in adaptaciones:
            if adapt.get('tipo') == 'individual':
                nombre = adapt.get('estudiante', 'Estudiante')
                num_acciones = len(adapt.get('acciones_especificas', []))
                resumen.append(f"{nombre}: {num_acciones} adaptaciones específicas")
            elif adapt.get('tipo') == 'grupal':
                modificaciones = adapt.get('modificaciones', [])
                resumen.append(f"Grupo: {len(modificaciones)} modificaciones generales")
        
        return '\n'.join(resumen)
    
    def _get_ejemplos_arquitecturas(self) -> str:
        """Ejemplos de arquitecturas exitosas de tareas paralelas"""
        return """
EJEMPLO_SUPERMERCADO:
- Cajeros (3): Alex, Elena, Emma → aprovecha visual/reflexivo para precisión
- Supervisor (1): Ana → altas capacidades para coordinación compleja  
- Clientes (4): resto → roles activos que requieren movimiento

EJEMPLO_FÁBRICA_FRACCIONES:
- Mobiliario (2): Luis+Alex → kinestésico+visual para construcción
- Carteles (2): Elena+María → visual+auditivo para comunicación
- Selección (2): Ana+Sara → análisis y preparación
- Paneles (2): Emma+Hugo → diseño y creatividad
"""
    
    def _parsear_tareas_paralelas(self, respuesta: str) -> List[Dict]:
        """Extrae la arquitectura de tareas de la respuesta"""
        tareas = []
        
        # Buscar fases
        fases = ['FASE_PREPARACIÓN', 'FASE_EJECUCIÓN', 'FASE_INTEGRACIÓN']
        
        for fase in fases:
            patron_fase = rf'{fase}[^:]*:(.*?)(?=FASE_|PUNTOS_DE_SINCRONIZACIÓN:|$)'
            match_fase = re.search(patron_fase, respuesta, re.DOTALL)
            
            if match_fase:
                contenido_fase = match_fase.group(1)
                
                # Extraer tareas individuales dentro de la fase
                patron_tarea = r'Tarea_\d+: ([^\n]+)\n((?:- [^\n]+\n?)*)'
                matches_tareas = re.findall(patron_tarea, contenido_fase)
                
                for nombre_tarea, detalles in matches_tareas:
                    # Parsear detalles de la tarea
                    estudiantes = self._extraer_detalle(detalles, 'Estudiantes')
                    funcion = self._extraer_detalle(detalles, 'Función')
                    resultado = self._extraer_detalle(detalles, 'Resultado')
                    materiales = self._extraer_detalle(detalles, 'Materiales')
                    
                    tareas.append({
                        'fase': fase.lower(),
                        'nombre': nombre_tarea.strip(),
                        'estudiantes': estudiantes,
                        'funcion': funcion,
                        'resultado_esperado': resultado,
                        'materiales': materiales
                    })
        
        return tareas
    
    def _extraer_detalle(self, texto: str, campo: str) -> str:
        """Extrae un campo específico de los detalles de una tarea"""
        patron = rf'- {campo}: (.+)'
        match = re.search(patron, texto)
        return match.group(1).strip() if match else ""
    
    def _log_proceso(self, state: ActividadState, num_tareas: int):
        """Log del proceso de arquitectura"""
        print(f"\n✅ [{self.name}] Arquitectura de tareas creada")
        print(f"Total tareas paralelas: {num_tareas}")
        
        # Agrupar por fases
        fases = {}
        for tarea in state.tareas_paralelas:
            fase = tarea.get('fase', 'sin_fase')
            if fase not in fases:
                fases[fase] = 0
            fases[fase] += 1
        
        for fase, cantidad in fases.items():
            print(f"  - {fase}: {cantidad} tareas")


class ValidadorCurricularAgent(BaseAgent):
    """Agente que verifica coherencia curricular y objetivos pedagógicos"""
    
    def __init__(self):
        super().__init__("ValidadorCurricular", llm_required=True)
        
    def procesar(self, state: ActividadState) -> ActividadState:
        """Valida que la actividad cumple objetivos curriculares y es pedagógicamente sólida"""
        
        # Validar inputs
        is_valid, msg = self.validar_inputs(state)
        if not is_valid:
            state.problemas_detectados.append(f"ValidadorCurricular: {msg}")
            return state
        
        # Actualizar estado
        state.agente_actual = self.name
        
        # Construir prompt para validación curricular
        prompt = self._construir_prompt_validacion(state)
        
        # Llamar a LLM
        respuesta = self.llamar_llm(prompt, temperatura=0.3)  # Baja creatividad, alta precisión
        
        # Parsear validación
        validacion_resultado = self._parsear_validacion(respuesta)
        state.validacion_curricular = validacion_resultado
        
        # Si hay problemas críticos, marcar para iteración
        if validacion_resultado.get('problemas_criticos'):
            state.necesita_human_input = True
            state.problemas_detectados.extend(validacion_resultado['problemas_criticos'])
        
        # Log del proceso
        self._log_proceso(state, validacion_resultado)
        
        return state
    
    def validar_inputs(self, state: ActividadState) -> Tuple[bool, str]:
        """Valida que tenemos toda la información necesaria para validar"""
        if not state.actividad_base:
            return False, "Se necesita actividad base para validar"
        
        if not state.tareas_paralelas:
            return False, "Se necesitan tareas definidas para validar"
            
        return True, ""
    
    def _construir_prompt_validacion(self, state: ActividadState) -> str:
        """Construye prompt para validación curricular exhaustiva"""
        
        # Extraer información clave
        titulo = state.actividad_base.get('titulo', 'Sin título')
        objetivo = state.actividad_base.get('objetivo_pedagogico', 'Sin objetivo')
        duracion = state.actividad_base.get('duracion', 'Sin duración')
        
        # Resumen de tareas
        resumen_tareas = self._resumir_tareas_para_validacion(state.tareas_paralelas)
        
        prompt = f"""
VALIDADOR_CURRICULAR_4º_PRIMARIA:

Tu función es hacer una EVALUACIÓN CRÍTICA de esta actividad educativa desde la perspectiva curricular y pedagógica.

ACTIVIDAD_A_VALIDAR:
Título: {titulo}
Tema: {state.tema}
Objetivo declarado: {objetivo}
Duración: {duracion}

ESTRUCTURA_DE_TAREAS:
{resumen_tareas}

CRITERIOS_DE_VALIDACIÓN_4º_PRIMARIA:

CURRICULARES:
- ¿El objetivo es apropiado para 9-10 años?
- ¿La complejidad cognitiva es adecuada?
- ¿Se conecta con aprendizajes previos?
- ¿Prepara para aprendizajes posteriores?

PEDAGÓGICOS:
- ¿Las tareas realmente logran el objetivo?
- ¿El tiempo asignado es realista?
- ¿Hay equilibrio entre desafío y éxito?
- ¿Los estudiantes entienden para qué sirve?

INCLUSIVOS:
- ¿Todos los estudiantes pueden participar significativamente?
- ¿Las adaptaciones mantienen el rigor académico?
- ¿Hay múltiples formas de mostrar aprendizaje?

EVALUACIÓN_AUTÉNTICA:
- ¿Cómo sabremos si aprendieron?
- ¿Los productos finales reflejan comprensión real?

RESPONDE EN ESTE FORMATO:

VALIDACIÓN_CURRICULAR:

FORTALEZAS_IDENTIFICADAS:
- [Lista de aspectos bien diseñados]

PROBLEMAS_MENORES:
- [Aspectos mejorables pero no críticos]

PROBLEMAS_CRÍTICOS:
- [Aspectos que DEBEN cambiarse antes de implementar]

COHERENCIA_CURRICULAR:
- Apropiado para edad: SÍ/NO - [justificación]
- Objetivo alcanzable: SÍ/NO - [justificación]  
- Tiempo realista: SÍ/NO - [justificación]
- Evaluación clara: SÍ/NO - [justificación]

RECOMENDACIONES_ESPECÍFICAS:
- [Sugerencias concretas de mejora]

APROBACIÓN_PEDAGÓGICA:
APROBADA/APROBADA_CON_CAMBIOS/RECHAZADA - [Razón principal]
"""
        
        return prompt
    
    def _resumir_tareas_para_validacion(self, tareas: List[Dict]) -> str:
        """Crea resumen de tareas para análisis curricular"""
        if not tareas:
            return "Sin tareas definidas"
            
        resumen = []
        for tarea in tareas:
            nombre = tarea.get('nombre', 'Tarea sin nombre')
            estudiantes = tarea.get('estudiantes', 'Sin asignar')
            funcion = tarea.get('funcion', 'Sin función definida')
            resultado = tarea.get('resultado_esperado', 'Sin resultado definido')
            
            resumen.append(f"- {nombre}: {estudiantes} → {funcion} → {resultado}")
        
        return '\n'.join(resumen)
    
    def _parsear_validacion(self, respuesta: str) -> Dict:
        """Extrae los resultados de la validación"""
        validacion = {}
        
        # Extraer secciones principales
        secciones = {
            'fortalezas': r'FORTALEZAS_IDENTIFICADAS:(.*?)(?=PROBLEMAS_MENORES:|$)',
            'problemas_menores': r'PROBLEMAS_MENORES:(.*?)(?=PROBLEMAS_CRÍTICOS:|$)', 
            'problemas_criticos': r'PROBLEMAS_CRÍTICOS:(.*?)(?=COHERENCIA_CURRICULAR:|$)',
            'coherencia': r'COHERENCIA_CURRICULAR:(.*?)(?=RECOMENDACIONES_ESPECÍFICAS:|$)',
            'recomendaciones': r'RECOMENDACIONES_ESPECÍFICAS:(.*?)(?=APROBACIÓN_PEDAGÓGICA:|$)',
            'aprobacion': r'APROBACIÓN_PEDAGÓGICA:(.*?)$'
        }
        
        # Procesar cada sección
        resultado_parsing = {}
        
        for seccion, patron in secciones.items():
            match = re.search(patron, contenido_respuesta, re.DOTALL)
            if match:
                resultado_parsing[seccion] = match.group(1).strip()
            else:
                resultado_parsing[seccion] = ""
        
        return resultado_parsing


def main():
    """Función principal del sistema de agentes inteligente"""
    print("🎯 Sistema Multi-Agente Inteligente para Actividades Educativas")
    print("=" * 60)
    
    try:
        # Cargar perfiles de estudiantes
        perfiles_estudiantes = {
            "estudiantes": [
                {"id": "001", "nombre": "ALEX M.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "temperamento": "reflexivo", "ci_base": 102},
                {"id": "002", "nombre": "MARÍA L.", "diagnostico_formal": "ninguno", "canal_preferido": "auditivo", "temperamento": "reflexivo"},
                {"id": "003", "nombre": "ELENA R.", "diagnostico_formal": "TEA_nivel_1", "canal_preferido": "visual", "temperamento": "reflexivo", "ci_base": 118},
                {"id": "004", "nombre": "LUIS T.", "diagnostico_formal": "TDAH_combinado", "canal_preferido": "kinestésico", "temperamento": "impulsivo", "ci_base": 102},
                {"id": "005", "nombre": "ANA V.", "diagnostico_formal": "altas_capacidades", "canal_preferido": "auditivo", "temperamento": "reflexivo", "ci_base": 141},
                {"id": "006", "nombre": "SARA M.", "diagnostico_formal": "ninguno", "canal_preferido": "auditivo", "temperamento": "equilibrado", "ci_base": 115},
                {"id": "007", "nombre": "EMMA K.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "temperamento": "reflexivo", "ci_base": 132},
                {"id": "008", "nombre": "HUGO P.", "diagnostico_formal": "ninguno", "canal_preferido": "visual", "temperamento": "equilibrado", "ci_base": 114}
            ]
        }
        
        # Solicitar tema
        print("\n📚 Configuración de la actividad:")
        tema = input("Tema de la actividad: ").strip()
        
        if not tema:
            print("❌ Tema es obligatorio")
            return
        
        # Configurar restricciones básicas
        restricciones = {
            "duracion_max": 45,
            "materiales": "básicos",
            "espacio_amplio": False
        }
        
        # Crear estado inicial
        estado_inicial = ActividadState(
            tema=tema,
            perfiles_estudiantes=perfiles_estudiantes,
            restricciones=restricciones
        )
        
        # Crear orquestador y ejecutar pipeline
        print(f"\n🤖 Iniciando sistema multi-agente...")
        orquestador = OrquestadorAgent()
        
        # Ejecutar pipeline completo
        estado_final = orquestador.procesar(estado_inicial)
        
        # Mostrar resultados
        print(f"\n✅ Proceso completado:")
        print(f"Estado final: {estado_final.estado}")
        print(f"Iteraciones realizadas: {estado_final.iteracion}")
        
        if estado_final.actividad_base:
            print(f"✅ Actividad base generada")
            
        if estado_final.adaptaciones_dua:
            print(f"✅ Adaptaciones DUA: {len(estado_final.adaptaciones_dua)}")
            
        if estado_final.tareas_paralelas:
            print(f"✅ Tareas paralelas: {len(estado_final.tareas_paralelas)}")
            
        if estado_final.problemas_detectados:
            print(f"⚠️  Problemas detectados: {len(estado_final.problemas_detectados)}")
            for problema in estado_final.problemas_detectados:
                print(f"   - {problema}")
        
        # Guardar resultado
        filename = f"actividad_inteligente_{tema.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        resultado_final = {
            'id': estado_final.id,
            'tema': estado_final.tema,
            'estado': estado_final.estado.value,
            'iteraciones': estado_final.iteracion,
            'timestamp': estado_final.timestamp,
            'actividad_base': estado_final.actividad_base,
            'adaptaciones_dua': estado_final.adaptaciones_dua,
            'tareas_paralelas': estado_final.tareas_paralelas,
            'validacion_curricular': estado_final.validacion_curricular,
            'recursos_necesarios': estado_final.recursos_necesarios,
            'problemas_detectados': estado_final.problemas_detectados,
            'historial_cambios': estado_final.historial_cambios
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultado_final, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Resultado guardado en: {filename}")
        
    except KeyboardInterrupt:
        print("\n❌ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante ejecución: {e}")
        logger.error(f"Error en main(): {e}")


if __name__ == "__main__":
    main()

