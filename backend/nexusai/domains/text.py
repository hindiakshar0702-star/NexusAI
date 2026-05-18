from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "A clear thesis or message in the first sentence.",
        "A structured body with a logical narrative arc.",
        "Concrete examples or data points to anchor the claims.",
        "A closing call-to-action aligned to the goal.",
    ])
    return (
        f"You are an expert writer crafting text for the user's idea.\n\n"
        f"Idea: {intent.raw_idea}\n\n"
        f"{header(intent)}\n\n"
        f"Deliver:\n{bullets}\n\n"
        f"Style: {skill_tier(skill)}"
    )
