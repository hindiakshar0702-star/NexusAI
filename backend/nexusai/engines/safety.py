"""Safety & ethics layer.

Lightweight rule-based gate that runs over every prompt before it is returned
to the user. The implementation is deterministic and dependency-free so it
can be exercised in tests, but it is structured so a model-based classifier
can be plugged in later (replace `_lexical_scan`).
"""
from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from ..types import SafetyReport


# Categories of disallowed content, expressed as regex word-stems. The patterns
# are intentionally conservative; the goal is to surface obvious red flags,
# not to be a complete content classifier.
_HIGH_SEVERITY_PATTERNS: List[Tuple[str, str]] = [
    ("weapons", r"\b(bioweapon|nerve\s*agent|sarin|vx\s*gas|dirty\s*bomb)\b"),
    ("malware", r"\b(ransomware|keylogger|rootkit|botnet)\s+(code|payload|builder)\b"),
    ("csam", r"\b(child|minor|underage)\b.*\b(sexual|nude|explicit)\b"),
    ("self_harm", r"\b(how\s+to\s+(kill|hurt)\s+myself|suicide\s+method)\b"),
]

_MEDIUM_SEVERITY_PATTERNS: List[Tuple[str, str]] = [
    ("piracy", r"\b(crack|keygen|pirate)\s+(software|license|key)\b"),
    ("phishing", r"\b(phishing\s+(kit|page|template)|spoofed\s+login)\b"),
    ("doxxing", r"\b(home\s+address|social\s+security\s+number|ssn)\b"),
]

_LOW_SEVERITY_PATTERNS: List[Tuple[str, str]] = [
    ("pii_email", r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    ("pii_phone", r"\b(\+?\d[\d\s\-().]{8,}\d)\b"),
]


class SafetyEngine:
    """Detect harmful prompts and optionally redact PII."""

    def review(self, text: str) -> SafetyReport:
        flags: List[str] = []
        severity = "none"

        for label, pattern in _HIGH_SEVERITY_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                flags.append(label)
                severity = "high"

        if severity != "high":
            for label, pattern in _MEDIUM_SEVERITY_PATTERNS:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    flags.append(label)
                    severity = "medium"

        redacted = None
        for label, pattern in _LOW_SEVERITY_PATTERNS:
            if re.search(pattern, text):
                flags.append(label)
                if severity == "none":
                    severity = "low"
                redacted = re.sub(pattern, f"[redacted:{label}]", redacted or text)

        safe = severity in {"none", "low"}
        explanation = (
            "Prompt cleared." if safe else
            "Prompt blocked: it appears to request content that violates our safety policy."
        )
        return SafetyReport(
            safe=safe,
            severity=severity,
            flags=flags,
            redacted_text=redacted,
            explanation=explanation,
        )

    def filter_many(self, texts: Iterable[str]) -> List[SafetyReport]:
        return [self.review(t) for t in texts]
