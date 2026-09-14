"""Every user-visible string resolves through translations/ (SPEC §19).

* ``en`` and ``it`` carry the same key set and the same placeholders, in both
  the Home Assistant file and the panel file — a missing translation fails CI
  rather than shipping an English screen to an Italian user;
* every key the frontend asks for exists;
* frontend templates contain no literal text;
* every rejection reason and notification the backend can produce is translated.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import string

import pytest

from custom_components.foyer.core.models import Moment, Reason
from custom_components.foyer.store.seed import seed_config

ROOT = Path(__file__).resolve().parents[2]
TRANSLATIONS = ROOT / "custom_components" / "foyer" / "translations"
FRONTEND_SRC = ROOT / "frontend" / "src"
LANGUAGES = ("en", "it")
FILE_SETS = {
    "home assistant": TRANSLATIONS,
    "panel": TRANSLATIONS / "panel",
}


def load(directory: Path, language: str) -> dict:
    return json.loads((directory / f"{language}.json").read_text(encoding="utf-8"))


def flatten(node: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(flatten(value, f"{path}."))
        else:
            out[path] = value
    return out


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_language_directory_has_the_same_languages():
    for name, directory in FILE_SETS.items():
        found = sorted(p.stem for p in directory.glob("*.json"))
        assert found == sorted(LANGUAGES), f"{name}: {found}"


@pytest.mark.parametrize("name", FILE_SETS)
def test_key_sets_match(name):
    directory = FILE_SETS[name]
    reference = flatten(load(directory, "en"))
    for language in LANGUAGES[1:]:
        other = flatten(load(directory, language))
        missing = sorted(reference.keys() - other.keys())
        extra = sorted(other.keys() - reference.keys())
        assert not missing and not extra, (
            f"{name}/{language}.json differs from en.json\n"
            f"missing: {missing}\nextra: {extra}"
        )


@pytest.mark.parametrize("name", FILE_SETS)
def test_placeholders_match(name):
    directory = FILE_SETS[name]
    reference = flatten(load(directory, "en"))
    for language in LANGUAGES[1:]:
        other = flatten(load(directory, language))
        for key, text in reference.items():
            assert placeholders(text) == placeholders(other.get(key, "")), (
                f"{name}/{language}.json: placeholders differ for {key}"
            )


@pytest.mark.parametrize("name", FILE_SETS)
def test_no_empty_strings(name):
    for language in LANGUAGES:
        for key, text in flatten(load(FILE_SETS[name], language)).items():
            assert isinstance(text, str) and text.strip(), f"{language}: {key}"


def test_help_pages_have_title_intro_and_items():
    help_ = load(TRANSLATIONS / "panel", "en")["help"]
    pages = {k: v for k, v in help_.items() if isinstance(v, dict)}
    assert "overview" in pages
    for page, body in pages.items():
        assert {"title", "intro", "items"} <= body.keys(), page
        for item, entry in body["items"].items():
            assert {"term", "text"} == entry.keys(), f"{page}.{item}"


# --- frontend --------------------------------------------------------------------

T_CALL = re.compile(r"""\bt\(\s*[\w.?]+\s*,\s*(["'`])(.+?)\1""")


def frontend_sources() -> list[Path]:
    files = sorted(FRONTEND_SRC.rglob("*.ts"))
    assert files
    return files


def test_every_key_the_frontend_uses_exists():
    keys = set(flatten(load(TRANSLATIONS / "panel", "en")))
    missing = []
    for path in frontend_sources():
        for _, key in T_CALL.findall(path.read_text(encoding="utf-8")):
            if "${" in key:
                # A dynamic key such as `state.${x}`: at least one real key must
                # fit the pattern, or the lookup can never succeed.
                parts = re.split(r"\$\{[^}]*\}", key)
                pattern = re.compile(".+".join(re.escape(p) for p in parts) + "$")
                if not any(pattern.match(k) for k in keys):
                    missing.append(f"{path.name}: {key}")
            elif key not in keys:
                missing.append(f"{path.name}: {key}")
    assert not missing, "keys not in translations/panel/en.json:\n" + "\n".join(missing)


def _strip_expressions(template: str) -> str:
    """Remove ${...} expressions, including nested braces and templates."""
    out, depth, i = [], 0, 0
    while i < len(template):
        if template.startswith("${", i):
            depth += 1
            i += 2
            continue
        char = template[i]
        if depth:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
        else:
            out.append(char)
        i += 1
    return "".join(out)


def _templates(source: str) -> list[str]:
    """The bodies of html`...` tagged templates (outermost only)."""
    bodies, start = [], 0
    while (i := source.find("html`", start)) != -1:
        j, depth = i + 5, 0
        while j < len(source):
            if source.startswith("${", j):
                depth += 1
                j += 2
                continue
            if depth and source[j] == "{":
                depth += 1
            elif depth and source[j] == "}":
                depth -= 1
            elif not depth and source[j] == "`":
                break
            j += 1
        bodies.append(source[i + 5 : j])
        start = j + 1
    return bodies


TEXT_NODE = re.compile(r">([^<>]*)<")
TEXT_ATTRIBUTE = re.compile(r"""\b(?:aria-label|title|placeholder|alt)=["']([^"']*)""")


def test_frontend_templates_contain_no_literal_text():
    offenders = []
    for path in frontend_sources():
        for body in _templates(path.read_text(encoding="utf-8")):
            text = _strip_expressions(body)
            for literal in TEXT_NODE.findall(text) + TEXT_ATTRIBUTE.findall(text):
                if re.search(r"[A-Za-zÀ-ÿ]", literal):
                    offenders.append(f"{path.name}: {literal.strip()!r}")
    assert not offenders, "hard-coded text in templates:\n" + "\n".join(offenders)


def test_the_literal_text_check_catches_text():
    """Guard the guard."""
    sample = 'html`<div>${t(s, "a")}</div><p>Arm now</p><b title="Hi">${x}</b>`'
    body = _strip_expressions(_templates(sample)[0])

    assert "Arm now" in TEXT_NODE.findall(body)
    assert TEXT_ATTRIBUTE.findall(body) == ["Hi"]


# --- backend -----------------------------------------------------------------------


def test_every_rejection_reason_has_an_exception_message():
    for language in LANGUAGES:
        exceptions = load(TRANSLATIONS, language)["exceptions"]
        for reason in Reason:
            assert f"rejected_{reason.value}" in exceptions, (language, reason)


def test_every_moment_has_a_notification():
    """Any moment an action may list can be announced in every language."""
    for language in LANGUAGES:
        notifications = load(TRANSLATIONS / "panel", language)["notification"]
        for moment in Moment:
            assert {"title", "message"} <= notifications[moment.value].keys()
        assert {"title", "message"} <= notifications["armed_area"].keys()


def test_every_notification_the_seed_can_send_is_translated():
    config = seed_config(
        area_name="a",
        scenario_name="s",
        zone_entity_id="binary_sensor.x",
        zone_name="z",
        trigger_states=["on"],
    )
    for language in LANGUAGES:
        notifications = load(TRANSLATIONS / "panel", language)["notification"]
        for moment in config.actions[0].moments:
            assert {"title", "message"} <= notifications[moment.value].keys()


def test_every_problem_and_reason_the_backend_returns_is_translated():
    """The panel shows backend problems by code: each needs text in each language."""
    sources = [
        ROOT / "custom_components" / "foyer" / "core" / "validation.py",
        ROOT / "custom_components" / "foyer" / "store" / "editing.py",
    ]
    text = "\n".join(p.read_text(encoding="utf-8") for p in sources)
    codes = set(re.findall(r"""(?:Problem\(|add\()\s*["'](\w+)["']""", text))
    fields = set(
        re.findall(
            r"""Problem\(\s*["']\w+["'],\s*["']\w+["'],\s*[\w.]+,\s*["'](\w+)["']""",
            text,
        )
    )
    fields |= set(re.findall(r"""add\(\s*["']\w+["'],\s*["'](\w+)["']\)""", text))
    assert "trigger_not_confirmed" in codes and "entry_delay" in fields
    for language in LANGUAGES:
        panel = load(TRANSLATIONS / "panel", language)
        assert not codes - panel["problem"].keys(), (
            language,
            codes - panel["problem"].keys(),
        )
        assert not fields - panel["field"].keys(), (
            language,
            fields - panel["field"].keys(),
        )
        assert {r.value for r in Reason} <= panel["reason"].keys()
