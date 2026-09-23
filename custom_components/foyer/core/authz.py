"""Who may ask for what, and when a code is needed (SPEC §8.2, §8.3, §8.4).

Pure, like everything in ``core/`` (INV-1): it is given the configuration, an
Actor and the clock, and it answers with a Reason or with nothing. It never
sees a code — ``security/`` verifies that and hands over a CodeResult — and it
performs no I/O, so the simulator and the tests can ask it the same questions
the runtime does.

Three checks, in this order, because the order is itself a decision:

1. **the lockout**, first, so a channel already shut is answered without
   another attempt being counted against it;
2. **the code**, which is a bad code (an attempt, counted) or a missing one
   (not an attempt: nobody guessed anything);
3. **the person**: enabled, inside their validity window, holding the
   permission, and allowed on this area or this scenario.

A refusal never says more than it must. "Bad code" is the same answer whoever
typed it, and it never reveals whose code came close.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta

from .models import (
    IDENTIFYING_CHANNELS,
    LOCKOUT_STRIKE_RESET,
    MAX_LOCKOUT_BACKOFF,
    Actor,
    Area,
    CodeResult,
    FoyerConfig,
    Lockout,
    Operation,
    Permission,
    Reason,
    Scenario,
    User,
)

# Which permission each operation needs (§8.3). Acknowledging is deliberately
# absent: §8.3 lists no permission for it, and whoever is woken by an alarm at
# four in the morning is allowed to say they have seen it.
PERMISSION_OF: dict[Operation, Permission] = {
    Operation.ARM: Permission.ARM,
    Operation.DISARM: Permission.DISARM,
    Operation.FORCE_ARM: Permission.FORCE_ARM,
    Operation.CHANGE_SCENARIO: Permission.CHANGE_SCENARIO,
    Operation.BYPASS_ZONE: Permission.BYPASS_ZONE,
    Operation.EDIT_CONFIG: Permission.EDIT_CONFIG,
    Operation.WALK_TEST: Permission.WALK_TEST,
    Operation.TEST_ACTION: Permission.TEST_ACTIONS,
}

# What a new user is offered by default. Not manage_users and not edit_config:
# handing out codes and rewriting the configuration are the two that have to
# be given deliberately.
DEFAULT_PERMISSIONS: frozenset[str] = frozenset(
    {
        Permission.ARM,
        Permission.DISARM,
        Permission.BYPASS_ZONE,
        Permission.CHANGE_SCENARIO,
        Permission.VIEW_LOG,
    }
)


def enforced(config: FoyerConfig, now: datetime) -> bool:
    """Is the code policy in force at all? (decision 78)

    It is not, while no enabled user holds a usable code. Nothing could be
    verified then, so enforcing the policy would not protect the house — it
    would only make it impossible to disarm, which is how an alarm teaches its
    owner to remove it. The panel and the card say so plainly meanwhile.
    """
    return any(u.usable(now) for u in config.users)


def code_required(
    config: FoyerConfig,
    operation: Operation,
    *,
    now: datetime,
    areas: tuple[Area, ...] = (),
    scenario: Scenario | None = None,
    user: User | None = None,
    identified: bool = False,
    channel: str = "api",
) -> bool:
    """Resolve §8.2 for one request.

    global default → the explicit settings of the areas and the scenario →
    the per-user exemption, which applies only on a channel that identifies
    the user by itself. Where an area and a scenario disagree, the strictest
    explicit setting wins (decision 80): arming a scenario touches several
    areas at once, and an area its owner deliberately protected must not be
    opened because a permissive scenario happens to include it.
    """
    if not enforced(config, now):
        return False

    explicit = [
        setting
        for setting in (
            *(_area_setting(area, operation) for area in areas),
            _scenario_setting(scenario, operation),
        )
        if setting is not None
    ]
    required = (
        any(explicit) if explicit else config.code_policy.requires_code(operation)
    )

    # The exemption is checked against the channel as well, so a keypad
    # claiming to have identified somebody cannot buy its way out of §8.2.
    exempt = user is not None and user.code_exempt_when_identified
    if required and exempt and identified and channel in IDENTIFYING_CHANNELS:
        return False
    return required


def _area_setting(area: Area | None, operation: Operation) -> bool | None:
    if area is None:
        return None
    if operation in (Operation.ARM, Operation.FORCE_ARM, Operation.CHANGE_SCENARIO):
        return area.require_code_to_arm
    if operation is Operation.DISARM:
        return area.require_code_to_disarm
    return None


def _scenario_setting(scenario: Scenario | None, operation: Operation) -> bool | None:
    if scenario is None:
        return None
    if operation in (Operation.ARM, Operation.FORCE_ARM, Operation.CHANGE_SCENARIO):
        return scenario.require_code_to_arm
    if operation is Operation.DISARM:
        return scenario.require_code_to_disarm
    return None


def check_user(
    config: FoyerConfig,
    actor: Actor,
    operation: Operation,
    now: datetime,
    *,
    area_ids: tuple[str, ...] = (),
    scenario: Scenario | None = None,
) -> Reason | None:
    """Is this person allowed to ask for this, here, now? (§8.1, §8.3, §4.6)

    Nobody identified is not an error in itself: it is what every request
    looks like while the policy is not in force, and what a codeless arming
    looks like afterwards. What that request may do is decided by the policy,
    not here.
    """
    user = config.user(actor.user_id)
    if user is None:
        return None
    if not user.enabled or not user.in_window(now):
        return Reason.USER_NOT_VALID
    permission = PERMISSION_OF.get(operation)
    if permission is not None and not user.may(permission):
        return Reason.NOT_PERMITTED
    if user.allowed_area_ids is not None and any(
        area_id not in user.allowed_area_ids for area_id in area_ids
    ):
        return Reason.AREA_NOT_ALLOWED
    if scenario is not None:
        allowed_here = user.allowed_scenario_ids
        if allowed_here is not None and scenario.id not in allowed_here:
            return Reason.SCENARIO_NOT_ALLOWED
        listed = scenario.allowed_user_ids
        if listed is not None and user.id not in listed:
            return Reason.SCENARIO_NOT_ALLOWED
    return None


def may_configure(
    config: FoyerConfig,
    actor: Actor,
    operation: Operation,
    permission: Permission,
    now: datetime,
    *,
    need_code: bool = True,
    open_while_inert: bool = False,
) -> Reason | None:
    """The gate in front of the configuration and the log (§8.2, §8.3).

    One function for the panel's commands and for the services that read or
    write the configuration, which never reach ``decide()``: two copies of
    this had drifted apart once already.

    * A wrong code is refused before anything else.
    * The person is the one a code or a linked account established. A
      ``user_id`` the request merely claimed grants nothing here (decision
      102): a permission comes from a code or a linked account, never from an
      id somebody typed.
    * A Home Assistant **administrator** is never refused for want of a
      permission. INV-6 already says they can read .storage and disable the
      integration, so refusing them buys nothing — and would lock out the
      owner who linked their own account and left ``manage_users`` unticked.
      The code still applies to them, linked or not (decision 101): it is
      what protects the configuration from their unlocked tablet.
    * Nobody named and no administrator: refused, except while the policy is
      inert (decision 78) on a path that is ``open_while_inert`` — the
      services, which an automation calls before any code exists.
    """
    if actor.code is CodeResult.INVALID:
        return Reason.BAD_CODE
    user = None if actor.claimed else config.user(actor.user_id)
    if user is None:
        if not actor.is_admin:
            if open_while_inert and not enforced(config, now):
                return None
            return Reason.NOT_PERMITTED
    else:
        if not user.enabled or not user.in_window(now):
            return Reason.USER_NOT_VALID
        if not user.may(permission) and not actor.is_admin:
            return Reason.NOT_PERMITTED
    if (
        need_code
        and code_required(
            config,
            operation,
            now=now,
            user=user,
            identified=actor.identified,
            channel=actor.channel,
        )
        and not actor.code_verified
    ):
        return Reason.CODE_REQUIRED
    return None


# --- lockout (§8.4) ------------------------------------------------------------


def lockout_key(actor: Actor) -> str:
    """One counter per channel and device: the garden keypad is not the hall's.

    A request to the device endpoint without a valid token has no device to
    count against, so it counts against its source address (§9.2.1): a
    token-guessing loop is a tamper signal like a keypad's, and one address
    guessing must not lock every keypad in the house.
    """
    if actor.device_id is None and actor.address:
        return f"http:{actor.address}"
    if actor.device_id is None and actor.account:
        # One counter per Home Assistant account on the panel and the
        # services: a read-only account typing wrong codes must not lock out
        # everybody else in the house (second review, decision 1).
        return f"{actor.channel}:@{actor.account}"
    return f"{actor.channel}:{actor.device_id or ''}"


def address_locked_until(
    lockouts: Mapping[str, Lockout], address: str, now: datetime
) -> datetime | None:
    """When this source address may try a token again, or None (§9.2.1)."""
    lock = lockouts.get(f"http:{address}")
    if lock is None or lock.until is None or lock.until <= now:
        return None
    return lock.until


def stale(lock: Lockout, now: datetime) -> bool:
    """A counter with nothing left to count: no lockout running, no failure
    inside any window, and no strike still able to lengthen the next one.

    Dropped rather than kept, because the counters of the device endpoint are
    keyed by address and a house reachable from outside meets many of them.
    """
    if lock.until is not None and lock.until > now:
        return False
    recent = max(lock.failures, default=None)
    last = max((t for t in (recent, lock.locked_at) if t is not None), default=None)
    return last is None or (now - last).total_seconds() > LOCKOUT_STRIKE_RESET


def locked_until(
    lockouts: Mapping[str, Lockout], actor: Actor, now: datetime
) -> datetime | None:
    """When this channel reopens, or None while it is open.

    The Home Assistant admin path is never locked (§8.4): an administrator who
    could not get back in would simply disable the integration, and an alarm
    that teaches that is worse than one which counts the attempt and says so.
    """
    if actor.is_admin:
        return None
    lock = lockouts.get(lockout_key(actor))
    if lock is None or lock.until is None or lock.until <= now:
        return None
    return lock.until


def register_failure(
    lock: Lockout | None,
    now: datetime,
    *,
    failures: int,
    window: int,
    duration: int,
) -> tuple[Lockout, bool]:
    """Count one wrong code, and say whether it has just shut the channel.

    Only failures inside the window count, so five wrong digits spread over a
    month are not a lockout. Each further lockout doubles, up to a cap: a
    keypad under attack must not end up shut for a fortnight while the person
    who lives there stands in the rain.
    """
    lock = lock or Lockout()
    recent = tuple(
        at for at in (*lock.failures, now) if (now - at).total_seconds() < window
    )
    strikes = lock.strikes
    if (
        strikes
        and lock.locked_at is not None
        and (now - lock.locked_at).total_seconds() > LOCKOUT_STRIKE_RESET
    ):
        strikes = 0
    if len(recent) < failures:
        return Lockout(recent, lock.until, strikes, lock.locked_at), False
    seconds = min(duration * (2**strikes), MAX_LOCKOUT_BACKOFF)
    return Lockout((), now + timedelta(seconds=seconds), strikes + 1, now), True


def clear_failures(lock: Lockout | None) -> Lockout | None:
    """A correct code ends the run of failures. It does not open a lockout."""
    if lock is None or lock.until is None:
        return None
    return Lockout((), lock.until, lock.strikes, lock.locked_at)
