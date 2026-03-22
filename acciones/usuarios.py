from mysql.connector import Error

def crear_usuario_y_rol(conexion, nombre, password, rol):
    if not conexion:
        return False, "No hay conexión a la base de datos."

    try:
        cursor = conexion.cursor()

        # 1. Crear el usuario
        # Usamos F-strings con cuidado o parámetros si el driver lo permite en DDL
        cursor.execute(f"CREATE USER IF NOT EXISTS '{nombre}'@'localhost' IDENTIFIED BY '{password}';")

        # 2. Manejo de Roles
        # Definimos qué puede hacer cada "etiqueta"
        if rol == "Administrador":
            cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{nombre}'@'localhost' WITH GRANT OPTION;")
        elif rol == "Solo Lectura":
            cursor.execute(f"GRANT SELECT ON *.* TO '{nombre}'@'localhost';")
        elif rol == "Operador de Respaldos":
            # Permisos mínimos para que el motor de exportación que hicimos funcione
            cursor.execute(f"GRANT SELECT, SHOW VIEW, EVENT, TRIGGER, LOCK TABLES ON *.* TO '{nombre}'@'localhost';")

        # 3. Aplicar cambios
        cursor.execute("FLUSH PRIVILEGES;")

        cursor.close()
        return True, f"Usuario '{nombre}' creado con éxito como {rol}."

    except Error as e:
        return False, f"Error de MariaDB: {e}"