"""Prompt analyzer.

Scores a prompt across clarity, specificity, creativity, realism, safety
and platform-fit, and returns concrete suggestions to improve weak areas.
The scoring uses transparent heuristics (lengths, vocabulary diversity,
section presence) so callers can audit and unit-test the output.
"""
from __future__ import annotations

import re
from typing import List

from ..types import Platform, PromptScore
from .safety import SafetyEngine


_WEAK_WORDS = {
    "thing", "stuff", "nice", "good", "very", "really", "great", "interesting",
    "amazing", "cool", "etc", "etc.",
}

_VAGUE_PHRASES = [
    r"\bdo\s+something\b",
    r"\bmake\s+it\s+(look|feel)\s+(good|nice|cool)\b",
    r"\bbe\s+creative\b",
]

_PLATFORM_HINTS = {
    Platform.MIDJOURNEY: ["--ar", "--style", "--v", "::"],
    Platform.STABLE_DIFFUSION: ["negative prompt", "(", ":1.", "lora"],
    Platform.RUNWAY: ["camera", "shot", "motion"],
    Platform.SORA: ["scene", "shot", "duration"],
    Platform.V0: ["component", "tailwind", "responsive"],
    Platform.BOLT: ["scaffold", "stack", "framework"],
    Platform.CURSOR: ["tests", "types", "edge cases"],
    Platform.FIGMA: ["frame", "auto layout", "tokens"],
}


class PromptAnalyzer:
    def __init__(self) -> None:
        self._safety = SafetyEngine()

    def analyze(self, text: str, platform: Platform = Platform.GENERIC) -> PromptScore:
        text = text or ""
        weaknesses: List[str] = []
        suggestions: List[str] = []

        clarity = self._clarity(text, weaknesses, suggestions)
        specificity = self._specificity(text, weaknesses, suggestions)
        creativity = self._creativity(text, weaknesses, suggestions)
        realism = self._realism(text, weaknesses, suggestions)
        safety = self._safety_score(text, weaknesses, suggestions)
        platform_fit = self._platform_fit(text, platform, weaknesses, suggestions)

        overall = round(
            0.22 * clarity + 0.22 * specificity + 0.16 * creativity +
            0.12 * realism + 0.14 * safety + 0.14 * platform_fit, 3
        )
        return PromptScore(
            clarity=round(clarity, 2),
            specificity=round(specificity, 2),
            creativity=round(creativity, 2),
            realism=round(realism, 2),
            safety=round(safety, 2),
            platform_fit=round(platform_fit, 2),
            overall=overall,
            weaknesses=weaknesses,
            suggestions=suggestions,
        )

    # -------------------------------------------------------------- dimensions
    def _clarity(self, text: str, weaknesses: List[str], suggestions: List[str]) -> float:
        if not text.strip():
            weaknesses.append("Prompt is empty.")
            return 0.0
        sentences = [s for s in re.split(r"[.!?]\s", text) if s.strip()]
        avg_len = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        score = 1.0
        if avg_len > 35:
            score -= 0.3
            weaknesses.append("Sentences are long; the model may lose focus.")
            suggestions.append("Break long sentences into shorter, single-purpose lines.")
        for phrase in _VAGUE_PHRASES:
            if re.search(phrase, text, flags=re.IGNORECASE):
                score -= 0.2
                weaknesses.append(f"Vague directive: '{phrase}'")
                suggestions.append("Replace vague directives with measurable criteria.")
                break
        return max(0.0, min(1.0, score))

    def _specificity(self, text: str, weaknesses: List[str], suggestions: List[str]) -> float:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
        if not words:
            return 0.0
        unique_ratio = len(set(words)) / len(words)
        weak_hits = sum(1 for w in words if w in _WEAK_WORDS)
        score = 0.4 + 0.6 * unique_ratio - 0.05 * weak_hits
        if weak_hits >= 3:
            weaknesses.append("Frequent weak filler words (e.g. 'thing', 'nice').")
            suggestions.append("Swap filler words for concrete nouns and adjectives.")
        if len(words) < 12:
            score -= 0.2
            weaknesses.append("Prompt is very short; missing context.")
            suggestions.append(
                "Add who/what/where/why/constraints. A useful prompt is usually 30-120 words.")
        return max(0.0, min(1.0, score))

    def _creativity(self, text: str, weaknesses: List[str], suggestions: List[str]) -> float:
        # Naive: density of sensory / stylistic words.
        creative_markers = [
            "style of", "in the manner of", "inspired by", "cinematic", "moody",
            "vibrant", "ethereal", "surreal", "metaphor", "narrative", "twist",
            "contrast", "tension", "unexpected",
        ]
        hits = sum(1 for m in creative_markers if m in text.lower())
        score = min(1.0, 0.3 + 0.12 * hits)
        if score < 0.5:
            suggestions.append(
                "Add a stylistic anchor (an artist, era, mood, or metaphor) to lift creativity.")
        return score

    def _realism(self, text: str, weaknesses: List[str], suggestions: List[str]) -> float:
        # Realism here = "is the prompt grounded enough that the model won't hallucinate?"
        score = 0.7
        if re.search(r"\b(everything|all the things|anything you want)\b", text, re.I):
            score -= 0.3
            weaknesses.append("Open-ended scope encourages hallucination.")
            suggestions.append("Bound the scope with a list of must-have / must-not-have items.")
        if "cite sources" in text.lower() or "if unsure" in text.lower():
            score += 0.2
        return max(0.0, min(1.0, score))

    def _safety_score(self, text: str, weaknesses: List[str], suggestions: List[str]) -> float:
        report = self._safety.review(text)
        if report.severity == "high":
            weaknesses.append("Prompt contains disallowed content.")
            return 0.0
        if report.severity == "medium":
            weaknesses.append("Prompt contains questionable content.")
            return 0.4
        if report.severity == "low":
            suggestions.append("Consider redacting embedded PII before sharing the prompt.")
            return 0.8
        return 1.0

    def _platform_fit(self, text: str, platform: Platform,
                      weaknesses: List[str], suggestions: List[str]) -> float:
        hints = _PLATFORM_HINTS.get(platform)
        if not hints:
            return 0.8  # generic platforms get a default decent score
        lowered = text.lower()
        hits = sum(1 for h in hints if h.lower() in lowered)
        score = min(1.0, 0.4 + 0.2 * hits)
        if hits == 0:
            suggestions.append(
                f"Add platform-native cues for {platform.value} "
                f"(e.g. {', '.join(hints[:3])}).")
        return score
