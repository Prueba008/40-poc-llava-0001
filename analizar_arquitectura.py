# %%
# Ejecuta esto en una celda
# %pip freeze > requirements.txt
# %pip install docling langchain-ollama llava chromadb tqdm langchain-text-splitters
# %ollama pull llava
# %%
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para analizar imágenes de arquitectura de software usando LLaVA (Ollama)
y generar descripciones detalladas + diagramas PlantUML.
Soporta PNG, JPG, JPEG y GIF (primer fotograma en caso de animación).
"""

import os
import base64
import re
import requests
import glob
from pathlib import Path

# ================= CONFIGURACIÓN =================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llava"                     # Asegurar que está descargado: ollama pull llava
IMAGES_DIR = "./imagenes"            # Directorio con las imágenes a analizar
OUTPUT_DIR = "./analisis"            # Directorio donde se guardarán los resultados
# =================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)
puml_dir = os.path.join(OUTPUT_DIR, "diagramas_puml")
os.makedirs(puml_dir, exist_ok=True)

def encode_image(image_path):
    """Convierte una imagen a base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def query_ollama(prompt, image_base64=None):
    """Envía una consulta a Ollama (modelo multimodal) y devuelve la respuesta."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    if image_base64:
        payload["images"] = [image_base64]

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"Error en consulta a Ollama: {e}")
        return ""

def extract_puml_blocks(text):
    """Extrae bloques de código PlantUML (```puml ... ``` o ```plantuml ... ```)."""
    pattern = r"```(?:puml|plantuml)\n(.*?)```"
    return re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

# Prompt detallado (en español) que pide el análisis completo
BASE_PROMPT = """
Extraer de la imagen adjunta como ingeniero de software Analizar la imagen adjunta para deducir y diseñar la arquitectura técnica necesaria para soportar el producto digital que se promociona (un curso/plataforma con bases de datos masivas).

Instrucciones de formato:

Proporciona una explicación técnica para cada punto.

Genera código PlantUML válido encerrado en bloques de código independientes para cada diagrama.

No utilices texto genérico; basa tus deducciones en los números y activos específicos de la imagen (ej. "38,000+ AI Tools", "40,000+ Prompts").

Análisis Requerido:

Componentes y Servicios: Desglosa la arquitectura necesaria (API Gateways, Microservicios de Búsqueda, CMS para videos, Motores de Recomendación).

Stack Tecnológico: Deduce tecnologías específicas (Bases de datos Vectoriales para prompts, NoSQL para el catálogo, CDNs para el contenido de video).

Patrones de Diseño: Justifica el uso de Microservicios, CQRS (para separar lectura de catálogos y escritura de usuarios) y Event-Driven.

Seguridad y Despliegue: Define estrategias de OAuth2/JWT para el acceso vía QR y una infraestructura en Kubernetes sobre AWS/GCP.

Escalabilidad: Explica cómo manejarías picos de tráfico masivos tras el escaneo del código QR.

Diagramas PlantUML solicitados:

A. Diagrama de Componentes: Detallando la lógica interna.

B. Diagrama de Secuencia: Flujo desde el escaneo del QR hasta la entrega del prompt/recurso.

C. Diagrama de Despliegue: Nodos, contenedores y balanceadores de carga.

D. Diagrama de Flujo de Datos: Movimiento de la información desde las DBs hacia el usuario final.
"""

def main():
    # Buscar imágenes en el directorio (incluyendo GIF)
    image_files = (glob.glob(os.path.join(IMAGES_DIR, "*.png")) +
                   glob.glob(os.path.join(IMAGES_DIR, "*.jpg")) +
                   glob.glob(os.path.join(IMAGES_DIR, "*.jpeg")) +
                   glob.glob(os.path.join(IMAGES_DIR, "*.gif")))

    if not image_files:
        print(f"No se encontraron imágenes en {IMAGES_DIR}")
        return

    all_analyses = []

    for img_path in image_files:
        print(f"Procesando {img_path}...")
        if img_path.lower().endswith('.gif'):
            print("  Nota: Los GIF animados se procesarán como imagen estática (primer fotograma).")
        img_b64 = encode_image(img_path)
        response = query_ollama(BASE_PROMPT, img_b64)

        if response:
            # Agregar al análisis global
            all_analyses.append(f"## Análisis de {os.path.basename(img_path)}\n\n{response}\n\n")

            # Extraer y guardar diagramas PUML individuales
            puml_blocks = extract_puml_blocks(response)
            for i, block in enumerate(puml_blocks):
                base_name = Path(img_path).stem
                filename = f"{base_name}_diagrama_{i+1}.puml"
                filepath = os.path.join(puml_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(block.strip())
                print(f"  Guardado diagrama: {filename}")
        else:
            print(f"  No se obtuvo respuesta para {img_path}")

    # Guardar el análisis completo en un archivo Markdown
    output_md = os.path.join(OUTPUT_DIR, "analisis_completo.md")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# Análisis de Arquitectura de Software\n\n")
        f.writelines(all_analyses)

    print(f"\n✅ Análisis completado. Revisa {output_md}")
    print(f"📁 Diagramas PUML guardados en {puml_dir}")

if __name__ == "__main__":
    main()
# %%
