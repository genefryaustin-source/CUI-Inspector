import streamlit as st
from db import db, init_db, now_iso
from auth import is_superadmin, is_auditor, tenant_id, audit

def render_tenant_selector_sidebar():
    init_db()
    if tenant_id() is None and not (is_superadmin() or is_auditor()):
        return
    with db() as con:
        tenants = con.execute("SELECT id,name FROM tenants WHERE is_active=1 ORDER BY name").fetchall()
    if not tenants:
        with db() as con:
            con.execute("INSERT INTO tenants (name,is_active,created_at) VALUES (?,?,?)", ("Default",1,now_iso()))
            con.commit()
        with db() as con:
            tenants = con.execute("SELECT id,name FROM tenants WHERE is_active=1 ORDER BY name").fetchall()
    opts = {f"{t['name']} (#{t['id']})": int(t["id"]) for t in tenants}
    labels = list(opts.keys())
    idx = 0
    cur = st.session_state.get("tenant_id")
    if cur:
        for i,l in enumerate(labels):
            if opts[l] == int(cur): idx=i; break
    st.sidebar.markdown("### Tenant")
    pick = st.sidebar.selectbox("Tenant", labels, index=idx)
    st.session_state["tenant_id"] = opts[pick]

def render_superadmin_tenant_management():
    st.header("🛡️ Tenant Management (SuperAdmin)")
    if not is_superadmin():
        st.error("SuperAdmin only."); return
    init_db()
    with db() as con:
        t = con.execute("SELECT * FROM tenants ORDER BY id").fetchall()
    st.dataframe([dict(r) for r in t], use_container_width=True)
    name = st.text_input("New tenant name").strip()
    if st.button("Create tenant", type="primary"):
        if not name:
            st.error("Name required."); return
        with db() as con:
            con.execute("INSERT OR IGNORE INTO tenants (name,is_active,created_at) VALUES (?,?,?)", (name,1,now_iso()))
            con.commit()
        audit("tenant_created", {"name": name})
        st.rerun()
