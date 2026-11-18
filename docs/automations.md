# Automation examples

All examples need **write access** (integration options). Replace the `config_entry_id` with
your own: in the automation editor, pick the device in the *Device* field of the action and switch
to YAML to see the ID.

> [!TIP]
> Only write when something changes. Each write is stored in the battery's flash memory.
> Triggers on state changes or fixed times are fine; `time_pattern` loops that write every
> minute are not.

## Charge from the grid during the cheapest hours

Uses a binary sensor that is `on` during cheap hours. Most dynamic-tariff integrations (Nord Pool,
Frank Energie, Tibber, ENTSO-e, ...) or a template can provide one.

```yaml
alias: Home battery - charge in cheap hours
mode: queued
triggers:
  - trigger: state
    entity_id: binary_sensor.cheap_electricity
    to: "on"
    id: cheap
  - trigger: state
    entity_id: binary_sensor.cheap_electricity
    to: "off"
    id: normal
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: cheap
        sequence:
          - action: hoymiles_hione.set_ems
            data:
              config_entry_id: 0123456789abcdef0123456789abcdef
              ems_mode: force_charge
              force_charge_target_soc: 90
              force_charge_power: 50
    default:
      - action: hoymiles_hione.set_ems
        data:
          config_entry_id: 0123456789abcdef0123456789abcdef
          ems_mode: self_use
```

## Keep more in reserve when an outage is likely

Raise the self-use reserve when, for example, a storm warning is active. Keep the reserve **below
the current state of charge**, otherwise the HiOne charges from the grid to reach it.

```yaml
alias: Home battery - storm reserve
triggers:
  - trigger: state
    entity_id: binary_sensor.storm_warning
actions:
  - variables:
      soc: "{{ states('sensor.hoymiles_hione_battery_state_of_charge') | int(0) }}"
      reserve: >-
        {{ ([soc - 1, 60] | min) if trigger.to_state.state == 'on' else 20 }}
  - action: hoymiles_hione.set_ems
    data:
      config_entry_id: 0123456789abcdef0123456789abcdef
      self_use_reserve_soc: "{{ [reserve, 10] | max }}"
```

## Notify on a fault

Works without write access.

```yaml
alias: Home battery - fault notification
triggers:
  - trigger: state
    entity_id: binary_sensor.hoymiles_hione_fault
    to: "on"
    for: "00:01:00"
actions:
  - action: notify.notify
    data:
      title: Home battery fault
      message: >-
        {{ state_attr('sensor.hoymiles_hione_active_faults', 'faults') | join(', ') }}
```

## Notify when the battery is unreachable

```yaml
alias: Home battery - connection lost
triggers:
  - trigger: state
    entity_id: sensor.hoymiles_hione_battery_state_of_charge
    to: unavailable
    for: "00:15:00"
actions:
  - action: notify.notify
    data:
      title: Home battery
      message: >-
        The HiOne has not answered for 15 minutes. It keeps running in the last mode
        ({{ states('sensor.hoymiles_hione_ems_mode') }}).
```
