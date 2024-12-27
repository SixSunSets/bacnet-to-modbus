import BAC0
import json
from temporal import puntos_bacnet, puntos

def crear_instancia_bacnet():
    try:
        bacnet = BAC0.connect(port=47811)
    except Exception as e:
        print(f"Error al conectar con BACnet: {e}")
        bacnet = None
    return bacnet

def descubrir_puntos_bacnet(bacnet,ip):
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

def mapear_a_modbus(puntos):

    modbus_mapeo = []
    # Contadores de direcciones
    address_counters = {
        'coil_read': 0,
        'coil_write': 1000,
        'input_register': 3000,
        'holding_register': 4000
    }

    for punto in puntos:
        if punto['object_type'] == 'binaryInput':
            # Los binaryInput de BACnet se asignan a las direcciones de "coil_read".
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'coil_read', # Tipo Modbus asociado (lectura de estado binario).
                'modbus_address': address_counters['coil_read']
            })
            address_counters['coil_read'] += 1
        elif punto['object_type'] == 'binaryOutput':
            # Los binaryOutput de BACnet se asignan a las direcciones de "coil_write".
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'coil_write', # Tipo Modbus asociado (escritura de estado binario).
                'modbus_address': address_counters['coil_write']
            })
            address_counters['coil_write'] += 1
        
        elif punto['object_type'] == 'analogInput':
            # Los analogInput de BACnet se asignan a los "input_register".
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'input_register',      # Tipo Modbus asociado (lectura analógica).
                'modbus_address': address_counters['input_register']
            })
            address_counters['input_register'] += 1

        elif punto['object_type'] == 'analogValue':
            # Los analogValue de BACnet se asignan a los "holding_register".
            modbus_mapeo.append({
                'object_type': punto['object_type'],
                'object_id': punto['object_id'],
                'modbus_type': 'holding_register',    # Tipo Modbus asociado (lectura/escritura analógica).
                'modbus_address': address_counters['holding_register']
            })
            address_counters['holding_register'] += 1

    return modbus_mapeo

modbus_mapeo = mapear_a_modbus(puntos)

with open('mapeo_modbus.json', 'w') as f:
    json.dump(modbus_mapeo, f, indent=4)