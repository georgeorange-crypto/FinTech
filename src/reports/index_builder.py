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
    ROOT,
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


def _price(value: float | None) -> str:
    return "n/a" if value is None else f"{value:,.2f}"


def _direction(value: float | None) -> str:
    if value is None:
        return "flat"
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return "flat"


def _compact_news(item: dict[str, Any]) -> dict[str, Any]:
    related_assets = item.get("related_assets") or []
    return {
        "title": item.get("title", "Untitled"),
        "source": item.get("source", "unknown"),
        "url": item.get("url", ""),
        "event_type": item.get("event_type", "other"),
        "importance_tier": item.get("importance_tier", 3),
        "impact_strength": item.get("impact_strength", "low"),
        "impact_direction": item.get("impact_direction", "unknown"),
        "reason": item.get("human_importance_reason", ""),
        "market_impact": item.get("expected_market_impact", ""),
        "assets": related_assets[:5],
    }


def _asset_movers(snapshots: list[dict[str, Any]], limit: int = 8) -> list[dict[str, str]]:
    ranked = sorted(
        snapshots,
        key=lambda item: abs(item.get("one_day_return") or 0),
        reverse=True,
    )
    movers = []
    for item in ranked[:limit]:
        value = item.get("one_day_return")
        movers.append(
            {
                "symbol": item.get("symbol", "n/a"),
                "group": item.get("group", "UNKNOWN"),
                "price": _price(item.get("latest_close")),
                "one_day": _pct(value),
                "five_day": _pct(item.get("five_day_return")),
                "trend": item.get("trend_label", "unknown"),
                "direction": _direction(value),
            }
        )
    return movers


def _load_market_snapshots(date_text: str) -> tuple[list[dict[str, Any]], str]:
    current = _load_json(PROCESSED_DATA_DIR / date_text / "market_snapshots.json") or []
    if current:
        return current, date_text
    if not PROCESSED_DATA_DIR.exists():
        return [], date_text
    for directory in sorted(PROCESSED_DATA_DIR.iterdir(), reverse=True):
        if not directory.is_dir() or directory.name == date_text:
            continue
        snapshots = _load_json(directory / "market_snapshots.json") or []
        if snapshots:
            return snapshots, directory.name
    return [], date_text


def _chart_tiles(date_text: str, limit: int = 4) -> tuple[list[dict[str, str]], str]:
    chart_dir = CHARTS_DIR / date_text
    chart_date = date_text
    if not chart_dir.exists():
        candidates = [path for path in sorted(CHARTS_DIR.iterdir(), reverse=True) if path.is_dir()] if CHARTS_DIR.exists() else []
        chart_dir = candidates[0] if candidates else chart_dir
        chart_date = chart_dir.name
    if not chart_dir.exists():
        return [], date_text
    charts = sorted(chart_dir.glob("*_summary.png"))[:limit]
    return [{"label": chart.stem.replace("_summary", ""), "src": f"charts/{chart_date}/{chart.name}"} for chart in charts], chart_date


def _metadata_for_date(date_text: str) -> dict[str, Any]:
    processed = PROCESSED_DATA_DIR / date_text
    brief = _load_json(processed / "daily_brief.json") or {}
    snapshots, market_data_date = _load_market_snapshots(date_text)
    chart_tiles, chart_date = _chart_tiles(date_text)
    snapshot_by_symbol = {item.get("symbol"): item for item in snapshots}
    cards = []
    for label, symbol in DASHBOARD_ASSETS.items():
        value = (snapshot_by_symbol.get(symbol) or {}).get("one_day_return")
        cards.append({"label": label, "value": _pct(value)})
    narrative = brief.get("market_narrative") or {}
    top_news = brief.get("top_news") or []
    policy_watch = brief.get("policy_watch") or []
    background_materials = brief.get("background_materials") or []
    return {
        "latest_date": date_text,
        "market_data_date": market_data_date,
        "chart_date": chart_date,
        "regime": narrative.get("regime", "unknown"),
        "regime_summary": narrative.get("summary_cn", "暂无市场状态摘要。"),
        "key_moves": narrative.get("key_moves") or [],
        "watch_points": narrative.get("watch_points") or [],
        "cards": cards,
        "top_themes": brief.get("top_themes") or [],
        "news_counts": {
            "must_read": len(top_news),
            "policy_watch": len(policy_watch),
            "background": len(background_materials),
        },
        "focus_news": [_compact_news(item) for item in top_news[:4]],
        "policy_news": [_compact_news(item) for item in policy_watch[:3]],
        "asset_movers": _asset_movers(snapshots),
        "chart_tiles": chart_tiles,
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
            "market_data_date": "n/a",
            "chart_date": "n/a",
            "regime": "unknown",
            "regime_summary": "No reports yet.",
            "key_moves": [],
            "watch_points": [],
            "cards": [],
            "top_themes": [],
            "news_counts": {"must_read": 0, "policy_watch": 0, "background": 0},
            "focus_news": [],
            "policy_news": [],
            "asset_movers": [],
            "chart_tiles": [],
        }
    )
    metadata["latest_report_href"] = entries[0]["href"] if entries else ""
    write_json(PUBLIC_DIR / "metadata.json", metadata)
    output_path = PUBLIC_DIR / "index.html"
    html = template.render(entries=entries, metadata=metadata, latest_report_body=_latest_report_body(reports[0] if reports else None))
    output_path.write_text(html, encoding="utf-8")
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    return output_path
