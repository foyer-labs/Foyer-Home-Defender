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
# `action` names who acknowledged (§7.2), so it is one of them (third review).
NAMED_CATEGORIES: tuple[str, ...] = ("arming", "alarm", "action", "security", "config")


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
    # The Home Assistant account linked to them, if any. It is here because a
    # configuration row records *the Home Assistant user* who saved it — a
    # different namespace from the Foyer user id every other row carries — so
    # without it an erasure reaches nothing anybody ever changed from the
    # panel, and reports honestly that it found nothing (found in review).
    ha_user_id: str | None = None
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
        return not (
            self.user_id
            or self.ha_user_id
            or self.names
            or self.device_ids
            or self.contact_ids
            or self.item_id
        )


def person_ref(config: FoyerConfig, user_id: str) -> PersonRef | None:
    """The person a request names, as the log knows them. None if unknown."""
    user = config.user(user_id)
    if user is None:
        return None
    return ref_for(config, user)


def ref_for(config: FoyerConfig, user: User) -> PersonRef:
    return PersonRef(
        user_id=user.id,
        ha_user_id=user.ha_user_id,
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
    changed by the *name* of the thing, so "Ana's tag" and a contact called
    after somebody are in there under `changes`.

    Matching is on whole words, not on substrings, and that is not tidiness.
    A person called Ed or Id, matched as a substring, redacts `added`,
    `changed`, `enabled`, `item_id`, `area_id` and `zone_id` — which is every
    key this project writes, and the erasure would destroy the *what happened*
    that §10.4 exists to preserve, in an UPDATE with nothing behind it.

    Two keys that both redact would collapse into one in a dict, losing a row's
    content with no error and no count, so a redacted key is made unique.
    """
    wanted = tuple(n.strip().casefold() for n in names if n and n.strip())
    if not wanted:
        return dict(detail)
    return _redact(dict(detail), wanted)  # type: ignore[return-value]


def _word_in(value: str, names: Sequence[str]) -> bool:
    """Whether one of these names appears in ``value`` as a whole word."""
    low = value.casefold()
    for name in names:
        start = low.find(name)
        while start != -1:
            before = low[start - 1] if start else ""
            after_at = start + len(name)
            after = low[after_at] if after_at < len(low) else ""
            # A word boundary on both sides, where "word" is what a name is
            # made of: letters, digits and the underscore that every key in
            # this project uses. An apostrophe is not one, so "Ana's tag"
            # still matches "Ana".
            if not (before.isalnum() or before == "_") and not (
                after.isalnum() or after == "_"
            ):
                return True
            start = low.find(name, start + 1)
    return False


def _redact(value: Any, names: Sequence[str]) -> Any:
    if isinstance(value, str):
        return REDACTED if _word_in(value, names) else value
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            clean = _redact(item, names)
            if isinstance(key, str) and _word_in(key, names):
                # Unique, so two redacted siblings stay two entries.
                marker = REDACTED
                index = 2
                while marker in out:
                    marker = f"{REDACTED} {index}"
                    index += 1
                out[marker] = clean
            else:
                out[key] = clean
        return out
    if isinstance(value, (list, tuple)):
        return [_redact(item, names) for item in value]
    return value


def unlink_detail(detail: Mapping[str, Any], user_id: str) -> dict[str, Any]:
    """The detail with the link back to a person removed.

    A configuration row *about* somebody carries their id in ``item_id``. An
    erasure that left it would leave the one field that still says which
    account the row was about — and would match the same row again on the next
    run, so the panel would go on reporting rows to erase after erasing them.
    """
    out = dict(detail)
    if out.get("item_id") == user_id:
        out.pop("item_id", None)
    return out
