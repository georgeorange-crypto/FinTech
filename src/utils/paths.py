from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT / "reports"
CHARTS_DIR = ROOT / "charts"
PUBLIC_DIR = ROOT / "public"
TEMPLATES_DIR = ROOT / "templates"
INPUT_REPORTS_DIR = ROOT / "inputs" / "reports"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def dated_dir(base: Path, run_date: date) -> Path:
    return ensure_dir(base / run_date.isoformat())


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", value, flags=re.UNICODE)
    return cleaned.strip("_") or "asset"
