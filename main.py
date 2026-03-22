import flet as ft
from BD.db import conectar_bd
import time
import asyncio  # Cambiamos threading por asyncio para que Flet no se maree

# Importaciones de nuestra lógica de base de datos
from acciones.respaldos import generar_respaldo_manual
from acciones.importar import restaurar_respaldo_manual
from acciones.usuarios import crear_usuario_y_rol
from acciones.monitor import obtener_estado_servidor  # <-- Recuerda actualizar monitor.py


# Usamos async para que el monitor y el FilePicker funcionen de la mano
async def main(page: ft.Page):
    page.title = "Sistema de Gestión MariaDB"
    page.window.width = 1000
    page.window.height = 800
    page.theme_mode = ft.ThemeMode.DARK

    # --- Verificación de Conexión (Tu lógica original) ---
    try:
        conexion = conectar_bd()
        estado_bd = "🟢 Conectado a MariaDB" if conexion else "🔴 Error de conexión"
    except Exception as e:
        conexion = None
        estado_bd = f"🔴 Error de conexión: {e}"

    # --- Lógica de Exportación ---
    texto_resultado_exportacion = ft.Text("", size=16, weight=ft.FontWeight.BOLD)

    def click_exportar(e):
        texto_resultado_exportacion.value = "Generando respaldo, espera..."
        texto_resultado_exportacion.color = ft.Colors.YELLOW
        page.update()

        if conexion:
            # Conexion a la BD, usar nombre en " "
            exito, mensaje = generar_respaldo_manual(conexion, "sakila")
        else:
            exito, mensaje = False, "No hay conexión a la base de datos."

        texto_resultado_exportacion.value = mensaje
        texto_resultado_exportacion.color = ft.Colors.GREEN if exito else ft.Colors.RED
        page.update()

    # --- Lógica de Importación (Asíncrona) ---
    texto_resultado_importacion = ft.Text("", size=16, weight=ft.FontWeight.BOLD)

    async def abrir_selector(e):
        # Abrimos el FilePicker y esperamos a que el usuario elija
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

    # --- Lógica de Usuarios ---
    input_user = ft.TextField(label="Nombre de Usuario", width=300)
    input_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)

    dropdown_rol = ft.Dropdown(
        label="Asignar Rol",
        width=300,
        options=[
            ft.dropdown.Option("Administrador"),
            ft.dropdown.Option("Solo Lectura"),
            ft.dropdown.Option("Operador de Respaldos"),
        ],
    )

    texto_res_user = ft.Text("", size=16, weight="bold")

    def ejecutar_crear_usuario(e):
        if not input_user.value or not input_pass.value or not dropdown_rol.value:
            texto_res_user.value = "¡Llena todos los campos, compa!"
            texto_res_user.color = ft.Colors.ORANGE
            page.update()
            return

        exito, mensaje = crear_usuario_y_rol(
            conexion,
            input_user.value,
            input_pass.value,
            dropdown_rol.value
        )

        texto_res_user.value = mensaje
        texto_res_user.color = ft.Colors.GREEN if exito else ft.Colors.RED

        if exito:
            input_user.value = ""
            input_pass.value = ""
            dropdown_rol.value = None

        page.update()

    # --- Lógica de Rendimiento (Dashboard Pro) ---
    val_conexiones = ft.Text("0", size=30, weight="bold", color=ft.Colors.CYAN)
    val_consultas = ft.Text("0", size=30, weight="bold", color=ft.Colors.GREEN)
    val_uptime = ft.Text("0 m", size=30, weight="bold", color=ft.Colors.AMBER)
    lista_logs = ft.ListView(expand=True, spacing=5)

    async def loop_monitor():
        while True:
            if conexion:
                try:
                    d = obtener_estado_servidor(conexion)
                    val_conexiones.value = str(d["conexiones"])
                    val_consultas.value = str(d["consultas"])
                    val_uptime.value = f"{d['uptime']} min"

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
            content=ft.Column([
                ft.Text(titulo, size=11, weight="bold", color=ft.Colors.WHITE70),
                control
            ], horizontal_alignment="center"),
            bgcolor=ft.Colors.WHITE10, padding=15, border_radius=10, width=180
        )

    # --- Construcción de la Interfaz ---
    page.add(
        ft.Row(
            [ft.Text(f"Dashboard Principal - {estado_bd}", weight=ft.FontWeight.BOLD, size=25)],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.Divider(),
        # CORRECCIÓN: Se agrega length=4 porque ahora es obligatorio
        ft.Tabs(
            length=4,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Exportar", icon=ft.Icons.DOWNLOAD),
                            ft.Tab(label="Importar", icon=ft.Icons.UPLOAD),
                            ft.Tab(label="Usuarios", icon=ft.Icons.PERSON),
                            ft.Tab(label="Monitor", icon=ft.Icons.ANALYTICS),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            # Pestaña 1: Exportar
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Generar Respaldo Manual (.sql)", size=25, weight=ft.FontWeight.BOLD),
                                        ft.Text("Extrae la estructura y los datos directamente desde MariaDB."),
                                        ft.ElevatedButton("Generar Archivo .sql", icon=ft.Icons.SAVE,
                                                          on_click=click_exportar),
                                        texto_resultado_exportacion
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                alignment=ft.Alignment.TOP_CENTER,
                                padding=40
                            ),
                            # Pestaña 2: Importar
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Restaurar Respaldo (.sql)", size=25, weight=ft.FontWeight.BOLD),
                                        ft.Text("Selecciona un archivo .sql para leer y ejecutar."),
                                        ft.ElevatedButton(
                                            "Buscar Archivo .sql",
                                            icon=ft.Icons.FOLDER_OPEN,
                                            on_click=abrir_selector
                                        ),
                                        texto_resultado_importacion
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                alignment=ft.Alignment.TOP_CENTER,
                                padding=40
                            ),
                            # Pestaña 3: Usuarios
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Gestión de Usuarios y Roles", size=25, weight=ft.FontWeight.BOLD),
                                        ft.Text("Crea cuentas nuevas y asigna privilegios específicos."),
                                        ft.Divider(height=20, color="transparent"),
                                        input_user,
                                        input_pass,
                                        dropdown_rol,
                                        ft.ElevatedButton(
                                            "Crear y Asignar",
                                            icon=ft.Icons.PERSON_ADD,
                                            on_click=ejecutar_crear_usuario
                                        ),
                                        texto_res_user
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                alignment=ft.Alignment.TOP_CENTER,
                                padding=40
                            ),
                            # Pestaña 4: RENDIMIENTO (DASHBOARD PRO)
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Dashboard de Salud del Servidor", size=25, weight="bold"),
                                    ft.Row([
                                        card_metrica("HILOS ACTIVOS", val_conexiones, ft.Colors.CYAN),
                                        card_metrica("CONSULTAS", val_consultas, ft.Colors.GREEN),
                                        card_metrica("UPTIME", val_uptime, ft.Colors.AMBER),
                                    ], alignment="center", spacing=20),
                                    ft.Text("Historial de Monitoreo:", size=16, weight="bold"),
                                    ft.Container(
                                        content=lista_logs,
                                        bgcolor=ft.Colors.BLACK,
                                        padding=15,
                                        border_radius=10,
                                        expand=True,
                                        border=ft.border.all(1, ft.Colors.WHITE10)
                                    )
                                ], horizontal_alignment="center", spacing=20),
                                padding=40
                            ),
                        ],
                    ),
                ],
            ),
        )
    )
    # Iniciamos el monitor asíncrono de fondo
    asyncio.create_task(loop_monitor())


if __name__ == "__main__":
    # CORRECCIÓN: Se usa run() en lugar de app()
    ft.run(main)