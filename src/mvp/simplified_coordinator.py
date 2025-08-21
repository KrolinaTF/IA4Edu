"""
Coordinador Simplificado - MVP del sistema ABP.
Un solo agente que hace todo el trabajo con prompt directo al LLM.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Importar solo componentes útiles del sistema actual
from core.ollama_integrator import OllamaIntegrator
from core.embeddings_manager import EmbeddingsManager

logger = logging.getLogger("SimplifiedABP.Coordinator")

class SimplifiedCoordinator:
    """
    Coordinador simplificado que genera actividades ABP usando:
    1. Ejemplos relevantes (via embeddings)
    2. Perfiles de estudiantes 
    3. Prompt directo al LLM (sin plantillas complejas)
    """
    
    def __init__(self, ollama_integrator=None):
        """
        Inicializa el coordinador simplificado
        
        Args:
            ollama_integrator: Integrador Ollama (opcional)
        """
        # Integrador LLM
        self.ollama = ollama_integrator or OllamaIntegrator()
        
        # Log para mostrar qué modelo se está usando
        provider = self.ollama.provider
        if provider == "groq":
            modelo_actual = self.ollama.groq_model
            logger.info(f"🤖 Usando modelo GROQ: {modelo_actual}")
        else:
            modelo_actual = self.ollama.model
            logger.info(f"🤖 Usando modelo OLLAMA: {modelo_actual} en {self.ollama.host}:{self.ollama.port}")
        
        # También log del modelo de embeddings
        logger.info(f"🔗 Modelo de embeddings: {self.ollama.embedding_model} (Ollama local)")
        
        # Gestor de embeddings para ejemplos
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        proyecto_root = os.path.dirname(base_dir)
        actividades_path = os.path.join(proyecto_root, "data", "actividades")
        self.embeddings_manager = EmbeddingsManager(actividades_path, self.ollama)
        
        # Cargar perfiles de estudiantes
        self.student_profiles = self._load_student_profiles()
        
        # Guardar información de agrupación para refinamientos
        self.last_grouping_info = None
        
        # Registro de problemas comunes para aprender
        self.common_issues = []
        
        logger.info("🚀 SimplifiedCoordinator inicializado")
    
    def _load_student_profiles(self) -> Dict[str, Any]:
        """
        Carga perfiles reales de estudiantes
        
        Returns:
            Diccionario con perfiles de estudiantes
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            perfiles_path = os.path.join(base_dir, "data", "perfiles_4_primaria.json")
            
            with open(perfiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            logger.info(f"✅ Cargados {len(data['estudiantes'])} perfiles de estudiantes")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error cargando perfiles: {e}")
            return {"estudiantes": []}
    
    def generate_activity(self, user_request: str, additional_details: str = "") -> Dict[str, Any]:
        """
        Genera actividad ABP completa de forma simplificada
        
        Args:
            user_request: Solicitud del usuario (ej: "actividad de geografía con rutas")
            additional_details: Detalles adicionales opcionales
            
        Returns:
            Actividad ABP completa generada
        """
        logger.info(f"🎯 Generando actividad para: '{user_request[:50]}...'")
        
        try:
            # 1. Detectar modo de agrupación solicitado
            grouping_info = self._detect_grouping_mode(user_request + " " + additional_details)
            self.last_grouping_info = grouping_info  # Guardar para refinamientos
            
            # 2. Buscar ejemplos relevantes
            ejemplos_relevantes = self._find_relevant_examples(user_request)
            
            # 3. Crear prompt directo con información de agrupación
            prompt_directo = self._create_direct_prompt(
                user_request, 
                ejemplos_relevantes, 
                additional_details,
                grouping_info
            )
            
            # 4. Generar con LLM
            response = self.ollama.generar_respuesta(
                prompt_directo, 
                max_tokens=1500, 
                temperatura=0.7
            )
            
            # 5. Procesar respuesta y crear estructura final
            activity_result = self._process_llm_response(response, user_request)
            
            # 6. Crear asignaciones específicas según modo de agrupación
            activity_result = self._assign_students_to_tasks(activity_result, grouping_info)
            
            # 7. Añadir metadatos
            activity_result['metadatos'] = {
                'timestamp': datetime.now().isoformat(),
                'sistema': 'SimplifiedCoordinator',
                'version': '1.0',
                'prompt_original': user_request,
                'modo_agrupacion': grouping_info,
                'ejemplos_utilizados': [ej[0] for ej in ejemplos_relevantes]
            }
            
            logger.info(f"✅ Actividad generada exitosamente")
            return activity_result
            
        except Exception as e:
            logger.error(f"❌ Error generando actividad: {e}")
            return self._create_fallback_activity(user_request)
    
    def _detect_grouping_mode(self, text: str) -> Dict[str, Any]:
        """
        Detecta el modo de agrupación solicitado en el texto
        
        Args:
            text: Texto del usuario (request + detalles)
            
        Returns:
            Diccionario con información de agrupación
        """
        text_lower = text.lower()
        
        # Detección por fases
        grouping_info = {
            'preparacion': {'modo': 'parejas', 'tamaño': 2},
            'ejecucion': {'modo': 'parejas', 'tamaño': 2},
            'general': {'modo': 'parejas', 'tamaño': 2}
        }
        
        # Patrones para detectar modos
        individual_patterns = [
            'individual', 'cada uno', 'por separado', 'solos', 'cada estudiante',
            'cada uno prepare', 'cada cual', 'por su cuenta', 'independientemente',
            'cada persona', 'cada niño', 'cada niña', 'de forma individual'
        ]
        pairs_patterns = ['parejas', 'en pareja', 'de a dos', 'duplas', 'pares']
        group_patterns = ['grupos', 'equipos', 'en grupo']
        
        # Detectar menciones de fases
        prep_patterns = ['preparación', 'preparacion', 'primera fase', 'fase 1', 'inicio']
        exec_patterns = ['ejecución', 'ejecucion', 'segunda fase', 'fase 2', 'desarrollo']
        
        # Analizar solicitud general
        if any(pattern in text_lower for pattern in individual_patterns):
            grouping_info['general']['modo'] = 'individual'
            grouping_info['general']['tamaño'] = 1
        elif any(pattern in text_lower for pattern in group_patterns):
            # Buscar tamaño de grupo
            import re
            size_match = re.search(r'grupos?\s+de\s+(\d+)', text_lower)
            if size_match:
                group_size = int(size_match.group(1))
            else:
                group_size = 4  # Default
            grouping_info['general']['modo'] = 'grupos'
            grouping_info['general']['tamaño'] = group_size
        
        # Detectar si hay instrucciones específicas por fase
        for line in text_lower.split('.'):
            # Fase de preparación
            if any(p in line for p in prep_patterns):
                if any(p in line for p in individual_patterns):
                    grouping_info['preparacion']['modo'] = 'individual'
                    grouping_info['preparacion']['tamaño'] = 1
                elif any(p in line for p in group_patterns):
                    size_match = re.search(r'grupos?\s+de\s+(\d+)', line)
                    grouping_info['preparacion']['modo'] = 'grupos'
                    grouping_info['preparacion']['tamaño'] = int(size_match.group(1)) if size_match else 4
                elif any(p in line for p in pairs_patterns):
                    grouping_info['preparacion']['modo'] = 'parejas'
                    grouping_info['preparacion']['tamaño'] = 2
            
            # Fase de ejecución
            elif any(p in line for p in exec_patterns):
                if any(p in line for p in individual_patterns):
                    grouping_info['ejecucion']['modo'] = 'individual'
                    grouping_info['ejecucion']['tamaño'] = 1
                elif any(p in line for p in group_patterns):
                    size_match = re.search(r'grupos?\s+de\s+(\d+)', line)
                    grouping_info['ejecucion']['modo'] = 'grupos'
                    grouping_info['ejecucion']['tamaño'] = int(size_match.group(1)) if size_match else 4
                elif any(p in line for p in pairs_patterns):
                    grouping_info['ejecucion']['modo'] = 'parejas'
                    grouping_info['ejecucion']['tamaño'] = 2
        
        # Si no hay instrucciones específicas por fase, usar general
        if grouping_info['preparacion'] == {'modo': 'parejas', 'tamaño': 2}:
            grouping_info['preparacion'] = grouping_info['general'].copy()
        if grouping_info['ejecucion'] == {'modo': 'parejas', 'tamaño': 2}:
            grouping_info['ejecucion'] = grouping_info['general'].copy()
        
        logger.info(f"🔍 Modo de agrupación detectado: {grouping_info}")
        return grouping_info
    
    def _find_relevant_examples(self, user_request: str) -> List[tuple]:
        """
        Busca ejemplos relevantes usando embeddings
        
        Args:
            user_request: Solicitud del usuario
            
        Returns:
            Lista de ejemplos relevantes (id, similitud, data)
        """
        try:
            ejemplos = self.embeddings_manager.encontrar_actividad_similar(
                user_request, 
                top_k=2  # Solo 2 ejemplos para no saturar
            )
            
            logger.info(f"🔍 Encontrados {len(ejemplos)} ejemplos relevantes")
            for i, (ej_id, sim, _) in enumerate(ejemplos):
                logger.info(f"   {i+1}. {ej_id} (similitud: {sim:.3f})")
            
            return ejemplos
            
        except Exception as e:
            logger.error(f"❌ Error buscando ejemplos: {e}")
            return []
    
    def _create_direct_prompt(self, user_request: str, ejemplos: List[tuple], 
                            additional_details: str, grouping_info: Dict[str, Any]) -> str:
        """
        Crea prompt directo para el LLM con información de agrupación
        
        Args:
            user_request: Solicitud del usuario
            ejemplos: Ejemplos relevantes encontrados
            additional_details: Detalles adicionales
            grouping_info: Información sobre modo de agrupación
            
        Returns:
            Prompt directo para el LLM
        """
        # Crear contexto de ejemplos (solo estructura, no contenido literal)
        contexto_ejemplos = ""
        if ejemplos:
            contexto_ejemplos = "\n--- EJEMPLOS DE REFERENCIA (solo para inspiración estructural) ---\n"
            for ej_id, sim, ej_data in ejemplos[:2]:  # Solo 2 ejemplos
                titulo = ej_data.get('titulo', 'Sin título')
                objetivo = ej_data.get('objetivo', 'Sin objetivo')[:100]
                contexto_ejemplos += f"• {titulo}: {objetivo}...\n"
            contexto_ejemplos += "--- FIN EJEMPLOS ---\n\n"
        
        # Crear información de estudiantes
        estudiantes_info = self._create_students_context()
        
        # Crear descripción de agrupaciones según lo solicitado
        agrupacion_prep = grouping_info['preparacion']
        agrupacion_ejec = grouping_info['ejecucion']
        
        agrupacion_instrucciones = f"""
MODO DE AGRUPACIÓN:
- Fase de Preparación: Trabajo {agrupacion_prep['modo']} {f'(grupos de {agrupacion_prep["tamaño"]})' if agrupacion_prep['modo'] == 'grupos' else ''}
- Fase de Ejecución: Trabajo {agrupacion_ejec['modo']} {f'(grupos de {agrupacion_ejec["tamaño"]})' if agrupacion_ejec['modo'] == 'grupos' else ''}"""
        
        # Ajustar formato de ejemplo según agrupación
        ejemplo_asignacion_prep = self._get_assignment_example(agrupacion_prep['modo'], agrupacion_prep['tamaño'])
        ejemplo_asignacion_ejec = self._get_assignment_example(agrupacion_ejec['modo'], agrupacion_ejec['tamaño'])
        
        # Prompt directo usando formato Markdown
        prompt = f"""Crea una actividad educativa ABP (Aprendizaje Basado en Proyectos) para 4º de Primaria.

SOLICITUD DEL PROFESOR:
{user_request}

{f"DETALLES ADICIONALES: {additional_details}" if additional_details else ""}

{contexto_ejemplos}

ESTUDIANTES DEL AULA (8 estudiantes):
{estudiantes_info}

{agrupacion_instrucciones}

INSTRUCCIONES:
1. Crea una actividad concreta y específica basada en la solicitud
2. Divide en 2 fases: Preparación y Ejecución
3. Asigna estudiantes según el modo de agrupación indicado para cada fase
4. Incluye adaptaciones para TEA, TDAH y altas capacidades
5. Sé específico: si pides rutas geográficas, nombra lugares reales
6. Si pides roles, define roles concretos (no genéricos)

RESPONDE EN FORMATO MARKDOWN usando esta estructura exacta:

# [Título específico de la actividad]

## Información General
- **Objetivo**: [Objetivo educativo claro]
- **Duración**: 2 sesiones de 45 minutos
- **Modo de trabajo**: {agrupacion_prep['modo']} en preparación, {agrupacion_ejec['modo']} en ejecución

## Fase 1: Preparación
**Modo de agrupación**: {agrupacion_prep['modo']}
**Descripción**: [Descripción específica de qué se hace]

### Tareas:
1. **[Nombre de la tarea]**
   - Descripción: [Descripción detallada y concreta]
   - Asignaciones: {ejemplo_asignacion_prep}
   - Detalles específicos: [Detalles concretos]

## Fase 2: Ejecución  
**Modo de agrupación**: {agrupacion_ejec['modo']}
**Descripción**: [Descripción específica de la fase principal]

### Tareas:
1. **[Nombre de la tarea]**
   - Descripción: [Descripción detallada y concreta]
   - Asignaciones: {ejemplo_asignacion_ejec}
   - Detalles específicos: [Detalles concretos y específicos]

## Adaptaciones por Neurotipo

### TEA (Trastorno del Espectro Autista)
- [Adaptaciones específicas para TEA]

### TDAH (Trastorno por Déficit de Atención e Hiperactividad)
- [Adaptaciones específicas para TDAH]

### Altas Capacidades
- [Desafíos específicos para altas capacidades]"""

        return prompt
    
    def _get_assignment_example(self, modo: str, tamaño: int) -> str:
        """
        Genera ejemplo de asignación según el modo de agrupación para Markdown
        
        Args:
            modo: Modo de agrupación ('individual', 'parejas', 'grupos')
            tamaño: Tamaño del grupo
            
        Returns:
            String con ejemplo de asignación para Markdown
        """
        if modo == 'individual':
            return 'Elena, Ana, Luis, Hugo, María, Emma, Alex, Sara'
        elif modo == 'parejas':
            return 'Elena y Ana, Luis y Hugo, María y Emma, Alex y Sara'
        elif modo == 'grupos':
            if tamaño == 3:
                return 'Elena, Ana y Luis; Hugo, María y Emma; Alex y Sara (grupo de 2)'
            elif tamaño == 4:
                return 'Elena, Ana, Luis y Hugo; María, Emma, Alex y Sara'
            else:
                return 'Grupo 1: Elena, Ana, Luis; Grupo 2: Hugo, María, Emma; Grupo 3: Alex, Sara'
        else:
            return 'Elena y Ana, Luis y Hugo, María y Emma, Alex y Sara'
    
    def _create_students_context(self) -> str:
        """
        Crea contexto simplificado de estudiantes
        
        Returns:
            Información resumida de estudiantes
        """
        if not self.student_profiles.get('estudiantes'):
            return "Alex, María, Elena (TEA), Luis (TDAH), Ana (altas capacidades), Sara, Emma, Hugo"
        
        estudiantes_resumen = []
        for estudiante in self.student_profiles['estudiantes']:
            nombre = estudiante.get('nombre', 'Sin nombre')
            diagnostico = estudiante.get('diagnostico_formal', 'ninguno')
            
            if diagnostico and diagnostico != 'ninguno':
                if 'TEA' in diagnostico:
                    estudiantes_resumen.append(f"{nombre} (TEA)")
                elif 'TDAH' in diagnostico:
                    estudiantes_resumen.append(f"{nombre} (TDAH)")
                elif 'altas_capacidades' in diagnostico:
                    estudiantes_resumen.append(f"{nombre} (altas capacidades)")
                else:
                    estudiantes_resumen.append(nombre)
            else:
                estudiantes_resumen.append(nombre)
        
        return ", ".join(estudiantes_resumen)
    
    def _process_llm_response(self, response: str, user_request: str) -> Dict[str, Any]:
        """
        Procesa respuesta del LLM en formato Markdown y crea estructura
        
        Args:
            response: Respuesta cruda del LLM en Markdown
            user_request: Solicitud original del usuario
            
        Returns:
            Estructura procesada de la actividad
        """
        try:
            # Parsear Markdown directamente
            activity = self._parse_markdown_response(response)
            logger.info("✅ Markdown parseado correctamente")
            return activity
                
        except Exception as e:
            logger.error(f"❌ Error parseando Markdown: {e}")
            logger.error(f"🔍 Respuesta completa del LLM: {response[:1000]}...")
            return self._create_fallback_activity(user_request)
    
    def _parse_markdown_response(self, response: str) -> Dict[str, Any]:
        """
        Parsea respuesta en formato Markdown y la convierte a estructura
        
        Args:
            response: Respuesta en Markdown del LLM
            
        Returns:
            Diccionario con estructura de actividad
        """
        import re
        
        activity = {
            "titulo": "Actividad ABP",
            "objetivo": "",
            "duracion": "2 sesiones de 45 minutos",
            "fases": [],
            "adaptaciones": {}
        }
        
        lines = response.split('\n')
        current_section = None
        current_phase = None
        current_task = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            # Título principal (# Título)
            if line.startswith('# '):
                activity["titulo"] = line[2:].strip()
            
            # Información General
            elif '**Objetivo**:' in line:
                activity["objetivo"] = line.split('**Objetivo**:')[1].strip()
            elif '**Duración**:' in line:
                activity["duracion"] = line.split('**Duración**:')[1].strip()
            
            # Fases
            elif line.startswith('## Fase '):
                phase_name = line[3:].strip()
                current_phase = {
                    "nombre": phase_name,
                    "descripcion": "",
                    "modo_agrupacion": "",
                    "tareas": []
                }
                activity["fases"].append(current_phase)
                current_section = "fase"
            
            elif line.startswith('**Descripción**:') and current_phase:
                current_phase["descripcion"] = line.split('**Descripción**:')[1].strip()
            
            elif line.startswith('**Modo de agrupación**:') and current_phase:
                current_phase["modo_agrupacion"] = line.split('**Modo de agrupación**:')[1].strip()
            
            # Tareas
            elif re.match(r'^\d+\.\s*\*\*.*\*\*', line) and current_phase:
                task_name = re.findall(r'\*\*(.*?)\*\*', line)[0]
                current_task = {
                    "nombre": task_name,
                    "descripcion": "",
                    "asignaciones": [],
                    "detalles_especificos": ""
                }
                current_phase["tareas"].append(current_task)
            
            elif line.startswith('- Descripción:') and current_task:
                current_task["descripcion"] = line.split('- Descripción:')[1].strip()
            elif line.startswith('- Asignaciones:') and current_task:
                asignaciones_text = line.split('- Asignaciones:')[1].strip()
                # Parsear las asignaciones (pueden estar en diferentes formatos)
                current_task["asignaciones"] = self._parse_assignments(asignaciones_text)
            elif line.startswith('- Detalles específicos:') and current_task:
                current_task["detalles_especificos"] = line.split('- Detalles específicos:')[1].strip()
            
            # Adaptaciones
            elif line.startswith('### TEA'):
                current_section = "TEA"
            elif line.startswith('### TDAH'):
                current_section = "TDAH"
            elif line.startswith('### Altas Capacidades'):
                current_section = "altas_capacidades"
            elif line.startswith('- ') and current_section in ["TEA", "TDAH", "altas_capacidades"]:
                if current_section not in activity["adaptaciones"]:
                    activity["adaptaciones"][current_section] = []
                activity["adaptaciones"][current_section].append(line[2:].strip())
        
        return activity
    
    def _parse_assignments(self, assignments_text: str) -> List[str]:
        """
        Parsea el texto de asignaciones en una lista
        
        Args:
            assignments_text: Texto con asignaciones
            
        Returns:
            Lista de asignaciones
        """
        import re
        
        # Remover corchetes si existen
        assignments_text = assignments_text.strip('[]"\'')
        
        # Separar por comas
        assignments = [a.strip().strip('"\'') for a in assignments_text.split(',')]
        
        return assignments
    
    def _create_structure_from_text(self, response: str, user_request: str) -> Dict[str, Any]:
        """
        Crea estructura básica cuando no hay JSON válido
        
        Args:
            response: Respuesta del LLM
            user_request: Solicitud original
            
        Returns:
            Estructura básica de actividad
        """
        # Extraer información básica del texto
        lines = response.split('\n')
        titulo = "Actividad generada"
        objetivo = f"Actividad basada en: {user_request}"
        
        # Buscar título en las primeras líneas
        for line in lines[:5]:
            if 'título' in line.lower() or 'title' in line.lower():
                titulo = line.split(':')[-1].strip()
                break
        
        return {
            "titulo": titulo,
            "objetivo": objetivo,
            "duracion": "2 sesiones de 45 minutos",
            "fases": [
                {
                    "nombre": "Preparación",
                    "descripcion": "Fase de preparación de la actividad",
                    "tareas": [
                        {
                            "nombre": "Organización inicial",
                            "descripcion": "Organizar materiales y formar parejas",
                            "parejas_asignadas": ["Elena y Ana", "Luis y Hugo"],
                            "detalles_especificos": "Según solicitud del profesor"
                        }
                    ]
                },
                {
                    "nombre": "Ejecución",
                    "descripcion": "Desarrollo principal de la actividad",
                    "tareas": [
                        {
                            "nombre": "Desarrollo principal",
                            "descripcion": "Ejecutar la actividad principal",
                            "parejas_asignadas": ["María y Emma", "Alex y Sara"],
                            "detalles_especificos": "Basado en la respuesta del LLM"
                        }
                    ]
                }
            ],
            "adaptaciones": {
                "TEA": ["Estructura clara", "Apoyos visuales"],
                "TDAH": ["Descansos frecuentes", "Tareas fragmentadas"],
                "altas_capacidades": ["Retos adicionales", "Autonomía"]
            },
            "respuesta_completa_llm": response
        }
    
    def _assign_students_to_tasks(self, activity: Dict[str, Any], grouping_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asigna estudiantes específicos a tareas según modo de agrupación
        
        Args:
            activity: Actividad generada
            grouping_info: Información sobre modo de agrupación
            
        Returns:
            Actividad con asignaciones específicas
        """
        if not self.student_profiles.get('estudiantes'):
            return activity
        
        # Importar ProfileManager para usar sus métodos de agrupación
        from mvp.profile_manager import ProfileManager
        profile_manager = ProfileManager()
        
        # Procesar cada fase con su modo de agrupación
        for i, fase in enumerate(activity.get('fases', [])):
            fase_nombre = fase.get('nombre', '').lower()
            
            # Determinar modo de agrupación para esta fase
            if 'preparación' in fase_nombre or 'preparacion' in fase_nombre:
                modo_info = grouping_info['preparacion']
            elif 'ejecución' in fase_nombre or 'ejecucion' in fase_nombre:
                modo_info = grouping_info['ejecucion']
            else:
                modo_info = grouping_info['general']
            
            # Crear agrupaciones según el modo
            agrupaciones = profile_manager.create_optimal_groupings(
                modo_info['modo'], 
                modo_info['tamaño']
            )
            
            # Asignar estudiantes a todas las tareas de la fase
            for tarea in fase.get('tareas', []):
                if modo_info['modo'] == 'individual':
                    # Todos trabajan en cada tarea individualmente
                    tarea['asignaciones'] = [est[0] for est in agrupaciones]
                elif modo_info['modo'] == 'parejas':
                    # Todas las parejas trabajan en cada tarea
                    tarea['asignaciones'] = [f"{pareja[0]} y {pareja[1]}" for pareja in agrupaciones]
                else:  # grupos
                    # Todos los grupos trabajan en cada tarea
                    tarea['asignaciones'] = [f"Grupo {i+1}: {', '.join(grupo)}" 
                                           for i, grupo in enumerate(agrupaciones)]
                
                # Mantener compatibilidad con campo antiguo
                tarea['parejas_asignadas'] = tarea.get('asignaciones', [])
            
            # Añadir modo de agrupación a la fase
            fase['modo_agrupacion'] = modo_info['modo']
        
        return activity
    
    
    def _create_fallback_activity(self, user_request: str) -> Dict[str, Any]:
        """
        Crea actividad de fallback cuando todo falla
        
        Args:
            user_request: Solicitud original
            
        Returns:
            Actividad básica de fallback
        """
        return {
            "titulo": f"Actividad ABP: {user_request}",
            "objetivo": f"Desarrollar proyecto basado en: {user_request}",
            "duracion": "2 sesiones de 45 minutos",
            "fases": [
                {
                    "nombre": "Preparación",
                    "descripcion": "Preparación y organización inicial",
                    "tareas": [
                        {
                            "nombre": "Organización inicial",
                            "descripcion": "Formar equipos y definir roles",
                            "parejas_asignadas": ["Elena y Ana", "Luis y Hugo"],
                            "detalles_especificos": "Organización básica"
                        }
                    ]
                },
                {
                    "nombre": "Ejecución",
                    "descripcion": "Desarrollo del proyecto",
                    "tareas": [
                        {
                            "nombre": "Desarrollo principal",
                            "descripcion": "Ejecutar el proyecto principal",
                            "parejas_asignadas": ["María y Emma", "Alex y Sara"],
                            "detalles_especificos": "Desarrollo del proyecto"
                        }
                    ]
                }
            ],
            "adaptaciones": {
                "TEA": ["Proporcionar estructura clara", "Usar apoyos visuales"],
                "TDAH": ["Permitir descansos frecuentes", "Fragmentar tareas"],
                "altas_capacidades": ["Ofrecer retos adicionales", "Fomentar autonomía"]
            },
            "metadatos": {
                "tipo": "fallback",
                "motivo": "Error en generación principal"
            }
        }
    
    def _analyze_feedback_intent(self, feedback: str) -> Dict[str, Any]:
        """
        Analiza dinámicamente qué está pidiendo el feedback
        
        Args:
            feedback: Feedback del profesor
            
        Returns:
            Análisis estructurado del feedback
        """
        import re
        feedback_lower = feedback.lower()
        
        analysis = {
            'summary': [],
            'tipo_cambio': [],
            'elementos_mencionados': [],
            'requiere_cambio_agrupacion': False
        }
        
        # Detectar tipos de peticiones
        if any(word in feedback_lower for word in ['no entiendo', 'no está claro', 'confuso', 'no comprendo']):
            analysis['summary'].append("El profesor necesita mayor claridad")
            analysis['tipo_cambio'].append('clarificacion')
        
        if any(word in feedback_lower for word in ['mecánica', 'dinámica', 'cómo funciona', 'en qué consiste']):
            analysis['summary'].append("Se requiere explicar mejor la mecánica/funcionamiento")
            analysis['tipo_cambio'].append('explicar_mecanica')
        
        if any(word in feedback_lower for word in ['juego', 'reglas', 'objetivo del juego', 'ganar', 'puntos']):
            analysis['summary'].append("Falta definir reglas o estructura del juego")
            analysis['tipo_cambio'].append('definir_juego')
        
        if any(word in feedback_lower for word in ['equipos', 'grupos', 'parejas', 'individual']):
            analysis['summary'].append("Hay mención de modo de trabajo")
            analysis['tipo_cambio'].append('modo_agrupacion')
            analysis['requiere_cambio_agrupacion'] = True
        
        if any(word in feedback_lower for word in ['materiales', 'recursos', 'necesito', 'qué usar']):
            analysis['summary'].append("Se requiere especificar materiales")
            analysis['tipo_cambio'].append('materiales')
        
        if any(word in feedback_lower for word in ['tiempo', 'duración', 'cuánto dura', 'más tiempo', 'menos tiempo']):
            analysis['summary'].append("Se requiere ajustar duración")
            analysis['tipo_cambio'].append('duracion')
        
        # Análisis de preguntas específicas
        questions = re.findall(r'¿([^?]+)\?', feedback)
        if questions:
            analysis['summary'].append(f"El profesor hace {len(questions)} preguntas específicas")
            analysis['elementos_mencionados'].extend(questions)
        
        # Si no se detectó ningún tipo específico, es feedback general
        if not analysis['tipo_cambio']:
            analysis['tipo_cambio'].append('general')
            analysis['summary'].append("Feedback general para mejorar la actividad")
        
        logger.info(f"📊 Análisis de feedback: {analysis['tipo_cambio']}")
        return analysis
    
    def _generate_specific_instructions(self, feedback_analysis: Dict[str, Any]) -> str:
        """
        Genera instrucciones específicas basadas en el análisis del feedback
        
        Args:
            feedback_analysis: Análisis del feedback
            
        Returns:
            Instrucciones específicas para el LLM
        """
        instructions = []
        
        for tipo in feedback_analysis['tipo_cambio']:
            if tipo == 'clarificacion':
                instructions.append("- Explica con más detalle los aspectos que no están claros")
                instructions.append("- Usa lenguaje simple y directo")
            
            elif tipo == 'explicar_mecanica':
                instructions.append("- Describe paso a paso cómo funciona la actividad")
                instructions.append("- Incluye: inicio, desarrollo, finalización")
                instructions.append("- Especifica qué hace cada participante en cada momento")
            
            elif tipo == 'definir_juego':
                instructions.append("- Define las reglas del juego claramente")
                instructions.append("- Especifica: objetivo del juego, cómo se juega, turnos (si aplica)")
                instructions.append("- Explica cómo se determina el ganador o cómo se completa")
                instructions.append("- Incluye ejemplos concretos de jugadas o situaciones")
            
            elif tipo == 'modo_agrupacion':
                instructions.append("- Revisa y corrige el modo de agrupación mencionado")
                instructions.append("- Asegura coherencia entre descripción y asignaciones")
                instructions.append("- Si dice 'equipos/grupos', las asignaciones deben ser grupos")
            
            elif tipo == 'materiales':
                instructions.append("- Lista TODOS los materiales necesarios")
                instructions.append("- Especifica cantidades exactas")
                instructions.append("- Incluye materiales alternativos si es posible")
            
            elif tipo == 'duracion':
                instructions.append("- Ajusta la duración según lo solicitado")
                instructions.append("- Redistribuye el tiempo entre las fases si es necesario")
        
        # Si hay preguntas específicas
        if feedback_analysis['elementos_mencionados']:
            instructions.append("\nRESPONDE ESPECÍFICAMENTE estas preguntas:")
            for pregunta in feedback_analysis['elementos_mencionados']:
                instructions.append(f"- ¿{pregunta}?")
        
        return '\n'.join(instructions)
    
    def _update_grouping_from_feedback(self, feedback: str) -> None:
        """
        Actualiza la información de agrupación basándose en el feedback
        
        Args:
            feedback: Feedback del profesor
        """
        feedback_lower = feedback.lower()
        import re
        
        # Detectar cambios en agrupación
        if 'equipos' in feedback_lower or 'grupos' in feedback_lower:
            # Buscar tamaño específico
            size_match = re.search(r'grupos?\s+de\s+(\d+)', feedback_lower)
            group_size = int(size_match.group(1)) if size_match else 4
            
            # Actualizar para fase mencionada o general
            if 'ejecución' in feedback_lower or 'ejecucion' in feedback_lower:
                self.last_grouping_info['ejecucion'] = {'modo': 'grupos', 'tamaño': group_size}
            elif 'preparación' in feedback_lower or 'preparacion' in feedback_lower:
                self.last_grouping_info['preparacion'] = {'modo': 'grupos', 'tamaño': group_size}
            else:
                # Aplicar a ambas fases si no se especifica
                self.last_grouping_info['general'] = {'modo': 'grupos', 'tamaño': group_size}
                self.last_grouping_info['ejecucion'] = {'modo': 'grupos', 'tamaño': group_size}
                self.last_grouping_info['preparacion'] = {'modo': 'grupos', 'tamaño': group_size}
        
        elif any(pattern in feedback_lower for pattern in [
            'individual', 'cada uno', 'cada uno prepare', 'por separado', 
            'cada cual', 'por su cuenta', 'independientemente'
        ]):
            if 'ejecución' in feedback_lower or 'ejecucion' in feedback_lower:
                self.last_grouping_info['ejecucion'] = {'modo': 'individual', 'tamaño': 1}
            elif 'preparación' in feedback_lower or 'preparacion' in feedback_lower:
                self.last_grouping_info['preparacion'] = {'modo': 'individual', 'tamaño': 1}
            else:
                # Si no especifica fase, aplicar a ambas
                self.last_grouping_info['general'] = {'modo': 'individual', 'tamaño': 1}
                self.last_grouping_info['preparacion'] = {'modo': 'individual', 'tamaño': 1}
                self.last_grouping_info['ejecucion'] = {'modo': 'individual', 'tamaño': 1}
        
        elif 'parejas' in feedback_lower:
            if 'ejecución' in feedback_lower or 'ejecucion' in feedback_lower:
                self.last_grouping_info['ejecucion'] = {'modo': 'parejas', 'tamaño': 2}
            elif 'preparación' in feedback_lower or 'preparacion' in feedback_lower:
                self.last_grouping_info['preparacion'] = {'modo': 'parejas', 'tamaño': 2}
        
        logger.info(f"📊 Grouping info actualizado: {self.last_grouping_info}")
    
    def refine_activity(self, current_activity: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refina actividad con análisis inteligente y validación
        
        Args:
            current_activity: Actividad actual
            feedback: Feedback del profesor
            
        Returns:
            Actividad refinada y validada
        """
        logger.info(f"🔄 Refinando actividad basándose en feedback")
        
        try:
            # 1. Analizar el feedback
            feedback_analysis = self._analyze_feedback_intent(feedback)
            
            # 2. Actualizar grouping_info si es necesario
            if feedback_analysis['requiere_cambio_agrupacion']:
                self._update_grouping_from_feedback(feedback)
            
            # 3. Crear prompt mejorado
            refinement_prompt = self._create_refinement_prompt_v2(
                current_activity, 
                feedback,
                feedback_analysis
            )
            
            # 4. Generar refinamiento con LLM
            response = self.ollama.generar_respuesta(
                refinement_prompt,
                max_tokens=1500,
                temperatura=0.6
            )
            
            # 5. Procesar respuesta
            refined_activity = self._process_refinement_response(response, current_activity, feedback)
            
            # 6. Validar y corregir inconsistencias
            refined_activity = self._validate_and_fix_activity(refined_activity, feedback_analysis)
            
            # 7. Añadir metadatos de refinamiento
            if 'historial_refinamientos' not in refined_activity:
                refined_activity['historial_refinamientos'] = []
            
            refined_activity['historial_refinamientos'].append({
                'timestamp': datetime.now().isoformat(),
                'feedback': feedback,
                'analisis': feedback_analysis['summary'],
                'cambios_aplicados': 'Refinamiento con análisis inteligente y validación'
            })
            
            logger.info(f"✅ Actividad refinada y validada exitosamente")
            return refined_activity
            
        except Exception as e:
            logger.error(f"❌ Error refinando actividad: {e}")
            return current_activity
    
    def _create_refinement_prompt_v2(self, current_activity: Dict[str, Any], 
                                    feedback: str, feedback_analysis: Dict[str, Any]) -> str:
        """
        Crea prompt mejorado para refinamiento con análisis dinámico
        
        Args:
            current_activity: Actividad actual
            feedback: Feedback del profesor
            feedback_analysis: Análisis del feedback
            
        Returns:
            Prompt de refinamiento mejorado
        """
        # Convertir actividad actual a texto legible
        activity_summary = self._activity_to_text(current_activity)
        
        # Información de estudiantes
        estudiantes_info = self._create_students_context()
        
        # Generar instrucciones específicas
        specific_instructions = self._generate_specific_instructions(feedback_analysis)
        
        # Información de agrupación si es relevante
        grouping_context = ""
        modo_prep = 'parejas'  # Default
        modo_ejec = 'parejas'  # Default
        
        if self.last_grouping_info:
            modo_prep = self.last_grouping_info['preparacion']['modo']
            modo_ejec = self.last_grouping_info['ejecucion']['modo']
            
            if 'modo_agrupacion' in feedback_analysis['tipo_cambio']:
                grouping_context = f"""
INFORMACIÓN DE AGRUPACIÓN ACTUALIZADA:
- Preparación: {self.last_grouping_info['preparacion']['modo']} (tamaño: {self.last_grouping_info['preparacion']['tamaño']})
- Ejecución: {self.last_grouping_info['ejecucion']['modo']} (tamaño: {self.last_grouping_info['ejecucion']['tamaño']})
"""
        
        prompt = f"""TAREA: Mejorar la actividad basándote ESPECÍFICAMENTE en el feedback del profesor.

ACTIVIDAD ACTUAL:
{activity_summary}

FEEDBACK DEL PROFESOR:
"{feedback}"

ANÁLISIS DEL FEEDBACK:
{'. '.join(feedback_analysis['summary'])}

CAMBIOS REQUERIDOS:
{specific_instructions}

ESTUDIANTES DEL AULA:
{estudiantes_info}
{grouping_context}

INSTRUCCIONES CRÍTICAS:
1. MANTÉN todo lo que NO se menciona en el feedback
2. MODIFICA SOLO los aspectos mencionados en el feedback
3. Si el feedback pide clarificación, AÑADE detalles sin eliminar lo existente
4. Si el feedback señala inconsistencias, CORRIGE manteniendo coherencia
5. Las asignaciones deben coincidir con el modo de agrupación declarado

RESPONDE con la actividad mejorada en formato JSON manteniendo la estructura original:
{{
  "titulo": "Título (modificar solo si el feedback lo solicita)",
  "objetivo": "Objetivo (modificar solo si el feedback lo solicita)",
  "duracion": "Duración (modificar solo si el feedback lo solicita)",
  "fases": [
    {{
      "nombre": "Preparación",
      "descripcion": "Descripción mejorada según feedback",
      "modo_agrupacion": "{modo_prep}",
      "tareas": [
        {{
          "nombre": "Tarea específica",
          "descripcion": "Descripción detallada y mejorada",
          "detalles_especificos": "Detalles concretos mejorados"
        }}
      ]
    }},
    {{
      "nombre": "Ejecución", 
      "descripcion": "Descripción mejorada según feedback",
      "modo_agrupacion": "{modo_ejec}",
      "tareas": [
        {{
          "nombre": "Tarea de ejecución",
          "descripcion": "Descripción mejorada",
          "detalles_especificos": "Detalles específicos"
        }}
      ]
    }}
  ],
  "adaptaciones": {{
    "TEA": "Adaptaciones para TEA mejoradas según feedback",
    "TDAH": "Adaptaciones para TDAH mejoradas según feedback",
    "altas_capacidades": "Desafíos para altas capacidades mejorados según feedback"
  }},
  "mejoras_aplicadas": "Resumen específico de qué cambios se hicieron basados en el feedback"
}}"""

        return prompt
    
    def _validate_and_fix_activity(self, activity: Dict[str, Any], 
                                  feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y corrige inconsistencias en la actividad refinada
        
        Args:
            activity: Actividad a validar
            feedback_analysis: Análisis del feedback para contexto
            
        Returns:
            Actividad validada y corregida
        """
        issues_found = []
        
        # Validar cada fase
        for fase in activity.get('fases', []):
            fase_nombre = fase.get('nombre', '').lower()
            modo_declarado = fase.get('modo_agrupacion', '')
            
            # Determinar modo esperado según grouping_info
            if self.last_grouping_info:
                if 'preparación' in fase_nombre or 'preparacion' in fase_nombre:
                    modo_esperado = self.last_grouping_info['preparacion']['modo']
                    tamaño_esperado = self.last_grouping_info['preparacion']['tamaño']
                elif 'ejecución' in fase_nombre or 'ejecucion' in fase_nombre:
                    modo_esperado = self.last_grouping_info['ejecucion']['modo']
                    tamaño_esperado = self.last_grouping_info['ejecucion']['tamaño']
                else:
                    modo_esperado = self.last_grouping_info['general']['modo']
                    tamaño_esperado = self.last_grouping_info['general']['tamaño']
            else:
                modo_esperado = modo_declarado
                tamaño_esperado = 2  # Default
            
            # Validar coherencia del modo declarado
            if modo_declarado and modo_declarado != modo_esperado:
                logger.warning(f"⚠️ Inconsistencia: fase '{fase_nombre}' declara '{modo_declarado}' pero debería ser '{modo_esperado}'")
                fase['modo_agrupacion'] = modo_esperado
                issues_found.append(f"Modo de {fase_nombre} corregido a {modo_esperado}")
            
            # Validar y corregir asignaciones en tareas
            for tarea in fase.get('tareas', []):
                asignaciones = tarea.get('asignaciones', tarea.get('parejas_asignadas', []))
                
                if asignaciones:
                    # Detectar modo real de las asignaciones
                    modo_real = self._detect_assignment_mode(asignaciones)
                    
                    # Si hay inconsistencia, corregir
                    if modo_real != modo_esperado:
                        logger.warning(f"⚠️ Asignaciones inconsistentes en '{tarea.get('nombre', 'tarea')}': modo real '{modo_real}' vs esperado '{modo_esperado}'")
                        
                        # Regenerar asignaciones correctas
                        from mvp.profile_manager import ProfileManager
                        pm = ProfileManager()
                        nuevas_asignaciones = pm.create_optimal_groupings(modo_esperado, tamaño_esperado)
                        
                        # Formatear según el modo
                        if modo_esperado == 'individual':
                            tarea['asignaciones'] = [est[0] for est in nuevas_asignaciones]
                        elif modo_esperado == 'parejas':
                            tarea['asignaciones'] = [f"{pareja[0]} y {pareja[1]}" for pareja in nuevas_asignaciones]
                        elif modo_esperado == 'grupos':
                            tarea['asignaciones'] = [f"Grupo {i+1}: {', '.join(grupo)}" 
                                                   for i, grupo in enumerate(nuevas_asignaciones)]
                        
                        # Mantener compatibilidad
                        tarea['parejas_asignadas'] = tarea['asignaciones']
                        issues_found.append(f"Asignaciones de '{tarea.get('nombre', 'tarea')}' corregidas a {modo_esperado}")
        
        # Log de correcciones
        if issues_found:
            logger.info(f"✅ Corregidas {len(issues_found)} inconsistencias: {', '.join(issues_found)}")
            
            # Guardar para aprender
            self.common_issues.extend(issues_found)
            
            # Añadir a metadatos
            if 'validacion' not in activity:
                activity['validacion'] = {}
            activity['validacion']['correcciones_aplicadas'] = issues_found
            activity['validacion']['timestamp'] = datetime.now().isoformat()
        
        return activity
    
    def _detect_assignment_mode(self, asignaciones: List[str]) -> str:
        """
        Detecta el modo real de las asignaciones
        
        Args:
            asignaciones: Lista de asignaciones
            
        Returns:
            Modo detectado ('individual', 'parejas', 'grupos')
        """
        if not asignaciones:
            return 'desconocido'
        
        # Analizar primera asignación
        primera = str(asignaciones[0])
        
        # Individual: no tiene conectores
        if ' y ' not in primera and ',' not in primera and 'Grupo' not in primera:
            return 'individual'
        
        # Parejas: tiene " y " pero no comas
        elif ' y ' in primera and ',' not in primera:
            return 'parejas'
        
        # Grupos: tiene "Grupo" o múltiples comas
        elif 'Grupo' in primera or primera.count(',') >= 2:
            return 'grupos'
        
        # Por defecto
        return 'parejas'
    
    def _activity_to_text(self, activity: Dict[str, Any]) -> str:
        """
        Convierte actividad a formato texto legible
        
        Args:
            activity: Actividad en formato dict
            
        Returns:
            Actividad en formato texto
        """
        text_parts = []
        
        text_parts.append(f"TÍTULO: {activity.get('titulo', 'Sin título')}")
        text_parts.append(f"OBJETIVO: {activity.get('objetivo', 'Sin objetivo')}")
        text_parts.append(f"DURACIÓN: {activity.get('duracion', 'No especificada')}")
        
        fases = activity.get('fases', [])
        for i, fase in enumerate(fases, 1):
            text_parts.append(f"\nFASE {i}: {fase.get('nombre', 'Sin nombre')}")
            text_parts.append(f"Descripción: {fase.get('descripcion', 'Sin descripción')}")
            
            tareas = fase.get('tareas', [])
            for j, tarea in enumerate(tareas, 1):
                text_parts.append(f"\n  Tarea {j}: {tarea.get('nombre', 'Sin nombre')}")
                text_parts.append(f"  Descripción: {tarea.get('descripcion', 'Sin descripción')}")
                
                parejas = tarea.get('parejas_asignadas', [])
                if parejas:
                    text_parts.append(f"  Parejas: {', '.join(parejas)}")
                
                detalles = tarea.get('detalles_especificos', '')
                if detalles:
                    text_parts.append(f"  Detalles: {detalles}")
        
        adaptaciones = activity.get('adaptaciones', {})
        if adaptaciones:
            text_parts.append(f"\nADAPTACIONES:")
            for neurotipo, lista_adaptaciones in adaptaciones.items():
                if lista_adaptaciones:
                    text_parts.append(f"  {neurotipo}: {', '.join(lista_adaptaciones)}")
        
        return "\n".join(text_parts)
    
    def _process_refinement_response(self, response: str, original_activity: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Procesa respuesta de refinamiento del LLM
        
        Args:
            response: Respuesta del LLM
            original_activity: Actividad original
            feedback: Feedback original
            
        Returns:
            Actividad refinada
        """
        try:
            # Intentar extraer JSON de la respuesta
            json_match = self._extract_json_from_response(response)
            if json_match:
                refined_activity = json.loads(json_match)
                
                # Asegurar que mantiene estructura básica
                if 'titulo' in refined_activity and 'fases' in refined_activity:
                    logger.info("✅ Refinamiento JSON válido")
                    return refined_activity
            
            # Si no hay JSON válido, devolver original con nota
            logger.warning("⚠️ JSON inválido en refinamiento, devolviendo actividad original")
            refined = original_activity.copy()
            refined['refinamiento_fallido'] = {
                'feedback_original': feedback,
                'respuesta_llm': response[:300],  # Primeros 300 chars
                'timestamp': datetime.now().isoformat(),
                'motivo': 'JSON inválido en respuesta del LLM'
            }
            return refined
            
        except Exception as e:
            logger.error(f"❌ Error procesando refinamiento: {e}")
            return original_activity
    

    def save_activity(self, activity: Dict[str, Any], filename: str = None) -> str:
        """
        Guarda actividad en archivo JSON
        
        Args:
            activity: Actividad a guardar
            filename: Nombre de archivo (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"abp_simplified_{timestamp}.json"
            
            # Asegurar directorio temp
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            temp_dir = os.path.join(base_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(activity, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Actividad guardada en: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error guardando actividad: {e}")
            return ""