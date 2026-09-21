"""INV-1 regression test: core/ imports nothing from Home Assistant (SPEC §19).

If this fails, the fix is the code, never the test.

Two checks, because each catches what the other misses:

* a static one over the source: every import in core/ is either the standard
  library or another module inside core/ — so a relative import that climbs out
  of core/ into Home Assistant-backed code is caught even if it is unused;
* a runtime one in a fresh interpreter: importing the pure modules leaves no
  ``homeassistant`` module loaded — so an indirect import is caught too.
"""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "custom_components" / "foyer"
CORE = PACKAGE / "core"

# Modules that must import without Home Assistant installed: core/ itself plus
# the pure halves of the store, which the core test suite also exercises.
PURE_MODULES = [
    "custom_components.foyer.core.engine",
    "custom_components.foyer.core.models",
    "custom_components.foyer.core.proposals",
    "custom_components.foyer.core.presets",
    "custom_components.foyer.core.triggers",
    "custom_components.foyer.core.validation",
    "custom_components.foyer.store.schema",
    "custom_components.foyer.store.seed",
    "custom_components.foyer.store.migrations",
    "custom_components.foyer.store.editing",
    # The Alarmo importer reads a foreign document and writes nothing: it is
    # tested without Home Assistant, so it must import without it (§20.2).
    "custom_components.foyer.store.alarmo",
    # security/ is not core/ — it holds a code in the clear for as long as a
    # comparison takes — but it must stay free of Home Assistant too, so that
    # the rules protecting codes are testable without one.
    "custom_components.foyer.security.codes",
]


def _core_files() -> list[Path]:
    files = sorted(CORE.rglob("*.py"))
    assert files, "core/ has no Python files — has it moved?"
    return files


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    # Depth of this module's package below core/ (core/x.py -> 0).
    depth = len(path.relative_to(CORE).parts) - 1
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # A relative import may not climb above core/.
                if node.level - 1 > depth:
                    problems.append(
                        f"{path.name}:{node.lineno} relative import leaves core/"
                    )
                continue
            names = [node.module or ""]
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top == "__future__" or top in sys.stdlib_module_names:
                continue
            problems.append(f"{path.name}:{node.lineno} imports {name!r}")
    return problems


def test_core_imports_only_stdlib_and_core():
    problems = [p for f in _core_files() for p in _violations(f)]
    assert not problems, "core/ must stay pure (INV-1):\n" + "\n".join(problems)


def test_the_static_check_catches_homeassistant(tmp_path, monkeypatch):
    """Guard the guard: the checker must flag the imports it exists to flag."""
    fake_core = tmp_path / "core"
    fake_core.mkdir()
    bad = fake_core / "bad.py"
    bad.write_text(
        "import homeassistant.core\n"
        "from homeassistant.const import STATE_ON\n"
        "from .. import const\n"
        "from .models import Zone\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "CORE", fake_core)

    problems = _violations(bad)

    assert len(problems) == 3
    assert "homeassistant.core" in problems[0]
    assert "homeassistant.const" in problems[1]
    assert "leaves core/" in problems[2]


def test_pure_modules_import_without_homeassistant():
    script = (
        "import sys\n"
        f"for name in {PURE_MODULES!r}:\n"
        "    __import__(name)\n"
        "loaded = sorted(m for m in sys.modules\n"
        "                if m == 'homeassistant' or m.startswith('homeassistant.'))\n"
        "print('\\n'.join(loaded))\n"
        "sys.exit(1 if loaded else 0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "importing the pure modules loaded Home Assistant:\n"
        f"{result.stdout}{result.stderr}"
    )
