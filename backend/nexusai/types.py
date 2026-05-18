"""Shared types and enums used across NexusAI engines.

Kept dependency-free (stdlib only) so engines can be imported cheaply.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid


class Domain(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ANIMATION = "animation"
    UI_UX = "ui_ux"
    WEBSITE = "website"
    APP = "app"
    VOICE = "voice"
    MUSIC = "music"
    THREE_D = "3d"
    GAME = "game"
    CODE = "code"
    MARKETING = "marketing"
    STORYTELLING = "storytelling"
    TRAINING = "training"


class Platform(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    MIDJOURNEY = "midjourney"
    STABLE_DIFFUSION = "stable_diffusion"
    LEONARDO = "leonardo"
    RUNWAY = "runway"
    SORA = "sora"
    FIGMA = "figma"
    V0 = "v0"
    BOLT = "bolt"
    CURSOR = "cursor"
    GENERIC = "generic"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    ADVANCED = "advanced"
    PRO = "pro"


@dataclass
class Intent:
    """Inferred user intent for a raw idea."""

    raw_idea: str
    domain: Domain
    platform: Platform
    audience: str
    tone: str
    goals: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    missing_details: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["domain"] = self.domain.value
        d["platform"] = self.platform.value
        return d


@dataclass
class PromptScore:
    clarity: float
    specificity: float
    creativity: float
    realism: float
    safety: float
    platform_fit: float
    overall: float
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Prompt:
    """A generated prompt artifact."""

    id: str
    text: str
    domain: Domain
    platform: Platform
    skill_level: SkillLevel
    title: str = ""
    system: Optional[str] = None
    negative: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    rationale: str = ""
    score: Optional[PromptScore] = None
    parent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:12]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["domain"] = self.domain.value
        d["platform"] = self.platform.value
        d["skill_level"] = self.skill_level.value
        if self.score is not None:
            d["score"] = self.score.to_dict()
        return d


@dataclass
class ChainStep:
    name: str
    purpose: str
    prompt: Prompt
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "prompt": self.prompt.to_dict(),
            "depends_on": self.depends_on,
        }


@dataclass
class PromptChain:
    id: str
    goal: str
    steps: List[ChainStep]
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "rationale": self.rationale,
        }


@dataclass
class SafetyReport:
    safe: bool
    severity: str  # "none" | "low" | "medium" | "high"
    flags: List[str]
    redacted_text: Optional[str] = None
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
