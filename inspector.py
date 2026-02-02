import json, os, re
import streamlit as st
from db import db, init_db, now_iso
from repo import write_object
from auth import tenant_id, audit, current_user
from analysis.cui_inspector import CUIInspector

def _logical(fn): return re.sub(r"\s+"," ", os.path.basename(fn or "document")).strip().lower()

def _upsert_version(tid, filename, data, mime, uploaded_by):
    sha, rel, size = write_object(data)
    logical = _logical(filename)
    init_db()
    with db() as con:
        a = con.execute("SELECT id FROM artifacts WHERE tenant_id=? AND logical_name=?", (tid, logical)).fetchone()
        if a: aid=int(a["id"])
        else:
            con.execute("INSERT INTO artifacts (tenant_id,logical_name,created_at) VALUES (?,?,?)", (tid, logical, now_iso()))
            aid=int(con.execute("SELECT id FROM artifacts WHERE tenant_id=? AND logical_name=?", (tid, logical)).fetchone()["id"])
        last = con.execute("SELECT id,version_int,sha256 FROM artifact_versions WHERE tenant_id=? AND artifact_id=? ORDER BY version_int DESC LIMIT 1", (tid, aid)).fetchone()
        if last and last["sha256"]==sha:
            return int(last["id"])
        v = 1 if not last else int(last["version_int"])+1
        con.execute("INSERT INTO artifact_versions (tenant_id,artifact_id,version_int,original_filename,object_relpath,sha256,size_bytes,mime,created_at,uploaded_by) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (tid, aid, v, filename, rel, sha, size, mime, now_iso(), uploaded_by))
        con.commit()
        return int(con.execute("SELECT id FROM artifact_versions WHERE tenant_id=? AND artifact_id=? AND version_int=?", (tid, aid, v)).fetchone()["id"])

def _save_inspection(tid, av_id, run_type, findings, started, finished):
    with db() as con:
        con.execute("INSERT INTO inspections (tenant_id,artifact_version_id,run_type,started_at,finished_at,cui_detected,risk_level,patterns_json,categories_json,summary_json,error) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (tid, av_id, run_type, started, finished,
                     None if findings.get("cui_detected") is None else (1 if findings.get("cui_detected") else 0),
                     findings.get("risk_level"),
                     json.dumps(findings.get("patterns_found") or {}),
                     json.dumps(findings.get("cui_categories") or []),
                     json.dumps(findings),
                     findings.get("error")))
        ins_id = int(con.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
        con.commit()
        return ins_id

def _attach_evidence(tid, ins_id, kind, filename, data):
    sha, rel, size = write_object(data)
    with db() as con:
        con.execute("INSERT INTO evidence_files (tenant_id,inspection_id,kind,filename,object_relpath,sha256,size_bytes,created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (tid, ins_id, kind, filename, rel, sha, size, now_iso()))
        con.commit()

def _save_index(tid, ins_id, av_id, filename, text, findings, store_excerpt):
    excerpt = (text or "")[:1200] if store_excerpt else ""
    ext = filename.lower().rsplit(".",1)[-1] if "." in filename else ""
    try:
        patterns_total = int(sum((findings.get("patterns_found") or {}).values()))
    except Exception:
        patterns_total = 0
    with db() as con:
        con.execute("INSERT INTO inspection_text_index (tenant_id,inspection_id,artifact_version_id,filename,file_ext,safe_excerpt,char_count,word_count,patterns_total,categories_json,risk_level,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (tid, ins_id, av_id, filename, ext, excerpt, len(text or ""), len((text or "").split()), patterns_total,
                     json.dumps(findings.get('cui_categories') or []), findings.get('risk_level'), now_iso()))
        con.commit()

def render_cui_inspector():
    st.header("📄 CUI Document Inspector")
    tid = tenant_id()
    if tid is None:
        st.error("Select a tenant first."); return
    insp = CUIInspector()
    autosave = st.toggle("Auto-save evidence (JSON + PDF)", value=True)
    store_index = st.toggle("Enable search index", value=True)
    store_excerpt = st.toggle("Store safe excerpt", value=True, help="Turn off for metadata-only indexing")
    uploaded_by = st.text_input("Run by", value=(current_user() or {}).get("username",""))
    files = st.file_uploader("Upload documents", accept_multiple_files=True)
    manual = st.text_area("Or paste text (optional)", height=160)
    manual_name = st.text_input("Pasted text name", value="manual_input.txt")
    if st.button("🔍 Inspect", type="primary"):
        init_db()
        results=[]
        if files:
            for f in files:
                data = f.read()
                started = now_iso()
                findings = insp.inspect_file(f.name, data)
                finished = now_iso()
                av_id = _upsert_version(int(tid), f.name, data, getattr(f,'type',None) or "application/octet-stream", uploaded_by)
                ins_id = _save_inspection(int(tid), av_id, "file", findings, started, finished)
                if autosave:
                    _attach_evidence(int(tid), ins_id, "findings_json", f"findings_{ins_id}.json", json.dumps(findings, indent=2).encode("utf-8"))
                    try:
                        pdf = insp.generate_cui_report_pdf(findings)
                        _attach_evidence(int(tid), ins_id, "report_pdf", f"cui_report_{ins_id}.pdf", pdf)
                    except Exception:
                        pass
                if store_index:
                    text = insp.extract_text_from_file(f.name, data)
                    _save_index(int(tid), ins_id, av_id, f.name, text, findings, store_excerpt)
                audit("inspection_run", {"inspection_id": ins_id, "filename": f.name, "risk": findings.get("risk_level")})
                results.append((ins_id, findings))
        if manual:
            started=now_iso()
            findings = insp.inspect_text(manual, manual_name)
            finished=now_iso()
            ins_id = _save_inspection(int(tid), None, "manual", findings, started, finished)
            if autosave:
                _attach_evidence(int(tid), ins_id, "findings_json", f"findings_{ins_id}.json", json.dumps(findings, indent=2).encode("utf-8"))
                try:
                    pdf = insp.generate_cui_report_pdf(findings)
                    _attach_evidence(int(tid), ins_id, "report_pdf", f"cui_report_{ins_id}.pdf", pdf)
                except Exception:
                    pass
            if store_index:
                _save_index(int(tid), ins_id, None, manual_name, manual, findings, store_excerpt)
            audit("inspection_run", {"inspection_id": ins_id, "filename": manual_name, "risk": findings.get("risk_level")})
            results.append((ins_id, findings))
        if not results:
            st.warning("Nothing to inspect."); return
        st.success(f"Inspected {len(results)} item(s).")
        for ins_id, findings in results:
            with st.expander(f"Inspection #{ins_id}: {findings.get('filename')}", expanded=True):
                st.json(findings)
