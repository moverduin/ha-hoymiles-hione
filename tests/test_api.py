"""Tests for the HiOne API (reading and safe writing)."""

from __future__ import annotations

import pytest

from custom_components.hoymiles_hione.api import (
    HiOneApi,
    HiOneError,
    HiOneValidationError,
    HiOneWriteError,
)
from custom_components.hoymiles_hione.registers import Layout, Table

from .fake import MODEL, SERIAL, FakeTransport


def _api(transport: FakeTransport, layout: Layout = Layout.G3) -> HiOneApi:
    return HiOneApi(transport, layout)


async def test_device_info() -> None:
    """Serial number, model and versions are decoded."""
    info = await _api(FakeTransport()).async_get_device_info()
    assert info.serial_number == SERIAL
    assert info.model == MODEL
    assert info.system_version == "V1.04.05"
    assert info.hardware_version == "H0.01.00"


async def test_read_all_values_and_signs() -> None:
    """Values are scaled and 32-bit signed values keep their sign."""
    data = await _api(FakeTransport()).async_read_all()
    assert data["battery_soc"] == 55
    assert data["battery_power"] == -1500
    assert data["grid_power_raw"] == -800
    assert data["battery_voltage"] == 26.2
    assert data["cell_temperature_max"] == 21.5
    assert data["battery_charge_energy_total"] == 1234.5
    assert data["force_charge_power"] == 50
    assert data["ems_mode"] == 0


async def test_layout_g1_g2_uses_16_bit_power() -> None:
    """Older hardware reports battery power as I16 at 51."""
    transport = FakeTransport()
    transport.input[51] = 0xFC18  # -1000
    data = await _api(transport, Layout.G1_G2).async_read_all()
    assert data["battery_power"] == -1000


async def test_unsupported_registers_are_skipped() -> None:
    """A rejected block is split once; unsupported registers are remembered."""
    transport = FakeTransport(illegal={30021, 30022})
    api = _api(transport)
    data = await api.async_read_all()
    assert data["battery_fault_bits"] is None
    assert data["dsp_pwr_fault_bits"] == 0b101
    assert api.unsupported == {"battery_fault_bits"}

    transport.reads.clear()
    await api.async_read_all()
    assert not any(addr == 30021 for _, addr, _ in transport.reads)


async def test_device_rejecting_gaps() -> None:
    """Devices that refuse reads spanning gaps still deliver every value."""
    transport = FakeTransport(reject_gaps=True)
    data = await _api(transport).async_read_all()
    assert data["battery_soc"] == 55
    assert data["battery_power"] == -1500
    assert data["ems_mode"] == 0


async def test_set_ems_writes_whole_block_with_fc16() -> None:
    """Mode changes write 4300-4306 in one request and are verified."""
    transport = FakeTransport()
    result = await _api(transport).async_set_ems(
        {
            "ems_mode": "force_charge",
            "force_charge_target_soc": 95,
            "force_charge_power": 80,
        }
    )
    assert transport.writes == [(4300, [4, 30, 90, 95, 800, 30, 500])]
    assert result["ems_mode"] == 4


async def test_set_ems_includes_4307_only_when_changed() -> None:
    """The economic mode reserve extends the write to eight registers."""
    transport = FakeTransport()
    await _api(transport).async_set_ems({"economic_reserve_soc": 40})
    assert transport.writes == [(4300, [0, 30, 90, 70, 500, 30, 500, 40])]


async def test_set_ems_skips_unchanged() -> None:
    """Nothing is written when the device already has the requested values."""
    transport = FakeTransport()
    await _api(transport).async_set_ems({"ems_mode": "self_use"})
    assert transport.writes == []


@pytest.mark.parametrize(
    "changes",
    [
        {"ems_mode": "off_grid"},
        {"ems_mode": "nonsense"},
        {"self_use_reserve_soc": 5},
        {"force_charge_power": 150},
        {"unknown": 1},
        {},
    ],
)
async def test_set_ems_rejects_invalid(changes: dict) -> None:
    """Invalid or unsafe requests never reach the device."""
    transport = FakeTransport()
    with pytest.raises(ValueError):  # noqa: PT011
        await _api(transport).async_set_ems(changes)
    assert transport.writes == []


@pytest.mark.parametrize(
    "block",
    [
        [77, 77, 77, 77, 77, 77, 77, 77],  # garbled: all identical
        [0, 30, 90, 70, 5000, 30, 500, 30],  # power out of range
        [9, 30, 90, 70, 500, 30, 500, 30],  # unknown mode
    ],
)
async def test_set_ems_refuses_implausible_read(block: list[int]) -> None:
    """A garbled read is never written back."""
    transport = FakeTransport()
    for offset, value in enumerate(block):
        transport.holding[4300 + offset] = value
    with pytest.raises(HiOneValidationError):
        await _api(transport).async_set_ems({"ems_mode": "self_use"})
    assert transport.writes == []


async def test_set_ems_detects_ignored_write() -> None:
    """If the device ignores the write, the caller is told."""
    transport = FakeTransport()
    transport.ignore_writes = True
    with pytest.raises(HiOneWriteError):
        await _api(transport).async_set_ems({"ems_mode": "force_charge"})


async def test_set_ems_without_4307() -> None:
    """Older firmware without 4307 still gets a 7-register write."""
    transport = FakeTransport(illegal={4307})
    api = _api(transport)
    await api.async_set_ems({"ems_mode": "backup"})
    assert transport.writes == [(4300, [2, 30, 90, 70, 500, 30, 500])]
    with pytest.raises(HiOneError, match="economic_reserve_soc"):
        await api.async_set_ems({"economic_reserve_soc": 40})


async def test_set_ems_never_writes_back_off_grid() -> None:
    """Changing a setting while in pure off-grid mode must not rewrite mode 3."""
    transport = FakeTransport()
    transport.holding[4300] = 3
    with pytest.raises(ValueError, match="off-grid"):
        await _api(transport).async_set_ems({"self_use_reserve_soc": 40})
    assert transport.writes == []


async def test_set_soc_limits_requires_both_registers() -> None:
    """A device without register 309 gets a clean error, not a crash."""
    transport = FakeTransport(illegal={309})
    with pytest.raises(HiOneError):
        await _api(transport).async_set_soc_limits(max_soc=90)
    assert transport.writes == []


async def test_set_soc_limits() -> None:
    """SOC limits are written together and must stay ordered."""
    transport = FakeTransport()
    api = _api(transport)
    await api.async_set_soc_limits(min_soc=20)
    assert transport.writes == [(308, [100, 20])]
    with pytest.raises(ValueError, match="lower than maximum"):
        await api.async_set_soc_limits(max_soc=15)
    with pytest.raises(ValueError):  # noqa: PT011
        await api.async_set_soc_limits()


async def test_reads_use_expected_tables() -> None:
    """Measurements come from input registers, settings from holding registers."""
    transport = FakeTransport()
    await _api(transport).async_read_all()
    tables = {(table, addr) for table, addr, _ in transport.reads}
    assert (Table.HOLDING, 4300) in tables
    assert any(t is Table.INPUT and a <= 1909 < a + 64 for t, a in tables)
