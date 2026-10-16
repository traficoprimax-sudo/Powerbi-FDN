# 🌧️ Poder Lluvia Perú — Guía de Instalación (Windows, 100 % gratuito)
Lleva el repo de "código" a "tablero que se actualiza solo". Tiempo estimado: 45–60 min.

## Paso 0 — Requisitos
- Windows 10/11, Python 3.11+ → https://python.org (marca **"Add python.exe to PATH"**)
- Power BI Desktop (gratis) → Microsoft Store o https://powerbi.microsoft.com/desktop
- Cuenta Microsoft con OneDrive (incluida en PC/M365 personal)
- (Solo para refresco automático del dataset) **On-premises Data Gateway – Personal**, gratis
  → descargar "Gateway (personal)" desde learn.microsoft.com/data-integration/gateway/service-gateway-personal-mode

## Paso 1 — Instalar dependencias ETL
```bat
cd C:\poder-lluvia-pbi\etl
pip install -r requirements.txt
```

## Paso 2 — Configurar carpeta en la nube
1. Mueve/copias toda la carpeta `poder-lluvia-pbi` dentro de tu **OneDrive** (ej. `C:\Users\TU\OneDrive\poder-lluvia-pbi`).
2. Verifica que `data\export\*.csv` se sincronizan (icono de nube al pasar el mouse).

## Paso 3 — Primera ejecución manual (prueba de fuego)
```bat
python etl\run.py          :: scrapea fuentes; exit 2 = alguna fuente fallida (WAF gob.pe es normal fuera de Perú)
python etl\load.py --check :: valida CSVs semilla sin escribir
python etl\load.py         :: carga data\*.csv (precipitaciones manuales + umbrales) a SQLite
python etl\criticidad.py   :: calcula niveles 1–5 por departamento
python etl\salida_csv.py   :: genera data\export\*.csv para Power BI
python tests\test_etl.py   :: 5 pruebas unitarias, todas PASS
```

## Paso 4 — Programar la actualización diaria (Task Scheduler)
```bat
:: Una sola vez (consola normal basta para /RL LIMITED):
schtasks /Create /TN "PoderLluvia_ETL" /SC DAILY /ST 06:00 ^
  /TR "'C:\Users\TU\OneDrive\poder-lluvia-pbi\etl\pipeline.bat'" ^
  /RL LIMITED
schtasks /Run /TN "PoderLluvia_ETL"     :: prueba inmediata
```
`pipeline.bat` ejecuta run → criticidad → salida_csv y deja rastro en `data\alertas.log` + tabla `etl_runs`.
✅ Recomendado además: Panel de control → Opciones de energía → "Reanudar tareas programadas" (el PC encendido a las 06:00 refresca; si estuvo apagado, lo hace al encenderse).

## Paso 5 — Conectar Power BI Desktop
1. Abrir Power BI Desktop → **Obtener datos → Carpeta** → `...\OneDrive\poder-lluvia-pbi\data\export`
2. Seleccionar: `precipitaciones`, `eventos_viales`, `criticidad_ultima`, `umbral_criticidad`, `meta`, `etl_runs` (la tabla `_ejemplo` márcala como demo o exclúyela en producción).
3. Modelar relaciones y pegar medidas DAX de `report\modelo_dax.md`.
4. Guardar como `poder_lluvia.pbix` en la misma carpeta OneDrive.

## Paso 6 — Publicar y refrescar en la nube
1. En PBI Desktop: **Archivo → Publicar → Mi área de trabajo** (gratis, sin licencia Pro).
2. app.powerbi.com → Configuración del conjunto de datos → **Credenciales de origen de datos** → Windows → autenticación de Windows → cuenta Microsoft.
3. **Gateway → Agregar (puerta de aplicación personal)**: instala el gateway del Paso 0 e inícialo con la misma cuenta.
4. **Actualización programada → Activada → frecuencia diaria 07:00** (≤8 veces/día gratis).
   - El *servicio* muestra el tablero aunque tu PC esté apagado (último estado guardado en la nube).
   - El *refresco* desde archivos locales requiere PC encendido + gateway activo a esa hora.
   - Alternativa 100 % nube: flujo de Power Automate que reescribe los CSV en SharePoint/OneDrive (ver arquitectura §5).

## Paso 7 — Alertas operativas (opcional, 5 min)
- Teams: canal → Conectores → "Webhook entrante" → copiar URL → variable de entorno:
  `setx PLP_ALERT_WEBHOOK "https://outlook.office.com/webhook/..."` (reabrir consola).
- O vista nativa: app.powerbi.com → tablero → ⋯ → **Alertas** sobre la tarjeta "Días desde última actualización" (medida `alerta_stale`).

## Verificación final (checklist)
- [ ] `python tests\test_etl.py` → 5× PASS
- [ ] `schtasks /Query /TN PoderLluvia_ETL /V` → "Last Task Result: 0" (o 2 con alerta explicada)
- [ ] `data\export\meta.csv` contiene `ultima_actualizacion_ok` reciente
- [ ] Tablero publicado: KPI "Última actualización" refleja fecha real
- [ ] Refresco manual en servicio (⋯ → Actualizar ahora) funciona vía gateway

## Solución de problemas
| Síntoma | Causa probable | Acción |
|---|---|---|
| HTTP 418 en gob.pe | WAF bloquea redes no peruanas | Ejecutar desde red peruana; el pipeline ya registra y alerta |
| Gateway "sin conexión" | PC apagado/suspendido o sesión expirada | Ajustar energía; reiniciar servicio del gateway |
| PBI no ve cambios de CSV | Ruta local ≠ ruta sincronizada | Reconfigurar origen con la ruta completa de OneDrive |
| 0 registros con HTTP 200 | Sitio cambió su HTML | Ajustar selectores en `extract_sutran.py`, subir `V` |
