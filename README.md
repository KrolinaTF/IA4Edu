# IA4Edu
🎓 **Asistente de IA para crear actividades de aprendizaje por proyectos inclusivas**

Aplicación para el desarrollo de proyectos educativos teniendo en cuenta la diversidad del aula usando agentes de IA que diseñan actividades adaptadas para diferentes neurotipos (TEA, TDAH, Altas Capacidades, y desarrollo típico).

En la DEMO se puede observar:
- Cómo se puede acceder a los perfiles de los alumnos (sin currículo completo, solo representativo para MVP)
- Cómo con un prompt muy sencillo se obtiene una actividad completa (con descripción, objetivos, reparto de grupos, reparto de tareas, etc.)
- Cómo se puede revisar la actividad para incluir aspectos que puedan resultar interesantes.
- Actividades guardadas, historial de actividad.  

https://github.com/user-attachments/assets/ead64a62-817d-4eb6-adb9-6ab36726eb98





## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.11 o superior
- Clave API de Google Gemini ([obtener aquí](https://aistudio.google.com/))

### Instalación Rápida

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/KrolinaTF/IA4Edu.git
   cd IA4Edu
   ```

2. **Configurar entorno virtual e instalar dependencias**
   
   **Opción A: Usando UV (recomendado)**
   ```bash
   # Instalar UV si no lo tienes
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Crear y activar entorno virtual, instalar dependencias
   uv venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```
   
   **Opción B: Usando venv tradicional**
   ```bash
   # Crear entorno virtual
   python -m venv .venv
   
   # Activar entorno virtual
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   
   # Instalar dependencias
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   
   Crear archivo `.env` en la raíz del proyecto:
   ```bash
   # LLM provider
   LLM_PROVIDER=gemini
   LLM_API_KEY=tu_clave_api_gemini_aqui
   LLM_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
   ```

   O exportar directamente:
   ```bash
   export GEMINI_API_KEY='tu_clave_api_gemini_aqui'
   ```

## 🎯 Uso

### Ejecutar la aplicación
```bash
python main.py
```

La aplicación te guiará a través de un proceso interactivo paso a paso:
1. Describe la actividad que quieres crear
2. Revisa los perfiles de estudiantes del aula
3. Los agentes de IA diseñan la actividad
4. Proporciona feedback para refinamientos
5. Guarda la actividad final

### Usando Docker
```bash
docker build -t ia4edu .
docker run --env-file .env ia4edu
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov

# Solo tests unitarios
pytest -m unit
```

## 🔧 Solución de Problemas

### Error: "API key expired. Please renew the API key."
Si recibes este error, tu clave API de Gemini ha expirado:

1. **Obtener nueva clave API:**
   - Visita [Google AI Studio](https://aistudio.google.com/)
   - Genera una nueva clave API
   
2. **Actualizar la configuración:**
   ```bash
   # Actualizar en el archivo .env
   LLM_API_KEY=tu_nueva_clave_api_gemini
   
   # O exportar directamente
   export GEMINI_API_KEY='tu_nueva_clave_api_gemini'
   ```

### Error: "No se encontró GEMINI_API_KEY"
Verifica que la variable de entorno esté configurada:
```bash
# Verificar si está configurada
echo $GEMINI_API_KEY

# Si está vacía, configurarla
export GEMINI_API_KEY='tu_clave_api_gemini'
```

## 📋 Características Principales

- 🧠 **Paradigma de adaptación de terreno**: Diseño inclusivo desde el inicio
- 👥 **8 perfiles de estudiantes**: TEA, TDAH, Altas Capacidades y perfiles típicos
- 🤖 **Sistema multi-agente**: Análisis, investigación, diseño y refinamiento
- 🔄 **Human-in-the-loop**: Refinamiento iterativo basado en feedback
- 📚 **Biblioteca de actividades**: Base de conocimiento de proyectos exitosos

## 📁 Estructura del Proyecto

```
IA4Edu/
├── main.py                 # Interfaz principal CLI
├── agents/                 # Sistema de agentes CrewAI
│   └── crew_agents.py     # Lógica de agentes
├── templates/             # Plantillas de actividades
├── data/                  # Perfiles y biblioteca de actividades
│   ├── perfiles_4_primaria.json
│   └── k_*.md            # Actividades de ejemplo
└── tests/                # Tests automatizados
```

## Licencia
Este proyecto está licenciado bajo la Licencia Apache 2.0 - ver el archivo [LICENSE](LICENSE) para más detalles.
