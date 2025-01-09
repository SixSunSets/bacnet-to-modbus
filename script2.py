import BAC0
import json
import threading
import time
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

global numero_equipos
numero_equipos = 190
local_data = threading.local()

instancia_bacnet = BAC0.connect(port=47813)

with open('C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos.json') as archivo_json:
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

def mapear_a_modbus(datos_equipos, context):
    address_counter = 1  # Dirección de inicio para los registros holding
    for id_equipo in sorted(datos_equipos.keys()):
        datos = datos_equipos[id_equipo]
        estado = 1 if datos['ESTADO'] == 'Encendido' else 0
        velocidad = {'Baja': 1, 'Media': 2, 'Alta': 3}.get(datos['VELOCIDAD'], 0)
        temperatura = int(float(datos['TEMPERATURA']) * 10)  # Convertir a entero para Modbus
        setpoint = int(float(datos['SETPOINT']) * 10)  # Convertir a entero para Modbus

        context[0].setValues(3, address_counter, [estado])
        print(f"Actualizado holding register en {address_counter} con valor {estado}")
        address_counter += 1

        context[0].setValues(3, address_counter, [velocidad])
        print(f"Actualizado holding register en {address_counter} con valor {velocidad}")
        address_counter += 1

        context[0].setValues(3, address_counter, [temperatura])
        print(f"Actualizado holding register en {address_counter} con valor {temperatura}")
        address_counter += 1

        context[0].setValues(3, address_counter, [setpoint])
        print(f"Actualizado holding register en {address_counter} con valor {setpoint}")
        address_counter += 1

def comando_unico(local_data,datos):
    local_data.id_equipo = int(datos[0])
    local_data.comando_on_off = datos[1]
    local_data.comando_ventilador = datos[2]
    local_data.comando_setpoint = datos[3]

    local_data.nombre_equipo = ''
    local_data.lista_datos = []
    local_data.equipos_ac = {}

    for sede, equipos in datos_json.items():
        for equipo_id, puntos in equipos.items():
            if int(equipo_id) == local_data.id_equipo:
                local_data.nombre_equipo = puntos[0][5]  
                local_data.lista_datos = puntos
                break
        if local_data.lista_datos:
            break

    if local_data.lista_datos:
        local_data.equipos_ac = {local_data.nombre_equipo: local_data.lista_datos}
     
    local_data.status_comando_1 = None
    local_data.status_comando_3 = None
    local_data.status_comando_5 = None
    
    for name, equipo in local_data.equipos_ac.items():
        for punto in equipo:
            local_data.type_signal = int(punto[11])
            if local_data.type_signal == 1:
                local_data.status_comando_1 = instancia_bacnet.write(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue "+str(local_data.comando_on_off))
            elif local_data.type_signal == 3:
                local_data.status_comando_3 = instancia_bacnet.write(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue "+str(local_data.comando_ventilador))
            elif local_data.type_signal == 5:
                local_data.status_comando_5 = instancia_bacnet.write(str(punto[2])+" "+str(punto[10])+" "+str(punto[9])+" presentValue "+str(local_data.comando_setpoint))

def comandar_datos_equipo(datos):
    local_data.id_equipo = datos["row_id"]
    local_data.comando_on_off = datos["values"]["col1"]
    local_data.comando_ventilador = datos["values"]["col2"]
    local_data.comando_setpoint = datos["values"]["col3"]
    local_data.datos = [local_data.id_equipo,local_data.comando_on_off,local_data.
    comando_ventilador,local_data.comando_setpoint]
    comando_unico(local_data,local_data.datos)

def manejar_escritura_modbus():
    #rowId = 1
    #on_off = "active"
    #ventilador = 2 #3
    #setpoint = 20 #21
    #datos = {"row_id":rowId,"values":{"col1": on_off, "col2":ventilador, "col3": setpoint}}
    #comandar_datos_equipo(datos)
    # Leer registros modificados
    valores_anteriores = {}
    while True:
        address_counter_rw = 1000
        for address in range(address_counter_rw, address_counter_rw + numero_equipos * 3, 3):
            estado = context[0].getValues(3, address, count=1)[0]
            ventilador = context[0].getValues(3, address + 1, count=1)[0]
            setpoint = context[0].getValues(3, address + 2, count=1)[0] / 10.0
            row_id = (address - address_counter_rw) // 3

            # Verificar si los valores han cambiado
            if address not in valores_anteriores or valores_anteriores[address] != (estado, ventilador, setpoint):
                valores_anteriores[address] = (estado, ventilador, setpoint)

                # Enviar comando BACnet correspondiente
                if address % 3 == 0:
                    # Comando de encendido/apagado
                    comando = "active" if estado == 1 else "inactive"
                    instancia_bacnet.write(f"10.84.67.185 binaryOutput {row_id} presentValue {comando}")

        time.sleep(1)  # Esperar un tiempo antes de la siguiente verificación


def iniciar_servidor():   
    StartTcpServer(context=context, identity=identity, address=("", 5020))

# Configurar servidor Modbus TCP
store = ModbusSlaveContext(hr=ModbusSequentialDataBlock.create(), zero_mode=True)
context = ModbusServerContext(slaves=store, single=True)
identity = ModbusDeviceIdentification()

# Iniciar el servidor en un hilo separado
modbus_thread = threading.Thread(target=iniciar_servidor)
modbus_thread.start()

# Iniciar el manejo de escrituras en un hilo separado
escritura_thread = threading.Thread(target=manejar_escritura_modbus, args=(context,))
escritura_thread.start()

try:
    while True:
        # Obtener datos de los equipos
        datos_equipos = obtener_datos_equipos(numero_equipos)
        # Mapear los datos a registros holding
        mapear_a_modbus(datos_equipos, context)
        # Esperar un tiempo antes de la siguiente actualización
        time.sleep(10)
except KeyboardInterrupt:
    print("Servidor detenido")

