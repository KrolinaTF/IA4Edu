#!/usr/bin/env python3
"""
Tests para los agentes de CrewAI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.crew_agents import (
    load_student_profiles, 
    load_activity_library,
    load_full_activity
)

def test_load_student_profiles():
    """Test de carga de perfiles de estudiantes"""
    print("🧑‍🎓 Testing load_student_profiles...")
    profiles = load_student_profiles()
    assert "Error" not in profiles, f"Error loading profiles: {profiles}"
    assert len(profiles) > 0, "No profiles loaded"
    print("✅ Student profiles loaded successfully")
    print(f"   - Loaded {profiles.count('estudiante')} student profiles")
    return True

def test_load_activity_library():
    """Test de carga de biblioteca de actividades"""
    print("\n📚 Testing load_activity_library...")
    library = load_activity_library()
    assert "Error" not in library, f"Error loading library: {library}"
    assert "BIBLIOTECA DE ACTIVIDADES" in library, "Library format incorrect"
    
    # Contar número de actividades
    activity_count = library.count("Archivo: data/k_")
    print(f"✅ Activity library loaded successfully")
    print(f"   - Found {activity_count} activities")
    return True

def test_load_full_activity():
    """Test de carga de actividad completa"""
    print("\n📄 Testing load_full_activity...")
    
    # Test con archivo existente
    activity = load_full_activity("data/k_feria_acertijos.md")
    assert "Error" not in activity, f"Error loading activity: {activity}"
    assert len(activity) > 100, "Activity content too short"
    print("✅ Full activity loaded successfully")
    print(f"   - Loaded {len(activity)} characters")
    
    # Test con archivo no existente
    error_activity = load_full_activity("data/no_existe.md")
    assert "Error" in error_activity, "Should return error for non-existent file"
    print("✅ Error handling works correctly")
    
    return True

def run_all_tests():
    """Ejecutar todos los tests"""
    print("🚀 Running IA4EDU Agent Tests")
    print("="*50)
    
    tests = [
        test_load_student_profiles,
        test_load_activity_library,
        test_load_full_activity
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {str(e)}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)