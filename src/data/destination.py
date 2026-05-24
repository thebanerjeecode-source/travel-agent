from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from src.data.base import Confidence, DataSource, ProviderResult, SourceType
from src.data.seeds import load_seed_json, normalize_city_key
from src.schemas import (
    AccommodationOption,
    AccommodationPlan,
    Attraction,
    DestinationResearch,
    InterCityLeg,
    Neighborhood,
    TransportPlan,
)


def _source(
    domain: str,
    provider: str,
    source: str,
    source_type: SourceType,
    confidence: Confidence,
) -> DataSource:
    return DataSource(
        domain=domain,
        provider=provider,
        source=source,
        source_type=source_type,
        confidence=confidence,
    )


class SeedDestinationProvider:
    name = "destination_seed"

    def fetch(self, *, city: str, interests: list[str] | None = None) -> Optional[ProviderResult]:
        seed = load_seed_json("destinations", city)
        if not seed:
            return None

        interests = interests or []
        interests_lower = [i.lower() for i in interests]

        neighborhoods = [
            Neighborhood(
                name=n["name"],
                fit_score=float(n.get("fit_score", 0.8)),
                reason=n.get("reason") or ", ".join(n.get("tags", [])),
            )
            for n in seed.get("neighborhoods", [])
        ]

        attractions_raw = seed.get("attractions", [])
        if interests_lower:
            filtered = [
                a
                for a in attractions_raw
                if any(
                    i in a.get("category", "").lower() or i in a.get("name", "").lower()
                    for i in interests_lower
                )
            ]
            if len(filtered) >= 2:
                attractions_raw = filtered

        attractions = [
            Attraction(
                name=a["name"],
                category=a.get("category", "sightseeing"),
                crowd_level=a.get("crowd_level", "medium"),
                best_time=a.get("best_time", ""),
                estimated_cost_usd=float(a.get("estimated_cost_usd", 0)),
            )
            for a in attractions_raw
        ]

        research = DestinationResearch(
            city=seed.get("city", city),
            neighborhoods=neighborhoods,
            attractions=attractions,
            food_highlights=seed.get("food_highlights", []),
        )

        return ProviderResult(
            data=research,
            source=_source(
                "destination",
                self.name,
                f"data/seeds/destinations/{normalize_city_key(city)}.json",
                "seed_file",
                "medium",
            ),
        )


class OpenTripMapProvider:
    name = "opentripmap"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENTRIPMAP_API_KEY")

    def fetch(self, *, city: str, interests: list[str] | None = None) -> Optional[ProviderResult]:
        if not self.api_key:
            return None

        seed = load_seed_json("destinations", city)
        coords = (seed or {}).get("coordinates")
        if not coords:
            return None

        lat, lon = coords["lat"], coords["lon"]
        url = (
            "https://api.opentripmap.com/0.1/en/places/radius?"
            + urllib.parse.urlencode(
                {
                    "radius": 8000,
                    "lon": lon,
                    "lat": lat,
                    "limit": 15,
                    "apikey": self.api_key,
                }
            )
        )

        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                payload = json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

        features = payload.get("features", [])
        if not features:
            return None

        category_map = {
            "historic": "history",
            "cultural": "culture",
            "religion": "temple",
            "foods": "food",
            "natural": "nature",
        }

        attractions: list[Attraction] = []
        for feat in features[:12]:
            props = feat.get("properties", {})
            name = props.get("name")
            if not name:
                continue
            kinds = props.get("kinds", "").split(",")
            category = "sightseeing"
            for kind in kinds:
                prefix = kind.split("_")[0] if "_" in kind else kind
                if prefix in category_map:
                    category = category_map[prefix]
                    break
            attractions.append(
                Attraction(
                    name=name,
                    category=category,
                    crowd_level="medium",
                    best_time="early morning",
                )
            )

        if not attractions:
            return None

        research = DestinationResearch(
            city=city,
            neighborhoods=[],
            attractions=attractions,
            food_highlights=[],
        )

        return ProviderResult(
            data=research,
            source=_source(
                "destination",
                self.name,
                "opentripmap.io/places/radius",
                "live_api",
                "high",
            ),
        )


def merge_destination_research(
    seed: DestinationResearch,
    live: DestinationResearch | None,
) -> DestinationResearch:
    if not live:
        return seed

    seen = {a.name.lower() for a in seed.attractions}
    merged_attractions = list(seed.attractions)
    for attr in live.attractions:
        if attr.name.lower() not in seen:
            merged_attractions.append(attr)
            seen.add(attr.name.lower())

    return DestinationResearch(
        city=seed.city,
        neighborhoods=seed.neighborhoods,
        attractions=merged_attractions[:15],
        food_highlights=seed.food_highlights or live.food_highlights,
    )
