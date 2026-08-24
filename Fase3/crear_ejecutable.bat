@echo off
echo --- Instalando PyInstaller ---
python -m pip install pyinstaller

echo.
echo --- Copiando datos actuales a la carpeta dist ---
if exist "data\gestor_datos.db" (
  if not exist "dist\data" mkdir "dist\data"
  copy /Y "data\gestor_datos.db" "dist\data\gestor_datos.db" >nul
)
if exist "data\config.ini" (
  if not exist "dist\data" mkdir "dist\data"
  copy /Y "data\config.ini" "dist\data\config.ini" >nul
)
if exist "logs\log_asignacion_conductores.txt" (
  if not exist "dist\logs" mkdir "dist\logs"
  copy /Y "logs\log_asignacion_conductores.txt" "dist\logs\log_asignacion_conductores.txt" >nul
)

echo.
echo --- Generando Ejecutable (esto puede tardar unos minutos) ---
python -m PyInstaller --noconsole --onefile --name "GestorAsignaciones" ^
  --hidden-import babel.numbers ^
  --add-data "data\gestor_datos.db;data" ^
  --add-data "data\config.ini;data" ^
  --add-data "logs\log_asignacion_conductores.txt;logs" ^
  app\gestor_asignaciones_completo_SQLite_estable_v1.1.py

if exist "data\gestor_datos.db" (
  if not exist "dist\data" mkdir "dist\data"
  copy /Y "data\gestor_datos.db" "dist\data\gestor_datos.db" >nul
)
if exist "data\config.ini" (
  if not exist "dist\data" mkdir "dist\data"
  copy /Y "data\config.ini" "dist\data\config.ini" >nul
)

echo.
echo Hecho. Busca el archivo "dist\GestorAsignaciones.exe".
pause