"""Optional GPT-4 teacher enhancement.

NexusAI's deterministic engine produces *structurally* correct prompts but
the language is templated. For training data, we want outputs that are
both well-structured AND naturally written. This module wraps the OpenAI
Chat Completions API to rewrite a NexusAI-generated prompt into a more
fluid, teacher-quality version while preserving its structure and intent.

Design decisions
----------------
* The OpenAI dependency is optional — code is written so the module imports
  cleanly even when the `openai` package is not installed. Callers should
  call `is_available()` first and gracefully fall back.
* Network and quota errors are caught and returned as `None` so the dataset
  exporter can transparently skip enhancement and keep the raw NexusAI
  output. We never crash a 1000-example run because example #347 timed out.
* A small in-process LRU cache (keyed on input text + model + temperature)
  avoids re-paying for the same prompt on retries.
* Concurrency uses a simple thread pool. The OpenAI SDK is sync-friendly and
  we don't need asyncio for export pipelines.
"""
from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# Default model. gpt-4o-mini is the cheapest gpt-4-class model and is more
# than capable of "polish this prompt" tasks. Users can override via env
# var or constructor.
DEFAULT_MODEL = os.environ.get("NEXUSAI_TEACHER_MODEL", "gpt-4o-mini")

# System prompt for the teacher. We keep it deliberately short so most
# tokens go to the user-supplied content.
TEACHER_SYSTEM_PROMPT = (
    "You are an expert prompt engineer. You will receive a structured prompt "
    "produced by an automated system. Your job is to rewrite it so it reads "
    "naturally to a human, while preserving every concrete instruction, "
    "constraint, parameter, and section header it contains. Do not add new "
    "facts. Do not remove guardrails. Do not change the target platform. "
    "Return only the rewritten prompt, no preamble, no commentary."
)


# ---------------------------------------------------------------- public API


def is_available() -> bool:
    """True if the openai package is importable AND an API key is configured."""
    try:
        import openai  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("OPENAI_API_KEY"))


@dataclass
class TeacherStats:
    requested: int = 0
    enhanced: int = 0
    cached_hits: int = 0
    skipped_unavailable: int = 0
    failed: int = 0
    total_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested": self.requested,
            "enhanced": self.enhanced,
            "cached_hits": self.cached_hits,
            "skipped_unavailable": self.skipped_unavailable,
            "failed": self.failed,
            "total_seconds": round(self.total_seconds, 3),
        }


class GPT4Teacher:
    """Optional rewriter that polishes NexusAI-generated prompts via GPT-4.

    Usage:
        teacher = GPT4Teacher()
        if teacher.available:
            improved = teacher.enhance(nexusai_prompt_text)
            if improved is not None:
                # use improved
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1500,
        timeout: float = 30.0,
        max_retries: int = 2,
        max_workers: int = 4,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_workers = max_workers

        self.stats = TeacherStats()

        self._client = None
        self._init_error: Optional[str] = None

        if api_key is not None:
            os.environ["OPENAI_API_KEY"] = api_key

        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            self._init_error = f"openai package not installed: {e}"
            return

        if not os.environ.get("OPENAI_API_KEY"):
            self._init_error = "OPENAI_API_KEY environment variable not set"
            return

        try:
            self._client = OpenAI(timeout=timeout)
        except Exception as e:  # pragma: no cover - openai sdk init paths
            self._init_error = f"failed to construct OpenAI client: {e}"

    # ------------------------------------------------------------------ status
    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    # ------------------------------------------------------------------ single
    def enhance(self, prompt_text: str) -> Optional[str]:
        """Rewrite one prompt. Returns None on failure or unavailable."""
        if not self.available:
            self.stats.skipped_unavailable += 1
            return None

        self.stats.requested += 1

        cached = _cached_call(self.model, self.temperature, prompt_text)
        if cached is not None:
            self.stats.cached_hits += 1
            self.stats.enhanced += 1
            return cached

        started = time.time()
        result = self._call_with_retries(prompt_text)
        self.stats.total_seconds += time.time() - started

        if result is None:
            self.stats.failed += 1
            return None

        # Populate the cache for subsequent identical calls.
        _store_in_cache(self.model, self.temperature, prompt_text, result)
        self.stats.enhanced += 1
        return result

    # -------------------------------------------------------------- concurrent
    def enhance_many(
        self,
        prompts: Iterable[str],
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[Optional[str]]:
        """Enhance many prompts concurrently. Preserves input order.

        Returns a list aligned with the input: each element is the enhanced
        text or None if the call failed (or teacher unavailable).
        """
        prompt_list = list(prompts)
        if not self.available:
            self.stats.skipped_unavailable += len(prompt_list)
            return [None] * len(prompt_list)

        results: List[Optional[str]] = [None] * len(prompt_list)
        total = len(prompt_list)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self.enhance, p): i for i, p in enumerate(prompt_list)}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results[idx] = fut.result()
                except Exception as e:
                    logger.warning("teacher.enhance failed for idx=%d: %s", idx, e)
                    results[idx] = None
                completed += 1
                if on_progress is not None:
                    on_progress(completed, total)

        return results

    # ----------------------------------------------------------------- helpers
    def _call_with_retries(self, prompt_text: str) -> Optional[str]:
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(  # type: ignore[union-attr]
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_text},
                    ],
                )
                content = response.choices[0].message.content
                if content is None:
                    return None
                return content.strip()
            except Exception as e:  # network, rate limit, etc.
                last_err = e
                if attempt < self.max_retries:
                    # exponential backoff with jitter-free determinism
                    time.sleep(0.5 * (2 ** attempt))
                else:
                    logger.warning("teacher exhausted retries: %s", e)
        # Should not reach here, but be safe.
        if last_err is not None:
            logger.warning("teacher final error: %s", last_err)
        return None


# ----------------------------------------------------------------- caching

# Module-level LRU cache. We key on (model, temperature, prompt_text). The
# wrapping below lets us "store" results post-hoc since lru_cache only
# remembers what it computed itself; we use a simple dict-backed cache.
_CACHE: Dict[tuple, str] = {}
_CACHE_MAX = 2048


def _cached_call(model: str, temperature: float, prompt_text: str) -> Optional[str]:
    return _CACHE.get((model, temperature, prompt_text))


def _store_in_cache(model: str, temperature: float, prompt_text: str, value: str) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        # Drop one arbitrary entry to keep memory bounded; ok for our use.
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[(model, temperature, prompt_text)] = value


def clear_cache() -> None:
    """For tests."""
    _CACHE.clear()
