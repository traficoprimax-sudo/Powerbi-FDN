# Modelo de datos Power BI — Poder Lluvia Perú

## Origen (elegir según escenario)
- **A (recomendado gratis):** carpeta `data/export/*.csv` sincronizada por OneDrive → PBI Desktop "Obtener datos → Carpeta".
- **B:** SQLite vía driver ODBC (solo escritorio local; no publicable con gateway personal).

## Tablas
| Tabla | Tipo | Columnas clave |
|---|---|---|
| precipitaciones(_ejemplo) | Hecho | fecha, departamento, estacion, mm_dia, fuente, url_origen |
| eventos_viales | Hecho | fecha, via, tipo_evento, estado, departamento, entidad, url_origen |
| umbral_criticidad | Dimensión | nivel, nombre_nivel, score_min, color_hex |
| criticidad_ultima | Hecho agregado | entidad_id, nivel, score, actualizado_en |
| etl_runs + meta | Gobernanza | ok, error, ultima_actualizacion_ok |
| Calendario | Generada | `Calendario = CALENDAR(MIN(precipitaciones[fecha]), TODAY()+365)` |

## Medidas DAX
```
mm_max_7d        = CALCULATE(MAX(precipitaciones[mm_dia]), DATESINPERIOD(Calendario[Date], MAX(Calendario[Date]), -7, DAY))
eventos_activos  = CALCULATE(COUNTROWS(eventos_viales), eventos_viales[estado] IN {"INTERRUMPIDO","RESTRINGIDO"}, DATESINPERIOD(Calendario[Date], MAX(Calendario[Date]), -30, DAY))
nivel_calc       = SWITCH(TRUE(),
    [eventos_activos]>0 && [mm_max_7d]>=90, 5,
    [mm_max_7d]>=70 || (eventos_viales[tipo_evento]="HUAICO"), 4,
    [mm_max_7d]>=40 || [eventos_activos]>0, 3,
    [mm_max_7d]>=20, 2, 1)
antiguedad_horas = DIVIDE((NOW() - max(meta[valor_fecha])), 1/24)   -- parsear meta en Power Query
alerta_stale     = IF([antiguedad_horas]>48, "⚠️ DATOS ANTIGUOS", "OK")
```
## Visuales
1. Mapa (campos personalizados lat/lon o Bing estándar por departamento) con color = nivel_calc.
2. Tarjetas KPI: eventos activos, mm máx 7d, última actualización OK, alerta_stale.
3. Matriz depto/prov/dist × nivel con formato condicional desde umbral_criticidad[color_hex].
4. Línea temporal: mm_dia vs. eventos por semana (persistencia histórica).
5. Página "Gobernanza": etl_runs (fuente, ok, error, http_status) — detección de fallos visible.
## Actualización programada
Publicar en Mi área de trabajo (gratis) + Gateway personal apuntando a la carpeta OneDrive; 8 refrescos/día gratis. Alternativa sin PC encendido: flujo de Power Automate que reescribe los CSV en SharePoint/OneDrive para usar "Actualización programada en la nube".
