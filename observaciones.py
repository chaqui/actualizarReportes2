from init import obtener_conexion, crear_directorio
from dictamen import guardar_plantilla_interna, obtener_plantilla, generar_uuid
from dotenv import load_dotenv
import click
import json
import os
load_dotenv()

def generar_consulta(codigo_proceso):
    return "SELECT vp.id as id, vp.codigo_version as codigo_version, vp.id_proceso FROM bpm_procesos.version_procesos vp where  vp.codigo_version like '"+codigo_proceso+"%'"

def ejecutar_consulta(consulta):
    cursor = obtener_conexion()
    cursor.execute(consulta)
    resultado = cursor.fetchall()
    cursor.close()
    return resultado

def obtener_listado_version_procesos(codigo_proceso):
    consulta = generar_consulta(codigo_proceso)
    listado_procesos = ejecutar_consulta(consulta)
    procesos = []
    for proceso in listado_procesos:
        procesos.append({
            "id_version_proceso": proceso[0],
            "codigo_version_proceso": proceso[1],
            "id_proceso": proceso[2]
        })
    return procesos

@click.group()
def cli():
    #esta funcion solamente funciona para agrupar los comandos
    pass

@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a consultar')
def consultar_version_proceso(codigo_proceso):
    version_procesos= obtener_listado_version_procesos(codigo_proceso)
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    crear_directorio(directorio)
    archivo_listado = "listado.json"
    guardar_plantilla_interna(version_procesos,directorio,archivo_listado,True)
    archivo_plantilla = "plantilla.html"
    guardar_plantilla_interna("",directorio,archivo_plantilla)
    archivo_plantilla = "desfavorable.html"
    guardar_plantilla_interna("",directorio,archivo_plantilla)
    
def generar_insert_plantilla(proceso, plantilla):
    return "INSERT INTO bpm_procesos.plantilla_observacion_forma (id,  id_version_proceso, id_proceso, plantilla_dictamen, created_at, updated_at, updated_user, created_user) VALUES ('"+proceso["id_plantilla"]+"','"+proceso["id_version_proceso"]+"','"+proceso["id_proceso"]+"','"+plantilla+"',now(),now(),'josue.fuentes','josue.fuentes'"

def generar_update_plantilla(proceso, plantilla):
    return "UPDATE bpm_procesos.plantilla_observacion_forma SET plantilla_dictamen = '"+plantilla+"', updated_at = now() WHERE id = '"+proceso["id_plantilla"]+"'"

def generar_select_plantiolla(proceso):
    return "SELECT * FROM bpm_procesos.plantilla_observacion_forma WHERE id = '"+proceso["id_plantilla"]+"'"

def validar_existencia_plantilla(proceso):
    consulta = generar_select_plantiolla(proceso)
    resultado = ejecutar_consulta(consulta)
    return len(resultado) > 0

def update_plantilla(proceso, plantilla):
    update = generar_update_plantilla(proceso, plantilla)
    ejecutar_consulta(update)
    
def insert_plantilla(proceso, plantilla):
    insert = generar_insert_plantilla(proceso, plantilla)
    ejecutar_consulta(insert)


def get_plantilla(directorio, version_proceso, archivo):
    directorio_proceso = directorio + version_proceso + "/"
    if(os.path.exists(directorio_proceso)):
        return obtener_plantilla(directorio_proceso, archivo)
    return obtener_plantilla(directorio, archivo)

def generar_json_plantilla(version_procesos, directorio):
    plantilla = []
    for version_proceso in version_procesos:
        plantilla.append({
            "plantilla": get_plantilla(directorio, version_proceso, "plantilla.html"),
            "desfavorable": get_plantilla(directorio, version_proceso, "desfavorable.html")
        })
    return plantilla

def guardar_plantilla_proceso(codigo_proceso): 
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    version_procesos = obtener_plantilla(directorio, "listado.json")
    for version_proceso in version_procesos:
        plantilla = obtener_plantilla(directorio, version_proceso["codigo_version_proceso"])
        if(not "id_plantilla" in version_proceso):
            version_proceso["id_plantilla"] =generar_uuid()
        if(validar_existencia_plantilla(version_proceso)):
            update_plantilla(version_proceso, plantilla)
        else:
            insert_plantilla(version_proceso, plantilla)


            
@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a guardar')
def generar_scripts(codigo_proceso):
    script =""
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    version_procesos = json.loads(obtener_plantilla(directorio, "listado.json"))
    print(type(version_procesos))
    for version_proceso in version_procesos:
        plantilla = generar_json_plantilla( version_proceso["codigo_version_proceso"],directorio)
        if(not "id_plantilla" in version_proceso):
            continue
        script += "--- "+version_proceso["codigo_version_proceso"]+" \n"
        script += generar_insert_plantilla(version_proceso, plantilla)
        script += "\n \n"

    print(script)
    guardar_plantilla_interna(script, directorio, "script.sql")
        
        
if __name__ == '__main__':
    cli()