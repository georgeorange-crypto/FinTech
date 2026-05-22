from __future__ import annotations

import logging
from datetime import date

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src.models import MarketSnapshot
from src.utils.paths import CHARTS_DIR, dated_dir, safe_filename

LOGGER = logging.getLogger(__name__)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def build_asset_chart(symbol: str, df: pd.DataFrame, snapshot: MarketSnapshot, run_date: date) -> str | None:
    if df.empty or "close" not in df.columns:
        return None
    output_dir = dated_dir(CHARTS_DIR, run_date)
    out = output_dir / f"{safe_filename(symbol)}.png"
    data = df.sort_index().tail(90).copy()
    data["ma20"] = data["close"].rolling(20).mean()
    data["ma60"] = data["close"].rolling(60).mean()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data["close"], label="Close", linewidth=1.8)
    ax.plot(data.index, data["ma20"], label="MA20", linewidth=1.2)
    ax.plot(data.index, data["ma60"], label="MA60", linewidth=1.2)
    ax.set_title(
        f"{symbol} | 1D {_pct(snapshot.one_day_return)} | 5D {_pct(snapshot.five_day_return)} | "
        f"1M {_pct(snapshot.one_month_return)} | YTD {_pct(snapshot.ytd_return)}"
    )
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return str(out)


def build_group_summary_chart(group: str, snapshots: list[MarketSnapshot], run_date: date) -> str | None:
    group_snapshots = [snapshot for snapshot in snapshots if snapshot.group == group]
    if not group_snapshots:
        return None
    output_dir = dated_dir(CHARTS_DIR, run_date)
    out = output_dir / f"{safe_filename(group)}_summary.png"
    symbols = [snapshot.symbol for snapshot in group_snapshots]
    one_day = [(snapshot.one_day_return or 0) * 100 for snapshot in group_snapshots]
    five_day = [(snapshot.five_day_return or 0) * 100 for snapshot in group_snapshots]

    x = range(len(symbols))
    fig, ax = plt.subplots(figsize=(max(8, len(symbols) * 0.9), 4.5))
    ax.bar([i - 0.18 for i in x], one_day, width=0.36, label="1D")
    ax.bar([i + 0.18 for i in x], five_day, width=0.36, label="5D")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(f"{group} Returns")
    ax.set_ylabel("Return (%)")
    ax.set_xticks(list(x), symbols, rotation=35, ha="right")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return str(out)


def build_charts(
    frames: dict[str, pd.DataFrame],
    snapshots: list[MarketSnapshot],
    run_date: date,
) -> dict[str, str]:
    chart_paths: dict[str, str] = {}
    snapshot_by_symbol = {snapshot.symbol: snapshot for snapshot in snapshots}
    for symbol, df in frames.items():
        snapshot = snapshot_by_symbol.get(symbol)
        if not snapshot:
            continue
        try:
            path = build_asset_chart(symbol, df, snapshot, run_date)
            if path:
                chart_paths[symbol] = path
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Chart failed symbol=%s error=%s", symbol, exc)

    for group in sorted({snapshot.group for snapshot in snapshots}):
        try:
            path = build_group_summary_chart(group, snapshots, run_date)
            if path:
                chart_paths[f"{group}_summary"] = path
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Summary chart failed group=%s error=%s", group, exc)
    return chart_paths
