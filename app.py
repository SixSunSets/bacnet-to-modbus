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
            print("Error: "+str(row_id)+" "+str(NameError))
        time.sleep(100) # Aumentar el tiempo de espera para más equipos
                         
@socketio.on('control_equipo')
def handle_update_row(data):
    local_data.datos = json.loads(data)
    print(local_data.datos)
    lm.escritura_unica(local_data.datos, local_data)
    
@socketio.on('control_grupal')
def handle_update_rows(data):
    local_data.datos = json.loads(data)
    print(local_data.datos)
    for id_equipo in local_data.datos["ids_equipos"]:
        local_data.datos = {"id_equipo":id_equipo,"comando_on_off":local_data.datos["comando_on_off"],"comando_ventilador":local_data.datos["comando_ventilador"],"comando_setpoint":local_data.datos["comando_setpoint"]}
        threading.Thread(target=lm.escritura_unica,args=(local_data.datos,local_data),daemon=True).start()

if __name__ == '__main__':
    numero_equipos = 190

    for row_id in range(1,numero_equipos+1):
        threading.Thread(target=actualizar_fila,args=(row_id,),daemon=True).start()

    # Inicia un hilo para actualizar las filas
    socketio.run(app)