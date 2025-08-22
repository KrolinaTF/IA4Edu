#!/usr/bin/env python3
"""
Test para verificar la carga de actividades desde archivos .md
"""

import sys
sys.path.append('.')
from agents.crew_agents import load_activity_library, load_full_activity

print("🔍 Probando carga de biblioteca de actividades...\n")
print("="*60)

# Cargar resumen de actividades
library = load_activity_library()
print(library)

print("="*60)
print("\n📄 Cargando una actividad completa de ejemplo...")
print("="*60)

# Cargar una actividad completa
full_activity = load_full_activity("data/k_feria_acertijos.md")
print(f"Primeras 500 caracteres de k_feria_acertijos.md:\n")
print(full_activity[:500] + "...")

print("\n✅ Test completado!")