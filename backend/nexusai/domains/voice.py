from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Speaker: age range, gender, accent, archetype.",
        "Pace: words per minute target.",
        "Prosody: where to lean in, where to pull back, where to pause.",
        "Microphone character: close, intimate, lightly compressed.",
        "Emotional arc across the read.",
    ])
    return (
        f"Voice brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Voice specification:\n{bullets}\n\n"
        f"Script formatting: short lines, one beat per line, [direction] tags inline.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
