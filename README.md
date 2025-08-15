# IA4EDU - Sistema de Agentes para Educación Inclusiva

## ¿Qué es este proyecto?

IA4EDU es un sistema experimental que utiliza inteligencia artificial para generar automáticamente actividades educativas colaborativas adaptadas a estudiantes con diferentes perfiles de aprendizaje.

El proyecto nació de la necesidad de ayudar a docentes a crear actividades ABP (Aprendizaje Basado en Proyectos) que tengan en cuenta la diversidad neurológica del aula, aplicando principios DUA (Diseño Universal de Aprendizaje) de forma sistemática.

## Evolución del proyecto

### Fase 1: Concepto inicial
- **Objetivo**: Generar actividades educativas básicas usando LLM
- **Implementación**: Script simple con GPT para crear actividades de matemáticas
- **Resultado**: Funcional pero poco estructurado

### Fase 2: Sistema de agentes especializado
- **Objetivo**: Mejorar la calidad y personalización usando múltiples agentes
- **Implementación**: Sistema con 4 agentes especializados:
  - **Coordinador**: Orquesta el flujo completo
  - **Analizador**: Procesa actividades y extrae tareas
  - **Perfilador**: Gestiona perfiles de estudiantes  
  - **Optimizador**: Asigna tareas según capacidades
- **Resultado**: Mejor estructura pero complejidad alta

### Fase 3: Refinamiento y validación (actual)
- **Objetivo**: Sistema robusto con validación de coherencia
- **Implementación**: 
  - Flujo MVP integrado más eficiente
  - Validador de coherencia avanzado
  - Integración con Ollama para modelos locales
  - Sistema de embeddings para selección inteligente de actividades
- **Resultado**: Sistema funcional y validado

## Estado actual

### ✅ Funcional
- **Generación de actividades**: El sistema puede crear actividades ABP completas
- **Personalización**: Adapta contenido según perfiles neurológicos (TEA, TDAH, altas capacidades)
- **Validación**: Sistema de coherencia que valida la calidad de las actividades
- **Datos reales**: Utiliza dataset de 394 estudiantes con perfiles auténticos
- **Selección inteligente**: Embeddings para elegir actividades base apropiadas

### ⚠️ En desarrollo
- **UI mejorada**: La interfaz CLI funciona but podría ser más intuitiva
- **Métricas**: Sistema de métricas básico implementado
- **Integración LLM**: Funciona con Ollama, conexión a APIs externas pendiente
- **Testing**: Pruebas automatizadas limitadas

### ❌ Pendiente
- **Interfaz web**: Solo disponible CLI
- **Validación empírica**: No probado en aulas reales
- **Escalabilidad**: Optimizado para grupos pequeños
- **Documentación**: README técnico incompleto

## Arquitectura técnica

```
src/
├── agents/          # Agentes especializados
│   ├── coordinador.py    # Orquestador principal
│   ├── analizador.py     # Procesamiento de actividades
│   ├── perfilador.py     # Gestión de perfiles
│   └── optimizador.py    # Asignación de tareas
├── core/            # Funcionalidad base
│   ├── sistema.py        # Sistema principal
│   ├── contexto.py       # Gestión de contexto
│   ├── embeddings_manager.py  # Selección inteligente
│   └── validador_coherencia.py  # Validación de calidad
├── models/          # Modelos de datos
├── ui/              # Interfaz de usuario
└── utils/           # Utilidades
```

### Flujo principal
1. **Input**: Usuario describe actividad deseada
2. **Selección**: Sistema elige actividad base usando embeddings
3. **Análisis**: Se extraen tareas y estructura
4. **Perfilado**: Se cargan perfiles de estudiantes
5. **Asignación**: Se optimizan tareas según capacidades
6. **Validación**: Se verifica coherencia pedagógica
7. **Output**: Actividad personalizada completa

## Cómo usar el sistema

### Instalación
```bash
git clone https://github.com/ANFAIA/ia4edu.git
cd ia4edu
pip install -r requirements.txt  # Si existe
```

### Ejecución
```bash
python src/app.py
```

### Configuración con Ollama (opcional)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo recomendado
ollama pull llama3.2

# Configurar en src/config.py
```

## Dataset y datos

El proyecto utiliza un dataset real de **394 estudiantes de 4º de primaria** con:
- **Perfiles neurológicos**: TEA, TDAH, altas capacidades, neurotípicos
- **Competencias curriculares**: Estados de aprendizaje por materia
- **Adaptaciones DUA**: Necesidades específicas documentadas

Los datos están anonimizados y se usan únicamente para investigación educativa.

## Contribuir

El proyecto está abierto a contribuciones. Áreas de interés:
- **Testing**: Implementar pruebas automatizadas
- **UI/UX**: Mejorar la interfaz de usuario
- **Validación**: Probar en aulas reales
- **Escalabilidad**: Optimizar para grupos grandes
- **Nuevas funcionalidades**: Otras materias, niveles educativos

## Estado de desarrollo

**Versión actual**: 0.8 (Beta funcional)
**Última actualización**: 2025-01-15
**Estado**: Activo - desarrollo continuo

### Próximos pasos
1. Limpiar código legacy restante
2. Implementar más tests automatizados  
3. Mejorar documentación técnica
4. Preparar demo para validación en aulas

## Licencia

Licencia Apache 2.0 - Ver archivo LICENSE para detalles completos.

## Contacto

Para preguntas, colaboraciones o feedback sobre el proyecto, abrir un issue en GitHub.

---

*Proyecto desarrollado para la investigación en educación inclusiva mediante IA*