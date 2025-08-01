#!/usr/bin/env python3
"""
Sistema Cuántico-Agentes SIMPLIFICADO para Generación de Actividades Educativas
Versión funcional que genera actividades reales con validación cuántica básica
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

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
logger = logging.getLogger("QUANTUM_SIMPLE_SYSTEM")

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    from crewai_tools import FileReadTool, DirectoryReadTool
    from langchain_community.llms import Ollama
    logger.info("✅ CrewAI y LangChain importados correctamente")
    
except ImportError as e:
    logger.error(f"❌ Error de importación: {e}")
    logger.error("💡 Instala dependencias: pip install crewai crewai-tools langchain-community")
    raise ImportError("Dependencias no están disponibles")

from ollama_api_integrator import OllamaAPIEducationGenerator
from prompt_template import PromptTemplateGenerator


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


class ValidadorCuanticoSimple:
    """Validador cuántico simplificado sin problemas de memoria"""
    
    def __init__(self):
        logger.info("🔬 Validador Cuántico Simple inicializado")
    
    def validar_actividad(self, contenido_actividad: str, estudiantes: List[Dict]) -> Dict:
        """Valida una actividad usando heurísticas cuánticas simplificadas"""
        
        # Validaciones heurísticas basadas en principios cuánticos
        puntuacion_total = 0.0
        validaciones = []
        
        # VALIDACIÓN 1: Coherencia narrativa (0-25 puntos)
        if any(palabra in contenido_actividad.lower() for palabra in ['historia', 'narrativa', 'contexto', 'aventura', 'misión']):
            puntuacion_total += 25
            validaciones.append("✅ Coherencia narrativa detectada")
        else:
            validaciones.append("⚠️ Falta narrativa envolvente")
        
        # VALIDACIÓN 2: Roles específicos (0-25 puntos)
        roles_detectados = sum(1 for palabra in ['rol', 'función', 'responsabilidad', 'tarea específica'] 
                             if palabra in contenido_actividad.lower())
        if roles_detectados >= 2:
            puntuacion_total += 25
            validaciones.append("✅ Roles específicos definidos")
        else:
            validaciones.append("⚠️ Faltan roles específicos claros")
        
        # VALIDACIÓN 3: Adaptaciones para diversidad (0-25 puntos)  
        adaptaciones_detectadas = sum(1 for estudiante in ['elena', 'luis', 'ana'] 
                                    if estudiante in contenido_actividad.lower())
        if adaptaciones_detectadas >= 2:
            puntuacion_total += 25
            validaciones.append("✅ Adaptaciones para diversidad incluidas")
        else:
            validaciones.append("⚠️ Faltan adaptaciones específicas")
        
        # VALIDACIÓN 4: Estructura temporal (0-25 puntos)
        if any(palabra in contenido_actividad.lower() for palabra in ['preparación', 'desarrollo', 'cierre', 'minutos', 'tiempo']):
            puntuacion_total += 25
            validaciones.append("✅ Estructura temporal definida")
        else:
            validaciones.append("⚠️ Falta estructura temporal clara")
        
        validez_final = puntuacion_total / 100.0
        
        return {
            'validez': validez_final,
            'puntuacion': puntuacion_total,
            'validaciones': validaciones,
            'estado': '✅ Óptima' if validez_final > 0.8 else '⚠️ Mejorable' if validez_final > 0.5 else '❌ Requiere mejoras'
        }


class SistemaCuanticoSimple:
    """Sistema principal simplificado cuántico-agentes"""
    
    def __init__(self, 
                 ollama_host: str = "192.168.1.10",
                 generador_model: str = "qwen3:latest",
                 optimizador_model: str = "qwen3:latest",
                 perfiles_path: str = "perfiles_4_primaria.json"):
        
        self.ollama_host = ollama_host
        self.generador_model = generador_model
        self.optimizador_model = optimizador_model
        self.perfiles_path = perfiles_path
        
        # Inicializar validador cuántico
        self.validador_cuantico = ValidadorCuanticoSimple()
        
        # Configurar LLMs
        self._configurar_llms()
        
        # Cargar perfiles
        self.perfiles_data = self._cargar_perfiles(perfiles_path)
        
        # Crear agentes
        self._crear_agentes()
        
        logger.info("✅ Sistema Cuántico Simple inicializado")
    
    def _configurar_llms(self):
        """Configura los LLMs usando el patrón exitoso del sistema fewshot"""
        try:
            # Configurar LiteLLM correctamente para Ollama
            import litellm
            
            # Mapear modelos para LiteLLM
            modelos_unicos = set([self.generador_model, self.optimizador_model])
            for modelo in modelos_unicos:
                litellm.model_cost[f"ollama/{modelo}"] = {
                    "input_cost_per_token": 0,
                    "output_cost_per_token": 0,
                    "max_tokens": 4096
                }
            
            # Configurar variables específicas
            os.environ["OLLAMA_API_BASE"] = f"http://{self.ollama_host}:11434"
            os.environ["OLLAMA_BASE_URL"] = f"http://{self.ollama_host}:11434"
            
            # Crear LLMs específicos
            self.generador_llm = Ollama(
                model=f"ollama/{self.generador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            self.optimizador_llm = Ollama(
                model=f"ollama/{self.optimizador_model}",
                base_url=f"http://{self.ollama_host}:11434"
            )
            
            logger.info(f"✅ LLMs configurados exitosamente (patrón fewshot)")
            
        except Exception as e:
            logger.error(f"❌ Error configurando LLMs: {e}")
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
    
    def _crear_agentes(self):
        """Crea agentes especializados"""
        
        # AGENTE 1: GENERADOR DE ACTIVIDADES
        self.agente_generador = Agent(
            role="Generador de Actividades Educativas",
            goal="Crear actividades educativas completas, detalladas y ejecutables",
            backstory="Eres un maestro experto en crear actividades educativas memorables. Diseñas experiencias completas con narrativa, roles específicos, y adaptaciones para todos los estudiantes. Respondes siempre en español.",
            tools=[],
            llm=self.generador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        # AGENTE 2: OPTIMIZADOR CUÁNTICO
        self.agente_optimizador = Agent(
            role="Optimizador Cuántico Pedagógico",
            goal="Mejorar actividades basándose en validación cuántica y crear versiones optimizadas",
            backstory="Eres un especialista en optimización pedagógica que usa retroalimentación cuántica para mejorar actividades educativas. Tu trabajo es perfeccionar actividades basándote en análisis de coherencia, roles, adaptaciones y estructura. Respondes siempre en español.",
            tools=[],
            llm=self.optimizador_llm,
            verbose=True,
            allow_delegation=False
        )
        
        logger.info("✅ Agentes creados")
    
    def generar_actividad_cuantica(self, materia: str, tema: str = None) -> ActividadEducativa:
        """Genera actividad con validación cuántica simplificada"""
        
        logger.info(f"🔬 Generando actividad cuántica simple para {materia}")
        
        try:
            # FASE 1: Generar actividad inicial
            tarea_generacion = Task(
                description=f"""Crea una actividad educativa COMPLETA para {materia} sobre {tema or 'temas generales'} para 8 estudiantes de 4º Primaria.

ESTUDIANTES:
- 001 ALEX M.: reflexivo, visual, CI 102
- 002 MARÍA L.: reflexivo, auditivo
- 003 ELENA R.: reflexivo, visual, TEA nivel 1, CI 118
- 004 LUIS T.: impulsivo, kinestésico, TDAH combinado, CI 102
- 005 ANA V.: reflexivo, auditivo, altas capacidades, CI 141
- 006 SARA M.: equilibrado, auditivo, CI 115
- 007 EMMA K.: reflexivo, visual, CI 132
- 008 HUGO P.: equilibrado, visual, CI 114

CREA UNA ACTIVIDAD TIPO "LABORATORIO" o "MERCADO" o "EXPLORACIÓN":

=== ACTIVIDAD COMPLETA ===
**Título**: [Nombre atractivo]
**Objetivo**: Qué aprenden sobre {tema or materia}
**Duración**: 45-60 minutos
**Narrativa**: Historia que motiva (ej: "Somos científicos explorando...")

=== DESARROLLO PASO A PASO ===
**Preparación (10 min):**
- Organización del aula
- Materiales que necesitan
- Explicación inicial

**Desarrollo Principal (35 min):**
- Secuencia detallada de la actividad
- Cómo participan todos
- Qué hace cada estudiante

**Cierre (10 min):**
- Finalización
- Presentación de resultados

=== ROLES ESPECÍFICOS ===
Asigna un rol específico a cada estudiante:
- **ELENA R.**: [Rol específico] - [Función exacta] - [Adaptaciones para TEA]
- **LUIS T.**: [Rol específico] - [Función exacta] - [Adaptaciones para TDAH]
- **ANA V.**: [Rol específico] - [Función exacta] - [Desafíos adicionales]
- **ALEX M.**: [Rol específico] - [Función exacta]
- **MARÍA L.**: [Rol específico] - [Función exacta]
- **SARA M.**: [Rol específico] - [Función exacta]
- **EMMA K.**: [Rol específico] - [Función exacta]
- **HUGO P.**: [Rol específico] - [Función exacta]

=== MATERIALES NECESARIOS ===
Lista exacta con cantidades.

=== ADAPTACIONES ESPECIALES ===
- **Elena (TEA)**: Estrategias específicas
- **Luis (TDAH)**: Apoyo para su energía
- **Ana (Altas capacidades)**: Desafíos adicionales

Responde en español con máximo detalle. La actividad debe ser completamente ejecutable.""",
                agent=self.agente_generador,
                expected_output="Actividad educativa completa y detallada"
            )
            
            # Ejecutar generación inicial
            crew_inicial = Crew(
                agents=[self.agente_generador],
                tasks=[tarea_generacion],
                process=Process.sequential,
                verbose=True
            )
            
            resultado_inicial = crew_inicial.kickoff()
            
            # FASE 2: Validación cuántica
            logger.info("🔬 FASE 2: Validación cuántica")
            validacion = self.validador_cuantico.validar_actividad(str(resultado_inicial), self.perfiles_data)
            
            # FASE 3: Optimización si es necesario
            if validacion['validez'] < 0.7:
                logger.info("🔄 FASE 3: Optimización cuántica")
                
                tarea_optimizacion = Task(
                    description=f"""Optimiza la actividad basándote en la validación cuántica.

ACTIVIDAD ORIGINAL:
{resultado_inicial}

VALIDACIÓN CUÁNTICA:
- Validez actual: {validacion['validez']:.1%}
- Estado: {validacion['estado']}
- Puntuación: {validacion['puntuacion']}/100

PROBLEMAS DETECTADOS:
{chr(10).join(validacion['validaciones'])}

OPTIMIZA LA ACTIVIDAD:
1. Si falta narrativa envolvente, añade una historia motivadora
2. Si faltan roles específicos, define funciones claras para cada estudiante
3. Si faltan adaptaciones, añade estrategias específicas para Elena (TEA), Luis (TDAH) y Ana (altas capacidades)
4. Si falta estructura temporal, detalla preparación, desarrollo y cierre con tiempos

ENTREGA LA ACTIVIDAD MEJORADA manteniendo todo lo bueno de la original pero corrigiendo los problemas detectados.

Responde en español con la actividad optimizada completa.""",
                    agent=self.agente_optimizador,
                    expected_output="Actividad optimizada cuánticamente"
                )
                
                crew_optimizacion = Crew(
                    agents=[self.agente_optimizador],
                    tasks=[tarea_optimizacion],
                    process=Process.sequential,
                    verbose=True
                )
                
                resultado_final = crew_optimizacion.kickoff()
                
                # Validar de nuevo
                validacion_final = self.validador_cuantico.validar_actividad(str(resultado_final), self.perfiles_data)
            else:
                resultado_final = resultado_inicial
                validacion_final = validacion
            
            # Crear actividad final
            contenido_completo = f"""================================================================================
ACTIVIDAD OPTIMIZADA CUÁNTICAMENTE
================================================================================

🔬 VALIDACIÓN CUÁNTICA FINAL:
- Validez: {validacion_final['validez']:.1%}
- Puntuación: {validacion_final['puntuacion']}/100
- Estado: {validacion_final['estado']}

DETALLES DE VALIDACIÓN:
{chr(10).join(validacion_final['validaciones'])}

================================================================================
ACTIVIDAD EDUCATIVA COMPLETA
================================================================================

{resultado_final}

================================================================================
METADATOS CUÁNTICOS
================================================================================
- Sistema: Cuántico Simple
- Validaciones realizadas: 2
- Optimización aplicada: {'Sí' if validacion['validez'] < 0.7 else 'No necesaria'}
- Validez final: {validacion_final['validez']:.1%}
"""
            
            return ActividadEducativa(
                id=f"cuantico_simple_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Actividad Cuántica Simple - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=contenido_completo,
                estudiantes_objetivo=["001", "002", "003", "004", "005", "006", "007", "008"],
                tipo="cuantico_simple",
                adaptaciones=["validacion_cuantica", "optimizacion_automatica", "roles_especificos"],
                metadatos={
                    "total_estudiantes": 8,
                    "sistema_cuantico": "simple",
                    "validez_final": validacion_final['validez'],
                    "puntuacion_final": validacion_final['puntuacion'],
                    "optimizacion_aplicada": validacion['validez'] < 0.7,
                    "modelos_usados": {
                        "generador": self.generador_model,
                        "optimizador": self.optimizador_model
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error generando actividad cuántica: {e}")
            return ActividadEducativa(
                id=f"error_cuantico_{materia.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                titulo=f"Error Cuántico - {materia}",
                materia=materia,
                tema=tema or "tema general",
                contenido=f"Error en generación cuántica: {e}",
                estudiantes_objetivo=[],
                tipo="error_cuantico",
                adaptaciones=[],
                metadatos={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
    
    def guardar_actividad(self, actividad: ActividadEducativa, output_dir: str = "actividades_cuanticas_simples") -> str:
        """Guarda una actividad en un archivo"""
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_output_dir = os.path.join(script_dir, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)
        
        filename = f"{actividad.id}.txt"
        filepath = os.path.join(full_output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ACTIVIDAD GENERADA CON SISTEMA CUÁNTICO SIMPLE\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"ID: {actividad.id}\n")
            f.write(f"Título: {actividad.titulo}\n")
            f.write(f"Materia: {actividad.materia}\n")
            f.write(f"Tema: {actividad.tema}\n")
            f.write(f"Tipo: {actividad.tipo}\n")
            f.write(f"Estudiantes objetivo: {', '.join(actividad.estudiantes_objetivo)}\n")
            f.write(f"Timestamp: {actividad.timestamp}\n")
            f.write("\n" + "-" * 50 + "\n")
            f.write("CONTENIDO DE LA ACTIVIDAD:\n")
            f.write("-" * 50 + "\n\n")
            f.write(actividad.contenido)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("METADATOS CUÁNTICOS:\n")
            f.write(json.dumps(actividad.metadatos, indent=2, ensure_ascii=False))
            f.write("\n")
        
        logger.info(f"💾 Actividad cuántica guardada en: {filepath}")
        return filepath


def main():
    """Función principal del sistema cuántico simple"""
    
    print("="*70)
    print("🔬 SISTEMA CUÁNTICO SIMPLE PARA EDUCACIÓN")
    print("="*70)
    
    try:
        sistema = SistemaCuanticoSimple()
        
        print("\n✅ Sistema cuántico simple inicializado correctamente!")
        
        # Menú simple
        while True:
            print("\n" + "="*50)
            print("🔬 GENERACIÓN CUÁNTICA SIMPLE")
            print("1. 🎯 Generar actividad con validación cuántica")
            print("2. ❌ Salir")
            
            opcion = input("\n👉 Selecciona una opción (1-2): ").strip()
            
            if opcion == "1":
                materia = input("📚 Materia (matematicas/lengua/ciencias): ").strip()
                tema = input("📝 Tema específico (opcional): ").strip() or None
                
                start_time = datetime.now()
                actividad = sistema.generar_actividad_cuantica(materia, tema)
                archivo = sistema.guardar_actividad(actividad)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n✅ Actividad cuántica generada en {duration:.1f}s:")
                print(f"   📄 ID: {actividad.id}")
                print(f"   📁 Archivo: {archivo}")
                print(f"   🔬 Validez cuántica: {actividad.metadatos.get('validez_final', 0):.1%}")
            
            elif opcion == "2":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\n❌ Opción no válida. Selecciona 1-2.")
    
    except Exception as e:
        print(f"\n❌ Error inicializando sistema cuántico: {e}")


if __name__ == "__main__":
    main()