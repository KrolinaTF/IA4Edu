#!/usr/bin/env python3
"""
Optimizador Educativo Cuántico con PennyLane
Implementa mejora de prompts educativos usando computación cuántica
"""

import pennylane as qml
import numpy as np
from pennylane import numpy as qnp
import json
from typing import Dict, List, Any, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuantumEducationalOptimizer")


class QuantumEducationalOptimizer:
    """
    Optimizador cuántico para parámetros educativos
    Utiliza PennyLane para codificar y optimizar contextos pedagógicos
    """
    
    def __init__(self, num_qubits: int = 16):
        self.num_qubits = num_qubits
        self.dev = qml.device("default.qubit", wires=num_qubits)
        logger.info(f"✅ Dispositivo cuántico inicializado con {num_qubits} qubits")
    
    def educational_encoding(self, params):
        """
        Codifica parámetros educativos en un estado cuántico
        params[0]: nivel de energía del aula
        params[1]: nivel de estructura
        params[2]: nivel de colaboración
        params[3:8]: perfiles estudiantiles (general, TEA, TDAH, etc.)
        params[8:13]: áreas curriculares
        """
        # Codificación de ángulos para parámetros principales
        qml.RY(params[0] * np.pi, wires=0)  # Energía
        qml.RY(params[1] * np.pi, wires=1)  # Estructura
        qml.RY(params[2] * np.pi, wires=2)  # Colaboración
        
        # Codificación de perfiles estudiantiles
        for i in range(5):
            qml.RY(params[3+i] * np.pi, wires=3+i)
        
        # Codificación de áreas curriculares
        for i in range(5):
            qml.RY(params[8+i] * np.pi, wires=8+i)
        
        # Entrelazamiento para modelar interdependencias educativas
        # La energía del aula afecta la colaboración
        qml.CNOT(wires=[0, 2])
        
        # La presencia de TEA afecta el nivel de estructura necesario
        qml.CNOT(wires=[4, 1])
        
        # La presencia de TDAH afecta el nivel de energía óptimo
        qml.CNOT(wires=[5, 0])
        
        # Entrelazamiento entre áreas curriculares y enfoques
        qml.CNOT(wires=[8, 13])  # Matemáticas - Pensamiento lógico
        qml.CNOT(wires=[9, 14])  # Lenguaje - Comunicación
        
        # Retornamos las expectativas para los parámetros principales
        return [qml.expval(qml.PauliZ(i)) for i in range(8)]
    
    def educational_hamiltonian(self, params):
        """
        Define el "hamiltoniano educativo" que representa la energía 
        del sistema que queremos optimizar
        """
        # Crear qnode dinámicamente
        @qml.qnode(self.dev)
        def circuit(params):
            return self.educational_encoding(params)
        
        # Ejecutamos el circuito para obtener valores esperados
        expectations = circuit(params)
        
        # Extraemos valores normalizados (de -1,1 a 0,1)
        energy = (expectations[0] + 1) / 2
        structure = (expectations[1] + 1) / 2
        collaboration = (expectations[2] + 1) / 2
        
        # Perfiles estudiantiles normalizados
        tea_presence = (expectations[4] + 1) / 2  # TEA
        tdah_presence = (expectations[5] + 1) / 2  # TDAH
        
        # Definimos penalizaciones basadas en buenas prácticas educativas
        
        # 1. Si hay estudiantes con TEA, necesitamos alta estructura
        tea_penalty = tea_presence * (1 - structure) * 2.0
        
        # 2. Si hay estudiantes con TDAH, balanceamos energía y estructura
        tdah_penalty = tdah_presence * ((1 - energy) + (energy * (1 - structure))) * 1.5
        
        # 3. Penalización por baja colaboración (principio pedagógico general)
        collab_penalty = (1 - collaboration) * 0.5
        
        # Sumamos todas las penalizaciones (queremos minimizar)
        total_cost = tea_penalty + tdah_penalty + collab_penalty
        
        return total_cost
    
    def optimize_educational_parameters(self, initial_params, steps: int = 100):
        """
        Optimiza los parámetros educativos para minimizar el hamiltoniano
        """
        logger.info(f"🔬 Iniciando optimización cuántica con {steps} pasos")
        
        # Configuración del optimizador
        opt = qml.GradientDescentOptimizer(stepsize=0.1)
        params = initial_params.copy()
        
        # Optimización iterativa
        cost_history = []
        for i in range(steps):
            params, cost = opt.step_and_cost(self.educational_hamiltonian, params)
            cost_history.append(cost)
            
            # Opcional: imprimir progreso
            if i % 20 == 0:
                logger.info(f"Optimización paso {i}: Costo = {cost:.4f}")
        
        logger.info(f"✅ Optimización completada. Costo final: {cost_history[-1]:.4f}")
        
        # Retornamos parámetros optimizados y el historial de optimización
        return params, cost_history
    
    def quantum_to_prompt_parameters(self, optimized_params, initial_context):
        """
        Convierte los parámetros optimizados en parámetros de prompt
        """
        # Crear qnode para obtener expectativas
        @qml.qnode(self.dev)
        def circuit(params):
            return self.educational_encoding(params)
        
        # Ejecutamos el circuito con los parámetros optimizados
        expectations = circuit(optimized_params)
        
        # Convertimos a valores normalizados entre 0 y 1
        normalized = [(exp + 1) / 2 for exp in expectations]
        
        # Creamos diccionario de parámetros para el prompt
        prompt_params = {
            "ambiente": {
                "energia": normalized[0],
                "estructura": normalized[1],
                "colaboracion": normalized[2]
            },
            "adaptaciones": {}
        }
        
        # Agregamos adaptaciones específicas basadas en perfiles
        # Solo si los perfiles están presentes en el contexto inicial
        if initial_context.get("perfiles", {}).get("tea", 0) > 0:
            tea_factor = normalized[4]  # Presencia de TEA (normalizada)
            prompt_params["adaptaciones"]["tea"] = {
                "estructuracion": max(0.8, normalized[1]),  # Garantizamos alta estructura
                "apoyos_visuales": 0.9 * tea_factor,
                "predictibilidad": 0.85 * tea_factor,
                "secuenciacion": 0.8 * tea_factor
            }
        
        if initial_context.get("perfiles", {}).get("tdah", 0) > 0:
            tdah_factor = normalized[5]  # Presencia de TDAH (normalizada)
            prompt_params["adaptaciones"]["tdah"] = {
                "fragmentacion_tareas": 0.75 * tdah_factor,
                "movimiento_integrado": min(0.8, normalized[0] + 0.2),  # Relacionado con energía
                "feedback_frecuente": 0.7 * tdah_factor,
                "reduccion_distractores": (1 - normalized[0]) * 0.6 * tdah_factor  # Inversamente proporcional a energía
            }
        
        return prompt_params
    
    def generate_enhanced_prompt(self, base_prompt: str, prompt_params: Dict):
        """
        Genera el prompt final matizado con los parámetros cuánticos
        """
        # Extractores de parámetros clave
        energia = prompt_params["ambiente"]["energia"]
        estructura = prompt_params["ambiente"]["estructura"]
        colaboracion = prompt_params["ambiente"]["colaboracion"]
        
        # Traducción a términos descriptivos
        energia_desc = "alta" if energia > 0.7 else ("moderada" if energia > 0.4 else "baja")
        estructura_desc = "alta" if estructura > 0.7 else ("moderada" if estructura > 0.4 else "baja")
        colaboracion_desc = "colaborativo" if colaboracion > 0.7 else ("semi-colaborativo" if colaboracion > 0.4 else "individual")
        
        # Construcción del prompt mejorado
        enhanced_prompt = f"""
        Diseña una actividad educativa siguiendo este proceso:

        1. AMBIENTE: Busco crear un ambiente de {energia_desc} energía ({energia:.2f}),
           con un nivel de estructuración {estructura_desc} ({estructura:.2f}) y
           un enfoque principalmente {colaboracion_desc} ({colaboracion:.2f}).

        2. CONTENIDO: {base_prompt}

        3. ACTIVIDAD GLOBAL: Diseña una actividad completa que:
           - Mantenga el ambiente descrito
           - Cumpla con el objetivo curricular
           - Involucre a todo el grupo de forma coherente
        """
        
        # Añadimos adaptaciones específicas si existen
        if "adaptaciones" in prompt_params and prompt_params["adaptaciones"]:
            enhanced_prompt += "\n\n4. ADAPTACIONES ESPECÍFICAS:\n"
            
            for profile, adaptations in prompt_params["adaptaciones"].items():
                enhanced_prompt += f"   - Para estudiantes con {profile.upper()}:\n"
                for adaptation_name, adaptation_value in adaptations.items():
                    # Convertimos snake_case a texto legible
                    readable_name = " ".join(word.capitalize() for word in adaptation_name.split("_"))
                    enhanced_prompt += f"     * {readable_name}: {adaptation_value:.2f}\n"
        
        return enhanced_prompt
    
    def quantum_enhanced_educational_prompt(self, base_prompt: str, curriculum_area: str, student_profiles: Dict):
        """
        Flujo completo para generar un prompt educativo mejorado con computación cuántica
        """
        logger.info("🌟 Iniciando mejora cuántica de prompt educativo")
        
        # Contexto inicial
        initial_context = {
            "perfiles": student_profiles,
            "area_curricular": curriculum_area
        }
        
        # Parámetros iniciales (13 parámetros totales)
        initial_params = np.zeros(13)
        
        # Valores iniciales para ambiente (neutros)
        initial_params[0:3] = 0.5  # Energía, estructura, colaboración
        
        # Valores para perfiles estudiantiles
        initial_params[3] = 1.0  # Perfil general siempre presente
        for i, (profile, value) in enumerate(student_profiles.items()):
            if profile == "tea":
                initial_params[4] = value
            elif profile == "tdah":
                initial_params[5] = value
            # Otros perfiles se pueden agregar aquí
        
        # Valores para área curricular (mapeo coherente)
        areas_map = {
            "mathematics": 0, "matematicas": 0, "mate": 0, "math": 0,
            "language": 1, "lengua": 1, "lenguaje": 1, "lang": 1,
            "science": 2, "ciencias": 2, "ciencia": 2, "sci": 2,
            "arts": 3, "arte": 3, "artistica": 3, "art": 3,
            "physical_education": 4, "educacion_fisica": 4, "ef": 4
        }
        
        # Mapear área curricular al índice correcto
        area_normalizada = curriculum_area.lower().strip()
        if area_normalizada in areas_map:
            initial_params[8 + areas_map[area_normalizada]] = 1.0
        else:
            # Por defecto, marcar como interdisciplinar (mathematics)
            initial_params[8] = 1.0
        
        # Optimizamos los parámetros educativos
        optimized_params, cost_history = self.optimize_educational_parameters(initial_params)
        
        # Convertimos a parámetros de prompt
        prompt_params = self.quantum_to_prompt_parameters(optimized_params, initial_context)
        
        # Generamos el prompt final
        enhanced_prompt = self.generate_enhanced_prompt(base_prompt, prompt_params)
        
        logger.info("✨ Prompt educativo mejorado cuánticamente completado")
        
        return enhanced_prompt, prompt_params, cost_history


def test_quantum_optimizer():
    """Función de prueba para el optimizador cuántico"""
    print("🧪 TESTING: Optimizador Educativo Cuántico")
    print("="*50)
    
    # Crear instancia del optimizador
    optimizer = QuantumEducationalOptimizer()
    
    # Datos de entrada para prueba
    base_prompt = "Necesito trabajar fracciones con mis alumnos de 4º de primaria"
    curriculum_area = "mathematics"
    student_profiles = {
        "tea": 0.2,  # 20% de estudiantes con TEA
        "tdah": 0.1  # 10% de estudiantes con TDAH
    }
    
    # Generar prompt mejorado
    try:
        enhanced_prompt, params, history = optimizer.quantum_enhanced_educational_prompt(
            base_prompt, curriculum_area, student_profiles
        )
        
        print("✅ PROMPT OPTIMIZADO CUÁNTICAMENTE:")
        print("-" * 50)
        print(enhanced_prompt)
        
        print("\n📊 PARÁMETROS OPTIMIZADOS:")
        print("-" * 30)
        for key, value in params.items():
            print(f"{key}: {value}")
        
        print(f"\n📈 CONVERGENCIA: {len(history)} pasos, costo final: {history[-1]:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        logger.error(f"Error en test: {e}")
        return False


if __name__ == "__main__":
    # Ejecutar prueba
    success = test_quantum_optimizer()
    if success:
        print("\n🎉 Sistema cuántico funcionando correctamente")
    else:
        print("\n⚠️ Hay problemas con el sistema cuántico")