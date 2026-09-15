"""Wall-clock helpers, pure: the time zone and the instant are always given.

Quiet hours use them today; part 3's time-window conditions (§6.3) will too,
so both read a window crossing midnight the same way.
"""

from __future__ import annotations

from datetime import datetime, time, tzinfo
import re

_HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def parse_hhmm(value: str) -> time | None:
    """ "07:30" -> 07:30; anything else -> None."""
    match = _HHMM.match(value)
    return time(int(match[1]), int(match[2])) if match else None


def in_daily_window(now: datetime, tz: tzinfo, start: str, end: str) -> bool:
    """Whether the local time is in [start, end), a window that may cross
    midnight. A window whose start equals its end is empty, never all day."""
    begin, finish = parse_hhmm(start), parse_hhmm(end)
    if begin is None or finish is None or begin == finish:
        return False
    local = now.astimezone(tz).time().replace(tzinfo=None)
    if begin < finish:
        return begin <= local < finish
    return local >= begin or local < finish
