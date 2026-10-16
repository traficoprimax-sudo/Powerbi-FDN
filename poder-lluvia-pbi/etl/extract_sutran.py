"""Extractores por fuente. Cada uno devuelve lista de dicts + versión de parser.
Si el HTML cambia y no se extrae NADA, run.py lo marca como sospecha de cambio
(version_parser o 0 registros con HTTP 200 => alerta)."""
import re, hashlib
from bs4 import BeautifulSoup

V = "1.0"  # bump cuando cambie la lógica de parseo

def _fecha(text):
    m = re.search(r"(\d{1,2})\s+ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic", text)
    return None  # extracción fina de fechas: TODO tras verificar estructura real

def extract_sutran(html: str):
    """Noticias SUTRN: toma títulos+enlaces del listado público gob.pe."""
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a[href*='/institucion/sutran/noticias/']"):
        titulo = a.get_text(strip=True)
        if len(titulo) < 25:            # ruido/menús
            continue
        url = a["href"]
        t = titulo.lower()
        tipo = next((k for k, words in {
            "HUAICO": ["huaico"], "DESLIZO": ["deslizamiento"],
            "CAIDA_ROCAS": ["caída de rocas", "caida de rocas", "rocas", "derrumbe"],
            "CRECIDA": ["crecida", "desborde"], "DANO_PUENTE": ["puente"],
        }.items() if any(w in t for w in words)), None)
        if not tipo and any(w in t for w in ["bloque", "interrump", "transitab"]):
            tipo = "BLOCKED"
        if not tipo:
            continue                     # solo eventos relevantes para criticidad
        estado = ("INTERRUMPIDO" if any(w in t for w in ["bloque", "interrump"]) else
                  "RESTRINGIDO" if "restring" in t else "VERIFICANDO")
        out.append({
            "tipo_evento": tipo, "estado": estado, "entidad": "SUTRN",
            "titulo": titulo, "url_origen": url, "fecha": _fecha(titulo),
            "hash_contenido": hashlib.sha256((titulo + "|" + url).encode()).hexdigest(),
        })
    return out, V
