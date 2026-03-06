"""
CAD Export Page

Generate STEP, STL, and FreeCAD scripts from cell archetypes.
"""

from datetime import datetime
from pathlib import Path

import streamlit as st

from forge.engine.cad import BUILD123D_AVAILABLE
from forge.engine.cad.freecad import FreeCADScriptGenerator
from forge.engine.geometry.loader import ArchetypeLoader
from forge.engine.geometry.validation import GeometryValidator
from forge.gui.utils import (
    check_cad_available,
    format_file_size,
    get_output_dir,
    init_session_state,
    render_validation_panel,
    render_validation_summary,
)
from forge.gui.visualization import PlotlyViewer

if BUILD123D_AVAILABLE:
    from forge.engine.cad import Build123dGenerator
    from forge.engine.cad.exporters.stl_exporter import STLExporter, STLQuality

st.set_page_config(
    page_title="CAD Export - FORGE",
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
        "selected_archetype": None,
        "geometry": None,
        "geometry_bol": None,
        "geometry_eol": None,
        "preview_detail": "simplified",
        "show_eol": False,
        "show_cross_section": False,
        "apply_swelling": True,
        "export_grouping": "by_material",
        "stl_quality": "medium",
        "stl_binary": True,
        "validation_report": None,
        "can_export": True,
        "include_tabs_terminals": True,
    }
)


# =============================================================================
# Helper Functions
# =============================================================================


def load_archetype(filepath: Path, apply_swelling: bool = True):
    """Load archetype and convert to DetailedGeometry."""
    loader = ArchetypeLoader(filepath)
    return loader.to_detailed_geometry(apply_swelling=apply_swelling)


def load_archetype_both_states(filepath: Path) -> tuple:
    """Load archetype as both BOL and EOL geometry."""
    loader = ArchetypeLoader(filepath)
    bol = loader.to_detailed_geometry(apply_swelling=False)

    loader_eol = ArchetypeLoader(filepath)
    eol = loader_eol.to_detailed_geometry(apply_swelling=True)

    return bol, eol


def get_archetype_path(selection: str, uploaded_file=None) -> Path | None:
    """Get archetype file path from selection or upload."""
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = get_output_dir() / "temp_archetype.json"
        temp_path.write_bytes(uploaded_file.getvalue())
        return temp_path
    elif selection and selection in ARCHETYPE_FILES:
        return ARCHETYPE_DIR / ARCHETYPE_FILES[selection]
    return None


def get_safe_filename(name: str) -> str:
    """Convert archetype name to safe filename."""
    return name.replace(" ", "_").replace("/", "-").replace("(", "").replace(")", "")


# =============================================================================
# Page Layout
# =============================================================================

st.title("CAD Export")
st.markdown("Generate industry-standard CAD files from validated cell archetypes.")

# Check CAD availability
cad_status = check_cad_available()

# -----------------------------------------------------------------------------
# Sidebar: Cell Selection
# -----------------------------------------------------------------------------

with st.sidebar:
    st.header("Cell Selection")

    # Archetype dropdown
    selected_name = st.selectbox(
        "Reference Cell Archetype",
        options=[""] + list(ARCHETYPE_FILES.keys()),
        index=0,
        help="Select a validated commercial cell archetype",
    )

    st.markdown("**- OR -**")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Custom Archetype",
        type=["json"],
        help="Upload a custom archetype JSON file",
    )

    st.markdown("---")

    # Preview Options
    st.header("Preview Options")

    detail_level = st.radio(
        "Detail Level",
        options=["simplified", "detailed"],
        index=0 if st.session_state.preview_detail == "simplified" else 1,
        horizontal=True,
        help="Simplified: grouped electrode pairs. Detailed: individual layers.",
    )
    st.session_state.preview_detail = detail_level

    show_eol = st.checkbox(
        "Show EOL Comparison",
        value=st.session_state.show_eol,
        help="Show Beginning of Life vs End of Life side-by-side",
    )
    st.session_state.show_eol = show_eol

    show_cross_section = st.checkbox(
        "Show Cross Section",
        value=st.session_state.show_cross_section,
        help="Show 2D cross-section view below 3D preview",
    )
    st.session_state.show_cross_section = show_cross_section

    apply_swelling = st.checkbox(
        "Apply EOL Swelling",
        value=st.session_state.apply_swelling,
        help="Apply chemistry-specific swelling factors to geometry",
    )
    st.session_state.apply_swelling = apply_swelling

    st.markdown("---")

    # Tab/Terminal Options
    st.header("Tab/Terminal Options")

    include_tabs = st.checkbox(
        "Include Tabs and Terminals",
        value=st.session_state.include_tabs_terminals,
        help="Add tab strips, busbars, terminals, and header assemblies to CAD exports",
    )
    st.session_state.include_tabs_terminals = include_tabs

    st.markdown("---")

    # CAD Status
    st.header("CAD Status")
    if cad_status["build123d"]:
        st.success(f"build123d {cad_status['build123d_version']}")
    else:
        st.warning("build123d not installed")
        st.caption("STEP/STL export unavailable")
        st.code("pip install forge[cad]", language="bash")

    st.success("FreeCAD scripts available")


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
        if st.session_state.show_eol:
            geometry_bol, geometry_eol = load_archetype_both_states(archetype_path)
            geometry = geometry_eol if st.session_state.apply_swelling else geometry_bol
            st.session_state.geometry_bol = geometry_bol
            st.session_state.geometry_eol = geometry_eol
        else:
            geometry = load_archetype(archetype_path, st.session_state.apply_swelling)
            geometry_bol = None
            geometry_eol = None

        st.session_state.geometry = geometry
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
    # Calculate tabs if not already done
    if geometry.tab_geometry is None:
        geometry.calculate_tabs()
    tab_count = geometry.tab_geometry.total_tab_count if geometry.tab_geometry else 0
    st.metric("Tabs", str(tab_count))

# Show warnings if any
if geometry.warnings:
    with st.expander(f"{len(geometry.warnings)} Warning(s)", expanded=False):
        for warning in geometry.warnings:
            st.warning(warning)

# -----------------------------------------------------------------------------
# Validation Panel
# -----------------------------------------------------------------------------

st.subheader("Validation")

validator = GeometryValidator()
validation_report = validator.validate(geometry)

# Store for export buttons
st.session_state.validation_report = validation_report
st.session_state.can_export = validation_report.passed

# Render summary
can_export, has_warnings = render_validation_summary(validation_report)

# Detailed panel
with st.expander("Validation Details", expanded=not can_export):
    render_validation_panel(validation_report, show_passed=True)

# Warning if export blocked
if not can_export:
    st.error("Export blocked: Fix errors above before exporting.")

# -----------------------------------------------------------------------------
# 3D Preview
# -----------------------------------------------------------------------------

st.subheader("3D Preview")

viewer = PlotlyViewer()

if st.session_state.show_eol and geometry_bol and geometry_eol:
    # Side-by-side BOL vs EOL
    st.markdown("**Beginning of Life (BOL) vs End of Life (EOL)**")

    preview_cols = st.columns(2)

    with preview_cols[0]:
        st.markdown("**BOL**")
        fig_bol = viewer.create_figure(
            geometry_bol,
            detail_level=st.session_state.preview_detail,
            title="BOL Geometry",
            height=450,
        )
        st.plotly_chart(fig_bol, use_container_width=True, key="preview_bol")
        st.caption(f"Stack: {geometry_bol.total_stack_thickness_mm():.2f} mm")

    with preview_cols[1]:
        st.markdown("**EOL (with swelling)**")
        fig_eol = viewer.create_figure(
            geometry_eol,
            detail_level=st.session_state.preview_detail,
            title="EOL Geometry",
            height=450,
        )
        st.plotly_chart(fig_eol, use_container_width=True, key="preview_eol")
        st.caption(f"Stack: {geometry_eol.total_stack_thickness_mm():.2f} mm")

    # Swelling delta
    delta = geometry_eol.total_stack_thickness_mm() - geometry_bol.total_stack_thickness_mm()
    delta_pct = (delta / geometry_bol.total_stack_thickness_mm()) * 100
    st.info(f"Swelling: +{delta:.3f} mm (+{delta_pct:.1f}%)")

else:
    # Single view
    fig = viewer.create_figure(
        geometry,
        detail_level=st.session_state.preview_detail,
        title=geometry.archetype_name,
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True, key="preview_main")

# Cross-section view
if st.session_state.show_cross_section:
    st.markdown("**Cross Section (XZ Plane)**")
    fig_cross = viewer.create_cross_section(geometry, plane="XZ")
    st.plotly_chart(fig_cross, use_container_width=True, key="cross_section")

# -----------------------------------------------------------------------------
# Export Options
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader("Export Options")

export_cols = st.columns(3)

# --- STEP Export ---
with export_cols[0]:
    st.markdown("### STEP Export")

    if not cad_status["step_export"]:
        st.warning("Requires build123d")
        st.code("pip install forge[cad]", language="bash")
    else:
        step_grouping = st.selectbox(
            "Grouping Mode",
            options=["by_material", "individual"],
            index=0,
            help="by_material: fewer bodies. individual: one per layer.",
            key="step_grouping",
        )

        if st.button(
            "Generate STEP",
            key="btn_step",
            use_container_width=True,
            disabled=not st.session_state.get("can_export", True),
        ):
            with st.spinner("Generating STEP file..."):
                try:
                    output_dir = get_output_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = get_safe_filename(geometry.archetype_name)
                    output_path = output_dir / f"{safe_name}_{timestamp}.step"

                    generator = Build123dGenerator(
                        grouping_mode=step_grouping,
                        include_tabs_terminals=st.session_state.include_tabs_terminals,
                    )
                    assembly = generator.generate(geometry)
                    result_path = generator.export_step(assembly, output_path)

                    st.success("STEP exported!")
                    st.code(str(result_path), language=None)
                    st.caption(f"Size: {format_file_size(result_path.stat().st_size)}")
                    st.caption(f"Bodies: {assembly.body_count()}")
                    if st.session_state.include_tabs_terminals:
                        st.caption("Includes tabs and terminals")

                except Exception as e:
                    st.error(f"Export failed: {e}")

# --- STL Export ---
with export_cols[1]:
    st.markdown("### STL Export")

    if not cad_status["stl_export"]:
        st.warning("Requires build123d")
        st.code("pip install forge[cad]", language="bash")
    else:
        stl_quality = st.selectbox(
            "Quality",
            options=["low", "medium", "high"],
            index=1,
            help="low: fast/small. high: smooth/large.",
            key="stl_quality_select",
        )

        stl_binary = st.checkbox(
            "Binary format",
            value=True,
            help="Binary is smaller. ASCII is human-readable.",
            key="stl_binary_check",
        )

        if st.button(
            "Generate STL",
            key="btn_stl",
            use_container_width=True,
            disabled=not st.session_state.get("can_export", True),
        ):
            with st.spinner("Generating STL file..."):
                try:
                    output_dir = get_output_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = get_safe_filename(geometry.archetype_name)
                    output_path = output_dir / f"{safe_name}_{timestamp}.stl"

                    generator = Build123dGenerator(
                        include_tabs_terminals=st.session_state.include_tabs_terminals,
                    )
                    assembly = generator.generate(geometry)

                    quality_map = {
                        "low": STLQuality.LOW,
                        "medium": STLQuality.MEDIUM,
                        "high": STLQuality.HIGH,
                    }
                    exporter = STLExporter(quality=quality_map[stl_quality], binary=stl_binary)
                    result = exporter.export_combined(assembly, output_path)

                    if result.success:
                        st.success("STL exported!")
                        st.code(str(result.filepath), language=None)
                        st.caption(f"Size: {format_file_size(result.file_size_bytes)}")
                        st.caption(f"Quality: {stl_quality}, {'Binary' if stl_binary else 'ASCII'}")
                        if st.session_state.include_tabs_terminals:
                            st.caption("Includes tabs and terminals")
                    else:
                        st.error(f"Export failed: {result.error_message}")

                except Exception as e:
                    st.error(f"Export failed: {e}")

# --- FreeCAD Script ---
with export_cols[2]:
    st.markdown("### FreeCAD Script")

    freecad_grouping = st.selectbox(
        "Grouping Mode",
        options=["by_material", "individual"],
        index=0,
        help="by_material: cleaner tree. individual: detailed layers.",
        key="freecad_grouping",
    )

    if st.button(
        "Generate Script",
        key="btn_freecad",
        use_container_width=True,
        disabled=not st.session_state.get("can_export", True),
    ):
        with st.spinner("Generating FreeCAD script..."):
            try:
                output_dir = get_output_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = get_safe_filename(geometry.archetype_name)
                output_path = output_dir / f"{safe_name}_{timestamp}_freecad.py"

                generator = FreeCADScriptGenerator(grouping_mode=freecad_grouping)
                result = generator.generate(geometry, output_path)

                if result.success:
                    st.success("FreeCAD script generated!")
                    st.code(str(result.filepath), language=None)
                    st.caption(f"Lines: {result.line_count}")
                    st.caption("Run in FreeCAD: Macro > Execute")

                    # Download button
                    with open(result.filepath) as f:
                        st.download_button(
                            label="Download Script",
                            data=f.read(),
                            file_name=result.filepath.name,
                            mime="text/x-python",
                        )
                else:
                    st.error(f"Generation failed: {result.error_message}")

            except Exception as e:
                st.error(f"Generation failed: {e}")

# -----------------------------------------------------------------------------
# Output Files Panel
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader("Output Files")

output_dir = get_output_dir()
output_files = list(output_dir.glob("*"))

# Filter out temp files
output_files = [f for f in output_files if not f.name.startswith("temp_")]

if not output_files:
    st.info("No files generated yet. Use the export buttons above.")
else:
    # Filter by type
    step_files = [f for f in output_files if f.suffix.lower() in (".step", ".stp")]
    stl_files = [f for f in output_files if f.suffix.lower() == ".stl"]
    py_files = [f for f in output_files if f.suffix.lower() == ".py"]

    file_cols = st.columns(3)

    with file_cols[0]:
        st.markdown("**STEP Files**")
        if step_files:
            for f in sorted(step_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                st.caption(f"{f.name} ({format_file_size(f.stat().st_size)})")
        else:
            st.caption("None")

    with file_cols[1]:
        st.markdown("**STL Files**")
        if stl_files:
            for f in sorted(stl_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                st.caption(f"{f.name} ({format_file_size(f.stat().st_size)})")
        else:
            st.caption("None")

    with file_cols[2]:
        st.markdown("**FreeCAD Scripts**")
        if py_files:
            for f in sorted(py_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                st.caption(f"{f.name}")
        else:
            st.caption("None")

    # Clear button
    if st.button("Clear All Outputs", key="btn_clear"):
        for f in output_files:
            if f.is_file():
                f.unlink()
        st.success("Outputs cleared!")
        st.rerun()
