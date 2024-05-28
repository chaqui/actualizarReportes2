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

def crear_conexion_release():
    host = os.getenv("HOST_RELEASE")
    user = os.getenv("USER_DB_RELEASE")
    passwd = os.getenv("PASSWORD_RELEASE")
    db = os.getenv("DATABASE_RELEASE")
    port = os.getenv("PORT_RELEASE")
    return pymysql.connect(host =host, user= user, passwd=passwd, db=db,port=int(port) )

def obtener_conexion():
    mi_conexion = crear_conexion()
    return mi_conexion.cursor()

def obtener_conexion_release():
    mi_conexion = crear_conexion_release()
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
@click.option('--codigo_proceso', help='codigo proceso a ejecutar')
def obtener_plantilla_codigo(codigo_proceso):
    print("Obteniendo plantilla")
    #obtener plantilla
    cursor = obtener_conexion()
    consulta = "SELECT plantilla_resolucion, codigo_version FROM bpm_procesos.version_procesos WHERE codigo_version LIKE '%"+codigo_proceso+"%'"
    print(consulta)
    cursor.execute(consulta)
    resultado = list(cursor.fetchall())
    guardar_plantilla(codigo_proceso, resultado[0], None)
    cerrar_conexion()


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
    query = "select ip.numero_solicitud, ip.datos_solicitud  from bpm_procesos.instancia_procesos ip where ip.id ='"+solicitud+"';"  
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    escribir_archivo_json(solicitud, row)
    print("json descargado..")

@cli.command()
@click.option("--solicitud",help="numero de solicitud a buscar")
def obtener_json_codigo(solicitud):
    cur = obtener_conexion() 
    query = crear_consulta_json(solicitud) 
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    if(row == None):
        print("No se encontro la solicitud")
        return
    escribir_archivo_json(solicitud, row)
    print("json descargado..")

@cli.command()
@click.option("--solicitud",help="numero de solicitud a buscar")
def obtener_json_release(solicitud):
    cur = obtener_conexion_release() 
    query = crear_consulta_json(solicitud) 
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    if(row == None):
        print("No se encontro la solicitud")
        return
    escribir_archivo_json(solicitud, row)
    print("json descargado..")
 
def crear_consulta_json(solicitud):
    return "select  ip.numero_solicitud, ip.datos_solicitud, vp.codigo_version  from bpm_procesos.instancia_procesos ip inner join  bpm_procesos.version_procesos vp on ip.id_version_proceso = vp.id where ip.numero_solicitud ='"+solicitud+"';"  

def crear_consulta_form_solicitud(solicitud):
    return "select  ip.numero_solicitud,  vp.plantilla_form_solicitud, vp.codigo_version  from bpm_procesos.instancia_procesos ip inner join  bpm_procesos.version_procesos vp on ip.id_version_proceso = vp.id where ip.numero_solicitud ='"+solicitud+"';"

def escribir_archivo_json(solicitud, data):
    directorio = "json/"+data[2]
    crear_directorio(directorio)
    print(directorio)
    escribirArchivo(directorio, solicitud,data)

def escribir_archivo_formulario(solicitud, data):
    directorio = "formularios/"+data[2]
    crear_directorio(directorio)
    print(directorio)
    escribirArchivo(directorio, solicitud, data)
    
    
def escribirArchivo(directorio, solicitud, data):
    archivo_json = open(directorio+"/"+data[0]+"-"+solicitud+".json",'w')
    archivo_json.writelines(data[1])
    archivo_json.close()
    
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

def actualizar_plantilla_interno(proceso, plantilla):
    print("actualizar plantilla")
    cursor = obtener_conexion()
    consulta = "UPDATE bpm_procesos.version_procesos SET plantilla_resolucion = '"+plantilla+"' WHERE id = '"+proceso+"'" 
    print(consulta)
    cursor.execute(consulta)
    cursor.execute("COMMIT")
    cerrar_conexion()
    print("Se actualizo la plantilla "+str(proceso))

@cli.command()
@click.option('--proceso_principal', help='nombre del grupo de procesos')
@click.option('--subproceso', help='nombre del subproceso')
def actualizar_plantilla(proceso_principal, subproceso):
    with open('cvs/'+proceso_principal+'.csv', newline='') as file:
        cvs_file =csv.reader(file, delimiter=',')
        for row in cvs_file:
            if(subproceso == row[1]):
                id=row[0]
                print("actualizar plantilla "+id)
                archivo_plantilla = open(proceso_principal+"/"+subproceso+"-"+id+".html",'r')
                plantilla = archivo_plantilla.read()
                archivo_plantilla.close()
                actualizar_plantilla_interno(row[0], plantilla)
                break

@cli.command()
@click.option('--proceso', help='nombre del grupo de procesos')
def generar_sql_migracion(proceso):
     with open('cvs/'+proceso+'_MODIFICADOS.csv', newline='') as file:
        cvs_file =csv.reader(file, delimiter=',')
        crear_directorio("sql")
        archivo_sql = open("sql/"+proceso+".sql",'w')
        for row in cvs_file:
            id=row[0]
            sub_proceso = row[1]
            print("actualizar plantilla "+id)
            archivo_plantilla = open(proceso+"/"+sub_proceso+"-"+id+".html",'r')
            plantilla = archivo_plantilla.read()
            archivo_plantilla.close()
            cursor = obtener_conexion()
            consulta = "UPDATE bpm_procesos.version_procesos SET plantilla_resolucion = '"+plantilla+"', updated_user='josue.fuentes', updated_at = NOW() WHERE id = '"+id+"'"
            print(consulta)
            cursor.execute(consulta)
            print("Se actualizo la plantilla "+str(sub_proceso))
            archivo_sql.writelines("-- subProceso: "+sub_proceso+" id:"+id+"\n")
            archivo_sql.writelines(consulta+";\n \n \n ")
        cursor.execute("COMMIT")
        archivo_sql.close()
    
@cli.command()
def prueba():
    print("prueba")

@cli.command()
@click.option('--proceso_principal', help='nombre del grupo de procesos')
@click.option('--sub_proceso', help='nombre del subproceso')
def generar_sql_migracion_por_proceso(proceso_principal, sub_proceso):
    with open('cvs/'+proceso_principal+'.csv', newline='') as file:
        cvs_file =csv.reader(file, delimiter=',')
        for row in cvs_file:
            if(sub_proceso == row[1]):
                id=row[0]
                print("actualizar plantilla "+id)
                archivo_plantilla = open(proceso_principal+"/"+sub_proceso+"-"+id+".html",'r')
                plantilla = archivo_plantilla.read()
                archivo_plantilla.close()
                cursor = obtener_conexion()
                consulta = "UPDATE bpm_procesos.version_procesos SET plantilla_resolucion = '"+plantilla+"', updated_user='josue.fuentes', updated_at = NOW() WHERE id = '"+id+"'"
                print(consulta)
                cursor.execute(consulta)
                print("Se actualizo la plantilla "+str(sub_proceso))
                directorio= "sql/"+sub_proceso
                crear_directorio(directorio)
                archivo_sql = open(directorio+"/"+sub_proceso+".sql",'w')
                archivo_sql.writelines("-- subProceso: "+sub_proceso+" id:"+id+"\n")
                archivo_sql.writelines(consulta+";\n \n \n ")
                cursor.execute("COMMIT")
                archivo_sql.close()
                
@cli.command()
@click.option('--numero_solicitud', help='numero de la solictud')
def obtener_plantilla_formulario(numero_solicitud):
    cur = obtener_conexion() 
    query = crear_consulta_form_solicitud(numero_solicitud) 
    print(query)
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    escribir_archivo_formulario(numero_solicitud, row)
    print("json descargado..")
    

if __name__ == '__main__':
    cli()
