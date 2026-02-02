import sqlite3
from pathlib import Path

DB_PATH = Path("cui_inspector.db")

def get_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()

    con.executescript("""
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        tenant_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        last_login_at TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        role TEXT,
        tenant_id INTEGER,
        action TEXT,
        target TEXT,
        timestamp TEXT
    );
    """)

    con.commit()
