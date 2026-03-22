import flet as ft
from BD.db import conectar_bd
import time
import asyncio

# Importaciones de tu lógica
from acciones.respaldos import generar_respaldo_manual
from acciones.importar import restaurar_respaldo_manual
from acciones.usuarios import crear_usuario_y_rol
from acciones.monitor import obtener_estado_servidor, obtener_bases_datos


async def main(page: ft.Page):
    page.title = "Sistema de Gestión MariaDB"
    page.window.width = 1000
    page.window.height = 800
    page.theme_mode = ft.ThemeMode.DARK

    # --- Verificación de Conexión ---
    try:
        conexion = conectar_bd()
        estado_bd = "🟢 Conectado a MariaDB" if conexion else "🔴 Error de conexión"
        # Traemos las bases de datos reales para el Dropdown
        lista_dbs = obtener_bases_datos(conexion) if conexion else []
    except Exception as e:
        conexion = None
        estado_bd = f"🔴 Error de conexión: {e}"
        lista_dbs = []

    # --- Lógica de Exportación (NUEVA: Con save_file y Dropdown) ---
    texto_resultado_exportacion = ft.Text("", size=16, weight=ft.FontWeight.BOLD)

    dropdown_db_exportar = ft.Dropdown(
        label="Seleccionar Base de Datos",
        width=300,
        options=[ft.dropdown.Option(db) for db in lista_dbs]
    )

    async def click_exportar(e):
        if not dropdown_db_exportar.value:
            texto_resultado_exportacion.value = "⚠️ Selecciona una base de datos primero."
            texto_resultado_exportacion.color = ft.Colors.ORANGE
            page.update()
            return

        # USAMOS SAVE_FILE como pediste (Igual que el pick_files que sí te sirve)
        ruta_guardar = await ft.FilePicker().save_file(
            file_name=f"respaldo_{dropdown_db_exportar.value}.sql",
            allowed_extensions=["sql"]
        )

        if ruta_guardar:
            texto_resultado_exportacion.value = "Generando respaldo, espera..."
            texto_resultado_exportacion.color = ft.Colors.YELLOW
            page.update()

            if conexion:
                # Se ejecuta la lógica de respaldo en la ruta elegida
                exito, mensaje = await asyncio.to_thread(generar_respaldo_manual, conexion, dropdown_db_exportar.value,
                                                         ruta_guardar)
            else:
                exito, mensaje = False, "No hay conexión a la base de datos."

            texto_resultado_exportacion.value = mensaje
            texto_resultado_exportacion.color = ft.Colors.GREEN if exito else ft.Colors.RED
            page.update()

    # --- Lógica de Importación (ESTA NO SE TOCÓ, ES TU CÓDIGO BASE) ---
    texto_resultado_importacion = ft.Text("", size=16, weight=ft.FontWeight.BOLD)

    async def abrir_selector(e):
        archivos = await ft.FilePicker().pick_files(allowed_extensions=["sql"])

        if archivos:
            ruta_archivo = archivos[0].path
            texto_resultado_importacion.value = f"Restaurando desde:\n{archivos[0].name}\nEspera..."
            texto_resultado_importacion.color = ft.Colors.YELLOW
            page.update()

            if conexion:
                exito, mensaje = restaurar_respaldo_manual(conexion, ruta_archivo)
            else:
                exito, mensaje = False, "No hay conexión a la base de datos."

            texto_resultado_importacion.value = mensaje
            texto_resultado_importacion.color = ft.Colors.GREEN if exito else ft.Colors.RED
            page.update()
        else:
            texto_resultado_importacion.value = "Operación cancelada."
            texto_resultado_importacion.color = ft.Colors.ORANGE
            page.update()

    # --- Lógica de Usuarios (NUEVA: Con Lista de Usuarios Actuales) ---
    input_user = ft.TextField(label="Nombre de Usuario", width=300)
    input_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)
    dropdown_rol = ft.Dropdown(label="Asignar Rol", width=300, options=[
        ft.dropdown.Option("Administrador"),
        ft.dropdown.Option("Solo Lectura"),
        ft.dropdown.Option("Operador de Respaldos"),
    ])
    texto_res_user = ft.Text("", size=16, weight="bold")

    # Lista para mostrar usuarios
    columna_usuarios = ft.Column(spacing=5)

    def ejecutar_crear_usuario(e):
        if not input_user.value or not input_pass.value or not dropdown_rol.value:
            texto_res_user.value = "¡Llena todos los campos, compa!"
            texto_res_user.color = ft.Colors.ORANGE
            page.update()
            return

        exito, mensaje = crear_usuario_y_rol(conexion, input_user.value, input_pass.value, dropdown_rol.value)
        texto_res_user.value = mensaje
        texto_res_user.color = ft.Colors.GREEN if exito else ft.Colors.RED
        if exito:
            input_user.value = "";
            input_pass.value = "";
            dropdown_rol.value = None
        page.update()

    def ver_usuarios_servidor(e):
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT user, host FROM mysql.user LIMIT 10")
                usuarios = cursor.fetchall()
                columna_usuarios.controls = [ft.Text(f"👤 {u[0]}@{u[1]}", size=12) for u in usuarios]
                cursor.close()
            except:
                columna_usuarios.controls = [ft.Text("Error al leer usuarios", color=ft.Colors.RED)]
        page.update()

    # --- Lógica de Rendimiento ---
    val_conexiones = ft.Text("0", size=30, weight="bold", color=ft.Colors.CYAN)
    val_consultas = ft.Text("0", size=30, weight="bold", color=ft.Colors.GREEN)
    val_uptime = ft.Text("0 m", size=30, weight="bold", color=ft.Colors.AMBER)
    lista_logs = ft.ListView(expand=True, spacing=5)

    async def loop_monitor():
        while True:
            if conexion:
                try:
                    d = obtener_estado_servidor(conexion)
                    val_conexiones.value, val_consultas.value, val_uptime.value = str(d["conexiones"]), str(
                        d["consultas"]), f"{d['uptime']} min"
                    hora = time.strftime("%H:%M:%S")
                    lista_logs.controls.insert(0, ft.Text(f"[{hora}] Check: OK | Threads: {d['conexiones']}", size=12,
                                                          color=ft.Colors.WHITE38))
                    if len(lista_logs.controls) > 10: lista_logs.controls.pop()
                    page.update()
                except:
                    pass
            await asyncio.sleep(2)

    def card_metrica(titulo, control, color):
        return ft.Container(
            content=ft.Column([ft.Text(titulo, size=11, weight="bold", color=ft.Colors.WHITE70), control],
                              horizontal_alignment="center"),
            bgcolor=ft.Colors.WHITE10, padding=15, border_radius=10, width=180
        )

    # --- Construcción de la Interfaz ---
    page.add(
        ft.Row([ft.Text(f"Dashboard Principal - {estado_bd}", weight=ft.FontWeight.BOLD, size=25)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        ft.Tabs(
            length=4, selected_index=0, expand=True,
            content=ft.Column(expand=True, controls=[
                ft.TabBar(tabs=[
                    ft.Tab(label="Exportar", icon=ft.Icons.DOWNLOAD),
                    ft.Tab(label="Importar", icon=ft.Icons.UPLOAD),
                    ft.Tab(label="Usuarios", icon=ft.Icons.PERSON),
                    ft.Tab(label="Monitor", icon=ft.Icons.ANALYTICS),
                ]),
                ft.TabBarView(expand=True, controls=[
                    # Pestaña 1: Exportar (CON SAVE_FILE)
                    ft.Container(content=ft.Column([
                        ft.Text("Generar Respaldo Manual (.sql)", size=25, weight=ft.FontWeight.BOLD),
                        dropdown_db_exportar,
                        ft.ElevatedButton("Seleccionar Destino y Exportar", icon=ft.Icons.SAVE,
                                          on_click=click_exportar),
                        texto_resultado_exportacion
                    ], horizontal_alignment="center"), padding=40),
                    # Pestaña 2: Importar (INTACTA)
                    ft.Container(content=ft.Column([
                        ft.Text("Restaurar Respaldo (.sql)", size=25, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton("Buscar Archivo .sql", icon=ft.Icons.FOLDER_OPEN, on_click=abrir_selector),
                        texto_resultado_importacion
                    ], horizontal_alignment="center"), padding=40),
                    # Pestaña 3: Usuarios (CON LISTA)
                    ft.Container(content=ft.Row([
                        ft.Column([ft.Text("Gestión de Usuarios", size=22, weight="bold"), input_user, input_pass,
                                   dropdown_rol, ft.ElevatedButton("Crear", icon=ft.Icons.PERSON_ADD,
                                                                   on_click=ejecutar_crear_usuario), texto_res_user],
                                  spacing=10),
                        ft.VerticalDivider(width=40),
                        ft.Column([ft.Text("Usuarios Actuales", weight="bold"),
                                   ft.ElevatedButton("Listar", on_click=ver_usuarios_servidor), columna_usuarios],
                                  expand=True, scroll=ft.ScrollMode.AUTO)
                    ], alignment="center"), padding=40),
                    # Pestaña 4: Monitor
                    ft.Container(content=ft.Column([
                        ft.Row([card_metrica("HILOS ACTIVOS", val_conexiones, ft.Colors.CYAN),
                                card_metrica("CONSULTAS", val_consultas, ft.Colors.GREEN),
                                card_metrica("UPTIME", val_uptime, ft.Colors.AMBER)], alignment="center", spacing=20),
                        ft.Container(content=lista_logs, bgcolor=ft.Colors.BLACK, padding=15, border_radius=10,
                                     expand=True, border=ft.border.all(1, ft.Colors.WHITE10))
                    ], horizontal_alignment="center", spacing=20), padding=40),
                ]),
            ]),
        )
    )
    asyncio.create_task(loop_monitor())


if __name__ == "__main__":
    ft.run(main)