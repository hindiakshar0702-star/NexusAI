from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Protagonist with a concrete external goal and a hidden internal need.",
        "Inciting incident that disrupts the status quo by page one.",
        "A midpoint reversal that re-frames the protagonists understanding.",
        "A climactic choice that forces the protagonist to pay an emotional cost.",
        "A final image that visually echoes (or inverts) the opening image.",
    ])
    return (
        f"Story brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Narrative structure:\n{bullets}\n\n"
        f"Voice: prefer concrete sensory detail over abstraction. Show, then name.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
