
import sqlite3
from pathlib import Path
from datetime import datetime

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "evidence_mt.db"

SCHEMA = '''
CREATE TABLE IF NOT EXISTS tenants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  username TEXT UNIQUE,
  password_hash TEXT,
  role TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  user_id INTEGER,
  event_type TEXT,
  details_json TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  logical_name TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS artifact_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id INTEGER,
  sha256 TEXT,
  object_path TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS inspections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  run_type TEXT,
  started_at TEXT,
  finished_at TEXT
);
CREATE TABLE IF NOT EXISTS evidence_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  inspection_id INTEGER,
  sha256 TEXT,
  object_path TEXT,
  created_at TEXT
);
'''

def now_iso():
    return datetime.utcnow().isoformat()

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.executescript(SCHEMA)

def db():
    init_db()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con
