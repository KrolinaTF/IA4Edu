#!/usr/bin/env python3
"""
Workflows del Sistema de Agentes Inteligente
- Flujo principal de generación de actividades
- Human-in-the-loop inteligente
- Coordinación de agentes
- Validaciones y refinamientos
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from crewai import Task, Crew, Process

from config import configure_environment, setup_logging, validate_dependencies
from agents_and_tasks import AgentesCrewAI, TemplatesTareas
from services import CargadorEjemplosK, MotorParalelismo, ActividadEducativa, AnalizadorMateriales

logger = logging.getLogger("AgentesInteligente")

class SistemaAgentesInteligente:
    """Sistema principal con CrewAI + Ollama + Few-shot estratégico + Human-in-the-loop"""
    
    def __init__(self, ollama_host: str = "192.168.1.10"):
        # Configurar entorno
        configure_environment(ollama_host)
        validate_dependencies()
        
        self.ollama_host = ollama_host
        
        # Inicializar servicios
        self.cargador_ejemplos = CargadorEjemplosK()
        
        # Inicializar agentes
        self.agentes = AgentesCrewAI(ollama_host)
        
        # Inicializar motor de paralelismo
        self.motor_paralelismo = MotorParalelismo(self.agentes.agente_coordinador_paralelismo)
        self.motor_paralelismo.ejemplos_k = self.cargador_ejemplos.ejemplos_k
        
        # Templates de tareas
        self.templates = TemplatesTareas()
        
        logger.info("✅ Sistema de Agentes Inteligente inicializado")
    
    def generar_actividad_completa(self, prompt_profesor: str) -> ActividadEducativa:
        """Flujo principal de generación de actividad completa"""
        
        print("🤖 Sistema de Agentes Inteligente")
        print("CrewAI + Ollama + Few-shot estratégico + Human-in-the-loop")
        print("="*70)
        
        try:
            # FASE 0: Validación de contexto general
            contexto_validado = self._validar_contexto_general(prompt_profesor)
            
            # FASE 1: Opciones específicas
            opciones_decididas = self._fase_opciones_dinamicas(contexto_validado)
            
            # FASE 2: Estructura libre
            estructura_definida = self._fase_estructura_libre(opciones_decididas, contexto_validado)
            
            # FASE 3: Actividad final iterativa
            actividad_final = self._crear_actividad_final_iterativa(estructura_definida, contexto_validado)
            
            return actividad_final
            
        except KeyboardInterrupt:
            print("\n👋 Proceso interrumpido por el usuario")
            return None
        except Exception as e:
            logger.error(f"Error en generación: {e}")
            print(f"❌ Error generando actividad: {e}")
            return None
    
    def _validar_contexto_general(self, prompt_profesor: str) -> Dict[str, Any]:
        """Validación de contexto general con human-in-the-loop"""
        
        print(f"\n✅ VALIDACIÓN PREVIA: CONTEXTO GENERAL")
        print("="*60)
        
        # Detectar contexto usando agente inteligente
        contexto_detectado = self.detectar_contexto_multidimensional(prompt_profesor)
        
        # Extraer y mostrar análisis
        try:
            import json
            # Convertir a string y buscar JSON
            contexto_str = str(contexto_detectado).encode('utf-8', errors='ignore').decode('utf-8')
            json_match = re.search(r'```json\\s*(\\{.*?\\})\\s*```', contexto_str, re.DOTALL | re.MULTILINE)
            
            if json_match:
                analisis = json.loads(json_match.group(1))
            else:
                # Fallback simple
                analisis = {
                    "contexto_base": {"materia": "detectado", "tema": "detectado"},
                    "recomendacion_ia": "Basado en tu descripción, te ayudo a crear una actividad específica."
                }
        except:
            analisis = {
                "contexto_base": {"materia": "general", "tema": "personalizado"},
                "recomendacion_ia": "Hubo un error analizando tu descripción."
            }
        
        # Mostrar contexto detectado
        print(f"\\n📋 CONTEXTO DETECTADO:")
        if "contexto_base" in analisis:
            base = analisis["contexto_base"]
            print(f"   📚 Materia: {base.get('materia', 'no detectado')}")
            print(f"   🎯 Tema: {base.get('tema', 'no detectado')}")
            print(f"   📈 Complejidad: {base.get('complejidad_conceptual', 'no detectado')}")
        
        # Mostrar recomendación de la IA
        if "recomendacion_ia" in analisis:
            print(f"\\n🤖 RECOMENDACIÓN GENERAL: {analisis['recomendacion_ia']}")
        
        # Validación del contexto general
        print(f"\\n🤔 ¿Este enfoque general te parece correcto?")
        print(f"   (Si dices 'no', podré cambiar completamente el enfoque)")
        
        respuesta = input(f"🗣️ (sí/no): ").strip().lower()
        
        if respuesta in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            print(f"\\n✅ ¡Perfecto! Continuemos con opciones específicas.")
            return analisis
        else:
            print(f"\\n🔄 ¿Qué enfoque prefieres?")
            feedback_general = input(f"🗣️ Tu respuesta: ").strip()
            
            # Re-analizar SOLO con el feedback del usuario
            contexto_refinado = self.detectar_contexto_multidimensional(feedback_general)
            
            # Mostrar el NUEVO contexto basado en el feedback
            print(f"\\n✅ NUEVO CONTEXTO BASADO EN TU FEEDBACK:")
            print("=" * 60)
            
            # Procesar contexto refinado
            try:
                contexto_str = str(contexto_refinado).encode('utf-8', errors='ignore').decode('utf-8')
                json_match = re.search(r'```json\\s*({.*?})\\s*```', contexto_str, re.DOTALL | re.MULTILINE)
                
                if json_match:
                    analisis_refinado = json.loads(json_match.group(1))
                else:
                    analisis_refinado = {
                        "contexto_base": {"materia": "personalizado", "tema": feedback_general[:50]},
                        "recomendacion_ia": f"Basado en tu feedback: {feedback_general}"
                    }
            except:
                analisis_refinado = {
                    "contexto_base": {"materia": "personalizado", "tema": feedback_general[:50]},
                    "recomendacion_ia": f"Enfoque personalizado: {feedback_general}"
                }
            
            # Mostrar el nuevo análisis
            if "contexto_base" in analisis_refinado:
                base = analisis_refinado["contexto_base"]
                print(f"   📚 Materia: {base.get('materia', 'personalizado')}")
                print(f"   🎯 Tema: {base.get('tema', feedback_general[:50])}")
                print(f"   📈 Complejidad: {base.get('complejidad_conceptual', 'según tu enfoque')}")
            
            if "recomendacion_ia" in analisis_refinado:
                print(f"\\n🤖 NUEVA RECOMENDACIÓN: {analisis_refinado['recomendacion_ia']}")
            
            # Confirmación del nuevo enfoque
            print(f"\\n🤔 ¿Este nuevo enfoque refleja mejor lo que quieres?")
            confirmacion = input(f"🗣️ (sí/no): ").strip().lower()
            
            if confirmacion in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
                print(f"\\n✅ ¡Perfecto! Continuemos con este enfoque personalizado.")
                return analisis_refinado
            else:
                print(f"\\n⚠️ Volvamos al enfoque original entonces.")
                return analisis
    
    def detectar_contexto_multidimensional(self, prompt_profesor: str) -> Dict[str, Any]:
        """Detector libre que analiza múltiples dimensiones y genera opciones dinámicas"""
        
        tarea_deteccion = self.templates.crear_tarea_deteccion_contexto(
            prompt_profesor, 
            self.agentes.agente_detector
        )
        
        crew_deteccion = Crew(
            agents=[self.agentes.agente_detector],
            tasks=[tarea_deteccion],
            process=Process.sequential,
            verbose=False  # Silencioso para no saturar
        )
        
        try:
            resultado = crew_deteccion.kickoff()
            logger.info(f"🔍 Contexto detectado exitosamente")
            return resultado
        except Exception as e:
            logger.warning(f"⚠️ Error en detección de contexto: {e}")
            return {
                "contexto_base": {"materia": "general", "tema": "actividad"},
                "recomendacion_ia": "Puedo ayudarte a crear una actividad educativa."
            }
    
    def _fase_opciones_dinamicas(self, contexto_aprobado) -> Dict[str, Any]:
        """Fase 1: Preguntas específicas sobre actividad (contexto ya validado)"""
        
        print(f"\\n🧠 FASE 1: OPCIONES ESPECÍFICAS")
        print("-" * 50)
        
        # Extraer análisis del detector
        try:
            # Convertir contexto_aprobado a string si es necesario
            contexto_str = str(contexto_aprobado)
            # Buscar JSON en el string
            json_match = re.search(r'```json\\s*(\\{.*?\\})\\s*```', contexto_str, re.DOTALL | re.MULTILINE)
            if json_match:
                analisis = json.loads(json_match.group(1))
            else:
                # Fallback si no encuentra JSON
                print(f"📝 Contexto recibido: {contexto_str[:500]}...")
                analisis = {
                    "contexto_base": {"materia": "detectado", "tema": "detectado"},
                    "opciones_dinamicas": ["¿Qué tipo de actividad prefieres?"],
                    "recomendacion_ia": "Basado en tu descripción, recomiendo una actividad práctica."
                }
        
        except Exception as e:
            logger.warning(f"Error procesando contexto: {e}")
            analisis = {
                "contexto_base": {"materia": "error", "tema": "error"},
                "opciones_dinamicas": ["¿Cómo te gustaría enfocar esta actividad?"],
                "recomendacion_ia": "Hubo un error analizando tu descripción, pero puedo ayudarte."
            }
        
        # Validación intermedia si es necesario
        if not self._validacion_humana_intermedia("OPCIONES", analisis):
            return self._refinar_opciones(contexto_aprobado, analisis)
        
        # El contexto ya fue mostrado y aprobado en la validación previa
        print(f"\\n🎯 Ahora vamos con las opciones específicas:")
        
        # Hacer preguntas dinámicas
        decisiones = {}
        opciones_dinamicas = analisis.get("opciones_dinamicas", [])
        
        for i, pregunta in enumerate(opciones_dinamicas, 1):
            print(f"\\n🤔 PREGUNTA {i}: {pregunta}")
            respuesta = input(f"🗣️ Tu respuesta: ").strip()
            decisiones[f"decision_{i}"] = respuesta
        
        # Si no hay opciones dinámicas, hacer una pregunta genérica
        if not opciones_dinamicas:
            print(f"\\n🤔 ¿Cómo te gustaría enfocar esta actividad?")
            respuesta = input(f"🗣️ Tu respuesta: ").strip()
            decisiones["enfoque_general"] = respuesta
        
        return {
            "analisis_detector": analisis,
            "decisiones_profesor": decisiones
        }
    
    def _validacion_humana_intermedia(self, fase: str, contenido: Any) -> bool:
        """Validación humana intermedia más natural"""
        
        print(f"\\n✅ VALIDACIÓN: {fase.upper()}")
        print("-" * 40)
        print(f"¿Te parece bien el enfoque hasta ahora?")
        
        respuesta = input(f"🗣️ (sí/no/cambiar): ").strip().lower()
        
        if respuesta in ['s', 'sí', 'si', 'vale', 'ok', 'bien']:
            return True
        elif respuesta in ['no', 'cambiar', 'modificar']:
            return False
        else:
            print("⚠️ No entendí tu respuesta, asumiré que está bien.")
            return True
    
    def _refinar_opciones(self, contexto_original: Dict, opciones_actuales: Dict) -> Dict:
        """Refina opciones basándose en feedback del profesor"""
        
        print(f"\\n🔄 REFINANDO OPCIONES...")
        feedback = input(f"🗣️ ¿Qué te gustaría cambiar?: ").strip()
        
        # Re-analizar con el feedback
        contexto_refinado = self.detectar_contexto_multidimensional(
            f"Contexto original: {contexto_original}\\nFeedback del profesor: {feedback}"
        )
        
        # Aplicar feedback directamente, no volver a preguntar
        return {
            "analisis_detector": contexto_refinado,
            "decisiones_profesor": {
                "feedback_aplicado": feedback,
                "contexto_refinado": "El profesor quiere cambiar el enfoque según su feedback"
            }
        }
    
    def _fase_estructura_libre(self, opciones_decididas: Dict, contexto_detectado: Dict) -> Dict[str, Any]:
        """Fase 2: Genera estructura completa basada en decisiones del profesor"""
        
        print(f"\\n🏠 FASE 2: CREANDO ESTRUCTURA COMPLETA")
        print("-" * 50)
        
        # SELECCIONAR EJEMPLO K_ ESTRATÉGICO
        contexto_base = opciones_decididas.get("analisis_detector", {}).get("contexto_base", {})
        materia_detectada = contexto_base.get("materia", "general")
        modalidad_detectada = contexto_base.get("modalidad_trabajo", "mixta")
        tema_detectado = contexto_base.get("tema", "")
        
        ejemplo_k_seleccionado = self.cargador_ejemplos.seleccionar_ejemplo_estrategico(
            materia_detectada, tema_detectado, modalidad_detectada
        )
        
        # Identificar qué ejemplo se seleccionó para mostrar
        ejemplo_nombre = "ninguno"
        for nombre_ejemplo in self.cargador_ejemplos.metadatos_ejemplos.keys():
            if nombre_ejemplo in ejemplo_k_seleccionado[:100]:  # Buscar en primeros 100 chars
                ejemplo_nombre = nombre_ejemplo
                break
        
        print(f"\\n📋 Ejemplo k_ seleccionado: {ejemplo_nombre}")
        
        # Crear prompt inteligente basado en las decisiones + ejemplo k_
        decisiones_texto = "\\n".join([f"- {k}: {v}" for k, v in opciones_decididas.get("decisiones_profesor", {}).items()])
        analisis_texto = str(opciones_decididas.get("analisis_detector", {}))
        
        tarea_estructura = Task(
            description=f"""
EJEMPLO K_ DE REFERENCIA (SIGUE ESTE ESTILO Y NIVEL DE DETALLE):
{ejemplo_k_seleccionado}

===============================

Crea una estructura completa para la actividad basada en:

DECISIONES DEL PROFESOR:
{decisiones_texto}

ANÁLISIS ORIGINAL:
{analisis_texto}

CREA:
1. Si el profesor pide un GUIÓN → genera el guión teatral completo
2. Si pide ORGANIZACIÓN → estructura por días/grupos como "Lunes: X, Y, Z hacen A mientras P, Q hacen B"
3. Si pide AMBOS → guión + organización

IMPORTANTE:
- Genera CONTENIDO REAL, no solo descripciones
- Si es teatro → diálogos completos entre personajes
- Si es organización → reparto práctico por días y grupos
- Adapta para Elena (TEA), Luis (TDAH), Ana (altas capacidades), etc.

FORMATO:
- Título atractivo
- Duración realista
- Materiales específicos
- Contenido/Guión si se pide
- Organización temporal si se pide
- Adaptaciones incluidas naturalmente
            """,
            agent=self.agentes.agente_estructurador,
            expected_output="Estructura completa con contenido real generado"
        )
        
        crew_estructura = Crew(
            agents=[self.agentes.agente_estructurador],
            tasks=[tarea_estructura],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_resultado = crew_estructura.kickoff()
        
        print(f"\\n🏠 ESTRUCTURA GENERADA:")
        print(str(estructura_resultado))
        
        # NUEVA FUNCIONALIDAD: Detección automática de oportunidades de paralelismo
        if self.motor_paralelismo.detectar_oportunidades_naturales(str(estructura_resultado)):
            print(f"\\n🔄 Detecté oportunidades de trabajo simultáneo entre estudiantes.")
            optimizar = input(f"¿Quieres que coordine el trabajo paralelo? (sí/no): ").strip().lower()
            
            if optimizar in ['s', 'sí', 'si', 'vale', 'ok']:
                print(f"\\n⚡ Optimizando coordinación paralela...")
                estructura_resultado = self.motor_paralelismo.optimizar_coordinacion(estructura_resultado, analisis_texto)
                print(f"\\n🔄 ESTRUCTURA OPTIMIZADA PARA PARALELISMO:")
                print(str(estructura_resultado))
        
        # Validación intermedia
        if not self._validacion_humana_intermedia("ESTRUCTURA", estructura_resultado):
            return self._refinar_estructura(contexto_detectado, {
                "estructura_completa": estructura_resultado,
                "opciones_base": opciones_decididas
            })
        
        # Identificar qué ejemplo k_ se usó realmente
        ejemplo_usado = "ninguno"
        for nombre_ejemplo in self.cargador_ejemplos.metadatos_ejemplos.keys():
            if nombre_ejemplo in ejemplo_k_seleccionado[:100]:  # Buscar en primeros 100 chars
                ejemplo_usado = nombre_ejemplo
                break
        
        return {
            "estructura_completa": estructura_resultado,
            "opciones_base": opciones_decididas,
            "ejemplo_k_usado": ejemplo_usado
        }
    
    def _refinar_estructura(self, contexto_original: Dict, estructura_actual: Dict) -> Dict:
        """Refina estructura basándose en feedback del profesor"""
        
        print(f"\\n🔄 REFINANDO ESTRUCTURA...")
        feedback = input(f"🗣️ ¿Qué te gustaría cambiar en la estructura?: ").strip()
        
        # Crear tarea de refinamiento
        tarea_refinamiento = Task(
            description=f"""
ESTRUCTURA ACTUAL:
{estructura_actual.get('estructura_completa', '')}

FEEDBACK DEL PROFESOR:
"{feedback}"

REFINA la estructura según el feedback:
- Mantén lo que funciona
- Cambia lo que el profesor pide
- Genera contenido real si se solicita
- Adapta organización si es necesario
            """,
            agent=self.agentes.agente_estructurador,
            expected_output="Estructura refinada según feedback del profesor"
        )
        
        crew_refinamiento = Crew(
            agents=[self.agentes.agente_estructurador],
            tasks=[tarea_refinamiento],
            process=Process.sequential,
            verbose=True
        )
        
        estructura_refinada = crew_refinamiento.kickoff()
        
        return {
            "estructura_completa": estructura_refinada,
            "opciones_base": estructura_actual.get("opciones_base", {})
        }
    
    def _crear_actividad_final_iterativa(self, estructura_completa: Dict, contexto_detectado: Dict) -> ActividadEducativa:
        """Fase 3: Crea actividad final con iteración hasta que el profesor esté satisfecho"""
        
        print(f"\\n✨ FASE 3: CREANDO ACTIVIDAD FINAL")
        print("-" * 50)
        
        # Extraer contexto real para la actividad final
        try:
            if isinstance(contexto_detectado, dict) and "contexto_base" in contexto_detectado:
                materia_real = contexto_detectado["contexto_base"].get("materia", "general")
                tema_real = contexto_detectado["contexto_base"].get("tema", "actividad")
            else:
                materia_real = "general"
                tema_real = "actividad"
        except:
            materia_real = "general"
            tema_real = "actividad"
        
        # Desglosar en tareas específicas
        tarea_desglose = self.templates.crear_tarea_desglose_tareas(
            str(estructura_completa.get("estructura_completa", "")),
            self.agentes.agente_tareas
        )
        
        crew_tareas = Crew(
            agents=[self.agentes.agente_tareas],
            tasks=[tarea_desglose],
            process=Process.sequential,
            verbose=True
        )
        
        tareas_desglosadas = crew_tareas.kickoff()
        
        print(f"\\n📋 TAREAS ESPECÍFICAS:")
        print(str(tareas_desglosadas))
        
        # Asignar a estudiantes específicos
        tarea_asignacion = self.templates.crear_tarea_asignacion_estudiantes(
            str(tareas_desglosadas),
            self.agentes.agente_repartidor
        )
        
        crew_asignacion = Crew(
            agents=[self.agentes.agente_repartidor],
            tasks=[tarea_asignacion],
            process=Process.sequential,
            verbose=True
        )
        
        asignaciones_finales = crew_asignacion.kickoff()
        
        print(f"\\n👥 ASIGNACIONES POR ESTUDIANTE:")
        print(str(asignaciones_finales))
        
        # Crear actividad final
        actividad_id = f"inteligente_{materia_real}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extraer tareas por estudiante del resultado
        tareas_estudiantes = self._parsear_asignaciones_estudiantes(str(asignaciones_finales))
        
        # Extraer materiales
        materiales = AnalizadorMateriales.extraer_materiales_de_actividad(
            str(estructura_completa.get("estructura_completa", ""))
        )
        
        actividad_final = ActividadEducativa(
            id=actividad_id,
            titulo=f"Actividad Inteligente - {materia_real.title()}",
            materia=materia_real,
            tema=tema_real,
            clima="inteligente",
            modalidad_trabajo="mixta_inteligente",
            contenido_completo=str(estructura_completa.get("estructura_completa", "")),
            tareas_estudiantes=tareas_estudiantes,
            materiales=materiales,
            duracion="45-60 minutos",
            fases=["Contexto", "Opciones", "Estructura", "Implementación"],
            metadatos={
                "sistema_usado": "agentes_inteligente",
                "paralelismo_optimizado": "detectado_automaticamente",
                "human_in_the_loop": True,
                "ejemplo_k_usado": estructura_completa.get("ejemplo_k_usado", "ninguno"),
                "agentes_participantes": [
                    "detector", "clima", "estructurador", 
                    "tareas", "repartidor", "paralelismo"
                ]
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Validación final
        print(f"\\n🎯 ACTIVIDAD GENERADA:")
        self.mostrar_actividad(actividad_final)
        
        satisfecho = input(f"\\n✅ ¿Estás satisfecho con el resultado? (sí/no): ").strip().lower()
        
        if satisfecho in ['s', 'sí', 'si', 'vale', 'ok', 'perfecto']:
            print(f"\\n🎉 ¡Actividad completada exitosamente!")
            return actividad_final
        else:
            # ITERACIÓN REAL: Refinamiento hasta satisfacción
            return self._refinar_actividad_hasta_satisfaccion(
                actividad_final, estructura_completa, contexto_detectado
            )
    
    def _refinar_actividad_hasta_satisfaccion(self, actividad_actual: ActividadEducativa, 
                                            estructura_completa: Dict, contexto_detectado: Dict) -> ActividadEducativa:
        """Refina la actividad iterativamente hasta que el profesor esté satisfecho"""
        
        max_iteraciones = 3
        iteracion_actual = 1
        
        while iteracion_actual <= max_iteraciones:
            print(f"\\n🔄 REFINAMIENTO - ITERACIÓN {iteracion_actual}/{max_iteraciones}")
            print("-" * 60)
            
            # Solicitar cambios específicos
            print(f"🗣️ ¿Qué te gustaría cambiar específicamente?")
            cambios = input("Describe los cambios: ").strip()
            
            if not cambios:
                print("⚠️ Sin cambios especificados, manteniendo actividad actual.")
                return actividad_actual
            
            # Guardar feedback en metadatos
            if "feedback_iteraciones" not in actividad_actual.metadatos:
                actividad_actual.metadatos["feedback_iteraciones"] = []
            
            actividad_actual.metadatos["feedback_iteraciones"].append({
                "iteracion": iteracion_actual,
                "feedback": cambios,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"\\n🔄 Procesando tus cambios...")
            
            # Crear tarea de refinamiento específico
            tarea_refinamiento = Task(
                description=f"""
ACTIVIDAD ACTUAL A REFINAR:
{actividad_actual.contenido_completo}

ASIGNACIONES ACTUALES:
{json.dumps(actividad_actual.tareas_estudiantes, indent=2, ensure_ascii=False)}

FEEDBACK ESPECÍFICO DEL PROFESOR:
"{cambios}"

INSTRUCCIONES DE REFINAMIENTO:
1. Lee CUIDADOSAMENTE el feedback del profesor
2. Si pide "problemas específicos" → genera problemas matemáticos concretos con números reales
3. Si pide "tareas para Luis y Sara" → crea asignaciones específicas para estos estudiantes
4. Si pide "contenido para 2 horas" → desarrolla suficientes actividades para completar ese tiempo
5. Mantén las adaptaciones para TEA (Elena), TDAH (Luis), altas capacidades (Ana)

GENERA:
- Contenido completamente renovado según el feedback
- Tareas específicas y detalladas por estudiante
- Problemas matemáticos con números concretos si se solicita
- Actividades suficientes para el tiempo solicitado

FORMATO DE SALIDA:
Estructura completa de la actividad refinada con contenido específico y detallado.
                """,
                agent=self.agentes.agente_estructurador,
                expected_output="Actividad completamente refinada según feedback específico"
            )
            
            crew_refinamiento = Crew(
                agents=[self.agentes.agente_estructurador],
                tasks=[tarea_refinamiento],
                process=Process.sequential,
                verbose=True
            )
            
            contenido_refinado = crew_refinamiento.kickoff()
            
            # Procesar nuevo contenido en tareas específicas
            tarea_nuevas_asignaciones = Task(
                description=f"""
CONTENIDO REFINADO:
{str(contenido_refinado)}

CREA asignaciones específicas para cada estudiante basadas en el contenido refinado:

ESTUDIANTES:
- 001 ALEX M. (visual, reflexivo, apoyo bajo)
- 002 MARÍA L. (auditivo, reflexivo, apoyo medio)  
- 003 ELENA R. (TEA nivel 1, visual, apoyo alto)
- 004 LUIS T. (TDAH combinado, kinestésico, apoyo alto)
- 005 ANA V. (altas capacidades, auditivo, apoyo bajo)
- 006 SARA M. (auditivo, reflexivo, apoyo medio)
- 007 EMMA K. (visual, equilibrado, apoyo medio)
- 008 HUGO P. (visual, reflexivo, apoyo bajo)

GENERA para cada estudiante UNA TAREA ESPECÍFICA Y DETALLADA, no descripciones genéricas.
                """,
                agent=self.agentes.agente_repartidor,
                expected_output="Lista específica de tareas detalladas por estudiante"
            )
            
            crew_nuevas_asignaciones = Crew(
                agents=[self.agentes.agente_repartidor],
                tasks=[tarea_nuevas_asignaciones],
                process=Process.sequential,
                verbose=True
            )
            
            nuevas_asignaciones = crew_nuevas_asignaciones.kickoff()
            
            # Crear actividad refinada
            actividad_refinada = ActividadEducativa(
                id=f"{actividad_actual.id}_refinada_v{iteracion_actual}",
                titulo=f"{actividad_actual.titulo} - Refinada v{iteracion_actual}",
                materia=actividad_actual.materia,
                tema=actividad_actual.tema,
                clima=actividad_actual.clima,
                modalidad_trabajo=actividad_actual.modalidad_trabajo,
                contenido_completo=str(contenido_refinado),
                tareas_estudiantes=self._parsear_asignaciones_estudiantes(str(nuevas_asignaciones)),
                materiales=actividad_actual.materiales,  # Se podrían actualizar también
                duracion=actividad_actual.duracion,
                fases=actividad_actual.fases + [f"Refinamiento {iteracion_actual}"],
                metadatos={
                    **actividad_actual.metadatos,
                    "refinamientos": iteracion_actual,
                    "feedback_iteraciones": actividad_actual.metadatos.get("feedback_iteraciones", [])
                },
                timestamp=datetime.now().isoformat()
            )
            
            # Mostrar actividad refinada
            print(f"\\n🎯 ACTIVIDAD REFINADA - ITERACIÓN {iteracion_actual}:")
            self.mostrar_actividad(actividad_refinada)
            
            # Verificar satisfacción
            satisfecho = input(f"\\n✅ ¿Estás satisfecho con esta versión refinada? (sí/no): ").strip().lower()
            
            if satisfecho in ['s', 'sí', 'si', 'vale', 'ok', 'perfecto']:
                print(f"\\n🎉 ¡Actividad refinada exitosamente en {iteracion_actual} iteraciones!")
                return actividad_refinada
            
            # Preparar para siguiente iteración
            actividad_actual = actividad_refinada
            iteracion_actual += 1
        
        # Si se agotaron las iteraciones
        print(f"\\n⏰ Se alcanzó el máximo de {max_iteraciones} refinamientos.")
        print("💾 Guardando la última versión con todo el feedback registrado.")
        return actividad_actual
    
    def _parsear_asignaciones_estudiantes(self, asignaciones_str: str) -> Dict[str, str]:
        """Parsea las asignaciones de estudiantes del resultado del agente"""
        
        tareas_estudiantes = {}
        
        # Buscar patrones mejorados para capturar tareas específicas
        patrones = [
            # Patrón principal: "001 ALEX M.: [TAREA]: descripción"
            r'(\\d{3})\\s+([A-Z\\s\\.]+):\\s*\\[([^\\]]+)\\]\\s*-?\\s*(.+?)(?=\\n\\d{3}|$)',
            # Patrón alternativo: "001 ALEX M.: descripción completa"  
            r'(\\d{3})\\s+([A-Z\\s\\.]+):\\s*(.+?)(?=\\n\\d{3}|$)',
            # Patrón con guión: "001 - ALEX M.: tarea"
            r'(\\d{3})\\s*-\\s*([A-Z\\s\\.]+):\\s*(.+?)(?=\\n\\d{3}|$)',
            # Patrón con bullet: "• 001 ALEX M.: tarea"
            r'•\\s*(\\d{3})\\s+([A-Z\\s\\.]+):\\s*(.+?)(?=\\n•|$)'
        ]
        
        for i, patron in enumerate(patrones):
            coincidencias = re.findall(patron, asignaciones_str, re.DOTALL | re.MULTILINE)
            
            for coincidencia in coincidencias:
                if len(coincidencia) == 4:  # Patrón con [TAREA]
                    codigo, nombre, titulo_tarea, descripcion = coincidencia
                    tarea_completa = f"{titulo_tarea}: {descripcion}".strip()
                elif len(coincidencia) == 3:  # Patrón estándar
                    codigo, nombre, tarea_completa = coincidencia
                else:
                    continue
                    
                tarea_limpia = tarea_completa.strip().replace('\\n', ' ')[:300]  # Limitar longitud
                tareas_estudiantes[codigo] = tarea_limpia
                
            # Si encontró coincidencias, no probar otros patrones
            if coincidencias:
                break
        
        # Si no encuentra patrones, usar asignación genérica
        if not tareas_estudiantes:
            estudiantes_base = ["001", "002", "003", "004", "005", "006", "007", "008"]
            for i, codigo in enumerate(estudiantes_base):
                tareas_estudiantes[codigo] = f"Participar en la actividad según sus capacidades"
        
        return tareas_estudiantes
    
    def mostrar_actividad(self, actividad: ActividadEducativa):
        """Muestra actividad de forma clara"""
        print("\\n" + "="*80)
        print(f"🎯 {actividad.titulo}")
        print("="*80)
        print(f"📖 Materia: {actividad.materia} | Tema: {actividad.tema}")
        print(f"🎭 Clima: {actividad.clima} | Modalidad: {actividad.modalidad_trabajo}")
        print(f"⏱️ Duración: {actividad.duracion}")
        
        print(f"\\n📦 MATERIALES:")
        for material in actividad.materiales:
            print(f"  • {material}")
        
        print(f"\\n👥 TAREAS POR ESTUDIANTE:")
        perfiles = {
            "001": "ALEX M.", "002": "MARÍA L.", "003": "ELENA R.", "004": "LUIS T.",
            "005": "ANA V.", "006": "SARA M.", "007": "EMMA K.", "008": "HUGO P."
        }
        
        for codigo, tarea in actividad.tareas_estudiantes.items():
            nombre = perfiles.get(codigo, f"Estudiante {codigo}")
            print(f"  {codigo} {nombre}: {tarea}")
        
        print(f"\\n🎯 GENERADO POR: Sistema de Agentes Inteligente")
        print(f"📅 Ejemplo k_ usado: {actividad.metadatos.get('ejemplo_k_usado', 'ninguno')}")