"""No foyer/* WebSocket command may declare its own "id" field.

"id" is the WebSocket message id. A command that also used it for, say, the
area to delete had its message id overwritten by the panel, and Home Assistant
dropped the command as invalid: deleting never worked until this was caught.
"""

from __future__ import annotations

from pathlib import Path
import re

WEBSOCKET = (
    Path(__file__).resolve().parents[2] / "custom_components/foyer/api/websocket.py"
)


def test_no_command_declares_an_id_field():
    source = WEBSOCKET.read_text(encoding="utf-8")
    assert not re.search(
        r"""vol\.(Required|Optional|Exclusive)\(\s*["']id["']""", source
    )
