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
Briefly, binary data types can only have two values: “active” or “inactive”, while multistate types accept integer values, and analog types allow decimal values. A detailed description of each `Object type` can be found in the official Daikin design guide: Interface for use in BACnet [1, p. 55].
We are only interested in a subset of points from the extensive list—five for reading and three for writing.

- Read points: These provide information about the on/off status, fan speed, room temperature, setpoint (adjusted value), and error code.
- Write points: These allow control over turning the unit on/off, adjusting the fan speed, and modifying the setpoint of indoor units.

### Creation of the Modbus Server
A Modbus server is a process that listens for requests from Modbus clients, allowing them to read or write data stored in registers. In the gateway, a Modbus server is created on the local machine, enabling clients such as building automation software or a web application to interact with the system. To standardize data storage, only holding registers are used. Holding registers are 16-bit memory locations that can store values for both reading and writing, making them suitable for maintaining the state of BACnet data within the Modbus server.
  
The server is initialized with the following Python script using pymodbus:

```python3
slaves  = {
                0x0A: ModbusSlaveContext(hr=ModbusSequentialDataBlock.create(), zero_mode=True)
            }

IP = ""
PORT = 502
context = ModbusServerContext(slaves=slaves, single=False)
identity = ModbusDeviceIdentification()
StartTcpServer(context=context, identity=identity, address=(IP, PORT))
```

For this implementation, the Modbus server was configured with the following characteristics:

- Unit ID: `0x0A` => Used to identify a specific slave device when multiple devices share the same network connection. 0x0A was chosen to follow the same convention as LG’s DDC controllers, which use this ID for their Modbus servers.
- Port: `502` => This is the default Modbus TCP port, commonly used for communication.
- Holding Registers (`hr`) => A sequential block of holding registers is created, which are stored inside a Modbus slave context.
- `context (ModbusServerContext)` => This represents the data model of the Modbus server. It stores the register values and manages the Modbus slaves (devices). Here, we configure a single slave (0x0A) with holding registers as its only storage type.
- `identity (ModbusDeviceIdentification)` => This provides device metadata, such as manufacturer name, product code, or version, that Modbus clients can query. In this case, it’s initialized but empty.
- `StartTcpServer(context=context, identity=identity, address=("", 502))` => This function starts the Modbus TCP server on the local machine and port (502), allowing clients to connect and interact with the Modbus registers.

Although BACnet data is read and stored in Modbus registers, the mapping is not direct—certain transformations are required to ensure compatibility between both protocols.

### Mapping BACnet Data to Modbus Registers
This process ensures that all BACnet data is adapted to a format compatible with Modbus holding registers. To maintain order in the assignment of Modbus registers, data is stored sequentially starting from register 0x01, corresponding to the first read point of the indoor unit with the lowest assigned ID (a convention for device identification). Thus, the first five registers in the Modbus server belong to the first indoor unit, the next five to the second unit, and so on.

## References
[1] [Daikin Design Guide: Interface for Use in BACnet®](https://research-onero.s3.ap-southeast-1.amazonaws.com/Daikin_dev/img/library/files/CI190128005_files2019-01-28_16-34-59files.pdf) 


