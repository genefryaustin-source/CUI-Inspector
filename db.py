import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cui_inspector.db"

def get_connection():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        sha256 TEXT,
        ruleset TEXT,
        risk_level TEXT,
        risk_score INTEGER,
        analysis_json TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id INTEGER,
        name TEXT,
        sha256 TEXT,
        content BLOB,
        created_at TEXT,
        FOREIGN KEY (inspection_id) REFERENCES inspections(id)
    )
    """)

    # 🔎 Indexes for Step 7
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insp_created ON inspections(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insp_filename ON inspections(filename)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insp_sha256 ON inspections(sha256)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insp_ruleset ON inspections(ruleset)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insp_risk ON inspections(risk_level)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_art_inspection ON artifacts(inspection_id)")

    con.commit()
    con.close()


