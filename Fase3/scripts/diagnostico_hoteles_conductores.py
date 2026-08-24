import pyodbc

conn_str = (
   r'DRIVER={ODBC Driver 17 for SQL Server};'
   r'SERVER=localhost;'
   r'DATABASE=Test;'
   r'Trusted_Connection=yes;'
)

def diagnostico_hoteles_conductores(conexion):
    cursor = conexion.cursor()
    print('--- Conductores activos y plazas ---')
    cursor.execute('SELECT id, nombre, Plazas_Vehiculo FROM conductores WHERE activo=1')
    for row in cursor.fetchall():
        print(f'Conductor ID: {row.id}, Nombre: {row.nombre}, Plazas: {row.Plazas_Vehiculo}')
    print('\n--- Hoteles y personas ---')
    cursor.execute('''
        SELECT h.id, h.personas, z.hora, z.id as zona_id
        FROM hoteles h
        JOIN zonas z ON h.zona_id = z.id
    ''')
    for row in cursor.fetchall():
        print(f'Hotel ID: {row.id}, Personas: {row.personas}, Hora: {row.hora}, Zona ID: {row.zona_id}')
    print('\n--- Hoteles con personas > plazas de cualquier conductor ---')
    cursor.execute('''
        SELECT h.id, h.personas FROM hoteles h
        WHERE h.personas > (SELECT MAX(Plazas_Vehiculo) FROM conductores WHERE activo=1)
    ''')
    rows = cursor.fetchall()
    if not rows:
        print('Ningún hotel supera el máximo de plazas de los conductores.')
    else:
        for row in rows:
            print(f'Hotel ID: {row.id}, Personas: {row.personas}')
    print('\n--- Total hoteles ---')
    cursor.execute('SELECT COUNT(*) FROM hoteles')
    print('Total hoteles:', cursor.fetchone()[0])
    print('\n--- Total conductores activos ---')
    cursor.execute('SELECT COUNT(*) FROM conductores WHERE activo=1')
    print('Total conductores activos:', cursor.fetchone()[0])
    cursor.close()

if __name__ == "__main__":
    try:
        conn = pyodbc.connect(conn_str)
        diagnostico_hoteles_conductores(conn)
        conn.close()
    except Exception as e:
        print('Error de diagnóstico:', e)
