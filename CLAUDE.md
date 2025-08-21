# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IA4EDU is an educational AI system that generates personalized collaborative learning activities for students with diverse neurological profiles. It uses a multi-agent architecture to create ABP (Project-Based Learning) activities that follow DUA (Universal Design for Learning) principles.

**Current Version**: 0.8 (Beta functional)  
**Main Language**: Python 3.x  
**Architecture**: Multi-agent system with LLM integration

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up Ollama (optional for local models)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
ollama pull mistral
ollama pull nomic-embed-text
```

### Running the System
```bash
# Main application (full system)
python src/app.py

# Simplified MVP version (recommended for development)
python src/mvp/simple_cli.py

# Data processing scripts
python data/data_processing/[script_name].py
```

### Development and Testing
```bash
# Run specific tests (limited test coverage currently)
python src/test_mejoras_analizador.py
python data/expansion\ datos/test_dataset_expandido.py

# Data analysis
python data/analyze_4th_grade_profiles.py
python data/simple_analysis_4th_grade.py
```

## Architecture Overview

### Core Components
- **Multi-Agent System**: 4 specialized agents work together
  - `Coordinador` - Orchestrates the complete workflow
  - `Analizador` - Processes activities and extracts tasks
  - `Perfilador` - Manages student profiles and neurological diversity
  - `Optimizador` - Assigns tasks based on student capabilities
  
- **LLM Integration**: Supports both local (Ollama) and cloud (Groq) models
- **Embeddings System**: Intelligent activity selection using semantic similarity
- **Coherence Validator**: Ensures pedagogical quality of generated activities

### Key Directories
```
src/
├── agents/          # Specialized AI agents
├── core/            # Core functionality (system, context, validation)
├── models/          # Data models (student, activity, project)  
├── mvp/             # Simplified MVP implementation (use for development)
├── ui/              # User interface components
└── utils/           # Utilities (JSON parsing, logging)

data/
├── actividades/     # Educational activity templates
├── data_processing/ # Data cleaning and processing scripts
├── processed/       # Processed student profiles
└── raw/             # Raw datasets and regulatory documents
```

### Entry Points
- `src/app.py` - Main application entry point (full system)
- `src/mvp/simple_cli.py` - Simplified CLI interface (recommended for development)
- Various data processing scripts in `data/data_processing/`

## Configuration

### Main Configuration
Configuration is centralized in `src/config.py`:
- LLM provider settings (Ollama/Groq)
- Agent behavior parameters
- Directory paths
- Logging configuration

### LLM Configuration
The system supports two providers:
- **Groq** (cloud): Currently configured as default, uses `GROQ_API_KEY` from `.env`
- **Ollama** (local): Available as fallback at `192.168.1.10:11434`

Current configuration:
- Generation: `openai/gpt-oss-120b` (Groq) 
- Embeddings: `nomic-embed-text` (Ollama local)
- Provider setting in `src/config.py` line 19

## Dataset Information

The system uses a real dataset of **394 4th grade students** with:
- Neurological profiles: Autism (TEA), ADHD, high capacity, neurotypical
- Curricular competencies by subject
- DUA adaptations and specific learning needs
- All data is anonymized for educational research

## Development Notes

### Current System State
- ✅ **Functional**: Activity generation, personalization, validation
- ⚠️  **In Development**: UI improvements, metrics, comprehensive testing
- ❌ **Pending**: Web interface, empirical validation, scalability optimization

### Code Conventions
- Spanish language used for comments and documentation (educational context)
- Agent-based architecture with clear separation of concerns
- JSON-based configuration and data exchange
- Comprehensive logging throughout the system

### Testing Approach
Limited automated testing currently implemented. Key test files:
- `src/test_mejoras_analizador.py` - Analyzer improvements
- `data/expansion datos/test_dataset_expandido.py` - Dataset expansion validation

### Important Implementation Details
- The MVP version (`src/mvp/`) is more stable and recommended for development
- System supports both synchronous and asynchronous agent communication
- Embeddings are used for intelligent activity template selection
- All generated activities undergo coherence validation before delivery
- Student privacy is protected through data anonymization

### Working with the Codebase
- Use the MVP version for development and testing
- The main system in `src/app.py` is more complex but feature-complete  
- Data processing scripts are independent and can be run individually
- Configuration changes should be made in `src/config.py`
- Student profiles are loaded from JSON files in the data directory