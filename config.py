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
        """Construye la configuración usando defaults reales y variables de entorno.

        Con ``slots=True`` los atributos de clase de la dataclass son descriptores,
        por lo que no deben utilizarse como valores predeterminados. Se crea una
        instancia base para recuperar los defaults efectivos.
        """
        defaults = cls()
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", defaults.ollama_url).strip(),
            ollama_model=os.getenv("OLLAMA_MODEL", defaults.ollama_model).strip(),
            images_dir=Path(os.getenv("IMAGES_DIR", str(defaults.images_dir))),
            output_dir=Path(os.getenv("OUTPUT_DIR", str(defaults.output_dir))),
            request_timeout_seconds=_positive_float(
                "OLLAMA_TIMEOUT_SECONDS", defaults.request_timeout_seconds
            ),
            plantuml_server=os.getenv(
                "PLANTUML_SERVER", defaults.plantuml_server
            ).strip(),
            plantuml_timeout_seconds=_positive_float(
                "PLANTUML_TIMEOUT_SECONDS", defaults.plantuml_timeout_seconds
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
