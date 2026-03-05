"""Streamlit integration helpers for PlotlyViewer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from forge.engine.geometry.detailed_geometry import DetailedGeometry

# Import streamlit conditionally to avoid import errors when not installed
try:
    import streamlit as st

    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None  # type: ignore


def _check_streamlit() -> None:
    """Check if Streamlit is available."""
    if not STREAMLIT_AVAILABLE:
        raise ImportError(
            "Streamlit is required for visualization widgets. "
            "Install it with: pip install streamlit"
        )


def render_geometry_viewer(
    geometry: DetailedGeometry,
    key: str = "geometry_viewer",
    default_detail_level: Literal["simplified", "detailed"] = "simplified",
    show_controls: bool = True,
    show_info: bool = True,
) -> None:
    """Render interactive geometry viewer in Streamlit.

    Includes:
    - Detail level toggle (simplified/detailed)
    - View controls (axes, legend)
    - Geometry info panel

    Args:
        geometry: DetailedGeometry to visualize
        key: Unique key for Streamlit widgets (use different keys for multiple viewers)
        default_detail_level: Initial detail level setting
        show_controls: Show control widgets (detail level, axes, legend toggles)
        show_info: Show geometry information panel

    Example:
        ```python
        import streamlit as st
        from forge.engine.geometry.loader import ArchetypeLoader
        from forge.gui.visualization import render_geometry_viewer

        loader = ArchetypeLoader("docs/byd_blade_138ah_archetype.json")
        geometry = loader.to_detailed_geometry()

        st.title("Cell Geometry Viewer")
        render_geometry_viewer(geometry)
        ```
    """
    _check_streamlit()
    from .plotly_viewer import PlotlyViewer

    viewer = PlotlyViewer()

    # Controls row
    if show_controls:
        col1, col2, col3 = st.columns([2, 2, 3])

        with col1:
            detail_level = st.radio(
                "Detail Level",
                options=["simplified", "detailed"],
                index=0 if default_detail_level == "simplified" else 1,
                key=f"{key}_detail",
                horizontal=True,
                help="Simplified: grouped electrode pairs. Detailed: individual layers.",
            )

        with col2:
            show_axes = st.checkbox("Show Axes", value=True, key=f"{key}_axes")
            show_legend = st.checkbox("Show Legend", value=True, key=f"{key}_legend")

        with col3:
            if show_info:
                # Compact info display
                st.caption(f"**{geometry.archetype_name}**")
                info_text = f"Chemistry: {geometry.chemistry} | Type: {geometry.cell_type.title()}"
                if hasattr(geometry.layer_stack, "num_electrode_pairs"):
                    info_text += f" | Pairs: {geometry.layer_stack.num_electrode_pairs}"
                elif hasattr(geometry.layer_stack, "num_winds"):
                    info_text += f" | Winds: {geometry.layer_stack.num_winds}"
                st.caption(info_text)

                if geometry.warnings:
                    st.warning(f"{len(geometry.warnings)} warning(s) - see details below")
    else:
        detail_level = default_detail_level
        show_axes = True
        show_legend = True

    # Create and display figure
    fig = viewer.create_figure(
        geometry,
        detail_level=detail_level,  # type: ignore
        show_axes=show_axes,
        show_legend=show_legend,
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{key}_chart")

    # Expandable details
    if show_info:
        with st.expander("Geometry Details", expanded=False):
            _render_geometry_details(geometry)


def render_geometry_comparison(
    geometry_bol: DetailedGeometry,
    geometry_eol: DetailedGeometry,
    key: str = "geometry_comparison",
    show_metrics: bool = True,
) -> None:
    """Render BOL vs EOL comparison view.

    Shows side-by-side 3D views and thickness change metrics.

    Args:
        geometry_bol: Beginning of Life geometry
        geometry_eol: End of Life geometry (with swelling applied)
        key: Unique key for Streamlit widgets
        show_metrics: Show thickness change metrics below the chart

    Example:
        ```python
        import streamlit as st
        from forge.engine.geometry.loader import ArchetypeLoader
        from forge.gui.visualization import render_geometry_comparison

        loader = ArchetypeLoader("docs/byd_blade_138ah_archetype.json")
        geometry_bol = loader.to_detailed_geometry(apply_swelling=False)
        geometry_eol = loader.to_detailed_geometry(apply_swelling=True)

        st.title("Swelling Comparison")
        render_geometry_comparison(geometry_bol, geometry_eol)
        ```
    """
    _check_streamlit()
    from .plotly_viewer import PlotlyViewer

    viewer = PlotlyViewer()

    fig = viewer.create_comparison_figure(geometry_bol, geometry_eol)
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_chart")

    # Show thickness change metrics
    if show_metrics:
        bol_thickness = geometry_bol.total_stack_thickness_mm()
        eol_thickness = geometry_eol.total_stack_thickness_mm()

        if bol_thickness > 0:
            change_pct = (eol_thickness - bol_thickness) / bol_thickness * 100
            change_mm = eol_thickness - bol_thickness

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "BOL Stack Thickness",
                    f"{bol_thickness:.2f} mm",
                )

            with col2:
                st.metric(
                    "EOL Stack Thickness",
                    f"{eol_thickness:.2f} mm",
                    f"+{change_mm:.2f} mm",
                )

            with col3:
                st.metric(
                    "Swelling",
                    f"+{change_pct:.1f}%",
                    help="Percentage increase in stack thickness due to swelling",
                )


def render_cross_section_viewer(
    geometry: DetailedGeometry,
    key: str = "cross_section_viewer",
) -> None:
    """Render 2D cross-section viewer in Streamlit.

    Args:
        geometry: DetailedGeometry to visualize
        key: Unique key for Streamlit widgets

    Example:
        ```python
        import streamlit as st
        from forge.engine.geometry.loader import ArchetypeLoader
        from forge.gui.visualization import render_cross_section_viewer

        loader = ArchetypeLoader("docs/byd_blade_138ah_archetype.json")
        geometry = loader.to_detailed_geometry()

        st.title("Cross Section View")
        render_cross_section_viewer(geometry)
        ```
    """
    _check_streamlit()
    from .plotly_viewer import PlotlyViewer

    viewer = PlotlyViewer()

    col1, col2 = st.columns([1, 4])

    with col1:
        plane = st.radio(
            "Cut Plane",
            options=["XZ", "YZ"],
            index=0,
            key=f"{key}_plane",
        )

    fig = viewer.create_cross_section(geometry, plane=plane)  # type: ignore
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_chart")


def _render_geometry_details(geometry: DetailedGeometry) -> None:
    """Render detailed geometry information in expandable section."""
    _check_streamlit()

    col_a, col_b = st.columns(2)

    with col_a:
        st.write("**External Dimensions**")
        ext = geometry.external_geometry

        if ext.length_mm:
            st.write(f"- Length: {ext.length_mm:.1f} mm")
        if ext.width_mm:
            st.write(f"- Width: {ext.width_mm:.1f} mm")
        if ext.thickness_mm:
            st.write(f"- Thickness: {ext.thickness_mm:.1f} mm")
        if ext.height_mm and geometry.cell_type != "pouch":
            st.write(f"- Height: {ext.height_mm:.1f} mm")
        if ext.diameter_mm:
            st.write(f"- Diameter: {ext.diameter_mm:.1f} mm")
        if ext.wall_thickness_mm:
            st.write(f"- Wall: {ext.wall_thickness_mm:.2f} mm")

    with col_b:
        st.write("**Internal Stack**")
        stack = geometry.layer_stack

        if hasattr(stack, "num_electrode_pairs"):
            st.write(f"- Electrode pairs: {stack.num_electrode_pairs}")
            st.write(f"- Total layers: {len(stack.layers)}")
        if hasattr(stack, "num_winds"):
            st.write(f"- Winds: {stack.num_winds}")
            st.write(f"- Mandrel: {stack.mandrel_diameter_mm:.1f} mm")

        st.write(f"- Stack thickness: {geometry.total_stack_thickness_mm():.2f} mm")
        st.write(f"- Swelling applied: {'Yes' if stack.swelling_applied else 'No'}")
        st.write(f"- Confidence: {geometry.confidence}")

    # Show warnings if any
    if geometry.warnings:
        st.write("**Warnings**")
        for warning in geometry.warnings:
            st.write(f"- {warning}")

    # Layer summary
    if hasattr(geometry.layer_stack, "layers"):
        st.write("**Layer Summary**")
        summary = geometry.get_layer_count_summary()
        cols = st.columns(len(summary))
        for i, (layer_type, count) in enumerate(summary.items()):
            with cols[i]:
                st.metric(layer_type.replace("_", " ").title(), count)


def render_archetype_selector(
    archetype_dir: str = "docs",
    key: str = "archetype_selector",
) -> DetailedGeometry | None:
    """Render archetype file selector and return loaded geometry.

    Args:
        archetype_dir: Directory containing archetype JSON files
        key: Unique key for Streamlit widgets

    Returns:
        DetailedGeometry if a file is selected, None otherwise

    Example:
        ```python
        import streamlit as st
        from forge.gui.visualization import render_archetype_selector, render_geometry_viewer

        st.title("Cell Geometry Explorer")

        geometry = render_archetype_selector()
        if geometry:
            render_geometry_viewer(geometry)
        ```
    """
    _check_streamlit()
    from pathlib import Path

    from forge.engine.geometry.loader import ArchetypeLoader

    archetype_path = Path(archetype_dir)

    if not archetype_path.exists():
        st.error(f"Archetype directory not found: {archetype_dir}")
        return None

    # Find archetype files
    archetype_files = list(archetype_path.glob("*_archetype.json"))

    if not archetype_files:
        st.warning(f"No archetype files found in {archetype_dir}")
        return None

    # Create selection
    file_names = [f.stem.replace("_archetype", "") for f in archetype_files]

    selected_name = st.selectbox(
        "Select Cell Archetype",
        options=file_names,
        key=f"{key}_select",
    )

    if selected_name:
        selected_idx = file_names.index(selected_name)
        selected_file = archetype_files[selected_idx]

        # Swelling option
        apply_swelling = st.checkbox(
            "Apply EOL Swelling",
            value=False,
            key=f"{key}_swelling",
            help="Apply End of Life swelling factors to show expanded geometry",
        )

        try:
            loader = ArchetypeLoader(selected_file)
            geometry = loader.to_detailed_geometry(apply_swelling=apply_swelling)

            if loader.warnings:
                with st.expander(f"{len(loader.warnings)} loading warning(s)"):
                    for warning in loader.warnings:
                        st.write(f"- {warning}")

            return geometry

        except Exception as e:
            st.error(f"Error loading archetype: {e}")
            return None

    return None

