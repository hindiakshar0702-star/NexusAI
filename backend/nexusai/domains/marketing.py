from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Audience: a one-line buyer persona with pain + desired outcome.",
        "Insight: one non-obvious truth about the audience.",
        "Promise: the single specific change the product makes in their life.",
        "Proof: a measurable claim, testimonial, or named customer.",
        "Call to action: one verb, one outcome, no hedging.",
    ])
    return (
        f"Marketing brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Required structure:\n{bullets}\n\n"
        f"Voice rules: no superlatives without proof; no buzzwords without translation.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
