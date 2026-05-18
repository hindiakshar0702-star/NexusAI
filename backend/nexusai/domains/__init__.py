"""Domain-specific prompt builders.

Each builder receives an `Intent` and a `SkillLevel` and returns a structured
prompt body (string). Builders are intentionally small and composable so the
prompt engine can mix-and-match without coupling to any single template.
"""
from __future__ import annotations

from typing import Callable, Dict

from ..types import Domain, Intent, SkillLevel
from . import (  # noqa: F401  -- registered via _BUILDERS
    text as _text,
    image as _image,
    video as _video,
    animation as _animation,
    ui_ux as _ui_ux,
    website as _website,
    app as _app,
    voice as _voice,
    music as _music,
    three_d as _three_d,
    game as _game,
    code as _code,
    marketing as _marketing,
    storytelling as _storytelling,
    training as _training,
)


Builder = Callable[[Intent, SkillLevel], str]

_BUILDERS: Dict[Domain, Builder] = {
    Domain.TEXT: _text.build,
    Domain.IMAGE: _image.build,
    Domain.VIDEO: _video.build,
    Domain.ANIMATION: _animation.build,
    Domain.UI_UX: _ui_ux.build,
    Domain.WEBSITE: _website.build,
    Domain.APP: _app.build,
    Domain.VOICE: _voice.build,
    Domain.MUSIC: _music.build,
    Domain.THREE_D: _three_d.build,
    Domain.GAME: _game.build,
    Domain.CODE: _code.build,
    Domain.MARKETING: _marketing.build,
    Domain.STORYTELLING: _storytelling.build,
    Domain.TRAINING: _training.build,
}


def build_for(intent: Intent, skill_level: SkillLevel) -> str:
    builder = _BUILDERS.get(intent.domain, _text.build)
    return builder(intent, skill_level)


def supported_domains() -> list[Domain]:
    return list(_BUILDERS.keys())
