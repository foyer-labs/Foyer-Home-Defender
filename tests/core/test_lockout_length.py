"""Fix phase: a lockout lasts as long as the Users page says, however long."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.foyer.core.authz import register_failure

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


def _lock(duration: int, strikes_before: int = 0):
    lock = None
    for _ in range(strikes_before + 1):
        for _ in range(5):
            lock, _shut = register_failure(
                lock, NOW, failures=5, window=300, duration=duration
            )
    return lock


def test_a_setting_longer_than_an_hour_is_honoured():
    """The page accepts up to a day; every lockout used to stop at an hour."""
    lock = _lock(7200)
    assert (lock.until - NOW).total_seconds() == 7200


def test_the_doubling_still_stops_at_an_hour_for_a_short_setting():
    lock = _lock(300, strikes_before=5)
    assert (lock.until - NOW).total_seconds() == 3600
