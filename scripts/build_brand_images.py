"""Render the integration's brand images from the symbol and lockup in docs/logo.

Home Assistant and HACS look for an integration's icon and logo in a ``brand``
directory next to its code; HACS needs at least ``icon.png`` there before the
integration can join its default list. This script writes all eight files to
custom_components/foyer/brand/: the icon at 256 and 512 px, the lockup at 256
and 512 px high, each in a light-ground and a dark-ground version. It draws
nothing of its own: if the SVGs change, run it again.

    pip install cairosvg
    python scripts/build_brand_images.py
"""

from __future__ import annotations

from pathlib import Path
import re

import cairosvg

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "docs" / "logo"
OUT = ROOT / "custom_components" / "foyer" / "brand"

# The shield and its stroke, squared, without the symbol's empty margin: an
# icon is shown small, and the margin would only make the shield smaller.
ICON_VIEWBOX = "3.2 3.2 57.6 57.6"
LOCKUP_RATIO = 186 / 64


def _svg(name: str, viewbox: str | None = None) -> bytes:
    text = (LOGO / name).read_text(encoding="utf-8")
    if viewbox:
        text = re.sub(r'viewBox="[^"]*"', f'viewBox="{viewbox}"', text, count=1)
    return text.encode()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for prefix, ground in (("", "light"), ("dark_", "dark")):
        icon = _svg(f"foyer-hd-symbol-{ground}-bg.svg", ICON_VIEWBOX)
        lockup = _svg(f"foyer-hd-lockup-{ground}-bg.svg")
        for suffix, size in (("", 256), ("@2x", 512)):
            cairosvg.svg2png(
                bytestring=icon,
                write_to=str(OUT / f"{prefix}icon{suffix}.png"),
                output_width=size,
                output_height=size,
            )
            cairosvg.svg2png(
                bytestring=lockup,
                write_to=str(OUT / f"{prefix}logo{suffix}.png"),
                output_width=round(size * LOCKUP_RATIO),
                output_height=size,
            )


if __name__ == "__main__":
    main()
