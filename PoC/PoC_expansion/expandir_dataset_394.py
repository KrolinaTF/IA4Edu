#!/usr/bin/env python3
"""
EXPANDIR DATASET - De 14 a 394+ estudiantes
Convierte los 394 perfiles reales+sintéticos al formato del diseñador colaborativo
"""

import json
import random
from typing import Dict, List
from pathlib import Path

class ExpandirDataset394:
    def __init__(self):
        self.ruta_base = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/processed/por_curso"
        self.cursos_disponibles = ["1_primaria", "2_primaria", "3_primaria", "4_primaria", "5_primaria", "6_primaria"]
        
    def cargar_todos_los_cursos(self) -> Dict:
        """Carga todos los perfiles de los 6 cursos disponibles"""
        
        perfiles_completos = {
            "metadatos": {
                "total_estudiantes": 0,
                "fecha_expansion": "2025-07-18",
                "fuente": "dataset_394_reales_sinteticos", 
                "version": "2.0_expandido"
            },
            "aulas": {}
        }
        
        for curso in self.cursos_disponibles:
            archivo_curso = f"{self.ruta_base}/perfiles_{curso}.json"
            
            try:
                with open(archivo_curso, 'r', encoding='utf-8') as f:
                    datos_curso = json.load(f)
                
                print(f"✅ Cargando {curso}: {datos_curso['metadata']['total_perfiles']} estudiantes")
                
                # Convertir perfiles del curso al formato del diseñador
                aula_convertida = self._convertir_curso_a_aula(curso, datos_curso)
                perfiles_completos["aulas"][f"AULA_{curso.upper()}"] = aula_convertida
                perfiles_completos["metadatos"]["total_estudiantes"] += len(aula_convertida["estudiantes"])
                
            except FileNotFoundError:
                print(f"⚠️ No encontrado: {archivo_curso}")
                
        return perfiles_completos
    
    def _convertir_curso_a_aula(self, curso: str, datos_curso: Dict) -> Dict:
        """Convierte un curso completo al formato de aula del diseñador"""
        
        aula_convertida = {
            "descripcion": f"{curso.replace('_', ' ').title()} - {datos_curso['metadata']['total_perfiles']} estudiantes",
            "estudiantes": {}
        }
        
        # Convertir cada perfil individual
        for i, perfil_original in enumerate(datos_curso["perfiles"]):
            estudiante_id = f"{curso}_{str(i+1).zfill(3)}"
            perfil_convertido = self._convertir_perfil_individual(estudiante_id, perfil_original, curso)
            aula_convertida["estudiantes"][estudiante_id] = perfil_convertido
            
        return aula_convertida
    
    def _convertir_perfil_individual(self, estudiante_id: str, perfil_original: Dict, curso: str) -> Dict:
        """Convierte un perfil individual al formato del diseñador colaborativo"""
        
        # Extraer información clave del perfil original
        identificacion = perfil_original.get("identificacion", {})
        perfil_academico = perfil_original.get("perfil_academico", {})
        perfil_cognitivo = perfil_original.get("perfil_cognitivo", {})
        perfil_conductual = perfil_original.get("perfil_conductual", {})
        estilo_aprendizaje = perfil_original.get("estilo_aprendizaje", {})
        metadatos = perfil_original.get("metadatos", {})
        
        # Generar nombre sintético
        nombres = ["ALEX", "MARÍA", "CARLOS", "ANA", "LUIS", "SARA", "DIEGO", "ELENA", "PABLO", "EMMA"]
        apellidos = ["M.", "L.", "R.", "V.", "T.", "G.", "S.", "K.", "P.", "B."]
        nombre_generado = f"{random.choice(nombres)} {random.choice(apellidos)}"
        
        perfil_convertido = {
            "datos_basicos": {
                "id": estudiante_id,
                "fecha_nacimiento": f"20{16 - identificacion.get('edad', 9)}",  # Aproximado
                "nombre": nombre_generado,
                "aula": f"AULA_{curso.upper()}"
            },
            
            "perfil_sintesis": {
                "CI_base": str(perfil_cognitivo.get("ci_estimado", 100)),
                "temperamento_base": self._inferir_temperamento(perfil_conductual),
                "canal_preferido": estilo_aprendizaje.get("canal_preferido", "visual"),
                "nivel_apoyo": self._calcular_nivel_apoyo(perfil_academico, perfil_conductual),
                "tolerancia_frustración": self._mapear_tolerancia_frustracion(perfil_conductual.get("tolerancia_frustracion", 3)),
                "agrupamiento_óptimo": estilo_aprendizaje.get("agrupamiento_optimo", "grupos"),
                "diagnóstico_formal": self._inferir_diagnostico(identificacion, perfil_cognitivo, perfil_conductual)
            },
            
            "competencias_matematicas": self._convertir_competencias_matematicas(perfil_academico, curso),
            "competencias_lengua": self._convertir_competencias_lengua(perfil_academico, curso),
            "competencias_ciencias": self._convertir_competencias_ciencias(perfil_academico, curso),
            
            "necesidades_dua_inferidas": self._inferir_necesidades_dua_394(perfil_conductual, estilo_aprendizaje),
            "fortalezas_inferidas": self._inferir_fortalezas_394(perfil_academico, perfil_cognitivo),
            "rol_colaborativo_optimo": self._calcular_rol_colaborativo_394(perfil_academico, perfil_conductual, estilo_aprendizaje)
        }
        
        return perfil_convertido
    
    def _inferir_temperamento(self, perfil_conductual: Dict) -> str:
        """Infiere temperamento basado en impulsividad y nivel de actividad"""
        impulsividad = perfil_conductual.get("impulsividad", 3)
        nivel_actividad = perfil_conductual.get("nivel_actividad", 3)
        
        if impulsividad >= 4 or nivel_actividad >= 4:
            return "impulsivo"
        elif impulsividad <= 2 and nivel_actividad <= 2:
            return "reflexivo"
        else:
            return "equilibrado"
    
    def _calcular_nivel_apoyo(self, perfil_academico: Dict, perfil_conductual: Dict) -> str:
        """Calcula nivel de apoyo necesario"""
        dificultades = len(perfil_academico.get("dificultades_observadas", []))
        regulacion_emocional = perfil_conductual.get("regulacion_emocional", 3)
        
        if dificultades >= 3 or regulacion_emocional <= 2:
            return "alto"
        elif dificultades <= 1 and regulacion_emocional >= 4:
            return "bajo"
        else:
            return "medio"
    
    def _mapear_tolerancia_frustracion(self, valor_numerico: int) -> str:
        """Convierte valor numérico a descriptivo"""
        if valor_numerico <= 2:
            return "baja"
        elif valor_numerico >= 4:
            return "alta"
        else:
            return "media"
    
    def _inferir_diagnostico(self, identificacion: Dict, perfil_cognitivo: Dict, perfil_conductual: Dict) -> str:
        """Infiere diagnóstico basado en el perfil completo"""
        diagnostico_oficial = identificacion.get("diagnostico_oficial")
        if diagnostico_oficial:
            return diagnostico_oficial
            
        # Inferencias basadas en patrones - con valores por defecto seguros
        ci = perfil_cognitivo.get("ci_estimado", 100) or 100
        atencion_sostenida = perfil_cognitivo.get("atencion_sostenida", 3) or 3
        impulsividad = perfil_conductual.get("impulsividad", 3) or 3
        control_inhibitorio = perfil_cognitivo.get("control_inhibitorio", 3) or 3
        
        if ci >= 130:
            return "altas_capacidades"
        elif atencion_sostenida <= 2 and impulsividad >= 4:
            return "TDAH_combinado"
        elif atencion_sostenida <= 2 and control_inhibitorio <= 2:
            return "TDAH_inatento"
        else:
            return "ninguno"
    
    def _convertir_competencias_matematicas(self, perfil_academico: Dict, curso: str) -> Dict:
        """Convierte competencias académicas a formato BOE"""
        nivel_matematicas = perfil_academico.get("matematicas", 3)
        
        # Mapear nivel académico (1-5) a estados curriculares
        estados = ["EMERGENTE", "INICIADO", "EN_PROCESO", "CONSEGUIDO", "SUPERADO"]
        estado_base = estados[min(nivel_matematicas - 1, 4)]
        
        return {
            "Números hasta 10.000": estado_base,
            "Operaciones complejas": estados[max(0, nivel_matematicas - 2)],
            "Fracciones simples": estados[max(0, nivel_matematicas - 2)],
            "Conversiones medidas": estados[max(0, nivel_matematicas - 1)],
            "Área rectángulos": estados[max(0, nivel_matematicas - 2)],
            "Probabilidad básica": estados[max(0, nivel_matematicas - 3)],
            "Divisiones con resto": estados[max(0, nivel_matematicas - 1)],
            "Porcentajes básicos": estados[max(0, nivel_matematicas - 3)],
            "Decimales avanzados": estados[max(0, nivel_matematicas - 2)]
        }
    
    def _convertir_competencias_lengua(self, perfil_academico: Dict, curso: str) -> Dict:
        """Convierte competencias de lengua"""
        nivel_lectura = perfil_academico.get("lectura", 3)
        nivel_escritura = perfil_academico.get("escritura", 3)
        
        estados = ["EMERGENTE", "INICIADO", "EN_PROCESO", "CONSEGUIDO", "SUPERADO"]
        
        return {
            "Análisis sintáctico": estados[min(nivel_lectura - 1, 4)],
            "Tiempos verbales": estados[min(nivel_escritura - 1, 4)],
            "Ortografía completa": estados[min(nivel_escritura - 1, 4)],
            "Textos informativos": estados[min(nivel_lectura - 1, 4)],
            "Teatro/representación": estados[min((nivel_lectura + nivel_escritura) // 2 - 1, 4)],
            "Vocabulario técnico": estados[min(nivel_lectura - 1, 4)],
            "Investigación fuentes": estados[min(nivel_lectura - 1, 4)],
            "Argumentación": estados[min((nivel_lectura + nivel_escritura) // 2 - 1, 4)]
        }
    
    def _convertir_competencias_ciencias(self, perfil_academico: Dict, curso: str) -> Dict:
        """Convierte competencias de ciencias"""
        nivel_ciencias = perfil_academico.get("ciencias", 3)
        
        estados = ["EMERGENTE", "INICIADO", "EN_PROCESO", "CONSEGUIDO", "SUPERADO"]
        estado_base = estados[min(nivel_ciencias - 1, 4)]
        
        return {
            "Fuerzas físicas": estado_base,
            "Método científico": estados[max(0, nivel_ciencias - 1)],
            "Reproducción/ciclos": estado_base,
            "Cuerpo humano": estado_base,
            "Rocas/minerales": estados[max(0, nivel_ciencias - 1)],
            "Electricidad": estados[max(0, nivel_ciencias - 2)]
        }
    
    def _inferir_necesidades_dua_394(self, perfil_conductual: Dict, estilo_aprendizaje: Dict) -> List[str]:
        """Infiere necesidades DUA del perfil 394"""
        necesidades = []
        
        # Basado en canal preferido
        canal = estilo_aprendizaje.get("canal_preferido", "visual")
        if canal == "visual":
            necesidades.append("apoyo_visual_prioritario")
        elif canal == "auditivo":
            necesidades.append("instrucciones_orales_claras")
        elif canal == "kinestesico":
            necesidades.append("aprendizaje_manipulativo")
            
        # Basado en agrupamiento
        agrupamiento = estilo_aprendizaje.get("agrupamiento_optimo", "grupos")
        if agrupamiento == "individual":
            necesidades.append("autonomia_alta_posible")
        elif agrupamiento == "pareja":
            necesidades.append("trabajo_en_pareja")
            
        # Basado en necesidades de estructura
        estructura = estilo_aprendizaje.get("estructura_necesaria", 3)
        if estructura >= 4:
            necesidades.append("estructura_visual_clara")
            
        # Basado en triggers y motivadores
        triggers = perfil_conductual.get("triggers", [])
        if "presion_tiempo" in triggers:
            necesidades.append("tiempo_extra_procesamiento")
        if "critica_publica" in triggers:
            necesidades.append("evaluacion_privada")
            
        motivadores = perfil_conductual.get("motivadores", [])
        if "autonomia" in motivadores:
            necesidades.append("autonomia_aprendizaje")
        if "reconocimiento" in motivadores:
            necesidades.append("feedback_positivo_frecuente")
            
        return list(set(necesidades))
    
    def _inferir_fortalezas_394(self, perfil_academico: Dict, perfil_cognitivo: Dict) -> List[str]:
        """Infiere fortalezas del perfil 394"""
        fortalezas = []
        
        # Basado en fortalezas observadas
        fortalezas_obs = perfil_academico.get("fortalezas_observadas", []) or []
        if "comprension_verbal" in fortalezas_obs:
            fortalezas.append("comunicacion_efectiva")
        if "vocabulario_rico" in fortalezas_obs:
            fortalezas.append("expresion_avanzada")
        if "atencion_sostenida" in fortalezas_obs:
            fortalezas.append("concentracion_prolongada")
        if "organizacion" in fortalezas_obs:
            fortalezas.append("planificacion_eficiente")
            
        # Basado en CI - manejo seguro de valores nulos
        ci = perfil_cognitivo.get("ci_estimado", 100)
        if ci is not None:
            if ci >= 130:
                fortalezas.append("razonamiento_superior")
            elif ci >= 115:
                fortalezas.append("capacidad_cognitiva_alta")
            
        # Basado en flexibilidad cognitiva
        flexibilidad = perfil_cognitivo.get("flexibilidad_cognitiva", 3) or 3
        if flexibilidad >= 4:
            fortalezas.append("adaptabilidad_alta")
        
        # Si no se encontraron fortalezas específicas, asignar una por defecto
        if not fortalezas:
            fortalezas.append("colaboracion_natural")
            
        return fortalezas
    
    def _calcular_rol_colaborativo_394(self, perfil_academico: Dict, perfil_conductual: Dict, estilo_aprendizaje: Dict) -> str:
        """Calcula rol colaborativo óptimo basado en perfil 394"""
        
        # Factores clave - manejo seguro de valores nulos
        matematicas = perfil_academico.get("matematicas", 3) or 3
        habilidades_sociales = perfil_conductual.get("habilidades_sociales", 3) or 3
        agrupamiento = estilo_aprendizaje.get("agrupamiento_optimo", "grupos") or "grupos"
        fortalezas = perfil_academico.get("fortalezas_observadas", []) or []
        
        # Lógica de asignación
        if matematicas >= 4 and habilidades_sociales >= 4:
            return "director_estrategico_mentor"
        elif "organizacion" in fortalezas and habilidades_sociales >= 3:
            return "coordinador_procesos_estructurado"
        elif agrupamiento == "individual" and matematicas >= 3:
            return "especialista_individual_apoyo"
        elif habilidades_sociales >= 4:
            return "facilitador_colaboracion"
        elif "atencion_sostenida" in fortalezas:
            return "verificador_detalle_estructurado"
        else:
            return "colaborador_equilibrado_adaptativo"
    
    def seleccionar_muestra_estratificada(self, dataset_completo: Dict, num_estudiantes: int = 30) -> Dict:
        """Selecciona muestra estratificada representativa"""
        
        dataset_muestra = {
            "metadatos": {
                "total_estudiantes": 0,
                "fecha_seleccion": "2025-07-18",
                "fuente": f"muestra_estratificada_{num_estudiantes}_de_394",
                "version": "2.1_muestra"
            },
            "aulas": {}
        }
        
        # Seleccionar estudiantes por curso de forma proporcional
        estudiantes_por_curso = num_estudiantes // len(dataset_completo["aulas"])
        
        for aula_id, aula_data in dataset_completo["aulas"].items():
            estudiantes_aula = list(aula_data["estudiantes"].items())
            
            # Selección aleatoria estratificada
            if len(estudiantes_aula) > estudiantes_por_curso:
                seleccionados = random.sample(estudiantes_aula, estudiantes_por_curso)
            else:
                seleccionados = estudiantes_aula
                
            dataset_muestra["aulas"][aula_id] = {
                "descripcion": f"{aula_data['descripcion']} (Muestra: {len(seleccionados)} estudiantes)",
                "estudiantes": dict(seleccionados)
            }
            
            dataset_muestra["metadatos"]["total_estudiantes"] += len(seleccionados)
        
        return dataset_muestra
    
    def guardar_dataset_expandido(self, dataset: Dict, archivo_salida: str):
        """Guarda el dataset expandido"""
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        print(f"✅ Dataset expandido guardado en: {archivo_salida}")
        print(f"📊 Total estudiantes: {dataset['metadatos']['total_estudiantes']}")

def main():
    """Función principal para expandir el dataset"""
    print("🚀 EXPANDIENDO DATASET: De 14 a 394+ estudiantes")
    print("=" * 60)
    
    expandir = ExpandirDataset394()
    
    # Cargar todos los cursos (394 estudiantes)
    print("📂 Cargando todos los cursos disponibles...")
    dataset_completo = expandir.cargar_todos_los_cursos()
    
    print(f"\n✅ DATASET COMPLETO CARGADO:")
    print(f"• Total estudiantes: {dataset_completo['metadatos']['total_estudiantes']}")
    print(f"• Aulas creadas: {len(dataset_completo['aulas'])}")
    
    # Guardar dataset completo
    archivo_completo = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/actividades/PoC/dataset_394_estudiantes_completo.json"
    expandir.guardar_dataset_expandido(dataset_completo, archivo_completo)
    
    # Crear muestra estratificada de 30 estudiantes para testing inicial
    print("\n🎯 Creando muestra estratificada de 30 estudiantes...")
    dataset_muestra = expandir.seleccionar_muestra_estratificada(dataset_completo, 30)
    
    archivo_muestra = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/actividades/PoC/dataset_30_estudiantes_muestra.json"
    expandir.guardar_dataset_expandido(dataset_muestra, archivo_muestra)
    
    print("\n🎊 EXPANSIÓN COMPLETADA:")
    print("• Dataset completo: 394 estudiantes disponibles")
    print("• Muestra de testing: 30 estudiantes estratificados")
    print("• Listos para entrenar modelos ML")

if __name__ == "__main__":
    main()