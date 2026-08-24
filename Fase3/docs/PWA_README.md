# 📱 PWA - Gestor de Rutas para Conductores

## Descripción

Una aplicación web progresiva (PWA) que permite a los conductores:
- ✅ Ver sus rutas/grupos asignados
- ✅ Consultar detalles de paradas (clientes)
- ✅ Marcar paradas como "recogida confirmada"
- ✅ Iniciar y finalizar rutas
- ✅ Seguimiento en tiempo real
- ✅ Funciona offline (con Service Worker)
- ✅ Instalable como app en móvil

---

## Requisitos

- Python 3.8+
- FastAPI y Uvicorn
- Navegador moderno con soporte PWA
- Conexión a la red (la app funciona offline también)

---

## Instalación

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn pydantic
```

O ejecutar directamente:

```bash
cd Fase3
.\iniciar_pwa.bat
```

### 2. Iniciar la API

```bash
python pwa_api.py
```

La API se iniciará en `http://0.0.0.0:8000`

### 3. Acceder desde el navegador

**Desde el ordenador:**
```
http://127.0.0.1:8000
```

**Desde móvil (en la misma red):**
```
http://<IP_DEL_ORDENADOR>:8000
```

Por ejemplo: `http://192.168.1.100:8000`

---

## Estructura de Carpetas

```
Fase3/
├── pwa_api.py              # API FastAPI
├── iniciar_pwa.bat         # Script para iniciar
├── pwa/
│   ├── index.html          # Interfaz principal
│   ├── app.js              # Lógica de la app
│   ├── styles.css          # Estilos optimizados
│   ├── sw.js               # Service Worker (offline)
│   └── manifest.json       # Configuración PWA
```

---

## Funcionalidades

### 1. Seleccionar Conductor

- Abre la app
- Selecciona tu nombre en el dropdown
- Se cargan automáticamente tus rutas

### 2. Ver Rutas

Cada ruta muestra:
- **Número de ruta** (grupo)
- **Estado** (Programada / En Curso / Completada)
- **Horarios** (salida y llegada)
- **Personas** totales
- **Paradas** y progreso de confirmaciones

### 3. Iniciar Ruta

- Abre el detalle de la ruta
- Presiona **"▶️ Iniciar Ruta"**
- Se registra automáticamente la hora de inicio

### 4. Confirmar Paradas

Para cada parada:
1. Ver detalles: establecimiento, hora, personas, agencia
2. Presionar **"✓ Confirmar Recogida"**
3. Se marca como completada (con check verde)

### 5. Finalizar Ruta

- Presiona **"⏹️ Finalizar Ruta"**
- Se registra la hora de fin
- La ruta pasa a estado "Completada"

---

## Campos de Base de Datos Utilizados

### Nuevos campos agregados:

**Tabla `rutas_operativas`:**
- `id` (PK)
- `asignacion_id` (FK a asignaciones_grupos)
- `fecha` (TEXT)
- `estado` (TEXT) - programada/en_curso/completada
- `hora_inicio_real` (TEXT) - timestamp de inicio
- `hora_fin_real` (TEXT) - timestamp de fin
- `observaciones` (TEXT)
- `actualizado_en` (TEXT)

**Tabla `confirmaciones_paradas`:**
- `id` (PK)
- `asignacion_id` (FK)
- `parada_id` (FK a hoteles)
- `estado` (TEXT) - confirmado_recogida/no_confirmado
- `timestamp` (TEXT)

---

## Endpoints API

### Conductor

```
GET  /api/conductores
→ Lista todos los conductores activos
```

### Rutas

```
GET  /api/conductor/{conductor_id}/rutas
→ Obtiene rutas del conductor

POST /api/ruta/{asignacion_id}/iniciar
→ Marca inicio de ruta

POST /api/ruta/{asignacion_id}/finalizar
→ Marca fin de ruta
```

### Paradas

```
GET  /api/ruta/{asignacion_id}/paradas
→ Obtiene paradas de una ruta

POST /api/parada/{asignacion_id}/{parada_id}/confirmar
→ Confirma una parada (recogida)
```

### Salud

```
GET  /api/health
→ Verifica estado de la API y BD
```

---

## Características PWA

### 1. Instalable como App

En navegadores soportados (Chrome, Firefox, Edge):
- Botón "Instalar" en la barra de direcciones
- O: Menú → "Instalar app"
- Se instala como app nativa en móvil

### 2. Funciona Offline

El Service Worker cachea:
- Archivos estáticos (HTML, CSS, JS)
- Intentos de API para sincronizar después
- Permite usar la app sin conexión

### 3. Notificaciones Push (Opcional)

Se puede extender para enviar notificaciones sobre:
- Nueva ruta asignada
- Recordatorio de inicio de ruta
- Alertas de entrega

---

## Optimización Móvil

✅ Diseño responsivo
✅ Interfaz táctil (botones grandes)
✅ Colores de alto contraste
✅ Fuentes legibles
✅ Carga rápida
✅ Scroll suave
✅ Touch feedback

---

## Troubleshooting

### Error: "No se puede conectar"

- Verifica que la API está corriendo: `python pwa_api.py`
- Verifica la IP del ordenador: `ipconfig` (Windows) o `ifconfig` (Linux)
- Asegúrate que móvil y PC están en la misma red
- Desactiva firewall temporalmente si es necesario

### Las rutas no se cargan

- Verifica que hay datos en la BD: `gestor_datos.db`
- Verifica que hay conductores activos
- Revisa la consola del navegador (F12 → Console)

### No funciona offline

- Service Worker debe estar registrado
- La app debe haber sido abierta al menos una vez online
- Revisa Application → Service Workers (F12)

---

## Desarrollo Futuro

Posibles mejoras:
- 🗺️ Integración con Google Maps
- 📸 Captura de foto en paradas
- 💬 Chat con supervisor
- 📊 Estadísticas de desempeño
- 🔔 Notificaciones en tiempo real
- 📍 GPS tracking continuo
- 🎙️ Comandos de voz

---

## Licencia

© 2024 - Gestor de Asignaciones

---

## Soporte

Para reportar bugs o sugerencias, contacta al equipo de desarrollo.
