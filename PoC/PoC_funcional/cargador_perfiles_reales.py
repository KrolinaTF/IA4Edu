#!/usr/bin/env python3
"""
CARGADOR DE PERFILES REALES
Extrae y estructura los 14 perfiles reales de estudiantes desde aulas_piloto
"""

import json
import re
import os
from typing import Dict, List

class CargadorPerfilesReales:
    def __init__(self):
        self.ruta_aulas = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/actividades/poc_datos/aulas_piloto"
        self.ruta_indice = f"{self.ruta_aulas}/indice_estudiante.json"
        
    def cargar_todos_los_perfiles(self) -> Dict:
        """Carga y estructura los 14 perfiles reales"""
        
        # Cargar índice para obtener metadatos
        with open(self.ruta_indice, 'r', encoding='utf-8') as f:
            indice = json.load(f)
        
        perfiles_estructurados = {
            "metadatos": {
                "total_estudiantes": 14,
                "fecha_carga": "2025-07-18",
                "fuente": "aulas_piloto_reales",
                "version": "1.0_real"
            },
            "aulas": {}
        }
        
        # Procesar cada aula
        for aula_id, aula_data in indice["aulas"].items():
            perfiles_estructurados["aulas"][aula_id] = {
                "descripcion": aula_data["descripcion"],
                "estudiantes": {}
            }
            
            # Procesar cada estudiante del aula
            for estudiante_meta in aula_data["estudiantes"]:
                perfil_completo = self._cargar_perfil_individual(estudiante_meta["id"])
                if perfil_completo:
                    perfiles_estructurados["aulas"][aula_id]["estudiantes"][estudiante_meta["id"]] = perfil_completo
        
        return perfiles_estructurados
    
    def _cargar_perfil_individual(self, estudiante_id: str) -> Dict:
        """Carga y estructura un perfil individual"""
        archivo_path = f"{self.ruta_aulas}/{estudiante_id.zfill(3)}.txt"
        
        if not os.path.exists(archivo_path):
            print(f"⚠️ Archivo no encontrado: {archivo_path}")
            return {}
        
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            return self._parsear_perfil(contenido)
            
        except Exception as e:
            print(f"❌ Error cargando {archivo_path}: {e}")
            return {}
    
    def _parsear_perfil(self, contenido: str) -> Dict:
        """Parsea el contenido del archivo de perfil y extrae información estructurada"""
        
        perfil = {
            "datos_basicos": {},
            "perfil_sintesis": {},
            "competencias_matematicas": {},
            "competencias_lengua": {},
            "competencias_ciencias": {},
            "necesidades_dua_inferidas": [],
            "fortalezas_inferidas": [],
            "rol_colaborativo_optimo": ""
        }
        
        # Extraer datos básicos
        perfil["datos_basicos"] = self._extraer_datos_basicos(contenido)
        
        # Extraer perfil síntesis
        perfil["perfil_sintesis"] = self._extraer_perfil_sintesis(contenido)
        
        # Extraer competencias por área
        perfil["competencias_matematicas"] = self._extraer_competencias_area(contenido, "MATEMÁTICAS")
        perfil["competencias_lengua"] = self._extraer_competencias_area(contenido, "LENGUA")
        perfil["competencias_ciencias"] = self._extraer_competencias_area(contenido, "CIENCIAS")
        
        # Inferir necesidades DUA basadas en diagnóstico y perfil
        perfil["necesidades_dua_inferidas"] = self._inferir_necesidades_dua(perfil["perfil_sintesis"])
        
        # Inferir fortalezas para colaboración
        perfil["fortalezas_inferidas"] = self._inferir_fortalezas_colaboracion(perfil["perfil_sintesis"], 
                                                                             perfil["competencias_matematicas"])
        
        # Calcular rol colaborativo óptimo
        perfil["rol_colaborativo_optimo"] = self._calcular_rol_colaborativo_optimo(perfil)
        
        return perfil
    
    def _extraer_datos_basicos(self, contenido: str) -> Dict:
        """Extrae ID, nombre, fecha nacimiento, aula"""
        datos = {}
        
        for linea in contenido.split('\n')[:10]:  # Solo las primeras líneas
            if linea.startswith('ID:'):
                datos['id'] = linea.split(':', 1)[1].strip()
            elif linea.startswith('NOMBRE:'):
                datos['nombre'] = linea.split(':', 1)[1].strip()
            elif linea.startswith('FECHA_NACIMIENTO:'):
                datos['fecha_nacimiento'] = linea.split(':', 1)[1].strip()
            elif linea.startswith('AULA_ASIGNADA:'):
                datos['aula'] = linea.split(':', 1)[1].strip()
        
        return datos
    
    def _extraer_perfil_sintesis(self, contenido: str) -> Dict:
        """Extrae perfil síntesis"""
        sintesis = {}
        
        # Buscar sección de perfil síntesis
        seccion_sintesis = re.search(r'=== PERFIL_SÍNTESIS ===(.*?)===.*?===', contenido, re.DOTALL)
        if seccion_sintesis:
            contenido_sintesis = seccion_sintesis.group(1)
            
            for linea in contenido_sintesis.split('\n'):
                linea = linea.strip()
                if ':' in linea and not linea.startswith('='):
                    clave, valor = linea.split(':', 1)
                    sintesis[clave.strip()] = valor.strip()
        
        return sintesis
    
    def _extraer_competencias_area(self, contenido: str, area: str) -> Dict:
        """Extrae competencias de un área específica (MATEMÁTICAS, LENGUA, CIENCIAS)"""
        competencias = {}
        
        # Buscar sección del área
        patron = rf'{area}\s+(.*?)(?={area.replace("ÁTICAS", "").replace("GUA", "").replace("CIAS", "")}|\n\n|$)'
        seccion = re.search(patron, contenido, re.DOTALL)
        
        if seccion:
            contenido_area = seccion.group(1)
            
            for linea in contenido_area.split('\n'):
                linea = linea.strip()
                if ':' in linea and not linea.startswith('=') and len(linea.split(':')) == 2:
                    competencia, estado = linea.split(':', 1)
                    competencias[competencia.strip()] = estado.strip()
        
        return competencias
    
    def _inferir_necesidades_dua(self, perfil_sintesis: Dict) -> List[str]:
        """Infiere necesidades DUA basadas en diagnóstico y características"""
        necesidades = []
        
        diagnostico = perfil_sintesis.get('diagnóstico_formal', '').lower()
        canal = perfil_sintesis.get('canal_preferido', '').lower()
        apoyo = perfil_sintesis.get('nivel_apoyo', '').lower()
        agrupamiento = perfil_sintesis.get('agrupamiento_óptimo', '').lower()
        
        # Según diagnóstico
        if 'tea' in diagnostico:
            necesidades.extend([
                "estructura_visual_clara",
                "instrucciones_paso_a_paso", 
                "rutinas_predecibles",
                "tiempo_extra_procesamiento",
                "evitar_cambios_repentinos"
            ])
        elif 'tdah_combinado' in diagnostico:
            necesidades.extend([
                "fragmentacion_tareas",
                "movimiento_fisico_permitido",
                "motivacion_extrinseca", 
                "pausas_frecuentes",
                "recordatorios_visuales"
            ])
        elif 'tdah_inatento' in diagnostico:
            necesidades.extend([
                "recordatorios_suaves",
                "trabajo_en_pareja",
                "instrucciones_repetidas",
                "atencion_sostenida_limitada"
            ])
        elif 'altas_capacidades' in diagnostico:
            necesidades.extend([
                "ampliacion_curricular",
                "autonomia_aprendizaje",
                "desafios_cognitivos",
                "oportunidades_mentoria"
            ])
        
        # Según canal preferido
        if 'visual' in canal:
            necesidades.append("apoyo_visual_prioritario")
        elif 'auditivo' in canal:
            necesidades.append("instrucciones_orales_claras")
        elif 'kinestésico' in canal or 'kinestesico' in canal:
            necesidades.append("aprendizaje_manipulativo")
        
        # Según nivel de apoyo
        if 'alto' in apoyo:
            necesidades.append("apoyo_intensivo_necesario")
        elif 'bajo' in apoyo:
            necesidades.append("autonomia_alta_posible")
        
        return list(set(necesidades))  # Eliminar duplicados
    
    def _inferir_fortalezas_colaboracion(self, perfil_sintesis: Dict, competencias_mates: Dict) -> List[str]:
        """Infiere fortalezas para colaboración basadas en perfil y competencias"""
        fortalezas = []
        
        # Según CI
        ci = perfil_sintesis.get('CI_base', '')
        if ci and ci.isdigit() and int(ci) > 130:
            fortalezas.append("razonamiento_superior")
        elif ci and ci.isdigit() and int(ci) > 110:
            fortalezas.append("capacidad_cognitiva_alta")
        
        # Según temperamento
        temperamento = perfil_sintesis.get('temperamento_base', '').lower()
        if 'reflexivo' in temperamento:
            fortalezas.append("analisis_profundo")
        elif 'impulsivo' in temperamento:
            fortalezas.append("rapidez_decision")
        
        # Según competencias matemáticas
        superadas = [comp for comp, estado in competencias_mates.items() if 'SUPERADO' in estado]
        conseguidas = [comp for comp, estado in competencias_mates.items() if 'CONSEGUIDO' in estado]
        
        if len(superadas) > 2:
            fortalezas.append("experticia_matematica")
        elif len(conseguidas) > 3:
            fortalezas.append("competencia_matematica_solida")
        
        # Según agrupamiento óptimo
        agrupamiento = perfil_sintesis.get('agrupamiento_óptimo', '').lower()
        if 'individual' in agrupamiento:
            fortalezas.append("trabajo_autonomo_efectivo")
        elif 'grupos' in agrupamiento:
            fortalezas.append("colaboracion_natural")
        
        return fortalezas
    
    def _calcular_rol_colaborativo_optimo(self, perfil: Dict) -> str:
        """Calcula rol colaborativo óptimo basado en todo el perfil"""
        diagnostico = perfil["perfil_sintesis"].get('diagnóstico_formal', '').lower()
        fortalezas = perfil["fortalezas_inferidas"]
        
        # Roles específicos por diagnóstico y fortalezas
        if 'tea' in diagnostico:
            if 'experticia_matematica' in fortalezas:
                return "especialista_precision_matematica"
            else:
                return "verificador_detalle_estructurado"
                
        elif 'tdah_combinado' in diagnostico:
            return "coordinador_dinamico_movil"
            
        elif 'altas_capacidades' in diagnostico:
            if 'razonamiento_superior' in fortalezas:
                return "director_estrategico_mentor"
            else:
                return "lider_cognitivo_ampliacion"
                
        elif 'colaboracion_natural' in fortalezas:
            return "facilitador_colaboracion"
            
        elif 'trabajo_autonomo_efectivo' in fortalezas:
            return "especialista_individual_apoyo"
            
        else:
            return "colaborador_equilibrado_adaptativo"
    
    def guardar_perfiles_estructurados(self, perfiles: Dict, archivo_salida: str):
        """Guarda los perfiles estructurados en archivo JSON"""
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(perfiles, f, indent=2, ensure_ascii=False)
        print(f"✅ Perfiles guardados en: {archivo_salida}")

def main():
    """Función principal para cargar y estructurar todos los perfiles"""
    print("🔄 CARGANDO PERFILES REALES DE 14 ESTUDIANTES...")
    
    cargador = CargadorPerfilesReales()
    perfiles_completos = cargador.cargar_todos_los_perfiles()
    
    # Guardar resultado
    archivo_salida = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/actividades/PoC/perfiles_reales_14_estudiantes.json"
    cargador.guardar_perfiles_estructurados(perfiles_completos, archivo_salida)
    
    # Mostrar resumen
    total_cargados = sum(len(aula["estudiantes"]) for aula in perfiles_completos["aulas"].values())
    print(f"📊 RESUMEN:")
    print(f"• Total estudiantes cargados: {total_cargados}")
    print(f"• Aulas procesadas: {len(perfiles_completos['aulas'])}")
    
    for aula_id, aula_data in perfiles_completos["aulas"].items():
        print(f"• {aula_id}: {len(aula_data['estudiantes'])} estudiantes")
        
        # Mostrar ejemplo de un estudiante
        if aula_data["estudiantes"]:
            primer_estudiante = list(aula_data["estudiantes"].values())[0]
            print(f"  Ejemplo: {primer_estudiante['datos_basicos']['nombre']} - {primer_estudiante['rol_colaborativo_optimo']}")

if __name__ == "__main__":
    main()