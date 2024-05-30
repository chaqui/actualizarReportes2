import os
import click
import pymysql
from dotenv import load_dotenv, find_dotenv
import json
import uuid
load_dotenv(find_dotenv())

raiz ="dictamenes/"

@click.group()
def cli():
    #esta funcion solamente funciona para agrupar los comandos
    pass

def crear_conexion():
    host = os.getenv("HOST")
    user = os.getenv("USER_DB")
    passwd = os.getenv("PASSWORD")
    db = os.getenv("DATABASE")
    port = os.getenv("PORT")
    return pymysql.connect(host =host, user= user, passwd=passwd, db=db,port=int(port) )

def obtener_conexion():
    mi_conexion = crear_conexion()
    return mi_conexion.cursor()

def crear_directorio(nombre):
    directorio = raiz + nombre
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    return directorio

def crear_data( data, directorio):
    directorio = directorio + "/data.json"
    archivo_data = open(directorio,'w')
    archivo_data.writelines(json.dumps(data))

def guardar_plantilla_interna(plantilla, directorio, archivo, isJson = False):
    directorio = directorio + "/"+archivo
    archivo_data = open(directorio,'w')
    if(type(plantilla) == dict):
        archivo_data.writelines(json.dumps(plantilla))
    else:
        archivo_data.writelines(str(plantilla))

def leer_data(directorio):
    directorio = directorio + "/data.json"
    with open(directorio) as file:
        return json.load(file)
    
def consultar_dictamen(codigo_dictamen):
    consulta = "SELECT td.id, td.codigo_tipo_dictamen, td.id_version_proceso  FROM bpm_procesos.tipos_dictamen td WHERE td.codigo_tipo_dictamen ='"+codigo_dictamen+"'"
    cursor = obtener_conexion()
    cursor.execute(consulta)
    return list(cursor.fetchall())

def copiar_data(directorio):
    directorio_raiz = raiz + "plantilla/"
    os.system("cp -r "+directorio_raiz+" "+directorio)

def obtener_plantilla(directorio, archivo):
    directorio = directorio+"/"+archivo
    with open(directorio) as file:
        return file.read()

def colocar_caracteres_especiales(texto):
    return texto.replace('\"', '\\\"').replace("\n", "")


@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def generar_plantilla(codigo_dictamen):
    print("Generando plantilla")
    print("Version del proceso: ", codigo_dictamen)
    dictamen = consultar_dictamen(codigo_dictamen)
    if(len(dictamen) == 0):
        print("No existe el dictamen")
        return
    dictamen = dictamen[0]
    print(dictamen)
    directorio = crear_directorio(codigo_dictamen)
    crear_data(dictamen, directorio)
    copiar_data(directorio)
    
    print("Plantilla generada")
    
@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def build_plantilla(codigo_dictamen):
    print("Generando plantilla")
    print("Version del proceso: ", codigo_dictamen)
    directorio = raiz + codigo_dictamen
    with open(directorio+"/plantilla.json") as file:
        plantilla = json.load(file)
        keys = plantilla[0].keys()
        for key in keys:
            if(plantilla[0][key] != ""):
                continue
            dato = input("Ingrese el valor para "+key+": ")
            plantilla[0][key] = dato
        
        if(len(plantilla) > 1 and plantilla[1]):
            plantilla[1]["header"] = colocar_caracteres_especiales( obtener_plantilla(directorio, "header.html"))
        else:
            plantilla.append({"header":colocar_caracteres_especiales(obtener_plantilla(directorio, "header.html"))})    
        if(len(plantilla) > 2 and plantilla[2]):
              plantilla[2]["plantilla"] = colocar_caracteres_especiales(obtener_plantilla(directorio, "body.html"))
        else:
            plantilla.append({"plantilla":colocar_caracteres_especiales(obtener_plantilla(directorio, "body.html"))})
        if(len(plantilla) > 3 and plantilla[3]):
            plantilla[3]["plantilla_desfavorable"] = colocar_caracteres_especiales(obtener_plantilla(directorio, "desfavorable.html"))
        else:
            plantilla.append({"plantilla_desfavorable":colocar_caracteres_especiales(obtener_plantilla(directorio, "desfavorable.html"))})

       
        guardar_plantilla_interna(json.dumps(plantilla), directorio, "plantilla.json")   
        
@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def reset_plantilla(codigo_dictamen):
    directorio = raiz + codigo_dictamen
    with open(directorio+"/plantilla.json") as file:
        plantilla = json.load(file)
        keys = plantilla[0].keys()
        for key in keys:
            plantilla[0][key] = ""
        del plantilla[1] 
        del plantilla[2]
        file2 = open(directorio+"/plantilla.json",'w')
        file2.writelines(json.dumps(plantilla))
def generar_select(plantilla, data):
    return ("INSERT INTO bpm_procesos.plantilla_dictamen (id, id_version_proceso, id_tipo_dictamen, nombre_dictamen, plantilla_dictamen, created_at, updated_at,updated_user, created_user) "
            "VALUES ('"+data[3]+"','"+str(data[2])+"','"+str(data[0])+"','"+str(data[4])+"','"+plantilla+"',now(),now(),'josue.fuentes','josue.fuentes')")
def realizar_insert(plantilla, data):
    insert = generar_select(plantilla, data)
    print(insert)
    cursor = obtener_conexion()
    cursor.execute(insert)
    cursor.execute("COMMIT")
    cursor.close()
def update_plantilla(plantilla,data):
    print("Actualizando plantilla")
    update = ("UPDATE bpm_procesos.plantilla_dictamen SET plantilla_dictamen = '"+plantilla+"', updated_at = now(), updated_user ='josue.fuentes' WHERE id = '"+data[3]+"'")
    print(update)
    cursor = obtener_conexion()
    cursor.execute(update)
    cursor.execute("COMMIT")
    cursor.close()
def verificar_existencia_plantilla(data):
    consulta = "SELECT * FROM bpm_procesos.plantilla_dictamen WHERE id = '"+str(data[3])+"'"
    cursor = obtener_conexion()
    cursor.execute(consulta)
    return len(cursor.fetchall()) > 0

def generar_uuid():
    uuid_plantilla = str(uuid.uuid4())
    return uuid_plantilla.replace("-","")[0:25] 

@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def guardar_plantilla(codigo_dictamen):
    directorio = raiz + codigo_dictamen
    data = leer_data(directorio)
    plantilla = obtener_plantilla(directorio, "plantilla.json")
    if(len(data) < 4):
        data.append(generar_uuid())
        crear_data(data, directorio)   
        print("data actualizada con el id de la plantilla")
    if(verificar_existencia_plantilla(data)):
        update_plantilla(plantilla, data)
    else:
        if(len(data) < 5):
            nombre_dictamen = input("Ingrese el nombre del dictamen: ")
            data.append(nombre_dictamen)
            crear_data(data, directorio)  
            print("data actualizada con nombre del dictamen") 
        realizar_insert(plantilla, data)
    print("Plantilla guardada")

@cli.command()
def generar_scripts():
    script =""
    files = os.listdir(raiz)
    for file in files:
        if os.path.isdir(raiz+file):
            if(file == "scripts" or file == "plantilla"):
                continue
            directorio = raiz + file
            data = leer_data(directorio)
            plantilla = obtener_plantilla(directorio, "plantilla.json")
            consulta = generar_select(plantilla, data)
            script = script + consulta + ";\n"
    directorio_script = raiz+"scripts"
    crear_directorio("scripts")
    guardar_plantilla_interna(script, directorio_script, "script.sql")
    
@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def obtener_data(codigo_dictamen):
    directorio = raiz + codigo_dictamen
    dictamen = consultar_dictamen(codigo_dictamen)
    if(len(dictamen) == 0):
        print("No existe el dictamen")
        return
    dictamen = dictamen[0]
    crear_data(dictamen, directorio)
    

if __name__ == '__main__':
    cli()
