from datetime import datetime, timezone

from src.analyzers.event_classifier import classify_event
from src.models import NewsItem


def _item(title: str, summary: str = "") -> NewsItem:
    return NewsItem(
        title=title,
        source="Test",
        url=f"https://example.com/{abs(hash(title))}",
        published_at=datetime.now(timezone.utc),
        summary=summary,
        credibility_weight=0.5,
    )


def test_major_events_get_higher_tier() -> None:
    cases = [
        ("US CPI comes in hotter than expected", "macro_data"),
        ("FOMC rate decision and dot plot released", "central_bank_decision"),
        ("OPEC weighs oil supply cuts", "commodity_supply"),
        ("SEC crypto ETF approval expected", "crypto_market_structure"),
    ]
    for title, event_type in cases:
        item = classify_event(_item(title))
        assert item.event_type == event_type
        assert item.importance_tier <= 2
        assert item.is_market_moving


def test_research_and_statistics_default_to_routine_tier3() -> None:
    for title in ["Research paper on wage expectations", "Statistics table accounts released"]:
        item = classify_event(_item(title))
        assert item.importance_tier == 3
        assert item.is_routine
