# Función para insertar dos datos aleatorios en la tabla conductores
import pyodbc   
import random
import string


# Define the connection string for Windows Authentication
conn_str = (
   r'DRIVER={ODBC Driver 17 for SQL Server};'
   r'SERVER=localhost;' # Replace with your server name
   r'DATABASE=Test;' # Replace with your database name
   r'Trusted_Connection=yes;'
)


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
        for _ in range(5):
            id = random.randint(1000, 9999)
            dni = ''.join(random.choices(string.digits, k=8))
            nombre = 'Nombre' + ''.join(random.choices(string.ascii_uppercase, k=3))
            apellido = 'Apellido' + ''.join(random.choices(string.ascii_uppercase, k=3))
            numero_licencia = ''.join(random.choices(string.digits, k=8))
            tipo_licencia = random.choice(['A', 'B', 'C'])
            fecha_expiracion = '2030-12-31'
            plazas_vehiculo = random.choice([55, 20, 4])
            
            
            cursor.execute(
                """
                INSERT INTO conductores (id ,dni ,nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion_licencia,plazas_vehiculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                id, dni, nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion, plazas_vehiculo
            )
        conexion.commit()
        print('Se insertaron 2 conductores aleatorios.')
        cursor.close()
    except Exception as e:
        print('No se pudo insertar en la tabla conductores:', e)

# Ejemplo de uso de la función de inserción
try:
    conn = pyodbc.connect(conn_str)
    insertar_datos_aleatorios_conductores(conn)
    leer_conductores(conn)
except Exception as e:
    print('No se pudo leer la tabla conductores:', e)