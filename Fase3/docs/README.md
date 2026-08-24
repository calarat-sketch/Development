Fase2 - Refactor y mejoras

Contenido:
- `Asignar_Tareas.py` : versión refactorizada con:
  - `config.ini` para configuración (o variables de entorno `DB_CONN`, `LOG_FILE`, `LIBERACION_HORAS`)
  - Logging con consola y rotación de fichero
  - Uso de context managers para la conexión
  - Funciones modularizadas y robustez en parseo de horas

Instrucciones rápidas:
1. Revisar `config.ini` y ajustar `connection_string` a tu entorno.
2. Ejecutar:

```bash
python Fase2/Asignar_Tareas.py
```

Notas:
- Este directorio es independiente; no modifica archivos fuera de `Fase2`.
- Si quieres que refactorice más scripts (por ejemplo `gestor_asignaciones_completo*.py`), indícamelo y lo hago en la misma estrategia.
