"""Orquestador ETL — Poder Lluvia Perú.
Uso: python run.py [--sources sutran_noticias,...]
Registra TODO en etl_runs (éxito/fallo/HTTP/nuevos), emite alertas operativas
(webhook opcional) y actualiza meta['ultima_actualizacion_ok']."""
import argparse, datetime as dt, sqlite3, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import config, fetch
import extract_sutran

CONNECTORS = {
    "sutran_noticias": lambda html: extract_sutran.extract_sutran(html),
    "coen_indeci":       lambda html: extract_sutran.extract_indeci(html),
}

def db():
    path = os.path.join(config.DATA_DIR, "poder_lluvia.db")
    con = sqlite3.connect(path)
    con.executescript(open(os.path.join(config.BASE_DIR, "schema.sql"), encoding="utf-8").read())
    return con, path

def log_run(con, fuente, url, ok, nuevos, error, status, vparser):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    con.execute("INSERT INTO etl_runs(started_at,finished_at,fuente,url,ok,registros_nuevos,error,http_status,version_parser) VALUES (?,?,?,?,?,?,?,?,?)",
                (now, now, fuente, url,
                 int(ok), nuevos, error, status, vparser))
    con.commit()

def alert(msg):
    print("[ALERTA]", msg)
    if config.ALERT_WEBHOOK_URL:
        try:
            import requests
            requests.post(config.ALERT_WEBHOOK_URL,
                          json={"text": f"PoderLluvia ETL: {msg}"}, timeout=15)
        except Exception as e:
            print("  webhook fallo:", e)

def ingest_events(con, rows):
    nuevos = 0
    for r in rows:
        cur = con.execute("""INSERT OR IGNORE INTO eventos_viales
            (fecha,via,carretera,kilometro,departamento,provincia,distrito,tipo_evento,estado,entidad,titulo,resumen,url_origen,hash_contenido)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r.get("date") or dt.date.today().isoformat(), r.get("via"), r.get("carretera"), r.get("kilometro"),
             r.get("departamento"), r.get("provincia"), r.get("distrito"), r["tipo_evento"], r["estado"],
             r["entidad"], r["titulo"], r.get("resumen"), r["url_origen"], r["hash_contenido"]))
        nuevos += cur.rowcount
    con.commit()
    return nuevos

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sources", default="")
    args = ap.parse_args()
    con, path = db()
    selected = [s for s in config.SOURCES if not args.sources or s in args.sources.split(",")]
    total_ok = total_fail = 0
    for name in selected:
        src = config.SOURCES[name]
        res = fetch.fetch(src["url"])
        if not res["ok"]:
            log_run(con, name, src["url"], False, 0, res["error"], res["status"], "-")
            alert(f"FALLO fuente '{name}': {res['error']}")
            total_fail += 1; continue
        connector = CONNECTORS.get(name)
        if not connector:   # fuentes aún sin extractor implementado: se registra la descarga, no se inventa nada
            log_run(con, name, src["url"], True, 0, "pendiente: extractor no implementado (sin datos inventados)", 200, "-")
            continue
        rows, vparser = connector(res["text"])
        nuevos = ingest_events(con, rows)
        log_run(con, name, src["url"], True, nuevos, None, 200, vparser)
        if len(rows) == 0:
            alert(f"SOSPECHA CAMBIO DE SITIO '{name}': HTTP 200 pero 0 registros (parser v{vparser}).")
        total_ok += 1
    con.execute("INSERT OR REPLACE INTO meta(clave,valor) VALUES ('ultima_ejecucion',?)",
                (dt.datetime.now().isoformat(),))
    if total_fail == 0:
        con.execute("INSERT OR REPLACE INTO meta(clave,valor) VALUES ('ultima_actualizacion_ok',?)",
                    (dt.datetime.now().isoformat(),))
    else:
        # borrar la marca "OK" anterior: así el vigía (alerta_stale) y Power BI
        # ven que HAY un fallo activo, no una fecha de éxito antigua.
        con.execute("DELETE FROM meta WHERE clave='ultima_actualizacion_ok'")
    con.commit(); con.close()
    print(json.dumps({"fuentes_ok": total_ok, "fuentes_fallidas": total_fail, "db": path}))
    sys.exit(0 if total_fail == 0 else 2)

if __name__ == "__main__":
    main()
