from datetime import date

from src.models import DailyBrief
from src.reports.markdown_report import build_markdown


def test_markdown_report_generation_not_empty() -> None:
    brief = DailyBrief(date=date(2026, 5, 22), executive_summary="测试总览")
    markdown = build_markdown(brief)
    assert "# Global Macro Morning Briefing - 2026-05-22" in markdown
    assert "非投资建议" in markdown
    assert "今日三大主线" in markdown
    assert "为什么重要" in markdown
    assert "市场状态" in markdown
    assert "背景材料" in markdown
    assert len(markdown) > 500
