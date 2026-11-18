# Security policy

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Report them privately via
[GitHub private vulnerability reporting](https://github.com/moverduin/ha-hoymiles-hione/security/advisories/new).

You can expect an acknowledgement within a week. Once a fix is available it is released and the
advisory is published.

## Scope and design notes

- Modbus TCP has **no authentication or encryption**. Anyone on the same network can read and
  change battery settings. Keep the DTS stick / Modbus gateway on a trusted network segment
  (for example an IoT VLAN that only Home Assistant can reach) and never expose port 502 to the
  internet.
- Write access in this integration is **off by default** and must be enabled in the options.
- Writes are limited to the EMS block (holding 4300-4307) and the SOC limits (holding 308-309).
  Grid code (safety) registers are never written.
- Diagnostics redact the host address and serial number.
