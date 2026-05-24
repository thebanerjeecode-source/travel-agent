from __future__ import annotations

import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime
from threading import Lock

from src.llm.types import ModelProvider


class RateLimitExceeded(Exception):
    def __init__(self, provider: ModelProvider, message: str) -> None:
        self.provider = provider
        super().__init__(message)


@dataclass
class ProviderLimits:
    rpm: int
    rpd: int
    tpm: int | None = None


@dataclass
class ProviderUsage:
    rpm_used: int
    rpm_limit: int
    rpd_used: int
    rpd_limit: int

    def summary(self) -> str:
        return f"{self.rpd_used}/{self.rpd_limit} RPD, {self.rpm_used}/{self.rpm_limit} RPM"


@dataclass
class _ProviderState:
    minute_timestamps: deque[float] = field(default_factory=deque)
    day_count: int = 0
    day_key: date = field(default_factory=date.today)
    token_minute: deque[tuple[float, int]] = field(default_factory=deque)


class RateLimiter:
    """In-memory rate limiter for Groq and Gemini API quotas."""

    _instance: RateLimiter | None = None
    _lock = Lock()

    DEFAULT_LIMITS: dict[ModelProvider, ProviderLimits] = {
        ModelProvider.GROQ: ProviderLimits(
            rpm=int(os.getenv("GROQ_RPM", "30")),
            rpd=int(os.getenv("GROQ_RPD", "1000")),
            tpm=int(os.getenv("GROQ_TPM", "12000")),
        ),
        ModelProvider.GEMINI: ProviderLimits(
            rpm=int(os.getenv("GEMINI_RPM", "5")),
            rpd=int(os.getenv("GEMINI_RPD", "20")),
            tpm=int(os.getenv("GEMINI_TPM", "250000")),
        ),
    }

    def __init__(self) -> None:
        self._states: dict[ModelProvider, _ProviderState] = {
            provider: _ProviderState() for provider in ModelProvider
        }

    @classmethod
    def get(cls) -> RateLimiter:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — useful for tests (not run in Phase 1 per user request)."""
        with cls._lock:
            cls._instance = None

    def _limits(self, provider: ModelProvider) -> ProviderLimits:
        return self.DEFAULT_LIMITS[provider]

    def _state(self, provider: ModelProvider) -> _ProviderState:
        return self._states[provider]

    def _reset_day_if_needed(self, state: _ProviderState) -> None:
        today = date.today()
        if state.day_key != today:
            state.day_key = today
            state.day_count = 0

    def _prune_minute_window(self, state: _ProviderState, now: float) -> None:
        cutoff = now - 60.0
        while state.minute_timestamps and state.minute_timestamps[0] < cutoff:
            state.minute_timestamps.popleft()
        while state.token_minute and state.token_minute[0][0] < cutoff:
            state.token_minute.popleft()

    def usage(self, provider: ModelProvider) -> ProviderUsage:
        limits = self._limits(provider)
        state = self._state(provider)
        self._reset_day_if_needed(state)
        now = time.monotonic()
        self._prune_minute_window(state, now)
        return ProviderUsage(
            rpm_used=len(state.minute_timestamps),
            rpm_limit=limits.rpm,
            rpd_used=state.day_count,
            rpd_limit=limits.rpd,
        )

    def can_acquire(self, provider: ModelProvider) -> bool:
        usage = self.usage(provider)
        return usage.rpd_used < usage.rpd_limit and usage.rpm_used < usage.rpm_limit

    def acquire(self, provider: ModelProvider, *, estimated_tokens: int = 0) -> None:
        limits = self._limits(provider)
        state = self._state(provider)
        self._reset_day_if_needed(state)

        if state.day_count >= limits.rpd:
            raise RateLimitExceeded(
                provider,
                f"{provider.value} daily request limit reached ({limits.rpd} RPD). "
                "Try again tomorrow or use --stub for offline mode.",
            )

        now = time.monotonic()
        self._prune_minute_window(state, now)

        while len(state.minute_timestamps) >= limits.rpm:
            sleep_for = 60.0 - (now - state.minute_timestamps[0]) + 0.05
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            self._prune_minute_window(state, now)

        if limits.tpm and estimated_tokens > 0:
            tokens_used = sum(t for _, t in state.token_minute)
            while tokens_used + estimated_tokens > limits.tpm and state.token_minute:
                sleep_for = 60.0 - (now - state.token_minute[0][0]) + 0.05
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                self._prune_minute_window(state, now)
                tokens_used = sum(t for _, t in state.token_minute)

    def record(self, provider: ModelProvider, *, tokens: int = 0) -> None:
        state = self._state(provider)
        self._reset_day_if_needed(state)
        now = time.monotonic()
        state.minute_timestamps.append(now)
        state.day_count += 1
        if tokens > 0:
            state.token_minute.append((now, tokens))
