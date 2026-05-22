from datetime import datetime, timedelta, timezone

from src.analyzers.news_importance import analyze_news, select_top_news
from src.models import NewsItem


def _item(title: str, weight: float = 0.5, hours_old: int = 1) -> NewsItem:
    return NewsItem(
        title=title,
        source="Test",
        url=f"https://example.com/{abs(hash(title))}",
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_old),
        credibility_weight=weight,
    )


def test_tier1_beats_high_credibility_routine_announcement() -> None:
    analyzed = analyze_news(
        [
            _item("Research paper on payment systems", weight=1.0),
            _item("US CPI hotter than expected", weight=0.4),
        ]
    )
    top = select_top_news(analyzed, limit=2)
    assert top[0].title == "US CPI hotter than expected"


def test_top_news_limits_tier3_items() -> None:
    analyzed = analyze_news(
        [_item(f"Research paper number {idx}", weight=1.0) for idx in range(8)]
        + [_item("FOMC rate decision", weight=0.5), _item("OPEC oil supply cut", weight=0.5)]
    )
    top = select_top_news(analyzed, limit=10, max_tier3=2)
    assert sum(item.importance_tier == 3 for item in top) <= 2
