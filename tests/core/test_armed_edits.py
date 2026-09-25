"""An armed house keeps the answer and the codes it was armed with (pure).

SPEC §15.1, decisions 138 and 139. While any area is not disarmed, an edit
that changes how the house answers an alarm, or what it asks a code for, is
refused; who may command the house stays editable, except an edit that
would leave nobody holding a usable code.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from datetime import timedelta
import typing

import pytest

from custom_components.foyer.core.models import (
    ActionKind,
    AreaState,
    ArmingDevice,
    ArmPolicy,
    Channel,
    CodePolicy,
    CodeResult,
    Contact,
    ContactChannel,
    Contributor,
    DeviceKind,
    DeviceTransport,
    Escalation,
    EscalationKind,
    FoyerConfig,
    Group,
    HealthSettings,
    Incident,
    KeyAction,
    KeyCommand,
    Moment,
    MqttSettings,
    ProfileAction,
    Radio,
    ResponseProfile,
    RuntimeState,
    ZoneType,
)
from custom_components.foyer.core.validation import (
    FREE_WHILE_ARMED,
    KEPT_WHILE_ARMED,
    Problem,
    edit_conflicts,
)
from custom_components.foyer.store.editing import (
    delete,
    set_device_token,
    update_chime,
    update_health,
    update_security,
    update_settings,
    upsert,
)
from custom_components.foyer.store.schema import (
    chime_to_dict,
    health_to_dict,
    settings_to_dict,
)

from .helpers import NOW, World, make_house, rule, user, zone


def armed(config: FoyerConfig | None = None) -> World:
    """The ground floor armed by Night; upstairs and the garage disarmed."""
    world = World(config)
    night = world.config.scenario("night")
    # A scenario limited to some people is armed by one of them, with a code:
    # a request that establishes nobody cannot use it.
    who = (
        {"user_id": "luca", "code": CodeResult.VALID}
        if night is not None and night.allowed_user_ids is not None
        else {}
    )
    world.arm("night", **who)
    assert world.area("ground").state is not AreaState.DISARMED
    return world


def disarmed(world: World) -> World:
    """Every area disarmed, with Luca's code where the policy asks one."""
    world.disarm(code=CodeResult.VALID, user_id="luca")
    assert all(rt.state is AreaState.DISARMED for rt in world.state.areas.values())
    return world


def codes(problems) -> list[str]:
    return [p.code for p in problems]


# --- every setting is classified (§19) ----------------------------------------------


def _paths(cls: type, prefix: str, classified: set[str]) -> list[str]:
    """Every field under ``prefix``, down to the first path the tables name.

    A nested block the tables do not name as a whole is walked into, so a
    field added to it is unclassified until somebody says which side it is
    on; a leaf nobody named is returned as it is, and fails the test.
    """
    hints = typing.get_type_hints(cls)
    out = []
    for f in fields(cls):
        path = f"{prefix}.{f.name}" if prefix else f.name
        kind = hints[f.name]
        if path not in classified and is_dataclass(kind):
            out.extend(_paths(kind, path, classified))
        else:
            out.append(path)
    return out


# The lists of things a household creates, each with a guard of its own: the
# armed areas and their zones and groups, the running scenario, the profiles
# in use and their contacts, the last usable code among the people. Only
# these are left out of the walk; a new block of settings on the
# configuration is walked into like any other.
COLLECTIONS = frozenset(
    {
        "areas",
        "zones",
        "scenarios",
        "profiles",
        "groups",
        "users",
        "devices",
        "contacts",
        "rules",
    }
)


def test_every_global_setting_is_kept_while_armed_or_free():
    """A setting added later cannot arrive unclassified: it has to be put on
    one side, by whoever adds it, rather than landing on the free side
    because nobody thought of it — a new field of the settings, or a new
    block of them on the configuration itself."""
    kept, free = set(KEPT_WHILE_ARMED), set(FREE_WHILE_ARMED)
    assert len(kept) == len(KEPT_WHILE_ARMED) and len(free) == len(FREE_WHILE_ARMED)
    assert not kept & free
    classified = kept | free
    assert {f.name for f in fields(FoyerConfig)} >= COLLECTIONS
    every = [p for p in _paths(FoyerConfig, "", classified) if p not in COLLECTIONS]
    assert not set(every) - classified, set(every) - classified
    # The code policy and the chime are whole blocks of the configuration.
    assert "code_policy" in kept and "chime" in free
    # Every path the tables name exists: a renamed field would otherwise be
    # guarded under a name nothing has.
    assert classified <= set(every), classified - set(every)


# --- what an armed house keeps ------------------------------------------------------


def _settings(**changes):
    return lambda c: replace(c, settings=replace(c.settings, **changes))


def _security(**changes):
    return lambda c: replace(
        c,
        settings=replace(c.settings, security=replace(c.settings.security, **changes)),
    )


def _health(**changes):
    return lambda c: replace(c, health=replace(c.health, **changes))


QUIET = ResponseProfile("quiet", "Quiet")

KEPT_CHANGES = {
    "settings.siren_duration": _settings(siren_duration=60),
    "settings.arm_hold_timeout": _settings(arm_hold_timeout=60),
    "settings.default_entry_delay": _settings(default_entry_delay=0),
    "settings.default_exit_delay": _settings(default_exit_delay=0),
    "settings.walk_test_timeout": _settings(walk_test_timeout=3600),
    "settings.default_profile_id": _settings(default_profile_id="quiet"),
    "settings.technical_profile_id": _settings(technical_profile_id="quiet"),
    "settings.silent_suppresses": _settings(silent_suppresses=()),
    "settings.camera_dir": _settings(camera_dir="media/elsewhere"),
    "settings.allow_auto_disarm": _settings(allow_auto_disarm=True),
    "code_policy": lambda c: replace(
        c, code_policy=replace(c.code_policy, disarm=False)
    ),
    "settings.security.code_length": _security(code_length=4),
    "settings.security.lockout_failures": _security(lockout_failures=50),
    "settings.security.lockout_window": _security(lockout_window=30),
    "settings.security.lockout_duration": _security(lockout_duration=30),
    "health.radios": _health(radios=(Radio("zigbee", "Zigbee", entry_id="zha1"),)),
    "health.rf_zones": _health(rf_zones=20),
    "health.rf_window": _health(rf_window=5),
    "health.rf_confirm": _health(rf_confirm=600),
}


def _house() -> FoyerConfig:
    config = make_house()
    return replace(config, profiles=(*config.profiles, QUIET))


def test_every_kept_setting_has_a_change_below():
    assert set(KEPT_CHANGES) == set(KEPT_WHILE_ARMED)


@pytest.mark.parametrize("path", KEPT_WHILE_ARMED)
def test_a_kept_setting_is_refused_while_an_area_is_armed(path):
    """Otherwise whoever holds edit_config could lower the guard of a house
    nobody disarmed — a shorter siren, no code to disarm, a lockout that
    never locks — and the log would show no disarm."""
    world = armed(_house())
    new = KEPT_CHANGES[path](world.config)
    assert new != world.config
    kind = "health" if path.startswith("health.") else "settings"
    field = path.rsplit(".", 1)[-1]
    assert edit_conflicts(world.config, new, world.state, now=world.now) == [
        Problem("armed_setting", kind, None, field)
    ]


@pytest.mark.parametrize("path", KEPT_WHILE_ARMED)
def test_a_kept_setting_is_accepted_once_every_area_is_disarmed(path):
    world = disarmed(armed(_house()))
    new = KEPT_CHANGES[path](world.config)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_the_code_policy_is_kept_raised_as_well_as_lowered():
    """What the house asks a code for, in both directions: a policy raised
    under an armed house is a house that suddenly cannot be armed or
    acknowledged the way it was a minute ago."""
    world = armed()
    raised = replace(world.config, code_policy=CodePolicy(arm=True, acknowledge=True))
    assert codes(edit_conflicts(world.config, raised, world.state)) == ["armed_setting"]


@pytest.mark.parametrize(
    "field_name", ["require_code_to_arm", "require_code_to_disarm"]
)
@pytest.mark.parametrize("value", [False, True])
def test_a_code_setting_of_a_disarmed_area_or_idle_scenario_is_kept(field_name, value):
    """Decision 142: the garage is disarmed and Away is not running, but both
    take part in the strictest-wins resolution of a command that touches the
    armed ground floor; lowering either opened it without a code."""
    world = armed()
    for kind, item_id in (("areas", "garage"), ("scenarios", "away")):
        changed = replace(
            world.config,
            **{
                kind: tuple(
                    replace(o, **{field_name: value}) if o.id == item_id else o
                    for o in getattr(world.config, kind)
                )
            },
        )
        problems = edit_conflicts(world.config, changed, world.state, now=world.now)
        assert [(p.code, p.ref, p.field) for p in problems] == [
            ("armed_code_policy", item_id, field_name)
        ]
        disarmed_world = disarmed(armed())
        assert (
            edit_conflicts(
                disarmed_world.config, changed, disarmed_world.state, now=world.now
            )
            == []
        )


# --- what stays free -----------------------------------------------------------------


FREE_CHANGES = {
    "settings.language": _settings(language="it"),
    "settings.log": _settings(
        log=replace(make_house().settings.log, pseudonymise_after=30)
    ),
    "settings.wizard_done": _settings(wizard_done=True),
    "settings.low_battery_threshold": _settings(low_battery_threshold=40),
    "chime": lambda c: replace(c, chime=replace(c.chime, during_exit=True)),
    "settings.mqtt": _settings(mqtt=MqttSettings(enabled=True)),
    "settings.ack_webhook_id": _settings(ack_webhook_id="a" * 64),
    "health.mains_entity_id": _health(mains_entity_id="binary_sensor.ups"),
    "health.mains_lost_states": _health(mains_lost_states=("off",)),
    "health.mains_mode": _health(mains_mode="outside_ups"),
    "health.mains_outside_entity_ids": _health(
        mains_outside_entity_ids=("switch.fridge_plug",)
    ),
    "health.mains_outside_delay": _health(mains_outside_delay=300),
    "health.startup_grace": _health(startup_grace=60),
    "health.watchdog": _health(
        watchdog=replace(HealthSettings().watchdog, payload=True, interval=600)
    ),
    "health.channel_sweep": _health(channel_sweep=1800),
    "health.channel_failures": _health(channel_failures=5),
    "health.repair_after": _health(repair_after=7200),
}


def test_every_free_setting_has_a_change_below():
    assert set(FREE_CHANGES) == set(FREE_WHILE_ARMED)


@pytest.mark.parametrize("path", FREE_WHILE_ARMED)
def test_a_free_setting_is_accepted_while_an_area_is_armed(path):
    """The language of messages, the log, privacy, the chime, the mains, the
    watchdog and the channel checks change nothing about the answer."""
    world = armed()
    new = FREE_CHANGES[path](world.config)
    assert new != world.config
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


# --- through the store, as the panel reaches it -------------------------------------


def test_a_settings_save_is_refused_field_by_field_while_armed():
    world = armed()
    result = update_settings(
        world.config,
        world.state,
        {"siren_duration": 60, "arm_hold_timeout": 300, "language": "it"},
        now=world.now,
    )
    assert result.config is None
    assert result.problems == (
        Problem("armed_setting", "settings", None, "siren_duration"),
    )


def test_a_settings_save_that_changes_only_what_is_free_is_accepted_while_armed():
    world = armed()
    stored = settings_to_dict(world.config.settings)
    result = update_settings(
        world.config,
        world.state,
        {**stored, "language": "it", "wizard_done": True},
        now=world.now,
    )
    assert result.problems == ()
    assert result.config.settings.language == "it"


def test_the_acknowledgement_webhook_can_be_switched_on_and_off_while_armed():
    """foyer/ack_webhook sends the whole settings block back unchanged, plus
    the one field it owns: the round trip must not read as a change to the
    siren or the delays."""
    world = armed()
    stored = settings_to_dict(world.config.settings)
    on = update_settings(
        world.config, world.state, stored, webhook_id="b" * 64, now=world.now
    )
    assert on.problems == ()
    off = update_settings(on.config, world.state, stored, webhook_id=None)
    assert off.problems == ()
    assert off.config.settings.ack_webhook_id is None


def test_the_code_policy_and_the_lockout_are_refused_through_page_7_while_armed():
    world = armed()
    security = {
        "code_length": 6,
        "lockout_failures": 5,
        "lockout_window": 300,
        "lockout_duration": 300,
    }
    lowered = update_security(
        world.config,
        world.state,
        {"code_policy": {"disarm": False}, "security": security},
        now=world.now,
    )
    assert lowered.problems == (
        Problem("armed_setting", "settings", None, "code_policy"),
    )
    longer = update_security(
        world.config,
        world.state,
        {"code_policy": {}, "security": {**security, "code_length": 8}},
        now=world.now,
    )
    assert longer.problems == (
        Problem("armed_setting", "settings", None, "code_length"),
    )
    unchanged = update_security(
        world.config, world.state, {"code_policy": {}, "security": security}
    )
    assert unchanged.problems == ()


def test_the_radios_are_refused_and_the_watchdog_is_free_through_page_14():
    world = armed()
    stored = health_to_dict(world.config.health)
    radios = update_health(
        world.config, world.state, {**stored, "rf_zones": 6}, now=world.now
    )
    assert radios.problems == (Problem("armed_setting", "health", None, "rf_zones"),)
    watchdog = update_health(
        world.config,
        world.state,
        {
            **stored,
            "mains_entity_id": "binary_sensor.ups",
            "watchdog": {**stored["watchdog"], "payload": True},
        },
        now=world.now,
    )
    assert watchdog.problems == ()
    assert watchdog.config.health.watchdog.payload is True


def test_the_chime_is_free_while_armed():
    world = armed()
    result = update_chime(
        world.config,
        world.state,
        {
            **chime_to_dict(world.config.chime),
            "targets": [{"entity_id": "siren.hall"}],
            "during_exit": True,
        },
        now=world.now,
    )
    assert result.problems == ()
    assert result.config.chime.during_exit is True


# --- the profiles in use -------------------------------------------------------------


def _profile(profile_id: str, *actions: ProfileAction) -> ResponseProfile:
    return ResponseProfile(profile_id, profile_id.capitalize(), actions=actions)


def _louder(config: FoyerConfig, profile_id: str) -> FoyerConfig:
    """The same profile with a higher severity: a change to what it does."""
    return replace(
        config,
        profiles=tuple(
            replace(p, severity=p.severity + 1) if p.id == profile_id else p
            for p in config.profiles
        ),
    )


def _with_profiles(config: FoyerConfig, *ids: str) -> FoyerConfig:
    return replace(config, profiles=(*config.profiles, *(_profile(i) for i in ids)))


def _area(config: FoyerConfig, area_id: str, **changes) -> FoyerConfig:
    return replace(
        config,
        areas=tuple(
            replace(a, **changes) if a.id == area_id else a for a in config.areas
        ),
    )


def _zone(config: FoyerConfig, zone_id: str, **changes) -> FoyerConfig:
    return replace(
        config,
        zones=tuple(
            replace(z, **changes) if z.id == zone_id else z for z in config.zones
        ),
    )


def _scenario(config: FoyerConfig, scenario_id: str, **changes) -> FoyerConfig:
    return replace(
        config,
        scenarios=tuple(
            replace(s, **changes) if s.id == scenario_id else s
            for s in config.scenarios
        ),
    )


TECHNICAL = zone(
    "smoke",
    "binary_sensor.smoke",
    "upstairs",  # disarmed under Night
    type=ZoneType.TECHNICAL,
    channel=Channel.TECHNICAL,
    always_on=True,
    bypassable=False,
    response_profile_id="smoke_profile",
)


def _in_use_house() -> FoyerConfig:
    """One profile for each way an armed ground floor could answer."""
    config = _with_profiles(
        make_house(),
        "ground_profile",
        "night_profile",
        "window_profile",
        "group_profile",
        "group_area_profile",
        "technical_profile",
        "smoke_profile",
        "escalation_profile",
        "incident_profile",
        "upstairs_profile",
        "spare",
    )
    config = _area(config, "ground", response_profile_id="ground_profile")
    config = _area(config, "garage", response_profile_id="group_area_profile")
    config = _area(config, "upstairs", response_profile_id="upstairs_profile")
    config = _scenario(config, "night", response_profile_id="night_profile")
    config = _zone(config, "window", response_profile_id="window_profile")
    config = replace(
        config,
        zones=(*config.zones, TECHNICAL),
        groups=(
            Group(
                "loud",
                "Loud",
                "upstairs",
                ("hall", "bath"),
                2,
                response_profile_id="group_profile",
            ),
            # No profile of its own: it answers with the garage's chain.
            Group("plain", "Plain", "garage", ("door", "landing"), 2),
        ),
        settings=replace(config.settings, technical_profile_id="technical_profile"),
    )
    return config


def _running(state: RuntimeState) -> RuntimeState:
    return replace(
        state,
        escalations=(
            Escalation(
                kind=EscalationKind.TECHNICAL,
                profile_id="escalation_profile",
                moment=Moment.TECHNICAL_RAISED,
                started_at=NOW,
            ),
        ),
        incident=Incident(
            "i1",
            NOW,
            contributors=(
                Contributor("ground", "window", NOW, profile_id="incident_profile"),
            ),
        ),
    )


@pytest.mark.parametrize(
    "profile_id",
    [
        "default",  # the end of every chain
        "ground_profile",  # the armed area's own
        "night_profile",  # the running scenario's
        "window_profile",  # a zone of the armed area
        "group_profile",  # a group with a member in the armed area
        "group_area_profile",  # a group with none, answering with its area's
        "technical_profile",  # the technical channel's
        "smoke_profile",  # a technical zone's, in a disarmed area
        "escalation_profile",  # what an escalation is running on
        "incident_profile",  # what a contributor joined with
    ],
)
def test_a_profile_the_house_could_answer_with_is_refused_while_armed(profile_id):
    world = armed(_in_use_house())
    state = _running(world.state)
    new = _louder(world.config, profile_id)
    assert edit_conflicts(world.config, new, state, now=world.now) == [
        Problem("profile_armed", "profile", profile_id)
    ]
    # And accepted once every area is disarmed, the escalation and the
    # incident still running: they alone do not freeze it (§19).
    disarmed(world)
    state = _running(world.state)
    assert edit_conflicts(world.config, new, state, now=world.now) == []


@pytest.mark.parametrize("profile_id", ["upstairs_profile", "spare"])
def test_a_profile_nothing_armed_could_answer_with_stays_free(profile_id):
    """Upstairs is disarmed under Night: its own profile may be edited."""
    world = armed(_in_use_house())
    new = _louder(world.config, profile_id)
    assert edit_conflicts(world.config, new, _running(world.state)) == []


def test_with_every_area_disarmed_nothing_running_freezes_a_profile():
    """The technical channel is live whatever the arming state, but on its
    own it does not freeze the configuration: with every area disarmed the
    profiles of a technical escalation stay editable."""
    world = World(_in_use_house())
    state = _running(world.state)
    for profile_id in ("technical_profile", "smoke_profile", "escalation_profile"):
        new = _louder(world.config, profile_id)
        assert edit_conflicts(world.config, new, state, now=world.now) == []


def test_a_profile_is_refused_through_the_store_while_armed():
    world = armed(_in_use_house())
    result = upsert(
        world.config,
        world.state,
        "profile",
        {"id": "ground_profile", "name": "Ground", "severity": 3, "actions": []},
        now=world.now,
    )
    assert codes(result.problems) == ["profile_armed"]


# --- the contacts those profiles name (§7.1) ----------------------------------------


LUCA = Contact(
    "luca",
    "Luca",
    channels=(
        ContactChannel("push", service="notify.mobile_app_luca"),
        ContactChannel("sms", service="notify.sms", target="+390000000"),
    ),
)
NEIGHBOUR = Contact(
    "neighbour", "Neighbour", channels=(ContactChannel("sms", service="notify.sms"),)
)
PLUMBER = Contact(
    "plumber", "Plumber", channels=(ContactChannel("sms", service="notify.sms"),)
)


def _notify(action_id: str, *contacts, offset: int | None = None) -> ProfileAction:
    return ProfileAction(
        action_id,
        ActionKind.NOTIFY,
        frozenset({Moment.TRIGGERED}),
        params={"message": "Alarm", "contacts": list(contacts)},
        escalation_offset=offset,
    )


def _contact_house() -> FoyerConfig:
    config = make_house()
    return replace(
        config,
        contacts=(LUCA, NEIGHBOUR, PLUMBER),
        profiles=(
            *config.profiles,
            # The armed ground floor answers with this one: Luca at once, the
            # neighbour as an escalation step two minutes later.
            _profile(
                "ground_profile",
                _notify("now", {"contact_id": "luca", "channel_id": "push"}),
                _notify("step", "neighbour", offset=120),
            ),
            # Upstairs is disarmed under Night.
            _profile("upstairs_profile", _notify("plumber", "plumber")),
        ),
        areas=tuple(
            replace(a, response_profile_id=f"{a.id}_profile")
            if a.id in ("ground", "upstairs")
            else a
            for a in config.areas
        ),
        rules=(rule(notify_contact_ids=("plumber",)),),
    )


def _contact(config: FoyerConfig, contact: Contact | None, contact_id: str):
    kept = tuple(c for c in config.contacts if c.id != contact_id)
    return replace(config, contacts=(*kept, contact) if contact else kept)


@pytest.mark.parametrize(
    ("contact_id", "change"),
    [
        # Switched off, deleted, a channel switched off or removed: a
        # notification naming none, or one switched off, goes over the
        # first enabled channel, so every channel counts.
        ("luca", lambda c: replace(c, enabled=False)),
        ("luca", lambda c: None),
        (
            "luca",
            lambda c: replace(
                c, channels=(c.channels[0], replace(c.channels[1], enabled=False))
            ),
        ),
        ("luca", lambda c: replace(c, channels=c.channels[:1])),
        # The number, the service, the quiet hours and the person it is
        # linked to all decide who hears the alarm.
        (
            "luca",
            lambda c: replace(
                c, channels=(c.channels[0], replace(c.channels[1], target="+391111"))
            ),
        ),
        ("luca", lambda c: replace(c, quiet_start="22:00", quiet_end="07:00")),
        ("luca", lambda c: replace(c, linked_user_id="luca")),
        ("luca", lambda c: replace(c, name="Luca C.")),
        # An escalation step names its contact as much as a notification.
        ("neighbour", lambda c: replace(c, enabled=False)),
    ],
)
def test_a_contact_a_profile_in_use_names_is_refused_while_armed(contact_id, change):
    world = armed(_contact_house())
    before = world.config.contact(contact_id)
    new = _contact(world.config, change(before), contact_id)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == [
        Problem("contact_armed", "contact", contact_id)
    ]
    disarmed(world)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_a_contact_only_a_disarmed_area_or_a_rule_names_stays_free():
    """The plumber is on the disarmed upstairs profile and on a rule. A
    rule's contacts hear the rule, not the alarm."""
    world = armed(_contact_house())
    plumber = world.config.contact("plumber")
    new = _contact(world.config, replace(plumber, enabled=False), "plumber")
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_saving_an_unchanged_contact_in_use_is_accepted_while_armed():
    world = armed(_contact_house())
    new = _contact(world.config, world.config.contact("luca"), "luca")
    assert edit_conflicts(world.config, new, world.state) == []


def test_a_contact_in_use_is_refused_through_the_store_while_armed():
    world = armed(_contact_house())
    item = {
        "id": "luca",
        "name": "Luca",
        "channels": [
            {"id": "push", "service": "notify.mobile_app_luca"},
            {"id": "sms", "service": "notify.sms", "target": "+390000000"},
        ],
        "enabled": False,
    }
    result = upsert(world.config, world.state, "contact", item, now=world.now)
    assert codes(result.problems) == ["contact_armed"]


# --- who may command the house stays free (decision 139) ----------------------------


def _people_house() -> FoyerConfig:
    config = replace(
        make_house(),
        users=(
            user("luca", "Luca", ha_user_id="ha-luca"),
            user("guest", "Guest"),
        ),
    )
    return replace(
        config,
        scenarios=tuple(
            replace(s, allowed_user_ids=("luca", "guest")) if s.id == "night" else s
            for s in config.scenarios
        ),
        zones=(
            *config.zones,
            zone(
                "key",
                "input_boolean.key_switch",
                "ground",
                type=ZoneType.KEY,
                channel=Channel.KEY,
                arm_policy=ArmPolicy.IGNORE,
                key=KeyAction(KeyCommand.DISARM, user_id="guest"),
            ),
        ),
        devices=(
            ArmingDevice(
                "hall",
                "Hall keypad",
                DeviceKind.KEYPAD,
                ref="hall",
                transport=DeviceTransport.HTTP,
                token_hash="c" * 64,
            ),
        ),
    )


def _user(config: FoyerConfig, user_id: str, **changes) -> FoyerConfig:
    return replace(
        config,
        users=tuple(
            replace(u, **changes) if u.id == user_id else u for u in config.users
        ),
    )


@pytest.mark.parametrize(
    "change",
    [
        # Taking a guest's code away from the other side of the world.
        lambda c: _user(c, "guest", code_hash=None),
        lambda c: _user(c, "guest", enabled=False),
        lambda c: _user(c, "guest", valid_until=NOW - timedelta(days=1)),
        # And giving somebody one, or more permissions, or the exemption.
        lambda c: replace(c, users=(*c.users, user("partner", "Partner"))),
        lambda c: _user(c, "guest", permissions=frozenset({"arm"})),
        lambda c: _user(c, "luca", code_exempt_when_identified=True),
        # Tags, keypads, tokens, scopes and the automatic rules.
        lambda c: replace(
            c, devices=(replace(c.devices[0], scopes=frozenset({"status", "zones"})),)
        ),
        lambda c: replace(c, devices=(replace(c.devices[0], enabled=False),)),
        lambda c: replace(c, rules=(rule(),)),
    ],
)
def test_who_may_command_the_house_stays_editable_while_armed(change):
    world = armed(_people_house())
    new = change(world.config)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_revoking_a_keypad_token_and_deleting_a_person_are_accepted_while_armed():
    world = armed(_people_house())
    revoked = set_device_token(world.config, world.state, "hall", None, now=world.now)
    assert revoked.problems == ()
    config = replace(
        world.config,
        zones=tuple(z for z in world.config.zones if z.id != "key"),
        scenarios=tuple(
            replace(s, allowed_user_ids=None) for s in world.config.scenarios
        ),
    )
    removed = delete(config, world.state, "user", "guest", now=world.now)
    assert removed.problems == ()


def test_a_key_switchs_person_and_a_running_scenarios_people_wait_for_the_disarm():
    """They belong to the zone and the scenario, which wait; the person
    themselves can be switched off at once."""
    world = armed(_people_house())
    key = world.config.zone("key")
    new_key = _zone(world.config, "key", key=replace(key.key, user_id="luca"))
    assert codes(edit_conflicts(world.config, new_key, world.state)) == [
        "area_not_disarmed"
    ]
    fewer = _scenario(world.config, "night", allowed_user_ids=("luca",))
    assert codes(edit_conflicts(world.config, fewer, world.state)) == [
        "scenario_active"
    ]
    disabled = _user(world.config, "guest", enabled=False)
    assert edit_conflicts(world.config, disabled, world.state, now=world.now) == []


# --- nobody left with a usable code -------------------------------------------------


@pytest.mark.parametrize(
    "change",
    [
        lambda c: _user(_user(c, "guest", enabled=False), "luca", code_hash=None),
        lambda c: _user(_user(c, "guest", code_hash=None), "luca", enabled=False),
        lambda c: replace(c, users=()),
        lambda c: _user(
            _user(c, "guest", code_hash=None),
            "luca",
            valid_until=NOW - timedelta(minutes=1),
        ),
    ],
)
def test_an_edit_leaving_nobody_with_a_usable_code_is_refused_while_armed(change):
    """With nobody holding a code, §8.2 switches the whole policy off: a
    house armed asking for a code to disarm is disarmed with one."""
    world = armed(_people_house())
    new = change(world.config)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == [
        Problem("last_usable_code", "user")
    ]
    disarmed(world)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_a_code_nobody_can_use_does_not_count_as_the_last_one():
    """Usable is read at the time given: a guest whose window has closed
    holds a code that verifies nothing, so revoking Luca's is the last."""
    world = armed(_user(_people_house(), "guest", valid_until=NOW - timedelta(days=1)))
    new = _user(world.config, "luca", code_hash=None)
    assert codes(edit_conflicts(world.config, new, world.state, now=world.now)) == [
        "last_usable_code"
    ]


@pytest.mark.parametrize(
    ("guest", "change"),
    [
        # A minute from now on the last person who holds one ...
        (
            {"code_hash": None},
            lambda c, now: _user(c, "luca", valid_until=now + timedelta(minutes=1)),
        ),
        # ... or the last open-ended code revoked, with a guest's week left.
        (
            {"valid_until": NOW + timedelta(days=7)},
            lambda c, now: _user(c, "luca", code_hash=None),
        ),
    ],
)
def test_an_edit_leaving_nobody_with_a_usable_code_later_is_refused_while_armed(
    guest, change
):
    """Usable now is not enough: a window ending a minute after the save
    passes a check made at the save, and a minute later the policy is off
    and a codeless disarm is accepted (third review). The edit may not
    bring nearer the moment nobody holds a usable code."""
    world = armed(_user(_people_house(), "guest", **guest))
    new = change(world.config, world.now)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == [
        Problem("last_usable_code", "user")
    ]
    disarmed(world)
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_a_window_that_moves_nothing_nearer_is_accepted_while_armed():
    """A guest's window shortened while an open-ended code remains: nobody
    runs out of codes any sooner. A window lengthened on the last usable
    person pushes that moment further away, and an edit that leaves it
    where it was moves nothing."""
    world = armed(_user(_people_house(), "guest", valid_until=NOW + timedelta(days=7)))
    now = world.now
    shorter = _user(world.config, "guest", valid_until=now + timedelta(minutes=1))
    assert edit_conflicts(world.config, shorter, world.state, now=now) == []
    alone = armed(
        replace(
            make_house(),
            users=(user("luca", "Luca", valid_until=NOW + timedelta(days=1)),),
        )
    )
    longer = _user(alone.config, "luca", valid_until=None)
    assert edit_conflicts(alone.config, longer, alone.state, now=alone.now) == []
    renamed = _user(alone.config, "luca", name="Luca C.")
    assert edit_conflicts(alone.config, renamed, alone.state, now=alone.now) == []


def test_a_house_that_had_no_usable_code_is_not_refused_for_having_none():
    world = armed(replace(make_house(), users=(user("luca", "Luca", code_hash=None),)))
    new = _user(world.config, "luca", name="Luca C.")
    assert edit_conflicts(world.config, new, world.state, now=world.now) == []


def test_removing_the_last_code_is_refused_through_the_store_while_armed():
    world = armed(replace(make_house(), users=(user("luca", "Luca"),)))
    result = upsert(
        world.config,
        world.state,
        "user",
        {"id": "luca", "name": "Luca", "code_hash": None, "permissions": ["arm"]},
        now=world.now,
    )
    assert codes(result.problems) == ["last_usable_code"]


def test_the_recovery_shape_of_edit_is_accepted_while_armed():
    """The Configure step's recovery enables a person, removes their window
    and sets a code (§8.2): it can never leave the house with nobody holding
    one, so an armed house never refuses it."""
    lapsed = user(
        "luca",
        "Luca",
        enabled=False,
        valid_until=NOW - timedelta(days=1),
        ha_user_id="ha-luca",
    )
    world = armed(replace(make_house(), users=(lapsed,)))
    result = upsert(
        world.config,
        world.state,
        "user",
        {
            "id": "luca",
            "name": "Luca",
            "ha_user_id": "ha-luca",
            "code_hash": "$2b$12$recovered",
            "permissions": ["arm", "disarm"],
            "enabled": True,
            "valid_until": None,
        },
        now=world.now,
    )
    assert result.problems == ()
