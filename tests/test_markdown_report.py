from datetime import date

from src.models import DailyBrief
from src.reports.markdown_report import build_markdown


def test_markdown_report_generation_not_empty() -> None:
    brief = DailyBrief(date=date(2026, 5, 22), executive_summary="测试总览")
    markdown = build_markdown(brief)
    assert "# Global Macro Morning Briefing - 2026-05-22" in markdown
    assert "非投资建议" in markdown
    assert len(markdown) > 500
