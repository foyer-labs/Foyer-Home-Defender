"""What Foyer's alarm panels tell Home Assistant about codes (SPEC §13, §8.2,
decision 136).

`code_arm_required` is one answer for everybody, and Home Assistant acts on
it before Foyer sees who is asking: while it is true, a codeless arming is
refused by Home Assistant itself. These tests pin down when it may be true,
that an exempt person then reaches the backend from Home Assistant's own
actions, and what the backend says to everybody else.
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context
from homeassistant.exceptions import ServiceValidationError
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import MASTER, PANEL_ENTITY
from .test_part2 import _ws
from .test_phase2 import CODE, OTHER, _config, _make_user, _me


def _attrs(hass, entity_id: str) -> dict:
    return dict(hass.states.get(entity_id).attributes)


async def _save(hass, client, kind: str, item: dict) -> None:
    result = await _ws(
        client,
        {"type": "foyer/config/save", "kind": kind, "item": item, "code": CODE},
    )
    assert result["success"], result
    # The save reloads the entry; the panels read the new policy after it.
    await hass.async_block_till_done()


async def _policy(hass, client, **policy) -> None:
    config = await _config(client)
    result = await _ws(
        client,
        {
            "type": "foyer/config/security",
            "code_policy": policy,
            "security": config["settings"]["security"],
            "code": CODE,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()


async def _arming_asks_a_code(hass, client) -> None:
    """The one area asks for a code to arm; the installation does not."""
    area = (await _config(client))["areas"][0]
    await _save(hass, client, "area", {**area, "require_code_to_arm": True})


async def _arm(
    hass, entity_id: str, user_id: str | None, service: str = "alarm_arm_away", **data
) -> None:
    await hass.services.async_call(
        "alarm_control_panel",
        service,
        {"entity_id": entity_id, **data},
        blocking=True,
        context=Context(user_id=user_id),
    )
    await hass.async_block_till_done()


async def _home_mode(hass, client) -> None:
    """A second scenario on the same area, armed as armed_home, asking
    nothing of its own."""
    away = (await _config(client))["scenarios"][0]
    home = {
        key: value
        for key, value in away.items()
        if key not in ("id", "require_code_to_arm", "require_code_to_disarm")
    }
    await _save(
        hass,
        client,
        "scenario",
        {**home, "name": "In casa", "ha_master_state": "armed_home"},
    )


async def _rows(hass, event_type: str) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    result = await system.log.async_query(limit=200, categories=["arming"])
    return [r for r in result["rows"] if r["event_type"] == event_type]


# --- while nobody is exempt, Home Assistant asks -----------------------------------


async def test_nobody_exempt_and_a_code_to_arm_tells_home_assistant_so(
    hass, hass_ws_client, loaded
):
    """Then Home Assistant refusing a codeless arming refuses nobody Foyer
    would have armed, and its dialog and tiles keep asking for the code."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    # The default policy asks no code to arm.
    assert _attrs(hass, PANEL_ENTITY)["code_arm_required"] is False
    assert _attrs(hass, MASTER)["code_arm_required"] is False

    await _arming_asks_a_code(hass, client)

    for entity_id in (PANEL_ENTITY, MASTER):
        assert _attrs(hass, entity_id)["code_arm_required"] is True
        assert _attrs(hass, entity_id)["code_format"] == "number"


async def test_before_anybody_holds_a_code_nothing_is_asked(hass, loaded):
    """Decision 78: the policy is inert, so no field and nothing required."""
    for entity_id in (PANEL_ENTITY, MASTER):
        assert _attrs(hass, entity_id)["code_arm_required"] is False
        assert _attrs(hass, entity_id)["code_format"] is None


# --- once somebody is exempt, Foyer answers ---------------------------------------


async def test_an_exempt_person_arms_from_home_assistants_panel_without_a_code(
    hass, hass_ws_client, loaded
):
    """The case decision 136 exists for: on beta.21 Home Assistant refused
    this with its own message before Foyer knew who was asking."""
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me)
    await _arming_asks_a_code(hass, client)
    assert _attrs(hass, PANEL_ENTITY)["code_arm_required"] is True

    person = hass.data[DOMAIN].config.users[0]
    await _make_user(hass, client, id=person.id, ha_user_id=me, exempt=True, code=CODE)

    # The configuration change is followed: the entities were rebuilt.
    for entity_id in (PANEL_ENTITY, MASTER):
        assert _attrs(hass, entity_id)["code_arm_required"] is False
        # The field stays: everybody else may still be asked.
        assert _attrs(hass, entity_id)["code_format"] == "number"

    await _arm(hass, PANEL_ENTITY, me)
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.ARMING
    assert not await _rows(hass, "arm_rejected")


async def test_the_master_arms_an_exempt_person_without_a_code(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me, exempt=True)
    await _arming_asks_a_code(hass, client)
    assert _attrs(hass, MASTER)["code_arm_required"] is False

    await _arm(hass, MASTER, me)
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.ARMING


async def test_anybody_else_is_asked_by_foyer_and_told_where_to_type_it(
    hass, hass_ws_client, loaded, hass_read_only_user
):
    """Somebody is exempt, so Home Assistant passes the arming on and the
    backend refuses it (INV-2), with a row in the log. Its dialog and tiles
    no longer ask, so the refusal names where a code can be typed."""
    client = await hass_ws_client(hass)
    # Exempt, and another account: the flag is false for everybody.
    await _make_user(
        hass, client, new_code=CODE, ha_user_id=hass_read_only_user.id, exempt=True
    )
    await _arming_asks_a_code(hass, client)
    assert _attrs(hass, PANEL_ENTITY)["code_arm_required"] is False

    for entity_id in (PANEL_ENTITY, MASTER):
        with pytest.raises(ServiceValidationError) as refused:
            await _arm(hass, entity_id, await _me(client))
        assert refused.value.translation_domain == DOMAIN
        assert refused.value.translation_key == "panel_arm_code_required"
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.DISARMED

    rows = await _rows(hass, "arm_rejected")
    assert len(rows) == 2
    assert {r["detail"]["reason"] for r in rows} == {"code_required"}
    assert {r["channel"] for r in rows} == {"ha_ui"}


async def test_an_automation_never_buys_the_exemption_through_the_panel(
    hass, hass_ws_client, loaded
):
    """An automation identifies nobody (§8.2), so Foyer asks it for the code
    whenever the policy does, exempt people in the house or not."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass, client, new_code=CODE, ha_user_id=await _me(client), exempt=True
    )
    await _arming_asks_a_code(hass, client)

    with pytest.raises(ServiceValidationError) as refused:
        await _arm(hass, PANEL_ENTITY, None)
    assert refused.value.translation_key == "panel_arm_code_required"
    rows = await _rows(hass, "arm_rejected")
    assert [r["channel"] for r in rows] == ["automation"]

    await _arm(hass, PANEL_ENTITY, None, code=CODE)
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.ARMING


async def test_a_disarm_keeps_the_message_every_other_path_gives(
    hass, hass_ws_client, loaded
):
    """Only an arming is told where to type: the dialog and the tiles ask
    for a code to disarm whenever there is a field, as they always did."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass, client, new_code=CODE, ha_user_id=await _me(client), exempt=True
    )
    await _arm(hass, PANEL_ENTITY, None)
    with pytest.raises(ServiceValidationError) as refused:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_disarm",
            {"entity_id": PANEL_ENTITY},
            blocking=True,
        )
    assert refused.value.translation_key == "rejected_code_required"


async def test_a_disabled_exempt_person_exempts_nobody(
    hass, hass_ws_client, loaded, hass_read_only_user
):
    """§13 says no *enabled* user: a disabled person cannot arm at all, so
    their exemption must not stop Home Assistant asking everybody else."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    guest = await _make_user(
        hass,
        client,
        name="Ospite",
        new_code=OTHER,
        ha_user_id=hass_read_only_user.id,
        exempt=True,
        enabled=False,
        code=CODE,
    )
    await _arming_asks_a_code(hass, client)

    for entity_id in (PANEL_ENTITY, MASTER):
        assert _attrs(hass, entity_id)["code_arm_required"] is True

    await _make_user(
        hass,
        client,
        id=guest,
        name="Ospite",
        ha_user_id=hass_read_only_user.id,
        exempt=True,
        code=CODE,
    )
    for entity_id in (PANEL_ENTITY, MASTER):
        assert _attrs(hass, entity_id)["code_arm_required"] is False


# --- the master follows the house --------------------------------------------------


async def test_a_change_of_mode_is_not_sent_to_the_alarm_panel_card(
    hass, hass_ws_client, loaded
):
    """Home Assistant's alarm panel card offers arming only while the entity
    is disarmed. With the house already armed, arming another mode from the
    master is a change of scenario, which asks a code by default while
    arming does not: the refusal names only the places that can take it."""
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me)
    await _home_mode(hass, client)

    await _arm(hass, MASTER, me, "alarm_arm_home")
    assert hass.states.get(MASTER).state == AlarmControlPanelState.ARMING
    # Arming asks no code, so Home Assistant passes the change on.
    assert _attrs(hass, MASTER)["code_arm_required"] is False

    with pytest.raises(ServiceValidationError) as refused:
        await _arm(hass, MASTER, me)
    assert refused.value.translation_domain == DOMAIN
    assert refused.value.translation_key == "panel_arm_code_required_not_disarmed"
    rows = await _rows(hass, "arm_rejected")
    assert [r["detail"]["reason"] for r in rows] == ["code_required"]

    # With the code, from wherever it was typed, the change goes through.
    await _arm(hass, MASTER, me, code=CODE)
    away = hass.data[DOMAIN].config.scenarios[0]
    assert hass.data[DOMAIN].state.active_scenario_id == away.id


async def test_an_area_armed_on_its_own_no_longer_asks_through_the_master(
    hass, hass_ws_client, loaded
):
    """Arming the scenario leaves an area already armed on its own as it is,
    so that area's setting has no say: Foyer arms the rest with no code, and
    Home Assistant must not refuse it first."""
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me)
    await _arming_asks_a_code(hass, client)
    assert _attrs(hass, MASTER)["code_arm_required"] is True

    await _arm(hass, PANEL_ENTITY, me, code=CODE)
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.ARMING
    assert _attrs(hass, MASTER)["code_arm_required"] is False

    await _arm(hass, MASTER, me)
    away = hass.data[DOMAIN].config.scenarios[0]
    assert hass.data[DOMAIN].state.active_scenario_id == away.id
    assert not await _rows(hass, "arm_rejected")


async def test_a_running_mode_with_nothing_left_to_arm_has_no_say(
    hass, hass_ws_client, loaded
):
    """Once In casa runs, arming it again is refused whatever the code, and
    the only mode still to arm asks for one: Home Assistant's dialog and
    tiles are told so, and ask."""
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me)
    away = (await _config(client))["scenarios"][0]
    await _save(hass, client, "scenario", {**away, "require_code_to_arm": True})
    await _home_mode(hass, client)
    # Away asks: with one answer for both modes, the dialog asks (decision 143).
    assert _attrs(hass, MASTER)["code_arm_required"] is True

    await _arm(hass, MASTER, me, "alarm_arm_home", code=CODE)
    assert _attrs(hass, MASTER)["code_arm_required"] is True

    with pytest.raises(ServiceValidationError) as refused:
        await _arm(hass, MASTER, me)
    # Refused by Home Assistant itself, as Foyer would have refused it.
    assert refused.value.translation_domain == "alarm_control_panel"
    assert refused.value.translation_key == "code_arm_required"


# --- the master reads every area and scenario -------------------------------------


async def test_the_master_offers_a_field_where_only_a_scenario_asks(
    hass, hass_ws_client, loaded
):
    """Read from the installation's policy alone, the master had no field
    here, and nowhere to type the code the scenario then asked for."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    await _policy(hass, client, arm=False, disarm=False)
    assert _attrs(hass, MASTER)["code_format"] is None

    scenario = (await _config(client))["scenarios"][0]
    await _save(hass, client, "scenario", {**scenario, "require_code_to_arm": True})

    assert _attrs(hass, MASTER)["code_format"] == "number"
    # Its only scenario asks, and nobody is exempt: the master says so.
    assert _attrs(hass, MASTER)["code_arm_required"] is True
    # The area on its own asks for nothing.
    assert _attrs(hass, PANEL_ENTITY)["code_format"] is None
    assert _attrs(hass, PANEL_ENTITY)["code_arm_required"] is False


async def test_the_master_asks_as_soon_as_one_scenario_it_arms_asks(
    hass, hass_ws_client, loaded
):
    """Decision 143: one answer for every mode, and the household chose the
    dialog asking. While one mode needs a code, Home Assistant asks for it —
    and refuses a codeless arming of the mode that needs none, which still
    arms through Foyer's own service."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    await _policy(hass, client, arm=False, disarm=False)
    config = await _config(client)
    away = config["scenarios"][0]
    await _save(hass, client, "scenario", {**away, "require_code_to_arm": True})
    home = {
        key: value
        for key, value in away.items()
        if key not in ("id", "require_code_to_arm")
    }
    await _save(
        hass,
        client,
        "scenario",
        {**home, "name": "In casa", "ha_master_state": "armed_home"},
    )

    assert _attrs(hass, MASTER)["code_arm_required"] is True
    assert _attrs(hass, MASTER)["code_format"] == "number"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_home",
            {"entity_id": MASTER},
            blocking=True,
        )
    await hass.async_block_till_done()
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.DISARMED

    # The same mode, through Foyer's service, needs no code.
    home_id = next(
        s["id"] for s in (await _config(client))["scenarios"] if s["name"] == "In casa"
    )
    await hass.services.async_call(
        "foyer", "arm", {"scenario_id": home_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.ARMING


async def test_the_master_offers_a_field_where_only_an_area_asks(
    hass, hass_ws_client, loaded
):
    """An area in no scenario is disarmed by the master's disarm, on its own
    terms: its setting alone has to draw the master's field."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    await _policy(hass, client, arm=False, disarm=False)
    assert _attrs(hass, MASTER)["code_format"] is None

    await _save(
        hass,
        client,
        "area",
        {
            "name": "Garage",
            "ha_state_when_armed": "armed_away",
            "require_code_to_disarm": True,
        },
    )

    assert _attrs(hass, MASTER)["code_format"] == "number"
    assert _attrs(hass, "alarm_control_panel.foyer_garage")["code_format"] == "number"
    assert _attrs(hass, PANEL_ENTITY)["code_format"] is None


async def test_an_area_panel_offers_a_field_for_the_scenario_that_armed_it(
    hass, hass_ws_client, loaded
):
    """The area's disarm hears the scenario that armed it (§8.2). Home
    Assistant's dialog asks for a disarm code only while there is a field, so
    without one no Home Assistant screen could disarm this area."""
    client = await hass_ws_client(hass)
    me = await _me(client)
    await _make_user(hass, client, new_code=CODE, ha_user_id=me)
    await _policy(hass, client, arm=False, disarm=False)
    assert _attrs(hass, PANEL_ENTITY)["code_format"] is None

    away = (await _config(client))["scenarios"][0]
    await _save(hass, client, "scenario", {**away, "require_code_to_disarm": True})
    assert _attrs(hass, PANEL_ENTITY)["code_format"] == "number"

    await _arm(hass, MASTER, me)
    with pytest.raises(ServiceValidationError) as refused:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_disarm",
            {"entity_id": PANEL_ENTITY},
            blocking=True,
            context=Context(user_id=me),
        )
    assert refused.value.translation_key == "rejected_code_required"

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY, "code": CODE},
        blocking=True,
        context=Context(user_id=me),
    )
    await hass.async_block_till_done()
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.DISARMED
