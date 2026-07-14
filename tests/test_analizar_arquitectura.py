from __future__ import annotations

import base64
from pathlib import Path

import pytest
import requests

from analizar_arquitectura import (
    InvalidImageError,
    OllamaError,
    build_ollama_payload,
    discover_images,
    encode_image,
    extract_puml_blocks,
    query_ollama,
    validate_puml_block,
    write_puml_blocks,
)


class FakeResponse:
    def __init__(self, body=None, status=200, content=b""):
        self._body = body
        self.status_code = status
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError("failure")
            error.response = self
            raise error

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.last_json = None
        self.last_timeout = None

    def post(self, _url, *, json, timeout):
        self.last_json = json
        self.last_timeout = timeout
        if self.error:
            raise self.error
        return self.response


def test_discover_images_filters_and_sorts(tmp_path: Path):
    for name in ["b.jpg", "a.PNG", "c.gif", "ignore.txt"]:
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in discover_images(tmp_path)] == ["a.PNG", "b.jpg", "c.gif"]


def test_encode_image_roundtrip(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\ncontent"
    image = tmp_path / "image.png"
    image.write_bytes(data)
    assert base64.b64decode(encode_image(image)) == data


def test_encode_image_rejects_empty(tmp_path: Path):
    image = tmp_path / "empty.png"
    image.touch()
    with pytest.raises(InvalidImageError):
        encode_image(image)


def test_build_payload_omits_images_when_absent():
    payload = build_ollama_payload("hola", None, "llava")
    assert payload == {"model": "llava", "prompt": "hola", "stream": False}


def test_query_ollama_validates_contract():
    session = FakeSession(FakeResponse({"model": "llava", "response": " análisis "}))
    result = query_ollama(
        "prompt",
        "base64",
        ollama_url="http://ollama/api/generate",
        model="llava",
        timeout_seconds=10,
        session=session,
    )
    assert result.response == "análisis"
    assert session.last_json["images"] == ["base64"]
    assert session.last_timeout == 10


def test_query_ollama_rejects_invalid_json():
    session = FakeSession(FakeResponse(ValueError("bad json")))
    with pytest.raises(OllamaError, match="JSON inválido"):
        query_ollama(
            "prompt",
            ollama_url="http://ollama",
            model="llava",
            timeout_seconds=10,
            session=session,
        )


def test_query_ollama_classifies_timeout():
    session = FakeSession(error=requests.Timeout("slow"))
    with pytest.raises(OllamaError, match="timeout"):
        query_ollama(
            "prompt",
            ollama_url="http://ollama",
            model="llava",
            timeout_seconds=10,
            session=session,
        )


def test_extract_and_write_multiple_puml_blocks(tmp_path: Path):
    response = """
```puml
@startuml
A -> B
@enduml
```
```plantuml
@startuml
B -> C
@enduml
```
"""
    blocks = extract_puml_blocks(response)
    paths = write_puml_blocks("arquitectura.png", blocks, tmp_path)
    assert len(paths) == 2
    assert all(path.read_text(encoding="utf-8").endswith("\n") for path in paths)


def test_validate_puml_rejects_invalid_block():
    with pytest.raises(Exception):
        validate_puml_block("A -> B")
