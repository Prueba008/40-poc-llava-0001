from pathlib import Path

import pytest

from renderizar_puml import encode_puml, render_puml_file


class FakeResponse:
    status_code = 200
    content = b"\x89PNG\r\n\x1a\nPNG"

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, response=None):
        self.url = None
        self.timeout = None
        self.closed = False
        self.response = response or FakeResponse()

    def get(self, url, timeout):
        self.url = url
        self.timeout = timeout
        return self.response

    def close(self):
        self.closed = True


def test_encode_puml_known_example():
    source = "@startuml\nAlice -> Bob: test\n@enduml"
    assert encode_puml(source) == "SoWkIImgAStDuNBCoKnELT2rKt3AJx9IA4ajBk5oICrB0Ke10000"


def test_render_writes_png(tmp_path: Path):
    source = tmp_path / "diagram.puml"
    source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    session = FakeSession()
    output = render_puml_file(
        source,
        tmp_path / "png",
        server_url="https://plantuml.example/png/",
        timeout_seconds=5,
        session=session,
    )
    assert output.read_bytes().startswith(b"\x89PNG")
    assert session.timeout == 5
    assert session.url.startswith("https://plantuml.example/png/")
    assert session.closed is False


def test_render_closes_owned_session(tmp_path: Path, monkeypatch):
    source = tmp_path / "diagram.puml"
    source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    session = FakeSession()
    monkeypatch.setattr("renderizar_puml.requests.Session", lambda: session)

    render_puml_file(
        source,
        tmp_path / "png",
        server_url="https://plantuml.example/png/",
        timeout_seconds=5,
    )

    assert session.closed is True


def test_render_rejects_invalid_source(tmp_path: Path):
    source = tmp_path / "bad.puml"
    source.write_text("A -> B", encoding="utf-8")
    with pytest.raises(ValueError):
        render_puml_file(
            source,
            tmp_path,
            server_url="https://plantuml.example/png/",
            timeout_seconds=5,
        )


@pytest.mark.parametrize(
    ("server_url", "timeout_seconds", "retries"),
    [
        ("", 5, 0),
        ("https://plantuml.example/png/", 0, 0),
        ("https://plantuml.example/png/", 5, -1),
    ],
)
def test_render_rejects_invalid_arguments(
    tmp_path: Path,
    server_url: str,
    timeout_seconds: float,
    retries: int,
):
    source = tmp_path / "diagram.puml"
    source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    with pytest.raises(ValueError):
        render_puml_file(
            source,
            tmp_path,
            server_url=server_url,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )
