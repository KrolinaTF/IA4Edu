import os
import google.generativeai as genai

# Configurar API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Listar modelos disponibles
print("Modelos disponibles:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")

# Probar gemini-1.5-flash
print("\nProbando modelos:")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Di hola")
    print("✅ gemini-1.5-flash funciona")
except Exception as e:
    print(f"❌ gemini-1.5-flash error: {e}")

# Probar gemini-1.5-pro
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Di hola")
    print("✅ gemini-1.5-pro funciona")
except Exception as e:
    print(f"❌ gemini-1.5-pro error: {e}")