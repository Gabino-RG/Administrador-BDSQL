# importar.py
from mysql.connector import Error


def restaurar_respaldo_manual(conexion, ruta_archivo):
    if not conexion:
        return False, "No hay conexión a la base de datos."

    try:
        cursor = conexion.cursor()

        # 1. Desactivamos llaves foráneas para que nos deje borrar/crear todo
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido_completo = f.read()

            # --- EL NUEVO TRUCO ---
            # Separamos por ";\n" para que los ";" internos de Sakila no nos engañen.
            # Los dumps que generamos con el respaldos.py que te di
            # siempre terminan sus comandos reales con ";\n\n"
            consultas = contenido_completo.split(';\n')

            for consulta in consultas:
                sql = consulta.strip()
                if sql:
                    try:
                        cursor.execute(sql)
                    except Error as e:
                        # Ignoramos errores menores como comentarios o warnings
                        print(f"Aviso en consulta: {e}")
                        continue

        # 2. Reactivamos la seguridad
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        conexion.commit()
        cursor.close()
        return True, "✅ Base de Datos restaurada con éxito (Manual Split)."

    except Exception as e:
        # Intentamos reactivar llaves por seguridad si algo truena
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        except:
            pass
        return False, f"❌ Error al restaurar: {str(e)}"