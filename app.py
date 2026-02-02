import streamlit as st
from cui_inspector.ui import render_app

st.set_page_config(
    page_title="CUI Inspector – Multi-Tenant",
    layout="wide",
)

if __name__ == "__main__":
    render_app()


