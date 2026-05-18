from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Composition: rule-of-thirds, clear focal point, layered depth (foreground / midground / background).",
        "Lighting: directional key light with soft fill, motivated by the scene.",
        "Color: cohesive palette with one accent color carrying emotional weight.",
        "Camera: 35mm equivalent, shallow depth of field, eye-level framing.",
        "Texture: physically plausible materials with subtle micro-detail.",
    ])
    return (
        f"Subject: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Visual specification:\n{bullets}\n\n"
        f"Avoid: warped anatomy, illegible text, watermarks, stock-photo cliches.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
