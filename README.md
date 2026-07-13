# 40-poc-llava-0001

Prueba de concepto para analizar imágenes de arquitectura de software utilizando LLaVA y gestionar prompts con una base de datos vectorial.

## Resumen del Proyecto

Este proyecto demuestra un flujo de trabajo completo para:
- Analizar imágenes de arquitectura de software usando LLaVA (modelo visión-lenguaje)
- Extraer componentes arquitectónicos y generar diagramas PlantUML
- Gestionar prompts en una base de datos vectorial basada en SQLite
- Renderizar diagramas PlantUML a imágenes PNG
- Generar documentación PDF a partir del análisis en markdown

## Estructura del Proyecto

```
40-poc-llava-0001/
├── base_vectorial.py          # Base de datos SQLite para gestión de prompts
├── generar_pdf.py             # Generación de PDF desde markdown
├── renderizar_puml.py         # Renderizado de PlantUML a PNG
├── analizar_arquitectura.py   # Script de análisis de arquitectura
├── requirements.txt           # Dependencias de Python
├── analisis/
│   ├── analisis_completo.md   # Análisis completo de arquitectura
│   ├── diagramas_puml/        # Fuentes de diagramas PlantUML
│   └── diagramas_png/         # Diagramas PNG renderizados
├── prompts/
│   ├── prompts_spec.md        # Especificaciones de prompts
│   └── prompt-ollama-llava.txt
├── documentacion/
│   └── poc-ollama-llava-0001.docx
└── prueba/
    └── analisis_completo.md   # Salida de análisis de prueba
```

## Instalación

### Requisitos Previos

- Python 3.13+
- Ollama (para el modelo LLaVA)
- Git

### Configuración

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd 40-poc-llava-0001
```

2. Crear entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Descargar el modelo LLaVA con Ollama:
```bash
ollama pull llava
```

## Uso

### 1. Gestión de Base de Datos Vectorial

El módulo `base_vectorial.py` proporciona una base de datos SQLite para almacenar y gestionar prompts.

#### Inicializar la Base de Datos
```python
from base_vectorial import BaseVectorial

base = BaseVectorial()
```

#### Agregar un Prompt
```python
base.add_prompt(
    prompt_id="prompt_001",
    text="Analizar arquitectura de software para plataformas con bases de datos masivas",
    metadata={
        "categoria": "arquitectura",
        "prioridad": "alta"
    },
    tags=["software", "database", "architecture"]
)
```

#### Buscar Prompts
```python
results = base.search_prompts("arquitectura", n_results=5)
for result in results:
    print(f"ID: {result['id']}")
    print(f"Texto: {result['text']}")
    print(f"Metadatos: {result['metadata']}")
```

#### Obtener un Prompt Específico
```python
prompt = base.get_prompt("prompt_001")
if prompt:
    print(f"Tags: {prompt['tags']}")
```

#### Actualizar un Prompt
```python
base.update_prompt(
    prompt_id="prompt_001",
    text="Texto actualizado",
    tags=["nuevos", "tags"]
)
```

#### Eliminar un Prompt
```python
base.delete_prompt("prompt_001")
```

#### Listar Todos los Prompts
```python
prompts = base.list_all_prompts(limit=10)
print(f"Total: {base.count_prompts()}")
```

### 2. Renderizar Diagramas PlantUML

El script `renderizar_puml.py` convierte archivos PlantUML a imágenes PNG utilizando el servidor PlantUML.

```bash
python renderizar_puml.py
```

Este script:
- Lee todos los archivos `.puml` de `./analisis/diagramas_puml/`
- Los renderiza a PNG usando el servidor PlantUML
- Guarda la salida en `./analisis/diagramas_png/`

### 3. Generar Documentación PDF

El script `generar_pdf.py` crea un documento PDF a partir del análisis en markdown y los diagramas.

```bash
python generar_pdf.py
```

Este script:
- Lee `./analisis/analisis_completo.md`
- Parsea las secciones markdown
- Incluye los diagramas PNG correspondientes
- Genera el PDF en `./documentacion/arquitectura_chatgpt_mastery.pdf`

### 4. Análisis de Arquitectura

Utilice el notebook de Jupyter `40-poc-llava-0001.ipynb` para:
- Analizar imágenes de arquitectura usando LLaVA
- Extraer componentes arquitectónicos
- Generar diagramas PlantUML
- Almacenar resultados en la base de datos vectorial

## Esquema de la Base de Datos

La base de datos SQLite (`./data/prompts.db`) contiene tres tablas:

### prompts
- `id` (TEXT, PRIMARY KEY): Identificador único del prompt
- `text` (TEXT): Contenido del texto del prompt
- `metadata` (TEXT): Metadatos en JSON (categoría, prioridad, etc.)
- `created_at` (TIMESTAMP): Timestamp de creación
- `updated_at` (TIMESTAMP): Timestamp de última actualización

### tags
- `id` (INTEGER, PRIMARY KEY): ID del tag con auto-incremento
- `name` (TEXT, UNIQUE): Nombre del tag

### prompt_tags
- `prompt_id` (TEXT, FOREIGN KEY): Referencia a prompts
- `tag_id` (INTEGER, FOREIGN KEY): Referencia a tags
- PRIMARY KEY (prompt_id, tag_id)

## Configuración

### Ruta de la Base de Datos
Por defecto: `./data/prompts.db`

Se puede personalizar:
```python
base = BaseVectorial(db_path="./ruta/personalizada/prompts.db")
```

### Servidor PlantUML
Por defecto: `http://www.plantuml.com/plantuml/png/`

Se puede modificar en `renderizar_puml.py`:
```python
PLANTUML_SERVER = "tu-servidor-personalizado"
```

## Dependencias

Las dependencias clave incluyen:
- `docling`: Procesamiento de documentos
- `langchain-ollama`: Integración de LangChain con Ollama
- `llava`: Modelo visión-lenguaje
- `chromadb`: Base de datos vectorial (alternativa a SQLite)
- `reportlab`: Generación de PDF
- `requests`: Peticiones HTTP para renderizado PlantUML

Consulte `requirements.txt` para la lista completa.

## Flujo de Trabajo de Análisis de Arquitectura

1. **Entrada de Imagen**: Proporcionar una imagen de diagrama de arquitectura
2. **Análisis LLaVA**: Usar LLaVA para analizar la imagen y extraer componentes
3. **Generación PlantUML**: Generar diagramas PlantUML para cada componente
4. **Renderizado de Diagramas**: Convertir PlantUML a imágenes PNG
5. **Almacenamiento en Base de Datos**: Guardar prompts y metadatos en la base de datos vectorial
6. **Generación de PDF**: Crear documentación PDF completa

## Salida de Ejemplo

El proyecto genera:
- **Diagramas PlantUML**: Diagramas de componentes para cada elemento arquitectónico
- **Imágenes PNG**: Diagramas renderizados para documentación
- **Reporte PDF**: Análisis completo de arquitectura con diagramas
- **Registros de Base de Datos**: Almacenamiento de prompts buscables con tags y metadatos

## Desarrollo

### Ejecutar Pruebas
```bash
python base_vectorial.py  # Ejecuta el ejemplo de uso
```

### Agregar Nuevos Prompts
Edite los prompts en `prompts/prompts_spec.md` y use la base de datos vectorial para almacenarlos.

## Solución de Problemas

### Problemas de Conexión con Ollama
Asegúrese de que Ollama esté ejecutándose:
```bash
ollama serve
```

### Fallos en Renderizado PlantUML
Verifique la conexión a internet (usa servidor PlantUML externo) o configure un servidor local.

### Problemas de Bloqueo de Base de Datos
Asegúrese de que solo un proceso acceda a la base de datos a la vez, o implemente un pool de conexiones adecuado.

## Licencia

[Especifique su licencia aquí]

## Contribuyendo

[Especifique las directrices de contribución aquí]
