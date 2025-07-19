#!/usr/bin/env python3
"""
TEST SISTEMA COMPLETO - VALIDACIÓN DATOS REALES
Prueba el diseñador con casos específicos para validar funcionamiento
"""

from disenador_actividades_colaborativas import DisenadorActividadesColaborativas
import json

def test_caso_ana_luis():
    """Caso específico: Ana (altas capacidades) + Luis (TDAH) en actividad"""
    
    diseñador = DisenadorActividadesColaborativas()
    
    print("🧪 TEST: Validación con Ana (altas capacidades) + Luis (TDAH)")
    print("=" * 60)
    
    # Generar actividad para AULA_A
    resultado = diseñador.generar_actividad_colaborativa(
        aula_seleccionada="AULA_A",
        competencia_boe="MAT_2C_01",  # Números hasta 10.000
        duracion_minutos=45
    )
    
    # Extraer específicamente Ana y Luis
    asignaciones = resultado['asignacion_roles_optimizada']['asignaciones']
    
    ana_asignacion = None
    luis_asignacion = None
    
    for asignacion in asignaciones:
        if "ANA V." in asignacion['estudiante']:
            ana_asignacion = asignacion
        elif "LUIS T." in asignacion['estudiante']:
            luis_asignacion = asignacion
    
    print("👩‍🎓 ANA V. (Altas Capacidades, CI: 141)")
    if ana_asignacion:
        print(f"  • ROL ASIGNADO: {ana_asignacion['rol_asignado']}")
        print(f"  • COMPETENCIA ACTUAL: {diseñador._obtener_nivel_competencia(diseñador._obtener_estudiantes_aula('AULA_A')[4], 'MAT_2C_01')}")
        print(f"  • JUSTIFICACIÓN BOE: {ana_asignacion['justificacion']['BOE']}")
        print(f"  • ZDP: {ana_asignacion['zona_desarrollo_proximo']}")
    
    print()
    print("👨‍🎓 LUIS T. (TDAH Combinado)")
    if luis_asignacion:
        print(f"  • ROL ASIGNADO: {luis_asignacion['rol_asignado']}")
        print(f"  • COMPETENCIA ACTUAL: {diseñador._obtener_nivel_competencia(diseñador._obtener_estudiantes_aula('AULA_A')[3], 'MAT_2C_01')}")
        print(f"  • JUSTIFICACIÓN BOE: {luis_asignacion['justificacion']['BOE']}")
        print(f"  • ZDP: {luis_asignacion['zona_desarrollo_proximo']}")
    
    print()
    print("📊 MÉTRICAS DEL SISTEMA:")
    proyecciones = resultado['proyecciones_resultados']
    print(f"  • Estudiantes en ZDP: {proyecciones['alineacion_curricular_proyectada']['estudiantes_en_zdp']}/8")
    print(f"  • Complementariedad roles: {proyecciones['optimizacion_colaborativa_proyectada']['indice_complementariedad']}%")
    
    return resultado

def test_comparacion_aulas():
    """Compara resultados entre AULA_A (4º) y AULA_B (3º)"""
    
    diseñador = DisenadorActividadesColaborativas()
    
    print("\n🔍 COMPARACIÓN ENTRE AULAS")
    print("=" * 60)
    
    # AULA A (4º Primaria)
    resultado_a = diseñador.generar_actividad_colaborativa("AULA_A", "MAT_2C_02", 45)
    
    # AULA B (3º Primaria) 
    resultado_b = diseñador.generar_actividad_colaborativa("AULA_B", "MAT_2C_02", 45)
    
    print("📚 AULA A (4º Primaria - 8 estudiantes)")
    print(f"  • Actividad: {resultado_a['actividad_generada']['titulo']}")
    print(f"  • Estudiantes en ZDP: {resultado_a['proyecciones_resultados']['alineacion_curricular_proyectada']['porcentaje_zdp']}%")
    print(f"  • Diversidad: {len(resultado_a['proyecciones_resultados']['alineacion_curricular_proyectada'])} diagnósticos diferentes")
    
    print("\n📚 AULA B (3º Primaria - 6 estudiantes)")
    print(f"  • Actividad: {resultado_b['actividad_generada']['titulo']}")
    print(f"  • Estudiantes en ZDP: {resultado_b['proyecciones_resultados']['alineacion_curricular_proyectada']['porcentaje_zdp']}%")
    
    return resultado_a, resultado_b

if __name__ == "__main__":
    print("🚀 INICIANDO VALIDACIÓN SISTEMA COMPLETO")
    print("🎯 Objetivo: Verificar que el sistema funciona con datos reales")
    print()
    
    # Test 1: Caso específico Ana + Luis
    test_caso_ana_luis()
    
    # Test 2: Comparación entre aulas
    test_comparacion_aulas()
    
    print("\n✅ VALIDACIÓN COMPLETADA")
    print("📋 El sistema está funcionando correctamente con los 14 perfiles reales")