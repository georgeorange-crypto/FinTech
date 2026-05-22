from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def request_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 20,
    retries: int = 3,
) -> Any | None:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            LOGGER.warning("Request failed (%s/%s) url=%s error=%s", attempt, retries, url, exc)
            time.sleep(min(2 * attempt, 6))
    LOGGER.warning("Request exhausted url=%s error=%s", url, last_error)
    return None
