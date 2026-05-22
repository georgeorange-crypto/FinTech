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


def _snapshot(snapshots: list[MarketSnapshot], symbol: str) -> MarketSnapshot | None:
    return next((snapshot for snapshot in snapshots if snapshot.symbol == symbol), None)


def _market_readthrough(snapshots: list[MarketSnapshot], brief: DailyBrief) -> str:
    spy = _snapshot(snapshots, "SPY")
    qqq = _snapshot(snapshots, "QQQ")
    tlt = _snapshot(snapshots, "TLT")
    dxy = _snapshot(snapshots, "DX-Y.NYB")
    gold = _snapshot(snapshots, "GC=F")
    oil = _snapshot(snapshots, "CL=F")
    btc = _snapshot(snapshots, "BTC")
    eth = _snapshot(snapshots, "ETH")
    hsi = _snapshot(snapshots, "^HSI")
    csi = _snapshot(snapshots, "沪深300") or _snapshot(snapshots, "上证指数")
    return "\n".join(
        [
            f"- 美股：SPY 1D {_pct(spy.one_day_return if spy else None)}，QQQ 1D {_pct(qqq.one_day_return if qqq else None)}，整体趋势需结合 VIX 和利率确认。",
            f"- 美债/美元：TLT 1D {_pct(tlt.one_day_return if tlt else None)}，美元指数 1D {_pct(dxy.one_day_return if dxy else None)}，是判断折现率压力的核心线索。",
            f"- 黄金/原油：黄金 1D {_pct(gold.one_day_return if gold else None)}，原油 1D {_pct(oil.one_day_return if oil else None)}，用于观察避险、通胀和地缘风险。",
            f"- 加密：BTC 1D {_pct(btc.one_day_return if btc else None)}，ETH 1D {_pct(eth.one_day_return if eth else None)}，关注是否独立于纳指走出加密自身行情。",
            f"- 港股/A股：恒生 1D {_pct(hsi.one_day_return if hsi else None)}，沪深300/上证 1D {_pct(csi.one_day_return if csi else None)}，重点看中国政策预期与人民币线索。",
            f"- 风险观察：{'; '.join(brief.market_narrative.watch_points)}",
        ]
    )


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


def _asset_impacts_block(item: NewsItem) -> list[str]:
    if not item.asset_impacts:
        return ["  - 资产：暂无明确资产映射", "  - 方向：unknown", "  - 强度：low", "  - 原因：公开信息不足以判断方向。"]
    lines: list[str] = []
    for impact in item.asset_impacts[:6]:
        lines.extend(
            [
                f"  - 资产：{impact.asset}",
                f"    方向：{impact.direction}",
                f"    强度：{impact.strength}",
                f"    原因：{impact.reason}",
            ]
        )
    return lines


def _news_block(items: list[NewsItem]) -> str:
    if not items:
        return "暂无可靠数据。\n\n- 为什么重要：没有可靠新闻时，不应为了填充版面编造市场解释。\n"
    lines: list[str] = []
    for idx, item in enumerate(items, start=1):
        lines.append(f"### {idx}. {item.title}")
        lines.append(f"- 来源：{item.source}")
        lines.append(f"- 时间：{item.published_at.isoformat()}")
        lines.append(f"- 地区：{item.region}")
        lines.append(f"- 事件类型：{item.event_type}")
        lines.append(f"- 重要性层级：Tier {item.importance_tier}")
        lines.append(f"- 一句话摘要：{item.summary or '暂无摘要'}")
        lines.append(f"- 为什么重要：{item.human_importance_reason}")
        lines.append(f"- 可能影响：{item.expected_market_impact}")
        lines.extend(_asset_impacts_block(item))
        lines.append(f"- 原文链接：[{item.url}]({item.url})")
        lines.append("")
    return "\n".join(lines)


def _background_block(items: list[NewsItem]) -> str:
    if not items:
        return "暂无背景材料。\n"
    lines = []
    for item in items[:20]:
        lines.append(f"- [{item.title}]({item.url})（{item.source}，{item.event_type}）：{item.summary or '暂无摘要'}")
    return "\n".join(lines) + "\n"


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


def dynamic_learning_notes(news: list[NewsItem]) -> list[dict[str, str]]:
    text = " ".join(f"{item.title} {item.summary}".lower() for item in news)
    candidates = [
        ("inflation expectations", "通胀预期，指家庭、企业或市场对未来通胀的预估。", "Inflation expectations can shape wage bargaining and bond yields.", ["inflation", "cpi", "pce"]),
        ("real yield", "实际收益率，名义利率扣除通胀预期后的收益率。", "Gold often reacts more to real yields than nominal yields.", ["inflation", "treasury", "gold"]),
        ("terminal rate", "终端利率，市场预期本轮加息周期的最高政策利率。", "A higher terminal rate can pressure growth stocks.", ["fomc", "rate hike", "hawkish"]),
        ("soft landing", "软着陆，指通胀回落而经济避免明显衰退。", "Markets often rally when data support a soft landing.", ["payrolls", "unemployment", "gdp"]),
        ("risk-off", "避险模式，资金偏向美元、国债、黄金等防御资产。", "A geopolitical shock can push markets into risk-off mode.", ["war", "sanctions", "vix"]),
        ("supply disruption", "供给扰动，通常指能源或商品供应受冲突、减产或天气影响。", "Supply disruption can lift oil prices and inflation expectations.", ["oil", "opec", "middle east"]),
        ("market structure", "市场结构，指交易、托管、清算、ETF、监管等制度安排。", "Crypto market structure rules can affect institutional participation.", ["sec", "etf", "stablecoin"]),
        ("AI capex", "AI 资本开支，指云厂商和科技公司投入 AI 基建的支出。", "AI capex guidance can move semiconductor stocks.", ["ai capex", "nvidia", "microsoft"]),
    ]
    selected = [item for item in candidates if any(keyword in text for keyword in item[3])]
    if len(selected) < 6:
        selected.extend(item for item in candidates if item not in selected)
    return [{"term": term, "zh": zh, "example": example} for term, zh, example, _ in selected[:6]]


def default_learning_notes() -> list[dict[str, str]]:
    return dynamic_learning_notes([])


def _calendar_block(items: list[str]) -> str:
    values = items or ["暂无可靠数据。"]
    labels = ["经济数据", "央行讲话", "财报", "政策事件", "风险提醒"]
    lines = []
    for label in labels:
        matched = [item for item in values if label in item]
        lines.append(f"- {label}：{matched[0] if matched else '暂无可靠数据'}")
    return "\n".join(lines)


def build_markdown(brief: DailyBrief, warnings: list[str] | None = None) -> str:
    warnings = warnings or []
    wall_street = brief.wall_street_public_views or ["暂无可靠公开观点。"]
    learning = brief.learning_notes or dynamic_learning_notes(brief.top_news)
    generated_at = datetime.now().isoformat(timespec="seconds")
    themes = brief.top_themes or [item.title for item in brief.top_news[:3]] or ["暂无足够新闻形成明确主线"]

    lines = [
        f"# Global Macro Morning Briefing - {brief.date.isoformat()}",
        "",
        "> Not financial advice / 非投资建议。",
        "",
        "## 0. 今日总览",
        f"- 市场状态：{brief.market_narrative.regime}。{brief.market_narrative.summary_cn}",
        "- 今日三大主线：",
    ]
    for idx, theme in enumerate(themes[:3], start=1):
        lines.append(f"  {idx}. {theme}")
    lines.extend(
        [
            f"- 一句话结论：{brief.executive_summary}",
            "",
            "## 1. 隔夜跨资产市场",
            _market_readthrough(brief.market_overview, brief),
            "",
            _market_tables(brief.market_overview),
            "## 2. 今日最重要的 10 条新闻",
            _news_block(brief.top_news[:10]),
            "## 3. 政策与央行观察",
            _news_block(brief.policy_watch),
            "## 4. 市场异动与图表",
            "\n".join(f"- {move}" for move in brief.market_narrative.key_moves),
            "",
        ]
    )
    if brief.market_narrative.contradictions:
        lines.append("### 信号矛盾")
        lines.extend(f"- {item}" for item in brief.market_narrative.contradictions)
        lines.append("")
    lines.extend(
        [
            _chart_block(brief.asset_charts),
            "## 5. 华尔街与机构公开观点",
            "\n".join(f"- {view}" for view in wall_street),
            "",
            "## 6. 今日重点关注",
            _calendar_block(brief.today_calendar),
            "",
            "## 7. 英文金融表达与宏观概念",
        ]
    )
    for note in learning[:6]:
        lines.append(f"- **{note['term']}**：{note['zh']} 例句：{note['example']}")
    lines.extend(
        [
            "",
            "## 8. 背景材料",
            _background_block(brief.background_materials),
            "## 9. 数据源、失败项与免责声明",
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
