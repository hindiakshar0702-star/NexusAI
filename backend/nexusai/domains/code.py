from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "State assumptions explicitly before writing code.",
        "Prefer pure functions and clear data shapes over clever abstractions.",
        "Handle the unhappy path (errors, empty inputs, partial failures).",
        "Add typing or schemas at module boundaries.",
        "Include unit tests covering one happy path and at least two edge cases.",
    ])
    return (
        f"Engineering task: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Working agreement:\n{bullets}\n\n"
        f"Deliverables: implementation, tests, and a short README section explaining how to run it.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
