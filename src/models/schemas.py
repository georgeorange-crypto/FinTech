from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ImpactDirection = Literal["positive", "negative", "mixed", "unknown"]
ImpactStrength = Literal["low", "medium", "high"]
TrendLabel = Literal["strong_uptrend", "uptrend", "range_bound", "downtrend", "strong_downtrend"]


class NewsItem(BaseModel):
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    url: str = Field(min_length=1)
    published_at: datetime
    region: str = "global"
    category: str = "general"
    language: str = "en"
    summary: str = ""
    credibility_weight: float = Field(default=0.5, ge=0, le=1)
    relevance_score: float = Field(default=0, ge=0)
    related_assets: list[str] = Field(default_factory=list)
    impact_direction: ImpactDirection = "unknown"
    impact_strength: ImpactStrength = "low"

    @field_validator("title", "source", "url")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be blank")
        return value


class MarketBar(BaseModel):
    symbol: str
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: float | None = None
    source: str


class MarketSnapshot(BaseModel):
    symbol: str
    name: str
    group: str
    latest_close: float | None = None
    one_day_return: float | None = None
    five_day_return: float | None = None
    one_month_return: float | None = None
    ytd_return: float | None = None
    volatility_20d: float | None = None
    ma_20: float | None = None
    ma_60: float | None = None
    rsi_14: float | None = None
    trend_label: TrendLabel = "range_bound"


class DailyBrief(BaseModel):
    date: date
    executive_summary: str
    market_overview: list[MarketSnapshot] = Field(default_factory=list)
    top_news: list[NewsItem] = Field(default_factory=list)
    policy_watch: list[NewsItem] = Field(default_factory=list)
    asset_charts: dict[str, str] = Field(default_factory=dict)
    wall_street_public_views: list[str] = Field(default_factory=list)
    today_calendar: list[str] = Field(default_factory=list)
    learning_notes: list[dict[str, str]] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
