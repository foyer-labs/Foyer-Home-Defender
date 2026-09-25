"""Schema migrations for the stored configuration.

Home Assistant's Store calls ``migrate`` whenever the version on disk differs
from the version in code. Each step upgrades one (major, minor) version to the
next and is a pure function over the JSON document, so it can be tested without
Home Assistant.
"""

from __future__ import annotations

from collections.abc import Callable
import copy
from typing import Any
import uuid

Document = dict[str, Any]
Version = tuple[int, int]


def _v1_1_to_v2_1(data: Document) -> Document:
    """Phase 0 → Phase 1: every new property, chosen to change nothing.

    A Phase 0 installation keeps behaving exactly as it did: its one zone
    becomes an explicit instant intrusion zone with the ``block`` policy, and
    its area gets exit and entry delays of 0 s, because Phase 0 armed at once.
    The new defaults (30 s) apply only to areas created from now on.

    Two notifications are added to the existing action, because the spec
    requires them rather than leaving them to taste: a failed arming (someone
    left believing the house was armed) and an automatic bypass (§5.4 says
    "notify").
    """
    out = copy.deepcopy(data)
    for area in out["areas"]:
        area.setdefault("default_entry_delay", 0)
        area.setdefault("default_exit_delay", 0)
    for zone in out["zones"]:
        zone.update(
            {
                "type": "instant",
                "channel": "intrusion",
                "entry_mode": "instant",
                "alarm_kind": "intrusion",
                "always_on": False,
                "entry_delay": None,
                "arm_policy": "block",
                "arm_hold_timeout": None,
                "allow_arm_when_faulted": False,
                "bypassable": True,
                "supervision_timeout": None,
                "enabled": True,
                "key": None,
            }
        )
    for scenario in out["scenarios"]:
        scenario.update(
            {"icon": None, "exit_delay_override": None, "siren_duration_override": None}
        )
    for action in out["actions"]:
        action["moments"] = sorted({*action["moments"], "arm_failed", "zone_bypassed"})
    out["code_policy"] = {
        "arm": bool(out["code_policy"]["arm"]),
        "disarm": bool(out["code_policy"]["disarm"]),
        # No codes until Phase 2, and no code for these until then (decision 7).
        "force_arm": False,
        "change_scenario": False,
    }
    out["settings"] = {"siren_duration": 180, "arm_hold_timeout": 300}
    return out


def _v2_1_to_v2_2(data: Document) -> Document:
    """0.1.0-alpha.1 → alpha.2: followers can follow delayed zones in other
    areas. An empty list is exactly the 2.1 behaviour (own area only)."""
    out = copy.deepcopy(data)
    for zone in out["zones"]:
        zone.setdefault("follows", [])
    return out


def _v2_2_to_v3_1(data: Document) -> Document:
    """0.1.0-alpha.3 → Phase 1 part 2: technical channel, incidents,
    verification groups, cross-zone, trigger counting and chime.

    A major step although every field is additive: a 2.x build would read a
    technical zone and never act on it, so it must refuse the file instead
    (see STORAGE_VERSION).

    Every new setting is chosen to change nothing that already works: no
    groups, no cross-zone, one activation to alarm, no chime anywhere (the
    chime block has no targets), and acknowledgement needs no code, as
    nothing does before Phase 2.

    One behaviour is added on purpose (part 2 decision 10): a technical alarm
    gets the persistent notification every existing action already sends for
    faults. Without it a smoke detector would fire in an empty house and say
    nothing until response profiles exist.
    """
    out = copy.deepcopy(data)
    for zone in out["zones"]:
        zone.setdefault("chime", False)
        zone.setdefault("cross_zone_id", None)
        zone.setdefault("cross_zone_window", 60)
        zone.setdefault("trigger_count", 1)
        zone.setdefault("trigger_window", 60)
    out.setdefault("groups", [])
    out["code_policy"].setdefault("acknowledge", False)
    out.setdefault(
        "chime",
        {
            "targets": [],
            "mode": "sound",
            "sound": None,
            "tts_entity": None,
            "volume": None,
            "quiet_start": None,
            "quiet_end": None,
            "during_exit": False,
        },
    )
    for action in out["actions"]:
        action["moments"] = sorted({*action["moments"], "technical_raised"})
    return out


# The id of the profile the 3.1 -> 4.1 migration builds. A constant, not a
# uuid: a migration is a pure function of the document and must give the same
# result every time it runs.
DEFAULT_PROFILE_ID = "default"


def _v3_1_to_v4_1(data: Document) -> Document:
    """Phase 1 part 2 -> part 3: response profiles, conditions, actions.

    The Phase 0 notification is not thrown away and not reimplemented: every
    action it had becomes a ``persistent_notification`` action inside the new
    global default profile, with the same moments, so an installation that
    updates hears exactly what it heard yesterday — plus ``triggered``, which
    had no notification at all and is the one moment that must never be silent
    (part 3 decision 3).

    Everything else is chosen to change nothing: no zone, area, scenario or
    group overrides the default yet, no zone is silent, and the chime keeps its
    targets, now able to carry quiet hours of their own.
    """
    out = copy.deepcopy(data)
    actions = []
    for action in out.pop("actions", []):
        actions.append(
            {
                "id": action["id"],
                "kind": "persistent_notification",
                # A notification on an alarm: Phase 0 had none (decision 3).
                "moments": sorted({*action["moments"], "triggered"}),
                "name": "",
                # No title and no message: the executor keeps using the
                # translated text it already uses, so nothing changes.
                "params": {},
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
            }
        )
    out["profiles"] = [
        {
            "id": DEFAULT_PROFILE_ID,
            "name": "Default",
            "severity": 1,
            "actions": actions,
        }
    ]
    settings = out["settings"]
    settings["default_profile_id"] = DEFAULT_PROFILE_ID
    # The technical channel falls back to the default profile until the user
    # gives it one: the default already carries technical_raised (part 2).
    settings["technical_profile_id"] = None
    settings["silent_suppresses"] = ["siren", "tts", "chime"]
    settings["camera_dir"] = "media/foyer"
    out["code_policy"]["bypass_zone"] = False
    for area in out["areas"]:
        area["response_profile_id"] = None
    for scenario in out["scenarios"]:
        scenario["response_profile_id"] = None
    for group in out["groups"]:
        group["response_profile_id"] = None
    for zone in out["zones"]:
        zone["response_profile_id"] = None
        zone["silent"] = False
    out["chime"]["targets"] = [
        {"entity_id": target, "quiet_start": None, "quiet_end": None}
        for target in out["chime"]["targets"]
    ]
    return out


def _v4_1_to_v4_2(data: Document) -> Document:
    """Phase 1 part 3 -> part 4: the event log, and the settings it needs.

    A minor step, and for once that is not a technicality: a 4.1 build reading
    this document ignores every key added here and keeps behaving exactly as
    it did, because none of them changes what is protected.

    The defaults are the documented ones (SPEC §10.2, §10.3): every category
    on, thirty days each, except zone activity while disarmed, which is off —
    a living-room PIR produces thousands of rows a day. The defaults for new
    areas are seeded from the areas that exist, so an installation whose areas
    all use 45 s does not get 30 s offered on the next one; a Phase 0 install
    whose area has 0 s delays keeps the documented 30 s instead of proposing
    "no delay at all" for every area created from now on.
    """
    out = copy.deepcopy(data)
    settings = out["settings"]
    settings["log"] = {
        "enabled": {c: c != "zone_disarmed" for c in LOG_CATEGORIES},
        "retention_days": {c: 30 for c in LOG_CATEGORIES},
    }
    entry = sorted({int(a["default_entry_delay"]) for a in out["areas"]})
    exit_ = sorted({int(a["default_exit_delay"]) for a in out["areas"]})
    settings["default_entry_delay"] = entry[0] if len(entry) == 1 and entry[0] else 30
    settings["default_exit_delay"] = exit_[0] if len(exit_) == 1 and exit_[0] else 30
    # None: the language Home Assistant itself runs in, which is what every
    # message has used until now.
    settings["language"] = None
    # An installation that already has areas and zones is not a first run:
    # offering it the first-run wizard would be telling somebody who has
    # finished to start.
    settings["wizard_done"] = True
    return out


def _v4_2_to_v5_1(data: Document) -> Document:
    """Phase 1 -> Phase 2: identity. The document learns about people.

    A major step, and the reason is the sharpest of the four so far: a 4.x
    build reading this document would find users it knows nothing about,
    ignore every code in it, and run the house exactly as it ran before codes
    existed. Refusing the file is the only safe downgrade there is.

    The code policy moves to the defaults of SPEC §8.2, which is the end of
    Phase 1 decision 6: forcing an arming and changing scenario while armed
    ask for a code from now on, as disarming and excluding a zone do. This
    changes behaviour, so it is in the changelog — but it changes nothing
    *yet*: the policy is inert while no user holds a code (decision 78), and
    an installation upgrading into this version has none. Without that rule
    this very step would leave an armed house nobody could disarm.

    Everything else is new and empty: no users, no per-area or per-scenario
    override, no identity on a key zone. An installation upgrading is exactly
    as it was, and stays so until somebody creates the first user.
    """
    out = copy.deepcopy(data)
    out["users"] = []
    out["code_policy"] = {
        "arm": False,
        "disarm": True,
        "force_arm": True,
        "change_scenario": True,
        "acknowledge": False,
        "bypass_zone": True,
        "edit_config": True,
        "walk_test": True,
        "test_action": True,
    }
    out["settings"]["security"] = {
        "code_length": 6,
        "lockout_failures": 5,
        "lockout_window": 300,
        "lockout_duration": 300,
    }
    for area in out["areas"]:
        area["require_code_to_arm"] = None
        area["require_code_to_disarm"] = None
    for scenario in out["scenarios"]:
        scenario["require_code_to_arm"] = None
        scenario["require_code_to_disarm"] = None
        scenario["allowed_user_ids"] = None
    for zone in out["zones"]:
        if zone.get("key") is not None:
            # Whose key it is. Nobody's, until somebody says: a key with no
            # user is still a key, and the log records the turn either way.
            zone["key"]["user_id"] = None
    return out


def _v5_1_to_v5_2(data: Document) -> Document:
    """Phase 2 part 1 -> part 2: the physical channels.

    A minor step, and honestly so: an installation upgrading gains an empty
    list of arming devices and an MQTT contract that is switched **off**. A
    5.1 build reading this document ignores both and is exactly the build it
    was — one with no physical channels at all, which is what it had.

    MQTT is off rather than on because a broker is somebody else's machine:
    an alarm that starts publishing its state on a shared broker the moment
    it is updated has made that choice for the household. The topics are left
    empty, which means "the default", resolved at runtime from the
    installation id — storing the resolved value here would freeze one
    installation's id into a document that gets exported and restored
    somewhere else.
    """
    out = copy.deepcopy(data)
    out["devices"] = []
    out["settings"]["mqtt"] = {
        "enabled": False,
        "command_topic": "",
        "state_topic": "",
        # The least that still lets a keypad give feedback (part 2 decision 3):
        # the retained message is told to whoever connects to the broker next.
        "detail": "minimal",
        "retain": True,
        "qos": 1,
    }
    return out


def _v5_2_to_v5_3(data: Document) -> Document:
    """Phase 2 part 2 -> Phase 3 part 1: a zone may name its battery.

    A minor step, and truthfully so: an installation upgrading gains one
    empty field on each zone and one number in its settings. A 5.2 build
    reading this document ignores both and never warns about a battery —
    which is exactly what it did the day before, because there was nothing
    to warn about.

    Nothing changes behaviour: no zone names a battery until somebody picks
    one, and a low battery blocks no arming even then (part 1 decision 2).
    The threshold is the documented default rather than something derived
    from the document, because there is nothing in a 5.2 document to derive
    it from.
    """
    out = copy.deepcopy(data)
    for zone in out["zones"]:
        zone.setdefault("battery_entity_id", None)
    out["settings"]["low_battery_threshold"] = 20
    return out


def _v5_3_to_v5_4(data: Document) -> Document:
    """Phase 3 part 1 -> part 2: the walk test.

    A minor step: one number in the settings, and two moments added to the
    default profile's notifications. A 5.3 build reading this document
    ignores both and has no walk test at all, which is what it had.

    The two moments are not decoration. §11.3 lists "a notification on start
    and on end" among the safeguards that are *not optional*, next to the
    banner and the non-disableable timeout — and a safeguard that only
    reaches an installation which happened to configure it is not a
    safeguard. They are added exactly where the 3.1 -> 4.1 step added
    ``triggered`` for the same reason, and only to ``persistent_notification``
    actions of the default profile: a moment added to a siren would make a
    walk test sound one.
    """
    out = copy.deepcopy(data)
    # §5.3: 15 minutes, mandatory, non-disableable. The documented default
    # rather than something derived, because a 5.3 document has nothing to
    # derive it from.
    out["settings"]["walk_test_timeout"] = 900
    default_id = out["settings"].get("default_profile_id")
    for profile in out.get("profiles", []):
        if profile["id"] != default_id:
            continue
        for action in profile.get("actions", []):
            if action.get("kind") != "persistent_notification":
                continue
            action["moments"] = sorted(
                {*action.get("moments", []), "walk_test_started", "walk_test_ended"}
            )
    return out


def _v5_4_to_v6_1(data: Document) -> Document:
    """Phase 3 -> Phase 4 part 1: contacts, escalation and acknowledgement.

    A major step for the reason 3.1 and 4.1 were major: a 5.x build reading
    this document would find a notify action naming contacts, know nothing
    about contacts, and send nothing at all.

    Nothing an installation already has changes. The address book starts
    empty, every existing notify action keeps the service it names — both
    forms stay, for ever, and page 6 offers to make a contact out of a
    service rather than rewriting anybody's configuration (part 1 decision
    8) — and no action becomes a step, because ``escalation_offset`` is null
    everywhere. An installation upgrading escalates nothing until somebody
    writes a step, which is exactly the state it was in yesterday.

    The DTMF webhook is off, and that is not a default chosen for tidiness:
    a Home Assistant webhook is unauthenticated, so switching one on is
    handing out a URL that stops an alarm (part 1 decision 6).
    """
    out = copy.deepcopy(data)
    out["contacts"] = []
    out["settings"]["ack_webhook_id"] = None
    for profile in out.get("profiles", []):
        for action in profile.get("actions", []):
            action["escalation_offset"] = None
    return out


def _v6_1_to_v7_1(data: Document) -> Document:
    """Automatic arming rules, and the perimeter flag they need (§9.4, §4.5).

    An installation upgrading gains no rules: the list is empty, so nothing
    arms itself until somebody writes one. Automatic disarming arrives off,
    which is §9.4 point 2 and not a matter of taste — enabling it is where
    the panel names the attack.

    Every area arrives as *not* the perimeter, and that is the one choice
    here worth defending. Marking them all as perimeter would be the safer
    direction in the abstract, but it is a guess about somebody's house, and
    a guess that quietly refuses the first disarm rule they write is worse
    than a field they set deliberately. There are no rules yet, so nothing
    can act on the flag before they have been asked (page 2 asks).
    """
    out = copy.deepcopy(data)
    out["rules"] = []
    out["settings"]["allow_auto_disarm"] = False
    out["code_policy"]["cancel_auto_action"] = False
    for area in out.get("areas", []):
        area["is_perimeter"] = False
    return out


def _v7_1_to_v7_2(data: Document) -> Document:
    """System health (§12): the mains, the watchdog and the radios.

    Every part of it arrives switched off, and that is not caution for its
    own sake. The watchdog needs a URL nobody has given yet and a ping to an
    empty string is a failure reported every quarter of an hour; the mains
    needs an entity and a state that means "lost", which INV-5 says is the
    household's to confirm rather than Foyer's to assume; and interference
    detection needs a coordinator entity named per radio, without which the
    gate that makes the heuristic worth having cannot be applied at all.

    A *minor* step, unlike decision 58's: a 7.1 build reading this document
    ignores the block and is a build with no system health — exactly what it
    was yesterday. Nothing it would have protected goes unprotected, and the
    one thing it would miss, it was already missing.
    """
    out = copy.deepcopy(data)
    # The four moments that must not be silent, added to whatever the
    # default profile already announces with a persistent notification —
    # decision 71's precedent exactly, and for the same reason: an
    # installation upgrading into this phase would otherwise gain a power
    # cut it is never told about. Only that one action is touched, and only
    # if it is there.
    default = data.get("settings", {}).get("default_profile_id")
    for profile in out.get("profiles", []):
        if profile.get("id") != default:
            continue
        for action in profile.get("actions", []):
            if action.get("kind") == "persistent_notification":
                action["moments"] = sorted(
                    {
                        *action.get("moments", []),
                        "system_power_lost",
                        "notification_channel_down",
                        "watchdog_unreachable",
                        "rf_interference_suspected",
                    }
                )
    out["health"] = {
        "mains_entity_id": None,
        "mains_lost_states": ["on"],
        "watchdog": {
            "enabled": False,
            "url": "",
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": False,
        },
        "radios": [],
        "rf_zones": 4,
        "rf_window": 60,
        "rf_confirm": 60,
        "channel_sweep": 900,
        "channel_failures": 2,
        "repair_after": 2 * 24 * 3600,
    }
    return out


def _v7_2_to_v7_3(data: Document) -> Document:
    """Phase 5 part 2: the privacy tooling of §10.4, and leaving cleanly.

    Three additions, none of which changes what an installation does. Timed
    pseudonymisation is off, because it trades away "who disarmed that night"
    and nobody has asked for that trade; removing the integration keeps the
    log database, because §16 says to ask rather than guess and keeping is
    the only answer that destroys nothing.

    Every existing person gains a pseudonym here rather than when they are
    next saved. It has to exist *before* the first sweep runs, or the first
    pseudonymised rows would carry nothing and the identifier would not be
    stable from the beginning — which is the whole of what makes it worth
    having.
    """
    out = copy.deepcopy(data)
    for user in out.get("users", []):
        if not user.get("pseudonym"):
            user["pseudonym"] = f"person-{uuid.uuid4().hex[:12]}"
    log = out.setdefault("settings", {}).setdefault("log", {})
    log.setdefault("pseudonymise_after", None)
    log.setdefault("delete_on_uninstall", False)
    return out


def _v7_3_to_v7_4(data: Document) -> Document:
    """Phase 5 part 3: a zone records whether its trigger was confirmed.

    Every zone already stored was saved through the editor, which has refused
    an unconfirmed trigger since Phase 1 (INV-5), so every one of them is
    confirmed and says so. Only the Alarmo importer ever writes ``False``.
    """
    out = copy.deepcopy(data)
    for zone in out.get("zones", []):
        zone.setdefault("trigger_confirmed", True)
    return out


def _v7_4_to_v8_1(data: Document) -> Document:
    """Zone cameras and the device endpoint (§6.2.1, §9.2.1).

    Nothing anybody receives changes (decision 92): a notify action that
    names a camera keeps exactly that camera (``fixed``) and every other one
    keeps carrying none. Only an action created from now on starts at
    ``zone``. Every zone starts with no cameras, and every keypad stays on
    the broker it was declared for — an endpoint keypad exists only once
    somebody has chosen it on page 8 and generated its token.
    """
    out = copy.deepcopy(data)
    for zone in out.get("zones", []):
        zone.setdefault("camera_entity_ids", [])
    for profile in out.get("profiles", []):
        for action in profile.get("actions", []):
            if action.get("kind") != "notify":
                continue
            # `or {}`, as action_from_dict reads it: a hand-edited document
            # with `"params": null` restored before this step existed.
            params = action["params"] = action.get("params") or {}
            params.setdefault(
                "images", "fixed" if params.get("camera_entity_id") else "none"
            )
    for device in out.get("devices", []):
        device.setdefault("transport", "mqtt")
        device.setdefault("token_hash", None)
    return out


def _v8_1_to_v8_2(data: Document) -> Document:
    """API devices (§9.2.2): scopes, the unlock, the clear-text confirmation.

    A keypad already on the endpoint keeps what it did — it reads the state
    stream and arms and disarms — spelled out as the scopes that say so
    (decision 116). Every other device starts with none; scopes mean nothing
    off the endpoint.
    """
    out = copy.deepcopy(data)
    for device in out.get("devices", []):
        on_endpoint = device.get("transport") == "http"
        device.setdefault("scopes", ["arm", "disarm", "status"] if on_endpoint else [])
        device.setdefault("free_scopes", ["status"])
        device.setdefault("arm_scenario_ids", None)
        device.setdefault("arm_area_ids", None)
        device.setdefault("disarm_area_ids", None)
        device.setdefault("unlock_seconds", 120)
        device.setdefault("clear_text_confirmed", False)
    return out


def _v8_2_to_v8_3(data: Document) -> Document:
    """A rule may arm excluding open zones (decision 126). Every rule stored
    before keeps refusing an open zone, as it always has."""
    out = copy.deepcopy(data)
    for rule in out.get("rules", []):
        rule.setdefault("exclude_open_zones", False)
    return out


def _v8_3_to_v8_4(data: Document) -> Document:
    """The mains may be known from devices outside the UPS (decision 162).
    Every configuration stored before keeps its sensor, as it always has."""
    out = copy.deepcopy(data)
    health = out.setdefault("health", {})
    health.setdefault("mains_mode", "sensor")
    health.setdefault("mains_outside_entity_ids", [])
    health.setdefault("mains_outside_delay", 120)
    return out


def _v8_4_to_v8_5(data: Document) -> Document:
    """A disarm rule may name every area (decision 163). Every rule stored
    before keeps its own list, as it always has."""
    out = copy.deepcopy(data)
    for rule in out.get("rules", []):
        rule.setdefault("all_areas", False)
    return out


# The categories of SPEC §10.2, spelled out rather than imported: a migration
# is a pure function of the document and must not change when an enum does.
LOG_CATEGORIES = (
    "arming",
    "alarm",
    "action",
    "config",
    "security",
    "system",
    "zone_armed",
    "zone_disarmed",
)


# (from_major, from_minor) -> (step, (to_major, to_minor))
STEPS: dict[Version, tuple[Callable[[Document], Document], Version]] = {
    (1, 1): (_v1_1_to_v2_1, (2, 1)),
    (2, 1): (_v2_1_to_v2_2, (2, 2)),
    (2, 2): (_v2_2_to_v3_1, (3, 1)),
    (3, 1): (_v3_1_to_v4_1, (4, 1)),
    (4, 1): (_v4_1_to_v4_2, (4, 2)),
    (4, 2): (_v4_2_to_v5_1, (5, 1)),
    (5, 1): (_v5_1_to_v5_2, (5, 2)),
    (5, 2): (_v5_2_to_v5_3, (5, 3)),
    (5, 3): (_v5_3_to_v5_4, (5, 4)),
    (5, 4): (_v5_4_to_v6_1, (6, 1)),
    (6, 1): (_v6_1_to_v7_1, (7, 1)),
    (7, 1): (_v7_1_to_v7_2, (7, 2)),
    (7, 2): (_v7_2_to_v7_3, (7, 3)),
    (7, 3): (_v7_3_to_v7_4, (7, 4)),
    (7, 4): (_v7_4_to_v8_1, (8, 1)),
    (8, 1): (_v8_1_to_v8_2, (8, 2)),
    (8, 2): (_v8_2_to_v8_3, (8, 3)),
    (8, 3): (_v8_3_to_v8_4, (8, 4)),
    (8, 4): (_v8_4_to_v8_5, (8, 5)),
}


class MigrationError(Exception):
    """The stored document cannot be brought to the current version."""


def migrate(
    from_version: Version,
    to_version: Version,
    data: Document,
    steps: dict[Version, tuple[Callable[[Document], Document], Version]] | None = None,
) -> Document:
    """Upgrade ``data`` from ``from_version`` to ``to_version``, one step at a time.

    A newer *minor* version of the same major is additive by contract and is
    read as is. A newer *major* version is refused rather than guessed at: a
    downgrade that silently drops fields could drop an alarm setting. Every
    older version needs an explicit step; there is no silent pass-through.
    """
    steps = STEPS if steps is None else steps
    if from_version[0] > to_version[0]:
        raise MigrationError(
            f"configuration was written by a newer version {from_version}; "
            f"this version understands up to {to_version}"
        )

    version = from_version
    while version < to_version:
        if version not in steps:
            raise MigrationError(f"no migration step from version {version}")
        step, next_version = steps[version]
        if next_version <= version:
            raise MigrationError(f"migration step from {version} does not advance")
        data = step(data)
        version = next_version
    return data
