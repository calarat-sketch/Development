# Función para insertar datos aleatorios en la tabla conductores (Versión SQLite)
import sqlite3
import random
import string
import os
from pathlib import Path

# Configuración de conexión a SQLite - buscar en data/ o en carpeta padre
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)  # Sube de scripts/ a Fase3/
db_path = os.path.join(parent_dir, 'data', 'gestor_datos.db')

# Fallback si no existe
if not os.path.exists(db_path):
    db_path = os.path.join(parent_dir, 'gestor_datos.db')

DB_FILE = db_path

# Función para leer la tabla 'conductores' usando una conexión existente
def leer_conductores(conexion):
   try:
      cursor = conexion.cursor()
      cursor.execute('SELECT * FROM conductores')
      filas = cursor.fetchall()
      columnas = [column[0] for column in cursor.description]
      print('Columnas:', columnas)
      for fila in filas:
         print(fila)
      cursor.close()
   except Exception as e:
      print('No se pudo leer la tabla conductores:', e)

def insertar_datos_aleatorios_conductores(conexion):
    try:
        cursor = conexion.cursor()
        
        # Aseguramos que la tabla exista con la estructura correcta para SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conductores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellido TEXT,
                dni TEXT,
                numero_licencia TEXT,
                tipo_licencia TEXT,
                fecha_expiracion_licencia TEXT,
                Plazas_Vehiculo INTEGER,
                activo INTEGER DEFAULT 1
            )
        """)

        for _ in range(5):
            id_val = random.randint(1000, 9999)
            dni = ''.join(random.choices(string.digits, k=8))
            nombre = 'Nombre' + ''.join(random.choices(string.ascii_uppercase, k=3))
            apellido = 'Apellido' + ''.join(random.choices(string.ascii_uppercase, k=3))
            numero_licencia = ''.join(random.choices(string.digits, k=8))
            tipo_licencia = random.choice(['A', 'B', 'C'])
            fecha_expiracion = '2030-12-31'
            plazas_vehiculo = random.choice([55, 20, 4])
            
            cursor.execute(
                """
                INSERT OR IGNORE INTO conductores (id, dni, nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion_licencia, Plazas_Vehiculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_val, dni, nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion, plazas_vehiculo)
            )
        conexion.commit()
        print('Se insertaron 5 conductores aleatorios en SQLite.')
        cursor.close()
    except Exception as e:
        print('No se pudo insertar en la tabla conductores:', e)

# Ejemplo de uso
try:
    conn = sqlite3.connect(DB_FILE)
    insertar_datos_aleatorios_conductores(conn)
    leer_conductores(conn)
    conn.close()
except Exception as e:
    print('Error:', e)