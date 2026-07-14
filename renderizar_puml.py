from __future__ import annotations

import argparse
import logging
import time
import zlib
from pathlib import Path

import requests

from config import AppConfig

LOGGER = logging.getLogger(__name__)


def encode_puml(source: str) -> str:
    """Codifica PlantUML con DEFLATE raw y el alfabeto oficial."""
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(source.encode("utf-8")) + compressor.flush()
    return _encode64(compressed)


def _encode64(data: bytes) -> str:
    result: list[str] = []
    index = 0
    while index < len(data):
        b1 = data[index]
        b2 = data[index + 1] if index + 1 < len(data) else 0
        b3 = data[index + 2] if index + 2 < len(data) else 0
        result.append(_append3bytes(b1, b2, b3))
        index += 3
    return "".join(result)


def _append3bytes(b1: int, b2: int, b3: int) -> str:
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return "".join(_encode6bit(value) for value in (c1, c2, c3, c4))


def _encode6bit(value: int) -> str:
    value &= 0x3F
    if value < 10:
        return chr(48 + value)
    value -= 10
    if value < 26:
        return chr(65 + value)
    value -= 26
    if value < 26:
        return chr(97 + value)
    return "-" if value == 0 else "_"


def render_puml_file(
    puml_path: str | Path,
    output_dir: str | Path,
    *,
    server_url: str,
    timeout_seconds: float,
    retries: int = 2,
    session: requests.Session | None = None,
) -> Path:
    source_path = Path(puml_path)
    source = source_path.read_text(encoding="utf-8")
    if "@startuml" not in source.casefold() or "@enduml" not in source.casefold():
        raise ValueError(f"PlantUML inválido: {source_path}")

    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{source_path.stem}.png"
    url = f"{server_url.rstrip('/')}/{encode_puml(source)}"
    client = session or requests.Session()

    for attempt in range(retries + 1):
        try:
            response = client.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            if not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
                raise RuntimeError("El servidor PlantUML no devolvió un PNG válido")
            destination.write_bytes(response.content)
            return destination
        except (requests.Timeout, requests.ConnectionError):
            if attempt >= retries:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("No se pudo renderizar el diagrama")


def render_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    config: AppConfig,
) -> list[Path]:
    return [
        render_puml_file(
            path,
            output_dir,
            server_url=config.plantuml_server,
            timeout_seconds=config.plantuml_timeout_seconds,
        )
        for path in sorted(Path(input_dir).glob("*.puml"))
    ]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Renderiza archivos PlantUML")
    parser.add_argument("--input-dir", type=Path, default=Path("analisis/diagramas_puml"))
    parser.add_argument("--output-dir", type=Path, default=Path("analisis/diagramas_png"))
    args = parser.parse_args()
    generated = render_directory(args.input_dir, args.output_dir, AppConfig.from_env())
    LOGGER.info("Renderizados %d diagramas", len(generated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
