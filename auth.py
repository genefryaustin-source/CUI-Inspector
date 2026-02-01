
import streamlit as st
import hashlib, secrets
from datetime import datetime
from db import db, now_iso

def pbkdf2_hash(password: str, iters: int = 200_000) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iters)
    return f"pbkdf2_sha256${iters}${salt}${dk.hex()}"

def pbkdf2_verify(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, hexhash = stored.split("$", 3)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
        return dk.hex() == hexhash
    except Exception:
        return False

def current_user():
    return st.session_state.get("auth_user")

def require_login():
    return current_user() is not None

def audit(event_type, details=None):
    u = current_user()
    with db() as con:
        con.execute(
            "INSERT INTO audit_events (tenant_id, user_id, event_type, details_json, created_at) VALUES (?,?,?,?,?)",
            (
                st.session_state.get("tenant_id"),
                u["id"] if u else None,
                event_type,
                json.dumps(details or {}),
                now_iso(),
            ),
        )

def render_login():
    st.header("🔐 Sign in")
    with db() as con:
        cnt = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    if cnt == 0:
        st.warning("Bootstrap SuperAdmin")
        u = st.text_input("Username", "superadmin")
        p = st.text_input("Password", type="password")
        if st.button("Create SuperAdmin"):
            with db() as con:
                con.execute(
                    "INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,?,?)",
                    (u, pbkdf2_hash(p), "superadmin", now_iso()),
                )
            st.success("Created. Reload.")
        return

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Sign in"):
        with db() as con:
            r = con.execute(
                "SELECT id,username,password_hash,role,tenant_id FROM users WHERE username=? AND is_active=1",
                (u,),
            ).fetchone()
        if not r or not pbkdf2_verify(p, r[2]):
            st.error("Invalid credentials")
            return
        st.session_state["auth_user"] = {
            "id": r[0],
            "username": r[1],
            "role": r[3],
            "tenant_id": r[4],
        }
        st.session_state["tenant_id"] = r[4]
        st.success("Signed in")
        st.rerun()

def render_logout():
    if current_user():
        st.sidebar.markdown(f"**{current_user()['username']}**")
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()
