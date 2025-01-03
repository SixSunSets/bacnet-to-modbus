import pandas as pd
from pyModbusTCP.client import ModbusClient

def leer_registro(c, registros):
    resultados = {}
    for registro in registros:
        address = int(registro['Register number'], 16)  # Convertir a decimal
        # Lee el registro de retención (holding register)
        regs = c.read_holding_registers(address, 1)
        
        if regs:
            equipo_id = registro['ID']
            if equipo_id not in resultados:
                resultados[equipo_id] = {
                    'SEDE': registro['Sede equipo'],
                    'MARCA': registro['Marca equipo'],
                    'NOMBRE': registro['Nombre equipo'],
                    'ESTADO': None,
                    'VELOCIDAD': None,
                    'TEMPERATURA': None,
                    'SETPOINT': None,
                    'ERROR': None
                }
            
            if registro['Register type'] == 0:
                resultados[equipo_id]['ESTADO'] = regs[0]
            elif registro['Register type'] == 1:
                resultados[equipo_id]['VELOCIDAD'] = regs[0]
            elif registro['Register type'] == 2:
                resultados[equipo_id]['SETPOINT'] = regs[0]
            elif registro['Register type'] == 3:
                resultados[equipo_id]['TEMPERATURA'] = regs[0]
            elif registro['Register type'] == 4:
                resultados[equipo_id]['ERROR'] = regs[0]
            
            print(f"Registro leído en {registro['Register number']}: {regs[0]}")
        else:
            print(f"Error al leer el registro en {registro['Register number']}. Respuesta: None")
    
    return list(resultados.values())

def forma():
    """
    {
    'SEDE': 
    'MARCA': 
    'NOMBRE': 
    'ESTADO': 
    'VELOCIDAD':
    'TEMPERATURA': 
    'SETPOINT': 
    'ERROR': 
    }
    """
    pass

# Leer los datos desde el archivo Excel
excel_path = 'C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Registros.xlsx'
df = pd.read_excel(excel_path)

# Contar el número de equipos
numero_equipos = 18

# Convertir el DataFrame a una lista de diccionarios
registros = df.to_dict(orient='records')

# Configurar el cliente Modbus
host = '10.84.67.185'
port = 502
unit_id = 10
c = ModbusClient(host=host, port=port, unit_id=unit_id)

# Conéctate al servidor
if c.open():
    print("Conexión al servidor Modbus exitosa")
    
    # Leer registros agrupados por equipo
    resultados = []
    for id_equipo in range(1, numero_equipos + 1):
        registros_equipo = [r for r in registros if r['ID'] == id_equipo]
        resultado = leer_registro(c, registros_equipo)
        resultados.extend(resultado)
    
    print("Resultados:", resultados)
    
    # Cierra la conexión
    c.close()
else:
    print("Error al conectar con el servidor Modbus")