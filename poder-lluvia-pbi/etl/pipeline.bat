@echo off
REM ===== Pipeline diario Poder Lluvia (Windows + Task Scheduler) =====
REM Ejecuta ETL -> criticidad -> export CSV. Códigos de salida visibles para alerta.
cd /d %~dp0
python run.py
set RUNERR=%errorlevel%
python criticidad.py
python salida_csv.py
if %RUNERR% neq 0 (
  echo %date% %time% ALERTA: fuentes fallidas (exit %RUNERR%) >> ..\data\alertas.log
)
REM Vigia de datos antiguos (cubre "el pipeline nunca corro"): exit 3 = STALE
python alerta_stale.py --horas 48
set STALEERR=%errorlevel%
if %STALEERR% equ 3 (
  echo %date% %time% ALERTA: datos STALE - ver meta.ultima_actualizacion_ok >> ..\data\alertas.log
)
if %RUNERR% neq 0 exit /b %RUNERR%
exit /b %STALEERR%
