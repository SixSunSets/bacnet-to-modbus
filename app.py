from flask import Flask
from flask_socketio import SocketIO
import threading
import time
from flask_cors import CORS
import lectura_modbus as lm
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

local_data = threading.local()

@app.route('/')
def actualizar_fila(row_id):
    while True:
        try:
            local_data.registros = lm.leer_registro(row_id, local_data)
            #print({'row_id': row_id, 'values': local_data.registros})
            socketio.emit('update_row', {'row_id': row_id, 'values': local_data.registros})
        except NameError:
            print(f"[-] Error: {row_id} {NameError}")
        time.sleep(100) # Aumentar el tiempo de espera para más equipos

def escritura_unica_controlada(datos, local_data):
    # Emitir un evento de actualización después de la escritura
    escritura_exitosa = False
    while(escritura_exitosa == False):
        row_id = datos["id_equipo"]
        print(f"[!] Intentando actualizar fila {row_id} con valores {datos['comando_on_off']}, {datos['comando_ventilador']}, {datos['comando_setpoint']}")
        lm.escritura_unica(datos, local_data)
        time.sleep(5)
        local_data.registros = lm.leer_registro(row_id, local_data)
        escritura_exitosa = datos["comando_on_off"] == local_data.registros["ESTADO"] and datos["comando_ventilador"] == local_data.registros["VELOCIDAD"] and int(datos["comando_setpoint"]) == local_data.registros["SETPOINT"]
    socketio.emit('update_row', {'row_id': row_id, 'values': local_data.registros})
    print(f"[+] Actualización exitosa de fila {row_id} con valores {local_data.registros}")
    # Emitir un mensaje de éxito "Fila actualizada"
       
@socketio.on('control_equipo')
def handle_update_row(data):
    local_data.datos = json.loads(data)
    print(local_data.datos)
    escritura_unica_controlada(local_data.datos, local_data)
    socketio.emit('backend_message', {'message': f'Equipo #{local_data.datos["id_equipo"]} controlado correctamente'})

@socketio.on('control_grupal')
def handle_update_rows(data):
    local_data.datos = json.loads(data)
    print(local_data.datos)
    for id_equipo in local_data.datos["ids_equipos"]:
        datos = {"id_equipo":id_equipo,"comando_on_off":local_data.datos["comando_on_off"],"comando_ventilador":local_data.datos["comando_ventilador"],"comando_setpoint":local_data.datos["comando_setpoint"]}
        threading.Thread(target=escritura_unica_controlada,args=(datos, local_data),daemon=True).start()
        #if id_equipo == local_data.datos["ids_equipos"][-1]:
        #    socketio.emit('backend_message', {'message': f'Equipos #{",".join(map(str, local_data.datos["ids_equipos"]))} controlados correctamente'})
    
if __name__ == '__main__':
    numero_equipos = 190

    for row_id in range(1,numero_equipos+1):
        threading.Thread(target=actualizar_fila,args=(row_id,),daemon=True).start()

    # Inicia un hilo para actualizar las filas
    socketio.run(app)