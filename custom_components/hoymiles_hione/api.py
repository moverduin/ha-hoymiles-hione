"""
Modbus client and API for Hoymiles HiOne energy storage systems.

No Home Assistant imports here so the logic can be tested in isolation.

Real-world notes that shaped this module:
* The Hoymiles DTS/Modbus stick ignores single-register writes (FC06),
  so every write uses "write multiple registers" (FC16).
* The stick serves one Modbus TCP client at a time. A second client causes
  responses to be delivered to the wrong connection.
* Requests need a short pause in between (150 ms works reliably).
* Settings are written read-modify-write as a whole block, after checking that
  the block read back is plausible, so a garbled read is never written back.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .registers import (
    EMS_BASE_COUNT,
    EMS_MODE_VALUES,
    EMS_SETTINGS,
    EMS_START,
    INFO_REGISTERS,
    MODEL_NAME,
    SERIAL_NUMBER,
    SETTINGS_BY_KEY,
    SOC_LIMIT_SETTINGS,
    SOC_LIMIT_START,
    WRITABLE_EMS_MODES,
    EmsMode,
    Layout,
    ReadBlock,
    Register,
    Setting,
    Table,
    decode,
    format_version,
    plan_blocks,
    polled_registers,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

_LOGGER = logging.getLogger(__name__)

ILLEGAL_DATA_ADDRESS = 0x02
MAX_GAP = 10
MAX_COUNT = 64

# Seconds to wait before reading back a written block. Patched in tests.
WRITE_SETTLE_DELAY = 2.0


class HiOneError(Exception):
    """Base error for this integration."""


class HiOneConnectionError(HiOneError):
    """The device could not be reached or did not answer."""


class HiOneIllegalAddressError(HiOneError):
    """The device rejected the requested register range."""


class HiOneValidationError(HiOneError):
    """Data read from the device is implausible, so nothing was written."""


class HiOneWriteError(HiOneError):
    """The device did not apply a write."""


class ModbusTransport(Protocol):
    """Minimal transport used by HiOneApi (allows a fake in tests)."""

    async def async_read(self, table: Table, address: int, count: int) -> list[int]:
        """Read ``count`` registers."""

    async def async_write(self, address: int, values: list[int]) -> None:
        """Write holding registers with FC16."""

    async def async_close(self) -> None:
        """Close the connection."""


def _unit_kwarg() -> str:
    """Return the unit id keyword of this pymodbus version (renamed in 3.10)."""
    params = inspect.signature(AsyncModbusTcpClient.read_holding_registers).parameters
    return "device_id" if "device_id" in params else "slave"


class HiOneModbusClient:
    """Serialised Modbus TCP / RTU-over-TCP client."""

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        port: int,
        unit_id: int,
        *,
        rtu_over_tcp: bool = False,
        timeout: float = 5.0,
        request_delay: float = 0.15,
    ) -> None:
        """Initialise the client (does not connect yet)."""
        self._unit = {_unit_kwarg(): unit_id}
        self._request_delay = request_delay
        self._lock = asyncio.Lock()
        self._last_request = 0.0
        self._client = AsyncModbusTcpClient(
            host,
            port=port,
            framer=FramerType.RTU if rtu_over_tcp else FramerType.SOCKET,
            timeout=timeout,
            retries=1,
            reconnect_delay=0,
        )

    async def _ensure_connected(self) -> None:
        if self._client.connected:
            return
        try:
            connected = await self._client.connect()
        except (OSError, ModbusException) as err:
            raise HiOneConnectionError(str(err)) from err
        if not connected:
            msg = "Unable to connect to the Modbus device"
            raise HiOneConnectionError(msg)

    async def _pace(self) -> None:
        loop = asyncio.get_running_loop()
        wait = self._last_request + self._request_delay - loop.time()
        if wait > 0:
            await asyncio.sleep(wait)

    async def _call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        async with self._lock:
            await self._ensure_connected()
            await self._pace()
            try:
                response = await func(*args, **kwargs, **self._unit)
            except (TimeoutError, ModbusException, OSError) as err:
                self._client.close()
                raise HiOneConnectionError(str(err) or type(err).__name__) from err
            finally:
                self._last_request = asyncio.get_running_loop().time()
        if response.isError():
            code = getattr(response, "exception_code", None)
            if code == ILLEGAL_DATA_ADDRESS:
                raise HiOneIllegalAddressError(str(response))
            msg = f"Modbus exception response: {response}"
            raise HiOneError(msg)
        return response

    async def async_read(self, table: Table, address: int, count: int) -> list[int]:
        """Read registers from the input or holding table."""
        func = (
            self._client.read_input_registers
            if table is Table.INPUT
            else self._client.read_holding_registers
        )
        response = await self._call(func, address, count=count)
        registers = list(response.registers)
        if len(registers) < count:
            msg = f"Short read at {address}: {len(registers)}/{count} registers"
            raise HiOneConnectionError(msg)
        return registers[:count]

    async def async_write(self, address: int, values: list[int]) -> None:
        """Write holding registers. Always FC16, even for one register."""
        await self._call(self._client.write_registers, address, values)

    async def async_close(self) -> None:
        """Close the connection."""
        self._client.close()


@dataclass(slots=True)
class DeviceInfo:
    """Static information about the connected device."""

    serial_number: str | None
    model: str | None
    system_version: str | None
    hardware_version: str | None
    power_version: str | None
    safety_version: str | None


@dataclass(slots=True)
class _PlanState:
    blocks: list[ReadBlock]
    unsupported: set[str] = field(default_factory=set)


class HiOneApi:
    """High-level access to the HiOne register map."""

    def __init__(self, transport: ModbusTransport, layout: Layout) -> None:
        """Initialise the API."""
        self._transport = transport
        registers = polled_registers(layout)
        self._state = _PlanState(
            plan_blocks(registers, max_gap=MAX_GAP, max_count=MAX_COUNT)
        )
        self._write_lock = asyncio.Lock()

    @property
    def unsupported(self) -> frozenset[str]:
        """Keys of registers the device rejected as illegal addresses."""
        return frozenset(self._state.unsupported)

    @property
    def blocks(self) -> list[ReadBlock]:
        """Return the current read plan (for diagnostics)."""
        return list(self._state.blocks)

    async def async_close(self) -> None:
        """Close the underlying connection."""
        await self._transport.async_close()

    async def async_get_device_info(self) -> DeviceInfo:
        """Read serial number, model and firmware versions."""
        serial = await self._read_optional(SERIAL_NUMBER)
        model = await self._read_optional(MODEL_NAME)
        info: dict[str, Any] = {}
        start = INFO_REGISTERS[0].address
        try:
            words = await self._transport.async_read(
                Table.HOLDING, start, len(INFO_REGISTERS)
            )
            info = {
                r.key: decode(r, words[r.address - start : r.end - start])
                for r in INFO_REGISTERS
            }
        except HiOneIllegalAddressError:
            _LOGGER.debug("Firmware version registers are not supported")
        return DeviceInfo(
            serial_number=serial if isinstance(serial, str) else None,
            model=model if isinstance(model, str) else None,
            system_version=format_version(info.get("system_software_version")),
            hardware_version=format_version(info.get("hardware_version"), "H"),
            power_version=format_version(info.get("power_software_version")),
            safety_version=format_version(info.get("safety_software_version")),
        )

    async def _read_optional(self, register: Register) -> int | float | str | None:
        try:
            words = await self._transport.async_read(
                register.table, register.address, register.count
            )
        except HiOneIllegalAddressError:
            return None
        return decode(register, words)

    async def async_read_all(self) -> dict[str, Any]:
        """
        Read every polled register.

        Blocks rejected with "illegal data address" are split into smaller
        reads once; registers the device does not support are remembered and
        skipped afterwards.
        """
        values: dict[str, Any] = {}
        new_plan: list[ReadBlock] = []
        for block in self._state.blocks:
            new_plan.extend(await self._read_block(block, values))
        self._state.blocks = new_plan
        return values

    async def _read_block(
        self, block: ReadBlock, values: dict[str, Any]
    ) -> list[ReadBlock]:
        try:
            words = await self._transport.async_read(
                block.table, block.start, block.count
            )
        except HiOneIllegalAddressError:
            return await self._split_block(block, values)
        for reg in block.registers:
            offset = reg.address - block.start
            values[reg.key] = decode(reg, words[offset : offset + reg.count])
        return [block]

    async def _split_block(
        self, block: ReadBlock, values: dict[str, Any]
    ) -> list[ReadBlock]:
        if len(block.registers) == 1:
            reg = block.registers[0]
            _LOGGER.debug("Register %s (%s) is not supported", reg.key, reg.address)
            self._state.unsupported.add(reg.key)
            values[reg.key] = None
            return []
        contiguous = plan_blocks(block.registers, max_gap=0, max_count=MAX_COUNT)
        if len(contiguous) == 1:
            contiguous = [
                ReadBlock(block.table, r.address, r.count, (r,))
                for r in block.registers
            ]
        _LOGGER.debug(
            "Splitting rejected read %s@%s into %s requests",
            block.table,
            block.start,
            len(contiguous),
        )
        result: list[ReadBlock] = []
        for sub in contiguous:
            result.extend(await self._read_block(sub, values))
        return result

    async def async_set_ems(self, changes: dict[str, Any]) -> dict[str, int]:
        """
        Change EMS settings (register 4300-4307) in one validated write.

        ``changes`` maps setting keys (see EMS_SETTINGS) to engineering values;
        ``ems_mode`` takes an EmsMode or its string value.
        Returns the raw block that is now active on the device.
        """
        if not changes:
            msg = "No EMS settings given"
            raise ValueError(msg)
        requested = {}
        for key, value in changes.items():
            if key == "ems_mode":
                mode = EmsMode(value)
                if mode not in WRITABLE_EMS_MODES:
                    msg = f"EMS mode {mode} cannot be set remotely"
                    raise ValueError(msg)
                requested[key] = EMS_MODE_VALUES[mode]
            elif key in SETTINGS_BY_KEY and SETTINGS_BY_KEY[key] in EMS_SETTINGS:
                requested[key] = SETTINGS_BY_KEY[key].to_raw(float(value))
            else:
                msg = f"Unknown EMS setting {key}"
                raise ValueError(msg)
        return await self._write_settings(
            EMS_START, EMS_SETTINGS, requested, check=_check_ems_mode
        )

    async def async_set_soc_limits(
        self, *, max_soc: float | None = None, min_soc: float | None = None
    ) -> dict[str, int]:
        """Change the battery SOC limits (register 308/309) in one write."""
        requested: dict[str, int] = {}
        if max_soc is not None:
            requested["max_soc"] = SETTINGS_BY_KEY["max_soc"].to_raw(max_soc)
        if min_soc is not None:
            requested["min_soc"] = SETTINGS_BY_KEY["min_soc"].to_raw(min_soc)
        if not requested:
            msg = "No SOC limits given"
            raise ValueError(msg)
        return await self._write_settings(
            SOC_LIMIT_START, SOC_LIMIT_SETTINGS, requested, check=_check_soc_limits
        )

    async def _write_settings(
        self,
        start: int,
        settings: tuple[Setting, ...],
        requested: dict[str, int],
        check: Any = None,
    ) -> dict[str, int]:
        async with self._write_lock:
            current = await self._read_settings(start, settings)
            missing = set(requested) - set(current)
            if missing:
                msg = f"Not supported by this device: {', '.join(sorted(missing))}"
                raise HiOneError(msg)
            new = {**current, **requested}
            if check is not None:
                check(new)
            if new == current:
                _LOGGER.debug("Settings at %s already as requested", start)
                return current
            keys = [s.key for s in settings if s.key in current]
            count = len(keys)
            if start == EMS_START and new.get(keys[-1]) == current.get(keys[-1]):
                count = min(count, EMS_BASE_COUNT)
            payload = [new[k] for k in keys[:count]]
            _LOGGER.debug("Writing %s to holding register %s (FC16)", payload, start)
            await self._transport.async_write(start, payload)
            await asyncio.sleep(WRITE_SETTLE_DELAY)
            readback = await self._read_settings(start, settings)
            if any(readback.get(k) != new[k] for k in keys[:count]):
                msg = (
                    f"Device did not apply the settings at {start}: "
                    f"wrote {payload}, read back {[readback.get(k) for k in keys]}"
                )
                raise HiOneWriteError(msg)
            return readback

    async def _read_settings(
        self, start: int, settings: tuple[Setting, ...]
    ) -> dict[str, int]:
        count = len(settings)
        while True:
            try:
                words = await self._transport.async_read(Table.HOLDING, start, count)
                break
            except HiOneIllegalAddressError:
                # Older firmware may not know 4307; every other register is required.
                if start != EMS_START or count <= EMS_BASE_COUNT:
                    raise
                count -= 1
        values = {s.key: words[i] for i, s in enumerate(settings[:count])}
        _validate(values, settings[:count])
        return values


def _validate(values: dict[str, int], settings: Iterable[Setting]) -> None:
    raw = list(values.values())
    if len(raw) > 1 and len(set(raw)) == 1:
        msg = f"Implausible settings read (all values identical: {raw})"
        raise HiOneValidationError(msg)
    for setting in settings:
        value = values[setting.key]
        if not setting.raw_min <= value <= setting.raw_max:
            msg = (
                f"Implausible value {value} for {setting.key} "
                f"(expected {setting.raw_min}-{setting.raw_max}); not writing"
            )
            raise HiOneValidationError(msg)


def _check_ems_mode(new: dict[str, int]) -> None:
    # Also covers changing another setting while the device is in pure off-grid
    # mode: the current mode would otherwise be written back.
    if new["ems_mode"] not in {EMS_MODE_VALUES[m] for m in WRITABLE_EMS_MODES}:
        msg = "The device is in pure off-grid mode; select another EMS mode first"
        raise ValueError(msg)


def _check_soc_limits(new: dict[str, int]) -> None:
    if new["min_soc"] >= new["max_soc"]:
        msg = "Minimum SOC must be lower than maximum SOC"
        raise ValueError(msg)
