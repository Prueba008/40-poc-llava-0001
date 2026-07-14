from pathlib import Path

import pytest

from config import AppConfig


_ENV_NAMES = (
    "OLLAMA_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
    "IMAGES_DIR",
    "OUTPUT_DIR",
    "PLANTUML_SERVER",
    "PLANTUML_TIMEOUT_SECONDS",
)


def test_from_env_uses_real_dataclass_defaults(monkeypatch):
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    config = AppConfig.from_env()

    assert config == AppConfig()
    assert config.images_dir == Path("imagenes")
    assert config.output_dir == Path("analisis")
    assert config.request_timeout_seconds == 180.0


def test_from_env_applies_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://ollama:11434/api/generate")
    monkeypatch.setenv("OLLAMA_MODEL", "llava:latest")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "240")
    monkeypatch.setenv("IMAGES_DIR", "entrada")
    monkeypatch.setenv("OUTPUT_DIR", "salida")
    monkeypatch.setenv("PLANTUML_SERVER", "http://plantuml:8080/png/")
    monkeypatch.setenv("PLANTUML_TIMEOUT_SECONDS", "45")

    config = AppConfig.from_env()

    assert config.ollama_url == "http://ollama:11434/api/generate"
    assert config.ollama_model == "llava:latest"
    assert config.request_timeout_seconds == 240.0
    assert config.images_dir == Path("entrada")
    assert config.output_dir == Path("salida")
    assert config.plantuml_server == "http://plantuml:8080/png/"
    assert config.plantuml_timeout_seconds == 45.0


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_from_env_rejects_invalid_timeout(monkeypatch, value):
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError):
        AppConfig.from_env()
