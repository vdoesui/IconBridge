import json
import sys

def merge_duplicates(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            # Si ambos son listas, las unimos
            if isinstance(d[k], list) and isinstance(v, list):
                d[k].extend(v)
            else:
                # Si no son listas, convertimos en lista o sobreescribimos (según prefieras)
                d[k] = [d[k], v] if not isinstance(d[k], list) else d[k] + [v]
        else:
            d[k] = v
    return d

# Lee tu archivo (cambia 'input.json' por tu archivo real)
input_filename = 'mappings.json' 
output_filename = 'mappings.json'

try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        # Aquí ocurre la magia: interceptamos la carga
        data = json.load(f, object_pairs_hook=merge_duplicates)
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    print(f"✅ ¡Éxito! Archivo guardado como {output_filename}")
except Exception as e:
    print(f"❌ Error: {e}")