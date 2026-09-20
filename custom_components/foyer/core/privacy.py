"""Who a log row is about, and what is left of it afterwards (SPEC §10.4).

The log records who was in the house, when they arrived and when they left,
for thirty days. That is personal data about everyone in the household, and
the household exemption stops covering it the moment the log records somebody
else — the cleaner whose arrivals are kept for a month, the boiler engineer,
the babysitter. `docs/privacy.md` says where that line is; this module is the
arithmetic behind the three operations §10.4 asks for.

It is pure, like everything else in ``core/``: it decides which rows are about
a person and what a row keeps, and it touches no database. ``store/log_store``
executes what it says, in its executor thread, off the alarm path.

Four decisions are written into the shapes here (part 2 decisions 1, 4, 6
and 12).

**Erasing is erasing.** ``user_id`` and ``user_name`` are emptied, not
replaced, unless whoever performs it asks for a pseudonym that run. The GDPR
request a cleaner actually makes is to be forgotten, and a stable identifier
that still says "the same person, eleven times that month" has not forgotten
them. The pseudonym stays available because the household that wants the
shape of its nights without the names is asking for something different and
legitimate.

**The pseudonym is minted once and stored on the user**, never recomputed.
Not a counter anchored to configuration order — deleting somebody would
renumber everyone after them, and "the same person on both nights" would stop
being true retroactively. Not a hash of the name either: a hash of a first
name falls to a list of first names, and §12.4 already refused hashing for
the diagnostics dump.

**Erasure is wide.** On a person's rows it takes ``user_id``, ``user_name``,
``channel`` and ``device_id`` — which keypad, and by which route, are as much
"who" as the name is once you know the household. What survives is what
happened, where and when, which is exactly the half §10.4 says must survive.

**A person is found by id and by name.** A row written before they were a
Foyer user, or under a name they have since changed, carries the name and
another id or none at all. Matching on the id alone would leave the oldest
rows — the ones most likely to be asked about — with the name still in them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .models import FoyerConfig, User

# What an erasure empties on a row it matched. Deliberately four columns and
# not two: see the module docstring.
ERASED_COLUMNS: tuple[str, ...] = ("user_id", "user_name", "channel", "device_id")

# What a redacted name is replaced by inside a JSON detail. A marker, not a
# blank: a row that once named somebody and no longer does should say so,
# because a silently empty field reads like a row that never had one.
REDACTED = "[erased]"

# The bounds of the pseudonymisation delay, in days. The floor is a day
# because the sweep runs daily and anything shorter would promise a precision
# it does not have; the ceiling is a year because a setting that outlives
# every retention in §10.2 would never once fire.
MIN_PSEUDONYMISE_DAYS = 1
MAX_PSEUDONYMISE_DAYS = 365

# The retention preset §10.4 asks for, "offered for installations with
# domestic staff", and the categories it touches: the ones that name people.
# `system` and the two `zone_*` categories are left alone — they carry faults,
# restarts and door states, which name nobody and are what somebody is reading
# when they ask why a sensor did not react three weeks ago (part 2 decision 8).
SHORT_RETENTION_DAYS = 7
NAMED_CATEGORIES: tuple[str, ...] = ("arming", "alarm", "security", "config")


@dataclass(frozen=True, slots=True)
class PersonRef:
    """Everything that points at one person in the log.

    ``user_id`` and ``names`` are how a row says they acted. ``device_ids``
    are the tags that are theirs and nobody else's (§9.3: a tag always names a
    person), and ``contact_ids`` are the address-book entries linked to them —
    both of which appear on rows where the person is the *subject* rather than
    the actor, which is what a subject access request is about (part 2
    decision 7).
    """

    user_id: str | None
    names: tuple[str, ...] = ()
    device_ids: tuple[str, ...] = ()
    contact_ids: tuple[str, ...] = ()
    pseudonym: str | None = None
    # Configuration rows written by somebody else *about* this person: they
    # carry the person's id in `detail.item_id` and the editor's name in the
    # user columns. Erasure reaches them too, or deleting an account would
    # leave the row that created it pointing at a person who no longer exists.
    item_id: str | None = field(default=None)

    @property
    def empty(self) -> bool:
        return not (self.user_id or self.names or self.device_ids or self.contact_ids)


def person_ref(config: FoyerConfig, user_id: str) -> PersonRef | None:
    """The person a request names, as the log knows them. None if unknown."""
    user = config.user(user_id)
    if user is None:
        return None
    return ref_for(config, user)


def ref_for(config: FoyerConfig, user: User) -> PersonRef:
    return PersonRef(
        user_id=user.id,
        names=(user.name,) if user.name else (),
        device_ids=tuple(
            device.id for device in config.devices if device.user_id == user.id
        ),
        contact_ids=tuple(
            contact.id
            for contact in config.contacts
            if contact.linked_user_id == user.id
        ),
        pseudonym=user.pseudonym,
        item_id=user.id,
    )


def new_pseudonym(token: str) -> str:
    """A stable opaque identifier, from a token the caller generated.

    The token is passed in rather than made here: ``core/`` reads no random
    source it was not given (INV-1), and a pseudonym that changed every time
    it was computed would be no pseudonym at all.
    """
    return f"person-{token[:12]}"


def cutoff(now: datetime, days: int) -> datetime:
    """The moment before which rows are old enough to lose their names."""
    return now - timedelta(days=max(MIN_PSEUDONYMISE_DAYS, int(days)))


def redact_detail(detail: Mapping[str, Any], names: Sequence[str]) -> dict[str, Any]:
    """The JSON detail with this person's name taken out of it.

    Names reach `detail` by the side door: a configuration row summarises what
    changed by the *name* of the thing, so "Luca's tag" and a contact called
    after somebody are in there under `changes`. Matching is case-insensitive
    and on the whole word or any string containing it, because that is how a
    person's name gets into an object's name in the first place.
    """
    wanted = tuple(n.strip().casefold() for n in names if n and n.strip())
    if not wanted:
        return dict(detail)
    return _redact(dict(detail), wanted)  # type: ignore[return-value]


def _redact(value: Any, names: Sequence[str]) -> Any:
    if isinstance(value, str):
        low = value.casefold()
        return REDACTED if any(name in low for name in names) else value
    if isinstance(value, dict):
        return {
            (_redact(key, names) if isinstance(key, str) else key): _redact(item, names)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item, names) for item in value]
    return value


def erased_row(
    row: Mapping[str, Any], ref: PersonRef, *, pseudonym: str | None = None
) -> dict[str, Any]:
    """One row as it looks after the erasure — for the preview, and for tests.

    The store writes the same thing; this is where what it writes is decided,
    so the panel can show a person exactly what will be left before anybody
    presses the button.
    """
    out = dict(row)
    for column in ERASED_COLUMNS:
        out[column] = None
    if pseudonym:
        # The minimisation form of the same operation: the shape of the nights
        # without the name (part 2 decision 1).
        out["user_id"] = pseudonym
        out["user_name"] = pseudonym
    if row.get("detail"):
        out["detail"] = redact_detail(row["detail"], ref.names)
    return out
