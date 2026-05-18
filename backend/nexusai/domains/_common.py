"""Shared helpers for domain builders."""
from __future__ import annotations

from typing import Iterable

from ..types import Intent, SkillLevel


def header(intent: Intent) -> str:
    parts = [f"Goal: {', '.join(intent.goals) or 'high-quality output'}."]
    if intent.audience and intent.audience != "general":
        parts.append(f"Audience: {intent.audience}.")
    if intent.tone and intent.tone != "neutral":
        parts.append(f"Tone: {intent.tone}.")
    if intent.emotions:
        parts.append(f"Emotional register: {', '.join(intent.emotions)}.")
    if intent.constraints:
        parts.append("Constraints: " + "; ".join(intent.constraints) + ".")
    return " ".join(parts)


def bullet_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def skill_tier(skill: SkillLevel) -> str:
    return {
        SkillLevel.BEGINNER: "Be friendly and explain choices in plain language.",
        SkillLevel.ADVANCED: "Assume the reader is fluent. Be terse and high-density.",
        SkillLevel.PRO: "Operate at expert level. Surface tradeoffs, edge cases, and second-order effects.",
    }[skill]
