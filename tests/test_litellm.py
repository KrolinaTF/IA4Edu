import os
import litellm

# Configurar API key
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

print("Probando diferentes formatos con litellm:\n")

# Formato 1: solo nombre del modelo
try:
    response = litellm.completion(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "Di hola"}]
    )
    print("✅ Formato 'gemini-1.5-flash' funciona")
except Exception as e:
    print(f"❌ Formato 'gemini-1.5-flash' error: {e}")

# Formato 2: con prefijo gemini/
try:
    response = litellm.completion(
        model="gemini/gemini-1.5-flash",
        messages=[{"role": "user", "content": "Di hola"}]
    )
    print("✅ Formato 'gemini/gemini-1.5-flash' funciona")
except Exception as e:
    print(f"❌ Formato 'gemini/gemini-1.5-flash' error: {e}")

# Formato 3: con prefijo vertex_ai/ (otra opción)
try:
    response = litellm.completion(
        model="vertex_ai/gemini-1.5-flash",
        messages=[{"role": "user", "content": "Di hola"}]
    )
    print("✅ Formato 'vertex_ai/gemini-1.5-flash' funciona")
except Exception as e:
    print(f"❌ Formato 'vertex_ai/gemini-1.5-flash' error: {e}")

print("\nNOTA: El formato correcto es el que muestra ✅")