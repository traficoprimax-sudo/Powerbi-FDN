@echo off
REM ===== Pipeline diario Poder Lluvia (Windows + Task Scheduler) =====
REM Ejecuta ETL -> criticidad -> export CSV. Códigos de salida visibles para alerta.
cd /d %~dp0
python run.py
python criticidad.py
python salida_csv.py
if %errorlevel% neq 0 (
  echo "[ALERTA] pipeline con fallos" >> ..\data\alertas.log
)
exit /b %errorlevel%
