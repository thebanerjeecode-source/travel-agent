from __future__ import annotations

import json
import os
import re
from pathlib import Path

from src.data.base import DataMode

SEEDS_ROOT = Path(__file__).parent.parent.parent / "data" / "seeds"


def get_data_mode() -> DataMode:
    raw = os.getenv("DATA_MODE", "auto").lower().strip()
    try:
        return DataMode(raw)
    except ValueError:
        return DataMode.AUTO


def normalize_city_key(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", city.lower().strip()).strip("_")


def seed_path(category: str, city: str | None = None) -> Path:
    if city:
        return SEEDS_ROOT / category / f"{normalize_city_key(city)}.json"
    return SEEDS_ROOT / category


def load_seed_json(category: str, city: str | None = None) -> dict | None:
    path = seed_path(category, city)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_category_file(category: str, filename: str) -> dict | None:
    path = SEEDS_ROOT / category / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_seed_cities(category: str) -> list[str]:
    folder = SEEDS_ROOT / category
    if not folder.is_dir():
        return []
    return [p.stem for p in folder.glob("*.json") if p.name != "_schema.json"]
