from pathlib import Path

from generar_pdf import generate_pdf, markdown_to_story


def test_markdown_to_story_ignores_code_blocks():
    story = markdown_to_story(
        """# Título

Texto visible

```plantuml
@startuml
A -> B
@enduml
```
"""
    )
    assert len(story) == 4


def test_generate_pdf_creates_valid_file(tmp_path: Path):
    source = tmp_path / "analisis.md"
    destination = tmp_path / "documentacion" / "analisis.pdf"
    source.write_text("# Informe\n\nContenido técnico", encoding="utf-8")

    result = generate_pdf(source, destination)

    assert result == destination
    assert destination.read_bytes().startswith(b"%PDF")
