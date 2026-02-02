import streamlit as st
from db import get_db
from utils import now_iso, verify_password

def render_login():
    st.title("🔐 CUI Inspector Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", type="primary"):
        if login(email, password):
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

def login(email, password):
    con = get_db()
    row = con.execute(
        "SELECT * FROM users WHERE email=? AND is_active=1",
        (email,)
    ).fetchone()

    if not row or not verify_password(password, row["password_hash"]):
        return False

    st.session_state.user = {
        "email": row["email"],
        "role": row["role"],
        "tenant_id": row["tenant_id"],
        "user_id": row["id"],
    }

    con.execute(
        "UPDATE users SET last_login_at=? WHERE id=?",
        (now_iso(), row["id"]),
    )
    con.commit()
    return True

def require_login():
    return "user" in st.session_state

def logout():
    st.session_state.clear()
    st.rerun()


