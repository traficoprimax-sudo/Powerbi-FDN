"""Pruebas unitarias del ETL — ejecutar: python tests/test_etl.py (o pytest tests/)
Cubre: parser de fechas, geocodificación conservadora, clasificación SUTRN/INDECI,
motor de criticidad, export CSV y vigía de datos antiguos. Sin red: todo con fixtures locales."""
import os, sys, sqlite3, tempfile, shutil, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ETL = os.path.join(HERE, "..", "etl")
sys.path.insert(0, ETL)

import extract_sutran, georef, criticidad, salida_csv, config  # noqa: E402

FIXTURE_SUTRAN = """
<html><body>
<a href="/institucion/sutran/noticias/12345-huaico-bloca-panamericana-norte-en-ancash">
SUTRN informa huaico bloquea la Panamericana Norte en Áncash, 15 de enero de 2026</a>
<a href="/institucion/sutran/noticias/999">Bienvenido al portal</a>
<a href="/institucion/sutran/noticias/77-caida-rocas-carretera-central">
SUTRN reporta caída de rocas en carretera Central km 88, restricción parcial</a>
</body></html>
"""

def test_fecha_textual():
    assert extract_sutran._fecha("15 de enero de 2026") == "2026-01-15"
    assert extract_sutran._fecha("3/setiembre/2025") == "2025-09-03"
    assert extract_sutran._fecha("sin fecha aqui") is None

def test_georef_exlicito_y_ruta():
    assert georef.infer_dep("Huaico en Áncash bloquea vía") == "Ancash"
    assert georef.infer_by_route("carretera Central km 88") in ("Lima", "Junin")
    assert georef.infer_dep("evento en el distrito X") is None  # no adivina

def test_extract_sutran_clasifica():
    rows, v = extract_sutran.extract_sutran(FIXTURE_SUTRAN)
    assert v == extract_sutran.V
    tipos = {r["tipo_evento"] for r in rows}
    assert "HUAICO" in tipos and "CAIDA_ROCAS" in tipos
    h = [r for r in rows if r["tipo_evento"] == "HUAICO"][0]
    assert h["departamento"] == "Ancash"
    assert h["estado"] == "INTERRUMPIDO"
    assert all(r["hash_contenido"] for r in rows)

def test_criticidad_motor():
    tmp = tempfile.mkdtemp()
    try:
        dbp = os.path.join(tmp, "poder_lluvia.db")
        con = sqlite3.connect(dbp)
        con.executescript(open(os.path.join(ETL, "schema.sql"), encoding="utf-8").read())
        hoy = dt.date.today().isoformat()
        con.execute("INSERT INTO precipitaciones(fecha,estacion,departamento,mm_dia,fuente) VALUES (?,?,?,?, 'MANUAL')",
                    (hoy, "SEN-047", "Ancash", 95.0))
        con.execute("""INSERT INTO eventos_viales(fecha,via,tipo_evento,estado,entidad,titulo,url_origen,hash_contenido,departamento)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (hoy, "PE-1N", "HUAICO", "INTERRUMPIDO", "SUTRN", "t", "u", "h1", "Ancash"))
        con.commit(); con.close()
        old = config.DATA_DIR
        config.DATA_DIR = tmp
        criticidad.main()
        config.DATA_DIR = old
        con = sqlite3.connect(dbp)
        row = con.execute("SELECT nivel,nombre_nivel FROM criticidad_ultima WHERE entidad_id='DEP:Ancash'").fetchone()
        assert row and row[0] == 5, row   # 95mm + huaico interrumpido => Extrema
        con.close()
    finally:
        shutil.rmtree(tmp)

def test_export_csv():
    tmp = tempfile.mkdtemp()
    try:
        dbp = os.path.join(tmp, "poder_lluvia.db")
        con = sqlite3.connect(dbp)
        con.executescript(open(os.path.join(ETL, "schema.sql"), encoding="utf-8").read())
        con.execute("INSERT INTO meta(clave,valor) VALUES ('k','v')"); con.commit(); con.close()
        old = config.DATA_DIR; config.DATA_DIR = tmp
        salida_csv.main()
        config.DATA_DIR = old
        assert os.path.exists(os.path.join(tmp, "export", "meta.csv"))
    finally:
        shutil.rmtree(tmp)

def test_alerta_stale():
    """Vigía: sin marca OK => STALE (exit 3); con marca reciente => OK (exit 0)."""
    import subprocess, tempfile as tf
    tmp = tf.mkdtemp()
    env = dict(os.environ, PLP_DATA=tmp)
    try:
        r = subprocess.run([sys.executable, os.path.join(ETL, "alerta_stale.py")],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 3 and "STALE" in r.stdout, (r.returncode, r.stdout)
        # crear DB con marca OK reciente
        dbp = os.path.join(tmp, "poder_lluvia.db")
        con = sqlite3.connect(dbp)
        con.executescript(open(os.path.join(ETL, "schema.sql"), encoding="utf-8").read())
        con.execute("INSERT INTO meta(clave,valor) VALUES ('ultima_actualizacion_ok',?)",
                    (dt.datetime.now().isoformat(),)); con.commit(); con.close()
        r = subprocess.run([sys.executable, os.path.join(ETL, "alerta_stale.py"), "--horas", "48"],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 0 and "OK" in r.stdout, (r.returncode, r.stdout)
        # marca vieja (100 h) => STALE
        con = sqlite3.connect(dbp)
        con.execute("UPDATE meta SET valor=? WHERE clave='ultima_actualizacion_ok'",
                    ((dt.datetime.now() - dt.timedelta(hours=100)).isoformat(),))
        con.commit(); con.close()
        r = subprocess.run([sys.executable, os.path.join(ETL, "alerta_stale.py"), "--horas", "48"],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 3, (r.returncode, r.stdout)
    finally:
        shutil.rmtree(tmp)

if __name__ == "__main__":
    fails = 0
    for name in sorted(k for k in globals() if k.startswith("test_")):
        fn = globals()[name]
        if callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except Exception as e:
                fails += 1; print(f"FAIL {name}: {e!r}")
    sys.exit(1 if fails else 0)
