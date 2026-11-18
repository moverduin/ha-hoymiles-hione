"""Battery setting numbers for the Hoymiles HiOne integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory

from .entity import HiOneEntity, is_supported
from .write import async_write

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .api import HiOneApi
    from .data import HiOneConfigEntry

PARALLEL_UPDATES = 1

Writer = Callable[["HiOneApi", str, float], Coroutine[Any, Any, Any]]


async def _write_ems(api: HiOneApi, key: str, value: float) -> Any:
    return await api.async_set_ems({key: value})


async def _write_soc_limit(api: HiOneApi, key: str, value: float) -> Any:
    return await api.async_set_soc_limits(**{key: value})


@dataclass(frozen=True, kw_only=True)
class HiOneNumberEntityDescription(NumberEntityDescription):
    """Describes a writable HiOne setting."""

    writer: Writer = _write_ems


def _percent(
    key: str,
    minimum: float,
    maximum: float,
    *,
    battery: bool = True,
    writer: Writer = _write_ems,
) -> HiOneNumberEntityDescription:
    return HiOneNumberEntityDescription(
        key=key,
        translation_key=key,
        device_class=NumberDeviceClass.BATTERY if battery else None,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        writer=writer,
    )


NUMBERS: tuple[HiOneNumberEntityDescription, ...] = (
    _percent("self_use_reserve_soc", 10, 100),
    _percent("backup_reserve_soc", 60, 100),
    _percent("economic_reserve_soc", 10, 100),
    _percent("force_charge_target_soc", 10, 100),
    _percent("force_charge_power", 10, 100, battery=False),
    _percent("force_discharge_target_soc", 10, 100),
    _percent("force_discharge_power", 10, 100, battery=False),
    _percent("max_soc", 10, 100, writer=_write_soc_limit),
    _percent("min_soc", 10, 90, writer=_write_soc_limit),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: HiOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the setting numbers when write access is enabled."""
    data = entry.runtime_data
    if not data.controls_enabled:
        return
    async_add_entities(
        HiOneNumber(data.coordinator, description)
        for description in NUMBERS
        if is_supported(data.coordinator, (description.key,))
    )


class HiOneNumber(HiOneEntity, NumberEntity):
    """A writable battery setting."""

    entity_description: HiOneNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return (self.coordinator.data or {}).get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return True when the last poll produced a value."""
        return super().available and self.native_value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Write the new value."""
        entry = self.coordinator.config_entry
        description = self.entity_description
        await async_write(
            entry,
            lambda: description.writer(
                entry.runtime_data.api, description.key, value
            ),
        )
