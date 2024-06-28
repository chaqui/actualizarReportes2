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
    if(consulta.find("SELECT") == -1):
        cursor.connection.commit()
    cursor.close()
    return resultado

def obtener_listado_version_procesos(codigo_proceso):
    consulta = generar_consulta(codigo_proceso)
    listado_procesos = ejecutar_consulta(consulta)
    procesos = []
    for proceso in listado_procesos:
        k =validar_mas_reciente(procesos, proceso) 
        if(k!= -1):
            procesos[k] = {
                "id_version_proceso": proceso[0],
                "codigo_version_proceso": proceso[1],
                "id_proceso": proceso[2]
            }
        else:
            procesos.append({
                "id_version_proceso": proceso[0],
                "codigo_version_proceso": proceso[1],
                "id_proceso": proceso[2]
            })

    return procesos

def validar_mas_reciente(procesos, proceso):
    for k, p in enumerate(procesos):
        codigo_version_proceso_anterior = p["codigo_version_proceso"]
        if(codigo_version_proceso_anterior.find(proceso[1][:-3]) != -1):
            version_nueva = int(proceso[1][-1:])
            print(version_nueva)
            version_anterior = int(codigo_version_proceso_anterior[-1:])
            print(version_anterior)
            if(version_nueva > version_anterior):
                return k
    return -1
            
@click.group()
def cli():
    #esta funcion solamente funciona para agrupar los comandos
    pass

@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a consultar')
def consultar_version_proceso(codigo_proceso):
    respuesta =input("Desea ejecutar este comando, se borra toda la data, (y) si, (n) no")
    if(respuesta == "y"):
        version_procesos= obtener_listado_version_procesos(codigo_proceso)
        directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
        crear_directorio(directorio)
        archivo_listado = "listado.json"
        guardar_plantilla_interna(version_procesos,directorio,archivo_listado,True)
        archivo_plantilla = "plantilla.html"
        guardar_plantilla_interna("",directorio,archivo_plantilla)
        archivo_header = "header.html"
        guardar_plantilla_interna("",directorio,archivo_header)
    
def generar_insert_plantilla(proceso, plantilla, header):
    return "INSERT INTO bpm_procesos.plantilla_observacion_forma (id,  id_version_proceso, id_proceso, plantilla_dictamen, created_at, updated_at, updated_user, created_user, header) VALUES ('"+proceso["id_plantilla"]+"','"+proceso["id_version_proceso"]+"','"+proceso["id_proceso"]+"','"+plantilla+"',now(),now(),'josue.fuentes','josue.fuentes','"+header+"')"

def generar_update_plantilla(proceso, plantilla,header):
    return "UPDATE bpm_procesos.plantilla_observacion_forma SET plantilla_dictamen = '"+plantilla+"', header ='"+header+"', updated_at = now() WHERE id = '"+proceso["id_plantilla"]+"'"

def generar_select_plantiolla(proceso):
    return "SELECT * FROM bpm_procesos.plantilla_observacion_forma WHERE id = '"+proceso["id_plantilla"]+"'"

def validar_existencia_plantilla(proceso):
    print("\033[;36m"+proceso["codigo_version_proceso"]+ " validando")
    consulta = generar_select_plantiolla(proceso)
    resultado = ejecutar_consulta(consulta)
    return len(resultado) > 0

def update_plantilla(proceso, plantilla,header):
    print("\x1b[1;33m"+proceso["codigo_version_proceso"]+ " actualizando")
    update = generar_update_plantilla(proceso, plantilla,header)
    ejecutar_consulta(update)
    print("\x1b[1;33m"+proceso["codigo_version_proceso"]+ " actualizado")
    
def insert_plantilla(proceso, plantilla, header):
    print(proceso["codigo_version_proceso"]+ " no insertado")
    insert = generar_insert_plantilla(proceso, plantilla, header)
    ejecutar_consulta(insert)
    print(proceso["codigo_version_proceso"]+" insertado")

def getPlantilla(directorio, version_proceso, archivo):
    directorio_proceso = directorio + version_proceso + "/"
    if(os.path.exists(directorio_proceso)):
        return obtener_plantilla(directorio_proceso, archivo)
    return obtener_plantilla(directorio, archivo)

@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a guardar')
def guardar_plantilla_proceso(codigo_proceso): 
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    version_procesos =  json.loads(obtener_plantilla(directorio, "listado.json"))
    for version_proceso in version_procesos:
        plantilla = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "plantilla.html")
        header = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "header.html")
        if(not "id_plantilla" in version_proceso):
            version_proceso["id_plantilla"] =generar_uuid()
        if(validar_existencia_plantilla(version_proceso)):
            update_plantilla(version_proceso, plantilla, header)
        else:
            insert_plantilla(version_proceso, plantilla, header)
    guardar_plantilla_interna(version_procesos, directorio, "listado.json", True)       
    


            
@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a guardar')
def generar_scripts(codigo_proceso):
    script =""
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    version_procesos = json.loads(obtener_plantilla(directorio, "listado.json"))
    for version_proceso in version_procesos:
        plantilla = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "plantilla.html")
        header = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "header.html")
        if(not "id_plantilla" in version_proceso):
            continue
            #version_proceso["id_plantilla"] =generar_uuid()
        script += "-- "+version_proceso["codigo_version_proceso"]+" \n"
        script += generar_insert_plantilla(version_proceso, plantilla, header)
        script += ";"
        script += "\n \n"

    print(script)
    guardar_plantilla_interna(script, directorio, "script.sql")
    
def escribirArchivo(directorio, data):
    archivo_json = open(directorio+"/"+data[0]+".json",'w')
    archivo_json.writelines(data[1])
    archivo_json.close()

@cli.command()
@click.option('--id-observacion', help='id de la observacion a consultar')
def obtener_observaciones_campo(id_observacion):
    consulta = "SELECT id, observacion_campos  FROM bpm_procesos.observaciones_solicitudes where id = '"+id_observacion+"'"
    observaciones_campo = ejecutar_consulta(consulta)
    directorio = "./observaciones/observaciones_campo/"
    crear_directorio(directorio)
    escribirArchivo(directorio, observaciones_campo[0])

@cli.command()
@click.option('--codigo-proceso', help='codigo del proceso a guardar')
def generar_scripts_update(codigo_proceso):
    directorio = "./observaciones/version_procesos/"+codigo_proceso+"/"
    version_procesos = json.loads(obtener_plantilla(directorio, "listado.json"))
    script =""
    for version_proceso in version_procesos:
        plantilla = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "plantilla.html")
        header = getPlantilla(directorio, version_proceso["codigo_version_proceso"], "header.html")
        script += "-- "+version_proceso["codigo_version_proceso"]+" \n"
        script += generar_update_plantilla(version_proceso, plantilla, header)
        script += ";"
        script += "\n \n"

    print(script)
    guardar_plantilla_interna(script, directorio, "script-update.sql")
    
        
if __name__ == '__main__':
    cli()