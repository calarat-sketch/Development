import pyodbc

# Configuración de conexión a SQL Server
conn_str = (
   r'DRIVER={ODBC Driver 17 for SQL Server};'
   r'SERVER=localhost;'
   r'DATABASE=Test;'
   r'Trusted_Connection=yes;'
)

def vaciar_todas_las_tablas(conexion):
    try:
        cursor = conexion.cursor()
        # Deshabilitar restricciones de clave foránea temporalmente
        cursor.execute('EXEC sp_msforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL"')
        # Borrar datos de todas las tablas
        cursor.execute('EXEC sp_msforeachtable "DELETE FROM ?"')
        # Habilitar restricciones de clave foránea
        cursor.execute('EXEC sp_msforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL"')
        conexion.commit()
        print('Todas las tablas han sido vaciadas.')
        cursor.close()
    except Exception as e:
        print('Error al vaciar las tablas:', e)

if __name__ == "__main__":
    try:
        conn = pyodbc.connect(conn_str)
        vaciar_todas_las_tablas(conn)
        conn.close()
    except Exception as e:
        print('Error de conexión o vaciado:', e)
