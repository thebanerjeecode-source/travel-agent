from __future__ import annotations

import os
from functools import lru_cache


@lru_cache
def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def get_api_secret() -> str | None:
    secret = os.getenv("API_SECRET", "").strip()
    return secret or None
