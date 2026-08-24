# Gestor de Asignaciones de Conductores

Aplicación de escritorio Kanban para la gestión de rutas y asignación de conductores.

## Estructura del Proyecto

```
Fase3/
├── app/                              # Aplicación principal Kanban
│   └── gestor_asignaciones_completo_SQLite_estable_v1.1.py
│
├── data/                             # Datos y configuración
│   ├── gestor_datos.db               # Base de datos SQLite principal
│   ├── config.ini                    # Configuración de la aplicación
│   └── Tablas Importacion XML.sql    # Script de inicialización de BD
│
├── scripts/                          # Scripts auxiliares y herramientas
│   ├── importar_albaranes_xml.py     # Importar albaranes desde XML
│   ├── agrupacion_hoteles_30min.py   # Agrupar hoteles por tiempo
│   ├── Asignar_Tareas.py             # Asignación de tareas
│   ├── InsertarAleatorio_Conductores_SQLite.py  # Generar datos de prueba
│   ├── InsertarAleatorio_Conductores.py
│   ├── InsertarConductores_sql.py
│   ├── vaciar_tablas.py              # Limpiar base de datos
│   └── diagnostico_hoteles_conductores.py
│
├── pwa/                              # PWA (Progressive Web App)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── sw.js                         # Service Worker
│   └── manifest.json
│
├── docs/                             # Documentación
│   ├── README.md                     # Este archivo
│   └── PWA_README.md
│
├── logs/                             # Registros de la aplicación
│   └── log_asignacion_conductores.txt
│
├── archive/                          # Versiones anteriores
│   ├── gestor_asignaciones_completo.py
│   ├── gestor_asignaciones_completo_SQLite_estable.py
│   └── gestor_asignaciones_completo_SQLite_estable_v1.0.py
│
├── importados/                       # Datos importados
│   ├── Entradas260102140056569.xml
│   └── Salidas260102135724335.xml
│
├── pwa_api.py                        # API FastAPI para PWA
├── crear_ejecutable.bat              # Script para compilar EXE
├── iniciar_pwa.bat                   # Script para iniciar PWA
├── GestorAsignaciones.spec           # Configuración PyInstaller
├── requirements.txt                  # Dependencias Python
├── Albaranes1.xml                    # Archivo de datos de ejemplo
├── .gitignore                        # Configuración de Git
└── .venv/                            # Entorno virtual Python

build/ y dist/                        # Generados por PyInstaller (no en control de versiones)
```

## Uso

### Instalación de dependencias
```bash
pip install -r requirements.txt
```

### Ejecutar la aplicación Kanban
```bash
python app/gestor_asignaciones_completo_SQLite_estable_v1.1.py
```

### Ejecutar la PWA API
```bash
python -m uvicorn pwa_api:app --host 127.0.0.1 --port 8010
```

O usar el batch file:
```bash
iniciar_pwa.bat
```

### Compilar ejecutable
```bash
crear_ejecutable.bat
```

El EXE se generará en `dist/GestorAsignaciones.exe`

## Scripts de Utilidad

### Limpiar Base de Datos
```bash
cd scripts
python vaciar_tablas.py
```

### Generar Datos de Prueba
```bash
cd scripts
python InsertarAleatorio_Conductores_SQLite.py
```

### Importar Albaranes desde XML
```bash
cd scripts
python importar_albaranes_xml.py
```

## Tecnología

- **Python 3.14**
- **Tkinter + CustomTkinter** - UI del Kanban
- **SQLite3** - Base de datos
- **FastAPI** - PWA Backend
- **PyInstaller** - Empaquetado de ejecutable

## Rutas de Archivos

Los archivos ahora están organizados en subcarpetas específicas. El código busca automáticamente:

- **Base de datos**: `data/gestor_datos.db`
- **Configuración**: `data/config.ini`
- **Logs**: `logs/log_asignacion_conductores.txt`

En modo EXE compilado, busca los archivos en:
```
dist/GestorAsignaciones.exe
dist/data/gestor_datos.db
dist/data/config.ini
dist/logs/log_asignacion_conductores.txt
```

## Notas Importantes

✅ **Todos los archivos están verificados y funcionando correctamente**

- El Kanban se carga correctamente con los datos
- La BD contiene 10 conductores y 16 asignaciones
- Los scripts auxiliares encuentran la BD en su nueva ubicación
- La PWA API está configurada para la nueva estructura
- El EXE se compilará correctamente con los datos incluidos

