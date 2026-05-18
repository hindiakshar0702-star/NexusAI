"""Platform adapters.

Each adapter takes a domain-built prompt body and tunes it for the target
platform's prompting conventions (negative prompts, sliders, syntax, etc.).
"""
from __future__ import annotations

from typing import Callable, Dict

from ..types import Domain, Platform


# An adapter takes (text, domain) and returns (system_prompt, user_prompt, parameters)
Adapter = Callable[[str, Domain], "AdaptedPrompt"]


from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdaptedPrompt:
    user: str
    system: str = ""
    negative: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


def _chatgpt(text: str, domain: Domain) -> AdaptedPrompt:
    system = (
        "You are a senior expert. Reason step by step internally, but only "
        "share the final answer with the user. If a fact is uncertain, say so."
    )
    return AdaptedPrompt(
        user=text,
        system=system,
        parameters={"temperature": 0.4, "top_p": 0.9},
        notes="Best for instruction-following and reasoning.",
    )


def _claude(text: str, domain: Domain) -> AdaptedPrompt:
    system = (
        "You are a careful, helpful expert. Use XML tags to structure your "
        "answer when it improves clarity (<plan>, <answer>)."
    )
    body = (
        f"<task>\n{text}\n</task>\n\n"
        f"<instructions>\n"
        f"1. Briefly outline a plan inside <plan>.\n"
        f"2. Produce the final deliverable inside <answer>.\n"
        f"</instructions>"
    )
    return AdaptedPrompt(
        user=body,
        system=system,
        parameters={"temperature": 0.3},
        notes="Claude responds well to XML-tagged structure.",
    )


def _gemini(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nFormat your answer with clear headings and short paragraphs.",
        parameters={"temperature": 0.5},
        notes="Gemini benefits from explicit formatting cues.",
    )


def _midjourney(text: str, domain: Domain) -> AdaptedPrompt:
    # Strip natural-language framing and convert to comma-separated descriptors.
    descriptors = ", ".join(
        line.strip(" -*").strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().lower().startswith(("goal:", "audience:", "tone:", "deliver:", "direction:"))
    )
    descriptors = descriptors[:1500]  # safety
    flags = "--ar 16:9 --style raw --v 6"
    return AdaptedPrompt(
        user=f"{descriptors} {flags}",
        notes="Midjourney prefers comma-delimited descriptors and trailing flags.",
        parameters={"aspect_ratio": "16:9", "version": 6},
    )


def _stable_diffusion(text: str, domain: Domain) -> AdaptedPrompt:
    positive = ", ".join(
        line.strip(" -*").strip() for line in text.splitlines() if line.strip()
    )[:1500]
    negative = (
        "blurry, low quality, deformed anatomy, extra limbs, watermark, "
        "text artifacts, jpeg artifacts, oversaturated"
    )
    return AdaptedPrompt(
        user=positive,
        negative=negative,
        parameters={"steps": 30, "cfg_scale": 6.5, "sampler": "DPM++ 2M Karras"},
        notes="Stable Diffusion needs an explicit negative prompt.",
    )


def _leonardo(text: str, domain: Domain) -> AdaptedPrompt:
    base = _stable_diffusion(text, domain)
    base.notes = "Leonardo Phoenix model accepts SD-style positive/negative prompts."
    return base


def _runway(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nMotion: continuous shot, no cuts. Duration: 5 seconds.",
        parameters={"duration_seconds": 5, "fps": 24, "aspect_ratio": "16:9"},
        notes="Runway Gen-3 is shot-list aware. Keep camera direction explicit.",
    )


def _sora(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nLength: 8 seconds. Single continuous take.",
        parameters={"duration_seconds": 8, "aspect_ratio": "16:9"},
        notes="Sora benefits from explicit shot duration and continuity constraints.",
    )


def _figma(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nUse auto-layout frames. Reference shared design tokens for color, type, spacing.",
        notes="Figma AI works best with explicit layout and token references.",
    )


def _v0(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nImplement as React components with Tailwind classes. "
                    "Make it responsive and accessible (semantic HTML, focus rings).",
        notes="v0 expects component-shaped requests.",
    )


def _bolt(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nScaffold a runnable project. State the stack, dependencies, "
                    "and entry command.",
        notes="Bolt builds full runnable projects.",
    )


def _cursor(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(
        user=text + "\n\nWrite production-quality code with explicit types and "
                    "include unit tests covering edge cases.",
        notes="Cursor works best when the request includes tests and edge cases.",
    )


def _generic(text: str, domain: Domain) -> AdaptedPrompt:
    return AdaptedPrompt(user=text)


_ADAPTERS: Dict[Platform, Adapter] = {
    Platform.CHATGPT: _chatgpt,
    Platform.CLAUDE: _claude,
    Platform.GEMINI: _gemini,
    Platform.MIDJOURNEY: _midjourney,
    Platform.STABLE_DIFFUSION: _stable_diffusion,
    Platform.LEONARDO: _leonardo,
    Platform.RUNWAY: _runway,
    Platform.SORA: _sora,
    Platform.FIGMA: _figma,
    Platform.V0: _v0,
    Platform.BOLT: _bolt,
    Platform.CURSOR: _cursor,
    Platform.GENERIC: _generic,
}


def adapt(text: str, platform: Platform, domain: Domain) -> AdaptedPrompt:
    adapter = _ADAPTERS.get(platform, _generic)
    return adapter(text, domain)


def supported_platforms() -> list:
    return list(_ADAPTERS.keys())
