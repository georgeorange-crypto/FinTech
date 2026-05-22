from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd

from src.analyzers.market_signal import compute_snapshot
from src.models import MarketSnapshot
from src.utils.http import request_json
from src.utils.paths import RAW_DATA_DIR, dated_dir, safe_filename

LOGGER = logging.getLogger(__name__)


def collect_crypto_data(symbols: list[str], run_date: date) -> tuple[dict[str, pd.DataFrame], list[MarketSnapshot], list[str]]:
    frames: dict[str, pd.DataFrame] = {}
    snapshots: list[MarketSnapshot] = []
    warnings: list[str] = []
    raw_dir = dated_dir(RAW_DATA_DIR / "crypto", run_date)
    api_key = os.getenv("COINGECKO_API_KEY")
    headers = {"x-cg-demo-api-key": api_key} if api_key else None

    for coin_id in symbols:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        payload = request_json(
            url,
            params={"vs_currency": "usd", "days": "365", "interval": "daily"},
            headers=headers,
            timeout=25,
            retries=3,
        )
        if not payload or "prices" not in payload:
            warning = f"crypto data failed coin={coin_id}"
            LOGGER.warning(warning)
            warnings.append(warning)
            continue
        try:
            df = pd.DataFrame(payload["prices"], columns=["timestamp_ms", "close"])
            df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms").dt.normalize()
            df = df.groupby("date", as_index=True)["close"].last().to_frame()
            df["open"] = df["close"]
            df["high"] = df["close"]
            df["low"] = df["close"]
            df["volume"] = None
            df.to_csv(raw_dir / f"{safe_filename(coin_id)}.csv", encoding="utf-8")
            symbol = coin_id.upper() if coin_id not in {"bitcoin", "ethereum"} else {"bitcoin": "BTC", "ethereum": "ETH"}[coin_id]
            frames[symbol] = df
            snapshots.append(compute_snapshot(df, symbol=symbol, group="CRYPTO", name=coin_id))
        except Exception as exc:  # noqa: BLE001
            warning = f"crypto parse failed coin={coin_id}: {exc}"
            LOGGER.warning(warning)
            warnings.append(warning)
    return frames, snapshots, warnings
