"""What the third full review found in runtime/system.py, pinned down.

Three ways the order of things could go wrong inside one Home Assistant: a
warning about a broken channel reporting its own send straight back, a
decision started from inside another landing in the log and the executor
before its cause, and the system being replaced by a reload still deciding
while its last save was writing. And what the review of that fix found: a
warning's delayed step or auto-revert driving the next, the last-event
sensor a decision behind, and nothing pinning down a call that leaves the
queue.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace

from homeassistant.core import Event as HassEvent, callback
from homeassistant.exceptions import HomeAssistantError
import pytest

from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.models import (
    ActionIntent,
    ActionKind,
    AreaState,
    HealthReport,
    Moment,
    Reason,
    SetAutoArming,
    Tick,
)
from custom_components.foyer.runtime import (
    executor as executor_module,
    system as system_module,
)
from custom_components.foyer.runtime.executor import ActionResult
from custom_components.foyer.store.log_store import EVENT_FOYER

from .conftest import ZONE
from .test_integration import _advance, _call
from .test_part2 import _ws
from .test_part7 import _break_in, _notify_recorder
from .test_part9 import _save_health

# A real send: a notification about the house, whose outcome is news about
# the channel it went over.
PROBE = ActionIntent(
    action_id="probe",
    kind=ActionKind.NOTIFY.value,
    moment=Moment.TRIGGERED,
)
# A send about a channel itself: the warning that one broke.
WARNING = ActionIntent(
    action_id="warning",
    kind=ActionKind.NOTIFY.value,
    moment=Moment.NOTIFICATION_CHANNEL_DOWN,
)
# An action that sends nothing: a siren going back, a chime.
REVERT = ActionIntent(
    action_id="siren",
    kind=ActionKind.SWITCH.value,
    moment=Moment.SIREN_CUTOFF,
)


def _system(hass):
    return hass.data[DOMAIN]


def _reports(monkeypatch) -> list[dict[str, bool]]:
    """Every report of sends the engine is handed, in order."""
    reports: list[dict[str, bool]] = []
    real = system_module.decide

    def decide(snapshot, event, config, now):
        if isinstance(event, HealthReport) and event.channel_sends:
            reports.append(dict(event.channel_sends))
        return real(snapshot, event, config, now)

    monkeypatch.setattr(system_module, "decide", decide)
    return reports


def _everything_sends(monkeypatch, system, outcome) -> tuple[list, list]:
    """The worst case for the guard, which the engine would never stop.

    Every decision on a Tick or on a report has a notification to send, and
    every send comes back with something to say about a channel: fed back
    without a guard, each report makes the next one, for ever. ``outcome``
    says what the n-th send did.
    """
    reports = _reports(monkeypatch)
    counted = system_module.decide

    def decide(snapshot, event, config, now):
        decision = counted(snapshot, event, config, now)
        if isinstance(event, Tick | HealthReport):
            decision = replace(decision, actions=(*decision.actions, PROBE))
        return decision

    monkeypatch.setattr(system_module, "decide", decide)
    runs: list = []

    async def run(decision):
        runs.append(decision)
        # A transport answers later, never at once: this is what made the
        # old flag useless, because it was down again by the time it did.
        await asyncio.sleep(0)
        # One result per intent, in the Decision's order, as the executor
        # answers.
        return [
            ActionResult(
                intent.action_id,
                intent.kind,
                True,
                sends=outcome(len(runs)) if intent is PROBE else {},
            )
            for intent in decision.actions
        ]

    monkeypatch.setattr(system._executor, "async_run", run)
    return reports, runs


def _answering(monkeypatch, system, actions, sends) -> list[dict[str, bool]]:
    """Every Tick decides ``actions``, and each of them did what ``sends``
    says it did; every report of sends the engine is handed is returned."""
    reports = _reports(monkeypatch)
    counted = system_module.decide

    def decide(snapshot, event, config, now):
        decision = counted(snapshot, event, config, now)
        if isinstance(event, Tick):
            decision = replace(decision, actions=tuple(actions))
        return decision

    monkeypatch.setattr(system_module, "decide", decide)

    async def run(decision):
        await asyncio.sleep(0)
        return [
            ActionResult(
                intent.action_id,
                intent.kind,
                True,
                sends=sends.get(intent.action_id, {}),
            )
            for intent in decision.actions
        ]

    monkeypatch.setattr(system._executor, "async_run", run)
    return reports


# --- (a) a warning's own send ---------------------------------------------------------


async def test_a_report_loop_ends_at_one_level_by_the_guard_not_the_engine(
    hass, loaded, monkeypatch
):
    system = _system(hass)
    # Bounded only so that a broken guard fails the test instead of hanging it.
    reports, runs = _everything_sends(
        monkeypatch, system, lambda n: {f"c:{n}": False} if n <= 10 else {}
    )

    await system.async_handle(Tick())
    await hass.async_block_till_done()

    assert reports == [{"c:1": False}]
    assert len(runs) == 2
    # Held, not lost: it is evidence about a real send.
    assert system._held_sends == [{"c:2": False}]


async def test_a_held_send_travels_with_the_next_real_one_and_counts_on_its_own(
    hass, loaded, monkeypatch
):
    system = _system(hass)
    outcomes = {1: {"c:push": False}, 2: {"c:sms": False}, 3: {"c:sms": False}}
    reports, _runs = _everything_sends(
        monkeypatch, system, lambda n: outcomes.get(n, {})
    )
    await system.async_handle(Tick())
    await hass.async_block_till_done()
    assert system._held_sends == [{"c:sms": False}]

    await system.async_handle(Tick())
    await hass.async_block_till_done()

    # The next real send reports the held one too, older first — and as a
    # report of its own, because two failures over one channel are two
    # failures, and merged the engine would have counted one.
    assert reports == [{"c:push": False}, {"c:sms": False}, {"c:sms": False}]
    assert system._held_sends == []


def test_sends_over_different_channels_travel_together_and_one_channel_twice_does_not():
    assert system_module._send_reports([{"a": False}, {"b": True}]) == [
        {"a": False, "b": True}
    ]
    assert system_module._send_reports([{"a": False}, {}, {"a": False, "b": True}]) == [
        {"a": False},
        {"a": False, "b": True},
    ]
    assert system_module._send_reports([]) == []


async def test_the_sweep_carries_what_was_held_and_holds_what_its_own_decision_sent(
    hass, loaded, monkeypatch
):
    system = _system(hass)
    reports, runs = _everything_sends(
        monkeypatch, system, lambda n: {"c:sms": True} if n == 1 else {}
    )
    system._held_sends = [{"c:push": False}]

    await system._async_channel_sweep()
    await hass.async_block_till_done()

    assert reports == [{"c:push": False}]
    assert len(runs) == 1
    # A sweep that carries sends is a report of sends: at most one step of
    # feedback per sweep.
    assert system._held_sends == [{"c:sms": True}]


async def test_actions_that_send_nothing_leave_what_is_held_where_it_is(
    hass, loaded, monkeypatch
):
    """A siren going back, a chime, a switch: no news about any channel.
    Carried by them, a warning's failure went straight back on the warning's
    own auto-revert, which is the loop the hold is there to stop."""
    system = _system(hass)
    reports = _answering(monkeypatch, system, [REVERT], {})
    system._held_sends = [{"c:sms": False}]

    await system.async_handle(Tick())
    await hass.async_block_till_done()

    assert reports == []
    assert system._held_sends == [{"c:sms": False}]


async def test_a_real_send_is_reported_and_the_warning_beside_it_is_held(
    hass, loaded, monkeypatch
):
    """Held by what the action answers, not only by where the decision came
    from: the warning's send in a Tick is held like one in a report."""
    system = _system(hass)
    reports = _answering(
        monkeypatch,
        system,
        [PROBE, WARNING],
        {PROBE.action_id: {"c:push": False}, WARNING.action_id: {"c:sms": True}},
    )
    system._held_sends = [{"c:old": False}]

    await system.async_handle(Tick())
    await hass.async_block_till_done()

    # The real send carries what was held before it; the warning's own send
    # waits for the next one.
    assert reports == [{"c:old": False, "c:push": False}]
    assert system._held_sends == [{"c:sms": True}]


async def _address_book_with_a_warning(
    hass, client, *, repeat_after: int | None = None
) -> str:
    """Luca, on a push that will fail and an SMS that works, and one profile:
    the push on a break-in, and Luca, by whatever still works, when a channel
    breaks — and, with ``repeat_after``, again that many seconds later."""
    contact = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "name": "Luca",
                "channels": [
                    {"id": "push", "kind": "push", "service": "notify.mobile_app_luca"},
                    {"id": "sms", "kind": "sms", "service": "notify.sms_gateway"},
                ],
            },
        },
    )
    assert contact["success"], contact
    await hass.async_block_till_done()
    contact_id = _system(hass).config.contacts[0].id
    profile = _system(hass).config.profiles[0]
    again = (
        []
        if repeat_after is None
        else [
            {
                "id": "wait",
                "kind": "delay",
                "moments": ["notification_channel_down"],
                "params": {"seconds": repeat_after},
            },
            {
                "id": "again",
                "kind": "notify",
                "moments": ["notification_channel_down"],
                "params": {
                    "message": "Still down",
                    "contacts": [{"contact_id": contact_id}],
                },
            },
        ]
    )
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "profile",
            "item": {
                "id": profile.id,
                "name": profile.name,
                "severity": profile.severity,
                "actions": [
                    {
                        "id": "alarm",
                        "kind": "notify",
                        "moments": ["triggered"],
                        "params": {
                            "message": "Alarm at home",
                            "contacts": [
                                {"contact_id": contact_id, "channel_id": "push"}
                            ],
                        },
                    },
                    {
                        "id": "warning",
                        "kind": "notify",
                        "moments": ["notification_channel_down"],
                        "params": {
                            "message": "A channel is down",
                            "contacts": [{"contact_id": contact_id}],
                        },
                    },
                    *again,
                ],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    return contact_id


async def test_the_warning_that_a_channel_broke_does_not_report_its_own_send(
    hass, hass_ws_client, loaded, freezer, monkeypatch
):
    monkeypatch.setattr(executor_module, "NOTIFY_RETRY_SECONDS", 0)

    async def refuse(call):
        raise HomeAssistantError("the provider refused it")

    hass.services.async_register("notify", "mobile_app_luca", refuse)
    sms = await _notify_recorder(hass, "sms_gateway")
    client = await hass_ws_client(hass)
    await _save_health(hass, client, channel_failures=1)
    contact_id = await _address_book_with_a_warning(hass, client)
    push, text = f"{contact_id}:push", f"{contact_id}:sms"
    reports = _reports(monkeypatch)
    system = _system(hass)

    await _break_in(hass, freezer)
    await hass.async_block_till_done()

    assert [c["message"] for c in sms] == ["A channel is down"]
    assert reports == [{push: False}]
    assert system._held_sends == [{text: True}]

    # The next sweep counts it: the SMS that carried the warning worked.
    await system._async_channel_sweep()
    await hass.async_block_till_done()
    assert reports[-1] == {text: True}
    assert system._held_sends == []
    assert system.state.health.channel(text).last_ok is not None


async def test_a_warning_step_a_delay_held_back_is_held_when_it_resumes(
    hass, hass_ws_client, loaded, freezer, monkeypatch
):
    """The rest of the warning runs in a Tick, which is not a report of sends.
    Reported at once, a warning profile with a delay drove its own next step,
    one channel after another at the pace of the delay."""
    monkeypatch.setattr(executor_module, "NOTIFY_RETRY_SECONDS", 0)

    async def refuse(call):
        raise HomeAssistantError("the provider refused it")

    hass.services.async_register("notify", "mobile_app_luca", refuse)
    sms = await _notify_recorder(hass, "sms_gateway")
    client = await hass_ws_client(hass)
    await _save_health(hass, client, channel_failures=1)
    contact_id = await _address_book_with_a_warning(hass, client, repeat_after=60)
    push, text = f"{contact_id}:push", f"{contact_id}:sms"
    reports = _reports(monkeypatch)
    system = _system(hass)

    await _break_in(hass, freezer)
    await hass.async_block_till_done()
    await _advance(hass, freezer, 60)

    assert [c["message"] for c in sms] == ["A channel is down", "Still down"]
    assert reports == [{push: False}]
    assert system._held_sends == [{text: True}, {text: True}]


async def test_a_second_channel_failing_twice_is_counted_twice(
    hass, hass_ws_client, loaded
):
    """Two warnings over the SMS, both failed, held until the sweep: merged,
    the engine would have counted one failure and kept calling it working."""

    async def accept(call):
        return None

    hass.services.async_register("notify", "mobile_app_luca", accept)
    hass.services.async_register("notify", "sms_gateway", accept)
    client = await hass_ws_client(hass)
    contact_id = await _address_book_with_a_warning(hass, client)
    text = f"{contact_id}:sms"
    system = _system(hass)
    system._held_sends = [{text: False}, {text: False}]

    await system._async_channel_sweep()
    await hass.async_block_till_done()

    channel = system.state.health.channel(text)
    assert channel.failures == 2
    assert channel.fault is not None


# --- (b) a decision started inside another --------------------------------------------


async def test_a_decision_started_inside_another_is_recorded_and_run_after_it(
    hass, loaded, freezer, monkeypatch
):
    system = _system(hass)
    await _call(hass, "alarm_arm_away")
    await hass.async_block_till_done()
    real = system_module.decide

    def decide(snapshot, event, config, now):
        decision = real(snapshot, event, config, now)
        # Something to run for every decision that has something to say,
        # so the order of the two dispatches can be seen.
        if decision.occurrences:
            decision = replace(decision, actions=(PROBE,))
        return decision

    monkeypatch.setattr(system_module, "decide", decide)
    batches: list[tuple[str, ...]] = []
    record = system.async_record

    def spy(rows):
        batches.append(tuple(row.event_type for row in rows))
        record(rows)

    monkeypatch.setattr(system, "async_record", spy)
    executed: list[tuple[str, ...]] = []

    async def execute(decision, **_kwargs):
        executed.append(tuple(o.moment.value for o in decision.occurrences))

    monkeypatch.setattr(system, "_async_execute", execute)
    inner: list[asyncio.Task] = []

    def listener() -> None:
        # What the watcher does when a zone, a rule or a condition watches one
        # of Foyer's own entities: an eager task, started inside _notify().
        armed = any(a.state is AreaState.ARMED for a in system.state.areas.values())
        if inner or not armed:
            return
        inner.append(
            hass.async_create_task(
                system.async_handle(
                    SetAutoArming(enabled=not system.state.auto_arming)
                ),
                eager_start=True,
            )
        )

    remove = system.async_add_listener(listener)
    try:
        # The exit delay runs out: the house is armed, and says so.
        await _advance(hass, freezer, 30)
    finally:
        remove()

    assert inner and inner[0].done() and inner[0].result().accepted
    # Cause before consequence, in the log and in front of the executor.
    recorded = [batch for batch in batches if batch]
    assert "auto_arming_switched" not in recorded[0], recorded
    assert "auto_arming_switched" in recorded[1], recorded
    assert len(executed) == 2
    assert "auto_arming_switched" not in executed[0], executed
    assert "auto_arming_switched" in executed[1], executed


async def test_an_action_that_finishes_at_once_is_still_filed_after_its_cause(
    hass, loaded, monkeypatch
):
    """A persistent notification never waits for anything, and the executor's
    task starts eagerly: its row reached the log before the decision's."""
    system = _system(hass)
    real = system_module.decide

    def decide(snapshot, event, config, now):
        decision = real(snapshot, event, config, now)
        return replace(decision, actions=(PROBE,)) if decision.occurrences else decision

    monkeypatch.setattr(system_module, "decide", decide)

    async def run(decision):
        return [ActionResult(PROBE.action_id, PROBE.kind, True)]

    monkeypatch.setattr(system._executor, "async_run", run)
    batches: list[tuple[str, ...]] = []
    record = system.async_record

    def spy(rows):
        batches.append(tuple(row.event_type for row in rows))
        record(rows)

    monkeypatch.setattr(system, "async_record", spy)

    await system.async_handle(SetAutoArming(enabled=not system.state.auto_arming))
    await hass.async_block_till_done()

    recorded = [batch for batch in batches if batch]
    assert recorded[0] == ("auto_arming_switched",), recorded
    assert len(recorded) == 2, recorded


async def test_foyer_feeding_its_own_entity_back_is_a_queue_not_a_recursion(
    hass, loaded, monkeypatch
):
    """Two re-entries per update, fifty in all: each is decided on its own,
    never inside another, and in the order it arrived."""
    system = _system(hass)
    real = system_module.decide
    decided: list[str] = []
    in_notify = False
    nested: list[str] = []

    def decide(snapshot, event, config, now):
        if isinstance(event, HealthReport) and event.watchdog_error:
            decided.append(event.watchdog_error)
            if in_notify:
                nested.append(event.watchdog_error)
        return real(snapshot, event, config, now)

    monkeypatch.setattr(system_module, "decide", decide)
    notify = system._notify

    def watched_notify() -> None:
        nonlocal in_notify
        in_notify = True
        try:
            notify()
        finally:
            in_notify = False

    monkeypatch.setattr(system, "_notify", watched_notify)
    tasks: list[asyncio.Task] = []

    def listener() -> None:
        for _ in range(2):
            if len(tasks) >= 50:
                return
            # A report that says nothing: a harmless event with a name.
            event = HealthReport(watchdog_error=str(len(tasks)))
            tasks.append(
                hass.async_create_task(system.async_handle(event), eager_start=True)
            )

    remove = system.async_add_listener(listener)
    try:
        await system.async_handle(Tick())
        await hass.async_block_till_done()
    finally:
        remove()

    assert len(tasks) == 50
    assert all(task.done() and task.exception() is None for task in tasks)
    assert nested == []
    assert decided == [str(n) for n in range(50)]
    assert system._deciding is False
    assert not system._queue


@pytest.mark.parametrize("how", ["handed", "queued", "timed_out"])
async def test_a_waiting_call_that_goes_away_never_stops_the_next(hass, loaded, how):
    """An automation restarted, a script stopped, a timeout run out: whatever
    becomes of a call waiting for its turn, the one behind it decides and the
    turn is free again afterwards. Left held, every later zone change, disarm
    and wake-up would wait for ever — an alarm silently dead."""
    system = _system(hass)
    # Another decision holds the turn: both calls queue behind it.
    system._deciding = True

    async def first():
        if how == "timed_out":
            async with asyncio.timeout(0.01):
                return await system.async_handle(Tick())
        return await system.async_handle(Tick())

    a = hass.async_create_task(first())
    b = hass.async_create_task(system.async_handle(Tick()))
    await asyncio.sleep(0)
    assert len(system._queue) == 2
    if how == "handed":
        # Handed the turn, and cancelled before it could take it.
        system._next_turn()
        a.cancel()
    elif how == "queued":
        a.cancel()
        await asyncio.sleep(0)
        system._next_turn()
    else:
        with pytest.raises(TimeoutError):
            await a
        system._next_turn()

    first_result, second = await asyncio.wait_for(
        asyncio.gather(a, b, return_exceptions=True), 5
    )
    assert isinstance(first_result, asyncio.CancelledError | TimeoutError)
    assert second.accepted
    assert system._deciding is False
    assert not system._queue
    assert (await asyncio.wait_for(system.async_handle(Tick()), 5)).accepted


async def test_the_last_event_sensor_shows_a_decision_without_waiting_for_the_next(
    hass, loaded, freezer
):
    """It is written by the notify, which came before the row it shows: it
    showed the decision before, until something else happened — all night,
    after an exit delay that ran out in an empty house."""
    seen: list[tuple[str, str]] = []

    @callback
    def announced(event: HassEvent) -> None:
        if event.data["category"] == "arming":
            shown = hass.states.get("sensor.foyer_last_event").state
            seen.append((event.data["event_type"], shown))

    hass.bus.async_listen(EVENT_FOYER, announced)
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)
    assert hass.states.get("sensor.foyer_last_event").state == "armed"

    await _call(hass, "alarm_disarm")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.foyer_last_event").state == "disarmed"
    # And it already showed each row when foyer_event announced it.
    assert ("armed", "armed") in seen
    assert ("disarmed", "disarmed") in seen


async def test_a_failed_action_reaches_the_last_event_sensor_on_its_own(
    hass, loaded, monkeypatch
):
    """How an action went is recorded after its decision's notify, and no
    other notify may be coming: a failure is the one action row shown."""
    system = _system(hass)
    real = system_module.decide

    def decide(snapshot, event, config, now):
        decision = real(snapshot, event, config, now)
        return (
            replace(decision, actions=(PROBE,)) if isinstance(event, Tick) else decision
        )

    monkeypatch.setattr(system_module, "decide", decide)

    async def run(decision):
        await asyncio.sleep(0)
        return [ActionResult(PROBE.action_id, PROBE.kind, False, "refused")]

    monkeypatch.setattr(system._executor, "async_run", run)

    await system.async_handle(Tick())
    await hass.async_block_till_done()

    sensor = hass.states.get("sensor.foyer_last_event")
    assert sensor.attributes["category"] == "action"
    assert sensor.attributes["outcome"] == "failed"


# --- (c) the reload and the state file -----------------------------------------------


@asynccontextmanager
async def _last_save_held(hass, entry, monkeypatch):
    """A reload, stopped inside the old system's last save until the block
    ends; then let through and finished, whatever the test found."""
    old = _system(hass)
    calls: list = []
    entered = asyncio.Event()
    release = asyncio.Event()
    real = old._state_store.async_save

    async def held(state, alive_at):
        calls.append(state)
        if len(calls) == 1:
            entered.set()
            await release.wait()
        await real(state, alive_at)

    monkeypatch.setattr(old._state_store, "async_save", held)
    reload = hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        yield old, calls
    finally:
        release.set()
        await asyncio.wait_for(reload, 10)
        await hass.async_block_till_done()


async def test_a_door_that_opens_during_the_last_save_is_left_to_the_next_start(
    hass, loaded, freezer, monkeypatch
):
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)
    async with _last_save_held(hass, loaded, monkeypatch) as (old, calls):
        before = old.state
        hass.states.async_set(ZONE, "on", {"friendly_name": "Front door"})
        assert old.state is before

    # The last save was the old system's last write.
    assert len(calls) == 1
    new = _system(hass)
    assert new is not old
    # And the door was not lost: the next start found it open.
    zone = new.config.zones[0]
    assert zone.id in new.state.active_zones
    assert new.state.areas[zone.area_id].state in (AreaState.ENTRY, AreaState.TRIGGERED)


async def test_a_stopping_system_arms_no_wake_up_and_saves_nothing_more(
    hass, loaded, monkeypatch
):
    await _call(hass, "alarm_arm_away")
    await hass.async_block_till_done()
    # The exit delay is running: there is a wake-up to arm.
    assert _system(hass)._unsub_wakeup is not None
    async with _last_save_held(hass, loaded, monkeypatch) as (old, calls):
        assert old._unsub_wakeup is None
        old.async_heartbeat(ZONE)
        old._reschedule()
        await old._async_save()
        decision = await old.async_handle(Tick())
        assert old._unsub_wakeup is None
        assert decision.accepted is False
        assert decision.reason is Reason.NOT_LOADED

    assert len(calls) == 1
    assert old._unsub_wakeup is None


async def test_a_call_still_waiting_for_its_turn_when_stopping_begins_is_refused(
    hass, loaded, monkeypatch
):
    """Checked once the turn is handed, not only when the call arrives: a
    stop may have begun while it waited."""
    system = _system(hass)
    # Another decision holds the turn, so this call waits in the queue.
    system._deciding = True
    waiting = hass.async_create_task(
        system.async_handle(SetAutoArming(enabled=not system.state.auto_arming))
    )
    await asyncio.sleep(0)
    assert not waiting.done()

    async with _last_save_held(hass, loaded, monkeypatch) as (old, calls):
        before = old.state
        old._next_turn()
        decision = await asyncio.wait_for(waiting, 5)
        assert decision.accepted is False
        assert decision.reason is Reason.NOT_LOADED
        assert old.state is before
        assert old._deciding is False
        assert not old._queue

    assert len(calls) == 1
