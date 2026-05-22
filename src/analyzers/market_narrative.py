from __future__ import annotations

from src.models import MarketNarrative, MarketSnapshot


def _by_symbol(snapshots: list[MarketSnapshot]) -> dict[str, MarketSnapshot]:
    return {snapshot.symbol: snapshot for snapshot in snapshots}


def _ret(snapshot: MarketSnapshot | None) -> float | None:
    return snapshot.one_day_return if snapshot else None


def _move_text(symbol: str, value: float | None, threshold: float = 0.01) -> str | None:
    if value is None or abs(value) < threshold:
        return None
    direction = "上涨" if value > 0 else "下跌"
    return f"{symbol} {direction} {value * 100:.2f}%"


def build_market_narrative(snapshots: list[MarketSnapshot]) -> MarketNarrative:
    data = _by_symbol(snapshots)
    spy = _ret(data.get("SPY"))
    qqq = _ret(data.get("QQQ"))
    vix = _ret(data.get("^VIX"))
    tlt = _ret(data.get("TLT"))
    dxy = _ret(data.get("DX-Y.NYB")) or _ret(data.get("DXY"))
    gold = _ret(data.get("GC=F"))
    oil = _ret(data.get("CL=F")) or _ret(data.get("BZ=F"))
    btc = _ret(data.get("BTC"))
    eth = _ret(data.get("ETH"))

    key_moves = [
        move
        for symbol, value, threshold in [
            ("SPY", spy, 0.004),
            ("QQQ", qqq, 0.004),
            ("VIX", vix, 0.03),
            ("TLT", tlt, 0.004),
            ("DXY", dxy, 0.003),
            ("Gold", gold, 0.005),
            ("Oil", oil, 0.01),
            ("BTC", btc, 0.02),
            ("ETH", eth, 0.02),
        ]
        if (move := _move_text(symbol, value, threshold))
    ]

    risk_assets_up = (spy or 0) > 0.003 and (qqq or 0) > 0.003
    risk_assets_down = (spy or 0) < -0.003 and (qqq or 0) < -0.003
    vix_down = (vix or 0) < -0.02
    vix_up = (vix or 0) > 0.02
    bonds_up = (tlt or 0) > 0.003
    bonds_down = (tlt or 0) < -0.003
    dollar_up = (dxy or 0) > 0.003
    dollar_down = (dxy or 0) < -0.003
    gold_up = (gold or 0) > 0.005
    oil_up = (oil or 0) > 0.01
    crypto_up = (btc or 0) > 0.02 or (eth or 0) > 0.02
    equity_flat = abs(spy or 0) < 0.004 and abs(qqq or 0) < 0.004

    contradictions: list[str] = []
    if risk_assets_up and vix_up:
        contradictions.append("股指上涨但 VIX 同时走高，风险偏好信号不一致。")
    if risk_assets_down and bonds_down:
        contradictions.append("股债同时承压，可能是利率或流动性冲击而非传统避险。")
    if gold_up and dollar_up:
        contradictions.append("黄金和美元同时上涨，可能反映避险或地缘风险。")
    if crypto_up and risk_assets_down:
        contradictions.append("加密资产走强但美股走弱，可能是加密市场自身事件驱动。")

    regime = "unknown"
    summary = "市场信号不足，暂不判断明确状态。"
    watch_points = ["关注后续数据是否确认当前跨资产信号。"]

    if risk_assets_up and (vix_down or bonds_up or dollar_down):
        regime = "risk_on"
        summary = "股指上涨、波动率或美元回落，市场更接近风险偏好改善。"
        watch_points = ["确认风险偏好是否扩散到小盘股、信用利差和周期品。"]
    elif risk_assets_down and vix_up and (bonds_up or gold_up):
        regime = "risk_off"
        summary = "股指回落、VIX 抬升且避险资产走强，市场偏风险规避。"
        watch_points = ["关注避险是否演变为信用或流动性压力。"]
    elif bonds_down and dollar_up and (qqq or 0) < -0.003:
        regime = "rates_shock"
        summary = "长债下跌、美元走强且成长股承压，市场像是在交易利率冲击。"
        watch_points = ["关注美债收益率、实际利率和成长股估值压力。"]
    elif dollar_up and risk_assets_down:
        regime = "dollar_liquidity_tightening"
        summary = "美元走强并压制风险资产，市场可能在交易美元流动性收紧。"
        watch_points = ["关注离岸美元、亚洲货币和新兴市场资产反应。"]
    elif oil_up and gold_up and risk_assets_down:
        regime = "inflation_shock"
        summary = "原油和黄金走强、股指承压，市场可能在交易通胀或地缘风险冲击。"
        watch_points = ["关注能源价格是否传导到通胀预期和央行沟通。"]
    elif crypto_up and equity_flat:
        regime = "crypto_specific"
        summary = "BTC/ETH 明显走强但美股平淡，行情更像加密自身事件驱动。"
        watch_points = ["关注 ETF、监管、稳定币或链上流动性新闻。"]

    if contradictions:
        regime = "mixed" if regime != "unknown" else "mixed"
        summary = f"{summary} 但存在信号冲突，需要降低单一叙事置信度。"

    return MarketNarrative(
        regime=regime,  # type: ignore[arg-type]
        summary_cn=summary,
        key_moves=key_moves or ["暂无显著跨资产异动。"],
        contradictions=contradictions,
        watch_points=watch_points,
    )
