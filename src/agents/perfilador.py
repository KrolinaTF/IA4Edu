"""
Agente Perfilador de Estudiantes - AULA_A_4PRIM.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional

from core.ollama_integrator import OllamaIntegrator
from agents.base_agent import BaseAgent
from models.estudiante import Estudiante
from models.proyecto import Tarea

class AgentePerfiladorEstudiantes(BaseAgent):
    """Agente Perfilador de Estudiantes - AULA_A_4PRIM"""
    
    def __init__(self, ollama_integrator: OllamaIntegrator):
        """
        Inicializa el Agente Perfilador de Estudiantes
        
        Args:
            ollama_integrator: Integrador de LLM
        """
        super().__init__(ollama_integrator)
        self.perfiles_base = self._cargar_perfiles_reales()
        self.logger.info(f"👥 Perfilador inicializado con {len(self.perfiles_base)} estudiantes del AULA_A_4PRIM")
    
    def _cargar_perfiles_reales(self) -> List[Estudiante]:
        """
        Carga los perfiles reales específicos del AULA_A_4PRIM desde el archivo JSON
        
        Returns:
            Lista de objetos Estudiante
        """
        try:
            # Obtener ruta absoluta al archivo de perfiles
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)  # Subir un nivel desde /agents
            perfiles_path = os.path.join(base_dir, "data", "perfiles_4_primaria.json")
            
            # Si el archivo no existe, crear uno genérico
            if not os.path.exists(perfiles_path):
                self._crear_perfiles_genericos(perfiles_path)
            
            with open(perfiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            estudiantes = []
            for perfil in data["estudiantes"]:
                # Extraer información rica del JSON
                fortalezas = self._extraer_fortalezas(perfil)
                necesidades_apoyo = self._extraer_necesidades_apoyo(perfil)
                adaptaciones = perfil.get("necesidades_especiales", [])
                historial_roles = self._generar_historial_roles(perfil)
                
                estudiante = Estudiante(
                    id=perfil["id"],
                    nombre=perfil["nombre"],
                    fortalezas=fortalezas,
                    necesidades_apoyo=necesidades_apoyo,
                    disponibilidad=self._calcular_disponibilidad(perfil),
                    historial_roles=historial_roles,
                    adaptaciones=adaptaciones
                )
                estudiantes.append(estudiante)
            
            # Log detallado de estudiantes cargados
            self.logger.info(f"✅ AULA_A_4PRIM: Cargados {len(estudiantes)} perfiles reales:")
            for est in estudiantes:
                # Buscar el perfil original para obtener el diagnóstico
                perfil_original = next((p for p in data["estudiantes"] if p["id"] == est.id), {})
                diagnostico = self._obtener_diagnostico_legible(perfil_original.get("diagnostico_formal", "ninguno"))
                self.logger.info(f"   • {est.nombre} (ID: {est.id}) - {diagnostico}")
            
            return estudiantes
            
        except FileNotFoundError:
            self.logger.error(f"❌ No se encontró el archivo de perfiles. Se creará uno genérico.")
            return self._crear_estudiantes_genericos()
        except Exception as e:
            self.logger.error(f"❌ Error cargando perfiles reales: {e}")
            return self._crear_estudiantes_genericos()
    
    def _crear_perfiles_genericos(self, perfiles_path: str) -> None:
        """
        Crea un archivo de perfiles genéricos si no existe
        
        Args:
            perfiles_path: Ruta donde crear el archivo
        """
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(perfiles_path), exist_ok=True)
        
        # Crear datos de perfiles genéricos
        perfiles = {
            "estudiantes": [
                {
                    "id": "001",
                    "nombre": "Alex M.",
                    "diagnostico_formal": "ninguno",
                    "nivel_apoyo": "bajo",
                    "estilo_aprendizaje": ["visual"],
                    "canal_preferido": "visual",
                    "temperamento": "reflexivo",
                    "tolerancia_frustracion": "media",
                    "intereses": ["ciencias", "lectura"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "EN_PROCESO"
                    },
                    "lengua": {
                        "tiempos_verbales": "CONSEGUIDO",
                        "textos_informativos": "CONSEGUIDO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "EN_PROCESO"
                    }
                },
                {
                    "id": "002",
                    "nombre": "María L.",
                    "diagnostico_formal": "ninguno",
                    "nivel_apoyo": "bajo",
                    "estilo_aprendizaje": ["auditivo"],
                    "canal_preferido": "auditivo",
                    "temperamento": "reflexivo",
                    "tolerancia_frustracion": "alta",
                    "intereses": ["lectura", "escritura"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "CONSEGUIDO"
                    },
                    "lengua": {
                        "tiempos_verbales": "SUPERADO",
                        "textos_informativos": "CONSEGUIDO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "CONSEGUIDO"
                    }
                },
                {
                    "id": "003",
                    "nombre": "Elena R.",
                    "diagnostico_formal": "TEA_nivel_1",
                    "nivel_apoyo": "alto",
                    "estilo_aprendizaje": ["visual"],
                    "canal_preferido": "visual",
                    "temperamento": "reflexivo",
                    "tolerancia_frustracion": "baja",
                    "intereses": ["patrones", "orden", "ciencias"],
                    "necesidades_especiales": ["apoyo visual", "estructuración", "predictibilidad"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "CONSEGUIDO"
                    },
                    "lengua": {
                        "tiempos_verbales": "EN_PROCESO",
                        "textos_informativos": "EN_PROCESO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "CONSEGUIDO"
                    }
                },
                {
                    "id": "004",
                    "nombre": "Luis T.",
                    "diagnostico_formal": "TDAH_combinado",
                    "nivel_apoyo": "alto",
                    "estilo_aprendizaje": ["kinestesico"],
                    "canal_preferido": "kinestesico",
                    "temperamento": "impulsivo",
                    "tolerancia_frustracion": "baja",
                    "intereses": ["deportes", "movimiento", "experimentos"],
                    "necesidades_especiales": ["movimiento", "fraccionamiento tareas", "descansos"],
                    "matematicas": {
                        "numeros_10000": "EN_PROCESO",
                        "operaciones_complejas": "INICIADO"
                    },
                    "lengua": {
                        "tiempos_verbales": "INICIADO",
                        "textos_informativos": "EN_PROCESO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "EN_PROCESO"
                    }
                },
                {
                    "id": "005",
                    "nombre": "Ana V.",
                    "diagnostico_formal": "altas_capacidades",
                    "nivel_apoyo": "medio",
                    "estilo_aprendizaje": ["auditivo"],
                    "canal_preferido": "auditivo",
                    "temperamento": "reflexivo",
                    "tolerancia_frustracion": "media",
                    "intereses": ["matemáticas", "lectura", "investigación"],
                    "necesidades_especiales": ["enriquecimiento", "desafíos", "autonomía"],
                    "matematicas": {
                        "numeros_10000": "SUPERADO",
                        "operaciones_complejas": "SUPERADO"
                    },
                    "lengua": {
                        "tiempos_verbales": "SUPERADO",
                        "textos_informativos": "SUPERADO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "SUPERADO"
                    }
                },
                {
                    "id": "006",
                    "nombre": "Sara M.",
                    "diagnostico_formal": "ninguno",
                    "nivel_apoyo": "bajo",
                    "estilo_aprendizaje": ["auditivo"],
                    "canal_preferido": "auditivo",
                    "temperamento": "equilibrado",
                    "tolerancia_frustracion": "alta",
                    "intereses": ["arte", "trabajo_en_grupo"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "EN_PROCESO"
                    },
                    "lengua": {
                        "tiempos_verbales": "CONSEGUIDO",
                        "textos_informativos": "CONSEGUIDO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "EN_PROCESO"
                    }
                },
                {
                    "id": "007",
                    "nombre": "Emma K.",
                    "diagnostico_formal": "ninguno",
                    "nivel_apoyo": "bajo",
                    "estilo_aprendizaje": ["visual"],
                    "canal_preferido": "visual",
                    "temperamento": "reflexivo",
                    "tolerancia_frustracion": "alta",
                    "intereses": ["lectura", "arte"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "CONSEGUIDO"
                    },
                    "lengua": {
                        "tiempos_verbales": "SUPERADO",
                        "textos_informativos": "SUPERADO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "CONSEGUIDO"
                    }
                },
                {
                    "id": "008",
                    "nombre": "Hugo P.",
                    "diagnostico_formal": "ninguno",
                    "nivel_apoyo": "medio",
                    "estilo_aprendizaje": ["visual"],
                    "canal_preferido": "visual",
                    "temperamento": "equilibrado",
                    "tolerancia_frustracion": "media",
                    "intereses": ["ciencias", "experimentos"],
                    "matematicas": {
                        "numeros_10000": "CONSEGUIDO",
                        "operaciones_complejas": "EN_PROCESO"
                    },
                    "lengua": {
                        "tiempos_verbales": "CONSEGUIDO",
                        "textos_informativos": "EN_PROCESO"
                    },
                    "ciencias": {
                        "metodo_cientifico": "CONSEGUIDO"
                    }
                }
            ]
        }
        
        # Guardar en archivo JSON
        with open(perfiles_path, "w", encoding="utf-8") as f:
            json.dump(perfiles, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"✅ Archivo de perfiles genéricos creado en: {perfiles_path}")
    
    def _crear_estudiantes_genericos(self) -> List[Estudiante]:
        """
        Crea estudiantes genéricos para casos donde no se puedan cargar perfiles
        
        Returns:
            Lista de objetos Estudiante
        """
        self.logger.warning("⚠️ Usando perfiles de estudiantes genéricos")
        
        return [
            Estudiante(
                id="001",
                nombre="Alex M.",
                fortalezas=["matemáticas_números", "comunicación_escrita"],
                necesidades_apoyo=[],
                disponibilidad=90,
                historial_roles=["analista_información"],
                adaptaciones=[]
            ),
            Estudiante(
                id="002",
                nombre="María L.",
                fortalezas=["comunicación_escrita", "gramática"],
                necesidades_apoyo=[],
                disponibilidad=95,
                historial_roles=["comunicador"],
                adaptaciones=[]
            ),
            Estudiante(
                id="003",
                nombre="Elena R.",
                fortalezas=["matemáticas_números", "pensamiento_analítico"],
                necesidades_apoyo=["rutinas_estructuradas", "ambiente_predecible", "apoyos_visuales"],
                disponibilidad=70,
                historial_roles=["diseñador_visual"],
                adaptaciones=["apoyo visual", "estructuración", "predictibilidad"]
            ),
            Estudiante(
                id="004",
                nombre="Luis T.",
                fortalezas=["experimentación"],
                necesidades_apoyo=["instrucciones_claras", "descansos_frecuentes", "actividades_manipulativas"],
                disponibilidad=65,
                historial_roles=["experimentador"],
                adaptaciones=["movimiento", "fraccionamiento tareas", "descansos"]
            ),
            Estudiante(
                id="005",
                nombre="Ana V.",
                fortalezas=["matemáticas_números", "operaciones_matemáticas", "comunicación_escrita", "investigación"],
                necesidades_apoyo=["retos_adicionales", "proyectos_autonomos"],
                disponibilidad=85,
                historial_roles=["investigador_científico", "mentor_académico"],
                adaptaciones=["enriquecimiento", "desafíos", "autonomía"]
            ),
            Estudiante(
                id="006",
                nombre="Sara M.",
                fortalezas=["colaboración", "comunicación_escrita"],
                necesidades_apoyo=["explicaciones_verbales"],
                disponibilidad=90,
                historial_roles=["facilitador_grupal"],
                adaptaciones=[]
            ),
            Estudiante(
                id="007",
                nombre="Emma K.",
                fortalezas=["pensamiento_analítico", "comunicación_escrita"],
                necesidades_apoyo=["apoyos_visuales"],
                disponibilidad=90,
                historial_roles=["diseñador_visual", "analista_información"],
                adaptaciones=[]
            ),
            Estudiante(
                id="008",
                nombre="Hugo P.",
                fortalezas=["experimentación", "investigación"],
                necesidades_apoyo=["apoyos_visuales"],
                disponibilidad=85,
                historial_roles=["experimentador"],
                adaptaciones=[]
            )
        ]
    
    def _extraer_fortalezas(self, perfil: dict) -> List[str]:
        """
        Extrae fortalezas basándose en competencias conseguidas e intereses
        
        Args:
            perfil: Diccionario con perfil del estudiante
            
        Returns:
            Lista de fortalezas
        """
        fortalezas = []
        
        # Basado en competencias conseguidas/superadas
        if perfil["matematicas"].get("numeros_10000") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("matemáticas_números")
        if perfil["matematicas"].get("operaciones_complejas") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("operaciones_matemáticas")
        if perfil["lengua"].get("tiempos_verbales") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("gramática")
        if perfil["lengua"].get("textos_informativos") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("comunicación_escrita")
        if perfil["ciencias"].get("metodo_cientifico") in ["CONSEGUIDO", "SUPERADO"]:
            fortalezas.append("investigación")
        
        # Basado en intereses
        for interes in perfil["intereses"]:
            if interes == "ciencias":
                fortalezas.append("curiosidad_científica")
            elif interes == "experimentos":
                fortalezas.append("experimentación")
            elif interes == "trabajo_en_grupo":
                fortalezas.append("colaboración")
            elif interes == "lectura":
                fortalezas.append("comprensión_lectora")
        
        # Basado en características específicas
        if perfil["temperamento"] == "reflexivo":
            fortalezas.append("pensamiento_analítico")
        if perfil["tolerancia_frustracion"] == "alta":
            fortalezas.append("perseverancia")
            
        return fortalezas  # Devolver todas las fortalezas identificadas
    
    def _extraer_necesidades_apoyo(self, perfil: dict) -> List[str]:
        """
        Extrae necesidades de apoyo basándose en el perfil completo
        
        Args:
            perfil: Diccionario con perfil del estudiante
            
        Returns:
            Lista de necesidades de apoyo
        """
        necesidades = []
        
        # Basado en nivel de apoyo
        if perfil["nivel_apoyo"] == "alto":
            necesidades.append("supervisión_continua")
        elif perfil["nivel_apoyo"] == "medio":
            necesidades.append("check_ins_regulares")
        
        # Basado en tolerancia a la frustración
        if perfil["tolerancia_frustracion"] == "baja":
            necesidades.append("apoyo_emocional")
            necesidades.append("tareas_graduadas")
        
        # Basado en canal preferido
        if perfil["canal_preferido"] == "visual":
            necesidades.append("apoyos_visuales")
        elif perfil["canal_preferido"] == "auditivo":
            necesidades.append("explicaciones_verbales")
        elif perfil["canal_preferido"] == "kinestésico":
            necesidades.append("actividades_manipulativas")
        
        # Basado en diagnóstico formal
        diagnostico = perfil.get("diagnostico_formal", "ninguno")
        if "TEA" in diagnostico:
            necesidades.extend(["rutinas_estructuradas", "ambiente_predecible"])
        elif "TDAH" in diagnostico:
            necesidades.extend(["instrucciones_claras", "descansos_frecuentes"])
        elif "altas_capacidades" in diagnostico:
            necesidades.extend(["retos_adicionales", "proyectos_autonomos"])
        
        return necesidades
    
    def _calcular_disponibilidad(self, perfil: dict) -> int:
        """
        Calcula disponibilidad basada en múltiples factores
        
        Args:
            perfil: Diccionario con perfil del estudiante
            
        Returns:
            Valor de disponibilidad (60-100)
        """
        disponibilidad = 85  # Base
        
        # Ajustar por nivel de apoyo
        if perfil["nivel_apoyo"] == "bajo":
            disponibilidad += 10
        elif perfil["nivel_apoyo"] == "alto":
            disponibilidad -= 15
        
        # Ajustar por tolerancia a frustración
        if perfil["tolerancia_frustracion"] == "alta":
            disponibilidad += 5
        elif perfil["tolerancia_frustracion"] == "baja":
            disponibilidad -= 10
        
        # Ajustar por temperamento
        if perfil["temperamento"] == "impulsivo":
            disponibilidad -= 5
        
        return max(60, min(100, disponibilidad))  # Entre 60-100
    
    def _generar_historial_roles(self, perfil: dict) -> List[str]:
        """
        Genera historial de roles basado en fortalezas y estilo de aprendizaje
        
        Args:
            perfil: Diccionario con perfil del estudiante
            
        Returns:
            Lista de roles
        """
        roles = []
        
        # Roles basados en estilo de aprendizaje
        if "visual" in perfil["estilo_aprendizaje"]:
            roles.append("diseñador_visual")
        if "auditivo" in perfil["estilo_aprendizaje"]:
            roles.append("comunicador")
        if "kinestésico" in perfil["estilo_aprendizaje"]:
            roles.append("experimentador")
        
        # Roles basados en intereses
        if "ciencias" in perfil["intereses"]:
            roles.append("investigador_científico")
        if "experimentos" in perfil["intereses"]:
            roles.append("experimentador")
        if "trabajo_colaborativo" in perfil["intereses"]:
            roles.append("facilitador_grupal")
        if "lectura" in perfil["intereses"]:
            roles.append("analista_información")
        
        # Roles específicos por diagnóstico
        diagnostico = perfil.get("diagnostico_formal", "ninguno")
        if "altas_capacidades" in diagnostico:
            roles.append("mentor_académico")
        
        return roles  # Devolver todos los roles identificados
    
    def _obtener_diagnostico_legible(self, diagnostico_formal: str) -> str:
        """
        Convierte el diagnóstico formal en texto legible
        
        Args:
            diagnostico_formal: Diagnóstico formal
            
        Returns:
            Diagnóstico en formato legible
        """
        if diagnostico_formal == "TEA_nivel_1":
            return "TEA Nivel 1 (requiere apoyo)"
        elif diagnostico_formal == "TEA_nivel_2":
            return "TEA Nivel 2 (requiere apoyo sustancial)"
        elif diagnostico_formal == "TEA_nivel_3":
            return "TEA Nivel 3 (requiere apoyo muy sustancial)"
        elif diagnostico_formal == "TDAH":
            return "Trastorno por Déficit de Atención e Hiperactividad"
        elif diagnostico_formal == "altas_capacidades":
            return "Altas Capacidades Intelectuales"
        elif diagnostico_formal == "dislexia":
            return "Dislexia"
        elif diagnostico_formal == "discalculia":
            return "Discalculia"
        elif diagnostico_formal == "ninguno":
            return "Sin diagnóstico específico"
        else:
            return diagnostico_formal.replace("_", " ").title()
    
    # ===== IMPLEMENTACIÓN DE MÉTODOS ABSTRACTOS =====
    
    def process(self, datos_entrada: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal de procesamiento del perfilador
        
        Args:
            datos_entrada: Diccionario con datos de entrada (pueden incluir 'tareas', etc.)
            
        Returns:
            Diccionario con análisis de estudiantes y perfiles
        """
        self._log_processing_start("análisis de perfiles de estudiantes")
        
        try:
            # Procesar los perfiles existentes
            resultado = {
                'estudiantes': {},
                'estadisticas': {
                    'total_estudiantes': len(self.perfiles_base),
                    'con_diagnostico': 0,
                    'sin_diagnostico': 0,
                    'estilos_aprendizaje': {}
                },
                'metadatos': {
                    'agente': 'AgentePerfiladorEstudiantes',
                    'version': '1.0',
                    'timestamp': self._get_timestamp()
                }
            }
            
            # Procesar cada estudiante
            for estudiante in self.perfiles_base:
                perfil_procesado = {
                    'id': estudiante.id,
                    'nombre': estudiante.nombre,
                    'fortalezas': estudiante.fortalezas,
                    'necesidades_apoyo': estudiante.necesidades_apoyo,
                    'disponibilidad': estudiante.disponibilidad,
                    'historial_roles': estudiante.historial_roles,
                    'adaptaciones': estudiante.adaptaciones
                }
                
                resultado['estudiantes'][estudiante.id] = perfil_procesado
                
                # Actualizar estadísticas
                if estudiante.adaptaciones:
                    resultado['estadisticas']['con_diagnostico'] += 1
                else:
                    resultado['estadisticas']['sin_diagnostico'] += 1
            
            self._log_processing_end(f"{len(resultado['estudiantes'])} perfiles procesados")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Error en proceso de perfilado: {e}")
            return {
                'estudiantes': {},
                'error': str(e),
                'metadatos': {
                    'agente': 'AgentePerfiladorEstudiantes',
                    'version': '1.0',
                    'timestamp': self._get_timestamp()
                }
            }
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """
        Parsea respuesta del LLM para perfilado
        
        Args:
            response: Respuesta cruda del LLM
            
        Returns:
            Diccionario con datos estructurados o None si falla el parseo
        """
        if not response or not response.strip():
            return None
            
        try:
            # Intentar parsear como JSON
            parsed = self._parse_json_response(response)
            if parsed:
                return parsed
                
            # Si no es JSON, extraer información estructurada
            resultado = {
                'perfil': {
                    'fortalezas': self._extraer_lista(response, 'fortalezas'),
                    'debilidades': self._extraer_lista(response, 'debilidades'),
                    'estilo_aprendizaje': self._extraer_campo(response, 'estilo'),
                    'nivel_apoyo': self._extraer_campo(response, 'apoyo'),
                    'adaptaciones': self._extraer_lista(response, 'adaptaciones')
                }
            }
            
            return resultado if any(resultado['perfil'].values()) else None
            
        except Exception as e:
            self.logger.error(f"❌ Error parseando respuesta de perfilado: {e}")
            return None
    
    def _get_timestamp(self) -> str:
        """
        Obtiene timestamp actual
        
        Returns:
            Timestamp en formato ISO
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def analizar_perfiles(self, datos_entrada: Dict[str, Any] = None, contexto_hibrido=None, **kwargs) -> Dict[str, Any]:
        """
        Método específico para análisis de perfiles (usado por comunicador)
        
        Args:
            datos_entrada: Datos de entrada con tareas y contexto (opcional)
            contexto_hibrido: Contexto híbrido compartido (opcional)
            **kwargs: Argumentos adicionales como contexto_global, timestamp, etc.
            
        Returns:
            Resultados del análisis de perfiles
        """
        # Usar información del contexto híbrido si está disponible
        if contexto_hibrido:
            contexto_hibrido.registrar_decision("AgentePerfilador", "Iniciando análisis de perfiles con contexto híbrido", {
                'perfiles_disponibles': len(self.perfiles_base),
                'metadatos_contexto': list(contexto_hibrido.metadatos.keys())
            })
            self.logger.info(f"🔄 Usando contexto híbrido con {len(contexto_hibrido.perfiles_estudiantes)} perfiles globales")
        
        # Combinar datos de entrada con kwargs
        if datos_entrada is None:
            datos_entrada = {}
        
        # Añadir contexto híbrido a datos si está disponible
        if contexto_hibrido:
            datos_entrada['contexto_hibrido'] = contexto_hibrido
        
        # Añadir kwargs a datos_entrada
        datos_entrada.update(kwargs)
        
        resultado = self.process(datos_entrada)
        
        # Registrar finalización en contexto híbrido
        if contexto_hibrido:
            contexto_hibrido.registrar_decision("AgentePerfilador", "Análisis de perfiles completado", {
                'perfiles_analizados': len(self.perfiles_base),
                'resultado_keys': list(resultado.keys()) if isinstance(resultado, dict) else 'No dict'
            })
        
        return resultado
    
    def obtener_perfiles_optimizados(self, actividad_contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Método optimizado Fase 2: Retorna perfiles existentes con análisis contextual mínimo
        
        Args:
            actividad_contexto: Contexto de la actividad seleccionada (opcional)
            
        Returns:
            Perfiles optimizados sin procesamiento LLM pesado
        """
        self._log_processing_start("obtención optimizada de perfiles")
        
        try:
            # Base: usar perfiles existentes directamente
            perfiles_base = {
                'estudiantes': {},
                'estadisticas': {
                    'total_estudiantes': len(self.perfiles_base),
                    'con_diagnostico': 0,
                    'sin_diagnostico': 0,
                    'distribución_neurotipos': {},
                    'fortalezas_grupales': {},
                    'necesidades_comunes': {}
                },
                'recomendaciones_colaboracion': [],
                'contexto_actividad': actividad_contexto or {},
                'metadatos': {
                    'agente': 'AgentePerfiladorEstudiantes',
                    'metodo': 'optimizado_fase2',
                    'version': '2.0',
                    'timestamp': self._get_timestamp(),
                    'procesamiento_llm': 'minimal'
                }
            }
            
            # Procesar cada estudiante con análisis contextual mínimo
            for estudiante in self.perfiles_base:
                perfil_optimizado = self._generar_perfil_optimizado(estudiante, actividad_contexto)
                perfiles_base['estudiantes'][estudiante.id] = perfil_optimizado
                
                # Actualizar estadísticas
                if perfil_optimizado['adaptaciones']:
                    perfiles_base['estadisticas']['con_diagnostico'] += 1
                    
                    # Contar neurotipos
                    for adaptacion in perfil_optimizado['adaptaciones']:
                        neurotipo = self._detectar_neurotipo(adaptacion)
                        if neurotipo:
                            perfiles_base['estadisticas']['distribución_neurotipos'][neurotipo] = \
                                perfiles_base['estadisticas']['distribución_neurotipos'].get(neurotipo, 0) + 1
                else:
                    perfiles_base['estadisticas']['sin_diagnostico'] += 1
                
                # Acumular fortalezas grupales
                for fortaleza in perfil_optimizado['fortalezas']:
                    perfiles_base['estadisticas']['fortalezas_grupales'][fortaleza] = \
                        perfiles_base['estadisticas']['fortalezas_grupales'].get(fortaleza, 0) + 1
                
                # Acumular necesidades comunes
                for necesidad in perfil_optimizado['necesidades_apoyo']:
                    perfiles_base['estadisticas']['necesidades_comunes'][necesidad] = \
                        perfiles_base['estadisticas']['necesidades_comunes'].get(necesidad, 0) + 1
            
            # Generar recomendaciones de colaboración basadas en estadísticas (sin LLM)
            perfiles_base['recomendaciones_colaboracion'] = self._generar_recomendaciones_colaboracion(
                perfiles_base['estadisticas']
            )
            
            self._log_processing_end(f"{len(perfiles_base['estudiantes'])} perfiles optimizados")
            
            return perfiles_base
            
        except Exception as e:
            self.logger.error(f"❌ Error en perfiles optimizados: {e}")
            return {
                'estudiantes': {},
                'error': str(e),
                'metadatos': {
                    'agente': 'AgentePerfiladorEstudiantes',
                    'metodo': 'optimizado_fase2_error',
                    'timestamp': self._get_timestamp()
                }
            }
    
    def _generar_perfil_optimizado(self, estudiante, actividad_contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera perfil optimizado con análisis contextual mínimo (sin LLM)
        
        Args:
            estudiante: Objeto Estudiante base
            actividad_contexto: Contexto de la actividad
            
        Returns:
            Perfil optimizado con recomendaciones contextuales
        """
        perfil_base = {
            'id': estudiante.id,
            'nombre': estudiante.nombre,
            'fortalezas': estudiante.fortalezas.copy(),
            'necesidades_apoyo': estudiante.necesidades_apoyo.copy(),
            'adaptaciones': estudiante.adaptaciones.copy(),
            'disponibilidad': estudiante.disponibilidad,
            'historial_roles': estudiante.historial_roles.copy(),
            'recomendaciones_contextuales': []
        }
        
        # Análisis contextual rápido (sin LLM)
        if actividad_contexto:
            actividad_data = actividad_contexto.get('actividad', {})
            
            # Recomendar roles basados en actividad
            titulo_actividad = actividad_data.get('titulo', '').lower()
            objetivo_actividad = actividad_data.get('objetivo', '').lower()
            
            # Mapeo rápido de fortalezas a roles contextuales
            if 'matemáticas' in estudiante.fortalezas or 'operaciones_matemáticas' in estudiante.fortalezas:
                if 'matemática' in titulo_actividad or 'números' in objetivo_actividad:
                    perfil_base['recomendaciones_contextuales'].append('coordinador_matematico')
                    
            if 'comunicación_escrita' in estudiante.fortalezas:
                if 'grupo' in objetivo_actividad or 'presenta' in objetivo_actividad:
                    perfil_base['recomendaciones_contextuales'].append('portavoz_grupo')
                    
            if 'experimentación' in estudiante.fortalezas:
                if 'experimento' in objetivo_actividad or 'investiga' in objetivo_actividad:
                    perfil_base['recomendaciones_contextuales'].append('investigador_principal')
                    
            if 'colaboración' in estudiante.fortalezas:
                perfil_base['recomendaciones_contextuales'].append('facilitador_colaboracion')
            
            # Ajustes por necesidades especiales en contexto
            for adaptacion in estudiante.adaptaciones:
                if 'TEA' in adaptacion:
                    perfil_base['recomendaciones_contextuales'].append('rol_estructurado')
                elif 'TDAH' in adaptacion:
                    if 'movimiento' in objetivo_actividad or 'manipul' in objetivo_actividad:
                        perfil_base['recomendaciones_contextuales'].append('rol_dinamico_movimiento')
                elif 'altas capacidades' in adaptacion.lower():
                    perfil_base['recomendaciones_contextuales'].append('rol_liderazgo_intelectual')
        
        return perfil_base
    
    def _detectar_neurotipo(self, adaptacion: str) -> str:
        """
        Detecta neurotipo de una adaptación (método rápido sin LLM)
        
        Args:
            adaptacion: String con adaptación
            
        Returns:
            Neurotipo detectado o None
        """
        adaptacion_lower = adaptacion.lower()
        
        if 'tea' in adaptacion_lower or 'autismo' in adaptacion_lower:
            return 'TEA'
        elif 'tdah' in adaptacion_lower or 'hiperactividad' in adaptacion_lower:
            return 'TDAH'
        elif 'altas capacidades' in adaptacion_lower or 'superdotacion' in adaptacion_lower:
            return 'Altas Capacidades'
        elif 'dislexia' in adaptacion_lower:
            return 'Dislexia'
        elif 'discalculia' in adaptacion_lower:
            return 'Discalculia'
        
        return None
    
    def _generar_recomendaciones_colaboracion(self, estadisticas: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones de colaboración basadas en estadísticas (sin LLM)
        
        Args:
            estadisticas: Estadísticas del grupo
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        total_estudiantes = estadisticas['total_estudiantes']
        con_diagnostico = estadisticas['con_diagnostico']
        neurotipos = estadisticas['distribución_neurotipos']
        fortalezas = estadisticas['fortalezas_grupales']
        
        # Recomendaciones basadas en diversidad
        if con_diagnostico > 0:
            porcentaje_diversidad = (con_diagnostico / total_estudiantes) * 100
            if porcentaje_diversidad > 50:
                recomendaciones.append("Grupo con alta neurodiversidad: fomentar roles complementarios")
            elif porcentaje_diversidad > 25:
                recomendaciones.append("Grupo con diversidad moderada: aprovechar fortalezas únicas")
        
        # Recomendaciones por neurotipos específicos
        if 'TEA' in neurotipos:
            recomendaciones.append("Presencia TEA: proporcionar estructura clara y rutinas predecibles")
        if 'TDAH' in neurotipos:
            recomendaciones.append("Presencia TDAH: incorporar movimiento y tareas fragmentadas")
        if 'Altas Capacidades' in neurotipos:
            recomendaciones.append("Altas capacidades: ofrecer desafíos adicionales y rol de mentoría")
        
        # Recomendaciones por fortalezas grupales
        fortalezas_ordenadas = sorted(fortalezas.items(), key=lambda x: x[1], reverse=True)
        if fortalezas_ordenadas:
            fortaleza_principal = fortalezas_ordenadas[0][0]
            if fortaleza_principal == 'matemáticas_números':
                recomendaciones.append("Fortaleza grupal matemática: asignar roles de cálculo y verificación")
            elif fortaleza_principal == 'comunicación_escrita':
                recomendaciones.append("Fortaleza comunicativa: asignar roles de documentación y presentación")
            elif fortaleza_principal == 'experimentación':
                recomendaciones.append("Fortaleza experimental: asignar roles de investigación práctica")
        
        # Recomendación de tamaño de grupos
        if total_estudiantes <= 4:
            recomendaciones.append("Grupo pequeño: trabajo individual con apoyo mutuo")
        elif total_estudiantes <= 8:
            recomendaciones.append("Grupo medio: formar 2-3 equipos colaborativos")
        else:
            recomendaciones.append("Grupo grande: formar múltiples equipos con rotación de roles")
        
        return recomendaciones[:5]  # Máximo 5 recomendaciones
    
    def _inferir_neurotipo_desde_perfil(self, perfil) -> str:
        """
        Infiere el neurotipo desde las adaptaciones y necesidades de apoyo del perfil
        
        Args:
            perfil: Objeto Estudiante
            
        Returns:
            Neurotipo inferido
        """
        adaptaciones_str = ' '.join(perfil.adaptaciones).lower()
        necesidades_str = ' '.join(perfil.necesidades_apoyo).lower()
        texto_completo = f"{adaptaciones_str} {necesidades_str}"
        
        if any(term in texto_completo for term in ['tea', 'autismo', 'estructuración', 'predictibilidad', 'rutinas_estructuradas']):
            return 'TEA'
        elif any(term in texto_completo for term in ['tdah', 'hiperactividad', 'movimiento', 'descansos_frecuentes']):
            return 'TDAH'
        elif any(term in texto_completo for term in ['altas capacidades', 'enriquecimiento', 'desafíos', 'retos_adicionales', 'superdotacion']):
            return 'altas_capacidades'
        elif any(term in texto_completo for term in ['dislexia']):
            return 'dislexia'
        elif any(term in texto_completo for term in ['discalculia']):
            return 'discalculia'
        else:
            return 'típico'
    
    # =================== MÉTODOS DE DEBATE ENTRE AGENTES ===================
    
    def evaluar_propuesta_debate(self, propuesta: Dict, contexto: Dict = None, contexto_perfiles: List = None) -> Dict:
        """
        Evalúa una propuesta desde perspectiva pedagógica y de perfil de estudiantes
        
        Args:
            propuesta: Propuesta del analizador para evaluar
            contexto_perfiles: Lista de perfiles de estudiantes (opcional, usa self.perfiles_base si no se proporciona)
            
        Returns:
            Evaluación pedagógica de la propuesta
        """
        self.logger.info(f"👥 Perfilador evaluando propuesta pedagógica")
        
        # Usar perfiles proporcionados o los propios
        perfiles_a_usar = contexto_perfiles if contexto_perfiles is not None else self.perfiles_base
        
        # Analizar compatibilidad con perfiles existentes
        compatibilidad = self._evaluar_compatibilidad_perfiles_debate(propuesta, perfiles_a_usar)
        
        # Evaluar adaptaciones necesarias para neurotipos
        adaptaciones = self._evaluar_adaptaciones_neurotipos_debate(propuesta, perfiles_a_usar)
        
        # Evaluar viabilidad grupal
        viabilidad_grupal = self._evaluar_viabilidad_grupal_debate(propuesta, perfiles_a_usar)
        
        evaluacion = {
            'compatibilidad_perfiles': compatibilidad,
            'adaptaciones_requeridas': adaptaciones,
            'viabilidad_grupal': viabilidad_grupal,
            'recomendaciones_pedagogicas': self._generar_recomendaciones_pedagogicas(propuesta, compatibilidad),
            'conflictos_detectados': self._detectar_conflictos_pedagogicos_debate(propuesta, perfiles_a_usar),
            'aprobacion_pedagogica': self._calcular_aprobacion_general(compatibilidad, adaptaciones, viabilidad_grupal)
        }
        
        return evaluacion
    
    def _evaluar_compatibilidad_perfiles_debate(self, propuesta: Dict, perfiles_a_usar: List) -> Dict:
        """Evalúa compatibilidad de la propuesta con perfiles de estudiantes para debate"""
        if not perfiles_a_usar:
            return {'puntuacion': 0.5, 'comentario': 'Sin perfiles para evaluar'}
        
        tipo_propuesto = propuesta.get('tipo_propuesto', 'desconocido')
        estructura = propuesta.get('estructura_sugerida', {})
        organizacion = estructura.get('organizacion', 'colaborativa')
        
        # Evaluar según neurotipos presentes
        puntuaciones = []
        comentarios = []
        
        for perfil in perfiles_a_usar:
            neurotipo = self._inferir_neurotipo_desde_perfil(perfil)
            
            if neurotipo == 'TEA':
                if organizacion in ['individual_con_apoyo', 'estructura_clara']:
                    puntuaciones.append(0.8)
                    comentarios.append(f"{perfil.nombre}: Compatible con TEA (estructura clara)")
                else:
                    puntuaciones.append(0.4)
                    comentarios.append(f"{perfil.nombre}: Requiere adaptación para TEA")
            
            elif neurotipo == 'TDAH':
                if 'rotacion' in str(propuesta) or 'dinamico' in str(propuesta):
                    puntuaciones.append(0.9)
                    comentarios.append(f"{perfil.nombre}: Excelente para TDAH (dinamismo)")
                else:
                    puntuaciones.append(0.6)
                    comentarios.append(f"{perfil.nombre}: Necesita más dinamismo para TDAH")
            
            elif neurotipo == 'altas_capacidades':
                complejidad = propuesta.get('estructura_sugerida', {}).get('complejidad', 'media')
                if complejidad in ['alta', 'media-alta']:
                    puntuaciones.append(0.9)
                    comentarios.append(f"{perfil.nombre}: Apropiado para altas capacidades")
                else:
                    puntuaciones.append(0.5)
                    comentarios.append(f"{perfil.nombre}: Puede requerir complejidad adicional")
            
            else:  # típico
                puntuaciones.append(0.7)
                comentarios.append(f"{perfil.nombre}: Compatible (perfil típico)")
        
        return {
            'puntuacion_media': sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0.5,
            'detalles_perfiles': comentarios,
            'neurotipos_detectados': [self._inferir_neurotipo_desde_perfil(p) for p in perfiles_a_usar]
        }
    
    def _evaluar_adaptaciones_neurotipos_debate(self, propuesta: Dict, perfiles_a_usar: List) -> Dict:
        """Evalúa qué adaptaciones específicas se necesitan para debate"""
        adaptaciones = {
            'TEA': [],
            'TDAH': [],
            'altas_capacidades': [],
            'generales': []
        }
        
        tipo_actividad = propuesta.get('tipo_propuesto', '')
        estructura = propuesta.get('estructura_sugerida', {})
        
        # Adaptaciones para TEA
        if any(self._inferir_neurotipo_desde_perfil(p) == 'TEA' for p in perfiles_a_usar):
            adaptaciones['TEA'].extend([
                'Proporcionar rutina clara y predecible',
                'Materiales con apoyo visual',
                'Tiempo extra para procesamiento',
                'Ambiente menos estimulante'
            ])
        
        # Adaptaciones para TDAH
        if any(self._inferir_neurotipo_desde_perfil(p) == 'TDAH' for p in perfiles_a_usar):
            adaptaciones['TDAH'].extend([
                'Permitir movimiento durante la actividad',
                'Cambios frecuentes de estación/actividad',
                'Tareas más cortas y variadas',
                'Elementos manipulativos'
            ])
        
        # Adaptaciones para altas capacidades
        if any(self._inferir_neurotipo_desde_perfil(p) == 'altas_capacidades' for p in perfiles_a_usar):
            adaptaciones['altas_capacidades'].extend([
                'Retos adicionales opcionales',
                'Rol de mentorización de compañeros',
                'Investigación extendida',
                'Proyectos de mayor complejidad'
            ])
        
        return adaptaciones
    
    def _evaluar_viabilidad_grupal_debate(self, propuesta: Dict, perfiles_a_usar: List) -> Dict:
        """Evalúa si la propuesta funciona con el grupo específico para debate"""
        estructura = propuesta.get('estructura_sugerida', {})
        organizacion = estructura.get('organizacion', 'colaborativa')
        
        total_estudiantes = len(perfiles_a_usar) if perfiles_a_usar else 8
        
        viabilidad = {
            'tamaño_optimo': True,
            'diversidad_neurotipos': True,
            'recursos_necesarios': 'standar',
            'tiempo_sugerido': estructura.get('duracion_sugerida', '45-60 minutos')
        }
        
        # Evaluar tamaño para organización propuesta
        if organizacion == 'parejas_rotativas' and total_estudiantes % 2 != 0:
            viabilidad['tamaño_optimo'] = False
            viabilidad['observacion_tamaño'] = 'Número impar - necesario ajuste para parejas'
        
        return viabilidad
    
    def _detectar_conflictos_pedagogicos_debate(self, propuesta: Dict, perfiles_a_usar: List) -> List[str]:
        """Detecta posibles conflictos pedagógicos en la propuesta para debate"""
        conflictos = []
        
        tipo_actividad = propuesta.get('tipo_propuesto', '')
        estructura = propuesta.get('estructura_sugerida', {})
        
        # Detectar conflictos potenciales
        if tipo_actividad == 'gymnkana':
            if any(self._inferir_neurotipo_desde_perfil(p) == 'TEA' for p in perfiles_a_usar):
                conflictos.append("⚠️ Gymnkana puede ser estimulante en exceso para estudiantes TEA")
        
        duracion = estructura.get('duracion_sugerida', '')
        if '90' in duracion or '2-3 sesiones' in duracion:
            if any(self._inferir_neurotipo_desde_perfil(p) == 'TDAH' for p in perfiles_a_usar):
                conflictos.append("⚠️ Duración extensa puede ser desafiante para TDAH")
        
        return conflictos
    
    def _evaluar_compatibilidad_perfiles(self, propuesta: Dict) -> Dict:
        """Evalúa compatibilidad de la propuesta con perfiles de estudiantes"""
        if not self.perfiles_base:
            return {'puntuacion': 0.5, 'comentario': 'Sin perfiles para evaluar'}
        
        tipo_propuesto = propuesta.get('tipo_propuesto', 'desconocido')
        estructura = propuesta.get('estructura_sugerida', {})
        organizacion = estructura.get('organizacion', 'colaborativa')
        
        # Evaluar según neurotipos presentes
        puntuaciones = []
        comentarios = []
        
        for perfil in self.perfiles_base:
            neurotipo = self._inferir_neurotipo_desde_perfil(perfil)
            
            if neurotipo == 'TEA':
                if organizacion in ['individual_con_apoyo', 'estructura_clara']:
                    puntuaciones.append(0.8)
                    comentarios.append(f"{perfil.nombre}: Compatible con TEA (estructura clara)")
                else:
                    puntuaciones.append(0.4)
                    comentarios.append(f"{perfil.nombre}: Requiere adaptación para TEA")
            
            elif neurotipo == 'TDAH':
                if 'rotacion' in str(propuesta) or 'dinamico' in str(propuesta):
                    puntuaciones.append(0.9)
                    comentarios.append(f"{perfil.nombre}: Excelente para TDAH (dinamismo)")
                else:
                    puntuaciones.append(0.6)
                    comentarios.append(f"{perfil.nombre}: Necesita más dinamismo para TDAH")
            
            elif neurotipo == 'altas_capacidades':
                complejidad = propuesta.get('estructura_sugerida', {}).get('complejidad', 'media')
                if complejidad in ['alta', 'media-alta']:
                    puntuaciones.append(0.9)
                    comentarios.append(f"{perfil.nombre}: Apropiado para altas capacidades")
                else:
                    puntuaciones.append(0.5)
                    comentarios.append(f"{perfil.nombre}: Puede requerir complejidad adicional")
            
            else:  # típico
                puntuaciones.append(0.7)
                comentarios.append(f"{perfil.nombre}: Compatible (perfil típico)")
        
        return {
            'puntuacion_media': sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0.5,
            'detalles_perfiles': comentarios,
            'neurotipos_detectados': [self._inferir_neurotipo_desde_perfil(p) for p in self.perfiles_base]
        }
    
    def _evaluar_adaptaciones_neurotipos(self, propuesta: Dict) -> Dict:
        """Evalúa qué adaptaciones específicas se necesitan"""
        adaptaciones = {
            'TEA': [],
            'TDAH': [],
            'altas_capacidades': [],
            'generales': []
        }
        
        tipo_actividad = propuesta.get('tipo_propuesto', '')
        estructura = propuesta.get('estructura_sugerida', {})
        
        # Adaptaciones para TEA
        if any(self._inferir_neurotipo_desde_perfil(p) == 'TEA' for p in self.perfiles_base):
            adaptaciones['TEA'].extend([
                'Proporcionar rutina clara y predecible',
                'Materiales con apoyo visual',
                'Tiempo extra para procesamiento',
                'Ambiente menos estimulante'
            ])
        
        # Adaptaciones para TDAH
        if any(self._inferir_neurotipo_desde_perfil(p) == 'TDAH' for p in self.perfiles_base):
            adaptaciones['TDAH'].extend([
                'Permitir movimiento durante la actividad',
                'Cambios frecuentes de estación/actividad',
                'Tareas más cortas y variadas',
                'Elementos manipulativos'
            ])
        
        # Adaptaciones para altas capacidades
        if any(self._inferir_neurotipo_desde_perfil(p) == 'altas_capacidades' for p in self.perfiles_base):
            adaptaciones['altas_capacidades'].extend([
                'Retos adicionales opcionales',
                'Rol de mentorización de compañeros',
                'Investigación extendida',
                'Proyectos de mayor complejidad'
            ])
        
        return adaptaciones
    
    def _evaluar_viabilidad_grupal(self, propuesta: Dict) -> Dict:
        """Evalúa si la propuesta funciona con el grupo específico"""
        estructura = propuesta.get('estructura_sugerida', {})
        organizacion = estructura.get('organizacion', 'colaborativa')
        
        total_estudiantes = len(self.perfiles_base) if self.perfiles_base else 8
        
        viabilidad = {
            'tamaño_optimo': True,
            'diversidad_neurotipos': True,
            'recursos_necesarios': 'standar',
            'tiempo_sugerido': estructura.get('duracion_sugerida', '45-60 minutos')
        }
        
        # Evaluar tamaño para organización propuesta
        if organizacion == 'parejas_rotativas' and total_estudiantes % 2 != 0:
            viabilidad['tamaño_optimo'] = False
            viabilidad['observacion_tamaño'] = 'Número impar - necesario ajuste para parejas'
        
        return viabilidad
    
    def _generar_recomendaciones_pedagogicas(self, propuesta: Dict, compatibilidad: Dict) -> List[str]:
        """Genera recomendaciones pedagógicas específicas"""
        recomendaciones = []
        
        puntuacion = compatibilidad.get('puntuacion_media', 0.5)
        
        if puntuacion < 0.6:
            recomendaciones.append("⚠️ Propuesta requiere adaptaciones significativas")
            recomendaciones.append("Considerar modificar la estructura para mayor inclusión")
        
        if puntuacion > 0.8:
            recomendaciones.append("✅ Propuesta muy compatible con el grupo")
            recomendaciones.append("Puede implementarse con adaptaciones mínimas")
        
        # Agregar recomendaciones específicas por neurotipos
        neurotipos = compatibilidad.get('neurotipos_detectados', [])
        if 'TEA' in neurotipos:
            recomendaciones.append("📋 Incluir rutinas claras y material visual de apoyo")
        
        if 'TDAH' in neurotipos:
            recomendaciones.append("🏃 Incorporar elementos de movimiento y variación")
        
        if 'altas_capacidades' in neurotipos:
            recomendaciones.append("🎯 Preparar desafíos adicionales opcionales")
        
        return recomendaciones
    
    def _detectar_conflictos_pedagogicos(self, propuesta: Dict) -> List[str]:
        """Detecta posibles conflictos pedagógicos en la propuesta"""
        conflictos = []
        
        tipo_actividad = propuesta.get('tipo_propuesto', '')
        estructura = propuesta.get('estructura_sugerida', {})
        
        # Detectar conflictos potenciales
        if tipo_actividad == 'gymnkana':
            if any(self._inferir_neurotipo_desde_perfil(p) == 'TEA' for p in self.perfiles_base):
                conflictos.append("⚠️ Gymnkana puede ser estimulante en exceso para estudiantes TEA")
        
        duracion = estructura.get('duracion_sugerida', '')
        if '90' in duracion or '2-3 sesiones' in duracion:
            if any(self._inferir_neurotipo_desde_perfil(p) == 'TDAH' for p in self.perfiles_base):
                conflictos.append("⚠️ Duración extensa puede ser desafiante para TDAH")
        
        return conflictos
    
    def _calcular_aprobacion_general(self, compatibilidad: Dict, adaptaciones: Dict, viabilidad: Dict) -> Dict:
        """Calcula aprobación general de la propuesta"""
        puntuacion_compatibilidad = compatibilidad.get('puntuacion_media', 0.5)
        
        # Factores de ajuste
        factor_viabilidad = 1.0 if viabilidad.get('tamaño_optimo', True) else 0.8
        factor_adaptaciones = 0.9 if any(adaptaciones.values()) else 1.0
        
        puntuacion_final = puntuacion_compatibilidad * factor_viabilidad * factor_adaptaciones
        
        if puntuacion_final >= 0.8:
            estado = 'APROBADO'
            mensaje = 'Propuesta aprobada con alta compatibilidad pedagógica'
        elif puntuacion_final >= 0.6:
            estado = 'APROBADO_CON_ADAPTACIONES'
            mensaje = 'Propuesta viable con adaptaciones recomendadas'
        else:
            estado = 'REQUIERE_REVISION'
            mensaje = 'Propuesta necesita modificaciones significativas'
        
        return {
            'estado': estado,
            'puntuacion': puntuacion_final,
            'mensaje': mensaje,
            'rechazo': estado == 'REQUIERE_REVISION'
        }