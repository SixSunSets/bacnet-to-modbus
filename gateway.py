import BAC0

bacnet = BAC0.lite(ip="10.84.0.66/24", port=47812)

device_addresses = ["10.84.67.185"]

for address in device_addresses:
    try:
        device_info = bacnet.read(f"{address} device")  
        print(f"Device Info from {address}: {device_info}")
    except Exception as e:
        print(f"Error al leer el dispositivo en {address}: {e}")