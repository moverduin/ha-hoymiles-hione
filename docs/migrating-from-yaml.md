# Migrating from a `modbus:` YAML configuration

Many HiOne owners start with Home Assistant's built-in Modbus integration and a list of registers in
YAML. This integration replaces that list. Because the DTS stick only serves **one** Modbus client,
the YAML hub and this integration cannot run side by side.

## Steps

1. **Write down what you use.** Note which `sensor.*` entities from the YAML hub are used in
   dashboards, automations, scripts, template sensors and the Energy dashboard.
2. **Remove the YAML hub.** Delete (or comment out) the `modbus:` entry for the HiOne, including any
   `modbus.write_register` calls in scripts.
3. **Restart Home Assistant** so the old connection is closed.
4. **Add this integration** (Settings → Devices & services → Add integration → Hoymiles HiOne (Modbus)).
5. **Update references** to the new entity IDs (table below). Alternatively, rename the new entities
   to the old IDs on the entity settings page so nothing else has to change.
6. **Energy dashboard:** select the new energy sensors. Long-term statistics of the old sensors stay
   available under their old IDs.
7. Replace scripts that wrote the EMS block with the `hoymiles_hione.set_ems` action (requires write
   access in the options). It already does read-validate-write-verify, so extra checks in your
   script are no longer needed.

## Register to entity mapping

| Register (YAML `address`) | Type | New entity |
|---|---|---|
| input 0 | uint16 | `sensor.hoymiles_hione_status` (as text) |
| input 50 | int32 | `sensor.hoymiles_hione_battery_power` |
| input 113 | int16 | `sensor.hoymiles_hione_inverter_temperature` |
| input 284 | int32 | `sensor.hoymiles_hione_house_consumption` |
| input 1808 / 1810 / 1812 | int32 | `sensor.hoymiles_hione_grid_power_l1` / `_l2` / `_l3` (**sign inverted**, disabled by default) |
| input 1814 | int32 | `sensor.hoymiles_hione_grid_power` (**sign inverted**: import is positive) |
| input 1904 | uint16 | `sensor.hoymiles_hione_battery_state` (as text) |
| input 1909 | uint16 | `sensor.hoymiles_hione_battery_state_of_charge` |
| input 1910 | uint16 | `sensor.hoymiles_hione_battery_state_of_health` |
| input 1911 | uint16 ×0.1 | `sensor.hoymiles_hione_battery_voltage` |
| input 1916 | uint16 ×0.1 | `sensor.hoymiles_hione_battery_max_charge_current` |
| input 1922 / 1923 | int16 ×0.1 | `sensor.hoymiles_hione_cell_temperature_max` / `_min` |
| input 2028 / 2030 | uint32 ×0.1 | `sensor.hoymiles_hione_battery_charged_energy` / `_discharged_energy` |
| input 2114 / 2115 | uint16 ×0.1 | `sensor.hoymiles_hione_battery_charged_today` / `_discharged_today` |
| holding 4300 | uint16 | `sensor.hoymiles_hione_ems_mode`, `select.hoymiles_hione_ems_mode` |
| holding 4301-4307 | uint16 | `number.hoymiles_hione_*` (see the README) |
| holding 308 / 309 | uint16 | `number.hoymiles_hione_maximum_soc` / `_minimum_soc` |

Templates that split battery power into charge and discharge parts are no longer needed: use
`sensor.hoymiles_hione_battery_charge_power` and `sensor.hoymiles_hione_battery_discharge_power`.
