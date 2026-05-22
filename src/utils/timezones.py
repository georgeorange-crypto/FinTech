from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def get_local_today(timezone: str = "Asia/Taipei") -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def parse_run_date(value: str | None, timezone: str = "Asia/Taipei") -> date:
    if not value or value == "today":
        return get_local_today(timezone)
    return date.fromisoformat(value)
