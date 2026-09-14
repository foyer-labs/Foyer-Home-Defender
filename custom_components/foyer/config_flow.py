"""Config flow: name the area and scenario, pick the zone, confirm its trigger."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
import voluptuous as vol

from .const import (
    CONF_AREA_NAME,
    CONF_SCENARIO_NAME,
    CONF_TRIGGER_STATES,
    CONF_ZONE_ENTITY,
    DOMAIN,
)
from .core.proposals import SUPPORTED_DOMAINS, invalid_trigger_states, propose_trigger

CONF_CONFIRM = "confirm_trigger"


class FoyerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data = {
                CONF_AREA_NAME: user_input[CONF_AREA_NAME].strip(),
                CONF_SCENARIO_NAME: user_input[CONF_SCENARIO_NAME].strip(),
                CONF_ZONE_ENTITY: user_input[CONF_ZONE_ENTITY],
            }
            return await self.async_step_trigger()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_NAME): TextSelector(),
                    vol.Required(CONF_SCENARIO_NAME): TextSelector(),
                    vol.Required(CONF_ZONE_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain=list(SUPPORTED_DOMAINS))
                    ),
                }
            ),
        )

    async def async_step_trigger(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """INV-5: the trigger is proposed, then explicitly confirmed by the user."""
        entity_id = self._data[CONF_ZONE_ENTITY]
        state = self.hass.states.get(entity_id)
        proposal = propose_trigger(entity_id, state.state if state else None)
        errors: dict[str, str] = {}

        if user_input is not None:
            states = user_input.get(CONF_TRIGGER_STATES) or []
            if not states:
                errors[CONF_TRIGGER_STATES] = "no_trigger_states"
            elif invalid_trigger_states(states):
                errors[CONF_TRIGGER_STATES] = "fault_state_as_trigger"
            elif not user_input.get(CONF_CONFIRM):
                errors[CONF_CONFIRM] = "trigger_not_confirmed"
            else:
                return self.async_create_entry(
                    title=self._data[CONF_AREA_NAME],
                    data={**self._data, CONF_TRIGGER_STATES: sorted(set(states))},
                )

        return self.async_show_form(
            step_id="trigger",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TRIGGER_STATES,
                        default=list(
                            (user_input or {}).get(CONF_TRIGGER_STATES)
                            or proposal.proposed
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=list(proposal.options),
                            multiple=True,
                            custom_value=True,
                            mode=SelectSelectorMode.LIST,
                            translation_key="trigger_state",
                        )
                    ),
                    vol.Required(CONF_CONFIRM, default=False): BooleanSelector(),
                }
            ),
            description_placeholders={
                "entity": state.name if state else entity_id,
                "current_state": state.state if state else "unavailable",
            },
            errors=errors,
        )
