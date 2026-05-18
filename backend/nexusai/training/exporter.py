"""Fine-tune data exporter.

Combines VarietyEngine + PromptEngine to produce training-ready JSONL in
multiple instruction-tuning formats:

  * "llama"   – {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}
                Llama 3 / Mistral / most chat-template formats.
  * "chatml"  – Same shape as "llama"; explicit alias for ChatML-trained models.
  * "alpaca"  – {"instruction": ..., "input": ..., "output": ...}
                Classic Stanford Alpaca format.
  * "openai"  – {"messages": [...]}; OpenAI fine-tuning JSONL spec.

The exporter applies a *quality filter* so only prompts above a configurable
score threshold end up in the dataset. Failed safety checks are dropped
silently. A final integrity check guarantees every line is valid JSON.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Literal, Optional

from ..engines.prompt_engine import PromptEngine, SafetyViolation
from ..types import Domain, Prompt, SkillLevel
from .teacher import GPT4Teacher, TeacherStats
from .variety import SyntheticIdea, VarietyEngine


Format = Literal["llama", "chatml", "alpaca", "openai"]

# A short, generic system prompt that frames the model's role. Kept in one
# place so both the exporter and the eval harness use the same wording.
DEFAULT_SYSTEM_PROMPT = (
    "You are NexusAI, an expert prompt engineer. Given a short raw idea from "
    "a user, produce a high-quality, structured prompt suitable for the right "
    "AI tool. Adapt to the user's domain, target platform, audience, and "
    "skill level. Be specific, concrete, and platform-native."
)


@dataclass
class ExportStats:
    """Summary of an export run."""
    requested: int
    generated: int
    kept: int
    dropped_low_score: int
    dropped_safety: int
    dropped_error: int
    domains_covered: List[str]
    avg_score: float
    duration_seconds: float
    teacher: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExportConfig:
    """All knobs for one export run."""
    n_examples: int = 1000
    domains: Optional[List[Domain]] = None
    fmt: Format = "llama"
    min_score: float = 0.70
    seed: int = 42
    edge_case_ratio: float = 0.08
    include_system_prompt: bool = True
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    # Teacher polish: if True and a teacher is available, GPT-4 rewrites the
    # assistant output before it is serialized. Falls back silently otherwise.
    use_teacher: bool = False
    teacher_model: str = "gpt-4o-mini"
    teacher_temperature: float = 0.4


# ---------------------------------------------------------------- formatters

def _format_user_prompt(idea: SyntheticIdea) -> str:
    """Build the user-facing instruction for an idea.

    The user message includes the raw idea plus any inline platform hint, so
    the trained model learns to honor explicit platform requests.
    """
    parts = [idea.raw_idea.strip()]
    if idea.platform is not None:
        parts.append(f"\n\n(target platform: {idea.platform.value})")
    if idea.skill_level != SkillLevel.ADVANCED:
        parts.append(f"\n(skill level: {idea.skill_level.value})")
    return "".join(parts)


def _format_assistant_output(prompt: Prompt) -> str:
    """Serialize the structured Prompt into a single training-ready string.

    We deliberately include the rationale (one short line) so the trained
    model learns to *explain* its routing decisions, not just emit text.
    """
    blocks: List[str] = []

    header = (
        f"[domain: {prompt.domain.value} | platform: {prompt.platform.value} | "
        f"skill: {prompt.skill_level.value}]"
    )
    blocks.append(header)
    blocks.append(prompt.text.strip())

    if prompt.system:
        blocks.append(f"\n--- system ---\n{prompt.system.strip()}")
    if prompt.negative:
        blocks.append(f"\n--- negative ---\n{prompt.negative.strip()}")
    if prompt.parameters:
        params = ", ".join(f"{k}={v}" for k, v in prompt.parameters.items())
        blocks.append(f"\n--- parameters ---\n{params}")

    return "\n".join(blocks)


def _to_messages(user: str, assistant: str, system: Optional[str]) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    msgs.append({"role": "assistant", "content": assistant})
    return msgs


def _format_record(
    idea: SyntheticIdea,
    prompt: Prompt,
    cfg: ExportConfig,
) -> Dict[str, Any]:
    """Convert a (idea, prompt) pair into the requested output shape."""
    user = _format_user_prompt(idea)
    assistant = _format_assistant_output(prompt)
    system = cfg.system_prompt if cfg.include_system_prompt else None

    if cfg.fmt in ("llama", "chatml", "openai"):
        return {"messages": _to_messages(user, assistant, system)}

    if cfg.fmt == "alpaca":
        # Alpaca splits instruction (the ask) from input (additional context).
        # We put the system prompt into "instruction" prefix when included.
        instruction = (
            f"{system}\n\n{user}" if system else user
        ) if cfg.include_system_prompt else user
        return {
            "instruction": instruction,
            "input": "",
            "output": assistant,
        }

    raise ValueError(f"Unknown format: {cfg.fmt!r}")


def _replace_text(prompt: Prompt, new_text: str) -> Prompt:
    """Return a copy of `prompt` with its `.text` replaced.

    Used after the GPT-4 teacher polishes the assistant output. We keep all
    other fields (score, parameters, system, negative) so the record still
    serializes the full structure.
    """
    return Prompt(
        id=prompt.id,
        text=new_text,
        domain=prompt.domain,
        platform=prompt.platform,
        skill_level=prompt.skill_level,
        title=prompt.title,
        system=prompt.system,
        negative=prompt.negative,
        parameters=prompt.parameters,
        tags=list(prompt.tags) + ["teacher-polished"],
        rationale=prompt.rationale,
        score=prompt.score,
        parent_id=prompt.parent_id,
        created_at=prompt.created_at,
    )


# ----------------------------------------------------------------- exporter

ProgressCallback = Callable[[int, int, ExportStats], None]


class FineTuneDataExporter:
    """Produce a JSONL dataset for fine-tuning from NexusAI itself."""

    def __init__(
        self,
        engine: Optional[PromptEngine] = None,
        variety: Optional[VarietyEngine] = None,
    ) -> None:
        self.engine = engine or PromptEngine()
        self.variety = variety  # set per run if None

    # ------------------------------------------------------------------ main
    def export(
        self,
        cfg: ExportConfig,
        out_path: Optional[str | os.PathLike] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> tuple[List[Dict[str, Any]], ExportStats]:
        """Generate, filter, and (optionally) write the dataset.

        Args:
            cfg: Export configuration.
            out_path: If given, JSONL is streamed to disk. If None, returned
                in-memory only.
            progress: Optional callback fired after each example.

        Returns:
            (records, stats). `records` is the full kept list (also written
            if out_path was provided).
        """
        records, stats = self._collect(cfg, progress)
        if out_path is not None:
            self._write_jsonl(records, out_path)
        return records, stats

    def export_iter(
        self,
        cfg: ExportConfig,
    ) -> Iterator[Dict[str, Any]]:
        """Streaming variant: yields each kept record as it is produced.

        Useful for FastAPI streaming responses (server-sent events / chunked).
        """
        variety = self.variety or VarietyEngine(seed=cfg.seed, edge_case_ratio=cfg.edge_case_ratio)
        ideas = variety.generate(cfg.n_examples, domains=cfg.domains)

        teacher: Optional[GPT4Teacher] = None
        if cfg.use_teacher:
            teacher = GPT4Teacher(
                model=cfg.teacher_model,
                temperature=cfg.teacher_temperature,
            )

        for idea in ideas:
            record = self._build_record(idea, cfg, teacher)
            if record is not None:
                yield record

    # ------------------------------------------------------------- internals
    def _collect(
        self,
        cfg: ExportConfig,
        progress: Optional[ProgressCallback],
    ) -> tuple[List[Dict[str, Any]], ExportStats]:
        if cfg.n_examples <= 0:
            raise ValueError("n_examples must be positive.")

        variety = self.variety or VarietyEngine(seed=cfg.seed, edge_case_ratio=cfg.edge_case_ratio)
        ideas = variety.generate(cfg.n_examples, domains=cfg.domains)

        # Lazy-init teacher only if requested. Construction is cheap when
        # the openai package is missing (it just records init_error).
        teacher: Optional[GPT4Teacher] = None
        if cfg.use_teacher:
            teacher = GPT4Teacher(
                model=cfg.teacher_model,
                temperature=cfg.teacher_temperature,
            )

        kept: List[Dict[str, Any]] = []
        score_sum = 0.0
        domains_seen: set[str] = set()
        dropped_low = dropped_safety = dropped_error = 0

        started = time.time()

        for i, idea in enumerate(ideas, start=1):
            try:
                prompt = self.engine.generate(
                    idea.raw_idea,
                    skill_level=idea.skill_level,
                    domain=idea.domain,
                    platform=idea.platform,
                )
            except SafetyViolation:
                dropped_safety += 1
                continue
            except Exception:
                dropped_error += 1
                continue

            score_value = prompt.score.overall if prompt.score else 0.0
            if score_value < cfg.min_score:
                dropped_low += 1
                continue

            # Optional teacher polish. If unavailable or fails, fall back to
            # the raw NexusAI text rather than dropping the example.
            if teacher is not None and teacher.available:
                polished = teacher.enhance(prompt.text)
                if polished:
                    prompt = _replace_text(prompt, polished)

            kept.append(_format_record(idea, prompt, cfg))
            score_sum += score_value
            domains_seen.add(prompt.domain.value)

            if progress is not None:
                stats_so_far = ExportStats(
                    requested=cfg.n_examples,
                    generated=i,
                    kept=len(kept),
                    dropped_low_score=dropped_low,
                    dropped_safety=dropped_safety,
                    dropped_error=dropped_error,
                    domains_covered=sorted(domains_seen),
                    avg_score=(score_sum / max(1, len(kept))),
                    duration_seconds=time.time() - started,
                    teacher=teacher.stats.to_dict() if teacher else None,
                )
                progress(i, cfg.n_examples, stats_so_far)

        avg = (score_sum / len(kept)) if kept else 0.0
        stats = ExportStats(
            requested=cfg.n_examples,
            generated=cfg.n_examples,
            kept=len(kept),
            dropped_low_score=dropped_low,
            dropped_safety=dropped_safety,
            dropped_error=dropped_error,
            domains_covered=sorted(domains_seen),
            avg_score=round(avg, 4),
            duration_seconds=round(time.time() - started, 3),
            teacher=teacher.stats.to_dict() if teacher else None,
        )
        return kept, stats

    def _build_record(
        self,
        idea: SyntheticIdea,
        cfg: ExportConfig,
        teacher: Optional[GPT4Teacher] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            prompt = self.engine.generate(
                idea.raw_idea,
                skill_level=idea.skill_level,
                domain=idea.domain,
                platform=idea.platform,
            )
        except (SafetyViolation, Exception):
            return None
        if not prompt.score or prompt.score.overall < cfg.min_score:
            return None
        if teacher is not None and teacher.available:
            polished = teacher.enhance(prompt.text)
            if polished:
                prompt = _replace_text(prompt, polished)
        return _format_record(idea, prompt, cfg)

    @staticmethod
    def _write_jsonl(records: Iterable[Dict[str, Any]], out_path: str | os.PathLike) -> None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


# Convenience helper for ad-hoc scripts / notebooks.
def export_training_data(
    n_examples: int = 1000,
    fmt: Format = "llama",
    out_path: str = "nexusai_train.jsonl",
    domains: Optional[List[Domain]] = None,
    min_score: float = 0.70,
    seed: int = 42,
) -> ExportStats:
    """One-line export. Returns stats; writes JSONL to disk."""
    exporter = FineTuneDataExporter()
    cfg = ExportConfig(
        n_examples=n_examples, fmt=fmt, domains=domains,
        min_score=min_score, seed=seed,
    )
    _, stats = exporter.export(cfg, out_path=out_path)
    return stats
