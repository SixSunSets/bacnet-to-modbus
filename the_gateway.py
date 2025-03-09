import BAC0
import time
import threading
import json
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from BAC0.core.io.IOExceptions import NoResponseFromController, Timeout

id_equipo_inicio = 191 # ID del primer equipo Daikin en Lista_de_Puntos_Daikin
id_equipo_fin = 468 # ID del último equipo Daikin en Lista_de_Puntos_Daikin
numero_equipos = id_equipo_fin - id_equipo_inicio + 1

local_data = threading.local() # Objeto para almacenar datos locales a cada hilo

# C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json
# C:/Users/bms/Documents/bacnet-to-modbus/Lista_de_Puntos_Daikin.json
# C:/Users/alexa/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json
with open("C:/Users/bms/Documents/bacnet-to-modbus/Lista_de_Puntos_Daikin.json") as archivo_json:
    datos_json = json.load(archivo_json) 

def leer_datos_equipo(local_data, id_equipo):

    local_data.id_equipo = id_equipo
    local_data.puntos = [] 

    # Bucle para extraer los puntos de lectura asociados a un equipo; puntos = [[],[],...]
    for hoja, equipos in datos_json.items():
        for id, puntos in equipos.items():
            if int(id) == id_equipo:
                for punto in puntos:
                    if punto[11] in (2,4,6,7,8):
                        local_data.puntos.append(punto)
                break

    #print(local_data.puntos)

    if local_data.puntos:
        # Datos del equipo con id_equipo
        local_data.datos_equipo = {}
        local_data.dicc = {}
        local_data.objetos = {}
        
        for punto in local_data.puntos:
            # Para cada punto de lectura, se extraen los datos necesarios para hacer un comando BACnet de lectura
            local_data.ip = punto[2]
            local_data.id_objeto = punto[9]
            local_data.tipo_objeto = punto[10]
            local_data.tipo_senal = punto[11]
            local_data.dicc[local_data.tipo_senal] = (local_data.tipo_objeto,local_data.id_objeto)
            local_data.objetos[f'{local_data.tipo_objeto}:{local_data.id_objeto}'] = ['presentValue']

        # print(local_data.objetos)
        # Se arma el diccionario para la lectura múltiple    
        _rpm = {'address': local_data.ip,
                    'objects': local_data.objetos
                    }
        try:
            lectura = instancia_bacnet.readMultiple('', request_dict=_rpm)
        except NoResponseFromController:
            print(f'[!] Error en la lectura de datos')
            return 
        except Timeout:
            print(f'[!] Error en la lectura de datos')
            return
        
        #print(lectura)
        #print(local_data.dicc)
        if lectura != ['']:
            local_data.estado_on_off = lectura[local_data.dicc[2]][0][1]
            local_data.estado_velocidad = lectura[local_data.dicc[4]][0][1]
            local_data.temperatura = lectura[local_data.dicc[6]][0][1]
            local_data.error = lectura[local_data.dicc[7]][0][1]
            local_data.setpoint = lectura[local_data.dicc[8]][0][1]
            
            local_data.datos_equipo = {
                        'estado_on_off': local_data.estado_on_off,
                        'estado_velocidad': local_data.estado_velocidad,
                        'temperatura': local_data.temperatura,
                        'error': local_data.error,
                        'setpoint': local_data.setpoint
                    }
        else:
            local_data.datos_equipo = {
                        'estado_on_off': 0,
                        'estado_velocidad': 0,
                        'temperatura': 0,
                        'error': 0,
                        'setpoint': 0
                    }
            
    #print(f'{local_data.id_equipo} : {local_data.puntos[0][5]} : {local_data.puntos[0][7]} {local_data.datos_equipo}')
    return local_data.datos_equipo

def almacenar_datos_equipo(id_equipo, resultados):
    # Obtiene el resultado de leer los datos del equipo con id_equipo
    local_data.resultado = leer_datos_equipo(local_data, id_equipo)

    # Almacena el resultado en el diccionario resultados
    if local_data.resultado:
        resultados[id_equipo] = local_data.resultado

def obtener_datos_equipos():
    resultados = {}
    hilos = []

    # Crea un hilo por equipo
    for id_equipo in range(id_equipo_inicio, id_equipo_fin + 1):
        hilo = threading.Thread(target=almacenar_datos_equipo, args=(id_equipo, resultados), daemon=True)
        hilos.append(hilo)
        hilo.start()

    # Asegura que todos los hilos terminen antes de continuar
    for hilo in hilos:
        hilo.join()

    return resultados

def iniciar_servidor():
    IP = "" # "": IP de la máquina local
    PORT = 501 # 502: puerto habitual para el protocolo Modbus 

    # Iniciar un servidor Modbus TCP
    StartTcpServer(context=context, identity=identity, address=(IP, PORT))

def configurar_servidor():
    # Unit ID o ID del único esclavo en el servidor: 0x0A
    slaves  = {
                0x0A: ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0]*65536), zero_mode=True)
            }
    
    # single = False para más de un esclavo. O para un solo esclavo con unit ID distinta de 0x01
    global context
    context = ModbusServerContext(slaves=slaves, single=False)

    # Información del servidor (está vacía)
    global identity  
    identity = ModbusDeviceIdentification()

def mapear_a_modbus(datos_equipos, context):
    address_counter = 1  # Dirección de inicio para los registros holding de lectura
    for id_equipo in sorted(datos_equipos.keys()):
        datos = datos_equipos[id_equipo]
        mapeo_lectura_velocidad = {0: 0, 1: 1, 2: 3, 3: 2}

        rlectura_on_off = 1 if datos['estado_on_off'] == 'active' else 0
        rlectura_velocidad = mapeo_lectura_velocidad.get(int(datos['estado_velocidad']))
        rlectura_temperatura = int(round(datos['temperatura'], 2)*10)
        rlectura_setpoint = int(round(datos['setpoint'], 2)*10)
        rlectura_error = 0 if datos['error'] == 1 else datos['error']

        # print(f'{rlectura_on_off} {rlectura_velocidad} {rlectura_temperatura} {rlectura_setpoint}')

        context[0xA].setValues(3, address_counter, [rlectura_on_off])
        #print(f"Actualizado holding register en {address_counter} con valor {rlectura_on_off}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [rlectura_velocidad])
        #print(f"Actualizado holding register en {address_counter} con valor {rlectura_velocidad}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [rlectura_setpoint])
        #print(f"Actualizado holding register en {address_counter} con valor {rlectura_setpoint}")
        address_counter += 1

        context[0xA].setValues(3, address_counter, [rlectura_temperatura])
        #print(f"Actualizado holding register en {address_counter} con valor {rlectura_temperatura}")
        address_counter += 1

        context[0XA].setValues(3, address_counter, [rlectura_error])
        #print(f"Actualizado holding register en {address_counter} con valor {rlectura_error}")
        address_counter += 1


def manejar_escritura_modbus(context):
    address_counter = 0xA000  # Dirección inicial para registros Modbus
    inicializados = set()  # Usar un conjunto para registros inicializados
    
    # Filtrar y almacenar los puntos de control (tipos de señal 1, 3 y 8)
    puntos_control = []
    for sede, equipos in datos_json.items():
        for equipo_id, puntos in equipos.items():
            for punto in puntos:
                if punto[11] in (1, 3, 8):  # Solo incluir tipos de señal 1, 3 y 8
                    puntos_control.append(punto)

    # print(puntos_control)

    for offset, punto in enumerate(puntos_control):  # Iterar sobre los puntos de control
            address = address_counter + offset  # Calcular la dirección Modbus
            # Leer el valor actual desde el contexto Modbus
            if offset % 3 == 0:
                context[0xA].setValues(3, address, [2])

    while True:
        for offset, punto in enumerate(puntos_control):  # Iterar sobre los puntos de control
            address = address_counter + offset  # Calcular la dirección Modbus

            value = context[0xA].getValues(3, address, count=1)[0]
            #print(address)
            #print(value)
            # Obtener los detalles del punto de control
            ip = punto[2]  # IP
            object_type = punto[10]  # Object Type (BACnet)
            object_id = punto[9]  # Object ID (BACnet)
            tipo_senal = punto[11]  # Tipo señal

            # Determinar el valor presente según el tipo de señal
            if tipo_senal == 1:  # binaryOutput (estado on/off)
                mapeo_escritura_on_off = {0: "inactive", 1: "active", 2: "None"}
                present_value = mapeo_escritura_on_off.get(value)
            elif tipo_senal == 3:  # multiStateOutput (velocidad)
                mapeo_escritura_velocidad = {0: 0, 1: 1, 2: 3, 3: 2, 4: 1}
                present_value = mapeo_escritura_velocidad.get(value)
            elif tipo_senal == 8:  # analogValue (setpoint)
                present_value = value / 10.0

            # Generar el f-string dinámicamente
            f_string = f"{ip} {object_type} {object_id} presentValue {present_value}"

            if present_value != ("None" if tipo_senal == 1 else 0):  # No se manda a comandar si el valor presente es 0 o None
                inicializados.add(address)

                print(f'[+] Escritura realizada: {f_string}')
                instancia_bacnet.write(f_string)
                # Volver a los valores por defecto para los registros de escritura (2 para on/off y 0 para velocidad y setpoint)
                if offset % 3 == 0:
                    context[0xA].setValues(3, address, [2])
                else:
                    context[0xA].setValues(3, address, [0])
            
        time.sleep(2)  # Esperar antes de la siguiente iteración
    
if __name__ == '__main__':
    
    # Crear instancia BACnet
    instancia_bacnet = BAC0.connect(port=47813)
    
    # Configurar el servidor Modbus
    configurar_servidor()

    # Iniciar el servidor Modbus en un hilo
    hilo_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo_servidor.start()
    
    # Iniciar el manejo de escrituras en un hilo
    hilo_escrituras = threading.Thread(target=manejar_escritura_modbus, args=(context,), daemon=True)
    hilo_escrituras.start()
    
    try:
        while(True):
            # Obtener datos de los equipos
            datos_equipos = obtener_datos_equipos()

            # Los datos se adaptan a un formato soportado por los registros holding de Modbus
            mapear_a_modbus(datos_equipos, context)    
            print('Mapeo realizado')
            time.sleep(10)
    except KeyboardInterrupt:
        print(f'[!] Servidor detenido')
        