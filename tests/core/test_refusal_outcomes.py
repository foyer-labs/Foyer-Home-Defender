"""Fix phase: "wrong code" in the log only when a code was wrong."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.foyer.core.journal import row_for
from custom_components.foyer.core.models import Moment, Occurrence, Reason

AT = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


def _outcome(reason: Reason) -> str | None:
    occurrence = Occurrence(
        moment=Moment.CODE_REJECTED,
        detail={"operation": "disarm", "reason": reason.value},
    )
    return row_for(occurrence, AT).outcome


def test_a_wrong_code_is_a_wrong_code():
    assert _outcome(Reason.BAD_CODE) == "bad_code"


def test_a_refusal_for_who_was_asking_is_blocked_not_a_wrong_code():
    for reason in (Reason.NOT_PERMITTED, Reason.USER_NOT_VALID):
        assert _outcome(reason) == "blocked", reason
