"""Exporta las tablas del SQLite a CSVs en data/export/ para Power BI Desktop.
Razones: (1) PBI gratuito + puerta de aplicación no soporta ODBC local;
(2) los CSV viajan por OneDrive y el gateway solo necesita un equipo encendido
para la actualización programada; (3) son el respaldo histórico consultable."""
import sqlite3, csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import config

TABLES = ["precipitaciones","precipitaciones_ejemplo","eventos_viales",
          "umbral_criticidad","criticidad_ultima","etl_runs","meta"]

def main():
    out = os.path.join(config.DATA_DIR, "export"); os.makedirs(out, exist_ok=True)
    con = sqlite3.connect(os.path.join(config.DATA_DIR, "poder_lluvia.db"))
    for t in TABLES:
        cur = con.execute(f"SELECT * FROM {t}")
        cols = [d[0] for d in cur.description]
        with open(os.path.join(out, f"{t}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(cur.fetchall())
        print("export:", t)
    con.close()

if __name__ == "__main__": main()
