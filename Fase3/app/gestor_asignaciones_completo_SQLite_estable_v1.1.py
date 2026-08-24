import sqlite3
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import shutil
import xml.etree.ElementTree as ET
import re
import random
import configparser

def instalar_paquete(paquete):
    try:
        print(f"Detectado {paquete} faltante. Instalando automáticamente...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])
        print(f"✓ {paquete} instalado correctamente.")
    except subprocess.CalledProcessError:
        print(f"❌ Error al intentar instalar {paquete}.")

# Verificación de dependencia CustomTkinter
try:
    import customtkinter as ctk
except ImportError:
    instalar_paquete("customtkinter")
    try:
        import customtkinter as ctk
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error Crítico", "No se pudo instalar 'customtkinter' automáticamente.\n\nPor favor ejecuta manualmente:\npip install customtkinter")
        sys.exit(1)

try:
    from tkcalendar import DateEntry
except ImportError:
    instalar_paquete("tkcalendar")
    try:
        from tkcalendar import DateEntry
    except ImportError:
        DateEntry = None

# Configuración de conexión a SQLite

def resolver_ruta_base():
    """Devuelve la carpeta correcta tanto en modo script como en EXE empaquetado."""
    if getattr(sys, 'frozen', False):
        # En modo EXE, buscar desde el directorio del ejecutable
        candidates = []
        if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
            candidates.append(sys._MEIPASS)
        if getattr(sys, 'executable', None):
            candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
        candidates.append(os.getcwd())
        return candidates[0] if candidates else os.getcwd()
    
    # En modo script, retornar el directorio de Fase3 (padre del directorio app/)
    if __file__:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(app_dir)  # Sube de app/ a Fase3/
    return os.getcwd()


BASE_DIR = resolver_ruta_base()


def resolver_ruta_archivo(nombre_archivo, subcarpeta=''):
    """Busca un archivo en la estructura de carpetas reorganizada."""
    if getattr(sys, 'frozen', False):
        # En EXE, buscar en data/ o logs/ según el archivo
        if nombre_archivo == "gestor_datos.db":
            subcarpeta = 'data'
        elif nombre_archivo == "log_asignacion_conductores.txt":
            subcarpeta = 'logs'
        elif nombre_archivo == "config.ini":
            subcarpeta = 'data'
        
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        if subcarpeta:
            path = os.path.join(exe_dir, subcarpeta, nombre_archivo)
            if os.path.exists(path):
                return path
        path = os.path.join(exe_dir, nombre_archivo)
        if os.path.exists(path):
            return path
        # Fallback: buscar junto al exe
        return os.path.join(exe_dir, nombre_archivo)
    
    # En modo script, usar la estructura de carpetas
    if nombre_archivo == "gestor_datos.db":
        subcarpeta = 'data'
    elif nombre_archivo == "log_asignacion_conductores.txt":
        subcarpeta = 'logs'
    elif nombre_archivo == "config.ini":
        subcarpeta = 'data'
    
    if subcarpeta:
        path = os.path.join(BASE_DIR, subcarpeta, nombre_archivo)
        if os.path.exists(path):
            return path
    
    # Fallback en BASE_DIR
    path = os.path.join(BASE_DIR, nombre_archivo)
    if os.path.exists(path):
        return path
    
    # Último intento: en el cwd
    if os.path.exists(nombre_archivo):
        return os.path.abspath(nombre_archivo)
    
    # Default: retornar ruta esperada en data/
    if subcarpeta:
        return os.path.join(BASE_DIR, subcarpeta, nombre_archivo)
    return os.path.join(BASE_DIR, nombre_archivo)


DB_FILE = resolver_ruta_archivo("gestor_datos.db")
LOG_FILE = resolver_ruta_archivo("log_asignacion_conductores.txt")
GUI_LOG_CALLBACK = None

def log(mensaje):
    """Imprime el mensaje y lo guarda en un archivo de texto con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(mensaje)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
    except Exception:
        pass
    
    if GUI_LOG_CALLBACK:
        try:
            GUI_LOG_CALLBACK(f"[{timestamp}] {mensaje}")
        except Exception:
            pass

def inicializar_tablas():
    """Crea las tablas necesarias en SQLite si no existen."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Tabla conductores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conductores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                Plazas_Vehiculo INTEGER,
                activo INTEGER DEFAULT 1
            )
        """)
        
        # Tabla albaranes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albaranes (
                numero TEXT PRIMARY KEY,
                empresa TEXT,
                fecha TEXT,
                tiporec TEXT,
                alias TEXT,
                proveedor TEXT,
                tiposer TEXT,
                hora TEXT,
                hora_aeropuerto TEXT,
                letrero TEXT,
                ttoo TEXT,
                agencia TEXT,
                excursion TEXT,
                guia TEXT,
                aeropuerto TEXT,
                vuelo TEXT,
                observacion TEXT,
                referencia TEXT,
                observacion_chofer TEXT
            )
        """)
        
        # Tabla zonas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zonas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                albaran_id TEXT,
                orden TEXT,
                zona_inicio TEXT,
                zona_fin TEXT,
                hora TEXT,
                personas INTEGER,
                adultos INTEGER,
                ninos INTEGER,
                bicis INTEGER,
                bebes INTEGER,
                ninosb INTEGER,
                invitados INTEGER
            )
        """)
        
        # Tabla hoteles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hoteles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id INTEGER,
                albaran TEXT,
                orden TEXT,
                establecimiento TEXT,
                hora TEXT,
                personas INTEGER,
                adultos INTEGER,
                ninos INTEGER,
                bebes INTEGER,
                bicis INTEGER,
                agencia TEXT,
                lugar_recogida TEXT,
                observacion TEXT
            )
        """)
        
        # Tabla registro de actividad (Auditoría)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_actividad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                accion TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pid INTEGER
            )
        """)
        
        # Verificar si existe la columna pid (migración para bases de datos existentes)
        cursor.execute("PRAGMA table_info(registro_actividad)")
        cols_actividad = [c[1] for c in cursor.fetchall()]
        if 'pid' not in cols_actividad:
            try:
                cursor.execute("ALTER TABLE registro_actividad ADD COLUMN pid INTEGER")
            except Exception as e:
                log(f"Error migrando tabla registro_actividad: {e}")
        
        # Tabla sesiones activas (Control de concurrencia)
        # Verificar si la tabla existe con el esquema antiguo para migrar
        cursor.execute("PRAGMA table_info(sesiones_activas)")
        cols = cursor.fetchall()
        is_old_schema = False
        if cols:
            # Si fecha_inicio NO es parte de la PK (pk=0), es el esquema viejo
            for col in cols:
                if col[1] == 'fecha_inicio' and col[5] == 0:
                    is_old_schema = True
                    break
        
        if is_old_schema:
            cursor.execute("DROP TABLE IF EXISTS sesiones_activas")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones_activas (
                usuario TEXT,
                fecha_inicio TEXT,
                pid INTEGER,
                PRIMARY KEY (usuario, fecha_inicio)
            )
        """)
        
        # Índices para mejorar rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asignaciones_conductor ON asignaciones_grupos(conductor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_grupos_hoteles_numero ON grupos_hoteles(grupo_numero)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hoteles_zona ON hoteles(zona_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zonas_albaran ON zonas(albaran_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_albaranes_fecha ON albaranes(fecha)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hoteles_albaran ON hoteles(albaran)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hoteles_hora ON hoteles(hora)")

        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Error inicializando tablas: {e}")

# ==============================================================================
# FUNCIONES DE AUDITORÍA Y USUARIO
# ==============================================================================

def obtener_usuario_actual():
    try:
        return os.getlogin()
    except:
        return os.environ.get('USERNAME', os.environ.get('USER', 'Desconocido'))

def registrar_actividad(accion):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        usuario = obtener_usuario_actual()
        pid = os.getpid()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO registro_actividad (usuario, accion, pid, fecha) VALUES (?, ?, ?, ?)", (usuario, accion, pid, fecha))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Error registrando actividad: {e}")

def registrar_inicio_sesion(fecha_inicio):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        usuario = obtener_usuario_actual()
        pid = os.getpid()
        cursor.execute("INSERT INTO sesiones_activas (usuario, fecha_inicio, pid) VALUES (?, ?, ?)", (usuario, fecha_inicio, pid))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Error registrando inicio sesión: {e}")

def registrar_fin_sesion(fecha_inicio):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        usuario = obtener_usuario_actual()
        pid = os.getpid()
        cursor.execute("DELETE FROM sesiones_activas WHERE usuario = ? AND fecha_inicio = ?", (usuario, fecha_inicio))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Error registrando fin sesión: {e}")

# ==============================================================================
# PARTE 0: IMPORTACIÓN DE ALBARANES
# ==============================================================================

def importar_albaranes_xml(xml_path, conexion):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        cursor = conexion.cursor()
        
        albaranes_data = []
        zonas_data = []
        hoteles_data = []

        for albaran in root.find('Albaranes').findall('Albaran'):
            numero = albaran.findtext('Numero')
            # ... recopilar datos de albarán ...
            albaranes_data.append((
                numero, albaran.findtext('Empresa'), albaran.findtext('Fecha'), albaran.findtext('TipoRec'),
                albaran.findtext('Alias'), albaran.findtext('Proveedor'), albaran.findtext('TipoSer'),
                albaran.findtext('Hora'), albaran.findtext('HoraAeropuerto'), albaran.findtext('Letrero'),
                albaran.findtext('TTOO'), albaran.findtext('Agencia'), albaran.findtext('Excursion'),
                albaran.findtext('Guia'), albaran.findtext('Aeropuerto'), albaran.findtext('Vuelo'),
                albaran.findtext('Observacion'), albaran.findtext('Referencia'), albaran.findtext('ObservacionChofer')
            ))
            
            zonas = albaran.find('Zonas')
            if zonas is not None:
                for zona in zonas.findall('Zona'):
                    # Para zonas necesitamos el ID generado, así que aquí seguiremos insertando 
                    # pero envolviendo todo en una transacción (que ya hace el commit al final)
                    # No obstante, para máxima velocidad usaremos un truco: insertar albaranes primero en lote.
                    pass

        # Inserción en lote de albaranes
        cursor.executemany(
            """
            INSERT OR REPLACE INTO albaranes (numero, empresa, fecha, tiporec, alias, proveedor, tiposer, hora, hora_aeropuerto, letrero, ttoo, agencia, excursion, guia, aeropuerto, vuelo, observacion, referencia, observacion_chofer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            albaranes_data
        )

        # Para Zonas y Hoteles, como hay dependencia de lastrowid, procesamos con cuidado
        # pero mantenemos la conexión abierta para que sea una sola transacción.
        for albaran in root.find('Albaranes').findall('Albaran'):
            numero = albaran.findtext('Numero')
            zonas = albaran.find('Zonas')
            if zonas is not None:
                for zona in zonas.findall('Zona'):
                    cursor.execute(
                        """
                        INSERT INTO zonas (albaran_id, orden, zona_inicio, zona_fin, hora, personas, adultos, ninos, bicis, bebes, ninosb, invitados)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (numero, zona.findtext('Orden'), zona.findtext('ZonaInicio'), zona.findtext('ZonaFin'), 
                         zona.findtext('Hora'), zona.findtext('Personas'), zona.findtext('Adultos'), 
                         zona.findtext('Niños'), zona.findtext('Bicis'), zona.findtext('Bebes'), 
                         zona.findtext('NiñosB'), zona.findtext('Invitados'))
                    )
                    zona_id = cursor.lastrowid
                    
                    hoteles = zona.find('Hoteles')
                    if hoteles is not None:
                        for hotel in hoteles.findall('Hotel'):
                            cursor.execute(
                                """
                                INSERT INTO hoteles (zona_id, albaran, orden, establecimiento, hora, personas, adultos, ninos, bebes, bicis, agencia, lugar_recogida, observacion)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (zona_id, numero, hotel.findtext('Orden'), hotel.findtext('Establecimiento'), 
                                 hotel.findtext('Hora'), hotel.findtext('Personas'), hotel.findtext('Adultos'), 
                                 hotel.findtext('Niños'), hotel.findtext('Bebes'), hotel.findtext('Bicis'), 
                                 hotel.findtext('Agencia'), hotel.findtext('LugarRecogida'), hotel.findtext('Observacion'))
                            )
        
        conexion.commit()
        log(f'✓ Importación optimizada completada ({len(albaranes_data)} albaranes).')
        cursor.close()
    except Exception as e:
        conexion.rollback()
        log(f'❌ Error al importar XML: {e}')
        raise e

# ==============================================================================
# PARTE 1: AGRUPACIÓN DE HOTELES
# ==============================================================================

def parsear_fecha(fecha_str):
    """Convierte strings de fecha (DD/MM/YYYY o texto) a objeto date."""
    if not fecha_str:
        return datetime.today().date()
    
    # Formato DD/MM/YYYY
    match_simple = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", fecha_str)
    if match_simple:
        return datetime(int(match_simple.group(3)), int(match_simple.group(2)), int(match_simple.group(1))).date()
    
    # Formato largo: "Martes, 17 de Junio de 2025"
    try:
        partes = fecha_str.lower().replace(',', '').split()
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        dia = int([p for p in partes if p.isdigit() and int(p) <= 31][0])
        anio = int([p for p in partes if p.isdigit() and int(p) > 1000][0])
        mes = next((v for k, v in meses.items() if k in fecha_str.lower()), 1)
        return datetime(anio, mes, dia).date()
    except:
        return datetime.today().date()

def agrupar_hoteles_por_tiempo(intervalo_minutos=30, solo_salidas=True):
    """
    Agrupa los hoteles de la tabla 'hoteles' en intervalos configurables (default 30 min).
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        log("--- Inicio Agrupación de Hoteles ---")

        query = '''
            SELECT h.id, h.establecimiento, h.hora, h.personas, h.adultos, h.ninos, h.bebes, h.zona_id, a.tiposer, a.fecha
            FROM hoteles h
            LEFT JOIN albaranes a ON h.albaran = a.numero
            WHERE h.hora IS NOT NULL ORDER BY h.zona_id, h.hora ASC
        '''
        cursor.execute(query)
        hoteles_raw = cursor.fetchall()
        
        if not hoteles_raw:
            log("⚠ No se encontraron hoteles en la base de datos.")
            return []

        log(f"Procesando {len(hoteles_raw)} hoteles candidatos...")
        hoteles_procesados = []
        ignorados = 0

        for row in hoteles_raw:
            hotel_id, establecimiento, hora_str, personas, adultos, ninos, bebes, zona_id, tiposer, fecha_str = row
            
            tiposer_upper = tiposer.upper() if tiposer else ''

            # Filtro por tipo de servicio
            if solo_salidas:
                if tiposer_upper != 'S':
                    ignorados += 1
                    continue
            else:
                if tiposer_upper not in ('S', 'E'):
                    ignorados += 1
                    continue

            try:
                # Manejo flexible de formatos de hora
                if isinstance(hora_str, str):
                    # SQLite a veces guarda solo HH:MM, aseguramos segundos
                    if len(hora_str) == 5: hora_str += ":00"
                    hora_time = datetime.strptime(hora_str, '%H:%M:%S').time()
                else:
                    hora_time = hora_str 
                
                fecha_obj = parsear_fecha(fecha_str)
                hora_datetime = datetime.combine(fecha_obj, hora_time)
                
                hoteles_procesados.append({
                    'id': hotel_id,
                    'establecimiento': establecimiento or 'Sin nombre',
                    'hora': hora_time,
                    'hora_datetime': hora_datetime,
                    'personas': personas or 0,
                    'zona_id': zona_id,
                    'tiposer': tiposer_upper
                })
            except ValueError:
                continue

        # Reordenar por Zona y luego por Fecha+Hora real (crucial para cruces de medianoche y múltiples días)
        hoteles_procesados.sort(key=lambda x: (x['zona_id'], x['hora_datetime']))

        grupos = []
        grupo_actual = []
        hora_inicio_grupo = None
        
        for hotel in hoteles_procesados:
            if not grupo_actual:
                grupo_actual.append(hotel)
                hora_inicio_grupo = hotel['hora_datetime']
            else:
                # Verificar misma zona, mismo tipo de servicio y tiempo
                misma_zona = (hotel['zona_id'] == grupo_actual[0]['zona_id'])
                mismo_tipo = (hotel['tiposer'] == grupo_actual[0]['tiposer'])
                diferencia_segundos = (hotel['hora_datetime'] - hora_inicio_grupo).total_seconds()
                
                if misma_zona and mismo_tipo and diferencia_segundos <= (intervalo_minutos * 60):
                    grupo_actual.append(hotel)
                else:
                    grupos.append({
                        'numero': len(grupos) + 1,
                        'hoteles': grupo_actual,
                        'hora_inicio': hora_inicio_grupo, # Guardamos datetime completo
                        'hora_fin': grupo_actual[-1]['hora_datetime'], # Guardamos datetime completo
                        'total_personas': sum(h['personas'] for h in grupo_actual)
                    })
                    grupo_actual = [hotel]
                    hora_inicio_grupo = hotel['hora_datetime']

        if grupo_actual:
            grupos.append({
                'numero': len(grupos) + 1,
                'hoteles': grupo_actual,
                'hora_inicio': hora_inicio_grupo,
                'hora_fin': grupo_actual[-1]['hora_datetime'],
                'total_personas': sum(h['personas'] for h in grupo_actual)
            })

        if ignorados > 0:
            log(f"ℹ Se ignoraron {ignorados} hoteles por configuración de tipo de servicio.")
            
        log(f"✓ Agrupación completada: {len(grupos)} grupos formados con {len(hoteles_procesados)} hoteles.")
        conn.close()
        return grupos

    except Exception as e:
        log(f"❌ Error en agrupación: {e}")
        return []

def guardar_grupos_en_bd(grupos):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grupos_hoteles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo_numero INTEGER,
                hotel_id INTEGER,
                establecimiento TEXT,
                hora TEXT,
                personas INTEGER,
                hora_inicio_grupo TEXT,
                hora_fin_grupo TEXT,
                total_personas_grupo INTEGER,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute('DELETE FROM grupos_hoteles')
        
        for grupo in grupos:
            for hotel in grupo['hoteles']:
                cursor.execute('''
                    INSERT INTO grupos_hoteles 
                    (grupo_numero, hotel_id, establecimiento, hora, personas, 
                     hora_inicio_grupo, hora_fin_grupo, total_personas_grupo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', 
                    (grupo['numero'], hotel['id'], hotel['establecimiento'], str(hotel['hora']),
                    hotel['personas'], str(grupo['hora_inicio']), str(grupo['hora_fin']),
                    grupo['total_personas'])
                )
        conn.commit()
        conn.close()
        log("✓ Grupos guardados en BD 'grupos_hoteles'.")
    except Exception as e:
        log(f"❌ Error guardando grupos: {e}")

# ==============================================================================
# PARTE 2: ASIGNACIÓN DE CONDUCTORES
# ==============================================================================

def ejecutar_asignacion_conductores(margen_minutos=120, margen_salida_entrada=150, max_horas_trabajo=9):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        log("--- Inicio Asignación de Conductores ---")

        # 1. Obtener grupos
        query_grupos = '''
            SELECT gh.grupo_numero, MAX(gh.hora_inicio_grupo), MAX(gh.hora_fin_grupo), MAX(gh.total_personas_grupo), MAX(a.tiposer)
            FROM grupos_hoteles gh
            LEFT JOIN hoteles h ON gh.hotel_id = h.id
            LEFT JOIN albaranes a ON h.albaran = a.numero
            GROUP BY gh.grupo_numero ORDER BY gh.grupo_numero
        '''
        try:
            cursor.execute(query_grupos)
            grupos = cursor.fetchall()
        except sqlite3.Error:
            log("❌ Error leyendo 'grupos_hoteles'.")
            return

        if not grupos:
            log("⚠ No hay grupos para asignar.")
            return

        # 2. Obtener conductores
        try:
            cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores WHERE activo=1")
            conductores = cursor.fetchall()
            if not conductores:
                # Fallback si no hay activos o tabla vacía
                cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores")
                conductores = cursor.fetchall()
        except sqlite3.Error:
            log("❌ Error leyendo tabla 'conductores'.")
            return

        if not conductores:
            log("❌ No hay conductores disponibles en la BD.")
            return

        # 3. Crear tabla asignaciones
        table_name = 'asignaciones_grupos'
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo_conductor INTEGER,
                conductor_id INTEGER,
                conductor_nombre TEXT,
                hora_inicio TEXT,
                hora_fin TEXT,
                total_personas INTEGER,
                fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_servicio TEXT
            )
        """)

        # 4. Asignar (Capacidad + Margen Configurable check)
        asignaciones = []
        disponibilidad = {} # {conductor_id: datetime_liberacion}
        
        log(f"--- Iniciando Asignación ---")
        log(f"Condiciones activas:")
        log(f"  1. Margen General: {margen_minutos} minutos")
        log(f"  2. Margen Salida -> Entrada: {margen_salida_entrada} minutos")
        log(f"  3. Orden de proceso: Cronológico (por hora de inicio)")
        log(f"  4. Criterio selección: Vehículo más ajustado (Best Fit)")
        log(f"  5. Máximo horas trabajo: {max_horas_trabajo}h")
        
        # Ordenar grupos por HORA (cronológico) para que la disponibilidad funcione correctamente
        grupos.sort(key=lambda x: x[1])

        for i, grupo in enumerate(grupos):
            grupo_num, hora_inicio, hora_fin, total_personas, tipo_servicio = grupo
            tipo_servicio_actual = str(tipo_servicio).upper() if tipo_servicio else ''
            
            try:
                # Intentar parsear formato completo YYYY-MM-DD HH:MM:SS
                dt_inicio = datetime.strptime(str(hora_inicio), "%Y-%m-%d %H:%M:%S")
                dt_fin = datetime.strptime(str(hora_fin), "%Y-%m-%d %H:%M:%S")
            except:
                # Fallback para datos antiguos (solo hora) - Asume HOY (comportamiento legacy)
                fecha_base = datetime.today().strftime('%Y-%m-%d')
                try:
                    dt_inicio = datetime.strptime(f"{fecha_base} {hora_inicio}", "%Y-%m-%d %H:%M:%S")
                    dt_fin = datetime.strptime(f"{fecha_base} {hora_fin}", "%Y-%m-%d %H:%M:%S")
                except:
                    dt_inicio = datetime.now()
                    dt_fin = datetime.now()
            
            duracion_servicio = dt_fin - dt_inicio

            conductor_asignado = None
            
            candidatos = []
            motivo_rechazo = "Sin conductores disponibles" # Default
            for cond in conductores:
                cond_id = cond[0]
                plazas = cond[2] if cond[2] is not None else 0
                
                if plazas < total_personas:
                    if motivo_rechazo == "Sin conductores disponibles":
                        motivo_rechazo = "Falta de capacidad en vehículos"
                    continue

                # Verificar límite de horas de trabajo
                datos_cond = disponibilidad.get(cond_id, {})
                tiempo_acumulado = datos_cond.get('tiempo_total', timedelta(0))
                
                if (tiempo_acumulado + duracion_servicio).total_seconds() > (max_horas_trabajo * 3600):
                    if motivo_rechazo == "Sin conductores disponibles":
                        motivo_rechazo = "Excede límite horas trabajo"
                    continue

                estado_conductor = disponibilidad.get(cond_id)
                if not estado_conductor: # Es la primera tarea para este conductor
                    candidatos.append(cond)
                    continue

                # El conductor ya tiene tareas, hay que verificar márgenes
                fin_ultimo_servicio = estado_conductor['fin_ultimo_servicio']
                tipo_ultimo_servicio = estado_conductor['tipo_ultimo_servicio']

                margen_requerido_minutos = margen_minutos
                if 'S' in str(tipo_ultimo_servicio).upper() and 'E' in tipo_servicio_actual:
                    margen_requerido_minutos = margen_salida_entrada
                
                hora_liberacion_calculada = fin_ultimo_servicio + timedelta(minutes=margen_requerido_minutos)

                if dt_inicio >= hora_liberacion_calculada:
                    candidatos.append(cond)
                else:
                    motivo_rechazo = f"Restricción horario ({margen_requerido_minutos} min)"
            
            if candidatos:
                candidatos.sort(key=lambda x: (x[2] if x[2] is not None else 0))
                conductor_asignado = candidatos[0]
                
                # Actualizar disponibilidad con tiempo acumulado
                prev_data = disponibilidad.get(conductor_asignado[0], {})
                prev_time = prev_data.get('tiempo_total', timedelta(0))
                
                disponibilidad[conductor_asignado[0]] = {'fin_ultimo_servicio': dt_fin, 'tipo_ultimo_servicio': tipo_servicio_actual, 'tiempo_total': prev_time + duracion_servicio}
                
                log(f"  [OK] Grupo {grupo_num} ({total_personas} pax) -> {conductor_asignado[1]} ({conductor_asignado[2]} plazas)")
            
            if conductor_asignado:
                asignaciones.append((grupo_num, conductor_asignado[0], conductor_asignado[1], hora_inicio, hora_fin, total_personas, tipo_servicio))
            else:
                # Log detallado de por qué falló para este grupo
                log(f"  [FAIL] Grupo {grupo_num} ({total_personas} pax, {hora_inicio}) NO ASIGNADO:")
                
                detalles_bd = [] # Lista para acumular razones y guardarlas en BD
                for cond in conductores:
                    cond_id = cond[0]
                    plazas = cond[2] if cond[2] is not None else 0
                    estado_conductor = disponibilidad.get(cond_id)
                    
                    tiempo_acumulado = estado_conductor.get('tiempo_total', timedelta(0)) if estado_conductor else timedelta(0)
                    
                    razon = ""
                    if plazas < total_personas:
                        razon = f"Capacidad ({plazas}<{total_personas})"
                    elif (tiempo_acumulado + duracion_servicio).total_seconds() > (max_horas_trabajo * 3600):
                        horas_totales = (tiempo_acumulado + duracion_servicio).total_seconds() / 3600
                        razon = f"Excede horas ({horas_totales:.1f} > {max_horas_trabajo})"
                    elif estado_conductor:
                        fin_ultimo_servicio = estado_conductor['fin_ultimo_servicio']
                        tipo_ultimo_servicio = estado_conductor['tipo_ultimo_servicio']

                        margen_requerido_minutos = margen_minutos
                        if 'S' in str(tipo_ultimo_servicio).upper() and 'E' in tipo_servicio_actual:
                            margen_requerido_minutos = margen_salida_entrada
                        
                        hora_liberacion_calculada = fin_ultimo_servicio + timedelta(minutes=margen_requerido_minutos)

                        if dt_inicio < hora_liberacion_calculada:
                            razon = f"Ocupado hasta {hora_liberacion_calculada.strftime('%H:%M')} (margen {margen_requerido_minutos} min)"
                    
                    if razon:
                        log(f"    - {cond[1]}: {razon}")
                        detalles_bd.append(f"{cond[1]}: {razon}")
                
                # Guardar el desglose completo en la BD
                motivo_completo = f'SIN ASIGNAR:\n' + "\n".join(detalles_bd) if detalles_bd else f'SIN ASIGNAR: {motivo_rechazo}'
                asignaciones.append((grupo_num, None, motivo_completo, hora_inicio, hora_fin, total_personas, tipo_servicio))

        cursor.executemany(f"INSERT INTO {table_name} (grupo_conductor, conductor_id, conductor_nombre, hora_inicio, hora_fin, total_personas, tipo_servicio) VALUES (?, ?, ?, ?, ?, ?, ?)", asignaciones)
        conn.commit()
        log(f"✓ Asignación completada: {len(asignaciones)} registros.")
        conn.close()

    except Exception as e:
        log(f"❌ Error en asignación: {e}")

# ==============================================================================
# PARTE 2B: ASIGNACIÓN ALEATORIA DE CONDUCTORES
# ==============================================================================

def asignar_conductores_aleatorios(cantidad=5, nombre_prefijo="Conductor", apellido_prefijo="Test", 
                                   incluir_dni=True, tipos_licencia=None, plazas_opciones=None, activo=True):
    """
    Inserta conductores aleatorios en la base de datos.
    
    Args:
        cantidad: Número de conductores a insertar
        nombre_prefijo: Prefijo para generar nombres aleatorios
        apellido_prefijo: Prefijo para generar apellidos aleatorios
        incluir_dni: Si True, genera DNI aleatorios
        tipos_licencia: Lista de tipos de licencia válidos (ej: ['A', 'B', 'C'])
        plazas_opciones: Lista de opciones de plazas de vehículo (ej: [4, 20, 55])
        activo: Si los conductores están activos por defecto
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Valores por defecto
        if tipos_licencia is None:
            tipos_licencia = ['A', 'B', 'C']
        if plazas_opciones is None:
            plazas_opciones = [4, 20, 55]
        
        log(f"--- Inicio Asignación Aleatoria de Conductores ---")
        log(f"Parámetros:")
        log(f"  - Cantidad: {cantidad}")
        log(f"  - Tipos de licencia: {tipos_licencia}")
        log(f"  - Opciones de plazas: {plazas_opciones}")
        log(f"  - Activos: {activo}")
        
        conductores_insertados = 0
        
        for i in range(cantidad):
            # Generar datos aleatorios
            nombre = f"{nombre_prefijo}_{random.randint(1000, 9999)}"
            apellido = f"{apellido_prefijo}_{random.randint(100, 999)}"
            
            if incluir_dni:
                dni = f"{random.randint(10000000, 99999999)}"
            else:
                dni = None
            
            numero_licencia = f"LIC{random.randint(1000000, 9999999)}"
            tipo_licencia = random.choice(tipos_licencia)
            fecha_expiracion = "2030-12-31"
            plazas_vehiculo = random.choice(plazas_opciones)
            
            # Insertar en la base de datos
            try:
                cursor.execute(
                    """
                    INSERT INTO conductores (nombre, apellido, dni, numero_licencia, tipo_licencia, 
                                           fecha_expiracion_licencia, Plazas_Vehiculo, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (nombre, apellido, dni, numero_licencia, tipo_licencia, fecha_expiracion, 
                     plazas_vehiculo, 1 if activo else 0)
                )
                conductores_insertados += 1
                log(f"  ✓ Insertado: {nombre} {apellido} ({plazas_vehiculo} plazas, Lic. {tipo_licencia})")
                
            except sqlite3.IntegrityError as e:
                log(f"  ⚠ Conductor {nombre} ya existe: {e}")
        
        conn.commit()
        conn.close()
        
        log(f"✓ Asignación aleatoria completada: {conductores_insertados} conductores insertados.")
        return conductores_insertados
        
    except Exception as e:
        log(f"❌ Error en asignación aleatoria: {e}")
        return 0

def cargar_config_conductores():
    """
    Carga la configuración de conductores desde config.ini
    Retorna un diccionario con los parámetros
    """
    try:
        import configparser
        config = configparser.ConfigParser()
        
        # Intentar leer config.ini en el mismo directorio que el script o el ejecutable
        config_path = resolver_ruta_archivo("config.ini")
        if not os.path.exists(config_path):
            log("⚠ config.ini no encontrado, usando valores por defecto")
            return None
        
        config.read(config_path)
        
        if not config.has_section("CONDUCTORES"):
            log("⚠ Sección [CONDUCTORES] no encontrada en config.ini")
            return None
        
        # Leer valores de configuración
        config_dict = {
            "cantidad": config.getint("CONDUCTORES", "cantidad_aleatoria", fallback=5),
            "nombre_prefijo": config.get("CONDUCTORES", "nombre_prefijo", fallback="Conductor"),
            "apellido_prefijo": config.get("CONDUCTORES", "apellido_prefijo", fallback="Test"),
            "incluir_dni": config.getboolean("CONDUCTORES", "incluir_dni", fallback=True),
            "tipos_licencia": config.get("CONDUCTORES", "tipos_licencia", fallback="A,B,C").split(","),
            "plazas_vehiculo": [int(x.strip()) for x in config.get("CONDUCTORES", "plazas_vehiculo", fallback="4,20,55").split(",")],
            "activo": config.getboolean("CONDUCTORES", "activo_por_defecto", fallback=True)
        }
        
        # Limpiar espacios en blanco
        config_dict["tipos_licencia"] = [x.strip() for x in config_dict["tipos_licencia"]]
        
        return config_dict
        
    except Exception as e:
        log(f"⚠ Error cargando config.ini: {e}")
        return None

# ==============================================================================
# PARTE 3: INTERFAZ GRÁFICA
# ==============================================================================

class KanbanBoard(ctk.CTk): # Heredamos de CTk
    def __init__(self):
        super().__init__()
        
        # Configuración de tema CustomTkinter
        ctk.set_appearance_mode("Light")  # O "System" / "Dark"
        ctk.set_default_color_theme("blue")
        
        self.title("Gestor de Asignaciones")
        self.geometry("1200x700")
        
        # Configurar para abrir en pantalla completa (maximizado)
        self.after(0, lambda: self.state('zoomed'))
        
        # --- TEMA VISUAL (Estilo Moderno/Flat) ---
        self.theme = {
            "bg_app": "#f0f2f5",        # Fondo de la ventana
            "bg_col": "#ebecf0",        # Fondo de las columnas
            "card_bg": "#ffffff",       # Fondo de las tarjetas
            "text_main": "#172b4d",     # Texto principal (Azul oscuro casi negro)
            "text_light": "#5e6c84",    # Texto secundario (Gris)
            "accent": "#0079bf",        # Color principal (Azul)
            "danger": "#eb5a46",        # Color error/sin asignar (Rojo)
            "success": "#61bd4f",       # Color éxito (Verde)
            "header_text": "#ffffff",   # Texto en cabeceras
            "btn_hover": "#dfe1e6"
        }
        self.configure(fg_color=self.theme["bg_app"]) # fg_color en lugar de bg

        # Inicializar BD
        inicializar_tablas()
        
        # --- Panel de Control Superior (Barra de Herramientas) ---
        # Usamos CTkFrame
        control_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Estilo base para botones CTk
        btn_style = {
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            "corner_radius": 6,
            "height": 32,
            "cursor": "hand2",
            "text_color": self.theme["text_main"],
            "fg_color": "#f4f5f7",
            "hover_color": self.theme["btn_hover"]
        }

        # Contenedor interno para padding
        toolbar = ctk.CTkFrame(control_frame, fg_color="transparent")
        toolbar.pack(padx=10, pady=10, fill="x")
        
        # Grupo 1: Datos
        ctk.CTkLabel(toolbar, text="DATOS:", font=("Segoe UI", 10, "bold"), text_color=self.theme["text_light"]).pack(side=tk.LEFT, padx=(0,5))
        ctk.CTkButton(toolbar, text="📂 Importar", command=self.accion_importar_albaranes, **btn_style).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="🔗 Agrupar", command=self.accion_agrupar, **btn_style).pack(side=tk.LEFT, padx=2)

        # Separador visual
        ctk.CTkFrame(toolbar, width=2, height=20, fg_color="#dfe1e6").pack(side=tk.LEFT, padx=10)
        
        # Grupo 2: Gestión
        ctk.CTkLabel(toolbar, text="GESTIÓN:", font=("Segoe UI", 10, "bold"), text_color=self.theme["text_light"]).pack(side=tk.LEFT, padx=(0,5))
        ctk.CTkButton(toolbar, text="🚍 Asignar Auto", command=self.accion_asignar, **dict(btn_style, fg_color="#e3f2fd")).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="🎲 Asignar Aleatorios", command=self.accion_asignar_aleatorios, **dict(btn_style, fg_color="#c8e6c9")).pack(side=tk.LEFT, padx=2)

        # Separador visual
        ctk.CTkFrame(toolbar, width=2, height=20, fg_color="#dfe1e6").pack(side=tk.LEFT, padx=10)

        # Grupo 3: Herramientas
        self.btn_refresh = ctk.CTkButton(toolbar, text="🔄 Refrescar", command=self.cargar_datos, **btn_style)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        # Buscador en tiempo real
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filtrar_tablero())
        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="🔍 Buscar hotel, grupo o pax...", 
                                        textvariable=self.search_var, width=250, height=32)
        self.search_entry.pack(side=tk.LEFT, padx=10)

        self.status_label = ctk.CTkLabel(toolbar, text="Listo", font=("Segoe UI", 10), text_color=self.theme["text_light"])
        self.status_label.pack(side=tk.LEFT, padx=(8, 0))

        self.loading_bar = ctk.CTkProgressBar(toolbar, width=140, height=8)
        self.loading_bar.pack(side=tk.LEFT, padx=(8, 0))
        self.loading_bar.set(0)
        self.loading_bar.pack_forget()

        # Separador visual
        ctk.CTkFrame(toolbar, width=2, height=20, fg_color="#dfe1e6").pack(side=tk.LEFT, padx=10)

        # Grupo 4: Estadísticas
        ctk.CTkLabel(toolbar, text="ESTADO:", font=("Segoe UI", 10, "bold"), text_color=self.theme["text_light"]).pack(side=tk.LEFT, padx=(0,5))
        self.lbl_stats_total = ctk.CTkLabel(toolbar, text="📊 Grupos: 0", font=("Segoe UI", 10), text_color=self.theme["text_main"])
        self.lbl_stats_total.pack(side=tk.LEFT, padx=5)
        
        self.lbl_stats_pax = ctk.CTkLabel(toolbar, text="👥 Total Pax: 0", font=("Segoe UI", 10), text_color=self.theme["text_main"])
        self.lbl_stats_pax.pack(side=tk.LEFT, padx=5)
        
        self.lbl_stats_asignados = ctk.CTkLabel(toolbar, text="✅ Asignados: 0%", font=("Segoe UI", 10), text_color=self.theme["text_main"])
        self.lbl_stats_asignados.pack(side=tk.LEFT, padx=5)
        
        self.lbl_stats_conductores = ctk.CTkLabel(toolbar, text="🚍 Conductores: 0", font=("Segoe UI", 10), text_color=self.theme["text_main"])
        self.lbl_stats_conductores.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(toolbar, text="⚙ Config", command=self.accion_configuracion, **btn_style).pack(side=tk.LEFT, padx=2)
        
        ctk.CTkButton(toolbar, text="❌ Salir", command=self.on_closing, **dict(btn_style, fg_color="#ffebee", text_color="#c62828", hover_color="#ffcdd2")).pack(side=tk.RIGHT, padx=5)

        # --- Panel de Logs (Consola en pantalla) ---
        log_frame = ctk.CTkFrame(self, fg_color="#172b4d", corner_radius=0, height=100)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # CTkTextbox reemplaza a Text + Scrollbar
        self.txt_log = ctk.CTkTextbox(log_frame, height=80, fg_color="#091e42", text_color="#57d9a3", font=("Consolas", 11), corner_radius=0)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        global GUI_LOG_CALLBACK
        GUI_LOG_CALLBACK = self.actualizar_log

        # --- Tablero Kanban ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Mantenemos tk.Canvas para el scroll 2D, pero usamos CTkScrollbar
        self.canvas = tk.Canvas(self.main_frame, bg=self.theme["bg_app"], highlightthickness=0)
        
        self.v_scrollbar = ctk.CTkScrollbar(self.main_frame, orientation="vertical", command=self.canvas.yview)
        self.h_scrollbar = ctk.CTkScrollbar(self.main_frame, orientation="horizontal", command=self.canvas.xview)
        
        # Frame interno donde van las columnas (usamos CTkFrame)
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color=self.theme["bg_app"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Bindings para scroll con rueda del ratón
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.conductores = []
        self.column_map = {}
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.intervalo_minutos = 30  # Valor por defecto
        self.margen_minutos = 120     # Valor por defecto
        self.margen_salida_entrada = 150 # Valor por defecto
        self.max_horas_trabajo = 9       # Valor por defecto
        self.solo_salidas = True     # Valor por defecto
        self.cargando_datos = False
        self.loading_bar_active = False
        
        # Estructuras para optimización de UI (Smart Refresh)
        self.cols_ui = {}   # {conductor_id: {'container': widget, 'lbl_main': widget, 'lbl_sub': widget}}
        self.cards_ui = {}  # {asignacion_id: widget_tarjeta}
        self.grupos_por_conductor = {} # {conductor_id: [lista_grupos]}
        
        # Auditoría y control de cambios
        self.fecha_inicio_sesion = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        registrar_actividad("Inicio de aplicación")
        registrar_inicio_sesion(self.fecha_inicio_sesion)
        self.ultimo_id_actividad = self.obtener_ultimo_id_actividad()
        
        # Cargar datos al inicio
        self.after(500, self.cargar_datos)
        
        # Iniciar verificación periódica de cambios externos (cada 5s)
        self.after(5000, self.verificar_cambios_externos)
        
        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def centrar_ventana(self, ventana, ancho, alto):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (ancho / 2))
        y = int((screen_height / 2) - (alto / 2))
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def on_closing(self):
        registrar_fin_sesion(self.fecha_inicio_sesion)
        self.destroy()

    def obtener_ultimo_id_actividad(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM registro_actividad")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row and row[0] else 0
        except:
            return 0

    def verificar_cambios_externos(self):
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            cursor = conn.cursor()
            # Buscar si hay registros nuevos creados por OTRO proceso (pid diferente)
            pid_actual = os.getpid()
            cursor.execute("SELECT COUNT(*) FROM registro_actividad WHERE id > ? AND pid != ?", (self.ultimo_id_actividad, pid_actual))
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                self.btn_refresh.config(bg="#FF5722", text="⚠ Refrescar (Cambios!)", fg="white")
        except:
            pass
        finally:
            self.after(5000, self.verificar_cambios_externos)

    def actualizar_log(self, mensaje):
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)
        self.update_idletasks()

    def accion_ver_importaciones(self):
        top = tk.Toplevel(self)
        top.title("Visor de Albaranes Importados")
        self.centrar_ventana(top, 1100, 600)
        
        # Asegurar que la ventana se abra en primer plano y sobre la principal
        top.transient(self)
        top.lift()
        top.focus_force()

        # --- Filtros ---
        f_filter = tk.Frame(top, bg="#f0f0f0", pady=10, relief=tk.RAISED, bd=1)
        f_filter.pack(fill=tk.X)

        tk.Label(f_filter, text="Filtrar por Fecha:", bg="#f0f0f0", font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        # Widget de Calendario o Entrada de texto
        if DateEntry:
            cal = DateEntry(f_filter, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            cal.pack(side=tk.LEFT, padx=5)
        else:
            cal = tk.Entry(f_filter, width=15)
            cal.pack(side=tk.LEFT, padx=5)
            cal.insert(0, datetime.today().strftime('%Y-%m-%d'))
            tk.Label(f_filter, text="(Instala 'tkcalendar' para ver calendario)", font=("Arial", 8), fg="red", bg="#f0f0f0").pack(side=tk.LEFT)

        # --- Tabla de Datos ---
        columns = ("numero", "fecha", "hora", "empresa", "proveedor", "observacion")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        
        tree.heading("numero", text="Número")
        tree.heading("fecha", text="Fecha")
        tree.heading("hora", text="Hora")
        tree.heading("empresa", text="Empresa")
        tree.heading("proveedor", text="Proveedor")
        tree.heading("observacion", text="Observación")
       
        tree.column("numero", width=100)
        tree.column("fecha", width=100)
        tree.column("hora", width=80)
        tree.column("empresa", width=150)
        tree.column("proveedor", width=150)
        tree.column("observacion", width=300)
        
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        def cargar_tabla(filtro_fecha=None):
            for item in tree.get_children():
                tree.delete(item)
            
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                query = "SELECT numero, fecha, hora, empresa, proveedor, observacion FROM albaranes"
                params = []
                if filtro_fecha:
                    query += " WHERE fecha = ?"
                    params.append(filtro_fecha)
                
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5]))
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar los albaranes: {e}")

        # Botones de acción del filtro
        btn_buscar = tk.Button(f_filter, text="🔍 Filtrar", command=lambda: cargar_tabla(cal.get()))
        btn_buscar.pack(side=tk.LEFT, padx=10)
        
        btn_todos = tk.Button(f_filter, text="Ver Todos", command=lambda: cargar_tabla(None))
        btn_todos.pack(side=tk.LEFT, padx=5)

        # Cargar datos iniciales (todos)
        cargar_tabla(None)

    def accion_importar_albaranes(self):
        archivos_xml = filedialog.askopenfilenames(
            title="Seleccionar archivos XML de Albaranes",
            filetypes=(("Archivos XML", "*.xml"), ("Todos los archivos", "*.*"))
        )
        if not archivos_xml:
            return

        # Definir carpeta de importados en el directorio del script/ejecutable
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        carpeta_importados = os.path.join(application_path, "Importados")
        if not os.path.exists(carpeta_importados):
            try:
                os.makedirs(carpeta_importados)
            except OSError as e:
                messagebox.showerror("Error", f"No se pudo crear carpeta 'Importados': {e}")
                return

        try:
            conn = sqlite3.connect(DB_FILE)
            
            for archivo_xml in archivos_xml:
                nombre_fichero = os.path.basename(archivo_xml)
                
                # Diferenciar entrada/salida por nombre
                tipo_fichero = "DESCONOCIDO"
                if "entrada" in nombre_fichero.lower():
                    tipo_fichero = "ENTRADA"
                elif "salida" in nombre_fichero.lower():
                    tipo_fichero = "SALIDA"
                
                log(f"Procesando fichero: {nombre_fichero} (Tipo: {tipo_fichero})")
                
                importar_albaranes_xml(archivo_xml, conn)
                
                # Mover a carpeta importados
                destino = os.path.join(carpeta_importados, nombre_fichero)
                if os.path.exists(destino):
                    os.remove(destino) # Eliminar si ya existe para sobrescribir
                shutil.move(archivo_xml, destino)
                log(f"✓ Archivo movido a: {destino}")

            conn.close()
            registrar_actividad(f"Importación de {len(archivos_xml)} albaranes")
            messagebox.showinfo("Éxito", f"Se han importado {len(archivos_xml)} archivos correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar XML: {e}")

    def accion_vaciar_tablas(self):
        top = ctk.CTkToplevel(self)
        top.title("Vaciar Tablas")
        self.centrar_ventana(top, 300, 450)

        ctk.CTkLabel(top, text="Selecciona las tablas a vaciar:", font=("Segoe UI", 12, "bold")).pack(pady=10)

        # Orden de borrado: primero las que dependen (FK), luego las independientes
        tables = [
            "asignaciones_grupos",  # Depende de conductores
            "grupos_hoteles",       # Depende de hoteles
            "hoteles",              # Depende de zonas
            "zonas",                # Depende de albaranes
            "albaranes",            # Independiente
            "conductores",          # Independiente
            "registro_actividad",   # Independiente
            "sesiones_activas"      # Independiente
        ]
        
        vars_dict = {}
        for tbl in tables:
            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(top, text=tbl, variable=var)
            chk.pack(anchor="w", padx=20)
            vars_dict[tbl] = var

        def ejecutar_borrado():
            selected_tables = [t for t, v in vars_dict.items() if v.get()]
            if not selected_tables:
                messagebox.showwarning("Aviso", "No has seleccionado ninguna tabla.")
                return
            
            if not messagebox.askyesno("Confirmar", f"¿Estás seguro de vaciar: {', '.join(selected_tables)}?"):
                return

            try:
                conn = sqlite3.connect(DB_FILE, timeout=10)
                cursor = conn.cursor()
                
                # Deshabilitar restricciones de claves foráneas
                cursor.execute('PRAGMA foreign_keys = OFF')
                
                # Borrar en el orden especificado (respetando dependencias)
                tablas_borradas = 0
                for tbl in tables:  # Usar el orden correcto de dependencias
                    if tbl in selected_tables:
                        # Verificar si la tabla existe
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
                        if cursor.fetchone():
                            cursor.execute(f"DELETE FROM {tbl}")
                            registros_borrados = cursor.rowcount
                            log(f"  ✓ {tbl}: {registros_borrados} registros borrados")
                            tablas_borradas += 1
                        else:
                            log(f"  ⚠ {tbl}: tabla no existe")
                
                # Habilitar restricciones de claves foráneas
                cursor.execute('PRAGMA foreign_keys = ON')
                
                # VACUUM para recuperar el espacio en disco
                cursor.execute('VACUUM')
                
                conn.commit()
                conn.close()
                
                registrar_actividad(f"Vaciado de {tablas_borradas} tabla(s): {', '.join(selected_tables)}")
                messagebox.showinfo("Éxito", f"✓ {tablas_borradas} tabla(s) vaciada(s) correctamente.\n✓ Base de datos optimizada (VACUUM).")
                top.destroy()
                self.cargar_datos()
                
            except Exception as e:
                log(f"Error al vaciar tablas: {e}")
                messagebox.showerror("Error", f"Error al vaciar tablas:\n{e}")

        ctk.CTkButton(top, text="Borrar Seleccionadas", command=ejecutar_borrado, fg_color="#ef5350", hover_color="#e53935").pack(pady=20)

    def ver_registro_actividad(self):
        top = ctk.CTkToplevel(self)
        top.title("Registro de Actividad")
        self.centrar_ventana(top, 900, 500)
        
        # Asegurar que la ventana se abra en primer plano y sobre la principal
        top.transient(self)
        top.lift()
        top.focus_force()

        frame = tk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "usuario", "accion", "fecha", "pid")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        tree.heading("id", text="ID")
        tree.heading("usuario", text="Usuario")
        tree.heading("accion", text="Acción")
        tree.heading("fecha", text="Fecha")
        tree.heading("pid", text="PID")
        
        tree.column("id", width=50, anchor="center")
        tree.column("usuario", width=100, anchor="center")
        tree.column("accion", width=400, anchor="w")
        tree.column("fecha", width=150, anchor="center")
        tree.column("pid", width=80, anchor="center")
        
        # Configurar colores alternos para filas (efecto tabla)
        tree.tag_configure('odd', background='#f5f5f5')
        tree.tag_configure('even', background='#ffffff')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def cargar():
            for item in tree.get_children():
                tree.delete(item)
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT id, usuario, accion, fecha, pid FROM registro_actividad ORDER BY id DESC LIMIT 1000")
                for i, row in enumerate(cursor.fetchall()):
                    tag = 'even' if i % 2 == 0 else 'odd'
                    tree.insert("", tk.END, values=row, tags=(tag,))
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error cargando registros: {e}")

        cargar()
        ctk.CTkButton(top, text="🔄 Refrescar", command=cargar).pack(pady=10)

    def ver_sesiones_activas(self):
        # Determinar ventana padre (si configuración está abierta, usarla)
        parent = self
        if hasattr(self, 'ventana_config') and self.ventana_config is not None and self.ventana_config.winfo_exists():
            parent = self.ventana_config
            
        top = ctk.CTkToplevel(parent)
        top.title("Sesiones Activas")
        self.centrar_ventana(top, 600, 300)
        
        # Asegurar que la ventana se abra en primer plano y sobre la ventana padre
        top.transient(parent)
        top.lift()
        top.focus_force()

        frame = ctk.CTkFrame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("usuario", "fecha_inicio", "pid")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        tree.heading("usuario", text="Usuario")
        tree.heading("fecha_inicio", text="Inicio Sesión")
        tree.heading("pid", text="PID")
        
        tree.column("usuario", width=150, anchor="center")
        tree.column("fecha_inicio", width=200, anchor="center")
        tree.column("pid", width=100, anchor="center")
        
        # Configurar colores alternos para filas (efecto tabla)
        tree.tag_configure('odd', background='#f5f5f5')
        tree.tag_configure('even', background='#ffffff')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def cargar():
            for item in tree.get_children():
                tree.delete(item)
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT usuario, fecha_inicio, pid FROM sesiones_activas")
                for i, row in enumerate(cursor.fetchall()):
                    tag = 'even' if i % 2 == 0 else 'odd'
                    tree.insert("", tk.END, values=row, tags=(tag,))
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error cargando sesiones: {e}")

        cargar()
        ctk.CTkButton(top, text="🔄 Refrescar", command=cargar).pack(pady=10)

    def accion_configuracion(self):
        # Evitar abrir múltiples ventanas (Solución al cierre inesperado por Garbage Collection)
        if hasattr(self, 'ventana_config') and self.ventana_config is not None and self.ventana_config.winfo_exists():
            self.ventana_config.lift()
            self.ventana_config.focus()
            return

        self.ventana_config = ctk.CTkToplevel(self)
        self.ventana_config.title("Configuración")
        self.centrar_ventana(self.ventana_config, 400, 520)
        self.ventana_config.configure(fg_color=self.theme["bg_app"])
        
        # Asegurar que la ventana se abra en primer plano y sobre la principal
        self.ventana_config.transient(self)
        self.ventana_config.lift()
        self.ventana_config.focus_force()
        
        # Frame principal con padding
        main_frame = ctk.CTkFrame(self.ventana_config, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Estilo local para botones de configuración
        btn_style = {
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            "height": 32,
            "cursor": "hand2",
            "text_color": self.theme["text_main"],
            "fg_color": "#f4f5f7",
            "hover_color": "#dfe1e6"
        }

        # Función auxiliar para filas
        def crear_fila(parent, texto, valor):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill=tk.X, pady=6)
            ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12), anchor="w", text_color=self.theme["text_main"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
            e = ctk.CTkEntry(f, justify="center", width=100)
            e.insert(0, str(valor))
            e.pack(side=tk.RIGHT)
            return e
        
        entry_minutos = crear_fila(main_frame, "Intervalo agrupación (min):", self.intervalo_minutos)
        entry_margen = crear_fila(main_frame, "Margen asignaciones (min):", self.margen_minutos)
        entry_se = crear_fila(main_frame, "Margen Salida -> Entrada (min):", self.margen_salida_entrada)
        entry_horas = crear_fila(main_frame, "Máximo Horas Trabajo:", self.max_horas_trabajo)

        # Checkbox para filtrar solo salidas
        var_solo_salidas = tk.BooleanVar(value=self.solo_salidas)
        chk_salidas = ctk.CTkCheckBox(main_frame, text="Solo procesar Salidas (S)", variable=var_solo_salidas, font=("Segoe UI", 12), text_color=self.theme["text_main"])
        chk_salidas.pack(pady=15)
        
        def guardar():
            try:
                valor = int(entry_minutos.get())
                valor_margen = int(entry_margen.get())
                valor_se = int(entry_se.get())
                valor_horas = float(entry_horas.get())
                if valor <= 0:
                    raise ValueError("Minutos debe ser positivo")
                if valor_margen < 0:
                    raise ValueError("Margen debe ser positivo")
                if valor_se < 0:
                    raise ValueError("Margen S->E debe ser positivo")
                if valor_horas <= 0:
                    raise ValueError("Horas deben ser positivas")
                self.intervalo_minutos = valor
                self.margen_minutos = valor_margen
                self.margen_salida_entrada = valor_se
                self.max_horas_trabajo = valor_horas
                self.solo_salidas = var_solo_salidas.get()
                # self.guardar_configuracion()
                registrar_actividad("Modificación de configuración")
                messagebox.showinfo("Guardado", f"Configuración actualizada:\n- Agrupación: {valor} min\n- Margen General: {valor_margen} min\n- Margen S->E: {valor_se} min\n- Max Horas: {self.max_horas_trabajo}h\n- Solo Salidas: {self.solo_salidas}")
                self.ventana_config.destroy()
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos.")

        ctk.CTkButton(main_frame, text="💾 Guardar Cambios", command=guardar, **dict(btn_style, fg_color="#c8e6c9")).pack(pady=10, fill=tk.X)

        # Separador y sección de auditoría
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        ctk.CTkLabel(main_frame, text="Herramientas de Base de Datos:", font=("Segoe UI", 11, "bold"), text_color=self.theme["text_light"]).pack(pady=(0, 10), anchor="w")
        
        f_audit = ctk.CTkFrame(main_frame, fg_color="transparent")
        f_audit.pack(fill=tk.X)

        # Organizar botones en cuadrícula
        ctk.CTkButton(f_audit, text="📜 Reg. Actividad", command=self.ver_registro_actividad, **btn_style).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(f_audit, text="👥 Sesiones", command=self.ver_sesiones_activas, **btn_style).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(f_audit, text="👁 Ver Datos", command=self.accion_ver_importaciones, **dict(btn_style, fg_color="#e3f2fd")).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(f_audit, text="🗑 Limpiar BD", command=self.accion_vaciar_tablas, **dict(btn_style, fg_color="#ffcdd2")).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        
        f_audit.grid_columnconfigure(0, weight=1)
        f_audit.grid_columnconfigure(1, weight=1)

    def accion_agrupar(self):
        grupos = agrupar_hoteles_por_tiempo(self.intervalo_minutos, self.solo_salidas)
        if grupos:
            guardar_grupos_en_bd(grupos)
            registrar_actividad(f"Agrupación generada ({len(grupos)} grupos)")
            messagebox.showinfo("Éxito", f"Se han generado {len(grupos)} grupos.")
        else:
            messagebox.showwarning("Atención", "No se generaron grupos (verifique datos de hoteles).")

    def accion_asignar(self):
        ejecutar_asignacion_conductores(self.margen_minutos, self.margen_salida_entrada, self.max_horas_trabajo)
        registrar_actividad("Asignación automática ejecutada")
        self.cargar_datos()
        messagebox.showinfo("Éxito", "Asignación de conductores completada.")

    def accion_asignar_aleatorios(self):
        """
        Abre un diálogo para asignar conductores aleatorios desde la configuración
        """
        # Cargar configuración
        config = cargar_config_conductores()
        
        if config is None:
            # Si no hay config, mostrar un diálogo para ingresar parámetros
            self.ventana_aleatorios = ctk.CTkToplevel(self)
            self.ventana_aleatorios.title("Asignar Conductores Aleatorios")
            self.centrar_ventana(self.ventana_aleatorios, 400, 350)
            self.ventana_aleatorios.configure(fg_color=self.theme["bg_app"])
            
            self.ventana_aleatorios.transient(self)
            self.ventana_aleatorios.lift()
            self.ventana_aleatorios.focus_force()
            
            main_frame = ctk.CTkFrame(self.ventana_aleatorios, fg_color="transparent")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(main_frame, text="Configurar Conductores Aleatorios", 
                        font=("Segoe UI", 14, "bold"), text_color=self.theme["text_main"]).pack(pady=10)
            
            # Cantidad
            frame_cantidad = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_cantidad.pack(fill=tk.X, pady=8)
            ctk.CTkLabel(frame_cantidad, text="Cantidad:", text_color=self.theme["text_main"]).pack(side=tk.LEFT)
            entry_cantidad = ctk.CTkEntry(frame_cantidad, width=100)
            entry_cantidad.insert(0, "5")
            entry_cantidad.pack(side=tk.RIGHT)
            
            # Tipos de licencia
            frame_licencia = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_licencia.pack(fill=tk.X, pady=8)
            ctk.CTkLabel(frame_licencia, text="Tipos de Licencia (A,B,C):", text_color=self.theme["text_main"]).pack(side=tk.LEFT)
            entry_licencia = ctk.CTkEntry(frame_licencia, width=100)
            entry_licencia.insert(0, "A,B,C")
            entry_licencia.pack(side=tk.RIGHT)
            
            # Plazas
            frame_plazas = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_plazas.pack(fill=tk.X, pady=8)
            ctk.CTkLabel(frame_plazas, text="Plazas Vehículo (4,20,55):", text_color=self.theme["text_main"]).pack(side=tk.LEFT)
            entry_plazas = ctk.CTkEntry(frame_plazas, width=100)
            entry_plazas.insert(0, "4,20,55")
            entry_plazas.pack(side=tk.RIGHT)
            
            # Nombre y Apellido
            frame_nombre = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_nombre.pack(fill=tk.X, pady=8)
            ctk.CTkLabel(frame_nombre, text="Prefijo Nombre:", text_color=self.theme["text_main"]).pack(side=tk.LEFT)
            entry_nombre = ctk.CTkEntry(frame_nombre, width=100)
            entry_nombre.insert(0, "Conductor")
            entry_nombre.pack(side=tk.RIGHT)
            
            frame_apellido = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_apellido.pack(fill=tk.X, pady=8)
            ctk.CTkLabel(frame_apellido, text="Prefijo Apellido:", text_color=self.theme["text_main"]).pack(side=tk.LEFT)
            entry_apellido = ctk.CTkEntry(frame_apellido, width=100)
            entry_apellido.insert(0, "Test")
            entry_apellido.pack(side=tk.RIGHT)
            
            # Botones
            frame_botones = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame_botones.pack(fill=tk.X, pady=20)
            
            def guardar_conductores_aleatorios():
                try:
                    cantidad = int(entry_cantidad.get())
                    tipos_licencia = [x.strip().upper() for x in entry_licencia.get().split(",")]
                    plazas = [int(x.strip()) for x in entry_plazas.get().split(",")]
                    nombre_prefijo = entry_nombre.get()
                    apellido_prefijo = entry_apellido.get()
                    
                    registrar_actividad("Asignación de conductores aleatorios ejecutada")
                    asignar_conductores_aleatorios(
                        cantidad=cantidad,
                        nombre_prefijo=nombre_prefijo,
                        apellido_prefijo=apellido_prefijo,
                        incluir_dni=True,
                        tipos_licencia=tipos_licencia,
                        plazas_opciones=plazas,
                        activo=True
                    )
                    self.cargar_datos()
                    self.ventana_aleatorios.destroy()
                    messagebox.showinfo("Éxito", f"Se han insertado {cantidad} conductores aleatorios.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar conductores: {e}")
            
            ctk.CTkButton(frame_botones, text="Guardar", command=guardar_conductores_aleatorios, 
                         fg_color="#4CAF50", text_color="white").pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(frame_botones, text="Cancelar", command=self.ventana_aleatorios.destroy,
                         fg_color="#f44336", text_color="white").pack(side=tk.RIGHT, padx=5)
        else:
            # Usar configuración del archivo config.ini
            log("Usando configuración de config.ini para asignación aleatoria")
            cantidad = asignar_conductores_aleatorios(
                cantidad=config["cantidad"],
                nombre_prefijo=config["nombre_prefijo"],
                apellido_prefijo=config["apellido_prefijo"],
                incluir_dni=config["incluir_dni"],
                tipos_licencia=config["tipos_licencia"],
                plazas_opciones=config["plazas_vehiculo"],
                activo=config["activo"]
            )
            registrar_actividad(f"Asignación de {cantidad} conductores aleatorios (desde config.ini)")
            self.cargar_datos()
            messagebox.showinfo("Éxito", f"Se han insertado {cantidad} conductores aleatorios desde configuración.")

    def _set_estado_carga(self, cargando, mensaje="Cargando datos..."):
        self.cargando_datos = cargando
        if not hasattr(self, "btn_refresh"):
            return

        if cargando:
            self.btn_refresh.configure(state="disabled", text="⏳ Cargando...")
            self.status_label.configure(text=mensaje, text_color=self.theme["accent"])
            if hasattr(self, "loading_bar"):
                self.loading_bar.pack(side=tk.LEFT, padx=(8, 0))
                self.loading_bar.start()
        else:
            self.btn_refresh.configure(state="normal", text="🔄 Refrescar")
            self.status_label.configure(text="Listo", text_color=self.theme["text_light"])
            if hasattr(self, "loading_bar"):
                self.loading_bar.stop()
                self.loading_bar.pack_forget()

    def _limpiar_tablero(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.column_map = {}
        self.cols_ui = {}
        self.cards_ui = {}

        placeholder = ctk.CTkLabel(
            self.scrollable_frame,
            text="Cargando tablero...",
            font=("Segoe UI", 14),
            text_color=self.theme["text_light"]
        )
        placeholder.pack(padx=20, pady=20, anchor="w")

    def _cargar_datos_en_segundo_plano(self):
        try:
            conn = sqlite3.connect(DB_FILE, timeout=30)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores")
                conductores = [{'id': row[0], 'nombre': row[1], 'plazas': row[2] if row[2] else 0} for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error cargando conductores: {e}")
                conductores = []

            conductores.insert(0, {'id': 0, 'nombre': 'Sin Asignar', 'plazas': 0})

            try:
                query = """
                    SELECT 
                        ag.id, ag.grupo_conductor, ag.conductor_id, ag.hora_inicio, ag.hora_fin, 
                        ag.total_personas, ag.conductor_nombre, ag.tipo_servicio,
                        (SELECT COUNT(*) FROM grupos_hoteles gh WHERE gh.grupo_numero = ag.grupo_conductor)
                    FROM asignaciones_grupos ag
                """
                cursor.execute(query)
                asignaciones_raw = cursor.fetchall()
            except Exception:
                asignaciones_raw = []

            grupos_por_conductor = {c['id']: [] for c in conductores}

            for row in asignaciones_raw:
                c_id = row[2] if row[2] else 0
                if c_id not in grupos_por_conductor:
                    c_id = 0

                hora_mostrar = row[3]
                try:
                    dt_ini = datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S")
                    hora_mostrar = dt_ini.strftime("%d/%m %H:%M")
                except Exception:
                    pass

                grupos_por_conductor[c_id].append({
                    'id': row[0],
                    'grupo': row[1],
                    'hora': hora_mostrar,
                    'hora_fin_raw': row[4],
                    'personas': row[5],
                    'motivo': row[6] if len(row) > 6 else "",
                    'tipo_servicio': row[7] if len(row) > 7 else "",
                    'total_hoteles': row[8] if len(row) > 8 else 0
                })

            conn.close()
            payload = {
                'conductores': conductores,
                'grupos_por_conductor': grupos_por_conductor,
                'error': None,
            }
        except Exception as e:
            payload = {
                'conductores': [],
                'grupos_por_conductor': {},
                'error': str(e),
            }

        self.after(0, lambda: self._aplicar_datos_ui(payload))

    def _aplicar_datos_ui(self, payload):
        self._set_estado_carga(False)

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.column_map = {}
        self.cols_ui = {}
        self.cards_ui = {}

        self.conductores = payload.get('conductores', [])
        self.grupos_por_conductor = payload.get('grupos_por_conductor', {})

        if payload.get('error'):
            ctk.CTkLabel(
                self.scrollable_frame,
                text=f"Error al cargar datos: {payload['error']}",
                font=("Segoe UI", 12),
                text_color=self.theme["danger"]
            ).pack(padx=20, pady=20, anchor="w")
            return

        # Calcular Estadísticas
        total_grupos = 0
        total_pax = 0
        asignados = 0
        for c_id, grupos in self.grupos_por_conductor.items():
            count = len(grupos)
            total_grupos += count
            total_pax += sum(g['personas'] for g in grupos)
            if c_id != 0:
                asignados += count
        
        pct_asignados = (asignados / total_grupos * 100) if total_grupos > 0 else 0
        
        self.lbl_stats_total.configure(text=f"📊 Grupos: {total_grupos}")
        self.lbl_stats_pax.configure(text=f"👥 Total Pax: {total_pax}")
        self.lbl_stats_asignados.configure(text=f"✅ Asignados: {pct_asignados:.1f}%")
        self.lbl_stats_conductores.configure(text=f"🚍 Conductores: {len(self.conductores)-1}")

        for conductor in self.conductores:
            self.crear_columna(conductor, self.grupos_por_conductor.get(conductor['id'], []))

        # Aplicar filtro si hay algo escrito
        if self.search_var.get():
            self.filtrar_tablero()

        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.ultimo_id_actividad = self.obtener_ultimo_id_actividad()

    def filtrar_tablero(self):
        termino = self.search_var.get().lower()
        if not termino:
            # Mostrar todo
            for card in self.cards_ui.values():
                card.pack(fill=tk.X, pady=2, padx=4)
            return

        for asignacion_id, card in self.cards_ui.items():
            # Buscar el objeto de datos del grupo
            grupo_obj = None
            for lista in self.grupos_por_conductor.values():
                for g in lista:
                    if g['id'] == asignacion_id:
                        grupo_obj = g
                        break
                if grupo_obj: break
            
            if not grupo_obj: continue

            # Criterios de búsqueda
            match = (
                termino in str(grupo_obj['grupo']).lower() or
                termino in str(grupo_obj['personas']).lower() or
                termino in str(grupo_obj.get('motivo', '')).lower() or
                termino in str(grupo_obj.get('tipo_servicio', '')).lower()
            )
            
            # También podríamos buscar en los hoteles del grupo, pero requeriría tenerlos en memoria
            # Por ahora filtramos por datos básicos de la tarjeta
            
            if match:
                card.pack(fill=tk.X, pady=2, padx=4)
            else:
                card.pack_forget()
        
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def cargar_datos(self):
        if self.cargando_datos:
            return

        self._limpiar_tablero()
        self._set_estado_carga(True)
        threading.Thread(target=self._cargar_datos_en_segundo_plano, daemon=True).start()

    def crear_columna(self, conductor, grupos):
        # Usamos CTkFrame para la columna con bordes redondeados
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color=self.theme["bg_col"], corner_radius=8, width=280)
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=10, anchor="n")
        
        self.column_map[frame] = conductor

        header_bg = self.theme["danger"] if conductor['id'] == 0 else self.theme["accent"]
        header_fg = self.theme["header_text"]
        
        # Calcular total pax para el header
        total_pax = sum(g['personas'] for g in grupos)
        
        texto_header = f"{conductor['nombre']}"
        subtexto = f"{len(grupos)} Grupos | {total_pax} Pax"
        
        if conductor['id'] != 0:
            subtexto += f"\n🚍 {conductor['plazas']} plazas"
            
            # Mostrar hasta qué hora está ocupado (última hora de fin de sus grupos)
            if grupos:
                horas_fin = [g['hora_fin_raw'] for g in grupos if g.get('hora_fin_raw')]
                if horas_fin:
                    try:
                        # Ordenar cronológicamente parseando la fecha completa
                        horas_fin.sort(key=lambda x: datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S"))
                        ultima_hora = horas_fin[-1]
                        dt_ultima = datetime.strptime(ultima_hora, "%Y-%m-%d %H:%M:%S")
                        texto_header += f"\n⌛ Ocup. hasta: {dt_ultima.strftime('%d/%m %H:%M')}"
                    except:
                        subtexto += f" | Fin: {max(horas_fin)}"
            
        # Header Frame
        header_frame = ctk.CTkFrame(frame, fg_color=header_bg, corner_radius=6)
        header_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Guardar referencias a etiquetas para actualizarlas luego sin recargar todo
        lbl_main = ctk.CTkLabel(header_frame, text=texto_header, text_color=header_fg, font=("Segoe UI", 12, "bold"), wraplength=230, justify="left")
        lbl_main.pack(anchor="w", padx=5, pady=(5,0))
        
        lbl_sub = ctk.CTkLabel(header_frame, text=subtexto, text_color=header_fg, font=("Segoe UI", 10), wraplength=230, justify="left")
        lbl_sub.pack(anchor="w", padx=5, pady=(0,5))
        
        # Contenedor de tarjetas
        cards_container = ctk.CTkFrame(frame, fg_color="transparent")
        cards_container.pack(fill=tk.BOTH, expand=True)
        
        # Registrar UI de columna
        self.cols_ui[conductor['id']] = {
            'container': cards_container,
            'lbl_main': lbl_main,
            'lbl_sub': lbl_sub
        }

        for g in grupos:
            self.crear_tarjeta(cards_container, g)

    def crear_tarjeta(self, parent, grupo):
        # Determinar colores según tipo de servicio
        tipo = str(grupo.get('tipo_servicio', '')).upper()
        strip_bg = "#9E9E9E" # Gris por defecto
        
        if 'S' in tipo: # Salida
            strip_bg = self.theme["accent"] # Azul
        elif 'E' in tipo: # Entrada
            strip_bg = self.theme["success"] # Verde
            
        # Sobrescribir si hay error/sin asignar
        motivo = grupo.get('motivo', '')
        if motivo and "SIN ASIGNAR" in motivo:
            strip_bg = self.theme["danger"] # Rojo

        # Tarjeta con CTkFrame (sombra y bordes redondeados nativos)
        card_frame = ctk.CTkFrame(parent, fg_color=self.theme["card_bg"], corner_radius=6, border_width=1, border_color="#dfe1e6")
        card_frame.pack(fill=tk.X, pady=2, padx=4)
        
        # Registrar UI de tarjeta
        self.cards_ui[grupo['id']] = card_frame

        # Layout interno
        inner = ctk.CTkFrame(card_frame, fg_color="transparent")
        inner.pack(fill=tk.BOTH, padx=1, pady=1)

        # Tira de color lateral
        strip = ctk.CTkFrame(inner, fg_color=strip_bg, width=4, corner_radius=2)
        strip.pack(side=tk.LEFT, fill=tk.Y, padx=(2, 3), pady=1)
        
        # Contenido
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Fila 1: ID y Pax
        r1 = ctk.CTkFrame(content, fg_color="transparent")
        r1.pack(fill=tk.X)
        ctk.CTkLabel(r1, text=f"G{grupo['grupo']}", font=("Segoe UI", 12, "bold"), text_color=self.theme["text_main"]).pack(side=tk.LEFT)
        ctk.CTkLabel(r1, text=f"👥 {grupo['personas']}", font=("Segoe UI", 12, "bold"), text_color=self.theme["text_light"]).pack(side=tk.RIGHT)

        # Fila 2: Total Hoteles
        total_hoteles = grupo.get('total_hoteles', 0)
        if total_hoteles > 0:
            ctk.CTkLabel(content, text=f"🏨 {total_hoteles} Paradas", font=("Segoe UI", 9), text_color=self.theme["text_main"], anchor="w", wraplength=190, justify="left").pack(fill=tk.X, pady=(0, 1))

        # Fila 3: Hora y Tipo
        r3 = ctk.CTkFrame(content, fg_color="transparent")
        r3.pack(fill=tk.X, pady=(1,0))
        ctk.CTkLabel(r3, text=f"🕒 {grupo['hora']}", font=("Segoe UI", 10, "bold"), text_color=self.theme["text_main"]).pack(side=tk.LEFT)
        if tipo:
            # Badge simulado
            lbl_tipo = ctk.CTkLabel(r3, text=tipo, font=("Segoe UI", 8, "bold"), fg_color=strip_bg, text_color="white", corner_radius=4, padx=4)
            lbl_tipo.pack(side=tk.RIGHT)
            # Bindings para el badge también
            lbl_tipo.bind("<Button-1>", lambda e, g=grupo: self.start_drag(e, g))
            lbl_tipo.bind("<B1-Motion>", self.do_drag)
            lbl_tipo.bind("<ButtonRelease-1>", self.stop_drag)
            lbl_tipo.bind("<Double-Button-1>", lambda e, g=grupo: self.mostrar_detalle_grupo(g))

        # Fila 4: Error (si existe)
        if motivo and "SIN ASIGNAR" in motivo:
            txt_err = motivo.replace("SIN ASIGNAR:", "").strip()
            ctk.CTkLabel(content, text=f"⚠ {txt_err}", font=("Segoe UI", 8), text_color=self.theme["danger"], anchor="w", wraplength=190, justify="left").pack(fill=tk.X, pady=(1,0))

        # Bindings para Drag & Drop en todos los widgets hijos
        def bind_recursive(w):
            w.bind("<Button-1>", lambda e, g=grupo: self.start_drag(e, g))
            w.bind("<B1-Motion>", self.do_drag)
            w.bind("<ButtonRelease-1>", self.stop_drag)
            w.bind("<Double-Button-1>", lambda e, g=grupo: self.mostrar_detalle_grupo(g))
            for child in w.winfo_children():
                bind_recursive(child)
        
        bind_recursive(card_frame)

    def start_drag(self, event, grupo):
        self.drag_data["item"] = grupo
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root

    def do_drag(self, event):
        if not self.drag_data["item"]:
            return

        if hasattr(self, 'drag_win'):
            self.drag_win.geometry(f"+{event.x_root+10}+{event.y_root+10}")
        else:
            # Solo iniciar arrastre si se mueve más de 5 píxeles (evita conflicto con click/doble click)
            dx = abs(event.x_root - self.drag_data["x"])
            dy = abs(event.y_root - self.drag_data["y"])
            if dx > 5 or dy > 5:
                grupo = self.drag_data["item"]
                self.drag_win = ctk.CTkToplevel(self)
                self.drag_win.overrideredirect(True)
                self.drag_win.attributes('-alpha', 0.7)
                lbl = ctk.CTkLabel(self.drag_win, text=f"G{grupo['grupo']} ({grupo['personas']}p)", fg_color="#ffeb3b", text_color="black", corner_radius=5, padx=10, pady=5)
                lbl.pack(fill="both", expand=True)
                self.drag_win.geometry(f"+{event.x_root+10}+{event.y_root+10}")

    def stop_drag(self, event):
        if hasattr(self, 'drag_win'):
            self.drag_win.destroy()
            del self.drag_win
            
            x, y = event.x_root, event.y_root
            target_conductor = None
            
            for col_frame, conductor in self.column_map.items():
                cx = col_frame.winfo_rootx()
                cy = col_frame.winfo_rooty()
                cw = col_frame.winfo_width()
                ch = col_frame.winfo_height()
                
                if cx <= x <= cx + cw and cy <= y <= cy + ch:
                    target_conductor = conductor
                    break
            
            if target_conductor and self.drag_data["item"]:
                self.mover_grupo(self.drag_data["item"]['id'], target_conductor['id'], target_conductor['nombre'])
        
        self.drag_data["item"] = None

    def fetch_single_group(self, asignacion_id):
        """Recupera los datos actualizados de un solo grupo desde la BD."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, grupo_conductor, conductor_id, hora_inicio, hora_fin, total_personas, conductor_nombre, tipo_servicio FROM asignaciones_grupos WHERE id = ?", (asignacion_id,))
            row = cursor.fetchone()
            
            # Obtener total hoteles
            total_hoteles = 0
            if row:
                cursor.execute("SELECT COUNT(*) FROM grupos_hoteles WHERE grupo_numero = ?", (row[1],))
                h_row = cursor.fetchone()
                if h_row: total_hoteles = h_row[0]
            conn.close()

            if not row: return None

            # Formatear
            hora_mostrar = row[3]
            try:
                dt_ini = datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S")
                hora_mostrar = dt_ini.strftime("%d/%m %H:%M")
            except: pass

            return {
                'id': row[0],
                'grupo': row[1],
                'hora': hora_mostrar,
                'hora_fin_raw': row[4],
                'personas': row[5],
                'motivo': row[6] if len(row) > 6 else "",
                'tipo_servicio': row[7] if len(row) > 7 else "",
                'total_hoteles': total_hoteles
            }
        except:
            return None

    def actualizar_header(self, conductor_id):
        """Recalcula y actualiza el texto de la cabecera de una columna."""
        if conductor_id not in self.cols_ui: return
        
        ui = self.cols_ui[conductor_id]
        grupos = self.grupos_por_conductor.get(conductor_id, [])
        
        # Buscar datos del conductor
        conductor = next((c for c in self.conductores if c['id'] == conductor_id), None)
        if not conductor: return

        total_pax = sum(g['personas'] for g in grupos)
        texto_header = f"{conductor['nombre']}"
        subtexto = f"{len(grupos)} Grupos | {total_pax} Pax"

        if conductor_id != 0:
            subtexto += f"\n🚍 {conductor['plazas']} plazas"
            if grupos:
                horas_fin = [g['hora_fin_raw'] for g in grupos if g.get('hora_fin_raw')]
                if horas_fin:
                    try:
                        horas_fin.sort(key=lambda x: datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S"))
                        dt_ultima = datetime.strptime(horas_fin[-1], "%Y-%m-%d %H:%M:%S")
                        texto_header += f"\n⌛ Ocup. hasta: {dt_ultima.strftime('%d/%m %H:%M')}"
                    except:
                        subtexto += f" | Fin: {max(horas_fin)}"
        
        ui['lbl_main'].configure(text=texto_header)
        ui['lbl_sub'].configure(text=subtexto)

    def mover_grupo(self, asignacion_id, conductor_id, conductor_nombre):
        """Mueve un grupo actualizando la BD y la UI localmente (sin recarga completa)."""
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            cursor = conn.cursor()
            
            # 1. Actualizar BD y Registrar Actividad en la misma transacción
            if conductor_id == 0:
                cursor.execute("UPDATE asignaciones_grupos SET conductor_id = NULL, conductor_nombre = 'SIN ASIGNAR' WHERE id = ?", (asignacion_id,))
                accion = f"Movimiento manual: Asignación {asignacion_id} -> SIN ASIGNAR"
            else:
                cursor.execute("UPDATE asignaciones_grupos SET conductor_id = ?, conductor_nombre = ? WHERE id = ?", (conductor_id, conductor_nombre, asignacion_id))
                accion = f"Movimiento manual: Asignación {asignacion_id} -> {conductor_nombre}"
            
            # Insertar log usando la misma conexión
            usuario = obtener_usuario_actual()
            pid = os.getpid()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO registro_actividad (usuario, accion, pid, fecha) VALUES (?, ?, ?, ?)", (usuario, accion, pid, fecha))
            
            conn.commit()
            conn.close()
            
            # --- ACTUALIZACIÓN UI OPTIMIZADA ---
            # 1. Eliminar tarjeta antigua
            if asignacion_id in self.cards_ui:
                self.cards_ui[asignacion_id].destroy()
                del self.cards_ui[asignacion_id]
            
            # 2. Actualizar datos en memoria (Reutilizar objeto, evitar fetch a BD)
            source_c_id = 0
            grupo_obj = None
            
            for c_id, lista in self.grupos_por_conductor.items():
                for i, g in enumerate(lista):
                    if g['id'] == asignacion_id:
                        source_c_id = c_id
                        grupo_obj = lista.pop(i)
                        break
                if grupo_obj: break
            
            if grupo_obj:
                # Actualizar datos del objeto en memoria
                grupo_obj['motivo'] = conductor_nombre if conductor_id != 0 else "SIN ASIGNAR"
                
                if conductor_id not in self.grupos_por_conductor:
                    self.grupos_por_conductor[conductor_id] = []
                self.grupos_por_conductor[conductor_id].append(grupo_obj)
                
                # 3. Crear nueva tarjeta en la columna destino
                if conductor_id in self.cols_ui:
                    self.crear_tarjeta(self.cols_ui[conductor_id]['container'], grupo_obj)
            
            # 4. Actualizar cabeceras
            self.actualizar_header(source_c_id)
            self.actualizar_header(conductor_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo mover el grupo: {e}")

    def mostrar_detalle_grupo(self, grupo_data):
        grupo_num = grupo_data['grupo']
        total_pax = grupo_data.get('personas', 0)
        
        # Obtener desglose de pasajeros (Adultos, Niños, Bebés)
        adultos, ninos, bebes = 0, 0, 0
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(h.adultos), SUM(h.ninos), SUM(h.bebes) FROM grupos_hoteles gh JOIN hoteles h ON gh.hotel_id = h.id WHERE gh.grupo_numero = ?", (grupo_num,))
            row = cursor.fetchone()
            if row:
                adultos = row[0] if row[0] else 0
                ninos = row[1] if row[1] else 0
                bebes = row[2] if row[2] else 0
            conn.close()
        except: pass
        
        top = ctk.CTkToplevel(self)
        top.title(f"Detalle Grupo {grupo_num}")
        self.centrar_ventana(top, 1000, 600)
        
        # Asegurar que la ventana se abra en primer plano y sobre la principal
        top.transient(self)
        top.lift()
        top.focus_force()
        
        # --- HEADER CON PAX DESTACADO ---
        header_frame = ctk.CTkFrame(top, fg_color="white", corner_radius=0)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        h_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        h_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # Título
        ctk.CTkLabel(h_inner, text=f"Grupo {grupo_num}", font=("Segoe UI", 26, "bold"), text_color=self.theme["text_main"]).pack(side=tk.LEFT)
        
        # Badge Pax
        pax_badge = ctk.CTkFrame(h_inner, fg_color=self.theme["accent"], corner_radius=8)
        pax_badge.pack(side=tk.RIGHT)
        ctk.CTkLabel(pax_badge, text=f"👥 {total_pax} PAX\n(Ad: {adultos} | Ni: {ninos} | Be: {bebes})", font=("Segoe UI", 16, "bold"), text_color="white").pack(padx=20, pady=10)
        # --------------------------------

        # Frame para información general del grupo
        info_frame = ctk.CTkFrame(top, fg_color="transparent")
        info_frame.pack(fill=tk.X)

        # Treeview para detalles
        columns = ("establecimiento", "personas", "hora_recogida", "albaran", "hora_vuelo", "tipo_servicio")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        
        tree.heading("establecimiento", text="Hotel/Establecimiento")
        tree.heading("personas", text="Pax")
        tree.heading("hora_recogida", text="Hora Recogida")
        tree.heading("albaran", text="Albarán")
        tree.heading("hora_vuelo", text="Hora Vuelo/Aeropuerto")
        tree.heading("tipo_servicio", text="Tipo Servicio")
        
        tree.column("establecimiento", width=250)
        tree.column("personas", width=50, anchor="center")
        tree.column("hora_recogida", width=100, anchor="center")
        tree.column("albaran", width=100, anchor="center")
        tree.column("hora_vuelo", width=120, anchor="center")
        tree.column("tipo_servicio", width=100, anchor="center")
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE, timeout=30)
            cursor = conn.cursor()
            
            # Obtener estado de la asignación
            cursor.execute("SELECT conductor_nombre FROM asignaciones_grupos WHERE grupo_conductor = ?", (grupo_num,))
            asignacion_row = cursor.fetchone()
            estado_asignacion = asignacion_row[0] if asignacion_row else "No procesado"

            query = """
                SELECT 
                    h.establecimiento,
                    h.personas,
                    h.hora,
                    h.albaran,
                    a.hora_aeropuerto,
                    a.tiposer
                FROM grupos_hoteles gh
                JOIN hoteles h ON gh.hotel_id = h.id
                LEFT JOIN albaranes a ON h.albaran = a.numero
                WHERE gh.grupo_numero = ?
                ORDER BY h.hora
            """
            cursor.execute(query, (grupo_num,))
            rows = cursor.fetchall()
            
            for row in rows:
                # Manejar valores None
                vals = [str(x) if x is not None else "" for x in row]
                tree.insert("", tk.END, values=vals)
                
            # Mostrar etiqueta con el estado/motivo
            texto_estado = f"Estado Asignación: {estado_asignacion}"
            color_estado = "green"
            if "SIN ASIGNAR" in str(estado_asignacion):
                color_estado = "red"
            
            # Reemplazar Label por Text con scrollbar para textos largos
            frame_txt = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame_txt.pack(fill=tk.X, pady=10)
            
            # Usar CTkTextbox para el estado
            txt_estado = ctk.CTkTextbox(frame_txt, height=60, font=("Segoe UI", 12, "bold"), fg_color="#f4f5f7", text_color=color_estado)
            txt_estado.pack(fill=tk.X, expand=True)
            
            txt_estado.insert(tk.END, texto_estado)
            txt_estado.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener detalles: {e}")
        finally:
            if conn: conn.close()

if __name__ == "__main__":
    app = KanbanBoard()
    app.mainloop()