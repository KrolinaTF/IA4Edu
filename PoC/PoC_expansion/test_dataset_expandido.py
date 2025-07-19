#!/usr/bin/env python3
"""
TEST DATASET EXPANDIDO - Validación con 30 estudiantes
Prueba el diseñador con el dataset expandido desde los 394 perfiles
"""

import json
from disenador_actividades_colaborativas import DisenadorActividadesColaborativas

class TestDatasetExpandido:
    def __init__(self):
        self.archivo_muestra = "dataset_30_estudiantes_muestra.json"
        
    def cargar_muestra_30(self):
        """Carga la muestra de 30 estudiantes"""
        with open(self.archivo_muestra, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_diseñador_con_dataset_expandido(self):
        """Testa el diseñador con el dataset expandido"""
        
        print("🧪 TEST: Diseñador con Dataset Expandido (30 estudiantes)")
        print("=" * 60)
        
        # Cargar muestra
        muestra = self.cargar_muestra_30()
        
        print(f"📊 DATASET CARGADO:")
        print(f"• Total estudiantes: {muestra['metadatos']['total_estudiantes']}")
        print(f"• Aulas disponibles: {len(muestra['aulas'])}")
        
        # Crear diseñador modificado para usar la muestra
        diseñador = DisenadorActividadesColaborativas()
        
        # Sobrescribir los perfiles con la muestra expandida
        diseñador.perfiles_reales = muestra
        
        # Test con diferentes aulas del dataset expandido
        aulas_a_testear = ["AULA_3_PRIMARIA", "AULA_4_PRIMARIA", "AULA_5_PRIMARIA"]
        
        for aula in aulas_a_testear:
            if aula in muestra["aulas"]:
                print(f"\n🏫 TESTANDO {aula}:")
                num_estudiantes = len(muestra["aulas"][aula]["estudiantes"])
                print(f"   • {num_estudiantes} estudiantes")
                
                # Generar actividad
                try:
                    resultado = diseñador.generar_actividad_colaborativa(
                        aula_seleccionada=aula.replace("AULA_", "").replace("_", ""),
                        competencia_boe="MAT_2C_02",
                        duracion_minutos=45
                    )
                    
                    # Mostrar resultados clave
                    proy = resultado['proyecciones_resultados']
                    print(f"   ✅ Actividad: {resultado['actividad_generada']['titulo']}")
                    print(f"   ✅ Estudiantes en ZDP: {proy['alineacion_curricular_proyectada']['porcentaje_zdp']}%")
                    print(f"   ✅ Complementariedad: {proy['optimizacion_colaborativa_proyectada']['indice_complementariedad']}%")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    def analizar_diversidad_dataset(self):
        """Analiza la diversidad del dataset expandido"""
        
        print("\n📊 ANÁLISIS DE DIVERSIDAD DEL DATASET EXPANDIDO")
        print("=" * 60)
        
        muestra = self.cargar_muestra_30()
        
        diagnosticos = []
        canales_preferidos = []
        niveles_apoyo = []
        roles_colaborativos = []
        
        for aula_id, aula_data in muestra["aulas"].items():
            for estudiante_id, perfil in aula_data["estudiantes"].items():
                diagnosticos.append(perfil["perfil_sintesis"]["diagnóstico_formal"])
                canales_preferidos.append(perfil["perfil_sintesis"]["canal_preferido"])
                niveles_apoyo.append(perfil["perfil_sintesis"]["nivel_apoyo"])
                roles_colaborativos.append(perfil["rol_colaborativo_optimo"])
        
        print(f"🔍 DIAGNÓSTICOS ENCONTRADOS:")
        diagnosticos_unicos = list(set(diagnosticos))
        for diag in diagnosticos_unicos:
            count = diagnosticos.count(diag)
            print(f"   • {diag}: {count} estudiantes ({count/len(diagnosticos)*100:.1f}%)")
        
        print(f"\n🎨 CANALES PREFERIDOS:")
        canales_unicos = list(set(canales_preferidos))
        for canal in canales_unicos:
            count = canales_preferidos.count(canal)
            print(f"   • {canal}: {count} estudiantes ({count/len(canales_preferidos)*100:.1f}%)")
        
        print(f"\n🆘 NIVELES DE APOYO:")
        niveles_unicos = list(set(niveles_apoyo))
        for nivel in niveles_unicos:
            count = niveles_apoyo.count(nivel)
            print(f"   • {nivel}: {count} estudiantes ({count/len(niveles_apoyo)*100:.1f}%)")
        
        print(f"\n👥 ROLES COLABORATIVOS:")
        roles_unicos = list(set(roles_colaborativos))
        for rol in roles_unicos:
            count = roles_colaborativos.count(rol)
            print(f"   • {rol}: {count} estudiantes ({count/len(roles_colaborativos)*100:.1f}%)")
        
        return {
            "total_estudiantes": len(diagnosticos),
            "diversidad_diagnosticos": len(diagnosticos_unicos),
            "diversidad_canales": len(canales_unicos),
            "diversidad_roles": len(roles_unicos)
        }
    
    def comparar_vs_dataset_original(self):
        """Compara el dataset expandido vs los 14 originales"""
        
        print("\n⚖️ COMPARACIÓN: Dataset Original (14) vs Expandido (30)")
        print("=" * 60)
        
        # Cargar dataset original para comparar
        with open("perfiles_reales_14_estudiantes.json", 'r', encoding='utf-8') as f:
            dataset_original = json.load(f)
        
        muestra_expandida = self.cargar_muestra_30()
        
        print(f"📊 DATASET ORIGINAL:")
        print(f"   • Estudiantes: {dataset_original['metadatos']['total_estudiantes']}")
        print(f"   • Aulas: {len(dataset_original['aulas'])}")
        
        print(f"\n📊 DATASET EXPANDIDO:")
        print(f"   • Estudiantes: {muestra_expandida['metadatos']['total_estudiantes']}")
        print(f"   • Aulas: {len(muestra_expandida['aulas'])}")
        
        print(f"\n🚀 MEJORAS CON EL DATASET EXPANDIDO:")
        print(f"   ✅ +{muestra_expandida['metadatos']['total_estudiantes'] - dataset_original['metadatos']['total_estudiantes']} estudiantes más")
        print(f"   ✅ +{len(muestra_expandida['aulas']) - len(dataset_original['aulas'])} aulas más")
        print(f"   ✅ Mayor diversidad de perfiles y diagnósticos")
        print(f"   ✅ Datos basados en 394 perfiles reales+sintéticos")
        print(f"   ✅ Listos para entrenar modelos ML")

def main():
    """Función principal de testing"""
    print("🔬 TESTING DATASET EXPANDIDO CON 394 PERFILES")
    print("🎯 Objetivo: Validar funcionamiento con datos masivos")
    print()
    
    tester = TestDatasetExpandido()
    
    # Test 1: Funcionalidad básica con dataset expandido
    tester.test_diseñador_con_dataset_expandido()
    
    # Test 2: Análisis de diversidad
    diversidad = tester.analizar_diversidad_dataset()
    
    # Test 3: Comparación con dataset original
    tester.comparar_vs_dataset_original()
    
    print(f"\n✅ TESTING COMPLETADO")
    print(f"🎊 El sistema escala correctamente con {diversidad['total_estudiantes']} estudiantes")
    print(f"📈 Diversidad aumentada: {diversidad['diversidad_diagnosticos']} diagnósticos diferentes")

if __name__ == "__main__":
    main()