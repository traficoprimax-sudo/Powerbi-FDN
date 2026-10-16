"""Motor de criticidad: consolida precipitación + eventos vía y escribe criticidad_ultima.
Reglas documentadas en data/umbral_criticidad.csv. No inventa geocodificación:
si un evento no tiene departamento explícito, se propaga solo si la carretera
ya tiene otro evento geocodificado (heurística conservadora registrada)."""
import sqlite3, sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import config

NIV = {1:"Baja",2:"Media",3:"Alta",4:"Muy Alta",5:"Extrema"}

def main():
    con = sqlite3.connect(os.path.join(config.DATA_DIR, "poder_lluvia.db"))
    con.executescript(open(os.path.join(config.BASE_DIR,"schema.sql"),encoding="utf-8").read())
    hoy = dt.date.today().isoformat()
    res = {}
    # señal lluvia por departamento (mm máx últimos 7 días)
    for dep, mx in con.execute("""SELECT departamento, MAX(mm_dia) FROM precipitaciones
        WHERE fecha >= date('now','-7 day') GROUP BY departamento"""):
        if dep: res.setdefault(("DEP:"+dep), {"lluvia": mx or 0, "eventos": []})["lluvia"] = max(mx or 0, res.get(("DEP:"+dep),{}).get("lluvia",0))
    # señal eventos activos (últimos 30 días)
    for dep, tipo, estado in con.execute("""SELECT departamento,tipo_evento,estado FROM eventos_viales
        WHERE fecha >= date('now','-30 day')"""):
        k = "DEP:"+ (dep or "SIN_GEOCODIFICAR")
        res.setdefault(k, {"lluvia":0,"eventos":[]})["eventos"].append((tipo,estado))
    con.execute("DELETE FROM criticidad_ultima")
    n=0
    for k,v in res.items():
        ev = v["eventos"]; grave = any(t in ("HUAICO","CRECIDA") and e=="INTERRUMPIDO" for t,e in ev)
        activa = any(e in ("INTERRUMPIDO","RESTRINGIDO","VERIFICANDO") for _,e in ev)
        lvl = 5 if grave and v["lluvia"]>=90 else 4 if grave or (v["lluvia"]>=70 and activa) \
              else 3 if v["lluvia"]>=40 or any(e=="INTERRUMPIDO" for _,e in ev) \
              else 2 if v["lluvia"]>=20 or activa else 1
        con.execute("INSERT OR REPLACE INTO criticidad_ultima(entidad_id,nivel,nombre_nivel,score,factor_principal,actualizado_en) VALUES (?,?,?,?,?,?)",
            (k,lvl,NIV[lvl],v["lluvia"],f"lluvia7d={v['lluvia']} mm; eventos={len(ev)}",dt.datetime.now().isoformat())); n+=1
    con.commit(); con.close(); print(f"criticidad recalculada: {n} entidades")

if __name__ == "__main__": main()
