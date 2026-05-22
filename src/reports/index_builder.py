from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.utils.json_io import write_json
from src.utils.paths import (
    CHARTS_DIR,
    PROCESSED_DATA_DIR,
    PUBLIC_DIR,
    REPORTS_DIR,
    TEMPLATES_DIR,
    ensure_dir,
)

DASHBOARD_ASSETS = {
    "美股 SPY": "SPY",
    "QQQ": "QQQ",
    "VIX": "^VIX",
    "BTC": "BTC",
    "Gold": "GC=F",
    "Oil": "CL=F",
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def _metadata_for_date(date_text: str) -> dict[str, Any]:
    processed = PROCESSED_DATA_DIR / date_text
    brief = _load_json(processed / "daily_brief.json") or {}
    snapshots = _load_json(processed / "market_snapshots.json") or []
    snapshot_by_symbol = {item.get("symbol"): item for item in snapshots}
    cards = []
    for label, symbol in DASHBOARD_ASSETS.items():
        value = (snapshot_by_symbol.get(symbol) or {}).get("one_day_return")
        cards.append({"label": label, "value": _pct(value)})
    narrative = brief.get("market_narrative") or {}
    return {
        "latest_date": date_text,
        "regime": narrative.get("regime", "unknown"),
        "regime_summary": narrative.get("summary_cn", "暂无市场状态摘要。"),
        "cards": cards,
        "top_themes": brief.get("top_themes") or [],
    }


def _copy_static_site_assets(reports: list[Path]) -> list[dict[str, str]]:
    public_reports_dir = ensure_dir(PUBLIC_DIR / "reports")
    public_charts_dir = ensure_dir(PUBLIC_DIR / "charts")
    entries: list[dict[str, str]] = []

    for report_path in reports:
        destination = public_reports_dir / report_path.name
        shutil.copy2(report_path, destination)
        chart_source = CHARTS_DIR / report_path.stem
        chart_destination = public_charts_dir / report_path.stem
        if chart_source.exists():
            if chart_destination.exists():
                shutil.rmtree(chart_destination)
            shutil.copytree(chart_source, chart_destination)
        entries.append({"date": report_path.stem, "href": f"reports/{report_path.name}"})
    return entries


def _latest_report_body(report_path: Path | None) -> str:
    if not report_path or not report_path.exists():
        return ""
    soup = BeautifulSoup(report_path.read_text(encoding="utf-8"), "html.parser")
    body = soup.find("main") or soup.body
    if not body:
        return ""
    for image in body.find_all("img"):
        source = image.get("src")
        if isinstance(source, str):
            image["src"] = source.replace("../charts/", "charts/")
    return "".join(str(child) for child in body.children)


def build_index(limit: int = 30) -> Path:
    ensure_dir(PUBLIC_DIR)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())
    template = env.get_template("index.html.j2")
    reports = sorted(REPORTS_DIR.glob("*.html"), reverse=True)[:limit]
    entries = _copy_static_site_assets(reports)
    metadata = (
        _metadata_for_date(reports[0].stem)
        if reports
        else {
            "latest_date": "n/a",
            "regime": "unknown",
            "regime_summary": "No reports yet.",
            "cards": [],
            "top_themes": [],
        }
    )
    metadata["latest_report_href"] = entries[0]["href"] if entries else ""
    write_json(PUBLIC_DIR / "metadata.json", metadata)
    output_path = PUBLIC_DIR / "index.html"
    output_path.write_text(
        template.render(entries=entries, metadata=metadata, latest_report_body=_latest_report_body(reports[0] if reports else None)),
        encoding="utf-8",
    )
    return output_path
