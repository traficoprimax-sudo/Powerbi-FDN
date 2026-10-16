# 🌧️ Poder Lluvia Perú — ETL + Power BI de criticidad por precipitaciones y transitabilidad vial
Repo ejecutable del diseño de arquitectura (ver `pages/docs/arquitectura.md`).

## 👉 ¿Recién llegado? Empieza por [`docs/INSTALACION_WINDOWS.md`](docs/INSTALACION_WINDOWS.md)
Guía paso a paso (Python → Task Scheduler → OneDrive → Power BI → Gateway → alertas). 45–60 min, $0.

## Estructura
```
etl/     config.py fetch.py extract_sutran.py georef.py run.py load.py criticidad.py salida_csv.py
         schema.sql pipeline.bat pipeline.sh requirements.txt
data/    poder_lluvia.db (SQLite) · *.csv semilla/manual/demo · export/*.csv (salida para PBI)
tests/   test_etl.py (6 pruebas unitarias sin red: fechas, geocodificación, clasificación, motor, export, vigía stale)
report/  modelo_dax.md (modelo, medidas DAX, visuales, programación de refresco)
docs/    INSTALACION_WINDOWS.md (recetario completo con checklist y troubleshooting)
pages/   index.html (tablero web espejo, opcional) · docs/arquitectura.md
.github/ workflows/etl.yml (pipeline opcional en la nube con GitHub Actions)
```

## Uso rápido
```bash
pip install -r etl/requirements.txt
python tests/test_etl.py       # 6× PASS antes de tocar nada
python etl/run.py              # scrapea fuentes oficiales; exit 2 si alguna falló (registrado + alerta)
python etl/load.py --check     # valida CSVs de data/ sin escribir
python etl/load.py             # carga semilla/manual/demo a SQLite (trazado en etl_runs)
python etl/criticidad.py       # recalcula niveles 1–5 por departamento
python etl/salida_csv.py       # exporta data/export/*.csv -> conectarlos a Power BI (origen "Carpeta")
python etl/alerta_stale.py     # vigía: exit 3 si no hay actualización OK reciente (>48h) — ya incluido en pipeline.bat/.sh
```
Windows: programar `etl/pipeline.bat` con el Programador de tareas (diario 06:00) — ver docs Paso 4.
Power BI: importar `data/export/` como origen de carpeta y seguir `report/modelo_dax.md`.

## Fuentes configuradas (páginas oficiales, NO APIs asumidas)
| Fuente | URL | Estado extractor |
|---|---|---|
| SUTRN noticias | gob.pe/institucion/sutran/noticias | ✅ parser v1.1 (clasifica HUAICO/CAIDA_ROCAS/CRECIDA/BLOCKED) |
| COEN/INDECI | indeci.gob.pe (avisos/alertas) | ✅ parser genérico v1.1 |
| SENAMHI advertencias | senamhi.gob.pe | ⏳ descarga registrada; parser pendiente de verificar HTML real |
| CENEPRED portal datos | cenepred.gob.pe | ⏳ idem |
| INABI Road Book | gob.pe/institucion/inabi/publicaciones | ⏳ PDF/XLS: vía carga manual trazada o futuro parser |

## Estado de verificación de fuentes (importante)
Desde redes no-peruanas, gob.pe responde **HTTP 418** (WAF), senamhi/cenepred/indeci pueden
no responder desde datacenters. El pipeline está diseñado para **fallar de forma controlada y
alertar** (tabla `etl_runs`, `meta`, webhook opcional, `alertas.log`), nunca para inventar datos.

## Datos DEMO vs reales
- `precipitaciones_demo.csv` / `eventos_viales_demo.csv`: valores ilustrativos **dentro de la
  ventana de 7/30 días** para que el tablero muestre niveles (Ancash=Extrema etc.). Marcados
  `fuente='MANUAL_DEMO'` y títulos `[DEMO]`. Elimínalos cuando tengas datos oficiales.
- `precipitaciones_ejemplo.csv`: set histórico de enero 2026 (fuera de ventana → no puntúa).
- Umbrales de nivel: `umbral_criticidad.csv` (documentados, editables sin tocar código).

## 🚀 Publicar en GitHub
```bash
cd poder-lluvia-pbi
git init -q && git add -A
git commit -qm "Poder Lluvia Perú: ETL + Power BI (arquitectura, pruebas 6/6)"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/poder-lluvia-peru.git
git push -u origin main
```
Luego: Settings → Pages → Deploy from branch → rama `main`, carpeta `/pages` → tablero espejo en `https://<tu-usuario>.github.io/poder-lluvia-peru/`.
Nota: la BD SQLite (`data/poder_lluvia.db`) y los logs están en `.gitignore`; se crean automáticamente al ejecutar `python etl/run.py` o `etl/load.py`.
