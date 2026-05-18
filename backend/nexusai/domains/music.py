from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Genre and adjacent references (1-3 artists, no plagiarism).",
        "Tempo, key, time signature.",
        "Instrumentation: lead, harmony, rhythm, texture, low end.",
        "Arrangement: intro -> build -> drop/chorus -> bridge -> outro.",
        "Mix character: clean / dusty / wide / intimate.",
    ])
    return (
        f"Music brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Composition specification:\n{bullets}\n\n"
        f"Deliver: a written brief plus a structural timeline in seconds.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
