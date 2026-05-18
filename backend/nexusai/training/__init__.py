"""AI training automation utilities.

Provides:
  * SyntheticDatasetGenerator – schema-driven synthetic example generation.
  * EvalSuiteBuilder          – build an evaluation rubric + held-out tasks.
  * RewardScenarioBuilder     – RL reward + anti-gaming penalty templates.
  * VarietyEngine             – diverse synthetic ideas for fine-tuning data.
  * FineTuneDataExporter      – produce JSONL datasets in 4 formats.
  * GPT4Teacher               – optional output polisher via OpenAI API.

These do not call any external model unless explicitly enabled
(GPT4Teacher). They produce structured artifacts (JSON-friendly dicts) that
downstream training code can consume.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Re-exports for the fine-tuning pipeline.
from .exporter import (  # noqa: F401
    DEFAULT_SYSTEM_PROMPT,
    ExportConfig,
    ExportStats,
    FineTuneDataExporter,
    Format,
    export_training_data,
)
from .teacher import GPT4Teacher, TeacherStats, is_available as teacher_is_available  # noqa: F401
from .variety import SyntheticIdea, VarietyEngine  # noqa: F401


@dataclass
class SyntheticExample:
    input: Dict[str, Any]
    output: Dict[str, Any]
    difficulty: str = "easy"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }


class SyntheticDatasetGenerator:
    """Generate deterministic synthetic examples from a schema."""

    DIFFICULTIES = ("easy", "medium", "hard")

    def generate(
        self,
        task: str,
        input_schema: Dict[str, str],
        output_schema: Dict[str, str],
        n_per_difficulty: int = 3,
        seed: int = 42,
    ) -> List[SyntheticExample]:
        rng = random.Random(seed)
        examples: List[SyntheticExample] = []
        for difficulty in self.DIFFICULTIES:
            for i in range(n_per_difficulty):
                examples.append(
                    SyntheticExample(
                        input=self._sample(input_schema, difficulty, i, rng),
                        output=self._sample(output_schema, difficulty, i, rng),
                        difficulty=difficulty,
                        tags=[task, difficulty],
                    )
                )
        return examples

    def _sample(
        self,
        schema: Dict[str, str],
        difficulty: str,
        idx: int,
        rng: random.Random,
    ) -> Dict[str, Any]:
        sample: Dict[str, Any] = {}
        for field_name, type_hint in schema.items():
            sample[field_name] = self._value_for(field_name, type_hint, difficulty, idx, rng)
        return sample

    @staticmethod
    def _value_for(field_name: str, type_hint: str, difficulty: str, idx: int,
                   rng: random.Random) -> Any:
        type_hint = type_hint.lower()
        if type_hint in ("str", "string", "text"):
            tail = {"easy": "simple", "medium": "ambiguous", "hard": "adversarial"}[difficulty]
            return f"{field_name}_{tail}_{idx}"
        if type_hint in ("int", "integer", "number"):
            base = {"easy": 10, "medium": 100, "hard": 10_000}[difficulty]
            return rng.randint(0, base)
        if type_hint in ("float", "double"):
            return round(rng.random() * (idx + 1), 4)
        if type_hint in ("bool", "boolean"):
            return rng.choice([True, False])
        if type_hint.startswith("list"):
            return [f"item_{difficulty}_{j}" for j in range(idx + 1)]
        return None


@dataclass
class EvalTask:
    name: str
    description: str
    metric: str
    threshold: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "metric": self.metric,
            "threshold": self.threshold,
        }


class EvalSuiteBuilder:
    DEFAULT_METRICS = {
        "classification": ("macro_f1", 0.85),
        "extraction": ("exact_match", 0.9),
        "generation": ("semantic_similarity", 0.8),
        "ranking": ("ndcg@10", 0.75),
        "safety": ("violation_rate", 0.0),
    }

    def build(self, task_type: str, custom_thresholds: Optional[Dict[str, float]] = None) -> List[EvalTask]:
        custom_thresholds = custom_thresholds or {}
        tasks: List[EvalTask] = []
        for category, (metric, default) in self.DEFAULT_METRICS.items():
            tasks.append(
                EvalTask(
                    name=f"{task_type}.{category}",
                    description=f"Measure {category} performance for the {task_type} task.",
                    metric=metric,
                    threshold=custom_thresholds.get(category, default),
                )
            )
        return tasks


@dataclass
class RewardScenario:
    name: str
    primary_reward: str
    anti_gaming_penalty: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primary_reward": self.primary_reward,
            "anti_gaming_penalty": self.anti_gaming_penalty,
            "notes": self.notes,
        }


class RewardScenarioBuilder:
    def build(self, task: str) -> RewardScenario:
        primary = (
            f"Reward = +1 when the model's output matches the gold answer for '{task}', "
            f"else 0. For free-form outputs, use a learned reward model trained on "
            f"human comparisons."
        )
        penalty = (
            "Subtract 0.5 when the model: (a) refuses without justification, "
            "(b) produces output that exceeds 2x the gold length, or (c) repeats "
            "the input verbatim."
        )
        return RewardScenario(
            name=f"reward.{task}",
            primary_reward=primary,
            anti_gaming_penalty=penalty,
            notes="Penalties prevent reward hacking via verbosity or trivial copying.",
        )
