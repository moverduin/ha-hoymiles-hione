"""Services for the Hoymiles HiOne integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import ATTR_CONFIG_ENTRY_ID, DOMAIN, SERVICE_SET_EMS
from .registers import EMS_SETTINGS, WRITABLE_EMS_MODES
from .write import async_write

if TYPE_CHECKING:
    from .data import HiOneConfigEntry

_PERCENT = vol.All(vol.Coerce(float), vol.Range(min=0, max=100))

SET_EMS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Optional("ems_mode"): vol.In([mode.value for mode in WRITABLE_EMS_MODES]),
        **{
            vol.Optional(setting.key): _PERCENT
            for setting in EMS_SETTINGS
            if setting.key != "ems_mode"
        },
    }
)


def _get_entry(hass: HomeAssistant, entry_id: str) -> HiOneConfigEntry:
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_found",
            translation_placeholders={"entry_id": entry_id},
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"entry_id": entry_id},
        )
    return entry


async def _async_set_ems(call: ServiceCall) -> None:
    entry = _get_entry(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    changes = {k: v for k, v in call.data.items() if k != ATTR_CONFIG_ENTRY_ID}
    if not changes:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="nothing_to_set"
        )
    await async_write(entry, lambda: entry.runtime_data.api.async_set_ems(changes))


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration services."""
    hass.services.async_register(
        DOMAIN, SERVICE_SET_EMS, _async_set_ems, schema=SET_EMS_SCHEMA
    )
