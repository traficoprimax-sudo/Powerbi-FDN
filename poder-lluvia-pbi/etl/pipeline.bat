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
exit /b %RUNERR%
