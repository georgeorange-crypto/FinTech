from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.models import MarketSnapshot


def _return(close: pd.Series, periods: int) -> float | None:
    clean = close.dropna()
    if len(clean) <= periods:
        return None
    previous = clean.iloc[-periods - 1]
    latest = clean.iloc[-1]
    if previous == 0 or pd.isna(previous):
        return None
    return float(latest / previous - 1)


def rsi(close: pd.Series, period: int = 14) -> float | None:
    clean = close.dropna()
    if len(clean) <= period:
        return None
    delta = clean.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    value = 100 - (100 / (1 + rs.iloc[-1]))
    if pd.isna(value):
        return None
    return float(value)


def trend_label(latest: float | None, ma20: float | None, ma60: float | None, one_month: float | None, rsi14: float | None) -> str:
    if any(value is None or (isinstance(value, float) and math.isnan(value)) for value in [latest, ma20, ma60]):
        return "range_bound"
    assert latest is not None and ma20 is not None and ma60 is not None
    one_month = one_month or 0
    rsi14 = rsi14 or 50
    if latest > ma20 > ma60 and one_month > 0.03 and rsi14 >= 55:
        return "strong_uptrend"
    if latest > ma20 and ma20 >= ma60:
        return "uptrend"
    if latest < ma20 < ma60 and one_month < -0.03 and rsi14 <= 45:
        return "strong_downtrend"
    if latest < ma20 and ma20 <= ma60:
        return "downtrend"
    return "range_bound"


def compute_snapshot(df: pd.DataFrame, symbol: str, group: str, name: str | None = None) -> MarketSnapshot:
    if df.empty or "close" not in df.columns:
        return MarketSnapshot(symbol=symbol, name=name or symbol, group=group)

    data = df.sort_index().copy()
    close = pd.to_numeric(data["close"], errors="coerce").dropna()
    if close.empty:
        return MarketSnapshot(symbol=symbol, name=name or symbol, group=group)

    returns = close.pct_change()
    ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else None
    vol20 = returns.tail(20).std() * np.sqrt(252) if len(returns.dropna()) >= 20 else None
    current_year = close[close.index >= pd.Timestamp(f"{close.index[-1].year}-01-01")]
    ytd = None
    if len(current_year) > 1 and current_year.iloc[0] != 0:
        ytd = float(close.iloc[-1] / current_year.iloc[0] - 1)
    rsi14 = rsi(close)
    one_month = _return(close, 21)

    return MarketSnapshot(
        symbol=symbol,
        name=name or symbol,
        group=group,
        latest_close=float(close.iloc[-1]),
        one_day_return=_return(close, 1),
        five_day_return=_return(close, 5),
        one_month_return=one_month,
        ytd_return=ytd,
        volatility_20d=float(vol20) if vol20 is not None and not pd.isna(vol20) else None,
        ma_20=float(ma20) if ma20 is not None and not pd.isna(ma20) else None,
        ma_60=float(ma60) if ma60 is not None and not pd.isna(ma60) else None,
        rsi_14=rsi14,
        trend_label=trend_label(
            float(close.iloc[-1]),
            float(ma20) if ma20 is not None and not pd.isna(ma20) else None,
            float(ma60) if ma60 is not None and not pd.isna(ma60) else None,
            one_month,
            rsi14,
        ),
    )
