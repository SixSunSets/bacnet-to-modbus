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

