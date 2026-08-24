import sqlite3
import sys
import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog
from datetime import datetime, timedelta
import os
import shutil
import xml.etree.ElementTree as ET
import re

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

# Configuración de conexión a SQLite
DB_FILE = "gestor_datos.db"

LOG_FILE = "log_asignacion_conductores.txt"
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

        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Error inicializando tablas: {e}")

# ==============================================================================
# PARTE 0: IMPORTACIÓN DE ALBARANES
# ==============================================================================

def importar_albaranes_xml(xml_path, conexion):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        cursor = conexion.cursor()
        
        for albaran in root.find('Albaranes').findall('Albaran'):
            numero = albaran.findtext('Numero')
            empresa = albaran.findtext('Empresa')
            fecha = albaran.findtext('Fecha')
            tiporec = albaran.findtext('TipoRec')
            alias = albaran.findtext('Alias')
            proveedor = albaran.findtext('Proveedor')
            tiposer = albaran.findtext('TipoSer')
            hora = albaran.findtext('Hora')
            hora_aeropuerto = albaran.findtext('HoraAeropuerto')
            letrero = albaran.findtext('Letrero')
            ttoo = albaran.findtext('TTOO')
            agencia = albaran.findtext('Agencia')
            excursion = albaran.findtext('Excursion')
            guia = albaran.findtext('Guia')
            aeropuerto = albaran.findtext('Aeropuerto')
            vuelo = albaran.findtext('Vuelo')
            observacion = albaran.findtext('Observacion')
            referencia = albaran.findtext('Referencia')
            observacion_chofer = albaran.findtext('ObservacionChofer')
            
            # Insertar o reemplazar si ya existe (para evitar duplicados de PK)
            cursor.execute(
                """
                INSERT OR REPLACE INTO albaranes (numero, empresa, fecha, tiporec, alias, proveedor, tiposer, hora, hora_aeropuerto, letrero, ttoo, agencia, excursion, guia, aeropuerto, vuelo, observacion, referencia, observacion_chofer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (numero, empresa, fecha, tiporec, alias, proveedor, tiposer, hora, hora_aeropuerto, letrero, ttoo, agencia, excursion, guia, aeropuerto, vuelo, observacion, referencia, observacion_chofer)
            )
            
            zonas = albaran.find('Zonas')
            if zonas is not None:
                for zona in zonas.findall('Zona'):
                    orden = zona.findtext('Orden')
                    zona_inicio = zona.findtext('ZonaInicio')
                    zona_fin = zona.findtext('ZonaFin')
                    hora_zona = zona.findtext('Hora')
                    personas = zona.findtext('Personas')
                    adultos = zona.findtext('Adultos')
                    ninos = zona.findtext('Niños')
                    bicis = zona.findtext('Bicis')
                    bebes = zona.findtext('Bebes')
                    ninosb = zona.findtext('NiñosB')
                    invitados = zona.findtext('Invitados')
                    cursor.execute(
                        """
                        INSERT INTO zonas (albaran_id, orden, zona_inicio, zona_fin, hora, personas, adultos, ninos, bicis, bebes, ninosb, invitados)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (numero, orden, zona_inicio, zona_fin, hora_zona, personas, adultos, ninos, bicis, bebes, ninosb, invitados)
                    )
                    zona_id = cursor.lastrowid
                    
                    hoteles = zona.find('Hoteles')
                    if hoteles is not None:
                        for hotel in hoteles.findall('Hotel'):
                            orden_hotel = hotel.findtext('Orden')
                            establecimiento = hotel.findtext('Establecimiento')
                            hora_hotel = hotel.findtext('Hora')
                            personas_hotel = hotel.findtext('Personas')
                            adultos_hotel = hotel.findtext('Adultos')
                            ninos_hotel = hotel.findtext('Niños')
                            bebes_hotel = hotel.findtext('Bebes')
                            bicis_hotel = hotel.findtext('Bicis')
                            agencia_hotel = hotel.findtext('Agencia')
                            lugar_recogida = hotel.findtext('LugarRecogida')
                            observacion_hotel = hotel.findtext('Observacion')
                            cursor.execute(
                                """
                                INSERT INTO hoteles (zona_id, albaran, orden, establecimiento, hora, personas, adultos, ninos, bebes, bicis, agencia, lugar_recogida, observacion)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (zona_id, numero, orden_hotel, establecimiento, hora_hotel, personas_hotel, adultos_hotel, ninos_hotel, bebes_hotel, bicis_hotel, agencia_hotel, lugar_recogida, observacion_hotel)
                            )
        conexion.commit()
        log('Importación completa de todos los nodos del XML.')
        cursor.close()
    except Exception as e:
        log(f'Error al importar XML: {e}')
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

def ejecutar_asignacion_conductores(margen_minutos=120, margen_salida_entrada=150):
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
                disponibilidad[conductor_asignado[0]] = {'fin_ultimo_servicio': dt_fin, 'tipo_ultimo_servicio': tipo_servicio_actual}
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
                    
                    razon = ""
                    if plazas < total_personas:
                        razon = f"Capacidad ({plazas}<{total_personas})"
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
# PARTE 3: INTERFAZ GRÁFICA
# ==============================================================================

class KanbanBoard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Asignaciones Completo (SQLite)")
        self.geometry("1200x700")
        
        # Inicializar BD
        inicializar_tablas()
        
        # --- Panel de Control Superior ---
        control_frame = tk.Frame(self, pady=10, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(control_frame, text="Acciones:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)

        btn_importar = tk.Button(control_frame, text="0. Importar XML", command=self.accion_importar_albaranes, bg="#fff9c4")
        btn_importar.pack(side=tk.LEFT, padx=5)

        btn_vaciar = tk.Button(control_frame, text="🗑 Vaciar Tablas", command=self.accion_vaciar_tablas, bg="#ffccbc")
        btn_vaciar.pack(side=tk.LEFT, padx=5)

        btn_ver_import = tk.Button(control_frame, text="3. Ver Importaciones", command=self.accion_ver_importaciones, bg="#e0f7fa")
        btn_ver_import.pack(side=tk.LEFT, padx=5)

        btn_config = tk.Button(control_frame, text="⚙ Configuración", command=self.accion_configuracion, bg="#e0e0e0")
        btn_config.pack(side=tk.LEFT, padx=5)

        btn_agrupar = tk.Button(control_frame, text="1. Generar Grupos", command=self.accion_agrupar, bg="#e1f5fe")
        btn_agrupar.pack(side=tk.LEFT, padx=5)
        
        btn_asignar = tk.Button(control_frame, text="2. Asignar Conductores", command=self.accion_asignar, bg="#e8f5e9")
        btn_asignar.pack(side=tk.LEFT, padx=5)

        btn_refresh = tk.Button(control_frame, text="🔄 Refrescar Tablero", command=self.cargar_datos)
        btn_refresh.pack(side=tk.LEFT, padx=20)

        btn_cerrar = tk.Button(control_frame, text="❌ Cerrar", command=self.destroy, bg="#ef9a9a")
        btn_cerrar.pack(side=tk.RIGHT, padx=10)

        # --- Panel de Logs (Consola en pantalla) ---
        log_frame = tk.Frame(self, bg="#212121", bd=1, relief=tk.SUNKEN)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.txt_log = tk.Text(log_frame, height=8, bg="#1e1e1e", fg="#00e676", font=("Consolas", 9))
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb_log = ttk.Scrollbar(log_frame, orient="vertical", command=self.txt_log.yview)
        sb_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.configure(yscrollcommand=sb_log.set)
        
        global GUI_LOG_CALLBACK
        GUI_LOG_CALLBACK = self.actualizar_log

        # --- Tablero Kanban ---
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(self.main_frame)
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = tk.Frame(self.canvas)

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
        self.solo_salidas = True     # Valor por defecto
        
        # Cargar datos al inicio
        self.after(500, self.cargar_datos)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def actualizar_log(self, mensaje):
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)
        self.update_idletasks()

    def accion_ver_importaciones(self):
        top = tk.Toplevel(self)
        top.title("Visor de Albaranes Importados")
        top.geometry("1100x600")

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
            messagebox.showinfo("Éxito", f"Se han importado {len(archivos_xml)} archivos correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar XML: {e}")

    def accion_vaciar_tablas(self):
        top = tk.Toplevel(self)
        top.title("Vaciar Tablas")
        top.geometry("300x400")

        tk.Label(top, text="Selecciona las tablas a vaciar:", font=("Arial", 10, "bold")).pack(pady=10)

        tables = [
            "asignaciones_grupos",
            "grupos_hoteles",
            "hoteles",
            "zonas",
            "albaranes",
            "conductores"
        ]
        
        vars_dict = {}
        for tbl in tables:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(top, text=tbl, variable=var)
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
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                # Deshabilitar restricciones temporalmente
                cursor.execute('PRAGMA foreign_keys = OFF')
                
                for tbl in selected_tables:
                    # Verificar si la tabla existe antes de borrar
                    cursor.execute(f"DELETE FROM {tbl}")
                
                # Habilitar restricciones
                cursor.execute('PRAGMA foreign_keys = ON')
                
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Tablas vaciadas correctamente.")
                top.destroy()
                self.cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al vaciar tablas: {e}")

        tk.Button(top, text="Borrar Seleccionadas", command=ejecutar_borrado, bg="#ffcdd2").pack(pady=20)

    def accion_configuracion(self):
        top = tk.Toplevel(self)
        top.title("Configuración")
        top.geometry("350x450")
        
        tk.Label(top, text="Intervalo de agrupación (minutos):", font=("Arial", 10)).pack(pady=10)
        
        # Campo numérico libre
        entry_minutos = tk.Entry(top, justify="center")
        entry_minutos.insert(0, str(self.intervalo_minutos))
        entry_minutos.pack(pady=5)

        tk.Label(top, text="Margen entre asignaciones (minutos):", font=("Arial", 10)).pack(pady=10)
        
        # Campo numérico para minutos
        entry_margen = tk.Entry(top, justify="center")
        entry_margen.insert(0, str(self.margen_minutos))
        entry_margen.pack(pady=5)

        tk.Label(top, text="Margen Salida -> Entrada (minutos):", font=("Arial", 10)).pack(pady=10)
        entry_se = tk.Entry(top, justify="center")
        entry_se.insert(0, str(self.margen_salida_entrada))
        entry_se.pack(pady=5)

        # Checkbox para filtrar solo salidas
        var_solo_salidas = tk.BooleanVar(value=self.solo_salidas)
        chk_salidas = tk.Checkbutton(top, text="Solo procesar Salidas (S)", variable=var_solo_salidas)
        chk_salidas.pack(pady=15)
        
        def guardar():
            try:
                valor = int(entry_minutos.get())
                valor_margen = int(entry_margen.get())
                valor_se = int(entry_se.get())
                if valor <= 0:
                    raise ValueError("Minutos debe ser positivo")
                if valor_margen < 0:
                    raise ValueError("Margen debe ser positivo")
                if valor_se < 0:
                    raise ValueError("Margen S->E debe ser positivo")
                self.intervalo_minutos = valor
                self.margen_minutos = valor_margen
                self.margen_salida_entrada = valor_se
                self.solo_salidas = var_solo_salidas.get()
                # self.guardar_configuracion()
                messagebox.showinfo("Guardado", f"Configuración actualizada:\n- Agrupación: {valor} min\n- Margen General: {valor_margen} min\n- Margen S->E: {valor_se} min\n- Solo Salidas: {self.solo_salidas}")
                top.destroy()
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos.")

        tk.Button(top, text="Guardar", command=guardar, bg="#c8e6c9").pack(pady=10)

    def accion_agrupar(self):
        grupos = agrupar_hoteles_por_tiempo(self.intervalo_minutos, self.solo_salidas)
        if grupos:
            guardar_grupos_en_bd(grupos)
            messagebox.showinfo("Éxito", f"Se han generado {len(grupos)} grupos.")
        else:
            messagebox.showwarning("Atención", "No se generaron grupos (verifique datos de hoteles).")

    def accion_asignar(self):
        ejecutar_asignacion_conductores(self.margen_minutos, self.margen_salida_entrada)
        self.cargar_datos()
        messagebox.showinfo("Éxito", "Asignación de conductores completada.")

    def cargar_datos(self):
        # Limpiar widgets existentes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.column_map = {}

        try:
            conn = sqlite3.connect(DB_FILE, timeout=30)
            cursor = conn.cursor()

            # 1. Obtener conductores
            try:
                # Mostrar TODOS los conductores para permitir asignación manual
                cursor.execute("SELECT id, nombre, Plazas_Vehiculo FROM conductores")
                self.conductores = [{'id': row[0], 'nombre': row[1], 'plazas': row[2] if row[2] else 0} for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error cargando conductores: {e}")
                self.conductores = []
            
            self.conductores.insert(0, {'id': 0, 'nombre': 'Sin Asignar', 'plazas': 0})

            # 2. Obtener asignaciones
            try:
                cursor.execute("SELECT id, grupo_conductor, conductor_id, hora_inicio, hora_fin, total_personas, conductor_nombre, tipo_servicio FROM asignaciones_grupos")
                asignaciones_raw = cursor.fetchall()
            except:
                asignaciones_raw = []
            
            grupos_por_conductor = {c['id']: [] for c in self.conductores}
            
            for row in asignaciones_raw:
                # row es una tupla en sqlite3: (id, grupo_conductor, conductor_id, hora_inicio, hora_fin, total_personas, conductor_nombre, tipo_servicio)
                c_id = row[2] if row[2] else 0
                if c_id not in grupos_por_conductor:
                    c_id = 0
                
                # Formatear hora para mostrar solo inicio (HH:MM)
                # Formatear hora para mostrar fecha e inicio (DD/MM HH:MM)
                hora_mostrar = row[3]
                try:
                    dt_ini = datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S")
                    hora_mostrar = dt_ini.strftime("%H:%M")
                    hora_mostrar = dt_ini.strftime("%d/%m %H:%M")
                except:
                    pass

                grupos_por_conductor[c_id].append({
                    'id': row[0],
                    'grupo': row[1],
                    'hora': hora_mostrar,
                    'hora_fin_raw': row[4],
                    'personas': row[5],
                    'motivo': row[6] if len(row) > 6 else "",
                    'tipo_servicio': row[7] if len(row) > 7 else ""
                })

            # 3. Dibujar columnas
            for conductor in self.conductores:
                self.crear_columna(conductor, grupos_por_conductor[conductor['id']])

            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            conn.close()

        except Exception as e:
            print(f"Error cargando datos: {e}")

    def crear_columna(self, conductor, grupos):
        frame = tk.Frame(self.scrollable_frame, bg="#e2e4e6", padx=5, pady=5, width=280)
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10, anchor="n")
        
        self.column_map[frame] = conductor

        header_bg = "#dc3545" if conductor['id'] == 0 else "#007bff"
        header_fg = "white"
        
        texto_header = f"{conductor['nombre']} ({len(grupos)})"
        if conductor['id'] != 0:
            texto_header += f"\n🚍 {conductor['plazas']} plazas"
            
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
                        texto_header += f"\n⌛ Ocup. hasta: {max(horas_fin)}"
            
        header = tk.Label(frame, text=texto_header, bg=header_bg, fg=header_fg, font=("Arial", 8, "bold"), pady=5, borderwidth=2, relief="groove")
        header.pack(fill=tk.X, pady=(0, 5))
        
        # Spacer para asegurar ancho mínimo
        tk.Frame(frame, width=280, height=1, bg="#e2e4e6").pack()

        # Contenedor de tarjetas
        cards_container = tk.Frame(frame, bg="#e2e4e6")
        cards_container.pack(fill=tk.BOTH, expand=True)

        for g in grupos:
            self.crear_tarjeta(cards_container, g)

    def crear_tarjeta(self, parent, grupo):
        card = tk.Frame(parent, bg="white", bd=2, relief="raised")
        card.pack(fill=tk.X, pady=3, padx=2)
        
        l1 = tk.Label(card, text=f"G{grupo['grupo']} | {grupo['personas']} pax", font=("Arial", 10, "bold"), bg="white")
        l1.pack(anchor="w")
        
        # Mostrar Tipo de Servicio
        if grupo.get('tipo_servicio'):
            l_tipo = tk.Label(card, text=f"{grupo['tipo_servicio']}", font=("Arial", 8, "bold"), fg="#007bff", bg="white")
            l_tipo.pack(anchor="w")
            for w in (l_tipo,):
                w.bind("<Button-1>", lambda e, g=grupo: self.start_drag(e, g))
                w.bind("<B1-Motion>", self.do_drag)
                w.bind("<ButtonRelease-1>", self.stop_drag)
                w.bind("<Double-Button-1>", lambda e, g=grupo: self.mostrar_detalle_grupo(g))
        
        # Mostrar motivo si no está asignado
        motivo = grupo.get('motivo', '')
        if motivo and "SIN ASIGNAR" in motivo:
            texto_motivo = motivo.replace("SIN ASIGNAR:", "").strip()
            
            # Truncar para la tarjeta (mostrar solo 1ª línea o resumen) para que quepa
            if "\n" in texto_motivo or len(texto_motivo) > 50:
                texto_motivo = texto_motivo.split("\n")[0][:50] + "..."
            
            if not texto_motivo: texto_motivo = "Sin asignar"
            l_motivo = tk.Label(card, text=f"⚠ {texto_motivo}", font=("Arial", 8, "italic"), fg="red", bg="white", wraplength=250, justify="left")
            l_motivo.pack(anchor="w")
            
            for w in (l_motivo,):
                w.bind("<Button-1>", lambda e, g=grupo: self.start_drag(e, g))
                w.bind("<B1-Motion>", self.do_drag)
                w.bind("<ButtonRelease-1>", self.stop_drag)
                w.bind("<Double-Button-1>", lambda e, g=grupo: self.mostrar_detalle_grupo(g))

        l2 = tk.Label(card, text=f"🕒 {grupo['hora']}", font=("Arial", 12, "bold"), bg="white", fg="#333")
        l2.pack(anchor="w")
        
        for w in (card, l1, l2):
            w.bind("<Button-1>", lambda e, g=grupo: self.start_drag(e, g))
            w.bind("<B1-Motion>", self.do_drag)
            w.bind("<ButtonRelease-1>", self.stop_drag)
            w.bind("<Double-Button-1>", lambda e, g=grupo: self.mostrar_detalle_grupo(g))

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
                self.drag_win = tk.Toplevel(self)
                self.drag_win.overrideredirect(True)
                self.drag_win.attributes('-alpha', 0.7)
                lbl = tk.Label(self.drag_win, text=f"G{grupo['grupo']} ({grupo['personas']}p)", bg="yellow", bd=2, relief="solid")
                lbl.pack()
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
                self.mover_grupo(self.drag_data["item"]['id'], target_conductor)
        
        self.drag_data["item"] = None

    def mover_grupo(self, grupo_id, target_conductor):
        try:
            conn = sqlite3.connect(DB_FILE, timeout=30)
            cursor = conn.cursor()
            
            if target_conductor['id'] == 0:
                cursor.execute("UPDATE asignaciones_grupos SET conductor_id = NULL, conductor_nombre = 'SIN ASIGNAR' WHERE id = ?", (grupo_id,))
            else:
                cursor.execute("UPDATE asignaciones_grupos SET conductor_id = ?, conductor_nombre = ? WHERE id = ?", (target_conductor['id'], target_conductor['nombre'], grupo_id))
            
            conn.commit()
            conn.close()
            self.cargar_datos()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo mover el grupo: {e}")

    def mostrar_detalle_grupo(self, grupo_data):
        grupo_num = grupo_data['grupo']
        
        top = tk.Toplevel(self)
        top.title(f"Detalle Grupo {grupo_num}")
        top.geometry("1000x600")
        
        # Frame para información general del grupo
        info_frame = tk.Frame(top, pady=10, padx=10, bg="#f0f0f0")
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
            frame_txt = tk.Frame(info_frame, bg="#f0f0f0")
            frame_txt.pack(fill=tk.X, pady=5)
            
            # Ajustar altura dinámicamente según el contenido (min 1, max 15 líneas)
            altura_texto = min(max(texto_estado.count('\n') + 1, 1), 15)
            txt_estado = tk.Text(frame_txt, height=altura_texto, font=("Arial", 10, "bold"), bg="#f0f0f0", fg=color_estado, relief=tk.FLAT, wrap=tk.WORD)
            txt_estado.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            sb_txt = ttk.Scrollbar(frame_txt, orient="vertical", command=txt_estado.yview)
            sb_txt.pack(side=tk.RIGHT, fill=tk.Y)
            txt_estado.config(yscrollcommand=sb_txt.set)
            
            txt_estado.insert(tk.END, texto_estado)
            txt_estado.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener detalles: {e}")
        finally:
            if conn: conn.close()

if __name__ == "__main__":
    app = KanbanBoard()
    app.mainloop()