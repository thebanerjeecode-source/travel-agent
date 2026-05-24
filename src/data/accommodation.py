from __future__ import annotations

from typing import Optional

from src.data.base import DataSource, ProviderResult, SourceType
from src.data.seeds import load_seed_json, normalize_city_key
from src.schemas import AccommodationOption, AccommodationPlan, TravelStyle


class SeedAccommodationProvider:
    name = "accommodation_seed"

    def fetch(
        self,
        *,
        city: str,
        nights: int,
        travel_style: TravelStyle,
        budget_usd: float,
        duration_days: int,
    ) -> Optional[ProviderResult]:
        seed = load_seed_json("accommodation", city)
        if not seed:
            return None

        tier = travel_style.value
        nightly_ceiling = (budget_usd * 0.35) / max(nights, 1)

        neighborhoods = seed.get("neighborhoods", [])
        best_hood = neighborhoods[0]["name"] if neighborhoods else city
        hood_reason = ", ".join(neighborhoods[0].get("pros", [])) if neighborhoods else ""

        tier_props = [p for p in seed.get("properties", []) if p.get("tier") == tier]
        options: list[AccommodationOption] = []
        for prop in tier_props:
            price = float(prop.get("price_per_night_usd", 0))
            if price <= nightly_ceiling * 1.2:
                options.append(
                    AccommodationOption(
                        name=prop["name"],
                        price_per_night_usd=price,
                        tier=prop.get("tier", "mid-range"),
                    )
                )

        if not options:
            for prop in tier_props[:3]:
                options.append(
                    AccommodationOption(
                        name=prop["name"],
                        price_per_night_usd=float(prop.get("price_per_night_usd", 0)),
                        tier=prop.get("tier", "mid-range"),
                    )
                )

        plan = AccommodationPlan(
            city=seed.get("city", city),
            nights=nights,
            recommended_neighborhood=best_hood,
            reason=hood_reason or f"Recommended area for a {tier} stay",
            options=options[:3],
        )

        return ProviderResult(
            data=plan,
            source=DataSource(
                domain="accommodation",
                provider=self.name,
                source=f"data/seeds/accommodation/{normalize_city_key(city)}.json",
                source_type="seed_file",
                confidence="medium",
            ),
        )
