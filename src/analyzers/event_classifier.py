from __future__ import annotations

import re
from typing import Any, cast

from src.models import NewsItem
from src.models.schemas import EventType
from src.utils.config import load_yaml
from src.utils.paths import CONFIG_DIR

MAJOR_THEME_KEYWORDS = {
    "inflation",
    "cpi",
    "pce",
    "fomc",
    "rate cut",
    "rate hike",
    "qe",
    "qt",
    "stimulus",
    "tariff",
    "sanctions",
    "war",
    "opec",
    "oil supply",
    "sec crypto etf",
    "stablecoin bill",
    "ai capex",
}


def _text(item: NewsItem) -> str:
    return f"{item.title} {item.summary}".lower()


def _contains(text: str, keyword: str) -> bool:
    keyword_lower = keyword.lower()
    if re.search(r"[\u4e00-\u9fff]", keyword_lower):
        return keyword_lower in text
    return re.search(rf"(?<!\w){re.escape(keyword_lower)}(?!\w)", text) is not None


def _rule_matches(text: str, rule: dict[str, Any]) -> bool:
    return any(_contains(text, keyword) for keyword in rule.get("keywords", []))


def classify_event(item: NewsItem, rules_config: dict[str, Any] | None = None) -> NewsItem:
    rules_config = rules_config or load_yaml(CONFIG_DIR / "importance_rules.yml")
    text = _text(item)
    matched_rule: dict[str, Any] | None = None
    for rule in rules_config.get("rules", []):
        if _rule_matches(text, rule):
            matched_rule = rule
            break

    if matched_rule:
        event_type = cast(EventType, matched_rule.get("event_type", "other"))
        tier = int(matched_rule.get("tier", 3))
        is_routine = bool(matched_rule.get("is_routine", False))
        is_market_moving = bool(matched_rule.get("is_market_moving", tier <= 2))
        reason = str(matched_rule.get("reason", "这条信息可能影响相关资产预期。"))
    else:
        event_type = "other"
        tier = 3
        is_routine = False
        is_market_moving = False
        reason = "这条信息暂未匹配到重大宏观、政策或市场事件，更适合作为背景跟踪。"

    if is_routine and any(keyword in text for keyword in MAJOR_THEME_KEYWORDS):
        tier = min(tier, 2)
        is_market_moving = True
        reason = f"{reason} 但标题或摘要同时涉及重大市场主题，因此提升为重要跟踪项。"

    item.event_type = event_type
    item.importance_tier = cast(Any, max(1, min(tier, 3)))
    item.is_routine = is_routine
    item.is_market_moving = is_market_moving
    item.affected_regions = sorted({item.region, *matched_rule.get("regions", [])}) if matched_rule else [item.region]
    item.human_importance_reason = reason
    return item


def classify_events(items: list[NewsItem]) -> list[NewsItem]:
    rules_config = load_yaml(CONFIG_DIR / "importance_rules.yml")
    return [classify_event(item, rules_config) for item in items]
