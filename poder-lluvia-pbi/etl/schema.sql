-- Esquema SQLite "capa dorada" — Poder Lluvia Perú (v1.1)

CREATE TABLE IF NOT EXISTS precipitaciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha DATE NOT NULL, estacion TEXT, departamento TEXT, provincia TEXT, distrito TEXT,
  mm_dia REAL, fuente TEXT NOT NULL, url_origen TEXT,
  fetched_at DATETIME DEFAULT (datetime('now')),
  UNIQUE(fecha, estacion, fuente)
);
CREATE TABLE IF NOT EXISTS precipitaciones_ejemplo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha DATE NOT NULL, estacion TEXT, departamento TEXT, provincia TEXT, distrito TEXT,
  mm_dia REAL, fuente TEXT NOT NULL, url_origen TEXT,
  UNIQUE(fecha, estacion, fuente)
);
CREATE TABLE IF NOT EXISTS eventos_viales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha DATE NOT NULL, via TEXT, carretera TEXT, kilometro TEXT,
  departamento TEXT, provincia TEXT, distrito TEXT,
  tipo_evento TEXT CHECK (tipo_evento IN ('HUAICO','DESLIZO','CAIDA_ROCAS','CRECIDA','BLOCKED','DANO_PUENTE','OTRO')),
  estado TEXT CHECK (estado IN ('INTERRUMPIDO','RESTRINGIDO','TRANSITABLE','VERIFICANDO')),
  entidad TEXT NOT NULL, titulo TEXT, resumen TEXT, url_origen TEXT,
  fetched_at DATETIME DEFAULT (datetime('now')), hash_contenido TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS umbral_criticidad (
  nivel INTEGER PRIMARY KEY CHECK (nivel BETWEEN 1 AND 5),
  nombre_nivel TEXT, score_min REAL, criterio_mm48h TEXT, criterio_evento TEXT, color_hex TEXT
);
CREATE TABLE IF NOT EXISTS criticidad_ultima (
  entidad_id TEXT PRIMARY KEY, nivel INTEGER NOT NULL CHECK (nivel BETWEEN 1 AND 5),
  nombre_nivel TEXT, score REAL, factor_principal TEXT,
  actualizado_en DATETIME DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS etl_runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at DATETIME, finished_at DATETIME, fuente TEXT, url TEXT,
  ok INTEGER, registros_nuevos INTEGER DEFAULT 0, error TEXT, http_status INTEGER, version_parser TEXT
);
CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT);
