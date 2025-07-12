import json
from datetime import datetime

# Cargar archivos uno por uno
with open('data/processed/perfiles_adhd_primaria.json', 'r', encoding='utf-8') as f:
    adhd_data = json.load(f)
    
with open('data/processed/perfiles_ayez_primaria.json', 'r', encoding='utf-8') as f:
    ayez_data = json.load(f)
    
with open('data/processed/perfiles_altas_capacidades_osf.json', 'r', encoding='utf-8') as f:
    ac_data = json.load(f)
    
with open('data/processed/perfiles_doble_excepcionalidad_2e.json', 'r', encoding='utf-8') as f:
    e2_data = json.load(f)

# Extraer perfiles (pueden ser directamente listas o tener clave 'perfiles')
adhd_perfiles = adhd_data if isinstance(adhd_data, list) else adhd_data.get('perfiles', [])
ayez_perfiles = ayez_data if isinstance(ayez_data, list) else ayez_data.get('perfiles', [])
ac_perfiles = ac_data if isinstance(ac_data, list) else ac_data.get('perfiles', [])
e2_perfiles = e2_data if isinstance(e2_data, list) else e2_data.get('perfiles', [])

# Unir todos
todos_perfiles = adhd_perfiles + ayez_perfiles + ac_perfiles + e2_perfiles

# Crear dataset final
dataset_final = {
    "metadata": {
        "proyecto": "ProyectIA", 
        "total_perfiles": len(todos_perfiles),
        "fecha_unificacion": datetime.now().isoformat()
    },
    "perfiles": todos_perfiles
}

# Guardar
with open('data/processed/dataset_unificado_proyectia.json', 'w', encoding='utf-8') as f:
    json.dump(dataset_final, f, ensure_ascii=False, indent=2)

# Verificar
with open('data/processed/dataset_unificado_proyectia.json', 'r', encoding='utf-8') as f:
    verificacion = json.load(f)

print(f"GUARDADO: {len(verificacion['perfiles'])} perfiles")