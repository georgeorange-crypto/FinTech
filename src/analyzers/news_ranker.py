from __future__ import annotations

from datetime import datetime, timezone

from src.analyzers.news_importance import rank_news_by_importance
from src.models import NewsItem

HIGH_FREQUENCY_KEYWORDS = [
    "inflation",
    "CPI",
    "PCE",
    "rate cut",
    "rate hike",
    "Federal Reserve",
    "FOMC",
    "Treasury",
    "tariff",
    "sanctions",
    "recession",
    "unemployment",
    "payrolls",
    "GDP",
    "liquidity",
    "debt ceiling",
    "earnings",
    "guidance",
    "AI capex",
    "oil supply",
    "OPEC",
    "gold",
    "bitcoin",
    "stablecoin",
    "SEC",
    "ETF",
    "Hong Kong",
    "China stimulus",
    "PBOC",
    "real estate",
    "local government debt",
]

POLICY_CATEGORIES = {"central_banks", "china_policy", "us_policy", "crypto_policy"}


def score_news_item(item: NewsItem, now: datetime | None = None) -> NewsItem:
    now = now or datetime.now(timezone.utc)
    published_at = item.published_at
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_hours = max((now - published_at.astimezone(timezone.utc)).total_seconds() / 3600, 0)

    text = f"{item.title} {item.summary}".lower()
    keyword_hits = sum(1 for keyword in HIGH_FREQUENCY_KEYWORDS if keyword.lower() in text)
    recency_score = max(0, 1 - age_hours / 72)
    category_bonus = 0.25 if item.category in POLICY_CATEGORIES else 0
    asset_bonus = min(len(item.related_assets) * 0.08, 0.4)

    item.relevance_score = round(
        item.credibility_weight * 2 + keyword_hits * 0.35 + recency_score + category_bonus + asset_bonus,
        4,
    )
    return item


def rank_news(items: list[NewsItem], limit: int | None = None) -> list[NewsItem]:
    ranked = rank_news_by_importance(items)
    return ranked[:limit] if limit else ranked
