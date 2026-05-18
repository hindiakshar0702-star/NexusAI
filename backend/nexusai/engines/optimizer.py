"""Prompt optimizer.

Applies deterministic rewrites to a prompt to improve the dimensions surfaced
by the analyzer:

* expand vague filler words into concrete asks
* add missing platform-specific cues
* attach guardrails that reduce hallucinations
* layer in tone / sensory anchors when creativity is low

Optimization is idempotent: calling `optimize` repeatedly converges quickly.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from ..types import Domain, Platform


_FILLER_REWRITES: List[Tuple[str, str]] = [
    (r"\bthings?\b", "specific elements"),
    (r"\bstuff\b", "specific elements"),
    (r"\bnice\b", "well-crafted"),
    (r"\bgood\b", "high-quality"),
    (r"\bcool\b", "visually compelling"),
    (r"\bvery\s+", ""),
    (r"\breally\s+", ""),
    (r"\bbe\s+creative\b", "explore an unexpected angle"),
]

_PLATFORM_AUGMENTS = {
    Platform.MIDJOURNEY: " --ar 16:9 --style raw --v 6",
    Platform.STABLE_DIFFUSION: "\nNegative prompt: blurry, low quality, deformed, watermark",
    Platform.RUNWAY: "\nCamera: slow dolly-in, 24fps, cinematic depth of field.",
    Platform.SORA: "\nScene length: 8 seconds. Single continuous shot.",
    Platform.V0: "\nUse Tailwind classes, responsive layout, accessible markup.",
    Platform.BOLT: "\nScaffold a runnable project. Specify the stack and entry command.",
    Platform.CURSOR: "\nInclude unit tests and explicit type annotations.",
    Platform.FIGMA: "\nUse auto-layout frames and reference design tokens.",
}

_DOMAIN_GUARDRAILS = {
    Domain.CODE: (
        "If a requirement is ambiguous, list your assumption explicitly before "
        "writing code."
    ),
    Domain.TEXT: (
        "If you are unsure of a fact, say so rather than guessing."
    ),
    Domain.MARKETING: (
        "Avoid superlatives that are not backed by a measurable claim."
    ),
    Domain.IMAGE: (
        "Avoid copyrighted characters, logos, or trademarks."
    ),
}


class PromptOptimizer:
    def optimize(self, text: str, domain: Domain, platform: Platform) -> str:
        if not text.strip():
            return text
        out = text

        # 1) replace filler words
        for pattern, repl in _FILLER_REWRITES:
            out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

        # 2) collapse repeated whitespace introduced by removals
        out = re.sub(r"\s{2,}", " ", out).strip()

        # 3) add a guardrail line if not present
        guardrail = _DOMAIN_GUARDRAILS.get(domain)
        if guardrail and guardrail not in out:
            out = f"{out}\n\nGuardrails: {guardrail}"

        # 4) add platform-native suffixes if not present
        suffix = _PLATFORM_AUGMENTS.get(platform)
        if suffix and suffix.strip() not in out:
            out = f"{out}{suffix}"

        return out

    def make_variations(self, text: str, n: int = 3) -> List[str]:
        """Produce N stylistic variants without changing meaning."""
        variants = []
        anchors = [
            "Tone: precise and minimal.",
            "Tone: vivid and sensory.",
            "Tone: cinematic and emotional.",
            "Tone: data-driven and skeptical.",
        ]
        for i in range(n):
            anchor = anchors[i % len(anchors)]
            variants.append(f"{text}\n\n{anchor}")
        return variants
