import streamlit as st

from cui_inspector.db import init_db
from cui_inspector.auth import render_login, require_login, logout
from cui_inspector.tenants import ensure_active_tenant
from cui_inspector.permissions import is_read_only
from cui_inspector.audit_log import log_event

from cui_inspector.document_inspector import render_document_inspector
from cui_inspector.evidence_vault import render_evidence_vault
from cui_inspector.search import render_search_page
from cui_inspector.compare import render_compare_page
from cui_inspector.manifest import render_manifest_export


def render_sidebar(user):
    st.sidebar.markdown(
        f"""
        **User:** {user['email']}  
        **Role:** `{user['role']}`
        """
    )

    if st.sidebar.button("Logout", key="logout_btn"):
        logout()

    st.sidebar.divider()

    return st.sidebar.radio(
        "Navigation",
        [
            "Document Inspector",
            "Evidence Vault",
            "Search",
            "Compare",
            "Manifest Export",
        ],
        key="nav_radio",
    )


def render_app():
    init_db()

    if not require_login():
        render_login()
        return

    user = st.session_state.user
    ensure_active_tenant()

    page = render_sidebar(user)

    if is_read_only(user["role"]) and page == "Document Inspector":
        st.warning("🔍 Auditor access is read-only.")
        return

    if page == "Document Inspector":
        render_document_inspector()
        log_event(user, "document_inspection")

    elif page == "Evidence Vault":
        render_evidence_vault()

    elif page == "Search":
        render_search_page()

    elif page == "Compare":
        render_compare_page()

    elif page == "Manifest Export":
        render_manifest_export()
        log_event(user, "manifest_export")







