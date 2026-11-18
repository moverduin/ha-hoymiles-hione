"""In-memory stand-in for the Modbus transport."""

from __future__ import annotations

from custom_components.hoymiles_hione.api import (
    HiOneConnectionError,
    HiOneIllegalAddressError,
)
from custom_components.hoymiles_hione.registers import Table

SERIAL = "HIONE0123456789"
MODEL = "HiOne"


def _string(text: str, words: int) -> list[int]:
    raw = text.encode().ljust(words * 2, b"\x00")
    return [int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw), 2)]


def _i32(value: int) -> list[int]:
    value &= 0xFFFFFFFF
    return [value >> 16, value & 0xFFFF]


def _put(store: dict[int, int], address: int, words: list[int]) -> None:
    for offset, word in enumerate(words):
        store[address + offset] = word


def sample_input() -> dict[int, int]:
    """Input registers of a HiOne charging at 1500 W while importing 800 W."""
    regs: dict[int, int] = {}
    regs[0] = 3  # on grid
    regs[26] = 0
    _put(regs, 50, _i32(-1500))  # battery power, negative = charging
    regs[113] = 31
    _put(regs, 284, _i32(700))  # house consumption
    regs[1800] = 1
    _put(regs, 1808, _i32(-300))
    _put(regs, 1810, _i32(-250))
    _put(regs, 1812, _i32(-250))
    _put(regs, 1814, _i32(-800))  # device: negative = import
    regs[1901] = 1
    regs[1904] = 1
    _put(regs, 1907, [0, 160])
    regs[1909] = 55
    regs[1910] = 99
    regs[1911] = 262
    regs[1916] = 1200
    regs[1922] = 215
    regs[1923] = 198
    _put(regs, 2028, [0, 12345])
    _put(regs, 2030, [0, 11111])
    regs[2114] = 52
    regs[2115] = 31
    _put(regs, 30023, [0, 0b101])
    return regs


def sample_holding() -> dict[int, int]:
    """Holding registers: EMS block, SOC limits and device information."""
    regs: dict[int, int] = {}
    _put(regs, 4300, [0, 30, 90, 70, 500, 30, 500, 30])
    _put(regs, 308, [100, 10])
    _put(regs, 7000, _string(SERIAL, 16))
    _put(regs, 7016, _string(MODEL, 18))
    _put(regs, 7034, [10203, 10203, 10405, 100])
    return regs


class FakeTransport:
    """Records requests and serves them from dictionaries."""

    def __init__(
        self,
        input_regs: dict[int, int] | None = None,
        holding_regs: dict[int, int] | None = None,
        *,
        illegal: set[int] | None = None,
        reject_gaps: bool = False,
    ) -> None:
        """Initialise with register contents."""
        self.input = sample_input() if input_regs is None else input_regs
        self.holding = sample_holding() if holding_regs is None else holding_regs
        self.illegal = illegal or set()
        self.reject_gaps = reject_gaps
        self.offline = False
        self.ignore_writes = False
        self.closed = False
        self.reads: list[tuple[Table, int, int]] = []
        self.writes: list[tuple[int, list[int]]] = []

    async def async_read(self, table: Table, address: int, count: int) -> list[int]:
        """Return stored values (0 for unknown addresses)."""
        self.reads.append((table, address, count))
        if self.offline:
            msg = "offline"
            raise HiOneConnectionError(msg)
        store = self.input if table is Table.INPUT else self.holding
        span = range(address, address + count)
        if any(a in self.illegal for a in span) or (
            self.reject_gaps and any(a not in store for a in span)
        ):
            msg = f"illegal {address}+{count}"
            raise HiOneIllegalAddressError(msg)
        return [store.get(a, 0) for a in span]

    async def async_write(self, address: int, values: list[int]) -> None:
        """Store written values unless the device 'ignores' writes."""
        if self.offline:
            msg = "offline"
            raise HiOneConnectionError(msg)
        self.writes.append((address, list(values)))
        if not self.ignore_writes:
            _put(self.holding, address, list(values))

    async def async_close(self) -> None:
        """Mark as closed."""
        self.closed = True
