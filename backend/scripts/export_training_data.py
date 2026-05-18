#!/usr/bin/env python3
"""Export a NexusAI fine-tuning dataset from the command line.

Usage examples
--------------

    # 200 llama-format examples, default quality threshold, default seed
    python -m scripts.export_training_data --n 200 --out data/train.jsonl

    # Restrict to specific domains
    python -m scripts.export_training_data --n 1000 \\
        --domains image code ui_ux \\
        --out data/train.jsonl

    # Use the GPT-4 teacher (requires OPENAI_API_KEY)
    python -m scripts.export_training_data --n 500 --use-teacher \\
        --teacher-model gpt-4o-mini --out data/train.jsonl

    # Alpaca format with a higher quality bar
    python -m scripts.export_training_data --n 500 --format alpaca \\
        --min-score 0.8 --out data/train_alpaca.jsonl

The script writes JSONL to disk and prints a one-screen summary at the end.
It runs entirely offline unless --use-teacher is set.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

# Allow running from anywhere: add the project root (parent of `scripts/`) to
# sys.path so `nexusai` resolves whether or not the user has pip-installed it.
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from nexusai.training import (  # noqa: E402  (sys.path mutation above is intentional)
    ExportConfig,
    ExportStats,
    FineTuneDataExporter,
    teacher_is_available,
)
from nexusai.types import Domain  # noqa: E402


VALID_FORMATS = ("llama", "chatml", "alpaca", "openai")
VALID_DOMAINS = [d.value for d in Domain]


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="export_training_data",
        description="Generate a fine-tuning JSONL dataset from NexusAI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--n", "--n-examples", dest="n_examples", type=int, default=200,
                   help="Number of synthetic ideas to attempt.")
    p.add_argument("--out", "--output", dest="out_path", type=str,
                   default="nexusai_train.jsonl",
                   help="Path to write the JSONL dataset.")
    p.add_argument("--format", dest="fmt", choices=VALID_FORMATS, default="llama",
                   help="Output format. llama/chatml/openai use {messages: ...}; "
                        "alpaca uses instruction/input/output.")
    p.add_argument("--domains", nargs="+", choices=VALID_DOMAINS, default=None,
                   help="Restrict to these domains (default: all).")
    p.add_argument("--min-score", type=float, default=0.70,
                   help="Drop prompts whose overall score is below this.")
    p.add_argument("--seed", type=int, default=42,
                   help="RNG seed for the variety engine.")
    p.add_argument("--edge-case-ratio", type=float, default=0.08,
                   help="Fraction of intentionally vague edge-case ideas.")
    p.add_argument("--no-system-prompt", dest="include_system_prompt",
                   action="store_false",
                   help="Omit the system prompt from each record.")
    p.add_argument("--use-teacher", action="store_true",
                   help="Polish outputs via OpenAI GPT-4 (requires OPENAI_API_KEY).")
    p.add_argument("--teacher-model", type=str, default="gpt-4o-mini",
                   help="OpenAI model used by the teacher.")
    p.add_argument("--teacher-temperature", type=float, default=0.4,
                   help="Sampling temperature for the teacher rewrites.")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress per-batch progress output.")
    return p.parse_args(argv)


def _domain_enums(values: Optional[List[str]]) -> Optional[List[Domain]]:
    if not values:
        return None
    return [Domain(v) for v in values]


def _format_progress(current: int, total: int, stats: ExportStats) -> str:
    pct = (current / total) * 100 if total else 0.0
    bar_width = 24
    filled = int(bar_width * current / total) if total else 0
    bar = "#" * filled + "-" * (bar_width - filled)
    return (
        f"\r[{bar}] {current}/{total} ({pct:5.1f}%) "
        f"kept={stats.kept} drop_low={stats.dropped_low_score} "
        f"avg={stats.avg_score:.3f}"
    )


def _print_summary(stats: ExportStats, out_path: str) -> None:
    print()  # newline after progress bar
    print("=" * 60)
    print("NexusAI training data export complete")
    print("=" * 60)
    rows = [
        ("Output file",            out_path),
        ("Requested",              str(stats.requested)),
        ("Kept",                   str(stats.kept)),
        ("Dropped (low score)",    str(stats.dropped_low_score)),
        ("Dropped (safety)",       str(stats.dropped_safety)),
        ("Dropped (error)",        str(stats.dropped_error)),
        ("Average score",          f"{stats.avg_score:.4f}"),
        ("Domains covered",        ", ".join(stats.domains_covered) or "—"),
        ("Duration (s)",           f"{stats.duration_seconds:.2f}"),
    ]
    if stats.teacher is not None:
        t = stats.teacher
        rows.extend([
            ("Teacher requested",   str(t.get("requested", 0))),
            ("Teacher enhanced",    str(t.get("enhanced", 0))),
            ("Teacher cache hits",  str(t.get("cached_hits", 0))),
            ("Teacher failed",      str(t.get("failed", 0))),
        ])
    width = max(len(k) for k, _ in rows)
    for k, v in rows:
        print(f"  {k.ljust(width)}  {v}")
    print()


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    # Friendly warnings about teacher availability so users know what to expect.
    if args.use_teacher and not teacher_is_available():
        print(
            "warning: --use-teacher was set but OpenAI is not available "
            "(package missing or OPENAI_API_KEY not set). The exporter will "
            "silently fall back to NexusAI-only outputs.",
            file=sys.stderr,
        )

    cfg = ExportConfig(
        n_examples=args.n_examples,
        domains=_domain_enums(args.domains),
        fmt=args.fmt,  # type: ignore[arg-type]
        min_score=args.min_score,
        seed=args.seed,
        edge_case_ratio=args.edge_case_ratio,
        include_system_prompt=args.include_system_prompt,
        use_teacher=args.use_teacher,
        teacher_model=args.teacher_model,
        teacher_temperature=args.teacher_temperature,
    )

    exporter = FineTuneDataExporter()

    last_render = 0.0

    def on_progress(current: int, total: int, stats: ExportStats) -> None:
        # Throttle prints so very fast runs don't flood the terminal.
        nonlocal last_render
        if args.quiet:
            return
        now = time.time()
        if current == total or (now - last_render) > 0.1:
            sys.stdout.write(_format_progress(current, total, stats))
            sys.stdout.flush()
            last_render = now

    try:
        _, stats = exporter.export(cfg, out_path=args.out_path, progress=on_progress)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    _print_summary(stats, args.out_path)

    # Useful sanity check: open the file we just wrote and confirm valid JSONL.
    out = Path(args.out_path)
    if not out.exists() or out.stat().st_size == 0:
        print(f"error: output file '{args.out_path}' is missing or empty.",
              file=sys.stderr)
        return 3

    bad = 0
    line_count = 0
    with out.open("r", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            try:
                json.loads(line)
            except json.JSONDecodeError:
                bad += 1
    if bad:
        print(f"warning: {bad}/{line_count} lines are not valid JSON.",
              file=sys.stderr)
        return 4

    print(f"validated: {line_count} valid JSON lines in {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
