import streamlit as st, hashlib
from db import db, init_db, now_iso
from auth import is_superadmin, role, tenant_id, audit, ROLES

def render_user_management():
    st.header("👥 User Management")
    init_db()
    if role() not in ("superadmin","tenant_admin"):
        st.error("Admin only."); return
    tid = tenant_id()
    with db() as con:
        if role() == "superadmin":
            rows = con.execute("SELECT id,tenant_id,username,role,is_active,created_at,last_login_at FROM users ORDER BY id").fetchall()
        else:
            rows = con.execute("SELECT id,tenant_id,username,role,is_active,created_at,last_login_at FROM users WHERE tenant_id=? ORDER BY id", (tid,)).fetchall()
    st.dataframe([dict(r) for r in rows], use_container_width=True)
    st.subheader("Create user")
    u = st.text_input("Username").strip()
    p = st.text_input("Temp password", type="password")
    role_choices = ["tenant_admin","analyst","viewer"] if role()!="superadmin" else ROLES
    r = st.selectbox("Role", role_choices)
    assign_tid = tid
    if role()=="superadmin":
        assign_tid_raw = st.number_input("Tenant ID (0 for none)", min_value=0, value=int(tid or 0), step=1)
        assign_tid = None if int(assign_tid_raw)==0 else int(assign_tid_raw)
    if st.button("Create user", type="primary"):
        if not u or not p:
            st.error("Username and password required."); return
        ph = hashlib.sha256(p.encode("utf-8")).hexdigest()
        with db() as con:
            con.execute("INSERT OR IGNORE INTO users (tenant_id,username,password_hash,role,is_active,created_at,last_login_at) VALUES (?,?,?,?,?,?,?)",
                        (assign_tid, u, ph, r, 1, now_iso(), None))
            con.commit()
        audit("user_created", {"username": u, "role": r, "tenant_id": assign_tid})
        st.success("User created."); st.rerun()
