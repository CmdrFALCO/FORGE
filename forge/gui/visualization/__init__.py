"""Visualization module for FORGE geometry.

This module provides Plotly-based 3D visualization for battery cell geometry
computed by the Internal Geometry Engine (Phase 1).

Main Components:
    PlotlyViewer: Interactive 3D viewer with simplified/detailed modes
    ColorScheme: Configurable material color mapping
    GeometryBuilder: Low-level mesh generation utilities

Streamlit Integration:
    render_geometry_viewer: Full-featured widget with controls
    render_geometry_comparison: BOL vs EOL side-by-side view
    render_cross_section_viewer: 2D cross-section view
    render_archetype_selector: File selection and loading widget

Example Usage:
    >>> from forge.engine.geometry.loader import ArchetypeLoader
    >>> from forge.gui.visualization import PlotlyViewer
    >>>
    >>> # Load archetype and generate geometry
    >>> loader = ArchetypeLoader("docs/byd_blade_138ah_archetype.json")
    >>> geometry = loader.to_detailed_geometry()
    >>>
    >>> # Create interactive 3D view
    >>> viewer = PlotlyViewer()
    >>> fig = viewer.create_figure(geometry, detail_level="simplified")
    >>> fig.show()

Streamlit Example:
    >>> import streamlit as st
    >>> from forge.gui.visualization import render_geometry_viewer
    >>>
    >>> st.title("Cell Geometry Viewer")
    >>> render_geometry_viewer(geometry)
"""

from importlib.util import find_spec

from .colors import DEFAULT_COLORS, ColorScheme


def _plotly_unavailable(*_args, **_kwargs):
    raise ImportError("plotly is required for geometry visualization")


class _MissingPlotlyViewer:
    """Placeholder viewer that fails with a clear optional-dependency error."""

    def __init__(self, *_args, **_kwargs) -> None:
        _plotly_unavailable()


# Plotly-backed modules are optional. Keep colors importable even when plotly
# is not installed so lightweight tests (e.g., color scheme tests) can run.
if find_spec("plotly") is not None:
    from .geometry_builders import (
        GeometryBuilder,
        create_box_mesh,
        create_cylinder_mesh,
    )
    from .plotly_viewer import PlotlyViewer

    _PLOTLY_AVAILABLE = True
else:
    _PLOTLY_AVAILABLE = False
    PlotlyViewer = _MissingPlotlyViewer
    GeometryBuilder = None
    create_box_mesh = _plotly_unavailable
    create_cylinder_mesh = _plotly_unavailable

# Streamlit helpers (only available if streamlit is installed)
if _PLOTLY_AVAILABLE:
    try:
        from . import streamlit_widget as _streamlit_widget

        render_geometry_viewer = _streamlit_widget.render_geometry_viewer
        render_geometry_comparison = _streamlit_widget.render_geometry_comparison
        render_cross_section_viewer = _streamlit_widget.render_cross_section_viewer
        render_archetype_selector = _streamlit_widget.render_archetype_selector

        _STREAMLIT_EXPORTS = [
            "render_geometry_viewer",
            "render_geometry_comparison",
            "render_cross_section_viewer",
            "render_archetype_selector",
        ]
    except ImportError:
        _STREAMLIT_EXPORTS = []
else:
    _STREAMLIT_EXPORTS = []

__all__ = [
    # Always available
    "ColorScheme",
    "DEFAULT_COLORS",
    # Plotly exports (present as real objects when plotly is installed)
    "PlotlyViewer",
    "GeometryBuilder",
    "create_box_mesh",
    "create_cylinder_mesh",
]

__all__.extend(_STREAMLIT_EXPORTS)

