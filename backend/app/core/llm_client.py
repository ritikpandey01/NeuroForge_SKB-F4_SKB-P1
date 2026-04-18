"""OpenAI SDK wrapper with a tiny circuit breaker (Module 6).

Mirrors the previous Anthropic wrapper: singleton client + process-local
circuit so a flaky upstream burst doesn't pin worker processes on slow
upstream failures. Anything model-specific (prompts, tools, image rendering)
belongs in `services/*`, not here.

States:
    closed     — normal traffic; failures increment a counter
    open       — short-circuits; raises `CircuitBreakerOpen` until cooldown elapses
    half-open  — one trial request; success closes the circuit, failure re-opens
"""

from __future__ import annotations

import threading
import time
from typing import Any

from openai import APIError, OpenAI

from app.core.config import settings


class LLMNotConfigured(RuntimeError):
    """Raised when an API call is attempted but OPENAI_API_KEY is unset."""


class CircuitBreakerOpen(RuntimeError):
    """Raised when the circuit is open. Surface as 503 in API handlers."""


class LLMClient:
    def __init__(
        self,
        *,
        failure_threshold: int | None = None,
        cooldown_seconds: int | None = None,
    ) -> None:
        self._failure_threshold = failure_threshold or settings.OPENAI_CB_FAILURES
        self._cooldown_seconds = cooldown_seconds or settings.OPENAI_CB_COOLDOWN_SECONDS
        self._lock = threading.Lock()
        self._client: OpenAI | None = None
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._half_open_in_flight = False

    # ── Lazy SDK init ───────────────────────────────────────────────────
    def _sdk(self) -> OpenAI:
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise LLMNotConfigured(
                    "OPENAI_API_KEY is empty. Set it in backend/.env to use "
                    "LLM-powered features (document parser, anomaly explanations, "
                    "scenario narratives)."
                )
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    # ── Circuit state ───────────────────────────────────────────────────
    def _check_circuit(self) -> None:
        with self._lock:
            if self._opened_at is None:
                return
            elapsed = time.monotonic() - self._opened_at
            if elapsed < self._cooldown_seconds:
                remaining = int(self._cooldown_seconds - elapsed)
                raise CircuitBreakerOpen(
                    f"LLM circuit is open after {self._consecutive_failures} "
                    f"consecutive failures; retry in ~{remaining}s."
                )
            if self._half_open_in_flight:
                raise CircuitBreakerOpen(
                    "LLM circuit is half-open; another trial request is in flight."
                )
            self._half_open_in_flight = True

    def _record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None
            self._half_open_in_flight = False

    def _record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            self._half_open_in_flight = False
            if self._consecutive_failures >= self._failure_threshold:
                self._opened_at = time.monotonic()

    # ── Public API ──────────────────────────────────────────────────────
    def chat_completions_create(self, **kwargs: Any) -> Any:
        """Forward to `client.chat.completions.create(**kwargs)` with circuit guarding."""
        self._check_circuit()
        try:
            response = self._sdk().chat.completions.create(**kwargs)
        except APIError:
            self._record_failure()
            raise
        except Exception:
            self._record_failure()
            raise
        else:
            self._record_success()
            return response

    def status(self) -> dict[str, Any]:
        with self._lock:
            state = "closed"
            if self._opened_at is not None:
                elapsed = time.monotonic() - self._opened_at
                state = "open" if elapsed < self._cooldown_seconds else "half_open"
            return {
                "state": state,
                "consecutive_failures": self._consecutive_failures,
                "configured": bool(settings.OPENAI_API_KEY),
                "model": settings.OPENAI_MODEL,
            }


llm = LLMClient()
