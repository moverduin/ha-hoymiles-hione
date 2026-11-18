"""Polling coordinator for the Hoymiles HiOne integration."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HiOneError
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import HiOneApi
    from .data import HiOneConfigEntry


class HiOneCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Read all registers of one HiOne in a single polling cycle."""

    config_entry: HiOneConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: HiOneConfigEntry,
        api: HiOneApi,
        scan_interval: int,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_read_all()
        except HiOneError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        if all(value is None for value in data.values()):
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_data",
            )
        return data
