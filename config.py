from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuración inmutable del pipeline."""

    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "llava"
    images_dir: Path = Path("imagenes")
    output_dir: Path = Path("analisis")
    request_timeout_seconds: float = 180.0
    plantuml_server: str = "https://www.plantuml.com/plantuml/png/"
    plantuml_timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", cls.ollama_url),
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
            images_dir=Path(os.getenv("IMAGES_DIR", str(cls.images_dir))),
            output_dir=Path(os.getenv("OUTPUT_DIR", str(cls.output_dir))),
            request_timeout_seconds=_positive_float(
                "OLLAMA_TIMEOUT_SECONDS", cls.request_timeout_seconds
            ),
            plantuml_server=os.getenv("PLANTUML_SERVER", cls.plantuml_server),
            plantuml_timeout_seconds=_positive_float(
                "PLANTUML_TIMEOUT_SECONDS", cls.plantuml_timeout_seconds
            ),
        )


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    if value <= 0:
        raise ValueError(f"{name} debe ser mayor que cero")
    return value
