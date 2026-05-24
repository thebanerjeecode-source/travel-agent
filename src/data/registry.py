from __future__ import annotations

import json
from typing import Optional

from src.context import TripContext
from src.data.accommodation import SeedAccommodationProvider
from src.data.base import DataMode, DataSource, ProviderResult
from src.data.budget import BudgetBenchmarksProvider
from src.data.destination import (
    OpenTripMapProvider,
    SeedDestinationProvider,
    merge_destination_research,
)
from src.data.seeds import get_data_mode
from src.data.transport import SeedTransportProvider
from src.schemas import AccommodationPlan, DestinationResearch, TransportPlan


class DataRegistry:
    """Central registry for Phase 4 data providers with fallback chains."""

    def __init__(self, mode: DataMode | None = None) -> None:
        self.mode = mode or get_data_mode()
        self.destination_seed = SeedDestinationProvider()
        self.destination_live = OpenTripMapProvider()
        self.accommodation_seed = SeedAccommodationProvider()
        self.transport_seed = SeedTransportProvider()
        self.budget = BudgetBenchmarksProvider()
        self.sources: list[DataSource] = []

    def enabled(self) -> bool:
        return self.mode != DataMode.SEED or True  # seeds always usable

    def record(self, result: ProviderResult | None) -> None:
        if result:
            self.sources.append(result.source)

    def provenance_summary(self) -> dict[str, str]:
        summary: dict[str, str] = {}
        for src in self.sources:
            existing = summary.get(src.domain, "")
            label = src.provider.replace("_", " ")
            summary[src.domain] = f"{existing} + {label}".strip(" + ") if existing else label
        return summary

    def fetch_destination(self, city: str, interests: list[str]) -> Optional[ProviderResult]:
        seed_result = self.destination_seed.fetch(city=city, interests=interests)
        live_result = None

        if self.mode in (DataMode.LIVE, DataMode.AUTO):
            live_result = self.destination_live.fetch(city=city, interests=interests)

        if seed_result and live_result:
            merged = merge_destination_research(seed_result.data, live_result.data)
            combined = ProviderResult(
                data=merged,
                source=live_result.source,
            )
            combined.source.provider = f"{seed_result.source.provider}+{live_result.source.provider}"
            self.record(seed_result)
            self.record(live_result)
            return combined

        if seed_result and self.mode != DataMode.LIVE:
            self.record(seed_result)
            return seed_result

        if live_result:
            self.record(live_result)
            return live_result

        return None

    def fetch_accommodation(
        self,
        city: str,
        nights: int,
        travel_style,
        budget_usd: float,
        duration_days: int,
    ) -> Optional[ProviderResult]:
        if self.mode == DataMode.LIVE:
            return None
        result = self.accommodation_seed.fetch(
            city=city,
            nights=nights,
            travel_style=travel_style,
            budget_usd=budget_usd,
            duration_days=duration_days,
        )
        self.record(result)
        return result

    def fetch_transport(self, context: TripContext) -> Optional[ProviderResult]:
        if not context.requirements:
            return None
        if self.mode == DataMode.LIVE:
            return None
        result = self.transport_seed.fetch(
            day_plans=context.day_plans,
            cities=context.requirements.destinations,
        )
        self.record(result)
        return result

    def compute_budget(self, context: TripContext) -> Optional[ProviderResult]:
        result = self.budget.compute(context)
        self.record(result)
        return result

    def provider_context_block(self, result: ProviderResult | None) -> str:
        if not result:
            return ""
        payload = result.data
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump(mode="json", by_alias=True)
        return (
            f"\n\nStructured provider data (prefer over guessing) "
            f"[{result.source.provider}, {result.source.confidence} confidence]:\n"
            f"{json.dumps(payload, indent=2)}\n"
        )

    def nights_for_city(self, context: TripContext, city: str) -> int:
        counts: dict[str, int] = {}
        for day in context.day_plans:
            counts[day.city] = counts.get(day.city, 0) + 1
        return counts.get(city, max(context.requirements.duration_days - 1, 1) if context.requirements else 1)


def build_data_registry(mode: DataMode | str | None = None) -> DataRegistry:
    if isinstance(mode, str):
        mode = DataMode(mode)
    return DataRegistry(mode=mode)


def apply_provenance(context: TripContext, registry: DataRegistry) -> None:
    from src.schemas import DataSourceRecord

    context.data_sources = [
        DataSourceRecord(
            domain=s.domain,
            provider=s.provider,
            source=s.source,
            source_type=s.source_type,
            confidence=s.confidence,
            fetched_at=s.fetched_at.isoformat(),
        )
        for s in registry.sources
    ]
    context.data_provenance = registry.provenance_summary()
