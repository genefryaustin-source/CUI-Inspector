import csv
import io
import zipfile
from datetime import datetime

import streamlit as st

from db import get_connection


def _parse_iso(dt_str: str) -> datetime:
    # expects like 2026-02-02T12:34:56Z
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def _fetch_inspections(con, where_sql: str, params: list):
    return con.execute(f"""
        SELECT id, filename, sha256, ruleset, risk_level, risk_score, created_at
        FROM inspections
        WHERE {where_sql}
        ORDER BY created_at DESC
    """, params).fetchall()


def _fetch_artifacts(con, inspection_ids: list[int]):
    if not inspection_ids:
        return []
    placeholders = ",".join(["?"] * len(inspection_ids))
    return con.execute(f"""
        SELECT id, inspection_id, name, sha256, content, created_at
        FROM artifacts
        WHERE inspection_id IN ({placeholders})
        ORDER BY inspection_id DESC, name ASC
    """, inspection_ids).fetchall()


def _build_manifest_csv(inspections, artifacts) -> bytes:
    # Flatten artifacts by inspection_id
    arts_by_insp = {}
    for a in artifacts:
        arts_by_insp.setdefault(a["inspection_id"], []).append(a)

    out = io.StringIO()
    writer = csv.writer(out)

    # Header: inspection + artifact
    writer.writerow([
        "inspection_id",
        "inspection_created_at",
        "filename",
        "file_sha256",
        "ruleset",
        "risk_level",
        "risk_score",
        "artifact_id",
        "artifact_name",
        "artifact_sha256",
        "artifact_created_at",
        "artifact_bytes",
    ])

    for insp in inspections:
        insp_id = insp["id"]
        insp_arts = arts_by_insp.get(insp_id, [])

        if not insp_arts:
            # still emit a row for inspection (artifact fields empty)
            writer.writerow([
                insp_id,
                insp["created_at"],
                insp["filename"],
                insp["sha256"],
                insp["ruleset"],
                insp["risk_level"],
                insp["risk_score"],
                "",
                "",
                "",
                "",
                "",
            ])
        else:
            for a in insp_arts:
                bsize = len(a["content"]) if a["content"] is not None else 0
                writer.writerow([
                    insp_id,
                    insp["created_at"],
                    insp["filename"],
                    insp["sha256"],
                    insp["ruleset"],
                    insp["risk_level"],
                    insp["risk_score"],
                    a["id"],
                    a["name"],
                    a["sha256"],
                    a["created_at"],
                    bsize,
                ])

    return out.getvalue().encode("utf-8")


def _build_hashes_txt(inspections, artifacts) -> bytes:
    # Format compatible with common sha256sum style:
    # <sha256>  <path>
    lines = []

    # Add source file hashes (inspection file_sha256)
    for insp in inspections:
        path = f"source/{insp['filename']}"
        lines.append(f"{insp['sha256']}  {path}")

    # Add artifact hashes
    for a in artifacts:
        path = f"inspection_{a['inspection_id']}/{a['name']}"
        lines.append(f"{a['sha256']}  {path}")

    txt = "\n".join(lines) + "\n"
    return txt.encode("utf-8")


def _build_bundle_zip(manifest_csv: bytes, hashes_txt: bytes, artifacts, include_artifacts: bool) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.csv", manifest_csv)
        zf.writestr("hashes.sha256.txt", hashes_txt)

        if include_artifacts:
            for a in artifacts:
                # Put artifacts under inspection folder for tidy packaging
                arc_path = f"inspection_{a['inspection_id']}/{a['name']}"
                zf.writestr(arc_path, a["content"] if a["content"] is not None else b"")

    return buf.getvalue()


def render_manifest_export():
    st.header("📦 Evidence Export Manifest (FedRAMP / CMMC)")

    st.markdown(
        "Generate a **manifest.csv** and **hash list** for evidence delivery. "
        "Optionally bundle all selected artifacts into a single ZIP."
    )

    con = get_connection()

    # ---- Selection mode
    mode = st.radio(
        "Select inspections by…",
        ["Most recent N", "Filter by date range", "Pick specific IDs"],
        horizontal=True,
        key="m_mode"
    )

    where_sql = "1=1"
    params = []

    if mode == "Most recent N":
        n = st.number_input("N (most recent inspections)", min_value=1, max_value=2000, value=25, step=1, key="m_n")
        inspections = con.execute("""
            SELECT id, filename, sha256, ruleset, risk_level, risk_score, created_at
            FROM inspections
            ORDER BY created_at DESC
            LIMIT ?
        """, (int(n),)).fetchall()

    elif mode == "Filter by date range":
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Start date (UTC)", key="m_start")
        with c2:
            end = st.date_input("End date (UTC)", key="m_end")

        # Convert to ISO bounds in a simple way:
        # We store created_at as ISO strings; lexical comparison works for Z timestamps.
        start_iso = f"{start.isoformat()}T00:00:00"
        end_iso = f"{end.isoformat()}T23:59:59"

        where_sql = "created_at >= ? AND created_at <= ?"
        params = [start_iso, end_iso]
        inspections = _fetch_inspections(con, where_sql, params)

    else:  # Pick specific IDs
        ids_str = st.text_input("Inspection IDs (comma-separated)", value="", key="m_ids")
        ids = []
        for part in ids_str.split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))

        if not ids:
            st.info("Enter one or more inspection IDs (e.g., 12, 15, 18).")
            con.close()
            return

        placeholders = ",".join(["?"] * len(ids))
        inspections = con.execute(f"""
            SELECT id, filename, sha256, ruleset, risk_level, risk_score, created_at
            FROM inspections
            WHERE id IN ({placeholders})
            ORDER BY created_at DESC
        """, ids).fetchall()

    if not inspections:
        st.warning("No inspections found for this selection.")
        con.close()
        return

    st.caption(f"Selected inspections: **{len(inspections)}**")

    # ---- Options
    include_artifacts = st.checkbox("Include artifact contents in ZIP bundle", value=True, key="m_inc_art")
    include_source_note = st.checkbox("Include file hash lines for source filenames (informational)", value=True, key="m_inc_src")
    # (hash list always includes artifacts; include_source_note controls whether we include the source/filename lines)
    # We'll implement by filtering later.

    insp_ids = [int(r["id"]) for r in inspections]
    artifacts = _fetch_artifacts(con, insp_ids)

    st.caption(f"Artifacts found: **{len(artifacts)}**")

    # ---- Build outputs
    if st.button("✅ Generate Manifest Package", type="primary", key="m_gen"):
        manifest_csv = _build_manifest_csv(inspections, artifacts)

        hashes_txt = _build_hashes_txt(inspections, artifacts)
        if not include_source_note:
            # remove the source lines; keep only inspection_*/artifact lines
            lines = hashes_txt.decode("utf-8").splitlines()
            lines = [ln for ln in lines if not ln.endswith(tuple([f"source/{r['filename']}" for r in inspections]))]
            hashes_txt = ("\n".join(lines) + "\n").encode("utf-8")

        bundle_zip = _build_bundle_zip(manifest_csv, hashes_txt, artifacts, include_artifacts)

        st.success("Manifest package generated.")

        # Downloads (KEY-SAFE)
        st.download_button(
            "⬇ Download manifest.csv",
            data=manifest_csv,
            file_name="manifest.csv",
            key="m_dl_manifest"
        )
        st.download_button(
            "⬇ Download hashes.sha256.txt",
            data=hashes_txt,
            file_name="hashes.sha256.txt",
            key="m_dl_hashes"
        )
        st.download_button(
            "⬇ Download evidence_bundle.zip",
            data=bundle_zip,
            file_name="evidence_bundle.zip",
            key="m_dl_zip"
        )

        with st.expander("Preview (first 50 lines of hashes)"):
            st.code("\n".join(hashes_txt.decode("utf-8").splitlines()[:50]))

        with st.expander("Manifest preview (first 30 rows)"):
            # Show a small preview without pandas dependency
            text = manifest_csv.decode("utf-8").splitlines()
            st.code("\n".join(text[:31]))

    con.close()
