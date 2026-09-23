"""The runtime owner of alarm state: builds snapshots, calls decide(), applies.

This is the only place where a Decision becomes new state. The engine chooses;
this module records the choice, persists it (INV-3), re-arms the scheduler and
hands the actions to the executor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientError, ClientTimeout
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import (
    CALLBACK_TYPE,
    Event as HassEvent,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .. import i18n, repairs
from ..const import CHANNEL_HA_UI, SIGNAL_UPDATE
from ..core import authz, health as health_engine, rules as rules_engine
from ..core.conditions import condition_entities
from ..core.diagnostics import as_dict as diagnostics_dict, diagnose
from ..core.engine import (
    arm_blockers,
    decide,
    master_state,
    next_wakeup,
    walk_test_zones,
)
from ..core.journal import (
    LogRow,
    action_row,
    rows_for,
    security_row,
    test_action_row,
)
from ..core.models import (
    ActionIntent,
    ActionKind,
    Actor,
    Area,
    AreaState,
    Decision,
    EntityState,
    Event,
    FoyerConfig,
    HealthReport,
    LogCategory,
    Moment,
    Operation,
    Outcome,
    Reason,
    RuntimeState,
    Scenario,
    Startup,
    Suspension,
    SystemSnapshot,
    Tick,
    User,
    Zone,
    ZoneStateChanged,
)
from ..core.privacy import cutoff as privacy_cutoff, ref_for
from ..core.response import (
    PlanContext,
    contact_test_intent,
    notify_test_intent,
    recipients_for,
    test_intent,
)
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

# How long one watchdog ping may take before it counts as a failure (§12.3).
# The interval between pings is a setting; this is not, because thirty
# seconds is already longer than any healthy endpoint takes and a longer one
# would only delay the answer Foyer is waiting for.
WATCHDOG_USER_AGENT = "FoyerHomeDefender"

# Categories that do not become sensor.foyer_last_event. Zone activity is the
# noisy part of the log and would keep overwriting the event that matters; an
# action is the consequence of an event rather than an event, and "Foyer sent
# a notification" is a worse thing for a dashboard to show than what the
# notification was about. A *failed* action is the exception: that one is
# news, and it is the failure this project exists to surface early.
_QUIET_CATEGORIES = frozenset(
    {LogCategory.ZONE_ARMED, LogCategory.ZONE_DISARMED, LogCategory.ACTION}
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _suspension_dict(suspension: Suspension) -> dict[str, Any]:
    """One suspension, as the panel and the card show it (§9.4)."""
    return {
        "id": suspension.id,
        "kind": suspension.kind.value,
        "rule_ids": list(suspension.rule_ids),
        "name": suspension.name,
        "start": suspension.start.isoformat() if suspension.start else None,
        "until": suspension.until.isoformat() if suspension.until else None,
        "reduced_scenario_id": suspension.reduced_scenario_id,
        "created_at": (
            suspension.created_at.isoformat() if suspension.created_at else None
        ),
        "user_id": suspension.user_id,
        "user_name": suspension.user_name,
    }


def _next_action_dict(
    upcoming: rules_engine.NextAction | None,
) -> dict[str, Any] | None:
    if upcoming is None:
        return None
    return {
        "rule_id": upcoming.rule_id,
        "rule_name": upcoming.rule_name,
        "action": upcoming.action.value,
        "at": upcoming.at.isoformat() if upcoming.at else None,
        "scenario_id": upcoming.scenario_id,
        "area_ids": list(upcoming.area_ids),
        "pending_id": upcoming.pending_id,
        "suspension": (
            _suspension_dict(upcoming.suspension)
            if upcoming.suspension is not None
            else None
        ),
    }


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

    # Set once this system has written a newer configuration and a reload
    # is on its way (api/backup.async_write). Until the reload replaces it,
    # it refuses further edits and the device endpoint answers nothing: both
    # would otherwise act on a document that is no longer the stored one.
    superseded: bool = False

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
        self.master_entity_id: str | None = None
        # The configuration reloads the entry on every change, so the language
        # Foyer speaks is read once, here, and never looked up mid-alarm.
        self._executor = Executor(hass, config.settings.language)
        self._listeners: list[Callable[[], None]] = []
        self._unsub_wakeup: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._started = False
        # Guards the one-level recursion of _async_report_sends, and holds
        # what that recursion could not carry.
        self._reporting = False
        self._pending_sends: dict[str, bool] = {}
        # Set by async_stop. Anything that was awaiting when the entry
        # unloaded checks it before touching state: a reload while a
        # watchdog ping is in flight would otherwise leave the old instance
        # writing its own state over the new one's, pushing updates to
        # removed entities and arming a wake-up nothing will ever cancel
        # (INV-3).
        self._stopped = False
        # Memoisation for the read model, invalidated on every change.
        self._revision = 0
        self._health_at = -1
        self._health_cache: dict[str, Any] | None = None
        self._unsub_started: CALLBACK_TYPE | None = None
        self._by_entity: dict[str, tuple[Zone, ...]] | None = None
        self._watched: list[str] | None = None
        self._blockers_rev = -1
        self._notify_pending = False
        self._blockers_cache: dict[tuple[str, ...], tuple[tuple[str, ...], ...]] = {}
        self._unsub_stop: CALLBACK_TYPE | None = None
        self._radio_cache: dict[str, str] | None = None
        # Which config entry this system belongs to, for the repair issues
        # of §12.4. Set by __init__.py once the entry exists.
        self.entry_id: str | None = None

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
            self._unsub_started = self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._on_ha_started
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_alive, ALIVE_INTERVAL)
        )
        # Which radio an entity sits on changes only with the registry, not
        # with every door that opens: the map was thrown away on every notify
        # and rebuilt from registry lookups on the next event (second review).
        self._unsubs.append(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_registry_updated
            )
        )
        self._unsub_stop = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._on_ha_stop
        )
        if self.log is not None:
            self._unsubs.append(
                async_track_time_interval(self.hass, self._on_purge, PURGE_INTERVAL)
            )
        # The third and fourth periodic jobs in this file (§12.2, §12.3).
        # Both are registered whatever the configuration says, because both
        # read the configuration when they fire: a watchdog switched on from
        # the panel must not wait for a reload, and the entry reloads on
        # every configuration change anyway, which is what unregisters them.
        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                self._on_watchdog,
                timedelta(seconds=self.config.health.watchdog.interval),
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                self._on_channel_sweep,
                timedelta(seconds=self.config.health.channel_sweep),
            )
        )
        self._reschedule()

    async def async_stop(self) -> None:
        """Unload: timers stop here, their state is on disk for the next start."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        # A listen-once handle is spent once its event has fired, and calling
        # it again makes Home Assistant log an error with a traceback — on
        # the first configuration save after every start (second review).
        for name in ("_unsub_started", "_unsub_stop"):
            if (unsub := getattr(self, name)) is not None:
                unsub()
                setattr(self, name, None)
        # The last save, and only then the flag that refuses every later one:
        # set first, it made this save return at once, and the restart gap
        # after a reload was measured from a stale `alive_at` (second review).
        await self._async_save()
        self._stopped = True
        # After the save: a zone that changed while it was writing ran a
        # decision, and that decision may have set a wake-up nothing else
        # would ever cancel.
        if self._unsub_wakeup:
            self._unsub_wakeup()
            self._unsub_wakeup = None

    @callback
    def _on_registry_updated(self, _event: HassEvent) -> None:
        self._radio_cache = None

    @callback
    def _on_ha_started(self, _event: HassEvent) -> None:
        self._unsub_started = None  # spent: see async_stop
        self.hass.async_create_task(self._async_started("ha_start"), eager_start=True)

    async def _async_started(self, cause: str) -> None:
        if self._started:
            return
        self._started = True
        self.settling = False
        await self.async_handle(Startup(down_since=self._down_since, cause=cause))
        self.async_reconcile_issues()
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
            removed = 0
        if removed:
            _LOGGER.debug("Foyer purged %s expired log rows", removed)
        # Whatever the purge did. The two jobs share a schedule and nothing
        # else: a locked database that stopped the purge must not also stop an
        # installation's names from ageing out, which is a thing somebody
        # asked for and would never be told had stopped happening.
        await self._async_pseudonymise()

    async def _async_pseudonymise(self) -> None:
        """Rows older than the configured delay keep an identifier, not a name.

        Off unless the installation asked for it (§10.4). It runs here, beside
        the purge, because it is the same kind of job — retention applied on a
        schedule — and because the one place it must never run is the write
        path: this is data minimisation, and an alarm must not wait for it.
        """
        after = self.config.settings.log.pseudonymise_after
        if self.log is None or not after:
            return
        people = [ref_for(self.config, user) for user in self.config.users]
        if not people:
            return
        try:
            changed = await self.log.async_pseudonymise(
                people, privacy_cutoff(dt_util.utcnow(), after)
            )
        except Exception:
            _LOGGER.exception("Foyer could not pseudonymise its older log rows")
            return
        if changed:
            _LOGGER.debug("Foyer pseudonymised %s older log rows", changed)

    @callback
    def _on_alive(self, _now: datetime) -> None:
        # The health status depends on the clock as well as on the state —
        # how long a zone has been unreachable, how many days — and on a
        # quiet house nothing else moves the revision it is cached on, so the
        # repair cards measured in days never appeared (second review).
        self._health_cache = None
        self.hass.async_create_task(self._async_save(), eager_start=True)
        # Persistent problems belong in Settings, where somebody sees them
        # without opening the Foyer panel (§12.4). Reconciled here rather
        # than after every decision: these are measured in hours and days,
        # and a door opening is not news about any of them.
        self.async_reconcile_issues()

    @callback
    def async_reconcile_issues(self) -> None:
        if self.entry_id is None or self._stopped:
            return
        try:
            keep = repairs.reconcile(
                self.hass,
                self.entry_id,
                self.health_status(),
                self.state.health.acknowledged_issues,
            )
        except Exception:
            # A repair card nobody could raise must never stop the alarm.
            _LOGGER.exception("Foyer could not reconcile its repair issues")
            return
        if keep != self.state.health.acknowledged_issues:
            self._remember_acknowledged(keep)

    def _remember_acknowledged(self, issues: frozenset[str]) -> None:
        """Write the acknowledged set straight into the state.

        The one thing in ``RuntimeState`` the engine does not decide: it is
        about a card in Home Assistant's Settings, not about the house, and
        ``decide()`` carries it through untouched. It is in the state at all
        because the alternative is a card that comes back five minutes after
        somebody dismissed it, and again after every restart.
        """
        self.state = replace(
            self.state,
            health=replace(self.state.health, acknowledged_issues=issues),
        )
        if not self._stopped:
            # Nothing this instance starts may outlive its unload: a save
            # scheduled here would write the old entry's state over the new
            # one's, which is the same hole the ping in flight had.
            self.hass.async_create_task(self._async_save(), eager_start=True)

    async def async_acknowledge_issue(self, issue_id: str) -> None:
        """Somebody pressed "mark as seen" on a repair card (§12.4)."""
        current = self.state.health.acknowledged_issues
        if issue_id in current:
            return
        self._remember_acknowledged(current | {issue_id})

    @callback
    def _on_ha_stop(self, _event: HassEvent) -> None:
        self._unsub_stop = None  # spent: see async_stop
        self.hass.async_create_task(self._async_save(), eager_start=True)

    # --- system health (§12) -------------------------------------------------

    @callback
    def _on_watchdog(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_watchdog(), eager_start=True)

    async def _async_watchdog(self) -> None:
        """Ping the external URL and tell the engine how it went (§12.3).

        The timer lives here and the meaning lives in ``core``: this method
        knows how to make an HTTP request and nothing else. How many
        failures in a row amount to an outage, when to say so and what to
        say is the engine's, which is why the simulator can show the moment
        this produces without anything reaching the network.
        """
        settings = self.config.health.watchdog
        if not settings.enabled or not settings.url:
            return
        if self.settling:
            # Not while Home Assistant is still starting (part 1 decision 6):
            # a ping that fails because the network stack is not up yet is a
            # failure about Home Assistant's boot order, not about the
            # watchdog, and three of them would announce an outage that
            # never happened.
            return
        payload = health_engine.watchdog_payload(self.config, self._snapshot())
        session = async_get_clientsession(self.hass)
        error = ""
        ok = False
        try:
            # GET with nothing at all unless the household explicitly asked
            # for a payload (P-1, decision 29). The default heartbeat is the
            # request itself: its arrival is the whole message.
            if payload is None:
                response = await session.get(
                    settings.url,
                    timeout=ClientTimeout(total=settings.timeout),
                    headers={"User-Agent": WATCHDOG_USER_AGENT},
                )
            else:
                response = await session.post(
                    settings.url,
                    json=dict(payload),
                    timeout=ClientTimeout(total=settings.timeout),
                    headers={"User-Agent": WATCHDOG_USER_AGENT},
                )
            async with response:
                ok = response.status < 400
                if not ok:
                    error = f"HTTP {response.status}"
        except (TimeoutError, ClientError, OSError, ValueError) as err:
            error = f"{type(err).__name__}: {err}"
        if settings.url:
            # The URL is the credential — whoever holds a healthchecks.io
            # ping URL can keep the check green for ever, which is to say
            # silence the one thing that reports Foyer's own death. aiohttp
            # puts it in the message; the log and page 14 must not.
            error = error.replace(settings.url, "<url>")
        await self.async_handle(HealthReport(watchdog=ok, watchdog_error=error))

    @callback
    def _on_channel_sweep(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_channel_sweep(), eager_start=True)

    async def _async_channel_sweep(self) -> None:
        """Is every configured notification channel still real? (§12.2)

        A read of the service registry, which is a dictionary in memory —
        cheap enough to do every quarter of an hour and the only way to
        notice that an integration was removed, renamed or failed to load
        after an update before the night somebody needs it.
        """
        present = {
            key: self._service_exists(service)
            for key, service in health_engine.configured_channels(self.config).items()
        }
        if present:
            await self.async_handle(HealthReport(channels_present=present))

    def _service_exists(self, service: str) -> bool:
        """Whether a channel's ``notify`` target is there to be called.

        Two shapes are configurable (§7.1): a ``notify.*`` service, and a
        ``notify`` entity. The first is a registry lookup; the second is an
        entity that has to exist and be readable, which is INV-4 read in the
        one other place it applies.
        """
        if not service:
            return False
        if "." not in service:
            return self.hass.services.has_service("notify", service)
        # An entity first, as the executor resolves it, and existing is
        # enough. A notify entity's state is the timestamp of the last
        # message it sent, so a channel nobody has used yet reads as
        # ``unknown`` — and calling that missing would break every newly
        # configured channel fifteen minutes after somebody added it.
        # Unavailable is different: that one really cannot be called.
        state = self.hass.states.get(service)
        if state is not None:
            return state.state != "unavailable"
        domain, _, name = service.partition(".")
        return self.hass.services.has_service(domain, name)

    # --- events --------------------------------------------------------------

    async def async_handle(
        self,
        event: Event,
        overrides: Mapping[str, EntityState] | None = None,
        old_state: str | None = None,
    ) -> Decision:
        """Decide, store, persist, execute, record. Returns the Decision."""
        if self._stopped:
            # This instance has been unloaded. Whatever was awaiting is
            # finishing after the fact, and the house belongs to whoever
            # replaced it.
            #
            # Refused, rather than an accepted Tick (found in review): a
            # disarm arriving in that gap would otherwise be answered
            # `success: true` — to the keypad, to the service caller and to
            # the panel — while nothing at all had happened.
            return replace(
                decide(self._snapshot(), Tick(), self.config, dt_util.utcnow()),
                accepted=False,
                reason=Reason.NOT_LOADED,
            )
        # No await between snapshot and store: on the event loop this block is
        # atomic, so two events can never interleave their decisions.
        was_active = self.state.active_zones
        previous = self.state
        decision = decide(
            self._snapshot(overrides), event, self.config, dt_util.utcnow()
        )
        self.state = decision.state
        _LOGGER.debug("%s -> %s", event, decision)
        # Neither the timers nor the log may stand between a stored decision
        # and its sirens: §10 says a log failure never blocks the alarm path,
        # and an exception here used to skip the executor (second review).
        try:
            self._reschedule()
        except Exception:
            _LOGGER.exception("Foyer could not schedule its next wake-up")
        self._notify()
        if decision.state != previous or decision.occurrences or decision.actions:
            # Only when something about the alarm moved: an attribute a
            # sensor reports every few seconds wrote the whole state file
            # each time, which on a Raspberry Pi's card is wear for nothing
            # (second review). The alive tick still saves every five minutes.
            await self._async_save()
        # The log is written before the actions run and again after them: what
        # happened is on record even if an action hangs, and how each action
        # went is recorded when it is known (§10.2, category ``action``).
        try:
            self.async_record(
                rows_for(
                    event,
                    decision,
                    self.config,
                    old_state=old_state,
                    was_active=was_active,
                )
            )
        except Exception:
            _LOGGER.exception("Foyer could not record a decision in its log")
        if decision.actions:
            # Run beside the caller, not inside it. A notification now waits
            # for its transport's answer, and a keypad, a service call or
            # the panel must not wait for that answer to learn that its
            # disarm was accepted; nor may a caller that is cancelled — an
            # automation restarted, a script stopped — cancel a notification
            # half-sent and lose its log row and its retry (second review).
            self.hass.async_create_task(
                self._async_execute(decision), f"foyer actions {decision.at}"
            )
        return decision

    async def _async_execute(self, decision: Decision) -> None:
        results = await self._executor.async_run(decision)
        self.async_record(_action_rows(decision, results))
        await self._async_report_sends(results)

    async def _async_report_sends(self, results: list[ActionResult]) -> None:
        """Tell the engine how each notification channel actually did (§12.2).

        One level deep and no further. The report itself may produce a
        notification — that is the whole of "announce a broken channel over
        a channel that still works" — and feeding *its* sends back in turn
        would be a loop that runs until something fails differently. What is
        lost is one cycle's evidence about the channel that carried the
        warning, which the next sweep or the next real send says again.
        """
        sends: dict[str, bool] = {}
        for result in results:
            sends.update(result.sends)
        if self._reporting:
            # Held rather than discarded: this is evidence about a real
            # send, and the alternative is losing what a dead channel did
            # while Foyer was busy saying another one was dead.
            self._pending_sends.update(sends)
            return
        sends = {**self._pending_sends, **sends}
        self._pending_sends = {}
        if not sends:
            return
        self._reporting = True
        try:
            await self.async_handle(HealthReport(channel_sends=sends))
        finally:
            self._reporting = False

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
        if self._stopped:
            # The watcher is unsubscribed after the unload returns, so a
            # report can still arrive here — and `_reschedule` below would
            # arm a wake-up on a dead instance that nothing will ever cancel
            # (found in review).
            return
        zones = self._zones_by_entity().get(entity_id, ())
        if any(z.id in self.state.faults for z in zones):
            # It may have been in supervision fault: let the engine clear it.
            self.hass.async_create_task(self.async_handle(Tick()), eager_start=True)
        elif any(z.supervision_timeout for z in zones):
            # Only a supervised zone's deadline moves with a report. A person
            # tracker or a battery sensor reporting every few seconds would
            # otherwise rebuild the snapshot to reschedule nothing (second
            # review).
            self._reschedule()

    def _zones_by_entity(self) -> dict[str, tuple[Zone, ...]]:
        if self._by_entity is None:
            index: dict[str, list[Zone]] = {}
            for zone in self.config.zones:
                index.setdefault(zone.entity_id, []).append(zone)
            self._by_entity = {k: tuple(v) for k, v in index.items()}
        return self._by_entity

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
        self.hass.async_create_task(self._async_wakeup(), eager_start=True)

    async def _async_wakeup(self) -> None:
        """The Tick a timer asked for, and the next one whatever happens.

        Found in review: this handle is the only thing that arms the next
        wake-up, so a decision that raised here stopped the scheduler
        permanently — no exit delay, entry delay, escalation step or bypass
        expiry would ever fire again until an unrelated zone happened to
        move.
        """
        try:
            await self.async_handle(Tick())
        except Exception:
            _LOGGER.exception("Foyer could not handle a scheduled wake-up")
            self._reschedule()

    # --- persistence ---------------------------------------------------------

    async def _async_save(self) -> None:
        if self._stopped:
            # A save started before the unload and finishing after it would
            # write this instance's state over the one that replaced it
            # (found in review) — the hole `_remember_acknowledged` already
            # closed for its own task.
            return
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
            # And the people an automatic rule watches (§9.4). A phone leaving
            # the house is a state change like any other, and a rule reading
            # an entity nobody subscribed to would arm the house at the next
            # periodic wake-up instead of when everybody actually left.
            | set(self.rule_entity_ids())
        )

    def watched_entity_ids(self) -> list[str]:
        """Zones and arming devices, plus every entity an action's condition
        reads (§6.3): the engine is given the world, it never looks anything
        up (INV-1).

        Worked out once: the configuration cannot change within a system's
        life (a save reloads it), and this ran on every snapshot (second
        review)."""
        if self._watched is None:
            self._watched = self._watched_entity_ids()
        return self._watched

    def _watched_entity_ids(self) -> list[str]:
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
        entities.update(self.rule_entity_ids())
        # System health (§12): the mains entity and every radio's
        # coordinator. Both are read on every decision — a power cut raises
        # a moment, a coordinator that has gone changes what a silent radio
        # means — so an entity nobody subscribed to is a power cut Foyer
        # notices at the next door opening.
        if self.config.health.mains_entity_id:
            entities.add(self.config.health.mains_entity_id)
        entities.update(
            r.coordinator_entity_id
            for r in self.config.health.radios
            if r.enabled and r.coordinator_entity_id
        )
        for profile in self.config.profiles:
            for action in profile.actions:
                entities.update(condition_entities(action))
        return sorted(entities)

    def rule_entity_ids(self) -> list[str]:
        """Every entity an automatic rule reads (§9.4): people, and the one
        entity an ``entity`` rule watches."""
        return sorted(
            {
                entity_id
                for rule in self.config.rules
                if rule.enabled
                for entity_id in rule.trigger.entity_ids
            }
        )

    def auto_status(self) -> dict[str, Any]:
        """Automatic arming, as page 12 and the two entities read it (§9.4).

        Everything here comes off the state the engine produced or from
        ``core.rules``: the panel never recomputes what a rule would do, or
        it would be able to disagree with the engine that does it.
        """
        now = dt_util.utcnow()
        tz = dt_util.get_default_time_zone()
        upcoming = rules_engine.next_action(self.config, self.state, now, tz)
        return {
            "enabled": self.state.auto_arming,
            "allow_auto_disarm": self.config.settings.allow_auto_disarm,
            "next": _next_action_dict(upcoming),
            "pending": [
                {
                    "id": pending.id,
                    "rule_id": pending.rule_id,
                    "rule_name": pending.rule_name,
                    "action": pending.action.value,
                    "due": pending.due.isoformat(),
                    "started_at": pending.started_at.isoformat(),
                    "seconds": pending.seconds,
                    "scenario_id": pending.scenario_id,
                    "area_ids": list(pending.area_ids),
                    "suspension_name": pending.suspension_name,
                }
                for pending in self.state.pending_rules
            ],
            "suspensions": [
                _suspension_dict(suspension) for suspension in self.state.suspensions
            ],
            "blocked": {
                rule_id: runtime.blocked.value
                for rule_id, runtime in self.state.rules.items()
                if runtime.blocked is not None
            },
        }

    def health_status(self) -> dict[str, Any]:
        """Memoised for one round of updates (see ``_health_status``).

        Every entity that shows system health asks for this twice — once
        for its state and once for its attributes — and they all ask inside
        ``_notify()``, which runs on the alarm path between the trigger and
        the siren. Each call otherwise builds a fresh snapshot and a fresh
        entity-registry walk.
        """
        if self._health_at != self._revision or self._health_cache is None:
            self._health_cache = self._health_status()
            self._health_at = self._revision
        return self._health_cache

    def _health_status(self) -> dict[str, Any]:
        """System health, as page 14 and the two entities read it (§12, §13).

        Everything here comes off the state the engine produced or from
        ``core.health``: the panel never works out for itself whether a
        radio is being jammed, or it would be able to disagree with the
        engine that decides it.
        """
        now = dt_util.utcnow()
        snapshot = self._snapshot()
        state = self.state.health
        config = self.config.health
        contacts = {c.id: c.name for c in self.config.contacts}
        names = {z.id: z.name for z in self.config.zones}
        return {
            "now": now.isoformat(),
            # Zones that have been unreadable long enough to be worth a card
            # in Settings (§12.4). "Unreachable for days" is a different
            # fact from "in fault", which is true the instant an entity
            # blinks, and only the first one is somebody's to act on.
            "unreachable_zones": [
                {
                    "id": zone_id,
                    "name": names.get(zone_id, zone_id),
                    "since": since.isoformat(),
                    "days": int((now - since).total_seconds() // 86400),
                }
                for zone_id, since in sorted(state.quiet_since.items())
                if (now - since).total_seconds() >= config.repair_after
            ],
            "causes": [
                c.value for c in health_engine.causes(state, self.config, snapshot)
            ],
            "mains": {
                "entity_id": config.mains_entity_id,
                "lost_states": list(config.mains_lost_states),
                "state": (
                    snapshot.entity(config.mains_entity_id).state
                    if config.mains_entity_id
                    else None
                ),
                "lost": health_engine.mains_state(self.config, snapshot),
                "since": _iso(state.mains_lost_since),
            },
            "watchdog": {
                "enabled": config.watchdog.enabled,
                # Never the URL, for the reason core/dump.py states about
                # the diagnostics dump: it is the credential. This page is
                # open to anyone holding view_log; editing the URL goes
                # through foyer/config, which is edit_config.
                "url_set": bool(config.watchdog.url),
                "interval": config.watchdog.interval,
                "timeout": config.watchdog.timeout,
                "failures_allowed": config.watchdog.failures,
                "payload": config.watchdog.payload,
                "failures": state.watchdog.failures,
                "down_since": _iso(state.watchdog.down_since),
                "last_ok": _iso(state.watchdog.last_ok),
                "last_attempt": _iso(state.watchdog.last_attempt),
                "last_error": state.watchdog.last_error,
                "ever_ok": state.watchdog.ever_ok,
            },
            "channels": [
                {
                    "key": key,
                    "contact_id": contact.id,
                    "contact_name": contacts.get(contact.id, contact.id),
                    "channel_id": channel.id,
                    "kind": channel.kind.value,
                    "service": channel.service,
                    "fault": (
                        state.channel(key).fault.value
                        if state.channel(key).fault
                        else None
                    ),
                    "since": _iso(state.channel(key).since),
                    "failures": state.channel(key).failures,
                    "last_ok": _iso(state.channel(key).last_ok),
                    # A send, not a sweep. Foyer can see that a service
                    # exists; only a send proves it delivers, and a channel
                    # nobody has ever used is exactly the one somebody
                    # should press the test button on (§11.4).
                    "checked": state.channel(key).last_ok is not None,
                }
                for contact in self.config.contacts
                if contact.enabled
                for channel in contact.channels
                if channel.enabled
                for key in (f"{contact.id}:{channel.id}",)
            ],
            "radios": [
                {
                    "id": radio.id,
                    "name": radio.name,
                    "entry_id": radio.entry_id,
                    "coordinator_entity_id": radio.coordinator_entity_id,
                    "coordinator_state": (
                        snapshot.entity(radio.coordinator_entity_id).state
                        if radio.coordinator_entity_id
                        else None
                    ),
                    "enabled": radio.enabled,
                    "zones": len(health_engine.zones_on(self.config, snapshot, radio)),
                    "quiet": len(
                        health_engine.burst(
                            state.quiet_since,
                            health_engine.zones_on(self.config, snapshot, radio),
                            config.rf_window_of(radio),
                        )
                    ),
                    "threshold": config.rf_threshold(
                        radio, len(health_engine.zones_on(self.config, snapshot, radio))
                    ),
                    "window": config.rf_window_of(radio),
                    "suspected_since": _iso(state.radio(radio.id).suspected_since),
                    "confirmed": state.radio(radio.id).confirmed,
                    "coordinator_down_since": _iso(
                        state.radio(radio.id).coordinator_down_since
                    ),
                }
                for radio in config.radios
            ],
            "rf": {
                "zones": config.rf_zones,
                "window": config.rf_window,
                "confirm": config.rf_confirm,
            },
            "faults": sorted(self.state.faults),
            "repair_after": config.repair_after,
        }

    def radio_candidates(self) -> list[dict[str, Any]]:
        """Config entries that back at least one zone, for page 14's picker.

        A radio is a config entry (part 1 decision 7), so the honest way to
        offer them is to ask which entries the zones of this installation
        actually come from. An installation with everything on Wi-Fi sees an
        empty list, which is the true answer rather than a menu of
        integrations that are not radios.
        """
        registry = er.async_get(self.hass)
        counts: dict[str, int] = {}
        for zone in self.config.zones:
            entry = registry.async_get(zone.entity_id)
            if entry is not None and entry.config_entry_id:
                counts[entry.config_entry_id] = counts.get(entry.config_entry_id, 0) + 1
        out: list[dict[str, Any]] = []
        for entry_id, zones in counts.items():
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            out.append(
                {
                    "entry_id": entry_id,
                    "title": entry.title,
                    "domain": entry.domain,
                    "zones": zones,
                }
            )
        return sorted(out, key=lambda e: (-e["zones"], e["title"]))

    def snapshot(self) -> SystemSnapshot:
        """The world as the engine would be handed it, for whoever reads it.

        Public because the diagnostics dump needs one and building a second
        one would be a second answer to "what does Foyer see".
        """
        return self._snapshot()

    def _snapshot(
        self, overrides: Mapping[str, EntityState] | None = None
    ) -> SystemSnapshot:
        entities = {
            entity_id: entity_state(self.hass.states.get(entity_id))
            for entity_id in self.watched_entity_ids()
        }
        entities.update(overrides or {})
        return SystemSnapshot(
            self.state,
            entities,
            self.settling,
            dt_util.get_default_time_zone(),
            self.radio_map(),
        )

    def radio_map(self) -> dict[str, str]:
        """Which radio each entity sits on (§12.5): entity id -> Radio.id.

        Home Assistant has no general notion of a radio, and this is the
        closest honest thing there is: every entity of one ZHA, Z-Wave JS or
        Zigbee2MQTT installation shares that integration's config entry. The
        household names the entry once, on page 14, and forty zones assign
        themselves.

        It covers the coordinators and the entities actions target as well
        as the zones, because "do not notify over the affected radio" is
        decided in ``core`` and a lookup it was never handed is a lookup it
        cannot make (INV-1).
        """
        if self._radio_cache is not None:
            return self._radio_cache
        radios = {r.entry_id: r.id for r in self.config.health.radios if r.enabled}
        if not radios:
            self._radio_cache = {}
            return self._radio_cache
        registry = er.async_get(self.hass)
        out: dict[str, str] = {}
        for entity_id in self.radio_entity_ids():
            entry = registry.async_get(entity_id)
            if entry is not None and (radio := radios.get(entry.config_entry_id or "")):
                out[entity_id] = radio
        self._radio_cache = out
        return out

    def radio_entity_ids(self) -> list[str]:
        """Everything whose radio Foyer needs to know: the zones it counts,
        the coordinators it gates on, and every entity an action targets."""
        entities = {z.entity_id for z in self.config.zones}
        entities.update(
            r.coordinator_entity_id
            for r in self.config.health.radios
            if r.coordinator_entity_id
        )
        for profile in self.config.profiles:
            for action in profile.actions:
                target = action.params.get("entity_ids") or action.params.get(
                    "entity_id"
                )
                if isinstance(target, str):
                    entities.add(target)
                elif isinstance(target, list | tuple):
                    entities.update(str(t) for t in target)
        entities.update(t.entity_id for t in self.config.chime.targets)
        return sorted(e for e in entities if e)

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

    @property
    def stopped(self) -> bool:
        """Stopping, or stopped: its log is closing or closed."""
        return self._stopped

    @callback
    def async_notify_soon(self) -> None:
        """One notify on the next turn of the loop, however many ask for it."""
        if self._notify_pending:
            return
        self._notify_pending = True

        @callback
        def run() -> None:
            self._notify_pending = False
            if not self._stopped:
                self.async_notify()

        self.hass.loop.call_soon(run)

    def _notify(self) -> None:
        # One revision per round of updates: what the entities read is
        # computed once and shared, rather than rebuilt per entity per
        # property.
        self._revision += 1
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                # An entity whose property raises must cost that entity its
                # update and nothing else (found in review). Unguarded, it
                # took with it every entity after it in the list, the state
                # save that follows — INV-3 — and the log rows for the
                # decision that was being announced.
                _LOGGER.exception("Foyer could not update one of its entities")
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    # --- read model ----------------------------------------------------------

    def blockers(self, area_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
        # Once per round of updates and set of areas: every ready-to-arm
        # entity asked twice per notify, each time with a new snapshot
        # (second review).
        if self._blockers_rev != self._revision:
            self._blockers_rev = self._revision
            self._blockers_cache = {}
        key = tuple(area_ids)
        if key not in self._blockers_cache:
            self._blockers_cache[key] = arm_blockers(
                self._snapshot(), self.config, key, dt_util.utcnow()
            )
        return self._blockers_cache[key]

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
        simulation = simulate_run(
            self.config,
            request,
            snapshot.entities,
            carry=self.state,
            radios=snapshot.radios,
        )
        return simulation_dict(simulation, self.config)

    async def async_access_recovered(
        self,
        *,
        account: str,
        user_id: str | None,
        user_name: str | None,
        created: bool,
    ) -> None:
        """Say, everywhere, that an administrator recovered access (§8.2).

        A `security` row, a Home Assistant notification, and a message to
        every enabled contact over their first channel, through quiet hours
        like an alarm: the recovery is the one way round a code, and it must
        never be the quiet one (decision 109).
        """
        from . import notices

        now = dt_util.utcnow()
        self.async_record(
            (
                security_row(
                    now,
                    event_type=Moment.ACCESS_RECOVERED.value,
                    channel="ha_config",
                    user_id=user_id,
                    user_name=user_name,
                    outcome=Outcome.OK.value,
                    detail={"account": account, "created": str(created).lower()},
                ),
            )
        )
        strings = await self.hass.async_add_executor_job(
            i18n.load_strings, self.language
        )
        notices.async_create(
            self.hass,
            i18n.translate(
                strings, "notification.access_recovered.message", account=account
            ),
            title=i18n.translate(strings, "notification.access_recovered.title"),
            notification_id="foyer_access_recovered",
        )
        refs = [
            {"contact_id": c.id, "channel_id": None}
            for c in self.config.contacts
            if c.enabled
        ]
        recipients, quiet = recipients_for(
            self.config,
            refs,
            now,
            dt_util.get_default_time_zone(),
            Moment.ACCESS_RECOVERED,
        )
        if not recipients:
            return
        decision = Decision(
            at=now,
            accepted=True,
            state=self.state,
            actions=(
                ActionIntent(
                    action_id="access_recovered",
                    kind=ActionKind.NOTIFY.value,
                    moment=Moment.ACCESS_RECOVERED,
                    placeholders={"account": account},
                    params={"recipients": recipients, "quiet": quiet},
                ),
            ),
        )
        results = await self._executor.async_run(decision)
        self.async_record(_action_rows(decision, results))

    async def async_test_action(
        self,
        *,
        profile_id: str | None = None,
        action_id: str | None = None,
        service: str | None = None,
        contact_id: str | None = None,
        channel_id: str | None = None,
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
        if contact_id:
            # The other half of §11.4: the button beside a contact's channel.
            # It is the same call the real thing makes, through the same
            # path, with the same permission and the same code — so what is
            # proved is the channel and not a simplified version of it.
            contact = self.config.contact(contact_id)
            channel = contact.channel(channel_id) if contact else None
            if contact is None or channel is None:
                return {"success": False, "reason": "unknown_contact"}
            intent = contact_test_intent(
                contact, channel, message or await self._async_test_message()
            )
        elif service:
            # A test of a channel with nothing to say is a message of one
            # empty line, which several transports refuse outright — and a
            # test that fails for that reason teaches nothing about the
            # channel. The words are the runtime's to choose, in the
            # language Foyer speaks (§15.1), because ``core`` writes none.
            intent = notify_test_intent(
                service, message or await self._async_test_message()
            )
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
            if (
                built.kind == ActionKind.NOTIFY.value
                and not built.params.get("service")
                and not built.params.get("recipients")
            ):
                # It names contacts and every one of them is disabled, or has
                # no channel left. Sending it would fail with "not a notify
                # service: ''", which answers a different question from the
                # one the button asked.
                return {"success": False, "reason": "no_recipients"}
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

    async def _async_test_message(self) -> str:
        """What a test notification says, in the language Foyer speaks
        (§15.1). The words are the runtime's: ``core`` writes none."""
        strings = await self.hass.async_add_executor_job(
            i18n.load_strings, self.language
        )
        return i18n.translate(strings, "notification.action_tested.message")

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
            # Automatic arming (§9.4). On the live status rather than only on
            # page 12, because a countdown is something the card has to be
            # able to show and stop: two minutes is not long enough to go and
            # find the right page.
            "auto": self.auto_status(),
            "master": {
                "state": master.value,
                "mode": mode,
                "entity_id": self.master_entity_id,
            },
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
            # The endpoint keypads whose last request arrived unencrypted
            # (§9.2.1), for page 8's permanent warning.
            "devices_in_clear": sorted(self.state.in_clear),
            "security": self.security_status(me, now, getattr(ha_user, "id", None)),
        }

    def security_status(
        self, me: User | None, now: datetime, ha_user_id: str | None = None
    ) -> dict[str, Any]:
        """What the panel and the card need to know about codes (§8.2, §8.4).

        No code, no hash and no name of anybody else: who is connected already
        knows who they are, and everything here is about them.
        """
        # The counter of the account asking: the panel's failures count per
        # Home Assistant account (second review, decision 1).
        locked = self.state.lockouts.get(
            f"{CHANNEL_HA_UI}:@{ha_user_id}" if ha_user_id else f"{CHANNEL_HA_UI}:"
        )
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
