"""Shared utilities for all agents."""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_llm(
    temperature: float = 0.3,
    max_tokens: int = 32768,
    agent_name: str = "",
) -> ChatOpenAI:
    """Build a ChatOpenAI instance from environment variables.

    If *agent_name* is provided (e.g. "frontend"), the function first checks
    for MODEL_FRONTEND before falling back to MODEL_NAME / LLM_MODEL.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE") or os.getenv("LLM_BASE_URL")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    # Per-agent model override: MODEL_FRONTEND, MODEL_BACKEND, etc.
    model = ""
    if agent_name:
        model = os.getenv(f"MODEL_{agent_name.upper()}", "")
    if not model:
        model = os.getenv("MODEL_NAME") or os.getenv("LLM_MODEL", "gpt-4")

    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if api_base:
        kwargs["base_url"] = api_base

    return ChatOpenAI(**kwargs)  # type: ignore[arg-type]


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that retries a function with exponential backoff on exception."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        "Retry %d/%d for %s after error: %s (waiting %.1fs)",
                        attempt + 1, max_retries, fn.__name__, exc, delay,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
