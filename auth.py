import json, hashlib
import streamlit as st
from db import db, init_db, now_iso

ROLES = ["superadmin","tenant_admin","analyst","viewer","auditor"]

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def current_user():
    return st.session_state.get("user")

def tenant_id():
    return st.session_state.get("tenant_id")

def role():
    return (current_user() or {}).get("role")

def is_superadmin(): return role() == "superadmin"
def is_tenant_admin(): return role() == "tenant_admin"
def is_auditor(): return role() == "auditor"

def audit(event_type: str, payload=None):
    init_db()
    u = current_user() or {}
    with db() as con:
        con.execute(
            "INSERT INTO audit_events (tenant_id,user_id,event_type,event_json,created_at) VALUES (?,?,?,?,?)",
            (tenant_id(), u.get("id"), event_type, json.dumps(payload or {}), now_iso()),
        )
        con.commit()

def _ensure_bootstrap_admin():
    init_db()
    with db() as con:
        n = con.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if int(n) > 0:
            return
        con.execute("INSERT OR IGNORE INTO tenants (name,is_active,created_at) VALUES (?,?,?)", ("Default",1,now_iso()))
        su_user = st.secrets.get("SUPERADMIN_USERNAME", "superadmin")
        su_pw = st.secrets.get("SUPERADMIN_PASSWORD", "ChangeMeNow!123")
        con.execute(
            "INSERT INTO users (tenant_id,username,password_hash,role,is_active,created_at,last_login_at) VALUES (?,?,?,?,?,?,?)",
            (None, su_user, _hash_pw(su_pw), "superadmin", 1, now_iso(), None),
        )
        con.commit()

def require_login():
    if st.session_state.get("user"):
        return True
    _ensure_bootstrap_admin()
    st.header("🔐 Sign in")
    with st.form("login"):
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary")
    if not ok:
        return False
    with db() as con:
        r = con.execute("SELECT * FROM users WHERE username=? AND is_active=1", (u,)).fetchone()
        if (not r) or r["password_hash"] != _hash_pw(p):
            st.error("Invalid credentials"); return False
        st.session_state["user"] = dict(r)
        st.session_state["tenant_id"] = r["tenant_id"] if r["role"] in ("tenant_admin","analyst","viewer") else None
        con.execute("UPDATE users SET last_login_at=? WHERE id=?", (now_iso(), int(r["id"])))
        con.commit()
    audit("login", {"username": u})
    st.rerun()

def render_logout_sidebar():
    st.sidebar.markdown("---")
    u = current_user()
    if u:
        st.sidebar.caption(f"Signed in as **{u.get('username')}** ({u.get('role')})")
    if st.sidebar.button("Log out"):
        st.session_state.pop("user", None)
        st.session_state.pop("tenant_id", None)
        st.rerun()
