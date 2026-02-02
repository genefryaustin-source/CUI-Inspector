import json
import pandas as pd
import streamlit as st
from db import db, init_db
from auth import tenant_id, audit

def render_search():
    st.header("🔎 Search")
    tid = tenant_id()
    if tid is None: st.error("Select a tenant first."); return
    init_db()
    q = st.text_input("Query (filename/excerpt contains)", "").strip()
    risk = st.selectbox("Risk filter", ["(any)","LOW","MEDIUM","HIGH"], index=0)
    clauses=["tenant_id=?"]; params=[tid]
    if risk!="(any)":
        clauses.append("risk_level=?"); params.append(risk)
    if q:
        like=f"%{q}%"
        clauses.append("(filename LIKE ? OR safe_excerpt LIKE ?)"); params.extend([like, like])
    where=" AND ".join(clauses)
    with db() as con:
        rows = con.execute(f"SELECT inspection_id,filename,risk_level,patterns_total,created_at,safe_excerpt,categories_json FROM inspection_text_index WHERE {where} ORDER BY created_at DESC LIMIT 400", tuple(params)).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if not df.empty:
        df["categories"] = df["categories_json"].apply(lambda x: ", ".join(json.loads(x or "[]")) if isinstance(x,str) else "")
        df = df.drop(columns=["categories_json"])
    audit("search", {"q": q, "risk": risk, "results": int(len(df))})
    st.dataframe(df, use_container_width=True)
