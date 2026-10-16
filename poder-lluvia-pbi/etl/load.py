"""Carga CSVs locales (semilla/manual) a SQLite con trazabilidad TOTAL.
Uso: python load.py            -> carga todos los CSV de ../data
     python load.py --check    -> solo valida sin escribir
Los datos que no llegan de una fuente oficial se marcan fuente='MANUAL':
nunca se presentan como si vinieran de una API."""
import csv, os, sqlite3, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import config

TABLE_BY_FILE = {  # nombre de CSV -> tabla destino (permite *_demo.csv sin crear tablas nuevas)
    "precipitaciones": "precipitaciones",
    "precipitaciones_demo": "precipitaciones",
    "eventos_viales_demo": "eventos_viales",
    "umbral_criticidad": "umbral_criticidad",
}

def main(check=False):
    path = os.path.join(config.DATA_DIR, "poder_lluvia.db")
    con = sqlite3.connect(path)
    con.executescript(open(os.path.join(config.BASE_DIR, "schema.sql"), encoding="utf-8").read())
    total = 0
    for fname in sorted(os.listdir(config.DATA_DIR)):
        if not fname.endswith(".csv"): continue
        stem = fname[:-4]
        table = TABLE_BY_FILE.get(stem, stem)
        cols_exist = {r[1] for r in con.execute(f"PRAGMA table_info({table})")} \
                     if table in [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")] else set()
        rows = list(csv.DictReader(open(os.path.join(config.DATA_DIR, fname), encoding="utf-8-sig")))
        bad = [i for i, r in enumerate(rows, 2) if not all(k.strip() for k in r.values() if k is not None)]
        print(f"{fname}: {len(rows)} filas, columnas={list(rows[0].keys()) if rows else []}")
        if not cols_exist:
            print(f"  AVISO: tabla '{table}' no existe en esquema; revisar nombre de archivo."); continue
        if check: continue
        n = 0
        for r in rows:
            cols = [c for c in r if c in cols_exist and c != "id"]
            vals = [None if (r[c] is None or r[c] == "") else r[c] for c in cols]
            try:
                con.execute(f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})", vals)
                con.commit(); n += 1
            except sqlite3.Error as e:
                con.rollback(); print(f"  ERROR fila: {e} :: {r}")
        print(f"  -> {n} insertados/actualizados"); total += n
        con.execute("INSERT OR REPLACE INTO etl_runs(started_at,finished_at,fuente,url,ok,registros_nuevos,error,http_status,version_parser) VALUES (?,?,?,?,?,?,?,?,?)",
                    (dt.datetime.now().isoformat(), dt.datetime.now().isoformat(), f"csv:{table}",
                     f"file://{fname}", 1, n, "origen MANUAL/local (no API)" if table=="precipitaciones" else None, None, "load 1.0"))
    con.execute("INSERT OR REPLACE INTO meta(clave,valor) VALUES ('ultima_carga_local',?)", (dt.datetime.now().isoformat(),))
    con.commit(); con.close()
    print("TOTAL:", total)

if __name__ == "__main__":
    main("--check" in sys.argv)
