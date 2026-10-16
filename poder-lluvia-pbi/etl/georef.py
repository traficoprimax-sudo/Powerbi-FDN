"""Referencia geográfica estática de carreteras peruanas (fuente: Red Vial Nacional, MTC).
NO es una API: es una tabla de conocimiento verificable, usada solo para PROPAGAR
departamento cuando un evento oficial no lo trae explícito. Si la carretera no está
en esta lista, el evento queda 'SIN_GEOCODIFICAR' (nunca se adivina).
formato: (via_pattern, departamento)  — pattern se busca en texto normalizado (minúsculas, sin acentos)
"""
import unicodedata

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.lower()

# Fuente documental: "Relación de rutas de la Red Vial Nacional" (MTC / gob.pe/institucion/mtc).
# Lista práctica: (carretera, departamento) — conservadora, solo tramos ampliamente conocidos.
ROUTES = [
    ("PE-1N", "Piura"), ("PE-1N", "Lambayeque"), ("PE-1N", "La Libertad"),
    ("PE-1N", "Ancash"), ("PE-1N", "Lima"), ("PE-1N", "Ica"),
    ("PE-1S", "Arequipa"), ("PE-1S", "Moquegua"), ("PE-1S", "Tacna"),
    ("PE-22", "Tumbes"),
    ("PE-3N", "Amazonas"), ("PE-3N", "Cajamarca"), ("PE-3N", "La Libertad"),
    ("PE-3N", "Lambayeque"), ("PE-3N", "Piura"), ("PE-3E", "San Martin"),
    ("PE-4N", "Loreto"), ("PE-4N", "Ucayali"), ("PE-4S", "Huanuco"),
    ("PE-5S", "Junin"), ("PE-5S", "Huancavelica"), ("PE-5S", "Ayacucho"),
    ("PE-5S", "Arequipa"), ("PE-5Z", "Puno"), ("PE-5Z", "Cusco"),
    ("PE-6N", "Cajamarca"), ("PE-6S", "Apurimac"), ("PE-6S", "Cusco"),
    ("PE-7S", "Puno"),
    # Corredores históricos con nombre propio (aparecen en noticias SUTRN/Policia Vial):
    ("central", "Lima"), ("carretera central", "Junin"),
    ("norte-sur", "Ancash"),
    ("panamericana norte", "Ancash"), ("panamericana sur", "Ica"),
]

DEPARTAMENTOS = [
    "Amazonas","Ancash","Apurimac","Arequipa","Ayacucho","Cajamarca","Callao",
    "Cusco","Huancavelica","Huanuco","Ica","Junin","La Libertad","Lambayeque",
    "Lima","Loreto","Madre de Dios","Moquegua","Pasco","Piura","Puno",
    "San Martin","Tacna","Tumbes","Ucayali",
]

def infer_dep(texto: str):
    """Devuelve el primer departamento mencionado explícitamente en el texto, o None."""
    t = norm(texto)
    for d in DEPARTAMENTOS:
        if norm(d) in t:
            return d
    return None

def infer_by_route(texto: str):
    """Devuelve departamento por patrón de carretera conocido, o None (sin adivinar)."""
    t = norm(texto)
    for pat, dep in ROUTES:
        if norm(pat) in t:
            return dep
    return None
