from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Primary user journey end-to-end (auth -> core action -> success state).",
        "Offline-first storage with optimistic UI for the core action.",
        "Push notifications scoped to high-signal events only.",
        "Settings: account, notifications, privacy, theme.",
    ])
    return (
        f"App brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Scope:\n{bullets}\n\n"
        f"Stack hint: React Native or Flutter, typed end-to-end, navigation stack with deep links.\n"
        f"Quality bar: cold start under 2s, P95 interaction latency under 100ms.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
