"""Diagnostics support for the Hoymiles HiOne integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import HiOneConfigEntry

TO_REDACT = {CONF_HOST, "serial_number", "unique_id", "title"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: HiOneConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = entry.runtime_data
    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "unique_id": entry.unique_id,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "device": async_redact_data(asdict(data.device), TO_REDACT),
        "unsupported_registers": sorted(data.api.unsupported),
        "read_plan": [
            {"table": b.table.value, "start": b.start, "count": b.count}
            for b in data.api.blocks
        ],
        "last_update_success": data.coordinator.last_update_success,
        "values": data.coordinator.data,
    }
