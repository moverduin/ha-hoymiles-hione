"""Constants for the Hoymiles HiOne integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "hoymiles_hione"
LOGGER = logging.getLogger(__package__)

MANUFACTURER: Final = "Hoymiles"
DEFAULT_MODEL: Final = "HiOne"

CONF_UNIT_ID: Final = "unit_id"
CONF_FRAMER: Final = "framer"
CONF_LAYOUT: Final = "layout"
CONF_ENABLE_CONTROLS: Final = "enable_controls"

FRAMER_TCP: Final = "tcp"
FRAMER_RTU_OVER_TCP: Final = "rtu_over_tcp"

DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600

SERVICE_SET_EMS: Final = "set_ems"
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
