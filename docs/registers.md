# Register map

Register reference for Hoymiles energy storage systems (HiOne and related models), compiled from the manufacturer's *Energy Storage MODBUS Protocol* version 2.8 and checked against a real HiOne where noted. The protocol document itself is not included in this repository.

## Conventions

- Addresses are **0-based protocol addresses** (the value sent on the wire), in decimal.
- **Input registers** are read with function code 0x04, **holding registers** with 0x03.
- **Writes:** the Hoymiles DTS stick ignores *Write Single Register* (0x06). Always use *Write Multiple Registers* (0x10), even for one register.
- 32/64-bit values are big-endian: high word first. Strings hold two ASCII characters per register.
- **Scale** shows the divisor: `÷10` means the raw value 262 is 26.2.
- **Default** and **Range** are copied as published; ranges are sometimes raw and sometimes in engineering units.
- Last column: ✅ = read by this integration, *verified* = confirmed on a real HiOne (G3).
- Only one Modbus TCP client can be connected to the DTS stick at a time.

## Verified on a HiOne

| Register | Finding |
|---|---|
| Input 50 (I32) | Battery power, **positive = discharging**, negative = charging (G3 layout). |
| Input 1814 (I32) | Grid power from the house meter, **negative = import**. The integration inverts it. |
| Input 1922/1923 | Cell temperatures are reported in **0.1 °C** (the document says factor 1). |
| Holding 4300-4306 | EMS block; written as a whole with FC16, read back afterwards. |
| Holding 4301 | Setting the self-use reserve **above the current SOC makes the HiOne charge from the grid**. |

## Contents

**Holding registers:** [Advanced configuration](#holding-advanced-configuration), [Safety / grid code parameters](#holding-safety--grid-code-parameters), [System parameters](#holding-system-parameters), [Battery charge/discharge parameters](#holding-battery-chargedischarge-parameters), [PV parameters](#holding-pv-parameters), [EPS (backup) parameters](#holding-eps-backup-parameters), [Generator parameters](#holding-generator-parameters), [Professional configuration](#holding-professional-configuration), [Inverter commands](#holding-inverter-commands), [Battery configuration](#holding-battery-configuration), [Dry contact, load control and generator](#holding-dry-contact-load-control-and-generator), [EMS parameters](#holding-ems-parameters), [Time of use (TOU)](#holding-time-of-use-tou), [Heat pump](#holding-heat-pump), [EV chargers](#holding-ev-chargers), [Gateway](#holding-gateway), [Installation information (parallel systems)](#holding-installation-information-parallel-systems), [System common settings](#holding-system-common-settings), [Inverter information](#holding-inverter-information), [Battery system information](#holding-battery-system-information), [Battery pack information](#holding-battery-pack-information), [DTU parameters](#holding-dtu-parameters)

**Input registers:** [System (inverter)](#input-system-inverter), [Meters](#input-meters), [Battery cluster](#input-battery-cluster), [Energy and power flow](#input-energy-and-power-flow), [EV chargers](#input-ev-chargers), [Gateway / HMID](#input-gateway--hmid), [Battery packs](#input-battery-packs), [Second-level data](#input-second-level-data), [Real-time load data](#input-real-time-load-data)

[Fault codes](#fault-codes)


# Holding registers


## Holding Advanced configuration

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 5 | Data Number Hi | 0x00 | The amount of regsters |  |  |  |  |  |  |
| 6 | Data Number Lo | 0x02 |  |  |  |  |  |  |  |
| 6 | Meter Model | RW | U16 |  |  | 1 | [0,7] | 0:No Meter 1:Single-phase Meter 2:Two-phase Meter 3:Three-phase Meter 4:HMID Meter 5.CT 6.Acrel Single Meter 7.Acrel Dual Meter |  |
| 7 | CRC-16 Lo | CRC Lo | CRC Code of verification |  |  |  |  |  |  |
| 8 | CRC-16 Hi | CRC Hi |  |  |  |  |  |  |  |
| 8 | Display Brightness | RW | U16 |  |  | 10 | [1,10] |  |  |
| 11 | GEN Port Mode | RW | U16 |  |  | 0 | [0,4] | 0:Disable 1:PV 2:Generator 3:Force On 4.Load Control |  |
| 12 | GEN Location | RW | U16 |  |  | 0 | [0,2] | 0:None 1:Gen Side 2:Grid Side |  |
| 13 | GEN Signal Setting | RW | U16 |  |  | 0 | [0,1] | 0:Manual 1:DI/DO |  |
| 14 | GEN Minimum Run Time | RW | U16 | min |  | 10 | [5,60] |  |  |
| 15 | GEN Maximum Run Time | RW | U16 | h |  | 8 | [6,10] |  |  |
| 16 | GEN Run Protection Interval | RW | U16 | min |  | 10 | [5,60] |  |  |
| 17 | GEN Synchronize Time | RW | U16 | min |  | 5 | [1,20] |  |  |
| 18 | GEN Shutdown Delay | RW | U16 | min |  | 5 | [1,20] |  |  |
| 20 | Grid CT Reverse Enable | RW | U16 |  |  | 0 | [0,1] | 0:Disable 1:Enable | verified |
| 21 | PV CT Reverse Enable | RW | U16 |  |  | 0 | [0,1] | 0:Disable 1:Enable |  |
| 25 | Grid CT Ratio | RW | U16 |  |  | 1 | [1,9999] |  | verified |
| 26 | PV CT Ratio | RW | U16 |  |  | 1 | [1,9999] |  |  |
| 28 | HMID/Gateway Enable | RW | U16 |  |  | 0 | [0,1] | 0:Disable 1:Enable |  |
| 32 | PV Meter Enable | RW | U16 |  |  | 0 | [0,1] | 0:Disable 1:Enable |  |

## Holding Safety / grid code parameters

> [!CAUTION]
> These registers hold the grid code (country) settings that were set by the installer. Changing them can make the installation non-compliant or unsafe. Writing any register in this range with FC06 switches **all** safety parameters to their defaults. Never write these registers.
> Bit definitions of the `FuncCode` registers are in the protocol document (appendix 1).

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 100 | Country | RW | U16 |  |  |  |  |  |  |
| 101 | Rated Voltage | RW | U16 | V | ÷10 |  |  |  |  |
| 102 | Rated Frequency | RW | U16 | Hz | ÷100 |  |  |  |  |
| 103 | VRT FuncCode | RW | U16 |  |  |  | [1, 65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 104 | Voltage High Limit3 | RW | U16 | V | ÷10 |  | [600,3000] | Overvoltage (60V~300V) |  |
| 105 | Voltage High Limit3 Time | RW | U16 | s | ÷100 |  | [ 1,65535] | Overvoltage Limit Time (0.01s~) |  |
| 106 | Voltage High Limit2 | RW | U16 | V | ÷10 |  | [600,3000] | (60V~300V) |  |
| 107 | Voltage High Limit2 Time | RW | U16 | s | ÷100 |  | [ 1,65535] | Overvoltage Limit Time (0.01s~) |  |
| 108 | Voltage High Limit1 | RW | U16 | V | ÷10 |  | [600,3000] | (60V~300V) |  |
| 109 | Voltage High Limit1 Time | RW | U16 | s | ÷10 |  | [ 1,65535] | Overvoltage Limit Time (0.01s~) |  |
| 110 | Voltage Low Limit1 | RW | U16 | V | ÷10 |  | [600,3000] | Undervoltage(60V~300V) |  |
| 111 | Voltage Low Limit1 Time | RW | U16 | s | ÷10 |  | [ 1,65535] | Undervoltage Limit Time (0.01s~) |  |
| 112 | Voltage Low Limit2 | RW | U16 | V | ÷10 |  | [600,3000] | (60V~300V) |  |
| 113 | Voltage Low Limit2 Time | RW | U16 | s | ÷100 |  | [ 1,65535] | Undervoltage Limit Time (0.01s~) |  |
| 114 | Voltage Low Limit3 | RW | U16 | V | ÷10 |  | [600,3000] | (60V~300V) |  |
| 115 | Voltage Low Limit3 Time | RW | U16 | s | ÷100 |  | [ 1,65535] | Undervoltage Limit Time (0.01s~) |  |
| 116 | Recovery Stable Time | RW | U16 | s | ÷10 |  | [ 1,65535] | Voltage recovery time |  |
| 117 | 10 Min Average High Voltage | RW | U16 | V | ÷10 |  | [ 1,65535] | Average Overvoltage Protection in 10 minutes (AHV) |  |
| 118 | VRT En | RW | U16 |  |  |  | [0,1] | Used together with register 30119-30120 0: Disable 1: Enable |  |
| 119 | VRT HighLimit(MCHV) | RW | U16 | V | ÷10 |  | [600,4000] | Upper threshold (60v ~400v) |  |
| 120 | VRT Low Limit(MCLV) | RW | U16 | V | ÷10 |  | [600,4000] | Lower threshold (60v ~400v) |  |
| 121 | Transient Over Voltage | RW | U16 | V | ÷10 |  | [600,5000] | Transient overvoltage (60v ~500v) |  |
| 122 | Transient Over Time | RW | U16 | s | ÷100 |  | [1, 65535] | Transient overvoltage time |  |
| 123 | FRT FuncCode | RW | U16 |  |  |  | [1, 65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 124 | FRT High Limit3 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Over Frequency (30HZ~80HZ) |  |
| 125 | FRT High Limit3 Time | RW | U16 | s | ÷100 |  | [ 1,65535] | Over Frequency Limit Time (0.01s~) |  |
| 126 | FRT High Limit2 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | (30HZ~80HZ) |  |
| 127 | FRT High Limit2 Time | RW | U16 | s | ÷100 |  | [ 1,65635] | Over Frequency Limit Time (0.01s~) |  |
| 128 | FRT High Limit1 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | (30HZ~80HZ) |  |
| 129 | FRT High Limit1 Time | RW | U16 | s | ÷10 |  | [ 1,65635] | Over Frequency Limit Time (0.01s~) |  |
| 130 | FRT Low Limit1 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | (30HZ~80HZ) |  |
| 131 | FRT Low Limit1 Time | RW | U16 | s | ÷10 |  | [ 1,65635] | Under Frequency Limit Time (0.01s~) |  |
| 132 | FRT Low Limit2 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | (30HZ~80HZ) |  |
| 133 | FRT Low Limit2 Time | RW | U16 | s | ÷100 |  | [ 1,65635] | Under Frequency Limit Time (0.01s~) |  |
| 134 | FRT Low Limit3 | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | (30HZ~80HZ) |  |
| 135 | FRT Low Limit3 Time | RW | U16 | s | ÷100 |  | [ 1,65635] | Under Frequency Limit Time (0.01s~) |  |
| 136 | RT FuncCode | RW | U16 |  |  |  | [1,65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 137 | RT NMTime(NM) | RW | U16 | s | ÷10 |  | [ 1,1200] | Normal Reconnect Time(0.1s~120s) |  |
| 138 | RT SRT Time | RW | U16 | s | ÷10 |  | [ 1,1200] | Normal Reconnect Time(0.1s~120s) |  |
| 140 | RT Volt Recovery High | RW | U16 | V | ÷10 |  | [600,3000] | Reconnect voltage (60v~300V) Value(RHV) |  |
| 141 | RT Volt Recovery Low Value(RLV) | RW | U16 | V | ÷10 |  | [600,3000] | Reconnect voltage (60v~300V) |  |
| 142 | RT Freq Recovery High | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Reconnect frequency (30HZ~80HZ) Value(RHF) |  |
| 143 | RT Freq Recovery Low Value(RLF) | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Reconnect frequency (30HZ~80HZ) |  |
| 144 | RCD Enable | RW | U16 |  |  |  | [0,1] | Enable RCD Function 0: disable 1: enable |  |
| 145 | Continue Limit Value | RW | U16 | mA |  |  | [1,1000] | (1mA~1A) |  |
| 146 | Continue Limit Time | RW | U16 | ms |  |  | [1,1000] | (1ms~1S) |  |
| 147 | Step1 Limit Value | RW | U16 | mA |  |  | [1,1000] | (1ma~1A) |  |
| 148 | Step1 Limit Time | RW | U16 | ms |  |  | [1,1000] | (1ms~1S) |  |
| 149 | Step2 Limit Value | RW | U16 | mA |  |  | [1,1000] | (1ma~1A) |  |
| 150 | Step2 Limit Time | RW | U16 | ms |  |  | [1,1000] | (1ms~1S) |  |
| 151 | Step3 Limit Value | RW | U16 | mA |  |  | [1,1000] | (1ma~1A) |  |
| 152 | Step3 Limit Time | RW | U16 | ms |  |  | [1,1000] | (1ms~1S) |  |
| 153 | DCI Enable | RW | U16 |  |  |  | [0,1] | Enable DCI Function 0: disable 1: enable |  |
| 154 | Upper Limit | RW | U16 | mA |  |  | [1,10000] | (1mA~10A) |  |
| 155 | Upper Time | RW | U16 | ms |  |  | [1,10000] | (1mS~10S) |  |
| 156 | Lower Limit | RW | U16 | mA |  |  | [1,10000] | (1mA~10A) |  |
| 157 | Lower Time | RW | U16 | ms |  |  | [1,10000] | (1mS~10S) |  |
| 160 | Rated Angle | RW | U16 | ° |  |  |  |  |  |
| 168 | Grid level 2 limit time scale | RW | U16 |  |  |  | [1,65535] | Time Magnification coefficient |  |
| 169 | Perimit Enable | RW | U16 |  |  |  | [0,1] | Enter service enable 0: disable 1: enable |  |
| 170 | ROCOF Protect Value | RW | U16 | Hz/s | ÷100 |  | [10,1000] |  |  |
| 171 | ROCOF Protect Time | RW | U16 | s | ÷10 |  | [1,50] |  |  |
| 172 | RT ST HighVolt(NHV) | RW | U16 | V | ÷10 |  | [600,3000] | Reconnect voltage (60v~300V) |  |
| 173 | RT ST LowVolt(NLV) | RW | U16 | V | ÷10 |  | [600,3000] | Reconnect voltage (60v~300V) |  |
| 174 | RT ST HighFreq(NHF) | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Reconnect frequency (30HZ~80HZ) |  |
| 175 | RT ST LowFreq(NLF) | RW | U16 | Hz | ÷100 |  |  | [3000 ,8000] Reconnect frequency (30HZ~80HZ) |  |
| 200 | DRM Enable | RW | U16 |  |  |  | [0,1] | DRM Function 0: disable 1: enable |  |
| 201 | Anti-islanding Enable | RW | U16 |  |  |  | [0,1] | Enable Island Detection |  |
| 202 | RR FuncCode | RW | U16 |  |  |  | [1, 65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 203 | RR RUR NM | RW | U16 | % | ÷100 |  | [1, 10000] | (0.01% /S~100%/S) |  |
| 204 | RR RUR SS | RW | U16 | % | ÷100 |  | [1, 10000] | (0.01% /S~100%/S) |  |
| 205 | FW FuncCode | RW | U16 |  |  |  | [1, 65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 206 | FW Enable | RW | U16 |  |  |  | [0,1] | Function Enable 0: disable 1: enable |  |
| 207 | FW DiffInBatMode | RW | I16 |  |  |  | [0,1] | Battery mode 0: disable 1: enable |  |
| 208 | FW Tr | RW | U16 | s | ÷10 |  | [0,1200] | Response time(0, 120s) |  |
| 209 | FW Recovery Upper | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Restore the frequency cap (30HZ~80HZ) Frequency(RVHF) |  |
| 210 | FW Recovery Lower | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Restore the lower limit offrequency(30HZ~80HZ) Frequency(RVLF) |  |
| 211 | FW Recovery Stable Time | RW | U16 | s | ÷10 |  | [0, 1200] | Restore stabilization time (0, 120s) |  |
| 212 | FW Over Start Freq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Over frequency start (30HZ~80HZ) |  |
| 213 | FW Over End Freq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Over frequency termination point (30HZ~80HZ) |  |
| 214 | FW Over TransFreq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Over frequency traversal frequency (30HZ~80HZ) |  |
| 215 | FW Under Start Freq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Underfrequency starting point (30HZ~80HZ) |  |
| 216 | FW Under End Freq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Underfrequency termination point (30HZ~80HZ) |  |
| 217 | FW Under StopFreq | RW | U16 | Hz | ÷100 |  | [3000 ,8000] | Underfrequency charging stop frequency (30HZ~80HZ) |  |
| 218 | VW FuncCode | RW | U16 |  |  |  | [1,65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 219 | VW Enable | RW | U16 |  |  |  | [0,1] | Voltage active control is enabled 0: disable 1: enable |  |
| 220 | VW DiffInBatMode | RW | U16 |  |  |  | [0,1] | The battery is force- charged |  |
| 221 | VW Tr | RW | U16 | s | ÷10 |  | [0,1200] | Response time (0, 120s) |  |
| 222 | VW Recovery Upper | RW | U16 | V | ÷10 |  | [600,3000] | The recover upper limit voltage (60V~300V) Voltage(RVHV) |  |
| 223 | VW Recovery Lower | RW | U16 | V | ÷10 |  | [600,3000] | The recover lower limit voltage(60V~300V) Voltage(RVLV) |  |
| 224 | VW Recovery Stable Time(RST) | RW | U16 | s | ÷10 |  | [0,1200] | Voltage returns to the stabilization time (0, 120s) |  |
| 225 | VW Over Start Volt | RW | U16 | V | ÷10 |  | [600,3000] | The starting value of the overvoltage load drop(60V~300V) |  |
| 226 | VW Over End Volt | RW | U16 | V | ÷10 |  | [600,3000] | Overvoltage load drop end value(60V~300V) |  |
| 227 | VW Over KPVolt | RW | U16 | % | ÷10 |  | [0, 1000] | Overvoltage load drop factor (*10) |  |
| 228 | VW Under Start Volt | RW | U16 | V | ÷10 |  | [600,3000] | The starting value of the underfrequency ramp load ( 60V~300V) |  |
| 229 | VW Under End Volt | RW | U16 | V | ÷10 |  | [600,3000] | The end value of the underfrequency ramp-up (60V~300V) |  |
| 230 | VW Under KPVolt | RW | U16 | % | ÷10 |  | [0, 1000] | Under pressure load lift factor (*10) |  |
| 231 | RP Mode | RW | U16 |  |  |  | [0, 5] | Reactive Power Control Mode 0 – Disable 1 - Fixed Power Factor, PF Mode 2 - Fixed Reactive Power, Q Mode 3 - WPF Watt Power Factor 4 - VV Volt Var 5 - PQ |  |
| 232 | RPC Tr | RW | U16 | s | ÷10 |  | [0,1000] | Reactive power adjustment time (0~100S ) |  |
| 233 | RPC PF | RW | I16 |  | ÷1000 |  | [- 1000,1000] | Power Factor (-1~ 1) |  |
| 234 | RPC ReactPower Ratio | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Fixed reactive power(- 100%~100%) |  |
| 235 | WPF FuncCode | RW | U16 |  |  |  | [0,65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 236 | WPF PowerStartRatio | RW | U16 | % | ÷10 |  | [0,1500] | The power factor regulates the starting power (0%, 150%) |  |
| 237 | WPF PowerEndRatio | RW | U16 | % | ÷10 |  | [0,1500] | The power factor regulates the end power (0%, 150%) |  |
| 238 | WPF MinPFOver | RW | I16 |  | ÷1000 |  | [- 1000,1000] | Minimum lead power factor (-1~ 1) |  |
| 239 | WPF MinPFUnder | RW | I16 |  | ÷1000 |  | [- 1000,1000] | Minimum hysteresis power factor (-1~ 1) |  |
| 240 | WPF LockIn(LIV) | RW | U16 | % | ÷10 |  | [0,1300] | Start PF to adjust the voltage ratio (0%~130%) |  |
| 241 | WPF LockOut(LOV) | RW | U16 | % | ÷10 |  | [0,1300] | Exit PF regulates the voltage ratio (0%~130%) |  |
| 242 | VV FuncCode | RW | U16 |  |  |  | [0,65535] | Defined By Bits, Details refer to Appendix 1 |  |
| 243 | VV V1 | RW | U16 | % | ÷10 |  | [0,1500] | Voltage, reactive power curve, voltage setting, V1 (0%~150%) |  |
| 244 | VV V2 | RW | U16 | % | ÷10 |  | [0,1500] | Voltage, reactive power curve, voltage setting, V2 (0%~150%) |  |
| 245 | VV V3 | RW | U16 | % | ÷10 |  | [0,1500] | Voltage, reactive power curve, voltage setting, V3 (0%~150%) |  |
| 246 | VV V4 | RW | U16 | % | ÷10 |  | [0,1500] | Voltage, reactive power curve, voltage set V4 (0%~150%) |  |
| 247 | VV Q1 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Voltage reactive power curve reactive power setting Q1 (- 100%~100%) |  |
| 248 | VV Q2 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Voltage reactive power curve reactive power setting Q2(- 100%~100%) |  |
| 249 | VV Q3 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Voltage reactive power curve reactive power setting Q3(- 100%~100%) |  |
| 250 | VV Q4 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Voltage reactive power curve reactive power setting Q4(- 100%~100%) |  |
| 251 | VV LockIn(LIV) | RW | U16 | % | ÷10 |  | [0, 1000] | Start reactive power regulation power (0%~100%) |  |
| 252 | VV LockOut(LOV) | RW | U16 | % | ÷10 |  | [0, 1000] | Exit reactive power regulation power (0%~100%) |  |
| 254 | VV Vref | RW | U16 | % | ÷10 |  | [0, 1000] | Voltage regulation reference value (0%~100%) |  |
| 255 | VV VrefTr | RW | U16 | s |  |  | [0,1000] | Voltage regulation response time(0,100s) |  |
| 257 | GCF FuncCode | RW | U16 |  |  |  | [0,65535] | Defined By Bits, Details refer to Appendix 1 | verified |
| 258 | GCF en | RW | U16 |  |  |  | [0,1] | Feeder power limit enabled 0: disable 1: enable | verified |
| 259 | GCF Export Soft Limit Ratio _ | RW | U16 | % | ÷10 |  | [0,1000] | Feeder power soft limit (0%~100%) | verified |
| 260 | GCF Export Hard Limit Ratio _ | RW | U16 | % | ÷10 |  | [0,1000] | Feeder power hard limit (0%~100%) | verified |
| 261 | GCF Export Hard Time | RW | U16 | s | ÷10 |  | [0,1000] | Feeder power protection time(0~100s) |  |
| 262 | GCF Generation Soft Limit Ratio _ | RW | U16 | % | ÷10 |  | [0,1000] | Soft limit value for power generation (0%~100%) |  |
| 263 | GCF Generation Hard Limit Ratio _ | RW | U16 | % | ÷10 |  | [0,1000] | Hard limit value of power generation (0%~100%) |  |
| 264 | GCF Generation Hard Time | RW | U16 | s | ÷10 |  | [0,1000] | Soft limit value of power generation(0,100s) |  |
| 265 | GCF Reconnection Time | RW | U16 | s | ÷10 |  | [0,1000] | Feeder power Reconnection Time(0,100s) |  |
| 266 | Watt Regulation Priority | RW | U16 |  |  |  | [ 0,1 ] | Active adjustment priority |  |
| 267 | PQ P6 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 268 | PQ P5 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 269 | PQ P4 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 270 | PQ P3 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 271 | PQ P2 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 272 | PQ P1 | RW | I16 | % | ÷10 |  | [0, 1000] | Active power (0~100%) |  |
| 273 | PQ Q6 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 274 | PQ Q5 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 275 | PQ Q4 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 276 | PQ Q3 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 277 | PQ Q2 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 278 | PQ Q1 | RW | I16 | % | ÷10 |  | [- 1000, 1000] | Reactive power (- 100%~100%) |  |
| 279 | APC En | RW | U16 |  |  |  | [0,1] | Active power control enabled 0: disable 1: enable | verified |
| 280 | APC PwrLmt | RW | U16 | % | ÷10 |  | [0,1000] | Active power limit (0,100%) |  |
| 281 | APC Ramp | RW | U16 | % | ÷100 |  | [1, 10000] | (0.01% /S~100%/S) |  |
| 282 | Relay u16NlineRlyTestDis | RW | U16 |  |  |  | [0,1] | N-line relay detection flag prohibited 0: disable 1: enable |  |
| 283 | GCF Import Limit Ratio(import | RW | U16 | % | ÷10 |  | [0,1000] | Power limit for grid power supply(0,100%) Limit Value) | verified |
| 284 | GCF Import Hard Time(import | RW | U16 | s | ÷10 |  | [0,1000] | Protection time(0,100s) MTT) |  |
| 285 | PhaseOrder Inverse Disable | RW | U16 |  |  |  | [0,1] | Phase sequence reverse connection alarm 0: disable 1: enable |  |
| 286 | FixPf Tr | RW | U16 | s | ÷10 |  | [0,1000] | Fixed PF first-order low- pass filter response time constant(0,100s) |  |
| 287 | WPF Tr | RW | U16 | s | ÷10 |  | [0,1000] | Fixed PF first-order low- pass filter response time constant(0,100s) |  |
| 288 | VV Tr | RW | U16 | s | ÷10 |  | [0,1000] | VV first-order low-pass filter response time constant(0,100s) |  |
| 289 | PQ Tr | RW | U16 | s | ÷10 |  | [0,1000] | PQ first-order low-pass filter response time constant(0,100s) |  |
| 290 | Function Code | RW | U16 |  |  |  | [0,65535] | Feeder power limit function |  |
| 291 | RPA P1 | RW | I16 | % | ÷10 |  | [0,1000] | Active power (0~100%) |  |
| 292 | RPA Q1 | RW | I16 | % | ÷10 |  | [- 1000,1000] | Reactive power (- 100%~100%) |  |
| 293 | RPA P2 | RW | I16 | % | ÷10 |  | [0,1000] | Active power (0~100%) |  |
| 294 | RPA Q2 | RW | I16 | % | ÷10 |  | [- 1000,1000] | Reactive power (- 100%~100%) |  |
| 295 | FW Over Fdroop | RW | U16 | % | ÷10 |  | [1,1000] | Droop(*10) |  |
| 296 | FW Under Fdroop | RW | U16 | % | ÷10 |  | [1,1000] | Droop(*10) |  |
| 297 | FW DelayTime | RW | U16 | s | ÷10 |  | [0,1000] | delay time (0~100s) |  |
| 298 | PQ FuncCode | RW | U16 |  |  |  | [0,65535] | Defined By Bits, Details refer to Appendix 1 |  |

## Holding System parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 301 | GridIn.Power.Limitation | RW | U16 | W |  |  | [0,20000] | When Vally |  |
| 302 | Three Phase Unbalance | RW | U16 |  |  | 1 | [0,1] | Three-phase unbalance control enabled, 1 effective Enable Battery Charge/Discharge Protection Parameters on inverter side |  |

## Holding Battery charge/discharge parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 306 | Battery Max Charge Power | RW | U16 | % | ÷10 | 1 | [10,100] | Battery maximum charge power rate |  |
| 307 | Battery Max Discharge | RW | U16 | % | ÷10 | 1 | [10,100] | Battery maximum discharge power rate Power |  |
| 308 | Max SOC | RW | U16 | % |  | 1 | [10,100] | Battery maximum charge SOC | ✅ verified |
| 309 | Min SOC | RW | U16 | % |  | 1 | [10,90] | Battery maximum Discharge SOC | ✅ verified |
| 310 | Replenish Power | RW | U16 | W |  | 1 | [0,2000] | Replenish Power when soc lower than reserved |  |
| 312 | Bat Grid Feed Power When | RW | U16 | % | ÷10 | 1 | [0,100] | Peak battery feed-in power, when peak power, the battery feeds power to the grid Peak |  |
| 313 | Bat Discharge Power When | RW | U16 | % | ÷10 | 1 | [0,100] | Flat battery discharge power, when flat power, the maximum discharge power of the battery Partial Peak |  |
| 314 | Lead-Acid Bat Replenish | RW | U16 | min |  | 1 | [0,65535] | Lead-acid battery replenishment maintenance time Time |  |

## Holding PV parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 316 | MPPT Golable Scan | RW | U16 |  |  |  | [0,1] | Enable |  |

## Holding EPS (backup) parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 322 | Bypass Disable | RW | U16 |  |  | 1 | [0, 1] | 0.Disable 1. Enable |  |
| 323 | EPS Mode | RW | U16 |  |  | 1 | [0, 2] | 0.Disable 1. EPS 2. UPS | verified |
| 324 | PV Island Mode En | RW | U16 |  |  | 1 | [0, 1] | 0.Disable 1. Enable |  |

## Holding Generator parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 359 | Gen Rated Power | RW | U16 | W |  |  | [0,30000] |  |  |
| 360 | High Voltage Limit | RW | U16 | V | ÷10 |  | [0,280] |  |  |
| 361 | Low Voltage Limit | RW | U16 | V | ÷10 |  | [0,180] |  |  |
| 362 | High Frequency Limit | RW | U16 | Hz | ÷100 |  | [0,70] |  |  |
| 363 | Low Frequency Limit | RW | U16 | Hz | ÷100 |  | [0,59] |  |  |
| 364 | Maximum Charging Power | RW | U16 | W |  |  | [0,20000] |  |  |

## Holding Professional configuration

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 1008 | Bms485 Com Set | RW | U16 |  |  | 0 | [0, 1] | 0: Bms 1: Dtu |  |
| 1013 | Bms Force Soc Limit | RW | U16 | % |  |  | [0, 100] |  |  |
| 1014 | PCS Mode | RW | U16 |  |  |  | [0, 3] | 0: No restriction; 1: Output only; 2: Input only; 3: No exchange; Instruction dependency parameter |  |

## Holding Inverter commands

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 3000 | Bat Activate | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3001 | Start/Stop System | RW | U16 |  |  | 1 | [0, 1] | 0.Stop System, 1.Start System |  |
| 3002 | Restart System | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3003 | Restore Default | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3004 | Clear Fault | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3006 | Self Test | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3009 | Arc Fault Clear | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3010 | System self-test | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3011 | Battery balancing | RW | U16 |  |  | 1 | [0, 1] | 1. Effective |  |
| 3016 | Parallel networking | RW | U16 |  |  |  |  | 0: invalid,1: networking,2: disassemble |  |
| 3017 | Meter Configuration | RW | U16 |  |  |  |  | 0: No meter (Change the meter type to no meter, delete the meter) 1: Configure grid meter (Trigger meter addressing and modify meter address) Addresses 3018 to 3499 are reserved Battery dependency parameter |  |

## Holding Battery configuration

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4100 | Battery type | RW | U16 |  |  | 0 |  | 0-No-1-Lithium battery, 2-Lead storage |  |
| 4101 | BMS Type | RW | U16 |  |  | 0 |  | Prototype of bms 1: Pylon LV 2: Pylon HV 3: Dyness HV 4: Dyness LV 5: Sunwoda LV 6: Uz LV 7: Soluna HV 8: Soluna LV 9: Steltec LV 10: XinYi LV 11: Vestwoods LV 12: JK HV 13: BYD LV 14: Uz HV 15: Zetara LV 16: FEB HV 17: Pytes LV 18: Dmegc LV 19: Weineng LV 20: Weineng HV 21: GSL LV 22: HOY LV 23: HOY HV 24: FEB LV 25: UHhome LV 26: UHhome HV 27: BYD HV 28: Vestwoods HV 29: Phylion HV 30: Hoymiles LV 31: Pholion LV 32: Wattsonic LV 33: Enershare HV 34: Beghelli LV 35: LvToPSUN LV 36: PYTES HV 37: LvToPSUN HV 38: RAJA HV 39: Felicity LV |  |
| 4102 | Battery Capacity | RW | U16 | Ah | ÷10 | 50 |  | Battery capacity |  |
| 4103 | Max Charge Current | RW | U16 | A | ÷10 | 200 |  | Maximum charging current |  |
| 4104 | Max Discharge Current | RW | U16 | A | ÷10 | 600 |  | Maximum discharge current |  |
| 4105 | Float Voltage | RW | U16 | V | ÷10 | 540 |  | Float charge voltage |  |
| 4106 | Absorption Voltage | RW | U16 | V | ÷10 | 564 |  | CV voltage |  |
| 4107 | End Of Charge Current | RW | U16 | A | ÷10 | 20 |  | Charge cut-off current |  |
| 4108 | Equalization Voltage | RW | U16 | V | ÷10 | 584 |  | Equalize the charge voltage |  |
| 4109 | Equalization Interval Days | RW | U16 | d |  | 3000 |  | Equalize the charging interval |  |
| 4110 | Equalization Time | RW | U16 | min |  | 6 |  | Equalize the charging time |  |
| 4113 | Temperature Correction Factor | RW | U16 | mV/ °C /cell |  | 3 |  | Temperature correction factor |  |
| 4114 | Initial Resistance | RW | U16 | mΩ |  | 0 |  |  |  |
| 4115 | CfgMultPcsBMSFlag | RW | U16 |  |  | 0 |  | 0.Disable 1. Enable |  |
| 4117 | EndChargeVoltage | RW | U16 | V | ÷10 | 650 |  | Cut-off charge voltage |  |
| 4118 | Equilization ChargeTimeOut | RW | U16 | min |  | 0 |  | Equalize charging delay time |  |
| 4119 | Equalization Enable | RW | U16 |  |  | 0 | [0, 1] | 0.Disable 1. Enable Dry contact settings parameter |  |

## Holding Dry contact, load control and generator

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4201 | Dry Working Mode | RW | U16 |  |  | 0 |  | 0.None 1. Earth fault 2. Load control 3. Generator |  |
| 4202 | Load Control Mode | RW | U16 |  |  | 2 |  | 1. Manual 2. Time mode 3. Smart load 4. Off-grid smart load 5. EV chrager |  |
| 4203 | Manual Mode Switch | RW | U16 |  |  | 0 |  | 0.Off 1.On |  |
| 4204 | Day of the week range 1 | RW | U16 |  |  | 0x1F |  | Day of the week range 1 Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4205 | Timer 1 - hour | RW | U16 |  |  | 0 |  | Timer 1 - hour |  |
| 4206 | Timed 1 from 1 min | RW | U16 |  |  | 0 |  | Timed 1 from 1 min |  |
| 4207 | Timed 1 end-hour | RW | U16 |  |  | 23 |  | Timed 1 end-hour |  |
| 4208 | Timed 1 end-minute | RW | U16 |  |  | 0 |  | Timed 1 end-minute |  |
| 4209 | Timer 2 - hour | RW | U16 |  |  | 0 |  | Timer 2 - hour |  |
| 4210 | Timed from 2 - minutes | RW | U16 |  |  | 0 |  | Timed from 2 - minutes |  |
| 4211 | Timed 2 end-hour | RW | U16 |  |  | 23 |  | Timed 2 end-hour |  |
| 4212 | Timed 2 end-minutes | RW | U16 |  |  | 0 |  | Timed 2 end-minutes |  |
| 4213 | Week range 2 | RW | U16 |  |  | 0x60 |  | Week range 2 Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4214 | Timer 1 - hour | RW | U16 |  |  | 0 |  | Timer 1 - hour |  |
| 4215 | Timed 1 from 1 min | RW | U16 |  |  | 0 |  | Timed 1 from 1 min |  |
| 4216 | Timed 1 end-hour | RW | U16 |  |  | 23 |  | Timed 1 end-hour |  |
| 4217 | Timed 1 end-minute | RW | U16 |  |  | 0 |  | Timed 1 end-minute |  |
| 4218 | Timer 2 - hour | RW | U16 |  |  | 0 |  | Timer 2 - hour |  |
| 4219 | Timed from 2 - minutes | RW | U16 |  |  | 0 |  | Timed from 2 - minutes |  |
| 4220 | Timed 2 end-hour | RW | U16 |  |  | 23 |  | Timed 2 end-hour |  |
| 4221 | Timed 2 end-minutes | RW | U16 |  |  | 0 |  | Timed 2 end-minutes |  |
| 4222 | Day of the week range 1 | RW | U16 |  |  | 0x1F |  | Day of the week range 1 Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4223 | Timed from - time | RW | U16 |  |  | 0 |  | Timed from - time |  |
| 4224 | Timed from - minutes | RW | U16 |  |  | 0 |  | Timed from - minutes |  |
| 4225 | Timed end-time | RW | U16 |  |  | 23 |  | Timed end-time |  |
| 4226 | Timed end-minute | RW | U16 |  |  | 0 |  | Timed end-minute |  |
| 4227 | Week range 2 | RW | U16 |  |  | 0x60 |  | Week range 2 Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4228 | Timed from - time | RW | U16 |  |  | 0 |  | Timed from - time |  |
| 4229 | Timed from - minutes | RW | U16 |  |  | 0 |  | Timed from - minutes |  |
| 4230 | Timed end-time | RW | U16 |  |  | 23 |  | Timed end-time |  |
| 4231 | Timed end-minute | RW | U16 |  |  | 0 |  | Timed end-minute |  |
| 4232 | Minimum on-time | RW | U16 | min |  | 30 | [10, 1440] | Minimum on-time |  |
| 4233 | Minimum on-load power | RW | U16 | kw |  | 0 |  | Minimum on-load power |  |
| 4235 | Off-grid protection SOC | RW | U16 | % |  | 1 |  | Off-grid smart load protection SOC |  |
| 4238 | Generator Mode | RW | U16 |  |  | 1 |  | 0:off 1:Manual 2:Auto |  |
| 4239 | Generator Open battery capacity | RW | U16 | V |  | 30 |  | battery capacity when generator turns on |  |
| 4240 | Generator Close battery capacity | RW | U16 | %/V |  | 90 |  | battery capacity when generator turns off |  |
| 4241 | Charge Time Start -H | RW | U16 |  |  | 0 |  | Charging time from -hour |  |
| 4242 | Charge Time Start -Min | RW | U16 |  | ÷0 |  |  | Charging time starts at - minutes |  |
| 4243 | Charge Time End -H | RW | U16 |  | ÷23 |  |  | Charging time end-hour |  |
| 4244 | Charge Time End - Min | RW | U16 |  |  |  |  | Charging time end-minute |  |
| 4245 | Quiet Time Enable | RW | U16 |  |  |  |  | Quiet Time1 is enabled |  |
| 4246 | Quiet Time1 Start -H | RW | U16 |  |  | 0 |  | Quiet Time1 |  |
| 4247 | Quiet Time1 Start -Min | RW | U16 |  | ÷0 |  |  | Quiet Time1 from - min |  |
| 4248 | Quiet Time1 End-H | RW | U16 |  | ÷7 |  |  | Quiet Time1 |  |
| 4249 | Quiet Time1 End -Min | RW | U16 |  | ÷0 |  |  | Quiet Time2 Final-Minute |  |
| 4250 | Quiet Time2 Start -H | RW | U16 |  |  | 0 |  | Quiet Time2 |  |
| 4251 | Quiet Time2 Start -Min | RW | U16 |  | ÷0 |  |  | Quiet Time2 from - min |  |
| 4252 | Quiet Time2 End-H | RW | U16 |  | ÷23 |  |  | Quiet2 Time |  |
| 4253 | Quiet Time2 End -Min | RW | U16 |  | ÷0 |  |  | Quiet Time2 Final-Minute |  |
| 4254 | Gen Practice Mode En | RW | U16 |  |  | 0 |  | 0:Disable,1:Enable |  |
| 4255 | Gen Practice Freq | RW | U16 |  |  | 0 |  | 0: none 1: once a week 2: once every two weeks 3: once every three weeks 4: once every four weeks |  |
| 4256 | Gen Practice Mode Week | RW | U16 |  |  | 0 |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4257 | Gen Practice Mode Start - H | RW | U16 | h |  | 0 |  |  |  |
| 4258 | Gen Practice Mode Start - Min | RW | U16 | min |  | 0 |  |  |  |
| 4259 | Gen Practice Mode - Running Time | RW | U16 | min |  | 10 | [10,1440] |  |  |

## Holding EMS parameters

4309-4338 describe economic mode date segment 1. Segments 2-4 repeat the same layout at 4343-4372, 4377-4406 and 4411-4440.

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4300 | Ems Mode | RW | U16 |  |  | 0 |  | 0: Self-Use 1: Economical Mode 2: Backup Mode 3: Pure Off-Grid Mode 4: Force Charge Mode 5: Force Discharge Mode 6: Peak-shaving Mode 7: TOU Mode | ✅ verified |
| 4301 | Self-Used SOC | RW | U16 | % |  | 30 | [10- 100] | **Above the current SOC the HiOne charges from the grid.** Reserved SOC in self-use mode | ✅ verified |
| 4302 | Back-up SOC | RW | U16 | % |  | 90 | [60- 100] | Reserved SOC in back-up mode | ✅ verified |
| 4303 | Force Charge SOC | RW | U16 | % |  | 70 | [10- 100] | Max SOC in force charge mode | ✅ verified |
| 4304 | Maximum Charge Power | RW | U16 | % | ÷10 | 500 |  | Maximum charge power rate | ✅ verified |
| 4305 | Force Disarge SOC | RW | U16 | % |  | 30 |  | Max SOC in force discharge mode | ✅ verified |
| 4306 | Maximum Discharge Power | RW | U16 | % | ÷10 | 500 |  | Maximum discharge power rate | ✅ verified |
| 4307 | Economic Mode SOC | RW | U16 | % |  | 30 |  | Reserved SOC in economic mode | ✅ |
| 4308 | Economy Mode Date | RW | U16 |  |  | 1 | [1-4] | The date segments number of economic mode Number |  |
| 4309 | Section1 Start month | RW | U16 |  |  | 1 |  |  |  |
| 4310 | Section1 Start day | RW | U16 |  |  | 1 |  |  |  |
| 4311 | Section1 stop month | RW | U16 |  |  | 12 |  |  |  |
| 4312 | Section1 stop day | RW | U16 |  |  | 31 |  |  |  |
| 4313 | Section1 Week range 1 | RW | U16 |  |  | 0x1F |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4314 | Section1 Peak start hour | RW | U16 |  |  | 14 |  | From Monday to Friday |  |
| 4315 | Section1 Peak start minute | RW | U16 |  |  | 0 |  | From Monday to Friday |  |
| 4316 | Section1 Peak stop hour | RW | U16 |  |  | 19 |  | From Monday to Friday |  |
| 4317 | Section1 Peak stop minute | RW | U16 |  |  | 59 |  | From Monday to Friday |  |
| 4320 | Section1 Valley start hour | RW | U16 |  |  | 22 |  | From Monday to Friday |  |
| 4321 | Section1 Valley start minute | RW | U16 |  |  | 0 |  | From Monday to Friday |  |
| 4322 | Section1 Valley stop hour | RW | U16 |  |  | 6 |  | From Monday to Friday |  |
| 4323 | Section1 Valley stop minute | RW | U16 |  |  | 59 |  | From Monday to Friday |  |
| 4328 | Section1 Week range 2 | RW | U16 |  |  | 0x60 |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4329 | Section1 Peak start hour | RW | U16 |  |  | 14 |  | From Saturday to Sunday |  |
| 4330 | Section1 Peak start minute | RW | U16 |  |  | 0 |  | From Saturday to Sunday |  |
| 4331 | Section1 Peak stop hour | RW | U16 |  |  | 19 |  | From Saturday to Sunday |  |
| 4332 | Section1 Peak stop minute | RW | U16 |  |  | 59 |  | From Saturday to Sunday |  |
| 4335 | Section1 Valley start hour | RW | U16 |  |  | 22 |  | From Saturday to Sunday |  |
| 4336 | Section1 Valley start minute | RW | U16 |  |  | 0 |  | From Saturday to Sunday |  |
| 4337 | Section1 Valley stop hour | RW | U16 |  |  | 6 |  | From Saturday to Sunday |  |
| 4338 | Section1 Valley stop minute | RW | U16 |  |  | 59 |  | From Saturday to Sunday 4343 to 4372 indicates the second segment of the EMS, and the information is the same as that in the first segment 4377 to 4406 indicates the third segment of the EMS, and the information is the same as that in the first segment 4411 to 4440 indicates the fouth segment of the EMS, and the information is the same as that in the first segment |  |
| 4445 | Batter Healing | RW | U16 |  |  | 0 |  |  |  |
| 4446 | Peak Meter SOC | RW | U16 | % |  | 20 | [10,100] |  |  |
| 4447 | Peak Meter Power | RW | U16 | W |  | 2000 |  | - TOU parameter |  |

## Holding Time of use (TOU)

4449-4460 describe TOU segment 1. Segments 2-8 repeat the same 12-register layout at 4461, 4473, 4485, 4497, 4509, 4521 and 4533.

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4448 | Time Of Use Range | RW | U16 | 1 |  | 1 | [1,8] | TOU supports eight segments |  |
| 4449 | Time Of Use Time1 Chrg Start | RW | U16 |  |  | 5 |  | TOU mode First charge start - hour - H |  |
| 4450 | Time Of Use Time1 Chrg Start | RW | U16 |  |  | 6 |  | TOU mode First charge start - minute - Min |  |
| 4451 | Time Of Use Time1 Chrg End - | RW | U16 |  |  | 9 |  | TOU mode First charge end - hour H |  |
| 4452 | Time Of Use Time1 Chrg End - | RW | U16 |  |  | 10 |  | TOU mode First charge end - minute Min |  |
| 4453 | Time Of Use Time1 Chrg | RW | U16 | % |  | 60 |  | First charging power in TOU mode Power |  |
| 4454 | Time Of Use Time1 Chrg Stop | RW | U16 | % |  | 50 | [10,100] | TOU mode first phase charge cut-off SOC Soc |  |
| 4455 | Time Of Use Time1 Dischrg | RW | U16 |  |  | 14 |  | TOU mode First discharge start - hour Start - H |  |
| 4456 | Time Of Use Time1 Dischrg | RW | U16 |  |  | 30 |  | TOU mode First discharge start - minute Start - Min |  |
| 4457 | Time Of Use Time1 Dischrg | RW | U16 |  |  | 18 |  | TOU mode First discharge end - hour End - H |  |
| 4458 | Time Of Use Time1 Dischrg | RW | U16 |  |  | 30 |  | TOU mode First discharge end - minute End - Min |  |
| 4459 | Time Of Use Time1 Dischrg | RW | U16 | % |  | 80 |  | First discharging power in TOU mode Power |  |
| 4460 | Time Of Use Time1 Dischrg | RW | U16 | % |  | 50 | [10,100] | TOU mode first phase discharge cut-off SOC Stop Soc 4461 to 4472 indicates the second segment of the TOU, and the information is the same as that in the first segment 4473 to 4484 indicates the third segment of TOU, and the information is the same as that in the first segment 4485 to 4496 indicates the fourth segment of TOU, and the information is the same as that in the first segment 4497 to 4508 indicates the fifth segment of TOU, and the information is the same as that in the first segment 4509 to 4520 indicates the sixth segment of TOU, and the information is the same as that in the first segment 4521 to 4532 indicates the seventh segment of TOU, and the information is the same as that in the first segment 4533 to 4544 indicates the eighth segment of TOU, and the information is the same as that in the first segment |  |
| 4545 | TOU Mode Reserved Soc | RW | U16 | % |  |  | [10,100] |  |  |

## Holding Heat pump

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4600 | HP Work Mode | RW | U16 |  |  | 0 |  | 0: NULL 1: DO |  |
| 4601 | HP Start Power | RW | U16 | w |  | 3000 |  | Starting power of heat pump |  |
| 4602 | HP Max Feedback Power | RW | U16 | w |  | 5000 |  | Maximum network feeding power of the heat pump |  |
| 4603 | HP Supply Power | RW | U16 | w |  | 2000 |  | The heat pump takes power |  |
| 4604 | HP Batt Soc Detect Mode | RW | U16 |  |  | 0 |  | SOC Enabling mode for heat pump batteries 0: Disable 1: Enable |  |
| 4605 | HP Delay Detect Time Lmt | RW | U16 | s |  | 30 |  | Delay detection threshold of heat pump |  |
| 4606 | HP Max Time Detect Enable | RW | U16 |  |  | 0 |  | Max Time Detect Enable of heat pump |  |
| 4607 | HP Min Run Time Lmt Of | RW | U16 | min |  | 360 |  | Minimum run time limit Once |  |
| 4608 | HP Max Run Time Of One | RW | U16 | min |  | 90 |  | The maximum running time limit in a single day Day |  |
| 4609 | HP Start Soc | RW | U16 | % |  | 90 |  | Heat pump start soc |  |
| 4610 | HP Close Soc | RW | U16 | % |  | 70 |  | Heat pump close soc |  |
| 4611 | HP Work Time Parts | RW | U16 |  |  | 1 | [1,4] | Number of working hours supported by the heat pump |  |
| 4612 | HP Time1 Start - Month | RW | U16 |  |  | 1 |  |  |  |
| 4613 | HP Time1 Start - Day | RW | U16 |  |  | 1 |  |  |  |
| 4614 | HP Time1 End- Month | RW | U16 |  |  | 3 |  |  |  |
| 4615 | HP Time1 End - Day | RW | U16 |  |  | 30 |  |  |  |
| 4616 | HP Time1 Week Range | RW | U16 |  |  | 0x7F |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4617 | HP Time2 Start - Month | RW | U16 |  |  | 4 |  |  |  |
| 4618 | HP Time2 Start - Day | RW | U16 |  |  | 1 |  |  |  |
| 4619 | HP Time2 End- Month | RW | U16 |  |  | 6 |  |  |  |
| 4620 | HP Time2 End - Day | RW | U16 |  |  | 30 |  |  |  |
| 4621 | HP Time2 Week Range | RW | U16 |  |  | 0x7F |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4622 | HP Time3 Start - Month | RW | U16 |  |  | 7 |  |  |  |
| 4623 | HP Time3 Start - Day | RW | U16 |  |  | 1 |  |  |  |
| 4624 | HP Time3 End- Month | RW | U16 |  |  | 9 |  |  |  |
| 4625 | HP Time3 End - Day | RW | U16 |  |  | 30 |  |  |  |
| 4626 | HP Time3 Week Range | RW | U16 |  |  | 0x7F |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |
| 4627 | HP Time4 Start - Month | RW | U16 |  |  | 10 |  |  |  |
| 4628 | HP Time4 Start - Day | RW | U16 |  |  | 1 |  |  |  |
| 4629 | HP Time4 End- Month | RW | U16 |  |  | 12 |  |  |  |
| 4630 | HP Time4 End - Day | RW | U16 |  |  | 30 |  |  |  |
| 4631 | HP Time4 Week Range | RW | U16 |  |  | 0x7F |  | Defined by bits, 1 enables 0 to be turned off, interlocking with range 1 bit0: Monday bit1: Tuesday bit2: Wednesday bit3: Thursday bit4 :Friday bit5: Saturday bit6: Sunday |  |

## Holding EV chargers

4750-4773 repeat the same layout for charger 2.

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 4700 | EV charger 1 max charge power limit | RW | U16 | kW | ÷10 | 70 |  | Maximum charging power limit |  |
| 4701 | EV charger 1 offline charge power limit | RW | U16 | W | ÷10 | 50 |  | Offline charging power limit |  |
| 4702 | EV charger 1 start mode | RW | U16 |  |  | 2 |  | 1: plug and charge, 2: RFID authentication |  |
| 4703 | EV charger 1 green mode enable | RW | U16 |  |  | 0 |  | 0: disable, 1: enable |  |
| 4704 | EV charger 1 green mode max power from grid | RW | U16 | kW | ÷10 | 50 |  | Maximum power taken from the grid in green mode |  |
| 4705 | EV charger 1 appointment 1 enable | RW | U16 |  |  | 0 |  | 0: disable, 1: enable |  |
| 4706 | EV charger 1 appointment 1 week range | RW | U16 |  |  | 0 |  | Bit mask, bit0 = Monday ... bit6 = Sunday |  |
| 4707 | EV charger 1 appointment 1 start time 0 | RW | U16 |  |  |  |  |  |  |
| 4708 | EV charger 1 appointment 1 end time 0 | RW | U16 |  |  |  |  |  |  |
| 4709 | EV charger 1 appointment 1 start time 1 | RW | U16 |  |  |  |  |  |  |
| 4710 | EV charger 1 appointment 1 end time 1 | RW | U16 |  |  |  |  |  |  |
| 4711 | EV charger 1 appointment 1 start time 2 | RW | U16 |  |  |  |  |  |  |
| 4712 | EV charger 1 appointment 1 end time 2 | RW | U16 |  |  |  |  |  |  |
| 4713 | EV charger 1 appointment 1 start time 3 | RW | U16 |  |  |  |  |  |  |
| 4714 | EV charger 1 appointment 1 end time 3 | RW | U16 |  |  |  |  |  |  |
| 4715 | EV charger 1 appointment 2 week range | RW | U16 |  |  |  |  | Bit mask, bit0 = Monday ... bit6 = Sunday |  |
| 4716 | EV charger 1 appointment 2 start time 0 | RW | U16 |  |  |  |  |  |  |
| 4717 | EV charger 1 appointment 2 end time 0 | RW | U16 |  |  |  |  |  |  |
| 4718 | EV charger 1 appointment 2 start time 1 | RW | U16 |  |  |  |  |  |  |
| 4719 | EV charger 1 appointment 2 end time 1 | RW | U16 |  |  |  |  |  |  |
| 4720 | EV charger 1 appointment 2 start time 2 | RW | U16 |  |  |  |  |  |  |
| 4721 | EV charger 1 appointment 2 end time 2 | RW | U16 |  |  |  |  |  |  |
| 4722 | EV charger 1 appointment 2 start time 3 | RW | U16 |  |  |  |  |  |  |
| 4723 | EV charger 1 appointment 2 end time 3 | RW | U16 |  |  |  |  |  |  |

## Holding Gateway

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 5000 | Gateway communication address | RW | U16 |  |  | 200 |  |  |  |
| 5001 | Board ambient temperature threshold | RW | U16 | °C | ÷10 |  |  |  |  |
| 5002 | Ambient temperature threshold | RW | U16 | °C | ÷10 |  |  |  |  |
| 5003 | ESS access point | RW | U16 |  |  |  |  |  |  |
| 5004 | PV connection status | RW | U16 |  |  |  |  |  |  |
| 5005 | Generator connection status | RW | U16 |  |  |  |  |  |  |
| 5006 | Service entrance breaker current | RW | U16 | A |  |  |  |  |  |

## Holding Installation information (parallel systems)

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 6048 | Machines Type | R | U16 |  |  | 0 |  | Machine Type Definition: 0:Single machine 1: Master 2: Slave |  |
| 6049 | Number Of Machines | R | U16 |  |  |  |  | - - (Master and Slave) |  |
| 6050 | Communication Address 1 | R | U16 |  |  |  |  | - (Master Device) |  |
| 6051-6054 | Machine Serial Number (Master Device) | R | U64 |  |  |  |  |  |  |
| 6055 | Communication Address 2 | R | U16 |  |  |  |  | - (Slave Device 1) |  |
| 6056-6059 | Machine Serial Number (Slave Device 1) | R | U64 |  |  |  |  |  |  |
| 6060 | Communication Address 3 | R | U16 |  |  |  |  | - (Slave Device 2) |  |
| 6061-6064 | Machine Serial Number (Slave Device 2) | R | U64 |  |  |  |  |  |  |
| 6065 | Communication Address 4 | R | U16 |  |  |  |  | - (Slave Device 3) |  |
| 6066-6069 | Machine Serial Number (Slave Device 3) | R | U64 |  |  |  |  |  |  |
| 6070 | Communication Address 5 | R | U16 |  |  |  |  | - (Slave Device 4) |  |
| 6071-6074 | Machine Serial Number (Slave Device 4) | R | U64 |  |  |  |  |  |  |
| 6075 | Communication Address 6 | R | U16 |  |  |  |  | - (Slave Device 5) |  |
| 6076-6079 | Machine Serial Number (Slave Device 5) | R | U64 |  |  |  |  |  |  |
| 6080 | Communication Address7 | R | U16 |  |  |  |  | - (Slave Device 6) |  |
| 6081-6084 | Machine Serial Number (Slave Device 6) | R | U64 |  |  |  |  |  |  |
| 6085 | Communication Address8 | R | U16 |  |  |  |  | - (Slave Device 7) |  |
| 6086-6089 | Machine Serial Number (Slave Device 7) | R | U64 |  |  |  |  |  |  |
| 6090 | Communication Address9 | R | U16 |  |  |  |  | - (Slave Device 8) |  |
| 6091-6094 | Machine Serial Number (Slave Device 8) | R | U64 |  |  |  |  |  |  |
| 6095 | Communication Address10 | R | U16 |  |  |  |  | - (Slave Device 9) |  |
| 6096-6099 | Machine Serial Number (Slave Device 9) | R | U64 |  |  |  |  |  |  |

## Holding System common settings

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 6200 | RS485 communication address | RW | U16 |  |  | 1 | [1,247] |  |  |

## Holding Inverter information

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 7000-7015 | Machine Serial Number | R | String |  |  | 1 |  |  | ✅ |
| 7016-7033 | Model Name | R | String |  |  | 1 |  |  | ✅ |
| 7034 | Power Software Version | R | U16 |  |  |  |  | The version number is 100, which means V0.01.00 | ✅ |
| 7035 | Safety Software Version | R | U16 |  |  |  |  | The version number is 100, which means V0.01.00 | ✅ |
| 7036 | System Software Version | R | U16 |  |  |  |  | The version number is 100, which means V0.01.00 | ✅ |
| 7037 | Machine Hardware | R | U16 |  |  | 1 |  | The version number is 100, which means H0.01.00 Version Addresses 7054 to 7999 are reserved | ✅ |

## Holding Battery system information

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 8000 | Brand | R | U16 |  |  |  |  |  |  |
| 8001 | Number of battery clusters | R | U16 |  |  |  |  |  |  |
| 8002 | Number of battery packs (cluster 1) | R | U16 |  |  |  |  |  |  |
| 8003 | Number of battery packs (cluster 2) | R | U16 |  |  |  |  |  |  |
| 8004 | Reporting flag | R | U16 |  |  |  |  |  |  |

## Holding Battery pack information

8100-8149 describe pack 1. Packs 2-16 repeat the same 50-register layout (8150, 8200, ...).

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 8100-8115 | Machine SN | R | String |  |  |  |  |  |  |
| 8116-8119 | Board SN | R | U64 |  |  |  |  |  |  |
| 8120 | DcDc Software Version | R | U16 |  |  |  |  |  |  |
| 8121 | DcDc Hardware Version | R | U16 |  |  |  |  |  |  |
| 8122-8123 | BMS Software Version | R | U32 |  |  |  |  |  |  |
| 8126-8127 | Rated Capacity | R | U32 |  |  |  |  |  |  |

## Holding DTU parameters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 62000 | Networking Status | RW | U16 |  |  | 0 |  | 0: Invalid 1: Networking |  |
| 62001-62006 | Serial Number1 Setting | RW | String |  |  |  |  |  |  |
| 62007-62012 | Serial Number2 Setting | RW | String |  |  |  |  |  |  |
| 62013-62018 | Serial Number3 Setting | RW | String |  |  |  |  |  |  |
| 62019-62024 | Serial Number4 Setting | RW | String |  |  |  |  |  |  |
| 62025-62030 | Serial Number5 Setting | RW | String |  |  |  |  |  |  |
| 62100 | Command Send Status | R | U16 |  |  | 0 |  | 0: Invalid 1:Start 2: in progress 3: Success 4: Failed |  |
| 62101 | Number of DTUs Successfully Configured | R | U16 |  |  | 0 | [0,5] |  |  |
| 62102 | DTU Online Status | R | U16 |  |  | 0 |  | bit0:0 means DTU1 offline,1 means DTU1 online bit1: 0 means DTU2 offline,1 means DTU2 online bit2: 0 means DTU3 offline,1 means DTU3 online bit3: 0 means DTU4 offline,1 means DTU4 online bit4: 0 means DTU5 offline,1 means DTU5 online |  |

# Input registers


## Input System (inverter)

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 0 | WorkStatus | RO | U16 |  |  |  |  | System working status 0: PowerInit 1: StdbyMode 2: GridOnTest 3: GridOnMode 4: FaultMode 5: GridOffMode 6: ByPassMode | ✅ verified |
| 1 | Power DSP FM Version | RO | U16 |  |  |  |  | Power DSP firmware version |  |
| 19 | SW Fault | RO | U32 |  |  |  |  | Software fault code | ✅ |
| 21 | HW Fault | RO | U32 |  |  |  |  | Hardware fault code | ✅ |
| 26 | PV Total Power | RO | U16 | W |  |  |  | PV total power | ✅ |
| 27 | PV1 Voltage | RO | U16 | V | ÷10 |  |  | PV1 voltage | ✅ |
| 28 | PV1 Current | RO | I16 | A | ÷100 |  |  | PV1 current | ✅ |
| 29 | PV1 Power | RO | U16 | W |  |  |  | PV1 power | ✅ |
| 30 | PV2 Voltage | RO | U16 | V | ÷10 |  |  | PV2 voltage | ✅ |
| 31 | PV2 Current | RO | I16 | A | ÷100 |  |  | PV2 current | ✅ |
| 32 | PV2 Power | RO | U16 | W |  |  |  | PV2 power | ✅ |
| 33 | PV3 Voltage | RO | U16 | V | ÷10 |  |  | PV3 voltage | ✅ |
| 34 | PV3 Current | RO | I16 | A | ÷100 |  |  | PV3 current | ✅ |
| 35 | PV3 Power | RO | U16 | W |  |  |  | PV3 power | ✅ |
| 36 | PV4 Voltage | RO | U16 | V | ÷10 |  |  | PV4 voltage | ✅ |
| 37 | PV4 Current | RO | I16 | A | ÷100 |  |  | PV4 current | ✅ |
| 38 | PV4 Power | RO | U16 | W |  |  |  | PV4 power | ✅ |
| 45 | Bat Total Power | RO | I16 | W |  |  |  | Battery total power |  |
| 46 | Bat1 Voltage | RO | U16 | V | ÷10 |  |  | Battery voltage |  |
| 48 | Bat1 Current | RO | I16 | A | ÷100 |  |  | The current expansion bit fits the G1/G2 model |  |
| 50 | Bat1 Power | RO | I32 | W |  |  |  | **HiOne: positive = discharging, negative = charging.** The current expansion bit fits the G3 model | ✅ verified |
| 51 | Bat1 Power | RO | I16 | W |  |  |  | The current expansion bit fits the G1/G2 model | ✅ |
| 58 | Positive Bus Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 59 | Negative Bus Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 60 | Bus Voltage | RO | U16 | V | ÷10 |  |  | DC bus voltage | ✅ |
| 62 | Grid Voltage A | RO | U16 | V | ÷10 |  |  | Phase AN of grid voltage | ✅ |
| 63 | Grid Voltage B | RO | U16 | V | ÷10 |  |  | Phase BN of grid voltage | ✅ |
| 64 | Grid Voltage C | RO | U16 | V | ÷10 |  |  | Phase CN of grid voltage | ✅ |
| 66 | Grid Frequency | RO | U16 | Hz | ÷100 |  |  | Grid frequency | ✅ |
| 67 | Inv Voltage A | RO | U16 | V | ÷10 |  |  | Phase AN of inverter side voltage |  |
| 68 | Inv Voltage B | RO | U16 | V | ÷10 |  |  | Phase BN of inverter side voltage |  |
| 69 | Inv Voltage C | RO | U16 | V | ÷10 |  |  | Phase CN of inverter side voltage |  |
| 70 | Inv Current A | RO | I16 | A | ÷100 |  |  | Phase AN of inverter side current |  |
| 71 | Inv Current B | RO | I16 | A | ÷100 |  |  | Phase BN of inverter side current |  |
| 72 | Inv Current C | RO | I16 | A | ÷100 |  |  | Phase CN of inverter side current |  |
| 73 | Inv Active Power | RO | I16 | W |  |  |  | Inverter combined active power | ✅ |
| 74 | Inv Active Power A | RO | I16 | W |  |  |  | Phase AN of inverter active power |  |
| 75 | Inv Active Power B | RO | I16 | W |  |  |  | Phase BN of inverter active power |  |
| 76 | Inv Active Power C | RO | I16 | W |  |  |  | Phase CN of inverter active power |  |
| 77 | Inv Reactive Power | RO | I16 | Var |  |  |  | Inverter combined reactive power |  |
| 78 | Inv Reactive Power A | RO | I16 | Var |  |  |  | Phase AN of inverter reactive power |  |
| 79 | Inv Reactive Power B | RO | I16 | Var |  |  |  | Phase BN of inverter reactive power |  |
| 80 | Inv Reactive Power C | RO | I16 | Var |  |  |  | Phase CN of inverter reactive power |  |
| 81 | Backup Voltage A | RO | U16 | V | ÷10 |  |  | Phase AN of backup port voltage |  |
| 82 | Backup Voltage B | RO | U16 | V | ÷10 |  |  | Phase BN of backup port voltage |  |
| 83 | Backup Voltage C | RO | U16 | V | ÷10 |  |  | Phase CN of backup port voltage |  |
| 84 | Backup Current A | RO | I16 | A | ÷100 |  |  | Phase AN of backup port current |  |
| 85 | Backup Current B | RO | I16 | A | ÷100 |  |  | Phase BN of backup port current |  |
| 86 | Backup Current C | RO | I16 | A | ÷100 |  |  | Phase CN of backup port current |  |
| 87 | Backup Apparent Power | RO | I16 | VA |  |  |  | Backup port combined apparent power |  |
| 88 | Backup Apparent Power A | RO | I16 | VA |  |  |  | Phase AN of backup port apparent power |  |
| 89 | Backup Apparent Power B | RO | I16 | VA |  |  |  | Phase BN of backup port apparent power |  |
| 90 | Backup Apparent Power C | RO | I16 | VA |  |  |  | Phase CN of backup port apparent power |  |
| 91 | Backup Active Power | RO | I16 | W |  |  |  | Backup port combined active power | ✅ |
| 92 | Backup Active Power A | RO | I16 | W |  |  |  | Phase AN of backup port active power |  |
| 93 | Backup Active Power B | RO | I16 | W |  |  |  | Phase BN of backup port active power |  |
| 94 | Backup Active Power C | RO | I16 | W |  |  |  | Phase CN of backup port active power |  |
| 103 | Gen Voltage A | RO | U16 | V | ÷10 |  |  | Phase AN of generator port voltage |  |
| 104 | Gen Voltage B | RO | U16 | V | ÷10 |  |  | Phase BN of generator port voltage |  |
| 105 | Gen Voltage C | RO | U16 | V | ÷10 |  |  | Phase CN of generator port voltage |  |
| 106 | Gen Current A | RO | I16 | A | ÷100 |  |  | Phase AN of generator port current |  |
| 107 | Gen Current B | RO | I16 | A | ÷100 |  |  | Phase BN of generator port current |  |
| 108 | Gen Current C | RO | I16 | A | ÷100 |  |  | Phase CN of generator port current |  |
| 109 | Gen Active Power A | RO | I16 | W |  |  |  | Phase AN of generator port active power |  |
| 110 | Gen Active Power B | RO | I16 | W |  |  |  | Phase BN of generator port active power |  |
| 111 | Gen Active Power C | RO | I16 | W |  |  |  | Phase CN of generator port active power |  |
| 112 | Pv Ths Temp | RO | I16 | °C |  |  |  | PV side radiator temperature | ✅ |
| 113 | Inv Ths Temp | RO | I16 | °C |  |  |  | Inverter side radiator temperature | ✅ verified |
| 114 | Bat Ths Temp | RO | I16 | °C |  |  |  | Battery-side radiator temperature | ✅ |
| 115 | Cav Temp | RO | I16 | °C |  |  |  | Ambient temperature | ✅ |
| 116 | 12V Aux supply | RO | U16 | V | ÷100 |  |  | 12V auxiliary power |  |
| 117 | 5V Aux supply | RO | U16 | V | ÷100 |  |  | 5V auxiliary power |  |
| 118 | 3.3V Aux supply | RO | U16 | V | ÷100 |  |  | 3.3V auxiliary power |  |
| 119 | 1.5V Aux supply | RO | U16 | V | ÷100 |  |  | 1.5V auxiliary power |  |
| 120 | Relay Aux supply | RO | U16 | V | ÷100 |  |  | Relay supply voltage |  |
| 121 | Fan Speed | RO | U16 | r/min |  |  |  | Internal fan speed |  |
| 122 | Fan Speed | RO | U16 | r/min |  |  |  | Internal fan speed |  |
| 123 | Fan Speed | RO | U16 | r/min |  |  |  | Internal fan speed |  |
| 125 | DC inject Current A | RO | I16 | mA |  |  |  | Phase AN of grid direct inject current |  |
| 126 | DC inject Current B | RO | I16 | mA |  |  |  | Phase BN of grid direct inject current |  |
| 127 | DC inject Current C | RO | I16 | mA |  |  |  | Phase CN of grid direct inject current |  |
| 153 | Fan Speed | RO | U16 | r/min |  |  |  | External fan speed |  |
| 154 | Fan Speed | RO | U16 | r/min |  |  |  | External fan speed |  |
| 155 | Fan Speed | RO | U16 | r/min |  |  |  | External fan speed |  |
| 156 | Fan Speed | RO | U16 | r/min |  |  |  | External fan speed |  |
| 201 | Safety DSP FM Version | RO | U16 |  |  |  |  | Safety DSP firmware Version number |  |
| 210 | ReConnect Counter | RO | U16 | s |  |  |  | Grid Reconnect counter |  |
| 214 | Bus balance Current | RO | I16 | A | ÷100 |  |  | Busbar balance bridge current |  |
| 241 | PE Voltage | RO | I16 | V | ÷10 |  |  | PE voltage |  |
| 242 | Iso Resistor | RO | U16 | kΩ |  |  |  | Insulation resistance |  |
| 243 | Residual Current | RO | I16 | mA |  |  |  | Leakage current |  |
| 284 | Load Active Power | RO | I32 | W |  |  |  | Load Active Power | ✅ verified |

## Input Meters

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 1800 | Meter Link Status | RO | U16 |  |  | 0 |  | 0: Offline 1: Online 3: HMID Connection Normal 4: HMID Connection Failure | ✅ |
| 1801 | Grid Voltage An | RO | U16 | V | ÷10 |  |  |  | ✅ |
| 1802 | Grid Voltage Bn | RO | U16 | V | ÷10 |  |  |  | ✅ |
| 1803 | Grid Voltage Cn | RO | U16 | V | ÷10 |  |  |  | ✅ |
| 1804 | Grid Current An | RO | I16 | A | ÷100 |  |  |  | ✅ |
| 1805 | Grid Current Bn | RO | I16 | A | ÷100 |  |  |  | ✅ |
| 1806 | Grid Current Cn | RO | I16 | A | ÷100 |  |  |  | ✅ |
| 1807 | Grid Frequency | RO | U16 | Hz | ÷100 |  |  |  | ✅ |
| 1808 | Grid Active Power An | RO | I32 | W |  |  |  |  | ✅ verified |
| 1810 | Grid Active Power Bn | RO | I32 | W |  |  |  |  | ✅ verified |
| 1812 | Grid Active Power Cn | RO | I32 | W |  |  |  |  | ✅ verified |
| 1814 | Grid Total Active Power | RO | I32 | W |  |  |  | **HiOne: negative = import from the grid.** | ✅ verified |
| 1816 | Grid Reactive Power An | RO | I32 | var |  |  |  |  |  |
| 1818 | Grid Reactive Power Bn | RO | I32 | var |  |  |  |  |  |
| 1820 | Grid Reactive Power Cn | RO | I32 | var |  |  |  |  |  |
| 1822 | Grid Total Reactive Power | RO | I32 | var |  |  |  |  |  |
| 1824 | Grid Power Factor | RO | I16 |  |  |  |  |  |  |
| 1825 | Grid Power Factor An | RO | I16 |  |  |  |  |  |  |
| 1826 | Grid Power Factor Bn | RO | I16 |  |  |  |  |  |  |
| 1827 | Grid Power Factor Cn | RO | I16 |  |  |  |  |  |  |
| 1850 | PV Link Status | RO | U16 |  |  | 0 |  | 0: Offline 1: Online |  |
| 1851 | PV Voltage An | RO | U16 | V | ÷10 |  |  |  |  |
| 1852 | PV Voltage Bn | RO | U16 | V | ÷10 |  |  |  |  |
| 1853 | PV Voltage Cn | RO | U16 | V | ÷10 |  |  |  |  |
| 1854 | PV Current An | RO | I16 | A | ÷100 |  |  |  |  |
| 1855 | PV Current Bn | RO | I16 | A | ÷100 |  |  |  |  |
| 1856 | PV Current Cn | RO | I16 | A | ÷100 |  |  |  |  |
| 1857 | PV Frequency | RO | U16 | Hz | ÷100 |  |  |  |  |
| 1858 | PV Active Power An | RO | I32 | W |  |  |  |  |  |
| 1860 | PV Active Power Bn | RO | I32 | W |  |  |  |  |  |
| 1862 | PV Active Power Cn | RO | I32 | W |  |  |  |  |  |
| 1864 | PV Total Active Power | RO | I32 | W |  |  |  |  |  |
| 1866 | PV Reactive Power An | RO | I32 | var |  |  |  |  |  |
| 1868 | PV Reactive Power Bn | RO | I32 | var |  |  |  |  |  |
| 1870 | PV Reactive Power Cn | RO | I32 | var |  |  |  |  |  |
| 1872 | PV Total Reactive Power | RO | I32 | var |  |  |  |  |  |
| 1874 | PV Power Factor | RO | I16 |  |  |  |  |  |  |
| 1875 | PV Power Factor An | RO | I16 |  |  |  |  |  |  |
| 1876 | PV Power Factor Bn | RO | I16 |  |  |  |  |  |  |
| 1877 | PV Power Factor Cn | RO | I16 |  |  |  |  |  |  |

## Input Battery cluster

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 1900 | Battery Type | RO | U16 |  |  | 0 |  | 0: No 1: Lithium battery 2: Phosphoric acid battery 3: Simulated battery |  |
| 1901 | Battery Link Status | RO | U16 |  |  | 1 |  | 0: Offline 1: Online | ✅ |
| 1902 | Packs Cfg Number | RO | U16 |  |  |  |  | bitx: "0" - Not configured, "1" - configured |  |
| 1903 | Packs Online Number | RO | U16 |  |  |  |  | bitx: "0" - Offline, "1" - Online |  |
| 1904 | Work Status | RO | U16 |  |  |  |  | 0: Standby 1:Charge 2:Discharge | ✅ verified |
| 1905 | Fault Code | RO | U32 |  |  |  |  |  | ✅ |
| 1907 | Total Capacity | RO | U32 | kWh | ÷10 |  |  |  | ✅ |
| 1909 | Battery Soc | RO | U16 | % |  |  |  |  | ✅ verified |
| 1910 | Battery Soh | RO | U16 | % |  |  |  |  | ✅ verified |
| 1911 | Battery Voltage | RO | U16 | V | ÷10 |  |  |  | ✅ verified |
| 1912 | Battery Current | RO | I32 | A | ÷10 |  |  |  | ✅ |
| 1914 | Battery Power | RO | I32 | W |  |  |  |  |  |
| 1916 | Max Charge Current | RO | U16 | A | ÷10 |  |  |  | ✅ verified |
| 1917 | Max Discharge Current | RO | U16 | A | ÷10 |  |  |  | ✅ |
| 1918 | Charge CutOff Voltage | RO | U16 | V | ÷10 |  |  |  | ✅ |
| 1919 | Discharge CutOff Voltage | RO | U16 | V | ÷10 |  |  |  | ✅ |
| 1920 | Module Max Temperature | RO | I16 | °C |  |  |  |  |  |
| 1921 | Module Min Temperature | RO | I16 | °C |  |  |  |  |  |
| 1922 | Cell Max Temperature | RO | I16 | °C |  |  |  | **HiOne reports 0.1 °C (÷10).** | ✅ verified |
| 1923 | Cell Min Temperature | RO | I16 | °C |  |  |  | **HiOne reports 0.1 °C (÷10).** | ✅ verified |
| 1924 | Module Max Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 1925 | Module Min Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 1926 | Cell Max Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 1927 | Cell Min Voltage | RO | U16 | V | ÷10 |  |  |  |  |

## Input Energy and power flow

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 2000 | PV Total Energy | RO | U32 | kWh | ÷10 |  |  | Cumulative PV power generation | ✅ |
| 2002 | PV1 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV1 power generation |  |
| 2004 | PV2 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV2 power generation |  |
| 2006 | PV3 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV3 power generation |  |
| 2008 | PV4 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV4 power generation |  |
| 2010 | PV5 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV5 power generation |  |
| 2012 | PV6 Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative PV6 power generation |  |
| 2014 | External PV Energy total | RO | U32 | kWh | ÷10 |  |  | Cumulative power generation of external PV |  |
| 2016 | Ext PV Energy An | RO | U32 | kWh | ÷10 |  |  | Cumulative power generation of external Phase A PV |  |
| 2018 | Ext PV Energy Bn | RO | U32 | kWh | ÷10 |  |  | Cumulative power generation of external Phase B PV |  |
| 2020 | Ext PV Energy Cn | RO | U32 | kWh | ÷10 |  |  | Cumulative power generation of external Phase C PV |  |
| 2022 | PvToBat Energy total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2024 | PvToLoad Energy total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2026 | PvToGrid Energy total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2028 | Bat Total Charge Energy | RO | U32 | kWh | ÷10 |  |  |  | ✅ verified |
| 2030 | Bat Total Discharge Energy | RO | U32 | kWh | ÷10 |  |  |  | ✅ verified |
| 2040 | Grid Energy Buy total | RO | U32 | kWh | ÷10 |  |  |  | ✅ |
| 2042 | Grid Energy Buy An total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2044 | Grid Energy Buy Bn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2046 | Grid Energy Buy Cn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2048 | Grid Energy Sell total | RO | U32 | kWh | ÷10 |  |  |  | ✅ |
| 2050 | Grid Energy Sell An total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2052 | Grid Energy Sell Bn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2054 | Grid Energy Sell Cn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2056 | Load Energy Use total | RO | U32 | kWh | ÷10 |  |  |  | ✅ |
| 2058 | Load Energy Use An total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2060 | Load Energy Use Bn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2062 | Load Energy Use Cn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2064 | Energy From PV total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2066 | Energy From Bat total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2068 | Energy From Grid total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2070 | Generator Energy total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2072 | Generator Energy An total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2074 | Generator Energy Bn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2076 | Generator Energy Cn total | RO | U32 | kWh | ÷10 |  |  |  |  |
| 2100 | PV Total Energy Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ |
| 2101 | PV1 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2102 | PV2 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2103 | PV3 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2104 | PV4 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2105 | PV5 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2106 | PV6 Today Energy | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2107 | External PV Todal Energy Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2108 | External PV Today Energy An | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2109 | External PV Today Energy Bn | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2110 | External PV Today Energy Cn | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2111 | PvToBat Energy Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2112 | PvToLoad Energy Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2113 | PvToGrid Energy Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2114 | Bat Charge Energy Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ verified |
| 2115 | Bat Discharge Energy Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ verified |
| 2120 | Grid Energy Buy Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ |
| 2121 | Grid Energy Buy An Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2122 | Grid Energy Buy Bn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2123 | Grid Energy Buy Cn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2124 | Grid Energy Sell Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ |
| 2125 | Grid Energy Sell An Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2126 | Grid Energy Sell Bn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2127 | Grid Energy Sell Cn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2128 | Load Energy Use Today | RO | U16 | kWh | ÷10 |  |  |  | ✅ |
| 2129 | Load Energy Use An Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2130 | Load Energy Use Bn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2131 | Load Energy Use Cn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2132 | Energy From PV Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2133 | Energy From Bat Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2134 | Energy From Grid Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2135 | Generator Energy total Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2136 | Generator Energy An Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2137 | Generator Energy Bn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2138 | Generator Energy Cn Today | RO | U16 | kWh | ÷10 |  |  |  |  |
| 2150 | PV Total Power | RO | U16 | W |  |  |  | PV Total Power (Internal + External) |  |
| 2151 | PV Power | RO | U16 | W |  |  |  | Internal PV Total power |  |
| 2152 | PV1 Power | RO | U16 | W |  |  |  |  |  |
| 2153 | PV2 Power | RO | U16 | W |  |  |  |  |  |
| 2154 | PV3 Power | RO | U16 | W |  |  |  |  |  |
| 2155 | PV4 Power | RO | U16 | W |  |  |  |  |  |
| 2156 | PV5 Power | RO | U16 | W |  |  |  |  |  |
| 2157 | PV6 Power | RO | U16 | W |  |  |  |  |  |
| 2158 | External PV Total Power | RO | U16 | W |  |  |  |  |  |
| 2159 | External PV An Power | RO | U16 | W |  |  |  |  |  |
| 2160 | External PV Bn Power | RO | U16 | W |  |  |  |  |  |
| 2161 | External PV Cn Power | RO | U16 | W |  |  |  |  |  |
| 2162 | Bat Total Power | RO | I16 | W |  |  |  |  |  |
| 2165 | Grid Active Power | RO | I16 | W |  |  |  |  |  |
| 2166 | Grid Active Power An | RO | I16 | W |  |  |  |  |  |
| 2167 | Grid Active Power Bn | RO | I16 | W |  |  |  |  |  |
| 2168 | Grid Active Power Cn | RO | I16 | W |  |  |  |  |  |
| 2169 | Load Power total | RO | U16 | W |  |  |  |  |  |
| 2170 | Load Power An | RO | U16 | W |  |  |  |  |  |
| 2171 | Load Power Bn | RO | U16 | W |  |  |  |  |  |
| 2172 | Load Power Cn | RO | U16 | W |  |  |  |  |  |
| 2173 | Generator Total Power | RO | U16 | W |  |  |  |  |  |
| 2174 | Generator Power An | RO | U16 | W |  |  |  |  |  |
| 2175 | Generator Power Bn | RO | U16 | W |  |  |  |  |  |
| 2176 | Generator Power Cn | RO | U16 | W |  |  |  |  |  |
| 2177 | PvToBat Power | RO | U16 | W |  |  |  |  |  |
| 2178 | PvToLoad Power | RO | U16 | W |  |  |  |  |  |
| 2179 | PvToGrid Power | RO | U16 | W |  |  |  |  |  |
| 2180 | Load From PV Power | RO | U16 | W |  |  |  |  |  |
| 2181 | Load From Bat Power | RO | U16 | W |  |  |  |  |  |
| 2182 | Load From Grid Power | RO | U16 | W |  |  |  |  |  |

## Input EV chargers

3250-3275 repeat the same layout for charger 2.

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 3200 | Ev Charger1 Connet Status | RO | U16 |  |  | 1 |  | 0:offline 1:online |  |
| 3201 | Ev Charger1 CommAddr | RO | U16 |  |  | 0x0A |  | Charging pile communication address |  |
| 3202 | Ev Charger1 Sn | RO | U64 |  |  |  |  | Serial number of charging pile(Hex format) |  |
| 3206 | Ev Charger1 start mode set | RO | U16 |  |  |  |  | Charger start mode get: 1: Plug and charge 2: RFID authentication |  |
| 3207 | Ev Charger1 bill start mode get | RO | U16 |  |  |  |  | Bills start mode get: 1: RS485 2: OCPP 3: Plug and charge |  |
| 3208 | Ev Charger1 bill end mode get | RO | U16 |  |  |  |  | Bills end mode get: 0: Fully charged 1: Swipe card 2: RS485 3: Draw arms 4: OCPP 5: Fault 6: EPO |  |
| 3209 | Ev Charger1 Soft Version | RO | U16 |  |  |  |  | Charging pile software version number |  |
| 3210 | Ev Charger1 Pill type | RO | U16 |  |  |  |  | Charging pile type |  |
| 3211 | Ev Charger1 Min Charge Power | RO | U16 | kW | ÷10 |  |  | Minimum charging power of charging pile |  |
| 3212 | Ev Charger1 pill status | RO | U16 |  |  |  |  | Pill status get: 0: Normal 1: Fault 2: Warning |  |
| 3213 | Ev Charger1 Pill Error Code | RO | U16 |  |  |  |  | Defined by bits, 1 fault, 0 noraml bit0: Ac pile scram button is pressed bit1: Dc pile scram button is pressed bit2: Ground fault bit3: Hatch opening failure bit4: The communication between some power modules is faulty bit5: The communication between all power modules is faulty bit6: Overtemperature fault bit7: Other fault bit8: Other warning bit9: CP fault bit10: Meter fault bit11: Undervoltage fault bit12: Overvoltage fault bit13: Relay bonding fault bit14: Leakage fault bit15: Overcurrent fault |  |
| 3214 | Ev Charger1 Rate Power | RO | U16 |  |  |  |  | Rated power of charging pile |  |
| 3215 | Ev Charger1 Real Output Power | RO | U16 |  |  |  |  | Charging pile real-time output power |  |
| 3216 | Ev Charger1 output percentage set value | RO | U16 |  |  |  |  | Charging pile charging output percentage Set value |  |
| 3217 | Ev Charger1 Offline charge power lmt | RO | U16 |  |  |  |  | Off-line charging power limit of charging pile |  |
| 3218 | Ev Charger1 output power set value | RO | U16 |  |  |  |  | Charging power setting of charging pile |  |
| 3219 | Ev Charger1 Gun Status | RO | U16 |  |  |  |  | Gun status get: bit0~bit7: 0: Direct current gun 1: Single-phase ac gun 2: Three-phase ac gun bit8~bit15: 0: Free and unplugged 1: Idle gun inserted 2: Run charge plugged gun 3: Running discharge plugged gun 4: Stop thrusting the gun 5: Run charge plugged gun 6: Pause 7: Fault |  |
| 3220 | Ev Charger1 Output Voltage | RO | U16 | V | ÷10 |  |  | Charging pile output voltage |  |
| 3221 | Ev Charger1 Output Current | RO | U16 | A | ÷10 |  |  | Charging pile output current |  |
| 3222 | Ev Charger1 Output Power | RO | U16 | kW | ÷10 |  |  | Output power of charging pile |  |
| 3223 | Ev Charger1 Output Time | RO | U16 | min |  |  |  | The charging time of the charging pile |  |
| 3224 | Ev Charger1 Output Cap | RO | U16 | kWh | ÷10 |  |  | The charging amount of the charging pile 3250~3275 input the information for charging pile 2, the information is consistent with the first paragraph |  |

## Input Gateway / HMID

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 5000 | APP Software Version | RO | U16 |  |  |  |  |  |  |
| 5009 | Boot Software Version | RO | U16 |  |  |  |  |  |  |
| 5010-5013 | Hoymiles Serial Number | RO | U64 |  |  |  |  |  |  |
| 5014-5029 | OEM Serial Number | RO | String |  |  |  |  |  |  |
| 5030-5044 | OEM Model Name | RO | String |  |  |  |  |  |  |
| 5045-5052 | Grid Meter Serial Number | RO | String |  |  |  |  |  |  |
| 5053-5060 | PV Meter Serial Number | RO | String |  |  |  |  |  |  |
| 5100 | Relay Supply Voltage Sampling | RO | U16 | V | ÷10 |  |  |  |  |
| 5101 | 12V Auxiliary Voltage Sampling | RO | U16 | V | ÷10 |  |  |  |  |
| 5102 | 12V Output Voltage Sampling | RO | U16 | V | ÷10 |  |  |  |  |
| 5103 | 5V Auxiliary Voltage Sampling | RO | U16 | V | ÷10 |  |  |  |  |
| 5104 | 3.3V Auxiliary Voltage Sampling | RO | U16 | V | ÷10 |  |  |  |  |
| 5105 | Ambient Temperature Sampling | RO | U16 | °C | ÷10 |  |  |  |  |
| 5106 | Busbar Temperature Sampling | RO | U16 | °C | ÷10 |  |  |  |  |
| 5107 | Relay Status | RO | U16 |  |  |  |  | The status is defined by a two-bit value: '1' represents open, '2' represents closed. bit0~1: KM1 Feed bit2~3: Gen Feed A bit4~5: Gen Feed B bit6~7 PV Feed AB bit8~9: SLoad Feed A bit10~11: SLoad Feed B bit12~15: Rsvd |  |
| 5108 | MID fault code | RO | U32 |  |  |  |  | Bit mask, 1 = fault: bit0 KM relay, bit1 gen relay A, bit2 gen relay B, bit3 PV relay AB, bit4 load relay A, bit5 load relay B, bit6 grid meter communication, bit7 inverter communication, bit8 inverter CAN communication, bit9 over-temperature, bit10 3.3V supply, bit11 5V supply, bit12 12V supply, bit13 emergency stop, bit14 GRID port overcurrent, bit15 GEN port overcurrent, bit16 PV port overcurrent, bit17 smart load port overcurrent |  |
| 5118 | Grid Meter Link Status | RO | U16 |  |  | 0 |  | 0: Offline 1: Online |  |
| 5119 | Pv Meter Link Status | RO | U16 |  |  | 0 |  | 0: Offline 1: Online |  |
| 5261 | Smart Load Voltage An | RO | U16 | V | ÷10 |  |  |  |  |
| 5262 | Smart Load Voltage Bn | RO | U16 | V | ÷10 |  |  |  |  |
| 5263 | Smart Load Voltage Cn | RO | U16 | V | ÷10 |  |  |  |  |
| 5264 | Smart Load Current An | RO | I16 | A | ÷100 |  |  |  |  |
| 5265 | Smart Load Current Bn | RO | I16 | A | ÷100 |  |  |  |  |
| 5266 | Smart Load Current Cn | RO | I16 | A | ÷100 |  |  |  |  |
| 5267 | Combined Active Power | RO | I32 | W |  |  |  |  |  |
| 5269 | Smart Load Active Power An | RO | I32 | W |  |  |  |  |  |
| 5271 | Smart Load Active Power An | RO | I32 | W |  |  |  |  |  |
| 5273 | Smart Load Active Power An | RO | I32 | W |  |  |  |  |  |
| 5275 | Smart Load Frequency | RO | I16 | Hz | ÷100 |  |  |  |  |

## Input Battery packs

22100-22199 describe pack 1. Packs 2-16 repeat the same layout in steps of 300 (22400, 22700, ...).

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 22100 | DCDC Status | RO | U16 |  |  | 1 |  | 0: Init 1: Wait 2: Relay detect 3: Running 4: Fault |  |
| 22101 | LLC Status | RO | U16 |  |  | 0x0A |  | 0: Init 1: Hv/Lv side drives are activated 2: Relay detect 3: Duty cycle adjustment 4: Adjustment completed |  |
| 22104 | DCDC Fault Code | RO | U32 |  |  |  |  |  |  |
| 22106 | Battery Voltage | RO | U16 | V | ÷100 | 0 |  |  |  |
| 22107 | Battery Current | RO | U16 | A | ÷10 |  |  |  |  |
| 22108 | Battert Power | RO | U16 | w |  |  |  |  |  |
| 22109 | DCDC Bus Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22110 | Output Voltage Of Relay Side | RO | U16 | kW | ÷10 |  |  |  |  |
| 22111 | Bus1 Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22112 | Bus2 Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22113 | HV Side Voltage1 | RO | U16 | V | ÷10 |  |  |  |  |
| 22114 | HV Side Voltage2 | RO | U16 | V | ÷10 |  |  |  |  |
| 22115 | Inductive Current1 | RO | I16 | A | ÷1000 |  |  |  |  |
| 22116 | Inductive Current2 | RO | I16 | A | ÷1000 |  |  |  |  |
| 22117 | Heating Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22118 | Ambient Temperature | RO | I16 | °C | ÷10 |  |  |  |  |
| 22119 | Radiator Temperature | RO | I16 | °C | ÷10 |  |  |  |  |
| 22120 | Positive Terminal Temperature Of The Floating Terminal | RO | I16 | °C | ÷10 |  |  |  |  |
| 22121 | The Negative Terminal Temperature Of The Floating Terminal | RO | I16 | °C | ÷10 |  |  |  |  |
| 22122 | Auxiliary Power 12V | RO | U16 | V | ÷1000 |  |  |  |  |
| 22123 | Auxiliary Power 7V | RO | U16 | V | ÷1000 |  |  |  |  |
| 22124 | Auxiliary Power 5V | RO | U16 | V | ÷1000 |  |  |  |  |
| 22125 | Auxiliary Power 1.5V | RO | U16 | V | ÷1000 |  |  |  |  |
| 22126 | The Minimum Allowable Bus Voltage For DCDC | RO | U16 | V | ÷10 |  |  |  |  |
| 22127 | DCDC System Working Status | RO | U16 |  |  |  |  | 0:Standby 1: Charge 2:Discharge |  |
| 22128 | DCDC Heating State | RO | U16 |  |  |  |  | 0: Stop heating 1: Heating is in progress 2: Heating circuit failuret 3: Heating circuit open circuit |  |
| 22150 | Group Terminal Voltage | RO | U16 | V | ÷10 | 0 |  |  |  |
| 22151 | Group Terminal Current | RO | I16 | A | ÷10 |  |  |  |  |
| 22152 | Group Soc | RO | U16 | % | ÷10 |  |  |  |  |
| 22153 | Group Soh | RO | U16 | % |  |  |  |  |  |
| 22154 | Pole Column Temperature 1 | RO | I16 | °C | ÷10 |  |  |  |  |
| 22155 | Pole Column Temperature 2 | RO | I16 | °C | ÷10 |  |  |  |  |
| 22156 | Cell Max Volt | RO | U16 | mV |  |  |  |  |  |
| 22157 | Cell Min Volt | RO | U16 | mV |  |  |  |  |  |
| 22158 | Cell Max Temperature | RO | I16 | °C | ÷10 |  |  |  |  |
| 22159 | Cell Min Temperature | RO | I16 | °C | ÷10 |  |  |  |  |
| 22160 | Level 1 Alarm status 1 | RO | U16 |  |  |  |  |  |  |
| 22161 | Level 1 Alarm status 2 | RO | U16 |  |  |  |  |  |  |
| 22162 | Level 1 Alarm status 3 | RO | U16 |  |  |  |  |  |  |
| 22163 | Level 2 Alarm status 1 | RO | U16 |  |  |  |  |  |  |
| 22164 | Level 2 Alarm status 2 | RO | U16 |  |  |  |  |  |  |
| 22165 | Level 2 Alarm status 3 | RO | U16 |  |  |  |  |  |  |
| 22166 | Level 3 Alarm status 1 | RO | U16 |  |  |  |  |  |  |
| 22167 | Level 3 Alarm status 2 | RO | U16 |  |  |  |  |  |  |
| 22168 | Level 3 Alarm status 3 | RO | U16 |  |  |  |  |  |  |
| 22169 | Hardware Fault Status | RO | U16 |  |  |  |  |  |  |
| 22170 | Fault Status/Main Control Fault | RO | U16 |  |  |  |  |  |  |
| 22171 | Maximum Allowable Charging Current | RO | U16 | A |  |  |  |  |  |
| 22172 | Minimum Allowable Discharging Current | RO | U16 | A |  |  |  |  |  |
| 22173 | Charging Cut-off Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22174 | Discharge Cut-off Voltage | RO | U16 | V | ÷10 |  |  |  |  |
| 22175 | Battery Cycle Count | RO | U16 |  |  |  |  |  |  |
| 22176 | Cumulative Battery Charge | RO | U16 | kWh | ÷10 | 0 |  |  |  |
| 22177 | Cumulative Battery Discharge | RO | U16 | kWh | ÷10 | 0 |  |  |  |
| 22178 | Single charge capacity | RO | U16 | kWh | ÷10 | 0 |  |  |  |
| 22179 | Single discharge quantity | RO | U16 | kWh | ÷10 | 0 |  |  |  |
| 22180 | Rated capacity | RO | U16 | kWh | ÷10 | 0 |  |  |  |
| 22181 | Current Power | RO | U16 | W |  | 0 |  |  |  |
| 22182 | Temperature of Low-Side Bridge Arm | RO | I16 | °C | ÷10 |  |  |  |  |
| 22183 | Instantaneous Maximum Charging Current | RO | U16 | A |  |  |  |  |  |
| 22184 | Instantaneous Maximum Discharging Current | RO | U16 | A |  |  |  |  |  |
| 22190 | Network Status | RO | U16 |  |  |  |  | 0: Invalid 1: Sucess 2: Fail 3: Process |  |
| 22191 | PWM Duty | RO | U16 | % |  | 0 |  |  |  |
| 22192 | End Pack Resist Status | RO | U16 |  |  |  |  | bit0: Upward terminal packet resistor bit1: Downlink terminal resistor |  |
| 22193 | RTC Time Stamp H | RO | U32 | s |  |  |  |  |  |
| 22194 | RTC Time Stamp L |  |  |  |  |  |  |  |  |
| 22195 | Button Number | RO | U16 |  |  |  |  |  |  |
| 22196 | Pre-charged Status | RO | U16 |  |  |  |  | 0: Invalid 1: Sucess 2: Fail 3: Process |  |
| 22197 | Battery Status | RO | U16 |  |  |  |  | bit0: Full charge Flag bit1: Empty Flag bit2: Force Charge Request Flag bit3: Full Charge Request Flag bit4: No Charge Flag bit5: No Disharge Flag |  |
| 22198 | Heating enable | RO | U16 |  |  |  |  | 0: Invalid 1: Enable 2: Disable |  |

## Input Second-level data

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 30000 | System WorkStatus | RO | U16 |  |  |  |  | System working status 0: PowerInit 1: StdbyMode 2: GridOnTest 3: GridOnMode 4: FaultMode 5: GridOffMode 6: ByPassMode |  |
| 30001 | PV Total Power | RO | U32 | W |  |  |  | PV Total Power (Internal + External) |  |
| 30003 | Internal PV Total power | RO | U32 | W |  |  |  |  |  |
| 30005 | External PV Total Power | RO | U32 | W |  |  |  |  |  |
| 30007 | Inv Active Power | RO | I32 | W |  |  |  | Inverter combined active power |  |
| 30009 | Battery Power | RO | I32 | W |  |  |  |  |  |
| 30011 | Grid Total Active Power | RO | I32 | W |  |  |  |  |  |
| 30013 | Generator Active Power | RO | I32 | W |  |  |  |  |  |
| 30015 | Load Active Power | RO | I32 | W |  |  |  | Load Active Power |  |
| 30017 | Smart Load active power | RO | I32 | W |  |  |  |  |  |
| 30019 | Battery Work Status | RO | U16 |  |  |  |  | 0: Standby 1:Charge 2:Discharge |  |
| 30020 | Battery Soc | RO | U16 | % |  |  |  |  |  |
| 30021 | Battery Fault Code | RO | U32 |  |  |  |  | Defined by bits, "1": fault, "0": no fault. Low-Voltage Battery: bit0: Battery Low-Voltage Alarm bit1: Battery High-Voltage Alarm bit2: Battery Pack Discharge Low- Voltage Alarm bit3: Battery Pack Charge High - Voltage Alarm bit4: Charge Low-Temperature Alarm bit5: Charge High-Temperature Alarm bit6: Discharge Low-Temperature Alarm bit7: Discharge High-Temperature Alarm bit8~bit31: Reserved; High-Voltage Battery: bit0 to bit7 are consistent with the Low-Voltage Battery bit8: Input Overvoltage Alarm bit9~bit31: Reserved; | ✅ |
| 30023 | DSP PWR Fault Code | RO | U32 |  |  |  |  | Defined by bits, "1": fault, "0": no fault, Details refer to Appendix 2. | ✅ |
| 30025 | DSP SAF Fault Code | RO | U32 |  |  |  |  | Defined by bits, "1": fault, "0": no fault, Details refer to Appendix 2. | ✅ |
| 30027 | Arm Fault Code1 | RO | U16 |  |  |  |  | Defined by bits, "0": fault, "1": no fault. bit0~bit4: Rsvd bit5:DSP PWR Communication Abnormality bit6: DSP SAF Communication Abnormality bit7~bit15: Rsvd |  |
| 30028 | Arm Fault Code2 | RO | U16 |  |  |  |  | Defined by bits, "0": fault, "1": no fault. bit0: Rsvd bit1: PV Meter Communication Abnormality bit2: Grid Meter Communication Abnormality bit3: BMS CAN Communication Abnormality bit4: Low DTU Version bit5: DTS Communication Abnormality bit6: Grid Meter Type Error bit7: PV Meter Type Error bit8: Slave Wrong Battery Connection (Multi-PCS, Single- Battery) bit9: DTU1 RS485 Communication Abnormality bit10: DTU2 RS485 Communication Abnormality bit11: DTU3 RS485 Communication Abnormality bit12: DTU4 RS485 Communication Abnormality bit13: DTU5 RS485 Communication Abnormality bit14: EV Charger1 Communication Abnormality bit15: EV Charger2 Communication Abnormality |  |
| 30029 | Arm Fault Code3 | RO | U16 |  |  |  |  | Defined by bits, "0": fault, "1": no fault. bit0: EV Charger1 Fault bit1: EV Charger2 Fault bit2: Sustained negative load bit3: Battery Capacity Abnormality bit4: Battery Fault bit5: Fan Speed Abnormality bit6: Battery Force Charge Request bit7: HMID Communication Abnormality bit8: HMID Machine Fault bit9: Master-Slave Communication Abnormality bit10~bit15: Rsvd |  |

## Input Real-time load data

| Address | Name | Access | Type | Unit | Scale | Default | Range | Description | |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| 30200 | Load Mode | RO | U16 |  |  |  |  | 0: Off-Grid 1: On-Grid |  |
| 30201 | Load Frequency | RO | I16 | Hz | ÷100 |  |  |  |  |
| 30203 | Load Voltage An | RO | U16 | V | ÷10 |  |  |  |  |
| 30204 | Load Active Power An | RO | I32 | W |  |  |  |  |  |
| 30206 | Load Energy Use Today An | RO | U32 | kWh | ÷10 |  |  |  |  |
| 30209 | Load Voltage Bn | RO | U16 | V | ÷10 |  |  |  |  |
| 30210 | Load Active Power Bn | RO | I32 | W |  |  |  |  |  |
| 30212 | Load Energy Use Today Bn | RO | U32 | kWh | ÷10 |  |  |  |  |
| 30215 | Load Voltage Cn | RO | U16 | V | ÷10 |  |  |  |  |
| 30216 | Load Active Power Cn | RO | I32 | W |  |  |  |  |  |
| 30218 | Load Energy Use Today Cn | RO | U32 | kWh | ÷10 |  |  |  |  |

# Fault codes

Bit definitions for HiOne hardware. Other Hoymiles models use different bit tables. Bits marked reserved are omitted.


## Input 30021-30022: battery fault code (1 = fault)

| Bit | Meaning |
|---:|---|
| 0 | Battery low-voltage alarm |
| 1 | Battery high-voltage alarm |
| 2 | Battery pack discharge low-voltage alarm |
| 3 | Battery pack charge high-voltage alarm |
| 4 | Charge low-temperature alarm |
| 5 | Charge high-temperature alarm |
| 6 | Discharge low-temperature alarm |
| 7 | Discharge high-temperature alarm |
| 8 | Input overvoltage alarm |

## Input 30023-30024: DSP power fault code (1 = fault)

| Bit | Meaning |
|---:|---|
| 0 | Shut down |
| 1 | Relay fault |
| 2 | SPI communication fault |
| 3 | Auxiliary power abnormality |
| 4 | CAN communication timeout |
| 5 | Shutdown fault from safety MCU |
| 6 | EPS wiring abnormality |
| 7 | Gateway off |
| 8 | Parallel communication abnormality |
| 9 | Persistent hardware fault |
| 10 | Sampling bias abnormality |
| 11 | SCI communication fault |
| 12 | Bus voltage abnormality |
| 13 | Fan fault |
| 14 | Hardware fault |
| 15 | Comparator fault |
| 16 | Wiring abnormality |
| 17 | Battery fault |
| 18 | Inverter drive fault / pre-synchronization failed |
| 19 | Temperature abnormality |
| 20 | PV fault |
| 21 | EEPROM fault |
| 22 | Phase order error |
| 23 | Bypass allow fault from safety MCU |
| 24 | CMPSS bias calculation error |
| 25 | Feed-in power limitation fault |
| 26 | EPS voltage abnormality |
| 27 | EPS overload |
| 28 | Generator voltage abnormality |
| 29 | Generator voltage ride-through |
| 30 | Grid voltage abnormality |
| 31 | Grid voltage ride-through |

## Input 30025-30026: DSP safety fault code (1 = fault)

| Bit | Meaning |
|---:|---|
| 0 | Grid overvoltage |
| 1 | Grid undervoltage |
| 2 | Grid 10-minute overvoltage |
| 3 | Grid overfrequency |
| 4 | Grid underfrequency |
| 5 | Grid three-phase imbalance |
| 6 | Grid reconnection fault |
| 7 | Grid lost |
| 10 | Auxiliary power abnormality |
| 11 | Grid relay fault |
| 12 | SPI communication fault |
| 13 | Arc self-test fault |
| 14 | Arc fault |
| 15 | Insulation (ISO) error |
| 16 | RCD self-test fault |
| 17 | RCD fault |
| 21 | SCI communication fault |
| 22 | Sampling bias abnormality |
| 23 | Flash fault |
| 24 | DC voltage overvoltage |
| 25 | DC current injection overcurrent |
| 26 | Interrupt overflow |
| 27 | Microelectronic fault |
| 28 | Low ambient temperature |
| 29 | Over temperature |
| 30 | Comparator fault |
| 31 | Fan fault |

## Input 30027-30029: ARM fault codes (0 = fault)

Note the inverted logic: a **0** bit means fault.

| Register | Bit | Meaning |
|---|---:|---|
| 30027 | 5 | DSP power communication abnormality |
| 30027 | 6 | DSP safety communication abnormality |
| 30028 | 1 | PV meter communication abnormality |
| 30028 | 2 | Grid meter communication abnormality |
| 30028 | 3 | BMS CAN communication abnormality |
| 30028 | 4 | Low DTU version |
| 30028 | 5 | DTS communication abnormality |
| 30028 | 6 | Grid meter type error |
| 30028 | 7 | PV meter type error |
| 30028 | 8 | Slave wrong battery connection |
| 30028 | 9-13 | DTU 1-5 RS485 communication abnormality |
| 30028 | 14-15 | EV charger 1-2 communication abnormality |
| 30029 | 0-1 | EV charger 1-2 fault |
| 30029 | 2 | Sustained negative load |
| 30029 | 3 | Battery capacity abnormality |
| 30029 | 4 | Battery fault |
| 30029 | 5 | Fan speed abnormality |
| 30029 | 6 | Battery force charge request |
| 30029 | 7 | HMID communication abnormality |
| 30029 | 8 | HMID machine fault |
| 30029 | 9 | Master-slave communication abnormality |

