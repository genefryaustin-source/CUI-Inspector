import json
import streamlit as st
from db import get_connection

def render_compare_page():
    st.header("🆚 Compare Inspections")

    con = get_connection()
    rows = con.execute("""
        SELECT id, filename, risk_level, risk_score, created_at
        FROM inspections
        ORDER BY created_at DESC
        LIMIT 200
    """).fetchall()

    if len(rows) < 2:
        st.info("At least two inspections required.")
        return

    labels = {
        f"#{r['id']} • {r['filename']} • {r['risk_level']}({r['risk_score']})": r["id"]
        for r in rows
    }

    left = st.selectbox("Left", list(labels.keys()), key="cmp_l")
    right = st.selectbox("Right", list(labels.keys()), key="cmp_r")

    if labels[left] == labels[right]:
        st.warning("Select two different inspections.")
        return

    def load(i):
        row = con.execute("SELECT * FROM inspections WHERE id=?", (i,)).fetchone()
        analysis = json.loads(row["analysis_json"])
        arts = con.execute("SELECT name, sha256 FROM artifacts WHERE inspection_id=?", (i,)).fetchall()
        return row, analysis, arts

    Lr, La, Larts = load(labels[left])
    Rr, Ra, Rarts = load(labels[right])

    st.subheader("Risk Delta")
    st.metric("Score", f"{Lr['risk_score']} → {Rr['risk_score']}")
    st.metric("Level", f"{Lr['risk_level']} → {Rr['risk_level']}")

    st.divider()
    st.subheader("Analysis Diff")

    for k in ["cui_detected", "cui_categories", "patterns_found"]:
        if La.get(k) != Ra.get(k):
            st.write(f"**{k}**")
            st.code(f"LEFT: {La.get(k)}\nRIGHT: {Ra.get(k)}")

    st.divider()
    st.subheader("Artifact Hash Comparison")

    lmap = {a["name"]: a["sha256"] for a in Larts}
    rmap = {a["name"]: a["sha256"] for a in Rarts}

    for name in sorted(set(lmap) | set(rmap)):
        st.write(
            f"{name}: "
            f"{'MATCH' if lmap.get(name)==rmap.get(name) else 'DIFFERENT'}"
        )

    con.close()
