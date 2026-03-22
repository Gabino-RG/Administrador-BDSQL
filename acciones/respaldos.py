import datetime


def generar_respaldo_manual(conexion, nombre_bd, ruta_destino):
    if not conexion:
        return False, "No hay conexión a la base de datos."

    try:
        cursor = conexion.cursor()
        cursor.execute(f"USE `{nombre_bd}`")

        with open(ruta_destino, 'w', encoding='utf-8') as archivo_sql:
            # Cabecera y desactivación de llaves foráneas
            archivo_sql.write(f"-- Respaldo Pro Generado por Sistema MariaDB\n")
            archivo_sql.write(f"-- Base de datos: {nombre_bd}\n")
            archivo_sql.write(f"-- Fecha: {datetime.datetime.now()}\n\n")
            archivo_sql.write("SET FOREIGN_KEY_CHECKS=0;\n\n")

            # 1. Identificar Tablas y Vistas
            cursor.execute("SHOW FULL TABLES")
            objetos = cursor.fetchall()

            for nombre_obj, tipo_obj in objetos:
                if tipo_obj == 'BASE TABLE':
                    # --- PROCESAR TABLA ---
                    cursor.execute(f"SHOW CREATE TABLE `{nombre_obj}`")
                    res_sql = cursor.fetchone()[1]
                    # Limpiamos saltos de línea para evitar errores de sintaxis al importar
                    res_sql = res_sql.replace('\n', ' ').replace('\r', '')

                    archivo_sql.write(f"DROP TABLE IF EXISTS `{nombre_obj}`;\n")
                    archivo_sql.write(f"{res_sql};\n\n")

                    # Volcar Datos
                    cursor.execute(f"SELECT * FROM `{nombre_obj}`")
                    registros = cursor.fetchall()

                    if registros:
                        archivo_sql.write(f"-- Datos de la tabla `{nombre_obj}`\n")
                        for registro in registros:
                            valores_formateados = []
                            for valor in registro:
                                if valor is None:
                                    valores_formateados.append("NULL")
                                elif isinstance(valor, (int, float)):
                                    valores_formateados.append(str(valor))
                                elif isinstance(valor, (bytes, bytearray)):
                                    # Manejo de datos binarios (imágenes/blobs)
                                    valores_formateados.append(f"X'{valor.hex()}'")
                                else:
                                    # Escapado de comillas y diagonales
                                    v_esc = str(valor).replace("'", "''").replace("\\", "\\\\")
                                    valores_formateados.append(f"'{v_esc}'")

                            linea_insert = f"INSERT INTO `{nombre_obj}` VALUES ({', '.join(valores_formateados)});\n"
                            archivo_sql.write(linea_insert)
                        archivo_sql.write("\n")

                else:
                    # --- PROCESAR VISTA ---
                    cursor.execute(f"SHOW CREATE VIEW `{nombre_obj}`")
                    res_view = cursor.fetchone()[1]
                    # Limpieza de la consulta de la vista
                    res_view = res_view.replace('\n', ' ').replace('\r', '')

                    archivo_sql.write(f"DROP VIEW IF EXISTS `{nombre_obj}`;\n")
                    archivo_sql.write(f"{res_view};\n\n")

            # Reactivamos llaves foráneas al final
            archivo_sql.write("SET FOREIGN_KEY_CHECKS=1;\n")

        cursor.close()
        return True, f"✅ Respaldo exitoso en:\n{ruta_destino}"

    except Exception as e:
        return False, f"❌ Error al generar respaldo: {str(e)}"