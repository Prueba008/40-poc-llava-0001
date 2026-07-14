from __future__ import annotations

import argparse
import base64
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import requests

from config import AppConfig

LOGGER = logging.getLogger(__name__)
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"}

BASE_PROMPT = """\
Actúa como ingeniero de software senior. Analiza únicamente la información visible
en la imagen. Separa claramente: (1) elementos observados, (2) inferencias y
(3) recomendaciones. Si la imagen no contiene información suficiente, indícalo y
no inventes componentes, cifras ni relaciones.

Entrega:
1. Resumen técnico.
2. Componentes y responsabilidades.
3. Integraciones y flujo de datos.
4. Seguridad, despliegue, escalabilidad y observabilidad.
5. Riesgos, supuestos y datos faltantes.
6. Diagramas PlantUML válidos, cada uno en un bloque ```plantuml```: componentes,
   secuencia, despliegue y flujo de datos. Cada bloque debe incluir @startuml y
   @enduml.
"""


class PipelineError(RuntimeError):
    """Error base del pipeline."""


class OllamaError(PipelineError):
    """Error de comunicación o contrato con Ollama."""


class InvalidImageError(PipelineError):
    """La imagen no puede procesarse."""


@dataclass(frozen=True, slots=True)
class OllamaResult:
    response: str
    model: str
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class ImageAnalysis:
    image_path: Path
    response: str
    generated_puml_files: tuple[Path, ...]
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class BatchResult:
    succeeded: tuple[ImageAnalysis, ...]
    failed: tuple[tuple[Path, str], ...]
    markdown_file: Path | None

    @property
    def partial(self) -> bool:
        return bool(self.succeeded and self.failed)


def discover_images(images_dir: str | Path) -> list[Path]:
    directory = Path(images_dir)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.casefold() in SUPPORTED_IMAGE_EXTENSIONS
    )


def encode_image(image_path: str | Path) -> str:
    path = Path(image_path)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise InvalidImageError(f"No se pudo leer la imagen {path}: {exc}") from exc
    if not content:
        raise InvalidImageError(f"La imagen {path} está vacía")
    return base64.b64encode(content).decode("ascii")


def build_ollama_payload(
    prompt: str,
    image_base64: str | None,
    model: str,
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("El prompt no puede estar vacío")
    if not model.strip():
        raise ValueError("El modelo no puede estar vacío")
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if image_base64:
        payload["images"] = [image_base64]
    return payload


def query_ollama(
    prompt: str,
    image_base64: str | None = None,
    *,
    ollama_url: str,
    model: str,
    timeout_seconds: float,
    session: requests.Session | None = None,
) -> OllamaResult:
    payload = build_ollama_payload(prompt, image_base64, model)
    client = session or requests.Session()
    owns_session = session is None
    started = perf_counter()
    try:
        try:
            response = client.post(ollama_url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
        except requests.Timeout as exc:
            raise OllamaError(f"Ollama excedió el timeout de {timeout_seconds}s") from exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "desconocido"
            raise OllamaError(f"Ollama respondió HTTP {status}") from exc
        except requests.RequestException as exc:
            raise OllamaError(f"No se pudo conectar con Ollama: {exc}") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise OllamaError("Ollama devolvió JSON inválido") from exc

        if not isinstance(body, dict):
            raise OllamaError("Ollama devolvió una estructura JSON inválida")

        text = body.get("response")
        if not isinstance(text, str) or not text.strip():
            raise OllamaError("Ollama no devolvió un campo 'response' válido")

        return OllamaResult(
            response=text.strip(),
            model=str(body.get("model") or model),
            elapsed_ms=round((perf_counter() - started) * 1000),
        )
    finally:
        if owns_session:
            client.close()


def extract_puml_blocks(text: str) -> list[str]:
    pattern = re.compile(
        r"```(?:puml|plantuml)\s*\r?\n(.*?)```",
        re.IGNORECASE | re.DOTALL,
    )
    return [match.strip() for match in pattern.findall(text)]


def validate_puml_block(block: str) -> None:
    normalized = block.casefold()
    start = normalized.find("@startuml")
    end = normalized.find("@enduml")
    if start < 0 or end < 0 or start >= end:
        raise PipelineError("Bloque PlantUML inválido: faltan @startuml/@enduml")
    if "```" in block:
        raise PipelineError("Bloque PlantUML inválido: contiene Markdown anidado")


def write_puml_blocks(
    image_path: str | Path,
    blocks: Iterable[str],
    output_dir: str | Path,
) -> list[Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for index, block in enumerate(blocks, start=1):
        validate_puml_block(block)
        path = target / f"{Path(image_path).stem}_diagrama_{index}.puml"
        path.write_text(block.strip() + "\n", encoding="utf-8")
        generated.append(path)
    return generated


def process_image(
    image_path: str | Path,
    config: AppConfig,
    *,
    prompt: str = BASE_PROMPT,
    session: requests.Session | None = None,
) -> ImageAnalysis:
    path = Path(image_path)
    encoded = encode_image(path)
    result = query_ollama(
        prompt,
        encoded,
        ollama_url=config.ollama_url,
        model=config.ollama_model,
        timeout_seconds=config.request_timeout_seconds,
        session=session,
    )
    blocks = extract_puml_blocks(result.response)
    generated = write_puml_blocks(
        path,
        blocks,
        config.output_dir / "diagramas_puml",
    )
    return ImageAnalysis(path, result.response, tuple(generated), result.elapsed_ms)


def write_analysis(output_path: str | Path, analyses: Iterable[ImageAnalysis]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sections = ["# Análisis de Arquitectura de Software\n"]
    for analysis in analyses:
        sections.append(f"## Análisis de {analysis.image_path.name}\n\n{analysis.response}\n")
    path.write_text("\n".join(sections), encoding="utf-8")
    return path


def run_pipeline(
    config: AppConfig,
    *,
    prompt: str = BASE_PROMPT,
    session: requests.Session | None = None,
) -> BatchResult:
    succeeded: list[ImageAnalysis] = []
    failed: list[tuple[Path, str]] = []

    for image in discover_images(config.images_dir):
        try:
            succeeded.append(process_image(image, config, prompt=prompt, session=session))
        except (PipelineError, OSError) as exc:
            LOGGER.error("Falló %s: %s", image, exc)
            failed.append((image, str(exc)))

    markdown = None
    if succeeded:
        markdown = write_analysis(config.output_dir / "analisis_completo.md", succeeded)
    return BatchResult(tuple(succeeded), tuple(failed), markdown)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analiza imágenes con Ollama/LLaVA")
    parser.add_argument("--images-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--ollama-url")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _build_parser().parse_args()
    base = AppConfig.from_env()
    config = AppConfig(
        ollama_url=args.ollama_url or base.ollama_url,
        ollama_model=args.model or base.ollama_model,
        images_dir=args.images_dir or base.images_dir,
        output_dir=args.output_dir or base.output_dir,
        request_timeout_seconds=base.request_timeout_seconds,
        plantuml_server=base.plantuml_server,
        plantuml_timeout_seconds=base.plantuml_timeout_seconds,
    )
    result = run_pipeline(config)
    if not result.succeeded and not result.failed:
        LOGGER.warning("No se encontraron imágenes en %s", config.images_dir)
        return 2
    if result.failed:
        LOGGER.warning("Ejecución con %d error(es)", len(result.failed))
        return 1
    LOGGER.info("Procesadas %d imagen(es)", len(result.succeeded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
