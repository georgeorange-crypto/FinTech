from __future__ import annotations

import argparse
import logging
from datetime import date

from bs4 import BeautifulSoup

from src.analyzers.llm_summarizer import summarize_news
from src.analyzers.market_narrative import build_market_narrative
from src.analyzers.news_importance import background_materials, policy_watch, select_top_news
from src.analyzers.news_ranker import rank_news
from src.charts.chart_builder import build_charts
from src.collectors.china_market_collector import collect_china_market_data
from src.collectors.crypto_collector import collect_crypto_data
from src.collectors.fred_collector import collect_fred_series
from src.collectors.market_collector import collect_market_data
from src.collectors.rss_collector import collect_rss_news
from src.collectors.sec_collector import collect_sec_filings
from src.models import DailyBrief, MarketSnapshot, NewsItem
from src.reports.html_report import render_html_report
from src.reports.index_builder import build_index
from src.reports.markdown_report import dynamic_learning_notes, write_markdown_report
from src.utils.config import load_yaml
from src.utils.history import append_history
from src.utils.json_io import write_json
from src.utils.logging import configure_logging
from src.utils.paths import CONFIG_DIR, INPUT_REPORTS_DIR, PROCESSED_DATA_DIR, dated_dir, ensure_dir
from src.utils.timezones import parse_run_date

LOGGER = logging.getLogger(__name__)
POLICY_CATEGORIES = {"central_banks", "china_policy", "us_policy", "crypto_policy"}


def _json_models(items: list) -> list[dict]:
    return [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in items]


def _top_themes(news: list[NewsItem]) -> list[str]:
    if not news:
        return ["暂无足够新闻形成明确主线"]
    themes = []
    for item in news:
        if item.importance_tier <= 2:
            themes.append(f"{item.event_type}: {item.title}")
        if len(themes) == 3:
            break
    return themes or [item.title for item in news[:3]]


def _summary_from_news(news: list[NewsItem], snapshots: list[MarketSnapshot], regime_summary: str) -> str:
    if not news and not snapshots:
        return "今日暂无足够可靠数据生成完整总览；系统已保留合规免责声明并记录失败数据源。"
    top_titles = "；".join(item.human_importance_reason for item in news[:2]) or "新闻数据有限"
    risk_assets = [snapshot for snapshot in snapshots if snapshot.symbol in {"SPY", "QQQ", "^VIX", "TLT", "GC=F", "CL=F", "BTC", "ETH"}]
    market_line = "；".join(
        f"{snapshot.symbol} 1D {snapshot.one_day_return * 100:.2f}%"
        for snapshot in risk_assets
        if snapshot.one_day_return is not None
    )
    market_line = market_line or "核心资产行情数据有限"
    return (
        f"今日晨报重点关注：{top_titles}。跨资产方面，{market_line}；{regime_summary}"
        "政策、通胀、利率、美元、美债、能源和加密监管仍是主要观察线索。"
        "所有结论仅基于公开数据与短摘要整理，不构成投资建议。"
    )


def _read_user_reports() -> list[str]:
    ensure_dir(INPUT_REPORTS_DIR)
    views: list[str] = []
    for path in sorted(INPUT_REPORTS_DIR.glob("*")):
        if path.is_dir():
            continue
        try:
            text = ""
            if path.suffix.lower() in {".md", ".txt"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
            elif path.suffix.lower() in {".html", ".htm"}:
                text = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser").get_text(" ", strip=True)
            elif path.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader

                    reader = PdfReader(str(path))
                    text = " ".join(page.extract_text() or "" for page in reader.pages[:5])
                except Exception as exc:  # noqa: BLE001
                    views.append(f"{path.name}: PDF 读取失败或缺少 pypdf，已跳过。原因：{exc}")
                    continue
            else:
                continue
            clean = " ".join(text.split())
            if clean:
                views.append(f"{path.name}: {clean[:260]}{'...' if len(clean) > 260 else ''}")
        except Exception as exc:  # noqa: BLE001
            views.append(f"{path.name}: 读取失败，原因：{exc}")
    return views


def _public_wall_street_views(news: list[NewsItem]) -> list[str]:
    views = []
    for item in news:
        if item.category == "wall_street_public":
            views.append(f"{item.source}: {item.title} - {item.summary or item.url}")
    views.extend(_read_user_reports())
    return views[:12]


def _calendar(sec_filings: list[dict[str, str]], fred_series: dict[str, list[dict[str, str]]]) -> list[str]:
    entries: list[str] = []
    entries.append("经济数据：暂无可靠公开日历数据；如配置经济日历源后可自动填充。")
    entries.append("央行讲话：暂无可靠公开日历数据；重点跟踪 Fed、ECB、BoJ、PBOC 官网 RSS。")
    if sec_filings:
        entries.append(f"财报：SEC watchlist 最近 7 天发现 {len(sec_filings)} 条 10-K/10-Q/8-K/20-F/6-K 披露。")
    else:
        entries.append("财报：暂无可靠数据。")
    if fred_series:
        entries.append(f"政策事件：FRED macro watch 已更新 {len(fred_series)} 个宏观序列。")
    else:
        entries.append("政策事件：暂无可靠数据。")
    entries.append("风险提醒：关注数据源失败项、突发地缘风险、利率和美元的二阶反应。")
    return entries


def run_daily_brief(
    run_date: date,
    *,
    no_llm: bool = False,
    only_market: bool = False,
    only_news: bool = False,
) -> DailyBrief:
    assets = load_yaml(CONFIG_DIR / "assets.yml")
    profile = load_yaml(CONFIG_DIR / "report_profile.yml")
    processed_dir = dated_dir(PROCESSED_DATA_DIR, run_date)
    warnings: list[str] = []
    frames = {}
    snapshots: list[MarketSnapshot] = []
    news: list[NewsItem] = []
    fred_series: dict[str, list[dict[str, str]]] = {}
    sec_filings: list[dict[str, str]] = []

    if not only_market:
        try:
            news = collect_rss_news()
            news = summarize_news(news, no_llm=no_llm)
            news = rank_news(news)
        except Exception as exc:  # noqa: BLE001
            warning = f"RSS/news pipeline failed: {exc}"
            LOGGER.warning(warning)
            warnings.append(warning)

    if not only_news:
        non_crypto_assets = {group: symbols for group, symbols in assets.items() if group not in {"CRYPTO", "CHINA_A_SHARE"}}
        market_frames, market_snapshots, market_warnings = collect_market_data(non_crypto_assets, run_date)
        frames.update(market_frames)
        snapshots.extend(market_snapshots)
        warnings.extend(market_warnings)

        crypto_frames, crypto_snapshots, crypto_warnings = collect_crypto_data(assets.get("CRYPTO", []), run_date)
        frames.update(crypto_frames)
        snapshots.extend(crypto_snapshots)
        warnings.extend(crypto_warnings)

        china_frames, china_snapshots, china_warnings = collect_china_market_data(assets.get("CHINA_A_SHARE", []), run_date)
        frames.update(china_frames)
        snapshots.extend(china_snapshots)
        warnings.extend(china_warnings)

        fred_series, fred_warnings = collect_fred_series(run_date)
        warnings.extend(fred_warnings)

        sec_filings, sec_warnings = collect_sec_filings(run_date)
        warnings.extend(sec_warnings)

    chart_paths = build_charts(frames, snapshots, run_date) if frames else {}
    market_narrative = build_market_narrative(snapshots)
    top_news = select_top_news(
        news,
        limit=int(profile.get("top_news_limit", 10)),
        max_tier3=int(profile.get("max_tier3_in_top_news", 2)),
    )
    policy_items = policy_watch(news)
    background_items = background_materials(news)
    top_themes = _top_themes(top_news)
    brief = DailyBrief(
        date=run_date,
        executive_summary=_summary_from_news(top_news, snapshots, market_narrative.summary_cn),
        market_overview=snapshots,
        top_news=top_news,
        policy_watch=policy_items,
        background_materials=background_items if profile.get("include_background_materials", True) else [],
        market_narrative=market_narrative,
        top_themes=top_themes,
        asset_charts=chart_paths,
        wall_street_public_views=_public_wall_street_views(news),
        today_calendar=_calendar(sec_filings, fred_series),
        learning_notes=dynamic_learning_notes(top_news),
        disclaimers=[
            "Not financial advice / 非投资建议。",
            "仅使用公开数据、公开 RSS 摘要和用户自有文件；不绕过任何付费墙。",
        ],
    )

    write_json(processed_dir / "news.json", _json_models(news))
    write_json(processed_dir / "news_analysis.json", _json_models(news))
    write_json(processed_dir / "events.json", _json_models(top_news + background_items))
    write_json(processed_dir / "market_narrative.json", market_narrative.model_dump(mode="json"))
    write_json(processed_dir / "market_snapshots.json", _json_models(snapshots))
    write_json(processed_dir / "fred_series.json", fred_series)
    write_json(processed_dir / "sec_filings.json", sec_filings)
    write_json(processed_dir / "warnings.json", warnings)
    write_json(processed_dir / "daily_brief.json", brief.model_dump(mode="json"))
    append_history(run_date.isoformat(), top_news + background_items, snapshots)

    markdown_path = write_markdown_report(brief, warnings)
    render_html_report(markdown_path)
    build_index()
    return brief


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate global macro morning brief.")
    parser.add_argument("--date", default="today", help="Run date: today or YYYY-MM-DD")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM summaries")
    parser.add_argument("--only-market", action="store_true", help="Collect only market data")
    parser.add_argument("--only-news", action="store_true", help="Collect only news data")
    parser.add_argument("--build-index", action="store_true", help="Only rebuild public/index.html")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    if args.only_market and args.only_news:
        raise SystemExit("--only-market and --only-news cannot be used together")
    if args.build_index:
        path = build_index()
        LOGGER.info("Index built: %s", path)
        return 0

    run_date = parse_run_date(args.date)
    LOGGER.info("Generating brief for %s", run_date.isoformat())
    brief = run_daily_brief(run_date, no_llm=args.no_llm, only_market=args.only_market, only_news=args.only_news)
    LOGGER.info("Generated brief date=%s news=%s markets=%s", brief.date, len(brief.top_news), len(brief.market_overview))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
