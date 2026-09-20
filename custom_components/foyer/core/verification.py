"""One windowed-activation engine for three settings (SPEC §4.2, §4.8).

A verification group (N of M zones within a window), a zone's cross-zone
field and a zone's trigger count are configured in three places and evaluated
here as one thing: a window of activations and a threshold. The cross-zone
field is a degenerate 2-of-2 group (decision 21); a trigger count is a window
over one zone that counts repeats instead of distinct zones.

Pure: it only derives Verification objects from the configuration and counts
activations. What an activation *is* (only what would trigger at once, part 2
decisions 6 and 12) is the engine's business.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Activation, Channel, FoyerConfig, Zone

GROUP = "group"  # a configured group or a cross-zone pair: one representation
COUNT = "count"


@dataclass(frozen=True, slots=True)
class Verification:
    """A window and its threshold, whichever setting it came from.

    ``key`` names its window in RuntimeState.windows. ``group_id`` is the
    group's id, or for a cross-zone pair a derived "cross:" id: otherwise a
    pair is a group in every respect, trace included (§4.8: one engine, one
    representation). ``distinct`` counts different zones (groups) rather than
    repeats of one (trigger count).
    """

    key: str
    kind: str
    group_id: str | None
    area_id: str
    members: tuple[str, ...]
    n: int
    window: int
    distinct: bool
    suppress: bool

    def expired(self, activation: Activation, now: datetime) -> bool:
        """Outside the window: strictly older than ``window`` seconds."""
        return now - activation.at > timedelta(seconds=self.window)

    def expires_at(self, activation: Activation) -> datetime:
        # Strictly after the window, matching expired().
        return activation.at + timedelta(seconds=self.window, microseconds=1)

    def count(self, activations: tuple[Activation, ...]) -> int:
        if self.distinct:
            return len({a.zone_id for a in activations})
        return len(activations)


def cross_zone_id(a: str, b: str) -> str:
    """The derived group id of a cross-zone pair, the same from either end."""
    return "cross:" + "+".join(sorted((a, b)))


def groups(config: FoyerConfig) -> tuple[Verification, ...]:
    """Every group: the configured ones, then one per cross-zone pair.

    A pair is symmetric (part 2 decision 4): A pointing at B forms {A, B}
    whether or not B points back; if it does, it is the same pair. A pair
    never suppresses its members: each zone still alarms on its own.
    """
    zones = {z.id: z for z in config.zones if z.enabled}
    out = [
        Verification(
            key=f"group:{g.id}",
            kind=GROUP,
            group_id=g.id,
            area_id=g.area_id,
            members=tuple(m for m in g.members if m in zones),
            n=g.n,
            window=g.window_seconds,
            distinct=True,
            suppress=g.suppress_members,
        )
        for g in config.groups
        # A group with fewer enabled members left than its threshold can
        # never be satisfied, and a suppressing one would then hold back
        # every alarm its survivors raise for ever — an enabled PIR seeing an
        # intruder in an armed area and producing one `verification_pending`
        # row and nothing else (found in review). Dropped entirely instead:
        # the members alarm on their own, which is what they do when no group
        # is watching them, and page 13 says the group is incomplete.
        if len([m for m in g.members if m in zones]) >= g.n
    ]
    seen: set[str] = set()
    for zone in config.zones:
        partner = zones.get(zone.cross_zone_id or "")
        if zone.id not in zones or partner is None:
            continue
        group_id = cross_zone_id(zone.id, partner.id)
        if group_id in seen:
            continue
        seen.add(group_id)
        out.append(
            Verification(
                key=f"group:{group_id}",
                kind=GROUP,
                group_id=group_id,
                area_id=zone.area_id,
                members=tuple(sorted((zone.id, partner.id))),
                n=2,
                window=zone.cross_zone_window,
                distinct=True,
                suppress=False,
            )
        )
    return tuple(out)


def group_of(config: FoyerConfig, zone_id: str) -> Verification | None:
    """The group a zone belongs to. Validation allows at most one."""
    return next((g for g in groups(config) if zone_id in g.members), None)


def counter_of(zone: Zone) -> Verification | None:
    """A zone's own trigger count, when it needs more than one activation."""
    if zone.trigger_count <= 1 or zone.channel is not Channel.INTRUSION:
        return None
    return Verification(
        key=f"count:{zone.id}",
        kind=COUNT,
        group_id=None,
        area_id=zone.area_id,
        members=(zone.id,),
        n=zone.trigger_count,
        window=zone.trigger_window,
        distinct=False,
        suppress=True,  # below the count the zone does nothing at all
    )


def all_windows(config: FoyerConfig) -> dict[str, Verification]:
    """Every window the configuration can open, by key."""
    out = {v.key: v for v in groups(config)}
    for zone in config.zones:
        if zone.enabled and (counter := counter_of(zone)) is not None:
            out[counter.key] = counter
    return out
