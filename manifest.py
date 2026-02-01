import io
import zipfile
import pandas as pd
import streamlit as st
from db import db
from auth import tenant_id, audit
from repo import read_object

def render_manifest_export():
    st.header("📦 Evidence Export Manifest (FedRAMP / CMMC)")
    tid = tenant_id()
    if tid is None:
        st.error("Select a tenant in the sidebar first.")
        return

    include_objects = st.toggle("Include evidence objects in ZIP (can be large)", value=False)

    if st.button("Generate manifest ZIP", type="primary"):
        with db() as con:
            rows = con.execute(
                """
                SELECT a.logical_name,
                       av.version_int,
                       av.original_filename,
                       av.sha256 AS artifact_sha256,
                       av.size_bytes AS artifact_size_bytes,
                       av.object_relpath AS artifact_object_relpath,
                       i.id AS inspection_id,
                       i.started_at,
                       i.finished_at,
                       i.risk_level,
                       ef.kind AS evidence_kind,
                       ef.filename AS evidence_filename,
                       ef.sha256 AS evidence_sha256,
                       ef.size_bytes AS evidence_size_bytes,
                       ef.object_relpath AS evidence_object_relpath
                FROM artifacts a
                LEFT JOIN artifact_versions av ON av.artifact_id=a.id AND av.tenant_id=a.tenant_id
                LEFT JOIN inspections i ON i.artifact_version_id=av.id AND i.tenant_id=a.tenant_id
                LEFT JOIN evidence_files ef ON ef.inspection_id=i.id AND ef.tenant_id=a.tenant_id
                WHERE a.tenant_id=?
                ORDER BY a.logical_name, av.version_int DESC, i.started_at DESC
                """,
                (tid,),
            ).fetchall()

        df = pd.DataFrame([dict(r) for r in rows])
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        hash_lines = []
        for _, r in df.iterrows():
            if isinstance(r.get("artifact_sha256"), str):
                hash_lines.append(f"{r['artifact_sha256']}  {r.get('original_filename','')}")
            if isinstance(r.get("evidence_sha256"), str):
                hash_lines.append(f"{r['evidence_sha256']}  {r.get('evidence_filename','')}")
        hashes_txt = ("\n".join(hash_lines) + "\n").encode("utf-8")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.csv", csv_bytes)
            z.writestr("hashes.sha256.txt", hashes_txt)
            if include_objects:
                rels = set(df["artifact_object_relpath"].dropna().tolist() + df["evidence_object_relpath"].dropna().tolist())
                for rel in rels:
                    try:
                        z.writestr(f"repo/{rel}", read_object(rel))
                    except Exception:
                        pass

        buf.seek(0)
        audit("export_manifest", {"tenant_id": int(tid), "rows": int(len(df))})
        st.download_button(
            "⬇️ Download manifest ZIP",
            data=buf.read(),
            file_name=f"evidence_manifest_tenant_{tid}.zip",
            mime="application/zip",
        )
