"""Pydantic schemas for the FastAPI surface."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..types import Domain, Platform, SkillLevel


class GenerateRequest(BaseModel):
    raw_idea: str = Field(..., min_length=2, description="Short user idea.")
    domain: Optional[Domain] = None
    platform: Optional[Platform] = None
    skill_level: SkillLevel = SkillLevel.ADVANCED
    include_negative: bool = True


class GenerateTieredRequest(BaseModel):
    raw_idea: str = Field(..., min_length=2)
    domain: Optional[Domain] = None
    platform: Optional[Platform] = None


class IntentRequest(BaseModel):
    raw_idea: str = Field(..., min_length=2)
    domain: Optional[Domain] = None
    platform: Optional[Platform] = None


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    platform: Platform = Platform.GENERIC


class OptimizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    domain: Domain = Domain.TEXT
    platform: Platform = Platform.GENERIC


class ChainRequest(BaseModel):
    raw_idea: str = Field(..., min_length=2)
    skill_level: SkillLevel = SkillLevel.ADVANCED
    platform: Optional[Platform] = None


class EvolveRequest(BaseModel):
    text: str
    domain: Domain = Domain.TEXT
    platform: Platform = Platform.GENERIC
    skill_level: SkillLevel = SkillLevel.ADVANCED
    generations: int = Field(default=3, ge=1, le=8)
    feedback_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AgentsRequest(BaseModel):
    raw_idea: str = Field(..., min_length=2)
    skill_level: SkillLevel = SkillLevel.ADVANCED


class FeedbackRequest(BaseModel):
    prompt_id: str
    score: float = Field(..., ge=0.0, le=1.0)


class TemplateRenderRequest(BaseModel):
    template_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class DatasetRequest(BaseModel):
    task: str = Field(..., min_length=2)
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    n_per_difficulty: int = Field(default=3, ge=1, le=20)


class EvalRequest(BaseModel):
    task_type: str = "generation"
    custom_thresholds: Optional[Dict[str, float]] = None


class RewardRequest(BaseModel):
    task: str = Field(..., min_length=2)


class SafetyRequest(BaseModel):
    text: str = Field(..., min_length=1)
