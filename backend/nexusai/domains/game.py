from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Core loop in one sentence; verb-first.",
        "Win condition, loss condition, session length target.",
        "Three pillars (e.g. exploration, mastery, expression) and a non-pillar to reject scope creep.",
        "Risk/reward curve and how it escalates over time.",
        "Failure recovery loop so losing is interesting, not punishing.",
    ])
    return (
        f"Game design brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Design specification:\n{bullets}\n\n"
        f"Deliver: a one-page design doc plus a paper-prototype description.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
