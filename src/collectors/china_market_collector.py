from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd

from src.analyzers.market_signal import compute_snapshot
from src.models import MarketSnapshot
from src.utils.paths import RAW_DATA_DIR, dated_dir, safe_filename

LOGGER = logging.getLogger(__name__)

INDEX_CODE_MAP = {
    "上证指数": "000001",
    "深证成指": "399001",
    "创业板指": "399006",
    "沪深300": "000300",
    "中证500": "000905",
    "科创50": "000688",
}


def collect_china_market_data(symbols: list[str], run_date: date) -> tuple[dict[str, pd.DataFrame], list[MarketSnapshot], list[str]]:
    frames: dict[str, pd.DataFrame] = {}
    snapshots: list[MarketSnapshot] = []
    warnings: list[str] = []
    raw_dir = dated_dir(RAW_DATA_DIR / "china_market", run_date)

    if os.getenv("TUSHARE_TOKEN"):
        LOGGER.info("TUSHARE_TOKEN detected; Tushare adapter can be added in this interface later.")

    try:
        import akshare as ak
    except Exception as exc:  # noqa: BLE001
        warning = f"akshare unavailable: {exc}"
        LOGGER.warning(warning)
        return frames, snapshots, [warning]

    for symbol in symbols:
        code = INDEX_CODE_MAP.get(symbol)
        if not code:
            warnings.append(f"unknown China index symbol={symbol}")
            continue
        try:
            df = ak.stock_zh_index_daily_em(symbol=code)
            if df.empty:
                raise ValueError("empty dataframe")
            df = df.rename(columns={"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index().tail(260)
            df.to_csv(raw_dir / f"{safe_filename(symbol)}.csv", encoding="utf-8")
            frames[symbol] = df
            snapshots.append(compute_snapshot(df, symbol=symbol, group="CHINA_A_SHARE"))
        except Exception as exc:  # noqa: BLE001
            warning = f"China market data failed symbol={symbol}: {exc}"
            LOGGER.warning(warning)
            warnings.append(warning)
    return frames, snapshots, warnings
