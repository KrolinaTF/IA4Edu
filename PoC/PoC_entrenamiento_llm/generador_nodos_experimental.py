#!/usr/bin/env python3
"""
Generador Experimental por Nodos - Arquitectura Limpia
======================================================

Sistema experimental para generar actividades educativas usando arquitectura de nodos.
- Sin prints excesivos
- Sin complejidad innecesaria  
- Niveles de abstracción reales
- Composabilidad de tareas y sujetos
- Escalabilidad gradual

Filosofía: Empezar simple, añadir complejidad solo cuando sea necesario.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

# Configuración minimalista
os.environ["OLLAMA_BASE_URL"] = "http://192.168.1.10:11434"
os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_MODEL_NAME"] = "qwen3:latest"

# =============================================================================
# TIPOS Y ESTRUCTURAS BÁSICAS
# =============================================================================

class TaskType(Enum):
    READ = "read"
    CREATE = "create"
    ANALYZE = "analyze"
    PRESENT = "present"
    DISCUSS = "discuss"
    SOLVE = "solve"

class SubjectRole(Enum):
    INDIVIDUAL = "individual"
    PAIR = "pair"
    GROUP = "group"
    COLLECTIVE = "collective"

@dataclass
class TaskNode:
    """Nodo básico de tarea"""
    id: str
    task_type: TaskType
    description: str
    duration_minutes: int
    complexity_level: int  # 1-5
    subjects_required: int
    subject_role: SubjectRole
    materials: List[str]
    dependencies: List[str]  # IDs of other TaskNodes
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class SubjectNode:
    """Nodo de sujeto/estudiante"""
    id: str
    name: str
    learning_style: str  # visual, auditivo, kinestésico
    attention_span: int  # minutos
    collaboration_preference: str  # individual, small_group, large_group
    
@dataclass
class ActivityGraph:
    """Grafo completo de actividad"""
    id: str
    title: str
    subject: str
    task_nodes: List[TaskNode]
    subject_assignments: Dict[str, List[str]]  # task_id -> [subject_ids]
    total_duration: int
    complexity_level: int
    created_at: str

# =============================================================================
# GENERADORES POR NIVEL DE COMPLEJIDAD
# =============================================================================

class BaseGenerator:
    """Generador base con funcionalidad común"""
    
    def __init__(self):
        # Estudiantes básicos - sin sobrecomplicar
        self.subjects = [
            SubjectNode("001", "Alex", "visual", 30, "small_group"),
            SubjectNode("002", "María", "auditivo", 25, "large_group"),
            SubjectNode("003", "Elena", "visual", 35, "individual"),
            SubjectNode("004", "Luis", "kinestésico", 20, "small_group"),
            SubjectNode("005", "Ana", "visual", 40, "individual"),
            SubjectNode("006", "Sara", "auditivo", 30, "large_group"),
            SubjectNode("007", "Emma", "visual", 35, "small_group"),
            SubjectNode("008", "Hugo", "kinestésico", 25, "large_group"),
        ]
        
    def _setup_llm(self):
        """Setup LLM solo cuando se necesite"""
        try:
            # Try new import first
            try:
                from langchain_ollama import OllamaLLM
                return OllamaLLM(model="qwen3:latest", base_url="http://192.168.1.10:11434")
            except ImportError:
                # Fallback to old import  
                from langchain_community.llms import Ollama
                return Ollama(model="qwen3:latest", base_url="http://192.168.1.10:11434")
        except Exception:
            return None
    
    def _generate_with_llm(self, prompt: str) -> str:
        """Llamada LLM simple"""
        llm = self._setup_llm()
        if llm:
            try:
                return llm.invoke(prompt).strip()
            except Exception:
                return "Error: LLM no disponible"
        return "Error: LLM no configurado"

class Level1Generator(BaseGenerator):
    """Nivel 1: Una sola tarea, todos participan, 45 minutos máximo"""
    
    def create_activity(self, prompt: str, subject: str) -> ActivityGraph:
        # LLM call minimalista para tarea simple
        llm_prompt = f"""
Crea UNA SOLA tarea educativa simple para 4º primaria sobre: {prompt}

Materia: {subject}
Duración: máximo 45 minutos
Participantes: 8 estudiantes trabajando juntos
Complejidad: básica

Responde SOLO con:
- Descripción de la tarea (1 línea)
- Materiales necesarios (máximo 3 items)

NO incluyas: múltiples fases, roles complejos, evaluaciones elaboradas
"""
        
        llm_response = self._generate_with_llm(llm_prompt)
        
        # Parsear respuesta simple
        lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
        description = lines[0] if lines else "Actividad de lectura y discusión grupal"
        materials = ["papel", "lápiz"] if len(lines) < 2 else lines[1].split(',')[:3]
        
        # Crear nodo único
        task_node = TaskNode(
            id="task_001",
            task_type=TaskType.DISCUSS,
            description=description,
            duration_minutes=45,
            complexity_level=1,
            subjects_required=8,
            subject_role=SubjectRole.COLLECTIVE,
            materials=materials,
            dependencies=[]
        )
        
        # Asignación simple: todos a la misma tarea
        subject_assignments = {
            "task_001": [s.id for s in self.subjects]
        }
        
        return ActivityGraph(
            id=f"level1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"Actividad Simple - {subject}",
            subject=subject,
            task_nodes=[task_node],
            subject_assignments=subject_assignments,
            total_duration=45,
            complexity_level=1,
            created_at=datetime.now().isoformat()
        )

class Level2Generator(BaseGenerator):
    """Nivel 2: Dos tareas conectadas, algunos grupos, 60-90 minutos"""
    
    def create_activity(self, prompt: str, subject: str) -> ActivityGraph:
        llm_prompt = f"""
Crea DOS tareas educativas conectadas para 4º primaria sobre: {prompt}

Materia: {subject}
Duración total: 60-90 minutos
Participantes: 8 estudiantes en 2 grupos de 4
Complejidad: intermedia

Responde con:
Tarea 1: [descripción] | [duración en minutos] | [materiales]
Tarea 2: [descripción] | [duración en minutos] | [materiales]

Ejemplo:
Tarea 1: Investigar información básica | 30 | libros, cuaderno
Tarea 2: Crear presentación simple | 45 | cartulina, rotuladores
"""
        
        llm_response = self._generate_with_llm(llm_prompt)
        
        # Parsear dos tareas
        tasks_data = self._parse_tasks(llm_response, 2)
        
        task_nodes = []
        for i, task_data in enumerate(tasks_data):
            task_nodes.append(TaskNode(
                id=f"task_{i+1:03d}",
                task_type=TaskType.CREATE if i == 1 else TaskType.READ,
                description=task_data['description'],
                duration_minutes=task_data['duration'],
                complexity_level=2,
                subjects_required=4,
                subject_role=SubjectRole.GROUP,
                materials=task_data['materials'],
                dependencies=[task_nodes[0].id] if i == 1 and task_nodes else []
            ))
        
        # Asignación: alternar grupos
        subject_assignments = {
            "task_001": [s.id for s in self.subjects[:4]],
            "task_002": [s.id for s in self.subjects[4:]]
        }
        
        total_duration = sum(task['duration'] for task in tasks_data)
        
        return ActivityGraph(
            id=f"level2_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"Actividad Colaborativa - {subject}",
            subject=subject,
            task_nodes=task_nodes,
            subject_assignments=subject_assignments,
            total_duration=total_duration,
            complexity_level=2,
            created_at=datetime.now().isoformat()
        )
    
    def _parse_tasks(self, llm_response: str, expected_tasks: int) -> List[Dict]:
        """Parsear respuesta LLM para extraer tareas"""
        tasks = []
        lines = [line.strip() for line in llm_response.split('\n') if 'Tarea' in line]
        
        for line in lines[:expected_tasks]:
            parts = line.split('|')
            if len(parts) >= 3:
                description = parts[0].split(':')[-1].strip()
                try:
                    duration = int(''.join(filter(str.isdigit, parts[1])))
                except:
                    duration = 30
                materials = [m.strip() for m in parts[2].split(',')][:3]
                
                tasks.append({
                    'description': description,
                    'duration': duration,
                    'materials': materials
                })
        
        # Fallback si parsing falla
        while len(tasks) < expected_tasks:
            tasks.append({
                'description': f"Tarea {len(tasks)+1}",
                'duration': 30,
                'materials': ["papel", "lápiz"]
            })
        
        return tasks

class Level3Generator(BaseGenerator):
    """Nivel 3: Proyecto multi-sesión, roles específicos, 2-3 días"""
    
    def create_activity(self, prompt: str, subject: str) -> ActivityGraph:
        llm_prompt = f"""
Crea un PROYECTO EDUCATIVO para 4º primaria sobre: {prompt}

Materia: {subject}
Duración: 2-3 días (sesiones de 45 min cada una)
Participantes: 8 estudiantes con roles específicos
Complejidad: avanzada

Crea 3-4 tareas en secuencia:
1. Investigación/preparación
2. Desarrollo/creación  
3. Revisión/mejora
4. Presentación/cierre

Para cada tarea especifica:
Tarea X: [descripción] | [duración] | [roles necesarios] | [materiales]
"""
        
        llm_response = self._generate_with_llm(llm_prompt)
        
        # Parsear proyecto complejo
        tasks_data = self._parse_complex_tasks(llm_response)
        
        task_nodes = []
        for i, task_data in enumerate(tasks_data):
            dependencies = [task_nodes[-1].id] if task_nodes else []
            
            task_nodes.append(TaskNode(
                id=f"task_{i+1:03d}",
                task_type=self._infer_task_type(task_data['description']),
                description=task_data['description'],
                duration_minutes=task_data['duration'],
                complexity_level=3,
                subjects_required=task_data['subjects_required'],
                subject_role=SubjectRole.GROUP,
                materials=task_data['materials'],
                dependencies=dependencies
            ))
        
        # Asignación más sofisticada
        subject_assignments = self._assign_subjects_to_tasks(task_nodes)
        
        total_duration = sum(node.duration_minutes for node in task_nodes)
        
        return ActivityGraph(
            id=f"level3_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"Proyecto - {subject}",
            subject=subject,
            task_nodes=task_nodes,
            subject_assignments=subject_assignments,
            total_duration=total_duration,
            complexity_level=3,
            created_at=datetime.now().isoformat()
        )
    
    def _parse_complex_tasks(self, llm_response: str) -> List[Dict]:
        """Parsear proyecto complejo"""
        # Implementación simplificada por ahora
        return [
            {'description': 'Investigación inicial', 'duration': 45, 'subjects_required': 8, 'materials': ['libros', 'internet']},
            {'description': 'Desarrollo del proyecto', 'duration': 60, 'subjects_required': 6, 'materials': ['cartulina', 'materiales']},
            {'description': 'Revisión y mejoras', 'duration': 30, 'subjects_required': 4, 'materials': ['checklist']},
            {'description': 'Presentación final', 'duration': 45, 'subjects_required': 8, 'materials': ['espacio', 'audiencia']}
        ]
    
    def _infer_task_type(self, description: str) -> TaskType:
        """Inferir tipo de tarea de la descripción"""
        desc_lower = description.lower()
        if 'investig' in desc_lower or 'buscar' in desc_lower:
            return TaskType.READ
        elif 'crear' in desc_lower or 'desarrollar' in desc_lower:
            return TaskType.CREATE
        elif 'revisar' in desc_lower or 'analizar' in desc_lower:
            return TaskType.ANALYZE
        elif 'presentar' in desc_lower or 'exponer' in desc_lower:
            return TaskType.PRESENT
        else:
            return TaskType.DISCUSS
    
    def _assign_subjects_to_tasks(self, task_nodes: List[TaskNode]) -> Dict[str, List[str]]:
        """Asignar sujetos a tareas de manera inteligente"""
        assignments = {}
        available_subjects = list(range(8))
        
        for task in task_nodes:
            if task.subjects_required >= 8:
                # Todos participan
                assignments[task.id] = [f"{i+1:03d}" for i in range(8)]
            elif task.subjects_required >= 4:
                # Grupo grande
                selected = available_subjects[:task.subjects_required]
                assignments[task.id] = [f"{i+1:03d}" for i in selected]
                # Rotar para próxima tarea
                available_subjects = available_subjects[2:] + available_subjects[:2]
            else:
                # Grupo pequeño
                selected = available_subjects[:task.subjects_required]
                assignments[task.id] = [f"{i+1:03d}" for i in selected]
        
        return assignments

# =============================================================================
# COORDINADOR PRINCIPAL
# =============================================================================

class NodeActivityGenerator:
    """Generador principal que decide qué nivel usar"""
    
    def __init__(self):
        self.generators = {
            1: Level1Generator(),
            2: Level2Generator(), 
            3: Level3Generator()
        }
    
    def generate(self, prompt: str, subject: str, complexity_level: int = None) -> ActivityGraph:
        """Genera actividad según nivel de complejidad"""
        
        if complexity_level is None:
            complexity_level = self._detect_complexity(prompt)
        
        # Clamp complexity level
        complexity_level = max(1, min(3, complexity_level))
        
        generator = self.generators[complexity_level]
        return generator.create_activity(prompt, subject)
    
    def _detect_complexity(self, prompt: str) -> int:
        """Detectar complejidad del prompt"""
        prompt_lower = prompt.lower()
        
        # Simple indicators
        simple_keywords = ['simple', 'básico', 'rápido', 'mañana', 'corto']
        complex_keywords = ['proyecto', 'semana', 'complejo', 'avanzado', 'investigación']
        
        if any(keyword in prompt_lower for keyword in simple_keywords):
            return 1
        elif any(keyword in prompt_lower for keyword in complex_keywords):
            return 3
        else:
            return 2
    
    def save_activity(self, activity: ActivityGraph, output_dir: str = "actividades_nodos"):
        """Guardar actividad generada"""
        
        # Crear directorio
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        # Generar contenido legible
        content = self._format_activity_content(activity)
        
        # Guardar archivo
        filename = f"{activity.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Guardar JSON para análisis
        json_filename = f"{activity.id}.json"
        json_filepath = os.path.join(full_output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            # Convert to dict for JSON serialization with enum handling
            activity_dict = self._convert_to_json_serializable(activity)
            json.dump(activity_dict, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _convert_to_json_serializable(self, activity: ActivityGraph) -> dict:
        """Convierte ActivityGraph a dict serializable en JSON"""
        activity_dict = asdict(activity)
        
        # Convertir enums a strings en task_nodes
        for task in activity_dict['task_nodes']:
            if 'task_type' in task:
                task['task_type'] = task['task_type'].value if hasattr(task['task_type'], 'value') else str(task['task_type'])
            if 'subject_role' in task:
                task['subject_role'] = task['subject_role'].value if hasattr(task['subject_role'], 'value') else str(task['subject_role'])
        
        return activity_dict
    
    def _format_activity_content(self, activity: ActivityGraph) -> str:
        """Formatear actividad para lectura humana"""
        
        content = f"""
{'='*80}
ACTIVIDAD GENERADA POR NODOS - {activity.title}
{'='*80}

📋 INFORMACIÓN GENERAL:
- ID: {activity.id}
- Materia: {activity.subject}
- Nivel de Complejidad: {activity.complexity_level}
- Duración Total: {activity.total_duration} minutos
- Número de Tareas: {len(activity.task_nodes)}
- Creado: {activity.created_at}

{'='*80}
📐 ESTRUCTURA DE TAREAS:
{'='*80}
"""
        
        for i, task in enumerate(activity.task_nodes, 1):
            assigned_subjects = activity.subject_assignments.get(task.id, [])
            
            content += f"""
🎯 TAREA {i}: {task.id}
───────────────────────────────────────────
• Tipo: {task.task_type.value}
• Descripción: {task.description}
• Duración: {task.duration_minutes} minutos
• Complejidad: {task.complexity_level}/5
• Sujetos requeridos: {task.subjects_required}
• Rol: {task.subject_role.value}
• Materiales: {', '.join(task.materials)}
• Dependencias: {', '.join(task.dependencies) if task.dependencies else 'Ninguna'}
• Estudiantes asignados: {', '.join(assigned_subjects)}

"""
        
        content += f"""
{'='*80}
👥 RESUMEN DE PARTICIPACIÓN:
{'='*80}
"""
        
        # Mostrar participación por estudiante
        for i in range(1, 9):
            student_id = f"{i:03d}"
            tasks_assigned = []
            for task_id, subjects in activity.subject_assignments.items():
                if student_id in subjects:
                    task_name = next((t.description for t in activity.task_nodes if t.id == task_id), task_id)
                    tasks_assigned.append(task_name)
            
            content += f"• Estudiante {student_id}: {len(tasks_assigned)} tareas\n"
            if tasks_assigned:
                for task in tasks_assigned:
                    content += f"  - {task}\n"
            content += "\n"
        
        content += f"""
{'='*80}
🔍 ANÁLISIS DEL GRAFO:
{'='*80}
- Tareas paralelas: {self._count_parallel_tasks(activity)}
- Tareas secuenciales: {self._count_sequential_tasks(activity)}
- Carga de trabajo equilibrada: {'Sí' if self._is_workload_balanced(activity) else 'No'}
- Duración promedio por tarea: {activity.total_duration / len(activity.task_nodes):.1f} minutos

{'='*80}
"""
        
        return content
    
    def _count_parallel_tasks(self, activity: ActivityGraph) -> int:
        """Contar tareas que pueden ejecutarse en paralelo"""
        return len([task for task in activity.task_nodes if not task.dependencies])
    
    def _count_sequential_tasks(self, activity: ActivityGraph) -> int:
        """Contar tareas que deben ejecutarse secuencialmente"""
        return len([task for task in activity.task_nodes if task.dependencies])
    
    def _is_workload_balanced(self, activity: ActivityGraph) -> bool:
        """Verificar si la carga está equilibrada entre estudiantes"""
        student_task_counts = {}
        for subjects in activity.subject_assignments.values():
            for subject in subjects:
                student_task_counts[subject] = student_task_counts.get(subject, 0) + 1
        
        if not student_task_counts:
            return True
        
        min_tasks = min(student_task_counts.values())
        max_tasks = max(student_task_counts.values())
        return (max_tasks - min_tasks) <= 1

# =============================================================================
# INTERFAZ SIMPLE PARA EXPERIMENTACIÓN
# =============================================================================

def main():
    """Interfaz minimalista para experimentar"""
    print("🧪 GENERADOR EXPERIMENTAL POR NODOS")
    print("="*50)
    
    generator = NodeActivityGenerator()
    
    while True:
        print("\n📝 ¿Qué actividad quieres generar?")
        prompt = input("Describe tu actividad: ").strip()
        
        if not prompt or prompt.lower() in ['salir', 'exit', 'quit']:
            break
        
        print("\n📚 ¿Qué materia?")
        subject = input("Materia (matematicas/lengua/ciencias): ").strip()
        if not subject:
            subject = "general"
        
        print("\n🎚️ ¿Qué nivel de complejidad?")
        print("1 = Simple (1 tarea, 45 min)")
        print("2 = Moderado (2-3 tareas, 60-90 min)")  
        print("3 = Complejo (proyecto, 2-3 días)")
        print("0 = Auto-detectar")
        
        try:
            complexity = int(input("Nivel (0-3): ").strip())
            if complexity == 0:
                complexity = None
        except:
            complexity = None
        
        print(f"\n🚀 Generando actividad...")
        
        try:
            activity = generator.generate(prompt, subject, complexity)
            filepath = generator.save_activity(activity)
            
            print(f"✅ Actividad generada:")
            print(f"   📁 Archivo: {filepath}")
            print(f"   🎯 Nivel: {activity.complexity_level}")
            print(f"   ⏱️ Duración: {activity.total_duration} min")
            print(f"   📋 Tareas: {len(activity.task_nodes)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        continue_prompt = input("\n¿Continuar? (s/n): ").strip().lower()
        if continue_prompt in ['n', 'no']:
            break
    
    print("\n👋 ¡Hasta luego!")

if __name__ == "__main__":
    main()