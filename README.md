# Hoymiles HiOne for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/moverduin/ha-hoymiles-hione/actions/workflows/validate.yml/badge.svg)](https://github.com/moverduin/ha-hoymiles-hione/actions/workflows/validate.yml)
[![Lint and test](https://github.com/moverduin/ha-hoymiles-hione/actions/workflows/ci.yml/badge.svg)](https://github.com/moverduin/ha-hoymiles-hione/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/moverduin/ha-hoymiles-hione?include_prereleases)](https://github.com/moverduin/ha-hoymiles-hione/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Local monitoring and control of a **Hoymiles HiOne** home battery in Home Assistant, over
**Modbus TCP**. No cloud, no YAML: set it up from the UI, use the sensors in the Energy dashboard
and (optionally) switch the battery between self-use, force charge and other modes from your
automations.

> [!NOTE]
> This is an independent community project. It is **not affiliated with or endorsed by Hoymiles**.
> "Hoymiles" and "HiOne" are trademarks of their respective owner.

> [!IMPORTANT]
> **Beta.** The register map is verified on a real HiOne, but this integration is new. Please
> [report](https://github.com/moverduin/ha-hoymiles-hione/issues/new/choose) what works and what does not.

## Features

- 🔌 **Local polling over Modbus TCP** (or RTU-over-TCP), set up via the UI.
- 🔋 Battery **state of charge**, health, power (with separate charge/discharge sensors), voltage,
  current limits and cell temperatures.
- 🏠 **Grid, house and PV power**, per phase where available.
- ⚡ **Energy counters** for the Energy dashboard (battery in/out, grid import/export, house, PV).
- 🚨 **Decoded fault codes**: an *Active faults* sensor that lists faults by name, plus a *Fault*
  problem sensor.
- 🎛️ **Optional controls** (off by default): EMS mode, reserve and target SOC, force charge/discharge
  power, SOC limits, and a `hoymiles_hione.set_ems` action that changes several settings in one write.
- 🛡️ **Safe writes**: only FC16, read-modify-write of whole blocks, plausibility checks, read-back
  verification, unchanged values are not written, and *pure off-grid* can never be selected remotely.
- 🧩 Adapts to your firmware: registers the device does not support are detected and skipped.
- 🩺 Diagnostics (redacted), English and Dutch translations.
- 📖 A full [register map](docs/registers.md) of the Hoymiles storage protocol.

## Supported hardware

| Device | Status |
|---|---|
| Hoymiles HiOne (G3) via the Hoymiles DTS stick | ✅ Register map verified |
| Other Hoymiles storage inverters using the same *Energy Storage MODBUS protocol* (G1/G2 layout) | ❓ Untested, please send a [device report](https://github.com/moverduin/ha-hoymiles-hione/issues/new?template=device_report.yml) |

You need network access to the Modbus interface: the Hoymiles DTS stick (Modbus TCP, port 502)
or an RS485-to-Ethernet/Wi-Fi gateway (for example Waveshare, Elfin/EW11 or USR) connected to the
RS485 port (115200 baud, 8N1).

## Important: read this first

1. **Only one Modbus client at a time.** The DTS stick serves a single TCP client. If a second
   client connects (a `modbus:` YAML hub, EVCC, Node-RED, a test tool, ...), responses get delivered
   to the wrong client and both see errors such as `request ask for transaction_id=X but got id=Y`.
   Remove other clients before adding this integration.
2. **Write access is off by default.** Turning it on lets Home Assistant change how your battery
   charges from and discharges to the grid. Use it at your own risk; the software comes without
   warranty (see [LICENSE](LICENSE)).
3. **Settings are stored in flash memory.** Do not write in a loop or every few seconds. The
   integration skips writes when nothing changes, but your automations should also only act on changes.
4. **Self-use reserve above the current SOC means charging from the grid.** If you set the
   *Self-use reserve SOC* higher than the battery's current level, the HiOne will charge from the grid
   until it reaches the reserve, whatever the electricity price.
5. **Grid code (safety) registers are never written** by this integration, and you should not write
   them yourself either (holding 100-299).
6. The Hoymiles **S-Miles app/cloud** can change the same settings. If you control the battery from
   Home Assistant, avoid also changing the mode in the app.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moverduin&repository=ha-hoymiles-hione&category=integration)

1. In HACS, open the ⋮ menu → **Custom repositories**.
2. Add `https://github.com/moverduin/ha-hoymiles-hione` with type **Integration**.
3. Search for **Hoymiles HiOne (Modbus)** and download it.
4. Restart Home Assistant.

### Manual

Copy `custom_components/hoymiles_hione` into the `custom_components` folder of your Home Assistant
configuration directory and restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hoymiles_hione)

Go to **Settings → Devices & services → Add integration → Hoymiles HiOne (Modbus)** and enter:

| Field | Description |
|---|---|
| Host | IP address or hostname of the DTS stick / Modbus gateway. Give it a fixed IP (DHCP reservation). |
| Port | Usually `502`. |
| Modbus unit ID | Usually `1`. |
| Protocol | *Modbus TCP* for the DTS stick and most gateways; *RTU over TCP* for gateways in transparent mode. |
| Hardware generation | *G3* for the HiOne. *G1/G2* only for older Hoymiles hybrid inverters. |

You can change the connection later with **Reconfigure**.

### Options

| Option | Default | Description |
|---|---|---|
| Polling interval | 30 s | How often all values are read (10-3600 s). |
| Enable write access | off | Adds the controls and enables the `set_ems` action. Read [Important: read this first](#important-read-this-first). |

## Entities

Entity IDs below assume the device is called *Hoymiles HiOne*.

### Enabled by default

| Entity | Description |
|---|---|
| `sensor.hoymiles_hione_battery_state_of_charge` | Battery level (%) |
| `sensor.hoymiles_hione_battery_state_of_health` | Battery health (%) |
| `sensor.hoymiles_hione_battery_power` | Battery power (W), **positive = discharging**, negative = charging |
| `sensor.hoymiles_hione_battery_charge_power` / `..._discharge_power` | Charge / discharge power, always ≥ 0 |
| `sensor.hoymiles_hione_grid_power` | Grid power from the HiOne's meter (W), **positive = import**, negative = export |
| `sensor.hoymiles_hione_house_consumption` | House consumption (W) |
| `sensor.hoymiles_hione_pv_power` | PV power connected to the HiOne (W) |
| `sensor.hoymiles_hione_status` | Inverter status (on grid, off grid, standby, fault, ...) |
| `sensor.hoymiles_hione_battery_state` | Charging / discharging / standby |
| `sensor.hoymiles_hione_ems_mode` | Active EMS mode |
| `sensor.hoymiles_hione_battery_charged_energy` / `..._discharged_energy` | Lifetime battery energy (kWh) |
| `sensor.hoymiles_hione_grid_import_energy` / `..._grid_export_energy` | Lifetime grid energy measured by the HiOne's meter (kWh) |
| `sensor.hoymiles_hione_house_consumption_energy`, `sensor.hoymiles_hione_pv_energy` | Lifetime house / PV energy (kWh) |
| `sensor.hoymiles_hione_battery_charged_today` / `..._discharged_today` | Today's battery energy (kWh) |
| `binary_sensor.hoymiles_hione_fault` | On when any fault bit is set |
| Diagnostic | Voltage, max charge current, capacity, cell and inverter temperatures, meter status, active faults (with a `faults` attribute), battery/meter connectivity |

### Disabled by default

Per-phase grid power/voltage/current, PV string values, inverter and backup port power, extra
temperatures, frequencies, cut-off voltages, raw fault codes and the *today* counters for grid,
house and PV. Enable them on the device page if you need them.

### Controls (only with write access)

| Entity | Register | Range |
|---|---|---|
| `select.hoymiles_hione_ems_mode` | 4300 | Self-use, economic, backup, force charge, force discharge, peak shaving, time of use |
| `number.hoymiles_hione_self_use_reserve_soc` | 4301 | 10-100 % |
| `number.hoymiles_hione_backup_reserve_soc` | 4302 | 60-100 % |
| `number.hoymiles_hione_force_charge_target_soc` | 4303 | 10-100 % |
| `number.hoymiles_hione_force_charge_power` | 4304 | 10-100 % of maximum |
| `number.hoymiles_hione_force_discharge_target_soc` | 4305 | 10-100 % |
| `number.hoymiles_hione_force_discharge_power` | 4306 | 10-100 % of maximum |
| `number.hoymiles_hione_economic_mode_reserve_soc` | 4307 | 10-100 % |
| `number.hoymiles_hione_maximum_soc` / `..._minimum_soc` | 308 / 309 | 10-100 % / 10-90 % |

## Action: `hoymiles_hione.set_ems`

Changes the EMS mode and/or its settings in **one** write. The current block is read and checked
first, unchanged values are not written, and the result is read back. Requires write access.

```yaml
action: hoymiles_hione.set_ems
data:
  config_entry_id: 0123456789abcdef0123456789abcdef  # pick the device in the UI editor
  ems_mode: force_charge
  force_charge_target_soc: 90
  force_charge_power: 50
```

Available fields: `ems_mode`, `self_use_reserve_soc`, `backup_reserve_soc`, `economic_reserve_soc`,
`force_charge_target_soc`, `force_charge_power`, `force_discharge_target_soc`, `force_discharge_power`.
See [docs/automations.md](docs/automations.md) for complete examples, such as charging during the
cheapest hours.

## Energy dashboard

**Settings → Dashboards → Energy**:

- **Home battery storage**: *energy going in* = `Battery charged energy`, *energy coming out* =
  `Battery discharged energy`. If Home Assistant asks for a battery power sensor, use
  `Battery power` (positive = discharging, negative = charging).
- **Grid**: if you have no other meter (such as a P1/DSMR reader), use `Grid import energy` and
  `Grid export energy`. A P1 meter is usually more accurate; prefer it when available.
- **Solar**: `PV energy`, only for PV connected to the HiOne itself.

## Migrating from a `modbus:` YAML configuration

See [docs/migrating-from-yaml.md](docs/migrating-from-yaml.md). In short: remove the YAML hub
first (only one client can be connected), restart, then add the integration.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md). When reporting a problem, attach the
diagnostics (device page → ⋮ → *Download diagnostics*) and enable debug logging:

```yaml
logger:
  logs:
    custom_components.hoymiles_hione: debug
```

## Register map

[docs/registers.md](docs/registers.md) lists all registers of the Hoymiles *Energy Storage MODBUS
protocol* (V2.8): addresses, types, scales and meanings, which registers this integration uses, and
the quirks found on real hardware. The vendor document itself is not distributed here.

## Contributing

Contributions are welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) to get started. Device reports
and register findings are especially valuable.

## License

[MIT](LICENSE)
