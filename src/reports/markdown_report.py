from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.models import DailyBrief, MarketSnapshot, NewsItem
from src.utils.paths import REPORTS_DIR, ensure_dir

CORE_CHARTS = ["SPY", "QQQ", "^VIX", "TLT", "GC=F", "CL=F", "BTC", "ETH", "^HSI", "沪深300", "上证指数"]


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:,.2f}"


def _market_tables(snapshots: list[MarketSnapshot]) -> str:
    groups: dict[str, list[MarketSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        groups[snapshot.group].append(snapshot)
    sections: list[str] = []
    for group, rows in groups.items():
        sections.append(f"### {group}\n")
        sections.append("| symbol | latest close | 1D | 5D | 1M | YTD | trend |")
        sections.append("|---|---:|---:|---:|---:|---:|---|")
        for row in rows:
            sections.append(
                f"| {row.symbol} | {_num(row.latest_close)} | {_pct(row.one_day_return)} | "
                f"{_pct(row.five_day_return)} | {_pct(row.one_month_return)} | {_pct(row.ytd_return)} | {row.trend_label} |"
            )
        sections.append("")
    return "\n".join(sections) if sections else "暂无可靠市场数据。\n"


def _news_block(items: list[NewsItem]) -> str:
    if not items:
        return "暂无可靠数据。\n"
    lines: list[str] = []
    for idx, item in enumerate(items, start=1):
        lines.append(f"### {idx}. {item.title}")
        lines.append(f"- 来源：{item.source}")
        lines.append(f"- 时间：{item.published_at.isoformat()}")
        lines.append(f"- 链接：[{item.url}]({item.url})")
        lines.append(f"- 一句话摘要：{item.summary or '暂无摘要'}")
        lines.append(f"- 为什么重要：相关性评分 {item.relevance_score:.2f}，类别 {item.category}，地区 {item.region}。")
        lines.append(f"- 相关资产：{', '.join(item.related_assets) if item.related_assets else '未知'}")
        lines.append(f"- 影响方向与强度：{item.impact_direction} / {item.impact_strength}")
        lines.append("")
    return "\n".join(lines)


def _chart_block(chart_paths: dict[str, str]) -> str:
    lines: list[str] = []
    for symbol in CORE_CHARTS:
        path = chart_paths.get(symbol)
        if path:
            chart_path = Path(path)
            relative = os.path.relpath(chart_path, REPORTS_DIR).replace("\\", "/") if chart_path.is_absolute() else chart_path.as_posix()
            lines.append(f"### {symbol}")
            lines.append(f"![{symbol}]({relative})")
            lines.append("")
    return "\n".join(lines) if lines else "暂无可靠图表数据。\n"


def default_learning_notes() -> list[dict[str, str]]:
    return [
        {
            "term": "soft landing",
            "zh": "软着陆，指经济在通胀回落时避免明显衰退。",
            "example": "Investors are pricing in a soft landing as inflation cools.",
        },
        {
            "term": "yield curve steepening",
            "zh": "收益率曲线变陡，通常指长端利率相对短端上升。",
            "example": "A steepening yield curve can reflect stronger growth expectations.",
        },
        {
            "term": "risk-off",
            "zh": "避险模式，资金偏向债券、美元、黄金等防御资产。",
            "example": "Markets turned risk-off after weaker payroll data.",
        },
        {
            "term": "real yield",
            "zh": "实际收益率，名义利率扣除通胀预期后的收益率。",
            "example": "Gold often reacts to moves in real yields.",
        },
        {
            "term": "liquidity",
            "zh": "流动性，既可指市场交易深度，也可指宏观资金环境。",
            "example": "Tighter liquidity can weigh on high-duration assets.",
        },
        {
            "term": "credit spread",
            "zh": "信用利差，企业债收益率相对国债的额外补偿。",
            "example": "Widening credit spreads may signal rising default concerns.",
        },
    ]


def build_markdown(brief: DailyBrief, warnings: list[str] | None = None) -> str:
    warnings = warnings or []
    policy_items = brief.policy_watch[:10]
    wall_street = brief.wall_street_public_views or ["暂无可靠公开机构观点；不会绕过付费墙。"]
    calendar = brief.today_calendar or ["暂无可靠数据。"]
    learning = brief.learning_notes or default_learning_notes()
    generated_at = datetime.now().isoformat(timespec="seconds")

    lines = [
        f"# Global Macro Morning Briefing - {brief.date.isoformat()}",
        "",
        "> 非投资建议，仅供学习、研究与信息整理。Not financial advice.",
        "",
        "## 0. 一句话总览",
        brief.executive_summary,
        "",
        "## 1. 隔夜跨资产市场",
        _market_tables(brief.market_overview),
        "## 2. 今日最重要的 10 条新闻",
        _news_block(brief.top_news[:10]),
        "## 3. 政策与央行观察",
        _news_block(policy_items),
        "## 4. 核心图表",
        _chart_block(brief.asset_charts),
        "## 5. 华尔街与机构公开观点",
        "\n".join(f"- {view}" for view in wall_street),
        "",
        "## 6. 今日重点关注",
        "\n".join(f"- {item}" for item in calendar),
        "",
        "## 7. 英文金融表达与宏观概念",
    ]
    for note in learning[:6]:
        lines.append(f"- **{note['term']}**：{note['zh']} 例句：{note['example']}")
    lines.extend(
        [
            "",
            "## 8. 数据源与免责声明",
            f"- 采集时间：{generated_at}",
            "- 数据源：公开 RSS、Yahoo Finance、CoinGecko、AKShare、FRED、SEC data.sec.gov，以及用户自有 inputs/reports 文件。",
            "- 合规说明：不绕过 WSJ、Bloomberg、FT、Reuters 等付费墙；对付费媒体只使用公开 RSS 标题、摘要、链接和发布时间。",
            "- 免责声明：Not financial advice / 非投资建议。本项目仅供个人学习、研究和信息整理，不构成投资建议、交易建议或任何收益承诺。",
        ]
    )
    if warnings:
        lines.append("- 失败或跳过的数据源：")
        for warning in warnings:
            lines.append(f"  - {warning}")
    return "\n".join(lines).strip() + "\n"


def write_markdown_report(brief: DailyBrief, warnings: list[str] | None = None) -> Path:
    ensure_dir(REPORTS_DIR)
    path = REPORTS_DIR / f"{brief.date.isoformat()}.md"
    path.write_text(build_markdown(brief, warnings), encoding="utf-8")
    return path
