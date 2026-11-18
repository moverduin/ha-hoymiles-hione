"""Write helpers shared by entities and services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .api import HiOneError, HiOneValidationError, HiOneWriteError
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .data import HiOneConfigEntry


async def async_write(
    entry: HiOneConfigEntry, write: Callable[[], Awaitable[Any]]
) -> None:
    """Run a write, translate errors and refresh the data afterwards."""
    if not entry.runtime_data.controls_enabled:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="controls_disabled"
        )
    try:
        await write()
    except ValueError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_value",
            translation_placeholders={"error": str(err)},
        ) from err
    except HiOneValidationError as err:
        LOGGER.warning("Write refused: %s", err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="implausible_read",
            translation_placeholders={"error": str(err)},
        ) from err
    except HiOneWriteError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="write_not_applied",
            translation_placeholders={"error": str(err)},
        ) from err
    except HiOneError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="write_failed",
            translation_placeholders={"error": str(err)},
        ) from err
    finally:
        await entry.runtime_data.coordinator.async_request_refresh()
