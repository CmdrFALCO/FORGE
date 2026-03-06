"""
FORGE - Battery Cell Design Tool

Main Streamlit application entry point.
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="FORGE",
    page_icon="battery",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Landing page content
st.title("FORGE")
st.markdown("""
**Battery Cell Design and Analysis Tool**

FORGE provides comprehensive tools for battery cell geometry calculation,
visualization, and CAD export.

### Available Tools

| Page | Description |
|------|-------------|
| **Cell Calculator** | Design pouch, prismatic, and cylindrical cells with full parameter control |
| **CAD Export** | Generate STEP, STL, and FreeCAD scripts from reference cell archetypes |
| **Geometry Viewer** | Interactive 3D visualization of cell internal geometry |

---

### Quick Start

1. **Design a Cell**: Use the Cell Calculator to define geometry and materials
2. **Load Reference**: Select from validated commercial cell archetypes
3. **Export CAD**: Generate industry-standard CAD files for simulation

---

*Select a tool from the sidebar to begin.*
""")

# Sidebar info
with st.sidebar:
    st.markdown("### FORGE v1.0")
    st.markdown("---")

    # Show CAD availability status
    from forge.gui.utils.cad_availability import show_cad_status

    show_cad_status()

    st.markdown("---")
    st.markdown("#### Resources")
    st.markdown("""
    - [GitHub Repository](https://github.com/CmdrFALCO/FORGE)
    - [Documentation](docs/)
    """)
