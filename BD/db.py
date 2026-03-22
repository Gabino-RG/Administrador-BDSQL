import mysql.connector
from mysql.connector import Error

def conectar_bd():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',          # Pon tu usuario de MariaDB
            password='',          # Pon tu contraseña
            database=''    # Crea una base de prueba y pon el nombre aquí
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MariaDB: {e}")
        return None