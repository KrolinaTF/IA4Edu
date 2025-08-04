#!/usr/bin/env python3
"""
Generador Cuántico de Actividades Educativas
===========================================

Sistema basado en simulación cuántica con Qiskit que optimiza actividades
para generar adaptaciones INHERENTES (no específicas por estudiante).

La idea: crear un "terreno preparado" donde la actividad incluye naturalmente
múltiples formas de participación que permiten a cada estudiante contribuir
según sus fortalezas, sin etiquetas específicas.

Proceso:
1. Simulación cuántica para explorar espacio de configuraciones de actividad
2. Optimización hacia actividades con máxima "inclusión inherente" 
3. Generación de prompt optimizado para LLM
4. Human-in-the-loop para ajuste fino
"""

import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configuración
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"

try:
    from qiskit import QuantumCircuit, transpile, assemble
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.algorithms.optimizers import SPSA
    from qiskit.algorithms import VQE
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("⚠️ Qiskit no disponible - usando simulación clásica")

@dataclass
class ConfiguracionActividad:
    """Configuración de actividad educativa con inclusión inherente"""
    fases: List[str]  # Lista de fases de la actividad
    roles_disponibles: List[str]  # Roles que los estudiantes pueden tomar
    modalidades: List[str]  # visual, auditivo, kinestésico, etc.
    tipos_interaccion: List[str]  # individual, parejas, grupal, etc.
    nivel_estructura: float  # 0.0 (muy libre) a 1.0 (muy estructurado)
    nivel_colaboracion: float  # 0.0 (individual) a 1.0 (muy colaborativo)
    flexibilidad_tiempo: float  # 0.0 (rígido) a 1.0 (muy flexible)
    inclusion_score: float  # Puntuación de inclusión inherente

@dataclass
class EstudiantePerfilCuantico:
    """Perfil de estudiante codificado para simulación cuántica"""
    id: str
    necesidades_estructura: float  # 0.0 a 1.0
    preferencia_social: float  # 0.0 (individual) a 1.0 (grupal)
    canal_dominante: int  # 0=visual, 1=auditivo, 2=kinestésico
    tolerancia_incertidumbre: float  # 0.0 a 1.0
    capacidad_atencion: float  # 0.0 a 1.0
    creatividad_vs_estructura: float  # 0.0 (estructura) a 1.0 (creatividad)

class CodificadorPerfiles:
    """Convierte perfiles de estudiantes en representación cuántica"""
    
    def __init__(self):
        self.diagnosticos_map = {
            'TEA_nivel_1': {'estructura': 0.9, 'social': 0.2, 'incertidumbre': 0.1},
            'TDAH_combinado': {'estructura': 0.7, 'social': 0.8, 'atencion': 0.3},
            'altas_capacidades': {'creatividad': 0.9, 'estructura': 0.3, 'incertidumbre': 0.8},
            'ninguno': {'estructura': 0.5, 'social': 0.6, 'incertidumbre': 0.6}
        }
        
        self.canales_map = {
            'visual': 0, 'auditivo': 1, 'kinestésico': 2
        }
        
        # Principios DUA como tensores cuánticos 
        self.tensores_dua = self._construir_tensores_dua_cuanticos()
        
        # Operadores cuánticos DUA
        self.operadores_dua = self._crear_operadores_dua_cuanticos()
    
    def _construir_tensores_dua_cuanticos(self) -> Dict:
        """Construye tensores cuánticos para los principios DUA"""
        
        # Estados base cuánticos para cada principio DUA
        # |0⟩ = deficiente, |1⟩ = óptimo
        estado_0 = np.array([1, 0], dtype=complex)
        estado_1 = np.array([0, 1], dtype=complex)
        
        # Superposiciones para representación múltiple
        superposicion_visual_auditiva = (estado_0 + estado_1) / np.sqrt(2)
        superposicion_multimodal = (estado_0 + 1j * estado_1) / np.sqrt(2)
        
        return {
            'representacion': {
                # Tensor 3D: visual ⊗ auditivo ⊗ kinestésico
                'percepcion_multimodal': np.kron(
                    np.kron(estado_1, superposicion_visual_auditiva), 
                    estado_0
                ),
                # Tensor para lenguaje y símbolos
                'lenguaje_tensor': np.kron(estado_1, superposicion_multimodal),
                # Tensor de comprensión
                'comprension_tensor': np.outer(estado_1, estado_1.conj())
            },
            'accion_expresion': {
                # Tensor de medios físicos
                'medios_fisicos_tensor': np.kron(
                    superposicion_multimodal, 
                    estado_1
                ),
                # Tensor de expresión y comunicación
                'expresion_tensor': np.array([
                    [0.8, 0.2], 
                    [0.3, 0.9]
                ], dtype=complex),
                # Tensor de funciones ejecutivas
                'ejecutivas_tensor': np.kron(estado_1, estado_1)
            },
            'implicacion': {
                # Tensor de interés y motivación
                'interes_tensor': np.array([
                    [0.8+0.2j, 0.7], 
                    [0.9, 0.8-0.1j]
                ], dtype=complex),
                # Tensor de esfuerzo y persistencia
                'esfuerzo_tensor': superposicion_multimodal,
                # Tensor de autorregulación
                'autorregulacion_tensor': np.outer(
                    superposicion_visual_auditiva, 
                    superposicion_visual_auditiva.conj()
                )
            }
        }
    
    def _crear_operadores_dua_cuanticos(self) -> Dict:
        """Crea operadores cuánticos para aplicar principios DUA"""
        
        # Operadores de Pauli
        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
        identidad = np.array([[1, 0], [0, 1]], dtype=complex)
        
        # Operadores DUA específicos
        return {
            'transformacion_representacion': sigma_x,  # Cambiar modalidad
            'amplificacion_expresion': sigma_y,        # Amplificar capacidad expresiva
            'regulacion_implicacion': sigma_z,         # Regular motivación
            'superposicion_habilidades': (sigma_x + sigma_y) / np.sqrt(2),
            'medicion_competencia': np.outer(
                np.array([1, 0]), np.array([1, 0])
            ),  # Proyector sobre competencia adquirida
            # Operadores compuestos para interacciones DUA
            'interaccion_rep_exp': np.kron(sigma_x, sigma_y),
            'interaccion_exp_imp': np.kron(sigma_y, sigma_z),
            'interaccion_imp_rep': np.kron(sigma_z, sigma_x)
        }
    
    def codificar_estudiante(self, perfil: Dict) -> EstudiantePerfilCuantico:
        """Convierte perfil tradicional a representación cuántica"""
        
        dx = perfil.get('diagnostico_formal', 'ninguno')
        dx_params = self.diagnosticos_map.get(dx, self.diagnosticos_map['ninguno'])
        
        return EstudiantePerfilCuantico(
            id=perfil['id'],
            necesidades_estructura=dx_params.get('estructura', 0.5),
            preferencia_social=dx_params.get('social', 0.6),
            canal_dominante=self.canales_map.get(perfil.get('canal_preferido', 'visual'), 0),
            tolerancia_incertidumbre=dx_params.get('incertidumbre', 0.6),
            capacidad_atencion=dx_params.get('atencion', 0.7),
            creatividad_vs_estructura=1.0 - dx_params.get('estructura', 0.5)
        )
    
    def codificar_aula(self, estudiantes: List[Dict]) -> List[EstudiantePerfilCuantico]:
        """Codifica todos los estudiantes del aula"""
        return [self.codificar_estudiante(est) for est in estudiantes]
    
    def calcular_compatibilidad_dua_cuantica(self, estudiante: EstudiantePerfilCuantico, 
                                           config: Dict[str, float]) -> float:
        """Calcula compatibilidad usando tensores cuánticos DUA"""
        
        # Codificar estudiante como estado cuántico DUA
        estado_estudiante = self._codificar_estado_dua_estudiante(estudiante)
        
        # Aplicar operadores DUA según configuración de actividad
        operador_actividad = self._construir_operador_actividad(config)
        
        # Evolución cuántica: |ψ_final⟩ = U_actividad |ψ_estudiante⟩
        estado_evolucionado = np.dot(operador_actividad, estado_estudiante)
        
        # Medir compatibilidad mediante expectation value
        operador_medicion = self.operadores_dua['medicion_competencia']
        compatibilidad = np.real(np.vdot(estado_evolucionado, 
                                       np.dot(operador_medicion, estado_evolucionado)))
        
        return min(1.0, max(0.0, compatibilidad))
    
    def _codificar_estado_dua_estudiante(self, estudiante: EstudiantePerfilCuantico) -> np.ndarray:
        """Codifica estudiante como estado cuántico en espacio DUA"""
        
        # Estado base según canal dominante
        if estudiante.canal_dominante == 0:  # Visual
            estado_base = np.array([1, 0], dtype=complex)
        elif estudiante.canal_dominante == 1:  # Auditivo
            estado_base = np.array([0, 1], dtype=complex)
        else:  # Kinestésico - superposición
            estado_base = np.array([1, 1], dtype=complex) / np.sqrt(2)
        
        # Amplificar según características del estudiante
        fase_social = 2 * np.pi * estudiante.preferencia_social
        fase_estructura = 2 * np.pi * estudiante.necesidades_estructura
        
        # Aplicar rotaciones según características
        factor_creatividad = np.exp(1j * fase_social) * estudiante.creatividad_vs_estructura
        factor_estructura = np.exp(1j * fase_estructura) * estudiante.necesidades_estructura
        
        # Estado final del estudiante en espacio DUA
        estado_estudiante = estado_base * (factor_creatividad + factor_estructura) / 2
        
        return estado_estudiante / np.linalg.norm(estado_estudiante)
    
    def _construir_operador_actividad(self, config: Dict[str, float]) -> np.ndarray:
        """Construye operador cuántico que representa la actividad"""
        
        # Operador base (identidad)
        operador = np.eye(2, dtype=complex)
        
        # Aplicar transformaciones según configuración
        if config.get('estructura', 0.5) > 0.6:
            # Alta estructura requiere regulación
            operador = np.dot(self.operadores_dua['regulacion_implicacion'], operador)
        
        if config.get('colaboracion', 0.5) > 0.6:
            # Alta colaboración requiere amplificación expresiva
            operador = np.dot(self.operadores_dua['amplificacion_expresion'], operador)
        
        if config.get('flexibilidad', 0.5) > 0.6:
            # Alta flexibilidad permite transformación de representación
            operador = np.dot(self.operadores_dua['transformacion_representacion'], operador)
        
        return operador
    
    def aplicar_tensor_dua(self, principio: str, componente: str, 
                          estado_estudiante: np.ndarray) -> np.ndarray:
        """Aplica tensor DUA específico a estado de estudiante"""
        
        if principio not in self.tensores_dua or componente not in self.tensores_dua[principio]:
            return estado_estudiante
        
        tensor = self.tensores_dua[principio][componente]
        
        # Verificar dimensiones compatibles
        if tensor.shape[0] == len(estado_estudiante):
            if len(tensor.shape) == 1:  # Vector
                return tensor * np.vdot(tensor, estado_estudiante)
            else:  # Matriz
                return np.dot(tensor, estado_estudiante)
        
        return estado_estudiante
    
    def calcular_entrelazamiento_dua(self, est1: EstudiantePerfilCuantico, 
                                   est2: EstudiantePerfilCuantico) -> float:
        """Calcula entrelazamiento DUA entre dos estudiantes"""
        
        estado1 = self._codificar_estado_dua_estudiante(est1)
        estado2 = self._codificar_estado_dua_estudiante(est2)
        
        # Estado conjunto |ψ⟩ ⊗ |φ⟩
        estado_conjunto = np.kron(estado1, estado2)
        
        # Aplicar operadores de interacción DUA
        operador_interaccion = self.operadores_dua['interaccion_rep_exp']
        estado_entrelazado = np.dot(operador_interaccion, estado_conjunto)
        
        # Calcular entropía de entrelazamiento (medida de Schmidt)
        # Simplificado: usar overlap cuántico
        entrelazamiento = abs(np.vdot(estado_conjunto, estado_entrelazado))
        
        return min(1.0, entrelazamiento)
    
    # Mantener compatibilidad con versión anterior
    def calcular_compatibilidad_dua(self, estudiante: EstudiantePerfilCuantico, config: Dict[str, float]) -> float:
        """Versión de compatibilidad para mantener funcionalidad existente"""
        return self.calcular_compatibilidad_dua_cuantica(estudiante, config)

@dataclass
class CompetenciaCurricular:
    """Competencia curricular de 4º primaria según BOE"""
    area: str  # matematicas, lengua, ciencias, etc.
    competencia: str  # descripción de la competencia
    criterio_evaluacion: str
    peso_curricular: float  # 0.0 a 1.0

class CodificadorCuanticoBOE:
    """Codificación cuántica del BOE usando Hamiltonianos educativos"""
    
    def __init__(self):
        # Hamiltoniano BOE: H_BOE = H_competencias + H_criterios + H_objetivos
        self.hamiltoniano_boe = self._construir_hamiltoniano_educativo()
        
        # Estados cuánticos de competencias (|competencia⟩)
        self.estados_competencias = {
            'matematicas': {
                'numeros': np.array([1, 0, 0, 0], dtype=complex),
                'fracciones': np.array([0, 1, 0, 0], dtype=complex), 
                'geometria': np.array([0, 0, 1, 0], dtype=complex),
                'problemas': np.array([0, 0, 0, 1], dtype=complex)
            },
            'lengua': {
                'lectura': np.array([1, 0, 0], dtype=complex),
                'escritura': np.array([0, 1, 0], dtype=complex),
                'oral': np.array([0, 0, 1], dtype=complex)
            },
            'ciencias': {
                'seres_vivos': np.array([1, 0, 0], dtype=complex),
                'materia': np.array([0, 1, 0], dtype=complex),
                'metodo': np.array([0, 0, 1], dtype=complex)
            }
        }
        
        # Operadores de evolución curricular
        self.operadores_evolucion = self._crear_operadores_evolucion()
    
    def _construir_hamiltoniano_educativo(self) -> Dict:
        """Construye el Hamiltoniano cuántico del sistema educativo"""
        
        # H = α|competencia⟩⟨competencia| + β|criterio⟩⟨criterio| + γ|objetivo⟩⟨objetivo|
        hamiltoniano = {
            'matematicas': {
                'energia_base': 1.0,  # Energía fundamental matemáticas
                'acoplamientos': {
                    'numeros_fracciones': 0.8,  # Fuerte acoplamiento
                    'fracciones_geometria': 0.6,
                    'geometria_problemas': 0.9,
                    'numeros_problemas': 0.7
                },
                'campos_externos': {
                    'motivacion': 0.3,
                    'dificultad': 0.5,
                    'tiempo': 0.4
                }
            },
            'lengua': {
                'energia_base': 0.9,
                'acoplamientos': {
                    'lectura_escritura': 0.9,
                    'oral_lectura': 0.7,
                    'escritura_oral': 0.8
                },
                'campos_externos': {
                    'expresividad': 0.6,
                    'comprension': 0.8,
                    'creatividad': 0.5
                }
            },
            'ciencias': {
                'energia_base': 0.8,
                'acoplamientos': {
                    'seres_metodo': 0.7,
                    'materia_metodo': 0.8,
                    'seres_materia': 0.5
                },
                'campos_externos': {
                    'curiosidad': 0.8,
                    'experimentacion': 0.7,
                    'observacion': 0.9
                }
            }
        }
        
        return hamiltoniano
    
    def _crear_operadores_evolucion(self) -> Dict:
        """Crea operadores cuánticos de evolución curricular"""
        
        # Operador de Pauli para transiciones entre competencias
        pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
        pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
        
        return {
            'transicion_competencias': pauli_x,  # |comp_A⟩ → |comp_B⟩
            'superposicion_habilidades': (pauli_x + pauli_y) / np.sqrt(2),
            'medicion_evaluacion': pauli_z,  # Colapso a resultado evaluativo
            'entrelazamiento_areas': np.kron(pauli_x, pauli_y)  # Entre áreas curriculares
        }
    
    def evolucionar_competencia_cuantica(self, competencia_inicial: str, area: str, 
                                       actividad_params: Dict) -> complex:
        """Evoluciona una competencia usando mecánica cuántica"""
        
        if area not in self.estados_competencias:
            return 0.5 + 0j
        
        if competencia_inicial not in self.estados_competencias[area]:
            return 0.5 + 0j
        
        # Estado inicial |ψ⟩
        estado_inicial = self.estados_competencias[area][competencia_inicial]
        
        # Aplicar Hamiltoniano H|ψ⟩
        energia_base = self.hamiltoniano_boe[area]['energia_base']
        
        # Evolución temporal: |ψ(t)⟩ = e^(-iHt)|ψ(0)⟩
        tiempo_actividad = actividad_params.get('duracion', 1.0)
        fase = energia_base * tiempo_actividad
        
        # Factor de evolución cuántica
        factor_evolucion = np.exp(-1j * fase)
        estado_evolucionado = factor_evolucion * estado_inicial
        
        # Probabilidad de éxito (amplitud al cuadrado)
        probabilidad = np.abs(np.sum(estado_evolucionado)) ** 2
        
        return probabilidad

class MatrizEntrelazamiento:
    """Matriz cuántica de entrelazamiento estudiante-estudiante para colaboración óptima"""
    
    def __init__(self):
        self.matriz_entrelazamiento = None
        self.estados_estudiantes = {}
        self.operadores_colaboracion = self._crear_operadores_colaboracion()
    
    def _crear_operadores_colaboracion(self) -> Dict:
        """Crea operadores cuánticos para diferentes tipos de colaboración"""
        
        # Operadores de Bell para máximo entrelazamiento
        phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)  # |Φ+⟩
        phi_minus = np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2)  # |Φ-⟩
        psi_plus = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)  # |Ψ+⟩
        psi_minus = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)  # |Ψ-⟩
        
        return {
            'colaboracion_complementaria': phi_plus,    # Habilidades complementarias
            'colaboracion_refuerzo': phi_minus,         # Refuerzo mutuo
            'colaboracion_creativa': psi_plus,          # Sinergia creativa
            'colaboracion_competitiva': psi_minus       # Competencia constructiva
        }
    
    def construir_matriz_entrelazamiento(self, aula: List[EstudiantePerfilCuantico]) -> np.ndarray:
        """Construye matriz de entrelazamiento cuántico para el aula"""
        
        n_estudiantes = len(aula)
        self.matriz_entrelazamiento = np.zeros((n_estudiantes, n_estudiantes), dtype=complex)
        
        # Codificar cada estudiante como estado cuántico
        for i, estudiante in enumerate(aula):
            self.estados_estudiantes[i] = self._codificar_estudiante_cuantico(estudiante)
        
        # Calcular entrelazamientos por pares
        for i in range(n_estudiantes):
            for j in range(i + 1, n_estudiantes):
                entrelazamiento = self._calcular_entrelazamiento_par(
                    aula[i], aula[j], i, j
                )
                self.matriz_entrelazamiento[i][j] = entrelazamiento
                self.matriz_entrelazamiento[j][i] = np.conj(entrelazamiento)  # Hermitiana
        
        return self.matriz_entrelazamiento
    
    def _codificar_estudiante_cuantico(self, estudiante: EstudiantePerfilCuantico) -> np.ndarray:
        """Codifica estudiante como estado cuántico |ψ⟩ = α|0⟩ + β|1⟩"""
        
        # Amplitud basada en características del estudiante
        alpha = np.sqrt(estudiante.necesidades_estructura)
        beta = np.sqrt(1 - estudiante.necesidades_estructura)
        
        # Fase basada en preferencias
        fase_social = 2 * np.pi * estudiante.preferencia_social
        fase_creatividad = 2 * np.pi * estudiante.creatividad_vs_estructura
        
        # Estado cuántico complejo
        estado = np.array([
            alpha * np.exp(1j * fase_social),
            beta * np.exp(1j * fase_creatividad)
        ], dtype=complex)
        
        return estado / np.linalg.norm(estado)  # Normalizar
    
    def _calcular_entrelazamiento_par(self, est1: EstudiantePerfilCuantico, 
                                    est2: EstudiantePerfilCuantico, i: int, j: int) -> complex:
        """Calcula entrelazamiento cuántico entre dos estudiantes"""
        
        estado1 = self.estados_estudiantes[i]
        estado2 = self.estados_estudiantes[j]
        
        # Producto tensorial |ψ⟩⊗|φ⟩
        estado_conjunto = np.kron(estado1, estado2)
        
        # Determinar tipo de colaboración óptima
        tipo_colaboracion = self._determinar_tipo_colaboracion(est1, est2)
        operador = self.operadores_colaboracion[tipo_colaboracion]
        
        # Overlap cuántico ⟨Ψ|Φ⟩
        entrelazamiento = np.vdot(operador, estado_conjunto)
        
        # Ajustar por compatibilidad de canales
        compatibilidad_canales = self._compatibilidad_canales(est1, est2)
        
        return entrelazamiento * compatibilidad_canales
    
    def _determinar_tipo_colaboracion(self, est1: EstudiantePerfilCuantico, 
                                    est2: EstudiantePerfilCuantico) -> str:
        """Determina el tipo óptimo de colaboración entre dos estudiantes"""
        
        # Análisis de características complementarias
        diff_estructura = abs(est1.necesidades_estructura - est2.necesidades_estructura)
        diff_social = abs(est1.preferencia_social - est2.preferencia_social)
        diff_creatividad = abs(est1.creatividad_vs_estructura - est2.creatividad_vs_estructura)
        
        if diff_estructura > 0.5:  # Muy diferentes en estructura
            return 'colaboracion_complementaria'
        elif diff_social < 0.3 and diff_creatividad < 0.3:  # Muy similares
            return 'colaboracion_refuerzo'
        elif est1.creatividad_vs_estructura > 0.7 and est2.creatividad_vs_estructura > 0.7:
            return 'colaboracion_creativa'
        else:
            return 'colaboracion_competitiva'
    
    def _compatibilidad_canales(self, est1: EstudiantePerfilCuantico, 
                              est2: EstudiantePerfilCuantico) -> float:
        """Calcula compatibilidad entre canales de aprendizaje"""
        
        # Complementariedad de canales
        if est1.canal_dominante != est2.canal_dominante:
            return 0.9  # Canales diferentes se complementan bien
        else:
            return 0.7  # Canales iguales pueden reforzarse
    
    def optimizar_grupos_cuanticos(self, aula: List[EstudiantePerfilCuantico], 
                                  num_grupos: int) -> List[List[int]]:
        """Optimiza formación de grupos usando entrelazamiento cuántico"""
        
        if self.matriz_entrelazamiento is None:
            self.construir_matriz_entrelazamiento(aula)
        
        n_estudiantes = len(aula)
        
        # Algoritmo cuántico de agrupación
        grupos_optimos = []
        estudiantes_restantes = list(range(n_estudiantes))
        tamaño_grupo = n_estudiantes // num_grupos
        
        for grupo_idx in range(num_grupos):
            if grupo_idx == num_grupos - 1:  # Último grupo toma los restantes
                grupos_optimos.append(estudiantes_restantes.copy())
                break
            
            # Seleccionar núcleo del grupo (máximo entrelazamiento promedio)
            mejor_nucleo = self._seleccionar_nucleo_cuantico(estudiantes_restantes)
            grupo_actual = [mejor_nucleo]
            estudiantes_restantes.remove(mejor_nucleo)
            
            # Completar grupo optimizando entrelazamiento total
            while len(grupo_actual) < tamaño_grupo and estudiantes_restantes:
                mejor_adicion = self._mejor_adicion_cuantica(grupo_actual, estudiantes_restantes)
                grupo_actual.append(mejor_adicion)
                estudiantes_restantes.remove(mejor_adicion)
            
            grupos_optimos.append(grupo_actual)
        
        return grupos_optimos
    
    def _seleccionar_nucleo_cuantico(self, candidatos: List[int]) -> int:
        """Selecciona el mejor núcleo para un grupo basado en entrelazamiento promedio"""
        
        mejor_score = -1
        mejor_candidato = candidatos[0]
        
        for candidato in candidatos:
            score_promedio = np.mean([
                abs(self.matriz_entrelazamiento[candidato][otro]) 
                for otro in candidatos if otro != candidato
            ])
            
            if score_promedio > mejor_score:
                mejor_score = score_promedio
                mejor_candidato = candidato
        
        return mejor_candidato
    
    def _mejor_adicion_cuantica(self, grupo_actual: List[int], 
                              candidatos: List[int]) -> int:
        """Encuentra la mejor adición al grupo basada en entrelazamiento total"""
        
        mejor_score = -1
        mejor_candidato = candidatos[0]
        
        for candidato in candidatos:
            # Calcular entrelazamiento total con el grupo
            score_total = sum(
                abs(self.matriz_entrelazamiento[candidato][miembro])
                for miembro in grupo_actual
            )
            
            if score_total > mejor_score:
                mejor_score = score_total
                mejor_candidato = candidato
        
        return mejor_candidato

class DistribuidorAutomaticoTareas:
    """Algoritmo cuántico de distribución automática de tareas basado en fortalezas emergentes"""
    
    def __init__(self):
        self.matriz_tareas = None
        self.matriz_fortalezas = None
        self.operador_asignacion = self._crear_operador_asignacion()
        
    def _crear_operador_asignacion(self) -> Dict:
        """Crea operadores cuánticos para asignación de tareas"""
        
        # Operadores para diferentes tipos de asignación
        hadamard = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        rotation_y = lambda theta: np.array([
            [np.cos(theta/2), -np.sin(theta/2)],
            [np.sin(theta/2), np.cos(theta/2)]
        ], dtype=complex)
        
        return {
            'superposicion_tareas': hadamard,  # Crear superposición de tareas posibles
            'rotacion_habilidad': rotation_y,  # Rotar hacia habilidad específica
            'medicion_asignacion': np.array([[1, 0], [0, 0]], dtype=complex)  # Colapsar a asignación
        }
    
    def analizar_actividad_para_tareas(self, config: ConfiguracionActividad, 
                                     aula: List[EstudiantePerfilCuantico]) -> Dict[str, List[str]]:
        """Analiza una actividad y extrae tareas distribuibles automáticamente"""
        
        # Banco de tareas emergentes según configuración
        tareas_base = {
            'organizacion': [
                'Coordinar materiales y recursos',
                'Gestionar cronograma y tiempos',
                'Distribuir roles dentro del grupo',
                'Mantener orden del espacio de trabajo'
            ],
            'investigacion': [
                'Buscar información relevante',
                'Sintetizar contenidos clave',
                'Verificar fuentes y datos',
                'Crear resúmenes y esquemas'
            ],
            'creacion': [
                'Diseñar elementos visuales',
                'Generar ideas innovadoras',
                'Crear contenido original',
                'Desarrollar prototipos o borradores'
            ],
            'comunicacion': [
                'Facilitar discusiones grupales',
                'Presentar resultados al aula',
                'Mediar conflictos o diferencias',
                'Documentar procesos y decisiones'
            ],
            'revision': [
                'Verificar calidad del trabajo',
                'Detectar errores o inconsistencias',
                'Proponer mejoras y optimizaciones',
                'Validar cumplimiento de objetivos'
            ]
        }
        
        # Seleccionar tareas según configuración de actividad
        tareas_actividad = {}
        
        if config.nivel_estructura > 0.6:
            tareas_actividad['organizacion'] = tareas_base['organizacion']
            tareas_actividad['revision'] = tareas_base['revision']
        
        if config.nivel_colaboracion > 0.5:
            tareas_actividad['comunicacion'] = tareas_base['comunicacion']
        
        if config.flexibilidad_tiempo > 0.4:
            tareas_actividad['investigacion'] = tareas_base['investigacion']
            tareas_actividad['creacion'] = tareas_base['creacion']
        
        # Filtrar tareas según tamaño del aula
        tareas_finales = {}
        total_tareas_deseadas = len(aula)  # Una tarea principal por estudiante
        
        for categoria, lista_tareas in tareas_actividad.items():
            num_tareas = min(len(lista_tareas), max(1, total_tareas_deseadas // len(tareas_actividad)))
            tareas_finales[categoria] = lista_tareas[:num_tareas]
            total_tareas_deseadas -= num_tareas
        
        return tareas_finales
    
    def distribuir_tareas_cuanticamente(self, tareas: Dict[str, List[str]], 
                                      aula: List[EstudiantePerfilCuantico],
                                      matriz_entrelazamiento: np.ndarray) -> Dict[str, Dict[str, Any]]:
        """Distribuye tareas usando algoritmos cuánticos de optimización"""
        
        # Construir matriz de compatibilidad tarea-estudiante
        self._construir_matriz_compatibilidad(tareas, aula)
        
        # Algoritmo cuántico de asignación óptima
        asignaciones = {}
        estudiantes_disponibles = list(range(len(aula)))
        
        # Aplanar tareas en lista única
        lista_tareas = []
        categorias_tareas = []
        for categoria, tareas_cat in tareas.items():
            for tarea in tareas_cat:
                lista_tareas.append(tarea)
                categorias_tareas.append(categoria)
        
        # Asignación cuántica usando superposición y medición
        for i, tarea in enumerate(lista_tareas):
            if not estudiantes_disponibles:
                break
                
            # Crear estado de superposición para estudiantes disponibles
            mejor_estudiante = self._asignar_tarea_cuantica(
                tarea, categorias_tareas[i], estudiantes_disponibles, 
                aula, matriz_entrelazamiento
            )
            
            # Registrar asignación
            estudiante = aula[mejor_estudiante]
            asignaciones[tarea] = {
                'estudiante_id': estudiante.id,
                'estudiante_idx': mejor_estudiante,
                'categoria': categorias_tareas[i],
                'compatibilidad': self.matriz_compatibilidad[i][mejor_estudiante],
                'justificacion': self._generar_justificacion(tarea, estudiante, categorias_tareas[i])
            }
            
            estudiantes_disponibles.remove(mejor_estudiante)
        
        return asignaciones
    
    def _construir_matriz_compatibilidad(self, tareas: Dict[str, List[str]], 
                                       aula: List[EstudiantePerfilCuantico]):
        """Construye matriz de compatibilidad tarea-estudiante"""
        
        # Aplanar tareas
        lista_tareas = []
        for tareas_cat in tareas.values():
            lista_tareas.extend(tareas_cat)
        
        n_tareas = len(lista_tareas)
        n_estudiantes = len(aula)
        
        self.matriz_compatibilidad = np.zeros((n_tareas, n_estudiantes))
        
        for i, tarea in enumerate(lista_tareas):
            for j, estudiante in enumerate(aula):
                compatibilidad = self._calcular_compatibilidad_tarea_estudiante(tarea, estudiante)
                self.matriz_compatibilidad[i][j] = compatibilidad
    
    def _calcular_compatibilidad_tarea_estudiante(self, tarea: str, 
                                                estudiante: EstudiantePerfilCuantico) -> float:
        """Calcula compatibilidad entre una tarea específica y un estudiante"""
        
        compatibilidad = 0.5  # Base neutral
        
        # Análisis semántico de la tarea
        tarea_lower = tarea.lower()
        
        # Tareas de organización
        if any(word in tarea_lower for word in ['coordinar', 'gestionar', 'organizar', 'mantener']):
            compatibilidad += estudiante.necesidades_estructura * 0.4
            
        # Tareas de investigación
        elif any(word in tarea_lower for word in ['buscar', 'investigar', 'sintetizar', 'verificar']):
            compatibilidad += (1 - estudiante.necesidades_estructura) * 0.3
            compatibilidad += estudiante.capacidad_atencion * 0.3
            
        # Tareas creativas
        elif any(word in tarea_lower for word in ['diseñar', 'crear', 'generar', 'innovar']):
            compatibilidad += estudiante.creatividad_vs_estructura * 0.5
            compatibilidad += estudiante.tolerancia_incertidumbre * 0.2
            
        # Tareas de comunicación
        elif any(word in tarea_lower for word in ['facilitar', 'presentar', 'comunicar', 'mediar']):
            compatibilidad += estudiante.preferencia_social * 0.5
            
        # Tareas de revisión
        elif any(word in tarea_lower for word in ['verificar', 'revisar', 'detectar', 'validar']):
            compatibilidad += estudiante.necesidades_estructura * 0.3
            compatibilidad += estudiante.capacidad_atencion * 0.4
        
        return min(1.0, compatibilidad)
    
    def _asignar_tarea_cuantica(self, tarea: str, categoria: str, 
                              estudiantes_disponibles: List[int],
                              aula: List[EstudiantePerfilCuantico],
                              matriz_entrelazamiento: np.ndarray) -> int:
        """Asigna una tarea usando algoritmos cuánticos"""
        
        if len(estudiantes_disponibles) == 1:
            return estudiantes_disponibles[0]
        
        # Crear vector de probabilidades cuánticas
        probabilidades = np.zeros(len(estudiantes_disponibles))
        
        for i, est_idx in enumerate(estudiantes_disponibles):
            # Compatibilidad base
            idx_tarea = self._encontrar_indice_tarea(tarea, categoria)
            prob_base = self.matriz_compatibilidad[idx_tarea][est_idx]
            
            # Amplificación por entrelazamiento con otros asignados
            amplificacion = 1.0
            for otro_est in range(len(aula)):
                if otro_est not in estudiantes_disponibles:  # Ya asignado
                    entrelazamiento = abs(matriz_entrelazamiento[est_idx][otro_est])
                    amplificacion += entrelazamiento * 0.2
            
            probabilidades[i] = prob_base * amplificacion
        
        # Normalizar probabilidades
        probabilidades = probabilidades / np.sum(probabilidades)
        
        # "Medición cuántica" - selección probabilística
        seleccion = np.random.choice(len(estudiantes_disponibles), p=probabilidades)
        return estudiantes_disponibles[seleccion]
    
    def _encontrar_indice_tarea(self, tarea: str, categoria: str) -> int:
        """Encuentra el índice de una tarea en la matriz de compatibilidad"""
        # Simplificado - en implementación real necesitaría mapeo completo
        return hash(tarea) % self.matriz_compatibilidad.shape[0]
    
    def _generar_justificacion(self, tarea: str, estudiante: EstudiantePerfilCuantico, 
                             categoria: str) -> str:
        """Genera justificación natural para la asignación"""
        
        justificaciones = {
            'organizacion': f"Asignado por sus habilidades organizativas y preferencia por estructura",
            'investigacion': f"Seleccionado por su capacidad de atención y enfoque analítico",
            'creacion': f"Elegido por su creatividad y tolerancia a la incertidumbre",
            'comunicacion': f"Designado por sus fuertes habilidades sociales y comunicativas",
            'revision': f"Asignado por su atención al detalle y enfoque meticuloso"
        }
        
        return justificaciones.get(categoria, "Asignado por compatibilidad con la tarea")

class CodificadorCurriculo:
    """Codifica competencias curriculares de 4º primaria"""
    
    def __init__(self):
        self.competencias_4_primaria = {
            'matematicas': {
                'numeros_operaciones': CompetenciaCurricular(
                    area='matematicas',
                    competencia='Números y operaciones hasta 10.000',
                    criterio_evaluacion='Leer, escribir, comparar y ordenar números naturales hasta 10.000',
                    peso_curricular=0.9
                ),
                'fracciones_decimales': CompetenciaCurricular(
                    area='matematicas', 
                    competencia='Fracciones y números decimales',
                    criterio_evaluacion='Interpretar fracciones sencillas y decimales hasta centésimas',
                    peso_curricular=0.8
                ),
                'geometria': CompetenciaCurricular(
                    area='matematicas',
                    competencia='Formas geométricas y medidas',
                    criterio_evaluacion='Reconocer y clasificar figuras geométricas, calcular perímetros y áreas',
                    peso_curricular=0.7
                ),
                'resolucion_problemas': CompetenciaCurricular(
                    area='matematicas',
                    competencia='Resolución de problemas matemáticos',
                    criterio_evaluacion='Aplicar estrategias de resolución de problemas en contextos reales',
                    peso_curricular=0.9
                )
            },
            'lengua': {
                'comprension_lectora': CompetenciaCurricular(
                    area='lengua',
                    competencia='Comprensión de textos escritos',
                    criterio_evaluacion='Comprender textos narrativos, descriptivos e informativos',
                    peso_curricular=0.9
                ),
                'expresion_escrita': CompetenciaCurricular(
                    area='lengua',
                    competencia='Producción de textos escritos',
                    criterio_evaluacion='Escribir textos coherentes con ortografía y gramática correctas',
                    peso_curricular=0.8
                ),
                'expresion_oral': CompetenciaCurricular(
                    area='lengua',
                    competencia='Comunicación oral',
                    criterio_evaluacion='Expresarse oralmente con claridad y corrección',
                    peso_curricular=0.7
                )
            },
            'ciencias': {
                'seres_vivos': CompetenciaCurricular(
                    area='ciencias',
                    competencia='Los seres vivos: células, tejidos y órganos',
                    criterio_evaluacion='Identificar estructuras básicas de los seres vivos',
                    peso_curricular=0.8
                ),
                'materia_energia': CompetenciaCurricular(
                    area='ciencias',
                    competencia='Materia y energía',
                    criterio_evaluacion='Conocer propiedades de la materia y formas de energía',
                    peso_curricular=0.7
                ),
                'metodo_cientifico': CompetenciaCurricular(
                    area='ciencias',
                    competencia='Iniciación al método científico',
                    criterio_evaluacion='Plantear hipótesis simples y realizar observaciones',
                    peso_curricular=0.6
                )
            }
        }
    
    def evaluar_cumplimiento_curricular(self, actividad_config: ConfiguracionActividad, 
                                      area_curricular: str) -> float:
        """Evalúa qué tan bien cumple una actividad con el currículo de 4º primaria"""
        
        if area_curricular not in self.competencias_4_primaria:
            return 0.5  # Puntuación neutral si no reconoce el área
        
        competencias_area = self.competencias_4_primaria[area_curricular]
        cumplimiento_total = 0.0
        peso_total = 0.0
        
        for comp_id, competencia in competencias_area.items():
            # Evaluar compatibilidad de la configuración con cada competencia
            score_competencia = self._evaluar_compatibilidad_competencia(
                actividad_config, competencia
            )
            
            cumplimiento_total += score_competencia * competencia.peso_curricular
            peso_total += competencia.peso_curricular
        
        return cumplimiento_total / peso_total if peso_total > 0 else 0.5
    
    def _evaluar_compatibilidad_competencia(self, config: ConfiguracionActividad, 
                                          competencia: CompetenciaCurricular) -> float:
        """Evalúa compatibilidad entre configuración de actividad y competencia curricular"""
        
        score = 0.5  # Base neutral
        
        # Evaluación específica por área
        if competencia.area == 'matematicas':
            if 'matemática' in str(config.fases).lower() or 'número' in str(config.fases).lower():
                score += 0.3
            if config.nivel_estructura > 0.6:  # Matemáticas requiere cierta estructura
                score += 0.2
                
        elif competencia.area == 'lengua':
            if 'comunicación' in str(config.tipos_interaccion).lower():
                score += 0.3
            if config.nivel_colaboracion > 0.5:  # Lengua se beneficia de colaboración
                score += 0.2
                
        elif competencia.area == 'ciencias':
            if 'experimento' in str(config.fases).lower() or 'observación' in str(config.fases).lower():
                score += 0.3
            if config.flexibilidad_tiempo > 0.6:  # Ciencias requiere flexibilidad para explorar
                score += 0.2
        
        return min(1.0, score)  # Limitar a máximo 1.0

class OptimizadorCuantico(ABC):
    """Interfaz abstracta para optimización cuántica/clásica"""
    
    @abstractmethod
    def optimizar_actividad(self, aula: List[EstudiantePerfilCuantico], 
                          intencion: str) -> ConfiguracionActividad:
        pass

class OptimizadorQiskit(OptimizadorCuantico):
    """Implementación con Qiskit para optimización cuántica real"""
    
    def __init__(self):
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit no disponible")
        
        self.simulator = AerSimulator()
        self.optimizer = SPSA(maxiter=100)
    
    def optimizar_actividad(self, aula: List[EstudiantePerfilCuantico], 
                          intencion: str) -> ConfiguracionActividad:
        """Optimiza configuración usando algoritmos cuánticos"""
        
        # Codificar problema como Hamiltoniano
        n_qubits = min(8, len(aula) + 3)  # Estudiantes + parámetros de actividad
        
        # Crear circuito variacional
        def crear_ansatz(params):
            qc = QuantumCircuit(n_qubits)
            
            # Capa de superposición inicial
            for i in range(n_qubits):
                qc.h(i)
            
            # Capas variacionales
            for layer in range(2):
                for i in range(n_qubits):
                    qc.ry(params[layer * n_qubits + i], i)
                
                # Entrelazamiento
                for i in range(n_qubits - 1):
                    qc.cx(i, i + 1)
            
            return qc
        
        # Función de coste: maximizar inclusión inherente + cumplimiento curricular
        def funcion_coste(params):
            qc = crear_ansatz(params)
            qc.measure_all()
            
            # Simular y extraer distribución
            transpiled = transpile(qc, self.simulator)
            job = self.simulator.run(transpiled, shots=1000)
            counts = job.result().get_counts()
            
            # Calcular inclusión basada en distribución de probabilidad
            inclusion_score = self._calcular_inclusion_desde_distribucion(counts, aula)
            
            # Calcular cumplimiento curricular
            config_temp = self._params_a_configuracion_temp(params)
            curriculum_score = self._evaluar_cumplimiento_curricular(config_temp, intencion)
            
            # Combinar ambos scores (70% inclusión + 30% currículo)
            score_total = 0.7 * inclusion_score + 0.3 * curriculum_score
            
            return -score_total  # Negativo porque VQE minimiza
        
        # Optimización
        initial_params = np.random.uniform(0, 2*np.pi, 2 * n_qubits)
        result = self.optimizer.minimize(funcion_coste, initial_params)
        
        # Convertir resultado óptimo a configuración
        return self._params_a_configuracion(result.x, aula, intencion)
    
    def _calcular_inclusion_desde_distribucion(self, counts: Dict, 
                                             aula: List[EstudiantePerfilCuantico]) -> float:
        """Calcula score de inclusión desde distribución cuántica"""
        
        total_shots = sum(counts.values())
        inclusion_total = 0.0
        
        for bitstring, count in counts.items():
            prob = count / total_shots
            
            # Interpretar bitstring como configuración de actividad
            config_params = self._bitstring_a_params(bitstring)
            
            # Calcular compatibilidad con cada estudiante
            compatibilidad_promedio = np.mean([
                self._compatibilidad_estudiante_config(est, config_params)
                for est in aula
            ])
            
            inclusion_total += prob * compatibilidad_promedio
        
        return inclusion_total
    
    def _bitstring_a_params(self, bitstring: str) -> Dict[str, float]:
        """Convierte bitstring cuántico a parámetros de configuración"""
        bits = [int(b) for b in bitstring]
        
        return {
            'estructura': sum(bits[:2]) / 2.0,
            'colaboracion': sum(bits[2:4]) / 2.0,
            'flexibilidad': sum(bits[4:6]) / 2.0,
        }
    
    def _compatibilidad_estudiante_config(self, estudiante: EstudiantePerfilCuantico, 
                                        config: Dict[str, float]) -> float:
        """Calcula compatibilidad entre estudiante y configuración usando DUA"""
        
        # Usar la nueva función DUA para cálculo de compatibilidad
        codificador = CodificadorPerfiles()
        return codificador.calcular_compatibilidad_dua(estudiante, config)
    
    def _params_a_configuracion_temp(self, params: np.ndarray) -> ConfiguracionActividad:
        """Convierte parámetros a configuración temporal para evaluación curricular"""
        estructura = (np.sin(params[0]) + 1) / 2
        colaboracion = (np.sin(params[1]) + 1) / 2
        flexibilidad = (np.sin(params[2]) + 1) / 2
        
        return ConfiguracionActividad(
            fases=["exploración", "desarrollo", "síntesis"],
            roles_disponibles=["investigador", "colaborador", "presentador"],
            modalidades=["visual", "auditivo", "kinestésico"],
            tipos_interaccion=["individual", "parejas", "grupal"],
            nivel_estructura=estructura,
            nivel_colaboracion=colaboracion,
            flexibilidad_tiempo=flexibilidad,
            inclusion_score=0.5  # Temporal
        )
    
    def _evaluar_cumplimiento_curricular(self, config: ConfiguracionActividad, intencion: str) -> float:
        """Evalúa cumplimiento curricular de una configuración"""
        codificador_curriculum = CodificadorCurriculo()
        
        # Inferir área curricular de la intención
        area = "matematicas"  # Default
        if "lengua" in intencion.lower() or "texto" in intencion.lower():
            area = "lengua"
        elif "ciencia" in intencion.lower() or "célula" in intencion.lower():
            area = "ciencias"
        elif "matemática" in intencion.lower() or "número" in intencion.lower():
            area = "matematicas"
        
        return codificador_curriculum.evaluar_cumplimiento_curricular(config, area)
    
    def _params_a_configuracion(self, params: np.ndarray, 
                              aula: List[EstudiantePerfilCuantico], 
                              intencion: str) -> ConfiguracionActividad:
        """Convierte parámetros optimizados a configuración de actividad"""
        
        # Extraer parámetros normalizados
        estructura = (np.sin(params[0]) + 1) / 2
        colaboracion = (np.sin(params[1]) + 1) / 2
        flexibilidad = (np.sin(params[2]) + 1) / 2
        
        # Generar configuración optimizada
        return ConfiguracionActividad(
            fases=self._generar_fases_optimizadas(estructura, intencion),
            roles_disponibles=self._generar_roles_optimizados(aula, colaboracion),
            modalidades=self._generar_modalidades_optimizadas(aula),
            tipos_interaccion=self._generar_interacciones_optimizadas(colaboracion),
            nivel_estructura=estructura,
            nivel_colaboracion=colaboracion,
            flexibilidad_tiempo=flexibilidad,
            inclusion_score=self._calcular_inclusion_final(params, aula)
        )
    
    def _generar_fases_optimizadas(self, nivel_estructura: float, intencion: str) -> List[str]:
        """Genera fases adaptadas al nivel de estructura óptimo"""
        
        if nivel_estructura > 0.7:
            return [
                "Preparación guiada con instrucciones claras",
                "Ejecución por pasos definidos", 
                "Verificación y ajustes",
                "Presentación estructurada"
            ]
        elif nivel_estructura > 0.4:
            return [
                "Exploración inicial libre",
                "Organización colaborativa",
                "Desarrollo flexible",
                "Reflexión compartida"
            ]
        else:
            return [
                "Brainstorming abierto",
                "Experimentación libre",
                "Síntesis creativa",
                "Presentación innovadora"
            ]
    
    def _generar_roles_optimizados(self, aula: List[EstudiantePerfilCuantico], 
                                 colaboracion: float) -> List[str]:
        """Genera roles que aprovechan las fortalezas naturales del aula"""
        
        roles_base = [
            "Organizador de materiales",
            "Coordinador de tiempos", 
            "Documentador visual",
            "Facilitador de ideas",
            "Verificador de calidad",
            "Presentador principal"
        ]
        
        # Ajustar según nivel de colaboración
        if colaboracion > 0.6:
            roles_base.extend([
                "Mediador de conflictos",
                "Integrador de perspectivas",
                "Motivador del equipo"
            ])
        
        return roles_base
    
    def _generar_modalidades_optimizadas(self, aula: List[EstudiantePerfilCuantico]) -> List[str]:
        """Genera modalidades que cubren los canales del aula"""
        
        canales_presentes = set(est.canal_dominante for est in aula)
        modalidades = []
        
        if 0 in canales_presentes:  # Visual
            modalidades.extend(["esquemas", "diagramas", "mapas_conceptuales"])
        
        if 1 in canales_presentes:  # Auditivo  
            modalidades.extend(["discusiones", "presentaciones_orales", "grabaciones"])
        
        if 2 in canales_presentes:  # Kinestésico
            modalidades.extend(["manipulación_objetos", "experimentos", "construcción"])
        
        return modalidades
    
    def _generar_interacciones_optimizadas(self, colaboracion: float) -> List[str]:
        """Genera tipos de interacción según nivel de colaboración"""
        
        if colaboracion > 0.7:
            return ["trabajo_grupal", "discusión_plenaria", "construcción_conjunta"]
        elif colaboracion > 0.4:
            return ["trabajo_parejas", "intercambio_roles", "revisión_cruzada"]
        else:
            return ["trabajo_individual", "presentación_personal", "autoevaluación"]
    
    def _calcular_inclusion_final(self, params: np.ndarray, 
                                aula: List[EstudiantePerfilCuantico]) -> float:
        """Calcula score final de inclusión"""
        
        # Simulación final para calcular inclusión
        config_final = {
            'estructura': (np.sin(params[0]) + 1) / 2,
            'colaboracion': (np.sin(params[1]) + 1) / 2,
            'flexibilidad': (np.sin(params[2]) + 1) / 2
        }
        
        inclusiones = [
            self._compatibilidad_estudiante_config(est, config_final)
            for est in aula
        ]
        
        return np.mean(inclusiones)
    
class OptimizadorClasico(OptimizadorCuantico):
    """Implementación clásica como respaldo cuando Qiskit no está disponible"""
    
    def __init__(self):
        self.codificador = CodificadorPerfiles()
    
    def optimizar_actividad(self, aula: List[EstudiantePerfilCuantico], 
                          intencion: str) -> ConfiguracionActividad:
        """Optimiza usando algoritmos clásicos"""
        
        # Análisis del aula
        estructura_promedio = np.mean([est.necesidades_estructura for est in aula])
        social_promedio = np.mean([est.preferencia_social for est in aula])
        incertidumbre_promedio = np.mean([est.tolerancia_incertidumbre for est in aula])
        
        # Optimización heurística para maximizar inclusión
        nivel_estructura = self._optimizar_estructura(aula, intencion)
        nivel_colaboracion = self._optimizar_colaboracion(aula)
        nivel_flexibilidad = self._optimizar_flexibilidad(aula)
        
        # Generar configuración
        return ConfiguracionActividad(
            fases=self._generar_fases_clasicas(nivel_estructura, intencion),
            roles_disponibles=self._generar_roles_clasicos(aula, nivel_colaboracion),
            modalidades=self._generar_modalidades_clasicas(aula),
            tipos_interaccion=self._generar_interacciones_clasicas(nivel_colaboracion),
            nivel_estructura=nivel_estructura,
            nivel_colaboracion=nivel_colaboracion,
            flexibilidad_tiempo=nivel_flexibilidad,
            inclusion_score=self._calcular_inclusion_clasica(aula, nivel_estructura, 
                                                           nivel_colaboracion, nivel_flexibilidad)
        )
    
    def _optimizar_estructura(self, aula: List[EstudiantePerfilCuantico], intencion: str) -> float:
        """Optimiza nivel de estructura para el aula"""
        
        # Peso hacia estructura si hay estudiantes que la necesitan
        necesidades_altas = sum(1 for est in aula if est.necesidades_estructura > 0.7)
        peso_estructura = necesidades_altas / len(aula)
        
        # Ajuste según intención
        if any(word in intencion.lower() for word in ['crear', 'libre', 'creativ']):
            return 0.3 + peso_estructura * 0.4  # Más creatividad, pero con estructura si se necesita
        else:
            return 0.5 + peso_estructura * 0.3
    
    def _optimizar_colaboracion(self, aula: List[EstudiantePerfilCuantico]) -> float:
        """Optimiza nivel de colaboración"""
        
        # Balancear preferencias sociales
        preferencias = [est.preferencia_social for est in aula]
        return np.mean(preferencias)
    
    def _optimizar_flexibilidad(self, aula: List[EstudiantePerfilCuantico]) -> float:
        """Optimiza nivel de flexibilidad temporal"""
        
        # Basado en tolerancia a incertidumbre y capacidad de atención
        tolerancias = [est.tolerancia_incertidumbre for est in aula]
        atenciones = [est.capacidad_atencion for est in aula]
        
        return (np.mean(tolerancias) + np.mean(atenciones)) / 2
    
    def _generar_fases_clasicas(self, estructura: float, intencion: str) -> List[str]:
        """Genera fases optimizadas clásicamente"""
        
        if estructura > 0.7:
            return [
                "Instrucciones claras y ejemplos",
                "Distribución de roles específicos",
                "Trabajo por etapas definidas",
                "Revisión y presentación guiada"
            ]
        elif estructura > 0.4:
            return [
                "Exploración guiada del tema",
                "Organización flexible en grupos",
                "Desarrollo con check-points",
                "Síntesis colaborativa"
            ]
        else:
            return [
                "Lluvia de ideas abierta",
                "Auto-organización de grupos",
                "Experimentación libre",
                "Presentación creativa"
            ]
    
    def _generar_roles_clasicos(self, aula: List[EstudiantePerfilCuantico], 
                              colaboracion: float) -> List[str]:
        """Genera roles optimizados clásicamente"""
        
        roles = [
            "Investigador de información",
            "Organizador de ideas", 
            "Creador de contenido visual",
            "Redactor principal",
            "Revisor de calidad",
            "Coordinador de presentación"
        ]
        
        if colaboracion > 0.6:
            roles.extend([
                "Facilitador de discusiones",
                "Integrador de aportes",
                "Gestor de consensos"
            ])
        
        return roles
    
    def _generar_modalidades_clasicas(self, aula: List[EstudiantePerfilCuantico]) -> List[str]:
        """Genera modalidades para todos los canales representados"""
        
        modalidades = ["trabajo_escrito", "presentacion_oral"]  # Base
        
        canales = [est.canal_dominante for est in aula]
        
        if 0 in canales:  # Visual
            modalidades.extend(["infografias", "esquemas", "mapas_mentales"])
        
        if 1 in canales:  # Auditivo
            modalidades.extend(["debates", "grabaciones", "música"])
        
        if 2 in canales:  # Kinestésico  
            modalidades.extend(["experimentos", "maquetas", "dramatizaciones"])
        
        return modalidades
    
    def _generar_interacciones_clasicas(self, colaboracion: float) -> List[str]:
        """Genera tipos de interacción"""
        
        base = ["individual", "parejas"]
        
        if colaboracion > 0.5:
            base.extend(["grupos_pequeños", "plenario"])
        
        if colaboracion > 0.7:
            base.extend(["rotación_roles", "peer_review"])
        
        return base
    
    def _calcular_inclusion_clasica(self, aula: List[EstudiantePerfilCuantico],
                                  estructura: float, colaboracion: float, 
                                  flexibilidad: float) -> float:
        """Calcula inclusión para configuración clásica"""
        
        config = {
            'estructura': estructura,
            'colaboracion': colaboracion,
            'flexibilidad': flexibilidad
        }
        
        inclusiones = []
        for est in aula:
            # Compatibilidad de estructura
            diff_est = abs(est.necesidades_estructura - estructura)
            comp_est = 1.0 - diff_est
            
            # Compatibilidad social
            diff_soc = abs(est.preferencia_social - colaboracion)
            comp_soc = 1.0 - diff_soc
            
            # Compatibilidad de flexibilidad
            diff_flex = abs(est.tolerancia_incertidumbre - flexibilidad)
            comp_flex = 1.0 - diff_flex
            
            inclusion_estudiante = (comp_est + comp_soc + comp_flex) / 3.0
            inclusiones.append(inclusion_estudiante)
        
        return np.mean(inclusiones)

class GeneradorPromptOptimizado:
    """Genera prompts optimizados para LLM basados en configuración cuántica"""
    
    def __init__(self):
        self.llm = self._setup_llm()
        self.ejemplos_k = self._cargar_ejemplos_k()
    
    def _setup_llm(self):
        """Setup LLM"""
        try:
            try:
                from langchain_ollama import OllamaLLM
                return OllamaLLM(model="qwen3:latest", base_url="http://192.168.1.10:11434")
            except ImportError:
                from langchain_community.llms import Ollama
                return Ollama(model="qwen3:latest", base_url="http://192.168.1.10:11434")
        except Exception:
            return None
    
    def _cargar_ejemplos_k(self) -> List[str]:
        """Carga tus ejemplos k_ para few-shot learning"""
        
        import glob
        import os
        
        ejemplos = []
        
        # Buscar archivos k_ en varias ubicaciones posibles
        posibles_rutas = [
            "actividades_generadas/k_*.txt",
            "../actividades_generadas/k_*.txt", 
            "../../PoC/PoC_entrenamiento_llm/actividades_generadas/k_*.txt",
            "/mnt/c/carolina/anfaia/ia4edu/PoC/PoC_entrenamiento_llm/actividades_generadas/k_*.txt"
        ]
        
        archivos_encontrados = []
        for patron in posibles_rutas:
            archivos = glob.glob(patron)
            if archivos:
                archivos_encontrados.extend(archivos)
                print(f"🎯 Encontrados {len(archivos)} archivos k_ en: {os.path.dirname(patron)}")
                break
        
        if not archivos_encontrados:
            print("⚠️ No se encontraron archivos k_ en ninguna ubicación")
            return []
        
        # Seleccionar los 3 archivos más relevantes
        archivos_k = archivos_encontrados[:3]
        
        for archivo in archivos_k:
            try:
                print(f"🔍 Intentando cargar: {archivo}")
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    if contenido.strip():
                        # Tomar solo las primeras 500 palabras para no saturar el prompt
                        palabras = contenido.split()[:500]
                        ejemplo = ' '.join(palabras)
                        ejemplos.append(f"=== EJEMPLO DE ACTIVIDAD EXITOSA ===\n{ejemplo}\n")
                        print(f"✅ Cargado exitosamente: {archivo}")
                    else:
                        print(f"⚠️ Archivo vacío: {archivo}")
            except FileNotFoundError as e:
                print(f"⚠️ No se encontró {archivo}: {e}")
            except UnicodeDecodeError as e:
                print(f"⚠️ Error de encoding en {archivo}: {e}")
                # Intentar con latin-1
                try:
                    with open(archivo, 'r', encoding='latin-1') as f:
                        contenido = f.read()
                        palabras = contenido.split()[:500]
                        ejemplo = ' '.join(palabras)
                        ejemplos.append(f"=== EJEMPLO DE ACTIVIDAD EXITOSA ===\n{ejemplo}\n")
                        print(f"✅ Cargado con latin-1: {archivo}")
                except Exception as e2:
                    print(f"⚠️ Error definitivo en {archivo}: {e2}")
            except Exception as e:
                print(f"⚠️ Error inesperado cargando {archivo}: {e}")
        
        print(f"📊 Resumen de carga: {len(ejemplos)} ejemplos k_ cargados exitosamente")
        return ejemplos
    
    def _seleccionar_ejemplos_relevantes(self, intencion: str) -> str:
        """Selecciona los ejemplos más relevantes según la intención"""
        
        if not self.ejemplos_k:
            return ""
        
        # Análisis básico de la intención para seleccionar ejemplos
        intencion_lower = intencion.lower()
        
        ejemplos_seleccionados = []
        
        # Lógica simple de selección
        if any(word in intencion_lower for word in ['matemática', 'números', 'contar', 'sumar']):
            # Preferir ejemplo de supermercado o feria de acertijos
            ejemplos_seleccionados = [ej for ej in self.ejemplos_k if 'supermercado' in ej.lower() or 'feria' in ej.lower()]
        elif any(word in intencion_lower for word in ['ciencia', 'célula', 'biología', 'mural']):
            # Preferir ejemplo de célula
            ejemplos_seleccionados = [ej for ej in self.ejemplos_k if 'célula' in ej.lower()]
        
        # Si no hay coincidencia específica, usar los 2 primeros ejemplos
        if not ejemplos_seleccionados:
            ejemplos_seleccionados = self.ejemplos_k[:2]
        
        return "\n".join(ejemplos_seleccionados[:2])  # Máximo 2 ejemplos
    
    def generar_actividad_inherentemente_adaptativa(self, 
                                                   config: ConfiguracionActividad,
                                                   intencion: str,
                                                   aula_info: str) -> str:
        """Genera actividad con adaptaciones inherentes basada en configuración optimizada"""
        
        # Obtener ejemplos relevantes para few-shot
        ejemplos_fewshot = self._seleccionar_ejemplos_relevantes(intencion)
        
        prompt_optimizado = f"""
{ejemplos_fewshot}

=== NUEVA ACTIVIDAD A CREAR ===

CREAR ACTIVIDAD: {intencion}

PARÁMETROS OPTIMIZADOS CUÁNTICAMENTE:
- {config.nivel_estructura:.0%} de tareas estructuradas / {100-config.nivel_estructura:.0%} de tareas libres
- {config.nivel_colaboracion:.0%} de trabajo colaborativo / {100-config.nivel_colaboracion:.0%} de trabajo individual  
- {config.flexibilidad_tiempo:.0%} de flexibilidad temporal / {100-config.flexibilidad_tiempo:.0%} de cronograma fijo

INFORMACIÓN DEL AULA: {aula_info}

INSTRUCCIONES CRÍTICAS:

USA EL ESTILO de los ejemplos anteriores como referencia de calidad y profundidad.
DISEÑA la actividad para que NATURALMENTE requiera exactamente esos porcentajes de:
- Tareas con pasos claros vs. exploración libre
- Momentos de trabajo conjunto vs. individual
- Tiempo flexible vs. cronograma definido

ASIGNA roles cuando sea necesario para la actividad específica.
INCLUYE adaptaciones solo si son naturales a la tarea.
NO fuerces listas genéricas de "roles disponibles".

ENFOQUE:
- Diseña una actividad que contenga MÚLTIPLES TIPOS de tareas
- Que permita a los estudiantes elegir cómo participar según sus preferencias
- Donde las diferentes formas de contribuir estén integradas naturalmente
- Si la actividad requiere roles específicos, inclúyelos naturalmente

EJEMPLO CORRECTO:
"Crear un mural del sistema solar donde necesitaremos:
- Investigar datos de planetas (tarea estructurada)
- Decidir el diseño artístico (tarea libre) 
- Medir y dividir el espacio (colaborativo)
- Cada uno desarrolla su parte (individual)
- Horario fijo para investigación (rígido)
- Tiempo libre para arte (flexible)"

FORMATO:
- Título y objetivo
- Materiales necesarios
- Desarrollo paso a paso
- Explicación de cómo emergen las diferentes formas de participar
- Tiempo estimado

La actividad debe ser inclusiva POR DISEÑO, no por adaptaciones.
"""
        
        if not self.llm:
            return self._generar_actividad_fallback(config, intencion, aula_info)
        
        try:
            print("🚀 Generando actividad optimizada con LLM...")
            resultado = self.llm.invoke(prompt_optimizado)
            print("✅ Actividad generada exitosamente")
            return resultado
        except Exception as e:
            print(f"❌ Error en LLM: {e}")
            return self._generar_actividad_fallback(config, intencion, aula_info)
    
    def _formatear_lista(self, lista: List[str]) -> str:
        """Formatea lista para prompt"""
        return "\n".join(f"  • {item}" for item in lista)
    
    def _generar_actividad_fallback(self, config: ConfiguracionActividad, 
                                  intencion: str, aula_info: str) -> str:
        """Genera actividad de respaldo si LLM no funciona"""
        
        return f"""
ACTIVIDAD EDUCATIVA CON INCLUSIÓN INHERENTE
=========================================

OBJETIVO: {intencion}

CONFIGURACIÓN OPTIMIZADA:
- Estructura: {config.nivel_estructura:.2f}
- Colaboración: {config.nivel_colaboracion:.2f}  
- Flexibilidad: {config.flexibilidad_tiempo:.2f}
- Inclusión: {config.inclusion_score:.2f}

DESARROLLO DE LA ACTIVIDAD:

{self._generar_desarrollo_fallback(config, intencion)}

ROLES DISPONIBLES:
{self._formatear_lista(config.roles_disponibles)}

MODALIDADES INTEGRADAS:
{self._formatear_lista(config.modalidades)}

[Esta actividad fue generada en modo fallback - LLM no disponible]
"""
    
    def _generar_desarrollo_fallback(self, config: ConfiguracionActividad, intencion: str) -> str:
        """Genera desarrollo básico de actividad"""
        
        desarrollo = ""
        for i, fase in enumerate(config.fases, 1):
            desarrollo += f"{i}. {fase}\n"
            desarrollo += f"   - Interacción: {config.tipos_interaccion[0] if config.tipos_interaccion else 'flexible'}\n"
            desarrollo += f"   - Modalidad: {config.modalidades[0] if config.modalidades else 'multimodal'}\n\n"
        
        return desarrollo

class TraductorPedagogico:
    """Traduce respuestas naturales del profesor a parámetros cuánticos"""
    
    def __init__(self):
        self.preguntas_clave = [
            {
                "id": "enfoque_actividad",
                "pregunta": "¿Cómo te imaginas que será esta actividad?",
                "opciones": [
                    "Los estudiantes siguen pasos claros y organizados",
                    "Hay una estructura pero con espacio para improvisar", 
                    "Los estudiantes exploran y experimentan libremente"
                ],
                "mapeo": {0: 0.8, 1: 0.5, 2: 0.2},  # estructura
                "parametro": "estructura"
            },
            {
                "id": "dinamica_trabajo",
                "pregunta": "¿Cómo quieres que trabajen los estudiantes?",
                "opciones": [
                    "Principalmente cada uno en su tarea individual",
                    "Alternando entre trabajo individual y en pequeños grupos",
                    "Colaborando todo el tiempo en equipos"
                ],
                "mapeo": {0: 0.2, 1: 0.6, 2: 0.9},  # colaboración
                "parametro": "colaboracion"
            },
            {
                "id": "gestion_tiempo",
                "pregunta": "¿Cómo manejarías los tiempos y ritmos?",
                "opciones": [
                    "Tiempos fijos para cada parte de la actividad",
                    "Tiempos orientativos que se pueden ajustar sobre la marcha",
                    "Que cada estudiante/grupo vaya a su ritmo"
                ],
                "mapeo": {0: 0.2, 1: 0.6, 2: 0.9},  # flexibilidad
                "parametro": "flexibilidad"
            },
            {
                "id": "distribucion_tareas", 
                "pregunta": "¿Cómo se repartirían las tareas entre los estudiantes?",
                "opciones": [
                    "Yo asigno roles específicos según las necesidades de cada uno",
                    "Ofrezco varios roles y que elijan según sus preferencias",
                    "Que se organicen ellos mismos según surja"
                ],
                "mapeo": {0: 0.8, 1: 0.5, 2: 0.2},  # estructura (influye en estructura)
                "parametro": "estructura_roles"
            }
        ]
    
    def recopilar_preferencias_profesor(self, intencion: str, aula_info: str) -> Dict[str, float]:
        """Recopila preferencias del profesor de forma natural"""
        
        print("🎓 ORIENTACIÓN DE LA ACTIVIDAD")
        print("=" * 50)
        print(f"📝 Intención: {intencion}")
        print(f"👥 {aula_info}")
        print("\nVamos a definir cómo orientar esta actividad con unas preguntas sencillas:\n")
        
        respuestas = {}
        
        for pregunta_data in self.preguntas_clave:
            print(f"❓ {pregunta_data['pregunta']}")
            
            for i, opcion in enumerate(pregunta_data['opciones'], 1):
                print(f"   {i}. {opcion}")
            
            while True:
                try:
                    respuesta = input(f"\n👨‍🏫 Tu elección (1-{len(pregunta_data['opciones'])}): ").strip()
                    
                    if respuesta.isdigit():
                        opcion_num = int(respuesta) - 1
                        if 0 <= opcion_num < len(pregunta_data['opciones']):
                            # Mapear respuesta a valor numérico
                            valor = pregunta_data['mapeo'][opcion_num]
                            respuestas[pregunta_data['parametro']] = valor
                            
                            print(f"✅ {pregunta_data['opciones'][opcion_num]}")
                            break
                        else:
                            print(f"❌ Elige un número entre 1 y {len(pregunta_data['opciones'])}")
                    else:
                        print("❌ Por favor, introduce un número")
                        
                except ValueError:
                    print("❌ Por favor, introduce un número válido")
                except KeyboardInterrupt:
                    print("\n⏹️ Proceso cancelado")
                    return {}
            
            print()  # Línea en blanco entre preguntas
        
        return respuestas
    
    def mostrar_orientacion_resultante(self, parametros: Dict[str, float]):
        """Muestra al profesor cómo se tradujeron sus respuestas"""
        
        print("🎯 ORIENTACIÓN RESULTANTE DE TUS RESPUESTAS:")
        print("-" * 50)
        
        # Traducir números a descripciones comprensibles
        estructura = parametros.get('estructura', 0.5)
        if parametros.get('estructura_roles'):
            estructura = (estructura + parametros['estructura_roles']) / 2
        
        colaboracion = parametros.get('colaboracion', 0.5)
        flexibilidad = parametros.get('flexibilidad', 0.5)
        
        # Estructura
        if estructura > 0.7:
            print("📋 Actividad MUY ESTRUCTURADA - pasos claros y organizados")
        elif estructura > 0.4:
            print("⚖️ Actividad SEMI-ESTRUCTURADA - estructura con flexibilidad")
        else:
            print("🎨 Actividad LIBRE - exploración y experimentación")
        
        # Colaboración
        if colaboracion > 0.7:
            print("👥 Enfoque MUY COLABORATIVO - trabajo en equipo constante")
        elif colaboracion > 0.4:
            print("🤝 Enfoque MIXTO - individual y grupal")
        else:
            print("👤 Enfoque INDIVIDUAL - cada uno en su tarea")
        
        # Flexibilidad
        if flexibilidad > 0.7:
            print("⏰ Tiempos MUY FLEXIBLES - cada uno a su ritmo")
        elif flexibilidad > 0.4:
            print("🕐 Tiempos ADAPTATIVOS - orientativos pero ajustables")
        else:
            print("⏱️ Tiempos FIJOS - cronograma definido")
        
        print()
        conformidad = input("✅ ¿Te parece bien esta orientación? (s/n): ").strip().lower()
        
        return conformidad in ['s', 'si', 'sí', 'y', 'yes']

class SistemaHumanInTheLoop:
    """Maneja la interacción humana para guiar la optimización - VERSION SIMPLIFICADA"""
    
    def __init__(self):
        self.traductor = TraductorPedagogico()
    
    def recopilar_preferencias_profesor_simple(self, intencion: str, aula_info: str) -> Dict[str, float]:
        """Interfaz simplificada para recopilar preferencias del profesor"""
        
        preferencias = self.traductor.recopilar_preferencias_profesor(intencion, aula_info)
        
        if not preferencias:
            # Valores por defecto si se cancela
            return {'estructura': 0.5, 'colaboracion': 0.6, 'flexibilidad': 0.5}
        
        # Mostrar resultado y confirmar
        if self.traductor.mostrar_orientacion_resultante(preferencias):
            return preferencias
        else:
            print("\n🔄 Volviendo a preguntar...")
            return self.recopilar_preferencias_profesor_simple(intencion, aula_info)
    
    def aplicar_preferencias_a_config(self, config: ConfiguracionActividad, 
                                    preferencias: Dict[str, float],
                                    aula: List[EstudiantePerfilCuantico]) -> ConfiguracionActividad:
        """Aplica las preferencias del profesor a la configuración optimizada"""
        
        # Combinar optimización cuántica con preferencias del profesor
        # Peso 70% optimización, 30% preferencias
        peso_optimizacion = 0.7
        peso_preferencias = 0.3
        
        estructura_final = (config.nivel_estructura * peso_optimizacion + 
                          preferencias.get('estructura', 0.5) * peso_preferencias)
        
        colaboracion_final = (config.nivel_colaboracion * peso_optimizacion + 
                            preferencias.get('colaboracion', 0.5) * peso_preferencias)
        
        flexibilidad_final = (config.flexibilidad_tiempo * peso_optimizacion + 
                            preferencias.get('flexibilidad', 0.5) * peso_preferencias)
        
        # Ajustar si estructura_roles influye
        if 'estructura_roles' in preferencias:
            estructura_final = (estructura_final + preferencias['estructura_roles']) / 2
        
        # Crear nueva configuración
        config_ajustada = ConfiguracionActividad(
            fases=self._regenerar_fases(estructura_final, config.fases),
            roles_disponibles=config.roles_disponibles,
            modalidades=config.modalidades,
            tipos_interaccion=self._regenerar_interacciones(colaboracion_final),
            nivel_estructura=estructura_final,
            nivel_colaboracion=colaboracion_final,
            flexibilidad_tiempo=flexibilidad_final,
            inclusion_score=self._recalcular_inclusion_simple(estructura_final, colaboracion_final, flexibilidad_final, aula)
        )
        
        print(f"\n🎯 CONFIGURACIÓN FINAL AJUSTADA:")
        print(f"  • Estructura: {estructura_final:.2f} (mezcla optimización + tu preferencia)")
        print(f"  • Colaboración: {colaboracion_final:.2f}")  
        print(f"  • Flexibilidad: {flexibilidad_final:.2f}")
        print(f"  • Score de inclusión: {config_ajustada.inclusion_score:.2f}")
        
        return config_ajustada
    
    def _regenerar_fases(self, estructura: float, fases_originales: List[str]) -> List[str]:
        """Regenera fases según nueva estructura"""
        
        if estructura > 0.7:
            return [
                "Introducción clara con ejemplos y objetivos",
                "Distribución de roles y responsabilidades específicas",
                "Desarrollo por etapas con verificaciones",
                "Síntesis guiada y presentación organizada"
            ]
        elif estructura > 0.4:
            return [
                "Exploración inicial guiada del tema",
                "Organización flexible de equipos y tareas", 
                "Desarrollo con puntos de control adaptativos",
                "Integración colaborativa de resultados"
            ]
        else:
            return [
                "Brainstorming libre y exploración abierta",
                "Auto-organización espontánea de grupos",
                "Experimentación y desarrollo creativo",
                "Presentación innovadora de descubrimientos"
            ]
    
    def _regenerar_interacciones(self, colaboracion: float) -> List[str]:
        """Regenera tipos de interacción según colaboración"""
        
        if colaboracion > 0.7:
            return ["equipos_grandes", "plenarios_frecuentes", "construccion_conjunta"]
        elif colaboracion > 0.4:
            return ["parejas", "grupos_pequenos", "intercambio_roles", "momentos_individuales"]
        else:
            return ["trabajo_individual", "consultas_puntuales", "presentacion_personal"]
    
    def _recalcular_inclusion_simple(self, estructura: float, colaboracion: float, 
                                   flexibilidad: float, aula: List[EstudiantePerfilCuantico]) -> float:
        """Recálculo simplificado de inclusión"""
        
        inclusiones = []
        for est in aula:
            diff_est = abs(est.necesidades_estructura - estructura)
            diff_soc = abs(est.preferencia_social - colaboracion)
            diff_flex = abs(est.tolerancia_incertidumbre - flexibilidad)
            
            inclusion = 1.0 - (diff_est + diff_soc + diff_flex) / 3.0
            inclusiones.append(inclusion)
        
        return np.mean(inclusiones)

class GeneradorCuanticoCompleto:
    """Sistema completo de generación de actividades con optimización cuántica"""
    
    def __init__(self):
        self.codificador = CodificadorPerfiles()
        
        # Intentar optimizador cuántico, fallback a clásico
        try:
            if QISKIT_AVAILABLE:
                self.optimizador = OptimizadorQiskit()
                print("🌟 Optimizador cuántico Qiskit activado")
            else:
                raise ImportError("Qiskit no disponible")
        except ImportError:
            self.optimizador = OptimizadorClasico()
            print("⚙️ Usando optimizador clásico")
        
        self.generador_prompt = GeneradorPromptOptimizado()
        self.human_loop = SistemaHumanInTheLoop()
    
    def generar_actividad_completa(self, intencion: str, 
                                 estudiantes: List[Dict]) -> Dict[str, Any]:
        """Proceso completo SIMPLIFICADO de generación de actividad optimizada"""
        
        print("🧬 GENERADOR CUÁNTICO DE ACTIVIDADES EDUCATIVAS")
        print("=" * 60)
        print(f"🎯 Intención: {intencion}")
        print(f"👥 Estudiantes: {len(estudiantes)}")
        
        # 1. Codificar perfiles de estudiantes
        print("\n🔬 Codificando perfiles de estudiantes...")
        aula_cuantica = self.codificador.codificar_aula(estudiantes)
        aula_info = self._formatear_info_aula(estudiantes)
        
        # 2. Recopilar preferencias del profesor de forma natural
        print("\n👨‍🏫 Recopilando tus preferencias pedagógicas...")
        preferencias_profesor = self.human_loop.recopilar_preferencias_profesor_simple(intencion, aula_info)
        
        # 3. Optimización cuántica/clásica
        print("\n⚛️ Ejecutando optimización cuántica...")
        config_optimizada = self.optimizador.optimizar_actividad(aula_cuantica, intencion)
        
        # 4. Combinar optimización con preferencias del profesor
        print("🎛️ Combinando optimización cuántica con tus preferencias...")
        config_final = self.human_loop.aplicar_preferencias_a_config(
            config_optimizada, preferencias_profesor, aula_cuantica
        )
        
        # 5. Generar actividad con LLM
        print("\n🚀 Generando actividad final...")
        actividad = self.generador_prompt.generar_actividad_inherentemente_adaptativa(
            config_final, intencion, aula_info
        )
        
        # 6. Mostrar la actividad generada
        print("\n" + "=" * 60)
        print("📋 ACTIVIDAD GENERADA")
        print("=" * 60)
        print(actividad)
        print("=" * 60)
        
        # 7. Revisión final simplificada
        satisfecho = input("\n✅ ¿Estás satisfecho con la actividad generada? (s/n): ").strip().lower()
        
        if satisfecho not in ['s', 'si', 'sí', 'y', 'yes']:
            feedback = input("💬 ¿Qué cambiarías? (opcional): ").strip()
            if feedback:
                print(f"📝 Feedback registrado: {feedback}")
                print("🔄 Regenerando actividad con tu feedback...")
                
                # Regenerar actividad incorporando el feedback
                actividad = self._regenerar_con_feedback(config_final, intencion, aula_info, feedback)
                
                print("\n" + "=" * 60)
                print("📋 ACTIVIDAD REGENERADA CON TU FEEDBACK")
                print("=" * 60)
                print(actividad)
                print("=" * 60)
        
        return {
            'actividad': actividad,
            'configuracion': config_final,
            'inclusion_score': config_final.inclusion_score,
            'metodo_optimizacion': 'cuantico' if isinstance(self.optimizador, OptimizadorQiskit) else 'clasico',
            'preferencias_profesor': preferencias_profesor,
            'timestamp': datetime.now().isoformat(),
            'estudiantes_procesados': len(estudiantes)
        }
    
    def _formatear_info_aula(self, estudiantes: List[Dict]) -> str:
        """Formatea información del aula para el prompt"""
        
        info = f"Aula de {len(estudiantes)} estudiantes:\n"
        
        for est in estudiantes:
            dx = est.get('diagnostico_formal', 'ninguno')
            canal = est.get('canal_preferido', 'no especificado')
            
            dx_texto = dx if dx != 'ninguno' else 'desarrollo típico'
            info += f"  • {est['nombre']}: {canal}, {dx_texto}\n"
        
        return info
    
    def _regenerar_con_feedback(self, config: ConfiguracionActividad, 
                              intencion: str, aula_info: str, feedback: str) -> str:
        """Regenera la actividad incorporando el feedback específico del usuario"""
        
        # Crear un prompt específico que incorpore el feedback
        prompt_con_feedback = f"""
ADAPTAR ACTIVIDAD: {intencion}

FEEDBACK DEL PROFESOR: "{feedback}"

PARÁMETROS CUÁNTICOS MANTENIDOS:
- {config.nivel_estructura:.0%} estructurado / {100-config.nivel_estructura:.0%} libre
- {config.nivel_colaboracion:.0%} colaborativo / {100-config.nivel_colaboracion:.0%} individual
- {config.flexibilidad_tiempo:.0%} flexible / {100-config.flexibilidad_tiempo:.0%} fijo

INSTRUCCIONES:
1. RESPONDE EXACTAMENTE a lo que pide el feedback
2. MANTÉN los porcentajes cuánticos en la actividad modificada
3. Si pide guión → da guión real con diálogos
4. Si pide materiales → lista específica de materiales
5. Si pide distribución → explica cómo se reparten las tareas naturalmente
6. CAMBIA completamente el formato si es necesario

NO vuelvas al formato genérico.
RESPONDE DIRECTAMENTE a la petición específica.
MANTÉN el diseño inclusivo - las adaptaciones deben ser naturales, no asignadas.

FORMATO: Lo que específicamente pide el profesor, manteniendo inclusión inherente.
"""
        
        if not self.generador_prompt.llm:
            return self._regenerar_fallback_con_feedback(config, intencion, feedback)
        
        try:
            print("🔧 Adaptando actividad según tu feedback específico...")
            resultado = self.generador_prompt.llm.invoke(prompt_con_feedback)
            print("✅ Actividad regenerada exitosamente")
            return resultado
        except Exception as e:
            print(f"❌ Error en LLM: {e}")
            return self._regenerar_fallback_con_feedback(config, intencion, feedback)
    
    def _regenerar_fallback_con_feedback(self, config: ConfiguracionActividad, 
                                       intencion: str, feedback: str) -> str:
        """Regeneración simplificada cuando LLM no está disponible"""
        
        return f"""
ACTIVIDAD ADAPTADA - {intencion}

FEEDBACK RECIBIDO: "{feedback}"

PARÁMETROS CUÁNTICOS:
- {config.nivel_estructura:.0%} estructurado / {100-config.nivel_estructura:.0%} libre
- {config.nivel_colaboracion:.0%} colaborativo / {100-config.nivel_colaboracion:.0%} individual
- {config.flexibilidad_tiempo:.0%} flexible / {100-config.flexibilidad_tiempo:.0%} fijo

[LLM no disponible - Esta actividad sería generada automáticamente]
[El sistema respondería exactamente a tu feedback específico]
[Manteniendo los parámetros cuánticos optimizados]
[Con diseño inclusivo inherente, sin asignaciones específicas]

En una implementación completa:
- Se adaptaría el formato según tu petición específica
- Se mantendría la optimización cuántica
- Se respondería directamente a lo que pides
"""
    
def cargar_estudiantes_test():
    """Carga estudiantes de prueba con perfiles diversos"""
    return [
        {
            "id": "001", 
            "nombre": "ALEX M.",
            "canal_preferido": "visual",
            "diagnostico_formal": "ninguno"
        },
        {
            "id": "003",
            "nombre": "ELENA R.", 
            "canal_preferido": "visual",
            "diagnostico_formal": "TEA_nivel_1"
        },
        {
            "id": "004",
            "nombre": "LUIS T.",
            "canal_preferido": "kinestésico", 
            "diagnostico_formal": "TDAH_combinado"
        },
        {
            "id": "005",
            "nombre": "ANA V.",
            "canal_preferido": "auditivo",
            "diagnostico_formal": "altas_capacidades"
        },
        {
            "id": "006",
            "nombre": "SARA M.",
            "canal_preferido": "auditivo",
            "diagnostico_formal": "ninguno"
        }
    ]

def main():
    """Función principal del generador cuántico"""
    
    print("🧬 GENERADOR CUÁNTICO DE ACTIVIDADES EDUCATIVAS")
    print("Concepto: Optimización cuántica para actividades con inclusión inherente")
    print("=" * 70)
    
    generador = GeneradorCuanticoCompleto()
    estudiantes = cargar_estudiantes_test()
    
    while True:
        print(f"\n📚 Estudiantes disponibles:")
        for est in estudiantes:
            dx = est['diagnostico_formal'] if est['diagnostico_formal'] != 'ninguno' else 'desarrollo típico'
            print(f"  • {est['nombre']} ({est['canal_preferido']}, {dx})")
        
        print(f"\n🎯 ¿Qué actividad quieres crear?")
        print("Ejemplos:")
        print("  - 'Crear un proyecto sobre el sistema solar'")
        print("  - 'Actividad colaborativa de matemáticas con fracciones'")
        print("  - 'Experimento de ciencias sobre electricidad'")
        
        intencion = input("\nDescribe tu intención: ").strip()
        
        if not intencion or intencion.lower() in ['salir', 'quit', 'exit']:
            break
        
        try:
            print("\n" + "🚀" * 20)
            resultado = generador.generar_actividad_completa(intencion, estudiantes)
            
            print("\n" + "=" * 60)
            print("📋 ACTIVIDAD FINAL GENERADA")
            print("=" * 60)
            print(resultado['actividad'])
            
            print(f"\n📊 MÉTRICAS FINALES:")
            print(f"  🎯 Score de inclusión: {resultado['inclusion_score']:.2f}")
            print(f"  ⚛️ Método de optimización: {resultado['metodo_optimizacion']}")
            print(f"  👥 Estudiantes procesados: {resultado['estudiantes_procesados']}")
            
            # Opción de guardar
            guardar = input(f"\n💾 ¿Guardar actividad? (s/n): ").strip().lower()
            if guardar in ['s', 'si', 'sí', 'y', 'yes']:
                filename = f"actividad_cuantica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("ACTIVIDAD GENERADA CON OPTIMIZACIÓN CUÁNTICA\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(f"Intención: {intencion}\n")
                    f.write(f"Generado: {resultado['timestamp']}\n")
                    f.write(f"Método: {resultado['metodo_optimizacion']}\n")
                    f.write(f"Score de inclusión: {resultado['inclusion_score']:.2f}\n\n")
                    
                    f.write("CONFIGURACIÓN OPTIMIZADA:\n")
                    f.write("-" * 40 + "\n")
                    config = resultado['configuracion']
                    f.write(f"Estructura: {config.nivel_estructura:.2f}\n")
                    f.write(f"Colaboración: {config.nivel_colaboracion:.2f}\n")
                    f.write(f"Flexibilidad: {config.flexibilidad_tiempo:.2f}\n\n")
                    
                    f.write("ACTIVIDAD:\n")
                    f.write("-" * 40 + "\n")
                    f.write(resultado['actividad'])
                
                print(f"💾 Guardado como: {filename}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        continuar = input(f"\n🔄 ¿Crear otra actividad? (s/n): ").strip().lower()
        if continuar not in ['s', 'si', 'sí', 'y', 'yes']:
            break
    
    print("\n👋 ¡Hasta luego!")
    print("💡 Tu hipótesis sobre el 'espacio de incertidumbre beneficioso' ha sido")
    print("   implementada mediante optimización cuántica para actividades inclusivas!")

if __name__ == "__main__":
    main()
