"""The Alarmo importer (SPEC §20.2): a best-effort translation that says no.

**The fixtures here are written by hand**, from the shape Alarmo 1.10.19's
own ``store.py`` writes (see the docstring of ``store/alarmo.py``, which
records the version, the commit and the date it was read). They were not
captured from a real installation, and nothing here claims they were: a
field Alarmo writes that the source did not show would be absent from them
too. What they do pin is every decision the importer makes about the shape it
was written against.
"""

from __future__ import annotations

from dataclasses import replace
import itertools

import pytest

from custom_components.foyer.core.models import (
    ActionKind,
    ArmPolicy,
    Channel,
    EntryMode,
    Moment,
    RuntimeState,
    User,
    ZoneType,
)
from custom_components.foyer.core.validation import edit_conflicts, validate
from custom_components.foyer.store.alarmo import (
    EntityInfo,
    Labels,
    Refused,
    plan,
)
from custom_components.foyer.store.seed import seed_config


def ids():
    counter = itertools.count()
    return lambda: f"id{next(counter)}"


def mode(enabled=True, exit_time=None, entry_time=None, trigger_time=None):
    return {
        "enabled": enabled,
        "exit_time": exit_time,
        "entry_time": entry_time,
        "trigger_time": trigger_time,
    }


def sensor(entity_id, sensor_type="door", modes=("armed_away",), **extra):
    """A sensor as Alarmo's SensorEntry writes it, defaults included."""
    return {
        "entity_id": entity_id,
        "type": sensor_type,
        "modes": list(modes),
        "use_exit_delay": True,
        "use_entry_delay": True,
        "always_on": False,
        "arm_on_close": False,
        "allow_open": False,
        "trigger_unavailable": False,
        "auto_bypass": False,
        "auto_bypass_modes": [],
        "area": "1705934512",
        "enabled": True,
        "entry_delay": None,
        "delay_on": None,
        **extra,
    }


ALL = ("armed_away", "armed_home", "armed_night")


def alarmo_file(**overrides):
    """One area, three modes, the sensors a real house has."""
    data = {
        "config": {
            "code_arm_required": False,
            "code_mode_change_required": False,
            "code_disarm_required": True,
            "code_format": "number",
            "disarm_after_trigger": False,
            "ignore_blocking_sensors_after_trigger": False,
            "master": {"enabled": True, "name": "master"},
            "mqtt": {
                "enabled": False,
                "state_topic": "alarmo/state",
                "state_payload": {},
                "command_topic": "alarmo/command",
                "command_payload": {},
                "require_code": True,
                "event_topic": "alarmo/event",
            },
        },
        "areas": [
            {
                "area_id": "1705934512",
                "name": "House",
                "modes": {
                    "armed_away": mode(exit_time=60, entry_time=30, trigger_time=1800),
                    "armed_home": mode(exit_time=0, entry_time=30, trigger_time=600),
                    "armed_night": mode(exit_time=20, entry_time=15, trigger_time=600),
                    "armed_vacation": mode(enabled=False),
                },
            }
        ],
        "sensors": [
            sensor("binary_sensor.front_door", modes=ALL),
            sensor(
                "binary_sensor.kitchen_window",
                "window",
                modes=ALL,
                use_entry_delay=False,
            ),
            sensor("binary_sensor.hall_pir", "motion", modes=("armed_away",)),
            sensor(
                "binary_sensor.kitchen_smoke",
                "environmental",
                modes=[],
                always_on=True,
                use_exit_delay=False,
                use_entry_delay=False,
            ),
            sensor(
                "binary_sensor.panel_tamper",
                "tamper",
                modes=[],
                always_on=True,
                use_exit_delay=False,
                use_entry_delay=False,
            ),
        ],
        "users": [
            {
                "user_id": "1705934600",
                "name": "Anna",
                "enabled": True,
                # base64(bcrypt("1234")) as Alarmo writes it; it must never
                # travel, which is exactly what makes it worth having here.
                "code": "JDJiJDEwJHh4eHh4eHh4eHh4eHh4eHh4eHh4eA==",
                "can_arm": True,
                "can_disarm": True,
                "is_override_code": False,
                "code_format": "number",
                "code_length": 4,
                "area_limit": [],
            }
        ],
        "automations": [
            {
                "automation_id": "1705934700",
                "type": "action",
                "name": "Siren on alarm",
                "triggers": [{"event": "triggered", "area": None, "modes": []}],
                "actions": [
                    {"service": "siren.turn_on", "entity_id": "siren.hall", "data": {}}
                ],
                "enabled": True,
            },
            {
                "automation_id": "1705934701",
                "type": "notification",
                "name": "Tell me",
                "triggers": [{"event": "triggered", "area": None, "modes": []}],
                "actions": [
                    {"service": "notify.mobile_app_anna", "entity_id": None, "data": {}}
                ],
                "enabled": True,
            },
        ],
        "sensor_groups": [
            {
                "group_id": "1705934800",
                "name": "Open plan",
                "entities": ["binary_sensor.hall_pir", "binary_sensor.kitchen_window"],
                "timeout": 60,
                "event_count": 2,
            }
        ],
    }
    data.update(overrides)
    return {"version": 6, "minor_version": 3, "key": "alarmo.storage", "data": data}


ENTITIES = {
    "binary_sensor.front_door": EntityInfo("off", "Front door", "door"),
    "binary_sensor.kitchen_window": EntityInfo("off", "Kitchen window", "window"),
    "binary_sensor.hall_pir": EntityInfo("off", "Hall PIR", "motion"),
    "binary_sensor.kitchen_smoke": EntityInfo("off", "Kitchen smoke", "smoke"),
    "binary_sensor.panel_tamper": EntityInfo("off", "Panel tamper", "tamper"),
}
LABELS = Labels(
    modes={"armed_away": "Away", "armed_home": "Home", "armed_night": "Night"}
)


def seed():
    """What every installation has: the config flow's area, zone and scenario
    (decision 75) — and the zone is, as it usually will be, the front door."""
    counter = itertools.count()
    return seed_config(
        area_name="Home",
        scenario_name="Everything",
        zone_entity_id="binary_sensor.front_door",
        zone_name="Front door",
        trigger_states=["on"],
        new_id=lambda: f"seed{next(counter)}",
    )


def run(document=None, config=None, entities=ENTITIES, labels=LABELS):
    return plan(
        alarmo_file() if document is None else document,
        seed() if config is None else config,
        entities,
        labels,
        ids(),
    )


def codes(result):
    return [line.code for line in result.lines]


def by_name(items, name):
    return next(i for i in items if i.name == name)


# --- the report says the two things first ------------------------------------------


def test_the_first_line_says_nobody_can_disarm_until_they_have_a_new_code():
    """An installation that imports at midnight and cannot disarm at midnight
    past is the worst first impression there is."""
    result = run()
    assert result.lines[0].code == "codes"
    assert result.lines[0].params == {"people": 1}
    assert result.lines[1].code == "zones_to_confirm"
    assert result.lines[1].params == {"zones": 4}


def test_no_code_and_no_hash_ever_crosses():
    result = run()
    anna = by_name(result.config.users, "Anna")
    assert anna.code_hash is None and anna.duress_code_hash is None
    # And nothing anywhere in the stored configuration carries it.
    from custom_components.foyer.store.schema import config_to_dict

    assert "JDJiJDEw" not in repr(config_to_dict(result.config))


# --- INV-5: nothing Alarmo believed about `on` is carried --------------------------


def test_every_imported_zone_is_switched_off_and_unconfirmed():
    result = run()
    before = {z.id for z in seed().zones}
    imported = [z for z in result.config.zones if z.id not in before]
    assert imported
    assert all(not z.enabled and not z.trigger_confirmed for z in imported)
    # The zone that was already here is exactly as it was.
    assert [z for z in result.config.zones if z.id in before] == list(seed().zones)


def test_the_trigger_is_foyers_proposal_not_alarmos_list():
    """Alarmo reads on/open/unlocked for everything. A lock is proposed by
    Foyer's own table instead, and even then only as a proposal."""
    document = alarmo_file(
        sensors=[sensor("lock.back_door", "door", modes=ALL)],
    )
    result = run(document, entities={"lock.back_door": EntityInfo("locked", "Back")})
    zone = by_name(result.config.zones, "Back")
    assert zone.trigger.states == frozenset({"unlocked", "open", "opening"})
    assert not zone.trigger_confirmed


def test_the_result_is_a_valid_configuration():
    """It goes through validate() like every other edit; this is the check
    that it would pass rather than be refused for a reason nobody can fix."""
    result = run()
    assert validate(result.config) == []
    assert edit_conflicts(seed(), result.config, RuntimeState()) == []


# --- areas, scenarios, modes -------------------------------------------------------


def test_an_area_splits_by_the_modes_its_sensors_are_watched_in():
    result = run()
    house = by_name(result.config.areas, "House")
    away_only = by_name(result.config.areas, "House (Away)")
    zones = {z.name: z for z in result.config.zones}
    assert zones["Kitchen window"].area_id == house.id
    assert zones["Hall PIR"].area_id == away_only.id
    # Always-on zones live where every mode is.
    assert zones["Kitchen smoke"].area_id == house.id
    assert "area_split" in codes(result)


def test_an_existing_scenario_for_the_same_mode_is_extended_not_duplicated():
    """Two scenarios reporting armed_away would make the master refuse the
    mode (decision 41): HomeKit's "away" would stop working."""
    result = run()
    away = [s for s in result.config.scenarios if s.ha_master_state == "armed_away"]
    assert len(away) == 1 and away[0].name == "Everything"
    house = by_name(result.config.areas, "House")
    away_only = by_name(result.config.areas, "House (Away)")
    assert set(away[0].areas) == {"seed0", house.id, away_only.id}
    assert result.counts["scenarios_extended"] == 1


def test_one_new_scenario_per_other_mode_the_house_used():
    result = run()
    home = by_name(result.config.scenarios, "Home")
    night = by_name(result.config.scenarios, "Night")
    house = by_name(result.config.areas, "House")
    assert home.areas == (house.id,) and home.ha_master_state == "armed_home"
    assert night.areas == (house.id,)
    # Vacation was not enabled: no scenario for it.
    assert not any(
        s.ha_master_state == "armed_vacation" for s in result.config.scenarios
    )


def test_one_area_takes_the_longest_exit_delay_and_says_so():
    """A delay too short locks somebody out of their own house with the
    siren going."""
    result = run()
    house = by_name(result.config.areas, "House")
    assert house.default_exit_delay == 60
    assert any(
        line.code == "exit_delay_varies" and line.params["area"] == "House"
        for line in result.lines
    )
    # The scenario keeps its own mode's exit time.
    assert by_name(result.config.scenarios, "Night").exit_delay_override == 20


def test_a_siren_that_sounded_for_ever_or_too_long_is_capped_and_reported():
    result = run()
    assert by_name(result.config.scenarios, "Home").siren_duration_override == 600
    document = alarmo_file()
    document["data"]["areas"][0]["modes"]["armed_home"]["trigger_time"] = 0
    result = run(document)
    assert by_name(result.config.scenarios, "Home").siren_duration_override == 900
    assert "siren_capped" in codes(result)


def test_labels_name_what_is_created_and_the_backend_writes_no_word():
    labels = Labels(
        modes={"armed_away": "Fuori casa", "armed_home": "In casa"},
        split="{area} · {modes}",
    )
    result = run(labels=labels)
    names = {a.name for a in result.config.areas}
    assert "House · Fuori casa" in names
    assert "In casa" in {s.name for s in result.config.scenarios}
    # A mode the panel sent no word for is named by Alarmo's identifier.
    assert "armed_night" in {s.name for s in result.config.scenarios}


def test_unusable_labels_fall_back_rather_than_collide():
    parsed = Labels.parse({"modes": {"armed_away": 7}, "split": "no placeholders"})
    assert parsed == Labels()


def test_a_name_already_taken_gets_a_number():
    config = seed()
    config = replace(config, areas=(replace(config.areas[0], name="House"),))
    result = run(config=config)
    assert {"House 2", "House (Away)"} <= {a.name for a in result.config.areas}
    assert any(
        line.code == "renamed" and line.params["name"] == "House 2"
        for line in result.lines
    )


# --- zones -------------------------------------------------------------------------


def test_zone_kinds_follow_what_alarmo_meant():
    result = run()
    zones = {z.name: z for z in result.config.zones}
    assert zones["Kitchen smoke"].channel is Channel.TECHNICAL
    assert zones["Panel tamper"].type is ZoneType.TAMPER
    # use_entry_delay false: instant, as Alarmo ran it.
    assert zones["Kitchen window"].entry_mode is EntryMode.INSTANT
    # A motion sensor with the entry delay in Away was delayed in Alarmo.
    assert zones["Hall PIR"].entry_mode is EntryMode.DELAYED


def test_a_sensor_foyer_already_watches_is_left_alone_and_named():
    result = run()
    line = next(line for line in result.lines if line.code == "sensor_exists")
    assert line.params == {"entity": "binary_sensor.front_door", "zone": "Front door"}
    assert (
        sum(z.entity_id == "binary_sensor.front_door" for z in result.config.zones) == 1
    )


@pytest.mark.parametrize(
    ("extra", "policy", "line"),
    [
        ({"allow_open": True}, ArmPolicy.IGNORE, None),
        ({"arm_on_close": True}, ArmPolicy.ARM_AFTER_CLOSING, "arm_on_close"),
        (
            {"auto_bypass": True, "auto_bypass_modes": list(ALL)},
            ArmPolicy.AUTO_BYPASS,
            None,
        ),
        (
            {"auto_bypass": True, "auto_bypass_modes": ["armed_home"]},
            ArmPolicy.BLOCK,
            "auto_bypass_partial",
        ),
    ],
)
def test_arm_policies(extra, policy, line):
    document = alarmo_file(
        sensors=[sensor("binary_sensor.patio", "door", modes=ALL, **extra)]
    )
    result = run(document, entities={"binary_sensor.patio": EntityInfo("off", "Patio")})
    assert by_name(result.config.zones, "Patio").arm_policy is policy
    if line:
        assert line in codes(result)


def test_what_foyer_cannot_do_for_a_sensor_is_a_line_not_a_rounding():
    document = alarmo_file(
        sensors=[
            sensor(
                "binary_sensor.shed",
                "door",
                modes=ALL,
                trigger_unavailable=True,
                delay_on=5,
                enabled=False,
            ),
            sensor("sensor.temperature", "other", modes=ALL),
            sensor("binary_sensor.gone", "door", modes=ALL),
            sensor("binary_sensor.nowhere", "door", modes=["armed_vacation"]),
        ]
    )
    result = run(document, entities={"binary_sensor.shed": EntityInfo("off", "Shed")})
    found = codes(result)
    for code in (
        "trigger_unavailable",
        "delay_on",
        "sensor_was_disabled",
        "sensor_domain",
        "sensor_missing",
        "sensor_no_mode",
    ):
        assert code in found, code


# --- people ------------------------------------------------------------------------


def test_people_bring_what_alarmo_let_them_do_and_nothing_more():
    document = alarmo_file()
    document["data"]["users"].append(
        {
            **document["data"]["users"][0],
            "name": "Guest",
            "can_disarm": False,
            "is_override_code": True,
        }
    )
    result = run(document)
    anna = by_name(result.config.users, "Anna")
    guest = by_name(result.config.users, "Guest")
    assert anna.permissions == {"arm", "change_scenario", "disarm"}
    assert guest.permissions == {"arm", "change_scenario", "force_arm"}
    assert anna.pseudonym and anna.pseudonym != guest.pseudonym


def test_a_person_already_here_is_not_created_again():
    config = replace(seed(), users=(User(id="u1", name="anna", code_hash="$2b$x"),))
    result = run(config=config)
    assert [u.id for u in result.config.users] == ["u1"]
    assert "person_exists" in codes(result)
    # Still the first line: nobody new, and still no code from Alarmo.
    assert result.lines[0].code == "codes_nobody"


def test_an_area_limit_becomes_the_foyer_areas_that_area_became():
    document = alarmo_file()
    document["data"]["users"][0]["area_limit"] = ["1705934512"]
    result = run(document)
    anna = by_name(result.config.users, "Anna")
    assert set(anna.allowed_area_ids) == {
        by_name(result.config.areas, "House").id,
        by_name(result.config.areas, "House (Away)").id,
    }


# --- actions -----------------------------------------------------------------------


def test_a_siren_comes_across_in_a_copy_of_the_default_profile():
    """A profile replaces the default for its areas; one with only a siren
    would be an alarm that notifies nobody (decision 63)."""
    result = run()
    house = by_name(result.config.areas, "House")
    profile = next(
        p for p in result.config.profiles if p.id == house.response_profile_id
    )
    kinds = [a.kind for a in profile.actions]
    assert ActionKind.PERSISTENT_NOTIFICATION in kinds
    siren = next(a for a in profile.actions if a.kind is ActionKind.SIREN)
    assert siren.moments == frozenset({Moment.TRIGGERED})
    assert list(siren.params["entity_ids"]) == ["siren.hall"]
    # No action id is shared with the default profile it was copied from.
    default = result.config.profiles[0]
    assert not {a.id for a in default.actions} & {a.id for a in profile.actions}


def test_a_notification_is_reported_rather_than_guessed_at():
    """A notification that arrives somewhere unintended is worse than one the
    report says was not brought across."""
    result = run()
    assert any(
        line.code == "automation_notification"
        and line.params["automation"] == "Tell me"
        for line in result.lines
    )


def test_a_switch_off_on_untriggered_ends_with_the_alarm():
    document = alarmo_file(
        automations=[
            {
                "automation_id": "1",
                "type": "action",
                "name": "Relay off",
                "triggers": [{"event": "untriggered", "area": 0, "modes": []}],
                "actions": [
                    {"service": "switch.turn_off", "entity_id": ["switch.relay"]}
                ],
                "enabled": True,
            }
        ]
    )
    result = run(document)
    action = next(
        a
        for p in result.config.profiles
        for a in p.actions
        if a.kind is ActionKind.SWITCH
    )
    assert action.params["state"] == "off"
    # The moment that is exactly Alarmo's: the alarm is over, by the cutoff
    # or by a disarm, and never an ordinary disarm (decision 105).
    assert action.moments == frozenset({Moment.ALARM_ENDED})


@pytest.mark.parametrize(
    ("automation", "code"),
    [
        ({"enabled": False}, "automation_disabled"),
        (
            {"triggers": [{"entity_id": "binary_sensor.x", "state": "on"}]},
            "automation_trigger",
        ),
        (
            {
                "triggers": [
                    {"event": "triggered", "area": None, "modes": ["armed_away"]}
                ]
            },
            "automation_modes",
        ),
        (
            {"actions": [{"service": "light.turn_on", "entity_id": "light.hall"}]},
            "action_not_imported",
        ),
        (
            {"actions": [{"service": "siren.turn_off", "entity_id": "siren.hall"}]},
            "siren_off_not_needed",
        ),
    ],
)
def test_automations_it_does_not_bring(automation, code):
    base = alarmo_file()["data"]["automations"][0]
    result = run(alarmo_file(automations=[{**base, **automation}]))
    assert code in codes(result)
    assert not any(
        a.kind in (ActionKind.SIREN, ActionKind.SWITCH)
        for p in result.config.profiles
        for a in p.actions
    )


def test_groups_are_reported_because_their_members_start_switched_off():
    result = run()
    line = next(line for line in result.lines if line.code == "group_not_imported")
    assert line.params == {"group": "Open plan", "n": 2, "members": 2, "seconds": 60}
    assert result.config.groups == ()


def test_alarmo_settings_foyer_has_no_place_for_are_named():
    result = run()
    assert any(
        line.code == "setting_not_imported"
        and line.params["setting"] == "code_disarm_required"
        for line in result.lines
    )


# --- untrusted input: refuse, never half-import ------------------------------------


@pytest.mark.parametrize(("version", "minor"), [(5, 1), (6, 4), (7, 1), (1, 1)])
def test_a_version_it_has_not_read_is_refused_by_name(version, minor):
    document = {**alarmo_file(), "version": version, "minor_version": minor}
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.code == "version_unsupported"
    assert refused.value.line.params == {"version": f"{version}.{minor}"}


@pytest.mark.parametrize("minor", [1, 2, 3])
def test_the_versions_it_has_read_are_read(minor):
    document = {**alarmo_file(), "minor_version": minor}
    assert run(document).counts["zones"] == 4


def test_a_file_that_is_not_alarmos_is_refused():
    for document in ({}, [], {"key": "foyer.config", "version": 6}, "text"):
        with pytest.raises(Refused) as refused:
            run(document)
        assert refused.value.line.code == "not_alarmo"


@pytest.mark.parametrize(
    ("path", "value", "where"),
    [
        (("sensors", 0, "always_on"), "yes", "sensors[0].always_on"),
        (("sensors", 0, "modes"), ["armed_everything"], "sensors[0].modes"),
        (("sensors", 0, "entity_id"), "../../etc", "sensors[0].entity_id"),
        (("sensors", 0, "entry_delay"), -5, "sensors[0].entry_delay"),
        (("users", 0, "can_disarm"), 1, "users[0].can_disarm"),
        (("areas", 0, "modes"), [], "areas[0].modes"),
    ],
)
def test_a_wrong_shape_is_refused_whole_naming_where(path, value, where):
    document = alarmo_file()
    node = document["data"]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.code == "invalid"
    assert refused.value.line.params == {"where": where}


def test_a_missing_section_is_refused():
    document = alarmo_file()
    del document["data"]["sensor_groups"]
    with pytest.raises(Refused):
        run(document)


def test_an_unknown_field_is_reported_not_refused():
    """Alarmo has added fields without a version bump three times; the next
    one should be a line in the report, not a wall."""
    document = alarmo_file()
    document["data"]["sensors"][1]["night_light"] = True
    result = run(document)
    assert any(
        line.code == "unknown_field" and line.params["field"] == "sensors.night_light"
        for line in result.lines
    )


def test_nothing_in_the_file_chooses_an_id_a_webhook_or_a_url():
    document = alarmo_file()
    document["data"]["areas"][0]["area_id"] = "seed0"  # an id Foyer already uses
    for s in document["data"]["sensors"]:
        s["area"] = "seed0"
    result = run(document)
    before = seed()
    new_ids = {a.id for a in result.config.areas} - {a.id for a in before.areas}
    assert new_ids and all(i.startswith("id") for i in new_ids)
    assert result.config.settings == before.settings
    assert result.config.health == before.health
    assert validate(result.config) == []


def test_a_file_with_nothing_to_bring_is_refused_rather_than_a_no_op():
    document = alarmo_file(
        sensors=[sensor("binary_sensor.front_door", modes=ALL)], users=[]
    )
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.code == "nothing_to_import"


def test_a_file_too_big_to_be_a_house_is_refused():
    document = alarmo_file(
        sensors=[sensor(f"binary_sensor.s{i}", modes=ALL) for i in range(1001)]
    )
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.code == "too_many"


def test_an_area_with_no_mode_enabled_brings_nothing_and_says_why():
    document = alarmo_file()
    for entry in document["data"]["areas"][0]["modes"].values():
        entry["enabled"] = False
    document["data"]["users"] = []
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.code == "nothing_to_import"
    document["data"]["users"] = alarmo_file()["data"]["users"]
    result = run(document)
    assert "area_no_modes" in codes(result)
    assert result.counts["zones"] == 0


# --- what the review found -------------------------------------------------------


def test_a_chirp_on_arming_is_not_turned_into_the_full_siren():
    """A siren with a tone or a duration, or at another moment than the alarm,
    would sound for the whole siren time on every arming (found in review)."""
    base = alarmo_file()["data"]["automations"][0]
    chirp = {
        **base,
        "triggers": [{"event": "armed", "area": None, "modes": []}],
    }
    toned = {
        **base,
        "actions": [
            {
                "service": "siren.turn_on",
                "entity_id": "siren.hall",
                "data": {"tone": "x"},
            }
        ],
    }
    for automation in (chirp, toned):
        result = run(alarmo_file(automations=[automation]))
        assert "siren_not_imported" in codes(result)
        assert not any(
            a.kind is ActionKind.SIREN
            for p in result.config.profiles
            for a in p.actions
        )


def test_an_area_profile_hiding_a_scenario_profile_is_said():
    """Extending a scenario with its own profile, and giving the imported area
    a profile of its own, stops the area inheriting the scenario's — which
    must be a line, never a notification that quietly stops (found in review)."""
    config = seed()
    profile = replace(config.profiles[0], id="phone", name="Phone")
    config = replace(
        config,
        profiles=(*config.profiles, profile),
        scenarios=(replace(config.scenarios[0], response_profile_id="phone"),),
    )
    result = run(config=config)
    assert "profile_hides_scenario" in codes(result)


def test_a_new_scenario_takes_its_times_only_from_areas_that_came_across():
    document = alarmo_file()
    document["data"]["areas"].append(
        {
            "area_id": "2",
            "name": "Shed",
            "modes": {"armed_home": mode(exit_time=200, trigger_time=0)},
        }
    )
    result = run(document)
    home = by_name(result.config.scenarios, "Home")
    assert home.exit_delay_override == 0
    assert home.siren_duration_override == 600
    assert "area_empty" in codes(result)


def test_an_automation_for_an_area_that_did_not_come_across_is_not_imported():
    document = alarmo_file()
    document["data"]["areas"].append(
        {"area_id": "2", "name": "Shed", "modes": {"armed_away": mode()}}
    )
    base = document["data"]["automations"][0]
    document["data"]["automations"] = [
        {**base, "triggers": [{"event": "triggered", "area": "2", "modes": []}]},
        {**base, "name": "Nothing", "actions": []},
    ]
    result = run(document)
    assert "automation_no_area" in codes(result)
    assert "automation_imported" not in codes(result)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("sensors", 0, "type"), ["door"]),
        (("automations", 0, "triggers", 0, "event"), ["armed"]),
        (("areas", 0, "modes", "armed_away", "enabled"), "yes"),
    ],
)
def test_an_unhashable_or_wrong_value_is_refused_not_a_crash(path, value):
    document = alarmo_file()
    node = document["data"]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(Refused):
        run(document)


def test_two_areas_with_one_id_are_refused():
    document = alarmo_file()
    document["data"]["areas"].append({**document["data"]["areas"][0], "name": "Other"})
    with pytest.raises(Refused) as refused:
        run(document)
    assert refused.value.line.params == {"where": "areas[1].area_id"}


def test_a_person_twice_in_the_file_is_not_reported_as_already_here():
    document = alarmo_file()
    document["data"]["users"].append({**document["data"]["users"][0], "name": "anna"})
    result = run(document)
    assert "person_duplicate" in codes(result)
    assert "person_exists" not in codes(result)


def test_a_zone_name_already_taken_is_reported():
    config = seed()
    config = replace(config, zones=(replace(config.zones[0], name="Kitchen window"),))
    result = run(config=config)
    assert any(
        line.code == "renamed" and line.params["kind"] == "zone"
        for line in result.lines
    )


def test_sensors_that_aborted_an_arming_are_counted():
    document = alarmo_file()
    document["data"]["sensors"][1]["use_exit_delay"] = False
    result = run(document)
    assert any(
        line.code == "exit_abort" and line.params["zones"] >= 1 for line in result.lines
    )
