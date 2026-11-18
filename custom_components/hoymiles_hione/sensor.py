"""Sensors for the Hoymiles HiOne integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from .entity import HiOneEntity, is_supported
from .registers import (
    BATTERY_STATE,
    EMS_MODE_BY_VALUE,
    METER_STATUS,
    WORK_STATUS,
    decode_faults,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .data import HiOneConfigEntry

PARALLEL_UPDATES = 0

Values = dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class HiOneSensorEntityDescription(SensorEntityDescription):
    """Describes a HiOne sensor."""

    keys: tuple[str, ...] = ()
    value_fn: Callable[[Values], StateType] | None = None
    attr_fn: Callable[[Values], dict[str, Any]] | None = None

    @property
    def register_keys(self) -> tuple[str, ...]:
        """Registers this sensor depends on."""
        return self.keys or (self.key,)


def _negated(key: str) -> Callable[[Values], StateType]:
    def value(data: Values) -> StateType:
        raw = data.get(key)
        return None if raw is None else -raw

    return value


def _part(key: str, *, positive: bool) -> Callable[[Values], StateType]:
    def value(data: Values) -> StateType:
        raw = data.get(key)
        if raw is None:
            return None
        return max(raw, 0) if positive else max(-raw, 0)

    return value


def _mapped(key: str, mapping: dict[int, str]) -> Callable[[Values], StateType]:
    def value(data: Values) -> StateType:
        raw = data.get(key)
        return None if raw is None else mapping.get(raw)

    return value


def _fault_count(data: Values) -> StateType:
    faults = decode_faults(data)
    return None if faults is None else len(faults)


def _fault_attrs(data: Values) -> dict[str, Any]:
    return {"faults": decode_faults(data) or []}


def _hex(key: str) -> Callable[[Values], StateType]:
    def value(data: Values) -> StateType:
        raw = data.get(key)
        return None if raw is None else f"0x{raw:08X}"

    return value


def _power(
    key: str, *, enabled: bool = False, **kwargs: Any
) -> HiOneSensorEntityDescription:
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_registry_enabled_default=enabled,
        **kwargs,
    )


def _energy(key: str, *, enabled: bool = True) -> HiOneSensorEntityDescription:
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
        entity_registry_enabled_default=enabled,
    )


def _voltage(key: str, **kwargs: Any) -> HiOneSensorEntityDescription:
    kwargs.setdefault("entity_registry_enabled_default", False)
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        **kwargs,
    )


def _current(key: str, **kwargs: Any) -> HiOneSensorEntityDescription:
    kwargs.setdefault("entity_registry_enabled_default", False)
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        **kwargs,
    )


def _temperature(key: str, **kwargs: Any) -> HiOneSensorEntityDescription:
    kwargs.setdefault("entity_registry_enabled_default", False)
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        **kwargs,
    )


def _frequency(key: str) -> HiOneSensorEntityDescription:
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
    )


def _enum(
    key: str,
    register: str,
    mapping: dict[int, str],
    **kwargs: Any,
) -> HiOneSensorEntityDescription:
    return HiOneSensorEntityDescription(
        key=key,
        translation_key=key,
        keys=(register,),
        device_class=SensorDeviceClass.ENUM,
        options=sorted(set(mapping.values())),
        value_fn=_mapped(register, mapping),
        **kwargs,
    )


SENSORS: tuple[HiOneSensorEntityDescription, ...] = (
    # Status
    _enum("status", "work_status", WORK_STATUS),
    _enum("battery_state", "battery_state", BATTERY_STATE),
    _enum(
        "ems_mode",
        "ems_mode",
        {value: mode.value for value, mode in EMS_MODE_BY_VALUE.items()},
    ),
    _enum(
        "meter_status",
        "meter_status",
        METER_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Battery
    HiOneSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    HiOneSensorEntityDescription(
        key="battery_soh",
        translation_key="battery_soh",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _power("battery_power", enabled=True),
    _power(
        "battery_charge_power",
        enabled=True,
        keys=("battery_power",),
        value_fn=_part("battery_power", positive=False),
    ),
    _power(
        "battery_discharge_power",
        enabled=True,
        keys=("battery_power",),
        value_fn=_part("battery_power", positive=True),
    ),
    _voltage("battery_voltage", entity_registry_enabled_default=True),
    _current("battery_current"),
    _current(
        "battery_max_charge_current",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
    ),
    _current(
        "battery_max_discharge_current", entity_category=EntityCategory.DIAGNOSTIC
    ),
    _voltage(
        "battery_charge_cutoff_voltage", entity_category=EntityCategory.DIAGNOSTIC
    ),
    _voltage(
        "battery_discharge_cutoff_voltage", entity_category=EntityCategory.DIAGNOSTIC
    ),
    HiOneSensorEntityDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _temperature("cell_temperature_max", entity_registry_enabled_default=True),
    _temperature("cell_temperature_min", entity_registry_enabled_default=True),
    # Grid (house connection meter)
    _power(
        "grid_power",
        enabled=True,
        keys=("grid_power_raw",),
        value_fn=_negated("grid_power_raw"),
    ),
    _power(
        "grid_power_l1",
        keys=("grid_power_l1_raw",),
        value_fn=_negated("grid_power_l1_raw"),
    ),
    _power(
        "grid_power_l2",
        keys=("grid_power_l2_raw",),
        value_fn=_negated("grid_power_l2_raw"),
    ),
    _power(
        "grid_power_l3",
        keys=("grid_power_l3_raw",),
        value_fn=_negated("grid_power_l3_raw"),
    ),
    _voltage("grid_voltage_l1"),
    _voltage("grid_voltage_l2"),
    _voltage("grid_voltage_l3"),
    _current("grid_current_l1"),
    _current("grid_current_l2"),
    _current("grid_current_l3"),
    _frequency("grid_frequency"),
    # House, PV and inverter
    _power("load_power", enabled=True),
    _power("pv_power", enabled=True),
    _power("pv1_power"),
    _power("pv2_power"),
    _power("pv3_power"),
    _power("pv4_power"),
    _voltage("pv1_voltage"),
    _voltage("pv2_voltage"),
    _voltage("pv3_voltage"),
    _voltage("pv4_voltage"),
    _current("pv1_current"),
    _current("pv2_current"),
    _current("pv3_current"),
    _current("pv4_current"),
    _power("inverter_power"),
    _power("backup_power"),
    _voltage("inverter_grid_voltage_l1"),
    _voltage("inverter_grid_voltage_l2"),
    _voltage("inverter_grid_voltage_l3"),
    _frequency("inverter_grid_frequency"),
    _voltage("bus_voltage", entity_category=EntityCategory.DIAGNOSTIC),
    _temperature("inverter_temperature", entity_registry_enabled_default=True),
    _temperature("pv_heatsink_temperature"),
    _temperature("battery_heatsink_temperature"),
    _temperature("internal_temperature"),
    # Energy counters
    _energy("battery_charge_energy_total"),
    _energy("battery_discharge_energy_total"),
    _energy("grid_import_energy_total"),
    _energy("grid_export_energy_total"),
    _energy("load_energy_total"),
    _energy("pv_energy_total"),
    _energy("battery_charge_energy_today"),
    _energy("battery_discharge_energy_today"),
    _energy("grid_import_energy_today", enabled=False),
    _energy("grid_export_energy_today", enabled=False),
    _energy("load_energy_today", enabled=False),
    _energy("pv_energy_today", enabled=False),
    # Faults
    HiOneSensorEntityDescription(
        key="active_faults",
        translation_key="active_faults",
        keys=("battery_fault_bits", "dsp_pwr_fault_bits", "dsp_saf_fault_bits"),
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_fault_count,
        attr_fn=_fault_attrs,
    ),
    HiOneSensorEntityDescription(
        key="battery_fault_code",
        translation_key="battery_fault_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_hex("battery_fault_code"),
    ),
    HiOneSensorEntityDescription(
        key="sw_fault",
        translation_key="sw_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_hex("sw_fault"),
    ),
    HiOneSensorEntityDescription(
        key="hw_fault",
        translation_key="hw_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_hex("hw_fault"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: HiOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HiOne sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        HiOneSensor(coordinator, description)
        for description in SENSORS
        if is_supported(coordinator, description.register_keys)
    )


class HiOneSensor(HiOneEntity, SensorEntity):
    """A HiOne sensor."""

    entity_description: HiOneSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        description = self.entity_description
        data = self.coordinator.data or {}
        if description.value_fn is not None:
            return description.value_fn(data)
        return data.get(description.key)

    @property
    def available(self) -> bool:
        """Return True when the last poll produced a value."""
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data or {})
