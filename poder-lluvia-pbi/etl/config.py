"""Configuración de fuentes ETL — Poder Lluvia Perú.
PRINCIPIO: ninguna API se asume como existente. Cada fuente tiene URL real
verificable en el sitio oficial; si cambia, el pipeline falla de forma
CONTROLADA y lo registra (no inventa datos)."""

import os

# --- Carpeta de trabajo (en la nube: se sincroniza con OneDrive) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("PLP_DATA", os.path.join(BASE_DIR, "..", "data"))

# --- Cabecera respetuosa (muchos sitios .gob.pe bloquean clientes sin User-Agent) ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124 Safari/537.36 PoderLluviaETL/1.0",
    "Accept-Language": "es-PE,es;q=0.9",
}
TIMEOUT = 30
MAX_RETRIES = 3          # reintentos por fuente con backoff exponencial
RETRY_BACKOFF = 5        # segundos: 5, 10, 20...

# --- Fuentes oficiales (URLs verificadas manualmente; NO son APIs, son páginas/listados HTML) ---
SOURCES = {
    "sutran_noticias": {
        "url": "https://www.gob.pe/institucion/sutran/noticias",
        "kind": "listing_html",
        "nota": "Listado público de noticias SUTRN-MTC. Bloquea WAF a clientes sin UA real.",
    },
    "senamhi_advertencias": {
        "url": "https://senamhi.gob.pe/index.php/productos/advertencias-especiales-por-lluvias",
        "kind": "listing_html",
        "nota": "Advertencias especiales por lluvias (ENERO). Página histórica del SENAMHI.",
    },
    "cenepred_alertas": {
        "url": "https://cenepred.gob.pe/web/portal-de-datos/",
        "kind": "html",
        "nota": "Portal de datos CENEPRED (alertas/evacuados). Verificar estructura antes de parsear.",
    },
    "inabi_roadbook": {
        "url": "https://www.gob.pe/institucion/inabi/publicaciones",
        "kind": "listing_html",
        "nota": "INABI publica el Road Book (estado de transitabilidad de redes viales) como PDF/XLS descargables.",
    },
}

# --- Canal de alertas operativas (Webhook Teams/Slack OPCIONAL) ---
ALERT_WEBHOOK_URL = os.environ.get("PLP_ALERT_WEBHOOK", "")  # vacío = sin webhook

# --- Umbrales de criticidad (tabla umbral_criticidad en SQLite) ---
# Se documentan en report/modelo_dax.md y se cargan desde data/umbral_criticidad.csv
