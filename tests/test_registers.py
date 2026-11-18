"""Tests for register decoding and read planning."""

from __future__ import annotations

import pytest

from custom_components.hoymiles_hione.registers import (
    DataType,
    Register,
    Setting,
    Table,
    decode,
    decode_faults,
    format_version,
    plan_blocks,
)


def _reg(data_type: DataType, scale: float = 1.0, **kwargs: object) -> Register:
    return Register("x", Table.INPUT, 0, data_type, scale, **kwargs)


@pytest.mark.parametrize(
    ("data_type", "words", "expected"),
    [
        (DataType.U16, [65535], 65535),
        (DataType.I16, [65535], -1),
        (DataType.U32, [1, 2], 65538),
        (DataType.I32, [0xFFFF, 0xFA24], -1500),
        (DataType.U64, [0, 0, 1, 0], 65536),
    ],
)
def test_decode_numbers(data_type: DataType, words: list[int], expected: int) -> None:
    """Multi-word values are big-endian, high word first."""
    assert decode(_reg(data_type), words) == expected


def test_decode_scale_and_range() -> None:
    """Scaled values are rounded; values outside the range are discarded."""
    assert decode(_reg(DataType.U16, 0.1), [262]) == 26.2
    soc = _reg(DataType.U16, valid_range=(0, 100))
    assert decode(soc, [55]) == 55
    assert decode(soc, [6553]) is None


def test_decode_string() -> None:
    """Strings are two ASCII characters per register, NUL padded."""
    reg = _reg(DataType.STRING, length=3)
    assert decode(reg, [0x4869, 0x4F6E, 0x6500]) == "HiOne"
    assert decode(reg, [0, 0, 0]) is None


def test_decode_wrong_length() -> None:
    """A short read is an error, not a silently wrong value."""
    with pytest.raises(ValueError, match="expected 2 words"):
        decode(_reg(DataType.U32), [1])


def test_format_version() -> None:
    """100 means V0.01.00 according to the protocol."""
    assert format_version(100) == "V0.01.00"
    assert format_version(10405, "H") == "H1.04.05"
    assert format_version(None) is None


def test_plan_blocks_merges_small_gaps_and_splits_large() -> None:
    """Registers close together share a request; distant ones do not."""
    regs = [
        Register("a", Table.INPUT, 0),
        Register("b", Table.INPUT, 5, DataType.U32),
        Register("c", Table.INPUT, 100),
        Register("d", Table.HOLDING, 1),
    ]
    blocks = plan_blocks(regs, max_gap=10, max_count=64)
    assert [(b.table, b.start, b.count) for b in blocks] == [
        (Table.INPUT, 0, 7),
        (Table.INPUT, 100, 1),
        (Table.HOLDING, 1, 1),
    ]
    assert [r.key for r in blocks[0].registers] == ["a", "b"]


def test_plan_blocks_respects_max_count() -> None:
    """Blocks never exceed the maximum request size."""
    regs = [Register(f"r{i}", Table.INPUT, i) for i in range(10)]
    blocks = plan_blocks(regs, max_gap=0, max_count=4)
    assert [b.count for b in blocks] == [4, 4, 2]


def test_decode_faults() -> None:
    """Fault bits are translated; unknown bits keep their number."""
    assert decode_faults({}) is None
    assert decode_faults({"dsp_pwr_fault_bits": 0}) == []
    faults = decode_faults({"dsp_pwr_fault_bits": 0b101, "battery_fault_bits": 1 << 12})
    assert faults == [
        "battery_fault_bits bit 12",
        "Shut down",
        "SPI communication fault",
    ]


def test_setting_to_raw() -> None:
    """Engineering values are scaled and range checked."""
    power = Setting("power", 1, 0, 1000, 0.1)
    assert power.to_raw(55) == 550
    with pytest.raises(ValueError, match="between 0 and 100"):
        power.to_raw(120)
