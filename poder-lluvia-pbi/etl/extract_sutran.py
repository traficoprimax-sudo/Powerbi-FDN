"""Extractores por fuente. Cada uno devuelve lista de dicts + versión de parser.
Si el HTML cambia y no se extrae NADA, run.py lo marca como sospecha de cambio
(version_parser o 0 registros con HTTP 200 => alerta)."""
import re, hashlib, datetime as dt
from bs4 import BeautifulSoup
import georef

V = "1.1"  # bump cuando cambie la lógica de parseo

MESES = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
         "julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,
         "noviembre":11,"diciembre":12}

def _fecha(text):
    """Extrae fecha ISO de textos tipo '15 de enero de 2026' o listados gob.pe.
    Acepta también formatos numéricos dd/mm/yyyy. Devuelve None si no hay certeza."""
    t = georef.norm(text)
    m = re.search(r"\b(\d{1,2})\s*(?:de\s+|[/\-])\s*(" + "|".join(MESES) + r")\s*(?:de\s+|[/\-])?\s*(\d{4})", t)
    if m:
        try:
            return dt.date(int(m.group(3)), MESES[m.group(2)], int(m.group(1))).isoformat()
        except ValueError:
            return None
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", t)
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None
    m = re.search(r"\b(" + "|".join(MESES) + r")\s+(\d{1,2}),?\s+(\d{4})\b", t)
    if m:
        try:
            return dt.date(int(m.group(3)), MESES[m.group(1)], int(m.group(2))).isoformat()
        except ValueError:
            return None
    return None

def _dep(text):
    """Departamento explícito; fallback conservador por carretera conocida."""
    return georef.infer_dep(text) or georef.infer_by_route(text)

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
            "departamento": _dep(titulo),
            "hash_contenido": hashlib.sha256((titulo + "|" + url).encode()).hexdigest(),
        })
    return out, V

def extract_indeci(html: str):
    """COEN/INDECI: avisos y alertas por lluvias. Mismo principio: si el HTML cambia
    y salen 0 registros con HTTP 200, run.py emite alerta de sospecha de cambio."""
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a[href]"):
        titulo = a.get_text(strip=True)
        if len(titulo) < 30:
            continue
        t = georef.norm(titulo)
        if not any(w in t for w in ["huaico", "deslizamiento", "derrumbe", "crecida",
                                    "inundacion", "bloque", "interrump", "transitab"]):
            continue
        tipo = ("HUAICO" if "huaico" in t else
                "DESLIZO" if "deslizamiento" in t or "derrumbe" in t else
                "CRECIDA" if "crecida" in t or "inundacion" in t else "BLOCKED")
        out.append({
            "tipo_evento": tipo,
            "estado": "INTERRUMPIDO" if ("bloque" in t or "interrump" in t) else "VERIFICANDO",
            "entidad": "INDECI", "titulo": titulo, "url_origen": a["href"],
            "fecha": _fecha(titulo), "departamento": _dep(titulo),
            "hash_contenido": hashlib.sha256(("INDECI|" + titulo + "|" + a["href"]).encode()).hexdigest(),
        })
    return out, V
