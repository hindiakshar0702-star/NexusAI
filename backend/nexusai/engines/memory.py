"""Self-learning memory store.

In-process key/value + vector-ish store for successful prompt structures.
A real deployment would back this with PostgreSQL + pgvector or a managed
vector DB; the interface below is shaped to make that swap a one-line change.
"""
from __future__ import annotations

import math
import re
import threading
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from ..types import Domain, Platform, Prompt


_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


class MemoryStore:
    """Stores prompts + feedback and supports lexical similarity recall."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._prompts: Dict[str, Prompt] = {}
        self._vectors: Dict[str, Counter] = {}
        self._feedback: Dict[str, List[float]] = defaultdict(list)
        self._success_patterns: Counter = Counter()

    # ------------------------------------------------------------------ writes
    def remember(self, prompt: Prompt, score: float = 0.0) -> None:
        with self._lock:
            self._prompts[prompt.id] = prompt
            self._vectors[prompt.id] = Counter(_tokenize(prompt.text))
            if score:
                self._feedback[prompt.id].append(score)
            if score >= 0.75:
                # Track which token n-grams correlate with high-quality prompts.
                tokens = _tokenize(prompt.text)
                for i in range(len(tokens) - 1):
                    self._success_patterns[(tokens[i], tokens[i + 1])] += 1

    def record_feedback(self, prompt_id: str, score: float) -> None:
        with self._lock:
            self._feedback[prompt_id].append(score)
            prompt = self._prompts.get(prompt_id)
            if prompt and score >= 0.75:
                tokens = _tokenize(prompt.text)
                for i in range(len(tokens) - 1):
                    self._success_patterns[(tokens[i], tokens[i + 1])] += 1

    # ------------------------------------------------------------------- reads
    def get(self, prompt_id: str) -> Optional[Prompt]:
        return self._prompts.get(prompt_id)

    def all(self) -> List[Prompt]:
        with self._lock:
            return list(self._prompts.values())

    def average_score(self, prompt_id: str) -> Optional[float]:
        scores = self._feedback.get(prompt_id)
        if not scores:
            return None
        return sum(scores) / len(scores)

    def recall(
        self,
        query: str,
        domain: Optional[Domain] = None,
        platform: Optional[Platform] = None,
        k: int = 5,
    ) -> List[Tuple[Prompt, float]]:
        q_vec = Counter(_tokenize(query))
        results: List[Tuple[Prompt, float]] = []
        with self._lock:
            for pid, vec in self._vectors.items():
                prompt = self._prompts[pid]
                if domain and prompt.domain != domain:
                    continue
                if platform and prompt.platform != platform:
                    continue
                sim = _cosine(q_vec, vec)
                if sim > 0:
                    results.append((prompt, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def top_success_patterns(self, n: int = 20) -> List[Tuple[str, int]]:
        return [
            (" ".join(bigram), count)
            for bigram, count in self._success_patterns.most_common(n)
        ]

    # used by some engines as a tiny snapshot
    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return {
                "prompts": len(self._prompts),
                "feedback_entries": sum(len(v) for v in self._feedback.values()),
                "success_patterns": len(self._success_patterns),
            }
