"""Binary sensors for the Hoymiles HiOne integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .entity import HiOneEntity, is_supported
from .registers import decode_faults

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import HiOneConfigEntry

PARALLEL_UPDATES = 0

METER_ONLINE = (1, 3)


@dataclass(frozen=True, kw_only=True)
class HiOneBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a HiOne binary sensor."""

    keys: tuple[str, ...]
    value_fn: Callable[[dict[str, Any]], bool | None]


def _fault(data: dict[str, Any]) -> bool | None:
    faults = decode_faults(data)
    return None if faults is None else bool(faults)


def _equals(key: str, accepted: tuple[int, ...]) -> Callable[[dict], bool | None]:
    def value(data: dict[str, Any]) -> bool | None:
        raw = data.get(key)
        return None if raw is None else raw in accepted

    return value


BINARY_SENSORS: tuple[HiOneBinarySensorEntityDescription, ...] = (
    HiOneBinarySensorEntityDescription(
        key="fault",
        translation_key="fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        keys=("battery_fault_bits", "dsp_pwr_fault_bits", "dsp_saf_fault_bits"),
        value_fn=_fault,
    ),
    HiOneBinarySensorEntityDescription(
        key="battery_connected",
        translation_key="battery_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        keys=("battery_link",),
        value_fn=_equals("battery_link", (1,)),
    ),
    HiOneBinarySensorEntityDescription(
        key="meter_connected",
        translation_key="meter_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        keys=("meter_status",),
        value_fn=_equals("meter_status", METER_ONLINE),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: HiOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HiOne binary sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        HiOneBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
        if is_supported(coordinator, description.keys)
    )


class HiOneBinarySensor(HiOneEntity, BinarySensorEntity):
    """A HiOne binary sensor."""

    entity_description: HiOneBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def available(self) -> bool:
        """Return True when the last poll produced a value."""
        return super().available and self.is_on is not None
