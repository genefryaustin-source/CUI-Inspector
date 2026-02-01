
import streamlit as st
from auth import render_login, require_login, render_logout
from tenants import render_tenant_admin
from evidence import render_manifest

def render_pages():
    if not require_login():
        render_login()
        return

    render_logout()
    page = st.sidebar.radio("Navigation", ["Evidence Manifest", "Tenants"])

    if page == "Evidence Manifest":
        render_manifest()
    elif page == "Tenants":
        render_tenant_admin()
