"""The runtime owner of alarm state: builds snapshots, calls decide(), applies.

This is the only place where a Decision becomes new state. The engine chooses;
this module records the choice, persists it (INV-3), re-arms the scheduler and
hands the actions to the executor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import (
    CALLBACK_TYPE,
    Event as HassEvent,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from ..const import CHANNEL_HA_UI, SIGNAL_UPDATE
from ..core import authz
from ..core.conditions import condition_entities
from ..core.diagnostics import as_dict as diagnostics_dict, diagnose
from ..core.engine import (
    arm_blockers,
    decide,
    master_state,
    next_wakeup,
    walk_test_zones,
)
from ..core.journal import LogRow, action_row, rows_for, test_action_row
from ..core.models import (
    Actor,
    Area,
    AreaState,
    Decision,
    EntityState,
    Event,
    FoyerConfig,
    LogCategory,
    Operation,
    Outcome,
    Reason,
    RuntimeState,
    Scenario,
    Startup,
    SystemSnapshot,
    Tick,
    User,
    ZoneStateChanged,
)
from ..core.response import PlanContext, notify_test_intent, test_intent
from ..core.simulate import (
    SimulationRequest,
    as_dict as simulation_dict,
    run as simulate_run,
)
from ..core.triggers import battery_level, battery_low, fault_cause
from ..store.log_store import LogStore
from ..store.state_store import StateStore, StoredState
from .executor import ActionResult, Executor

_LOGGER = logging.getLogger(__name__)

# How often "still alive" is written, bounding how much a crash can overstate
# the restart gap. Never understate: see store/state_store.py.
ALIVE_INTERVAL = timedelta(minutes=5)

# How often the log drops what is older than its retention (SPEC §10.3).
PURGE_INTERVAL = timedelta(days=1)

# Categories that do not become sensor.foyer_last_event. Zone activity is the
# noisy part of the log and would keep overwriting the event that matters; an
# action is the consequence of an event rather than an event, and "Foyer sent
# a notification" is a worse thing for a dashboard to show than what the
# notification was about. A *failed* action is the exception: that one is
# news, and it is the failure this project exists to surface early.
_QUIET_CATEGORIES = frozenset(
    {LogCategory.ZONE_ARMED, LogCategory.ZONE_DISARMED, LogCategory.ACTION}
)


def _ok(row: LogRow) -> bool:
    return row.outcome == Outcome.OK.value


def _action_rows(decision: Decision, results: list[ActionResult]) -> tuple[LogRow, ...]:
    """How each action went, filed against what asked for it.

    An action is planned from an occurrence, so the first occurrence of the
    same moment is where it happened: that is what gives the row its area,
    its zone and, when there is one, its incident.
    """
    context = {}
    for occurrence in decision.occurrences:
        context.setdefault(
            occurrence.moment,
            (occurrence.area_id, occurrence.zone_id, occurrence.incident_id),
        )
    by_id = {intent.action_id: intent for intent in decision.actions}
    rows = []
    for result in results:
        intent = by_id.get(result.action_id)
        moment = intent.moment if intent is not None else None
        area_id, zone_id, incident_id = context.get(moment, (None, None, None))
        rows.append(
            action_row(
                decision.at,
                action_id=result.action_id,
                kind=result.kind,
                moment=moment,
                ok=result.ok,
                error=result.error,
                profile_id=intent.profile_id if intent is not None else None,
                area_id=area_id,
                zone_id=zone_id,
                incident_id=incident_id,
            )
        )
    return tuple(rows)


def entity_state(state: State | None) -> EntityState:
    if state is None:
        return EntityState(state=None)
    return EntityState(
        state=state.state,
        attributes=dict(state.attributes),
        last_reported=state.last_reported,
        last_changed=state.last_changed,
    )


class FoyerSystem:
    """Holds the configuration and the runtime state of one config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: FoyerConfig,
        state_store: StateStore,
        stored: StoredState | None,
        log: LogStore | None = None,
    ) -> None:
        self.hass = hass
        self.config = config
        self.state = stored.state if stored else RuntimeState()
        self._down_since = stored.alive_at if stored else None
        self._state_store = state_store
        self.log = log
        self.last_row: LogRow | None = None
        # Until Home Assistant has started, entities are still appearing:
        # faults are not announced yet (see SystemSnapshot.settling).
        self.settling = not hass.is_running
        self.area_entity_ids: dict[str, str] = {}
        # The configuration reloads the entry on every change, so the language
        # Foyer speaks is read once, here, and never looked up mid-alarm.
        self._executor = Executor(hass, config.settings.language)
        self._listeners: list[Callable[[], None]] = []
        self._unsub_wakeup: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._started = False

    @property
    def language(self) -> str:
        """What Foyer speaks in what it sends out (§15.1, part 4 decision 2)."""
        return self._executor.language

    # --- lifecycle -----------------------------------------------------------

    @callback
    def async_start(self) -> None:
        """Begin: restore timers, then hand over to the engine once HA runs."""
        if self.hass.is_running:
            # A reload (a configuration change) or the integration being
            # enabled: Home Assistant itself did not restart.
            self.hass.async_create_task(self._async_started("reload"), eager_start=True)
        else:
            self._unsubs.append(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, self._on_ha_started
                )
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_alive, ALIVE_INTERVAL)
        )
        self._unsubs.append(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_ha_stop)
        )
        if self.log is not None:
            self._unsubs.append(
                async_track_time_interval(self.hass, self._on_purge, PURGE_INTERVAL)
            )
        self._reschedule()

    async def async_stop(self) -> None:
        """Unload: timers stop here, their state is on disk for the next start."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._unsub_wakeup:
            self._unsub_wakeup()
            self._unsub_wakeup = None
        await self._async_save()

    @callback
    def _on_ha_started(self, _event: HassEvent) -> None:
        self.hass.async_create_task(self._async_started("ha_start"), eager_start=True)

    async def _async_started(self, cause: str) -> None:
        if self._started:
            return
        self._started = True
        self.settling = False
        await self.async_handle(Startup(down_since=self._down_since, cause=cause))
        # Once at every start, as well as daily. A timer that only fires after
        # twenty-four hours never fires at all on a house that restarts more
        # often than that — and every configuration change reloads the entry,
        # which is a restart. Retention would be a setting that does nothing.
        await self._async_purge()

    @callback
    def _on_purge(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_purge(), eager_start=True)

    async def _async_purge(self) -> None:
        if self.log is None:
            return
        try:
            removed = await self.log.async_purge(
                self.config.settings.log, dt_util.utcnow()
            )
        except Exception:
            _LOGGER.exception("Foyer could not purge its event log")
            return
        if removed:
            _LOGGER.debug("Foyer purged %s expired log rows", removed)

    @callback
    def _on_alive(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_save(), eager_start=True)

    @callback
    def _on_ha_stop(self, _event: HassEvent) -> None:
        self.hass.async_create_task(self._async_save(), eager_start=True)

    # --- events --------------------------------------------------------------

    async def async_handle(
        self,
        event: Event,
        overrides: Mapping[str, EntityState] | None = None,
        old_state: str | None = None,
    ) -> Decision:
        """Decide, store, persist, execute, record. Returns the Decision."""
        # No await between snapshot and store: on the event loop this block is
        # atomic, so two events can never interleave their decisions.
        was_active = self.state.active_zones
        decision = decide(
            self._snapshot(overrides), event, self.config, dt_util.utcnow()
        )
        self.state = decision.state
        _LOGGER.debug("%s -> %s", event, decision)
        self._reschedule()
        self._notify()
        await self._async_save()
        # The log is written before the actions run and again after them: what
        # happened is on record even if an action hangs, and how each action
        # went is recorded when it is known (§10.2, category ``action``).
        self.async_record(
            rows_for(
                event,
                decision,
                self.config,
                old_state=old_state,
                was_active=was_active,
            )
        )
        results = await self._executor.async_run(decision)
        self.async_record(_action_rows(decision, results))
        return decision

    async def async_zone_changed(
        self, entity_id: str, old: State | None, new: State | None
    ) -> Decision:
        # Home Assistant has already stored the new state; the engine must see
        # the world as it was *before* the change to detect transitions.
        return await self.async_handle(
            ZoneStateChanged(entity_id=entity_id, new=entity_state(new)),
            overrides={entity_id: entity_state(old)},
            old_state=old.state if old else None,
        )

    @callback
    def async_record(self, rows: tuple[LogRow, ...]) -> None:
        """Hand rows to the log. Never waits for it: a slow or broken log must
        not delay the alarm path by one millisecond."""
        if not rows:
            return
        if self.log is not None:
            self.log.async_write(rows, self.config.settings.log)
        # sensor.foyer_last_event shows the last row that is worth showing,
        # which is not the thousandth motion of the day.
        for row in rows:
            quiet = row.category in _QUIET_CATEGORIES
            if not quiet or (row.category is LogCategory.ACTION and not _ok(row)):
                self.last_row = row

    @callback
    def async_heartbeat(self, entity_id: str) -> None:
        """An entity reported without changing: supervision moves on (decision 11)."""
        zones = [z for z in self.config.zones if z.entity_id == entity_id]
        if any(z.id in self.state.faults for z in zones):
            # It may have been in supervision fault: let the engine clear it.
            self.hass.async_create_task(self.async_handle(Tick()), eager_start=True)
        else:
            self._reschedule()

    # --- scheduler -----------------------------------------------------------

    @callback
    def _reschedule(self) -> None:
        """The scheduler owns the clock: one wake-up, at the next due time."""
        if self._unsub_wakeup:
            self._unsub_wakeup()
            self._unsub_wakeup = None
        now = dt_util.utcnow()
        due = next_wakeup(self._snapshot(), self.config, now)
        if due is None:
            return
        self._unsub_wakeup = async_track_point_in_utc_time(
            self.hass, self._on_wakeup, max(due, now)
        )

    @callback
    def _on_wakeup(self, _now: datetime) -> None:
        self._unsub_wakeup = None
        self.hass.async_create_task(self.async_handle(Tick()), eager_start=True)

    # --- persistence ---------------------------------------------------------

    async def _async_save(self) -> None:
        try:
            await self._state_store.async_save(self.state, dt_util.utcnow())
        except Exception:
            # Keep running: an alarm that stops because the disk is full is
            # worse than one that cannot remember. Say so loudly.
            _LOGGER.exception("Foyer could not persist its state")

    # --- snapshot ------------------------------------------------------------

    def zone_entity_ids(self) -> list[str]:
        """What the watcher subscribes to: zones, and the tags that command.

        An arming device's entity belongs here for the same reason a zone's
        does — a scan is a state change, and an entity nobody is listening to
        is a tag that works once, at the next restart (§9.3).
        """
        return sorted(
            {z.entity_id for z in self.config.zones}
            | {d.entity_id for d in self.config.devices if d.entity_id}
        )

    def watched_entity_ids(self) -> list[str]:
        """Zones and arming devices, plus every entity an action's condition
        reads (§6.3): the engine is given the world, it never looks anything
        up (INV-1)."""
        entities = {z.entity_id for z in self.config.zones}
        # A zone's battery entity is watched like the zone itself: it is read
        # on every decision — a battery that cannot be read is a fault, and
        # one that falls below the threshold raises a moment — so an entity
        # nobody subscribed to is a battery Foyer notices only at the next
        # restart (§4.2, part 1 decision 2).
        entities.update(
            z.battery_entity_id for z in self.config.zones if z.battery_entity_id
        )
        entities.update(d.entity_id for d in self.config.devices if d.entity_id)
        for profile in self.config.profiles:
            for action in profile.actions:
                entities.update(condition_entities(action))
        return sorted(entities)

    def _snapshot(
        self, overrides: Mapping[str, EntityState] | None = None
    ) -> SystemSnapshot:
        entities = {
            entity_id: entity_state(self.hass.states.get(entity_id))
            for entity_id in self.watched_entity_ids()
        }
        entities.update(overrides or {})
        return SystemSnapshot(
            self.state, entities, self.settling, dt_util.get_default_time_zone()
        )

    # --- listeners -----------------------------------------------------------

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            self._listeners.remove(listener)

        return remove

    @callback
    def async_notify(self) -> None:
        """Tell subscribers something visible changed (e.g. a zone state)."""
        self._notify()

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    # --- read model ----------------------------------------------------------

    def blockers(self, area_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
        return arm_blockers(self._snapshot(), self.config, area_ids, dt_util.utcnow())

    def master(self) -> tuple[AreaState, str | None]:
        return master_state(self.state, self.config)

    def diagnostics(self) -> dict[str, Any]:
        """The §11.1 table, built by core from a snapshot it is handed."""
        return diagnostics_dict(
            diagnose(self._snapshot(), self.config, dt_util.utcnow())
        )

    def simulate(self, request: SimulationRequest) -> dict[str, Any]:
        """Rehearse the configuration and answer with the trace (§11.2).

        The live entity states are read here, because reading Home Assistant
        is this layer's job, and handed to a pure function that calls the same
        decide() this class calls. Nothing is executed and nothing is stored:
        the Decisions never reach the executor and never reach ``self.state``.
        """
        snapshot = self._snapshot()
        simulation = simulate_run(self.config, request, snapshot.entities)
        return simulation_dict(simulation, self.config)

    async def async_test_action(
        self,
        *,
        profile_id: str | None = None,
        action_id: str | None = None,
        service: str | None = None,
        message: str = "",
        actor: Actor | None = None,
    ) -> dict[str, Any]:
        """Really execute one action, and record that it was a test (§11.4).

        It really executes because that is the whole point: the failure this
        prevents is discovering during the emergency that the emergency
        channel was misconfigured. The intent is built by ``core/response``,
        exactly as the engine builds every other one, and handed to the same
        executor — a test that went through a path of its own would prove
        that path works.

        Nothing about the alarm changes: no Decision is made, no state is
        stored, and the row it leaves is filed as a test rather than as the
        alarm it imitates.
        """
        if service:
            intent = notify_test_intent(service, message)
        else:
            profile = self.config.profile(profile_id)
            if profile is None:
                return {"success": False, "reason": "unknown_profile"}
            ctx = PlanContext(
                config=self.config,
                snapshot=self._snapshot(),
                now=dt_util.utcnow(),
                areas=self.state.areas,
                incident=self.state.incident,
                active_zones=self.state.active_zones,
            )
            built = test_intent(ctx, profile, action_id or "")
            if built is None:
                return {"success": False, "reason": "unknown_action"}
            intent = built
        results = await self._executor.async_run(
            Decision(
                at=dt_util.utcnow(), accepted=True, state=self.state, actions=(intent,)
            )
        )
        result = results[0]
        named = self.config.user(actor.user_id) if actor else None
        self.async_record(
            (
                test_action_row(
                    dt_util.utcnow(),
                    action_id=intent.action_id,
                    kind=intent.kind,
                    ok=result.ok,
                    error=result.error,
                    profile_id=profile_id,
                    user_id=actor.user_id if actor else None,
                    user_name=named.name if named else None,
                    channel=actor.channel if actor else None,
                ),
            )
        )
        return {
            "success": result.ok,
            "reason": None if result.ok else "action_failed",
            "kind": intent.kind,
            "error": result.error,
        }

    def walk_test_status(self) -> dict[str, Any] | None:
        """What page 9 and the banner need while a walk test runs (§11.3).

        ``expected`` is every zone the walk should have reached, so that
        silence can be shown as a finding rather than as an empty table —
        which is the whole feature. `always_on` zones are left out: they are
        live rather than under test, and nobody sets off the smoke detector
        to prove it works.
        """
        walk = self.state.walk_test
        if walk is None:
            return None
        # The engine's own list, so the table and the row the engine writes
        # when the test ends can never name different zones.
        expected = list(walk_test_zones(self.config, self.state.bypassed))
        return {
            "started_at": walk.started_at.isoformat(),
            "until": walk.until.isoformat(),
            "hard_until": walk.hard_until.isoformat(),
            "deadline": walk.deadline().isoformat(),
            "window": walk.window,
            "armed_areas": list(walk.armed_areas),
            "user_id": walk.user_id,
            "user_name": walk.user_name,
            "channel": walk.channel,
            "expected_zones": expected,
            "detections": {
                zone_id: {
                    "first": d.first.isoformat(),
                    "last": d.last.isoformat(),
                    "count": d.count,
                }
                for zone_id, d in walk.detections.items()
            },
        }

    def result(self, decision: Decision, ha_user: Any = None) -> dict[str, Any]:
        """The structured result of SPEC §9.1.

        One function, so that a service call, a WebSocket command and an MQTT
        message cannot answer three different shapes — which is the whole
        point of §9.1: a keypad adapter must be able to tell a wrong code from
        arming blocked by an open zone, whatever it is speaking through. The
        zones are named as well as identified, because a keypad with a display
        shows a name and has no configuration to look one up in.
        """
        names = {z.id: z.name for z in self.config.zones}
        return {
            "success": decision.accepted,
            "reason": decision.reason.value if decision.reason else None,
            "blocking_zones": [
                {"id": z, "name": names.get(z, z)} for z in decision.blocking_zones
            ],
            "bypassed_zones": [
                {"id": z, "name": names.get(z, z)} for z in decision.bypassed_zones
            ],
            # Not a blocker and never presented as one: an arming that went
            # ahead with a zone on a dying cell says so, every time, on every
            # channel (part 1 decision 2).
            "low_battery_zones": [
                {"id": z, "name": names.get(z, z)} for z in decision.low_battery_zones
            ],
            "state": self.status(ha_user),
        }

    def refusal(self, reason: Reason, ha_user: Any = None) -> dict[str, Any]:
        """The same shape for a request refused before the engine saw it.

        A device that is not registered never reaches decide(): there is
        nothing for the engine to decide about it (part 2 decision 1). The
        caller must still be answered in the shape it was promised.
        """
        return {
            "success": False,
            "reason": reason.value,
            "blocking_zones": [],
            "bypassed_zones": [],
            "low_battery_zones": [],
            "state": self.status(ha_user),
        }

    def status(self, ha_user: Any = None) -> dict[str, Any]:
        """The live state as sent to the panel and the card. Contains no secrets.

        It is personal, which is why the connected Home Assistant user is
        passed in: whether a code will be asked for depends on who is asking
        (§8.2), and a card that demanded one from somebody exempt — or hid the
        keypad from somebody who needs it — would be wrong in both directions.
        The answer is a courtesy either way; the backend decides (INV-2).
        """
        now = dt_util.utcnow()
        # The Foyer user linked to this Home Assistant account, if any. It is
        # what makes the answer personal; a connection with no linked user is
        # simply told what the policy asks of everybody.
        me = self.config.user_of_ha(getattr(ha_user, "id", None))
        snapshot = self._snapshot()
        master, mode = master_state(self.state, self.config)
        areas = []
        for area in self.config.areas:
            rt = self.state.area(area.id)
            faulted, open_ = arm_blockers(snapshot, self.config, (area.id,), now)
            areas.append(
                {
                    "id": area.id,
                    "name": area.name,
                    "state": rt.state.value,
                    "entity_id": self.area_entity_ids.get(area.id),
                    "scenario_id": rt.scenario_id,
                    "memory": rt.memory,
                    "causes": list(rt.causes),
                    "timer": None
                    if rt.timer is None
                    else {"kind": rt.timer.kind.value, "due": rt.timer.due.isoformat()},
                    "ready": not faulted and not open_,
                    "blocking": {"fault": list(faulted), "open": list(open_)},
                    "require_code": self._require_code(area=area, user=me, now=now),
                }
            )
        zones = []
        threshold = self.config.settings.low_battery_threshold
        for zone in self.config.zones:
            entity = snapshot.entity(zone.entity_id)
            battery = snapshot.entity(zone.battery_entity_id or "")
            zones.append(
                {
                    "id": zone.id,
                    "name": zone.name,
                    "area_id": zone.area_id,
                    "entity_id": zone.entity_id,
                    "type": zone.type.value,
                    "channel": zone.channel.value,
                    "enabled": zone.enabled,
                    "state": entity.state,
                    "fault": (
                        fault_cause(zone, entity, now, battery)
                        if zone.enabled
                        else None
                    ),
                    "battery": (
                        battery_level(battery) if zone.battery_entity_id else None
                    ),
                    "low_battery": battery_low(zone, battery, threshold),
                    "open": zone.id in self.state.active_zones,
                    "bypassed": (
                        self.state.bypassed[zone.id].value
                        if zone.id in self.state.bypassed
                        else None
                    ),
                    "bypassable": zone.bypassable,
                    "bypass_until": (
                        self.state.bypass_until[zone.id].isoformat()
                        if zone.id in self.state.bypass_until
                        else None
                    ),
                }
            )
        return {
            "now": now.isoformat(),
            "active_scenario_id": self.state.active_scenario_id,
            # §11.3: an unmissable banner in the panel and on every card
            # while it is active. Both read it from here.
            "walk_test": self.walk_test_status(),
            "master": {"state": master.value, "mode": mode},
            "areas": areas,
            "scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "icon": s.icon,
                    "areas": list(s.areas),
                    "ha_master_state": s.ha_master_state,
                    "require_code": self._require_code(scenario=s, user=me, now=now),
                }
                for s in self.config.scenarios
            ],
            "zones": zones,
            "technical": self.technical_status(),
            "incident": self.incident_status(),
            "chime_enabled": self.state.chime_enabled,
            "security": self.security_status(me, now),
        }

    def security_status(self, me: User | None, now: datetime) -> dict[str, Any]:
        """What the panel and the card need to know about codes (§8.2, §8.4).

        No code, no hash and no name of anybody else: who is connected already
        knows who they are, and everything here is about them.
        """
        locked = self.state.lockouts.get(f"{CHANNEL_HA_UI}:")
        return {
            # False while nobody holds a code: the panel says so plainly,
            # because "anyone who can reach Home Assistant can disarm" is a
            # fact about this installation and not a detail (decision 78).
            "enforced": authz.enforced(self.config, now),
            "code_length": self.config.settings.security.code_length,
            "has_users": bool(self.config.users),
            "me": (
                None
                if me is None
                else {
                    "user_id": me.id,
                    "name": me.name,
                    "permissions": sorted(me.permissions),
                    "code_exempt": me.code_exempt_when_identified,
                }
            ),
            # What each operation would ask of this person right now, with no
            # area or scenario in mind: the global picture, refined per area
            # and per scenario above.
            "require_code": {
                operation.value: self._require_code(
                    operation=operation, user=me, now=now
                )
                for operation in Operation
            },
            "locked_until": (
                locked.until.isoformat()
                if locked is not None and locked.until and locked.until > now
                else None
            ),
        }

    def _require_code(
        self,
        *,
        now: datetime,
        user: User | None = None,
        area: Area | None = None,
        scenario: Scenario | None = None,
        operation: Operation | None = None,
    ) -> Any:
        """Resolve §8.2 for the panel, through the same function the engine uses."""

        def ask(op: Operation) -> bool:
            areas = (area,) if area is not None else ()
            if scenario is not None:
                areas = tuple(
                    a for a in (self.config.area(i) for i in scenario.areas) if a
                )
            return authz.code_required(
                self.config,
                op,
                now=now,
                areas=tuple(a for a in areas if a is not None),
                scenario=scenario,
                user=user,
                identified=user is not None,
                channel=CHANNEL_HA_UI,
            )

        if operation is not None:
            return ask(operation)
        return {"arm": ask(Operation.ARM), "disarm": ask(Operation.DISARM)}

    def technical_status(self) -> list[dict[str, Any]]:
        """The technical channel (§5.5): every zone in alarm or in memory."""
        names = {z.id: z for z in self.config.zones}
        out = []
        for zone_id, alarm in self.state.technical.items():
            zone = names.get(zone_id)
            out.append(
                {
                    "zone_id": zone_id,
                    "name": zone.name if zone else zone_id,
                    "area_id": zone.area_id if zone else None,
                    "since": alarm.since.isoformat(),
                    "active": zone_id in self.state.active_zones,
                    "acknowledged": alarm.acknowledged,
                }
            )
        return out

    def incident_status(self) -> dict[str, Any] | None:
        incident = self.state.incident
        if incident is None:
            return None
        return {
            "id": incident.id,
            "opened_at": incident.opened_at.isoformat(),
            "zone_ids": list(incident.zone_ids),
            "area_ids": list(incident.area_ids),
            "acknowledged": incident.acknowledged,
        }
