import BAC0

bacnet = BAC0.connect(port=47811)

def crear_instancia_bacnet():
    try:
        bacnet = BAC0.connect(port=47809)
    except:
        bacnet = None
    return bacnet

def descubrir_puntos_bacnet(ip):
    tabla = bacnet.readMultiple(f'{ip} device 1001 all')
