# Arquitectura de actualización automática — Power BI "Poder Lluvia Perú"

## 0. Verificaciones realizadas (no se asume ninguna API)
| Fuente | URL | Resultado verificado hoy |
|---|---|---|
| SUTRN (gob.pe) | https://www.gob.pe/institucion/sutran | HTTP **418** desde esta red: el WAF de gob.pe bloquea clientes sin navegador real. Funciona desde residencial/VPN PE. El ETL lo registra como fallo y alerta; **no inventa datos**. |
| SENAMHI | https://senamhi.gob.pe | Sin respuesta desde esta red (bloqueo geográfico probable). Verificar desde Perú. |
| CENEPRED portal de datos | https://cenepred.gob.pe/web/portal-de-datos/ | Verificar manualmente la estructura antes de programar el extractor. |
| INABI Road Book | https://www.gob.pe/institucion/inabi/publicaciones | Publicaciones PDF/XLS descargables (transitabilidad). |

**Conclusión honesta:** SENAMHI/SUTRN **no publican una API abierta documentada y verificada** para precipitación en tiempo real ni para bloqueos. Por eso la arquitectura usa tres carriles: scraping de páginas oficiales (con consentimiento y rate-limit), carga manual/semilla CSV marcada `fuente='MANUAL'`, y export intermedio para Power BI.

## 1. Diagrama (ASCII)
```
 [SITIOS OFICIALES]                [SEMILLA/MANUAL]
 SUTRN·MTC·SENAMHI·CENEPRED·INABI   CSV editados a mano
        │ scraping HTML (run.py)         │ load.py --check→load
        ▼                                ▼
   ┌──────────── SQLite poder_lluvia.db ("capa dorada", append-only, histórico)─────┐
   │ precipitaciones · eventos_viales · umbral_criticidad · criticidad_ultima      │
   │ etl_runs (auditoría de fallos) · meta (ultima_actualizacion_ok)               │
   └──────────────┬───────────────────────────────────────────────┬────────────────┘
        criticidad.py (motor de nivel 1–5)            salida_csv.py → data/export/*.csv
                                                                  │ sincroniza OneDrive
                        PC encendido (Task Scheduler diario) ◄────┘
                                  │ Gateway personal (gratis, ≤8 refrescos/día)
                                  ▼
                    POWER BI SERVICE (app.powerbi.com)  ← el servicio en la NUBE renderiza
                                          y sirve el tablero aunque tu PC esté APAGADO
    Alertas operativas: webhook Teams/Slack desde run.py + KPI "antigüedad>48h" en PBI
```
**Aclaración clave sobre "PC apagado":** dos cosas distintas corren en la nube:
1. *Ver el tablero* siempre: gratis (Power BI Service). ✔️
2. *Refrescar los datos* automáticamente: si el origen es local (OneDrive+gateway), **el PC debe estar encendido a la hora del refresco**. Para 100 % sin PC: usar un disparador en la nube (ver §3).

## 2. Herramientas por capa
| Capa | Herramienta | Costo |
|---|---|---|
| Ingesta | Python + requests/BeautifulSoup (`etl/`) | Gratis |
| Almacén histórico | SQLite (archivo único, versionable) | Gratis |
| Puerta a PBI | CSV en OneDrive (recomendado) o ODBC SQLite solo-local | Gratis |
| Modelado/visual | Power BI Desktop (modelo DAX en `report/modelo_dax.md`) | Gratis |
| Programación | Task Scheduler de Windows (`etl/pipeline.bat`) | Gratis |
| Refresco en Service | Gateway de instalación personal | Gratis, máx. 8/día |
| Alternativa sin PC | Power Automate (mover/regenerar CSV en la nube) o GitHub Actions (correr `pipeline.sh` y subir artefactos) | PA incluido en M365 personal; GH Actions gratis 2000 min/mes público |
| Alertas operativas | Webhook Teams/Slack desde `run.py`; banner "datos antiguos" en página y en PBI | Gratis |
| Escalado futuro | Fabric: Lakehouse + Dataflow Gen2 + Notebook (capa gratuita de Fabric con capacidad F0 desde ~US$5/mes pagándose por usuario, o incluido según licencia) | Variable |

## 3. Pasos de implementación (recetario)
> Versión ejecutable y detallada para Windows: **`docs/INSTALACION_WINDOWS.md`** (con checklist final y troubleshooting). Resumen:

1. **Clonar/cargar** este repo; `pip install -r etl/requirements.txt`; validar con `python tests/test_etl.py` (6× PASS).
2. **Verificar fuentes desde Perú**: abrir cada URL en navegador; si cambió la estructura, ajustar el selector en `etl/extract_sutran.py` (el pipeline avisa "HTTP 200 pero 0 registros" = sospecha de cambio de sitio). Extractores activos: SUTRN y COEN/INDECI; SENAMHI/CENEPRED/INABI quedan registrados como descargas pendientes de parser.
3. **Programar**: Task Scheduler → diaria 06:00 ejecutando `etl\pipeline.bat` (`schtasks /Create ...`, ver docs Paso 4; "reanudar tareas programadas" si el PC estuvo apagado).
4. **Nube**: mover `data/` a OneDrive; en PBI Desktop: Obtener datos → Carpeta → ruta OneDrive; aplicar modelo de `report/modelo_dax.md`.
5. **Publicar** en Mi área de trabajo (gratis); instalar **Gateway personal**, registrar la carpeta, configurar ≤8 refrescos/día. *(Si prefieres cero PC encendido: `.github/workflows/etl.yml` corre el pipeline en GitHub Actions y/o Power Automate regenera los CSV en SharePoint — PBI usa origen 100 % nube sin gateway.)*
6. **Alertas**: definir `PLP_ALERT_WEBHOOK` (Teams) → fallos de fuente y 0-registros llegan al canal; en el tablero, medida `alerta_stale` muestra ⚠️ si `ultima_actualizacion_ok` > 48 h. Dos mecanismos complementarios: (a) `run.py` borra la marca OK cuando alguna fuente falla → el KPI ve "SIN ACTUALIZACIÓN OK" ante un fallo activo; (b) el vigía `etl/alerta_stale.py` (incluido en `pipeline.bat/.sh` y en GitHub Actions, exit 3 + webhook + `alertas.log`) detecta además el caso "el pipeline nunca corrió" (PC apagado / tarea desactivada).
7. **Gobernanza**: página "Etl_runs" visible; toda fila lleva `url_origen` y `fuente` (SENAMHI vs MANUAL nunca se mezclan); geocodificación conservadora vía `etl/georef.py` (sin adivinar: lo no identificado queda `SIN_GEOCODIFICAR`).

## 4. Riesgos y mitigaciones
- **WAF/bloqueo (418/403):** reintentos con backoff, User-Agent identificado, frecuencia baja (1/día), registro del fallo + alerta. Nunca simulamos datos.
- **Cambios de HTML:** versión de parser en `etl_runs.version_parser`; alerta si 2 corridas seguidas dan 0 filas.
- **Falta de coordenadas:** no se geocodifica "a ojo"; tabla de centros poblados INEI cargada como CSV separado y auditable.
- **Uso de datos personales/límites de scraping:** solo contenido informativo público oficial; respetar términos de gob.pe.
- **Costo oculto:** todo lo esencial es $0; únicos pagos potenciales: almacenamiento extra OneDrive, capacidad Fabric F0, o SMS de alerta (opcional).
