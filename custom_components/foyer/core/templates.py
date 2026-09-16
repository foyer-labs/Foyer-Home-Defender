"""Message templates over a fixed variable set (SPEC §6.4).

Not Jinja over the whole state machine: exactly the documented variables, so a
template can be validated when it is saved and can never read something the
simulator would not also see. An unknown name is left as the user wrote it,
which makes a typo visible instead of silently blank.
"""

from __future__ import annotations

from collections.abc import Mapping
import re

# The whole vocabulary (SPEC §6.4). ``user`` stays empty until Phase 2.
TEMPLATE_VARIABLES: tuple[str, ...] = (
    "zone",
    "area",
    "scenario",
    "user",
    "channel",
    "time",
    "date",
    "state",
    "open_zones",
    "reason",
    "incident_zones",
)

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render(text: str, variables: Mapping[str, str]) -> str:
    """Substitute ``{{ name }}`` for every documented variable."""

    def replace(match: re.Match[str]) -> str:
        name = match[1]
        if name not in TEMPLATE_VARIABLES:
            return match[0]
        return variables.get(name, "")

    return _PLACEHOLDER.sub(replace, text)


def unknown_variables(text: str) -> tuple[str, ...]:
    """Names used in ``text`` that are not in the documented set."""
    return tuple(
        dict.fromkeys(
            name
            for name in _PLACEHOLDER.findall(text)
            if name not in TEMPLATE_VARIABLES
        )
    )
