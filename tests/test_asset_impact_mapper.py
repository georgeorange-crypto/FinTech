from datetime import datetime, timezone

from src.analyzers.asset_impact_mapper import map_news_item
from src.models import NewsItem


def _mapped(title: str) -> dict[str, str]:
    item = map_news_item(
        NewsItem(
            title=title,
            source="Test",
            url=f"https://example.com/{abs(hash(title))}",
            published_at=datetime.now(timezone.utc),
        )
    )
    return {impact.asset: impact.direction for impact in item.asset_impacts}


def test_rate_cut_maps_to_positive_risk_assets_and_negative_dxy() -> None:
    impacts = _mapped("Fed signals rate cut and dovish easing")
    assert impacts["QQQ"] == "positive"
    assert impacts["SPY"] == "positive"
    assert impacts["TLT"] == "positive"
    assert impacts["BTC"] == "positive"
    assert impacts["GC=F"] == "positive"
    assert impacts["DXY"] == "negative"


def test_hawkish_rate_hike_maps_to_negative_risk_assets_and_positive_dxy() -> None:
    impacts = _mapped("Fed warns rate hike and hawkish tightening may continue")
    assert impacts["QQQ"] == "negative"
    assert impacts["SPY"] == "negative"
    assert impacts["TLT"] == "negative"
    assert impacts["BTC"] == "negative"
    assert impacts["DXY"] == "positive"
