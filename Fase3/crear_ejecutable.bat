@echo off
echo --- Instalando PyInstaller ---
pip install pyinstaller

echo.
echo --- Generando Ejecutable (esto puede tardar unos minutos) ---
python -m PyInstaller --noconsole --onefile --name "GestorAsignaciones" --hidden-import babel.numbers gestor_asignaciones_completo.py

echo.
echo Hecho. Busca el archivo "GestorAsignacionesFase1.exe" en la carpeta "dist".
pause