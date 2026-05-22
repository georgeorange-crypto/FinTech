from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
from bs4 import BeautifulSoup

from src.analyzers.news_ranker import HIGH_FREQUENCY_KEYWORDS
from src.models import NewsItem
from src.utils.config import load_yaml
from src.utils.paths import CONFIG_DIR

LOGGER = logging.getLogger(__name__)


def _parse_datetime(entry: Any) -> datetime:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                parsed = parsedate_to_datetime(value)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except Exception:  # noqa: BLE001
                continue
    if entry.get("published_parsed"):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _clean_html(value: str | None) -> str:
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def _dedupe_key(item: NewsItem) -> str:
    raw = item.url.strip().lower() or item.title.strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _keyword_related(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in HIGH_FREQUENCY_KEYWORDS)


def collect_rss_news(config_path=None, *, lookback_hours: int = 48) -> list[NewsItem]:
    config_path = config_path or CONFIG_DIR / "rss_feeds.yml"
    config = load_yaml(config_path)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    items: list[NewsItem] = []
    seen: set[str] = set()

    for category, feeds in config.items():
        for feed in feeds or []:
            try:
                parsed = feedparser.parse(feed["url"])
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("RSS fetch failed source=%s error=%s", feed.get("name"), exc)
                continue
            if getattr(parsed, "bozo", False):
                LOGGER.warning("RSS parse warning source=%s detail=%s", feed.get("name"), parsed.get("bozo_exception"))

            for entry in parsed.entries:
                published_at = _parse_datetime(entry)
                if published_at.astimezone(timezone.utc) < cutoff:
                    continue
                title = _clean_html(entry.get("title")) or "Untitled"
                summary = _clean_html(entry.get("summary") or entry.get("description"))
                text = f"{title} {summary}"
                if not _keyword_related(text) and category not in {"central_banks", "china_policy", "us_policy"}:
                    continue
                try:
                    item = NewsItem(
                        title=title,
                        source=feed.get("name", "Unknown"),
                        url=entry.get("link") or feed["url"],
                        published_at=published_at,
                        region=feed.get("region", "global"),
                        category=feed.get("category", category),
                        language=feed.get("language", "en"),
                        summary=summary,
                        credibility_weight=float(feed.get("credibility_weight", 0.5)),
                    )
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("Invalid RSS item source=%s error=%s", feed.get("name"), exc)
                    continue
                key = _dedupe_key(item)
                title_key = hashlib.sha256(item.title.lower().encode("utf-8")).hexdigest()
                if key in seen or title_key in seen:
                    continue
                seen.add(key)
                seen.add(title_key)
                items.append(item)
    return items


def dedupe_news(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    deduped: list[NewsItem] = []
    for item in items:
        key = _dedupe_key(item)
        title_key = hashlib.sha256(item.title.lower().encode("utf-8")).hexdigest()
        if key in seen or title_key in seen:
            continue
        seen.add(key)
        seen.add(title_key)
        deduped.append(item)
    return deduped
