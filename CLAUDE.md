# CLAUDE.md

you can use it with the command:

```bash
npx @anthropic-ai/claude-code
```

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IA4EDU is an AI assistant for creating inclusive project-based learning activities for diverse neurotype classrooms. The system uses CrewAI agents with Gemini models to analyze teacher requests, research activity libraries, and design personalized activities for 8 student profiles including TEA (autism), TDAH (ADHD), High Abilities, and typical development.

## Key Architecture

### Agent System (`agents/crew_agents.py`)
- **AnalystAgent**: Analyzes teacher requests and student profiles using pedagogical expertise
- **ResearcherAgent**: Searches activity library (`data/k_*.md` files) for relevant examples
- **DesignerAgent**: Creates complete activities using structured templates
- **RefinementAgent**: Iteratively improves activities based on teacher feedback
- **IA4EDUCrew**: Orchestrates the multi-agent workflow using CrewAI

### Core Components
- **Main Interface** (`main.py`): Interactive CLI using Typer and Rich for teacher interaction
- **Activity Template** (`templates/activity_template.py`): Pydantic models defining activity structure
- **Student Profiles** (`data/perfiles_4_primaria.json`): 8 detailed student profiles with neurotype characteristics
- **Activity Library** (`data/k_*.md`): Knowledge base of successful inclusive activities

### Data Flow
1. Teacher describes desired activity via CLI
2. Analyst agent analyzes request + student profiles
3. Researcher agent finds relevant examples from library
4. Designer agent creates complete activity with neurotype-specific adaptations
5. Human-in-the-loop refinement based on teacher feedback

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy .env.example to .env if needed)
# Key variables:
LLM_PROVIDER=gemini  # Default LLM provider
LLM_API_KEY=your_gemini_api_key  # Or GEMINI_API_KEY for backward compatibility
LLM_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
```

### Running the Application
```bash
# Interactive CLI session
python main.py

# Using Docker
docker build -t ia4edu .
docker run --env-file .env ia4edu
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Key Design Principles

### Terrain Adaptation Paradigm
The system designs activities from the ground up for all neurotypes rather than retrofitting adaptations. Each activity includes specific strategies for:
- TEA: Structure, visual instructions, processing time
- TDAH: Movement, breaks, multisensory stimuli
- High Abilities: Additional complexity, autonomy, independent projects
- Typical: Collaboration, feedback, concrete examples

### Activity Structure
Activities follow a structured template with:
- General information (title, subject, duration)
- Learning and inclusion objectives
- Multi-phase implementation with specific tasks
- Student group assignments leveraging individual strengths
- Neurotype-specific materials and adaptations
- Inclusive evaluation criteria

### Student-Centered Design
The system works with 8 predefined student profiles containing:
- Formal diagnosis and support level
- Learning style and preferred channels
- Temperament and frustration tolerance
- Subject-specific competency levels
- Individual interests and strengths

## Key Files for Modification

- `agents/crew_agents.py`: Agent logic and AI model configuration
- `templates/activity_template.py`: Activity structure and validation
- `data/perfiles_4_primaria.json`: Student profiles (modify for different grade levels)
- `data/k_*.md`: Activity library examples
- `main.py`: User interface and workflow orchestration