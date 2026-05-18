from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    system = bullet_list([
        "Layout: 12-column responsive grid, 4px spacing rhythm.",
        "Typography: pairing of one display face with one neutral text face; 1.25 modular scale.",
        "Color: 1 primary + 1 accent + 4 neutrals; AA contrast minimum.",
        "Components: buttons, inputs, cards, modals, navigation; consistent corner radius.",
        "Motion: entrances under 200ms, easing on real curves not linear.",
        "Accessibility: visible focus rings, 44x44 minimum touch targets, semantic landmarks.",
    ])
    deliver = bullet_list([
        "Wireframe of each key screen.",
        "High-fidelity mock with the design tokens applied.",
        "A short rationale for each major design decision.",
    ])
    return (
        f"UI/UX brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Design system:\n{system}\n\n"
        f"Deliver:\n{deliver}\n\n"
        f"Direction: {skill_tier(skill)}"
    )
