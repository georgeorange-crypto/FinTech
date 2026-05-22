from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone

from src.utils.config import load_yaml
from src.utils.http import request_json
from src.utils.json_io import write_json
from src.utils.paths import CONFIG_DIR, RAW_DATA_DIR, dated_dir

LOGGER = logging.getLogger(__name__)

FORMS = {"10-K", "10-Q", "8-K", "20-F", "6-K"}


def collect_sec_filings(run_date: date) -> tuple[list[dict[str, str]], list[str]]:
    config_path = CONFIG_DIR / "watchlist_cik.yml"
    if not config_path.exists():
        return [], ["watchlist_cik.yml not found; skipping SEC filings"]

    user_agent = os.getenv("SEC_USER_AGENT", "global-macro-morning-brief contact@example.com")
    companies = load_yaml(config_path).get("companies", [])
    cutoff = datetime.combine(run_date - timedelta(days=7), datetime.min.time(), tzinfo=timezone.utc)
    filings: list[dict[str, str]] = []
    warnings: list[str] = []

    for company in companies:
        cik = str(company["cik"]).zfill(10)
        payload = request_json(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
            timeout=20,
            retries=3,
        )
        if not payload:
            warnings.append(f"SEC failed cik={cik}")
            continue
        recent = payload.get("filings", {}).get("recent", {})
        for form, filed_at, accession in zip(
            recent.get("form", []),
            recent.get("filingDate", []),
            recent.get("accessionNumber", []),
            strict=False,
        ):
            if form not in FORMS:
                continue
            filed_dt = datetime.fromisoformat(filed_at).replace(tzinfo=timezone.utc)
            if filed_dt < cutoff:
                continue
            accession_clean = accession.replace("-", "")
            filings.append(
                {
                    "company": company.get("name", cik),
                    "cik": cik,
                    "form": form,
                    "filed_at": filed_at,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/",
                }
            )

    write_json(dated_dir(RAW_DATA_DIR / "sec", run_date) / "filings.json", filings)
    return filings, warnings
