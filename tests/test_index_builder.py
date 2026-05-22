import json

import src.reports.index_builder as index_builder


def test_build_index_exports_pages_ready_static_site(monkeypatch, tmp_path) -> None:
    reports_dir = tmp_path / "reports"
    charts_dir = tmp_path / "charts"
    processed_dir = tmp_path / "data" / "processed"
    public_dir = tmp_path / "public"
    date_text = "2026-05-22"

    reports_dir.mkdir()
    (reports_dir / f"{date_text}.html").write_text(
        '<!doctype html><html><body><main><h1>Latest Report</h1><img src="../charts/2026-05-22/SPY.png"></main></body></html>',
        encoding="utf-8",
    )
    (charts_dir / date_text).mkdir(parents=True)
    (charts_dir / date_text / "SPY.png").write_bytes(b"png")
    (processed_dir / date_text).mkdir(parents=True)
    (processed_dir / date_text / "daily_brief.json").write_text(
        json.dumps(
            {
                "market_narrative": {"regime": "risk_on", "summary_cn": "风险偏好改善。"},
                "top_themes": ["theme one", "theme two", "theme three"],
            }
        ),
        encoding="utf-8",
    )
    (processed_dir / date_text / "market_snapshots.json").write_text(
        json.dumps([{"symbol": "SPY", "one_day_return": 0.01}]),
        encoding="utf-8",
    )

    monkeypatch.setattr(index_builder, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(index_builder, "CHARTS_DIR", charts_dir)
    monkeypatch.setattr(index_builder, "PROCESSED_DATA_DIR", processed_dir)
    monkeypatch.setattr(index_builder, "PUBLIC_DIR", public_dir)
    monkeypatch.setattr(index_builder, "ROOT", tmp_path)

    output = index_builder.build_index()
    html = output.read_text(encoding="utf-8")

    assert "Latest Report" in html
    assert 'src="charts/2026-05-22/SPY.png"' in html
    assert (public_dir / "reports" / f"{date_text}.html").exists()
    assert (public_dir / "charts" / date_text / "SPY.png").exists()
    assert (tmp_path / "index.html").exists()
    assert json.loads((public_dir / "metadata.json").read_text(encoding="utf-8"))["latest_report_href"] == "reports/2026-05-22.html"
