@echo off
REM Script para iniciar la PWA API
REM Gestor de Rutas para Conductores

echo.
echo ========================================
echo  Gestor de Rutas - PWA
echo  API FastAPI para Conductores
echo ========================================
echo.

REM Verificar si el entorno virtual existe
if not exist .venv (
    echo Error: Entorno virtual no encontrado
    echo Ejecuta primero: python -m venv .venv
    exit /b 1
)

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Verificar si FastAPI está instalado
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Instalando FastAPI y uvicorn...
    pip install fastapi uvicorn -q
)

REM Obtener la IP local
for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set LOCAL_IP=%%a

echo.
echo 🚀 Iniciando PWA API...
echo.
echo 📱 Accede desde tu navegador:
echo    - Local:   http://127.0.0.1:8000
echo    - Móvil:   http://%LOCAL_IP%:8000
echo.
echo Presiona Ctrl+C para detener
echo.

REM Iniciar la API
python pwa_api.py

pause
