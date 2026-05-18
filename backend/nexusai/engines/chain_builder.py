"""Prompt chain builder.

Decomposes a goal into a sequence of dependent prompts (a "master prompt
with sub-prompts"). The decomposition is rule-driven, but the produced
chain is fully usable: each step is a real Prompt with its own platform
adapter and score.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from ..types import (
    ChainStep,
    Domain,
    Intent,
    Platform,
    Prompt,
    PromptChain,
    SkillLevel,
)
from .prompt_engine import PromptEngine


# Recipe: ordered (name, purpose, optional domain override) tuples per top-level domain.
_RECIPES = {
    Domain.WEBSITE: [
        ("research", "List target audience pains, competitors, positioning insights.", Domain.MARKETING),
        ("ia", "Define site information architecture and primary user flows.", Domain.UI_UX),
        ("copy", "Write hero, feature, pricing, FAQ, and footer copy.", Domain.MARKETING),
        ("design", "Design the visual system: color, type, spacing, components.", Domain.UI_UX),
        ("build", "Implement the site with Next.js + Tailwind, responsive and accessible.", Domain.WEBSITE),
        ("qa", "Lighthouse audit, accessibility audit, and conversion-friction review.", Domain.CODE),
    ],
    Domain.APP: [
        ("research", "Identify the core user job, top objections, and competitor gaps.", Domain.MARKETING),
        ("flows", "Design the primary user journey end-to-end.", Domain.UI_UX),
        ("design", "Design the visual system and key screens.", Domain.UI_UX),
        ("build", "Scaffold the app, wire the primary journey, add offline-first storage.", Domain.APP),
        ("qa", "Performance, accessibility, and crash-free-session audit.", Domain.CODE),
    ],
    Domain.IMAGE: [
        ("concept", "Generate 3 distinct concepts for the subject.", Domain.STORYTELLING),
        ("style", "Pick one concept and define the visual style in detail.", Domain.IMAGE),
        ("compose", "Render the final image with full visual specification.", Domain.IMAGE),
    ],
    Domain.VIDEO: [
        ("script", "Write a tight, beat-by-beat script for the scene.", Domain.STORYTELLING),
        ("storyboard", "Storyboard the scene with shot descriptions.", Domain.VIDEO),
        ("generate", "Generate the video with full camera and motion direction.", Domain.VIDEO),
        ("score", "Define the music and sound design for the scene.", Domain.MUSIC),
    ],
    Domain.MARKETING: [
        ("research", "Build a one-line buyer persona and identify the top 3 objections.", Domain.MARKETING),
        ("angles", "Brainstorm 5 distinct messaging angles.", Domain.MARKETING),
        ("draft", "Write the final asset for the chosen angle.", Domain.MARKETING),
        ("test_plan", "Define an A/B test plan and success metric.", Domain.MARKETING),
    ],
    Domain.CODE: [
        ("design", "Design the data model, public interface, and error cases.", Domain.CODE),
        ("implement", "Implement the design with explicit types.", Domain.CODE),
        ("test", "Write unit tests covering happy path and edge cases.", Domain.CODE),
        ("review", "Self-review for readability, performance, and security.", Domain.CODE),
    ],
    Domain.TRAINING: [
        ("dataset", "Specify the synthetic dataset: schema, sources, augmentations.", Domain.TRAINING),
        ("eval", "Define the evaluation rubric and held-out test set.", Domain.TRAINING),
        ("train", "Specify the fine-tuning configuration and curriculum.", Domain.TRAINING),
        ("rl", "Define an optional RL reward and anti-gaming penalty.", Domain.TRAINING),
    ],
}

_DEFAULT_RECIPE = [
    ("plan", "Outline the deliverable and constraints.", None),
    ("draft", "Produce the first complete draft.", None),
    ("refine", "Critique and rewrite for clarity, specificity, and impact.", None),
]


class ChainBuilder:
    def __init__(self, engine: Optional[PromptEngine] = None) -> None:
        self.engine = engine or PromptEngine()

    def build_chain(
        self,
        raw_goal: str,
        skill_level: SkillLevel = SkillLevel.ADVANCED,
        platform: Optional[Platform] = None,
    ) -> PromptChain:
        # Predict the dominant domain so we can pick a recipe.
        intent = self.engine.intent.predict(raw_goal, hint_platform=platform)
        recipe = _RECIPES.get(intent.domain, _DEFAULT_RECIPE)

        steps: List[ChainStep] = []
        prev_name: Optional[str] = None
        for name, purpose, override_domain in recipe:
            sub_idea = f"{purpose} Context: {raw_goal}"
            sub_intent = self.engine.intent.predict(
                sub_idea,
                hint_domain=override_domain or intent.domain,
                hint_platform=platform or intent.platform,
            )
            prompt = self.engine.generate_from_intent(sub_intent, skill_level)
            depends = [prev_name] if prev_name else []
            steps.append(ChainStep(name=name, purpose=purpose, prompt=prompt, depends_on=depends))
            prev_name = name

        return PromptChain(
            id=uuid.uuid4().hex[:12],
            goal=raw_goal,
            steps=steps,
            rationale=(
                f"Chain composed for domain={intent.domain.value} with "
                f"{len(steps)} steps."
            ),
        )
