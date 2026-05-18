"""Variety engine for generating diverse synthetic ideas.

NexusAI's PromptEngine is deterministic (same input -> same output), which is
great for testing but bad for training data: a fine-tuned model needs to see
many *different* shapes of input. This module produces synthetic raw ideas
across all 15 domains, with randomized skill levels, tones, audiences, and
edge cases (vague inputs, multilingual, very short, very long).

The implementation is dependency-free (stdlib only) and seeded for
reproducibility.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from ..types import Domain, Platform, SkillLevel


# Per-domain idea seeds. These are realistic short user prompts that map to
# the domain, ranging from vague ("a cool image") to detailed ("cinematic 8s
# clip of robot..."). Variety here directly determines training generalization.
_DOMAIN_IDEAS: dict[Domain, List[str]] = {
    Domain.TEXT: [
        "explain quantum computing to a high schooler",
        "summarize the french revolution in 3 paragraphs",
        "write a haiku about late summer evenings",
        "rewrite this email to sound more confident",
        "explain attention mechanism in transformers",
        "compare stoicism and buddhism",
        "write release notes for a bug fix",
        "explain why the sky is blue to a child",
    ],
    Domain.IMAGE: [
        "cyberpunk samurai on neon rooftop in tokyo",
        "watercolor portrait of an old fisherman at dawn",
        "photorealistic close-up of a hummingbird mid-flight",
        "minimalist logo for a coffee subscription startup",
        "concept art for a floating island city",
        "isometric illustration of a developer's workspace",
        "fantasy book cover for a dragon-rider epic",
        "moody black and white street photography in mumbai monsoon",
    ],
    Domain.VIDEO: [
        "cinematic 8s clip of a robot sipping espresso in paris",
        "drone shot of mountain village waking up at sunrise",
        "slow motion ink dropping into water",
        "product reveal for a sleek smart watch",
        "trailer for a sci-fi thriller about memory",
        "b-roll of a busy chef plating a dish",
        "first-person motorcycle ride through tokyo at night",
        "stop motion of paper origami coming to life",
    ],
    Domain.ANIMATION: [
        "loading spinner with bouncing dots in brand colors",
        "page transition that feels like turning a magazine page",
        "animated logo reveal for a fintech startup",
        "lottie animation of an empty inbox state",
        "hover effect on a pricing card",
        "parallax hero scroll for a portfolio site",
        "card flip animation revealing back content",
        "menu open animation with staggered children",
    ],
    Domain.UI_UX: [
        "design a saas dashboard for analytics with futuristic vibe",
        "settings screen for a meditation app",
        "checkout flow for a luxury fashion brand",
        "onboarding for a developer tool",
        "admin panel for managing user permissions",
        "mobile-first signup flow with social login",
        "calendar interface for booking interviews",
        "kanban board with drag and drop and dark mode",
    ],
    Domain.WEBSITE: [
        "landing page for an ai test runner saas",
        "marketing site for a meal kit startup targeting families",
        "homepage for a personal portfolio of a 3d artist",
        "product page for a $200 leather bag",
        "agency website for a boutique design studio",
        "saas pricing page with three tiers and annual discount",
        "documentation site for an open source library",
        "coming-soon page for a private beta",
    ],
    Domain.APP: [
        "habit tracker app with streaks and reminders",
        "expense splitter for friends on a trip",
        "language learning app with daily 5 minute lessons",
        "ios app for tracking gym progressive overload",
        "android app for plant care reminders",
        "react native app for journaling with mood tracking",
        "meditation app with offline guided sessions",
        "recipe app that suggests meals from fridge contents",
    ],
    Domain.VOICE: [
        "voiceover for a 30s product ad for noise cancelling headphones",
        "narration for a meditation breathing exercise",
        "intro voice for a true crime podcast",
        "tts script for an airport announcement",
        "audiobook narration for a fantasy chapter opening",
        "voice prompt for a smart home assistant",
        "phone IVR menu for a small business",
        "elearning narrator explaining photosynthesis",
    ],
    Domain.MUSIC: [
        "lofi hip hop track for late night coding",
        "epic orchestral cue for a fantasy battle",
        "upbeat indie pop song about summer road trips",
        "ambient soundscape for a meditation app",
        "synthwave track for a retro video game",
        "acoustic folk ballad about leaving home",
        "trap beat for a workout playlist",
        "cinematic trailer music with rising tension",
    ],
    Domain.THREE_D: [
        "3d model of a stylized treasure chest for a game",
        "blender scene of a cozy bookshop interior",
        "low poly character of a wizard for mobile rpg",
        "3d render of a futuristic motorcycle",
        "glb asset of a coffee cup with steam particles",
        "topology-clean character head for animation",
        "3d product visualization of a perfume bottle",
        "voxel art scene of a tiny village",
    ],
    Domain.GAME: [
        "puzzle game where you bend physics to escape rooms",
        "roguelike deckbuilder with cooking theme",
        "platformer where the world rewinds when you die",
        "incremental idle game about building a galactic empire",
        "narrative adventure about a detective with amnesia",
        "city builder where every citizen has a real name and goals",
        "horror game with a single fixed camera",
        "competitive multiplayer card game with bluffing",
    ],
    Domain.CODE: [
        "fix this python bug where list comprehension throws KeyError",
        "write typescript function to debounce async calls",
        "refactor this react component to use hooks",
        "regex to extract emails from a messy log file",
        "sql query for top 5 customers by revenue last quarter",
        "implement a thread-safe LRU cache in go",
        "write rust function to parse a json config file",
        "convert this callback-based code to async/await",
    ],
    Domain.MARKETING: [
        "ad copy for a b2b saas that helps founders track churn",
        "linkedin post announcing a series A raise",
        "cold email sequence for selling design services to ecommerce brands",
        "twitter thread teaching the basics of prompt engineering",
        "headline for a black friday sale on premium headphones",
        "landing copy for a meditation app trial",
        "google ad for a local plumber in austin",
        "email subject lines for a saas onboarding sequence",
    ],
    Domain.STORYTELLING: [
        "short story about a lighthouse keeper who finds a message in a bottle",
        "screenplay scene where two ex-friends meet 10 years later",
        "novel opening chapter about a city that runs on dreams",
        "fairy tale about a fox who learns to share",
        "thriller plot about a hacker who discovers an ai is alive",
        "character backstory for a tired bounty hunter",
        "scene where a parent tells their child the truth",
        "drabble (100 words) about losing and finding hope",
    ],
    Domain.TRAINING: [
        "fine-tune a model to classify product reviews by sentiment",
        "synthetic dataset for teaching an llm to write SQL",
        "evaluation rubric for code generation models",
        "rl reward function for a customer support chatbot",
        "curriculum learning plan for math word problems",
        "synthetic data plan for a medical triage classifier",
        "eval harness for testing prompt injection resistance",
        "fine tune dataset for converting english to formal hindi",
    ],
}

# Common modifiers that we randomly append/prepend to ideas to teach the model
# how to handle additional context.
_TONE_MODIFIERS = [
    "minimalist", "playful", "luxury", "futuristic", "cinematic",
    "warm", "professional", "urgent", "sci-fi", "cyberpunk", "cozy",
]
_AUDIENCE_MODIFIERS = [
    "for developers", "for designers", "for founders", "for teens",
    "for enterprise buyers", "for marketers", "for kids", "for beginners",
]
_PLATFORM_MODIFIERS = [
    ("midjourney", Platform.MIDJOURNEY),
    ("for stable diffusion", Platform.STABLE_DIFFUSION),
    ("for sora", Platform.SORA),
    ("on figma", Platform.FIGMA),
    ("with v0", Platform.V0),
    ("using cursor", Platform.CURSOR),
]

# Edge cases that intentionally stress the system. A robust trained model
# should still produce reasonable output for these.
_EDGE_CASE_IDEAS = [
    "make it cool",
    "something nice",
    "idk just be creative",
    "do the thing",
    "kuch achha bana do",  # multilingual
    "design something for me",
    "write me stuff",
    "make it pop",
]


@dataclass
class SyntheticIdea:
    """One synthetic raw idea ready to feed into PromptEngine.generate()."""
    raw_idea: str
    domain: Optional[Domain] = None
    platform: Optional[Platform] = None
    skill_level: SkillLevel = SkillLevel.ADVANCED
    is_edge_case: bool = False
    tags: List[str] = field(default_factory=list)


class VarietyEngine:
    """Generate diverse synthetic ideas for training data."""

    def __init__(self, seed: int = 42, edge_case_ratio: float = 0.08) -> None:
        """
        Args:
            seed: RNG seed for reproducibility.
            edge_case_ratio: Fraction of generated ideas that are intentionally
                vague edge cases (default 8%).
        """
        self._rng = random.Random(seed)
        self._edge_case_ratio = edge_case_ratio

    def generate(self, n: int, domains: Optional[List[Domain]] = None) -> List[SyntheticIdea]:
        """Generate n diverse synthetic ideas.

        Distribution:
            - ~`edge_case_ratio` fraction are intentionally vague edge cases.
            - The rest are sampled across the requested domains, with random
              tone/audience/platform modifiers applied to roughly half.
        """
        return list(self.iter_ideas(n, domains))

    def iter_ideas(self, n: int, domains: Optional[List[Domain]] = None) -> Iterator[SyntheticIdea]:
        active_domains = list(domains) if domains else list(_DOMAIN_IDEAS.keys())
        # Filter to only domains we have seeds for (defensive).
        active_domains = [d for d in active_domains if d in _DOMAIN_IDEAS]
        if not active_domains:
            raise ValueError("No valid domains provided.")

        n_edge = int(n * self._edge_case_ratio)
        n_normal = n - n_edge

        # Round-robin across domains so we don't end up imbalanced.
        for i in range(n_normal):
            domain = active_domains[i % len(active_domains)]
            yield self._make_normal_idea(domain)

        for _ in range(n_edge):
            yield self._make_edge_case()

    def _make_normal_idea(self, domain: Domain) -> SyntheticIdea:
        seeds = _DOMAIN_IDEAS[domain]
        base = self._rng.choice(seeds)

        # ~50% chance to add a tone modifier
        tags: List[str] = [domain.value]
        if self._rng.random() < 0.5:
            tone = self._rng.choice(_TONE_MODIFIERS)
            base = f"{tone} {base}"
            tags.append(f"tone:{tone}")

        # ~30% chance to add an audience modifier
        if self._rng.random() < 0.3:
            audience = self._rng.choice(_AUDIENCE_MODIFIERS)
            base = f"{base} {audience}"
            tags.append("audience-cued")

        # ~25% chance to specify a platform inline (model learns platform routing)
        platform: Optional[Platform] = None
        if self._rng.random() < 0.25:
            phrase, platform = self._rng.choice(_PLATFORM_MODIFIERS)
            base = f"{base} {phrase}"
            tags.append(f"platform:{platform.value}")

        # Random skill level so model learns all 3 tiers
        skill = self._rng.choice(list(SkillLevel))

        return SyntheticIdea(
            raw_idea=base,
            domain=domain,
            platform=platform,
            skill_level=skill,
            is_edge_case=False,
            tags=tags,
        )

    def _make_edge_case(self) -> SyntheticIdea:
        idea = self._rng.choice(_EDGE_CASE_IDEAS)
        return SyntheticIdea(
            raw_idea=idea,
            domain=None,           # let predictor figure it out
            platform=None,
            skill_level=self._rng.choice(list(SkillLevel)),
            is_edge_case=True,
            tags=["edge-case"],
        )

    @property
    def total_seed_count(self) -> int:
        """Total number of unique seed ideas available across all domains."""
        return sum(len(v) for v in _DOMAIN_IDEAS.values()) + len(_EDGE_CASE_IDEAS)
