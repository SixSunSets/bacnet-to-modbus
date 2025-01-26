import openpyxl
import json

# Cargar el archivo Excel
arch_excel = r"C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.xlsx"
libro = openpyxl.load_workbook(arch_excel)
nombres_hojas = libro.sheetnames[0:1]  # :-1
print(nombres_hojas)

def excel_a_json():
    equipos_ac = dict()
    # Obtener las ids en un conjunto y luego convirtiendo a lista
    todas_las_ids = set()
    for hoja in nombres_hojas:
        tabla = libro[hoja]
        for fila in tabla.iter_rows(values_only=True):
            if isinstance(fila[1], int):
                todas_las_ids.add(fila[1])
    todas_las_ids = list(todas_las_ids)

    # Para todas las ids
    for id in todas_las_ids:
        # Dentro de las hojas especificas
        for hoja in nombres_hojas:
            tabla = libro[hoja]
            # Para cada equipo
            for fila in tabla.iter_rows(values_only=True):
                if fila[1] == id and fila[0] == "SI":
                    # Si la hoja no existe en el diccionario, se crea
                    if hoja not in equipos_ac:
                        equipos_ac[hoja] = {}

                    # Si el ID no existe dentro de la hoja se crea su lista
                    if id not in equipos_ac[hoja]:
                        equipos_ac[hoja][id] = []
                    equipos_ac[hoja][id].append(fila)

                    if len(equipos_ac[hoja][id]) == 8:
                        break

    # Guardar el json
    with open(r"C:/Users/User/Desktop/bacnet-to-modbus/Lista_de_Puntos_Daikin.json", "w") as archivo_json:
        json.dump(equipos_ac, archivo_json)

excel_a_json()
