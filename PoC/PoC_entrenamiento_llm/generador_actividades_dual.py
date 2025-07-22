"""
Generador principal de actividades educativas adaptadas
Soporte para GROQ API y OLLAMA API
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import random

from prompt_template import PromptTemplateGenerator, TEMAS_MATEMATICAS_4_PRIMARIA, TEMAS_LENGUA_4_PRIMARIA, TEMAS_CIENCIAS_4_PRIMARIA
from groq_api_integrator import GroqAPIEducationGenerator
from ollama_api_integrator import OllamaAPIEducationGenerator

class GeneradorActividadesEducativasDual:
    
    def __init__(self, 
                 archivo_perfiles: str = None,
                 provider: str = "groq",  # "groq" o "ollama" 
                 modelo_groq: str = "llama-3.1-8b-instant",
                 ollama_host: str = "localhost",
                 ollama_port: int = 11434,
                 modelo_ollama: str = "llama3.2"):
        """
        Inicializa el generador de actividades con soporte dual
        
        Args:
            archivo_perfiles: Ruta al archivo JSON con perfiles de estudiantes
            provider: "groq" o "ollama"
            modelo_groq: Modelo de Groq a utilizar
            ollama_host: IP del servidor Ollama
            ollama_port: Puerto del servidor Ollama  
            modelo_ollama: Modelo de Ollama a utilizar
        """
        # Buscar archivo de perfiles en directorio del script
        if archivo_perfiles is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            archivo_perfiles = os.path.join(script_dir, "perfiles_4_primaria.json")
        
        self.archivo_perfiles = archivo_perfiles
        self.perfiles = self._cargar_perfiles()
        self.prompt_generator = PromptTemplateGenerator()
        self.provider = provider.lower()
        
        # Inicializar el generador según el provider
        if self.provider == "groq":
            print(f"🚀 Inicializando con Groq API - Modelo: {modelo_groq}")
            self.ai_generator = GroqAPIEducationGenerator(model_name=modelo_groq)
            self.modelo_actual = modelo_groq
        elif self.provider == "ollama":
            print(f"🦙 Inicializando con Ollama API - Host: {ollama_host}:{ollama_port} - Modelo: {modelo_ollama}")
            self.ai_generator = OllamaAPIEducationGenerator(
                host=ollama_host, 
                port=ollama_port, 
                model_name=modelo_ollama
            )
            self.modelo_actual = modelo_ollama
        else:
            raise ValueError("Provider debe ser 'groq' o 'ollama'")
        
        # Mapeo de temas por materia
        self.temas_por_materia = {
            "Matemáticas": TEMAS_MATEMATICAS_4_PRIMARIA,
            "Lengua": TEMAS_LENGUA_4_PRIMARIA,
            "Ciencias": TEMAS_CIENCIAS_4_PRIMARIA
        }
        
        print(f"✅ Generador inicializado con {self.provider.upper()}")
    
    def cambiar_provider(self, 
                        provider: str,
                        modelo_groq: str = "llama-3.1-8b-instant",
                        ollama_host: str = "localhost", 
                        ollama_port: int = 11434,
                        modelo_ollama: str = "llama3.2"):
        """Cambia el provider de IA dinámicamente"""
        
        provider = provider.lower()
        print(f"🔄 Cambiando a provider: {provider.upper()}")
        
        if provider == "groq":
            self.ai_generator = GroqAPIEducationGenerator(model_name=modelo_groq)
            self.modelo_actual = modelo_groq
            self.provider = "groq"
        elif provider == "ollama":
            self.ai_generator = OllamaAPIEducationGenerator(
                host=ollama_host,
                port=ollama_port, 
                model_name=modelo_ollama
            )
            self.modelo_actual = modelo_ollama
            self.provider = "ollama"
        else:
            raise ValueError("Provider debe ser 'groq' o 'ollama'")
        
        print(f"✅ Cambiado a {provider.upper()} - Modelo: {self.modelo_actual}")
    
    def _cargar_perfiles(self) -> List[Dict]:
        """Carga los perfiles de estudiantes desde el archivo JSON"""
        try:
            with open(self.archivo_perfiles, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['estudiantes']
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {self.archivo_perfiles}")
            return []
        except json.JSONDecodeError:
            print(f"❌ Error: El archivo {self.archivo_perfiles} no tiene formato JSON válido")
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
    
    def generar_actividad_grupal_rapida(self, materia: str, tema: str = None, output_dir: str = None) -> Dict:
        """
        Genera UNA actividad grupal rápida para probar el sistema
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
        
        print(f"🎯 Generando actividad grupal: {materia_normalizada} - {tema}")
        print(f"🤖 Provider: {self.provider.upper()} - Modelo: {self.modelo_actual}")
        
        # Analizar diversidad del aula
        diversidad = self._analizar_diversidad_aula()
        
        # Crear prompt optimizado para prueba rápida
        prompt_grupal = self._generar_prompt_grupal_compacto(materia_normalizada, tema, diversidad)
        
        try:
            # Generar actividad
            start_time = datetime.now()
            actividad_grupal = self.ai_generator.generar_texto(prompt_grupal, max_tokens=1200)
            end_time = datetime.now()
            
            duracion = (end_time - start_time).total_seconds()
            print(f"⏱️ Tiempo de generación: {duracion:.2f} segundos")
            
            if not actividad_grupal or "Error" in actividad_grupal:
                return {"error": "No se pudo generar la actividad grupal"}
            
            # Crear archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_actividad = os.path.join(output_dir, 
                f"actividad_{self.provider}_{materia_normalizada.lower()}_{tema.replace(' ', '_')}_{timestamp}.txt")
            
            with open(archivo_actividad, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"ACTIVIDAD GRUPAL: {materia_normalizada} - {tema}\n")
                f.write(f"GENERADOR: {self.provider.upper()} - {self.modelo_actual}\n")
                f.write(f"AULA: AULA_A_4PRIM ({len(self.perfiles)} estudiantes)\n")
                f.write(f"DURACIÓN: {duracion:.2f} segundos\n")
                f.write("=" * 80 + "\n\n")
                f.write("DIVERSIDAD DEL AULA:\n")
                f.write(f"- Diagnósticos: {diversidad['diagnosticos']}\n")
                f.write(f"- Canales: {diversidad['canales_aprendizaje']}\n") 
                f.write(f"- Niveles apoyo: {diversidad['niveles_apoyo']}\n\n")
                f.write("ACTIVIDAD GENERADA:\n")
                f.write("-" * 50 + "\n")
                f.write(actividad_grupal)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Generado: {datetime.now().isoformat()}\n")
            
            print(f"✅ Actividad guardada en: {archivo_actividad}")
            
            return {
                "success": True,
                "archivo": archivo_actividad,
                "duracion_segundos": duracion,
                "provider": self.provider,
                "modelo": self.modelo_actual,
                "tema": tema,
                "materia": materia_normalizada,
                "actividad": actividad_grupal[:300] + "..." if len(actividad_grupal) > 300 else actividad_grupal
            }
            
        except Exception as e:
            return {"error": f"Error generando actividad: {e}"}
    
    def _generar_prompt_grupal_compacto(self, materia: str, tema: str, diversidad: Dict) -> str:
        """Genera un prompt más compacto para pruebas rápidas"""
        
        # Lista compacta de estudiantes
        estudiantes_compacto = []
        for perfil in self.perfiles:
            estudiantes_compacto.append(
                f"{perfil['nombre']} ({perfil['id']}): {perfil['diagnostico_formal']}, {perfil['canal_preferido']}, apoyo {perfil['nivel_apoyo']}"
            )
        
        prompt = f"""Eres un docente especializado en educación inclusiva de 4º de Primaria.

TAREA: Crear UNA actividad grupal de {materia} sobre "{tema}" para estos 8 estudiantes:

ESTUDIANTES:
{chr(10).join(estudiantes_compacto)}

DIVERSIDAD: 
- Diagnósticos: {list(diversidad['diagnosticos'].keys())}
- Canales: {list(diversidad['canales_aprendizaje'].keys())}
- Niveles apoyo: {list(diversidad['niveles_apoyo'].keys())}

ESTRUCTURA REQUERIDA:
1. TÍTULO atractivo
2. OBJETIVO común del grupo  
3. DESCRIPCIÓN de la actividad grupal
4. ROLES ESPECÍFICOS: Qué hace cada estudiante (menciona por nombre)
5. MATERIALES necesarios
6. PROCESO paso a paso
7. PRODUCTO FINAL del grupo
8. DURACIÓN estimada

REQUISITOS:
- Todos trabajan hacia UN objetivo común
- Cada estudiante tiene un rol específico según sus necesidades
- Respeta diagnósticos TEA, TDAH, altas capacidades
- Utiliza canales visual, auditivo, kinestésico  
- Interdependencia positiva (todos se necesitan)

Responde de forma concisa y práctica."""

        return prompt
    
    def _analizar_diversidad_aula(self) -> Dict:
        """Analiza la diversidad presente en el aula"""
        
        diversidad = {
            "diagnosticos": {},
            "canales_aprendizaje": {},
            "niveles_apoyo": {},
            "temperamentos": {}
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
        
        return diversidad
    
    def listar_modelos_disponibles(self) -> List[Dict]:
        """Lista modelos disponibles según el provider actual"""
        if self.provider == "ollama":
            return self.ai_generator.listar_modelos()
        else:
            return [{"name": "groq-models", "info": "Ver https://console.groq.com/docs/models"}]
    
    def benchmarking_rapido(self, prompt_test: str = None) -> Dict:
        """Hace un benchmark rápido del modelo actual"""
        
        if not prompt_test:
            prompt_test = "Explica las fracciones para niños de 4º primaria en máximo 100 palabras"
        
        print(f"🏃 Benchmarking {self.provider.upper()} - {self.modelo_actual}")
        
        start_time = datetime.now()
        resultado = self.ai_generator.generar_texto(prompt_test, max_tokens=150)
        end_time = datetime.now()
        
        duracion = (end_time - start_time).total_seconds()
        palabras = len(resultado.split()) if resultado else 0
        tokens_aprox = int(palabras * 1.3)  # Aproximación
        
        benchmark = {
            "provider": self.provider,
            "modelo": self.modelo_actual,
            "duracion_segundos": duracion,
            "palabras_generadas": palabras,
            "tokens_aprox": tokens_aprox,
            "tokens_por_segundo": tokens_aprox / duracion if duracion > 0 else 0,
            "resultado": resultado[:200] + "..." if len(resultado) > 200 else resultado
        }
        
        print(f"⏱️ Duración: {duracion:.2f}s")
        print(f"📊 Palabras: {palabras}")
        print(f"⚡ ~{benchmark['tokens_por_segundo']:.1f} tokens/seg")
        
        return benchmark


def main():
    """Función principal de demostración"""
    
    print("🎓 GENERADOR DE ACTIVIDADES EDUCATIVAS DUAL (GROQ + OLLAMA)")
    print("=" * 70)
    
    # Configuración por defecto
    config = {
        "ollama_host": "192.168.1.146",  # Tu servidor Ollama
        "ollama_port": 11434,
        "modelo_ollama": "llama3.2",
        "modelo_groq": "llama-3.1-8b-instant"
    }
    
    generador = None
    
    while True:
        print("\n📋 OPCIONES DISPONIBLES:")
        print("1. Inicializar con Groq")
        print("2. Inicializar con Ollama") 
        print("3. Generar actividad rápida")
        print("4. Cambiar provider")
        print("5. Benchmark rápido")
        print("6. Listar modelos disponibles")
        print("7. Salir")
        
        opcion = input("\nSelecciona una opción (1-7): ").strip()
        
        if opcion == "1":
            try:
                generador = GeneradorActividadesEducativasDual(
                    provider="groq",
                    modelo_groq=config["modelo_groq"]
                )
                print(f"✅ Inicializado con Groq: {config['modelo_groq']}")
            except Exception as e:
                print(f"❌ Error inicializando Groq: {e}")
        
        elif opcion == "2":
            try:
                generador = GeneradorActividadesEducativasDual(
                    provider="ollama",
                    ollama_host=config["ollama_host"],
                    ollama_port=config["ollama_port"],
                    modelo_ollama=config["modelo_ollama"]
                )
                print(f"✅ Inicializado con Ollama: {config['modelo_ollama']}")
            except Exception as e:
                print(f"❌ Error inicializando Ollama: {e}")
        
        elif opcion == "3":
            if not generador:
                print("❌ Primero inicializa un provider (opción 1 o 2)")
                continue
            
            print("\n🎯 GENERACIÓN RÁPIDA")
            materia = input("Materia (Matemáticas/Lengua/Ciencias): ").strip()
            
            resultado = generador.generar_actividad_grupal_rapida(materia)
            
            if resultado.get("success"):
                print(f"\n✅ ACTIVIDAD GENERADA EXITOSAMENTE")
                print(f"📁 Archivo: {resultado['archivo']}")
                print(f"⏱️ Duración: {resultado['duracion_segundos']:.2f}s")
                print(f"🤖 Provider: {resultado['provider'].upper()}")
                print(f"🎯 Tema: {resultado['tema']}")
                print(f"\n📄 Previa:")
                print(resultado['actividad'])
            else:
                print(f"❌ Error: {resultado.get('error')}")
        
        elif opcion == "4":
            if not generador:
                print("❌ Primero inicializa un provider (opción 1 o 2)")
                continue
            
            print(f"\n🔄 Provider actual: {generador.provider.upper()}")
            nuevo_provider = input("Cambiar a (groq/ollama): ").strip().lower()
            
            if nuevo_provider in ["groq", "ollama"]:
                try:
                    generador.cambiar_provider(
                        provider=nuevo_provider,
                        modelo_groq=config["modelo_groq"],
                        ollama_host=config["ollama_host"],
                        ollama_port=config["ollama_port"],
                        modelo_ollama=config["modelo_ollama"]
                    )
                except Exception as e:
                    print(f"❌ Error cambiando provider: {e}")
            else:
                print("❌ Provider debe ser 'groq' o 'ollama'")
        
        elif opcion == "5":
            if not generador:
                print("❌ Primero inicializa un provider (opción 1 o 2)")
                continue
            
            print("\n🏃 BENCHMARK RÁPIDO")
            benchmark = generador.benchmarking_rapido()
            print(f"\n📊 RESULTADOS:")
            print(f"🤖 {benchmark['provider'].upper()}: {benchmark['modelo']}")
            print(f"⏱️ Tiempo: {benchmark['duracion_segundos']:.2f}s")
            print(f"⚡ Velocidad: {benchmark['tokens_por_segundo']:.1f} tokens/seg")
        
        elif opcion == "6":
            if not generador:
                print("❌ Primero inicializa un provider (opción 1 o 2)")
                continue
            
            print(f"\n📋 MODELOS DISPONIBLES ({generador.provider.upper()}):")
            modelos = generador.listar_modelos_disponibles()
            for modelo in modelos:
                if 'parameter_size' in modelo:
                    print(f"  🤖 {modelo['name']} ({modelo['parameter_size']})")
                else:
                    print(f"  🤖 {modelo.get('name', 'N/A')}")
        
        elif opcion == "7":
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()