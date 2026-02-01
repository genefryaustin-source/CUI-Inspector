# CUI Streamlit Portal — Fixed + Enhanced (Evidence Vault v2)

## What was fixed
- Corrected an indentation/syntax issue in the bulk runner that prevented the app from starting.

## New capabilities added
1) Evidence vault integrity verification (SHA-256 recomputation vs DB).
2) Full text/metadata search via `inspection_text_index` (stores redacted excerpt only).
3) Artifact diff (latest vs previous versions: hash/size + inspection deltas).
4) Role-based access with SQLite users table, login screen, admin user management, and audit log.

## Run
pip install -r requirements.txt
streamlit run app.py

## First run
If no users exist, the app will prompt you to create the first admin account.

## Storage
- SQLite: `data/evidence.db`
- Repo objects: `data/repo/objects/<xx>/<sha256>`
- Versioned refs: `data/repo/refs/artifact_<id>/v####/<filename>`
