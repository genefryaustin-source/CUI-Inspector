CREATE TABLE IF NOT EXISTS tenants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  logical_name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, logical_name),
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifact_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  artifact_id INTEGER NOT NULL,
  version_int INTEGER NOT NULL,
  original_filename TEXT NOT NULL,
  object_relpath TEXT NOT NULL,
  ref_relpath TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  mime TEXT,
  created_at TEXT NOT NULL,
  uploaded_by TEXT,
  UNIQUE(artifact_id, version_int),
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  FOREIGN KEY(artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inspections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  artifact_version_id INTEGER,
  run_type TEXT NOT NULL,               -- single|bulk|qa|training|verify|export
  app_version TEXT NOT NULL,
  inspector_version TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  cui_detected INTEGER,
  risk_level TEXT,
  patterns_json TEXT,
  categories_json TEXT,
  summary_json TEXT,
  error TEXT,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  FOREIGN KEY(artifact_version_id) REFERENCES artifact_versions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS evidence_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  inspection_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  object_relpath TEXT NOT NULL,
  filename TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,                    -- NULL for superadmin/auditor (cross-tenant)
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer',   -- superadmin|tenant_admin|auditor|analyst|viewer
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  last_login_at TEXT,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  user_id INTEGER,
  event_type TEXT NOT NULL,
  details_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);

CREATE TABLE IF NOT EXISTS inspection_text_index (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  inspection_id INTEGER NOT NULL,
  artifact_version_id INTEGER,
  filename TEXT,
  file_ext TEXT,
  safe_excerpt TEXT,
  char_count INTEGER,
  word_count INTEGER,
  patterns_total INTEGER,
  categories_json TEXT,
  risk_level TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE,
  FOREIGN KEY(artifact_version_id) REFERENCES artifact_versions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_text_index_risk ON inspection_text_index(risk_level);
CREATE INDEX IF NOT EXISTS idx_text_index_filename ON inspection_text_index(filename);

CREATE INDEX IF NOT EXISTS idx_inspections_started_at ON inspections(started_at);
CREATE INDEX IF NOT EXISTS idx_artifact_versions_sha256 ON artifact_versions(sha256);
CREATE INDEX IF NOT EXISTS idx_evidence_files_sha256 ON evidence_files(sha256);
