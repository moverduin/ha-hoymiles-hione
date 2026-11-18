# Contributing

Thanks for helping to improve this integration! Contributions of all kinds are welcome:
bug reports, device reports, register findings, translations, documentation and code.

## Ground rules

- Be kind. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- **Never commit vendor documents** (such as the Hoymiles protocol PDF), serial numbers, IP
  addresses or other personal data. Describe register findings in your own words in
  [`docs/registers.md`](docs/registers.md).
- **Changes that write to the device must be tested on real hardware.** Mention the model and
  firmware in the pull request.
- Keep writes conservative: read-modify-write whole blocks, validate what is read back, and
  only use *Write Multiple Registers* (FC16). The Hoymiles DTS stick ignores FC06.

## Reporting a problem

Use the [issue forms](https://github.com/moverduin/ha-hoymiles-hione/issues/new/choose) and attach
the diagnostics file (device page → ⋮ → *Download diagnostics*). It is redacted automatically.

Enable debug logging to capture what happens on the wire:

```yaml
logger:
  default: warning
  logs:
    custom_components.hoymiles_hione: debug
    pymodbus: info
```

## Development setup

The integration targets the current Home Assistant release (Python 3.14).

### Dev container (recommended)

Open the repository in VS Code and choose *Reopen in Container*. Then run:

```bash
scripts/setup      # install requirements
scripts/develop    # start Home Assistant on http://localhost:8123 with this integration loaded
```

### Local virtual environment

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements_dev.txt
```

## Project layout

| Path | Purpose |
|---|---|
| `custom_components/hoymiles_hione/registers.py` | Register definitions, decoding, read planning, fault tables. **No Home Assistant imports.** |
| `custom_components/hoymiles_hione/api.py` | Modbus client and the safe read/write API. **No Home Assistant imports.** |
| `custom_components/hoymiles_hione/coordinator.py` | Polling via `DataUpdateCoordinator`. |
| `custom_components/hoymiles_hione/sensor.py`, `binary_sensor.py`, `select.py`, `number.py` | Entities. |
| `custom_components/hoymiles_hione/services.py` | The `hoymiles_hione.set_ems` action. |
| `custom_components/hoymiles_hione/translations/` | English and Dutch texts. |
| `tests/` | Pytest suite with an in-memory fake Modbus device (`tests/fake.py`). |
| `docs/` | Register map and user documentation. |

### Adding a sensor

1. Add the register to `COMMON_REGISTERS` in `registers.py` (address, type, scale, plausible range).
2. Add an entity description to `SENSORS` in `sensor.py`. Prefer `entity_registry_enabled_default=False`
   for niche values.
3. Add the name to `translations/en.json` and `translations/nl.json`, and an icon to `icons.json` if useful.
4. Mark the register as used in `docs/registers.md` and add a test.

Registers the device rejects are detected automatically; entities for them are not created.

## Checks

Run these before opening a pull request. CI runs the same checks, plus `hassfest` and the HACS validation.

```bash
ruff format .
ruff check .
pytest
```

The tests for `registers.py` and `api.py` also run without Home Assistant installed (`pytest`
skips the Home Assistant tests automatically), which is handy for quick iterations.

## Translations

Every user-facing string lives in `translations/en.json`. Copy new keys to every other language
file. If you add a language, translate all keys of `en.json`.

## Releasing (maintainers)

1. Update `version` in `manifest.json` and move the *Unreleased* notes in `CHANGELOG.md` to a new version.
2. Merge to `main`.
3. Create a GitHub release with tag `vX.Y.Z`. The release workflow checks the version and attaches a zip.
