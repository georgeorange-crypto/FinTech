from __future__ import annotations

import logging
import os

import requests
from bs4 import BeautifulSoup

from src.models import NewsItem

LOGGER = logging.getLogger(__name__)


def extractive_summary(text: str, max_chars: int = 180) -> str:
    clean = BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "..."


def summarize_news(items: list[NewsItem], *, no_llm: bool = False) -> list[NewsItem]:
    provider = os.getenv("LLM_PROVIDER")
    api_key = os.getenv("LLM_API_KEY")
    if no_llm or not provider or not api_key:
        for item in items:
            if not item.summary:
                item.summary = extractive_summary(item.title)
        return items

    if provider.lower() not in {"openai", "compatible"}:
        LOGGER.warning("Unsupported LLM_PROVIDER=%s; using fallback summaries", provider)
        return summarize_news(items, no_llm=True)

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    for item in items[:20]:
        prompt = (
            "请基于给定标题和摘要，用中文输出一句话摘要。必须区分事实、市场反应、可能影响，"
            "不得编造来源或加入没有证据的判断。\n"
            f"标题: {item.title}\n来源: {item.source}\n摘要: {item.summary}"
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是严谨的宏观新闻摘要助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 220,
        }
        try:
            raw = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            raw.raise_for_status()
            response = raw.json()
            item.summary = response["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("LLM summary failed source=%s title=%s error=%s", item.source, item.title, exc)
            item.summary = extractive_summary(item.summary or item.title)
    return items
