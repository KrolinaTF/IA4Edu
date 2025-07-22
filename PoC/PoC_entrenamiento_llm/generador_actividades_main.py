"""
Generador principal de actividades educativas adaptadas
Combina perfiles de estudiantes, templates de prompts y API de Groq
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import random

from prompt_template import PromptTemplateGenerator, TEMAS_MATEMATICAS_4_PRIMARIA, TEMAS_LENGUA_4_PRIMARIA, TEMAS_CIENCIAS_4_PRIMARIA
from groq_api_integrator import GroqAPIEducationGenerator



class GeneradorActividadesEducativas:
    
    def __init__(self, archivo_perfiles: str = None, modelo_groq: str = "llama-3.1-8b-instant"):
        """
        Inicializa el generador de actividades
        
        Args:
            archivo_perfiles: Ruta al archivo JSON con perfiles de estudiantes
            modelo_groq: Modelo de Groq a utilizar
        """
        # Buscar archivo de perfiles en directorio del script
        if archivo_perfiles is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            archivo_perfiles = os.path.join(script_dir, "perfiles_4_primaria.json")
        self.archivo_perfiles = archivo_perfiles
        self.perfiles = self._cargar_perfiles()
        self.prompt_generator = PromptTemplateGenerator()
        self.groq_generator = GroqAPIEducationGenerator(model_name=modelo_groq)
        
        # Mapeo de temas por materia
        self.temas_por_materia = {
            "Matemáticas": TEMAS_MATEMATICAS_4_PRIMARIA,
            "Lengua": TEMAS_LENGUA_4_PRIMARIA,
            "Ciencias": TEMAS_CIENCIAS_4_PRIMARIA
        }
    
    def _cargar_perfiles(self) -> List[Dict]:
        """Carga los perfiles de estudiantes desde el archivo JSON"""
        try:
            with open(self.archivo_perfiles, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['estudiantes']
        except FileNotFoundError:
            print(f"ERROR Error: No se encontró el archivo {self.archivo_perfiles}")
            return []
        except json.JSONDecodeError:
            print(f"ERROR Error: El archivo {self.archivo_perfiles} no tiene formato JSON válido")
            return []
    
    def _normalizar_materia(self, materia: str) -> str:
        """Normaliza el nombre de la materia para evitar errores tipográficos"""
        materia_limpia = materia.lower().strip()
        
        # Mapeo de variaciones comunes
        mapeo = {
            'matematicas': 'Matemáticas',
            'matemáticas': 'Matemáticas', 
            'matemáticaas': 'Matemáticas',  # Error tipográfico común
            'mates': 'Matemáticas',
            'math': 'Matemáticas',
            'lengua': 'Lengua',
            'español': 'Lengua',
            'castellano': 'Lengua',
            'lenguaje': 'Lengua',
            'ciencias': 'Ciencias',
            'naturales': 'Ciencias',
            'ciencias naturales': 'Ciencias'
        }
        
        return mapeo.get(materia_limpia, None)
    
    def generar_actividad_individual(self, estudiante_id: str, materia: str, tema: str = None) -> Dict:
        """
        Genera una actividad para un estudiante específico
        
        Args:
            estudiante_id: ID del estudiante (001-008)
            materia: Materia (Matemáticas, Lengua, Ciencias)
            tema: Tema específico (opcional, se selecciona automáticamente)
            
        Returns:
            Diccionario con la actividad generada y metadatos
        """
        
        # Normalizar materia
        materia_normalizada = self._normalizar_materia(materia)
        if not materia_normalizada:
            return {"error": f"Materia '{materia}' no reconocida. Usa: Matemáticas, Lengua, o Ciencias"}
        
        # Buscar el perfil del estudiante
        perfil = None
        for estudiante in self.perfiles:
            if estudiante['id'] == estudiante_id:
                perfil = estudiante
                break
        
        if not perfil:
            return {"error": f"No se encontró el estudiante con ID {estudiante_id}"}
        
        # Seleccionar tema si no se proporciona
        if not tema:
            if materia_normalizada in self.temas_por_materia:
                tema = random.choice(self.temas_por_materia[materia_normalizada])
            else:
                return {"error": f"Materia '{materia_normalizada}' no disponible"}
        
        # Generar prompt según la materia
        if materia_normalizada == "Matemáticas":
            prompt = self.prompt_generator.generar_prompt_matematicas(perfil, tema)
        elif materia_normalizada == "Lengua":
            prompt = self.prompt_generator.generar_prompt_lengua(perfil, tema)
        elif materia_normalizada == "Ciencias":
            prompt = self.prompt_generator.generar_prompt_ciencias(perfil, tema)
        else:
            return {"error": f"Materia '{materia_normalizada}' no soportada"}
        
        # Generar actividad con Groq API
        actividad = self.groq_generator.generar_texto(prompt, max_tokens=800)
        
        if not actividad:
            return {"error": "No se pudo generar la actividad"}
        
        # Crear metadatos
        metadatos = {
            "estudiante": {
                "id": perfil['id'],
                "nombre": perfil['nombre'],
                "edad": perfil['edad'],
                "diagnostico": perfil['diagnostico_formal']
            },
            "actividad": {
                "materia": materia_normalizada,
                "tema": tema,
                "nivel_apoyo": perfil['nivel_apoyo'],
                "canal_preferido": perfil['canal_preferido'],
                "agrupamiento": perfil['agrupamiento_optimo']
            },
            "generacion": {
                "timestamp": datetime.now().isoformat(),
                "modelo": self.groq_generator.model_name
            }
        }
        
        return {
            "success": True,
            "metadatos": metadatos,
            "prompt": prompt,
            "actividad": actividad
        }
    
    def generar_actividades_aula_completa(self, materia: str, tema: str = None, output_dir: str = None) -> Dict:
        """
        Genera actividades para toda el aula (8 estudiantes)
        
        Args:
            materia: Materia para todas las actividades
            tema: Tema específico (opcional)
            output_dir: Directorio de salida (opcional)
            
        Returns:
            Diccionario con resultados de la generación
        """
        
        # Normalizar materia
        materia_normalizada = self._normalizar_materia(materia)
        if not materia_normalizada:
            return {"error": f"Materia '{materia}' no reconocida. Usa: Matemáticas, Lengua, o Ciencias"}
        
        if not output_dir:
            output_dir = "actividades_generadas"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # En lugar de generar actividades individuales, creamos una actividad grupal
        # Analizar la diversidad del aula
        diversidad = self._analizar_diversidad_aula()
        
        # Crear prompt para actividad grupal con roles individuales  
        prompt_grupal = self._generar_prompt_actividad_grupal(materia_normalizada, tema, diversidad)
        
        try:
            print(f"Generando actividad grupal de {materia_normalizada}: {tema}")
            actividad_grupal = self.groq_generator.generar_texto(prompt_grupal, max_tokens=2000)
            
            if not actividad_grupal:
                return {"error": "No se pudo generar la actividad grupal"}
            
            # Crear archivo único con la actividad grupal (con timestamp para evitar sobrescribir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_actividad = os.path.join(output_dir, f"actividad_grupal_{materia_normalizada.lower()}_{tema.replace(' ', '_')}_{timestamp}.txt")
            
            with open(archivo_actividad, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"ACTIVIDAD GRUPAL: {materia_normalizada} - {tema}\n")
                f.write(f"AULA: AULA_A_4PRIM ({len(self.perfiles)} estudiantes)\n")
                f.write("=" * 80 + "\n\n")
                f.write("ESTUDIANTES DEL AULA:\n")
                for perfil in self.perfiles:
                    f.write(f"- {perfil['id']}: {perfil['nombre']} ({perfil['diagnostico_formal']}, {perfil['canal_preferido']}, apoyo {perfil['nivel_apoyo']})\n")
                f.write("\n")
                f.write("DIVERSIDAD CONSIDERADA:\n")
                f.write(f"- Diagnósticos: {diversidad['diagnosticos']}\n")
                f.write(f"- Canales: {diversidad['canales_aprendizaje']}\n")
                f.write(f"- Niveles apoyo: {diversidad['niveles_apoyo']}\n")
                f.write(f"- Temperamentos: {diversidad['temperamentos']}\n\n")
                f.write("ACTIVIDAD GRUPAL:\n")
                f.write("-" * 50 + "\n")
                f.write(actividad_grupal)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Generado: {datetime.now().isoformat()}\n")
                f.write(f"Modelo: {self.groq_generator.model_name}\n")
            
            resultados = {
                "success": True,
                "tipo": "actividad_grupal", 
                "materia": materia_normalizada,
                "tema": tema,
                "output_dir": output_dir,
                "archivo": archivo_actividad,
                "estudiantes_incluidos": len(self.perfiles),
                "actividad": actividad_grupal
            }
            
        except Exception as e:
            return {"error": f"Error generando actividad grupal: {e}"}
            
        # Mantener el código original comentado por si lo necesitas
        """
        # CÓDIGO ORIGINAL PARA ACTIVIDADES INDIVIDUALES
        prompts_batch = []
        resultados = {
            "materia": materia_normalizada,
            "tema": tema,
            "output_dir": output_dir,
            "estudiantes_procesados": [],
            "actividades_generadas": []
        }
        
        for perfil in self.perfiles:
            # Usar tema específico o seleccionar uno apropiado para cada estudiante
            tema_estudiante = tema
            if not tema_estudiante:
                if materia_normalizada in self.temas_por_materia:
                    # Seleccionar tema basado en el nivel de competencia del estudiante
                    tema_estudiante = self._seleccionar_tema_adaptado(perfil, materia_normalizada)
                else:
                    print(f"ERROR Materia '{materia_normalizada}' no disponible")
                    continue
            
            # Generar prompt
            if materia_normalizada == "Matemáticas":
                prompt = self.prompt_generator.generar_prompt_matematicas(perfil, tema_estudiante)
            elif materia_normalizada == "Lengua":
                prompt = self.prompt_generator.generar_prompt_lengua(perfil, tema_estudiante)
            elif materia_normalizada == "Ciencias":
                prompt = self.prompt_generator.generar_prompt_ciencias(perfil, tema_estudiante)
            else:
                continue
            
            # Crear metadatos para el archivo
            metadatos = {
                "estudiante": {
                    "id": perfil['id'],
                    "nombre": perfil['nombre'],
                    "edad": perfil['edad'],
                    "diagnostico": perfil['diagnostico_formal'],
                    "canal_preferido": perfil['canal_preferido'],
                    "nivel_apoyo": perfil['nivel_apoyo']
                },
                "actividad": {
                    "materia": materia_normalizada,
                    "tema": tema_estudiante,
                    "adaptaciones": perfil.get('necesidades_especiales', [])
                }
            }
            
            # Nombre del archivo
            nombre_archivo = f"actividad_{perfil['id']}_{perfil['nombre'].replace(' ', '_')}_{materia_normalizada.lower()}_{tema_estudiante.replace(' ', '_')}"
            
            prompts_batch.append((prompt, nombre_archivo, metadatos))
            resultados["estudiantes_procesados"].append({
                "id": perfil['id'],
                "nombre": perfil['nombre'],
                "tema": tema_estudiante
            })
        
        # Generar todas las actividades individualmente
        actividades_generadas = 0
        actividades_fallidas = 0
        
        for prompt, nombre_archivo, metadatos in prompts_batch:
            try:
                actividad = self.groq_generator.generar_texto(prompt, max_tokens=800)
                
                # Guardar archivo individual
                archivo_path = os.path.join(output_dir, f"{nombre_archivo}.txt")
                with open(archivo_path, 'w', encoding='utf-8') as f:
                    f.write(f"METADATOS:\n{json.dumps(metadatos, indent=2, ensure_ascii=False)}\n\n")
                    f.write(f"ACTIVIDAD GENERADA:\n{actividad}")
                
                resultados["actividades_generadas"].append({
                    "archivo": archivo_path,
                    "estudiante": metadatos['estudiante']['id'],
                    "success": True
                })
                actividades_generadas += 1
                
            except Exception as e:
                print(f"ERROR Error generando actividad para {metadatos['estudiante']['nombre']}: {e}")
                actividades_fallidas += 1
                resultados["actividades_generadas"].append({
                    "estudiante": metadatos['estudiante']['id'],
                    "success": False,
                    "error": str(e)
                })
        
        resultados["exitosas"] = actividades_generadas
        resultados["fallidas"] = actividades_fallidas
        
        # Crear archivo resumen del aula
        resumen_aula = {
            "metadata": {
                "aula": "AULA_A_4PRIM",
                "materia": materia,
                "tema_general": tema,
                "fecha_generacion": datetime.now().isoformat(),
                "total_estudiantes": len(self.perfiles)
            },
            "diversidad_aula": self._analizar_diversidad_aula(),
            "adaptaciones_implementadas": self._resumir_adaptaciones(materia),
            "resultados_generacion": resultados
        }
        
        resumen_path = os.path.join(output_dir, "resumen_aula_completa.json")
        with open(resumen_path, 'w', encoding='utf-8') as f:
            json.dump(resumen_aula, f, indent=2, ensure_ascii=False)
        
        print(f"\n Resumen del aula guardado en: {resumen_path}")
        """
        
        return resultados
    
    def generar_actividad_colaborativa_aula(self, materia: str, tema: str = None, output_dir: str = None) -> Dict:
        """
        Genera UNA actividad colaborativa para toda el aula considerando la diversidad
        
        Args:
            materia: Materia (Matemáticas, Lengua, Ciencias)
            tema: Tema específico (opcional)
            output_dir: Directorio de salida (opcional)
            
        Returns:
            Diccionario con la actividad colaborativa generada
        """
        
        # Normalizar materia
        materia_normalizada = self._normalizar_materia(materia)
        if not materia_normalizada:
            return {"error": f"Materia '{materia}' no reconocida. Usa: Matemáticas, Lengua, o Ciencias"}
        
        if not output_dir:
            output_dir = "actividades_generadas"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Seleccionar tema si no se proporciona
        if not tema:
            if materia_normalizada in self.temas_por_materia:
                tema = random.choice(self.temas_por_materia[materia_normalizada])
            else:
                return {"error": f"Materia '{materia_normalizada}' no disponible"}
        
        # Analizar la diversidad del aula para crear el prompt colaborativo
        diversidad = self._analizar_diversidad_aula()
        
        # Crear prompt colaborativo que tenga en cuenta toda la diversidad
        prompt_colaborativo = self._generar_prompt_colaborativo(materia_normalizada, tema, diversidad)
        
        try:
            # Generar la actividad colaborativa
            print(f"Generando actividad colaborativa para {materia_normalizada}: {tema}")
            actividad_colaborativa = self.groq_generator.generar_texto(prompt_colaborativo, max_tokens=1500)
            
            if not actividad_colaborativa:
                return {"error": "No se pudo generar la actividad colaborativa"}
            
            # Crear metadatos de la actividad colaborativa
            metadatos = {
                "tipo": "actividad_colaborativa",
                "aula": "AULA_A_4PRIM", 
                "materia": materia_normalizada,
                "tema": tema,
                "total_estudiantes": len(self.perfiles),
                "diversidad_considerada": diversidad,
                "adaptaciones_incluidas": self._resumir_adaptaciones(materia_normalizada),
                "timestamp": datetime.now().isoformat(),
                "modelo_ia": self.groq_generator.model_name
            }
            
            # Guardar la actividad colaborativa (con timestamp para evitar sobrescribir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_actividad = os.path.join(output_dir, f"actividad_colaborativa_{materia_normalizada.lower()}_{tema.replace(' ', '_')}_{timestamp}.txt")
            
            with open(archivo_actividad, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"ACTIVIDAD COLABORATIVA: {materia_normalizada} - {tema}\n")
                f.write(f"AULA: AULA_A_4PRIM ({len(self.perfiles)} estudiantes)\n")
                f.write("=" * 80 + "\n\n")
                f.write("DIVERSIDAD DEL AULA CONSIDERADA:\n")
                f.write(f"- Diagnósticos: {diversidad['diagnosticos']}\n")
                f.write(f"- Canales de aprendizaje: {diversidad['canales_aprendizaje']}\n")
                f.write(f"- Niveles de apoyo: {diversidad['niveles_apoyo']}\n")
                f.write(f"- Temperamentos: {diversidad['temperamentos']}\n\n")
                f.write("ACTIVIDAD COLABORATIVA:\n")
                f.write("-" * 50 + "\n")
                f.write(actividad_colaborativa)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("INFORMACIÓN TÉCNICA:\n")
                f.write(f"Generado: {datetime.now().isoformat()}\n")
                f.write(f"Modelo: {self.groq_generator.model_name}\n")
            
            # Guardar metadatos (con timestamp)
            archivo_metadatos = os.path.join(output_dir, f"metadatos_actividad_colaborativa_{timestamp}.json")
            with open(archivo_metadatos, 'w', encoding='utf-8') as f:
                json.dump(metadatos, f, indent=2, ensure_ascii=False)
            
            print(f"OK Actividad colaborativa guardada en: {archivo_actividad}")
            
            return {
                "success": True,
                "tipo": "actividad_colaborativa",
                "archivo": archivo_actividad,
                "metadatos": metadatos,
                "actividad": actividad_colaborativa,
                "estudiantes_incluidos": len(self.perfiles)
            }
            
        except Exception as e:
            return {"error": f"Error generando actividad colaborativa: {e}"}
    
    def _generar_prompt_colaborativo(self, materia: str, tema: str, diversidad: Dict) -> str:
        """Genera un prompt para actividad colaborativa considerando toda la diversidad del aula"""
        
        # Extraer información clave de la diversidad
        diagnosticos = diversidad['diagnosticos']
        canales = diversidad['canales_aprendizaje'] 
        niveles_apoyo = diversidad['niveles_apoyo']
        temperamentos = diversidad['temperamentos']
        
        # Crear descripción de los estudiantes para el prompt
        estudiantes_info = []
        for perfil in self.perfiles:
            info = f"- {perfil['nombre']} ({perfil['id']}): {perfil['diagnostico_formal']}, canal {perfil['canal_preferido']}, apoyo {perfil['nivel_apoyo']}, temperamento {perfil['temperamento']}"
            estudiantes_info.append(info)
        
        prompt = f"""Eres un docente especializado en educación inclusiva y actividades colaborativas. 

Debes crear UNA actividad colaborativa para un aula de 4º de Primaria con {len(self.perfiles)} estudiantes sobre {materia} - tema: {tema}.

DIVERSIDAD DEL AULA:
- Diagnósticos presentes: {', '.join([f'{k}: {v}' for k,v in diagnosticos.items() if v > 0])}
- Canales de aprendizaje: {', '.join([f'{k}: {v}' for k,v in canales.items() if v > 0])}
- Niveles de apoyo: {', '.join([f'{k}: {v}' for k,v in niveles_apoyo.items() if v > 0])}
- Temperamentos: {', '.join([f'{k}: {v}' for k,v in temperamentos.items() if v > 0])}

ESTUDIANTES ESPECÍFICOS:
{chr(10).join(estudiantes_info)}

REQUISITOS PARA LA ACTIVIDAD COLABORATIVA:
1. UNA sola actividad que incluya a TODOS los estudiantes trabajando juntos
2. Diferentes roles/tareas adaptados a las necesidades específicas de cada perfil
3. Utiliza múltiples canales de aprendizaje (visual, auditivo, kinestésico)
4. Incluye adaptaciones específicas para TEA, TDAH, altas capacidades según corresponda
5. Respeta los temperamentos (reflexivos vs impulsivos)
6. Proporciona diferentes niveles de complejidad dentro de la misma actividad
7. Fomenta la colaboración e interdependencia positiva
8. Incluye momentos de evaluación colaborativa

ESTRUCTURA REQUERIDA:
- TÍTULO atractivo
- OBJETIVO COLABORATIVO 
- DESCRIPCIÓN de la actividad grupal
- ROLES ESPECÍFICOS para cada estudiante (menciona por nombre/ID)
- MATERIALES necesarios
- DESARROLLO paso a paso
- ADAPTACIONES específicas por diagnóstico
- EVALUACIÓN colaborativa
- TIEMPO estimado

Crea una actividad donde todos trabajen hacia un objetivo común pero con contribuciones diferenciadas según sus fortalezas y necesidades."""

        return prompt
    
    def _generar_prompt_actividad_grupal(self, materia: str, tema: str, diversidad: Dict) -> str:
        """Genera un prompt para actividad grupal con roles específicos por estudiante"""
        
        # Crear descripción detallada de cada estudiante
        estudiantes_detalle = []
        for perfil in self.perfiles:
            detalle = f"""- {perfil['nombre']} ({perfil['id']}): 
  * Diagnóstico: {perfil['diagnostico_formal']}
  * Canal preferido: {perfil['canal_preferido']}
  * Nivel apoyo: {perfil['nivel_apoyo']}
  * Temperamento: {perfil['temperamento']}
  * CI: {perfil['ci_base']}
  * Necesidades: {', '.join(perfil.get('necesidades_especiales', ['Ninguna']))}"""
            estudiantes_detalle.append(detalle)
        
        prompt = f"""Eres un docente especializado en educación inclusiva. 

Debes crear UNA actividad grupal para un aula de 4º de Primaria sobre {materia} - tema: {tema}.

INFORMACIÓN DETALLADA DE CADA ESTUDIANTE:
{chr(10).join(estudiantes_detalle)}

DIVERSIDAD DEL AULA:
- Diagnósticos: {diversidad['diagnosticos']}
- Canales de aprendizaje: {diversidad['canales_aprendizaje']}
- Niveles de apoyo: {diversidad['niveles_apoyo']}
- Temperamentos: {diversidad['temperamentos']}

REQUISITOS PARA LA ACTIVIDAD GRUPAL:
1. UNA actividad donde todos participan hacia un objetivo común
2. ROLES ESPECÍFICOS y TAREAS DIFERENCIADAS para cada estudiante (menciona por nombre/ID)
3. Respeta las necesidades individuales de cada diagnóstico
4. Utiliza los canales de aprendizaje preferidos de cada estudiante
5. Proporciona diferentes niveles de complejidad adaptados al CI y nivel de apoyo
6. Incluye adaptaciones específicas para TEA, TDAH, altas capacidades
7. Fomenta la interdependencia positiva (cada uno necesita a los otros)
8. Especifica QUÉ HACE CADA ALUMNO/A por nombre

ESTRUCTURA REQUERIDA:
- TÍTULO atractivo de la actividad
- OBJETIVO GENERAL del grupo
- DESCRIPCIÓN de la actividad grupal
- ROLES Y TAREAS ESPECÍFICAS:
  * Para cada estudiante, especifica: "NOMBRE (ID): [descripción detallada de su rol y tareas específicas, adaptadas a sus necesidades]"
- MATERIALES necesarios
- PROCESO paso a paso (qué hace cada uno en cada fase)
- ADAPTACIONES específicas por diagnóstico
- PRODUCTO FINAL del grupo
- EVALUACIÓN (individual y grupal)
- DURACIÓN estimada

IMPORTANTE: 
- Menciona a TODOS los estudiantes por nombre e ID
- Detalla específicamente qué hace cada uno
- Las tareas deben ser complementarias (interdependencia)
- Respeta las fortalezas y limitaciones de cada perfil
- La actividad debe resultar en UN producto final del grupo"""

        return prompt
    
    def _seleccionar_tema_adaptado(self, perfil: Dict, materia: str) -> str:
        """Selecciona un tema apropiado según el nivel del estudiante"""
        
        # Determinar nivel general del estudiante en la materia
        if materia == "Matemáticas":
            competencias = perfil['matematicas']
        elif materia == "Lengua":
            competencias = perfil['lengua']
        elif materia == "Ciencias":
            competencias = perfil['ciencias']
        else:
            return random.choice(self.temas_por_materia[materia])
        
        # Contar competencias por nivel
        niveles = {"SUPERADO": 0, "CONSEGUIDO": 0, "EN_PROCESO": 0, "INICIADO": 0, "EMERGENTE": 0}
        for nivel in competencias.values():
            if nivel in niveles:
                niveles[nivel] += 1
        
        # Seleccionar tema según el nivel predominante
        total_competencias = sum(niveles.values())
        if total_competencias == 0:
            return random.choice(self.temas_por_materia[materia])
        
        # Porcentaje de competencias avanzadas
        avanzadas = (niveles["SUPERADO"] + niveles["CONSEGUIDO"]) / total_competencias
        
        temas = self.temas_por_materia[materia]
        
        if avanzadas > 0.6:  # Estudiante avanzado
            return random.choice(temas[-3:])  # Temas más complejos
        elif avanzadas > 0.3:  # Estudiante intermedio
            return random.choice(temas[2:-2])  # Temas intermedios
        else:  # Estudiante que necesita refuerzo
            return random.choice(temas[:3])  # Temas básicos
    
    def _analizar_diversidad_aula(self) -> Dict:
        """Analiza la diversidad presente en el aula"""
        
        diversidad = {
            "diagnosticos": {},
            "canales_aprendizaje": {},
            "niveles_apoyo": {},
            "temperamentos": {},
            "ci_distribution": []
        }
        
        for perfil in self.perfiles:
            # Diagnósticos
            diagnostico = perfil['diagnostico_formal']
            diversidad["diagnosticos"][diagnostico] = diversidad["diagnosticos"].get(diagnostico, 0) + 1
            
            # Canales de aprendizaje
            canal = perfil['canal_preferido']
            diversidad["canales_aprendizaje"][canal] = diversidad["canales_aprendizaje"].get(canal, 0) + 1
            
            # Niveles de apoyo
            apoyo = perfil['nivel_apoyo']
            diversidad["niveles_apoyo"][apoyo] = diversidad["niveles_apoyo"].get(apoyo, 0) + 1
            
            # Temperamentos
            temperamento = perfil['temperamento']
            diversidad["temperamentos"][temperamento] = diversidad["temperamentos"].get(temperamento, 0) + 1
            
            # CI (si está disponible)
            if perfil['ci_base'] != "no_evaluado":
                diversidad["ci_distribution"].append(perfil['ci_base'])
        
        return diversidad
    
    def _resumir_adaptaciones(self, materia: str) -> Dict:
        """Resume las adaptaciones implementadas para la materia"""
        
        adaptaciones = {
            "por_diagnostico": {},
            "por_canal": {},
            "estrategias_aplicadas": []
        }
        
        for perfil in self.perfiles:
            diagnostico = perfil['diagnostico_formal']
            canal = perfil['canal_preferido']
            
            if diagnostico != "ninguno":
                if diagnostico not in adaptaciones["por_diagnostico"]:
                    adaptaciones["por_diagnostico"][diagnostico] = []
                
                if diagnostico == "TEA_nivel_1":
                    adaptaciones["por_diagnostico"][diagnostico].extend([
                        "Rutinas claras", "Instrucciones visuales", "Tiempo extra"
                    ])
                elif diagnostico == "TDAH_combinado":
                    adaptaciones["por_diagnostico"][diagnostico].extend([
                        "Descansos frecuentes", "Actividades físicas", "Instrucciones cortas"
                    ])
                elif diagnostico == "altas_capacidades":
                    adaptaciones["por_diagnostico"][diagnostico].extend([
                        "Retos intelectuales", "Profundización", "Proyectos autónomos"
                    ])
            
            # Adaptaciones por canal
            if canal not in adaptaciones["por_canal"]:
                adaptaciones["por_canal"][canal] = 0
            adaptaciones["por_canal"][canal] += 1
        
        return adaptaciones
    
    def verificar_sistema(self) -> bool:
        """Verifica que todos los componentes del sistema estén listos"""
        
        print(" Verificando sistema de generación de actividades...")
        
        # Verificar perfiles
        if not self.perfiles:
            print("ERROR No se cargaron perfiles de estudiantes")
            return False
        print(f"OK {len(self.perfiles)} perfiles de estudiantes cargados")
        
        # Verificar Groq API
        try:
            test_result = self.groq_generator.generar_texto("Test de conexión", max_tokens=10)
            if "error" in test_result.lower():
                print("ERROR Groq API no está disponible")
                print("💡 Asegúrate de tener configurado tu GROQ_API_KEY")
                return False
            print("OK Groq API conectada correctamente")
        except Exception as e:
            print(f"ERROR Error conectando con Groq API: {e}")
            return False
        
        # Verificar templates
        try:
            test_perfil = self.perfiles[0]
            test_prompt = self.prompt_generator.generar_prompt_matematicas(test_perfil, "Fracciones")
            if len(test_prompt) > 100:
                print("OK Templates de prompts funcionando")
            else:
                print("ERROR Error en templates de prompts")
                return False
        except Exception as e:
            print(f"ERROR Error en templates: {e}")
            return False
        
        print(" Sistema listo para generar actividades educativas!")
        return True


def main():
    """Función principal de demostración"""
    
    print(" GENERADOR DE ACTIVIDADES EDUCATIVAS CON GROQ API")
    print("=" * 50)
    
    # Inicializar generador con modelo de Groq
    generador = GeneradorActividadesEducativas(modelo_groq="llama-3.1-8b-instant")
    
    # Verificar sistema
    if not generador.verificar_sistema():
        print("\nERROR El sistema no está listo. Revisa la configuración.")
        print("\n💡 Para usar el sistema necesitas:")
        print("  1. Configurar tu GROQ_API_KEY (export GROQ_API_KEY=tu_token)")
        print("  2. O crear un archivo .env con GROQ_API_KEY=tu_token")
        print("  3. Puedes obtener tu token en: https://console.groq.com/")
        return
    
    # Menú de opciones
    while True:
        print("\n OPCIONES DISPONIBLES:")
        print("1. Generar actividad individual")
        print("2. Generar UNA actividad grupal (todos en un archivo)")
        print("3. Generar UNA actividad colaborativa para toda el aula")
        print("4. Ver perfiles de estudiantes")
        print("5. Ver estadísticas de Groq API")
        print("6. Salir")
        
        opcion = input("\nSelecciona una opción (1-6): ").strip()
        
        if opcion == "1":
            # Actividad individual
            print("\n GENERACIÓN INDIVIDUAL")
            print(f"Estudiantes disponibles:")
            for perfil in generador.perfiles:
                print(f"  {perfil['id']}: {perfil['nombre']}")
            
            estudiante_id = input("ID del estudiante: ").strip()
            materia = input("Materia (Matemáticas/Lengua/Ciencias): ").strip()
            tema = input("Tema específico (opcional): ").strip() or None
            
            resultado = generador.generar_actividad_individual(estudiante_id, materia, tema)
            
            if resultado.get("success"):
                print(f"\nOK Actividad generada para {resultado['metadatos']['estudiante']['nombre']}")
                print(f" Tema: {resultado['metadatos']['actividad']['tema']}")
                
                # Guardar en archivo
                os.makedirs("actividades_generadas", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join("actividades_generadas", f"actividad_individual_{estudiante_id}_{timestamp}.txt")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"METADATOS:\n{json.dumps(resultado['metadatos'], indent=2, ensure_ascii=False)}\n\n")
                    f.write(f"ACTIVIDAD GENERADA:\n{resultado['actividad']}")
                
                print(f"Guardada en: {filename}")
            else:
                print(f"ERROR Error: {resultado.get('error')}")
        
        elif opcion == "2":
            # Actividad grupal (todos en un archivo)
            print("\n GENERACIÓN DE ACTIVIDAD GRUPAL")
            materia = input("Materia (Matemáticas/Lengua/Ciencias): ").strip()
            tema = input("Tema específico (opcional): ").strip() or None
            
            print(f"\n Generando actividad grupal de {materia} para 8 estudiantes...")
            resultado = generador.generar_actividades_aula_completa(materia, tema)
            
            if resultado.get("success"):
                print(f"\nOK Actividad grupal generada exitosamente")
                print(f"Archivo: {resultado['archivo']}")
                print(f"Estudiantes incluidos: {resultado['estudiantes_incluidos']}")
                print(f"Tipo: {resultado['tipo']}")
            else:
                print(f"ERROR {resultado.get('error', 'Error desconocido')}")
        
        elif opcion == "3":
            # Actividad colaborativa
            print("\n GENERACIÓN DE ACTIVIDAD COLABORATIVA")
            materia = input("Materia (Matemáticas/Lengua/Ciencias): ").strip()
            tema = input("Tema específico (opcional): ").strip() or None
            
            print(f"\n Generando UNA actividad colaborativa de {materia} para toda el aula...")
            resultado = generador.generar_actividad_colaborativa_aula(materia, tema)
            
            if resultado.get("success"):
                print(f"\nOK Actividad colaborativa generada exitosamente")
                print(f"Archivo: {resultado['archivo']}")
                print(f"Estudiantes incluidos: {resultado['estudiantes_incluidos']}")
                print(f"Tipo: {resultado['tipo']}")
            else:
                print(f"ERROR {resultado.get('error', 'Error desconocido')}")
        
        elif opcion == "4":
            # Ver perfiles
            print("\n PERFILES DE ESTUDIANTES:")
            for perfil in generador.perfiles:
                print(f"\n{perfil['id']}: {perfil['nombre']}")
                print(f"  Edad: {perfil['edad']} años")
                print(f"  Diagnóstico: {perfil['diagnostico_formal']}")
                print(f"  Canal preferido: {perfil['canal_preferido']}")
                print(f"  Nivel de apoyo: {perfil['nivel_apoyo']}")
        
        elif opcion == "5":
            # Estadísticas
            print(f"\n ESTADÍSTICAS DE GROQ API:")
            print(f"  Modelo utilizado: {generador.groq_generator.model_name}")
            print(f"  API URL: {generador.groq_generator.api_url}")
            print(f"  Estado: Conectado")
        
        elif opcion == "6":
            print("¡Hasta luego!")
            break
        
        else:
            print("ERROR Opción no válida")


if __name__ == "__main__":
    main()