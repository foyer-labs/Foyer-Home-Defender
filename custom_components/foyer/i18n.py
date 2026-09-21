"""Frontend and notification strings from ``translations/panel/<lang>.json``.

Home Assistant's own ``translations/<lang>.json`` is validated by hassfest
against a closed schema that has no room for panel text or ``help.<page>``, so
those strings live alongside it in ``translations/panel/``. Home Assistant
ignores the subdirectory; Foyer serves it over ``foyer/translations``.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

PANEL_TRANSLATIONS = Path(__file__).parent / "translations" / "panel"
FALLBACK_LANGUAGE = "en"


def available_languages() -> list[str]:
    return sorted(p.stem for p in PANEL_TRANSLATIONS.glob("*.json"))


def resolve_language(language: str | None) -> str:
    """Map a Home Assistant language ("it", "en-GB", "pt-BR") to a file we have."""
    languages = set(available_languages())
    if language:
        for candidate in (language, language.split("-")[0]):
            if candidate in languages:
                return candidate
    return FALLBACK_LANGUAGE


@lru_cache(maxsize=8)
def load_strings(language: str) -> dict[str, Any]:
    """Blocking read; call from an executor. Cached for the process lifetime."""
    path = PANEL_TRANSLATIONS / f"{resolve_language(language)}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def languages() -> list[dict[str, str]]:
    """Every language on disk, each named in itself. Blocking; use an executor.

    The name comes from the language's own file (``language.self``) rather than
    from a table here or in the frontend, so that adding a language is copying
    two files and nothing else (§20.3): a list written in code is a line a
    translator has to find, and one they will not know exists.
    """
    return [
        {"code": code, "name": translate(load_strings(code), "language.self")}
        for code in available_languages()
    ]


def translate(strings: dict[str, Any], key: str, **placeholders: str) -> str:
    """Look up a dotted key and fill ``{placeholders}``. Missing keys return the key."""
    node: Any = strings
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return key
        node = node[part]
    if not isinstance(node, str):
        return key
    try:
        return node.format(**placeholders)
    except (KeyError, IndexError):
        return node
