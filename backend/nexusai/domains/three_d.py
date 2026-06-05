from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Topology: quads, even loops around deformation areas.",
        "Polycount budget appropriate for the platform (game / film).",
        "UV layout: non-overlapping, packed, with consistent texel density.",
        "Materials: PBR (base color, roughness, metallic, normal, AO).",
        "LODs and collision shapes if game-bound.",
    ])
    return (
        f"3D model brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Asset specification:\n{bullets}\n\n"
        f"Deliver: blockout, hi-poly, retopo, bakes, final textured asset.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
