import requests
import os
import json
from django.conf import settings

class HuggingFaceLLMService:
    def __init__(self):
        # Usar modelos que SÍ funcionan para generación de texto
        self.modelo_actual = "gpt2"  # El básico siempre funciona
        self.api_url = f"https://api-inference.huggingface.co/models/{self.modelo_actual}"
        self.token = os.getenv('HUGGINGFACE_TOKEN')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Modelos alternativos si gpt2 falla
        self.modelos_backup = [
            "distilgpt2",
            "microsoft/DialoGPT-small", 
            "facebook/opt-350m"
        ]
    
    def generar_adaptacion_tea(self, proyecto_titulo, contenido_proyecto):
        """Genera adaptaciones específicas para TEA"""
        
        # Prompt muy simple que funciona con GPT-2
        prompt = f"Adaptaciones TEA para proyecto {proyecto_titulo}:\n1. Usar rutinas claras\n2. Apoyo visual\n3."
        
        print(f"🔍 DEBUG TEA - Prompt: {prompt}")
        
        resultado = self._llamar_api_simple(prompt)
        print(f"🔍 DEBUG TEA - Resultado: {resultado}")
        
        return resultado
    
    def generar_adaptacion_tdah(self, proyecto_titulo, contenido_proyecto):
        """Genera adaptaciones específicas para TDAH"""
        
        prompt = f"Adaptaciones TDAH para proyecto {proyecto_titulo}:\n1. Descansos frecuentes\n2. Tareas cortas\n3."
        
        print(f"🔍 DEBUG TDAH - Prompt: {prompt}")
        
        resultado = self._llamar_api_simple(prompt)
        print(f"🔍 DEBUG TDAH - Resultado: {resultado}")
        
        return resultado
    
    def generar_adaptacion_aacc(self, proyecto_titulo, contenido_proyecto):
        """Genera adaptaciones para Altas Capacidades"""
        
        prompt = f"Adaptaciones AACC para proyecto {proyecto_titulo}:\n1. Retos complejos\n2. Liderazgo\n3."
        
        print(f"🔍 DEBUG AACC - Prompt: {prompt}")
        
        resultado = self._llamar_api_simple(prompt)
        print(f"🔍 DEBUG AACC - Resultado: {resultado}")
        
        return resultado
    
    def _llamar_api_simple(self, prompt):
        """Método simplificado que SÍ funciona"""
        
        # Formato estándar para GPT-2 y similares
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 150,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        print(f"🌐 Usando modelo: {self.modelo_actual}")
        print(f"📤 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload, 
                timeout=30
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Response raw: {response.text}")
            
            if response.status_code == 200:
                try:
                    resultado = response.json()
                    print(f"✅ JSON parseado: {resultado}")
                    
                    # Extraer texto generado
                    if isinstance(resultado, list) and len(resultado) > 0:
                        if "generated_text" in resultado[0]:
                            texto_generado = resultado[0]["generated_text"]
                            print(f"✅ Texto extraído: {texto_generado}")
                            return {"adaptaciones": texto_generado}
                    
                    # Si no se puede extraer, devolver respuesta completa
                    return {"adaptaciones": str(resultado)}
                    
                except json.JSONDecodeError:
                    return {"adaptaciones": f"Respuesta no JSON: {response.text}"}
            
            elif response.status_code == 503:
                # Modelo cargando
                return {"adaptaciones": "El modelo se está cargando. Intenta de nuevo en 1-2 minutos."}
            
            else:
                # Probar con modelo backup
                print(f"❌ Error {response.status_code}, probando modelo backup...")
                return self._probar_modelo_backup(prompt)
                
        except requests.exceptions.Timeout:
            return {"adaptaciones": "Timeout - el modelo tardó demasiado en responder"}
        except Exception as e:
            print(f"❌ Excepción: {str(e)}")
            return {"error": f"Error de conexión: {str(e)}"}
    
    def _probar_modelo_backup(self, prompt):
        """Prueba con modelos backup"""
        
        for modelo_backup in self.modelos_backup:
            try:
                print(f"🔄 Probando modelo backup: {modelo_backup}")
                
                backup_url = f"https://api-inference.huggingface.co/models/{modelo_backup}"
                
                # Payload más simple para modelos backup
                payload = {"inputs": prompt}
                
                response = requests.post(
                    backup_url, 
                    headers=self.headers, 
                    json=payload, 
                    timeout=20
                )
                
                print(f"📊 Backup status: {response.status_code}")
                
                if response.status_code == 200:
                    resultado = response.json()
                    print(f"✅ Backup funcionó: {resultado}")
                    
                    if isinstance(resultado, list) and len(resultado) > 0:
                        if "generated_text" in resultado[0]:
                            return {"adaptaciones": resultado[0]["generated_text"]}
                    
                    return {"adaptaciones": str(resultado)}
                    
            except Exception as e:
                print(f"❌ Backup {modelo_backup} falló: {str(e)}")
                continue
        
        # Si todos fallan, devolver adaptaciones predefinidas
        return self._adaptaciones_fallback(prompt)
    
    def _adaptaciones_fallback(self, prompt):
        """Adaptaciones predefinidas si la API falla completamente"""
        
        if "TEA" in prompt:
            return {
                "adaptaciones": """1. Proporcionar estructura clara y rutinas predecibles en las actividades
2. Usar apoyos visuales como pictogramas, esquemas y organizadores gráficos
3. Facilitar espacios de trabajo tranquilos y reducir estímulos sensoriales excesivos"""
            }
        elif "TDAH" in prompt:
            return {
                "adaptaciones": """1. Dividir tareas en pasos pequeños y ofrecer descansos frecuentes
2. Incorporar actividades manipulativas y oportunidades de movimiento
3. Utilizar refuerzos positivos inmediatos y señales visuales para mantener la atención"""
            }
        elif "AACC" in prompt:
            return {
                "adaptaciones": """1. Proponer retos adicionales de mayor complejidad conceptual
2. Asignar roles de liderazgo y mentoría con compañeros
3. Ofrecer extensiones creativas que permitan explorar el tema en profundidad"""
            }
        else:
            return {"adaptaciones": "Adaptaciones generales disponibles"}

    def test_conexion(self):
        """Probar si la conexión a Hugging Face funciona"""
        simple_prompt = "Hello, how are you?"
        payload = {"inputs": simple_prompt}
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            print(f"🌐 Modelo: {self.modelo_actual}")
            print(f"📊 Status code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return response.status_code, response.text
        except Exception as e:
            return "error", str(e)