#!/usr/bin/env python3
"""
PWA API para Gestión de Rutas de Conductores
Permite a los conductores ver sus rutas, marcar recogidas e iniciar/finalizar tareas
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Configuración de rutas - buscar BD en carpeta data/
base_path = Path(__file__).parent
data_path = base_path / 'data' / 'gestor_datos.db'
pwa_path = base_path / 'pwa'

if data_path.exists():
    DB_FILE = str(data_path)
elif (base_path / 'gestor_datos.db').exists():
    DB_FILE = str(base_path / 'gestor_datos.db')
else:
    DB_FILE = str(data_path)  # Default path

BASE_DIR = base_path
PWA_DIR = pwa_path

# Crear app FastAPI
app = FastAPI(title="GestorAsignaciones - PWA", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Los assets de la PWA deben estar accesibles desde la raíz para que
# el manifest, el service worker y los archivos JS/CSS se carguen correctamente.
# Se sirven de forma explícita para evitar que el navegador intente cargar
# recursos desde rutas inexistentes como /manifest.json o /sw.js.
if PWA_DIR.exists():
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(str(PWA_DIR / "manifest.json"), media_type="application/manifest+json")

    @app.get("/sw.js")
    async def service_worker():
        return FileResponse(str(PWA_DIR / "sw.js"), media_type="application/javascript")

    @app.get("/app.js")
    async def app_js():
        return FileResponse(str(PWA_DIR / "app.js"), media_type="application/javascript")

    @app.get("/styles.css")
    async def styles_css():
        return FileResponse(str(PWA_DIR / "styles.css"), media_type="text/css")

# ============================================================================
# MODELOS
# ============================================================================

class RutaResumen(BaseModel):
    id: int
    grupo_numero: int
    conductor_nombre: str
    hora_inicio: str
    hora_fin: str
    total_personas: int
    tipo_servicio: str
    estado: str  # programada, en_curso, completada
    total_paradas: int
    confirmados: int
    fecha_inicio_real: Optional[str] = None
    fecha_fin_real: Optional[str] = None

class ParadaInfo(BaseModel):
    id: int
    orden: int
    establecimiento: str
    hora: str
    personas: int
    adultos: int
    ninos: int
    bebes: int
    agencia: str
    lugar_recogida: str
    confirmado: bool
    timestamp_confirmacion: Optional[str] = None

class AccionRuta(BaseModel):
    accion: str  # iniciar, finalizar, confirmado
    timestamp: str

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Redirige a la interfaz principal"""
    index_file = PWA_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"mensaje": "PWA de Gestión de Rutas - API v1.0"}

@app.get("/api/conductores")
async def listar_conductores():
    """Lista todos los conductores activos"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, Plazas_Vehiculo 
            FROM conductores 
            WHERE activo = 1
            ORDER BY nombre
        """)
        
        conductores = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"conductores": conductores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conductor/{conductor_id}/rutas")
async def obtener_rutas_conductor(conductor_id: int):
    """Obtiene todas las rutas asignadas a un conductor"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener rutas del conductor
        cursor.execute("""
            SELECT 
                ag.id,
                ag.grupo_conductor as grupo_numero,
                ag.conductor_nombre,
                ag.hora_inicio,
                ag.hora_fin,
                ag.total_personas,
                ag.tipo_servicio,
                COALESCE(ro.estado, 'programada') as estado,
                COALESCE(ro.hora_inicio_real, NULL) as fecha_inicio_real,
                COALESCE(ro.hora_fin_real, NULL) as fecha_fin_real,
                COALESCE(ro.observaciones, '') as observaciones,
                (SELECT COUNT(*) FROM grupos_hoteles gh WHERE gh.grupo_numero = ag.grupo_conductor) as total_paradas,
                (
                    SELECT COUNT(*)
                    FROM confirmaciones_paradas cp
                    JOIN rutas_operativas ro2 ON ro2.id = cp.ruta_id
                    WHERE ro2.asignacion_id = ag.id
                    AND cp.estado = 'confirmado_recogida'
                ) as confirmados
            FROM asignaciones_grupos ag
            LEFT JOIN rutas_operativas ro ON ro.asignacion_id = ag.id
            WHERE ag.conductor_id = ? AND ag.tipo_servicio IN ('S', 'E')
            ORDER BY ag.hora_inicio ASC
        """, (conductor_id,))
        
        rutas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"rutas": rutas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ruta/{asignacion_id}/paradas")
async def obtener_paradas_ruta(asignacion_id: int):
    """Obtiene todas las paradas de una ruta"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener grupo_numero
        cursor.execute("SELECT grupo_conductor FROM asignaciones_grupos WHERE id = ?", (asignacion_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        
        grupo_numero = row['grupo_conductor']
        
        # Obtener la ruta operativa asociada a la asignación para consultar
        # confirmaciones reales usando la estructura actual de la BD.
        cursor.execute("SELECT id FROM rutas_operativas WHERE asignacion_id = ?", (asignacion_id,))
        ruta_operativa = cursor.fetchone()
        ruta_operativa_id = ruta_operativa['id'] if ruta_operativa else None

        # Obtener paradas del grupo
        cursor.execute("""
            SELECT 
                h.id,
                COALESCE(CAST(h.orden AS INTEGER), gh.id) as orden,
                h.establecimiento,
                h.hora,
                h.personas,
                h.adultos,
                h.ninos,
                h.bebes,
                h.agencia,
                h.lugar_recogida,
                COALESCE(cp.estado, 'pendiente') as confirmado_estado,
                cp.hora_confirmacion as timestamp_confirmacion
            FROM grupos_hoteles gh
            JOIN hoteles h ON h.id = gh.hotel_id
            LEFT JOIN confirmaciones_paradas cp ON cp.ruta_id = ? AND cp.hotel_id = h.id
            WHERE gh.grupo_numero = ?
            ORDER BY COALESCE(CAST(h.orden AS INTEGER), gh.id) ASC
        """, (ruta_operativa_id, grupo_numero))
        
        paradas = []
        for row in cursor.fetchall():
            parada = {
                'id': row['id'],
                'orden': row['orden'],
                'establecimiento': row['establecimiento'],
                'hora': row['hora'],
                'personas': row['personas'],
                'adultos': row['adultos'],
                'ninos': row['ninos'],
                'bebes': row['bebes'],
                'agencia': row['agencia'],
                'lugar_recogida': row['lugar_recogida'],
                'confirmado': row['confirmado_estado'] == 'confirmado_recogida',
                'timestamp_confirmacion': row['timestamp_confirmacion']
            }
            paradas.append(parada)
        
        conn.close()
        return {"paradas": paradas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ruta/{asignacion_id}/iniciar")
async def iniciar_ruta(asignacion_id: int):
    """Marca el inicio de una ruta"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Crear o actualizar ruta operativa
        cursor.execute("""
            INSERT INTO rutas_operativas (asignacion_id, fecha, estado, hora_inicio_real, actualizado_en)
            VALUES (?, ?, 'en_curso', ?, ?)
            ON CONFLICT(asignacion_id) DO UPDATE SET
                estado = 'en_curso',
                hora_inicio_real = excluded.hora_inicio_real,
                actualizado_en = excluded.actualizado_en
        """, (asignacion_id, datetime.now().strftime("%Y-%m-%d"), timestamp, timestamp))
        
        conn.commit()
        conn.close()
        
        return {"status": "ok", "mensaje": "Ruta iniciada", "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ruta/{asignacion_id}/finalizar")
async def finalizar_ruta(asignacion_id: int):
    """Marca el fin de una ruta"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Actualizar ruta operativa
        cursor.execute("""
            UPDATE rutas_operativas 
            SET estado = 'completada', hora_fin_real = ?, actualizado_en = ?
            WHERE asignacion_id = ?
        """, (timestamp, timestamp, asignacion_id))
        
        conn.commit()
        conn.close()
        
        return {"status": "ok", "mensaje": "Ruta finalizada", "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parada/{asignacion_id}/{parada_id}/confirmar")
async def confirmar_parada(asignacion_id: int, parada_id: int):
    """Marca una parada como confirmada (recogida realizada)"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("SELECT id FROM rutas_operativas WHERE asignacion_id = ?", (asignacion_id,))
        ruta_operativa = cursor.fetchone()
        if not ruta_operativa:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")

        ruta_operativa_id = ruta_operativa[0]

        # Verificar si ya existe
        cursor.execute("""
            SELECT id FROM confirmaciones_paradas 
            WHERE ruta_id = ? AND hotel_id = ?
        """, (ruta_operativa_id, parada_id))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE confirmaciones_paradas 
                SET estado = 'confirmado_recogida', hora_confirmacion = ?, actualizado_en = ?
                WHERE ruta_id = ? AND hotel_id = ?
            """, (timestamp, timestamp, ruta_operativa_id, parada_id))
        else:
            cursor.execute("""
                INSERT INTO confirmaciones_paradas (ruta_id, hotel_id, estado, hora_confirmacion, actualizado_en)
                VALUES (?, ?, 'confirmado_recogida', ?, ?)
            """, (ruta_operativa_id, parada_id, timestamp, timestamp))
        
        conn.commit()
        conn.close()
        
        return {"status": "ok", "mensaje": "Parada confirmada", "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Verifica que la API está activa y accesible a la BD"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conductores")
        count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "ok",
            "database": "conectada",
            "conductores": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "desconectada",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando PWA API en http://0.0.0.0:8000")
    print("📱 Accede desde tu móvil: http://IP_DEL_ORDENADOR:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
