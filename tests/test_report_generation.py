from datetime import date

from src.models import DailyBrief
from src.reports.markdown_report import build_markdown


def test_report_contains_research_radar_sections() -> None:
    markdown = build_markdown(DailyBrief(date=date(2026, 5, 22), executive_summary="测试"))
    for phrase in ["今日三大主线", "为什么重要", "市场状态", "背景材料"]:
        assert phrase in markdown
