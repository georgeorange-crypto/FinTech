import pandas as pd

from src.analyzers.market_signal import compute_snapshot


def test_market_signal_metrics_for_increasing_series() -> None:
    index = pd.date_range("2026-01-01", periods=90, freq="D")
    df = pd.DataFrame({"close": range(100, 190), "open": range(100, 190), "high": range(101, 191), "low": range(99, 189), "volume": 1000}, index=index)
    snapshot = compute_snapshot(df, symbol="SPY", group="US_EQUITY")
    assert snapshot.one_day_return is not None
    assert snapshot.ma_20 is not None
    assert snapshot.ma_60 is not None
    assert snapshot.trend_label in {"uptrend", "strong_uptrend"}
