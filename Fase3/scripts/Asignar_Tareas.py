import pyodbc
from datetime import datetime, timedelta

# Configuración de conexión a SQL Server
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=Test;'
    r'Trusted_Connection=yes;'
)

LOG_FILE = "log_asignacion_conductores.txt"

def log(mensaje):
    """Imprime el mensaje y lo guarda en un archivo de texto con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(mensaje)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensaje}\n")

def asignar_conductores():
    """
    Asigna conductores de la tabla 'conductores' a los grupos existentes en 'grupos_hoteles'.
    Genera una nueva tabla 'asignaciones_grupos' con el campo 'grupo_conductor'.
    """
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        log("✓ Conexión exitosa a la base de datos.\n")

        # 1. Obtener los grupos únicos de la tabla grupos_hoteles
        log("Obteniendo grupos de 'grupos_hoteles'...")
        # Agrupamos por número de grupo para obtener una fila por grupo
        query_grupos = '''
            SELECT 
                grupo_numero,
                MAX(hora_inicio_grupo) as hora_inicio,
                MAX(hora_fin_grupo) as hora_fin,
                MAX(total_personas_grupo) as total_personas
            FROM grupos_hoteles
            GROUP BY grupo_numero
            ORDER BY grupo_numero
        '''
        
        try:
            cursor.execute(query_grupos)
            grupos = cursor.fetchall()
        except pyodbc.Error:
            log("❌ Error: No se pudo leer la tabla 'grupos_hoteles'. Asegúrate de ejecutar primero el script de agrupación.")
            return

        if not grupos:
            log("⚠ No se encontraron grupos en la tabla 'grupos_hoteles'.")
            return

        log(f"📊 Total de grupos encontrados: {len(grupos)}")

        # 2. Obtener conductores de la tabla conductores
        log("Obteniendo conductores disponibles...")
        try:
            cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores where activo=1")
            conductores = cursor.fetchall()
            
            if not conductores:
                log("⚠ La tabla 'conductores' existe pero está vacía.")
                # Insertar datos dummy si está vacía para que el script funcione
                log("   -> Insertando conductores de prueba...")
                cursor.execute("INSERT INTO conductores (nombre, Plazas_Vehiculo) VALUES ('Juan Pérez', 55), ('María García', 20), ('Carlos López', 4)")
                conn.commit()
                cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores")
                conductores = cursor.fetchall()
                
        except pyodbc.Error:
            log("⚠ La tabla 'conductores' no existe. Creándola con datos de prueba...")
            cursor.execute("""
                CREATE TABLE conductores (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    nombre VARCHAR(100),
                    Plazas_Vehiculo INT
                )
            """)
            cursor.execute("INSERT INTO conductores (nombre, Plazas_Vehiculo) VALUES ('Juan Pérez', 55), ('María García', 20), ('Carlos López', 4)")
            conn.commit()
            cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores")
            conductores = cursor.fetchall()

        log(f"👨‍✈️ Conductores disponibles: {len(conductores)}\n")

        # 3. Crear la nueva tabla para las asignaciones
        table_name = 'asignaciones_grupos'
        log(f"Creando tabla nueva '{table_name}'...")
        
        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                grupo_conductor INT, -- Campo solicitado para vincular el grupo
                conductor_id INT,
                conductor_nombre VARCHAR(100),
                hora_inicio VARCHAR(20),
                hora_fin VARCHAR(20),
                total_personas INT,
                fecha_asignacion DATETIME DEFAULT GETDATE()
            )
        """)

        # 4. Asignar conductores a grupos (Validación de capacidad y 1.5h)
        asignaciones = []
        disponibilidad_conductores = {} # {conductor_id: datetime_liberacion}
        
        # Ordenar grupos por total_personas descendente para priorizar los más grandes
        grupos.sort(key=lambda x: x[3], reverse=True)

        for i, grupo in enumerate(grupos):
            grupo_num, hora_inicio, hora_fin, total_personas = grupo
            
            # Convertir horas a datetime para comparar
            try:
                fecha_base = datetime.today().strftime('%Y-%m-%d')
                # Asumimos formato HH:MM:SS en la BD
                dt_inicio = datetime.strptime(f"{fecha_base} {hora_inicio}", "%Y-%m-%d %H:%M:%S")
                dt_fin = datetime.strptime(f"{fecha_base} {hora_fin}", "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                log(f"⚠ Error formato hora en grupo {grupo_num}. Saltando validación estricta.")
                dt_inicio = datetime.now()
                dt_fin = datetime.now()

            conductor_asignado = None
            
            # Buscar candidatos que cumplan capacidad y horario
            candidatos = []
            for cond in conductores:
                cond_id = cond[0]
                plazas = cond[2] if cond[2] is not None else 0
                
                if plazas < total_personas:
                    continue

                hora_liberacion = disponibilidad_conductores.get(cond_id, datetime.min)
                if dt_inicio >= hora_liberacion:
                    candidatos.append(cond)
            
            if candidatos:
                # Elegir el conductor con menor capacidad suficiente (Best Fit)
                candidatos.sort(key=lambda x: (x[2] if x[2] is not None else 0))
                conductor_asignado = candidatos[0]
                cond_id = conductor_asignado[0]
                disponibilidad_conductores[cond_id] = dt_fin + timedelta(hours=1.5)
            
            # (grupo_conductor, conductor_id, conductor_nombre, ...)
            if conductor_asignado:
                asignaciones.append((grupo_num, conductor_asignado[0], conductor_asignado[1], hora_inicio, hora_fin, total_personas))
            else:
                log(f"⚠ Grupo {grupo_num} sin conductor disponible por restricción de 1.5h.")
                asignaciones.append((grupo_num, None, 'SIN ASIGNAR', hora_inicio, hora_fin, total_personas))

        # 5. Guardar en BD
        cursor.executemany(f"INSERT INTO {table_name} (grupo_conductor, conductor_id, conductor_nombre, hora_inicio, hora_fin, total_personas) VALUES (?, ?, ?, ?, ?, ?)", asignaciones)
        conn.commit()
        
        log(f"✓ Se han generado y guardado {len(asignaciones)} asignaciones en '{table_name}'.")

    except Exception as e:
        log(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asignar_conductores()