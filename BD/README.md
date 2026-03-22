# 🗄️ Administrador de BD SQL (MariaDB)

Sistema de gestión desarrollado con **Python** y **Flet** para administrar servidores MariaDB de forma gráfica y sencilla.

## 🚀 Funciones Principales
* **Exportar:** Respaldos manuales con ventana de guardado personalizada.
* **Importar:** Restauración de archivos `.sql` (soporta Vistas y Datos Binarios).
* **Usuarios:** Panel para crear y listar usuarios reales del servidor.
* **Monitor:** Dashboard en vivo de hilos, consultas y uptime.

## 🛠️ Requisitos
* Python 3.10+
* MariaDB / MySQL Server
* Librerías: `flet`, `mysql-connector-python`

## 📦 Instalación
1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Configurar credenciales en `BD/db.py`.
4. Ejecutar `prueba.py`.