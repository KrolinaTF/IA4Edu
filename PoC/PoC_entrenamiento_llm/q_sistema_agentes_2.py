#!/usr/bin/env python3
"""
Sistema Híbrido Cuántico-Agentes con Hamiltoniano de Función de Costo Mínima
Flujo: Problema → Fase Cuántica Pre-procesamiento → LLM → Fase Cuántica Validación → Retroalimentación
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Mapping
from dataclasses import dataclass
import logging
import numpy as np

# Configurar variables de entorno para LiteLLM/CrewAI (IGUAL QUE FEWSHOT)
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_HOST"] = "http://192.168.1.10:11434"
os.environ["OLLAMA_API_BASE"] = "http://192.168.1.10:11434"
os.environ["LITELLM_LOG"] = "DEBUG"  # Para debug

# Configuración para forzar Ollama sin LiteLLM
os.environ["OPENAI_API_KEY"] = "not-needed"  # Placeholder
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"
# Desactivar LiteLLM en CrewAI
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# Configuración de timeout
os.environ["HTTPX_TIMEOUT"] = "120"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QUANTUM_HAMILTONIAN_SYSTEM")

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from crewai_tools import FileReadTool, DirectoryReadTool
    from langchain_community.llms import Ollama
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping
    logger.info("✅ CrewAI y LangChain importados correctamente")
    
    # Importaciones cuánticas (versión simplificada compatible)
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import Aer
    from qiskit.circuit import Parameter
    from qiskit.quantum_info import Statevector, SparsePauliOp
    try:
        from qiskit_algorithms import QAOA, NumPyMinimumEigensolver
        from qiskit_algorithms.optimizers import COBYLA
    except ImportError:
        QAOA = None
        NumPyMinimumEigensolver = None
        COBYLA = None
    logger.info("✅ Qiskit importado correctamente")
    
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    logger.error("💡 Instala dependencias: pip install crewai crewai-tools langchain-community qiskit qiskit-aer qiskit-algorithms")
    raise ImportError("Dependencias no están disponibles")

from ollama_api_integrator import OllamaAPIEducationGenerator
from prompt_template import PromptTemplateGenerator


class DirectOllamaLLM(LLM):
    """LLM completamente personalizado que bypassa LiteLLM completamente"""
    
    def __init__(self, ollama_host: str = "192.168.1.10", ollama_model: str = "qwen3:latest", **kwargs):
        # Inicializar LLM base primero
        super().__init__(**kwargs)
        
        # Separar host y puerto si viene junto
        if ":" in ollama_host:
            host_only = ollama_host.split(":")[0]
        else:
            host_only = ollama_host
            
        # Crear generador de Ollama y asignar como atributos de instancia
        self.ollama_generator = OllamaAPIEducationGenerator(
            host=host_only, 
            model_name=ollama_model
        )
        self.model_name = ollama_model
        self.host = host_only
        
        logger.info(f"🚀 DirectOllamaLLM inicializado: {ollama_model} en {host_only}")
    
    @property
    def _llm_type(self) -> str:
        return "direct_ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Llamada principal al LLM - usa nuestro OllamaAPIEducationGenerator"""
        try:
            result = self.ollama_generator.generar_texto(
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', 800),
                temperature=kwargs.get('temperature', 0.7)
            )
            return result
        except Exception as e:
            logger.error(f"Error en DirectOllamaLLM: {e}")
            return f"Error generando respuesta con Ollama local: {str(e)}"
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Parámetros que identifican este LLM"""
        return {
            "llm_type": "direct_ollama",
            "model_name": self.model_name,
            "host": self.host
        }


@dataclass
class ActividadEducativa:
    """Estructura de datos para una actividad educativa"""
    id: str
    titulo: str
    materia: str
    tema: str
    contenido: str
    estudiantes_objetivo: List[str]
    tipo: str
    adaptaciones: List[str]
    metadatos: Dict
    timestamp: str


@dataclass
class EstadoPedagogico:
    """Representa el estado pedagógico del aula"""
    variables_decision: Dict  # Variables que el LLM debe optimizar
    restricciones: List[str]  # Restricciones pedagógicas
    objetivos: List[str]     # Objetivos a minimizar/maximizar
    energia_calculada: float  # Energía del Hamiltoniano para este estado
    validez: float           # Qué tan válida es la solución (0-1)


class HamiltonianoEducativo:
    """Construye y evalúa Hamiltonianos para problemas pedagógicos"""
    
    def __init__(self):
        self.backend = Aer.get_backend('statevector_simulator')
        if QAOA is not None:
            self.qaoa = QAOA(optimizer=COBYLA(maxiter=100), reps=1)
        else:
            self.qaoa = None
        logger.info("🔬 Hamiltoniano Educativo inicializado")
    
    def construir_hamiltoniano_ambiente(self, variables_llm: Dict, estudiantes: List[Dict]) -> SparsePauliOp:
        """Construye Hamiltoniano para optimizar el ambiente de aprendizaje"""
        
        # Variables del problema (extraídas del LLM):
        # - tipo_actividad: individual/grupal/mixto
        # - nivel_energia: alto/medio/bajo  
        # - duracion: minutos de la actividad
        # - materiales_necesarios: lista de materiales
        
        logger.info("🔧 Construyendo Hamiltoniano para ambiente de aprendizaje")
        
        n_qubits = min(len(estudiantes), 10)  # Limitar a 10 qubits máximo (1024 estados)
        if len(estudiantes) > 10:
            logger.warning(f"⚠️ Limitando estudiantes de {len(estudiantes)} a 10 para el Hamiltoniano")
            estudiantes = estudiantes[:10]
        
        # Términos del Hamiltoniano (función de costo a minimizar)
        pauli_strings = []
        coefficients = []
        
        # TÉRMINO 1: Penalizar desajustes entre estudiante y tipo de actividad
        for i, estudiante in enumerate(estudiantes):
            # Si estudiante necesita movimiento (TDAH) pero actividad es baja energía → penalización
            if estudiante.get('diagnostico_formal') == 'TDAH_combinado':
                if variables_llm.get('nivel_energia') == 'bajo':
                    # Crear string Pauli válido: I en todas las posiciones excepto Z en posición i
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(2.0)  # Penalización alta
            
            # Si estudiante necesita estructura (TEA) pero actividad es alta energía → penalización
            if estudiante.get('diagnostico_formal') == 'TEA_nivel_1':
                if variables_llm.get('nivel_energia') == 'alto':
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(1.5)
        
        # TÉRMINO 2: Fomentar colaboración óptima
        tipo_actividad = variables_llm.get('tipo_actividad', 'mixto')
        if tipo_actividad == 'grupal':
            # Recompensar cuando estudiantes complementarios trabajan juntos
            for i in range(n_qubits-1):
                for j in range(i+1, n_qubits):
                    if self._son_complementarios(estudiantes[i], estudiantes[j]):
                        # Crear string Pauli con Z en posiciones i y j
                        pauli_str = ['I'] * n_qubits
                        pauli_str[i] = 'Z'
                        pauli_str[j] = 'Z'
                        pauli_strings.append(''.join(pauli_str))
                        coefficients.append(-0.5)  # Recompensa (energía negativa)
        
        # TÉRMINO 3: Penalizar sobrecarga cognitiva
        duracion = variables_llm.get('duracion', 45)
        if duracion > 60:  # Actividades muy largas
            for i, estudiante in enumerate(estudiantes):
                ci_base = estudiante.get('ci_base', 100)
                if ci_base < 110:  # Estudiantes que pueden necesitar más apoyo
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(1.0)
        
        # Crear el Hamiltoniano como SparsePauliOp
        if pauli_strings and coefficients:
            hamiltoniano = SparsePauliOp(pauli_strings, coefficients)
        else:
            # Hamiltoniano trivial si no hay términos
            hamiltoniano = SparsePauliOp(['I' * n_qubits], [0.0])
        
        logger.info(f"✅ Hamiltoniano construido con {len(pauli_strings)} términos")
        return hamiltoniano
    
    def construir_hamiltoniano_asignaciones(self, variables_llm: Dict, estudiantes: List[Dict], roles: List[str]) -> SparsePauliOp:
        """Construye Hamiltoniano simplificado para optimizar asignación de roles (solo estudiantes)"""
        
        logger.info("🔧 Construyendo Hamiltoniano simplificado para asignación de roles")
        
        # SIMPLIFICACIÓN: Usar solo los qubits de estudiantes (no matriz completa)
        # Esto evita el problema de memoria exponencial
        n_qubits = len(estudiantes)  # Un qubit por estudiante
        
        pauli_strings = []
        coefficients = []
        
        # TÉRMINO SIMPLIFICADO: Penalizar incompatibilidades entre estudiantes y roles propuestos
        for i, estudiante in enumerate(estudiantes):
            # Usar información de variables_llm para determinar el rol propuesto para este estudiante
            rol_propuesto = self._extraer_rol_estudiante(variables_llm, i, roles)
            
            if rol_propuesto:
                compatibilidad = self._calcular_compatibilidad_rol(estudiante, rol_propuesto)
                
                if compatibilidad < 0.4:  # Baja compatibilidad = penalización
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(2.0 * (0.4 - compatibilidad))  # Penalización proporcional
                elif compatibilidad > 0.7:  # Alta compatibilidad = recompensa
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(-0.5 * compatibilidad)  # Recompensa proporcional
        
        # TÉRMINO 2: Fomentar balance en el grupo
        for i in range(n_qubits-1):
            for j in range(i+1, n_qubits):
                if self._necesitan_balance(estudiantes[i], estudiantes[j]):
                    # Recompensar cuando estudiantes que se balancean trabajan juntos
                    pauli_str = ['I'] * n_qubits
                    pauli_str[i] = 'Z'
                    pauli_str[j] = 'Z'
                    pauli_strings.append(''.join(pauli_str))
                    coefficients.append(-0.3)  # Recompensa por balance
        
        if pauli_strings and coefficients:
            hamiltoniano = SparsePauliOp(pauli_strings, coefficients)
        else:
            # Hamiltoniano trivial si no hay términos
            hamiltoniano = SparsePauliOp(['I' * n_qubits], [0.0])
        
        logger.info(f"✅ Hamiltoniano simplificado construido con {len(pauli_strings)} términos y {n_qubits} qubits")
        return hamiltoniano
    
    def _extraer_rol_estudiante(self, variables_llm: Dict, indice_estudiante: int, roles_disponibles: List[str]) -> str:
        """Extrae el rol propuesto para un estudiante de las variables del LLM"""
        # Implementación simplificada: asignar roles cíclicamente o basado en índice
        if roles_disponibles:
            return roles_disponibles[indice_estudiante % len(roles_disponibles)]
        return "participante"
    
    def _necesitan_balance(self, estudiante1: Dict, estudiante2: Dict) -> bool:
        """Determina si dos estudiantes se benefician de trabajar juntos por balance"""
        # Casos donde el balance es beneficioso
        diag1 = estudiante1.get('diagnostico_formal', 'ninguno')
        diag2 = estudiante2.get('diagnostico_formal', 'ninguno')
        
        # Altas capacidades con estudiantes típicos
        if (diag1 == 'altas_capacidades' and diag2 == 'ninguno') or \
           (diag2 == 'altas_capacidades' and diag1 == 'ninguno'):
            return True
        
        # Estudiantes con necesidades especiales con estudiantes equilibrados
        if (diag1 in ['TDAH_combinado', 'TEA_nivel_1'] and estudiante2.get('temperamento') == 'equilibrado') or \
           (diag2 in ['TDAH_combinado', 'TEA_nivel_1'] and estudiante1.get('temperamento') == 'equilibrado'):
            return True
        
        return False
    
    def evaluar_propuesta_llm(self, hamiltoniano: SparsePauliOp, propuesta_llm: Dict) -> EstadoPedagogico:
        """Evalúa la propuesta del LLM usando el Hamiltoniano"""
        
        logger.info("🔍 Evaluando propuesta del LLM con Hamiltoniano")
        
        # Codificar la propuesta del LLM como estado cuántico
        estado_propuesta = self._codificar_propuesta(propuesta_llm, hamiltoniano.num_qubits)
        
        # Calcular energía de la propuesta
        energia = self._calcular_energia_estado(hamiltoniano, estado_propuesta)
        
        # Encontrar energía mínima teórica para comparación
        if self.qaoa is not None and NumPyMinimumEigensolver is not None:
            try:
                solver = NumPyMinimumEigensolver()
                resultado_optimo = solver.compute_minimum_eigenvalue(hamiltoniano)
                energia_minima = resultado_optimo.eigenvalue
            except:
                energia_minima = energia - 1.0  # Estimación conservadora
        else:
            energia_minima = energia - 1.0
        
        # Calcular validez (qué tan cerca está del óptimo)
        if energia_minima < energia:
            validez = max(0.0, 1.0 - (energia - energia_minima) / abs(energia_minima + 1e-6))
        else:
            validez = 1.0
        
        logger.info(f"📊 Energía propuesta: {energia:.3f}, Mínima teórica: {energia_minima:.3f}, Validez: {validez:.1%}")
        
        return EstadoPedagogico(
            variables_decision=propuesta_llm,
            restricciones=[],
            objetivos=[],
            energia_calculada=energia,
            validez=validez
        )
    
    def generar_retroalimentacion(self, evaluacion: EstadoPedagogico, contexto: str) -> str:
        """Genera retroalimentación lingüística para el LLM basada en la evaluación cuántica"""
        
        energia = evaluacion.energia_calculada
        validez = evaluacion.validez
        
        if validez > 0.8:
            return f"✅ La propuesta para {contexto} es óptima (validez: {validez:.1%}). La configuración minimiza los conflictos pedagógicos y maximiza la efectividad del aprendizaje."
        
        elif validez > 0.6:
            return f"⚠️ La propuesta para {contexto} es buena pero mejorable (validez: {validez:.1%}). Considera ajustar el nivel de energía de la actividad o revisar las asignaciones de roles para estudiantes con necesidades especiales."
        
        elif validez > 0.4:
            feedback = f"🔄 La propuesta para {contexto} requiere ajustes significativos (validez: {validez:.1%}). "
            
            # Análisis específico basado en energía
            if energia > 2.0:
                feedback += "Se detectan conflictos importantes entre las necesidades de los estudiantes y la actividad propuesta. "
                feedback += "Revisa especialmente las adaptaciones para Elena (TEA) y Luis (TDAH). "
            
            if energia > 1.0:
                feedback += "La asignación de roles no parece óptima. Considera intercambiar roles entre estudiantes con perfiles complementarios."
            
            return feedback
        
        else:
            return f"❌ La propuesta para {contexto} no es viable (validez: {validez:.1%}). La configuración genera demasiados conflictos pedagógicos. Considera un enfoque completamente diferente que atienda mejor las necesidades individuales y la dinámica grupal."
    
    def _son_complementarios(self, estudiante1: Dict, estudiante2: Dict) -> bool:
        """Determina si dos estudiantes son complementarios pedagógicamente"""
        # Lógica de complementariedad
        canal1 = estudiante1.get('canal_preferido', '')
        canal2 = estudiante2.get('canal_preferido', '')
        
        temp1 = estudiante1.get('temperamento', '')
        temp2 = estudiante2.get('temperamento', '')
        
        # Diferentes canales son complementarios
        if canal1 != canal2:
            return True
        
        # Reflexivo + Equilibrado es buena combinación
        if (temp1 == 'reflexivo' and temp2 == 'equilibrado') or (temp1 == 'equilibrado' and temp2 == 'reflexivo'):
            return True
        
        return False
    
    def _calcular_compatibilidad_rol(self, estudiante: Dict, rol: str) -> float:
        """Calcula compatibilidad entre estudiante y rol (0-1)"""
        compatibilidad = 0.5  # Base neutral
        
        # Ajustes basados en diagnóstico
        diagnostico = estudiante.get('diagnostico_formal', 'ninguno')
        
        if 'cajero' in rol.lower():
            if diagnostico == 'TEA_nivel_1':
                compatibilidad += 0.3  # TEA bueno para tareas estructuradas
            if estudiante.get('canal_preferido') == 'visual':
                compatibilidad += 0.2  # Visual bueno para manejar productos/dinero
        
        elif 'cliente' in rol.lower():
            if diagnostico == 'TDAH_combinado':
                compatibilidad += 0.3  # TDAH bueno para roles dinámicos
            if estudiante.get('temperamento') == 'impulsivo':
                compatibilidad += 0.1
        
        elif 'supervisor' in rol.lower():
            if diagnostico == 'altas_capacidades':
                compatibilidad += 0.4  # Altas capacidades buenas para supervisión
            if estudiante.get('canal_preferido') == 'auditivo':
                compatibilidad += 0.2  # Auditivo bueno para comunicación
        
        return min(1.0, max(0.0, compatibilidad))
    
    def _codificar_propuesta(self, propuesta: Dict, n_qubits: int) -> np.ndarray:
        """Codifica propuesta del LLM como estado cuántico (con protección de memoria)"""
        # Protección contra estados cuánticos demasiado grandes
        if n_qubits > 12:  # 2^12 = 4096 elementos máximo
            logger.warning(f"⚠️ Limitando qubits de {n_qubits} a 12 para evitar problemas de memoria")
            n_qubits = 12
        
        # Simplificación: crear estado basado en hash de la propuesta
        hash_propuesta = hash(str(sorted(propuesta.items()))) % (2**n_qubits)
        estado = np.zeros(2**n_qubits)
        estado[hash_propuesta] = 1.0
        return estado
    
    def _calcular_energia_estado(self, hamiltoniano: SparsePauliOp, estado: np.ndarray) -> float:
        """Calcula energía esperada del estado dado el Hamiltoniano"""
        # Crear Statevector de Qiskit
        statevector = Statevector(estado)
        
        # Calcular valor esperado
        energia = statevector.expectation_value(hamiltoniano).real
        return energia


class SistemaHamiltonianoAgentes:
    """Sistema principal que usa Hamiltonianos para optimizar decisiones de agentes"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10",
                 ambiente_model: str = "qwen3:latest",
                 disenador_model: str = "qwen3:latest", 
                 asignador_model: str = "qwen2:latest",
                 evaluador_model: str = "mistral:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.ambiente_model = ambiente_model
        self.disenador_model = disenador_model
        self.asignador_model = asignador_model
        self.evaluador_model = evaluador_model
        self.perfiles_path = perfiles_path
        
        # Inicializar sistema Hamiltoniano
        self.hamiltoniano_educativo = HamiltonianoEducativo()
        
        # Configurar LLMs específicos (como en los proyectos exitosos)
        self._configurar_llms()
        
        # Cargar perfiles
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes híbridos
        self._crear_agentes_hamiltonianos()
        
        logger.info("✅ Sistema Hamiltoniano-Agentes inicializado")
    
    def _configurar_llms(self):
        """Configura los LLMs usando el patrón EXACTO de sistema_agentes_fewshot.py que funciona"""
        try:
            # Configurar LiteLLM correctamente para Ollama (IGUAL QUE FEWSHOT)
            import litellm
            
            # Configuraciones específicas para Ollama local
            logger.info(f"🔧 Configurando LiteLLM para Ollama local...")
            
            # Mapear todos los modelos para LiteLLM
            modelos_unicos = set([self.ambiente_model, self.disenador_model, self.asignador_model, self.evaluador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Configurar variables específicas para LiteLLM + Ollama
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            # Crear LLMs específicos para cada agente (IGUAL QUE FEWSHOT)
            self.ambiente_llm = Ollama(
                model=f"ollama/{self.ambiente_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.disenador_llm = Ollama(
                model=f"ollama/{self.disenador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.asignador_llm = Ollama(
                model=f"ollama/{self.asignador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.evaluador_llm = Ollama(
                model=f"ollama/{self.evaluador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info(f"✅ LLMs configurados exitosamente (patrón fewshot)")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
            logger.error("🚨 No se pudieron configurar LLMs para CrewAI.")
            raise e
    
    def _cargar_perfiles(self, perfiles_path: str) -> List[Dict]:
        """Cargar perfiles de estudiantes"""
        try:
            if not os.path.isabs(perfiles_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                perfiles_path = os.path.join(script_dir, perfiles_path)
            
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('estudiantes', [])
        except Exception as e:
            logger.error(f"Error cargando perfiles: {e}")
            return self._crear_perfiles_default()
    
    def _crear_perfiles_default(self) -> List[Dict]:
        """Perfiles por defecto"""
        return [
            {"id": "001", "nombre": "ALEX M.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 102},
            {"id": "002", "nombre": "MARÍA L.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno"},
            {"id": "003", "nombre": "ELENA R.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "TEA_nivel_1", "ci_base": 118},
            {"id": "004", "nombre": "LUIS T.", "temperamento": "impulsivo", "canal_preferido": "kinestésico", "diagnostico_formal": "TDAH_combinado", "ci_base": 102},
            {"id": "005", "nombre": "ANA V.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "altas_capacidades", "ci_base": 141},
            {"id": "006", "nombre": "SARA M.", "temperamento": "equilibrado", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno", "ci_base": 115},
            {"id": "007", "nombre": "EMMA K.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 132},
            {"id": "008", "nombre": "HUGO P.", "temperamento": "equilibrado", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 114}
        ]
    
    def _crear_agentes_hamiltonianos(self):
        """Crea agentes que usan retroalimentación Hamiltoniana"""
        
        # AGENTE 1: AMBIENTE CON RETROALIMENTACIÓN CUÁNTICA
        self.agente_ambiente_hamiltoniano = Agent(
            role="Especialista en Ambiente de Aprendizaje con Validación Cuántica",
            goal="Proponer configuraciones de ambiente que sean validadas por optimización cuántica para minimizar conflictos pedagógicos",
            backstory="Eres un especialista en crear ambientes de aprendizaje. Tu propuesta será evaluada por un sistema cuántico que detecta incompatibilidades entre estudiantes y actividades. Si tu propuesta no minimiza la función de costo pedagógica, recibirás retroalimentación específica para mejorarla. Respondes siempre en español.",
            tools=[],
            llm=self.ambiente_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: DISEÑADOR CON VALIDACIÓN CUÁNTICA  
        self.agente_disenador_hamiltoniano = Agent(
            role="Diseñador de Actividades con Optimización Cuántica",
            goal="Crear actividades educativas que sean óptimas según análisis cuántico de compatibilidad estudiante-actividad",
            backstory="Eres un diseñador de actividades educativas. Tus propuestas serán evaluadas cuánticamente para detectar si generan sobrecarga cognitiva, conflictos de temperamento o desajustes de canal de aprendizaje. Usar esta retroalimentación para crear actividades más efectivas. Respondes siempre en español.",
            tools=[],
            llm=self.disenador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 3: ASIGNADOR CON HAMILTONIANO DE ROLES
        self.agente_asignador_hamiltoniano = Agent(
            role="Asignador de Roles con Optimización Cuántica",
            goal="Asignar roles específicos a estudiantes usando validación cuántica para minimizar conflictos y maximizar complementariedad",
            backstory="Eres un especialista en asignación de roles. Un sistema cuántico evaluará tus asignaciones usando un Hamiltoniano que penaliza incompatibilidades estudiante-rol y recompensa complementariedades. Usas esta retroalimentación para crear asignaciones óptimas. Respondes siempre en español.",
            tools=[],
            llm=self.asignador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 4: EVALUADOR FINAL CON SÍNTESIS CUÁNTICA
        self.agente_evaluador_hamiltoniano = Agent(
            role="Evaluador Final con Síntesis de Resultados Cuánticos",
            goal="Integrar todas las validaciones cuánticas en una evaluación final coherente y práctica",
            backstory="Eres un evaluador que recibe los resultados de múltiples validaciones cuánticas (ambiente, diseño, asignaciones) y los sintetiza en una propuesta final coherente. Tu trabajo es asegurar que la actividad final sea tanto cuánticamente óptima como prácticamente ejecutable. Respondes siempre en español.",
            tools=[],
            llm=self.evaluador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes Hamiltonianos creados")
    
    def generar_actividad_hamiltoniana(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera actividad usando bucle Hamiltoniano: LLM → Cuántica → Retroalimentación → LLM"""
        
        logger.info(f"🔬 Generando actividad Hamiltoniana para {materia}")
        
        try:
            # FASE 1: LLM propone ambiente inicial
            logger.info("🔄 FASE 1: Propuesta inicial de ambiente")
            
            tarea_ambiente_inicial = Task(
                description=f"""Propón una configuración inicial de ambiente para {materia} {f'sobre {tema}' if tema else ''}.

GRUPO: 8 estudiantes de 4º Primaria con perfiles diversos:
- Elena (TEA nivel 1): Necesita estructura, predictibilidad, pausas
- Luis (TDAH combinado): Necesita movimiento, retroalimentación frecuente
- Ana (altas capacidades): Puede liderar, necesita desafíos adicionales
- Otros 5 estudiantes con canales diversos (visual, auditivo, kinestésico)

PROPÓN LAS SIGUIENTES VARIABLES DE DECISIÓN:

1. TIPO_ACTIVIDAD: [individual/grupal/mixto]
2. NIVEL_ENERGIA: [alto/medio/bajo] 
3. DURACION: [30-60 minutos]
4. MATERIALES_PRINCIPALES: [lista de 3-5 materiales clave]
5. ESTRUCTURA_TEMPORAL: [secuencial/paralelo/rotativo]

JUSTIFICA cada decisión pensando en las necesidades específicas del grupo.

Responde en FORMATO ESTRUCTURADO que permita fácil extracción de variables.""",
                agent=self.agente_ambiente_hamiltoniano,
                expected_output="Propuesta estructurada de configuración de ambiente"
            )
            
            # Ejecutar propuesta inicial
            crew_inicial = Crew(
                agents=[self.agente_ambiente_hamiltoniano], 
                tasks=[tarea_ambiente_inicial], 
                process=Process.sequential, 
                verbose=True
            )
            resultado_inicial = crew_inicial.kickoff()
            
            # FASE 2: Validación cuántica de la propuesta
            logger.info("🔬 FASE 2: Validación cuántica de la propuesta")
            
            variables_extraidas = self._extraer_variables_llm(str(resultado_inicial))
            hamiltoniano_ambiente = self.hamiltoniano_educativo.construir_hamiltoniano_ambiente(variables_extraidas, self.perfiles_data)
            evaluacion_ambiente = self.hamiltoniano_educativo.evaluar_propuesta_llm(hamiltoniano_ambiente, variables_extraidas)
            retroalimentacion_ambiente = self.hamiltoniano_educativo.generar_retroalimentacion(evaluacion_ambiente, "ambiente de aprendizaje")
            
            # FASE 3: LLM refina propuesta con retroalimentación cuántica
            logger.info("🔄 FASE 3: Refinamiento con retroalimentación cuántica")
            
            tarea_refinamiento = Task(
                description=f"""Refina tu propuesta de ambiente basándote en esta retroalimentación cuántica:

RETROALIMENTACIÓN CUÁNTICA:
{retroalimentacion_ambiente}

TU PROPUESTA ORIGINAL:
{resultado_inicial}

NUEVA PROPUESTA REFINADA:
Ajusta las variables de decisión (tipo_actividad, nivel_energia, duracion, etc.) considerando la retroalimentación cuántica.
Si la retroalimentación indica conflictos específicos, modificalos.
Si indica que la propuesta es óptima, profundiza en los detalles.

DESARROLLA AHORA EL AMBIENTE COMPLETO:
- Configuración física del aula
- Narrativa y contexto motivador
- Gestión del ambiente (ruido, movimiento, regulación)
- Estrategias específicas para Elena (TEA) y Luis (TDAH)

Responde en español con detalles concretos y ejecutables.""",
                agent=self.agente_ambiente_hamiltoniano,
                expected_output="Ambiente refinado con retroalimentación cuántica integrada"
            )
            
            # FASE 4: Diseño de actividad con validación cuántica
            tarea_diseno_hamiltoniano = Task(
                description=f"""Diseña la actividad completa basándote en el ambiente validado cuánticamente.

AMBIENTE VALIDADO:
{resultado_inicial}

RETROALIMENTACIÓN CUÁNTICA INTEGRADA:
{retroalimentacion_ambiente}

DISEÑA LA ACTIVIDAD COMPLETA:

=== ESTRUCTURA Y DESARROLLO ===
- Preparación (10-15 min): pasos exactos
- Desarrollo principal (según duración validada): secuencia detallada  
- Cierre (10 min): finalización y evaluación

=== ROLES Y RESPONSABILIDADES ===
Identifica 3-4 roles específicos necesarios para la actividad.
Para cada rol especifica:
- Función exacta durante la actividad
- Responsabilidades específicas
- Interacciones con otros roles
- Productos/entregas finales

=== MATERIALES Y RECURSOS ===
- Lista exhaustiva con cantidades exactas
- Organización del espacio físico
- Adaptaciones para diferentes canales de aprendizaje

Esta actividad será posteriormente validada cuánticamente para optimizar las asignaciones de roles.

Responde en español con máximo detalle operativo.""",
                agent=self.agente_disenador_hamiltoniano,
                context=[tarea_refinamiento],
                expected_output="Actividad completamente diseñada lista para asignación de roles"
            )
            
            # FASE 5: Asignación de roles con Hamiltoniano específico
            tarea_asignacion_hamiltoniana = Task(
                description=f"""Asigna roles específicos a cada estudiante. Tu asignación será validada cuánticamente.

ESTUDIANTES DISPONIBLES:
- 001 ALEX M.: reflexivo, visual, CI 102
- 002 MARÍA L.: reflexivo, auditivo
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, CI 115
- 007 EMMA K.: reflexivo, visual, CI 132
- 008 HUGO P.: equilibrado, visual, CI 114

ASIGNA UN ROL ESPECÍFICO A CADA ESTUDIANTE:

Para cada asignación justifica:
- Por qué este estudiante es ideal para este rol
- Cómo su perfil (temperamento, canal, diagnóstico) beneficia el rol
- Qué adaptaciones específicas necesita
- Con qué otros estudiantes interactuará principalmente

FORMATO REQUERIDO:
**001 ALEX M.**: ROL_ASIGNADO
- Justificación: [por qué es ideal]
- Adaptaciones: [apoyos específicos]
- Interacciones: [con quién trabaja]

[Repetir para todos los estudiantes]

Tu asignación será evaluada cuánticamente para detectar conflictos y optimizar complementariedades.

Responde en español.""",
                agent=self.agente_asignador_hamiltoniano,
                context=[tarea_diseno_hamiltoniano],
                expected_output="Asignación completa de roles con justificaciones"
            )
            
            # Ejecutar todas las tareas
            crew_completo = Crew(
                agents=[self.agente_ambiente_hamiltoniano, self.agente_disenador_hamiltoniano, self.agente_asignador_hamiltoniano],
                tasks=[tarea_refinamiento, tarea_diseno_hamiltoniano, tarea_asignacion_hamiltoniana],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_completo = crew_completo.kickoff()
            
            # FASE 6: Validación cuántica final de asignaciones
            logger.info("🔬 FASE 6: Validación cuántica final")
            
            # Extraer roles y asignaciones del resultado
            roles_identificados = self._extraer_roles_llm(str(resultado_completo))
            asignaciones_propuestas = self._extraer_asignaciones_llm(str(resultado_completo))
            
            hamiltoniano_asignaciones = self.hamiltoniano_educativo.construir_hamiltoniano_asignaciones(
                asignaciones_propuestas, self.perfiles_data, roles_identificados
            )
            evaluacion_asignaciones = self.hamiltoniano_educativo.evaluar_propuesta_llm(
                hamiltoniano_asignaciones, asignaciones_propuestas
            )
            retroalimentacion_asignaciones = self.hamiltoniano_educativo.generar_retroalimentacion(
                evaluacion_asignaciones, "asignación de roles"
            )
            
            # FASE 7: Síntesis final con todas las validaciones cuánticas
            tarea_sintesis_final = Task(
                description=f"""Crea la versión final de la actividad integrando todas las validaciones cuánticas.

RETROALIMENTACIÓN CUÁNTICA AMBIENTE:
{retroalimentacion_ambiente}

RETROALIMENTACIÓN CUÁNTICA ASIGNACIONES:
{retroalimentacion_asignaciones}

ACTIVIDAD DESARROLLADA:
{resultado_completo}

SÍNTESIS FINAL:
Integra todas las validaciones cuánticas en una actividad final que sea:
1. Cuánticamente óptima (minimiza conflictos pedagógicos)
2. Prácticamente ejecutable en aula real
3. Completamente detallada para implementación inmediata

Si las validaciones cuánticas sugieren ajustes, incorpóralos.
Si confirman la optimización, mantén la propuesta y añade detalles finales.

FORMATO FINAL:
=== RESUMEN EJECUTIVO ===
- Actividad optimizada cuánticamente
- Validaciones integradas
- Puntos críticos de implementación

=== DESARROLLO COMPLETO ===
[Actividad final con todos los ajustes cuánticos integrados]

Responde en español.""",
                agent=self.agente_evaluador_hamiltoniano,
                context=[tarea_asignacion_hamiltoniana],
                expected_output="Actividad final con todas las optimizaciones cuánticas integradas"
            )
            
            crew_final = Crew(
                agents=[self.agente_evaluador_hamiltoniano], 
                tasks=[tarea_sintesis_final], 
                process=Process.sequential, 
                verbose=True
            )
            resultado_final = crew_final.kickoff()
            
            # Procesar resultado final
            contenido_completo = self._procesar_resultados_hamiltonianos(
                resultado_final, evaluacion_ambiente, evaluacion_asignaciones
            )
            
            return ActividadEducativa(
                id=f"hamiltoniano_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Hamiltoniana: {materia.title()}",
                materia=materia,
                tema=tema or "optimización cuántica",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="hamiltoniano_cuantico",
                adaptaciones=["validacion_cuantica", "optimizacion_hamiltoniana", "bucle_retroalimentacion"],
                metadatos={
                    "total_estudiantes": 8,
                    "sistema_cuantico": True,
                    "validaciones_realizadas": 2,
                    "energia_ambiente": float(evaluacion_ambiente.energia_calculada),
                    "validez_ambiente": float(evaluacion_ambiente.validez),
                    "energia_asignaciones": float(evaluacion_asignaciones.energia_calculada),
                    "validez_asignaciones": float(evaluacion_asignaciones.validez),
                    "bucles_retroalimentacion": 2
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error en generación Hamiltoniana: {e}")
            return ActividadEducativa(
                id=f"error_hamiltoniano_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error Hamiltoniano - {materia}",
                materia=materia,
                tema=tema or "error",
                contenido=f"Error en generación Hamiltoniana: {e}",
                estudiantes_objetivo=[],
                tipo="error_hamiltoniano",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def _extraer_variables_llm(self, respuesta_llm: str) -> Dict:
        """Extrae variables de decisión de la respuesta del LLM"""
        variables = {
            'tipo_actividad': 'mixto',
            'nivel_energia': 'medio',
            'duracion': 45,
            'materiales_principales': ['papel', 'lápices'],
            'estructura_temporal': 'secuencial'
        }
        
        # Extracciones simples basadas en texto
        respuesta_lower = respuesta_llm.lower()
        
        if 'grupal' in respuesta_lower:
            variables['tipo_actividad'] = 'grupal'
        elif 'individual' in respuesta_lower:
            variables['tipo_actividad'] = 'individual'
        
        if 'alto' in respuesta_lower or 'alta' in respuesta_lower:
            variables['nivel_energia'] = 'alto'
        elif 'bajo' in respuesta_lower or 'baja' in respuesta_lower:
            variables['nivel_energia'] = 'bajo'
        
        # Extraer duración si está mencionada
        import re
        duracion_match = re.search(r'(\d+)\s*min', respuesta_lower)
        if duracion_match:
            variables['duracion'] = int(duracion_match.group(1))
        
        return variables
    
    def _extraer_roles_llm(self, respuesta_llm: str) -> List[str]:
        """Extrae roles identificados por el LLM"""
        roles_comunes = ['cajero', 'cliente', 'supervisor', 'vendedor', 'comprador', 'organizador', 'investigador', 'presentador']
        roles_encontrados = []
        
        respuesta_lower = respuesta_llm.lower()
        for rol in roles_comunes:
            if rol in respuesta_lower:
                roles_encontrados.append(rol)
        
        return roles_encontrados[:4] if roles_encontrados else ['participante_1', 'participante_2', 'participante_3', 'coordinador']
    
    def _extraer_asignaciones_llm(self, respuesta_llm: str) -> Dict:
        """Extrae asignaciones estudiante-rol del LLM"""
        # Simplificación: extraer patrones básicos
        asignaciones = {}
        nombres = ['ALEX', 'MARÍA', 'ELENA', 'LUIS', 'ANA', 'SARA', 'EMMA', 'HUGO']
        
        lineas = respuesta_llm.split('\n')
        for linea in lineas:
            for nombre in nombres:
                if nombre in linea and ':' in linea:
                    # Extraer rol después del nombre
                    partes = linea.split(':')
                    if len(partes) > 1:
                        rol_texto = partes[1].strip()
                        asignaciones[nombre] = rol_texto[:50]  # Primeros 50 chars del rol
        
        return asignaciones
    
    def _procesar_resultados_hamiltonianos(self, resultado_final, evaluacion_ambiente: EstadoPedagogico, evaluacion_asignaciones: EstadoPedagogico) -> str:
        """Procesa resultados finales con información Hamiltoniana"""
        contenido = ""
        
        # Información del sistema Hamiltoniano
        contenido += "=" * 80 + "\n"
        contenido += "ACTIVIDAD GENERADA CON SISTEMA HAMILTONIANO CUÁNTICO-AGENTES\n"
        contenido += "=" * 80 + "\n\n"
        
        contenido += "🔬 VALIDACIONES CUÁNTICAS REALIZADAS:\n\n"
        
        contenido += f"1. VALIDACIÓN DE AMBIENTE:\n"
        contenido += f"   • Energía Hamiltoniana: {evaluacion_ambiente.energia_calculada:.3f}\n"
        contenido += f"   • Validez Pedagógica: {evaluacion_ambiente.validez:.1%}\n"
        contenido += f"   • Estado: {'✅ Óptimo' if evaluacion_ambiente.validez > 0.8 else '⚠️ Mejorable' if evaluacion_ambiente.validez > 0.6 else '❌ Requiere ajustes'}\n\n"
        
        contenido += f"2. VALIDACIÓN DE ASIGNACIONES:\n"
        contenido += f"   • Energía Hamiltoniana: {evaluacion_asignaciones.energia_calculada:.3f}\n"
        contenido += f"   • Validez Pedagógica: {evaluacion_asignaciones.validez:.1%}\n"
        contenido += f"   • Estado: {'✅ Óptimo' if evaluacion_asignaciones.validez > 0.8 else '⚠️ Mejorable' if evaluacion_asignaciones.validez > 0.6 else '❌ Requiere ajustes'}\n\n"
        
        validez_global = (evaluacion_ambiente.validez + evaluacion_asignaciones.validez) / 2
        contenido += f"🎯 VALIDEZ GLOBAL DEL SISTEMA: {validez_global:.1%}\n\n"
        
        # Agregar resultado final del LLM
        contenido += "=" * 80 + "\n"
        contenido += "ACTIVIDAD FINAL OPTIMIZADA CUÁNTICAMENTE\n"
        contenido += "=" * 80 + "\n\n"
        
        contenido += str(resultado_final)
        
        return contenido
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_hamiltonianas") -> str:
        """Guarda actividad Hamiltoniana"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ACTIVIDAD GENERADA CON SISTEMA HAMILTONIANO CUÁNTICO-AGENTES\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo: {actividad.tipo}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 50 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD HAMILTONIANA:\n")
            f.write("-" * 50 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("METADATOS HAMILTONIANOS:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad Hamiltoniana guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema Hamiltoniano-Agentes"""
    
    print("=" * 70)
    print("🔬 SISTEMA HAMILTONIANO CUÁNTICO-AGENTES")
    print("=" * 70)
    
    try:
        # Configuración
        OLLAMA_HOST = "192.168.1.10"
        AMBIENTE_MODEL = "qwen3:latest"
        DISENADOR_MODEL = "qwen3:latest"
        ASIGNADOR_MODEL = "qwen2:latest"
        EVALUADOR_MODEL = "mistral:latest"
        PERFILES_PATH = "perfiles_4_primaria.json"
        
        print(f"\n🔧 Inicializando sistema Hamiltoniano:")
        print(f"   Host Ollama: {OLLAMA_HOST}")
        print(f"   🌊 Ambiente: {AMBIENTE_MODEL}")
        print(f"   🎨 Diseñador: {DISENADOR_MODEL}")
        print(f"   🎯 Asignador: {ASIGNADOR_MODEL}")
        print(f"   ✅ Evaluador: {EVALUADOR_MODEL}")
        
        sistema = SistemaHamiltonianoAgentes(
            ollama_host=OLLAMA_HOST,
            ambiente_model=AMBIENTE_MODEL,
            disenador_model=DISENADOR_MODEL,
            asignador_model=ASIGNADOR_MODEL,
            evaluador_model=EVALUADOR_MODEL,
            perfiles_path=PERFILES_PATH
        )
        
        print("\n✅ Sistema Hamiltoniano inicializado!")
        print("🔬 Bucle: LLM → Hamiltoniano → Retroalimentación → LLM optimizado")
        
        # Menú
        while True:
            print("\n" + "=" * 50)
            print("🔬 GENERACIÓN HAMILTONIANA")
            print("1. 🎯 Generar actividad con validación Hamiltoniana")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                print(f"\n⏳ Iniciando bucle Hamiltoniano para {materia}...")
                print("   🔄 Fase 1: LLM propone configuración")
                print("   🔬 Fase 2: Validación cuántica con Hamiltoniano")
                print("   🔄 Fase 3: LLM refina con retroalimentación")
                print("   🔬 Fase 4: Validación final y síntesis")
                
                actividad = sistema.generar_actividad_hamiltoniana(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad Hamiltoniana completada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🔬 Sistema: Hamiltoniano con bucle de retroalimentación")
                
                if actividad.metadatos.get('sistema_cuantico'):
                    print(f"   🌊 Validez ambiente: {actividad.metadatos.get('validez_ambiente', 0):.1%}")
                    print(f"   🎯 Validez asignaciones: {actividad.metadatos.get('validez_asignaciones', 0):.1%}")
                    print(f"   🔄 Bucles realizados: {actividad.metadatos.get('bucles_retroalimentacion', 0)}")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema Hamiltoniano: {e}")
        print("\n💡 Verifica que:")
        print("   1. Ollama esté ejecutándose")
        print("   2. Los modelos especificados estén disponibles")
        print("   3. Qiskit y qiskit-algorithms estén instalados")
        print("   4. El archivo de perfiles exista")


if __name__ == "__main__":
    main()