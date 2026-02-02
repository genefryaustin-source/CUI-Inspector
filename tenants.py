import streamlit as st
from db import get_db
from permissions import can_view_all_tenants

def ensure_active_tenant():
    user = st.session_state.user

    if can_view_all_tenants(user["role"]):
        con = get_db()
        tenants = con.execute(
            "SELECT id, name FROM tenants WHERE is_active=1 ORDER BY name"
        ).fetchall()

        if not tenants:
            st.error("No active tenants exist")
            st.stop()

        selected = st.sidebar.selectbox(
            "Tenant",
            tenants,
            format_func=lambda t: t["name"],
            key="tenant_select",
        )
        st.session_state.active_tenant = selected["id"]
    else:
        st.session_state.active_tenant = user["tenant_id"]

