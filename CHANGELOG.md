# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-18

### Added

- UI setup (config flow) for Modbus TCP and RTU-over-TCP, with reconfigure and options.
- Sensors for state of charge, state of health, battery/grid/house/PV power, voltages, currents,
  temperatures, EMS mode, status and energy counters (Energy dashboard ready).
- Decoded HiOne fault codes (`Active faults` sensor and `Fault` binary sensor).
- Optional write access (off by default): EMS mode select, reserve/target SOC and power numbers,
  SOC limits, and the `hoymiles_hione.set_ems` action.
- Safe writes: FC16 only, read-modify-write of the whole block, plausibility checks, read-back
  verification, no-op writes skipped, pure off-grid mode blocked.
- Automatic handling of registers that a firmware does not support.
- Diagnostics with redaction, English and Dutch translations.
- Register map documentation for protocol V2.8.

[Unreleased]: https://github.com/moverduin/ha-hoymiles-hione/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/moverduin/ha-hoymiles-hione/releases/tag/v0.1.0
