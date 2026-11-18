# Troubleshooting

## "Could not connect"

- Check that the host and port are right and that Home Assistant can reach the gateway
  (`ping`, or `nc -vz <host> 502` from a terminal add-on).
- Give the DTS stick / gateway a fixed IP address (DHCP reservation).
- Make sure **no other Modbus client** is connected (see below). While another client holds the
  connection, the device may accept the TCP connection but never answer.
- Gateways with a *Modbus TCP to RTU* option must have it enabled; otherwise choose *RTU over TCP*.

## Errors like `request ask for transaction_id=24 but got id=1`

A second Modbus client is talking to the same gateway, and responses are being delivered to the
wrong connection. Remove the other client: a `modbus:` hub in YAML, EVCC, Node-RED, a second Home
Assistant instance, or a test tool. This also happens when the old YAML configuration and this
integration run at the same time.

## "The device answered, but not like a Hoymiles storage system"

The gateway answered, but the battery level register (input 1909) was rejected. Check the Modbus
unit ID (usually `1`) and, for RS485 gateways, the serial settings (115200 baud, 8N1).

## Some entities are missing

Registers that your firmware does not support are detected during the first poll; no entities
are created for them. The diagnostics file lists them under `unsupported_registers`. Many niche
entities are also **disabled by default**: open the device page and enable them.

## Values look wrong

- **Battery power** is positive while discharging and negative while charging.
- **Grid power** is positive for import and negative for export (the device reports it the other way
  round; the integration inverts it).
- If a value is consistently off by a factor of 10, or has the wrong sign, please open a
  [device report](https://github.com/moverduin/ha-hoymiles-hione/issues/new?template=device_report.yml)
  with your model and firmware.
- If you have older Hoymiles hardware and the battery power is nonsense, try the *G1/G2* hardware
  generation via **Reconfigure**.

## A control does nothing or reports "did not apply the new settings"

- Check that write access is enabled in the options.
- The integration reads the setting back after writing. If the device reports a different value,
  it did not accept the write. Some firmware versions may reject a mode or value; check the device
  page for the current EMS mode.
- The Hoymiles S-Miles app/cloud can overwrite settings. Avoid changing the mode in the app at the
  same time.

## "Nothing was written because the current settings could not be read reliably"

Before every write the integration reads the whole settings block. If the values are implausible
(all identical, or out of range), nothing is written. This protects your battery from a corrupted
read being written back. It is usually caused by a second Modbus client or a flaky Wi-Fi gateway.
Try again; if it persists, attach diagnostics to an issue.

## Debug logging

```yaml
logger:
  default: warning
  logs:
    custom_components.hoymiles_hione: debug
    pymodbus: info
```

Or use **Enable debug logging** on the integration page, reproduce the problem and then disable it
again to download the log.
