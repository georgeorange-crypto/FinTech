from datetime import date

import src.main as main_module


def test_main_pipeline_continues_when_news_source_fails(monkeypatch, tmp_path) -> None:
    def boom():
        raise RuntimeError("source down")

    markdown_path = tmp_path / "brief.md"

    def fake_write_markdown(brief, warnings):
        markdown_path.write_text("brief", encoding="utf-8")
        return markdown_path

    monkeypatch.setattr(main_module, "collect_rss_news", boom)
    monkeypatch.setattr(main_module, "write_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "write_markdown_report", fake_write_markdown)
    monkeypatch.setattr(main_module, "render_html_report", lambda path: path.with_suffix(".html"))
    monkeypatch.setattr(main_module, "build_index", lambda: tmp_path / "index.html")

    brief = main_module.run_daily_brief(date(2026, 5, 22), only_news=True, no_llm=True)
    assert brief.date == date(2026, 5, 22)
    assert brief.top_news == []
