#!/usr/bin/env bash
# Versión Linux/macOS/cron del pipeline
cd "$(dirname "$0")"
python3 run.py; R1=$?
python3 criticidad.py
python3 salida_csv.py
[ $R1 -ne 0 ] && echo "$(date) ALERTA: fuentes fallidas" >> ../data/alertas.log
exit $R1
