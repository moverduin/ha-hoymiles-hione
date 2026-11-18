"""Config flow for the Hoymiles HiOne integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import HiOneApi, HiOneConnectionError, HiOneError, HiOneModbusClient
from .const import (
    CONF_ENABLE_CONTROLS,
    CONF_FRAMER,
    CONF_LAYOUT,
    CONF_UNIT_ID,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    FRAMER_RTU_OVER_TCP,
    FRAMER_TCP,
    LOGGER,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .registers import Layout, Table

if TYPE_CHECKING:
    from .data import HiOneConfigEntry

SOC_ADDRESS = 1909


def _connection_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): (
                TextSelector()
            ),
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_UNIT_ID, default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=247, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_FRAMER, default=defaults.get(CONF_FRAMER, FRAMER_TCP)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[FRAMER_TCP, FRAMER_RTU_OVER_TCP],
                    translation_key=CONF_FRAMER,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_LAYOUT, default=defaults.get(CONF_LAYOUT, Layout.G3.value)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[layout.value for layout in Layout],
                    translation_key=CONF_LAYOUT,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _normalise(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_HOST: str(user_input[CONF_HOST]).strip(),
        CONF_PORT: int(user_input[CONF_PORT]),
        CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
        CONF_FRAMER: user_input[CONF_FRAMER],
        CONF_LAYOUT: user_input[CONF_LAYOUT],
    }


async def _async_probe(data: dict[str, Any]) -> tuple[str, str]:
    """Connect to the device and return (unique_id, title)."""
    client = HiOneModbusClient(
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_UNIT_ID],
        rtu_over_tcp=data[CONF_FRAMER] == FRAMER_RTU_OVER_TCP,
    )
    api = HiOneApi(client, Layout(data[CONF_LAYOUT]))
    try:
        info = await api.async_get_device_info()
        # The SOC register proves this really is a Hoymiles storage system.
        await client.async_read(Table.INPUT, SOC_ADDRESS, 1)
    finally:
        await api.async_close()
    unique_id = info.serial_number or (
        f"{data[CONF_HOST]}:{data[CONF_PORT]}:{data[CONF_UNIT_ID]}"
    )
    title = info.model or DEFAULT_MODEL
    return unique_id, title


class HiOneConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI setup of a HiOne."""

    VERSION = 1

    async def _async_try(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> tuple[dict[str, Any], str, str] | None:
        data = _normalise(user_input)
        try:
            unique_id, title = await _async_probe(data)
        except HiOneConnectionError:
            errors["base"] = "cannot_connect"
        except HiOneError:
            errors["base"] = "not_supported"
        except Exception:  # noqa: BLE001 - surface any unexpected error as "unknown"
            LOGGER.exception("Unexpected error while connecting")
            errors["base"] = "unknown"
        else:
            return data, unique_id, title
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the connection details."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_HOST: str(user_input[CONF_HOST]).strip(),
                    CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
                }
            )
            result = await self._async_try(user_input, errors)
            if result is not None:
                data, unique_id, title = result
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the connection details of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            # The gateway serves one Modbus client: release the running connection
            # before probing, and restore it if the new settings are rejected.
            was_loaded = entry.state is ConfigEntryState.LOADED
            if was_loaded:
                await self.hass.config_entries.async_unload(entry.entry_id)
            result = await self._async_try(user_input, errors)
            if result is not None and result[1] == entry.unique_id:
                return self.async_update_reload_and_abort(entry, data=result[0])
            if was_loaded:
                await self.hass.config_entries.async_setup(entry.entry_id)
            if result is not None:
                return self.async_abort(reason="wrong_device")
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(user_input or dict(entry.data)),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: HiOneConfigEntry) -> HiOneOptionsFlow:  # noqa: ARG004
        """Return the options flow."""
        return HiOneOptionsFlow()


class HiOneOptionsFlow(OptionsFlowWithReload):
    """Polling interval and write access."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_ENABLE_CONTROLS: bool(user_input[CONF_ENABLE_CONTROLS]),
                }
            )
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_ENABLE_CONTROLS,
                    default=options.get(CONF_ENABLE_CONTROLS, False),
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
