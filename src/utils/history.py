from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models import MarketSnapshot, NewsItem
from src.utils.paths import DATA_DIR, ensure_dir


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_history(run_date: str, events: list[NewsItem], snapshots: list[MarketSnapshot]) -> None:
    history_dir = ensure_dir(DATA_DIR / "history")
    event_rows = []
    for item in events:
        row = item.model_dump(mode="json")
        row["run_date"] = run_date
        event_rows.append(row)
    snapshot_rows = []
    for snapshot in snapshots:
        row = snapshot.model_dump(mode="json")
        row["run_date"] = run_date
        snapshot_rows.append(row)
    append_jsonl(history_dir / "events.jsonl", event_rows)
    append_jsonl(history_dir / "market_snapshots.jsonl", snapshot_rows)
