import json
import streamlit as st
from db import get_connection

def render_search_page():
    st.header("🔎 Search Inspections")

    con = get_connection()

    col1, col2, col3 = st.columns(3)
    with col1:
        filename_q = st.text_input("Filename contains", key="s_fn")
        sha_q = st.text_input("SHA-256 starts with", key="s_sha")

    with col2:
        ruleset = st.selectbox("Ruleset", ["(any)", "Basic", "DoD / GovCon"], key="s_rs")
        risk = st.selectbox("Risk Level", ["(any)", "LOW", "MEDIUM", "HIGH"], key="s_rl")

    with col3:
        min_score = st.slider("Min score", 0, 100, 0, key="s_min")
        max_score = st.slider("Max score", 0, 100, 100, key="s_max")

    where, params = [], []

    if filename_q:
        where.append("filename LIKE ?")
        params.append(f"%{filename_q}%")
    if sha_q:
        where.append("sha256 LIKE ?")
        params.append(f"{sha_q}%")
    if ruleset != "(any)":
        where.append("ruleset=?")
        params.append(ruleset)
    if risk != "(any)":
        where.append("risk_level=?")
        params.append(risk)

    where.append("risk_score BETWEEN ? AND ?")
    params.extend([min_score, max_score])

    sql = " AND ".join(where)

    rows = con.execute(f"""
        SELECT id, filename, ruleset, risk_level, risk_score, created_at
        FROM inspections
        WHERE {sql}
        ORDER BY created_at DESC
        LIMIT 300
    """, params).fetchall()

    st.caption(f"{len(rows)} result(s)")

    for r in rows:
        with st.expander(f"#{r['id']} • {r['filename']} • {r['risk_level']} ({r['risk_score']})"):
            art_rows = con.execute("""
                SELECT name, sha256, content FROM artifacts WHERE inspection_id=?
            """, (r["id"],)).fetchall()

            for a in art_rows:
                st.download_button(
                    f"⬇ {a['name']}",
                    data=a["content"],
                    file_name=a["name"],
                    key=f"s_dl_{r['id']}_{a['name']}"
                )

    con.close()
