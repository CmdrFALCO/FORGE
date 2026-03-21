"""
FORGE landing page.

Run with: streamlit run forge/gui/app.py
"""

from pathlib import Path

import streamlit as st

from forge.gui.utils.cad_availability import show_cad_status

st.set_page_config(
    page_title="FORGE",
    page_icon="battery",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FORGE")
st.markdown(
    """
**Parametric battery cell design and simulation platform**

FORGE combines validated reference cells, engineering calculators, CAD export,
and interactive geometry inspection in one Streamlit workspace.
"""
)

hero_image = Path(__file__).resolve().parents[2] / "docs" / "FORGE_v1.jpg"
if hero_image.exists():
    _, image_col, _ = st.columns([1, 3, 1])
    with image_col:
        st.image(str(hero_image), width="stretch")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Cell Calculator")
    st.write(
        "Parametric cell design with reference loading, material inputs, "
        "and optional PyBaMM-backed parameter sets."
    )
with col2:
    st.subheader("CAD Export")
    st.write(
        "Generate STEP, STL, and FreeCAD outputs from validated cell "
        "archetypes for downstream engineering work."
    )
with col3:
    st.subheader("Geometry Viewer")
    st.write(
        "Inspect internal layer geometry in an interactive 3D view before "
        "export or simulation."
    )

st.markdown("---")
st.subheader("Recommended Workflow")
st.markdown(
    """
1. Load a validated reference cell or enter custom inputs.
2. Calculate electrical, mass, and energy-density results.
3. Export CAD or inspect geometry in the 3D viewer.
"""
)

st.info(
    "Use the sidebar to open Cell Calculator, CAD Export, or Geometry Viewer. "
    "PyBaMM-backed material loading is available when PyBaMM is installed."
)

with st.sidebar:
    st.markdown("### FORGE v1.0")
    st.markdown("---")
    show_cad_status()
    st.markdown("---")
    st.markdown("#### Resources")
    st.markdown(
        """
- [GitHub Repository](https://github.com/CmdrFALCO/FORGE)
- [Documentation](docs/)
"""
    )
