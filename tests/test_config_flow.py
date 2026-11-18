"""Tests for the config, options and reconfigure flows."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hoymiles_hione.const import (
    CONF_ENABLE_CONTROLS,
    CONF_FRAMER,
    CONF_LAYOUT,
    CONF_UNIT_ID,
    DOMAIN,
)

from .fake import SERIAL, FakeTransport

USER_INPUT = {
    CONF_HOST: "192.0.2.10",
    CONF_PORT: 502,
    CONF_UNIT_ID: 1,
    CONF_FRAMER: "tcp",
    CONF_LAYOUT: "g3",
}


@pytest.fixture
def transport() -> Generator[FakeTransport]:
    """Patch the Modbus client everywhere with an in-memory fake."""
    fake = FakeTransport()
    with (
        patch(
            "custom_components.hoymiles_hione.config_flow.HiOneModbusClient",
            return_value=fake,
        ),
        patch("custom_components.hoymiles_hione.HiOneModbusClient", return_value=fake),
    ):
        yield fake


async def test_user_flow(hass: HomeAssistant, transport: FakeTransport) -> None:
    """A reachable HiOne creates an entry keyed by its serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HiOne"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == SERIAL
    assert transport.closed


@pytest.mark.parametrize(
    ("setup", "error"),
    [
        (lambda t: setattr(t, "offline", True), "cannot_connect"),
        (lambda t: t.illegal.add(1909), "not_supported"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, transport: FakeTransport, setup, error: str
) -> None:
    """Errors are shown and the user can retry."""
    setup(transport)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    transport.offline = False
    transport.illegal.clear()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_already_configured(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """The same device cannot be added twice, even via another address."""
    MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_HOST: "192.0.2.99"}
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, transport: FakeTransport) -> None:
    """Options set the polling interval and write access."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60, CONF_ENABLE_CONTROLS: True}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_SCAN_INTERVAL: 60, CONF_ENABLE_CONTROLS: True}
    assert entry.runtime_data.controls_enabled


async def test_reconfigure(hass: HomeAssistant, transport: FakeTransport) -> None:
    """The address can change as long as it is the same device."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT)
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_HOST: "192.0.2.20"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.0.2.20"


async def test_reconfigure_loaded_entry_uses_one_connection(
    hass: HomeAssistant,
) -> None:
    """Reconfiguring never opens a second connection next to the running one."""
    clients: list[FakeTransport] = []

    def factory(*_args, **_kwargs) -> FakeTransport:
        assert all(client.closed for client in clients), "second Modbus client opened"
        clients.append(FakeTransport())
        return clients[-1]

    with (
        patch(
            "custom_components.hoymiles_hione.config_flow.HiOneModbusClient",
            side_effect=factory,
        ),
        patch(
            "custom_components.hoymiles_hione.HiOneModbusClient", side_effect=factory
        ),
    ):
        entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, CONF_HOST: "192.0.2.20"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.state is ConfigEntryState.LOADED
    assert entry.data[CONF_HOST] == "192.0.2.20"


async def test_reconfigure_failure_restores_entry(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """If the new address does not work, the running entry is set up again."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport.illegal.add(1909)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_HOST: "192.0.2.20"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_supported"}
    assert entry.state is ConfigEntryState.LOADED
    assert entry.data[CONF_HOST] == "192.0.2.10"


async def test_reconfigure_wrong_device(
    hass: HomeAssistant, transport: FakeTransport
) -> None:
    """Pointing an entry at another HiOne is refused."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="OTHER-SERIAL", data=USER_INPUT)
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
