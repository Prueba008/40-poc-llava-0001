# 40-poc-llava-0001

Prueba de concepto para analizar imágenes de arquitectura de software con Ollama y LLaVA, generar resúmenes técnicos y extraer diagramas PlantUML.

## Resumen del proyecto

Este repositorio demuestra un flujo de trabajo completo para:

- Analizar imágenes de arquitectura con un modelo multimodal de visión y lenguaje.
- Construir prompts orientados a componentes, seguridad, despliegue y escalabilidad.
- Extraer bloques PlantUML desde la respuesta generada.
- Guardar resultados en Markdown y archivos .puml.
- Preparar una base para pruebas funcionales, de contrato e integración.

## Estructura del repositorio

- [analizar_arquitectura.py](analizar_arquitectura.py): flujo principal de análisis y generación de artefactos.
- [base_vectorial.py](base_vectorial.py): gestión de prompts con SQLite.
- [renderizar_puml.py](renderizar_puml.py): renderizado de diagramas PlantUML a imágenes PNG.
- [generar_pdf.py](generar_pdf.py): generación de PDF a partir del análisis Markdown.
- [prompts](prompts): prompts y especificaciones de referencia.
- [analisis](analisis): salida generada por el pipeline.
- [imagenes](imagenes): imágenes de entrada para pruebas y demostraciones.

## Requisitos previos

- Python 3.13+
- Ollama ejecutándose en localhost:11434
- Modelo LLaVA instalado localmente
- Git

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
ollama pull llava
```

## Uso básico

### 1. Ejecutar el análisis

```bash
python analizar_arquitectura.py
```

Esto procesa las imágenes encontradas en [imagenes](imagenes) y genera:

- [analisis/analisis_completo.md](analisis/analisis_completo.md)
- [analisis/diagramas_puml](analisis/diagramas_puml)

### 2. Renderizar diagramas PlantUML

```bash
python renderizar_puml.py
```

### 3. Generar PDF

```bash
python generar_pdf.py
```

## Estrategia de pruebas

El proyecto está orientado a cubrir un pipeline funcional con pruebas deterministas, con mocks y de integración real contra Ollama.

### Pruebas rápidas

```bash
pytest -m "unit or functional" -q
```

### Cobertura

```bash
pytest -m "unit or functional" --cov=analizar_arquitectura --cov=base_vectorial --cov-report=term-missing --cov-report=html
```

### Integración real

```bash
pytest -m "integration and slow" -v
```

## Calidad esperada

La suite de pruebas busca verificar que el flujo:

- descubra imágenes correctamente,
- codifique archivos a Base64,
- construya el payload correcto para Ollama,
- extraiga bloques PlantUML válidos,
- genere Markdown y archivos .puml,
- detecte alucinaciones y abstenciones cuando la imagen no aporta suficiente información.

## Solución de problemas

### Ollama no responde

Asegúrese de que el servicio esté ejecutándose:

```bash
ollama serve
```

### Renderizado de PlantUML

Verifique la conectividad con el servidor externo o configure una alternativa local si es necesario.

### Base de datos vectorial

Si aparecen problemas de acceso, asegúrese de que no haya otros procesos usando el mismo archivo de base de datos.

## Notas importantes

- El flujo actual procesa archivos PNG, JPG, JPEG y GIF.
- Si Ollama no está disponible o el modelo no responde correctamente, la ejecución debe reportar el fallo de forma explícita.
- Para entornos locales, es recomendable mantener el modelo y el servicio Ollama en buen estado antes de ejecutar inferencia multimodal.
