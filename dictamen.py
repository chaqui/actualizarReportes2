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
    print(host)
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

def crear_data( dictamen, directorio):
    directorio = directorio + "/data.json"
    archivo_data = open(directorio,'w')
    archivo_data.writelines(json.dumps(dictamen))

def guardar_plantilla_interna(plantilla, directorio, archivo, isJson = False):
    directorio = directorio + "/"+archivo
    archivo_data = open(directorio,'w')
    if(isJson):
        archivo_data.writelines(json.dumps(plantilla))
    else:
        archivo_data.writelines(plantilla)

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

def colocar_caracteres_especiales(texto):
    return texto.replace('"', '/"')

def obtener_plantilla(directorio, archivo):
    directorio = directorio+"/"+archivo
    with open(directorio) as file:
        return colocar_caracteres_especiales(file.read())

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
            dato = input("Ingrese el valor para "+key+": ")
            plantilla[0][key] = dato
       
        plantilla.append({"plantilla":obtener_plantilla(directorio, "body.html")})
        plantilla.append({"header":obtener_plantilla(directorio, "header.html")})    
        guardar_plantilla(plantilla, directorio, "plantilla.json")   
        
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
    return ("INSERT INTO bpm_procesos.tipos_dictamen (id, id_version_proceso, id_tipo_dictamen, nombre_dictamen, plantilla_dictamen, created_at, updated_at,updated_user, created_user) "
            "VALUES ('"+data[3]+"',"+str(data[2])+","+str(data[0])+",'"+str(data[4])+"','"+plantilla+"',now(),now(),'josue.fuentes','josue.fuentes')")
def realizar_insert(plantilla, data):
    insert = generar_select(plantilla, data)
    cursor = obtener_conexion()
    print(insert)
    cursor.execute(insert)

def update_plantilla(plantilla,data):
    update = ("UPDATE bpm_procesos.tipos_dictamen SET plantilla_dictamen = '"+plantilla+"', updated_at = now(), updated_user ='josue.fuentes' WHERE id = '"+data[4]+"'")
    cursor = obtener_conexion()
    print(update)
    cursor.execute(update)

def verificar_existencia_plantilla(data):
    consulta = "SELECT * FROM bpm_procesos.tipos_dictamen WHERE id = "+str(data[4])
    cursor = obtener_conexion()
    cursor.execute(consulta)
    return len(cursor.fetchall()) > 0

@cli.command()
@click.option('--codigo_dictamen', help='version proceso a ejecutar')
def guardar_plantilla(codigo_dictamen):
    directorio = raiz + codigo_dictamen
    data = leer_data(directorio)
    plantilla = obtener_plantilla(directorio, "plantilla.json")
    if(len(data) < 4):
        uuid_plantilla = str(uuid.uuid4())
        uuid_plantilla = uuid_plantilla.replace("-","")[0:25] 
        data.append(uuid_plantilla)
        guardar_plantilla_interna(data, directorio, "data.json",True)   
        print("data actualizada con el id de la plantilla")
    if(verificar_existencia_plantilla(data)):
        update_plantilla(plantilla, data)
    else:
        if(len(data) < 5):
            nombre_dictamen = input("Ingrese el nombre del dictamen: ")
            data.append(nombre_dictamen)
            guardar_plantilla_interna(data, directorio, "data.json",True)  
            print("data actualizada con nombre del dictamen") 
        realizar_insert(plantilla, data)
    print("Plantilla guardada")

@cli.command()
def generar_scripts():
    files = os.listdir(raiz)
    for file in files:
        if os.path.isdir(raiz+file):
            if(file == "scripts"):
                continue
            directorio = raiz + file
            data = leer_data(directorio)
            plantilla = obtener_plantilla(directorio, "plantilla.json")
            consulta = generar_select(plantilla, data)
            guardar_plantilla_interna(consulta, raiz+"scripts", "script.sql")
    
        
        
    

if __name__ == '__main__':
    cli()
