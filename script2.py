import BAC0
import json
import threading
from pyModbusTCP.server import ModbusServer, DataBank

global numero_equipos
numero_equipos = 10
local_data = threading.local()

instancia_bacnet = BAC0.connect(port=47813)

with open('C:/Users/bms/Documents/Web Socket/backend/Lista_de_Puntos.json') as archivo_json:
    datos_json = json.load(archivo_json)

def leer_dato(local_data,id_equipo):
    #global instancia_bacnet
    local_data.nombre_equipo = ''
    local_data.lista_datos = []
    local_data.equipos_ac = {}

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
                #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                if local_data.type_signal == 2:  # Estado Encendido/Apagado
                    while ('active' not in local_data.lectura_punto):
                        #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                        local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                    if local_data.lectura_punto == 'active':
                        local_data.estado_on_off = 'Encendido'
                    elif local_data.lectura_punto == 'inactive':
                        local_data.estado_on_off = 'Apagado'
                    else:
                        local_data.estado_on_off = 'Undefined'

                elif local_data.type_signal == 4:  # Velocidad del ventilador
                    while ('active' in local_data.lectura_punto or '.' in local_data.lectura_punto):
                        #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                        local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                    if local_data.lectura_punto != '':
                        local_data.indice = int(local_data.lectura_punto)
                    else:
                        local_data.indice = 0
                    local_data.estados = ['Undefined', 'Baja', 'Media', 'Alta', 'Auto']
                    local_data.estado_velocidad = local_data.estados[local_data.indice]

                elif local_data.type_signal == 6:  # Temperatura ambiente
                    while ('.' not in local_data.lectura_punto):
                        #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                        local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                    if local_data.lectura_punto != '':
                        local_data.temperatura = round(float(local_data.lectura_punto), 2)
                    else:
                        local_data.temperatura = 0

                elif local_data.type_signal == 8:  # Setpoint de temperatura
                    while ('.' not in local_data.lectura_punto):
                        #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                        local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                    if local_data.lectura_punto != '':
                        local_data.setpoint_temperatura = round(float(local_data.lectura_punto), 2)
                    else:
                        local_data.setpoint_temperatura = 0

                elif local_data.type_signal == 7:  # Código de error
                    while ('.' not in local_data.lectura_punto):
                        #local_data.lectura_punto = str(bf.leer_punto(instancia_bacnet, punto[2], punto[10], punto[9]))
                        local_data.lectura_punto = str(instancia_bacnet.read(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue"))
                    if local_data.lectura_punto != '':
                        local_data.error = int(float(local_data.lectura_punto))
                    else:
                        local_data.error = 242
                    
            local_data.dato = {
                'SEDE': equipo[0][7],
                'MARCA': equipo[0][6],
                'NOMBRE': str(name),
                'ESTADO': str(local_data.estado_on_off),
                'VELOCIDAD': str(local_data.estado_velocidad),
                'TEMPERATURA': str(local_data.temperatura),
                'SETPOINT': str(local_data.setpoint_temperatura),
                'ERROR': str(local_data.error)
            }

    return local_data.dato

def leer_datos_equipo(id_equipo, resultados):
    local_data = threading.local()
    resultados[id_equipo] = leer_dato(local_data, id_equipo)

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
    address_counter = 4000  # Starting address for holding registers
    for id_equipo, datos in resultados.items():
        estado = 1 if datos['ESTADO'] == 'Encendido' else 0
        velocidad = {'Baja': 1, 'Media': 2, 'Alta': 3}.get(datos['VELOCIDAD'], 0)
        temperatura = int(float(datos['TEMPERATURA']) * 10)  # Convertir a entero para Modbus
        setpoint = int(float(datos['SETPOINT']) * 10)  # Convertir a entero para Modbus

        DataBank.set_words(address_counter, [estado])
        print(f"Actualizado holding register en {address_counter} con valor {estado}")
        address_counter += 1

        DataBank.set_words(address_counter, [velocidad])
        print(f"Actualizado holding register en {address_counter} con valor {velocidad}")
        address_counter += 1

        DataBank.set_words(address_counter, [temperatura])
        print(f"Actualizado holding register en {address_counter} con valor {temperatura}")
        address_counter += 1

        DataBank.set_words(address_counter, [setpoint])
        print(f"Actualizado holding register en {address_counter} con valor {setpoint}")
        address_counter += 1

# Configurar y arrancar el servidor Modbus TCP
server = ModbusServer("0.0.0.0", 502, no_block=True)
server.start()

try:
    # Leer datos de los equipos
    datos_equipos = obtener_datos_equipos(numero_equipos)
    print(datos_equipos)
    
    # Mapear y actualizar los registros holding de Modbus
    mapear_a_modbus(datos_equipos)
except KeyboardInterrupt:
    print("Servidor detenido")
finally:
    server.stop()
