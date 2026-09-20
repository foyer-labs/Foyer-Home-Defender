"""Turning occurrences into actions: response profiles, pure (SPEC §6).

The engine says *what happened*; this module says *what should happen about
it*. It resolves the profile, evaluates the conditions, renders the templates
and produces the ActionIntents the executor runs — deciding everything, so the
executor decides nothing and the simulator's trace cannot disagree with the
runtime (INV-1).

Who answers for an occurrence (part 3 decision 1): **the area is the unit of
response**. Its chain is area → scenario → global default. A zone's own
profile is read only for its own alarm — the trigger, the entry it opens, the
group it satisfies — which is what makes graduated response work (§4.8): quiet
member profiles, a loud group profile. The technical channel has its own
default, because a smoke alarm must not respond differently depending on how
the house is armed (§5.5).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, tzinfo
from typing import Any

from .clock import in_daily_window
from .conditions import evaluate, unmet
from .journal import severity_of
from .models import (
    ActionIntent,
    ActionKind,
    AreaRuntime,
    ChimeSettings,
    Contact,
    ContactChannel,
    FoyerConfig,
    Incident,
    LogSeverity,
    Moment,
    Occurrence,
    PendingRun,
    ProfileAction,
    ResponseProfile,
    RunningAction,
    StateCondition,
    SystemSnapshot,
    TimeCondition,
    Zone,
)
from .templates import render
from .validation import notify_contacts

# The log's own scale, ordered (§10.1). A contact's quiet hours are read
# against it rather than against the profile ``severity`` of §6.5, which that
# section states is used for nothing but choosing an escalation.
SEVERITY_ORDER: tuple[LogSeverity, ...] = (
    LogSeverity.INFO,
    LogSeverity.WARNING,
    LogSeverity.ALARM,
)

# The alarm of a zone: the only moments that read the zone's own profile
# (part 3 decision 1).
ZONE_MOMENTS: frozenset[Moment] = frozenset(
    {Moment.TRIGGERED, Moment.ENTRY_STARTED, Moment.VERIFICATION_SATISFIED}
)

# The technical channel's own moments (§5.5).
TECHNICAL_MOMENTS: frozenset[Moment] = frozenset(
    {
        Moment.TECHNICAL_RAISED,
        Moment.TECHNICAL_ACKNOWLEDGED,
        Moment.TECHNICAL_CLEARED,
    }
)

# Inside one incident these are unioned and deduplicated: a siren already
# sounding is not restarted (§5.6). Everything else — a disarm, a fault —
# happens in its own right even in an incident's area.
UNION_MOMENTS: frozenset[Moment] = frozenset(
    {
        Moment.TRIGGERED,
        Moment.ENTRY_STARTED,
        Moment.VERIFICATION_SATISFIED,
        Moment.INCIDENT_OPENED,
        Moment.INCIDENT_JOINED,
    }
)

# What an acknowledgement can stop, and therefore what an actionable button
# may offer to stop (§7.2). Two things escalate, and these are the moments
# that start them; a button on an "armed" notification would acknowledge
# nothing.
ACK_MOMENTS: frozenset[Moment] = frozenset(
    {
        Moment.TRIGGERED,
        Moment.INCIDENT_OPENED,
        Moment.INCIDENT_JOINED,
        Moment.TECHNICAL_RAISED,
    }
)

# Kinds that leave something switched on and need switching off again.
REVERTIBLE: frozenset[str] = frozenset(
    {ActionKind.SIREN.value, ActionKind.SWITCH.value}
)

REVERT = "revert"


@dataclass(frozen=True, slots=True)
class PlanContext:
    """Everything the planner may read. Given, never looked up (INV-1)."""

    config: FoyerConfig
    snapshot: SystemSnapshot
    now: datetime
    areas: Mapping[str, AreaRuntime]
    incident: Incident | None = None
    active_zones: frozenset[str] = frozenset()
    # A walk test is running (§11.3). Not a switch the executor flips: what
    # it inhibits is decided here, per occurrence, because `always_on` zones
    # stay fully live and a walk test must never silence a smoke detector.
    walk_test: bool = False
    # Radios whose interference is confirmed right now (§12.5). An action's
    # targets on one of them are dropped: announcing a Zigbee blackout
    # through a Zigbee siren is not a notification, and it is the one rule
    # that defeats the whole feature if it is missed. What was dropped
    # travels on the intent, so the message can say the siren did not sound
    # rather than leaving somebody to find out later.
    impaired: frozenset[str] = frozenset()
    # The contact channels Foyer currently believes are broken (§12.2),
    # keyed "<contact_id>:<channel_id>". Given rather than read off the
    # snapshot because the decision that discovered the breakage is the one
    # planning the message about it: the snapshot still holds the state the
    # call began with.
    broken_channels: frozenset[str] = frozenset()

    @property
    def tz(self) -> tzinfo:
        return self.snapshot.timezone


@dataclass(slots=True)
class Plan:
    """What one batch of occurrences produces."""

    intents: list[ActionIntent] = field(default_factory=list)
    pending: list[PendingRun] = field(default_factory=list)
    running: list[RunningAction] = field(default_factory=list)
    started: list[str] = field(default_factory=list)
    # Actions a walk test held back: built like the others and deliberately
    # not in ``intents``, so they cannot reach the executor by accident
    # (part 2 decision 1).
    inhibited: list[ActionIntent] = field(default_factory=list)

    def extend(self, other: Plan) -> None:
        self.intents.extend(other.intents)
        self.pending.extend(other.pending)
        self.running.extend(other.running)
        self.started.extend(other.started)
        self.inhibited.extend(other.inhibited)


# --- profile resolution ------------------------------------------------------------


# Where an effective profile came from. §6 says the UI must always show it —
# "otherwise the behaviour looks arbitrary" — and the simulator's trace says
# it on every step (§11.2).
FROM_ZONE = "zone"
FROM_GROUP = "group"
FROM_AREA = "area"
FROM_SCENARIO = "scenario"
FROM_TECHNICAL = "technical"
FROM_DEFAULT = "default"
FROM_NONE = "none"


def _area_chain(
    config: FoyerConfig, area_id: str | None, scenario_id: str | None
) -> tuple[ResponseProfile | None, str]:
    area = config.area(area_id)
    scenario = config.scenario(scenario_id)
    for candidate, source in (
        (area.response_profile_id if area else None, FROM_AREA),
        (scenario.response_profile_id if scenario else None, FROM_SCENARIO),
        (config.settings.default_profile_id, FROM_DEFAULT),
    ):
        if (profile := config.profile(candidate)) is not None:
            return profile, source
    return None, FROM_NONE


def area_profile(
    config: FoyerConfig, area_id: str | None, scenario_id: str | None
) -> ResponseProfile | None:
    """area → scenario → global default (SPEC §6)."""
    return _area_chain(config, area_id, scenario_id)[0]


def resolve_profile(
    config: FoyerConfig,
    *,
    area_id: str | None = None,
    zone_id: str | None = None,
    group_id: str | None = None,
    scenario_id: str | None = None,
    moment: Moment | None = None,
) -> tuple[ResponseProfile | None, str]:
    """The profile that answers, **and where it was inherited from** (§6).

    The two are resolved together, in one function, because they are the same
    walk down the same chain: a separate "where did it come from" would be a
    second implementation of the inheritance rule, free to disagree with the
    first, and the trace would then explain a decision the engine did not
    make (part 3 decision 1, §11.2).
    """
    zone = config.zone(zone_id)
    if moment in TECHNICAL_MOMENTS:
        for candidate, source in (
            (zone.response_profile_id if zone else None, FROM_ZONE),
            (config.settings.technical_profile_id, FROM_TECHNICAL),
            (config.settings.default_profile_id, FROM_DEFAULT),
        ):
            if (profile := config.profile(candidate)) is not None:
                return profile, source
        return None, FROM_NONE
    if moment is Moment.VERIFICATION_SATISFIED and (
        (group := config.group(group_id)) is not None
    ):
        # Only the satisfied group answers with the group's profile: its
        # members keep their own when they alarm on their own (§4.8). That is
        # what makes the response graduated instead of uniform.
        if (profile := config.profile(group.response_profile_id)) is not None:
            return profile, FROM_GROUP
        return _area_chain(config, group.area_id, scenario_id)
    if (
        moment in ZONE_MOMENTS
        and zone is not None
        and (profile := config.profile(zone.response_profile_id)) is not None
    ):
        return profile, FROM_ZONE
    return _area_chain(config, area_id, scenario_id)


def effective_profile(
    config: FoyerConfig,
    *,
    area_id: str | None = None,
    zone_id: str | None = None,
    group_id: str | None = None,
    scenario_id: str | None = None,
    moment: Moment | None = None,
) -> ResponseProfile | None:
    """The profile that answers — the one rule of part 3 decision 1."""
    return resolve_profile(
        config,
        area_id=area_id,
        zone_id=zone_id,
        group_id=group_id,
        scenario_id=scenario_id,
        moment=moment,
    )[0]


# --- the actions of one moment -----------------------------------------------------


def sequence(profile: ResponseProfile, moment: Moment) -> tuple[ProfileAction, ...]:
    """The profile's actions for this moment, in the order the user put them.

    A ``delay`` participates like any other action: it holds back whatever
    comes after it *in this sequence*.

    An escalation step is **not** here, and this is the one place that takes
    it out (§7.2, part 1 decision 1). A step is an action at an offset, run
    by core.escalation when its time comes; leaving it in the sequence would
    send every step at once, which is the phone spam §5.6 exists to prevent.
    """
    return tuple(
        a
        for a in profile.actions
        if a.enabled and moment in a.moments and not a.is_step
    )


# Why an action in a profile's sequence did not run. The simulator shows
# these words (§11.2: "which were skipped AND WHY"), and it shows them
# because skip_reason below is the one place that decides — a second copy of
# the rule would let the trace explain a skip that never happened.
SKIP_SILENT = "silent"
SKIP_ALREADY_RUNNING = "already_running"
SKIP_CONDITION = "condition"
SKIP_HELD_BY_DELAY = "held_by_delay"
SKIP_WALK_TEST = "walk_test"
# Every contact this notification names is inside their quiet hours and what
# happened is not loud enough to reach them (§7.1, part 1 decision 3).
SKIP_QUIET_HOURS = "quiet_hours"


def reachable(
    ctx: PlanContext, action: ProfileAction, moment: Moment
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """Who a notification actually reaches now, and who is in quiet hours.

    Returns the recipients — each one a contact, a channel and everything
    that channel's transport needs, complete, so the executor looks nothing
    up (INV-1) — and the ids of the contacts the window held back.

    A contact's quiet hours let through what is at least as loud as the
    severity they set, on the log's own scale of info / warning / alarm
    (§10.1, part 1 decision 3). The default is ``alarm``: a break-in gets
    through at four in the morning and a successful arming does not.
    """
    refs = notify_contacts(action)
    if not refs:
        return (), ()
    return recipients_for(
        ctx.config,
        refs,
        ctx.now,
        ctx.tz,
        moment,
        ack=moment in ACK_MOMENTS,
        # §12.2, and only here: the message that says a channel is broken
        # does not go over that channel. Every other message still tries
        # one Foyer believes is broken — two failed sends can be a provider
        # with a hiccup, and being wrong about a channel must never be the
        # reason an alarm reached nobody.
        avoid=(
            ctx.broken_channels
            if moment is Moment.NOTIFICATION_CHANNEL_DOWN
            else frozenset()
        ),
    )


def recipients_for(
    config: FoyerConfig,
    refs: Sequence[Mapping[str, Any]],
    now: datetime,
    tz: tzinfo,
    moment: Moment,
    *,
    ack: bool = False,
    cancel: str | None = None,
    avoid: frozenset[str] = frozenset(),
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """The contacts a message actually reaches now, and who quiet hours held.

    Shared by an escalation's notification and by an automatic rule's
    countdown (§9.4), so that "who hears this" is answered in one place and a
    contact's quiet hours mean the same thing whatever is speaking.

    ``ack`` and ``cancel`` are the two buttons an actionable channel can
    carry, and they are the same mechanism with a different action id: one
    stops an escalation, the other stops a house arming itself.
    """
    # A test really executes: that is the whole of §11.4, and the failure it
    # prevents is discovering during the emergency that the channel was
    # misconfigured. Quiet hours are a rule about alarms, not about whether
    # the phone rings when somebody presses "test".
    testing = moment is Moment.ACTION_TESTED
    loudness = SEVERITY_ORDER.index(severity_of(moment))
    recipients: list[Mapping[str, Any]] = []
    quiet: list[str] = []
    for ref in refs:
        contact = config.contact(ref["contact_id"])
        if contact is None or not contact.enabled:
            continue
        if (
            not testing
            and contact.quiet_start
            and contact.quiet_end
            and in_daily_window(now, tz, contact.quiet_start, contact.quiet_end)
            and loudness < SEVERITY_ORDER.index(contact.quiet_min_severity)
        ):
            quiet.append(contact.id)
            continue
        channel = contact.channel(ref["channel_id"])
        if channel is None:
            continue
        if f"{contact.id}:{channel.id}" in avoid:
            # Warning somebody about a dead channel over the dead channel is
            # the joke that writes itself (§12.2). The caller says when this
            # applies; it is not a general rule about broken channels.
            continue
        recipients.append(
            {
                "contact_id": contact.id,
                "contact_name": contact.name,
                "channel_id": channel.id,
                "kind": channel.kind.value,
                "service": channel.service,
                "target": channel.target,
                "data": dict(channel.data),
                # Whether this channel can carry the button that
                # acknowledges the alarm, and whether there is anything to
                # acknowledge (§7.2). Decided here, so the executor adds a
                # button or does not and decides neither. The Cancel button
                # of §9.4 is the same mechanism, carrying which countdown it
                # would stop.
                "ack": channel.actionable and ack,
                "cancel": cancel if channel.actionable else None,
                "user_id": contact.linked_user_id,
            }
        )
    return tuple(recipients), tuple(quiet)


def skip_reason(
    action: ProfileAction,
    ctx: PlanContext,
    *,
    moment: Moment,
    suppressed: frozenset[str],
    already_started: frozenset[str],
    inhibited: bool = False,
) -> str | None:
    """Why this action does not run now, or None when it does.

    The order is the order of the reasons, not of the checks: a walk test
    answers before anything else is asked, a silent zone suppresses before
    anything is evaluated, a siren already sounding is not restarted before
    its conditions are asked again, and only what survives all three is put
    to its conditions. Changing the order changes what the trace says
    happened, so there is one of it.
    """
    if inhibited:
        # §11.3: during a walk test the response is held back and nothing
        # else about this action matters. Whether it *would* have run is a
        # different question, and the simulator is the page that answers it.
        return SKIP_WALK_TEST
    if action.kind.value in suppressed:
        return SKIP_SILENT
    if action.id in already_started and moment in UNION_MOMENTS:
        return SKIP_ALREADY_RUNNING
    if not evaluate(action, ctx.snapshot, ctx.now, ctx.tz):
        return SKIP_CONDITION
    if notify_contacts(action) and not reachable(ctx, action, moment)[0]:
        # Nobody left: every contact named is inside their quiet hours, or
        # has no channel to reach them by. A notification to nobody is not a
        # notification, and the trace says which it was.
        return SKIP_QUIET_HOURS
    return None


def _names(ids: Sequence[str | None], lookup: Mapping[str, str]) -> str:
    seen: list[str] = []
    for item in ids:
        if item and (name := lookup.get(item, item)) not in seen:
            seen.append(name)
    return ", ".join(seen)


def variables(ctx: PlanContext, group: Sequence[Occurrence]) -> dict[str, str]:
    """The fixed template variable set of §6.4, for one batch of occurrences."""
    config = ctx.config
    areas = {a.id: a.name for a in config.areas}
    zones = {z.id: z.name for z in config.zones}
    scenarios = {s.id: s.name for s in config.scenarios}
    local = ctx.now.astimezone(ctx.tz)
    detail: dict[str, str] = {}
    for occurrence in group:
        detail.update(occurrence.detail)
    zone_ids = [o.zone_id for o in group] + [z for o in group for z in o.zone_ids]
    states = [
        ctx.areas[o.area_id].state.value
        for o in group
        if o.area_id is not None and o.area_id in ctx.areas
    ]
    incident_zones = ctx.incident.zone_ids if ctx.incident is not None else ()
    return {
        "zone": _names([o.zone_id for o in group], zones) or _names(zone_ids, zones),
        "area": _names([o.area_id for o in group], areas),
        "scenario": _names([o.scenario_id for o in group], scenarios),
        "user": "",  # identities arrive in Phase 2
        "channel": _names([o.channel for o in group], {}),
        "time": local.strftime("%H:%M"),
        "date": local.strftime("%Y-%m-%d"),
        "state": _names(states, {}),
        "open_zones": _names(
            [z.id for z in config.zones if z.id in ctx.active_zones], zones
        ),
        "reason": detail.get("reason") or detail.get("cause", ""),
        "incident_zones": _names(list(incident_zones), zones),
        # Not a §6.4 variable: the built-in notification's own placeholder for
        # every zone of the batch, kept from Phase 0 so its text is unchanged.
        "zones": _names(zone_ids, zones),
        # The same kind of thing for system health (§12): facts the built-in
        # message needs and no household template may use. They are read
        # straight off the occurrence's detail, so a moment that does not
        # carry one simply leaves it empty.
        "radio": detail.get("radio", ""),
        "count": detail.get("count", ""),
        "of": detail.get("of", ""),
        "service": detail.get("service", ""),
        "contact": _names(
            [detail.get("contact_id")], {c.id: c.name for c in config.contacts}
        ),
        "seconds": detail.get("seconds", ""),
        "failures": detail.get("failures", ""),
        # Filled by run_sequence when a radio is suspected: what this
        # response will not be able to do (part 1 decision 9).
        "skipped": "",
    }


def _params(
    action: ProfileAction,
    values: Mapping[str, str],
    ctx: PlanContext,
    area_id: str | None,
    moment: Moment = Moment.TRIGGERED,
) -> dict[str, Any]:
    """The action's parameters, with every template already rendered."""
    params = {
        key: render(value, values) if isinstance(value, str) else value
        for key, value in action.params.items()
    }
    if action.kind is ActionKind.CALL_SERVICE and isinstance(
        params.get("data"), Mapping
    ):
        params["data"] = {
            key: render(value, values) if isinstance(value, str) else value
            for key, value in params["data"].items()
        }
    if action.kind is ActionKind.SIREN:
        # Never beyond the siren cutoff: a sounder that outlives the alarm is
        # what the cutoff exists to prevent (§5.3).
        area = ctx.areas.get(area_id or "")
        scenario = ctx.config.scenario(area.scenario_id if area else None)
        cutoff = ctx.config.siren_duration(scenario)
        duration = params.get("duration")
        params["duration"] = cutoff if not duration else min(int(duration), cutoff)
    if action.kind is ActionKind.CAMERA:
        params.setdefault("directory", ctx.config.settings.camera_dir)
    if action.kind is ActionKind.NOTIFY and notify_contacts(action):
        # The address book, resolved: who this reaches, through which
        # transport, with what that transport needs. The executor is handed
        # the answer and never opens the configuration (INV-1). ``quiet``
        # travels with it so the trace and the log can say who was not told
        # and why, which is the whole point of a window that holds messages
        # back (§7.1).
        recipients, quiet = reachable(ctx, action, moment)
        params["recipients"] = recipients
        params["quiet"] = quiet
    if ctx.impaired:
        _drop_impaired(params, ctx)
    if action.kind is ActionKind.NOTIFY and params.get("camera_entity_id"):
        # A notification that has to write the picture to a file writes it
        # where every other camera file goes, and the choice is made here so
        # the executor is left with nothing to decide (INV-1).
        params.setdefault("directory", ctx.config.settings.camera_dir)
    return params


# Every key an action can put an entity in, because "do not act through
# the affected radio" (§12.5) is the rule that defeats the whole feature if
# it is missed — and it is missed by reading only the obvious one. A siren
# names ``entity_ids``, a tts action names its media players, and
# ``call_service`` — §6.2's escape hatch, which is exactly what somebody
# reaches for when the native action does not fit — puts its targets inside
# ``target`` or ``data``.
_TARGET_KEYS = ("entity_ids", "entity_id", "media_player_entity_ids")
_NESTED_TARGETS = ("target", "data")


def _as_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(v) for v in value)
    return ()


def _entity_ids(params: Mapping[str, Any]) -> tuple[str, ...]:
    """Every entity this action would act on, wherever it names them."""
    found: list[str] = []
    for key in _TARGET_KEYS:
        found.extend(_as_list(params.get(key)))
    for key in _NESTED_TARGETS:
        nested = params.get(key)
        if isinstance(nested, Mapping):
            found.extend(_as_list(nested.get("entity_id")))
            found.extend(_as_list(nested.get("entity_ids")))
    return tuple(dict.fromkeys(found))


def _drop_impaired(params: dict[str, Any], ctx: PlanContext) -> None:
    """Remove every target that sits on a radio Foyer must not act through.

    In place, and across all the shapes above. What was dropped travels on
    the intent so the message can say the siren did not sound, rather than
    leaving somebody to find out afterwards.
    """

    def keep(value: Any) -> tuple[Any, tuple[str, ...]]:
        ids = _as_list(value)
        kept = [e for e in ids if ctx.snapshot.radio_of(e) not in ctx.impaired]
        dropped = tuple(e for e in ids if e not in kept)
        if not dropped:
            return value, ()
        return (kept[0] if kept else "") if isinstance(value, str) else kept, dropped

    dropped: list[str] = []
    for key in _TARGET_KEYS:
        if key in params:
            params[key], gone = keep(params[key])
            dropped.extend(gone)
    for key in _NESTED_TARGETS:
        nested = params.get(key)
        if not isinstance(nested, Mapping):
            continue
        updated = dict(nested)
        for inner in ("entity_id", "entity_ids"):
            if inner in updated:
                updated[inner], gone = keep(updated[inner])
                dropped.extend(gone)
        if dropped:
            params[key] = updated
    if dropped:
        params["skipped_entity_ids"] = list(dict.fromkeys(dropped))


def _emptied(action: ProfileAction, params: Mapping[str, Any]) -> bool:
    """The impaired-radio filter left this action with nothing to act on.

    Asked of the result rather than flagged during the filtering, so every
    caller of ``_params`` gets the same answer — an escalation step whose
    only siren is on the jammed radio must be skipped exactly as an
    immediate one is, and a marker riding in the params is a marker one
    call site forgets to read.
    """
    return bool(_entity_ids(action.params)) and not _entity_ids(params)


def _on_impaired_radio(
    ctx: PlanContext, actions: Sequence[ProfileAction]
) -> tuple[str, ...]:
    """The entities this sequence targets that sit on a suspected radio."""
    return tuple(
        dict.fromkeys(
            entity_id
            for action in actions
            for entity_id in _entity_ids(action.params)
            if ctx.snapshot.radio_of(entity_id) in ctx.impaired
        )
    )


def run_sequence(
    ctx: PlanContext,
    profile: ResponseProfile,
    moment: Moment,
    values: Mapping[str, str],
    *,
    start: int = 0,
    area_id: str | None = None,
    zone_id: str | None = None,
    incident_id: str | None = None,
    silent: bool = False,
    already_started: frozenset[str] = frozenset(),
    run_id: str = "",
    inhibited: bool = False,
) -> Plan:
    """Walk a profile's actions for one moment, from ``start``.

    Stops at a ``delay``, leaving a PendingRun that resumes at the same index
    in the same sequence. Skips actions whose conditions are not met, actions a
    silent zone suppresses, and actions this incident has already started.

    ``inhibited`` is a walk test (§11.3): every action of the sequence is
    built and diverted to ``plan.inhibited`` instead of ``plan.intents``, so
    nothing is executed and the record of what would have been survives. A
    ``delay`` is simply walked past — there is no sequence to hold back when
    none of it is going to run, and a PendingRun left behind would fire after
    the walk test ended.
    """
    plan = Plan()
    actions = sequence(profile, moment)
    suppressed = (
        frozenset(ctx.config.settings.silent_suppresses) if silent else frozenset()
    )
    if ctx.impaired and (dropped := _on_impaired_radio(ctx, actions)):
        # Said in plain words rather than left to be discovered: the message
        # that reports the interference also names what this response will
        # not be able to do because of it (part 1 decision 9). Not a §6.4
        # template variable — it reaches the built-in notification text and
        # nothing a household writes.
        values = {**values, "skipped": ", ".join(dropped)}
    for index in range(start, len(actions)):
        action = actions[index]
        if action.kind is ActionKind.DELAY:
            if inhibited:
                continue
            seconds = max(0, int(action.params.get("seconds", 0)))
            if seconds and index + 1 < len(actions):
                plan.pending.append(
                    PendingRun(
                        id=run_id,
                        profile_id=profile.id,
                        moment=moment,
                        index=index + 1,
                        due=ctx.now + timedelta(seconds=seconds),
                        area_id=area_id,
                        zone_id=zone_id,
                        incident_id=incident_id,
                        silent=silent,
                        placeholders=dict(values),
                    )
                )
                return plan
            continue
        why = skip_reason(
            action,
            ctx,
            moment=moment,
            suppressed=suppressed,
            already_started=already_started,
            inhibited=inhibited,
        )
        if why is not None and why != SKIP_WALK_TEST:
            continue
        params = _params(action, values, ctx, area_id, moment)
        if _emptied(action, params):
            # Every target of this action was on the affected radio, so
            # there is nothing left to run. Skipped rather than run empty:
            # an action with no targets is a service call that either errors
            # or does nothing, and neither is an honest record of what
            # happened.
            continue
        intent = ActionIntent(
            action_id=action.id,
            kind=action.kind.value,
            moment=moment,
            profile_id=profile.id,
            placeholders=dict(values),
            variant="area"
            if moment is Moment.ARMED and not values.get("scenario")
            else None,
            params=params,
        )
        if why == SKIP_WALK_TEST:
            # Nothing is switched on, so nothing is recorded as running and
            # the incident has started nothing: a siren that did not sound
            # must not be remembered as already sounding.
            plan.inhibited.append(intent)
            continue
        plan.intents.append(intent)
        if incident_id is not None and moment in UNION_MOMENTS:
            plan.started.append(action.id)
        if action.kind.value in REVERTIBLE:
            running = _running(action, params, area_id, incident_id, ctx.now)
            if running is not None:
                plan.running.append(running)
    return plan


def _running(
    action: ProfileAction,
    params: Mapping[str, Any],
    area_id: str | None,
    incident_id: str | None,
    now: datetime,
) -> RunningAction | None:
    entity_ids = _entity_ids(params)
    if not entity_ids:
        return None
    if action.kind is ActionKind.SIREN:
        duration = int(params.get("duration") or 0)
        return RunningAction(
            action_id=action.id,
            kind=action.kind.value,
            entity_ids=entity_ids,
            until=now + timedelta(seconds=duration) if duration else None,
            restore="off",
            area_id=area_id,
            incident_id=incident_id,
        )
    revert_after = params.get("revert_after")
    if not revert_after:
        return None
    return RunningAction(
        action_id=action.id,
        kind=action.kind.value,
        entity_ids=entity_ids,
        until=now + timedelta(seconds=int(revert_after)),
        restore="off" if params.get("state", "on") == "on" else "on",
        area_id=area_id,
        incident_id=incident_id,
    )


def revert_intent(running: RunningAction, moment: Moment) -> ActionIntent:
    """Switch off what an action switched on: the siren cutoff, a disarm, or
    the auto-revert running out (§6.2)."""
    return ActionIntent(
        action_id=running.action_id,
        kind=REVERT,
        moment=moment,
        placeholders={},
        params={
            "target_kind": running.kind,
            "entity_ids": running.entity_ids,
            "state": running.restore or "off",
        },
    )


# --- the batch ---------------------------------------------------------------------


# The walk test's own two moments (§6.1). They are never inhibited: §11.3
# requires a notification on start and on end, and a walk test that silenced
# the one message announcing it would be the safeguard defeating itself.
WALK_TEST_MOMENTS: frozenset[Moment] = frozenset(
    {Moment.WALK_TEST_STARTED, Moment.WALK_TEST_ENDED}
)


def inhibits(ctx: PlanContext, occurrence: Occurrence) -> bool:
    """Whether a walk test holds back the response to this occurrence (§11.3).

    Inhibition is per occurrence, not a state the executor reads, because the
    rule has exceptions and every one of them matters:

    - an ``always_on`` zone — 24h, tamper, technical, panic — is **fully
      live**. A walk test must never silence a smoke detector, and that is
      the sentence this function is written against;
    - so is everything belonging to an open incident, which during a walk
      test can only have been opened by one of those zones (part 2 decision
      3: an ordinary detection does not drive the state machine);
    - and so are the walk test's own start and end, which §11.3 requires to
      be announced.

    Everything else — the arming the walk test performs, a chime, a fault —
    is held back, because §11.3 says all actions are inhibited and means it.
    """
    if not ctx.walk_test:
        return False
    if occurrence.moment in WALK_TEST_MOMENTS:
        return False
    if occurrence.moment in TECHNICAL_MOMENTS or occurrence.incident_id is not None:
        return False
    zone = ctx.config.zone(occurrence.zone_id)
    return not (zone is not None and zone.always_on)


@dataclass(frozen=True, slots=True)
class Answer:
    """Who answers one occurrence, and under what run it is grouped.

    ``key`` is what decides that three areas arming together send one
    notification naming all three (see plan_occurrences). The simulator
    groups its trace by the same key, from this same function, so the trace
    shows one line where the house sends one message (§11.2).
    """

    profile: ResponseProfile
    source: str
    silent: bool
    incident_id: str | None
    moment: Moment
    # Held back by a walk test (§11.3). Part of the key as well as the
    # answer: two occurrences of one moment that a walk test treats
    # differently — a 24h zone and an ordinary one — are two different
    # things the house does, and one run cannot be both.
    inhibited: bool = False

    @property
    def key(self) -> tuple[str, Moment, bool, str | None, bool]:
        return (
            self.profile.id,
            self.moment,
            self.silent,
            self.incident_id,
            self.inhibited,
        )


def answer_for(ctx: PlanContext, occurrence: Occurrence) -> Answer | None:
    """The profile that answers this occurrence, or None when none does."""
    zone = ctx.config.zone(occurrence.zone_id)
    area = ctx.areas.get(occurrence.area_id or "")
    scenario_id = occurrence.scenario_id or (area.scenario_id if area else None)
    profile, source = resolve_profile(
        ctx.config,
        area_id=occurrence.area_id,
        zone_id=occurrence.zone_id,
        group_id=occurrence.group_id,
        scenario_id=scenario_id,
        moment=occurrence.moment,
    )
    if profile is None:
        return None
    return Answer(
        profile=profile,
        source=source,
        silent=bool(zone and zone.silent and occurrence.moment in ZONE_MOMENTS),
        incident_id=occurrence.incident_id,
        moment=occurrence.moment,
        inhibited=inhibits(ctx, occurrence),
    )


def plan_occurrences(
    ctx: PlanContext, occurrences: Sequence[Occurrence], run_seq: int
) -> tuple[Plan, int]:
    """One run per (profile, moment, silent), so three areas arming together
    send one notification naming all three, not three notifications."""
    plan = Plan()
    started = set(ctx.incident.actions_started if ctx.incident else ())
    batches: dict[tuple[Any, ...], list[Occurrence]] = {}
    for occurrence in occurrences:
        if (answer := answer_for(ctx, occurrence)) is not None:
            batches.setdefault(answer.key, []).append(occurrence)
    for (profile_id, moment, silent, incident_id, inhibited), group in batches.items():
        profile = ctx.config.profile(profile_id)
        assert profile is not None
        run_seq += 1
        batch = run_sequence(
            ctx,
            profile,
            moment,
            variables(ctx, group),
            area_id=next((o.area_id for o in group if o.area_id), None),
            zone_id=next((o.zone_id for o in group if o.zone_id), None),
            incident_id=incident_id,
            silent=silent,
            already_started=frozenset(started),
            run_id=f"run-{run_seq}",
            inhibited=inhibited,
        )
        started.update(batch.started)
        plan.extend(batch)
    return plan, run_seq


def resume(ctx: PlanContext, run: PendingRun) -> Plan:
    """Carry on a sequence a ``delay`` held back (part 3 decision 5)."""
    profile = ctx.config.profile(run.profile_id)
    if profile is None:
        return Plan()
    # A sequence started before the walk test and falling due inside it is
    # held back like everything else: it is the same rule read through the
    # occurrence the run was planned from.
    inhibited = inhibits(
        ctx,
        Occurrence(
            moment=run.moment,
            area_id=run.area_id,
            zone_id=run.zone_id,
            incident_id=run.incident_id,
        ),
    )
    return run_sequence(
        ctx,
        profile,
        run.moment,
        run.placeholders,
        start=run.index,
        area_id=run.area_id,
        zone_id=run.zone_id,
        incident_id=run.incident_id,
        silent=run.silent,
        already_started=frozenset(ctx.incident.actions_started if ctx.incident else ()),
        run_id=run.id,
        inhibited=inhibited,
    )


# --- chime (§6.6) ------------------------------------------------------------------


def audible_targets(chime: ChimeSettings, now: datetime, tz: tzinfo) -> tuple[str, ...]:
    """The targets not inside quiet hours right now.

    A target's own window replaces the global one (part 3 decision 8): the
    speakers all day, the phone only between nine and ten.
    """
    out: list[str] = []
    for target in chime.targets:
        start = target.quiet_start or chime.quiet_start
        end = target.quiet_end or chime.quiet_end
        if start and end and in_daily_window(now, tz, start, end):
            continue
        out.append(target.entity_id)
    return tuple(out)


def chime_suppressed(config: FoyerConfig, zone: Zone) -> bool:
    """A silent zone makes no noise in the house, the chime included."""
    return zone.silent and "chime" in config.settings.silent_suppresses


def condition_summary(
    action: ProfileAction, ctx: PlanContext
) -> tuple[Mapping[str, str], ...]:
    """Which of an action's conditions failed, so the trace can say why (§11.2).

    Data, never a sentence. "time 22:00-07:00" and "binary_sensor.x is on"
    read like English because they are English, and a backend that writes the
    words a person reads is a backend an Italian installation cannot
    translate. The panel builds the sentence from these fields, as it does for
    every other word on the page.
    """
    out: list[Mapping[str, str]] = []
    for condition in unmet(action, ctx.snapshot, ctx.now, ctx.tz):
        if isinstance(condition, TimeCondition):
            out.append(
                {"kind": "time", "after": condition.after, "before": condition.before}
            )
        elif isinstance(condition, StateCondition):
            out.append(
                {
                    "kind": "state",
                    "entity_id": condition.entity_id,
                    "operator": condition.operator.value,
                    "state": condition.state,
                }
            )
    return tuple(out)


# --- the real action test (§11.4) --------------------------------------------------

# How long a siren sounds when it is being tested: long enough to hear, short
# enough that nobody in the street reaches for a phone. The prototype's
# "sounds for 3 s", and it overrides whatever duration the action carries —
# a test that sounded for the configured three minutes is a test nobody runs
# twice.
TEST_SIREN_SECONDS = 3


def test_intent(
    ctx: PlanContext, profile: ResponseProfile, action_id: str
) -> ActionIntent | None:
    """One configured action, built to be really executed (§11.4).

    It **really executes**, which is the entire point: the failure this
    prevents is discovering during the emergency that the emergency channel
    was misconfigured. So the action's conditions are not asked — "only
    between 22:00 and 07:00" is a rule about alarms, not about whether the
    light works — and a silent zone suppresses nothing, because no zone is
    involved.

    Built here rather than in the runtime for the same reason every other
    intent is: the executor interprets nothing, and a second place that
    turned an action into an instruction would be a second place free to
    turn it into a different one.
    """
    action = next((a for a in profile.actions if a.id == action_id), None)
    if action is None or action.kind is ActionKind.DELAY:
        # A delay has nothing to test: it is the waiting itself.
        return None
    values = variables(ctx, ())
    params = dict(_params(action, values, ctx, None, Moment.ACTION_TESTED))
    if action.kind is ActionKind.SIREN:
        params["duration"] = TEST_SIREN_SECONDS
    return ActionIntent(
        action_id=action.id,
        kind=action.kind.value,
        moment=Moment.ACTION_TESTED,
        profile_id=profile.id,
        placeholders=dict(values),
        params=params,
    )


def escalation_intent(
    ctx: PlanContext,
    profile: ResponseProfile,
    action: ProfileAction,
    values: Mapping[str, str],
    *,
    moment: Moment,
    index: int,
    kind: str,
    area_id: str | None = None,
    incident_id: str | None = None,
) -> tuple[ActionIntent | None, str | None]:
    """One escalation step, built exactly as any other action (§7.2).

    Returns the intent, or None and the reason it did not run — a condition
    that is not met, or every contact inside their quiet hours. It is
    ``skip_reason`` that decides, the same function the ordinary sequence
    asks, so the trace can never explain a skip the engine did not make.
    """
    why = skip_reason(
        action,
        ctx,
        moment=moment,
        suppressed=frozenset(),
        already_started=frozenset(),
    )
    if why is not None:
        return None, why
    params = _params(action, values, ctx, area_id, moment)
    # Which step this is, for the log, the trace and the card. The executor
    # ignores it, as every transport ignores what it does not know.
    params["escalation"] = kind
    params["escalation_step"] = index
    return (
        ActionIntent(
            action_id=action.id,
            kind=action.kind.value,
            moment=moment,
            profile_id=profile.id,
            placeholders=dict(values),
            params=params,
        ),
        None,
    )


def notify_test_intent(service: str, message: str) -> ActionIntent:
    """A notification channel tested on its own, with no action behind it.

    §11.4 asks for a test button beside every action *and every contact
    channel*. This is the half Phase 3 built, and the wizard still uses it:
    "prove a notification arrives", off the browser and onto the one path
    that verifies server-side and records the attempt.
    """
    return ActionIntent(
        action_id=f"notify:{service}",
        kind=ActionKind.NOTIFY.value,
        moment=Moment.ACTION_TESTED,
        profile_id=None,
        params={"service": service, "message": message},
    )


def contact_test_intent(
    contact: Contact, channel: ContactChannel, message: str
) -> ActionIntent:
    """The other half of §11.4: the test button beside a contact's channel.

    It is the same call the real thing makes — the same service, the same
    target, the same extra data the transport needs — so what is proved is
    the channel, not a simplified version of it. It goes through
    ``foyer.test_action`` like the button beside an action, needs the same
    permission and the same code, and leaves the same row marked as a test.
    """
    return ActionIntent(
        action_id=f"contact:{contact.id}:{channel.id}",
        kind=ActionKind.NOTIFY.value,
        moment=Moment.ACTION_TESTED,
        profile_id=None,
        params={
            "message": message,
            "recipients": (
                {
                    "contact_id": contact.id,
                    "contact_name": contact.name,
                    "channel_id": channel.id,
                    "kind": channel.kind.value,
                    "service": channel.service,
                    "target": channel.target,
                    "data": dict(channel.data),
                    # No button: there is nothing to acknowledge, and a test
                    # that could stop a real escalation would be a way of
                    # silencing an alarm from the configuration page.
                    "ack": False,
                    "user_id": contact.linked_user_id,
                },
            ),
        },
    )


def without(
    running: Sequence[RunningAction], stopped: Sequence[RunningAction]
) -> tuple[RunningAction, ...]:
    ids = {(r.action_id, r.entity_ids) for r in stopped}
    return tuple(r for r in running if (r.action_id, r.entity_ids) not in ids)


def renumber(run: PendingRun, run_seq: int) -> tuple[PendingRun, int]:
    run_seq += 1
    return replace(run, id=f"run-{run_seq}"), run_seq
