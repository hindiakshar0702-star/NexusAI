from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Establishing shot: wide, slow push-in, sets the world.",
        "Medium shot: subject in environment, motivated lighting.",
        "Close-up: emotional beat on the subject.",
        "Insert: a meaningful detail that pays off the theme.",
        "Final shot: outro frame that reinforces the message.",
    ])
    return (
        f"Scene: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Shot list:\n{bullets}\n\n"
        f"Camera & motion: smooth gimbal moves, 24fps, cinematic depth of field, "
        f"motivated lens choices (35mm wide, 85mm portrait).\n"
        f"Sound design: diegetic foreground + low-frequency bed; one signature SFX.\n"
        f"Pacing: cuts on motion or audio cues, not on a timer.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
