import sys
from pathlib import Path
import streamlit as st

# -------------------------------------------------
# Streamlit Cloud: ensure local modules resolve
# -------------------------------------------------
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui import render_app  # ← LOCAL import, not package

st.set_page_config(
    page_title="CUI Inspector – Multi-Tenant",
    layout="wide",
)

if __name__ == "__main__":
    render_app()


