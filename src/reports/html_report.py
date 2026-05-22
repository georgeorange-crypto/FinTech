from __future__ import annotations

from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.utils.paths import REPORTS_DIR, TEMPLATES_DIR, ensure_dir


def markdown_to_html(markdown_text: str) -> str:
    return markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "toc"])


def render_html_report(markdown_path: Path) -> Path:
    ensure_dir(REPORTS_DIR)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())
    template = env.get_template("report.html.j2")
    body = markdown_to_html(markdown_path.read_text(encoding="utf-8"))
    html = template.render(title=markdown_path.stem, body=body)
    output_path = markdown_path.with_suffix(".html")
    output_path.write_text(html, encoding="utf-8")
    return output_path
