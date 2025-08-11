"""
Agente Generador de Recursos (Resource Generator Agent).
"""

import logging
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator
from agents.base_agent import BaseAgent
from utils.json_parser import parse_json_seguro

class AgenteGeneradorRecursos(BaseAgent):
    """Agente Generador de Recursos (Resource Generator Agent)"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """
        Inicializa el Agente Generador de Recursos
        
        Args:
            ollama_integrator: Integrador de LLM
        """
        super().__init__(ollama_integrator)
    
    def generar_recursos(self, proyecto_base: dict, tareas: list, asignaciones: dict, **kwargs) -> dict:
        """
        Genera una lista de recursos materiales, analógicos y digitales para el proyecto
        
        Args:
            proyecto_base: Información base del proyecto
            tareas: Lista de tareas
            asignaciones: Asignaciones de tareas a estudiantes
            **kwargs: Parámetros adicionales
            
        Returns:
            Diccionario con recursos generados
        """
        
        # Obtener información específica del proyecto
        titulo = proyecto_base.get('titulo', 'Actividad educativa')
        descripcion = proyecto_base.get('descripcion', 'No disponible')
        
        # Prompt mejorado para recursos con contexto específico
        prompt_recursos = f"""
Eres un experto en recursos educativos para 4º de Primaria.

PROYECTO: {titulo}
DESCRIPCIÓN: {descripcion}

TAREAS DEL PROYECTO:
{self._formatear_tareas_para_prompt(tareas)}

ESTUDIANTES ESPECIALES A CONSIDERAR:
- Elena (TEA): Necesita materiales estructurados y predecibles
- Luis (TDAH): Materiales que permitan movimiento y manipulación
- Ana (Altas capacidades): Recursos adicionales para profundizar

RESPONDE ÚNICAMENTE CON ESTE JSON (sin texto adicional):
{{
  "recursos_materiales": [
    "Recurso físico 1",
    "Recurso físico 2",
    "Recurso físico 3"
  ],
  "recursos_analogicos": [
    "Herramienta manipulativa 1",
    "Herramienta manipulativa 2"
  ],
  "recursos_digitales": [
    "Recurso digital 1",
    "Recurso digital 2"
  ]
}}"""
        
        self._log_processing_start(f"Generando recursos para: {titulo}")
        
        try:
            # Llamada al LLM y parseo robusto
            respuesta_llm = self.ollama.generar_respuesta(prompt_recursos, max_tokens=500)
            recursos_dict = parse_json_seguro(respuesta_llm)
            
            if recursos_dict:
                self.logger.info(f"✅ Recursos parseados correctamente")
                self._log_processing_end(f"Generados {self._contar_recursos(recursos_dict)} recursos")
                return recursos_dict
            else:
                raise ValueError("No se pudo parsear JSON de recursos")
                
        except Exception as e:
            self.logger.error(f"❌ Error al parsear recursos del LLM: {e}")
            self.logger.info("⚠️ Usando lógica de fallback para los recursos")
            
            # Generar recursos de fallback
            recursos_fallback = self._generar_recursos_fallback()
            self._log_processing_end(f"Generados {self._contar_recursos(recursos_fallback)} recursos fallback")
            return recursos_fallback
    
    def _formatear_tareas_para_prompt(self, tareas: list) -> str:
        """
        Formatea tareas para el prompt
        
        Args:
            tareas: Lista de tareas
            
        Returns:
            Texto formateado
        """
        texto = ""
        for i, tarea in enumerate(tareas):
            if hasattr(tarea, 'id') and hasattr(tarea, 'descripcion'):
                texto += f"- {tarea.id}: {tarea.descripcion}\n"
            elif isinstance(tarea, dict):
                tarea_id = tarea.get('id', f'tarea_{i+1}')
                desc = tarea.get('descripcion', 'No disponible')
                texto += f"- {tarea_id}: {desc}\n"
        
        return texto
    
    def _contar_recursos(self, recursos: dict) -> int:
        """
        Cuenta el número total de recursos
        
        Args:
            recursos: Diccionario con recursos
            
        Returns:
            Número total de recursos
        """
        total = 0
        for tipo, lista in recursos.items():
            if isinstance(lista, list):
                total += len(lista)
        return total
    
    def _generar_recursos_fallback(self) -> Dict:
        """
        Genera recursos de fallback
        
        Returns:
            Diccionario con recursos de fallback
        """
        return {
            "recursos_materiales": [
                # Materiales educativos básicos
                "Papel", "Lápices", "Marcadores", "Pintura", "Tijeras", "Pegamento",
                "Cartulinas", "Rotuladores", "Reglas", "Gomas de borrar"
            ],
            "recursos_analogicos": [
                # Recursos manipulativos básicos
                "Regletas de Cuisenaire", "Bloques lógicos", "Material de construcción",
                "Juegos de mesa educativos", "Puzzles", "Dados"
            ],
            "recursos_digitales": [
                # Herramientas digitales básicas
                "Editor de texto", "Buscador de imágenes", "Calculadora", 
                "Herramientas de presentación", "Apps educativas"
            ]
        }
    
    def _generar_recursos_contextuales(self, tematica: str) -> Dict:
        """
        Genera recursos contextuales según la temática
        
        Args:
            tematica: Temática del proyecto
            
        Returns:
            Diccionario con recursos contextuales
        """
        recursos_base = self._generar_recursos_fallback()
        
        # Recursos específicos según temática
        recursos_tematicos = {
            "matematicas": {
                "recursos_materiales": ["Ábacos", "Fichas numéricas", "Monedas didácticas", "Billetes didácticos"],
                "recursos_analogicos": ["Balanzas", "Metros", "Relojes manipulativos"],
                "recursos_digitales": ["GeoGebra", "Aplicaciones de cálculo mental"]
            },
            "lengua": {
                "recursos_materiales": ["Tarjetas de vocabulario", "Libros de lectura", "Fichas de ortografía"],
                "recursos_analogicos": ["Juegos de letras", "Dados para crear historias", "Títeres"],
                "recursos_digitales": ["Procesador de textos", "Aplicaciones de lectura"]
            },
            "ciencias": {
                "recursos_materiales": ["Muestras de rocas", "Semillas", "Lupas", "Microscopios escolares"],
                "recursos_analogicos": ["Maquetas del cuerpo humano", "Kits de experimentos", "Terrarios"],
                "recursos_digitales": ["Simuladores de experimentos", "Vídeos educativos de ciencias"]
            },
            "geografia": {
                "recursos_materiales": ["Mapas físicos", "Globo terráqueo", "Atlas", "Fichas de países"],
                "recursos_analogicos": ["Maquetas de relieve", "Puzzles de mapas", "Juegos de orientación"],
                "recursos_digitales": ["Google Earth", "Mapas interactivos"]
            },
            "historia": {
                "recursos_materiales": ["Líneas del tiempo", "Imágenes históricas", "Reproducciones de objetos"],
                "recursos_analogicos": ["Disfraces históricos", "Maquetas de monumentos", "Juegos de rol"],
                "recursos_digitales": ["Vídeos históricos", "Reconstrucciones virtuales"]
            },
            "arte": {
                "recursos_materiales": ["Témperas", "Arcilla", "Pinceles", "Papel de diferentes texturas"],
                "recursos_analogicos": ["Moldes", "Espátulas", "Caballetes pequeños"],
                "recursos_digitales": ["Aplicaciones de dibujo", "Galerías de arte virtuales"]
            }
        }
        
        # Comprobar si la temática existe
        if tematica.lower() in recursos_tematicos:
            recursos_tematicos_especificos = recursos_tematicos[tematica.lower()]
            
            # Añadir recursos temáticos a recursos base
            for tipo, lista in recursos_tematicos_especificos.items():
                if tipo in recursos_base:
                    recursos_base[tipo].extend(lista)
        
        return recursos_base
    
    # Implementación de métodos abstractos de BaseAgent
    def process(self, proyecto_base: dict, tareas: list, asignaciones: dict, **kwargs) -> Dict:
        """
        Implementa el método abstracto process de BaseAgent
        
        Args:
            proyecto_base: Información base del proyecto
            tareas: Lista de tareas
            asignaciones: Asignaciones de tareas a estudiantes
            **kwargs: Parámetros adicionales
            
        Returns:
            Diccionario con recursos generados
        """
        return self.generar_recursos(proyecto_base, tareas, asignaciones, **kwargs)
    
    def _parse_response(self, response: str) -> Dict:
        """
        Parsea respuesta del LLM para recursos
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Diccionario con recursos
        """
        return parse_json_seguro(response)