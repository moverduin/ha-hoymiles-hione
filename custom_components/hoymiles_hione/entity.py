"""Base entity for the Hoymiles HiOne integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import HiOneCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class HiOneEntity(CoordinatorEntity[HiOneCoordinator]):
    """An entity backed by one or more HiOne registers."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HiOneCoordinator, description: EntityDescription
    ) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        device = entry.runtime_data.device
        base_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{base_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, base_id)},
            manufacturer=MANUFACTURER,
            model=device.model or DEFAULT_MODEL,
            name=f"{MANUFACTURER} {device.model or DEFAULT_MODEL}",
            serial_number=device.serial_number,
            sw_version=device.system_version,
            hw_version=device.hardware_version,
        )


def is_supported(coordinator: HiOneCoordinator, keys: tuple[str, ...]) -> bool:
    """Return True when the device supports at least one of the registers."""
    unsupported = coordinator.api.unsupported
    return any(key not in unsupported for key in keys)
