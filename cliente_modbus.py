from pyModbusTCP.client import ModbusClient
import logging

HOST = "10.84.8.12"
PORT = 502
UNIT_ID = 1

# Crear instancia del cliente Modbus
c = ModbusClient(host=HOST, port=PORT, unit_id=UNIT_ID)
logging.basicConfig()
logging.getLogger('pyModbusTCP.client').setLevel(logging.DEBUG)


# Intentar conectar al servidor Modbus
if not c.open():
    print(f"Error al conectar con el servidor Modbus en {HOST}:{PORT}")
else:
    print(f"Conectado al servidor Modbus en {HOST}:{PORT}")

# Dirección del registro a leer
address_hex = "0x0001"
address = int(address_hex, 16)

# Leer el registro holding
reg = c.read_holding_registers(address, 1)

# Verificar si la lectura fue exitosa
if reg is None:
    print(f"Error al leer el registro en la dirección {address}")
else:
    print(f"Registro en la dirección {address}: {reg}")

# Cerrar la conexión
c.close()