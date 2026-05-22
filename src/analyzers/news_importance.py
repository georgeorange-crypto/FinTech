from __future__ import annotations

from datetime import datetime, timezone

from src.analyzers.asset_impact_mapper import map_news_item
from src.analyzers.event_classifier import classify_event
from src.models import NewsItem
from src.utils.config import load_yaml
from src.utils.paths import CONFIG_DIR

POLICY_EVENT_TYPES = {
    "central_bank_decision",
    "central_bank_speech",
    "fiscal_policy",
    "regulation",
    "crypto_market_structure",
    "financial_stability",
}


def _age_hours(item: NewsItem, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    published = item.published_at
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return max((now - published.astimezone(timezone.utc)).total_seconds() / 3600, 0)


def expected_market_impact(item: NewsItem) -> str:
    if item.asset_impacts:
        lead = item.asset_impacts[0]
        return f"主要影响 {lead.asset}，方向为 {lead.direction}，强度 {lead.strength}；{lead.reason}"
    if item.is_market_moving:
        return "可能影响利率、汇率、风险资产或大宗商品预期，但当前公开信息不足以判断明确方向。"
    return "更偏背景信息，短期市场影响可能有限。"


def analyze_news_item(item: NewsItem) -> NewsItem:
    item = classify_event(item)
    item = map_news_item(item)
    item.expected_market_impact = expected_market_impact(item)
    item.affected_asset_classes = sorted({impact.asset_class for impact in item.asset_impacts})
    item.related_assets = sorted({impact.asset for impact in item.asset_impacts} | set(item.related_assets))

    tier_base = {1: 100.0, 2: 50.0, 3: 10.0}[item.importance_tier]
    recency = max(0, 1 - _age_hours(item) / 72) * 8
    asset_bonus = min(len(item.asset_impacts) * 2, 12)
    market_bonus = 8 if item.is_market_moving else 0
    routine_penalty = 20 if item.is_routine and item.importance_tier == 3 else 0
    source_reliability_bonus = item.credibility_weight * 3
    item.relevance_score = round(tier_base + recency + asset_bonus + market_bonus + source_reliability_bonus - routine_penalty, 4)
    return item


def analyze_news(items: list[NewsItem]) -> list[NewsItem]:
    return [analyze_news_item(item) for item in items]


def select_top_news(items: list[NewsItem], *, limit: int = 10, max_tier3: int = 2) -> list[NewsItem]:
    ranked = sorted(items, key=lambda item: (item.importance_tier, -item.relevance_score, item.published_at), reverse=False)
    selected: list[NewsItem] = []
    tier3_count = 0
    for item in ranked:
        if item.importance_tier == 3:
            if tier3_count >= max_tier3:
                continue
            tier3_count += 1
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def rank_news_by_importance(items: list[NewsItem]) -> list[NewsItem]:
    profile = load_yaml(CONFIG_DIR / "report_profile.yml")
    analyzed = analyze_news(items)
    top = select_top_news(
        analyzed,
        limit=int(profile.get("top_news_limit", 10)),
        max_tier3=int(profile.get("max_tier3_in_top_news", 2)),
    )
    top_urls = {item.url for item in top}
    rest = sorted((item for item in analyzed if item.url not in top_urls), key=lambda item: item.relevance_score, reverse=True)
    return top + rest


def policy_watch(items: list[NewsItem], limit: int = 10) -> list[NewsItem]:
    policies = [
        item
        for item in items
        if item.event_type in POLICY_EVENT_TYPES and item.importance_tier <= 2 and not item.is_routine
    ]
    return sorted(policies, key=lambda item: item.relevance_score, reverse=True)[:limit]


def background_materials(items: list[NewsItem], limit: int = 20) -> list[NewsItem]:
    background = [item for item in items if item.importance_tier == 3 or item.is_routine]
    return sorted(background, key=lambda item: item.published_at, reverse=True)[:limit]
