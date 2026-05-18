"""Smart prompt templates.

A small, hand-curated library of high-leverage prompt frameworks indexed by
domain. The library auto-selects a template based on the user's idea by
matching keywords; this is intentionally simple but already useful. A real
deployment would back this with a vector store and learned routing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..types import Domain


@dataclass
class Template:
    id: str
    name: str
    domain: Domain
    description: str
    body: str
    variables: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        try:
            return self.body.format(**kwargs)
        except KeyError as e:
            missing = e.args[0]
            raise ValueError(f"Template '{self.id}' is missing variable '{missing}'.") from e

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "body": self.body,
            "variables": self.variables,
            "keywords": self.keywords,
        }


_TEMPLATES: List[Template] = [
    Template(
        id="text.feynman",
        name="Feynman explainer",
        domain=Domain.TEXT,
        description="Explain a complex topic in clear, layered language.",
        body=(
            "Explain {topic} to a {audience}.\n"
            "1) Start with a one-sentence intuition.\n"
            "2) Walk through it with one concrete example.\n"
            "3) Identify the most common misconception and correct it.\n"
            "4) End with a one-sentence takeaway."
        ),
        variables=["topic", "audience"],
        keywords=["explain", "teach", "tutorial", "learn"],
    ),
    Template(
        id="image.cinematic_portrait",
        name="Cinematic portrait",
        domain=Domain.IMAGE,
        description="Strong portrait composition with motivated lighting.",
        body=(
            "Cinematic portrait of {subject}, {mood} mood, {lens} lens, "
            "shallow depth of field, motivated key light from {light_direction}, "
            "{color_palette} color palette, photographed on {camera}."
        ),
        variables=["subject", "mood", "lens", "light_direction", "color_palette", "camera"],
        keywords=["portrait", "person", "headshot", "character"],
    ),
    Template(
        id="ui.saas_dashboard",
        name="Modern SaaS dashboard",
        domain=Domain.UI_UX,
        description="Information-dense dashboard with clear hierarchy.",
        body=(
            "Design a SaaS dashboard for {product}. Sidebar nav with {sections}. "
            "Top bar with global search, notifications, account menu. "
            "Main canvas: 3-column metric cards above a primary chart, table below. "
            "Use {primary_color} as the single accent. Glassmorphic surfaces, "
            "4px spacing rhythm, AA contrast. Include empty, loading, and error states."
        ),
        variables=["product", "sections", "primary_color"],
        keywords=["dashboard", "saas", "admin", "analytics"],
    ),
    Template(
        id="code.refactor_with_tests",
        name="Refactor with tests",
        domain=Domain.CODE,
        description="Behavior-preserving refactor anchored by tests.",
        body=(
            "Refactor the following {language} code:\n\n"
            "```{language}\n{code}\n```\n\n"
            "Constraints: {constraints}. First, write characterization tests that pin "
            "current behavior. Then refactor without changing public behavior. "
            "Finally, list the smells removed and the tradeoffs introduced."
        ),
        variables=["language", "code", "constraints"],
        keywords=["refactor", "clean up", "rewrite", "improve"],
    ),
    Template(
        id="marketing.cold_outreach",
        name="Cold outreach (PAS)",
        domain=Domain.MARKETING,
        description="Pain-Agitate-Solution with one specific proof point.",
        body=(
            "Write a cold {channel} message from {sender} to {recipient}. "
            "Pain: {pain}. Agitate it with one concrete consequence. "
            "Solution: {solution}, backed by {proof}. "
            "End with one specific 15-minute ask. No hedging."
        ),
        variables=["channel", "sender", "recipient", "pain", "solution", "proof"],
        keywords=["cold email", "outreach", "linkedin", "sales"],
    ),
    Template(
        id="story.three_act",
        name="Three-act story spine",
        domain=Domain.STORYTELLING,
        description="Classic three-act structure with concrete beats.",
        body=(
            "Write a {length} {genre} story about {protagonist}. "
            "Act 1: status quo and inciting incident. "
            "Act 2: rising stakes culminating in a midpoint reversal. "
            "Act 3: climactic choice and a final image that mirrors or inverts the opening. "
            "Theme: {theme}."
        ),
        variables=["length", "genre", "protagonist", "theme"],
        keywords=["story", "narrative", "screenplay", "novel"],
    ),
    Template(
        id="training.synthetic_dataset",
        name="Synthetic dataset spec",
        domain=Domain.TRAINING,
        description="Specify a synthetic dataset for fine-tuning.",
        body=(
            "Specify a synthetic dataset for fine-tuning a model on {task}.\n"
            "- Input schema: {input_schema}\n"
            "- Output schema: {output_schema}\n"
            "- Difficulty curriculum: easy / medium / hard split with held-out test set\n"
            "- Augmentations: paraphrase, perturb, contrastive negative\n"
            "- Anti-contamination check vs. {known_test_set}\n"
            "- Acceptance metric: {metric} above {threshold}"
        ),
        variables=["task", "input_schema", "output_schema", "known_test_set", "metric", "threshold"],
        keywords=["fine-tune", "dataset", "training data"],
    ),
]


class TemplateLibrary:
    def __init__(self, templates: Optional[List[Template]] = None) -> None:
        self._by_id: Dict[str, Template] = {t.id: t for t in (templates or _TEMPLATES)}

    def all(self) -> List[Template]:
        return list(self._by_id.values())

    def by_domain(self, domain: Domain) -> List[Template]:
        return [t for t in self._by_id.values() if t.domain == domain]

    def get(self, template_id: str) -> Optional[Template]:
        return self._by_id.get(template_id)

    def auto_select(self, raw_idea: str, domain: Optional[Domain] = None) -> Optional[Template]:
        lowered = raw_idea.lower()
        candidates = (
            self.by_domain(domain) if domain else self.all()
        )
        best: Optional[Template] = None
        best_score = 0
        for template in candidates:
            score = sum(1 for kw in template.keywords if kw in lowered)
            if score > best_score:
                best_score = score
                best = template
        return best
