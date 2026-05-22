from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def flatten_assets(config: dict[str, list[str]]) -> list[tuple[str, str]]:
    return [(group, symbol) for group, symbols in config.items() for symbol in symbols]
