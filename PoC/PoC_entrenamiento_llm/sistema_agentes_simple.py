#!/usr/bin/env python3
"""
Sistema de Agentes Simple con Human-in-the-Loop
Basado en patrones exitosos de actividades k_
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any

class AgenteSelector:
    """Selecciona plantilla k_ más adecuada"""
    
    def __init__(self):
        self.plantillas_k = {
            "matematicas": {
                "area_volumen": "k_feria_acertijos",
                "fracciones": "k_sonnet_supermercado", 
                "geometria": "k_feria_acertijos"
            },
            "ciencias": {
                "celula": "k_celula",
                "sistema_solar": "k_celula",
                "cuerpo_humano": "k_celula"
            },
            "lengua": {
                "narrativa": "k_piratas",
                "escritura": "k_piratas"
            }
        }
    
    def seleccionar_plantilla(self, materia: str, tema: str) -> str:
        """Selecciona plantilla k_ sin IA, mapeo directo"""
        if materia in self.plantillas_k:
            for tema_key in self.plantillas_k[materia]:
                if tema_key in tema.lower():
                    return self.plantillas_k[materia][tema_key]
            # Fallback a primera plantilla de la materia
            return list(self.plantillas_k[materia].values())[0]
        return "k_celula"  # Fallback general

class AgenteAsignador:
    """Asigna tareas específicas a cada estudiante"""
    
    def __init__(self):
        self.perfiles_estudiantes = {
            "001": {"nombre": "ALEX M.", "estilo": "reflexivo, visual"},
            "002": {"nombre": "MARÍA L.", "estilo": "reflexivo, auditivo"},
            "003": {"nombre": "ELENA R.", "estilo": "reflexivo, visual, TEA_nivel_1"},
            "004": {"nombre": "LUIS T.", "estilo": "impulsivo, kinestésico, TDAH_combinado"},
            "005": {"nombre": "ANA V.", "estilo": "reflexivo, auditivo, altas_capacidades"},
            "006": {"nombre": "SARA M.", "estilo": "equilibrado, auditivo"},
            "007": {"nombre": "EMMA K.", "estilo": "reflexivo, visual"},
            "008": {"nombre": "HUGO P.", "estilo": "equilibrado, visual"}
        }
    
    def asignar_tareas(self, plantilla: str, tema: str) -> Dict[str, str]:
        """Asigna tareas específicas basadas en plantilla k_"""
        if plantilla == "k_feria_acertijos":
            return self._tareas_matematicas_feria(tema)
        elif plantilla == "k_celula":
            return self._tareas_ciencias_celula(tema)
        elif plantilla == "k_piratas":
            return self._tareas_lengua_piratas(tema)
        else:
            return self._tareas_genericas(tema)
    
    def _tareas_matematicas_feria(self, tema: str) -> Dict[str, str]:
        return {
            "001": "Diseñar 3 figuras geométricas en papel cuadriculado y calcular su área",
            "002": "Explicar en voz alta el proceso de medición a otros equipos", 
            "003": "Usar plantilla visual para medir áreas de 2 objetos reales",
            "004": "Construir torre con bloques y contar su volumen (máx 6 bloques)",
            "005": "Resolver problemas de optimización: máxima área con 10 bloques",
            "006": "Registrar resultados de todos los equipos en tabla común",
            "007": "Crear cartel visual con ejemplos de área y volumen",
            "008": "Medir perímetros con cinta métrica y comparar resultados"
        }
    
    def _tareas_ciencias_celula(self, tema: str) -> Dict[str, str]:
        return {
            "001": "Buscar información sobre núcleo celular en libros disponibles",
            "002": "Explicar función de mitocondrias al grupo usando esquemas",
            "003": "Organizar materiales por colores y texturas para cada orgánulo", 
            "004": "Recortar y pegar elementos móviles del mural (ribosomas, etc)",
            "005": "Crear carteles informativos detallados de cada parte celular",
            "006": "Coordinar presentación final: quién explica qué parte",
            "007": "Dibujar contorno de célula y delimitar espacios en papel grande",
            "008": "Medir proporciones reales vs libro y documentar diferencias"
        }
    
    def _tareas_lengua_piratas(self, tema: str) -> Dict[str, str]:
        return {
            "001": "Crear mapa del tesoro con pistas escritas en rimas",
            "002": "Narrar historia de piratas con voces y sonidos", 
            "003": "Escribir diario de capitán con letra clara y dibujos",
            "004": "Representar escenas de aventura con movimiento y acción",
            "005": "Inventar acertijos complejos para encontrar el tesoro",
            "006": "Organizar representación teatral: vestuario y escenario",
            "007": "Ilustrar personajes y barcos con detalles visuales",
            "008": "Crear cronología visual de la aventura pirata"
        }
    
    def _tareas_genericas(self, tema: str) -> Dict[str, str]:
        return {
            "001": f"Investigar {tema} en libros y tomar notas visuales",
            "002": f"Presentar hallazgos sobre {tema} al grupo",
            "003": f"Organizar materiales necesarios para trabajar {tema}",
            "004": f"Crear elementos físicos relacionados con {tema}",
            "005": f"Desarrollar preguntas avanzadas sobre {tema}",
            "006": f"Coordinar trabajo en equipo para proyecto {tema}",
            "007": f"Diseñar representación visual de {tema}",
            "008": f"Documentar proceso y resultados del trabajo en {tema}"
        }

class AgenteAdaptador:
    """Adapta contenido según feedback del usuario"""
    
    def adaptar_tiempo(self, actividad: Dict, nuevo_tiempo: str) -> Dict:
        """Ajusta duración de actividad"""
        if "30" in nuevo_tiempo:
            actividad["duracion"] = "30 minutos"
            actividad["fases"] = ["Preparación (5 min)", "Ejecución (20 min)", "Cierre (5 min)"]
        elif "45" in nuevo_tiempo:
            actividad["duracion"] = "45 minutos" 
            actividad["fases"] = ["Preparación (10 min)", "Ejecución (25 min)", "Cierre (10 min)"]
        elif "90" in nuevo_tiempo:
            actividad["duracion"] = "90 minutos"
            actividad["fases"] = ["Preparación (15 min)", "Ejecución (60 min)", "Cierre (15 min)"]
        return actividad
    
    def adaptar_materiales(self, actividad: Dict, materiales_disponibles: str) -> Dict:
        """Sustituye materiales según disponibilidad"""
        materiales_base = actividad.get("materiales", [])
        
        if "sin bloques" in materiales_disponibles.lower():
            materiales_base = [m.replace("bloques", "dados de papel") for m in materiales_base]
            materiales_base = [m.replace("cubos", "cajas pequeñas") for m in materiales_base]
        
        if "solo papel" in materiales_disponibles.lower():
            actividad["materiales"] = ["Papel", "Lápices", "Reglas", "Tijeras", "Pegamento"]
        
        actividad["materiales"] = materiales_base
        return actividad
    
    def adaptar_dificultad(self, actividad: Dict, ajuste: str) -> Dict:
        """Ajusta nivel de dificultad"""
        if "más fácil" in ajuste.lower():
            # Simplificar tareas
            for key, tarea in actividad["tareas"].items():
                if "3 figuras" in tarea:
                    actividad["tareas"][key] = tarea.replace("3 figuras", "2 figuras")
                if "problemas complejos" in tarea:
                    actividad["tareas"][key] = tarea.replace("complejos", "simples")
        
        elif "más difícil" in ajuste.lower():
            # Complicar tareas
            for key, tarea in actividad["tareas"].items():
                if "2 objetos" in tarea:
                    actividad["tareas"][key] = tarea.replace("2 objetos", "4 objetos")
        
        return actividad

class AgenteValidador:
    """Valida coherencia básica de la actividad"""
    
    def validar(self, actividad: Dict) -> Dict:
        """Checklist básico sin pseudociencia"""
        errores = []
        
        # Verificar que todos tengan tarea
        if len(actividad.get("tareas", {})) != 8:
            errores.append("No todos los estudiantes tienen tarea asignada")
        
        # Verificar interdependencia
        tareas = list(actividad.get("tareas", {}).values())
        if not any("grupo" in t.lower() or "equipo" in t.lower() or "otros" in t.lower() for t in tareas):
            errores.append("Falta interdependencia entre estudiantes")
        
        # Verificar tiempo factible
        if actividad.get("duracion") == "30 minutos" and len(tareas) > 6:
            errores.append("Demasiadas tareas para el tiempo disponible")
        
        return {
            "valido": len(errores) == 0,
            "errores": errores,
            "puntuacion": max(0, 10 - len(errores) * 2)
        }

class SistemaAgentesSimple:
    """Sistema principal con human-in-the-loop"""
    
    def __init__(self):
        self.selector = AgenteSelector()
        self.asignador = AgenteAsignador()
        self.adaptador = AgenteAdaptador()
        self.validador = AgenteValidador()
    
    def generar_actividad(self, materia: str, tema: str) -> Dict:
        """Genera actividad base usando agentes"""
        
        # 1. Seleccionar plantilla
        plantilla = self.selector.seleccionar_plantilla(materia, tema)
        
        # 2. Asignar tareas específicas
        tareas = self.asignador.asignar_tareas(plantilla, tema)
        
        # 3. Crear actividad base
        actividad = {
            "id": f"simple_{materia}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "titulo": f"Actividad {materia.title()} - {tema.title()}",
            "materia": materia,
            "tema": tema,
            "plantilla_usada": plantilla,
            "duracion": "45 minutos",
            "materiales": self._materiales_por_plantilla(plantilla),
            "tareas": tareas,
            "fases": ["Preparación (10 min)", "Ejecución (25 min)", "Cierre (10 min)"]
        }
        
        # 4. Validar
        validacion = self.validador.validar(actividad)
        actividad["validacion"] = validacion
        
        return actividad
    
    def _materiales_por_plantilla(self, plantilla: str) -> List[str]:
        """Materiales según plantilla k_"""
        if plantilla == "k_feria_acertijos":
            return ["Papel cuadriculado", "Reglas", "Bloques", "Cinta métrica", "Lápices"]
        elif plantilla == "k_celula":
            return ["Papel grande", "Pinturas", "Materiales textura", "Libros ciencias", "Pegamento"]
        elif plantilla == "k_piratas":
            return ["Papel", "Colores", "Cartulinas", "Vestuario simple", "Mapas"]
        else:
            return ["Papel", "Lápices", "Materiales básicos"]
    
    def procesar_comando(self, actividad: Dict, comando: str) -> Dict:
        """Procesa comandos human-in-the-loop"""
        
        if comando.startswith("@selector"):
            # Cambiar tipo de actividad
            request = comando.replace("@selector", "").strip()
            if "kinestésico" in request:
                actividad["plantilla_usada"] = "k_feria_acertijos"
                actividad["tareas"] = self.asignador.asignar_tareas("k_feria_acertijos", actividad["tema"])
        
        elif comando.startswith("@asignador"):
            # Modificar asignaciones específicas
            request = comando.replace("@asignador", "").strip()
            if "Elena" in request and "visual" in request:
                actividad["tareas"]["003"] = "Usar plantilla visual con códigos de colores para organizar materiales"
            # Agregar más modificaciones según necesidad
        
        elif comando.startswith("@adaptador"):
            # Modificar contenido
            request = comando.replace("@adaptador", "").strip()
            if "tiempo" in request or "minutos" in request:
                actividad = self.adaptador.adaptar_tiempo(actividad, request)
            elif "materiales" in request:
                actividad = self.adaptador.adaptar_materiales(actividad, request)
            elif "dificultad" in request:
                actividad = self.adaptador.adaptar_dificultad(actividad, request)
        
        elif comando.startswith("@validador"):
            # Re-validar
            actividad["validacion"] = self.validador.validar(actividad)
        
        return actividad
    
    def mostrar_actividad(self, actividad: Dict):
        """Muestra actividad de forma clara"""
        print("\n" + "="*60)
        print(f"ACTIVIDAD: {actividad['titulo']}")
        print("="*60)
        print(f"Materia: {actividad['materia']} | Tema: {actividad['tema']}")
        print(f"Duración: {actividad['duracion']}")
        print(f"Plantilla usada: {actividad['plantilla_usada']}")
        
        print(f"\n📋 MATERIALES:")
        for material in actividad['materiales']:
            print(f"  • {material}")
        
        print(f"\n👥 TAREAS ESPECÍFICAS:")
        for student_id, tarea in actividad['tareas'].items():
            nombre = self.asignador.perfiles_estudiantes[student_id]["nombre"]
            print(f"  {student_id} {nombre}: {tarea}")
        
        print(f"\n⏱️ FASES:")
        for fase in actividad['fases']:
            print(f"  • {fase}")
        
        validacion = actividad.get('validacion', {})
        print(f"\n✅ VALIDACIÓN: {validacion.get('puntuacion', 0)}/10")
        if validacion.get('errores'):
            print("Errores detectados:")
            for error in validacion['errores']:
                print(f"  ⚠️ {error}")
    
    def human_in_the_loop(self, actividad: Dict) -> Dict:
        """Interfaz human-in-the-loop"""
        print("\n🔄 ¿Quieres modificar algo? Comandos disponibles:")
        print("@selector = cambiar tipo de actividad")
        print("@asignador = modificar asignaciones específicas")  
        print("@adaptador = ajustar materiales/tiempo/dificultad")
        print("@validador = revisar actividad")
        print("'ok' para continuar sin cambios")
        
        while True:
            comando = input("\n> ").strip()
            
            if comando.lower() == "ok":
                break
            elif comando.startswith("@"):
                actividad = self.procesar_comando(actividad, comando)
                self.mostrar_actividad(actividad)
                print("\n¿Algo más? (ok para terminar)")
            else:
                print("Comando no reconocido. Usa @selector, @asignador, @adaptador, @validador o 'ok'")
        
        return actividad

def main():
    """Función principal"""
    sistema = SistemaAgentesSimple()
    
    print("Sistema de Agentes Simple - Generador de Actividades")
    print("="*50)
    
    # Input del usuario
    materia = input("Materia (matematicas/ciencias/lengua): ").strip().lower()
    tema = input("Tema específico: ").strip().lower()
    
    # Generar actividad base
    print("\n🤖 Generando actividad...")
    actividad = sistema.generar_actividad(materia, tema)
    
    # Mostrar y permitir modificaciones
    sistema.mostrar_actividad(actividad)
    actividad_final = sistema.human_in_the_loop(actividad)
    
    # Guardar resultado
    filename = f"actividad_simple_{actividad['id']}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(actividad_final, indent=2, ensure_ascii=False))
    
    print(f"\n✅ Actividad guardada en: {filename}")
    print(f"Puntuación final: {actividad_final['validacion']['puntuacion']}/10")

if __name__ == "__main__":
    main()