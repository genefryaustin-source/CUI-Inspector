import pandas as pd
import streamlit as st
from db import db
from auth import tenant_id, audit
from repo import read_object, verify_object

def render_evidence_vault():
    st.header("🗄️ Evidence Vault")
    tid = tenant_id()
    if tid is None:
        st.error("Select a tenant in the sidebar first.")
        return

    limit = st.slider("Show latest N inspections", 25, 500, 200, step=25)
    with db() as con:
        rows = con.execute(
            "SELECT i.id, i.started_at, i.finished_at, i.risk_level, i.cui_detected, av.original_filename, av.version_int, av.sha256 AS artifact_sha "
            "FROM inspections i LEFT JOIN artifact_versions av ON av.id=i.artifact_version_id "
            "WHERE i.tenant_id=? ORDER BY i.started_at DESC LIMIT ?",
            (tid, limit),
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df, use_container_width=True)
    if df.empty:
        return

    selected = st.selectbox("Inspection ID", options=df["id"].tolist())
    with db() as con:
        files = con.execute(
            "SELECT id, kind, filename, sha256, size_bytes, object_relpath, created_at "
            "FROM evidence_files WHERE tenant_id=? AND inspection_id=? ORDER BY created_at DESC",
            (tid, int(selected)),
        ).fetchall()

    st.subheader("Evidence files")
    df2 = pd.DataFrame([dict(r) for r in files])
    st.dataframe(df2, use_container_width=True)

    if not df2.empty:
        row_id = st.selectbox("Evidence file row", options=df2["id"].tolist())
        rec = next((r for r in files if int(r["id"]) == int(row_id)), None)
        if rec:
            data = read_object(rec["object_relpath"])
            st.download_button("⬇️ Download selected evidence", data=data, file_name=rec["filename"], mime="application/octet-stream")

def render_verify_evidence_vault():
    st.header("✅ Verify Evidence Integrity")
    tid = tenant_id()
    if tid is None:
        st.error("Select a tenant in the sidebar first.")
        return

    st.caption("Recomputes SHA-256 for stored objects and compares to database records.")
    if st.button("Run integrity verification", type="primary"):
        problems = []
        checked = 0
        with db() as con:
            av_rows = con.execute("SELECT id, sha256, object_relpath, original_filename FROM artifact_versions WHERE tenant_id=?", (tid,)).fetchall()
            ef_rows = con.execute("SELECT id, sha256, object_relpath, filename, kind FROM evidence_files WHERE tenant_id=?", (tid,)).fetchall()

        for r in av_rows:
            ok, actual = verify_object(r["object_relpath"], r["sha256"])
            checked += 1
            if not ok:
                problems.append({"table": "artifact_versions", "row_id": int(r["id"]), "name": r["original_filename"], "expected": r["sha256"], "actual": actual})

        for r in ef_rows:
            ok, actual = verify_object(r["object_relpath"], r["sha256"])
            checked += 1
            if not ok:
                problems.append({"table": "evidence_files", "row_id": int(r["id"]), "name": r["filename"], "expected": r["sha256"], "actual": actual})

        audit("verify_vault", {"checked": checked, "problems": len(problems)})

        st.write(f"Checked {checked} objects.")
        if problems:
            st.error(f"Integrity check FAILED for {len(problems)} object(s).")
            st.dataframe(problems, use_container_width=True)
        else:
            st.success("Integrity check PASSED (all hashes match).")
