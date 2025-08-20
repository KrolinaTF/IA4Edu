"""
Profile Manager Simplificado - Gestión de perfiles de estudiantes para MVP.
Solo las funciones esenciales sin complejidad innecesaria.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SimplifiedABP.ProfileManager")

class ProfileManager:
    """
    Gestor simplificado de perfiles de estudiantes.
    Solo carga y proporciona información básica de neurotipos y adaptaciones.
    """
    
    def __init__(self):
        """Inicializa el gestor de perfiles"""
        self.profiles = self._load_profiles()
        self.neurotipo_map = self._create_neurotipo_mapping()
        
        logger.info(f"👥 ProfileManager inicializado con {len(self.profiles)} estudiantes")
    
    def _load_profiles(self) -> List[Dict[str, Any]]:
        """
        Carga perfiles de estudiantes desde JSON
        
        Returns:
            Lista de perfiles de estudiantes
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)
            perfiles_path = os.path.join(base_dir, "data", "perfiles_4_primaria.json")
            
            with open(perfiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            profiles = data.get('estudiantes', [])
            logger.info(f"✅ Cargados {len(profiles)} perfiles")
            
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Error cargando perfiles: {e}")
            return self._create_default_profiles()
    
    def _create_default_profiles(self) -> List[Dict[str, Any]]:
        """
        Crea perfiles por defecto si no se pueden cargar
        
        Returns:
            Lista de perfiles por defecto
        """
        return [
            {
                "id": "001", "nombre": "Alex M.", 
                "diagnostico_formal": "ninguno", 
                "fortalezas": ["matemáticas", "análisis"]
            },
            {
                "id": "002", "nombre": "María L.", 
                "diagnostico_formal": "ninguno", 
                "fortalezas": ["comunicación", "liderazgo"]
            },
            {
                "id": "003", "nombre": "Elena R.", 
                "diagnostico_formal": "TEA_nivel_1", 
                "fortalezas": ["precisión", "matemáticas"],
                "necesidades_especiales": ["apoyo visual", "estructura"]
            },
            {
                "id": "004", "nombre": "Luis T.", 
                "diagnostico_formal": "TDAH_combinado", 
                "fortalezas": ["creatividad", "energía"],
                "necesidades_especiales": ["movimiento", "descansos"]
            },
            {
                "id": "005", "nombre": "Ana V.", 
                "diagnostico_formal": "altas_capacidades", 
                "fortalezas": ["investigación", "pensamiento crítico"],
                "necesidades_especiales": ["desafíos", "autonomía"]
            },
            {
                "id": "006", "nombre": "Sara M.", 
                "diagnostico_formal": "ninguno", 
                "fortalezas": ["colaboración", "organización"]
            },
            {
                "id": "007", "nombre": "Emma K.", 
                "diagnostico_formal": "ninguno", 
                "fortalezas": ["creatividad", "comunicación"]
            },
            {
                "id": "008", "nombre": "Hugo P.", 
                "diagnostico_formal": "ninguno", 
                "fortalezas": ["experimentación", "curiosidad"]
            }
        ]
    
    def _create_neurotipo_mapping(self) -> Dict[str, List[str]]:
        """
        Crea mapeo de neurotipos presentes en el aula
        
        Returns:
            Diccionario con neurotipos y estudiantes
        """
        mapping = {
            'típico': [],
            'TEA': [],
            'TDAH': [],
            'altas_capacidades': [],
            'otros': []
        }
        
        for profile in self.profiles:
            nombre = profile.get('nombre', 'Sin nombre')
            diagnostico = profile.get('diagnostico_formal', 'ninguno')
            
            if 'TEA' in diagnostico:
                mapping['TEA'].append(nombre)
            elif 'TDAH' in diagnostico:
                mapping['TDAH'].append(nombre)
            elif 'altas_capacidades' in diagnostico:
                mapping['altas_capacidades'].append(nombre)
            elif diagnostico == 'ninguno':
                mapping['típico'].append(nombre)
            else:
                mapping['otros'].append(nombre)
        
        return mapping
    
    def get_students_summary(self) -> str:
        """
        Obtiene resumen simple de estudiantes para prompts
        
        Returns:
            String con resumen de estudiantes
        """
        summary_parts = []
        
        for neurotipo, estudiantes in self.neurotipo_map.items():
            if estudiantes and neurotipo != 'otros':
                if neurotipo == 'típico':
                    summary_parts.append(f"{', '.join(estudiantes)} (desarrollo típico)")
                else:
                    summary_parts.append(f"{', '.join(estudiantes)} ({neurotipo})")
        
        return "; ".join(summary_parts)
    
    def get_adaptations_needed(self) -> Dict[str, List[str]]:
        """
        Obtiene adaptaciones necesarias para el aula
        
        Returns:
            Diccionario con adaptaciones por neurotipo
        """
        adaptaciones = {}
        
        if self.neurotipo_map['TEA']:
            adaptaciones['TEA'] = [
                "Proporcionar estructura clara y predecible",
                "Usar apoyos visuales (pictogramas, esquemas)",
                "Dar tiempo extra para transiciones",
                "Crear ambiente menos estimulante"
            ]
        
        if self.neurotipo_map['TDAH']:
            adaptaciones['TDAH'] = [
                "Permitir movimiento durante actividades",
                "Fragmentar tareas en pasos pequeños",
                "Ofrecer descansos frecuentes",
                "Usar elementos manipulativos"
            ]
        
        if self.neurotipo_map['altas_capacidades']:
            adaptaciones['altas_capacidades'] = [
                "Proporcionar retos adicionales",
                "Fomentar rol de mentoría",
                "Permitir investigación autónoma",
                "Ofrecer proyectos de mayor complejidad"
            ]
        
        return adaptaciones
    
    def create_optimal_pairs(self) -> List[tuple]:
        """
        Crea parejas optimizadas considerando neurotipos
        
        Returns:
            Lista de tuplas con parejas optimizadas
        """
        parejas = []
        estudiantes_disponibles = self.profiles.copy()
        
        # Estrategia simple: emparejar estudiantes con necesidades especiales con típicos
        especiales = [e for e in estudiantes_disponibles 
                     if e.get('diagnostico_formal', 'ninguno') != 'ninguno']
        tipicos = [e for e in estudiantes_disponibles 
                  if e.get('diagnostico_formal', 'ninguno') == 'ninguno']
        
        # Emparejar cada estudiante con necesidades especiales con uno típico
        for especial in especiales:
            if tipicos:
                tipico = tipicos.pop(0)
                parejas.append((especial['nombre'], tipico['nombre']))
                estudiantes_disponibles.remove(especial)
                estudiantes_disponibles.remove(tipico)
        
        # Emparejar los estudiantes restantes
        while len(estudiantes_disponibles) >= 2:
            est1 = estudiantes_disponibles.pop(0)
            est2 = estudiantes_disponibles.pop(0)
            parejas.append((est1['nombre'], est2['nombre']))
        
        # Si queda uno solo, añadirlo a la última pareja (grupo de 3)
        if estudiantes_disponibles:
            ultimo = estudiantes_disponibles[0]
            if parejas:
                ultima_pareja = parejas[-1]
                parejas[-1] = (ultima_pareja[0], ultima_pareja[1], ultimo['nombre'])
        
        logger.info(f"👥 Creadas {len(parejas)} parejas optimizadas")
        return parejas
    
    def get_student_by_name(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene perfil de estudiante por nombre
        
        Args:
            nombre: Nombre del estudiante
            
        Returns:
            Perfil del estudiante o None
        """
        for profile in self.profiles:
            if profile.get('nombre', '').lower() == nombre.lower():
                return profile
        return None
    
    def get_neurotipo_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de neurotipos en el aula
        
        Returns:
            Diccionario con conteos por neurotipo
        """
        stats = {}
        for neurotipo, estudiantes in self.neurotipo_map.items():
            stats[neurotipo] = len(estudiantes)
        
        return stats
    
    def get_adaptations_summary(self) -> str:
        """
        Obtiene resumen de adaptaciones para incluir en prompts
        
        Returns:
            String con resumen de adaptaciones necesarias
        """
        adaptaciones = self.get_adaptations_needed()
        
        if not adaptaciones:
            return "No se requieren adaptaciones especiales para este grupo."
        
        summary_parts = []
        
        for neurotipo, adaptacion_list in adaptaciones.items():
            estudiantes = self.neurotipo_map.get(neurotipo, [])
            if estudiantes:
                summary_parts.append(
                    f"Para {neurotipo} ({', '.join(estudiantes)}): {'; '.join(adaptacion_list[:2])}"
                )
        
        return ". ".join(summary_parts)
    
    def get_all_student_names(self) -> List[str]:
        """
        Obtiene lista de todos los nombres de estudiantes
        
        Returns:
            Lista de nombres
        """
        return [profile.get('nombre', f'Estudiante {profile.get("id", "")}') 
                for profile in self.profiles]