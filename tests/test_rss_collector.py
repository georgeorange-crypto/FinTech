from datetime import datetime, timezone

from src.collectors.rss_collector import dedupe_news
from src.models import NewsItem


def test_rss_dedupe_by_url_and_title() -> None:
    now = datetime.now(timezone.utc)
    items = [
        NewsItem(title="CPI cools", source="A", url="https://example.com/a", published_at=now),
        NewsItem(title="CPI cools", source="B", url="https://example.com/b", published_at=now),
        NewsItem(title="Different", source="A", url="https://example.com/a", published_at=now),
    ]
    deduped = dedupe_news(items)
    assert len(deduped) == 1
