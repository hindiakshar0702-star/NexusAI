from __future__ import annotations

from ..types import Intent, SkillLevel
from ._common import bullet_list, header, skill_tier


def build(intent: Intent, skill: SkillLevel) -> str:
    bullets = bullet_list([
        "Hero: one-line value proposition, supporting subhead, single primary CTA.",
        "Social proof: logos or quantified results immediately under the hero.",
        "Feature blocks: outcome-led headlines, not feature-led.",
        "Pricing: 3 tiers, recommended tier visually emphasized.",
        "FAQ: address the top 5 objections truthfully.",
        "Footer: legal, sitemap, contact, status.",
    ])
    return (
        f"Website brief: {intent.raw_idea}\n"
        f"{header(intent)}\n\n"
        f"Site architecture:\n{bullets}\n\n"
        f"Stack: Next.js + Tailwind, server components by default, animated with Framer Motion.\n"
        f"Performance: target Lighthouse >= 95 across all categories.\n\n"
        f"Direction: {skill_tier(skill)}"
    )
