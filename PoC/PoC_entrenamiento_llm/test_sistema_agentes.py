#!/usr/bin/env python3
"""
Script de prueba para el Sistema de Agentes CrewAI + Ollama
Ejecuta pruebas básicas del sistema multi-agente
"""

import os
import sys
import time
from datetime import datetime

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    
    print("🔍 Verificando dependencias...")
    
    dependencias = {
        'crewai': 'CrewAI framework',
        'crewai_tools': 'CrewAI tools',
        'requests': 'HTTP requests para Ollama',
        'json': 'JSON processing (built-in)',
        'os': 'OS utilities (built-in)',
        'datetime': 'Date/time utilities (built-in)'
    }
    
    faltantes = []
    
    for dep, descripcion in dependencias.items():
        try:
            if dep in ['json', 'os', 'datetime']:
                # Built-in modules
                __import__(dep)
            else:
                __import__(dep)
            print(f"  ✅ {dep}: {descripcion}")
        except ImportError:
            print(f"  ❌ {dep}: {descripcion}")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\n❌ Faltan {len(faltantes)} dependencias:")
        for dep in faltantes:
            print(f"  • {dep}")
        print(f"\n💡 Para instalar:")
        print(f"   pip install -r requirements_crewai.txt")
        return False
    
    print("✅ Todas las dependencias están disponibles")
    return True

def verificar_ollama():
    """Verifica que Ollama esté disponible"""
    
    print("\n🦙 Verificando conexión con Ollama...")
    
    try:
        import requests
        
        # Probar diferentes hosts comunes
        hosts_to_test = [
            "http://localhost:11434",
            "http://192.168.1.146:11434"  # Basado en tu configuración
        ]
        
        for host in hosts_to_test:
            try:
                response = requests.get(f"{host}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    print(f"  ✅ Ollama disponible en: {host}")
                    print(f"  📋 Modelos encontrados: {len(models)}")
                    
                    # Mostrar modelos disponibles
                    if models:
                        print("     Modelos disponibles:")
                        for model in models[:3]:  # Mostrar solo los primeros 3
                            name = model.get('name', 'unknown')
                            size = model.get('details', {}).get('parameter_size', 'N/A')
                            print(f"       • {name} ({size})")
                        if len(models) > 3:
                            print(f"       ... y {len(models) - 3} más")
                    
                    return host, models
                    
            except requests.exceptions.ConnectionError:
                print(f"  ❌ No se puede conectar a: {host}")
            except Exception as e:
                print(f"  ❌ Error en {host}: {e}")
        
        print("❌ No se pudo conectar a ningún servidor Ollama")
        return None, []
        
    except ImportError:
        print("❌ Módulo 'requests' no disponible")
        return None, []

def verificar_perfiles():
    """Verifica que el archivo de perfiles exista"""
    
    print("\n👥 Verificando archivo de perfiles...")
    
    perfiles_path = "perfiles_4_primaria.json"
    
    if os.path.exists(perfiles_path):
        try:
            import json
            with open(perfiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                estudiantes = data.get('estudiantes', [])
                print(f"  ✅ Archivo de perfiles encontrado")
                print(f"  👥 {len(estudiantes)} estudiantes cargados")
                
                # Mostrar algunos ejemplos
                if estudiantes:
                    print("     Ejemplos:")
                    for est in estudiantes[:3]:
                        nombre = est.get('nombre', 'N/A')
                        diagnostico = est.get('diagnostico_formal', 'ninguno')
                        print(f"       • {est.get('id', 'N/A')}: {nombre} ({diagnostico})")
                
                return True, len(estudiantes)
        except Exception as e:
            print(f"  ❌ Error leyendo perfiles: {e}")
            return False, 0
    else:
        print(f"  ❌ Archivo no encontrado: {perfiles_path}")
        return False, 0

def test_sistema_basico():
    """Prueba básica del sistema sin ejecutar agentes completos"""
    
    print("\n🧪 INICIANDO PRUEBAS BÁSICAS DEL SISTEMA")
    print("=" * 50)
    
    # 1. Verificar dependencias
    if not verificar_dependencias():
        return False
    
    # 2. Verificar Ollama
    ollama_host, models = verificar_ollama()
    if not ollama_host:
        print("\n⚠️  Ollama no disponible. El sistema no funcionará completamente.")
        print("💡 Para continuar con las pruebas:")
        print("   1. Instala Ollama: https://ollama.ai")
        print("   2. Ejecuta: ollama serve")
        print("   3. Descarga un modelo: ollama pull llama3.2")
        return False
    
    # 3. Verificar perfiles
    perfiles_ok, num_estudiantes = verificar_perfiles()
    if not perfiles_ok:
        print("\n❌ Archivo de perfiles no disponible")
        return False
    
    # 4. Intentar importar el sistema
    print("\n🔧 Probando importación del sistema...")
    try:
        from sistema_agentes_crewai import SistemaAgentesEducativos
        print("  ✅ Sistema importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando sistema: {e}")
        return False
    
    # 5. Intentar inicializar (sin ejecutar agentes)
    print("\n⚙️  Probando inicialización...")
    try:
        # Extraer host sin protocolo para el constructor
        host = ollama_host.replace("http://", "").split(":")[0]
        
        # Buscar un modelo disponible
        modelo_usar = "llama3:latest"  # Default
        if models:
            modelo_usar = models[0].get('name', 'llama3:latest')
        
        print(f"  🎯 Usando host: {host}")
        print(f"  🤖 Usando modelo: {modelo_usar}")
        
        # Intentar crear el sistema (esto podría fallar si hay problemas con CrewAI)
        sistema = SistemaAgentesEducativos(
            ollama_host=host,
            ollama_model=modelo_usar,
            perfiles_path="perfiles_4_primaria.json"
        )
        
        print("  ✅ Sistema inicializado correctamente")
        
        # Verificar que los agentes se crearon
        print("  🤖 Verificando agentes...")
        agentes = ['agente_perfiles', 'agente_disenador', 'agente_colaborativo', 'agente_evaluador']
        for agente_name in agentes:
            if hasattr(sistema, agente_name):
                agente = getattr(sistema, agente_name)
                print(f"    ✅ {agente_name}: {agente.role}")
            else:
                print(f"    ❌ {agente_name}: No encontrado")
                return False
        
        print(f"\n🎉 ¡SISTEMA LISTO PARA USAR!")
        print(f"   📊 {num_estudiantes} estudiantes disponibles")
        print(f"   🤖 {len(agentes)} agentes especializados")
        print(f"   🦙 Ollama conectado en {ollama_host}")
        print(f"   🧠 Modelo: {modelo_usar}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error inicializando sistema: {e}")
        print(f"  🔍 Tipo de error: {type(e).__name__}")
        return False

def test_generacion_simple():
    """Prueba simple de generación (solo si el sistema básico funciona)"""
    
    print("\n🚀 PRUEBA DE GENERACIÓN SIMPLE")
    print("=" * 40)
    
    try:
        from sistema_agentes_crewai import SistemaAgentesEducativos
        
        # Configuración mínima
        sistema = SistemaAgentesEducativos(
            ollama_host="localhost",  # Ajustar si es necesario
            ollama_model="llama3:latest",
            perfiles_path="perfiles_4_primaria.json"
        )
        
        # Prueba rápida de análisis de perfiles
        print("🔍 Probando análisis de perfiles...")
        diversidad = sistema.perfil_tool._analizar_diversidad()
        print("✅ Análisis de diversidad completado")
        
        # No ejecutar agentes completos en la prueba (tomaría mucho tiempo)
        print("⚠️  Prueba de generación completa omitida (tomaría varios minutos)")
        print("💡 Para probar generación completa, ejecuta:")
        print("   python sistema_agentes_crewai.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de generación: {e}")
        return False

def main():
    """Función principal de pruebas"""
    
    print("🧪 SISTEMA DE PRUEBAS - CREWAI + OLLAMA PARA EDUCACIÓN")
    print("=" * 60)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar pruebas en secuencia
    pruebas = [
        ("Verificación básica del sistema", test_sistema_basico),
        ("Prueba de generación simple", test_generacion_simple)
    ]
    
    resultados = []
    
    for nombre, test_func in pruebas:
        print(f"\n{'=' * 60}")
        print(f"🔬 EJECUTANDO: {nombre}")
        print('=' * 60)
        
        start_time = time.time()
        try:
            resultado = test_func()
            end_time = time.time()
            duration = end_time - start_time
            
            if resultado:
                print(f"\n✅ {nombre}: EXITOSA ({duration:.2f}s)")
                resultados.append((nombre, "EXITOSA", duration))
            else:
                print(f"\n❌ {nombre}: FALLIDA ({duration:.2f}s)")
                resultados.append((nombre, "FALLIDA", duration))
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"\n💥 {nombre}: ERROR - {e} ({duration:.2f}s)")
            resultados.append((nombre, f"ERROR: {e}", duration))
    
    # Resumen final
    print(f"\n{'=' * 60}")
    print("📊 RESUMEN DE PRUEBAS")
    print('=' * 60)
    
    exitosas = 0
    for nombre, resultado, duracion in resultados:
        status_emoji = "✅" if resultado == "EXITOSA" else ("❌" if resultado == "FALLIDA" else "💥")
        print(f"{status_emoji} {nombre}: {resultado} ({duracion:.2f}s)")
        if resultado == "EXITOSA":
            exitosas += 1
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   Exitosas: {exitosas}/{len(resultados)}")
    print(f"   Tiempo total: {sum(r[2] for r in resultados):.2f}s")
    
    if exitosas == len(resultados):
        print(f"\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print(f"   El sistema está listo para usar.")
    else:
        print(f"\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print(f"   Revisa los errores antes de usar el sistema.")
    
    print(f"\n🕐 Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()