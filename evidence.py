
import streamlit as st
import hashlib, os
from db import db, now_iso

REPO = "data/repo"
os.makedirs(REPO, exist_ok=True)

def store_object(data: bytes) -> str:
    sha = hashlib.sha256(data).hexdigest()
    path = os.path.join(REPO, sha)
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(data)
    return sha

def render_manifest():
    st.header("📦 Evidence Manifest")
    with db() as con:
        rows = con.execute(
            "SELECT a.logical_name, av.sha256 AS artifact_hash, ef.sha256 AS evidence_hash "
            "FROM artifacts a "
            "LEFT JOIN artifact_versions av ON av.artifact_id=a.id "
            "LEFT JOIN evidence_files ef ON ef.inspection_id=av.id"
        ).fetchall()
    csv = "logical_name,artifact_hash,evidence_hash\n"
    for r in rows:
        csv += f"{r['logical_name']},{r['artifact_hash']},{r['evidence_hash']}\n"
    st.download_button("Download manifest.csv", csv.encode(), "manifest.csv")
