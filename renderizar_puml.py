#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para renderizar todos los archivos PlantUML (.puml) a PNG.
"""

import os
import glob
from pathlib import Path
import requests
import zlib
import base64

# ================= CONFIGURACIÓN =================
PUML_DIR = "./analisis/diagramas_puml"
OUTPUT_DIR = "./analisis/diagramas_png"
PLANTUML_SERVER = "http://www.plantuml.com/plantuml/png/"
# =================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

def encode_puml(puml_content: str) -> str:
    """Codifica contenido PlantUML usando el algoritmo de PlantUML."""
    # Comprimir con zlib
    zlibbed = zlib.compress(puml_content.encode('utf-8'))
    # Codificar en base64
    return base64.b64encode(zlibbed).decode('utf-8')

def renderizar_puml_a_png(puml_path: str, output_dir: str) -> bool:
    """
    Renderiza un archivo PlantUML a PNG.
    
    Args:
        puml_path: Ruta del archivo .puml
        output_dir: Directorio de salida para el PNG
        
    Returns:
        True si se renderizó correctamente
    """
    try:
        # Leer archivo PlantUML
        with open(puml_path, 'r', encoding='utf-8') as f:
            puml_content = f.read()
        
        # Generar nombre de salida
        base_name = Path(puml_path).stem
        output_path = os.path.join(output_dir, f"{base_name}.png")
        
        # Codificar y hacer request al servidor
        encoded = encode_puml(puml_content)
        url = f"{PLANTUML_SERVER}{encoded}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Guardar PNG
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Renderizado: {base_name}.png")
        return True
        
    except Exception as e:
        print(f"❌ Error al renderizar {puml_path}: {e}")
        return False

def main():
    """Renderiza todos los archivos .puml a PNG."""
    # Buscar archivos .puml
    puml_files = glob.glob(os.path.join(PUML_DIR, "*.puml"))
    
    if not puml_files:
        print(f"No se encontraron archivos .puml en {PUML_DIR}")
        return
    
    print(f"Encontrados {len(puml_files)} archivos PlantUML")
    print(f"Directorio de salida: {OUTPUT_DIR}\n")
    
    # Renderizar cada archivo
    exitosos = 0
    for puml_file in puml_files:
        if renderizar_puml_a_png(puml_file, OUTPUT_DIR):
            exitosos += 1
    
    print(f"\n✨ Completado: {exitosos}/{len(puml_files)} archivos renderizados")
    print(f"📁 PNGs guardados en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
