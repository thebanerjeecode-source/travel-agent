from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from src.context import TripContext
from src.schemas import TripPlan


@dataclass
class StoredPlan:
    trip_plan: TripPlan
    context: TripContext


class SessionStore:
    """In-memory store for completed plans (MVP — single-process only)."""

    def __init__(self, max_entries: int = 100) -> None:
        self._entries: dict[str, StoredPlan] = {}
        self._order: list[str] = []
        self._max_entries = max_entries
        self._lock = Lock()

    def put(self, session_id: str, trip_plan: TripPlan, context: TripContext) -> None:
        with self._lock:
            if session_id not in self._entries:
                self._order.append(session_id)
            self._entries[session_id] = StoredPlan(trip_plan=trip_plan, context=context)
            while len(self._order) > self._max_entries:
                oldest = self._order.pop(0)
                self._entries.pop(oldest, None)

    def get(self, session_id: str) -> StoredPlan | None:
        with self._lock:
            return self._entries.get(session_id)


session_store = SessionStore()
