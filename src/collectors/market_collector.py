from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from src.analyzers.market_signal import compute_snapshot
from src.models import MarketSnapshot
from src.utils.paths import RAW_DATA_DIR, dated_dir, safe_filename

LOGGER = logging.getLogger(__name__)


def _normalize_yfinance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    normalized = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    normalized.index = pd.to_datetime(normalized.index).tz_localize(None)
    return normalized


def collect_market_data(
    assets: dict[str, list[str]],
    run_date: date,
    *,
    groups: set[str] | None = None,
) -> tuple[dict[str, pd.DataFrame], list[MarketSnapshot], list[str]]:
    warnings: list[str] = []
    frames: dict[str, pd.DataFrame] = {}
    snapshots: list[MarketSnapshot] = []
    raw_dir = dated_dir(RAW_DATA_DIR / "market", run_date)

    try:
        import yfinance as yf
    except Exception as exc:  # noqa: BLE001
        warning = f"yfinance unavailable: {exc}"
        LOGGER.warning(warning)
        return frames, snapshots, [warning]

    for group, symbols in assets.items():
        if groups and group not in groups:
            continue
        for symbol in symbols:
            try:
                df = yf.download(symbol, period="1y", interval="1d", auto_adjust=False, progress=False, threads=False)
                df = _normalize_yfinance(df)
                if df.empty:
                    raise ValueError("empty dataframe")
                output_path = raw_dir / f"{safe_filename(symbol)}.csv"
                df.to_csv(output_path, encoding="utf-8")
                frames[symbol] = df
                snapshots.append(compute_snapshot(df, symbol=symbol, group=group))
            except Exception as exc:  # noqa: BLE001
                warning = f"market data failed symbol={symbol}: {exc}"
                LOGGER.warning(warning)
                warnings.append(warning)
    return frames, snapshots, warnings


def read_market_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date")
