from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Timing: anticipation -> action -> overshoot -> settle (12-frame rhythm).",
        "Easing: prefer cubic-bezier(0.22, 1, 0.36, 1) for entrances.",
        "Hierarchy: stagger child elements 60-120ms apart.",
        "Loops: seamless, with no perceptible seam at the boundary.",
        "Performance: keep to transform/opacity to stay GPU-accelerated.",
    ])
    return (
        f"Animation brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Motion specification:\n{bullets}\n\n"
        f"Deliver: a storyboard, key poses, and the final motion description.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
