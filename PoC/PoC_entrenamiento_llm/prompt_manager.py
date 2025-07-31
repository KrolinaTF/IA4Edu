#!/usr/bin/env python3
"""
Sistema Modular de Templates y Prompts para CrewAI
Gestiona prompts reutilizables, concisos y contextualizados
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EstudianteResumen:
    """Resumen conciso de un estudiante"""
    id: str
    nombre: str
    temperamento: str
    canal: str
    diagnostico: str
    ci: Optional[int] = None


class PromptTemplateManager:
    """Gestiona templates reutilizables y contextualizados"""
    
    def __init__(self, perfiles_data: List[Dict]):
        self.perfiles = perfiles_data
        self.estudiantes_resumen = self._procesar_estudiantes()
        self.templates = self._cargar_templates()
    
    def _procesar_estudiantes(self) -> List[EstudianteResumen]:
        """Convierte perfiles completos en resúmenes concisos"""
        estudiantes = []
        for p in self.perfiles[:8]:  # Solo 8 estudiantes del aula
            estudiante = EstudianteResumen(
                id=p.get('id', 'N/A'),
                nombre=p.get('nombre', 'N/A'),
                temperamento=p.get('temperamento', 'equilibrado'),
                canal=p.get('canal_preferido', 'mixto'),
                diagnostico=p.get('diagnostico_formal', 'ninguno'),
                ci=p.get('ci_base', None)
            )
            estudiantes.append(estudiante)
        return estudiantes
    
    def _cargar_templates(self) -> Dict:
        """Carga templates organizados por materia y tipo de tarea"""
        return {
            "matematicas": {
                "ambiente": """Analiza el grupo y diseña el ambiente de aprendizaje óptimo para matemáticas.

GRUPO DE ESTUDIANTES:
{estudiantes}

TAREA:
1. USA la herramienta diseñar_ambiente UNA SOLA VEZ pasando el resumen de estudiantes
2. Define el tono y características generales de la actividad

El resultado debe incluir nivel de energía, tipo de interacción, modalidad sensorial y duración óptima.""",

                "diseno": """Diseña una actividad colaborativa de matemáticas: {tema}

Basa el diseño en el ambiente definido anteriormente.

Crea una actividad con:
- Título y objetivo matemático claro
- Lista de materiales necesarios  
- 3 fases: Preparación (10min) + Desarrollo (45min) + Cierre (15min)
- Componentes que requieran colaboración real

Usa verificar_curriculum para confirmar que cumple objetivos de 4º Primaria.

Ejemplo de actividad: {ejemplo}""",

                "desglose": """Descompone la actividad en tareas específicas.

USA la herramienta descomponer_tareas UNA SOLA VEZ pasando la descripción completa de la actividad diseñada.

La herramienta identificará las tareas principales y sus características.""",

                "asignacion": """Asigna roles específicos a cada estudiante según sus fortalezas.

USA la herramienta asignar_tareas_estudiantes UNA SOLA VEZ pasando toda la información disponible (actividad + tareas + perfiles).

La herramienta creará asignaciones personalizadas considerando la Zona de Desarrollo Próximo de cada estudiante."""
            },
            
            "ciencias": {
                "ambiente": """Analiza el grupo y diseña el ambiente de aprendizaje óptimo para ciencias.

GRUPO DE ESTUDIANTES:
{estudiantes}

TAREA:
USA la herramienta diseñar_ambiente UNA SOLA VEZ pasando el resumen de estudiantes.
Considera las necesidades para experimentación y observación científica.""",

                "diseno": """Diseña una actividad colaborativa de ciencias: {tema}

Basa el diseño en el ambiente definido anteriormente.

Crea una actividad científica con:
- Título y objetivo de investigación
- Materiales para experimentación u observación
- 3 fases: Hipótesis (10min) + Investigación (40min) + Conclusiones (10min)
- Aplicación del método científico

Usa verificar_curriculum para confirmar objetivos de 4º Primaria.

Ejemplo: {ejemplo}""",

                "desglose": """Descompone la actividad científica en tareas específicas.

USA la herramienta descomponer_tareas UNA SOLA VEZ pasando la descripción completa de la actividad científica.

La herramienta identificará las tareas del método científico.""",

                "asignacion": """Asigna roles de investigación a cada estudiante.

USA la herramienta asignar_tareas_estudiantes UNA SOLA VEZ pasando toda la información disponible.

La herramienta creará un equipo investigativo equilibrado considerando fortalezas científicas."""
            },
            
            "lengua": {
                "ambiente": """Analiza el grupo y diseña el ambiente de aprendizaje óptimo para lengua.

GRUPO DE ESTUDIANTES:
{estudiantes}

TAREA:
USA la herramienta diseñar_ambiente UNA SOLA VEZ pasando el resumen de estudiantes.
Considera las necesidades comunicativas y de expresión del grupo.""",

                "diseno": """Diseña una actividad colaborativa de lengua: {tema}

Basa el diseño en el ambiente definido anteriormente.

Crea una actividad comunicativa con:
- Título y objetivo lingüístico
- Materiales textuales o audiovisuales
- 3 fases: Planificación (10min) + Creación (35min) + Presentación (15min)
- Integración de competencias comunicativas

Usa verificar_curriculum para confirmar objetivos de 4º Primaria.

Ejemplo: {ejemplo}""",

                "desglose": """Descompone la actividad comunicativa en tareas específicas.

USA la herramienta descomponer_tareas UNA SOLA VEZ pasando la descripción completa de la actividad de lengua.

La herramienta identificará las tareas comunicativas necesarias.""",

                "asignacion": """Asigna roles comunicativos a cada estudiante.

USA la herramienta asignar_tareas_estudiantes UNA SOLA VEZ pasando toda la información disponible.

La herramienta creará un equipo comunicativo equilibrado considerando fortalezas lingüísticas."""
            }
        }
    
    def get_estudiantes_resumen(self) -> str:
        """Resumen detallado para análisis"""
        return "\n".join([
            f"- {e.id} {e.nombre}: {e.temperamento}, {e.canal}, {e.diagnostico}" + 
            (f", CI {e.ci}" if e.ci and isinstance(e.ci, int) else "")
            for e in self.estudiantes_resumen
        ])
    
    def get_estudiantes_corto(self) -> str:
        """Resumen muy conciso para tareas de diseño"""
        return f"{len(self.estudiantes_resumen)} estudiantes 4º Primaria: {self._get_diversidad_resumen()}"
    
    def _get_diversidad_resumen(self) -> str:
        """Resumen de diversidad del grupo"""
        diagnosticos = [e.diagnostico for e in self.estudiantes_resumen if e.diagnostico != 'ninguno']
        canales = [e.canal for e in self.estudiantes_resumen]
        
        div_text = []
        if diagnosticos:
            div_text.append(f"{len(diagnosticos)} con diagnósticos")
        
        canal_counts = {canal: canales.count(canal) for canal in set(canales)}
        canal_main = max(canal_counts, key=canal_counts.get)
        div_text.append(f"mayoría {canal_main}")
        
        return ", ".join(div_text)
    
    def get_ejemplo_template(self, materia: str) -> str:
        """Template breve específico por materia"""
        ejemplos = {
            "matematicas": "Tienda matemática: 3 cajeros + 4 clientes + 1 supervisor",
            "ciencias": "Laboratorio espacial: 2 investigadores + 4 técnicos + 2 comunicadores", 
            "lengua": "Redacción colaborativa: 1 coordinador + 3 escritores + 4 revisores"
        }
        return ejemplos.get(materia, "Actividad colaborativa estructurada")
    
    def generar_prompt(self, materia: str, tipo_tarea: str, tema: str = None) -> str:
        """Genera prompt contextualizado dinámicamente"""
        if materia not in self.templates:
            raise ValueError(f"Materia '{materia}' no disponible. Disponibles: {list(self.templates.keys())}")
        
        if tipo_tarea not in self.templates[materia]:
            raise ValueError(f"Tipo tarea '{tipo_tarea}' no disponible para {materia}")
        
        template = self.templates[materia][tipo_tarea]
        
        # Contexto dinámico según tipo de tarea
        contexto = {
            "tema": tema or f"tema general de {materia}",
            "estudiantes": self.get_estudiantes_resumen(),
            "estudiantes_corto": self.get_estudiantes_corto(),
            "ejemplo": self.get_ejemplo_template(materia)
        }
        
        return template.format(**contexto)
    
    def listar_templates_disponibles(self) -> Dict[str, List[str]]:
        """Lista todos los templates disponibles"""
        return {materia: list(tareas.keys()) for materia, tareas in self.templates.items()}


# EJEMPLOS DE USO
if __name__ == "__main__":
    # Simular datos de perfiles
    perfiles_ejemplo = [
        {"id": "001", "nombre": "ALEX M.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 102},
        {"id": "002", "nombre": "MARÍA L.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno"},
        {"id": "003", "nombre": "ELENA R.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "TEA_nivel_1", "ci_base": 118},
        {"id": "004", "nombre": "LUIS T.", "temperamento": "impulsivo", "canal_preferido": "kinestésico", "diagnostico_formal": "TDAH_combinado", "ci_base": 102},
        {"id": "005", "nombre": "ANA V.", "temperamento": "reflexivo", "canal_preferido": "auditivo", "diagnostico_formal": "altas_capacidades", "ci_base": 141},
        {"id": "006", "nombre": "SARA M.", "temperamento": "equilibrado", "canal_preferido": "auditivo", "diagnostico_formal": "ninguno", "ci_base": 115},
        {"id": "007", "nombre": "EMMA K.", "temperamento": "reflexivo", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 132},
        {"id": "008", "nombre": "HUGO P.", "temperamento": "equilibrado", "canal_preferido": "visual", "diagnostico_formal": "ninguno", "ci_base": 114}
    ]
    
    # Crear manager
    manager = PromptTemplateManager(perfiles_ejemplo)
    
    # Generar prompts
    print("=== PROMPT ANÁLISIS MATEMÁTICAS ===")
    print(manager.generar_prompt("matematicas", "analisis"))
    
    print("\n=== PROMPT DISEÑO CIENCIAS ===")
    print(manager.generar_prompt("ciencias", "diseno", "el sistema solar"))
    
    print("\n=== TEMPLATES DISPONIBLES ===")
    print(json.dumps(manager.listar_templates_disponibles(), indent=2, ensure_ascii=False))