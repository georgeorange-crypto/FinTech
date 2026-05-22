from src.analyzers.market_narrative import build_market_narrative
from src.models import MarketSnapshot


def _snap(symbol: str, ret: float) -> MarketSnapshot:
    return MarketSnapshot(symbol=symbol, name=symbol, group="TEST", one_day_return=ret)


def test_market_narrative_risk_on() -> None:
    narrative = build_market_narrative([_snap("SPY", 0.01), _snap("QQQ", 0.012), _snap("^VIX", -0.05), _snap("TLT", 0.004)])
    assert narrative.regime == "risk_on"


def test_market_narrative_risk_off() -> None:
    narrative = build_market_narrative([_snap("SPY", -0.01), _snap("QQQ", -0.012), _snap("^VIX", 0.08), _snap("TLT", 0.006), _snap("GC=F", 0.01)])
    assert narrative.regime == "risk_off"


def test_market_narrative_rates_shock() -> None:
    narrative = build_market_narrative([_snap("QQQ", -0.01), _snap("TLT", -0.01), _snap("DX-Y.NYB", 0.006)])
    assert narrative.regime == "rates_shock"


def test_market_narrative_crypto_specific() -> None:
    narrative = build_market_narrative([_snap("SPY", 0.001), _snap("QQQ", 0.001), _snap("BTC", 0.05)])
    assert narrative.regime == "crypto_specific"


def test_market_narrative_mixed_when_signals_conflict() -> None:
    narrative = build_market_narrative([_snap("SPY", 0.01), _snap("QQQ", 0.012), _snap("^VIX", 0.08)])
    assert narrative.regime == "mixed"
