"""Schema migrations for the stored configuration.

Home Assistant's Store calls ``migrate`` whenever the version on disk differs
from the version in code. Each step upgrades one (major, minor) version to the
next and is a pure function over the JSON document, so it can be tested without
Home Assistant.

There are no steps yet: version 1.1 is the first schema. The hook is wired now so
that the first real change is a new entry in ``STEPS``, not new plumbing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Document = dict[str, Any]
Version = tuple[int, int]

# (from_major, from_minor) -> (step, (to_major, to_minor))
STEPS: dict[Version, tuple[Callable[[Document], Document], Version]] = {}


class MigrationError(Exception):
    """The stored document cannot be brought to the current version."""


def migrate(
    from_version: Version,
    to_version: Version,
    data: Document,
    steps: dict[Version, tuple[Callable[[Document], Document], Version]] | None = None,
) -> Document:
    """Upgrade ``data`` from ``from_version`` to ``to_version``, one step at a time.

    A newer *minor* version of the same major is additive by contract and is
    read as is. A newer *major* version is refused rather than guessed at: a
    downgrade that silently drops fields could drop an alarm setting. Every
    older version needs an explicit step; there is no silent pass-through.
    """
    steps = STEPS if steps is None else steps
    if from_version[0] > to_version[0]:
        raise MigrationError(
            f"configuration was written by a newer version {from_version}; "
            f"this version understands up to {to_version}"
        )

    version = from_version
    while version < to_version:
        if version not in steps:
            raise MigrationError(f"no migration step from version {version}")
        step, next_version = steps[version]
        if next_version <= version:
            raise MigrationError(f"migration step from {version} does not advance")
        data = step(data)
        version = next_version
    return data
