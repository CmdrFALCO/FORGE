"""
Geometry Viewer Page

Standalone 3D viewer for exploring cell geometry without export.
"""

from pathlib import Path

import streamlit as st

from forge.engine.geometry.loader import ArchetypeLoader
from forge.gui.utils import (
    get_output_dir,
    init_session_state,
)
from forge.gui.visualization import PlotlyViewer

st.set_page_config(
    page_title="Geometry Viewer - FORGE",
    page_icon="battery",
    layout="wide",
)

# =============================================================================
# Constants
# =============================================================================

ARCHETYPE_DIR = Path("docs")
ARCHETYPE_FILES = {
    "BYD Blade 138Ah (Prismatic LFP)": "byd_blade_138ah_archetype.json",
    "Tesla 4680 (Cylindrical NMC811)": "tesla_4680_archetype.json",
    "LG E66A (Pouch NMC712)": "lg_e66a_archetype.json",
    "Samsung 21700-50G (Cylindrical NMC811)": "samsung_21700_50g_archetype.json",
    "Samsung SDI 94Ah (Prismatic NMC)": "samsung_sdi_94ah_archetype.json",
    "CATL Qilin (Prismatic)": "catl_qilin_archetype.json",
}


# =============================================================================
# Session State Initialization
# =============================================================================

init_session_state(
    {
        "viewer_geometry": None,
        "viewer_detail": "simplified",
        "viewer_show_cross_section": False,
        "viewer_cross_section_plane": "XZ",
        "viewer_apply_swelling": True,
        "viewer_show_layer_table": False,
    }
)


# =============================================================================
# Helper Functions
# =============================================================================


def load_archetype(filepath: Path, apply_swelling: bool = True):
    """Load archetype and convert to DetailedGeometry."""
    loader = ArchetypeLoader(filepath)
    return loader.to_detailed_geometry(apply_swelling=apply_swelling)


def get_archetype_path(selection: str, uploaded_file=None) -> Path | None:
    """Get archetype file path from selection or upload."""
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = get_output_dir() / "temp_viewer_archetype.json"
        temp_path.write_bytes(uploaded_file.getvalue())
        return temp_path
    elif selection and selection in ARCHETYPE_FILES:
        return ARCHETYPE_DIR / ARCHETYPE_FILES[selection]
    return None


# =============================================================================
# Page Layout
# =============================================================================

st.title("Geometry Viewer")
st.markdown("Interactive 3D visualization of battery cell internal geometry.")

# -----------------------------------------------------------------------------
# Sidebar: Cell Selection and View Options
# -----------------------------------------------------------------------------

with st.sidebar:
    st.header("Cell Selection")

    # Archetype dropdown
    selected_name = st.selectbox(
        "Reference Cell Archetype",
        options=[""] + list(ARCHETYPE_FILES.keys()),
        index=0,
        help="Select a validated commercial cell archetype",
        key="viewer_archetype_select",
    )

    st.markdown("**- OR -**")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Custom Archetype",
        type=["json"],
        help="Upload a custom archetype JSON file",
        key="viewer_upload",
    )

    st.markdown("---")

    # View Options
    st.header("View Options")

    detail_level = st.radio(
        "Detail Level",
        options=["simplified", "detailed"],
        index=0 if st.session_state.viewer_detail == "simplified" else 1,
        horizontal=True,
        help="Simplified: grouped electrode pairs. Detailed: individual layers.",
        key="viewer_detail_radio",
    )
    st.session_state.viewer_detail = detail_level

    apply_swelling = st.checkbox(
        "Apply EOL Swelling",
        value=st.session_state.viewer_apply_swelling,
        help="Apply chemistry-specific swelling factors to geometry",
        key="viewer_swelling_check",
    )
    st.session_state.viewer_apply_swelling = apply_swelling

    st.markdown("---")

    # Cross Section Options
    st.header("Cross Section")

    show_cross_section = st.checkbox(
        "Show Cross Section",
        value=st.session_state.viewer_show_cross_section,
        help="Display 2D cross-section view",
        key="viewer_cross_check",
    )
    st.session_state.viewer_show_cross_section = show_cross_section

    if show_cross_section:
        cross_plane = st.radio(
            "Plane",
            options=["XZ", "YZ", "XY"],
            index=["XZ", "YZ", "XY"].index(st.session_state.viewer_cross_section_plane)
            if st.session_state.viewer_cross_section_plane in ["XZ", "YZ", "XY"]
            else 0,
            horizontal=True,
            help="XZ/YZ: Side view. XY: Top-down view (best for cylindrical).",
            key="viewer_plane_radio",
        )
        st.session_state.viewer_cross_section_plane = cross_plane

    st.markdown("---")

    # Layer Information
    st.header("Layer Info")

    show_layer_table = st.checkbox(
        "Show Layer Table",
        value=st.session_state.viewer_show_layer_table,
        help="Display detailed layer breakdown",
        key="viewer_layer_check",
    )
    st.session_state.viewer_show_layer_table = show_layer_table


# -----------------------------------------------------------------------------
# Main Content
# -----------------------------------------------------------------------------

# Get archetype path
archetype_path = get_archetype_path(selected_name, uploaded_file)

if archetype_path is None:
    st.info("Select a reference cell or upload an archetype to begin.")
    st.stop()

# Load geometry
try:
    with st.spinner("Loading archetype..."):
        geometry = load_archetype(archetype_path, st.session_state.viewer_apply_swelling)
        st.session_state.viewer_geometry = geometry
except Exception as e:
    st.error(f"Failed to load archetype: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# Cell Information Panel
# -----------------------------------------------------------------------------

st.subheader("Cell Information")

info_cols = st.columns(5)

with info_cols[0]:
    st.metric("Cell Type", geometry.cell_type.title())

with info_cols[1]:
    st.metric("Chemistry", geometry.chemistry)

with info_cols[2]:
    ext = geometry.external_geometry
    if geometry.cell_type == "cylindrical":
        dims = f"{ext.diameter_mm:.0f} x {ext.height_mm:.0f} mm"
    else:
        thickness = ext.thickness_mm or ext.height_mm
        dims = f"{ext.length_mm:.0f} x {ext.width_mm:.0f} x {thickness:.1f} mm"
    st.metric("Dimensions", dims)

with info_cols[3]:
    stack_thickness = geometry.total_stack_thickness_mm()
    st.metric("Stack Thickness", f"{stack_thickness:.2f} mm")

with info_cols[4]:
    # Handle both stacked (layers) and wound (winds) geometries
    if hasattr(geometry.layer_stack, "layers"):
        layer_count = len(geometry.layer_stack.layers)
    elif hasattr(geometry.layer_stack, "winds"):
        layer_count = len(geometry.layer_stack.winds)
    else:
        layer_count = 0
    st.metric("Layers/Winds", layer_count)

# Show warnings if any
if geometry.warnings:
    with st.expander(f"{len(geometry.warnings)} Warning(s)", expanded=False):
        for warning in geometry.warnings:
            st.warning(warning)


# -----------------------------------------------------------------------------
# 3D Preview
# -----------------------------------------------------------------------------

st.subheader("3D View")

viewer = PlotlyViewer()

# Main 3D view
fig = viewer.create_figure(
    geometry,
    detail_level=st.session_state.viewer_detail,
    title=geometry.archetype_name,
    height=600,
)
st.plotly_chart(fig, use_container_width=True, key="viewer_main")


# -----------------------------------------------------------------------------
# Cross Section View
# -----------------------------------------------------------------------------

if st.session_state.viewer_show_cross_section:
    st.subheader(f"Cross Section ({st.session_state.viewer_cross_section_plane} Plane)")

    fig_cross = viewer.create_cross_section(
        geometry, plane=st.session_state.viewer_cross_section_plane
    )
    st.plotly_chart(fig_cross, use_container_width=True, key="viewer_cross")


# -----------------------------------------------------------------------------
# Layer Information Table
# -----------------------------------------------------------------------------

if st.session_state.viewer_show_layer_table:
    st.subheader("Layer Stack Details")

    # Build layer data - handle both stacked and wound geometries
    layer_data = []

    if hasattr(geometry.layer_stack, "layers"):
        # Stacked cells (pouch/prismatic)
        for i, layer in enumerate(geometry.layer_stack.layers):
            layer_info = {
                "Index": i + 1,
                "Type": layer.layer_type.value,
                "Material": layer.material,
                "Thickness (um)": f"{layer.thickness_um:.1f}",
            }
            layer_data.append(layer_info)

        if layer_data:
            st.dataframe(layer_data, use_container_width=True, hide_index=True)

            # Summary statistics
            st.markdown("**Stack Summary**")
            summary_cols = st.columns(4)

            # Count layers by type
            type_counts = {}
            for layer in geometry.layer_stack.layers:
                layer_type = layer.layer_type.value
                type_counts[layer_type] = type_counts.get(layer_type, 0) + 1

            for col_idx, (layer_type, count) in enumerate(sorted(type_counts.items())):
                with summary_cols[col_idx % 4]:
                    st.metric(layer_type.replace("_", " ").title(), count)

    elif hasattr(geometry.layer_stack, "winds"):
        # Wound cells (cylindrical)
        for wind in geometry.layer_stack.winds:
            wind_info = {
                "Wind": wind.wind_index + 1,
                "Inner R (mm)": f"{wind.r_inner_um / 1000:.3f}",
                "Outer R (mm)": f"{wind.r_outer_um / 1000:.3f}",
                "Thickness (um)": f"{wind.r_outer_um - wind.r_inner_um:.1f}",
            }
            layer_data.append(wind_info)

        if layer_data:
            st.dataframe(layer_data, use_container_width=True, hide_index=True)
            st.caption(f"Total winds: {len(geometry.layer_stack.winds)}")

    if not layer_data:
        st.info("No layer data available.")


# -----------------------------------------------------------------------------
# Geometry Statistics
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader("Geometry Statistics")

stats_cols = st.columns(3)

with stats_cols[0]:
    st.markdown("**Stack Composition**")

    if hasattr(geometry.layer_stack, "layers"):
        # Stacked cells - calculate total thickness by layer type
        thickness_by_type = {}
        total_thickness = 0.0

        for layer in geometry.layer_stack.layers:
            layer_type = layer.layer_type.value
            t = layer.thickness_um / 1000.0  # Convert to mm
            thickness_by_type[layer_type] = thickness_by_type.get(layer_type, 0) + t
            total_thickness += t

        for layer_type, thickness in sorted(thickness_by_type.items()):
            pct = (thickness / total_thickness * 100) if total_thickness > 0 else 0
            display_name = layer_type.replace("_", " ").title()
            st.caption(f"{display_name}: {thickness:.3f} mm ({pct:.1f}%)")

    elif hasattr(geometry.layer_stack, "winds"):
        # Wound cells - show winding info
        winding = geometry.layer_stack
        st.caption(f"Winds: {len(winding.winds)}")
        if hasattr(winding, "mandrel_diameter_mm"):
            st.caption(f"Mandrel: {winding.mandrel_diameter_mm:.2f} mm")
        if hasattr(winding, "outer_diameter_mm"):
            st.caption(f"Outer diameter: {winding.outer_diameter_mm:.2f} mm")

with stats_cols[1]:
    st.markdown("**External Geometry**")
    ext = geometry.external_geometry

    if geometry.cell_type == "cylindrical":
        st.caption(f"Diameter: {ext.diameter_mm:.1f} mm")
        st.caption(f"Height: {ext.height_mm:.1f} mm")
        if hasattr(ext, "can_thickness_mm"):
            st.caption(f"Can Thickness: {ext.can_thickness_mm:.2f} mm")
    else:
        st.caption(f"Length: {ext.length_mm:.1f} mm")
        st.caption(f"Width: {ext.width_mm:.1f} mm")
        thickness = ext.thickness_mm or ext.height_mm
        st.caption(f"Thickness: {thickness:.2f} mm")

with stats_cols[2]:
    st.markdown("**Swelling Status**")
    if st.session_state.viewer_apply_swelling:
        st.caption("EOL swelling applied")
        if hasattr(geometry, "swelling_factor"):
            st.caption(f"Swelling factor: {geometry.swelling_factor:.1%}")
    else:
        st.caption("BOL (no swelling)")
