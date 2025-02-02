# BACnet IP to Modbus TCP Gateway
## BACnet IP
BACnet (Building Automation and Control Network) is a standardized communication protocol for building automation, developed by ASHRAE (American Society of Heating, Refrigerating and Air-Conditioning Engineers) in the 1990s. Its main goal is to enable interoperability between devices from different manufacturers in HVAC, lighting, security, and other control systems.

Some brands, such as LG, integrate BACnet natively into their DDC (Direct Digital Controllers). However, other manufacturers, like Daikin, require a D-BACS device to convert their proprietary protocol to the BACnet standard.

To connect as a BACnet client from Python, the `BAC0==23.7.3` library can be used.

```python3
import BAC0
BAC0.connect(port=PORT)
```

## Modbus TCP
Modbus is a communication protocol created in 1979 by Modicon (now Schneider Electric). While it is widely known for its use in IoT applications, its simplicity makes it a perfect fit for building automation.

The need for converting from one protocol to another arises for two main reasons: 
Building automation software typically works with proprietary protocols, which are often modified versions of BACnet, or Modbus, requiring a translation layer. On the other hand, for the web application used to monitor and control VRV system equipment, Modbus provided better performance than BACnet, making it the preferred protocol.

In Python, a Modbus server can be created using the `pymodbus==2.5.3` library.

```python3
from pymodbus.server.sync import StartTcpServer
StartTcpServer(context=context, identity=identity, address=(IP, PORT))
```

## Gateway
<p align="center">
  <img src="https://github.com/user-attachments/assets/8e727f08-2724-4701-8630-381aa296d3ee" width="750"/>
</p>

The gateway acts as a BACnet client, reading the available points from each Daikin device, each with its own IP address and located in different buildings. The points represent specific variables such as on/off status, fan speed, and temperature, and are identified by an `Object type` and an `Object ID`.

With this information, we can determine whether a point is read-only or read/write. Therefore, we need a list of points for each Daikin device, which can be easily obtained using a BACnet Explorer such as YABE (Yet Another BACnet Explorer).

### Example of a BACnet point list
<div align="center">

| Object name | Object type | Object ID|
|-----------|-----------|-----------|
| StartStopCommand_001    | binaryOutput   | 257 |
| StartStopStatus_001    | binaryInput    | 258 |
| MalfunctionCode_001    | multiStateInput | 260 |
| AirFlowRateCommand_001    | multiStateOutput | 263 |
| AirFlowRateStatus_001    | multiStateInput | 264 |
| RoomTemp_001    | analogInput | 265 |
| TempAdjust_001    | analogValue | 266 |

</div>

### Interacting with BACnet points
A detailed description of each `Object type` can be found in the official Daikin design guide: Interface for use in BACnet® (p 55).


