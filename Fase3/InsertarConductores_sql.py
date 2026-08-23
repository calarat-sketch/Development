
import pyodbc


# Define the connection string for Windows Authentication
conn_str = (
   r'DRIVER={ODBC Driver 17 for SQL Server};'
   r'SERVER=localhost;' # Replace with your server name
   r'DATABASE=Test;' # Replace with your database name
   r'Trusted_Connection=yes;'
)
# Establish a connection to the database
try:
   conn = pyodbc.connect(conn_str)
   print("Connection Successful using Windows Authentication")
except pyodbc.Error as e:
   print(f"Error: {e}")






   # Función para insertar datos en la tabla conductores desde un archivo XML
import xml.etree.ElementTree as ET

def insertar_conductores_desde_xml(conexion, xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        cursor = conexion.cursor()
        for conductor in root.findall('conductor'):
            nombre = conductor.find('nombre').text
            apellido = conductor.find('apellido').text
            numero_licencia = conductor.find('numero_licencia').text
            tipo_licencia = conductor.find('tipo_licencia').text if conductor.find('tipo_licencia') is not None else None
            fecha_expiracion = conductor.find('fecha_expiracion_licencia').text if conductor.find('fecha_expiracion_licencia') is not None else None
            cursor.execute(
                """
                INSERT INTO conductores (nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion_licencia)
                VALUES (?, ?, ?, ?, ?)
                """,
                nombre, apellido, numero_licencia, tipo_licencia, fecha_expiracion
            )
        conexion.commit()
        print('Datos insertados desde XML correctamente.')
        cursor.close()
    except Exception as e:
        print('No se pudo insertar desde XML:', e)
