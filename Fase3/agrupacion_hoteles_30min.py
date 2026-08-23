import pyodbc

from datetime import datetime, timedelta

# Configuración de conexión a SQL Server
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=Test;'
    r'Trusted_Connection=yes;'
)

def agrupar_hoteles_por_tiempo(intervalo_minutos=30):
    """
    Agrupa los hoteles de la tabla 'hoteles' en intervalos configurables (default 30 min)
    basándose únicamente en el campo 'hora' de cada hotel.
    """
    try:
        # Conectar a la base de datos
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("✓ Conexión exitosa a la base de datos.\n")

        # Obtener todos los hoteles con su hora
        query = '''
            SELECT 
                id,
                establecimiento,
                hora,
                personas,
                adultos,
                ninos,
                bebes
            FROM hoteles
            WHERE hora IS NOT NULL
            ORDER BY hora ASC
        '''
        
        cursor.execute(query)
        hoteles_raw = cursor.fetchall()
        
        if not hoteles_raw:
            print("⚠ No se encontraron hoteles en la base de datos.")
            return []

        print(f"📊 Total de hoteles encontrados: {len(hoteles_raw)}\n")

        # Procesar hoteles y convertir horas a objetos datetime
        hoteles_procesados = []
        for row in hoteles_raw:
            hotel_id, establecimiento, hora_str, personas, adultos, ninos, bebes = row
            
            try:
                # Convertir la hora string a objeto time
                hora_time = datetime.strptime(hora_str, '%H:%M:%S').time()
                
                # Crear objeto datetime para facilitar cálculos
                hora_datetime = datetime.combine(datetime.today(), hora_time)
                
                hoteles_procesados.append({
                    'id': hotel_id,
                    'establecimiento': establecimiento or 'Sin nombre',
                    'hora': hora_time,
                    'hora_datetime': hora_datetime,
                    'personas': personas or 0,
                    'adultos': adultos or 0,
                    'ninos': ninos or 0,
                    'bebes': bebes or 0
                })
            except ValueError as e:
                print(f"⚠ Advertencia: Formato de hora inválido para hotel {hotel_id} ({hora_str}). Ignorado.")
                continue

        if not hoteles_procesados:
            print("⚠ No se pudieron procesar hoteles con horas válidas.")
            return []

        # Algoritmo de agrupación por intervalos de 30 minutos
        grupos = []
        grupo_actual = []
        hora_inicio_grupo = None
        
        print("=" * 80)
        print("PROCESO DE AGRUPACIÓN (Intervalo máximo: 30 minutos)")
        print("=" * 80 + "\n")

        for i, hotel in enumerate(hoteles_procesados):
            if not grupo_actual:
                # Iniciar el primer grupo
                grupo_actual.append(hotel)
                hora_inicio_grupo = hotel['hora_datetime']
                print(f"🆕 Grupo {len(grupos) + 1} iniciado")
                print(f"   └─ Hotel {hotel['id']}: {hotel['establecimiento']} a las {hotel['hora']}")
            else:
                # Calcular diferencia de tiempo desde el inicio del grupo
                diferencia_segundos = (hotel['hora_datetime'] - hora_inicio_grupo).total_seconds()
                diferencia_minutos = diferencia_segundos / 60
                
                if diferencia_segundos <= (intervalo_minutos * 60):
                    # El hotel cabe en el grupo actual
                    grupo_actual.append(hotel)
                    print(f"   ├─ Hotel {hotel['id']}: {hotel['establecimiento']} a las {hotel['hora']} (+{diferencia_minutos:.1f} min)")
                else:
                    # El hotel excede los 30 minutos, cerrar grupo actual
                    grupos.append({
                        'numero': len(grupos) + 1,
                        'hoteles': grupo_actual,
                        'hora_inicio': hora_inicio_grupo.time(),
                        'hora_fin': grupo_actual[-1]['hora_datetime'].time(),
                        'total_hoteles': len(grupo_actual),
                        'total_personas': sum(h['personas'] for h in grupo_actual),
                        'total_adultos': sum(h['adultos'] for h in grupo_actual),
                        'total_ninos': sum(h['ninos'] for h in grupo_actual),
                        'total_bebes': sum(h['bebes'] for h in grupo_actual)
                    })
                    
                    print(f"   └─ ✓ Grupo cerrado ({len(grupo_actual)} hoteles)\n")
                    
                    # Iniciar nuevo grupo con el hotel actual
                    grupo_actual = [hotel]
                    hora_inicio_grupo = hotel['hora_datetime']
                    print(f"🆕 Grupo {len(grupos) + 1} iniciado")
                    print(f"   └─ Hotel {hotel['id']}: {hotel['establecimiento']} a las {hotel['hora']}")

        # Añadir el último grupo
        if grupo_actual:
            grupos.append({
                'numero': len(grupos) + 1,
                'hoteles': grupo_actual,
                'hora_inicio': hora_inicio_grupo.time(),
                'hora_fin': grupo_actual[-1]['hora_datetime'].time(),
                'total_hoteles': len(grupo_actual),
                'total_personas': sum(h['personas'] for h in grupo_actual),
                'total_adultos': sum(h['adultos'] for h in grupo_actual),
                'total_ninos': sum(h['ninos'] for h in grupo_actual),
                'total_bebes': sum(h['bebes'] for h in grupo_actual)
            })
            print(f"   └─ ✓ Grupo cerrado ({len(grupo_actual)} hoteles)\n")

        # Mostrar resumen de grupos
        print("\n" + "=" * 80)
        print("RESUMEN DE AGRUPACIÓN")
        print("=" * 80 + "\n")
        print(f"📦 Total de grupos formados: {len(grupos)}\n")

        for grupo in grupos:
            print(f"┌─ GRUPO {grupo['numero']} ─────────────────────────────────────────")
            print(f"│  ⏰ Horario: {grupo['hora_inicio']} - {grupo['hora_fin']}")
            print(f"│  🏨 Hoteles: {grupo['total_hoteles']}")
            print(f"│  👥 Personas: {grupo['total_personas']} (Adultos: {grupo['total_adultos']}, Niños: {grupo['total_ninos']}, Bebés: {grupo['total_bebes']})")
            print(f"│")
            print(f"│  Detalle de hoteles:")
            for hotel in grupo['hoteles']:
                print(f"│    • [{hotel['id']}] {hotel['establecimiento'][:40]} - {hotel['hora']} ({hotel['personas']} pax)")
            print(f"└{'─' * 70}\n")

        # Cerrar conexión
        cursor.close()
        conn.close()
        print("✓ Conexión a la base de datos cerrada.")
        
        return grupos

    except pyodbc.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []


def guardar_grupos_en_bd(grupos):
    """
    Guarda los grupos formados en una tabla de la base de datos.
    """
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            IF OBJECT_ID('grupos_hoteles', 'U') IS NULL
            CREATE TABLE grupos_hoteles (
                id INT IDENTITY(1,1) PRIMARY KEY,
                grupo_numero INT,
                hotel_id INT,
                establecimiento VARCHAR(255),
                hora VARCHAR(20),
                personas INT,
                hora_inicio_grupo VARCHAR(20),
                hora_fin_grupo VARCHAR(20),
                total_personas_grupo INT,
                fecha_creacion DATETIME DEFAULT GETDATE()
            )
        ''')
        
        # Limpiar tabla antes de insertar
        cursor.execute('DELETE FROM grupos_hoteles')
        
        # Insertar grupos
        for grupo in grupos:
            for hotel in grupo['hoteles']:
                cursor.execute('''
                    INSERT INTO grupos_hoteles 
                    (grupo_numero, hotel_id, establecimiento, hora, personas, 
                     hora_inicio_grupo, hora_fin_grupo, total_personas_grupo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', 
                    grupo['numero'],
                    hotel['id'],
                    hotel['establecimiento'],
                    str(hotel['hora']),
                    hotel['personas'],
                    str(grupo['hora_inicio']),
                    str(grupo['hora_fin']),
                    grupo['total_personas']
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ Grupos guardados exitosamente en la tabla 'grupos_hoteles'")
        
    except Exception as e:
        print(f"\n❌ Error al guardar grupos en BD: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AGRUPACIÓN DE HOTELES POR INTERVALOS DE 30 MINUTOS")
    print("=" * 80 + "\n")
    
    # Ejecutar agrupación
    grupos = agrupar_hoteles_por_tiempo()    

    guardar_grupos_en_bd(grupos)
    
    print("\n" + "=" * 80)
    print("PROCESO FINALIZADO")
    print("=" * 80 + "\n")
