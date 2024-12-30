import BAC0
import json
from pyModbusTCP.server import ModbusServer, DataBank

def crear_instancia_bacnet():
    try:
        bacnet = BAC0.connect(port=47811)
    except Exception as e:
        print(f"Error al conectar con BACnet: {e}")
        bacnet = None
    return bacnet

def descubrir_puntos_bacnet(bacnet, ip):
    try:
        tabla = bacnet.readMultiple(f'{ip} device 1001 all')
        if not tabla:
            print("No se encontraron puntos.")
            return []

        puntos = [{'object_type': punto[0], 'object_id': punto[1]} for punto in tabla[-15]]
        return puntos
    except Exception as e:
        print(f"Error al descubrir puntos BACnet: {e}")
        return []

def leer_valores_bacnet(bacnet, ip, puntos):
    valores = {}
    for punto in puntos:
        try:
            valor = bacnet.read(f'{ip} {punto["object_type"]} {punto["object_id"]} presentValue')
            valores[punto["object_id"]] = valor
        except Exception as e:
            print(f"Error al leer valor de {punto}: {e}")
    return valores

def mapear_a_modbus(puntos):
    modbus_mapeo = []
    address_counters = {
        'coil_read': 0,
        'coil_write': 1000,
        'input_register': 3000,
        'holding_register': 4000
    }

    for punto in puntos:
        if punto['object_type'] == 'binaryInput':
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'coil_read',
                'modbus_address': address_counters['coil_read']
            })
            address_counters['coil_read'] += 1
        elif punto['object_type'] == 'binaryOutput':
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'coil_write',
                'modbus_address': address_counters['coil_write']
            })
            address_counters['coil_write'] += 1
        elif punto['object_type'] == 'analogInput':
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'input_register',
                'modbus_address': address_counters['input_register']
            })
            address_counters['input_register'] += 1
        elif punto['object_type'] == 'analogValue':
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'holding_register',
                'modbus_address': address_counters['holding_register']
            })
            address_counters['holding_register'] += 1

    return modbus_mapeo

def actualizar_modbus(valores, mapeo):
    for punto in mapeo:
        valor = valores.get(punto['object_id'])
        if valor is not None:
            if punto['modbus_type'] == 'coil_read':
                DataBank.set_bits(punto['modbus_address'], [valor])
            elif punto['modbus_type'] == 'coil_write':
                DataBank.set_bits(punto['modbus_address'], [valor])
            elif punto['modbus_type'] == 'input_register':
                DataBank.set_words(punto['modbus_address'], [valor])
            elif punto['modbus_type'] == 'holding_register':
                DataBank.set_words(punto['modbus_address'], [valor])

bacnet = crear_instancia_bacnet()
puntos = descubrir_puntos_bacnet(bacnet, '10.84.67.185')
modbus_mapeo = mapear_a_modbus(puntos)

# Configurar y arrancar el servidor Modbus TCP
server = ModbusServer("0.0.0.0", 502, no_block=True)
server.start()

try:
    while True:
        valores_bacnet = leer_valores_bacnet(bacnet,'10.84.67.185', puntos)
        actualizar_modbus(valores_bacnet, modbus_mapeo)
except KeyboardInterrupt:
    print("Servidor detenido")
finally:
    server.stop()

# modbus_mapeo = mapear_a_modbus(puntos)
# with open('mapeo_modbus.json', 'w') as f:
#    json.dump(modbus_mapeo, f, indent=4)