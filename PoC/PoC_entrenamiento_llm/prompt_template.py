"""
Prompt Template para generación de actividades educativas adaptadas
Diseñado para entrenar LLM local con Ollama
"""

class PromptTemplateGenerator:
    
    def __init__(self):
        self.base_template = """Eres un docente especializado en educación inclusiva y diversidad en el aula. Tu misión es crear actividades pedagógicas para todo el aula que se adapten específicamente al perfil de cada estudiante.

PERFIL DEL ESTUDIANTE:
- Nombre: {nombre}
- Edad: {edad} años
- Grado: {grado}º de Primaria
- Materia de enfoque: {materia_foco}
- CI: {ci_base}
- Temperamento: {temperamento}
- Canal de aprendizaje preferido: {canal_preferido}
- Nivel de apoyo necesario: {nivel_apoyo}
- Tolerancia a la frustración: {tolerancia_frustracion}
- Agrupamiento óptimo: {agrupamiento_optimo}
- Diagnóstico formal: {diagnostico_formal}

COMPETENCIAS ACTUALES:
Matemáticas: {matematicas_estado}
Lengua: {lengua_estado}  
Ciencias: {ciencias_estado}

CARACTERÍSTICAS PERSONALES:
- Intereses principales: {intereses}
- Estilo de aprendizaje: {estilo_aprendizaje}
- Necesidades especiales: {necesidades_especiales}

TEMA DE LA ACTIVIDAD: {tema}

INSTRUCCIONES PARA LA ACTIVIDAD:
Diseña una actividad educativa completamente adaptada a los perfiles de este aula que incluya:

1. **TÍTULO ATRACTIVO**: Que conecte con los intereses de los estudiantes

2. **OBJETIVO DE APRENDIZAJE**: Específico para el nivel de competencia actual de los estudiantes en el tema e incluyendo aspectos curriculares que no sean directamente los espeficados en el tema, pero que estén adecuados también al nivel curricular de los aulumnos del aula. 

3. **DESCRIPCIÓN DE LA ACTIVIDAD**: Detallada y adaptada a las características de los estudiantes.

4. **ROL DEL PROFESOR**: En cada actividad, la estrategía que ha de controlar el profesor ha de estar detallada.

4. **ADAPTACIONES METODOLÓGICAS**: 
   - Para el canal de aprendizaje preferido ({canal_preferido})
   - Para el nivel de apoyo ({nivel_apoyo})
   - Para el agrupamiento ({agrupamiento_optimo})
   - Para la tolerancia a la frustración ({tolerancia_frustracion})

5. **INSTRUCCIONES PASO A PASO**: Claras y adaptadas al temperamento {temperamento}

6. **MATERIALES NECESARIOS**: Apropiados para el estilo de aprendizaje

7. **ESTRATEGIAS DE MOTIVACIÓN**: Basadas en los intereses: {intereses}

8. **EVALUACIÓN Y RETROALIMENTACIÓN**: Adaptada al perfil del estudiante

9. **ADAPTACIONES ESPECIALES**: {adaptaciones_especificas}

La actividad debe ser:
- Apropiada para la edad de {edad} años
- Adaptada al nivel de competencia actual
- Respetuosa con las necesidades especiales
- Incluir en qué se traduce en esta actividad específica cada una de las adaptaciones mencionadas
- Ser posible de realizar en un aula con los materiales estandar 
- Motivante según los intereses personales
- Viable en el agrupamiento preferido

Responde en español con un formato estructurado y práctico para implementar en el aula."""

    def generar_prompt_matematicas(self, perfil, tema_especifico):
        """Genera prompt específico para matemáticas"""
        matematicas_estado = self._formatear_competencias(perfil['matematicas'])
        adaptaciones = self._generar_adaptaciones_matematicas(perfil)
        
        return self._aplicar_template(perfil, "Matemáticas", tema_especifico, 
                                    matematicas_estado, adaptaciones)
    
    def generar_prompt_lengua(self, perfil, tema_especifico):
        """Genera prompt específico para lengua"""
        lengua_estado = self._formatear_competencias(perfil['lengua'])
        adaptaciones = self._generar_adaptaciones_lengua(perfil)
        
        return self._aplicar_template(perfil, "Lengua", tema_especifico,
                                    lengua_estado, adaptaciones)
    
    def generar_prompt_ciencias(self, perfil, tema_especifico):
        """Genera prompt específico para ciencias"""
        ciencias_estado = self._formatear_competencias(perfil['ciencias'])
        adaptaciones = self._generar_adaptaciones_ciencias(perfil)
        
        return self._aplicar_template(perfil, "Ciencias", tema_especifico,
                                    ciencias_estado, adaptaciones)
    
    def _aplicar_template(self, perfil, materia, tema, competencias_estado, adaptaciones):
        """Aplica el template base con los datos del perfil"""
        
        # Preparar necesidades especiales
        necesidades = perfil.get('necesidades_especiales', ['ninguna'])
        necesidades_str = ', '.join(necesidades) if necesidades != ['ninguna'] else 'ninguna'
        
        return self.base_template.format(
            nombre=perfil['nombre'],
            edad=perfil['edad'],
            grado=perfil['grado'],
            materia_foco=materia,
            ci_base=perfil['ci_base'],
            temperamento=perfil['temperamento'],
            canal_preferido=perfil['canal_preferido'],
            nivel_apoyo=perfil['nivel_apoyo'],
            tolerancia_frustracion=perfil['tolerancia_frustracion'],
            agrupamiento_optimo=perfil['agrupamiento_optimo'],
            diagnostico_formal=perfil['diagnostico_formal'],
            matematicas_estado=self._formatear_competencias(perfil['matematicas']),
            lengua_estado=self._formatear_competencias(perfil['lengua']),
            ciencias_estado=self._formatear_competencias(perfil['ciencias']),
            intereses=', '.join(perfil['intereses']),
            estilo_aprendizaje=perfil['estilo_aprendizaje'],
            necesidades_especiales=necesidades_str,
            tema=tema,
            adaptaciones_especificas=adaptaciones
        )
    
    def _formatear_competencias(self, competencias_dict):
        """Formatea el estado de competencias para el prompt"""
        estado_items = []
        for competencia, nivel in competencias_dict.items():
            estado_items.append(f"{competencia.replace('_', ' ').title()}: {nivel}")
        return '; '.join(estado_items)
    
    def _generar_adaptaciones_matematicas(self, perfil):
        """Genera adaptaciones específicas para matemáticas según el perfil"""
        adaptaciones = []
        
        if perfil['diagnostico_formal'] == 'TEA_nivel_1':
            adaptaciones.extend([
                "Usar materiales manipulativos concretos",
                "Presentar problemas con imágenes claras",
                "Evitar cambios bruscos en la metodología"
            ])
        
        if perfil['diagnostico_formal'] == 'TDAH_combinado':
            adaptaciones.extend([
                "Actividades cortas (10-15 minutos máximo)",
                "Incluir movimiento físico en los ejercicios",
                "Usar colores y elementos visuales llamativos"
            ])
        
        if perfil['diagnostico_formal'] == 'altas_capacidades':
            adaptaciones.extend([
                "Proponer problemas de mayor complejidad",
                "Incluir retos de pensamiento lógico",
                "Permitir múltiples estrategias de resolución"
            ])
        
        if perfil['canal_preferido'] == 'visual':
            adaptaciones.append("Usar diagramas, gráficos y representaciones visuales")
        elif perfil['canal_preferido'] == 'auditivo':
            adaptaciones.append("Incluir explicaciones verbales y discusión grupal")
        elif perfil['canal_preferido'] == 'kinestésico':
            adaptaciones.append("Incorporar manipulativos y actividades físicas")
        
        return '; '.join(adaptaciones) if adaptaciones else "Seguir metodología estándar adaptada al perfil"
    
    def _generar_adaptaciones_lengua(self, perfil):
        """Genera adaptaciones específicas para lengua según el perfil"""
        adaptaciones = []
        
        if perfil['diagnostico_formal'] == 'TEA_nivel_1':
            adaptaciones.extend([
                "Usar estructuras de texto predecibles",
                "Proporcionar ejemplos visuales de cada concepto",
                "Evitar metáforas complejas o lenguaje figurado"
            ])
        
        if perfil['diagnostico_formal'] == 'TDAH_combinado':
            adaptaciones.extend([
                "Textos cortos y fragmentados",
                "Actividades interactivas y dinámicas",
                "Uso de timer para gestionar tiempo"
            ])
        
        if perfil['diagnostico_formal'] == 'altas_capacidades':
            adaptaciones.extend([
                "Textos de mayor complejidad léxica",
                "Análisis crítico y debates",
                "Conexiones interdisciplinares"
            ])
        
        return '; '.join(adaptaciones) if adaptaciones else "Seguir metodología estándar adaptada al perfil"
    
    def _generar_adaptaciones_ciencias(self, perfil):
        """Genera adaptaciones específicas para ciencias según el perfil"""
        adaptaciones = []
        
        if perfil['canal_preferido'] == 'visual':
            adaptaciones.extend([
                "Usar experimentos con resultados visibles",
                "Incluir diagramas y esquemas científicos"
            ])
        elif perfil['canal_preferido'] == 'kinestésico':
            adaptaciones.extend([
                "Priorizar experimentos hands-on",
                "Incluir actividades de construcción y manipulación"
            ])
        
        if perfil['diagnostico_formal'] == 'altas_capacidades':
            adaptaciones.extend([
                "Plantear hipótesis más complejas",
                "Conectar con fenómenos científicos avanzados"
            ])
        
        return '; '.join(adaptaciones) if adaptaciones else "Seguir metodología experimental estándar"

# Ejemplos de temas por materia para 4º de Primaria
TEMAS_MATEMATICAS_4_PRIMARIA = [
    "Fracciones equivalentes",
    "Multiplicación por dos cifras", 
    "División con resto",
    "Área de rectángulos",
    "Números decimales",
    "Problemas de proporción",
    "Perímetro de figuras",
    "Medidas de tiempo",
    "Probabilidad básica",
    "Patrones numéricos"
]

TEMAS_LENGUA_4_PRIMARIA = [
    "Análisis sintáctico básico",
    "Tiempos verbales compuestos",
    "Ortografía de palabras homófonas",
    "Textos argumentativos",
    "Comprensión lectora inferencial",
    "Vocabulario técnico",
    "Escritura de diálogos",
    "Uso de conectores",
    "Descripción de personajes",
    "Poesía y recursos literarios"
]

TEMAS_CIENCIAS_4_PRIMARIA = [
    "Ciclo del agua",
    "Estados de la materia",
    "Fuerzas y movimiento",
    "Sistema solar",
    "Plantas y fotosíntesis",
    "Cadenas alimentarias",
    "Rocas y minerales",
    "Electricidad básica",
    "Cuerpo humano: digestión",
    "Ecosistemas locales"
]