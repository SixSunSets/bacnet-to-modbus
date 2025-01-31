import BAC0
import json
import threading
import time
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

id_equipo_inicio = 191 # 1
numero_equipos = 75 # 190
local_data = threading.local()

instancia_bacnet = BAC0.connect(port=47813)

# C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json
# C:/Users/bms/Documents/bacnet-to-modbus/Lista_de_Puntos_Daikin.json
# C:/Users/alexa/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json

with open("C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json") as archivo_json:
    datos_json = json.load(archivo_json)

def leer_dato(local_data, id_equipo):
    local_data.nombre_equipo = ''
    local_data.lista_datos = []
    local_data.equipos_ac = {}
    local_data.dato = {}
    local_data.error = None

    for sede, equipos in datos_json.items():
        # print(equipos)
        for equipo_id, puntos in equipos.items():
            # print(equipo_id)
            if int(equipo_id) == id_equipo:
                local_data.nombre_equipo = puntos[0][5]
                local_data.lista_datos = puntos
                break
        if local_data.lista_datos:
            break

    if local_data.lista_datos:
        local_data.equipos_ac = {local_data.nombre_equipo: local_data.lista_datos}
        local_data.dato = {}

        # print(local_data.equipos_ac) #######
        # print(f'{local_data.equipos_ac}\n') #####
        for name, equipo in local_data.equipos_ac.items():
            for punto in equipo:
                local_data.type_signal = int(punto[11])
                local_data.marca = punto[6]
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
                        if local_data.marca == 'LG':
                            local_data.estados = {0: 'Undefined', 1: 'Baja', 2:'Media', 3:'Alta', 4:'Auto'}
                            local_data.estado_velocidad = local_data.estados[local_data.indice]
                        if local_data.marca == 'Daikin':
                            local_data.estados = {1: 'Baja', 2:'Alta', 3:'Media'} # Solo los que tienen 3 niveles vel. pueden tener 'Media'
                            local_data.estado_velocidad = local_data.estados[local_data.indice]

                elif local_data.type_signal == 6:  # Temperatura ambiente
                    if local_data.lectura_punto is None or '.' not in local_data.lectura_punto:
                        local_data.temperatura = 0.0
                    else:
                        local_data.temperatura = round(float(local_data.lectura_punto), 2) if local_data.lectura_punto != '' else 0

                elif local_data.type_signal == 7:
                    if local_data.marca == 'Daikin': 
                        if int(local_data.lectura_punto) == 1:
                            local_data.error = 0 # No hay error
                        else:
                            local_data.error = 242 # Hay error

                elif local_data.type_signal == 8:  # Setpoint de temperatura
                    if local_data.lectura_punto is None or '.' not in local_data.lectura_punto:
                        local_data.setpoint_temperatura = 0.0
                    else:
                        local_data.setpoint_temperatura = round(float(local_data.lectura_punto), 2) if local_data.lectura_punto != '' else 0

            local_data.dato = {
                'MARCA': equipo[0][6],
                'NOMBRE': str(name),
                'ESTADO': str(local_data.estado_on_off),
                'VELOCIDAD': str(local_data.estado_velocidad),
                'TEMPERATURA': str(local_data.temperatura),
                'SETPOINT': str(local_data.setpoint_temperatura),
                'ERROR': str(local_data.error)
            }

    print(local_data.dato)
    return local_data.dato

def leer_datos_equipo(id_equipo, resultados):
    local_data = threading.local()
    resultado = leer_dato(local_data, id_equipo)
    if resultado:  # Solo agregar resultados válidos
        resultados[id_equipo] = resultado

def obtener_datos_equipos(numero_equipos):
    resultados = {}
    hilos = []

    for id_equipo in range(id_equipo_inicio, id_equipo_inicio + numero_equipos):
        hilo = threading.Thread(target=leer_datos_equipo, args=(id_equipo, resultados))
        hilos.append(hilo)
        hilo.start()

    for hilo in hilos:
        hilo.join()

    return resultados

def mapear_a_modbus(datos_equipos, context):
    address_counter = 1  # Dirección de inicio para los registros holding 0x0001
    for id_equipo in sorted(datos_equipos.keys()):
        datos = datos_equipos[id_equipo]
        estado = 1 if datos['ESTADO'] == 'Encendido' else 0
        if datos['MARCA'] == 'LG':
            velocidad = {'Baja': 1, 'Media': 2, 'Alta': 3}.get(datos['VELOCIDAD'], 0) # Daikin {Baja: 1, Media: 3, Alta: 5}, solo algunos equipos tienen media
        elif datos['MARCA'] == 'Daikin':
            velocidad = {'Baja': 1, 'Alta': 2, 'Media': 3}.get(datos['VELOCIDAD'], 0)
        temperatura = int(float(datos['TEMPERATURA']) * 10)  # Convertir a entero para Modbus
        setpoint = int(float(datos['SETPOINT']) * 10)  # Convertir a entero para Modbus
        error = int(datos['ERROR'])

        context[0xA].setValues(3, address_counter, [estado])
        print(f"Actualizado holding register en {address_counter} con valor {estado}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [velocidad])
        print(f"Actualizado holding register en {address_counter} con valor {velocidad}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [setpoint])
        print(f"Actualizado holding register en {address_counter} con valor {setpoint}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [temperatura])
        print(f"Actualizado holding register en {address_counter} con valor {temperatura}")
        address_counter += 1

        context[0XA].setValues(3, address_counter, [error])
        print(f"Actualizado holding register en {address_counter} con valor {error}")
        address_counter += 1

def manejar_escritura_modbus(context):
    address_counter = 0xA000  # Dirección inicial para registros Modbus
    inicializados = set()  # Usar un conjunto para registros inicializados
    valores_pasados = {}  # Diccionario para almacenar valores anteriores

    # Filtrar y almacenar los puntos de control (tipos de señal 1, 3 y 8)
    puntos_control = []
    for sede, equipos in datos_json.items():
        for equipo_id, puntos in equipos.items():
            for punto in puntos:
                if punto[11] in (1, 3, 8):  # Solo incluir tipos de señal 1, 3 y 8
                    puntos_control.append(punto)

    print(puntos_control)

    while True:
        for offset, punto in enumerate(puntos_control):  # Iterar sobre los puntos de control
            address = address_counter + offset  # Calcular la dirección Modbus

            # Leer el valor actual desde el contexto Modbus
            value = context[0xA].getValues(3, address, count=1)[0]

            # Obtener los detalles del punto de control
            ip = punto[2]  # IP
            object_type = punto[10]  # Object Type (BACnet)
            object_id = punto[9]  # Object ID (BACnet)
            tipo_senal = punto[11]  # Tipo señal

            # Determinar el valor presente según el tipo de señal
            if tipo_senal == 1:  # binaryOutput (estado on/off)
                present_value = "active" if value == 1 else "inactive"
            elif tipo_senal == 3:  # multiStateOutput (velocidad)
                present_value = value
            elif tipo_senal == 8:  # analogValue (setpoint)
                present_value = value / 10.0

            # Generar el f-string dinámicamente
            f_string = f"{ip} {object_type} {object_id} presentValue {present_value}"

            # Lógica de inicialización y cambios
            if address not in inicializados:
                if present_value != ("inactive" if tipo_senal == 1 else 0):
                    inicializados.add(address)
                    valores_pasados[address] = present_value
                    #instancia_bacnet.write(f_string)  # Imprimir en la primera escritura
                    print(f_string)
            elif valores_pasados[address] != present_value:
                #instancia_bacnet.write(f_string)  # Imprimir en cambios posteriores
                print(f_string)
                valores_pasados[address] = present_value  # Actualizar el valor anterior

        time.sleep(2)  # Esperar antes de la siguiente iteración

def iniciar_servidor():   
    StartTcpServer(context=context, identity=identity, address=("", 502))

if __name__ == '__main__':
    # Configurar servidor Modbus TCP
    slaves  = {
                0xA: ModbusSlaveContext(hr=ModbusSequentialDataBlock.create(), zero_mode=True) # = store
            }
    context = ModbusServerContext(slaves=slaves, single=False)
    identity = ModbusDeviceIdentification()

    # Iniciar el servidor en un hilo separado
    modbus_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    modbus_thread.start()

    # Iniciar el manejo de escrituras en un hilo separado
    escritura_thread = threading.Thread(target=manejar_escritura_modbus, args=(context,), daemon=True)
    escritura_thread.start()

    try:
        while True:
            # Obtener datos de los equipos
            # datos_equipos = obtener_datos_equipos(numero_equipos)
            # Mapear los datos a registros holding
            # mapear_a_modbus(datos_equipos, context)
            # Esperar un tiempo antes de la siguiente actualización
            time.sleep(10)
    except KeyboardInterrupt:
        print("Servidor detenido")

