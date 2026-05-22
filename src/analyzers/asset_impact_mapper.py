from __future__ import annotations

import re
from typing import Any

from src.models import AssetImpact, NewsItem
from src.utils.config import load_yaml
from src.utils.paths import CONFIG_DIR

STRENGTH_RANK = {"low": 1, "medium": 2, "high": 3}


def _text(item: NewsItem) -> str:
    return f"{item.title} {item.summary}".lower()


def _contains(text: str, keyword: str) -> bool:
    keyword_lower = keyword.lower()
    if re.search(r"[\u4e00-\u9fff]", keyword_lower):
        return keyword_lower in text
    return re.search(rf"(?<!\w){re.escape(keyword_lower)}(?!\w)", text) is not None


def _rule_matches(text: str, rule: dict[str, Any]) -> bool:
    return any(_contains(text, keyword) for keyword in rule.get("keywords", []))


def _dedupe_impacts(impacts: list[AssetImpact]) -> list[AssetImpact]:
    by_asset: dict[str, AssetImpact] = {}
    for impact in impacts:
        current = by_asset.get(impact.asset)
        if not current or STRENGTH_RANK[impact.strength] > STRENGTH_RANK[current.strength]:
            by_asset[impact.asset] = impact
    return list(by_asset.values())


def _aggregate_direction(impacts: list[AssetImpact]) -> str:
    directions = {impact.direction for impact in impacts if impact.direction != "unknown"}
    if len(directions) == 1:
        return directions.pop()
    if directions:
        return "mixed"
    return "unknown"


def _aggregate_strength(impacts: list[AssetImpact]) -> str:
    if not impacts:
        return "low"
    return max((impact.strength for impact in impacts), key=lambda value: STRENGTH_RANK[value])


def map_news_item(item: NewsItem, rules_config: dict[str, Any] | None = None) -> NewsItem:
    rules_config = rules_config or load_yaml(CONFIG_DIR / "asset_impact_rules.yml")
    text = _text(item)
    impacts: list[AssetImpact] = []
    for rule in rules_config.get("rules", []):
        if not _rule_matches(text, rule):
            continue
        for raw_impact in rule.get("impacts", []):
            impacts.append(AssetImpact(**raw_impact))

    impacts = _dedupe_impacts(impacts)
    if not impacts and item.related_assets:
        impacts = [
            AssetImpact(
                asset=asset,
                direction="unknown",
                strength="low",
                reason="新闻提到该资产或主题，但公开信息不足以判断方向。",
            )
            for asset in item.related_assets
        ]

    item.asset_impacts = impacts
    item.related_assets = sorted({impact.asset for impact in impacts} | set(item.related_assets))
    item.impact_direction = _aggregate_direction(impacts)  # type: ignore[assignment]
    item.impact_strength = _aggregate_strength(impacts)  # type: ignore[assignment]
    return item


def map_asset_impacts(items: list[NewsItem]) -> list[NewsItem]:
    rules_config = load_yaml(CONFIG_DIR / "asset_impact_rules.yml")
    return [map_news_item(item, rules_config) for item in items]
