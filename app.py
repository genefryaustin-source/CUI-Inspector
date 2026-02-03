import sys
from pathlib import Path
import streamlit as st

# -------------------------------------------------
# Add PROJECT ROOT (parent of cui-inspector)
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui import render_app  # now resolves correctly

st.set_page_config(
    page_title="CUI Inspector – Multi-Tenant",
    layout="wide",
)

if __name__ == "__main__":
    render_app()



