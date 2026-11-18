"""Tests for setup, entities, controls, services and diagnostics."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hoymiles_hione.const import (
    CONF_ENABLE_CONTROLS,
    CONF_FRAMER,
    CONF_LAYOUT,
    CONF_UNIT_ID,
    DOMAIN,
)
from custom_components.hoymiles_hione.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .fake import SERIAL, FakeTransport

DATA = {
    CONF_HOST: "192.0.2.10",
    CONF_PORT: 502,
    CONF_UNIT_ID: 1,
    CONF_FRAMER: "tcp",
    CONF_LAYOUT: "g3",
}
SELECT = "select.hoymiles_hione_ems_mode"


@pytest.fixture
def transport() -> Generator[FakeTransport]:
    """Patch the Modbus client with an in-memory fake."""
    fake = FakeTransport()
    with patch("custom_components.hoymiles_hione.HiOneModbusClient", return_value=fake):
        yield fake


async def _setup(hass: HomeAssistant, *, controls: bool = False) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SERIAL,
        title="HiOne",
        data=DATA,
        options={CONF_SCAN_INTERVAL: 30, CONF_ENABLE_CONTROLS: controls},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return state.state


async def test_sensors(hass: HomeAssistant, transport: FakeTransport) -> None:
    """Sensors expose values with Home Assistant sign conventions."""
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    assert _state(hass, "sensor.hoymiles_hione_battery_state_of_charge") == "55"
    assert _state(hass, "sensor.hoymiles_hione_battery_power") == "-1500"
    assert _state(hass, "sensor.hoymiles_hione_battery_charge_power") == "1500"
    assert _state(hass, "sensor.hoymiles_hione_battery_discharge_power") == "0"
    # Device reports import as negative; Home Assistant expects import positive.
    assert _state(hass, "sensor.hoymiles_hione_grid_power") == "800"
    assert _state(hass, "sensor.hoymiles_hione_house_consumption") == "700"
    assert _state(hass, "sensor.hoymiles_hione_battery_state") == "charging"
    assert _state(hass, "sensor.hoymiles_hione_status") == "on_grid"
    assert _state(hass, "sensor.hoymiles_hione_ems_mode") == "self_use"
    assert _state(hass, "sensor.hoymiles_hione_battery_charged_energy") == "1234.5"
    assert _state(hass, "binary_sensor.hoymiles_hione_fault") == "on"

    faults = hass.states.get("sensor.hoymiles_hione_active_faults")
    assert faults is not None
    assert faults.state == "2"
    assert faults.attributes["faults"] == ["Shut down", "SPI communication fault"]

    # Write access is off by default: no controls.
    assert hass.states.get(SELECT) is None

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, SERIAL), entry.entry_id
    )
    assert device is not None
    assert device.serial_number == SERIAL
    assert device.sw_version == "V1.04.05"


async def test_unsupported_registers_create_no_entities(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Registers the firmware does not know do not become dead entities."""
    transport.illegal.update(range(30021, 30027))
    await _setup(hass)
    assert hass.states.get("sensor.hoymiles_hione_active_faults") is None
    assert hass.states.get("binary_sensor.hoymiles_hione_fault") is None
    assert _state(hass, "sensor.hoymiles_hione_battery_state_of_charge") == "55"


async def test_setup_retry_when_offline(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """An unreachable device is retried later."""
    transport.offline = True
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert transport.closed


async def test_unload_closes_connection(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Unloading releases the Modbus connection for other clients."""
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert transport.closed


async def test_select_writes_ems_block(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Selecting a mode writes the whole EMS block with FC16."""
    await _setup(hass, controls=True)
    assert _state(hass, SELECT) == "self_use"
    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: SELECT, "option": "force_charge"},
        blocking=True,
    )
    assert transport.writes == [(4300, [4, 30, 90, 70, 500, 30, 500])]


async def test_select_refuses_off_grid(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Pure off-grid can be displayed but not selected."""
    await _setup(hass, controls=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: SELECT, "option": "off_grid"},
            blocking=True,
        )
    assert transport.writes == []


async def test_numbers_write(hass: HomeAssistant, transport: FakeTransport) -> None:
    """Numbers write scaled values to the right block."""
    await _setup(hass, controls=True)
    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: "number.hoymiles_hione_force_charge_power", "value": 80},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: "number.hoymiles_hione_minimum_soc", "value": 20},
        blocking=True,
    )
    assert transport.writes == [
        (4300, [0, 30, 90, 70, 800, 30, 500]),
        (308, [100, 20]),
    ]


async def test_ignored_write_raises(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """A write the device does not apply is reported to the user."""
    await _setup(hass, controls=True)
    transport.ignore_writes = True
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: SELECT, "option": "backup"},
            blocking=True,
        )


async def test_set_ems_service(hass: HomeAssistant, transport: FakeTransport) -> None:
    """The action changes several settings in one write."""
    entry = await _setup(hass, controls=True)
    await hass.services.async_call(
        DOMAIN,
        "set_ems",
        {
            "config_entry_id": entry.entry_id,
            "ems_mode": "force_charge",
            "force_charge_target_soc": 90,
            "force_charge_power": 60,
        },
        blocking=True,
    )
    assert transport.writes == [(4300, [4, 30, 90, 90, 600, 30, 500])]


async def test_set_ems_service_requires_write_access(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Without write access the action refuses to run."""
    entry = await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "set_ems",
            {"config_entry_id": entry.entry_id, "ems_mode": "backup"},
            blocking=True,
        )
    assert transport.writes == []


async def test_set_ems_service_unknown_entry(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """An unknown config entry is a validation error."""
    await _setup(hass, controls=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "set_ems",
            {"config_entry_id": "missing", "ems_mode": "backup"},
            blocking=True,
        )


async def test_diagnostics_redacts(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Diagnostics do not leak the address or serial number."""
    entry = await _setup(hass)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["entry"]["data"][CONF_HOST] == "**REDACTED**"
    assert diag["entry"]["unique_id"] == "**REDACTED**"
    assert diag["device"]["serial_number"] == "**REDACTED**"
    assert diag["values"]["battery_soc"] == 55
