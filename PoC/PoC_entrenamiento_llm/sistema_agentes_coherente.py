#!/usr/bin/env python3
"""
Sistema de Agentes Coherente con Human-in-the-Loop Natural
Basado en patrones k_ exitosos, sin pseudociencia cuántica
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AgentesCoherente")

@dataclass
class ActividadEducativa:
    id: str
    titulo: str
    materia: str
    tema: str
    contenido: str
    tareas_estudiantes: Dict[str, str]
    materiales: List[str]
    duracion: str
    fases: List[str]
    validacion: Dict
    timestamp: str

class CargadorEjemplosK:
    """Carga y analiza ejemplos k_ reales para extraer patrones"""
    
    def __init__(self, directorio_ejemplos: str = "."):
        self.directorio = directorio_ejemplos
        self.ejemplos_k = {}
        self.patrones_extraidos = {}
        self._cargar_ejemplos()
    
    def _cargar_ejemplos(self):
        """Carga ejemplos k_ desde archivos reales"""
        archivos_k = [
            "actividades_generadas/k_celula.txt",
            "actividades_generadas/k_feria_acertijos.txt", 
            "actividades_generadas/k_sonnet_supermercado.txt",
            "actividades_generadas/k_piratas.txt"
        ]
        
        for archivo in archivos_k:
            ruta_completa = os.path.join(self.directorio, archivo)
            if os.path.exists(ruta_completa):
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        nombre_ejemplo = os.path.basename(archivo).replace('.txt', '')
                        self.ejemplos_k[nombre_ejemplo] = contenido
                        logger.info(f"✅ Cargado ejemplo: {nombre_ejemplo}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {archivo}: {e}")
        
        if not self.ejemplos_k:
            logger.warning("⚠️ No se encontraron ejemplos k_. Usando ejemplos básicos.")
            self._crear_ejemplos_basicos()
        
        self._extraer_patrones()
    
    def _crear_ejemplos_basicos(self):
        """Ejemplos básicos si no se encuentran archivos k_"""
        self.ejemplos_k = {
            "k_basico_matematicas": """
Actividad: Medición con Objetos Reales
- Alex: Medir 3 objetos con regla y anotar medidas
- Elena: Organizar materiales por tamaños usando criterio visual
- Luis: Construir torre con bloques y contar cuántos usó
- Ana: Comparar medidas de Alex y proponer mejoras
- Sara: Documentar proceso completo en tabla
- Hugo: Verificar que todos tengan materiales necesarios
Interdependencia: Sara necesita datos de Alex, Ana verifica trabajo de Alex, Hugo distribuye para que todos puedan trabajar.
            """,
            "k_basico_ciencias": """
Actividad: Exploración de Materiales
- Alex: Clasificar 10 objetos por texturas y documentar
- Elena: Crear etiquetas visuales para cada categoría  
- Luis: Tocar y describir 5 objetos diferentes
- Ana: Explicar por qué ciertos materiales van juntos
- Sara: Escuchar explicaciones y hacer preguntas
- Hugo: Organizar espacio de trabajo con materiales
Interdependencia: Elena usa clasificación de Alex, Ana explica a Sara, Hugo facilita trabajo de todos.
            """
        }
    
    def _extraer_patrones(self):
        """Extrae patrones de coherencia de ejemplos k_"""
        for nombre, contenido in self.ejemplos_k.items():
            self.patrones_extraidos[nombre] = {
                "tiene_roles_especificos": bool(re.search(r'(Alex|Elena|Luis|Ana|Sara|Hugo):', contenido)),
                "tiene_interdependencia": bool(re.search(r'(necesita|depende|verifica|usa.*de)', contenido, re.IGNORECASE)),
                "tiene_materiales_fisicos": bool(re.search(r'(regla|bloques|papel|objetos|materiales)', contenido, re.IGNORECASE)),
                "tiene_secuencia_temporal": bool(re.search(r'(primero|luego|después|al final)', contenido, re.IGNORECASE)),
                "evita_roles_abstractos": not bool(re.search(r'(investigador|diseñador|coordinador)', contenido, re.IGNORECASE))
            }
    
    def seleccionar_ejemplo_para_materia(self, materia: str, tema: str = "") -> str:
        """Selecciona ejemplo k_ más adecuado para la materia"""
        if materia.lower() in ["matematicas", "mates", "math"]:
            if "k_feria_acertijos" in self.ejemplos_k:
                return self.ejemplos_k["k_feria_acertijos"]
            return self.ejemplos_k.get("k_basico_matematicas", "")
        
        elif materia.lower() in ["ciencias", "naturales", "ciencia"]:
            if "k_celula" in self.ejemplos_k:
                return self.ejemplos_k["k_celula"]
            return self.ejemplos_k.get("k_basico_ciencias", "")
        
        # Fallback al primer ejemplo disponible
        return list(self.ejemplos_k.values())[0] if self.ejemplos_k else ""

class AnalizadorIntenciones:
    """Analiza prompts libres del usuario según el flujo de 4 pasos"""
    
    def __init__(self):
        # Patrones para cada fase del flujo
        self.patrones_clima = {
            "simple": [
                r"simple", r"básico", r"sin.*historia", r"tareas.*concretas", 
                r"directo", r"rápido", r"sencillo"
            ],
            "juego": [
                r"juego", r"lúdico", r"divertido", r"competencia", 
                r"puntos", r"reglas", r"ganador"
            ],
            "narrativa": [
                r"historia", r"cuento", r"aventura", r"personajes", 
                r"narrativa", r"contexto", r"situación"
            ],
            "complejo": [
                r"complejo", r"elaborado", r"proyecto", r"varias.*sesiones",
                r"multi.*parte", r"profundo", r"investigación"
            ]
        }
        
        self.patrones_estructuracion = {
            "materiales": [
                r"sin.*(bloques|pinturas|reglas)", r"solo.*papel", r"no.*tengo.*(\w+)",
                r"materiales.*disponibles.*(\w+)"
            ],
            "duracion": [
                r"(\d+).*minutos", r"más.*corto", r"una.*hora", r"media.*mañana"
            ],
            "enfoque": [
                r"más.*manipulativo", r"menos.*teoría", r"tocar.*objetos",
                r"visual", r"auditivo", r"kinestésico"
            ],
            "modalidad_trabajo": [
                r"individual", r"por.*grupos", r"en.*equipos", r"colaborativo",
                r"cada.*uno.*solo", r"trabajo.*grupal", r"parejas"
            ]
        }
        
        self.patrones_tareas = {
            "modificar_tarea": [
                r"esta.*tarea.*(\w+)", r"cambiar.*(\w+).*por.*(\w+)",
                r"quitar.*(\w+)", r"añadir.*(\w+)"
            ],
            "adaptacion_especifica": [
                r"más.*kinestésico", r"apoyo.*visual", r"menos.*texto",
                r"estructura.*clara", r"paso.*a.*paso"
            ]
        }
        
        self.patrones_reparto = {
            "estudiante_especifico": [
                r"Elena.*necesita", r"Luis.*problema", r"Ana.*muy.*fácil",
                r"para.*(\w+).*(\w+)"
            ],
            "equilibrio": [
                r"menos.*carga", r"más.*ayuda", r"puede.*ayudar",
                r"redistribuir", r"equilibrar"
            ]
        }
    
    def analizar_fase_clima(self, prompt: str) -> str:
        """Detecta qué tipo de clima/complejidad quiere el usuario"""
        prompt_lower = prompt.lower()
        
        for clima, patrones in self.patrones_clima.items():
            if any(re.search(patron, prompt_lower) for patron in patrones):
                return clima
        
        return "simple"  # Default
    
    def analizar_fase_estructuracion(self, prompt: str) -> Dict[str, Any]:
        """Analiza modificaciones en estructuración"""
        prompt_lower = prompt.lower()
        cambios = {
            "materiales": [],
            "duracion": None,
            "enfoque": None,
            "modalidad_trabajo": None
        }
        
        # Detectar cambios en materiales
        for patron in self.patrones_estructuracion["materiales"]:
            match = re.search(patron, prompt_lower)
            if match:
                cambios["materiales"].append(match.group(1) if match.groups() else "general")
        
        # Detectar duración
        for patron in self.patrones_estructuracion["duracion"]:
            match = re.search(patron, prompt_lower)
            if match:
                cambios["duracion"] = match.group(1) if match.groups() else "ajustar"
        
        # Detectar enfoque
        for patron in self.patrones_estructuracion["enfoque"]:
            if re.search(patron, prompt_lower):
                cambios["enfoque"] = "manipulativo"
        
        # Detectar modalidad de trabajo
        for patron in self.patrones_estructuracion["modalidad_trabajo"]:
            if re.search(patron, prompt_lower):
                if any(palabra in prompt_lower for palabra in ["individual", "solo"]):
                    cambios["modalidad_trabajo"] = "individual"
                elif any(palabra in prompt_lower for palabra in ["grupos", "equipos", "colaborativo"]):
                    cambios["modalidad_trabajo"] = "grupal"
                elif "parejas" in prompt_lower:
                    cambios["modalidad_trabajo"] = "parejas"
        
        return cambios
    
    def analizar_fase_tareas(self, prompt: str) -> Dict[str, Any]:
        """Analiza modificaciones en tareas específicas"""
        prompt_lower = prompt.lower()
        cambios = {
            "modificaciones": [],
            "adaptaciones": []
        }
        
        # Detectar modificaciones de tareas
        for patron in self.patrones_tareas["modificar_tarea"]:
            match = re.search(patron, prompt_lower)
            if match:
                cambios["modificaciones"].append(match.groups() if match.groups() else [prompt_lower])
        
        # Detectar adaptaciones específicas
        for patron in self.patrones_tareas["adaptacion_especifica"]:
            if re.search(patron, prompt_lower):
                cambios["adaptaciones"].append(patron.replace(".*", " "))
        
        return cambios
    
    def analizar_fase_reparto(self, prompt: str) -> Dict[str, Any]:
        """Analiza modificaciones en reparto de estudiantes"""
        prompt_lower = prompt.lower()
        cambios = {
            "estudiantes_especificos": [],
            "equilibrio": False
        }
        
        # Detectar estudiantes específicos mencionados
        for patron in self.patrones_reparto["estudiante_especifico"]:
            match = re.search(patron, prompt_lower)
            if match:
                cambios["estudiantes_especificos"].append(match.groups() if match.groups() else [prompt_lower])
        
        # Detectar necesidad de equilibrio
        for patron in self.patrones_reparto["equilibrio"]:
            if re.search(patron, prompt_lower):
                cambios["equilibrio"] = True
        
        return cambios
    
    def detectar_fase_actual(self, prompt: str) -> str:
        """Detecta en qué fase del flujo está el usuario"""
        prompt_lower = prompt.lower()
        
        # Fase 1: Clima/Complejidad
        if any(re.search(patron, prompt_lower) for patrones in self.patrones_clima.values() for patron in patrones):
            return "clima"
        
        # Fase 4: Reparto (debe ir antes que tareas porque es más específico)
        if any(re.search(patron, prompt_lower) for patrones in self.patrones_reparto.values() for patron in patrones):
            return "reparto"
        
        # Fase 3: Tareas
        if any(re.search(patron, prompt_lower) for patrones in self.patrones_tareas.values() for patron in patrones):
            return "tareas"
        
        # Fase 2: Estructuración
        if any(re.search(patron, prompt_lower) for patrones in self.patrones_estructuracion.values() for patron in patrones):
            return "estructuracion"
        
        return "general"  # No detectado específicamente

class GeneradorActividades:
    """Genera actividades siguiendo el flujo de 4 fases con human-in-the-loop"""
    
    def __init__(self, cargador_ejemplos: CargadorEjemplosK):
        self.ejemplos = cargador_ejemplos
        self.perfiles_estudiantes = {
            "001": {"nombre": "ALEX M.", "estilo": "reflexivo, visual", "necesidades": "tareas visuales estructuradas"},
            "002": {"nombre": "MARÍA L.", "estilo": "reflexivo, auditivo", "necesidades": "explicaciones verbales"},
            "003": {"nombre": "ELENA R.", "estilo": "reflexivo, visual, TEA_nivel_1", "necesidades": "rutinas claras, apoyo visual"},
            "004": {"nombre": "LUIS T.", "estilo": "impulsivo, kinestésico, TDAH_combinado", "necesidades": "movimiento, tareas cortas"},
            "005": {"nombre": "ANA V.", "estilo": "reflexivo, auditivo, altas_capacidades", "necesidades": "desafío extra, liderazgo"},
            "006": {"nombre": "SARA M.", "estilo": "equilibrado, auditivo", "necesidades": "trabajo colaborativo"},
            "007": {"nombre": "EMMA K.", "estilo": "reflexivo, visual", "necesidades": "representación gráfica"},
            "008": {"nombre": "HUGO P.", "estilo": "equilibrado, visual", "necesidades": "organización espacial"}
        }
        
        # Plantillas por clima/complejidad
        self.plantillas_clima = {
            "simple": {
                "estructura": ["objetivo", "materiales", "tareas", "tiempo"],
                "duracion_base": 30,
                "enfoque": "tareas concretas directas"
            },
            "juego": {
                "estructura": ["reglas", "objetivo", "equipos", "puntuación", "materiales"],
                "duracion_base": 45,
                "enfoque": "competencia lúdica"
            },
            "narrativa": {
                "estructura": ["contexto", "personajes", "desarrollo", "climax", "desenlace"],
                "duracion_base": 60,
                "enfoque": "historia envolvente"
            },
            "complejo": {
                "estructura": ["investigación", "planificación", "ejecución", "presentación", "evaluación"],
                "duracion_base": 90,
                "enfoque": "proyecto multi-fase"
            }
        }
    
    # FASE 1: CLIMA/COMPLEJIDAD
    def generar_estructura_por_clima(self, materia: str, tema: str, clima: str) -> Dict[str, Any]:
        """Fase 1: Genera estructura base según clima elegido"""
        plantilla = self.plantillas_clima[clima]
        
        estructura_base = {
            "clima": clima,
            "materia": materia,
            "tema": tema,
            "duracion_base": plantilla["duracion_base"],
            "enfoque": plantilla["enfoque"],
            "elementos_estructura": plantilla["estructura"]
        }
        
        if clima == "simple":
            estructura_base.update({
                "titulo": f"Práctica Directa de {tema.title()}",
                "objetivo": f"Trabajar {tema} de forma directa y práctica",
                "materiales_base": ["objetos físicos", "papel", "lápices"],
                "formato": "tareas individuales que se conectan",
                "modalidad_trabajo": "mixta"  # Por defecto, mixta
            })
        
        elif clima == "juego":
            estructura_base.update({
                "titulo": f"Juego de {tema.title()}",
                "objetivo": f"Aprender {tema} jugando en equipos",
                "materiales_base": ["elementos de juego", "tablero", "fichas"],
                "formato": "competencia con reglas y puntuación",
                "modalidad_trabajo": "grupal"  # Juegos tienden a ser grupales
            })
        
        elif clima == "narrativa":
            estructura_base.update({
                "titulo": f"Aventura de {tema.title()}",
                "objetivo": f"Explorar {tema} a través de una aventura",
                "materiales_base": ["materiales para escenario", "disfraces", "props"],
                "formato": "historia con personajes y desarrollo",
                "modalidad_trabajo": "grupal"  # Narrativas tienden a ser colaborativas
            })
        
        elif clima == "complejo":
            estructura_base.update({
                "titulo": f"Proyecto de Investigación: {tema.title()}",
                "objetivo": f"Investigar {tema} en profundidad mediante proyecto",
                "materiales_base": ["recursos investigación", "materiales construcción"],
                "formato": "proyecto multi-sesión con fases",
                "modalidad_trabajo": "mixta"  # Proyectos suelen combinar ambas
            })
        
        return estructura_base
    
    # FASE 2: ESTRUCTURACIÓN ESPECÍFICA
    def estructurar_actividad(self, estructura_base: Dict, modificaciones: Dict = None) -> Dict[str, Any]:
        """Fase 2: Estructurar actividad específica según clima y modificaciones"""
        clima = estructura_base["clima"]
        materia = estructura_base["materia"]
        tema = estructura_base["tema"]
        
        if modificaciones:
            # Aplicar modificaciones de duración
            if modificaciones.get("duracion"):
                try:
                    nueva_duracion = int(modificaciones["duracion"])
                    estructura_base["duracion_base"] = nueva_duracion
                except:
                    pass
            
            # Aplicar modificaciones de materiales
            if modificaciones.get("materiales"):
                estructura_base["materiales_limitados"] = modificaciones["materiales"]
            
            # Aplicar enfoque específico
            if modificaciones.get("enfoque"):
                estructura_base["enfoque"] = modificaciones["enfoque"]
            
            # Aplicar modalidad de trabajo
            if modificaciones.get("modalidad_trabajo"):
                estructura_base["modalidad_trabajo"] = modificaciones["modalidad_trabajo"]
        
        # Generar actividad específica según clima
        if clima == "simple":
            return self._estructurar_simple(estructura_base)
        elif clima == "juego":
            return self._estructurar_juego(estructura_base)
        elif clima == "narrativa":
            return self._estructurar_narrativa(estructura_base)
        elif clima == "complejo":
            return self._estructurar_complejo(estructura_base)
    
    # FASE 3: DESGLOSE DE TAREAS
    def descomponer_en_tareas(self, actividad_estructurada: Dict, modificaciones_tareas: Dict = None) -> List[str]:
        """Fase 3: Descompone actividad en tareas específicas"""
        clima = actividad_estructurada["clima"]
        tema = actividad_estructurada["tema"]
        modalidad = actividad_estructurada.get("modalidad_trabajo", "mixta")
        
        if clima == "simple":
            if modalidad == "individual":
                tareas_base = [
                    f"Examinar individualmente 3 objetos relacionados con {tema}",
                    f"Medir y anotar personalmente características de {tema}",
                    f"Organizar tu espacio de trabajo con materiales de {tema}",
                    f"Experimentar solo con diferentes usos de objetos",
                    f"Escribir conclusiones individuales sobre {tema}",
                    f"Comparar tus resultados con los de un compañero",
                    f"Crear tu propia representación visual de {tema}",
                    f"Completar ficha personal de documentación"
                ]
            elif modalidad == "grupal":
                tareas_base = [
                    f"Explorar en equipo objetos relacionados con {tema}",
                    f"Medir colaborativamente características de {tema}",
                    f"Organizar materiales entre todo el grupo",
                    f"Experimentar juntos con diferentes usos",
                    f"Discutir y consensuar hallazgos grupales sobre {tema}",
                    f"Verificar resultados como equipo completo",
                    f"Crear representación visual colaborativa de {tema}",
                    f"Documentar proceso grupal conjunto"
                ]
            else:  # mixta
                tareas_base = [
                    f"Examinar objetos relacionados con {tema}",
                    f"Medir y documentar características de {tema}",
                    f"Organizar materiales por categorías",
                    f"Experimentar con diferentes usos",
                    f"Explicar hallazgos al grupo",
                    f"Verificar resultados entre todos",
                    f"Crear representación visual",
                    f"Documentar proceso completo"
                ]
        
        elif clima == "juego":
            tareas_base = [
                f"Preparar equipo y materiales de juego",
                f"Explicar reglas de {tema} a compañeros",
                f"Llevar puntuación del equipo",
                f"Ejecutar jugadas principales",
                f"Verificar cumplimiento de reglas",
                f"Ayudar a equipos que tienen dificultades",
                f"Presentar estrategias ganadoras",
                f"Evaluar qué funcionó mejor"
            ]
        
        elif clima == "narrativa":
            tareas_base = [
                f"Crear personaje relacionado con {tema}",
                f"Desarrollar escenario de la historia",
                f"Narrar parte inicial de la aventura",
                f"Representar conflicto principal",
                f"Proponer solución creativa",
                f"Coordinar actuación grupal",
                f"Crear props y vestuario",
                f"Presentar desenlace de la historia"
            ]
        
        elif clima == "complejo":
            tareas_base = [
                f"Investigar antecedentes de {tema}",
                f"Planificar fases del proyecto",
                f"Recopilar materiales necesarios",
                f"Ejecutar experimento principal",
                f"Analizar resultados obtenidos",
                f"Preparar presentación final",
                f"Evaluar proceso seguido",
                f"Proponer mejoras futuras"
            ]
        
        # Aplicar modificaciones si las hay
        if modificaciones_tareas:
            tareas_modificadas = self._aplicar_modificaciones_tareas(tareas_base, modificaciones_tareas)
            return tareas_modificadas
        
        return tareas_base
    
    # FASE 4: REPARTO EQUILIBRADO
    def repartir_tareas_equilibradas(self, tareas: List[str], modificaciones_reparto: Dict = None) -> Dict[str, str]:
        """Fase 4: Reparte tareas según perfiles de estudiantes"""
        
        # Análisis de carga por tarea
        cargas_tareas = self._analizar_carga_cognitiva(tareas)
        
        # Reparto inicial automático
        reparto = {}
        estudiantes_ids = list(self.perfiles_estudiantes.keys())
        
        # Ordenar estudiantes por necesidades especiales primero
        estudiantes_ordenados = self._ordenar_por_prioridad_adaptacion(estudiantes_ids)
        
        # Asignar tareas según perfil
        for i, estudiante_id in enumerate(estudiantes_ordenados):
            if i < len(tareas):
                tarea_asignada = self._adaptar_tarea_a_perfil(tareas[i], estudiante_id)
                reparto[estudiante_id] = tarea_asignada
        
        # Aplicar modificaciones específicas si las hay
        if modificaciones_reparto:
            reparto = self._aplicar_modificaciones_reparto(reparto, modificaciones_reparto)
        
        return reparto
    
    # MÉTODOS AUXILIARES PARA LAS 4 FASES
    
    def _estructurar_simple(self, estructura_base: Dict) -> Dict[str, Any]:
        """Estructura actividad simple según clima"""
        tema = estructura_base["tema"]
        return {
            **estructura_base,
            "titulo": f"Práctica Directa de {tema.title()}",
            "contenido": f"Actividad práctica donde trabajamos {tema} mediante tareas concretas y materiales físicos",
            "materiales": estructura_base["materiales_base"] + [f"objetos relacionados con {tema}"],
            "fases": [
                f"Preparación materiales (5 min)",
                f"Trabajo individual con {tema} (20 min)",
                f"Verificación grupal (5 min)"
            ]
        }
    
    def _estructurar_juego(self, estructura_base: Dict) -> Dict[str, Any]:
        """Estructura actividad de juego"""
        tema = estructura_base["tema"]
        return {
            **estructura_base,
            "titulo": f"Juego de {tema.title()}",
            "contenido": f"Competencia por equipos donde aprendemos {tema} jugando con reglas y puntuación",
            "materiales": estructura_base["materiales_base"] + [f"elementos de juego de {tema}", "marcador"],
            "fases": [
                "Explicación de reglas (10 min)",
                "Competencia por equipos (30 min)",
                "Evaluación de estrategias (5 min)"
            ]
        }
    
    def _estructurar_narrativa(self, estructura_base: Dict) -> Dict[str, Any]:
        """Estructura actividad narrativa"""
        tema = estructura_base["tema"]
        return {
            **estructura_base,
            "titulo": f"Aventura de {tema.title()}",
            "contenido": f"Historia donde exploramos {tema} a través de personajes y situaciones envolventes",
            "materiales": estructura_base["materiales_base"] + [f"props para {tema}", "vestuario básico"],
            "fases": [
                "Introducción de personajes (15 min)",
                "Desarrollo de la aventura (35 min)",
                "Desenlace y reflexión (10 min)"
            ]
        }
    
    def _estructurar_complejo(self, estructura_base: Dict) -> Dict[str, Any]:
        """Estructura actividad compleja/proyecto"""
        tema = estructura_base["tema"]
        return {
            **estructura_base,
            "titulo": f"Proyecto de Investigación: {tema.title()}",
            "contenido": f"Investigación profunda de {tema} mediante proyecto colaborativo multi-fase",
            "materiales": estructura_base["materiales_base"] + [f"recursos de investigación sobre {tema}"],
            "fases": [
                "Investigación inicial (20 min)",
                "Planificación y ejecución (50 min)",
                "Presentación de resultados (20 min)"
            ]
        }
    
    def _analizar_carga_cognitiva(self, tareas: List[str]) -> Dict[str, str]:
        """Analiza carga cognitiva de cada tarea"""
        cargas = {}
        for tarea in tareas:
            if any(palabra in tarea.lower() for palabra in ["investigar", "analizar", "planificar"]):
                cargas[tarea] = "alta"
            elif any(palabra in tarea.lower() for palabra in ["organizar", "preparar", "verificar"]):
                cargas[tarea] = "media"
            else:
                cargas[tarea] = "baja"
        return cargas
    
    def _ordenar_por_prioridad_adaptacion(self, estudiantes_ids: List[str]) -> List[str]:
        """Ordena estudiantes priorizando adaptaciones especiales"""
        def prioridad_adaptacion(estudiante_id):
            perfil = self.perfiles_estudiantes[estudiante_id]
            if "TEA" in perfil["estilo"]:
                return 1  # Máxima prioridad
            elif "TDAH" in perfil["estilo"]:
                return 2
            elif "altas_capacidades" in perfil["estilo"]:
                return 3
            else:
                return 4
        
        return sorted(estudiantes_ids, key=prioridad_adaptacion)
    
    def _adaptar_tarea_a_perfil(self, tarea: str, estudiante_id: str) -> str:
        """Adapta tarea específica al perfil del estudiante"""
        perfil = self.perfiles_estudiantes[estudiante_id]
        
        # Adaptaciones para TEA
        if "TEA" in perfil["estilo"]:
            if "organizar" in tarea.lower():
                return tarea + " usando etiquetas visuales con colores"
            elif "explicar" in tarea.lower():
                return tarea.replace("explicar", "mostrar con apoyo visual")
        
        # Adaptaciones para TDAH
        elif "TDAH" in perfil["estilo"]:
            if "documentar" in tarea.lower():
                return tarea.replace("documentar", "registrar rápidamente")
            elif "examinar" in tarea.lower():
                return tarea + " tocando y manipulando objetos"
        
        # Adaptaciones para altas capacidades
        elif "altas_capacidades" in perfil["estilo"]:
            if "verificar" in tarea.lower():
                return tarea + " y proponer mejoras al proceso"
            elif "presentar" in tarea.lower():
                return tarea + " liderando la discusión grupal"
        
        return tarea
    
    def _aplicar_modificaciones_tareas(self, tareas: List[str], modificaciones: Dict) -> List[str]:
        """Aplica modificaciones específicas a las tareas"""
        tareas_modificadas = tareas.copy()
        
        # Aplicar adaptaciones específicas
        if modificaciones.get("adaptaciones"):
            for adaptacion in modificaciones["adaptaciones"]:
                if "kinestésico" in adaptacion:
                    tareas_modificadas = [t.replace("examinar", "tocar y manipular") for t in tareas_modificadas]
                elif "visual" in adaptacion:
                    tareas_modificadas = [t + " con apoyo visual" if "organizar" in t else t for t in tareas_modificadas]
        
        return tareas_modificadas
    
    def _aplicar_modificaciones_reparto(self, reparto: Dict[str, str], modificaciones: Dict) -> Dict[str, str]:
        """Aplica modificaciones específicas al reparto"""
        reparto_modificado = reparto.copy()
        
        # Modificaciones para estudiantes específicos
        if modificaciones.get("estudiantes_especificos"):
            for modificacion in modificaciones["estudiantes_especificos"]:
                # Aquí se pueden aplicar cambios específicos según la modificación detectada
                pass
        
        # Re-equilibrio si se solicita
        if modificaciones.get("equilibrio"):
            # Lógica para reequilibrar cargas
            pass
        
        return reparto_modificado
    
    # MÉTODO PRINCIPAL QUE INTEGRA LAS 4 FASES
    def generar_actividad_completa(self, materia: str, tema: str, clima: str = "simple") -> ActividadEducativa:
        """Genera actividad completa siguiendo el flujo de 4 fases"""
        
        # FASE 1: Clima/Complejidad
        estructura_base = self.generar_estructura_por_clima(materia, tema, clima)
        
        # FASE 2: Estructuración
        actividad_estructurada = self.estructurar_actividad(estructura_base)
        
        # FASE 3: Desglose de tareas
        tareas = self.descomponer_en_tareas(actividad_estructurada)
        
        # FASE 4: Reparto equilibrado
        reparto = self.repartir_tareas_equilibradas(tareas)
        
        # Crear actividad final
        return ActividadEducativa(
            id=f"coherente_{clima}_{materia}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=actividad_estructurada["titulo"],
            materia=materia,
            tema=tema,
            contenido=actividad_estructurada["contenido"],
            tareas_estudiantes=reparto,
            materiales=actividad_estructurada["materiales"],
            duracion=f"{actividad_estructurada['duracion_base']} minutos",
            fases=actividad_estructurada["fases"],
            validacion={"puntuacion": 0, "observaciones": []},
            timestamp=datetime.now().isoformat()
        )
    
    # Los métodos de hardcodeo han sido eliminados - ahora todo se genera dinámicamente
    
    def adaptar_segun_intenciones(self, actividad: ActividadEducativa, intenciones: Dict) -> ActividadEducativa:
        """Adapta actividad según intenciones detectadas en prompt"""
        
        cambios = intenciones.get("cambios_detectados", [])
        parametros = intenciones.get("parametros", {})
        
        # Cambio completo de tema
        if "tema_completo" in cambios and "nuevo_tema" in parametros:
            nuevo_tema = parametros["nuevo_tema"]
            if nuevo_tema == "fracciones":
                return self._generar_fracciones_manipulativas()
        
        # Ajustar duración
        if "duracion" in cambios and "tiempo_minutos" in parametros:
            minutos = int(parametros["tiempo_minutos"])
            actividad.duracion = f"{minutos} minutos"
            
            if minutos <= 30:
                # Reducir tareas manteniendo interdependencia
                tareas_reducidas = {}
                claves_importantes = ["001", "003", "004", "006", "008"]  # Mantener interdependencia
                for clave in claves_importantes:
                    if clave in actividad.tareas_estudiantes:
                        tareas_reducidas[clave] = actividad.tareas_estudiantes[clave]
                actividad.tareas_estudiantes = tareas_reducidas
        
        # Adaptar materiales
        if "materiales" in cambios:
            if "material_faltante" in parametros:
                material_faltante = parametros["material_faltante"]
                actividad.materiales = [m for m in actividad.materiales if material_faltante not in m.lower()]
                
                # Sustituir materiales faltantes
                if "bloques" in material_faltante:
                    actividad.materiales.append("Dados de papel caseros")
                if "reglas" in material_faltante:
                    actividad.materiales.append("Tiras de papel marcadas cada cm")
        
        # Hacer más manipulativo
        if "tipo_actividad" in cambios:
            for clave, tarea in actividad.tareas_estudiantes.items():
                # Convertir tareas abstractas en físicas
                if "buscar información" in tarea:
                    actividad.tareas_estudiantes[clave] = tarea.replace("buscar información", "tocar y examinar objetos")
                if "crear cartel" in tarea:
                    actividad.tareas_estudiantes[clave] = tarea.replace("crear cartel", "construir modelo físico")
        
        return actividad

class ValidadorCoherenciaK:
    """Valida actividades usando principios extraídos de ejemplos k_"""
    
    def __init__(self, cargador_ejemplos: CargadorEjemplosK):
        self.patrones_k = cargador_ejemplos.patrones_extraidos
    
    def validar_actividad(self, actividad: ActividadEducativa) -> Dict:
        """Valida actividad contra principios k_"""
        puntuacion = 10
        observaciones = []
        
        # Principio 1: Roles específicos (no abstractos)
        tareas = list(actividad.tareas_estudiantes.values())
        roles_abstractos = sum(1 for t in tareas if any(
            palabra in t.lower() for palabra in ["investigador", "diseñador", "coordinador", "gestor"]
        ))
        if roles_abstractos > 2:
            puntuacion -= 2
            observaciones.append(f"Detectados {roles_abstractos} roles abstractos. Usa tareas concretas.")
        
        # Principio 2: Interdependencia real
        interdependencia = sum(1 for t in tareas if any(
            palabra in t.lower() for palabra in ["verifica", "usa", "necesita", "recoger", "todos", "entre"]
        ))
        if interdependencia < 2:
            puntuacion -= 3
            observaciones.append("Falta interdependencia real entre estudiantes.")
        
        # Principio 3: Materialidad física
        materiales_fisicos = sum(1 for m in actividad.materiales if any(
            palabra in m.lower() for palabra in ["regla", "tijeras", "papel", "objetos", "bloques", "plastilina"]
        ))
        if materiales_fisicos < 3:
            puntuacion -= 2
            observaciones.append("Pocos materiales físicos manipulables.")
        
        # Principio 4: Especificidad en tareas
        tareas_especificas = sum(1 for t in tareas if any(
            caracteristica in t for caracteristica in ["medir", "cortar", "3", "2", "4", "cm", "exactos"]
        ))
        if tareas_especificas < 3:
            puntuacion -= 1
            observaciones.append("Tareas poco específicas. Añade medidas, cantidades concretas.")
        
        # Principio 5: Tiempo factible
        duracion_texto = actividad.duracion.lower()
        if "minutos" in duracion_texto:
            try:
                minutos = int(re.search(r'(\d+)', duracion_texto).group(1))
                num_tareas = len(actividad.tareas_estudiantes)
                if minutos < num_tareas * 3:  # Mínimo 3 min por tarea
                    puntuacion -= 2
                    observaciones.append(f"Tiempo insuficiente: {minutos} min para {num_tareas} tareas.")
            except:
                pass
        
        return {
            "puntuacion": max(0, puntuacion),
            "observaciones": observaciones,
            "coherencia_k": puntuacion >= 7,
            "principios_cumplidos": 5 - len(observaciones)
        }

class SistemaAgentesCoherente:
    """Sistema principal con flujo de 4 fases y human-in-the-loop natural"""
    
    def __init__(self, directorio_ejemplos: str = "."):
        self.cargador_ejemplos = CargadorEjemplosK(directorio_ejemplos)
        self.analizador_intenciones = AnalizadorIntenciones()
        self.generador = GeneradorActividades(self.cargador_ejemplos)
        self.validador = ValidadorCoherenciaK(self.cargador_ejemplos)
        
        # Estado del flujo
        self.fase_actual = "clima"
        self.estructura_temporal = {}
        self.actividad_temporal = None
        
        logger.info("✅ Sistema de Agentes Coherente inicializado con flujo de 4 fases")
    
    def iniciar_flujo(self, materia: str, tema: str) -> str:
        """Inicia flujo de 4 fases - Fase 1: Clima/Complejidad"""
        self.fase_actual = "clima"
        self.estructura_temporal = {"materia": materia, "tema": tema}
        
        print(f"\n🎯 FASE 1: ¿Qué tipo de actividad quieres para {tema}?")
        print("📋 Opciones de clima:")
        print("  • simple: Tareas directas sin historia")
        print("  • juego: Competencia lúdica con reglas") 
        print("  • narrativa: Historia con personajes")
        print("  • complejo: Proyecto de investigación")
        
        return "Elige tipo de actividad o descríbeme qué tienes en mente"
    
    def procesar_fase_clima(self, prompt: str) -> str:
        """Procesa la fase 1: clima/complejidad"""
        clima = self.analizador_intenciones.analizar_fase_clima(prompt)
        self.estructura_temporal["clima"] = clima
        
        # Generar estructura base
        estructura_base = self.generador.generar_estructura_por_clima(
            self.estructura_temporal["materia"],
            self.estructura_temporal["tema"], 
            clima
        )
        self.estructura_temporal.update(estructura_base)
        
        self.fase_actual = "estructuracion"
        
        print(f"\n🏗️ FASE 2: Estructuración ({clima})")
        print(f"📋 Actividad: {estructura_base['titulo']}")
        print(f"⏱️ Duración base: {estructura_base['duracion_base']} minutos")
        print(f"📦 Materiales: {estructura_base['materiales_base']}")
        print(f"👥 Modalidad: {estructura_base['modalidad_trabajo']}")
        
        return "¿Quieres cambiar duración, materiales, enfoque o modalidad de trabajo? (o 'ok' para continuar)"
    
    def procesar_fase_estructuracion(self, prompt: str) -> str:
        """Procesa la fase 2: estructuración"""
        if prompt.lower() == "ok":
            modificaciones = None
        else:
            modificaciones = self.analizador_intenciones.analizar_fase_estructuracion(prompt)
        
        # Estructurar actividad
        actividad_estructurada = self.generador.estructurar_actividad(
            self.estructura_temporal, modificaciones
        )
        self.estructura_temporal.update(actividad_estructurada)
        
        self.fase_actual = "tareas"
        
        print(f"\n📝 FASE 3: Desglose de Tareas")
        print(f"📋 {actividad_estructurada['titulo']}")
        print(f"🎯 {actividad_estructurada['contenido']}")
        
        return "¿Quieres modificar alguna tarea específica? (o 'ok' para continuar)"
    
    def procesar_fase_tareas(self, prompt: str) -> str:
        """Procesa la fase 3: desglose de tareas"""
        if prompt.lower() == "ok":
            modificaciones_tareas = None
        else:
            modificaciones_tareas = self.analizador_intenciones.analizar_fase_tareas(prompt)
        
        # Descomponer en tareas
        tareas = self.generador.descomponer_en_tareas(
            self.estructura_temporal, modificaciones_tareas
        )
        self.estructura_temporal["tareas"] = tareas
        
        self.fase_actual = "reparto"
        
        print(f"\n👥 FASE 4: Reparto de Tareas")
        print("📋 Tareas identificadas:")
        for i, tarea in enumerate(tareas, 1):
            print(f"  {i}. {tarea}")
        
        return "¿Quieres ajustar el reparto para algún estudiante específico? (o 'ok' para finalizar)"
    
    def procesar_fase_reparto(self, prompt: str) -> ActividadEducativa:
        """Procesa la fase 4: reparto equilibrado - Retorna actividad final"""
        if prompt.lower() == "ok":
            modificaciones_reparto = None
        else:
            modificaciones_reparto = self.analizador_intenciones.analizar_fase_reparto(prompt)
        
        # Repartir tareas
        reparto = self.generador.repartir_tareas_equilibradas(
            self.estructura_temporal["tareas"], modificaciones_reparto
        )
        
        # Crear actividad final
        actividad_final = ActividadEducativa(
            id=f"coherente_{self.estructura_temporal['clima']}_{self.estructura_temporal['materia']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            titulo=self.estructura_temporal["titulo"],
            materia=self.estructura_temporal["materia"],
            tema=self.estructura_temporal["tema"],
            contenido=self.estructura_temporal["contenido"],
            tareas_estudiantes=reparto,
            materiales=self.estructura_temporal["materiales"],
            duracion=f"{self.estructura_temporal['duracion_base']} minutos",
            fases=self.estructura_temporal["fases"],
            validacion={"puntuacion": 0, "observaciones": []},
            timestamp=datetime.now().isoformat()
        )
        
        # Validar actividad final
        validacion = self.validador.validar_actividad(actividad_final)
        actividad_final.validacion = validacion
        
        self.actividad_temporal = actividad_final
        self.fase_actual = "completado"
        
        return actividad_final
    
    def procesar_prompt_conversacional(self, prompt: str) -> str:
        """Procesa prompt según la fase actual del flujo"""
        
        if self.fase_actual == "clima":
            return self.procesar_fase_clima(prompt)
        elif self.fase_actual == "estructuracion":
            return self.procesar_fase_estructuracion(prompt)
        elif self.fase_actual == "tareas":
            return self.procesar_fase_tareas(prompt)
        elif self.fase_actual == "reparto":
            # Esta fase retorna ActividadEducativa, no string
            actividad = self.procesar_fase_reparto(prompt)
            return f"✅ Actividad completada: {actividad.titulo}"
        else:
            return "Flujo completado. Usa 'reiniciar' para empezar de nuevo."
    
    def mostrar_actividad(self, actividad: ActividadEducativa):
        """Muestra actividad de forma clara y organizada"""
        print("\n" + "="*60)
        print(f"📚 {actividad.titulo}")
        print("="*60)
        print(f"📖 Materia: {actividad.materia} | Tema: {actividad.tema}")
        print(f"⏱️ Duración: {actividad.duracion}")
        print(f"🎯 {actividad.contenido}")
        
        print(f"\n📦 MATERIALES:")
        for material in actividad.materiales:
            print(f"  • {material}")
        
        print(f"\n👥 TAREAS ESPECÍFICAS:")
        for student_id, tarea in actividad.tareas_estudiantes.items():
            if student_id in self.generador.perfiles_estudiantes:
                nombre = self.generador.perfiles_estudiantes[student_id]["nombre"]
                print(f"  {student_id} {nombre}: {tarea}")
        
        print(f"\n📅 FASES:")
        for i, fase in enumerate(actividad.fases, 1):
            print(f"  {i}. {fase}")
        
        validacion = actividad.validacion
        print(f"\n✅ COHERENCIA K_: {validacion['puntuacion']}/10")
        if validacion.get('observaciones'):
            print("💡 Sugerencias:")
            for obs in validacion['observaciones']:
                print(f"    • {obs}")
    
    def interfaz_conversacional(self, actividad: ActividadEducativa) -> ActividadEducativa:
        """Interfaz conversacional para modificaciones"""
        print("\n💬 Dime qué quieres cambiar (en lenguaje natural)")
        print("   Ejemplo: 'quiero actividad de fracciones manipulativa, no sobre células'")
        print("   Escribe 'ok' para continuar")
        
        while True:
            prompt = input("\n> ").strip()
            
            if prompt.lower() in ["ok", "vale", "continuar", "seguir"]:
                break
            elif len(prompt) > 8:  # Prompt real
                actividad = self.procesar_feedback_natural(actividad, prompt)
                self.mostrar_actividad(actividad)
                print("\n¿Algo más?")
            else:
                print("💭 Escribe tu petición completa o 'ok' para terminar")
        
        return actividad
    
    def guardar_actividad(self, actividad: ActividadEducativa) -> str:
        """Guarda actividad en archivo"""
        filename = f"actividad_{actividad.id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            # Convertir a dict para JSON
            actividad_dict = {
                "id": actividad.id,
                "titulo": actividad.titulo,
                "materia": actividad.materia,
                "tema": actividad.tema,
                "contenido": actividad.contenido,
                "tareas_estudiantes": actividad.tareas_estudiantes,
                "materiales": actividad.materiales,
                "duracion": actividad.duracion,
                "fases": actividad.fases,
                "validacion": actividad.validacion,
                "timestamp": actividad.timestamp
            }
            json.dump(actividad_dict, f, indent=2, ensure_ascii=False)
        return filename

def main():
    """Función principal con flujo de 4 fases"""
    print("🎯 Sistema de Agentes Coherente - Flujo de 4 Fases")
    print("Basado en patrones k_ exitosos + Human-in-the-Loop natural")
    print("="*60)
    
    # Inicializar sistema
    sistema = SistemaAgentesCoherente()
    
    # Input inicial
    materia = input("📖 Materia: ").strip()
    tema = input("📋 Tema: ").strip()
    
    # INICIAR FLUJO DE 4 FASES
    mensaje = sistema.iniciar_flujo(materia, tema)
    print(f"\n💬 {mensaje}")
    
    # BUCLE CONVERSACIONAL POR FASES
    while sistema.fase_actual != "completado":
        prompt = input("\n> ").strip()
        
        if prompt.lower() in ["salir", "exit", "quit"]:
            break
        
        mensaje = sistema.procesar_prompt_conversacional(prompt)
        print(f"\n💬 {mensaje}")
        
        # Si completamos el reparto, mostrar actividad final
        if sistema.fase_actual == "completado" and sistema.actividad_temporal:
            print("\n🎉 ¡ACTIVIDAD COMPLETADA!")
            sistema.mostrar_actividad(sistema.actividad_temporal)
            
            # Guardar actividad
            archivo = sistema.guardar_actividad(sistema.actividad_temporal)
            print(f"\n✅ Actividad guardada: {archivo}")
            print(f"🎯 Coherencia K_: {sistema.actividad_temporal.validacion['puntuacion']}/10")
            
            if sistema.actividad_temporal.validacion['coherencia_k']:
                print("🌟 ¡Actividad cumple estándares k_!")
            else:
                print("⚠️ Sugerencias de mejora:")
                for obs in sistema.actividad_temporal.validacion['observaciones']:
                    print(f"    • {obs}")
            
            break
    
    print("\n👋 ¡Gracias por usar el Sistema de Agentes Coherente!")

if __name__ == "__main__":
    main()