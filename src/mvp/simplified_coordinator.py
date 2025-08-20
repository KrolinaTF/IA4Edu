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
        
        # Gestor de embeddings para ejemplos
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        proyecto_root = os.path.dirname(base_dir)
        actividades_path = os.path.join(proyecto_root, "data", "actividades")
        self.embeddings_manager = EmbeddingsManager(actividades_path, self.ollama)
        
        # Cargar perfiles de estudiantes
        self.student_profiles = self._load_student_profiles()
        
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
            # 1. Buscar ejemplos relevantes
            ejemplos_relevantes = self._find_relevant_examples(user_request)
            
            # 2. Crear prompt directo (sin plantilla compleja)
            prompt_directo = self._create_direct_prompt(
                user_request, 
                ejemplos_relevantes, 
                additional_details
            )
            
            # 3. Generar con LLM
            response = self.ollama.generar_respuesta(
                prompt_directo, 
                max_tokens=1500, 
                temperatura=0.7
            )
            
            # 4. Procesar respuesta y crear estructura final
            activity_result = self._process_llm_response(response, user_request)
            
            # 5. Crear asignaciones específicas para los 8 estudiantes
            activity_result = self._assign_students_to_tasks(activity_result)
            
            # 6. Añadir metadatos
            activity_result['metadatos'] = {
                'timestamp': datetime.now().isoformat(),
                'sistema': 'SimplifiedCoordinator',
                'version': '1.0',
                'prompt_original': user_request,
                'ejemplos_utilizados': [ej[0] for ej in ejemplos_relevantes]
            }
            
            logger.info(f"✅ Actividad generada exitosamente")
            return activity_result
            
        except Exception as e:
            logger.error(f"❌ Error generando actividad: {e}")
            return self._create_fallback_activity(user_request)
    
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
                            additional_details: str) -> str:
        """
        Crea prompt directo para el LLM (sin plantilla compleja)
        
        Args:
            user_request: Solicitud del usuario
            ejemplos: Ejemplos relevantes encontrados
            additional_details: Detalles adicionales
            
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
        
        # Prompt directo sin instrucciones complejas
        prompt = f"""Crea una actividad educativa ABP (Aprendizaje Basado en Proyectos) para 4º de Primaria.

SOLICITUD DEL PROFESOR:
{user_request}

{f"DETALLES ADICIONALES: {additional_details}" if additional_details else ""}

{contexto_ejemplos}

ESTUDIANTES DEL AULA (8 estudiantes):
{estudiantes_info}

INSTRUCCIONES:
1. Crea una actividad concreta y específica basada en la solicitud
2. Divide en 2 fases: Preparación y Ejecución
3. Cada fase debe tener tareas específicas para parejas de estudiantes
4. Incluye adaptaciones para TEA, TDAH y altas capacidades
5. Sé específico: si pides rutas geográficas, nombra lugares reales
6. Si pides roles, define roles concretos (no genéricos)

RESPONDE EN FORMATO JSON:
{{
  "titulo": "Título específico de la actividad",
  "objetivo": "Objetivo educativo claro",
  "duracion": "2 sesiones de 45 minutos",
  "fases": [
    {{
      "nombre": "Preparación",
      "descripcion": "Descripción específica de qué se hace",
      "tareas": [
        {{
          "nombre": "Tarea específica 1",
          "descripcion": "Descripción detallada y concreta",
          "parejas_asignadas": ["Pareja 1: Elena y Ana", "Pareja 2: Luis y Hugo"],
          "detalles_especificos": "Detalles concretos (lugares, roles, materiales específicos)"
        }}
      ]
    }},
    {{
      "nombre": "Ejecución",
      "descripcion": "Descripción específica de la fase principal",
      "tareas": [
        {{
          "nombre": "Tarea específica 2",
          "descripcion": "Descripción detallada y concreta",
          "parejas_asignadas": ["Pareja 3: María y Emma", "Pareja 4: Alex y Sara"],
          "detalles_especificos": "Detalles concretos y específicos"
        }}
      ]
    }}
  ],
  "adaptaciones": {{
    "TEA": ["Adaptación específica 1", "Adaptación específica 2"],
    "TDAH": ["Adaptación específica 1", "Adaptación específica 2"],
    "altas_capacidades": ["Desafío específico 1", "Desafío específico 2"]
  }}
}}"""

        return prompt
    
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
        Procesa respuesta del LLM y crea estructura
        
        Args:
            response: Respuesta cruda del LLM
            user_request: Solicitud original del usuario
            
        Returns:
            Estructura procesada de la actividad
        """
        try:
            # Intentar extraer JSON
            json_match = self._extract_json_from_response(response)
            if json_match:
                activity = json.loads(json_match)
                logger.info("✅ JSON extraído y parseado correctamente")
                return activity
            else:
                logger.warning("⚠️ No se pudo extraer JSON, creando estructura desde texto")
                return self._create_structure_from_text(response, user_request)
                
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta: {e}")
            return self._create_fallback_activity(user_request)
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """
        Extrae JSON de la respuesta del LLM
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            JSON extraído o None
        """
        import re
        
        # Buscar JSON entre llaves
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            return match.group(0)
        
        return None
    
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
    
    def _assign_students_to_tasks(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asigna estudiantes específicos a tareas (usando perfiles reales)
        
        Args:
            activity: Actividad generada
            
        Returns:
            Actividad con asignaciones específicas
        """
        if not self.student_profiles.get('estudiantes'):
            return activity
        
        estudiantes = self.student_profiles['estudiantes']
        
        # Crear parejas optimizadas
        parejas = self._create_optimal_pairs(estudiantes)
        
        # Asignar parejas a fases
        activity['asignaciones_estudiantes'] = {}
        
        for i, fase in enumerate(activity.get('fases', [])):
            for j, tarea in enumerate(fase.get('tareas', [])):
                # Asignar parejas disponibles
                parejas_asignadas = []
                
                if i == 0:  # Preparación
                    if j < len(parejas):
                        pareja = parejas[j]
                        parejas_asignadas.append(f"{pareja[0]['nombre']} y {pareja[1]['nombre']}")
                else:  # Ejecución
                    if j + 2 < len(parejas):
                        pareja = parejas[j + 2]
                        parejas_asignadas.append(f"{pareja[0]['nombre']} y {pareja[1]['nombre']}")
                
                tarea['parejas_asignadas'] = parejas_asignadas
        
        return activity
    
    def _create_optimal_pairs(self, estudiantes: List[Dict]) -> List[tuple]:
        """
        Crea parejas optimizadas considerando neurotipos
        
        Args:
            estudiantes: Lista de estudiantes
            
        Returns:
            Lista de parejas optimizadas
        """
        parejas = []
        estudiantes_disponibles = estudiantes.copy()
        
        # Estrategia: emparejar estudiantes con necesidades especiales con típicos
        tea_estudiantes = [e for e in estudiantes_disponibles if 'TEA' in e.get('diagnostico_formal', '')]
        tdah_estudiantes = [e for e in estudiantes_disponibles if 'TDAH' in e.get('diagnostico_formal', '')]
        altas_cap_estudiantes = [e for e in estudiantes_disponibles if 'altas_capacidades' in e.get('diagnostico_formal', '')]
        tipicos = [e for e in estudiantes_disponibles if e.get('diagnostico_formal', 'ninguno') == 'ninguno']
        
        # Emparejar TEA con típicos de alta tolerancia a frustración
        for tea_est in tea_estudiantes:
            compañero = None
            for tipico in tipicos:
                if tipico.get('tolerancia_frustracion') == 'alta':
                    compañero = tipico
                    break
            
            if compañero:
                parejas.append((tea_est, compañero))
                tipicos.remove(compañero)
                estudiantes_disponibles.remove(tea_est)
                estudiantes_disponibles.remove(compañero)
        
        # Emparejar TDAH con estudiantes que toleren dinamismo
        for tdah_est in tdah_estudiantes:
            compañero = None
            for tipico in tipicos:
                parejas.append((tdah_est, tipico))
                tipicos.remove(tipico)
                estudiantes_disponibles.remove(tdah_est)
                estudiantes_disponibles.remove(tipico)
                break
        
        # Emparejar altas capacidades con estudiantes colaborativos
        for ac_est in altas_cap_estudiantes:
            compañero = None
            for est in estudiantes_disponibles:
                if est != ac_est:
                    parejas.append((ac_est, est))
                    estudiantes_disponibles.remove(ac_est)
                    estudiantes_disponibles.remove(est)
                    break
        
        # Emparejar resto
        while len(estudiantes_disponibles) >= 2:
            est1 = estudiantes_disponibles.pop(0)
            est2 = estudiantes_disponibles.pop(0)
            parejas.append((est1, est2))
        
        return parejas
    
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
    
    def refine_activity(self, current_activity: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refina actividad existente basándose en feedback del profesor
        
        Args:
            current_activity: Actividad actual
            feedback: Feedback del profesor
            
        Returns:
            Actividad refinada
        """
        logger.info(f"🔄 Refinando actividad basándose en feedback")
        
        try:
            # Crear prompt de refinamiento
            refinement_prompt = self._create_refinement_prompt(current_activity, feedback)
            
            # Generar refinamiento con LLM
            response = self.ollama.generar_respuesta(
                refinement_prompt,
                max_tokens=1500,
                temperatura=0.6  # Menos creatividad, más precisión
            )
            
            # Procesar respuesta
            refined_activity = self._process_refinement_response(response, current_activity, feedback)
            
            # Añadir metadatos de refinamiento
            if 'historial_refinamientos' not in refined_activity:
                refined_activity['historial_refinamientos'] = []
            
            refined_activity['historial_refinamientos'].append({
                'timestamp': datetime.now().isoformat(),
                'feedback': feedback,
                'cambios_aplicados': 'Refinamiento basado en feedback del profesor'
            })
            
            logger.info(f"✅ Actividad refinada exitosamente")
            return refined_activity
            
        except Exception as e:
            logger.error(f"❌ Error refinando actividad: {e}")
            # Devolver actividad original si falla el refinamiento
            return current_activity
    
    def _create_refinement_prompt(self, current_activity: Dict[str, Any], feedback: str) -> str:
        """
        Crea prompt para refinamiento basado en feedback
        
        Args:
            current_activity: Actividad actual
            feedback: Feedback del profesor
            
        Returns:
            Prompt de refinamiento
        """
        # Convertir actividad actual a texto legible
        activity_summary = self._activity_to_text(current_activity)
        
        # Información de estudiantes
        estudiantes_info = self._create_students_context()
        
        prompt = f"""Mejora la siguiente actividad ABP basándote en el feedback específico del profesor.

ACTIVIDAD ACTUAL:
{activity_summary}

FEEDBACK DEL PROFESOR:
{feedback}

ESTUDIANTES DEL AULA:
{estudiantes_info}

INSTRUCCIONES:
1. Mantén lo que está funcionando bien
2. Aplica ESPECÍFICAMENTE los cambios sugeridos en el feedback
3. Conserva la estructura JSON original
4. Mejora solo los aspectos mencionados en el feedback
5. Sé específico y concreto en los cambios

RESPONDE CON LA ACTIVIDAD MEJORADA EN FORMATO JSON:
{{
  "titulo": "Título mejorado si es necesario",
  "objetivo": "Objetivo refinado",
  "duracion": "Duración ajustada si es necesario", 
  "fases": [
    {{
      "nombre": "Fase mejorada",
      "descripcion": "Descripción refinada",
      "tareas": [
        {{
          "nombre": "Tarea específica mejorada",
          "descripcion": "Descripción más detallada según feedback",
          "parejas_asignadas": ["Mantener asignaciones o mejorarlas"],
          "detalles_especificos": "Detalles específicos mejorados según feedback"
        }}
      ]
    }}
  ],
  "adaptaciones": {{
    "TEA": ["Adaptaciones mejoradas"],
    "TDAH": ["Adaptaciones mejoradas"], 
    "altas_capacidades": ["Desafíos mejorados"]
  }},
  "mejoras_aplicadas": "Resumen de cambios realizados basados en feedback"
}}"""

        return prompt
    
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
            
            # Si no hay JSON válido, hacer refinamiento manual
            logger.warning("⚠️ JSON inválido en refinamiento, aplicando cambios manuales")
            return self._manual_refinement(original_activity, feedback, response)
            
        except Exception as e:
            logger.error(f"❌ Error procesando refinamiento: {e}")
            return original_activity
    
    def _manual_refinement(self, original_activity: Dict[str, Any], feedback: str, llm_response: str) -> Dict[str, Any]:
        """
        Aplica refinamiento manual cuando el JSON no es válido
        
        Args:
            original_activity: Actividad original
            feedback: Feedback del profesor
            llm_response: Respuesta del LLM
            
        Returns:
            Actividad con refinamientos manuales
        """
        refined = original_activity.copy()
        
        # Añadir información del refinamiento
        refined['refinamiento_manual'] = {
            'feedback_original': feedback,
            'respuesta_llm': llm_response[:500],  # Primeros 500 chars
            'timestamp': datetime.now().isoformat()
        }
        
        # Modificaciones básicas basadas en keywords en feedback
        feedback_lower = feedback.lower()
        
        if 'título' in feedback_lower or 'titulo' in feedback_lower:
            refined['titulo'] = f"{original_activity.get('titulo', '')} - Refinado"
        
        if 'tiempo' in feedback_lower or 'duración' in feedback_lower:
            if 'más' in feedback_lower:
                refined['duracion'] = "3 sesiones de 45 minutos"
            elif 'menos' in feedback_lower:
                refined['duracion'] = "1 sesión de 45 minutos"
        
        return refined

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