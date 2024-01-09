import pymysql
import click
import tabulate
import os
import csv 
from dotenv import load_dotenv

load_dotenv()
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

def cerrar_conexion():
    mi_conexion = crear_conexion()
    mi_conexion.close()

def guardar_plantilla(nombre, data, directorio):
    print("guardar plantilla")
    nombre = data[1]+"-"+nombre
    print(nombre)
    if(directorio == None):
        directorio = nombre+".html"
    else:
        directorio = directorio+"/"+nombre+".html"
    
    archivo_plantilla = open(directorio,'w')
    if(data[0] != None):
        archivo_plantilla.writelines(data[0])
    archivo_plantilla.close()

def crear_directorio(nombre):
    if not os.path.exists(nombre):
        os.makedirs(nombre)


@click.group()
def cli():
    #esta funcion solamente funciona para agrupar los comandos
    pass

def obtener_plantilla_interno(proceso, directorio):
    print("Obteniendo plantilla")
    #obtener plantilla
    cursor = obtener_conexion()
    cursor.execute("SELECT plantilla_resolucion, codigo_version FROM bpm_procesos.version_procesos WHERE id = %s", (proceso))
    resultado = list(cursor.fetchall())
    guardar_plantilla(proceso, resultado[0], directorio)
    cerrar_conexion()

@cli.command()
@click.option('--proceso', help='Proceso a ejecutar')
def obtener_plantilla(proceso):
    obtener_plantilla_interno(proceso, None)


@cli.command()
@click.option('--version', help='version proceso a ejecutar')
def obtener_id_proceso(version):
    print("Obteniendo id proceso")
    #obtener plantilla
    cursor = obtener_conexion()
    consulta = "SELECT id, codigo_version, created_at FROM bpm_procesos.version_procesos WHERE codigo_version LIKE '%"+version+"%' ORDER BY codigo_version ASC"
    cursor.execute(consulta)
    resultado = cursor.fetchall()
    print(tabulate.tabulate(resultado, headers=["id","codigo_version","created_at"]))
    print("Se encontraron "+str(len(resultado))+" procesos")
    cerrar_conexion()
    ids_para_cambiar = list()
    i = 0
    for row in resultado:
        if(len(ids_para_cambiar) == 0):
            ids_para_cambiar.append(row)
        else:
            encontrado = False
            for i in range(len(ids_para_cambiar)):
                id = ids_para_cambiar[i]
                if(row[1][:-1] in id[1]):
                    
                    ids_para_cambiar[i] = row
                    encontrado = True
                    break
            if(encontrado == False):  
                ids_para_cambiar.append(row)
    print(tabulate.tabulate(ids_para_cambiar, headers=["id","codigo_version","created_at"]))
    print("Se filtron "+str(len(ids_para_cambiar))+" procesos")
    
    crear_directorio(version)
    for id in ids_para_cambiar:
        obtener_plantilla_interno(id[0], version)
        print("Se guardo la plantilla "+str(id[0]))  
        
@cli.command()
@click.option("--solicitud",help="numero de solicitud a buscar")
def obtener_json(solicitud):
    cur = obtener_conexion() 
    query = "select ip.datos_solicitud  from bpm_procesos.instancia_procesos ip where ip.id ='"+solicitud+"';"  
    print(query)
    cur.execute(query)
    row = cur.fetchone()
    print(row)
    crear_directorio("json")
    archivo_json = open("json/"+solicitud+".json",'w')
    archivo_json.writelines(row[0])
    archivo_json.close()
    cur.close()
    print("json descargado..")
    
@cli.command()
@click.option('--version', help='version proceso a ejecutar')
def obtener_listado_procesos_to_cvs(version):
    print("Obteniendo id proceso")
    #obtener plantilla
    cursor = obtener_conexion()
    consulta = "SELECT id, codigo_version, created_at FROM bpm_procesos.version_procesos WHERE codigo_version LIKE '%"+version+"%' ORDER BY codigo_version ASC"
    cursor.execute(consulta)
    resultado = cursor.fetchall()
    print(tabulate.tabulate(resultado, headers=["id","codigo_version","created_at"]))
    print("Se encontraron "+str(len(resultado))+" procesos")
    cerrar_conexion()
    ids_para_cambiar = list()
    i = 0
    for row in resultado:
        if(len(ids_para_cambiar) == 0):
            ids_para_cambiar.append(row)
        else:
            encontrado = False
            for i in range(len(ids_para_cambiar)):
                id = ids_para_cambiar[i]
                if(row[1][:-1] in id[1]):
                    
                    ids_para_cambiar[i] = row
                    encontrado = True
                    break
            if(encontrado == False):  
                ids_para_cambiar.append(row)
    print(tabulate.tabulate(ids_para_cambiar, headers=["id","codigo_version","created_at"]))
    print("Se filtron "+str(len(ids_para_cambiar))+" procesos")
    crear_directorio(version)
    crear_directorio("cvs")
    archivo_cvs = open("cvs/"+version+".csv",'w')
    for id in ids_para_cambiar:
        archivo_cvs.writelines(str(id[0])+","+str(id[1])+"\n")
    archivo_cvs.close()
    print("Se guardo el cvs "+version)

def actualizar_plantilla_interno(proceso, plantilla, directorio):
    print("actualizar plantilla")
    cursor = obtener_conexion()
    cursor.execute("UPDATE bpm_procesos.version_procesos SET plantilla_resolucion = %s WHERE id = %s", (plantilla, proceso))
    cerrar_conexion()
    print("Se actualizo la plantilla "+str(proceso))

    

@cli.command()
def prueba():
    print("prueba")



if __name__ == '__main__':
    cli()
