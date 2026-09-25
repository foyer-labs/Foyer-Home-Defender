"""System health arithmetic (SPEC §12). Pure, like everything in ``core``.

"An alarm that cannot tell you it has stopped working has stopped working."
This module owns the counting behind that sentence — how many zones went
quiet inside one window, how many sends failed in a row, how many pings were
missed — and nothing else. It performs no I/O and reads no clock it was not
given: the HTTP request, the service-registry read and the entity lookup all
happen in ``runtime/`` and arrive here as facts (``HealthReport``, and the
snapshot's ``radios`` map).

The engine spends what this module computes, exactly as it spends
``core.rules``. Keeping the arithmetic here is what lets the simulator and
the test suite ask "eight zones on one radio, coordinator answering — what
does Foyer do?" with no Home Assistant instance anywhere near it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from .models import (
    MAINS_OUTSIDE_UPS,
    AreaState,
    ChannelFault,
    ChannelHealth,
    EntityState,
    FoyerConfig,
    HealthCause,
    Radio,
    SystemHealth,
    SystemSnapshot,
    channel_key,
)

# What "cannot be read" means, once, so mains, coordinators and zones all
# answer it the same way (INV-4). A missing entity is the strongest form of
# it: the integration is not even loaded.
UNREADABLE: frozenset[str] = frozenset({"unavailable", "unknown"})


def is_unreadable(entity: EntityState | None) -> bool:
    return entity is None or entity.state is None or entity.state in UNREADABLE


# --- mains power (§12.1) -----------------------------------------------------------


def mains_state(
    config: FoyerConfig,
    snapshot: SystemSnapshot,
    quiet_since: Mapping[str, datetime] | None = None,
    now: datetime | None = None,
) -> bool | None:
    """True when the mains has failed, False when it is fine, None unreadable.

    The three answers are deliberately not two. An entity Foyer cannot read
    is not a power cut — a UPS integration that has not finished loading
    would announce one at every restart — and it is not "all quiet" either,
    which is the whole of INV-4.

    With devices outside the UPS (decision 162) silence *is* the reading,
    so the rule turns round: the mains is present while any of them
    answers, and lost once every one has been silent for the delay since
    Foyer saw it go (``quiet_since``). A device silent since before Foyer
    was watching is not in ``quiet_since``, and while one of them is among
    the silent the answer is None — not known — rather than a power cut
    Foyer never saw happen. Without ``now`` the delay cannot be measured and
    a silence still counts as present: the established failure is carried by
    ``mains_lost_since``, which the engine sets.
    """
    health = config.health
    if health.mains_mode == MAINS_OUTSIDE_UPS:
        entity_ids = health.mains_outside_entity_ids
        if not entity_ids:
            return False
        entities = [snapshot.entity(e) for e in entity_ids]
        if any(e is None or e.state is None for e in entities):
            return None  # removed from Home Assistant: a configuration fault
        if not all(is_unreadable(e) for e in entities):
            return False
        since = quiet_since or {}
        if not all(e in since for e in entity_ids):
            return None
        if now is None:
            return False
        started = max(since[e] for e in entity_ids)
        return now - started >= timedelta(seconds=health.mains_outside_delay)
    entity_id = health.mains_entity_id
    if not entity_id:
        return False  # nothing configured: not a failure, and not unreadable
    entity = snapshot.entity(entity_id)
    if is_unreadable(entity):
        return None
    return entity.state in config.health.mains_lost_states


# --- radios and correlated silence (§12.5) -----------------------------------------


def zones_on(
    config: FoyerConfig, snapshot: SystemSnapshot, radio: Radio
) -> tuple[str, ...]:
    """The enabled zones whose entity sits on this radio."""
    return tuple(
        zone.id
        for zone in config.zones
        if zone.enabled and snapshot.radio_of(zone.entity_id) == radio.id
    )


def coordinator_answering(radio: Radio, snapshot: SystemSnapshot) -> bool | None:
    """Whether the coordinator is reachable. None when none was named.

    None is not "yes". A radio with no coordinator entity cannot be gated,
    and §12.5 is explicit that the gate is what separates interference from a
    dead switch — so Foyer raises nothing on such a radio and the panel says
    why. Half a heuristic is a heuristic that teaches people to ignore it.
    """
    if not radio.coordinator_entity_id:
        return None
    return not is_unreadable(snapshot.entity(radio.coordinator_entity_id))


def burst(
    quiet_since: Mapping[str, datetime],
    zone_ids: Sequence[str],
    window: int,
) -> tuple[str, ...]:
    """The largest group of these zones that fell silent inside one window.

    Not "how many are quiet now": a house with four flat batteries collected
    over four months is not being jammed. What §12.5 describes is a burst, so
    what is counted is how close together the silences began. The zones stay
    counted while they are still quiet — the timestamps do not move — which
    is what keeps a confirmed suspicion confirmed instead of expiring one
    window later while the radio is still down.
    """
    times = sorted(
        ((quiet_since[z], z) for z in zone_ids if z in quiet_since),
        key=lambda pair: (pair[0], pair[1]),
    )
    if not times:
        return ()
    span = timedelta(seconds=max(0, window))
    best: tuple[str, ...] = ()
    start = 0
    for end in range(len(times)):
        while times[end][0] - times[start][0] > span:
            start += 1
        if end - start + 1 > len(best):
            best = tuple(zone for _, zone in times[start : end + 1])
    return best


# --- notification channels (§12.2) -------------------------------------------------


def configured_channels(config: FoyerConfig) -> dict[str, str]:
    """Every enabled channel of every enabled contact: key -> notify service."""
    return {
        channel_key(contact.id, channel.id): channel.service
        for contact in config.contacts
        if contact.enabled
        for channel in contact.channels
        if channel.enabled
    }


def all_channels(config: FoyerConfig) -> frozenset[str]:
    """Every channel key the configuration holds, enabled or not: what the
    stored health may still speak of (see ``Engine.__init__``)."""
    return frozenset(
        channel_key(contact.id, channel.id)
        for contact in config.contacts
        for channel in contact.channels
    )


def channel_after(
    current: ChannelHealth,
    now: datetime,
    *,
    present: bool | None = None,
    sent_ok: bool | None = None,
    threshold: int = 2,
) -> ChannelHealth:
    """This channel's health after one observation. The only place it moves.

    Two kinds of evidence, and they are not the same weight. A service that
    is not in the registry is broken with certainty, now, on the first
    sweep that finds it gone: the integration was removed, renamed, or
    failed to load after an update, and no send can possibly succeed. A
    failed send is evidence, so it takes ``threshold`` of them in a row —
    and any success clears everything, because a channel that has just
    delivered a message works whatever it did last week.
    """
    failures = current.failures
    last_ok = current.last_ok
    last_failed = current.last_failed
    if sent_ok is True:
        failures = 0
        last_ok = now
    elif sent_ok is False:
        failures += 1
        last_failed = now
    known = current.present if present is None else present
    fault: ChannelFault | None = None
    if known is False:
        fault = ChannelFault.MISSING_SERVICE
    elif failures >= max(1, threshold):
        fault = ChannelFault.SEND_FAILED
    since = current.since
    if fault is None:
        since = None
    elif current.fault is None or since is None:
        since = now
    return ChannelHealth(
        fault=fault,
        since=since,
        failures=failures,
        last_ok=last_ok,
        last_failed=last_failed,
        present=known,
    )


def broken_channels(health: SystemHealth, config: FoyerConfig) -> tuple[str, ...]:
    """The keys of every configured channel currently broken, in config order."""
    return tuple(
        key for key in configured_channels(config) if health.channel(key).fault
    )


def announce_over(
    config: FoyerConfig, channels: Mapping[str, ChannelHealth], key: str
) -> tuple[str, str] | None:
    """A working channel of the same contact, to say the broken one is broken.

    §12.2's rule, and the only part of it Foyer can answer by itself:
    warning somebody about a dead channel over the dead channel is the joke
    that writes itself. Which *contacts* hear about it is the household's to
    configure, through a response profile on ``notification_channel_down``;
    what is decided here is that the message never goes out over anything
    that is itself broken. Returns (contact_id, channel_id), or None when
    this contact has nothing left that works — the case that is itself worth
    saying out loud, and which the moment's own notification does.
    """
    contact_id, _, _ = key.partition(":")
    contact = config.contact(contact_id)
    if contact is None:
        return None
    for channel in contact.channels:
        if not channel.enabled:
            continue
        candidate = channel_key(contact.id, channel.id)
        known = channels.get(candidate)
        if candidate != key and (known is None or known.fault is None):
            return contact.id, channel.id
    return None


# --- the watchdog's payload (§12.3, P-1) -------------------------------------------


def watchdog_payload(
    config: FoyerConfig, snapshot: SystemSnapshot
) -> Mapping[str, object] | None:
    """What the heartbeat carries. Nothing, unless somebody turned it on.

    This is P-1 in its original case (decision 29). A ping saying "armed,
    Night, nobody home" is a channel telling whoever holds the other end
    exactly when to come, and the other end is a third party by definition —
    that is the whole point of an external watchdog. So the default is an
    empty request, and the option that adds the state of the house is off,
    with the reason written next to it in the panel.

    Even switched on it says the least that is useful: how many areas are
    armed and whether anything is wrong, never which scenario, never which
    areas, never which zones are open.
    """
    if not config.health.watchdog.payload:
        return None
    armed = sum(
        1 for rt in snapshot.state.areas.values() if rt.state is not AreaState.DISARMED
    )
    return {
        "armed_areas": armed,
        "areas": len(config.areas),
        "healthy": not causes(snapshot.state.health, config, snapshot),
    }


# --- the whole picture (§13) -------------------------------------------------------


def causes(
    health: SystemHealth,
    config: FoyerConfig,
    snapshot: SystemSnapshot,
) -> tuple[HealthCause, ...]:
    """Why ``binary_sensor.foyer_system_health`` is on, in a stable order.

    Zone faults are in here as well as on ``binary_sensor.foyer_fault``
    (§13): the two entities answer different questions — "can I arm" and "is
    anything wrong with the system" — and a house whose only fault is a dead
    contact should light exactly one of them.
    """
    found: list[HealthCause] = []
    if snapshot.state.faults:
        found.append(HealthCause.ZONE_FAULT)
    mains = mains_state(config, snapshot, health.mains_quiet_since)
    # A failure already established stands even when the entity stops
    # answering — which is the realistic case, because the NUT server and
    # the router die with the mains (§12.3). Withdrawing a fault because
    # the thing reporting it went with the power is the "quiet night" §12.1
    # says this must never be confused with.
    if mains is True or health.mains_lost_since is not None:
        found.append(HealthCause.MAINS_LOST)
    if mains is None:
        found.append(HealthCause.MAINS_UNKNOWN)
    if broken_channels(health, config):
        found.append(HealthCause.CHANNEL_DOWN)
    if config.health.watchdog.enabled and health.watchdog.down_since is not None:
        found.append(HealthCause.WATCHDOG_UNREACHABLE)
    if any(r.confirmed for r in health.radios.values()):
        found.append(HealthCause.RF_INTERFERENCE)
    if any(r.coordinator_down_since is not None for r in health.radios.values()):
        found.append(HealthCause.COORDINATOR_DOWN)
    return tuple(found)
