"""Self-prompt evolution engine.

Given a prompt and (optional) user feedback, propose improved variants and
let the analyzer pick the strongest. Implements a simple hill-climb: each
"generation" the engine emits N mutations of the best prompt so far, scores
them, and keeps the best. Mutations are deterministic operations (rephrasing,
guardrail injection, sensory anchor injection) so the loop is reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from ..types import Platform, Prompt, PromptScore
from .analyzer import PromptAnalyzer
from .optimizer import PromptOptimizer


Mutator = Callable[[str], str]


def _add_sensory_anchor(text: str) -> str:
    if "Tone:" in text:
        return text
    return text + "\n\nTone: vivid, sensory, with one unexpected metaphor."


def _add_audience_anchor(text: str) -> str:
    if "Audience:" in text:
        return text
    return text + "\n\nAudience: assume an intelligent skeptic. Earn every claim."


def _add_anti_hallucination(text: str) -> str:
    cue = "If a fact is uncertain, label it [UNVERIFIED] rather than guessing."
    if cue in text:
        return text
    return text + "\n\n" + cue


def _add_format_anchor(text: str) -> str:
    cue = "Format: use a short header, then bullet points with concrete examples."
    if cue in text:
        return text
    return text + "\n\n" + cue


def _tighten(text: str) -> str:
    # collapse double-bullets, trim trailing whitespace
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = []
    prev_blank = False
    for ln in lines:
        if not ln.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


_DEFAULT_MUTATORS: List[Mutator] = [
    _add_sensory_anchor,
    _add_audience_anchor,
    _add_anti_hallucination,
    _add_format_anchor,
    _tighten,
]


@dataclass
class EvolutionResult:
    best: Prompt
    history: List[Prompt]
    generations_run: int

    def to_dict(self) -> dict:
        return {
            "best": self.best.to_dict(),
            "history": [p.to_dict() for p in self.history],
            "generations_run": self.generations_run,
        }


class EvolutionEngine:
    def __init__(
        self,
        analyzer: Optional[PromptAnalyzer] = None,
        optimizer: Optional[PromptOptimizer] = None,
        mutators: Optional[Iterable[Mutator]] = None,
    ) -> None:
        self.analyzer = analyzer or PromptAnalyzer()
        self.optimizer = optimizer or PromptOptimizer()
        self.mutators = list(mutators) if mutators else list(_DEFAULT_MUTATORS)

    def evolve(
        self,
        seed: Prompt,
        generations: int = 3,
        feedback_score: Optional[float] = None,
    ) -> EvolutionResult:
        best = seed
        best_score = self._score_value(seed.score, feedback_score)
        history: List[Prompt] = [seed]

        for _ in range(generations):
            candidates: List[Prompt] = []
            for mutator in self.mutators:
                mutated_text = mutator(best.text)
                if mutated_text == best.text:
                    continue
                score = self.analyzer.analyze(mutated_text, best.platform)
                candidate = Prompt(
                    id=Prompt.new_id(),
                    text=mutated_text,
                    domain=best.domain,
                    platform=best.platform,
                    skill_level=best.skill_level,
                    title=best.title,
                    system=best.system,
                    negative=best.negative,
                    parameters=dict(best.parameters),
                    tags=list(best.tags) + ["evolved"],
                    rationale=f"Mutation of {best.id} via {mutator.__name__}",
                    score=score,
                    parent_id=best.id,
                )
                candidates.append(candidate)

            if not candidates:
                break

            challenger = max(candidates, key=lambda p: p.score.overall if p.score else 0.0)
            history.extend(candidates)
            challenger_score = challenger.score.overall if challenger.score else 0.0

            if challenger_score > best_score:
                best = challenger
                best_score = challenger_score
            else:
                # No improvement this generation; stop early.
                break

        return EvolutionResult(best=best, history=history, generations_run=len(history) - 1)

    @staticmethod
    def _score_value(score: Optional[PromptScore], feedback: Optional[float]) -> float:
        base = score.overall if score else 0.0
        if feedback is not None:
            # Weighted average so user feedback steers but doesn't dominate.
            return 0.6 * base + 0.4 * feedback
        return base
