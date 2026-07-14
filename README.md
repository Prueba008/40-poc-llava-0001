# LLaVA Local Architecture Analyzer

POC local para analizar imágenes de arquitectura con **Ollama + LLaVA**, generar un informe Markdown, extraer diagramas PlantUML, renderizarlos y producir un PDF.

## Principios

- Sin OpenAI API ni servicios LLM externos.
- Dependencias de runtime mínimas.
- Configuración por variables de entorno o argumentos CLI.
- Errores HTTP, timeout, JSON inválido e imágenes defectuosas diferenciados.
- Procesamiento parcial: una imagen fallida no detiene el lote.
- SQLite se utiliza como repositorio textual de prompts; no se presenta como base vectorial.

## Requisitos

- Python 3.13+
- Ollama disponible en `http://localhost:11434`
- Modelo multimodal instalado:

```bash
ollama pull llava
```

## Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Ejecución

```bash
python analizar_arquitectura.py --images-dir imagenes --output-dir analisis
python renderizar_puml.py
python generar_pdf.py
```

Variables disponibles:

```text
OLLAMA_URL
OLLAMA_MODEL
OLLAMA_TIMEOUT_SECONDS
IMAGES_DIR
OUTPUT_DIR
PLANTUML_SERVER
PLANTUML_TIMEOUT_SECONDS
```

## Pruebas

```bash
pip install -r requirements-test.txt
pytest -q
```

Las pruebas unitarias no requieren Ollama ni acceso a Internet.

## Estructura

```text
analizar_arquitectura.py   pipeline multimodal
base_vectorial.py          repositorio SQLite de prompts
renderizar_puml.py         renderizado PlantUML
generar_pdf.py             generación de PDF
config.py                  configuración
tests/                     pruebas determinísticas
```
