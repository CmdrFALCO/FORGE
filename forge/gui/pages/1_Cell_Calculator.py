"""
Cell Calculator Page

This page wraps/imports the existing calculator functionality.
"""

import streamlit as st


st.set_page_config(
    page_title="Cell Calculator - FORGE",
    page_icon="battery",
    layout="wide",
)

st.title("Cell Calculator")

st.info("""
**Note**: The Cell Calculator is currently available in the legacy interface.

Run the original calculator with:
```bash
streamlit run streamlit_app.py
```

This page will be integrated in a future update.
""")

st.markdown("---")

st.markdown("""
### Calculator Features

The Cell Calculator provides comprehensive design tools for:

**Pouch Cells**
- Full material specification (cathode, anode, separator, electrolyte)
- Sheet geometry and stack configuration
- Packaging and tab design
- Reference cell validation

**Prismatic Cells**
- Case geometry specification
- Housing and header parameters
- Insulation and fixing tape configuration

**Cylindrical Cells**
- Jelly roll winding parameters
- Can geometry (18650, 21700, 4680, etc.)
- Header assembly

### Data Sources
- PyBaMM parameter sets
- Validated reference cells from literature
- Custom material input

### Outputs
- Capacity and energy calculations
- Mass breakdown (BOM)
- Energy density metrics
- Validation against reference data
""")

# Show available reference cells
st.markdown("---")
st.subheader("Available Reference Cells")

try:
    from forge.engine.validation.result_validation import get_reference_info, list_reference_cells

    pouch_cells = list_reference_cells(cell_type="pouch")
    prismatic_cells = list_reference_cells(cell_type="prismatic")
    cylindrical_cells = list_reference_cells(cell_type="cylindrical")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Pouch Cells**")
        for ref_id in pouch_cells[:5]:
            try:
                info = get_reference_info(ref_id)
                st.caption(f"- {info.get('name', ref_id)}")
            except Exception:
                st.caption(f"- {ref_id}")

    with col2:
        st.markdown("**Prismatic Cells**")
        for ref_id in prismatic_cells[:5]:
            try:
                info = get_reference_info(ref_id)
                st.caption(f"- {info.get('name', ref_id)}")
            except Exception:
                st.caption(f"- {ref_id}")

    with col3:
        st.markdown("**Cylindrical Cells**")
        for ref_id in cylindrical_cells[:5]:
            try:
                info = get_reference_info(ref_id)
                st.caption(f"- {info.get('name', ref_id)}")
            except Exception:
                st.caption(f"- {ref_id}")

except ImportError:
    st.warning("Reference cell database not available.")
