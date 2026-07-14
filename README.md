# LLaVA Local Architecture Analyzer

[![Tests](https://github.com/Prueba008/40-poc-llava-0001/actions/workflows/tests.yml/badge.svg)](https://github.com/Prueba008/40-poc-llava-0001/actions/workflows/tests.yml)

POC en Python para analizar imágenes de arquitectura de software mediante **Ollama + LLaVA**, generar documentación técnica en Markdown, extraer diagramas PlantUML, renderizarlos como PNG y producir un informe PDF.

El proyecto funciona sin OpenAI API, LangChain, ChromaDB, Gradio, Kubernetes ni Jupyter como dependencias de ejecución.

## Objetivos

- Ejecutar el análisis multimodal localmente con Ollama.
- Diferenciar información observada, inferencias y recomendaciones.
- Evitar la invención de componentes, cifras o relaciones no visibles.
- Procesar varias imágenes sin cancelar todo el lote por un error individual.
- Generar artefactos técnicos reproducibles: Markdown, PlantUML, PNG y PDF.
- Mantener un repositorio SQLite simple para administrar prompts reutilizables.

## Flujo de procesamiento

```text
Imágenes PNG/JPG/JPEG/GIF
          |
          v
analizar_arquitectura.py
          |
          +--> Ollama / LLaVA
          |
          +--> analisis/analisis_completo.md
          |
          +--> analisis/diagramas_puml/*.puml
                          |
                          v
                 renderizar_puml.py
                          |
                          +--> analisis/diagramas_png/*.png

analisis/analisis_completo.md
          |
          v
     generar_pdf.py
          |
          +--> documentacion/analisis_arquitectura.pdf
```

## Principios de diseño

- **LLM local:** el análisis de imágenes se envía a la instancia de Ollama configurada.
- **Dependencias mínimas:** el runtime utiliza únicamente `requests` y `reportlab`.
- **Configuración externa:** rutas, modelo, endpoints y timeouts se controlan mediante variables de entorno o argumentos CLI.
- **Errores diferenciados:** se distinguen timeouts, errores HTTP, problemas de conexión, JSON inválido e imágenes vacías o ilegibles.
- **Procesamiento parcial:** una imagen fallida se registra y las restantes continúan.
- **PlantUML validado:** cada bloque debe incluir `@startuml` y `@enduml`.
- **SQLite textual:** `base_vectorial.py` no implementa embeddings ni búsqueda vectorial; realiza persistencia y búsqueda textual con SQLite.

## Requisitos

- Python **3.13 o superior**.
- Ollama instalado y en ejecución.
- Modelo multimodal compatible, por defecto `llava`.
- Acceso al servidor PlantUML configurado únicamente cuando se desean generar PNG.

Instalar el modelo predeterminado:

```bash
ollama pull llava
```

Comprobar Ollama:

```bash
ollama list
```

El endpoint utilizado por defecto es:

```text
http://localhost:11434/api/generate
```

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/Prueba008/40-poc-llava-0001.git
cd 40-poc-llava-0001
```

Crear y activar un entorno virtual.

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux o macOS

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Inicio rápido

1. Copiar las imágenes que se analizarán dentro de `imagenes/`.
2. Confirmar que Ollama está ejecutándose.
3. Ejecutar el pipeline:

```bash
python analizar_arquitectura.py
python renderizar_puml.py
python generar_pdf.py
```

## Análisis de imágenes

Ejecución con valores predeterminados:

```bash
python analizar_arquitectura.py
```

Ejecución personalizada:

```bash
python analizar_arquitectura.py \
  --images-dir imagenes \
  --output-dir analisis \
  --model llava \
  --ollama-url http://localhost:11434/api/generate
```

Argumentos disponibles:

| Argumento | Descripción |
|---|---|
| `--images-dir` | Directorio con imágenes de entrada. |
| `--output-dir` | Directorio donde se generan Markdown y PlantUML. |
| `--model` | Modelo multimodal servido por Ollama. |
| `--ollama-url` | Endpoint completo de generación de Ollama. |

Formatos admitidos:

```text
.png  .jpg  .jpeg  .gif
```

Códigos de salida:

| Código | Significado |
|---:|---|
| `0` | Todas las imágenes fueron procesadas correctamente. |
| `1` | El lote finalizó con una o más imágenes fallidas. |
| `2` | No se encontraron imágenes compatibles. |

## Renderizado PlantUML

Renderizar los diagramas generados:

```bash
python renderizar_puml.py
```

Personalizar directorios:

```bash
python renderizar_puml.py \
  --input-dir analisis/diagramas_puml \
  --output-dir analisis/diagramas_png
```

El renderizador:

- valida la presencia de `@startuml` y `@enduml`;
- utiliza DEFLATE raw y el alfabeto oficial de PlantUML;
- reintenta errores de conexión y timeout;
- verifica que la respuesta tenga una cabecera PNG válida.

> **Privacidad:** el servidor predeterminado es `https://www.plantuml.com/plantuml/png/`. Al renderizar, el contenido textual del diagrama se envía a ese servidor. Para un procesamiento completamente local, configure `PLANTUML_SERVER` apuntando a una instancia local de PlantUML o no ejecute esta etapa.

Ejemplo con un servidor local:

```bash
export PLANTUML_SERVER=http://localhost:8080/png/
python renderizar_puml.py
```

En PowerShell:

```powershell
$env:PLANTUML_SERVER = "http://localhost:8080/png/"
python renderizar_puml.py
```

## Generación del PDF

Generar el documento con las rutas predeterminadas:

```bash
python generar_pdf.py
```

Personalizar entrada y salida:

```bash
python generar_pdf.py \
  --input analisis/analisis_completo.md \
  --output documentacion/analisis_arquitectura.pdf
```

La implementación actual transforma títulos y texto Markdown en un PDF A4. Los bloques de código se omiten y los PNG generados se conservan como artefactos separados; todavía no se insertan automáticamente dentro del PDF.

## Configuración

| Variable | Valor predeterminado | Descripción |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Endpoint completo de Ollama. |
| `OLLAMA_MODEL` | `llava` | Modelo multimodal. |
| `OLLAMA_TIMEOUT_SECONDS` | `180` | Timeout de análisis por imagen. |
| `IMAGES_DIR` | `imagenes` | Directorio de imágenes. |
| `OUTPUT_DIR` | `analisis` | Directorio principal de salida. |
| `PLANTUML_SERVER` | `https://www.plantuml.com/plantuml/png/` | Endpoint de renderizado PlantUML. |
| `PLANTUML_TIMEOUT_SECONDS` | `30` | Timeout del renderizado. |

Los timeouts deben ser valores numéricos mayores que cero.

Ejemplo Linux/macOS:

```bash
export OLLAMA_MODEL=llava
export OLLAMA_TIMEOUT_SECONDS=240
export IMAGES_DIR=imagenes
export OUTPUT_DIR=analisis
python analizar_arquitectura.py
```

Ejemplo Windows PowerShell:

```powershell
$env:OLLAMA_MODEL = "llava"
$env:OLLAMA_TIMEOUT_SECONDS = "240"
$env:IMAGES_DIR = "imagenes"
$env:OUTPUT_DIR = "analisis"
python analizar_arquitectura.py
```

## Artefactos generados

```text
analisis/
├── analisis_completo.md
├── diagramas_puml/
│   ├── imagen_diagrama_1.puml
│   └── ...
└── diagramas_png/
    ├── imagen_diagrama_1.png
    └── ...

documentacion/
└── analisis_arquitectura.pdf
```

Los artefactos generados están excluidos del control de versiones mediante `.gitignore`.

## Repositorio de prompts SQLite

`base_vectorial.py` conserva el nombre histórico por compatibilidad, pero implementa un repositorio relacional y textual.

Ejemplo:

```python
from base_vectorial import PromptRepository

repository = PromptRepository("data/prompts.db")

repository.upsert(
    "arquitectura-base",
    "Analiza la imagen separando observaciones, inferencias y riesgos.",
    metadata={"idioma": "es"},
    tags=["arquitectura", "llava"],
)

prompt = repository.get("arquitectura-base")
resultados = repository.search("riesgos", limit=10)

print(prompt)
print(resultados)
```

Operaciones disponibles:

- `upsert(...)`
- `get(prompt_id)`
- `search(query, limit)`
- `delete(prompt_id)`
- `count()`

La búsqueda utiliza coincidencias SQL `LIKE`; no es búsqueda semántica ni vectorial.

## Pruebas

Instalar dependencias de prueba:

```bash
pip install -r requirements-test.txt
```

Ejecutar la suite:

```bash
pytest -q
```

Ejecutar con cobertura:

```bash
pytest \
  --cov=analizar_arquitectura \
  --cov=base_vectorial \
  --cov=renderizar_puml \
  --cov=config \
  --cov-report=term-missing
```

Las pruebas utilizan mocks y archivos temporales. No requieren Ollama, el servidor PlantUML ni acceso a Internet.

## Integración continua

El workflow `.github/workflows/tests.yml` ejecuta la suite con Python 3.13 en:

- pushes a `master`;
- pushes a ramas `agent/**`;
- pull requests.

## Estructura del repositorio

```text
.
├── .github/workflows/tests.yml
├── analizar_arquitectura.py
├── base_vectorial.py
├── config.py
├── generar_pdf.py
├── renderizar_puml.py
├── requirements.txt
├── requirements-test.txt
├── imagenes/
├── tests/
│   ├── test_analizar_arquitectura.py
│   ├── test_base_vectorial.py
│   ├── test_config.py
│   ├── test_generar_pdf.py
│   └── test_renderizar_puml.py
└── README.md
```

## Manejo de errores

El analizador identifica y reporta, entre otros:

- imagen inexistente, vacía o ilegible;
- endpoint de Ollama inaccesible;
- timeout de inferencia;
- respuesta HTTP no exitosa;
- respuesta que no contiene JSON válido;
- ausencia del campo `response` en Ollama;
- bloques PlantUML incompletos o con Markdown anidado.

Cuando una imagen falla, el error se incorpora al resultado del lote y las siguientes imágenes continúan procesándose.

## Seguridad y privacidad

- Las imágenes se codifican en Base64 y se envían únicamente al endpoint configurado en `OLLAMA_URL`.
- Con la configuración predeterminada, Ollama se ejecuta en `localhost`.
- No se utilizan credenciales de OpenAI ni servicios LLM externos.
- SQLite se almacena en el sistema de archivos local.
- El renderizado PNG puede utilizar un servicio externo; revise `PLANTUML_SERVER` antes de procesar diagramas confidenciales.
- No almacene secretos, tokens ni información sensible dentro de prompts versionados.

## Limitaciones actuales

- El análisis depende de la capacidad y precisión del modelo multimodal seleccionado.
- LLaVA puede producir PlantUML sintácticamente incorrecto; el pipeline valida delimitadores básicos, no toda la gramática UML.
- La búsqueda de prompts es textual, no semántica.
- El PDF no incorpora automáticamente los PNG renderizados.
- El procesamiento es secuencial y no distribuye inferencias entre múltiples workers.

## Estado del proyecto

POC técnico orientado a ejecución local, experimentación y generación asistida de documentación de arquitectura. Antes de utilizarlo en producción se recomienda agregar autenticación del endpoint, límites de tamaño de imagen, trazabilidad estructurada, métricas, control de concurrencia y validación avanzada de PlantUML.
