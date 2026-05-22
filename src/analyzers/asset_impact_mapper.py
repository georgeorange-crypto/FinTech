from __future__ import annotations

import re

from src.models import NewsItem

KEYWORD_ASSET_RULES: list[tuple[tuple[str, ...], list[str], str, str]] = [
    (("inflation", "cpi", "pce"), ["DXY", "TLT", "IEF", "SPY", "QQQ", "GC=F", "BTC"], "mixed", "high"),
    (("rate cut", "dovish", "easing"), ["SPY", "QQQ", "TLT", "GC=F", "BTC"], "positive", "high"),
    (("rate hike", "hawkish", "tightening"), ["DXY", "TLT", "SPY", "QQQ", "BTC"], "mixed", "high"),
    (("oil", "opec", "middle east"), ["CL=F", "BZ=F", "energy equities"], "mixed", "medium"),
    (("china stimulus", "pboc", "reserve requirement", "rrr"), ["CSI300", "HSI", "CNH", "commodities"], "positive", "medium"),
    (("sec", "etf", "stablecoin"), ["BTC", "ETH", "COIN", "crypto market"], "mixed", "medium"),
    (("recession", "unemployment", "payrolls"), ["SPY", "QQQ", "TLT", "DXY", "GC=F"], "mixed", "high"),
    (("tariff", "sanctions"), ["SPY", "QQQ", "DXY", "CL=F", "CNH"], "mixed", "medium"),
]


def map_news_item(item: NewsItem) -> NewsItem:
    text = f"{item.title} {item.summary}".lower()
    assets: list[str] = []
    direction = "unknown"
    strength = "low"

    for keywords, mapped_assets, rule_direction, rule_strength in KEYWORD_ASSET_RULES:
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            assets.extend(mapped_assets)
            if rule_strength == "high" or strength == "low":
                direction = rule_direction
                strength = rule_strength

    item.related_assets = sorted(set(item.related_assets + assets))
    item.impact_direction = direction  # type: ignore[assignment]
    item.impact_strength = strength  # type: ignore[assignment]
    return item


def map_asset_impacts(items: list[NewsItem]) -> list[NewsItem]:
    return [map_news_item(item) for item in items]
