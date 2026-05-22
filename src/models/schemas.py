from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ImpactDirection = Literal["positive", "negative", "mixed", "unknown"]
ImpactStrength = Literal["low", "medium", "high"]
TrendLabel = Literal["strong_uptrend", "uptrend", "range_bound", "downtrend", "strong_downtrend"]
EventType = Literal[
    "macro_data",
    "central_bank_decision",
    "central_bank_speech",
    "fiscal_policy",
    "regulation",
    "geopolitical_risk",
    "earnings",
    "commodity_supply",
    "crypto_market_structure",
    "financial_stability",
    "research_publication",
    "routine_announcement",
    "other",
]
AssetClass = Literal["equity", "rates", "fx", "commodity", "crypto", "credit", "multi_asset", "unknown"]
MarketRegime = Literal[
    "risk_on",
    "risk_off",
    "rates_shock",
    "inflation_shock",
    "dollar_liquidity_tightening",
    "crypto_specific",
    "mixed",
    "unknown",
]


class AssetImpact(BaseModel):
    asset: str
    asset_class: AssetClass = "unknown"
    direction: ImpactDirection = "unknown"
    strength: ImpactStrength = "low"
    reason: str = "信息不足以判断方向。"


class NewsAnalysis(BaseModel):
    title: str
    source: str
    url: str
    published_at: datetime
    event_type: EventType = "other"
    importance_tier: Literal[1, 2, 3] = 3
    human_importance_reason: str = "这条信息目前更适合作为背景材料跟踪。"
    expected_market_impact: str = "公开信息不足以判断明确市场方向。"
    affected_regions: list[str] = Field(default_factory=list)
    affected_asset_classes: list[AssetClass] = Field(default_factory=list)
    asset_impacts: list[AssetImpact] = Field(default_factory=list)
    is_routine: bool = False
    is_market_moving: bool = False


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
    asset_impacts: list[AssetImpact] = Field(default_factory=list)
    event_type: EventType = "other"
    importance_tier: Literal[1, 2, 3] = 3
    human_importance_reason: str = "这条信息目前更适合作为背景材料跟踪。"
    expected_market_impact: str = "公开信息不足以判断明确市场方向。"
    affected_regions: list[str] = Field(default_factory=list)
    affected_asset_classes: list[AssetClass] = Field(default_factory=list)
    is_routine: bool = False
    is_market_moving: bool = False

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


class MarketNarrative(BaseModel):
    regime: MarketRegime = "unknown"
    summary_cn: str = "市场信号不足，暂不判断明确状态。"
    key_moves: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    watch_points: list[str] = Field(default_factory=list)


class DailyBrief(BaseModel):
    date: date
    executive_summary: str
    market_overview: list[MarketSnapshot] = Field(default_factory=list)
    top_news: list[NewsItem] = Field(default_factory=list)
    policy_watch: list[NewsItem] = Field(default_factory=list)
    background_materials: list[NewsItem] = Field(default_factory=list)
    market_narrative: MarketNarrative = Field(default_factory=MarketNarrative)
    top_themes: list[str] = Field(default_factory=list)
    asset_charts: dict[str, str] = Field(default_factory=dict)
    wall_street_public_views: list[str] = Field(default_factory=list)
    today_calendar: list[str] = Field(default_factory=list)
    learning_notes: list[dict[str, str]] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
