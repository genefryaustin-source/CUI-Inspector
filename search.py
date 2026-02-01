import pandas as pd
import streamlit as st
from db import db
from auth import tenant_id, audit

def render_search():
    st.header("🔎 Search (Safe Excerpts + Metadata)")
    tid = tenant_id()
    if tid is None:
        st.error("Select a tenant in the sidebar first.")
        return

    q = st.text_input("Search query (filename or excerpt contains)", value="").strip()
    risk = st.selectbox("Risk filter", ["(any)", "NONE", "LOW", "MODERATE", "HIGH"])
    limit = st.slider("Max results", 25, 500, 100, step=25)

    if not q and risk == "(any)":
        st.info("Enter a search query and/or select a risk filter.")
        return

    like = f"%{q}%"
    with db() as con:
        if q and risk != "(any)":
            rows = con.execute(
                "SELECT inspection_id, filename, file_ext, risk_level, patterns_total, created_at, safe_excerpt "
                "FROM inspection_text_index WHERE tenant_id=? AND (filename LIKE ? OR safe_excerpt LIKE ?) AND risk_level=? "
                "ORDER BY created_at DESC LIMIT ?",
                (tid, like, like, risk, limit),
            ).fetchall()
        elif q:
            rows = con.execute(
                "SELECT inspection_id, filename, file_ext, risk_level, patterns_total, created_at, safe_excerpt "
                "FROM inspection_text_index WHERE tenant_id=? AND (filename LIKE ? OR safe_excerpt LIKE ?) "
                "ORDER BY created_at DESC LIMIT ?",
                (tid, like, like, limit),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT inspection_id, filename, file_ext, risk_level, patterns_total, created_at, safe_excerpt "
                "FROM inspection_text_index WHERE tenant_id=? AND risk_level=? ORDER BY created_at DESC LIMIT ?",
                (tid, risk, limit),
            ).fetchall()

    df = pd.DataFrame([dict(r) for r in rows])
    audit("search", {"q": q, "risk": risk, "results": int(len(df))})
    st.dataframe(df, use_container_width=True)
