#!/usr/bin/env python3
"""
Analyzer for 4th grade student profiles to select diverse pilot classroom
"""

import json
import statistics
from collections import defaultdict, Counter
import random

def load_profiles(file_path):
    """Load and parse the 4th grade profiles JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def analyze_academic_levels(profiles):
    """Analyze the range of academic levels across subjects"""
    # Handle different profile structures
    subjects_mapping = {
        'matematicas': ['matematicas'],
        'lectura': ['lectura'],
        'escritura': ['escritura', 'lengua_castellana'],  # escritura might be called lengua_castellana
        'ciencias': ['ciencias', 'ciencias_naturales']
    }
    
    analysis = {}
    
    for subject, possible_fields in subjects_mapping.items():
        levels = []
        for p in profiles:
            value = None
            for field in possible_fields:
                if field in p['perfil_academico']:
                    value = p['perfil_academico'][field]
                    break
            if value is not None:
                levels.append(value)
        
        if levels:
            analysis[subject] = {
                'min': min(levels),
                'max': max(levels),
                'mean': round(statistics.mean(levels), 2),
                'distribution': dict(Counter(levels)),
                'count': len(levels)
            }
    
    return analysis

def analyze_cognitive_profiles(profiles):
    """Analyze cognitive profile ranges"""
    cognitive_attrs = ['atencion_sostenida', 'atencion_selectiva', 'memoria_trabajo', 
                      'velocidad_procesamiento', 'control_inhibitorio', 'flexibilidad_cognitiva', 
                      'ci_estimado', 'variabilidad_rendimiento']
    
    analysis = {}
    for attr in cognitive_attrs:
        values = [p['perfil_cognitivo'][attr] for p in profiles]
        analysis[attr] = {
            'min': min(values),
            'max': max(values),
            'mean': round(statistics.mean(values), 2),
            'std': round(statistics.stdev(values), 2) if len(values) > 1 else 0
        }
    
    return analysis

def analyze_behavioral_patterns(profiles):
    """Analyze behavioral patterns and emotional regulation"""
    behavioral_attrs = ['regulacion_emocional', 'tolerancia_frustracion', 'habilidades_sociales',
                       'impulsividad', 'nivel_actividad']
    
    analysis = {}
    for attr in behavioral_attrs:
        values = [p['perfil_conductual'][attr] for p in profiles]
        analysis[attr] = {
            'min': min(values),
            'max': max(values),
            'mean': round(statistics.mean(values), 2),
            'distribution': dict(Counter(values))
        }
    
    # Analyze triggers and motivators
    all_triggers = []
    all_motivators = []
    
    for p in profiles:
        all_triggers.extend(p['perfil_conductual']['triggers'])
        all_motivators.extend(p['perfil_conductual']['motivadores'])
    
    analysis['triggers'] = dict(Counter(all_triggers))
    analysis['motivadores'] = dict(Counter(all_motivators))
    
    return analysis

def analyze_learning_styles(profiles):
    """Analyze learning style preferences"""
    styles_analysis = {}
    
    # Channel preferences
    channels = [p['estilo_aprendizaje']['canal_preferido'] for p in profiles]
    styles_analysis['canal_preferido'] = dict(Counter(channels))
    
    # Grouping preferences
    groupings = [p['estilo_aprendizaje']['agrupamiento_optimo'] for p in profiles]
    styles_analysis['agrupamiento_optimo'] = dict(Counter(groupings))
    
    # Movement needs
    movement_needs = [p['estilo_aprendizaje']['necesita_movimiento'] for p in profiles]
    styles_analysis['necesita_movimiento'] = dict(Counter(movement_needs))
    
    # Noise sensitivity
    noise_sensitive = [p['estilo_aprendizaje']['sensible_ruido'] for p in profiles]
    styles_analysis['sensible_ruido'] = dict(Counter(noise_sensitive))
    
    # Learning support preferences
    learning_supports = []
    for p in profiles:
        learning_supports.extend(p['estilo_aprendizaje']['aprende_mejor_con'])
    styles_analysis['aprende_mejor_con'] = dict(Counter(learning_supports))
    
    return styles_analysis

def analyze_curricular_states(profiles):
    """Analyze the curricular states across all subjects"""
    subjects = ['matematicas', 'lengua', 'ciencias']
    states_analysis = {}
    
    for subject in subjects:
        states_analysis[subject] = {}
        
        # Get all curriculum items for this subject
        if profiles and 'estado_curricular' in profiles[0]:
            curriculum_items = list(profiles[0]['estado_curricular'][subject].keys())
            
            for item in curriculum_items:
                states = []
                for p in profiles:
                    if 'estado_curricular' in p and subject in p['estado_curricular']:
                        if item in p['estado_curricular'][subject]:
                            states.append(p['estado_curricular'][subject][item]['estado'])
                
                if states:
                    states_analysis[subject][item] = dict(Counter(states))
    
    return states_analysis

def analyze_student_types(profiles):
    """Analyze distribution of student types"""
    types = []
    for p in profiles:
        if 'metadatos' in p and 'fuente_datos' in p['metadatos']:
            source = p['metadatos']['fuente_datos']
            if 'doble_excepcionalidad' in source or '2e' in source.lower():
                types.append('doble_excepcionalidad')
            else:
                types.append('tipico')
        else:
            types.append('tipico')  # Default assumption
    
    return dict(Counter(types))

def calculate_diversity_score(profile):
    """Calculate a diversity score for profile selection"""
    # Get academic scores, handling different profile structures
    academic_scores = []
    
    if 'matematicas' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['matematicas'])
    if 'lectura' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['lectura'])
    if 'escritura' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['escritura'])
    elif 'lengua_castellana' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['lengua_castellana'])
    if 'ciencias' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['ciencias'])
    elif 'ciencias_naturales' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['ciencias_naturales'])
    
    # Calculate academic variance
    academic_variance = statistics.stdev(academic_scores) if len(academic_scores) > 1 and len(set(academic_scores)) > 1 else 0
    
    cognitive_profile = [
        profile['perfil_cognitivo']['atencion_sostenida'],
        profile['perfil_cognitivo']['memoria_trabajo'],
        profile['perfil_cognitivo']['velocidad_procesamiento'],
        profile['perfil_cognitivo']['ci_estimado']
    ]
    
    # Normalize CI to same scale (1-5)
    ci_normalized = min(5, max(1, (profile['perfil_cognitivo']['ci_estimado'] - 70) / 20))
    cognitive_profile[-1] = ci_normalized
    
    cognitive_variance = statistics.stdev(cognitive_profile) if len(set(cognitive_profile)) > 1 else 0
    
    return academic_variance + cognitive_variance

def select_diverse_students(profiles, n=25):
    """Select 25 diverse students using stratified sampling"""
    selected = []
    
    # Add all double exceptionality students first (they're rare)
    de_students = []
    typical_students = []
    
    for i, p in enumerate(profiles):
        if 'metadatos' in p and 'fuente_datos' in p['metadatos']:
            source = p['metadatos']['fuente_datos']
            if 'doble_excepcionalidad' in source or '2e' in source.lower():
                de_students.append((i, p))
            else:
                typical_students.append((i, p))
        else:
            typical_students.append((i, p))
    
    # Include all double exceptionality students (should be ~3)
    for idx, profile in de_students:
        selected.append((idx, profile, "doble_excepcionalidad"))
    
    # Now select from typical students to fill remaining spots
    remaining_spots = n - len(selected)
    
    # Stratify by academic performance levels
    low_performers = []   # Average score 1-2.5
    mid_performers = []   # Average score 2.6-3.5
    high_performers = []  # Average score 3.6-5
    
    for idx, profile in typical_students:
        # Get academic scores, handling different profile structures
        academic_scores = []
        
        # Math
        if 'matematicas' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['matematicas'])
        
        # Reading  
        if 'lectura' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['lectura'])
        
        # Writing (escritura or lengua_castellana)
        if 'escritura' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['escritura'])
        elif 'lengua_castellana' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['lengua_castellana'])
        
        # Science
        if 'ciencias' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['ciencias'])
        elif 'ciencias_naturales' in profile['perfil_academico']:
            academic_scores.append(profile['perfil_academico']['ciencias_naturales'])
        
        if academic_scores:
            avg_academic = statistics.mean(academic_scores)
        else:
            avg_academic = 3.0  # Default middle value
        
        if avg_academic <= 2.5:
            low_performers.append((idx, profile))
        elif avg_academic <= 3.5:
            mid_performers.append((idx, profile))
        else:
            high_performers.append((idx, profile))
    
    # Select proportionally with some diversity focus
    groups = [
        ("bajo_rendimiento", low_performers, max(1, remaining_spots // 4)),
        ("medio_rendimiento", mid_performers, max(1, remaining_spots // 2)),
        ("alto_rendimiento", high_performers, max(1, remaining_spots // 4))
    ]
    
    for group_name, group_profiles, target_count in groups:
        # Sort by diversity score and select
        group_with_scores = [(idx, p, calculate_diversity_score(p)) for idx, p in group_profiles]
        group_with_scores.sort(key=lambda x: x[2], reverse=True)  # High diversity first
        
        # Select up to target_count, but don't exceed available
        actual_count = min(target_count, len(group_with_scores), remaining_spots)
        
        for i in range(actual_count):
            idx, profile, _ = group_with_scores[i]
            selected.append((idx, profile, group_name))
            remaining_spots -= 1
    
    # Fill any remaining spots with highest diversity scores
    if remaining_spots > 0:
        remaining_profiles = []
        selected_indices = {idx for idx, _, _ in selected}
        
        for idx, profile in typical_students:
            if idx not in selected_indices:
                remaining_profiles.append((idx, profile, calculate_diversity_score(profile)))
        
        remaining_profiles.sort(key=lambda x: x[2], reverse=True)
        
        for i in range(min(remaining_spots, len(remaining_profiles))):
            idx, profile, _ = remaining_profiles[i]
            selected.append((idx, profile, "diversidad_adicional"))
    
    return selected

def generate_profile_summary(idx, profile, selection_reason):
    """Generate a summary for a selected student profile"""
    # Get academic scores, handling different profile structures
    academic_scores = []
    academic_detail = {}
    
    if 'matematicas' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['matematicas'])
        academic_detail['matematicas'] = profile['perfil_academico']['matematicas']
    
    if 'lectura' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['lectura'])
        academic_detail['lectura'] = profile['perfil_academico']['lectura']
    
    if 'escritura' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['escritura'])
        academic_detail['escritura'] = profile['perfil_academico']['escritura']
    elif 'lengua_castellana' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['lengua_castellana'])
        academic_detail['escritura'] = profile['perfil_academico']['lengua_castellana']
    
    if 'ciencias' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['ciencias'])
        academic_detail['ciencias'] = profile['perfil_academico']['ciencias']
    elif 'ciencias_naturales' in profile['perfil_academico']:
        academic_scores.append(profile['perfil_academico']['ciencias_naturales'])
        academic_detail['ciencias'] = profile['perfil_academico']['ciencias_naturales']
    
    # Calculate average academic performance
    avg_academic = statistics.mean(academic_scores) if academic_scores else 3.0
    
    # Get key cognitive characteristics
    ci = profile['perfil_cognitivo']['ci_estimado']
    attention = profile['perfil_cognitivo']['atencion_sostenida']
    memory = profile['perfil_cognitivo']['memoria_trabajo']
    processing_speed = profile['perfil_cognitivo']['velocidad_procesamiento']
    
    # Get behavioral characteristics
    emotional_reg = profile['perfil_conductual']['regulacion_emocional']
    impulsivity = profile['perfil_conductual']['impulsividad']
    activity_level = profile['perfil_conductual']['nivel_actividad']
    
    # Get learning preferences
    learning_channel = profile['estilo_aprendizaje']['canal_preferido']
    grouping = profile['estilo_aprendizaje']['agrupamiento_optimo']
    needs_movement = profile['estilo_aprendizaje']['necesita_movimiento']
    
    # Get strengths and difficulties
    strengths = profile['perfil_academico'].get('fortalezas_observadas', [])
    difficulties = profile['perfil_academico'].get('dificultades_observadas', [])
    
    # Get motivators and triggers
    motivators = profile['perfil_conductual']['motivadores']
    triggers = profile['perfil_conductual']['triggers']
    
    summary = {
        'student_id': f"Estudiante_{idx+1}",
        'selection_reason': selection_reason,
        'academic_average': round(avg_academic, 1),
        'academic_detail': academic_detail,
        'cognitive_profile': {
            'ci_estimado': ci,
            'atencion': attention,
            'memoria_trabajo': memory,
            'velocidad_procesamiento': processing_speed
        },
        'behavioral_profile': {
            'regulacion_emocional': emotional_reg,
            'impulsividad': impulsivity,
            'nivel_actividad': activity_level
        },
        'learning_style': {
            'canal_preferido': learning_channel,
            'agrupamiento_optimo': grouping,
            'necesita_movimiento': needs_movement
        },
        'strengths': strengths,
        'difficulties': difficulties,
        'motivators': motivators,
        'triggers': triggers
    }
    
    return summary

def main():
    """Main analysis function"""
    file_path = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/processed/por_curso/perfiles_4_primaria.json"
    
    print("Loading 4th grade profiles...")
    data = load_profiles(file_path)
    profiles = data['perfiles']
    
    print(f"Total profiles loaded: {len(profiles)}")
    print(f"Metadata shows: {data['metadata']['total_perfiles']} profiles")
    print(f"Distribution: {data['metadata']['distribucion_tipos']}")
    
    print("\n" + "="*80)
    print("COMPREHENSIVE ANALYSIS OF 4TH GRADE PROFILES")
    print("="*80)
    
    # 1. Academic levels analysis
    print("\n1. ACADEMIC LEVELS ANALYSIS")
    print("-" * 40)
    academic_analysis = analyze_academic_levels(profiles)
    for subject, stats in academic_analysis.items():
        print(f"{subject.upper()}:")
        print(f"  Range: {stats['min']}-{stats['max']} (Mean: {stats['mean']})")
        print(f"  Distribution: {stats['distribution']}")
    
    # 2. Cognitive profiles analysis  
    print("\n2. COGNITIVE PROFILES ANALYSIS")
    print("-" * 40)
    cognitive_analysis = analyze_cognitive_profiles(profiles)
    for attr, stats in cognitive_analysis.items():
        print(f"{attr}: {stats['min']}-{stats['max']} (Mean: {stats['mean']}, SD: {stats['std']})")
    
    # 3. Behavioral patterns analysis
    print("\n3. BEHAVIORAL PATTERNS ANALYSIS")
    print("-" * 40)
    behavioral_analysis = analyze_behavioral_patterns(profiles)
    for attr in ['regulacion_emocional', 'tolerancia_frustracion', 'habilidades_sociales', 'impulsividad', 'nivel_actividad']:
        if attr in behavioral_analysis:
            stats = behavioral_analysis[attr]
            print(f"{attr}: {stats['min']}-{stats['max']} (Mean: {stats['mean']})")
    
    print(f"\nTop triggers: {list(behavioral_analysis['triggers'].items())[:5]}")
    print(f"Top motivators: {list(behavioral_analysis['motivadores'].items())[:5]}")
    
    # 4. Learning styles analysis
    print("\n4. LEARNING STYLES ANALYSIS")
    print("-" * 40)
    learning_analysis = analyze_learning_styles(profiles)
    for style_type, distribution in learning_analysis.items():
        print(f"{style_type}: {distribution}")
    
    # 5. Curricular states analysis
    print("\n5. CURRICULAR STATES ANALYSIS")
    print("-" * 40)
    curricular_analysis = analyze_curricular_states(profiles)
    for subject, items in curricular_analysis.items():
        print(f"\n{subject.upper()}:")
        for item, states in items.items():
            print(f"  {item}: {states}")
    
    # 6. Student types analysis
    print("\n6. STUDENT TYPES ANALYSIS")
    print("-" * 40)
    types_analysis = analyze_student_types(profiles)
    print(f"Student types distribution: {types_analysis}")
    
    # 7. Select diverse students for pilot
    print("\n" + "="*80)
    print("SELECTION OF 25 DIVERSE STUDENTS FOR PILOT CLASSROOM")
    print("="*80)
    
    selected_students = select_diverse_students(profiles, 25)
    
    print(f"\nSelected {len(selected_students)} students for pilot classroom:")
    print("\nDETAILED PROFILES OF SELECTED STUDENTS:")
    print("="*60)
    
    for idx, (orig_idx, profile, reason) in enumerate(selected_students, 1):
        summary = generate_profile_summary(orig_idx, profile, reason)
        
        print(f"\n{idx}. {summary['student_id']} (Original index: {orig_idx})")
        print(f"Selection reason: {summary['selection_reason']}")
        print(f"Academic average: {summary['academic_average']}/5")
        print(f"Academic detail: Math:{summary['academic_detail']['matematicas']} Reading:{summary['academic_detail']['lectura']} Writing:{summary['academic_detail']['escritura']} Science:{summary['academic_detail']['ciencias']}")
        print(f"Cognitive: CI:{summary['cognitive_profile']['ci_estimado']} Attention:{summary['cognitive_profile']['atencion']} Memory:{summary['cognitive_profile']['memoria_trabajo']} Speed:{summary['cognitive_profile']['velocidad_procesamiento']}")
        print(f"Behavioral: EmotReg:{summary['behavioral_profile']['regulacion_emocional']} Impulsivity:{summary['behavioral_profile']['impulsividad']} Activity:{summary['behavioral_profile']['nivel_actividad']}")
        print(f"Learning: {summary['learning_style']['canal_preferido']} channel, {summary['learning_style']['agrupamiento_optimo']} grouping, movement:{summary['learning_style']['necesita_movimiento']}")
        print(f"Strengths: {', '.join(summary['strengths'][:3])}")
        print(f"Difficulties: {', '.join(summary['difficulties'])}")
        print(f"Motivators: {', '.join(summary['motivators'][:3])}")
        print(f"Triggers: {', '.join(summary['triggers'][:2])}")
    
    # Summary statistics of selection
    print("\n" + "="*60)
    print("SELECTION SUMMARY STATISTICS")
    print("="*60)
    
    selection_reasons = [reason for _, _, reason in selected_students]
    selection_distribution = Counter(selection_reasons)
    print(f"Selection distribution: {dict(selection_distribution)}")
    
    # Academic diversity in selection
    selected_profiles = [profile for _, profile, _ in selected_students]
    selected_academic = analyze_academic_levels(selected_profiles)
    print(f"\nAcademic diversity in selection:")
    for subject, stats in selected_academic.items():
        print(f"  {subject}: {stats['min']}-{stats['max']} (Mean: {stats['mean']})")
    
    # Cognitive diversity in selection
    selected_cognitive = analyze_cognitive_profiles(selected_profiles)
    print(f"\nCognitive diversity in selection:")
    print(f"  CI range: {selected_cognitive['ci_estimado']['min']}-{selected_cognitive['ci_estimado']['max']}")
    print(f"  Attention range: {selected_cognitive['atencion_sostenida']['min']}-{selected_cognitive['atencion_sostenida']['max']}")
    print(f"  Memory range: {selected_cognitive['memoria_trabajo']['min']}-{selected_cognitive['memoria_trabajo']['max']}")
    
    # Learning style diversity
    selected_learning = analyze_learning_styles(selected_profiles)
    print(f"\nLearning style diversity in selection:")
    print(f"  Channels: {selected_learning['canal_preferido']}")
    print(f"  Grouping: {selected_learning['agrupamiento_optimo']}")
    print(f"  Movement needs: {selected_learning['necesita_movimiento']}")

if __name__ == "__main__":
    main()