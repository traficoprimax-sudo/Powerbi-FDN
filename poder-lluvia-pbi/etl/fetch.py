"""Capa de obtención: descarga HTML/CSV con reintentos y trazabilidad.
Nunca lanza excepción no controlada al pipeline: devuelve (ok, contenido, error)."""
import time, hashlib, requests, config

def fetch(url: str, retries=None):
    """GET con User-Agent real + backoff exponencial.
    Devuelve dict: {ok, status, text|bytes, sha256, error}"""
    retries = retries or config.MAX_RETRIES
    last_err, last_status = None, None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=config.HEADERS, timeout=config.TIMEOUT)
            last_status = r.status_code
            if r.status_code == 200 and r.text.strip():
                return {"ok": True, "status": 200, "text": r.text,
                        "sha256": hashlib.sha256(r.content).hexdigest(), "error": None}
            # 403/418/429/5xx = bloqueo WAF o caída: reintentar con espera
            last_err = f"HTTP {r.status_code} (intento {attempt}/{retries})"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e} (intento {attempt}/{retries})"
        time.sleep(config.RETRY_BACKOFF * (2 ** (attempt - 1)))
    return {"ok": False, "status": last_status, "text": None,
            "sha256": None, "error": last_err}
