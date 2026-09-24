"""Config flow: accept the disclaimer, name the area and scenario, pick the
zone, confirm its trigger.

And the Configure step, which is one thing only: an administrator recovering
access (SPEC §8.2, decisions 109, 110). Everything else is the panel's.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import (
    CONF_AREA_NAME,
    CONF_DISCLAIMER,
    CONF_SCENARIO_NAME,
    CONF_TRIGGER_STATES,
    CONF_ZONE_ENTITY,
    DISCLAIMER_VERSION,
    DOMAIN,
)
from .core.proposals import SUPPORTED_DOMAINS, invalid_trigger_states, propose_trigger

CONF_CONFIRM = "confirm_trigger"
CONF_ACCEPT = "accept_disclaimer"
CONF_ACCOUNT = "account"
CONF_CODE = "code"


class FoyerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return FoyerRecoveryFlow()

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """SPEC §20.4: what Foyer is and is not, before anything is set up.

        Read where the decision is made, and accepted with a tick rather than
        dismissed with a button: nothing is installed until it is (decision
        151). The entry keeps the version accepted and when.
        """
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_ACCEPT):
                self._data[CONF_DISCLAIMER] = {
                    "version": DISCLAIMER_VERSION,
                    "accepted_at": dt_util.utcnow().isoformat(),
                }
                return await self.async_step_setup()
            errors[CONF_ACCEPT] = "disclaimer_not_accepted"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ACCEPT, default=False): BooleanSelector()}
            ),
            errors=errors,
        )

    async def async_step_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data = {
                **self._data,
                CONF_AREA_NAME: user_input[CONF_AREA_NAME].strip(),
                CONF_SCENARIO_NAME: user_input[CONF_SCENARIO_NAME].strip(),
                CONF_ZONE_ENTITY: user_input[CONF_ZONE_ENTITY],
            }
            return await self.async_step_trigger()

        return self.async_show_form(
            step_id="setup",
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


class FoyerRecoveryFlow(OptionsFlow):
    """Recover access for an administrator's account, loudly (§8.2).

    Home Assistant opens this step to administrators only and does not say
    which one: the step asks for the account, among administrators' only.
    Once the write has been tried it is said in the log — as failed, if it
    failed — and, when written, in a Home Assistant notification and to
    every enabled contact (api/recovery).
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        from .api.recovery import async_accounts, async_recover
        from .runtime.system import FoyerSystem

        system = self.hass.data.get(DOMAIN)
        if not isinstance(system, FoyerSystem) or system.superseded:
            return self.async_abort(reason="not_loaded")
        accounts = await async_accounts(self.hass)
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await async_recover(
                self.hass,
                system,
                user_input[CONF_ACCOUNT],
                str(user_input.get(CONF_CODE) or "").strip(),
            )
            if error is None:
                # Nothing of its own to store: the recovery is in the
                # configuration Foyer keeps, and the entry keeps its options.
                return self.async_create_entry(data=dict(self.config_entry.options))
            errors["base"] = error
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCOUNT): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=value, label=label)
                                for value, label in accounts.items()
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_CODE): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            description_placeholders={
                "length": str(system.config.settings.security.code_length)
            },
            errors=errors,
        )
