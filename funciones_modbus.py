import pandas as pd
from pyModbusTCP.client import ModbusClient

# Leer los datos desde el archivo Excel
excel_path = 'Lista_de_Registros.xlsx'
df = pd.read_excel(excel_path)

# Convertir el DataFrame a una lista de diccionarios
registros = df.to_dict(orient='records')

# Configurar el cliente Modbus
PORT = 502 # 502
UNIT_ID = 10 # 10
#global c
#c = ModbusClient(host=host, port=port, unit_id=unit_id)

def leer_registro(id_equipo, local_data):
    local_data.dato = {
        'SEDE': None,
        'MARCA': None,
        'NOMBRE': None,
        'ESTADO': None,
        'VELOCIDAD': None,
        'TEMPERATURA': None,
        'SETPOINT': None,
        'ERROR': None
    }
    registros_equipo = [r for r in registros if r['ID'] == id_equipo]
    for registro in registros_equipo:
        host = registro['IP']  # IP del equipo
        address = int(registro['Register number'], 16)  # Convertir a decimal
        try:
            # Lee el registro de retención (holding register)
            c = ModbusClient(host=host, port=PORT, unit_id=UNIT_ID)
            if registro['Register type'] == 0:
                if registro['Marca equipo'] == 'LG':
                    regs = c.read_coils(address, 1)
                if registro['Marca equipo'] == 'Daikin':
                    regs = c.read_holding_registers(address, 1)
            else:
                regs = c.read_holding_registers(address, 1)
            if regs:
                local_data.dato['SEDE'] = registro['Sede equipo']
                local_data.dato['MARCA'] = registro['Marca equipo']
                local_data.dato['NOMBRE'] = registro['Nombre equipo']
                
                if registro['Register type'] == 0:
                    if regs[0] == 0:
                        local_data.dato['ESTADO'] = 'Apagado'
                    elif regs[0] == 1:
                        local_data.dato['ESTADO'] = 'Encendido'
                    else:
                        local_data.dato['ESTADO'] = 'Undefined'
                if registro['Register type'] == 1:
                    if registro['Marca equipo'] == 'LG':
                        if regs[0] == 0:
                            local_data.dato['VELOCIDAD'] = 'Undefined'
                        elif regs[0] == 1:
                            local_data.dato['VELOCIDAD'] = 'Baja'
                        elif regs[0] == 2:
                            local_data.dato['VELOCIDAD'] = 'Media'
                        elif regs[0] == 3:
                            local_data.dato['VELOCIDAD'] = 'Alta'
                        elif regs[0] == 4:
                            local_data.dato['VELOCIDAD'] = 'Auto'
                    if registro['Marca equipo'] == 'Daikin':
                        if regs[0] == 1:
                            local_data.dato['VELOCIDAD'] = 'Baja'
                        elif regs[0] == 2:
                            local_data.dato['VELOCIDAD'] = 'Alta'
                        elif regs[0] == 3:
                            local_data.dato['VELOCIDAD'] = 'Media'
                if registro['Register type'] == 2:
                    if registro['Marca equipo'] == 'LG':
                        local_data.dato['SETPOINT'] = round(float(regs[0]), 2)
                    if registro['Marca equipo'] == 'Daikin':
                        local_data.dato['SETPOINT'] = round(float(regs[0])/10, 2)
                if registro['Register type'] == 3:
                    if registro['Marca equipo'] == 'LG':
                        local_data.dato['TEMPERATURA'] = round(float(regs[0]), 2)
                    if registro['Marca equipo'] == 'Daikin':
                        local_data.dato['TEMPERATURA'] = round(float(regs[0])/10, 2)
                if registro['Register type'] == 4:
                    local_data.dato['ERROR'] = regs[0]
                
                print(f"Registro leído en {registro['Register number']}: {regs[0]}")
            else:
                print(f"[-] Error al leer el registro en {registro['Register number']}. Respuesta: None")
        except Exception as e:
            print(f"[-] Error al leer el registro en {registro['Register number']}: {e}")
        finally:
            c.close()
    
    return local_data.dato

def escritura_unica(datos, local_data):
    local_data.id_equipo = datos["id_equipo"]
    local_data.comando_on_off = datos["comando_on_off"]
    local_data.comando_ventilador = datos["comando_ventilador"]
    local_data.comando_setpoint = int(datos["comando_setpoint"])

    on_off_map = {
        "Apagado": 0,
        "Encendido": 1
    }

    ventilador_map_lg = {
        "Undefined": 0,
        "Baja": 1,
        "Media": 2,
        "Alta": 3,
        "Auto": 4
    }

    ventilador_map_daikin = {
        "Baja": 1,
        "Alta": 2,
        "Media": 3,
    }

    registros_equipo = [r for r in registros if r['ID'] == local_data.id_equipo]

    # Convertir los valores de comando_on_off y comando_ventilador a números enteros
    local_data.comando_on_off = on_off_map.get(local_data.comando_on_off, local_data.comando_on_off)
    if registros_equipo[0]['Marca equipo'] == 'LG':
        local_data.comando_ventilador = ventilador_map_lg.get(local_data.comando_ventilador, local_data.comando_ventilador)
    if registros_equipo[0]['Marca equipo'] == 'Daikin':
        local_data.comando_ventilador = ventilador_map_daikin.get(local_data.comando_ventilador, local_data.comando_ventilador)


    if not registros_equipo:
        print(f"[-] No se encontraron registros para el equipo ID {local_data.id_equipo}")
        return

    # Usar la IP del primer registro para conectar el cliente
    host = registros_equipo[0]['IP']
    try:
        # Crear un único cliente Modbus
        c = ModbusClient(host=host, port=PORT, unit_id=UNIT_ID)
        if not c.open():
            print(f"[-] Error al conectar con el servidor Modbus en {host}:{PORT}")
            return 

        for registro in registros_equipo:
            address = int(registro['Register number'], 16)  # Convertir a decimal
            try:
                # Para los equipos LG, los registros modbus se usan tanto para lectura como escritura
                # -----------------------------------------
                # | Nombre       | Point-1 | Function Code | Register Type |
                # -----------------------------------------
                # | On/Off       | 0       | coil          | 0             |
                # | Velocidad    | 1       | holding register | 1          |
                # | Setpoint     | 2       | holding register | 2          |
                # | Temperatura  | 5       | holding register | 3          |
                # | Error        | 6       | holding register | 4          |
                # -----------------------------------------

                if registro['Marca equipo'] == 'LG':
                    if local_data.comando_on_off is not None and registro['Register type'] == 0:
                        result = c.write_single_coil(address, local_data.comando_on_off)
                        print(f"Escritura  de coil en {registro['Register number']}")

                    if local_data.comando_ventilador is not None and registro['Register type'] == 1:
                        result = c.write_single_register(address, local_data.comando_ventilador)
                        print(f"Escritura  de holding register en {registro['Register number']}")

                    if local_data.comando_setpoint is not None and registro['Register type'] == 2:
                        result = c.write_single_register(address, local_data.comando_setpoint)
                        print(f"Escritura  de holding register en {registro['Register number']}")
                
                # Para los equipos Daikin, nuestro intermediario, un servidor Modbus podría gestionar mejor la lectura y escritura usando registros dedicados a uno u otro
                # Ver la Lista de Registros 
                if registro['Marca equipo'] == 'Daikin':
                    if local_data.comando_on_off is not None and registro['Register type'] == 5:
                        result = c.write_single_register(address, local_data.comando_on_off)
                        print(f"Escritura  de holding register en {registro['Register number']}")

                    if local_data.comando_ventilador is not None and registro['Register type'] == 6:
                        result = c.write_single_register(address, local_data.comando_ventilador)
                        print(f"Escritura  de holding register en {registro['Register number']}")

                    if local_data.comando_setpoint is not None and registro['Register type'] == 7:
                        result = c.write_single_register(address, local_data.comando_setpoint)
                        print(f"Escritura  de holding register en {registro['Register number']}")
                    

            except Exception as e:
                print(f"[-] Error al escribir en {registro['Register number']}: {e}")

    except Exception as e:
        print(f"[-] Error al conectar con el servidor Modbus en {host}: {e}")
    finally:
        # Cerrar el cliente al final
        c.close()
