"""Runtime data for the Hoymiles HiOne integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import DeviceInfo, HiOneApi
    from .coordinator import HiOneCoordinator


type HiOneConfigEntry = ConfigEntry[HiOneData]


@dataclass
class HiOneData:
    """Objects shared by the platforms of one config entry."""

    api: HiOneApi
    coordinator: HiOneCoordinator
    device: DeviceInfo
    controls_enabled: bool
