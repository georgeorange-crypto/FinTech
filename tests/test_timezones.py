from src.utils.timezones import get_local_today, parse_run_date


def test_parse_today_uses_asia_taipei_by_default() -> None:
    assert parse_run_date("today") == get_local_today("Asia/Taipei")


def test_parse_explicit_date() -> None:
    assert parse_run_date("2026-05-22").isoformat() == "2026-05-22"
