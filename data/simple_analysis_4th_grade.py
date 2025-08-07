#!/usr/bin/env python3
"""
Simplified analyzer for 4th grade student profiles to select diverse pilot classroom
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

def get_academic_score(profile, subject):
    """Get academic score for a subject, handling different profile structures"""
    academic = profile['perfil_academico']
    
    subject_mappings = {
        'matematicas': ['matematicas'],
        'lectura': ['lectura'],
        'escritura': ['escritura', 'lengua_castellana'],
        'ciencias': ['ciencias', 'ciencias_naturales']
    }
    
    for field in subject_mappings.get(subject, [subject]):
        if field in academic:
            return academic[field]
    
    return None

def get_cognitive_score(profile, attribute):
    """Get cognitive score for an attribute, handling different profile structures"""
    if 'perfil_cognitivo' not in profile:
        return None
        
    cognitive = profile['perfil_cognitivo']
    
    # Mapping between different naming conventions
    attr_mappings = {
        'atencion': ['atencion_sostenida', 'atencion_concentracion'],
        'memoria': ['memoria_trabajo'],
        'velocidad': ['velocidad_procesamiento'],
        'ci': ['ci_estimado']
    }
    
    for field in attr_mappings.get(attribute, [attribute]):
        if field in cognitive:
            return cognitive[field]
    
    return None

def get_behavioral_score(profile, attribute):
    """Get behavioral score for an attribute, handling different profile structures"""
    if 'perfil_conductual' not in profile:
        return None
        
    behavioral = profile['perfil_conductual']
    
    # Mapping between different naming conventions
    attr_mappings = {
        'regulacion': ['regulacion_emocional', 'autorregulacion'],
        'impulsividad': ['impulsividad'],
        'actividad': ['nivel_actividad', 'hiperactividad'],
        'habilidades_sociales': ['habilidades_sociales']
    }
    
    for field in attr_mappings.get(attribute, [attribute]):
        if field in behavioral:
            return behavioral[field]
    
    return None

def analyze_complete_dataset(profiles):
    """Provide comprehensive analysis of all profiles"""
    print("="*80)
    print("COMPREHENSIVE ANALYSIS OF 4TH GRADE PROFILES")
    print("="*80)
    
    total_profiles = len(profiles)
    print(f"Total profiles: {total_profiles}")
    
    # 1. Academic Levels Analysis
    print("\n1. ACADEMIC LEVELS ANALYSIS")
    print("-" * 40)
    
    subjects = ['matematicas', 'lectura', 'escritura', 'ciencias']
    academic_analysis = {}
    
    for subject in subjects:
        scores = []
        for profile in profiles:
            score = get_academic_score(profile, subject)
            if score is not None:
                scores.append(score)
        
        if scores:
            academic_analysis[subject] = {
                'count': len(scores),
                'min': min(scores),
                'max': max(scores),
                'mean': round(statistics.mean(scores), 2),
                'distribution': dict(Counter(scores))
            }
            
            print(f"{subject.upper()}: {len(scores)} students")
            print(f"  Range: {min(scores)}-{max(scores)} (Mean: {round(statistics.mean(scores), 2)})")
            print(f"  Distribution: {dict(Counter(scores))}")
    
    # 2. Cognitive Profiles Analysis
    print("\n2. COGNITIVE PROFILES ANALYSIS")
    print("-" * 40)
    
    cognitive_attrs = ['atencion', 'memoria', 'velocidad', 'ci']
    cognitive_analysis = {}
    
    for attr in cognitive_attrs:
        scores = []
        for profile in profiles:
            score = get_cognitive_score(profile, attr)
            if score is not None:
                scores.append(score)
        
        if scores:
            cognitive_analysis[attr] = {
                'count': len(scores),
                'min': min(scores),
                'max': max(scores),
                'mean': round(statistics.mean(scores), 2)
            }
            
            print(f"{attr}: {len(scores)} students, range {min(scores)}-{max(scores)}, mean {round(statistics.mean(scores), 2)}")
    
    # 3. Behavioral Patterns Analysis
    print("\n3. BEHAVIORAL PATTERNS ANALYSIS")
    print("-" * 40)
    
    behavioral_attrs = ['regulacion', 'impulsividad', 'actividad', 'habilidades_sociales']
    behavioral_analysis = {}
    
    for attr in behavioral_attrs:
        scores = []
        for profile in profiles:
            score = get_behavioral_score(profile, attr)
            if score is not None:
                scores.append(score)
        
        if scores:
            behavioral_analysis[attr] = {
                'count': len(scores),
                'min': min(scores),
                'max': max(scores),
                'mean': round(statistics.mean(scores), 2)
            }
            
            print(f"{attr}: {len(scores)} students, range {min(scores)}-{max(scores)}, mean {round(statistics.mean(scores), 2)}")
    
    # 4. Learning Styles Analysis
    print("\n4. LEARNING STYLES ANALYSIS")
    print("-" * 40)
    
    learning_channels = []
    grouping_prefs = []
    movement_needs = []
    
    for profile in profiles:
        if 'estilo_aprendizaje' in profile:
            estilo = profile['estilo_aprendizaje']
            
            # Channel preferences
            if 'canal_preferido' in estilo:
                learning_channels.append(estilo['canal_preferido'])
            elif 'canal_preferente' in estilo:
                learning_channels.append(estilo['canal_preferente'])
            
            # Grouping preferences
            if 'agrupamiento_optimo' in estilo:
                grouping_prefs.append(estilo['agrupamiento_optimo'])
            elif 'tipo_agrupamiento' in estilo:
                grouping_prefs.append(estilo['tipo_agrupamiento'])
            
            # Movement needs
            if 'necesita_movimiento' in estilo:
                movement_needs.append(estilo['necesita_movimiento'])
    
    if learning_channels:
        print(f"Learning channels: {dict(Counter(learning_channels))}")
    if grouping_prefs:
        print(f"Grouping preferences: {dict(Counter(grouping_prefs))}")
    if movement_needs:
        print(f"Movement needs: {dict(Counter(movement_needs))}")
    
    # 5. Student Types Analysis
    print("\n5. STUDENT TYPES ANALYSIS")
    print("-" * 40)
    
    student_types = []
    for profile in profiles:
        if 'metadatos' in profile and 'fuente_datos' in profile['metadatos']:
            source = profile['metadatos']['fuente_datos']
            if 'doble_excepcionalidad' in source or '2e' in source.lower():
                student_types.append('doble_excepcionalidad')
            else:
                student_types.append('tipico')
        else:
            student_types.append('tipico')
    
    type_distribution = dict(Counter(student_types))
    print(f"Student types: {type_distribution}")
    
    return {
        'academic': academic_analysis,
        'cognitive': cognitive_analysis,
        'behavioral': behavioral_analysis,
        'types': type_distribution,
        'total': total_profiles
    }

def calculate_academic_average(profile):
    """Calculate academic average for a profile"""
    subjects = ['matematicas', 'lectura', 'escritura', 'ciencias']
    scores = []
    
    for subject in subjects:
        score = get_academic_score(profile, subject)
        if score is not None:
            scores.append(score)
    
    return statistics.mean(scores) if scores else 3.0

def select_diverse_students(profiles, n=25):
    """Select diverse students for pilot classroom"""
    print("\n" + "="*80)
    print("SELECTION OF 25 DIVERSE STUDENTS FOR PILOT CLASSROOM")
    print("="*80)
    
    selected = []
    
    # First, separate by student type
    de_students = []
    typical_students = []
    
    for i, profile in enumerate(profiles):
        if 'metadatos' in profile and 'fuente_datos' in profile['metadatos']:
            source = profile['metadatos']['fuente_datos']
            if 'doble_excepcionalidad' in source or '2e' in source.lower():
                de_students.append((i, profile))
            else:
                typical_students.append((i, profile))
        else:
            typical_students.append((i, profile))
    
    # Include all double exceptionality students (diversity priority)
    print(f"Found {len(de_students)} double exceptionality students - including all")
    for idx, profile in de_students:
        selected.append((idx, profile, "doble_excepcionalidad"))
    
    # Select from typical students to fill remaining spots
    remaining_spots = n - len(selected)
    print(f"Selecting {remaining_spots} typical students from {len(typical_students)} available")
    
    # Stratify typical students by academic performance
    low_performers = []   # Average score <= 2.5
    mid_performers = []   # Average score 2.6-3.5
    high_performers = []  # Average score >= 3.6
    
    for idx, profile in typical_students:
        avg_academic = calculate_academic_average(profile)
        
        if avg_academic <= 2.5:
            low_performers.append((idx, profile))
        elif avg_academic <= 3.5:
            mid_performers.append((idx, profile))
        else:
            high_performers.append((idx, profile))
    
    print(f"Performance distribution: Low: {len(low_performers)}, Mid: {len(mid_performers)}, High: {len(high_performers)}")
    
    # Select proportionally but ensure representation from each group
    target_low = max(1, remaining_spots // 4)
    target_mid = max(1, remaining_spots // 2)
    target_high = remaining_spots - target_low - target_mid
    
    # Adjust if we don't have enough in any category
    target_low = min(target_low, len(low_performers))
    target_mid = min(target_mid, len(mid_performers))
    target_high = min(target_high, len(high_performers))
    
    # Fill remaining if needed
    remaining_after_targets = remaining_spots - target_low - target_mid - target_high
    if remaining_after_targets > 0:
        # Add to mid performers first (largest group typically)
        if len(mid_performers) > target_mid:
            target_mid += remaining_after_targets
        elif len(high_performers) > target_high:
            target_high += remaining_after_targets
        else:
            target_low += remaining_after_targets
    
    # Randomly select from each group (could be made more sophisticated)
    import random
    random.seed(42)  # For reproducible results
    
    # Select low performers
    low_selected = random.sample(low_performers, min(target_low, len(low_performers)))
    for idx, profile in low_selected:
        selected.append((idx, profile, "bajo_rendimiento"))
    
    # Select mid performers
    mid_selected = random.sample(mid_performers, min(target_mid, len(mid_performers)))
    for idx, profile in mid_selected:
        selected.append((idx, profile, "medio_rendimiento"))
    
    # Select high performers
    high_selected = random.sample(high_performers, min(target_high, len(high_performers)))
    for idx, profile in high_selected:
        selected.append((idx, profile, "alto_rendimiento"))
    
    return selected

def generate_student_summary(idx, profile, selection_reason):
    """Generate summary for a selected student"""
    # Academic scores
    academic_scores = {}
    subjects = ['matematicas', 'lectura', 'escritura', 'ciencias']
    for subject in subjects:
        score = get_academic_score(profile, subject)
        if score is not None:
            academic_scores[subject] = score
    
    avg_academic = calculate_academic_average(profile)
    
    # Cognitive scores
    cognitive_scores = {}
    cognitive_attrs = ['atencion', 'memoria', 'velocidad', 'ci']
    for attr in cognitive_attrs:
        score = get_cognitive_score(profile, attr)
        if score is not None:
            cognitive_scores[attr] = score
    
    # Behavioral scores
    behavioral_scores = {}
    behavioral_attrs = ['regulacion', 'impulsividad', 'actividad', 'habilidades_sociales']
    for attr in behavioral_attrs:
        score = get_behavioral_score(profile, attr)
        if score is not None:
            behavioral_scores[attr] = score
    
    # Learning style
    learning_style = {}
    if 'estilo_aprendizaje' in profile:
        estilo = profile['estilo_aprendizaje']
        
        # Get channel preference
        if 'canal_preferido' in estilo:
            learning_style['canal'] = estilo['canal_preferido']
        elif 'canal_preferente' in estilo:
            learning_style['canal'] = estilo['canal_preferente']
        
        # Get grouping preference
        if 'agrupamiento_optimo' in estilo:
            learning_style['agrupamiento'] = estilo['agrupamiento_optimo']
        elif 'tipo_agrupamiento' in estilo:
            learning_style['agrupamiento'] = estilo['tipo_agrupamiento']
        
        # Get movement needs
        if 'necesita_movimiento' in estilo:
            learning_style['movimiento'] = estilo['necesita_movimiento']
    
    # Get strengths and difficulties if available
    strengths = []
    difficulties = []
    if 'fortalezas_observadas' in profile['perfil_academico']:
        strengths = profile['perfil_academico']['fortalezas_observadas']
    if 'dificultades_observadas' in profile['perfil_academico']:
        difficulties = profile['perfil_academico']['dificultades_observadas']
    
    # Get motivators and triggers if available
    motivators = []
    triggers = []
    if 'perfil_conductual' in profile:
        if 'motivadores' in profile['perfil_conductual']:
            motivators = profile['perfil_conductual']['motivadores']
        if 'triggers' in profile['perfil_conductual']:
            triggers = profile['perfil_conductual']['triggers']
    
    return {
        'student_id': f"Estudiante_{idx+1}",
        'original_index': idx,
        'selection_reason': selection_reason,
        'academic_average': round(avg_academic, 1),
        'academic_scores': academic_scores,
        'cognitive_scores': cognitive_scores,
        'behavioral_scores': behavioral_scores,
        'learning_style': learning_style,
        'strengths': strengths,
        'difficulties': difficulties,
        'motivators': motivators,
        'triggers': triggers
    }

def main():
    """Main analysis function"""
    file_path = "/mnt/c/CAROLINA/ANFAIA/IA4EDU/data/processed/por_curso/perfiles_4_primaria.json"
    
    print("Loading 4th grade profiles...")
    data = load_profiles(file_path)
    profiles = data['perfiles']
    
    print(f"Total profiles loaded: {len(profiles)}")
    
    # Comprehensive analysis
    analysis_results = analyze_complete_dataset(profiles)
    
    # Select diverse students
    selected_students = select_diverse_students(profiles, 25)
    
    print(f"\nSelected {len(selected_students)} students:")
    print("\nDETAILED PROFILES OF SELECTED STUDENTS:")
    print("="*80)
    
    selection_summary = Counter()
    
    for i, (orig_idx, profile, reason) in enumerate(selected_students, 1):
        summary = generate_student_summary(orig_idx, profile, reason)
        selection_summary[reason] += 1
        
        print(f"\n{i}. {summary['student_id']} (Index: {orig_idx})")
        print(f"   Selection: {summary['selection_reason']}")
        print(f"   Academic avg: {summary['academic_average']}/5")
        
        if summary['academic_scores']:
            academic_str = " ".join([f"{k}:{v}" for k, v in summary['academic_scores'].items()])
            print(f"   Academic detail: {academic_str}")
        
        if summary['cognitive_scores']:
            cognitive_str = " ".join([f"{k}:{v}" for k, v in summary['cognitive_scores'].items()])
            print(f"   Cognitive: {cognitive_str}")
        
        if summary['behavioral_scores']:
            behavioral_str = " ".join([f"{k}:{v}" for k, v in summary['behavioral_scores'].items()])
            print(f"   Behavioral: {behavioral_str}")
        
        if summary['learning_style']:
            style_str = " ".join([f"{k}:{v}" for k, v in summary['learning_style'].items()])
            print(f"   Learning style: {style_str}")
        
        if summary['strengths']:
            print(f"   Strengths: {', '.join(summary['strengths'][:3])}")
        
        if summary['difficulties']:
            print(f"   Difficulties: {', '.join(summary['difficulties'])}")
        
        if summary['motivators']:
            print(f"   Motivators: {', '.join(summary['motivators'][:3])}")
        
        if summary['triggers']:
            print(f"   Triggers: {', '.join(summary['triggers'][:2])}")
    
    print("\n" + "="*80)
    print("SELECTION SUMMARY")
    print("="*80)
    print(f"Selection distribution: {dict(selection_summary)}")
    
    # Academic diversity in selection
    selected_profiles = [profile for _, profile, _ in selected_students]
    selected_academics = []
    for profile in selected_profiles:
        avg = calculate_academic_average(profile)
        selected_academics.append(avg)
    
    if selected_academics:
        print(f"Academic diversity in selection:")
        print(f"  Range: {min(selected_academics):.1f} - {max(selected_academics):.1f}")
        print(f"  Mean: {statistics.mean(selected_academics):.1f}")
    
    print(f"\nPilot classroom characteristics:")
    print(f"- Total students: {len(selected_students)}")
    print(f"- Double exceptionality: {selection_summary.get('doble_excepcionalidad', 0)}")
    print(f"- Low performers: {selection_summary.get('bajo_rendimiento', 0)}")
    print(f"- Mid performers: {selection_summary.get('medio_rendimiento', 0)}")
    print(f"- High performers: {selection_summary.get('alto_rendimiento', 0)}")
    
    return selected_students

if __name__ == "__main__":
    selected = main()