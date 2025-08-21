# PROYECTO IA4EDU - Documentación Técnica Completa

## Resumen Ejecutivo

IA4EDU es un sistema de inteligencia artificial educativa que genera automáticamente actividades de Aprendizaje Basado en Proyectos (ABP) personalizadas para estudiantes con diversidad neurológica. El sistema utiliza una arquitectura multi-agente con integración de modelos de lenguaje local (Ollama) y en la nube (Groq) para crear experiencias educativas inclusivas siguiendo los principios del Diseño Universal para el Aprendizaje (DUA).

**Versión Actual:** 0.8 (Beta funcional)  
**Dataset:** 394 estudiantes reales de 4º de Primaria  
**Arquitectura:** Sistema multi-agente con LLM integration  

## Arquitectura General del Sistema

### Punto de Entrada: `simple_cli.py`

El sistema se inicia a través de `src/mvp/simple_cli.py`, que implementa una interfaz de línea de comandos simplificada. Este archivo actúa como el **controlador principal** del flujo de trabajo:

```python
# Flujo principal de ejecución
def main():
    coordinator = SimplifiedCoordinator()    # Motor de generación
    profile_manager = ProfileManager()       # Gestión de perfiles estudiantiles
    
    # Opciones disponibles:
    # 1. Generar actividad ABP (con feedback iterativo)
    # 2. Ver perfiles de estudiantes  
    # 3. Ver parejas optimizadas
    # 4. Salir
```

### Componentes Principales

#### 1. SimplifiedCoordinator (Motor Central)

**Ubicación:** `src/mvp/simplified_coordinator.py`  
**Responsabilidad:** Coordinación completa del proceso de generación de actividades

**Proceso paso a paso:**

1. **Análisis de Solicitud**
   ```python
   def generate_activity(user_request, additional_details):
       # 1. Detectar modo de agrupación (individual/parejas/grupos)
       grouping_info = self._detect_grouping_mode(user_request)
       
       # 2. Buscar ejemplos relevantes usando embeddings
       ejemplos_relevantes = self._find_relevant_examples(user_request)
       
       # 3. Crear prompt directo optimizado
       prompt_directo = self._create_direct_prompt(...)
       
       # 4. Generar con LLM (Groq/Ollama)
       response = self.ollama.generar_respuesta(prompt_directo)
       
       # 5. Procesar y estructurar respuesta
       activity_result = self._process_llm_response(response)
       
       # 6. Asignar estudiantes específicos a tareas
       activity_result = self._assign_students_to_tasks(activity_result)
   ```

2. **Detección Inteligente de Agrupación**
   - Analiza el texto del usuario para identificar modalidades de trabajo
   - Soporta patrones como: "cada uno prepare", "en parejas", "grupos de 4"
   - Diferencia entre fases (preparación vs ejecución)

3. **Sistema de Refinamiento Iterativo**
   ```python
   def refine_activity(current_activity, feedback):
       # 1. Análisis semántico del feedback
       feedback_analysis = self._analyze_feedback_intent(feedback)
       
       # 2. Actualización de parámetros de agrupación si necesario
       if feedback_analysis['requiere_cambio_agrupacion']:
           self._update_grouping_from_feedback(feedback)
       
       # 3. Generación de prompt de refinamiento específico
       refinement_prompt = self._create_refinement_prompt_v2(...)
       
       # 4. Validación y corrección de inconsistencias
       refined_activity = self._validate_and_fix_activity(...)
   ```

#### 2. ProfileManager (Gestión Estudiantil)

**Ubicación:** `src/mvp/profile_manager.py`  
**Responsabilidad:** Gestión de perfiles y creación de agrupaciones óptimas

**Funcionalidades principales:**

1. **Carga y Mapeo de Perfiles**
   ```python
   def _create_neurotipo_mapping(self):
       # Clasifica estudiantes por neurotipo
       mapping = {
           'típico': [],
           'TEA': [],           # Trastorno Espectro Autista
           'TDAH': [],          # Déficit de Atención e Hiperactividad  
           'altas_capacidades': [],
           'otros': []
       }
   ```

2. **Creación de Agrupaciones Óptimas**
   ```python
   def create_optimal_groupings(self, grouping_mode, group_size):
       if grouping_mode == "individual":
           return self._create_individual_assignments()
       elif grouping_mode == "parejas":
           return self._create_optimal_pairs()
       elif grouping_mode == "grupos":
           return self._create_optimal_groups(group_size)
   ```

3. **Estrategia de Emparejamiento**
   - Combina estudiantes con necesidades especiales con neurotipos típicos
   - Equilibra las agrupaciones para maximizar el apoyo mutuo
   - Considera fortalezas complementarias

#### 3. OllamaIntegrator (Interface LLM)

**Ubicación:** `src/core/ollama_integrator.py`  
**Responsabilidad:** Gestión unificada de proveedores de LLM

**Arquitectura Dual:**

1. **Proveedor Principal (Groq Cloud)**
   ```python
   # Configuración actual
   self.provider = "groq"
   self.groq_model = "openai/gpt-oss-120b"
   self.groq_base_url = "https://api.groq.com/openai/v1"
   ```

2. **Proveedor Embeddings (Ollama Local)**
   ```python
   # Solo para embeddings
   self.host = "192.168.1.10"
   self.embedding_model = "nomic-embed-text"
   ```

3. **Sistema de Fallback**
   - Si Groq falla → Ollama local
   - Si ambos fallan → Respuesta estructurada predeterminada

#### 4. EmbeddingsManager (Selección Inteligente)

**Ubicación:** `src/core/embeddings_manager.py`  
**Responsabilidad:** Selección de ejemplos relevantes mediante similitud semántica

**Proceso de Funcionamiento:**

1. **Carga de Actividades Base**
   ```python
   def _cargar_actividades_json_y_txt(self):
       # Carga actividades JSON del directorio json_actividades/
       # Carga plantillas de estructura (plantilla_guiada.json)
       # Enriquece cada actividad con texto para embeddings
   ```

2. **Generación de Embeddings con Cache**
   ```python
   def crear_embedding_cached(self, texto):
       hash_texto = hashlib.md5(texto.encode()).hexdigest()
       
       # 1. Buscar en cache de memoria
       # 2. Buscar en cache persistente
       # 3. Generar nuevo embedding si no existe
       # 4. Guardar en ambos caches
   ```

3. **Búsqueda por Similitud Semántica**
   ```python
   def encontrar_actividad_similar(self, prompt, top_k=3):
       # 1. Enriquecer prompt del usuario
       prompt_enriquecido = self._enriquecer_prompt_usuario(prompt)
       
       # 2. Generar embedding del prompt
       prompt_embedding = self.crear_embedding_cached(prompt_enriquecido)
       
       # 3. Calcular similitud coseno con todas las actividades
       # 4. Aplicar boost semántico según contexto
       # 5. Ordenar y filtrar resultados
   ```

## Flujo Completo de Generación de Actividades

### 1. Inicio de Solicitud

```
Usuario: "Crea una actividad de matemáticas con fracciones donde trabajen en parejas"
```

### 2. Procesamiento en SimplifiedCoordinator

1. **Detección de Agrupación:**
   - Identifica "en parejas" → modo_agrupacion = {'preparacion': 'parejas', 'ejecucion': 'parejas'}

2. **Búsqueda de Ejemplos:**
   - EmbeddingsManager busca actividades similares a "matemáticas fracciones parejas"
   - Encuentra: `k_fabrica_fracciones.json` (similitud: 0.847)

3. **Construcción de Prompt:**
   ```markdown
   Crea una actividad educativa ABP para 4º de Primaria.
   
   SOLICITUD DEL PROFESOR: matemáticas con fracciones en parejas
   
   ESTUDIANTES DEL AULA: Elena (TEA), Luis (TDAH), Ana (altas capacidades), Alex, María, Emma, Sara, Hugo
   
   MODO DE AGRUPACIÓN:
   - Preparación: parejas
   - Ejecución: parejas
   
   RESPONDE EN FORMATO MARKDOWN usando estructura exacta...
   ```

### 3. Generación LLM y Procesamiento

1. **Llamada a Groq API:**
   - Modelo: `openai/gpt-oss-120b`
   - Temperatura: 0.7
   - Max tokens: 1500

2. **Parseo de Respuesta Markdown:**
   ```python
   def _parse_markdown_response(self, response):
       # Extrae título, objetivo, duración
       # Procesa fases y tareas
       # Parsea adaptaciones por neurotipo
       # Convierte a estructura JSON
   ```

### 4. Asignación de Estudiantes

```python
def _assign_students_to_tasks(self, activity, grouping_info):
    # ProfileManager crea parejas óptimas:
    # - Elena (TEA) + Alex (típico)
    # - Luis (TDAH) + María (típica)  
    # - Ana (altas capacidades) + Emma (típica)
    # - Sara + Hugo (ambos típicos)
    
    for tarea in fase.tareas:
        tarea['asignaciones'] = ["Elena y Alex", "Luis y María", "Ana y Emma", "Sara y Hugo"]
```

### 5. Validación y Metadatos

```python
activity_result['metadatos'] = {
    'timestamp': '2024-01-15T10:30:00',
    'sistema': 'SimplifiedCoordinator',
    'modo_agrupacion': grouping_info,
    'ejemplos_utilizados': ['k_fabrica_fracciones'],
    'validacion': {'correcciones_aplicadas': []}
}
```

## Sistema de Refinamiento Iterativo

### Análisis Inteligente de Feedback

El sistema analiza dinámicamente el feedback del profesor:

```python
def _analyze_feedback_intent(self, feedback):
    # Detecta tipos de peticiones:
    # - 'clarificacion': "no entiendo", "confuso"  
    # - 'explicar_mecanica': "cómo funciona", "mecánica"
    # - 'definir_juego': "reglas", "objetivo del juego"
    # - 'modo_agrupacion': "equipos", "individual"
    # - 'materiales': "qué necesito", "materiales"
    # - 'duracion': "más tiempo", "cuánto dura"
```

### Ejemplo de Refinamiento

```
Feedback: "No entiendo cómo funciona el juego, ¿qué reglas tiene?"

Análisis: ['clarificacion', 'definir_juego']

Instrucciones generadas:
- Explica paso a paso cómo funciona la actividad
- Define las reglas del juego claramente
- Especifica: objetivo del juego, cómo se juega, turnos
- Incluye ejemplos concretos de jugadas
```

## Gestión de Perfiles Estudiantiles

### Dataset Real

El sistema trabaja con **394 estudiantes reales** de 4º de Primaria:

```json
{
  "estudiantes": [
    {
      "id": "001",
      "nombre": "Elena R.",
      "diagnostico_formal": "TEA_nivel_1",
      "fortalezas": ["precisión", "matemáticas"],
      "necesidades_especiales": ["apoyo visual", "estructura clara"],
      "competencias_curriculares": {
        "matematicas": 7.2,
        "lengua": 6.8,
        "ciencias": 8.1
      }
    }
    // ... 393 estudiantes más
  ]
}
```

### Estrategias de Agrupación

#### Parejas Óptimas
- **TEA + Neurotipos típicos:** Apoyo social estructurado
- **TDAH + Estudiantes organizados:** Balance de energía/estructura
- **Altas capacidades + Cualquier perfil:** Mentoría natural

#### Grupos Balanceados
- Máximo 1 estudiante con necesidades especiales por grupo
- Distribución equitativa de fortalezas académicas
- Consideración de dinámicas sociales

## Adaptaciones Específicas por Neurotipo

### TEA (Trastorno del Espectro Autista)
```python
adaptaciones_TEA = [
    "Proporcionar estructura clara y predecible",
    "Usar apoyos visuales (pictogramas, esquemas)",
    "Dar tiempo extra para transiciones", 
    "Crear ambiente menos estimulante"
]
```

### TDAH (Déficit de Atención e Hiperactividad)
```python
adaptaciones_TDAH = [
    "Permitir movimiento durante actividades",
    "Fragmentar tareas en pasos pequeños",
    "Ofrecer descansos frecuentes",
    "Usar elementos manipulativos"
]
```

### Altas Capacidades
```python
adaptaciones_altas_capacidades = [
    "Proporcionar retos adicionales",
    "Fomentar rol de mentoría", 
    "Permitir investigación autónoma",
    "Ofrecer proyectos de mayor complejidad"
]
```

## Configuración del Sistema

### Configuración LLM (config.py)

```python
OLLAMA_CONFIG = {
    "provider": "groq",                    # Proveedor principal
    "groq_model": "openai/gpt-oss-120b",  # Modelo de generación
    "groq_api_key": os.getenv("GROQ_API_KEY"),
    
    # Ollama local (solo embeddings)
    "host": "192.168.1.10", 
    "embedding_model": "nomic-embed-text",
    
    "timeout": 60
}
```

### Variables de Entorno Requeridas

```bash
# .env file
GROQ_API_KEY=your_groq_api_key_here
```

## Estructura de Datos de Actividades

### Formato de Entrada (Solicitud del Usuario)
```
"Crea una gymkana de ciencias naturales sobre la célula donde cada uno prepare su estación"
```

### Formato de Salida (Actividad Generada)
```json
{
  "titulo": "Gymkana Científica: Explorando la Célula",
  "objetivo": "Comprender la estructura celular mediante estaciones interactivas",
  "duracion": "2 sesiones de 45 minutos",
  "fases": [
    {
      "nombre": "Preparación", 
      "modo_agrupacion": "individual",
      "descripcion": "Cada estudiante prepara su estación especializada",
      "tareas": [
        {
          "nombre": "Preparar estación del núcleo",
          "descripcion": "Crear material informativo sobre la función del núcleo",
          "asignaciones": ["Elena"],
          "detalles_especificos": "Incluir esquemas visuales para apoyo TEA"
        }
      ]
    },
    {
      "nombre": "Ejecución",
      "modo_agrupacion": "individual", 
      "descripcion": "Rotación por estaciones de aprendizaje",
      "tareas": [
        {
          "nombre": "Rotación guiada por estaciones",
          "descripcion": "Visitar cada estación y completar actividades",
          "asignaciones": ["Elena", "Luis", "Ana", "Alex", "María", "Emma", "Sara", "Hugo"],
          "detalles_especificos": "Rotación cada 8 minutos con descanso para TDAH"
        }
      ]
    }
  ],
  "adaptaciones": {
    "TEA": ["Esquemas visuales claros", "Tiempo extra en transiciones"],
    "TDAH": ["Descansos cada 15 minutos", "Material manipulativo"],
    "altas_capacidades": ["Preguntas de profundización", "Rol de mentor"]
  },
  "metadatos": {
    "timestamp": "2024-01-15T10:30:00",
    "sistema": "SimplifiedCoordinator",
    "modo_agrupacion": {
      "preparacion": {"modo": "individual", "tamaño": 1},
      "ejecucion": {"modo": "individual", "tamaño": 1}
    }
  }
}
```

## Optimizaciones y Características Avanzadas

### Cache Inteligente de Embeddings

```python
# Cache persistente con detección de cambios
def _cargar_o_generar_embeddings(self):
    # 1. Calcular hash MD5 de archivos fuente
    # 2. Comparar con cache existente  
    # 3. Regenerar solo embeddings de archivos modificados
    # 4. Reutilizar embeddings válidos
    
    # Resultado: Arranque ~2s en lugar de ~30s
```

### Boost Semántico Contextual

```python
def _aplicar_boost_semantico(self, similitud_base, prompt, actividad_data):
    # Detecta mismatch semántico:
    # - Usuario pide "gymkana" pero actividad es "construcción" → penalización
    # - Usuario pide "fracciones" y actividad contiene "fracciones" → boost
    # - Usuario pide "parejas" pero actividad es individual → penalización
```

### Validación Automática de Coherencia

```python  
def _validate_and_fix_activity(self, activity, feedback_analysis):
    # Detecta y corrige inconsistencias:
    # - Modo declarado ≠ asignaciones reales
    # - Falta de estudiantes en asignaciones
    # - Incoherencia entre fases
    
    # Auto-corrige y registra cambios en metadatos
```

## Comandos de Uso

### Instalación y Setup
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar Ollama (opcional, solo para local)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull nomic-embed-text

# Configurar variables de entorno
echo "GROQ_API_KEY=your_key_here" > .env
```

### Ejecución
```bash
# Versión MVP simplificada (recomendada)
python src/mvp/simple_cli.py

# Sistema completo (más complejo)
python src/app.py
```

### Opciones de Testing
```bash
# Testing de componentes específicos
python src/test_mejoras_analizador.py
python data/expansion\ datos/test_dataset_expandido.py

# Análisis de datos  
python data/analyze_4th_grade_profiles.py
```

## Limitaciones y Consideraciones

### Limitaciones Actuales
- **Testing:** Cobertura limitada de pruebas automatizadas
- **Escalabilidad:** Optimizado para aulas de ~8-30 estudiantes
- **Idioma:** Sistema en español (contexto educativo español)
- **Dependencia LLM:** Requiere conexión a internet para Groq

### Consideraciones de Privacidad
- **Anonimización:** Todos los datos estudiantiles están anonimizados
- **Local First:** Embeddings se generan y almacenan localmente
- **No logging personal:** No se registra información estudiantil sensible

### Requerimientos de Sistema
- **Python:** 3.8+
- **Memoria:** 2GB RAM mínimo para embeddings
- **Almacenamiento:** ~100MB para cache de embeddings
- **Red:** Conexión estable para API de Groq

## Roadmap y Desarrollo Futuro

### Version 0.9 (Próxima)
- [ ] Interfaz web básica
- [ ] Métricas de uso y efectividad  
- [ ] Exportación a múltiples formatos
- [ ] Testing automatizado completo

### Version 1.0 (Objetivo)
- [ ] Validación empírica con profesores reales
- [ ] Optimización de escalabilidad
- [ ] Multilenguaje (inglés, catalán)
- [ ] Integración con plataformas LMS

---

*Documentación generada automáticamente basada en análisis de código fuente del MVP `simple_cli.py` y sus dependencias.*