# monitor.py
def obtener_bases_datos(conexion):
    if not conexion: return []
    try:
        cursor = conexion.cursor()
        cursor.execute("SHOW DATABASES;")
        # Filtramos bases del sistema para no romper nada
        dbs = [db[0] for db in cursor.fetchall() if db[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
        cursor.close()
        return dbs
    except:
        return []

def obtener_estado_servidor(conexion):
    if not conexion:
        return {"conexiones": 0, "consultas": 0, "uptime": 0}
    try:
        cursor = conexion.cursor()
        cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected', 'Questions', 'Uptime');")
        res = dict(cursor.fetchall())
        cursor.close()
        return {
            "conexiones": res.get('Threads_connected', 0),
            "consultas": res.get('Questions', 0),
            "uptime": int(res.get('Uptime', 0)) // 60
        }
    except:
        return {"conexiones": 0, "consultas": 0, "uptime": 0}