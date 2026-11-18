"""
Register definitions and decoding for Hoymiles HiOne energy storage systems.

This module has no Home Assistant dependency so it can be unit tested on its own.
Addresses are 0-based protocol addresses (the value sent on the wire).
Multi-register values are big-endian: high word first, high byte first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Table(StrEnum):
    """Modbus register table."""

    INPUT = "input"  # function code 0x04, read-only
    HOLDING = "holding"  # function code 0x03 (read) / 0x10 (write)


class DataType(StrEnum):
    """Register data type."""

    U16 = "u16"
    I16 = "i16"
    U32 = "u32"
    I32 = "i32"
    U64 = "u64"
    STRING = "string"


class Layout(StrEnum):
    """
    Battery register layout.

    G3 hardware (HiOne) reports battery current/power as 32-bit values at
    48/50; G1/G2 hardware uses 16-bit values at 48/51.
    """

    G3 = "g3"
    G1_G2 = "g1_g2"


_WORDS = {
    DataType.U16: 1,
    DataType.I16: 1,
    DataType.U32: 2,
    DataType.I32: 2,
    DataType.U64: 4,
}


@dataclass(frozen=True, slots=True)
class Register:
    """A single (possibly multi-word) register value."""

    key: str
    table: Table
    address: int
    data_type: DataType = DataType.U16
    scale: float = 1.0
    length: int | None = None
    valid_range: tuple[float, float] | None = None

    @property
    def count(self) -> int:
        """Return the number of 16-bit words this value occupies."""
        if self.data_type is DataType.STRING:
            if not self.length:
                msg = f"String register {self.key} needs a length"
                raise ValueError(msg)
            return self.length
        return _WORDS[self.data_type]

    @property
    def end(self) -> int:
        """Return the address after the last word of this value."""
        return self.address + self.count


@dataclass(frozen=True, slots=True)
class ReadBlock:
    """A contiguous range of registers read with a single request."""

    table: Table
    start: int
    count: int
    registers: tuple[Register, ...] = field(compare=False)


def _signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value >= 1 << (bits - 1) else value


def _combine(words: list[int]) -> int:
    value = 0
    for word in words:
        value = (value << 16) | (word & 0xFFFF)
    return value


def decode_raw(register: Register, words: list[int]) -> int | str:
    """Decode the raw words of a register into an int (unscaled) or string."""
    if len(words) != register.count:
        msg = f"{register.key}: expected {register.count} words, got {len(words)}"
        raise ValueError(msg)
    match register.data_type:
        case DataType.U16 | DataType.U32 | DataType.U64:
            return _combine(words)
        case DataType.I16:
            return _signed(words[0] & 0xFFFF, 16)
        case DataType.I32:
            return _signed(_combine(words), 32)
        case DataType.STRING:
            raw = b"".join((w & 0xFFFF).to_bytes(2, "big") for w in words)
            return raw.replace(b"\x00", b"").decode("ascii", "ignore").strip()
    msg = f"Unsupported data type {register.data_type}"  # pragma: no cover
    raise ValueError(msg)  # pragma: no cover


def decode(register: Register, words: list[int]) -> int | float | str | None:
    """
    Decode and scale a register value.

    Returns None when the value is outside the register's plausible range,
    which protects entities from garbled reads.
    """
    raw = decode_raw(register, words)
    if isinstance(raw, str):
        return raw or None
    value: int | float = raw * register.scale if register.scale != 1 else raw
    if isinstance(value, float):
        value = round(value, 3)
    if register.valid_range is not None:
        low, high = register.valid_range
        if not low <= value <= high:
            return None
    return value


def format_version(value: int | None, prefix: str = "V") -> str | None:
    """Format a firmware version number (100 means V0.01.00)."""
    if value is None:
        return None
    return f"{prefix}{value // 10000}.{(value // 100) % 100:02d}.{value % 100:02d}"


def plan_blocks(
    registers: list[Register] | tuple[Register, ...],
    *,
    max_gap: int,
    max_count: int,
) -> list[ReadBlock]:
    """
    Group registers into as few read requests as possible.

    Registers in the same table are merged when the gap between them is at most
    ``max_gap`` words and the resulting block stays within ``max_count`` words.
    """
    blocks: list[ReadBlock] = []
    for table in Table:
        regs = sorted(
            (r for r in registers if r.table is table), key=lambda r: r.address
        )
        current: list[Register] = []
        for reg in regs:
            if current:
                start = current[0].address
                end = max(r.end for r in current)
                if reg.address - end <= max_gap and reg.end - start <= max_count:
                    current.append(reg)
                    continue
                blocks.append(_block(table, current))
            current = [reg]
        if current:
            blocks.append(_block(table, current))
    return blocks


def _block(table: Table, regs: list[Register]) -> ReadBlock:
    start = regs[0].address
    end = max(r.end for r in regs)
    return ReadBlock(table, start, end - start, tuple(regs))


def _r(  # noqa: PLR0913
    key: str,
    address: int,
    data_type: DataType = DataType.U16,
    scale: float = 1.0,
    *,
    table: Table = Table.INPUT,
    valid_range: tuple[float, float] | None = None,
) -> Register:
    return Register(key, table, address, data_type, scale, valid_range=valid_range)


U16, I16, U32, I32 = DataType.U16, DataType.I16, DataType.U32, DataType.I32
PERCENT = (0, 100)
POWER = (-50_000, 50_000)

# Input registers (FC04) polled every update.
COMMON_REGISTERS: tuple[Register, ...] = (
    _r("work_status", 0, valid_range=(0, 6)),
    _r("sw_fault", 19, U32),
    _r("hw_fault", 21, U32),
    _r("pv_power", 26, valid_range=(0, 50_000)),
    _r("pv1_voltage", 27, U16, 0.1),
    _r("pv1_current", 28, I16, 0.01),
    _r("pv1_power", 29),
    _r("pv2_voltage", 30, U16, 0.1),
    _r("pv2_current", 31, I16, 0.01),
    _r("pv2_power", 32),
    _r("pv3_voltage", 33, U16, 0.1),
    _r("pv3_current", 34, I16, 0.01),
    _r("pv3_power", 35),
    _r("pv4_voltage", 36, U16, 0.1),
    _r("pv4_current", 37, I16, 0.01),
    _r("pv4_power", 38),
    _r("bus_voltage", 60, U16, 0.1),
    _r("inverter_grid_voltage_l1", 62, U16, 0.1),
    _r("inverter_grid_voltage_l2", 63, U16, 0.1),
    _r("inverter_grid_voltage_l3", 64, U16, 0.1),
    _r("inverter_grid_frequency", 66, U16, 0.01),
    _r("inverter_power", 73, I16, valid_range=POWER),
    _r("backup_power", 91, I16, valid_range=POWER),
    _r("pv_heatsink_temperature", 112, I16, valid_range=(-40, 150)),
    _r("inverter_temperature", 113, I16, valid_range=(-40, 150)),
    _r("battery_heatsink_temperature", 114, I16, valid_range=(-40, 150)),
    _r("internal_temperature", 115, I16, valid_range=(-40, 150)),
    _r("load_power", 284, I32, valid_range=POWER),
    _r("meter_status", 1800),
    _r("grid_voltage_l1", 1801, U16, 0.1),
    _r("grid_voltage_l2", 1802, U16, 0.1),
    _r("grid_voltage_l3", 1803, U16, 0.1),
    _r("grid_current_l1", 1804, I16, 0.01),
    _r("grid_current_l2", 1805, I16, 0.01),
    _r("grid_current_l3", 1806, I16, 0.01),
    _r("grid_frequency", 1807, U16, 0.01),
    _r("grid_power_l1_raw", 1808, I32, valid_range=POWER),
    _r("grid_power_l2_raw", 1810, I32, valid_range=POWER),
    _r("grid_power_l3_raw", 1812, I32, valid_range=POWER),
    _r("grid_power_raw", 1814, I32, valid_range=POWER),
    _r("battery_link", 1901),
    _r("battery_state", 1904, valid_range=(0, 2)),
    _r("battery_fault_code", 1905, U32),
    _r("battery_capacity", 1907, U32, 0.1),
    _r("battery_soc", 1909, valid_range=PERCENT),
    _r("battery_soh", 1910, valid_range=PERCENT),
    _r("battery_voltage", 1911, U16, 0.1),
    _r("battery_current", 1912, I32, 0.1),
    _r("battery_max_charge_current", 1916, U16, 0.1),
    _r("battery_max_discharge_current", 1917, U16, 0.1),
    _r("battery_charge_cutoff_voltage", 1918, U16, 0.1),
    _r("battery_discharge_cutoff_voltage", 1919, U16, 0.1),
    # The protocol document lists factor 1, real devices report 0.1 °C.
    _r("cell_temperature_max", 1922, I16, 0.1, valid_range=(-40, 100)),
    _r("cell_temperature_min", 1923, I16, 0.1, valid_range=(-40, 100)),
    _r("pv_energy_total", 2000, U32, 0.1),
    _r("battery_charge_energy_total", 2028, U32, 0.1),
    _r("battery_discharge_energy_total", 2030, U32, 0.1),
    _r("grid_import_energy_total", 2040, U32, 0.1),
    _r("grid_export_energy_total", 2048, U32, 0.1),
    _r("load_energy_total", 2056, U32, 0.1),
    _r("pv_energy_today", 2100, U16, 0.1),
    _r("battery_charge_energy_today", 2114, U16, 0.1),
    _r("battery_discharge_energy_today", 2115, U16, 0.1),
    _r("grid_import_energy_today", 2120, U16, 0.1),
    _r("grid_export_energy_today", 2124, U16, 0.1),
    _r("load_energy_today", 2128, U16, 0.1),
    _r("battery_fault_bits", 30021, U32),
    _r("dsp_pwr_fault_bits", 30023, U32),
    _r("dsp_saf_fault_bits", 30025, U32),
)

LAYOUT_REGISTERS: dict[Layout, tuple[Register, ...]] = {
    # Sign verified on a HiOne: positive = discharging, negative = charging.
    Layout.G3: (_r("battery_power", 50, I32, valid_range=POWER),),
    Layout.G1_G2: (_r("battery_power", 51, I16, valid_range=POWER),),
}


@dataclass(frozen=True, slots=True)
class Setting:
    """A writable holding register with raw limits."""

    key: str
    address: int
    raw_min: int
    raw_max: int
    scale: float = 1.0

    def to_raw(self, value: float) -> int:
        """Convert an engineering value to a raw register value."""
        raw = round(value / self.scale)
        if not self.raw_min <= raw <= self.raw_max:
            low, high = self.raw_min * self.scale, self.raw_max * self.scale
            msg = f"{self.key} must be between {low:g} and {high:g}"
            raise ValueError(msg)
        return raw


EMS_START = 4300
# The EMS block is always read and written as a whole (4300-4307).
# Raw limits double as a sanity check of what is read back from the device.
EMS_SETTINGS: tuple[Setting, ...] = (
    Setting("ems_mode", 4300, 0, 7),
    Setting("self_use_reserve_soc", 4301, 10, 100),
    Setting("backup_reserve_soc", 4302, 60, 100),
    Setting("force_charge_target_soc", 4303, 10, 100),
    Setting("force_charge_power", 4304, 0, 1000, 0.1),
    Setting("force_discharge_target_soc", 4305, 0, 100),
    Setting("force_discharge_power", 4306, 0, 1000, 0.1),
    Setting("economic_reserve_soc", 4307, 10, 100),
)
# 4300-4306 is the block known to work on real devices; 4307 is only included
# in a write when it changes.
EMS_BASE_COUNT = 7

SOC_LIMIT_START = 308
SOC_LIMIT_SETTINGS: tuple[Setting, ...] = (
    Setting("max_soc", 308, 10, 100),
    Setting("min_soc", 309, 10, 90),
)

SETTINGS_BY_KEY: dict[str, Setting] = {
    s.key: s for s in (*EMS_SETTINGS, *SOC_LIMIT_SETTINGS)
}


class EmsMode(StrEnum):
    """EMS operating modes (holding register 4300)."""

    SELF_USE = "self_use"
    ECONOMIC = "economic"
    BACKUP = "backup"
    OFF_GRID = "off_grid"
    FORCE_CHARGE = "force_charge"
    FORCE_DISCHARGE = "force_discharge"
    PEAK_SHAVING = "peak_shaving"
    TIME_OF_USE = "time_of_use"


EMS_MODE_VALUES: dict[EmsMode, int] = {mode: i for i, mode in enumerate(EmsMode)}
EMS_MODE_BY_VALUE: dict[int, EmsMode] = {v: k for k, v in EMS_MODE_VALUES.items()}
# Pure off-grid disconnects the house from the grid; never set it remotely.
WRITABLE_EMS_MODES: tuple[EmsMode, ...] = tuple(
    m for m in EmsMode if m is not EmsMode.OFF_GRID
)


def _holding(key: str, address: int, data_type: DataType = U16) -> Register:
    return _r(key, address, data_type, table=Table.HOLDING)


SETTING_REGISTERS: tuple[Register, ...] = tuple(
    _r(s.key, s.address, U16, s.scale, table=Table.HOLDING)
    for s in (*EMS_SETTINGS, *SOC_LIMIT_SETTINGS)
)

# Device information, read once at setup.
SERIAL_NUMBER = Register(
    "serial_number", Table.HOLDING, 7000, DataType.STRING, length=16
)
MODEL_NAME = Register("model_name", Table.HOLDING, 7016, DataType.STRING, length=18)
INFO_REGISTERS: tuple[Register, ...] = (
    _holding("power_software_version", 7034),
    _holding("safety_software_version", 7035),
    _holding("system_software_version", 7036),
    _holding("hardware_version", 7037),
)

WORK_STATUS: dict[int, str] = {
    0: "power_init",
    1: "standby",
    2: "grid_on_test",
    3: "on_grid",
    4: "fault",
    5: "off_grid",
    6: "bypass",
}
BATTERY_STATE: dict[int, str] = {0: "standby", 1: "charging", 2: "discharging"}
METER_STATUS: dict[int, str] = {
    0: "offline",
    1: "online",
    3: "hmid_online",
    4: "hmid_failure",
}

# Fault bit descriptions for HiOne hardware (protocol V2.8, appendix 2).
DSP_PWR_FAULTS: dict[int, str] = {
    0: "Shut down",
    1: "Relay fault",
    2: "SPI communication fault",
    3: "Auxiliary power abnormality",
    4: "CAN communication timeout",
    5: "Shutdown fault from safety MCU",
    6: "EPS wiring abnormality",
    7: "Gateway off",
    8: "Parallel communication abnormality",
    9: "Persistent hardware fault",
    10: "Sampling bias abnormality",
    11: "SCI communication fault",
    12: "Bus voltage abnormality",
    13: "Fan fault",
    14: "Hardware fault",
    15: "Comparator fault",
    16: "Wiring abnormality",
    17: "Battery fault",
    18: "Inverter drive fault / pre-synchronization failed",
    19: "Temperature abnormality",
    20: "PV fault",
    21: "EEPROM fault",
    22: "Phase order error",
    23: "Bypass allow fault from safety MCU",
    24: "CMPSS bias calculation error",
    25: "Feed-in power limitation fault",
    26: "EPS voltage abnormality",
    27: "EPS overload",
    28: "Generator voltage abnormality",
    29: "Generator voltage ride-through",
    30: "Grid voltage abnormality",
    31: "Grid voltage ride-through",
}
DSP_SAF_FAULTS: dict[int, str] = {
    0: "Grid overvoltage",
    1: "Grid undervoltage",
    2: "Grid 10-minute overvoltage",
    3: "Grid overfrequency",
    4: "Grid underfrequency",
    5: "Grid three-phase imbalance",
    6: "Grid reconnection fault",
    7: "Grid lost",
    10: "Auxiliary power abnormality",
    11: "Grid relay fault",
    12: "SPI communication fault",
    13: "Arc self-test fault",
    14: "Arc fault",
    15: "Insulation (ISO) error",
    16: "RCD self-test fault",
    17: "RCD fault",
    21: "SCI communication fault",
    22: "Sampling bias abnormality",
    23: "Flash fault",
    24: "DC voltage overvoltage",
    25: "DC current injection overcurrent",
    26: "Interrupt overflow",
    27: "Microelectronic fault",
    28: "Low ambient temperature",
    29: "Over temperature",
    30: "Comparator fault",
    31: "Fan fault",
}
BATTERY_FAULTS: dict[int, str] = {
    0: "Battery low-voltage alarm",
    1: "Battery high-voltage alarm",
    2: "Battery pack discharge low-voltage alarm",
    3: "Battery pack charge high-voltage alarm",
    4: "Charge low-temperature alarm",
    5: "Charge high-temperature alarm",
    6: "Discharge low-temperature alarm",
    7: "Discharge high-temperature alarm",
    8: "Input overvoltage alarm",
}
FAULT_TABLES: dict[str, dict[int, str]] = {
    "battery_fault_bits": BATTERY_FAULTS,
    "dsp_pwr_fault_bits": DSP_PWR_FAULTS,
    "dsp_saf_fault_bits": DSP_SAF_FAULTS,
}


def decode_faults(values: dict[str, int | float | str | None]) -> list[str] | None:
    """
    Return the active fault descriptions from the fault bit registers.

    Returns None when none of the fault registers could be read.
    """
    faults: list[str] = []
    seen = False
    for key, table in FAULT_TABLES.items():
        bits = values.get(key)
        if not isinstance(bits, int):
            continue
        seen = True
        faults.extend(
            table.get(bit, f"{key} bit {bit}")
            for bit in range(32)
            if bits & (1 << bit)
        )
    return faults if seen else None


def polled_registers(layout: Layout) -> tuple[Register, ...]:
    """Return all registers polled on every update for the given layout."""
    return (*COMMON_REGISTERS, *LAYOUT_REGISTERS[layout], *SETTING_REGISTERS)
