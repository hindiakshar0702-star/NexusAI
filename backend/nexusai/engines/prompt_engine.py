"""The top-level autonomous prompt-generation engine.

This is what most callers will use. It wires together:

  raw idea ─► IntentPredictor ─► domain builder ─► PromptOptimizer
           ─► PlatformAdapter  ─► PromptAnalyzer ─► SafetyEngine

The result is a fully scored, platform-tuned, safety-checked Prompt object.
"""
from __future__ import annotations

from typing import List, Optional

from ..domains import build_for
from ..platforms import adapt
from ..types import Domain, Intent, Platform, Prompt, SkillLevel
from .analyzer import PromptAnalyzer
from .intent_predictor import IntentPredictor
from .memory import MemoryStore
from .optimizer import PromptOptimizer
from .safety import SafetyEngine


_TITLE_MAX = 80


def _make_title(idea: str) -> str:
    title = idea.strip().split("\n", 1)[0]
    if len(title) > _TITLE_MAX:
        title = title[:_TITLE_MAX - 1].rstrip() + "..."
    return title or "Untitled Prompt"


class PromptEngine:
    def __init__(
        self,
        intent_predictor: Optional[IntentPredictor] = None,
        optimizer: Optional[PromptOptimizer] = None,
        analyzer: Optional[PromptAnalyzer] = None,
        safety: Optional[SafetyEngine] = None,
        memory: Optional[MemoryStore] = None,
    ) -> None:
        self.intent = intent_predictor or IntentPredictor()
        self.optimizer = optimizer or PromptOptimizer()
        self.analyzer = analyzer or PromptAnalyzer()
        self.safety = safety or SafetyEngine()
        self.memory = memory or MemoryStore()

    # ------------------------------------------------------------------ public
    def generate(
        self,
        raw_idea: str,
        skill_level: SkillLevel = SkillLevel.ADVANCED,
        domain: Optional[Domain] = None,
        platform: Optional[Platform] = None,
        include_negative: bool = True,
    ) -> Prompt:
        intent = self.intent.predict(raw_idea, hint_domain=domain, hint_platform=platform)
        return self._compose(intent, skill_level, include_negative=include_negative)

    def generate_tiered(self, raw_idea: str, **kwargs) -> List[Prompt]:
        """Return beginner / advanced / pro variants of the same prompt."""
        return [self.generate(raw_idea, skill_level=lv, **kwargs) for lv in SkillLevel]

    def generate_from_intent(self, intent: Intent, skill_level: SkillLevel) -> Prompt:
        return self._compose(intent, skill_level)

    # ----------------------------------------------------------------- helpers
    def _compose(self, intent: Intent, skill_level: SkillLevel,
                 include_negative: bool = True) -> Prompt:
        # 1) build a domain-aware body
        body = build_for(intent, skill_level)

        # 2) optimize wording / add guardrails
        optimized = self.optimizer.optimize(body, intent.domain, intent.platform)

        # 3) safety check
        safety_report = self.safety.review(optimized)
        if not safety_report.safe:
            raise SafetyViolation(
                f"Prompt blocked by safety policy: {', '.join(safety_report.flags)}"
            )

        # 4) platform adaptation
        adapted = adapt(optimized, intent.platform, intent.domain)

        # 5) score
        score = self.analyzer.analyze(adapted.user, intent.platform)

        prompt = Prompt(
            id=Prompt.new_id(),
            text=adapted.user,
            domain=intent.domain,
            platform=intent.platform,
            skill_level=skill_level,
            title=_make_title(intent.raw_idea),
            system=adapted.system or None,
            negative=(adapted.negative or None) if include_negative else None,
            parameters=adapted.parameters,
            tags=self._derive_tags(intent),
            rationale=self._rationale(intent, adapted.notes),
            score=score,
        )
        self.memory.remember(prompt, score=score.overall)
        return prompt

    def _derive_tags(self, intent: Intent) -> List[str]:
        tags = [intent.domain.value, intent.platform.value]
        if intent.tone and intent.tone != "neutral":
            tags.append(intent.tone)
        for emotion in intent.emotions:
            tags.append(emotion)
        return tags

    def _rationale(self, intent: Intent, platform_notes: str) -> str:
        bits = [
            f"Inferred domain={intent.domain.value} and platform={intent.platform.value} "
            f"with confidence {intent.confidence}.",
        ]
        if intent.missing_details:
            bits.append("Open questions: " + " | ".join(intent.missing_details))
        if platform_notes:
            bits.append(platform_notes)
        return " ".join(bits)


class SafetyViolation(Exception):
    """Raised when the safety gate refuses a prompt."""
