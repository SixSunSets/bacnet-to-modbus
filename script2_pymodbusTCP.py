import BAC0
import json
import threading
import time
from pyModbusTCP.server import ModbusServer

global numero_equipos
numero_equipos = 190
local_data = threading.local()

instancia_bacnet = BAC0.connect(port=47813)

with open('C:/Users/bms/Documents/bacnet-to-modbus/Lista_de_Puntos.json') as archivo_json:
    datos_json = json.load(archivo_json)

def leer_dato(local_data, id_equipo):
    local_data.nombre_equipo = ''
    local_data.lista_datos = []
    local_data.equipos_ac = {}
    local_data.dato = {}

    for sede, equipos in datos_json.items():
        for equipo_id, puntos in equipos.items():
            if int(equipo_id) == id_equipo:
                local_data.nombre_equipo = puntos[0][5]
                local_data.lista_datos = puntos
                break
        if local_data.lista_datos:
            break

    if local_data.lista_datos:
        local_data.equipos_ac = {local_data.nombre_equipo: local_data.lista_datos}

        local_data.dato = {}
        for name, equipo in local_data.equipos_ac.items():
            for punto in equipo:
                local_data.type_signal = int(punto[11])
                try:
                    local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2]) + " " + str(punto[10]) + " " + str(punto[9]) + " presentValue"))
                except BAC0.core.io.IOExceptions.NoResponseFromController:
                    local_data.lectura_punto = None

                if local_data.type_signal == 2:  # Estado Encendido/Apagado
                    if local_data.lectura_punto is None or 'active' not in local_data.lectura_punto:
                        local_data.estado_on_off = 'Desconocido'
                    else:
                        local_data.estado_on_off = 'Encendido' if local_data.lectura_punto == 'active' else 'Apagado'

                elif local_data.type_signal == 4:  # Velocidad del ventilador
                    if local_data.lectura_punto is None or 'active' in local_data.lectura_punto or '.' in local_data.lectura_punto:
                        local_data.estado_velocidad = 'Undefined'
                    else:
                        local_data.indice = int(local_data.lectura_punto) if local_data.lectura_punto != '' else 0
                        local_data.estados = ['Undefined', 'Baja', 'Media', 'Alta', 'Auto']
                        local_data.estado_velocidad = local_data.estados[local_data.indice]

                elif local_data.type_signal == 6:  # Temperatura ambiente
                    if local_data.lectura_punto is None or '.' not in local_data.lectura_punto:
                        local_data.temperatura = 0.0
                    else:
                        local_data.temperatura = round(float(local_data.lectura_punto), 2) if local_data.lectura_punto != '' else 0

                elif local_data.type_signal == 8:  # Setpoint de temperatura
                    if local_data.lectura_punto is None or '.' not in local_data.lectura_punto:
                        local_data.setpoint_temperatura = 0.0
                    else:
                        local_data.setpoint_temperatura = round(float(local_data.lectura_punto), 2) if local_data.lectura_punto != '' else 0

            local_data.dato = {
                'NOMBRE': str(name),
                'ESTADO': str(local_data.estado_on_off),
                'VELOCIDAD': str(local_data.estado_velocidad),
                'TEMPERATURA': str(local_data.temperatura),
                'SETPOINT': str(local_data.setpoint_temperatura)
            }

    return local_data.dato


def leer_datos_equipo(id_equipo, resultados):
    local_data = threading.local()
    resultado = leer_dato(local_data, id_equipo)
    if resultado:  # Solo agregar resultados válidos
        resultados[id_equipo] = resultado

def obtener_datos_equipos(numero_equipos):
    resultados = {}
    hilos = []

    for id_equipo in range(numero_equipos):
        hilo = threading.Thread(target=leer_datos_equipo, args=(id_equipo, resultados))
        hilos.append(hilo)
        hilo.start()

    for hilo in hilos:
        hilo.join()

    return resultados

def mapear_a_modbus(resultados):
    address_counter = 1  # Dirección de inicio para los registros holding
    for id_equipo in sorted(resultados.keys()):  # Ordenar por id_equipo
        datos = resultados[id_equipo]
        estado = 1 if datos['ESTADO'] == 'Encendido' else 0
        velocidad = {'Baja': 1, 'Media': 2, 'Alta': 3}.get(datos['VELOCIDAD'], 0)
        temperatura = int(float(datos['TEMPERATURA']) * 10)  # Convertir a entero para Modbus
        setpoint = int(float(datos['SETPOINT']) * 10)  # Convertir a entero para Modbus

        server.data_bank.set_holding_registers(address_counter, [estado])
        print(f"Actualizado holding register en {address_counter} con valor {estado}")
        address_counter += 1

        server.data_bank.set_holding_registers(address_counter, [velocidad])
        print(f"Actualizado holding register en {address_counter} con valor {velocidad}")
        address_counter += 1

        server.data_bank.set_holding_registers(address_counter, [temperatura])
        print(f"Actualizado holding register en {address_counter} con valor {temperatura}")
        address_counter += 1

        server.data_bank.set_holding_registers(address_counter, [setpoint])
        print(f"Actualizado holding register en {address_counter} con valor {setpoint}")
        address_counter += 1

# Configurar y arrancar el servidor Modbus TCP
server = ModbusServer("0.0.0.0", 5020, no_block=True)
server.start()

try:
    while True:
        # Leer datos de los equipos
        datos_equipos = obtener_datos_equipos(numero_equipos)
        print(datos_equipos)
        
        # Mapear y actualizar los registros holding de Modbus
        mapear_a_modbus(datos_equipos)

        time.sleep(10)
except KeyboardInterrupt:
    print("Servidor detenido")
finally:
    server.stop()