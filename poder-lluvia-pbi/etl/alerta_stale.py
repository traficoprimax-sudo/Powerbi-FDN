"""Vigía de datos antiguos ("stale") — Poder Lluvia Perú.
Compara la hora local actual contra meta['ultima_actualizacion_ok'] y emite
alerta si hace más de N horas (default 48) que ninguna ejecución del ETL
terminó con TODAS las fuentes OK. Cubre el caso "el pipeline nunca se ejecutó"
(Task Scheduler desactivado, PC apagado, OneDrive pausado), que run.py por sí
solo no puede detectar.

Uso:  python alerta_stale.py [--horas 48]
Exit: 0 = datos frescos | 3 = datos STALE (alerta emitada)
Programar en Task Scheduler a una hora DISTINTA del ETL (ej. 09:00).
"""
import argparse, datetime as dt, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(__file__))
import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horas", type=float, default=48.0)
    args = ap.parse_args()

    dbp = os.path.join(config.DATA_DIR, "poder_lluvia.db")
    if not os.path.exists(dbp):
        msg = f"STALE: no existe {dbp} (¿pipeline nunca corrió?)"
        print("[ALERTA]", msg)
        _webhook(msg)
        sys.exit(3)

    con = sqlite3.connect(dbp)
    con.executescript(open(os.path.join(config.BASE_DIR, "schema.sql"),
                           encoding="utf-8").read())
    row = con.execute("SELECT valor FROM meta WHERE clave='ultima_actualizacion_ok'").fetchone()
    con.close()

    if not row:
        msg = "STALE: meta['ultima_actualizacion_ok'] vacío — ninguna ejecución completa OK todavía."
        print("[ALERTA]", msg)
        _webhook(msg)
        sys.exit(3)

    try:
        last = dt.datetime.fromisoformat(row[0])
    except ValueError:
        msg = f"STALE: fecha ilegible en meta: {row[0]!r}"
        print("[ALERTA]", msg)
        _webhook(msg)
        sys.exit(3)

    age_h = (dt.datetime.now() - last).total_seconds() / 3600.0
    if age_h > args.horas:
        msg = (f"STALE: última actualización OK hace {age_h:.1f} h "
               f"(umbral {args.horas:g} h). Revisar Task Scheduler/red/sitios.")
        print("[ALERTA]", msg)
        _webhook(msg)
        log = os.path.join(config.DATA_DIR, "alertas.log")
        try:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"{dt.datetime.now().isoformat()} {msg}\n")
        except OSError:
            pass
        sys.exit(3)

    print(f"OK: datos frescos ({age_h:.1f} h desde última actualización OK, umbral {args.horas:g} h)")
    sys.exit(0)


def _webhook(msg):
    if config.ALERT_WEBHOOK_URL:
        try:
            import requests
            requests.post(config.ALERT_WEBHOOK_URL,
                          json={"text": f"PoderLluvia vigía: {msg}"}, timeout=15)
        except Exception as e:
            print("  webhook fallo:", e)


if __name__ == "__main__":
    main()
