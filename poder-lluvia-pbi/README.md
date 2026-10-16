# 🌧️ Poder Lluvia Perú — ETL + Power BI de criticidad por precipitaciones y transitabilidad vial
Repo ejecutable del diseño de arquitectura (ver `pages/docs/arquitectura.md`).

## Estructura
```
etl/     config.py fetch.py extract_sutran.py run.py load.py criticidad.py salida_csv.py
         schema.sql pipeline.bat pipeline.sh requirements.txt
data/    poder_lluvia.db (SQLite) · *.csv semilla/manual · export/*.csv (salida para PBI)
report/  modelo_dax.md (modelo, medidas DAX, visuales, programación de refresco)
pages/   index.html (tablero web espejo, opcional) · docs/arquitectura.md
```
## Uso rápido
```bash
pip install -r etl/requirements.txt
python etl/run.py            # scrapea fuentes oficiales y registra fallos (exit 2 si alguna falló)
python etl/load.py           # carga CSVs manuales/semilla a SQLite (primero: --check)
python etl/criticidad.py     # recalcula niveles 1–5 por departamento
python etl/salida_csv.py     # exporta data/export/*.csv -> conectarlos a Power BI (carpeta)
```
Windows: programar `etl/pipeline.bat` con el Programador de tareas (diario 06:00).
Power BI: importar `data/export/` como origen de carpeta y seguir `report/modelo_dax.md`.

## Estado de verificación de fuentes (importante)
Desde redes no-peruanas, gob.pe responde **HTTP 418** (WAF) y senamhi.gob.pe puede no responder.
El pipeline está diseñado para **fallar de forma controlada y alertar**, nunca para inventar datos.
Los datos de ejemplo están marcados `fuente='MANUAL'` y separados de los oficiales.
