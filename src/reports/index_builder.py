from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.utils.paths import PUBLIC_DIR, REPORTS_DIR, TEMPLATES_DIR, ensure_dir


def build_index(limit: int = 30) -> Path:
    ensure_dir(PUBLIC_DIR)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())
    template = env.get_template("index.html.j2")
    reports = sorted(REPORTS_DIR.glob("*.html"), reverse=True)[:limit]
    latest_body = ""
    if reports:
        latest_body = reports[0].read_text(encoding="utf-8")
    entries = [{"date": path.stem, "href": f"../reports/{path.name}"} for path in reports]
    output_path = PUBLIC_DIR / "index.html"
    output_path.write_text(template.render(entries=entries, latest_body=latest_body), encoding="utf-8")
    return output_path
