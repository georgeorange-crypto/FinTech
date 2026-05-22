from __future__ import annotations

import logging
import os
from datetime import date, timedelta

from src.utils.config import load_yaml
from src.utils.http import request_json
from src.utils.json_io import write_json
from src.utils.paths import CONFIG_DIR, RAW_DATA_DIR, dated_dir

LOGGER = logging.getLogger(__name__)


def collect_fred_series(run_date: date) -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        warning = "FRED_API_KEY not set; skipping FRED macro series"
        LOGGER.info(warning)
        return {}, [warning]

    config = load_yaml(CONFIG_DIR / "macro_series.yml")
    observation_start = (run_date - timedelta(days=365 * 5)).isoformat()
    output_dir = dated_dir(RAW_DATA_DIR / "fred", run_date)
    results: dict[str, list[dict[str, str]]] = {}
    warnings: list[str] = []

    for series in config.get("series", []):
        series_id = series["id"]
        payload = request_json(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": observation_start,
            },
            timeout=20,
            retries=3,
        )
        if not payload or "observations" not in payload:
            warnings.append(f"FRED failed series={series_id}")
            continue
        observations = payload["observations"]
        results[series_id] = observations
        write_json(output_dir / f"{series_id}.json", observations)
    return results, warnings
