from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.utils.json_io import write_json
from src.utils.paths import PROCESSED_DATA_DIR, PUBLIC_DIR, REPORTS_DIR, TEMPLATES_DIR, ensure_dir

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


def build_index(limit: int = 30) -> Path:
    ensure_dir(PUBLIC_DIR)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())
    template = env.get_template("index.html.j2")
    reports = sorted(REPORTS_DIR.glob("*.html"), reverse=True)[:limit]
    entries = [{"date": path.stem, "href": f"../reports/{path.name}"} for path in reports]
    metadata = _metadata_for_date(reports[0].stem) if reports else {
        "latest_date": "n/a",
        "regime": "unknown",
        "regime_summary": "No reports yet.",
        "cards": [],
        "top_themes": [],
    }
    write_json(PUBLIC_DIR / "metadata.json", metadata)
    output_path = PUBLIC_DIR / "index.html"
    output_path.write_text(template.render(entries=entries, metadata=metadata), encoding="utf-8")
    return output_path
