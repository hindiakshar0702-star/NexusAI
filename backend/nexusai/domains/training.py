from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Task definition: one input schema, one output schema, success metric.",
        "Synthetic dataset plan: sources, augmentation rules, contamination checks.",
        "Curriculum: easy -> medium -> hard with a held-out test set.",
        "Evaluation: a rubric mapping each metric to a measurable behavior.",
        "RL reward (if applicable): primary reward + at least one anti-gaming penalty.",
    ])
    return (
        f"Training automation brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Pipeline specification:\n{bullets}\n\n"
        f"Deliver: dataset spec, eval harness description, and acceptance criteria.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
