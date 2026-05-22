from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models import NewsItem


def test_news_item_validation_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        NewsItem(
            title=" ",
            source="Fed",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
        )


def test_news_item_validation_accepts_valid_item() -> None:
    item = NewsItem(
        title="Federal Reserve leaves rates unchanged",
        source="Federal Reserve",
        url="https://example.com/fed",
        published_at=datetime.now(timezone.utc),
        credibility_weight=1,
    )
    assert item.title.startswith("Federal Reserve")
