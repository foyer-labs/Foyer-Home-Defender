"""Escalation: reaching people until one of them answers (SPEC §7.2). Pure.

An escalation step **is** an action — a notification at an offset from the
start (part 1 decision 1). That is the whole of the model: the same editor,
the same conditions, the same contacts, the same executor and the same line
in the trace as any other notification. What makes it a step is
``ProfileAction.escalation_offset``, and the one place that keeps a step out
of the ordinary sequence is ``response.sequence``.

Two things escalate and they never merge (part 1 decision 2): an intrusion
incident, whose policy is the one belonging to the highest-severity
contributing profile (§5.6), and the technical channel, which §5.5 gives "its
own escalation, independent of any intrusion incident". Nothing else does:
there is no acknowledgement for an ``armed`` or a ``zone_fault``, so there
would be nothing to stop.

Nothing here executes anything or reads a clock it was not given (INV-1).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from .models import (
    Escalation,
    EscalationKind,
    FoyerConfig,
    Incident,
    Moment,
    ProfileAction,
    ResponseProfile,
    ScheduledStep,
)
from .validation import notify_contacts

# Which moment carries each escalation's steps. An escalation is not a third
# kind of object with its own editor: it is the profile's answer to the
# moment that started it, spread over time.
STEP_MOMENT: dict[EscalationKind, Moment] = {
    EscalationKind.INCIDENT: Moment.TRIGGERED,
    EscalationKind.TECHNICAL: Moment.TECHNICAL_RAISED,
}


def steps(profile: ResponseProfile, moment: Moment) -> tuple[ProfileAction, ...]:
    """The profile's escalation steps for this moment, earliest first.

    Sorted by offset, and by the user's own order where two share one: an
    escalation is read as a list of times, so two steps at +120 s stay in the
    order the page shows them.
    """
    numbered = [
        (a.escalation_offset or 0, index, a)
        for index, a in enumerate(profile.actions)
        if a.enabled and a.is_step and moment in a.moments
    ]
    return tuple(action for _, _, action in sorted(numbered, key=lambda t: t[:2]))


def has_steps(profile: ResponseProfile | None, moment: Moment) -> bool:
    return profile is not None and bool(steps(profile, moment))


def policy_for(config: FoyerConfig, incident: Incident) -> ResponseProfile | None:
    """The escalation an incident adopts: the highest-severity contributor's.

    §5.6 says this in one sentence and §6.5 says the ``severity`` integer
    exists for nothing else. Each contributor recorded the profile it
    answered with when it joined, so the choice is made from what was true
    then, not from a configuration that may have been edited since.

    Only contributors whose profile actually **defines** an escalation are
    considered. Read at its most literal, "the policy of the highest-severity
    contributing profile" would mean that a louder zone joining a running
    incident, with no steps of its own, silences the escalation already on
    its way to the neighbour — a louder alarm reaching fewer people. The
    sentence exists to choose between policies, so it chooses between the
    policies there are.

    Ties go to the contributor that joined first: the alarm that opened the
    incident is the one the household is being told about.
    """
    best: tuple[int, int, str] | None = None
    for order, contributor in enumerate(incident.contributors):
        profile = config.profile(contributor.profile_id)
        if profile is None or not steps(profile, Moment.TRIGGERED):
            continue
        key = (-(contributor.severity or 0), order, profile.id)
        if best is None or key < best:
            best = key
    return config.profile(best[2]) if best is not None else None


def start(
    kind: EscalationKind,
    profile: ResponseProfile,
    now: datetime,
    *,
    reference: str | None = None,
) -> Escalation:
    return Escalation(
        kind=kind,
        profile_id=profile.id,
        moment=STEP_MOMENT[kind],
        started_at=now,
        severity=profile.severity,
        reference=reference,
    )


def pending(
    escalation: Escalation, profile: ResponseProfile
) -> tuple[ProfileAction, ...]:
    """The steps this escalation has not reached yet."""
    done = set(escalation.done)
    return tuple(a for a in steps(profile, escalation.moment) if a.id not in done)


def due_at(escalation: Escalation, action: ProfileAction) -> datetime:
    return escalation.started_at + timedelta(seconds=action.escalation_offset or 0)


def due(
    escalation: Escalation, profile: ResponseProfile, now: datetime
) -> tuple[ProfileAction, ...]:
    """The steps whose time has come. Several at once is normal: a policy
    adopted late (§5.6) finds its early steps already overdue and sends them
    rather than starting the clock again."""
    return tuple(
        a for a in pending(escalation, profile) if due_at(escalation, a) <= now
    )


def next_due(
    escalation: Escalation, profile: ResponseProfile, now: datetime
) -> datetime | None:
    """When the scheduler must wake for this escalation, or None."""
    times = [
        due_at(escalation, a)
        for a in pending(escalation, profile)
        if due_at(escalation, a) > now
    ]
    return min(times, default=None)


def wakeups(
    escalations: Sequence[Escalation], config: FoyerConfig, now: datetime
) -> list[datetime]:
    out: list[datetime] = []
    for escalation in escalations:
        profile = config.profile(escalation.profile_id)
        if profile is not None and (at := next_due(escalation, profile, now)):
            out.append(at)
    return out


def index_of(escalation: Escalation, profile: ResponseProfile, action_id: str) -> int:
    """Which step this is, counted from zero, as §7.2 numbers them."""
    ordered = steps(profile, escalation.moment)
    return next((i for i, a in enumerate(ordered) if a.id == action_id), 0)


def scheduled(
    escalation: Escalation, profile: ResponseProfile, now: datetime
) -> tuple[ScheduledStep, ...]:
    """The steps still to come, for the panel and the simulator's trace.

    Read off the state the engine produced and never computed a second time
    somewhere else (INV-1): the "⏱ escalation step 1 at +60s → Luca (SMS)"
    of §11.2 is this, rendered.
    """
    out: list[ScheduledStep] = []
    for action in pending(escalation, profile):
        at = due_at(escalation, action)
        if at <= now:
            continue
        refs = notify_contacts(action)
        out.append(
            ScheduledStep(
                kind=escalation.kind,
                profile_id=profile.id,
                action_id=action.id,
                index=index_of(escalation, profile, action.id),
                offset=action.escalation_offset or 0,
                due=at,
                contact_ids=tuple(r["contact_id"] for r in refs),
                channel_ids=tuple(r["channel_id"] or "" for r in refs),
            )
        )
    return tuple(sorted(out, key=lambda s: (s.due, s.index)))


def exhausted(escalation: Escalation, profile: ResponseProfile | None) -> bool:
    """Every step has gone out and nobody has acknowledged (§7.2).

    An escalation whose profile has lost its steps is exhausted too: there is
    nothing left to reach anybody with, and saying so is better than a policy
    that sits open for ever waiting for a step that no longer exists.
    """
    return profile is None or not pending(escalation, profile)
