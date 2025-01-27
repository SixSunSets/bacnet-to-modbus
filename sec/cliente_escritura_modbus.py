from pyModbusTCP.client import ModbusClient

def escribir_registro_modbus(host, port, unit_id, direccion_hex):
    # Configura la dirección IP, el puerto del servidor Modbus y el Unit ID
    c = ModbusClient(host=host, port=port, unit_id=unit_id)
    
    # Conéctate al servidor
    if c.open():
        print("Conexión al servidor Modbus exitosa")
        
        address = int(direccion_hex, 16)  # Convertir a decimal
        # Escribe el registro de retención (holding register)
        regs = c.write_single_register(address, 2)  # address: velocidad del ventilador / 1=baja, 2=media, 3=alta
        #regs = c.write_single_coil(address, 1)  # address: estado del equipo / 1=encendido, 0=apagado
        if regs:
            print(f"Escritura exitosa de holding register en {direccion_hex}")
        else:  
            print(f"Error al escribir el holding register en {direccion_hex}. Respuesta: None")
        # Cierra la conexión
        c.close()
    else:
        print("Error al conectar con el servidor Modbus")
        return None

# Ejemplo de uso
host = 'localhost'#10.84.35.185
port = 502
unit_id = 10
direccion_hex = "0xA001" #0x0101= estado, 0x0101= velocidad, 0x0102: Setpoint, 0x0105: Temperatura

escribir_registro_modbus(host, port, unit_id, direccion_hex)

