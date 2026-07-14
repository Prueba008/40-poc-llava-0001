from __future__ import annotations

import argparse
import html
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def markdown_to_story(markdown: str) -> list:
    styles = getSampleStyleSheet()
    story: list = []
    in_code = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line:
            continue
        if line.startswith("# "):
            style = styles["Title"]
            text = line[2:]
        elif line.startswith("## "):
            style = styles["Heading2"]
            text = line[3:]
        elif line.startswith("### "):
            style = styles["Heading3"]
            text = line[4:]
        else:
            style = styles["BodyText"]
            text = line.removeprefix("- ")
        story.append(Paragraph(html.escape(text), style))
        story.append(Spacer(1, 6))
    return story


def generate_pdf(markdown_file: str | Path, output_file: str | Path) -> Path:
    source = Path(markdown_file)
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    markdown = source.read_text(encoding="utf-8")
    document = SimpleDocTemplate(str(destination), pagesize=A4)
    document.build(markdown_to_story(markdown))
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera PDF desde el análisis Markdown")
    parser.add_argument("--input", type=Path, default=Path("analisis/analisis_completo.md"))
    parser.add_argument("--output", type=Path, default=Path("documentacion/analisis_arquitectura.pdf"))
    args = parser.parse_args()
    generate_pdf(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
