"""Test configuration."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

HAS_HA = importlib.util.find_spec("pytest_homeassistant_custom_component") is not None

if not HAS_HA:
    # Without Home Assistant installed only the pure modules (registers, api) are
    # tested. Register the packages manually so their __init__ is not executed.
    root = Path(__file__).resolve().parents[1] / "custom_components"
    for name, path in (
        ("custom_components", root),
        ("custom_components.hoymiles_hione", root / "hoymiles_hione"),
    ):
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules.setdefault(name, module)
    collect_ignore = ["test_config_flow.py", "test_init.py"]
else:

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
        """Allow loading the custom integration in every test."""


@pytest.fixture(autouse=True)
def no_write_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not wait for the device to settle after writes."""
    from custom_components.hoymiles_hione import api  # noqa: PLC0415

    monkeypatch.setattr(api, "WRITE_SETTLE_DELAY", 0)
