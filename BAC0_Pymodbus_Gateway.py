import pymodbus
import BAC0
import threading
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import time

class ServidorModbus:
    def __init__(self, ip, puerto):
        self.ip = ip
        self.puerto = puerto
        self.context = None
        self.servidor = None

    def iniciar_servidor_modbus(self):
        def inicializar_registros():
            store = ModbusSlaveContext(hr=ModbusSequentialDataBlock.create(), zero_mode=True)
            self.context = ModbusServerContext(slaves=store, single=True)
            identity = ModbusDeviceIdentification()
            print(f'[+] Servidor Modbus TCP iniciado en (IP = {self.ip}, PUERTO = {self.puerto})')
            StartTcpServer(context=self.context, identity=identity, address=(self.ip, self.puerto))
            
        self.servidor = threading.Thread(target=inicializar_registros, daemon=True).start()

class ClienteBacnet:
    def __init__(self, puerto):
        self.puerto = puerto
        self.cliente = None

    def iniciar_cliente_bacnet(self):
        print(f'[+] Conectando al servidor BACnet en PUERTO = {self.puerto}')
        self.cliente = BAC0.connect(port = self.puerto)

if __name__ == '__main__':
    instancia_bacnet = ClienteBacnet(47813)
    instancia_bacnet.iniciar_cliente_bacnet()
    instancia_modbus = ServidorModbus('localhost', 5020)
    instancia_modbus.iniciar_servidor_modbus()

    # Probando el acceso al contexto del servidor Modbus
    #address_counter = 0
    #estado = 1
    #instancia_modbus.context[0].setValues(3, address_counter, [estado])
    #print(f"Actualizado holding register en {address_counter} con valor {estado}")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("[-] Servidor Modbus TCP detenido")