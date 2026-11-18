"""EMS mode select for the Hoymiles HiOne integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory

from .entity import HiOneEntity, is_supported
from .registers import EMS_MODE_BY_VALUE, EmsMode
from .write import async_write

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import HiOneConfigEntry

PARALLEL_UPDATES = 1

EMS_MODE_SELECT = SelectEntityDescription(
    key="ems_mode_control",
    translation_key="ems_mode_control",
    entity_category=EntityCategory.CONFIG,
    options=[mode.value for mode in EmsMode],
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: HiOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the EMS mode select when write access is enabled."""
    data = entry.runtime_data
    if data.controls_enabled and is_supported(data.coordinator, ("ems_mode",)):
        async_add_entities([HiOneEmsModeSelect(data.coordinator, EMS_MODE_SELECT)])


class HiOneEmsModeSelect(HiOneEntity, SelectEntity):
    """Select the EMS operating mode (holding register 4300)."""

    @property
    def current_option(self) -> str | None:
        """Return the active mode."""
        raw = (self.coordinator.data or {}).get("ems_mode")
        mode = EMS_MODE_BY_VALUE.get(raw) if raw is not None else None
        return mode.value if mode else None

    async def async_select_option(self, option: str) -> None:
        """Write the new mode (the whole EMS block is written with FC16)."""
        entry = self.coordinator.config_entry
        await async_write(
            entry, lambda: entry.runtime_data.api.async_set_ems({"ems_mode": option})
        )
