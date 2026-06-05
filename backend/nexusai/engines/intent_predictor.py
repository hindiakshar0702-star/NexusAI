"""Intent prediction.

Given a short, possibly underspecified user idea, infer:
  * domain (text/image/video/code/etc.)
  * target platform (ChatGPT, Midjourney, ...)
  * audience, tone, emotional register
  * goals and constraints
  * what details are *missing* and worth asking about

The implementation is rule-based (keyword tables + scoring), intentionally
deterministic so callers can rely on it without an external API key. Replace
`predict` with an LLM call when ready.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..types import Domain, Intent, Platform


# ---------------------------------------------------------------- keyword maps
_DOMAIN_KEYWORDS: Dict[Domain, List[str]] = {
    Domain.IMAGE: [
        "image", "photo", "picture", "illustration", "art", "render", "portrait",
        "concept art", "logo", "poster", "wallpaper", "scene", "character design",
        "cyberpunk", "samurai", "fantasy art", "anime",
    ],
    Domain.VIDEO: ["video", "footage", "cinematic shot", "trailer", "b-roll", "vfx"],
    Domain.ANIMATION: ["animation", "motion graphic", "animated", "loop", "lottie"],
    Domain.UI_UX: [
        "ui", "ux", "interface", "screen", "dashboard", "wireframe", "mockup",
        "design system", "component",
    ],
    Domain.WEBSITE: ["website", "landing page", "homepage", "marketing site"],
    Domain.APP: ["mobile app", "ios app", "android app", "react native"],
    Domain.VOICE: ["voiceover", "tts", "speech synthesis", "narration", "podcast voice"],
    Domain.MUSIC: ["music", "song", "soundtrack", "beat", "melody", "lyrics"],
    Domain.THREE_D: ["3d model", "blender", "three.js", "obj", "glb"],
    Domain.GAME: ["game", "level design", "npc", "quest", "game mechanic"],
    Domain.CODE: [
        "code", "function", "class", "refactor", "bug", "api", "endpoint",
        "schema", "regex", "sql", "typescript", "python",
    ],
    Domain.MARKETING: [
        "ad copy", "advertisement", "ads", "campaign", "headline", "tagline", "seo",
        "email sequence", "linkedin post", "twitter post", "tweet", "thread",
        "landing copy", "marketing copy", "cold email",
    ],
    Domain.STORYTELLING: ["story", "novel", "screenplay", "scene", "character arc"],
    Domain.TRAINING: [
        "fine-tune", "fine tuning", "dataset", "synthetic data", "evaluation",
        "rl reward", "reinforcement learning",
    ],
}

_PLATFORM_KEYWORDS: Dict[Platform, List[str]] = {
    Platform.CHATGPT: ["chatgpt", "gpt-4", "gpt"],
    Platform.CLAUDE: ["claude", "anthropic"],
    Platform.GEMINI: ["gemini", "bard"],
    Platform.MIDJOURNEY: ["midjourney", "mj"],
    Platform.STABLE_DIFFUSION: ["stable diffusion", "sdxl", "automatic1111", "comfyui"],
    Platform.LEONARDO: ["leonardo"],
    Platform.RUNWAY: ["runway", "gen-3", "gen 3"],
    Platform.SORA: ["sora"],
    Platform.FIGMA: ["figma"],
    Platform.V0: ["v0", "v0.dev"],
    Platform.BOLT: ["bolt.new", "bolt "],
    Platform.CURSOR: ["cursor"],
}

_TONE_KEYWORDS: Dict[str, List[str]] = {
    "playful": ["fun", "playful", "quirky", "whimsical"],
    "professional": ["professional", "corporate", "b2b", "enterprise"],
    "cinematic": ["cinematic", "dramatic", "epic", "movie"],
    "minimalist": ["minimal", "minimalist", "clean", "simple"],
    "luxury": ["luxury", "premium", "high-end"],
    "futuristic": ["futuristic", "sci-fi", "cyberpunk", "neon"],
    "warm": ["warm", "cozy", "friendly", "approachable"],
    "urgent": ["urgent", "limited time", "now", "today"],
}

_EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "joy": ["happy", "joyful", "fun"],
    "awe": ["awe", "wonder", "majestic", "epic"],
    "trust": ["trust", "reliable", "secure"],
    "excitement": ["exciting", "thrilling", "energetic"],
    "calm": ["calm", "peaceful", "serene"],
    "tension": ["tense", "suspense", "dark"],
}

_AUDIENCE_HINTS: List[Tuple[str, str]] = [
    (r"\b(children|kids|toddler)\b", "children"),
    (r"\b(teenager|teen|gen[\s-]?z)\b", "teens"),
    (r"\b(developer|engineer|programmer|coder)\b", "developers"),
    (r"\b(designer|ui designer|ux designer)\b", "designers"),
    (r"\b(founder|startup|entrepreneur)\b", "founders"),
    (r"\b(marketer|growth)\b", "marketers"),
    (r"\b(enterprise|b2b|cio|cto)\b", "enterprise buyers"),
    (r"\b(consumer|shopper|buyer)\b", "consumers"),
]


def _score_match(text: str, keywords: List[str]) -> int:
    """Score keyword presence with word-boundary respect.

    Single-word keywords must match as whole words (so 'ad' won't match 'already').
    Multi-word keywords match as a phrase (with space-tolerant boundaries).
    """
    score = 0
    lowered = text.lower()
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if not kw_clean:
            continue
        if " " in kw_clean:
            # Phrase: anchor on a word boundary at the start.
            pattern = r"(?<![a-z0-9])" + re.escape(kw_clean) + r"(?![a-z0-9])"
            if re.search(pattern, lowered):
                score += 2
        else:
            pattern = r"\b" + re.escape(kw_clean) + r"\b"
            if re.search(pattern, lowered):
                score += 1
    return score


class IntentPredictor:
    """Predict user intent from a short raw idea."""

    def predict(self, raw_idea: str, hint_domain: Domain | None = None,
                hint_platform: Platform | None = None) -> Intent:
        text = raw_idea.strip()
        if not text:
            raise ValueError("raw_idea must be non-empty")

        domain = hint_domain or self._predict_domain(text, hint_platform)
        platform = hint_platform or self._predict_platform(text, domain)
        tone = self._predict_tone(text)
        emotions = self._predict_emotions(text)
        audience = self._predict_audience(text)
        goals = self._predict_goals(text, domain)
        constraints = self._predict_constraints(text)
        missing = self._missing_details(text, domain)

        # confidence ~ how many signals matched
        signal_count = sum([
            bool(emotions), tone != "neutral", audience != "general",
            bool(goals), bool(_score_match(text, sum(_DOMAIN_KEYWORDS.values(), []))),
        ])
        confidence = min(1.0, 0.4 + 0.12 * signal_count)

        return Intent(
            raw_idea=text,
            domain=domain,
            platform=platform,
            audience=audience,
            tone=tone,
            goals=goals,
            emotions=emotions,
            constraints=constraints,
            missing_details=missing,
            confidence=round(confidence, 2),
        )

    # ------------------------------------------------------------- predictors
    _PLATFORM_DOMAINS = {
        Platform.MIDJOURNEY: Domain.IMAGE,
        Platform.STABLE_DIFFUSION: Domain.IMAGE,
        Platform.LEONARDO: Domain.IMAGE,
        Platform.RUNWAY: Domain.VIDEO,
        Platform.SORA: Domain.VIDEO,
        Platform.FIGMA: Domain.UI_UX,
        Platform.V0: Domain.WEBSITE,
        Platform.BOLT: Domain.APP,
        Platform.CURSOR: Domain.CODE,
    }

    def _predict_domain(self, text: str, hint_platform: Platform | None = None) -> Domain:
        # Prefer keyword evidence when present; otherwise fall back to platform hint.
        best_domain = Domain.TEXT
        best_score = 0
        for domain, kws in _DOMAIN_KEYWORDS.items():
            s = _score_match(text, kws)
            if s > best_score:
                best_score = s
                best_domain = domain
        if best_score == 0 and hint_platform is not None:
            return self._PLATFORM_DOMAINS.get(hint_platform, Domain.TEXT)
        return best_domain

    def _predict_platform(self, text: str, domain: Domain) -> Platform:
        for platform, kws in _PLATFORM_KEYWORDS.items():
            if _score_match(text, kws) > 0:
                return platform
        # sensible defaults per domain
        defaults = {
            Domain.IMAGE: Platform.MIDJOURNEY,
            Domain.VIDEO: Platform.RUNWAY,
            Domain.ANIMATION: Platform.RUNWAY,
            Domain.UI_UX: Platform.FIGMA,
            Domain.WEBSITE: Platform.V0,
            Domain.APP: Platform.BOLT,
            Domain.CODE: Platform.CURSOR,
        }
        return defaults.get(domain, Platform.CHATGPT)

    def _predict_tone(self, text: str) -> str:
        best_tone = "neutral"
        best_score = 0
        for tone, kws in _TONE_KEYWORDS.items():
            s = _score_match(text, kws)
            if s > best_score:
                best_tone = tone
                best_score = s
        return best_tone

    def _predict_emotions(self, text: str) -> List[str]:
        emotions = []
        for emotion, kws in _EMOTION_KEYWORDS.items():
            if _score_match(text, kws) > 0:
                emotions.append(emotion)
        return emotions

    def _predict_audience(self, text: str) -> str:
        for pattern, label in _AUDIENCE_HINTS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return label
        return "general"

    def _predict_goals(self, text: str, domain: Domain) -> List[str]:
        goals: List[str] = []
        lowered = text.lower()
        if any(w in lowered for w in ["sell", "convert", "signup", "sign up", "buy"]):
            goals.append("drive conversion")
        if any(w in lowered for w in ["explain", "teach", "learn", "tutorial"]):
            goals.append("educate the audience")
        if any(w in lowered for w in ["inspire", "wow", "impress"]):
            goals.append("create emotional impact")
        if any(w in lowered for w in ["debug", "fix", "error"]):
            goals.append("diagnose and fix a problem")
        if not goals:
            # Domain-specific fallbacks
            goals.append({
                Domain.IMAGE: "produce a visually striking image",
                Domain.VIDEO: "produce an engaging short-form video",
                Domain.UI_UX: "produce a clean, conversion-ready interface",
                Domain.CODE: "produce correct, readable code",
                Domain.MARKETING: "produce persuasive marketing copy",
                Domain.STORYTELLING: "produce an engaging narrative",
            }.get(domain, "produce a high-quality output"))
        return goals

    def _predict_constraints(self, text: str) -> List[str]:
        constraints: List[str] = []
        lowered = text.lower()
        m = re.search(r"\bunder\s+(\d+)\s*(words?|chars?|characters?|tokens?)\b", lowered)
        if m:
            constraints.append(f"length under {m.group(1)} {m.group(2)}")
        if "no jargon" in lowered:
            constraints.append("avoid jargon")
        if any(w in lowered for w in ["no copyright", "royalty-free", "original"]):
            constraints.append("avoid copyrighted material")
        if "responsive" in lowered:
            constraints.append("must be responsive on mobile and desktop")
        return constraints

    def _missing_details(self, text: str, domain: Domain) -> List[str]:
        ask: List[str] = []
        lowered = text.lower()

        # Generic gaps
        if not re.search(r"\b(audience|users|customers|for\s+\w+)\b", lowered):
            ask.append("Who is the target audience?")
        if domain in {Domain.IMAGE, Domain.VIDEO, Domain.ANIMATION}:
            if not any(w in lowered for w in ["style", "lighting", "camera", "lens"]):
                ask.append("What art style, lighting and camera framing do you want?")
            if not any(w in lowered for w in ["aspect ratio", "16:9", "9:16", "1:1", "square"]):
                ask.append("What aspect ratio should the output use?")
        if domain == Domain.UI_UX:
            if "color" not in lowered and "palette" not in lowered:
                ask.append("Any preferred color palette or brand colors?")
            if "platform" not in lowered and "device" not in lowered:
                ask.append("Web, mobile, or both?")
        if domain == Domain.CODE:
            if "language" not in lowered and not re.search(r"\b(python|typescript|javascript|go|rust|java)\b", lowered):
                ask.append("Which programming language and runtime?")
            if "test" not in lowered:
                ask.append("Should I include unit tests?")
        if domain == Domain.MARKETING:
            if "channel" not in lowered and "platform" not in lowered:
                ask.append("Which channel: email, LinkedIn, X, ad copy, landing page?")
        return ask
