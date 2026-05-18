"""Multi-agent collaboration.

Three agents collaborate to produce a final prompt:

  * WriterAgent   – generates an initial prompt.
  * CriticAgent   – analyzes weaknesses with PromptAnalyzer.
  * OptimizerAgent– rewrites based on critique using EvolutionEngine.

The orchestrator runs Writer -> Critic -> Optimizer (-> Critic) loops until
the score plateaus or a quality target is met. This is how "AI agents
collaborate" maps to a real, runnable, deterministic pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..types import Prompt, PromptScore, SkillLevel
from .evolution import EvolutionEngine
from .prompt_engine import PromptEngine


@dataclass
class AgentTrace:
    agent: str
    action: str
    prompt_id: str
    score: float
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "action": self.action,
            "prompt_id": self.prompt_id,
            "score": self.score,
            "note": self.note,
        }


@dataclass
class AgentRunResult:
    final: Prompt
    trace: List[AgentTrace]

    def to_dict(self) -> dict:
        return {"final": self.final.to_dict(), "trace": [t.to_dict() for t in self.trace]}


class AgentOrchestrator:
    """Coordinate Writer / Critic / Optimizer agents."""

    def __init__(
        self,
        engine: Optional[PromptEngine] = None,
        evolution: Optional[EvolutionEngine] = None,
        target_score: float = 0.78,
        max_rounds: int = 3,
    ) -> None:
        self.engine = engine or PromptEngine()
        self.evolution = evolution or EvolutionEngine(analyzer=self.engine.analyzer)
        self.target_score = target_score
        self.max_rounds = max_rounds

    def run(self, raw_idea: str, skill_level: SkillLevel = SkillLevel.ADVANCED) -> AgentRunResult:
        trace: List[AgentTrace] = []

        # 1) Writer
        current = self.engine.generate(raw_idea, skill_level=skill_level)
        trace.append(AgentTrace(
            agent="writer",
            action="generate",
            prompt_id=current.id,
            score=current.score.overall if current.score else 0.0,
            note="Initial prompt drafted.",
        ))

        # 2) Critic + Optimizer loop
        for round_index in range(self.max_rounds):
            critic_score = self.engine.analyzer.analyze(current.text, current.platform)
            trace.append(AgentTrace(
                agent="critic",
                action="analyze",
                prompt_id=current.id,
                score=critic_score.overall,
                note=self._critic_note(critic_score),
            ))
            if critic_score.overall >= self.target_score:
                break

            evolved = self.evolution.evolve(current, generations=2)
            improvement = (evolved.best.score.overall if evolved.best.score else 0.0) - critic_score.overall
            trace.append(AgentTrace(
                agent="optimizer",
                action="evolve",
                prompt_id=evolved.best.id,
                score=evolved.best.score.overall if evolved.best.score else 0.0,
                note=f"Round {round_index + 1}: {improvement:+.3f} delta.",
            ))
            if evolved.best.id == current.id:
                # No improvement was possible.
                break
            current = evolved.best

        return AgentRunResult(final=current, trace=trace)

    @staticmethod
    def _critic_note(score: PromptScore) -> str:
        if not score.weaknesses and not score.suggestions:
            return "No weaknesses found."
        bits = []
        if score.weaknesses:
            bits.append("Weak: " + "; ".join(score.weaknesses[:3]))
        if score.suggestions:
            bits.append("Try: " + "; ".join(score.suggestions[:3]))
        return " | ".join(bits)
