import pandas as pd
from pyModbusTCP.client import ModbusClient

# Leer los datos desde el archivo Excel
excel_path = 'Lista_de_Registros.xlsx'
df = pd.read_excel(excel_path)

# Convertir el DataFrame a una lista de diccionarios
registros = df.to_dict(orient='records')

# Configurar el cliente Modbus
PORT = 502
UNIT_ID = 10
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
                regs = c.read_coils(address, 1)
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
                if registro['Register type'] == 2:
                    local_data.dato['SETPOINT'] = round(float(regs[0]), 2)
                if registro['Register type'] == 3:
                    local_data.dato['TEMPERATURA'] = round(float(regs[0]), 2)
                if registro['Register type'] == 4:
                    local_data.dato['ERROR'] = regs[0]
                
                #print(f"Registro leído en {registro['Register number']}: {regs[0]}")
            else:
                print(f"Error al leer el registro en {registro['Register number']}. Respuesta: None")
        except Exception as e:
            print(f"Error al leer el registro en {registro['Register number']}: {e}")
        finally:
            c.close()
    
    return local_data.dato

