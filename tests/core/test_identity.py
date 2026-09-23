"""Identity: who is asking, whether they may, and what a code changes.

SPEC §8.2, §8.3, §8.4. Nothing here verifies a code — that is security/'s
work, and it needs bcrypt and no Home Assistant either (tests/core/test_codes).
What is tested here is what the engine does once it has been told.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core import authz
from custom_components.foyer.core.models import (
    Channel,
    CodePolicy,
    CodeResult,
    KeyAction,
    KeyCommand,
    Moment,
    Operation,
    Permission,
    Reason,
    ZoneType,
)
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import NOW, World, make_house, user, zone


def house(**changes) -> World:
    """A house with one user, so the policy is in force (decision 78)."""
    changes.setdefault("users", (user(),))
    return World(replace(make_house(), **changes))


def typed(**kwargs) -> dict:
    """A request carrying a code that verified, from the panel."""
    return {
        "code": CodeResult.VALID,
        "user_id": "luca",
        "channel": "ha_ui",
        **kwargs,
    }


# --- the policy is inert until somebody holds a code (decision 78) --------------


def test_without_users_nothing_asks_for_a_code():
    world = World(make_house())  # no users at all
    assert world.disarm.__self__ is world  # (guard: the helper is the world's)
    world.arm("night")
    world.advance(5)
    assert world.disarm().accepted


def test_a_user_with_a_code_puts_the_policy_in_force():
    world = house()
    world.arm("night")
    world.advance(5)
    assert world.disarm().reason is Reason.CODE_REQUIRED
    assert world.disarm(**typed()).accepted


def test_a_user_without_a_code_does_not_put_it_in_force():
    """A half-finished user — created, no code yet — must not lock the house."""
    world = house(users=(user(code_hash=None),))
    world.arm("night")
    world.advance(5)
    assert world.disarm().accepted


def test_an_expired_guest_does_not_keep_the_policy_in_force():
    world = house(users=(user(valid_until=NOW - timedelta(days=1)),))
    world.arm("night")
    world.advance(5)
    assert world.disarm().accepted


# --- resolution (§8.2) ---------------------------------------------------------


def test_arming_needs_no_code_and_disarming_does():
    world = house()
    assert world.arm("night").accepted
    world.advance(5)
    assert world.disarm().reason is Reason.CODE_REQUIRED


def test_an_area_can_ask_for_a_code_to_arm():
    config = make_house()
    areas = tuple(
        replace(a, require_code_to_arm=True) if a.id == "ground" else a
        for a in config.areas
    )
    world = house(areas=areas)
    assert world.arm("night").reason is Reason.CODE_REQUIRED
    assert world.arm("night", **typed()).accepted


def test_the_strictest_explicit_setting_wins():
    """Decision 80: a permissive scenario cannot open a protected area."""
    config = make_house()
    areas = tuple(
        replace(a, require_code_to_arm=True) if a.id == "ground" else a
        for a in config.areas
    )
    scenarios = tuple(replace(s, require_code_to_arm=False) for s in config.scenarios)
    world = house(areas=areas, scenarios=scenarios)

    # "night" arms the ground floor, which asks for a code whatever the
    # scenario says. "away" would too; an area outside it would not.
    assert world.arm("night").reason is Reason.CODE_REQUIRED

    relaxed = house(
        areas=tuple(replace(a, require_code_to_arm=False) for a in config.areas),
        scenarios=scenarios,
        code_policy=CodePolicy(arm=True),
    )
    assert relaxed.arm("night").accepted


# --- the per-user exemption (decision 79) --------------------------------------


def test_the_exemption_applies_only_on_a_channel_that_identifies():
    exempt = user(code_exempt_when_identified=True, ha_user_id="ha-1")
    world = house(users=(exempt,))
    world.arm("night")
    world.advance(5)

    # From the panel, identified, no code typed: accepted.
    assert world.disarm(user_id="luca", channel="ha_ui", identified=True).accepted

    world.arm("night")
    world.advance(5)
    # The same person at a shared keypad: the code IS the identity there.
    assert (
        world.disarm(user_id="luca", channel="keypad", identified=True).reason
        is Reason.CODE_REQUIRED
    )


def test_without_the_switch_even_an_identified_admin_types_the_code():
    world = house()
    world.arm("night")
    world.advance(5)
    refused = world.disarm(
        user_id="luca", channel="ha_ui", identified=True, is_admin=True
    )
    assert refused.reason is Reason.CODE_REQUIRED


# --- permissions and scope (§8.3, §8.1, §4.6) ----------------------------------


def test_a_permission_the_ui_hides_is_still_refused_when_sent_by_hand():
    limited = user(permissions=frozenset({Permission.ARM}))
    world = house(users=(limited,))
    world.arm("night", **typed())
    world.advance(5)
    assert world.disarm(**typed()).reason is Reason.NOT_PERMITTED


def test_a_user_outside_their_validity_window_is_refused():
    guest = user(valid_from=NOW + timedelta(days=1))
    world = house(users=(guest, user("other", "Other")))
    assert world.arm("night", **typed()).reason is Reason.USER_NOT_VALID


def test_a_disabled_user_is_refused():
    world = house(users=(user(enabled=False), user("other", "Other")))
    assert world.arm("night", **typed()).reason is Reason.USER_NOT_VALID


def test_an_area_outside_the_users_scope_is_refused():
    world = house(users=(user(allowed_area_ids=("upstairs",)),))
    assert world.arm("night", **typed()).reason is Reason.AREA_NOT_ALLOWED


def test_a_scenario_can_name_who_may_use_it():
    config = make_house()
    scenarios = tuple(
        replace(s, allowed_user_ids=("someone_else",)) if s.id == "night" else s
        for s in config.scenarios
    )
    world = house(scenarios=scenarios)
    assert world.arm("night", **typed()).reason is Reason.SCENARIO_NOT_ALLOWED
    assert world.arm("away", **typed()).accepted


# --- wrong codes and lockout (§8.4) --------------------------------------------


def wrong(**kwargs) -> dict:
    return {"code": CodeResult.INVALID, "channel": "keypad", **kwargs}


def test_a_wrong_code_is_refused_and_recorded():
    world = house()
    decision = world.arm("night", **wrong())

    assert decision.reason is Reason.BAD_CODE
    assert Moment.CODE_REJECTED in decision.moments
    # Nothing in the answer says whose code it nearly was.
    rejected = next(o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED)
    assert "luca" not in str(dict(rejected.detail))


def test_five_wrong_codes_lock_that_channel_and_not_another():
    world = house()
    for _ in range(4):
        assert world.arm("night", **wrong()).reason is Reason.BAD_CODE
    fifth = world.arm("night", **wrong())
    assert Moment.LOCKOUT in fifth.moments

    # Even a correct code is refused now, and the refusal says why.
    assert world.arm("night", **typed(channel="keypad")).reason is Reason.LOCKED_OUT
    # The hall keypad's trouble is not the garden keypad's.
    assert world.arm("night", **wrong(device_id="garden")).reason is Reason.BAD_CODE


def test_the_lockout_ends_and_the_next_one_is_longer():
    world = house()
    for _ in range(5):
        world.arm("night", **wrong())
    world.advance(300)
    assert world.arm("night", **typed(channel="keypad")).accepted

    world.advance(5)
    world.disarm(**typed(channel="keypad"))
    for _ in range(5):
        world.arm("night", **wrong())
    locked = world.state.lockouts["keypad:"]
    assert (locked.until - world.now).total_seconds() == 600


def test_failures_outside_the_window_do_not_add_up():
    world = house()
    for _ in range(4):
        world.arm("night", **wrong())
    world.advance(301)
    assert Moment.LOCKOUT not in world.arm("night", **wrong()).moments


def test_a_correct_code_forgets_the_failures_before_it():
    world = house()
    for _ in range(4):
        world.arm("night", **wrong())
    world.arm("night", **typed(channel="keypad"))
    world.advance(5)
    world.disarm(**typed(channel="keypad"))
    for _ in range(4):
        world.arm("night", **wrong())
    assert "keypad:" not in world.state.lockouts or (
        world.state.lockouts["keypad:"].until is None
    )


def test_the_admin_path_is_never_locked_out():
    """§8.4: nobody may shut themselves out of their own house."""
    world = house()
    for _ in range(8):
        decision = world.arm("night", **wrong(channel="ha_ui", is_admin=True))
        assert decision.reason is Reason.BAD_CODE
        assert Moment.LOCKOUT not in decision.moments
    assert world.arm("night", **typed(is_admin=True)).accepted


def test_a_lockout_survives_a_restart():
    """INV-3. A lockout a restart clears is an invitation to restart."""
    world = house()
    for _ in range(5):
        world.arm("night", **wrong())
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.lockouts["keypad:"].until == world.state.lockouts["keypad:"].until


# --- duress (§8.1) -------------------------------------------------------------


def test_a_duress_code_disarms_exactly_as_the_ordinary_one_does():
    world = house()
    world.arm("night", **typed())
    world.advance(5)
    decision = world.disarm(**typed(duress=True))

    assert decision.accepted
    assert world.states()["ground"] == "disarmed"
    # The only trace is this, which the default profile can answer quietly.
    # Raised once, before the disarm it was used for, naming it — and on no
    # area, so nothing that is an area's to show shows it (decisions 131, 132).
    duress = [o for o in decision.occurrences if o.moment is Moment.DURESS]
    assert len(duress) == 1
    assert duress[0].detail["operation"] == "disarm"
    assert duress[0].area_id is None and duress[0].incident_id is None
    assert decision.moments.index(Moment.DURESS) < decision.moments.index(
        Moment.DISARMED
    )


def test_a_duress_code_is_its_owners_code_for_anything_else_too():
    """Not only disarming (decision 131): arming and excluding a zone get the
    answer the ordinary code gets, and one `duress` each. Every other
    operation is in tests/core/test_duress.py."""
    world = house()
    for decision in (
        world.arm("night", **typed(duress=True)),
        world.bypass("patio", **typed(duress=True)),
    ):
        assert decision.accepted
        assert decision.moments.count(Moment.DURESS) == 1


# --- key zones carry identity and no code (§4.7, §9.3) -------------------------


def test_a_key_zone_arms_although_a_code_is_required_and_says_whose_key():
    key = zone(
        "key",
        "switch.key",
        "ground",
        type=ZoneType.KEY,
        channel=Channel.KEY,
        key=KeyAction(on_activate=KeyCommand.ARM, scenario_id="night", user_id="luca"),
    )
    config = replace(make_house(), users=(user(),))
    world = World(replace(config, zones=(*config.zones, key)))
    world.set("switch.key", "off")

    world.set("switch.key", "on")
    decision = world.advance(5)
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert armed.user_id == "luca"
    assert armed.user_name == "Luca"
    assert armed.channel == "key_zone"


def test_a_key_zone_still_obeys_the_permissions_of_the_user_it_names():
    key = zone(
        "key",
        "switch.key",
        "ground",
        type=ZoneType.KEY,
        channel=Channel.KEY,
        key=KeyAction(on_activate=KeyCommand.ARM, scenario_id="night", user_id="guest"),
    )
    guest = user("guest", "Guest", permissions=frozenset({Permission.DISARM}))
    config = replace(make_house(), users=(user(), guest))
    world = World(replace(config, zones=(*config.zones, key)))
    world.set("switch.key", "off")

    decision = world.set("switch.key", "on")
    assert world.states()["ground"] == "disarmed"
    failed = next(o for o in decision.occurrences if o.moment is Moment.ARM_FAILED)
    assert failed.detail["reason"] == Reason.NOT_PERMITTED.value


# --- the resolution, read directly ---------------------------------------------


def test_code_required_reads_the_global_default_when_nothing_is_explicit():
    config = replace(make_house(), users=(user(),))
    assert authz.code_required(config, Operation.DISARM, now=NOW)
    assert not authz.code_required(config, Operation.ARM, now=NOW)


def test_every_operation_of_the_table_has_a_policy_entry():
    """§8.2 is one table: half of it is how a setting quietly goes missing."""
    policy = CodePolicy()
    for operation in Operation:
        assert isinstance(policy.requires_code(operation), bool)
