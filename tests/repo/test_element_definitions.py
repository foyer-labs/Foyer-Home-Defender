"""Frontend elements are defined only through ``shared/define.ts`` (decision 167).

The card is loaded as an extra module and can run before the Home Assistant app
replaces the custom element registry: an element defined directly lands in the old
registry, and the card is listed in the "add card" picker but cannot be created.
``define`` waits for the final registry.
"""

from __future__ import annotations

from pathlib import Path
import re

SOURCES = Path(__file__).resolve().parents[2] / "frontend" / "src"
ALLOWED = SOURCES / "shared" / "define.ts"


def test_no_direct_custom_element_definitions():
    direct = [
        f"{path.relative_to(SOURCES)}:{number}"
        for path in SOURCES.rglob("*.ts")
        if path != ALLOWED
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"customElements\.define\(", line)
    ]
    assert not direct, "use define() from shared/define.ts:\n" + "\n".join(direct)


def test_the_card_joins_the_picker_after_its_definition():
    card = (SOURCES / "card" / "foyer-card.ts").read_text(encoding="utf-8")
    assert 'define("foyer-card", FoyerCard)' in card
    assert 'define("foyer-card-editor", FoyerCardEditor)' in card
    picker = card[card.index("window.customCards = window.customCards ?? [];") - 200 :]
    assert "whenReady(() => {" in picker
