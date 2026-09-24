"""The panel's new person starts with the backend's defaults (§8.3).

The Users page builds an empty draft with its own copy of the permissions a
new person is offered. A copy that drifted from ``DEFAULT_PERMISSIONS`` would
put a permission on every new person without any test noticing — the walk
test's whole-house reach (decision 137) is the one this exists for.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from custom_components.foyer.core.authz import DEFAULT_PERMISSIONS

USERS_PAGE = Path(__file__).resolve().parents[2] / "frontend/src/panel/pages/users.ts"


def test_the_empty_draft_offers_exactly_the_default_permissions():
    source = USERS_PAGE.read_text(encoding="utf-8")
    empty = re.search(r"const EMPTY: Draft = \{(.*?)\n\};", source, re.S)
    assert empty, "users.ts no longer declares its empty draft as EMPTY"
    listed = re.search(r"permissions:\s*(\[[^\]]*\])", empty.group(1))
    assert listed, "the empty draft no longer lists its permissions inline"
    assert sorted(json.loads(listed.group(1))) == sorted(DEFAULT_PERMISSIONS)
