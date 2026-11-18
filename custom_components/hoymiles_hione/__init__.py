"""
The Hoymiles HiOne integration.

Local Modbus TCP integration for Hoymiles HiOne home batteries.
https://github.com/moverduin/ha-hoymiles-hione
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .api import HiOneApi, HiOneError, HiOneModbusClient
from .const import (
    CONF_ENABLE_CONTROLS,
    CONF_FRAMER,
    CONF_LAYOUT,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FRAMER_RTU_OVER_TCP,
)
from .coordinator import HiOneCoordinator
from .data import HiOneData
from .registers import Layout
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .data import HiOneConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:  # noqa: ARG001
    """Register the integration services."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HiOneConfigEntry) -> bool:
    """Set up a HiOne from a config entry."""
    client = HiOneModbusClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_UNIT_ID],
        rtu_over_tcp=entry.data.get(CONF_FRAMER) == FRAMER_RTU_OVER_TCP,
    )
    api = HiOneApi(client, Layout(entry.data.get(CONF_LAYOUT, Layout.G3)))
    try:
        device = await api.async_get_device_info()
    except HiOneError as err:
        await api.async_close()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"error": str(err)},
        ) from err

    coordinator = HiOneCoordinator(
        hass,
        entry,
        api,
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    entry.runtime_data = HiOneData(
        api=api,
        coordinator=coordinator,
        device=device,
        controls_enabled=entry.options.get(CONF_ENABLE_CONTROLS, False),
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await api.async_close()
        raise

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HiOneConfigEntry) -> bool:
    """Unload a config entry and close the Modbus connection."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.api.async_close()
    return unloaded
