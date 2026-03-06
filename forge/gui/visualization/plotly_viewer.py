"""Plotly-based 3D viewer for DetailedGeometry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import plotly.graph_objects as go

from .colors import DEFAULT_COLORS, ColorScheme
from .geometry_builders import GeometryBuilder

if TYPE_CHECKING:
    from forge.engine.geometry.detailed_geometry import DetailedGeometry


class PlotlyViewer:
    """Interactive 3D viewer for battery cell geometry.

    Supports two detail levels:
    - Simplified: Fast rendering, electrode pairs grouped into blocks
    - Detailed: Individual layers shown with material colors

    Usage:
        viewer = PlotlyViewer()
        fig = viewer.create_figure(detailed_geometry, detail_level="simplified")
        fig.show()  # Or return to Streamlit

    Attributes:
        colors: ColorScheme used for material visualization
        builder: GeometryBuilder for mesh generation
    """

    def __init__(self, colors: ColorScheme | None = None) -> None:
        """Initialize viewer with color scheme.

        Args:
            colors: ColorScheme to use, defaults to DEFAULT_COLORS
        """
        self.colors = colors or DEFAULT_COLORS
        self.builder = GeometryBuilder(self.colors)

    def create_figure(
        self,
        geometry: DetailedGeometry,
        detail_level: Literal["simplified", "detailed"] = "simplified",
        title: str | None = None,
        show_axes: bool = True,
        show_legend: bool = True,
        show_tabs: bool = False,
        width: int = 800,
        height: int = 600,
    ) -> go.Figure:
        """Create Plotly figure from DetailedGeometry.

        Args:
            geometry: DetailedGeometry from Phase 1
            detail_level: "simplified" (fast) or "detailed" (individual layers)
            title: Figure title (defaults to archetype name)
            show_axes: Show X/Y/Z axes
            show_legend: Show component legend
            show_tabs: Show tab geometry if available
            width, height: Figure dimensions in pixels

        Returns:
            Plotly Figure ready for display
        """
        # Build mesh traces
        if detail_level == "simplified":
            traces = self.builder.build_simplified(geometry)
        else:
            traces = self.builder.build_detailed(geometry)

        # Add tab geometry if requested
        if show_tabs:
            if geometry.tab_geometry is None:
                geometry.calculate_tabs()

            if geometry.tab_geometry:
                from .geometry_builders import create_tab_meshes

                tab_meshes = create_tab_meshes(geometry.tab_geometry, self.colors)
                traces.extend(tab_meshes)

        # Create figure
        fig = go.Figure(data=traces)

        # Configure layout
        display_title = title or f"{geometry.archetype_name} - {detail_level.title()} View"

        fig.update_layout(
            title=dict(
                text=display_title,
                x=0.5,
                xanchor="center",
            ),
            width=width,
            height=height,
            showlegend=show_legend,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
            ),
            scene=dict(
                xaxis=dict(
                    title="X (mm)",
                    visible=show_axes,
                    backgroundcolor="rgba(230, 230, 230, 0.5)",
                    gridcolor="rgba(200, 200, 200, 0.5)",
                    showbackground=True,
                ),
                yaxis=dict(
                    title="Y (mm)",
                    visible=show_axes,
                    backgroundcolor="rgba(230, 230, 230, 0.5)",
                    gridcolor="rgba(200, 200, 200, 0.5)",
                    showbackground=True,
                ),
                zaxis=dict(
                    title="Z (mm)",
                    visible=show_axes,
                    backgroundcolor="rgba(230, 230, 230, 0.5)",
                    gridcolor="rgba(200, 200, 200, 0.5)",
                    showbackground=True,
                ),
                aspectmode="data",  # True proportions
                camera=dict(
                    eye=self._get_default_camera_eye(geometry),
                ),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )

        return fig

    def create_comparison_figure(
        self,
        geometry_bol: DetailedGeometry,
        geometry_eol: DetailedGeometry,
        title: str = "BOL vs EOL Comparison",
        width: int = 1200,
        height: int = 600,
    ) -> go.Figure:
        """Create side-by-side comparison of BOL and EOL geometry.

        Useful for visualizing swelling effects.

        Args:
            geometry_bol: Beginning of Life geometry
            geometry_eol: End of Life geometry (with swelling applied)
            title: Figure title
            width, height: Figure dimensions in pixels

        Returns:
            Plotly Figure with two 3D subplots
        """
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "scene"}, {"type": "scene"}]],
            subplot_titles=["Beginning of Life (BOL)", "End of Life (EOL)"],
            horizontal_spacing=0.05,
        )

        # Build traces for both
        traces_bol = self.builder.build_simplified(geometry_bol)
        traces_eol = self.builder.build_simplified(geometry_eol)

        # Add BOL traces to scene1
        for trace in traces_bol:
            trace.scene = "scene1"
            trace.showlegend = False
            fig.add_trace(trace)

        # Add EOL traces to scene2
        for trace in traces_eol:
            trace.scene = "scene2"
            trace.showlegend = False
            fig.add_trace(trace)

        # Configure layout for both scenes
        camera_eye = self._get_default_camera_eye(geometry_bol)

        for scene_key in ["scene1", "scene2"]:
            fig.update_layout(
                **{
                    scene_key: dict(
                        xaxis=dict(title="X (mm)", backgroundcolor="rgba(230, 230, 230, 0.5)"),
                        yaxis=dict(title="Y (mm)", backgroundcolor="rgba(230, 230, 230, 0.5)"),
                        zaxis=dict(title="Z (mm)", backgroundcolor="rgba(230, 230, 230, 0.5)"),
                        aspectmode="data",
                        camera=dict(eye=camera_eye),
                    )
                }
            )

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center"),
            width=width,
            height=height,
            showlegend=False,
        )

        return fig

    def create_cross_section(
        self,
        geometry: DetailedGeometry,
        plane: Literal["XZ", "YZ", "XY"] = "XZ",
        position_mm: float = 0.0,
    ) -> go.Figure:
        """Create 2D cross-section view.

        Shows a slice through the cell, useful for examining layer structure.

        Args:
            geometry: DetailedGeometry
            plane: Cut plane:
                - "XZ": Side view (X horizontal, Z vertical) - default
                - "YZ": Side view (Y horizontal, Z vertical)
                - "XY": Top-down view (X horizontal, Y vertical) - best for cylindrical
            position_mm: Position along the perpendicular axis

        Returns:
            2D Plotly figure showing cross-section
        """
        fig = go.Figure()

        if geometry.cell_type in ("pouch", "prismatic"):
            self._add_stacked_cross_section(fig, geometry, plane)
        elif geometry.cell_type == "cylindrical":
            self._add_wound_cross_section(fig, geometry, plane)

        # Configure axis labels based on plane and cell type
        if plane == "XY":
            x_label = "X (mm)"
            y_label = "Y (mm)"
            view_name = "Top View"
        elif plane == "XZ":
            x_label = "X (mm)"
            y_label = "Z (mm)" if geometry.cell_type != "cylindrical" else "Height (mm)"
            view_name = "Side View (XZ)"
        else:  # YZ
            x_label = "Y (mm)"
            y_label = "Z (mm)" if geometry.cell_type != "cylindrical" else "Height (mm)"
            view_name = "Side View (YZ)"

        # Configure layout
        fig.update_layout(
            title=dict(
                text=f"{geometry.archetype_name} - {view_name}",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title=x_label,
            yaxis_title=y_label,
            xaxis=dict(scaleanchor="y", scaleratio=1, constrain="domain"),
            yaxis=dict(constrain="domain"),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
            ),
            margin=dict(l=60, r=20, t=60, b=60),
        )

        return fig

    def _add_stacked_cross_section(
        self,
        fig: go.Figure,
        geometry: DetailedGeometry,
        plane: str,
    ) -> None:
        """Add stacked cell cross-section to figure."""
        from forge.engine.geometry.layer_stack import LayerStackGeometry

        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        # Get horizontal extent
        if plane == "XZ":
            x_size = ext.length_mm or 100.0
        else:
            x_size = ext.width_mm or 100.0

        # Track layer types shown for legend
        shown_types: set[str] = set()

        for layer in stack.layers:
            z_min = layer.z_bottom_um / 1000.0
            z_max = (layer.z_bottom_um + layer.thickness_um) / 1000.0
            color = self.builder._get_layer_color(layer, geometry.chemistry)

            layer_type = layer.layer_type.value
            show_legend = layer_type not in shown_types
            shown_types.add(layer_type)

            fig.add_shape(
                type="rect",
                x0=-x_size / 2,
                x1=x_size / 2,
                y0=z_min,
                y1=z_max,
                fillcolor=color,
                line=dict(width=0.5, color="rgba(100, 100, 100, 0.5)"),
            )

            # Add trace for legend entry (invisible scatter)
            if show_legend:
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="markers",
                        marker=dict(size=12, color=color),
                        name=layer_type.replace("_", " ").title(),
                        showlegend=True,
                    )
                )

    def _add_wound_cross_section(
        self,
        fig: go.Figure,
        geometry: DetailedGeometry,
        plane: str,
    ) -> None:
        """Add wound cell cross-section to figure.

        XY plane: Top-down view showing concentric rings
        XZ/YZ plane: Side view showing rectangular profile with radial layers
        """

        from forge.engine.geometry.layer_stack import WindingGeometry

        winding: WindingGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry
        height = ext.height_mm or 65.0  # Default height if not specified

        # Limit displayed winds for performance
        shown_winds = min(15, winding.num_winds)
        max(1, winding.num_winds // shown_winds)

        # Track which layers we've added to legend
        shown_legend: set[str] = set()

        if plane == "XY":
            # Top-down view: continuous concentric rings (no gaps)
            self._add_wound_xy_view_continuous(
                fig, winding, geometry.chemistry, shown_legend
            )

        else:
            # XZ or YZ plane: Side view - draw continuous bands (no gaps)
            self._add_wound_side_view_continuous(
                fig, winding, height, geometry.chemistry, shown_legend
            )

            # Add center void
            r_mandrel = winding.mandrel_diameter_mm / 2
            fig.add_shape(
                type="rect",
                x0=-r_mandrel,
                x1=r_mandrel,
                y0=0,
                y1=height,
                fillcolor="rgba(50, 50, 60, 0.9)",
                line=dict(width=1, color="rgba(80, 80, 90, 0.9)"),
            )

    def _add_wind_sublayers_xy(
        self,
        fig: go.Figure,
        wind,
        chemistry: str,
        shown_legend: set[str],
    ) -> None:
        """Add concentric ring sublayers for XY (top-down) view."""
        import numpy as np

        # Define sublayers with their radii and colors
        sublayers = [
            ("anode_collector_r", "Anode collector", self.colors.anode_collector),
            ("anode_coating_inner_r", "Anode coating", self.colors.anode_coating),
            ("separator_inner_r", "Separator", self.colors.separator),
            ("cathode_coating_inner_r", "Cathode coating",
             self.colors.get_cathode_color(chemistry)),
            ("cathode_collector_r", "Cathode collector", self.colors.cathode_collector),
            ("cathode_coating_outer_r", "Cathode coating",
             self.colors.get_cathode_color(chemistry)),
            ("separator_outer_r", "Separator", self.colors.separator),
            ("anode_coating_outer_r", "Anode coating", self.colors.anode_coating),
        ]

        theta = np.linspace(0, 2 * np.pi, 60)

        for attr, name, color in sublayers:
            radii = getattr(wind, attr, (0, 0))
            if radii[0] == 0 and radii[1] == 0:
                continue

            r_inner, r_outer = radii[0] / 1000, radii[1] / 1000

            # Create annular ring using two circles
            x_outer = (r_outer * np.cos(theta)).tolist()
            y_outer = (r_outer * np.sin(theta)).tolist()
            x_inner = (r_inner * np.cos(theta))[::-1].tolist()
            y_inner = (r_inner * np.sin(theta))[::-1].tolist()

            fig.add_trace(
                go.Scatter(
                    x=x_outer + x_inner + [x_outer[0]],
                    y=y_outer + y_inner + [y_outer[0]],
                    fill="toself",
                    fillcolor=color,
                    line=dict(color="rgba(80, 80, 80, 0.3)", width=0.5),
                    name=name,
                    showlegend=name not in shown_legend,
                    hoverinfo="name",
                )
            )
            shown_legend.add(name)

    def _add_wind_sublayers_side(
        self,
        fig: go.Figure,
        wind,
        height: float,
        chemistry: str,
        shown_legend: set[str],
    ) -> None:
        """Add rectangular sublayers for side (XZ/YZ) view."""
        # Define sublayers - draw from inside out on both left and right sides
        sublayers = [
            ("anode_collector_r", "Anode collector", self.colors.anode_collector),
            ("anode_coating_inner_r", "Anode coating", self.colors.anode_coating),
            ("separator_inner_r", "Separator", self.colors.separator),
            ("cathode_coating_inner_r", "Cathode coating",
             self.colors.get_cathode_color(chemistry)),
            ("cathode_collector_r", "Cathode collector", self.colors.cathode_collector),
            ("cathode_coating_outer_r", "Cathode coating",
             self.colors.get_cathode_color(chemistry)),
            ("separator_outer_r", "Separator", self.colors.separator),
            ("anode_coating_outer_r", "Anode coating", self.colors.anode_coating),
        ]

        for attr, _name, color in sublayers:
            radii = getattr(wind, attr, (0, 0))
            if radii[0] == 0 and radii[1] == 0:
                continue

            r_inner, r_outer = radii[0] / 1000, radii[1] / 1000

            # Draw on right side (positive X)
            fig.add_shape(
                type="rect",
                x0=r_inner,
                x1=r_outer,
                y0=0,
                y1=height,
                fillcolor=color,
                line=dict(width=0.3, color="rgba(80, 80, 80, 0.3)"),
            )

            # Draw on left side (negative X) - mirror
            fig.add_shape(
                type="rect",
                x0=-r_outer,
                x1=-r_inner,
                y0=0,
                y1=height,
                fillcolor=color,
                line=dict(width=0.3, color="rgba(80, 80, 80, 0.3)"),
            )

        # Add legend entries via invisible scatter traces
        for _attr, name, color in sublayers:
            if name not in shown_legend:
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="markers",
                        marker=dict(size=12, color=color),
                        name=name,
                        showlegend=True,
                    )
                )
                shown_legend.add(name)

    def _add_wound_xy_view_continuous(
        self,
        fig: go.Figure,
        winding,
        chemistry: str,
        shown_legend: set[str],
    ) -> None:
        """Draw continuous concentric rings for wound cell XY (top-down) view.

        Instead of sampling individual winds, draws continuous annular bands
        from inner to outer radius based on typical layer fractions.
        """
        import numpy as np

        if not winding.winds:
            return

        inner_wind = winding.winds[0]
        outer_wind = winding.winds[-1]

        r_inner = inner_wind.r_inner_um / 1000
        r_outer = outer_wind.r_outer_um / 1000
        total_thickness = r_outer - r_inner

        # Layer pattern and fractions (same as side view)
        fractions = [0.03, 0.22, 0.05, 0.22, 0.06, 0.22, 0.05, 0.15]
        colors_pattern = [
            self.colors.anode_collector,
            self.colors.anode_coating,
            self.colors.separator,
            self.colors.get_cathode_color(chemistry),
            self.colors.cathode_collector,
            self.colors.get_cathode_color(chemistry),
            self.colors.separator,
            self.colors.anode_coating,
        ]
        names_pattern = [
            "Anode collector",
            "Anode coating",
            "Separator",
            "Cathode coating",
            "Cathode collector",
            "Cathode coating",
            "Separator",
            "Anode coating",
        ]

        theta = np.linspace(0, 2 * np.pi, 80)

        # Draw continuous annular bands from inside out
        current_r = r_inner
        for frac, color, name in zip(fractions, colors_pattern, names_pattern):
            band_thickness = total_thickness * frac
            next_r = current_r + band_thickness

            # Create annular ring (outer circle + reversed inner circle)
            x_outer = (next_r * np.cos(theta)).tolist()
            y_outer = (next_r * np.sin(theta)).tolist()
            x_inner = (current_r * np.cos(theta))[::-1].tolist()
            y_inner = (current_r * np.sin(theta))[::-1].tolist()

            fig.add_trace(
                go.Scatter(
                    x=x_outer + x_inner + [x_outer[0]],
                    y=y_outer + y_inner + [y_outer[0]],
                    fill="toself",
                    fillcolor=color,
                    line=dict(color="rgba(60, 60, 60, 0.2)", width=0.3),
                    name=name,
                    showlegend=name not in shown_legend,
                    hoverinfo="name",
                )
            )
            shown_legend.add(name)
            current_r = next_r

        # Add center void (mandrel)
        r_mandrel = winding.mandrel_diameter_mm / 2
        x_mandrel = (r_mandrel * np.cos(theta)).tolist()
        y_mandrel = (r_mandrel * np.sin(theta)).tolist()
        fig.add_trace(
            go.Scatter(
                x=x_mandrel,
                y=y_mandrel,
                fill="toself",
                fillcolor="rgba(40, 40, 50, 0.95)",
                line=dict(color="rgba(60, 60, 70, 0.8)", width=1),
                name="Center void",
                showlegend="Center void" not in shown_legend,
            )
        )
        shown_legend.add("Center void")

    def _add_wound_side_view_continuous(
        self,
        fig: go.Figure,
        winding,
        height: float,
        chemistry: str,
        shown_legend: set[str],
    ) -> None:
        """Draw continuous bands for wound cell side view (no gaps).

        Instead of drawing each wind separately, aggregate all sublayers
        into continuous bands from inner to outer radius.
        """
        # Get innermost and outermost wind to determine total extent
        if not winding.winds:
            return

        inner_wind = winding.winds[0]
        outer_wind = winding.winds[-1]

        # Define layer types and their colors
        layer_configs = [
            ("Anode collector", self.colors.anode_collector),
            ("Anode coating", self.colors.anode_coating),
            ("Separator", self.colors.separator),
            ("Cathode coating", self.colors.get_cathode_color(chemistry)),
            ("Cathode collector", self.colors.cathode_collector),
        ]

        # Calculate approximate radial extents for each layer type
        # Based on typical jellyroll structure (repeated pattern)
        r_inner = inner_wind.r_inner_um / 1000
        r_outer = outer_wind.r_outer_um / 1000
        total_thickness = r_outer - r_inner

        # Approximate layer thicknesses as fractions of wind thickness
        # Typical pattern: anode_cc | anode | sep | cathode | cathode_cc | cathode | sep | anode
        fractions = [0.03, 0.22, 0.05, 0.22, 0.06, 0.22, 0.05, 0.15]  # Must sum to 1
        colors_pattern = [
            self.colors.anode_collector,
            self.colors.anode_coating,
            self.colors.separator,
            self.colors.get_cathode_color(chemistry),
            self.colors.cathode_collector,
            self.colors.get_cathode_color(chemistry),
            self.colors.separator,
            self.colors.anode_coating,
        ]

        # Draw continuous bands
        current_r = r_inner
        for frac, color in zip(fractions, colors_pattern):
            band_thickness = total_thickness * frac
            next_r = current_r + band_thickness

            # Draw on right side
            fig.add_shape(
                type="rect",
                x0=current_r,
                x1=next_r,
                y0=0,
                y1=height,
                fillcolor=color,
                line=dict(width=0),
            )

            # Draw on left side (mirror)
            fig.add_shape(
                type="rect",
                x0=-next_r,
                x1=-current_r,
                y0=0,
                y1=height,
                fillcolor=color,
                line=dict(width=0),
            )

            current_r = next_r

        # Add legend entries
        for name, color in layer_configs:
            if name not in shown_legend:
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="markers",
                        marker=dict(size=12, color=color),
                        name=name,
                        showlegend=True,
                    )
                )
                shown_legend.add(name)

    def _get_default_camera_eye(self, geometry: DetailedGeometry) -> dict[str, float]:
        """Get default camera eye position based on cell type.

        Args:
            geometry: DetailedGeometry to determine viewing angle

        Returns:
            Camera eye position dict with x, y, z coordinates
        """
        if geometry.cell_type == "cylindrical":
            # View cylindrical cells from slight angle to see top and side
            return {"x": 1.2, "y": 1.2, "z": 0.8}
        elif geometry.cell_type == "pouch":
            # View pouch cells from above-ish to see thin profile
            return {"x": 1.5, "y": 1.5, "z": 0.5}
        else:
            # Default for prismatic
            return {"x": 1.5, "y": 1.5, "z": 1.0}

    def create_exploded_view(
        self,
        geometry: DetailedGeometry,
        explosion_factor: float = 1.5,
        max_layers: int = 20,
    ) -> go.Figure:
        """Create exploded view showing layer structure.

        Separates layers with gaps to show internal structure.

        Args:
            geometry: DetailedGeometry
            explosion_factor: Multiplier for layer spacing (1.0 = no explosion)
            max_layers: Maximum number of layers to show (samples if more)

        Returns:
            Plotly Figure with exploded view
        """
        if geometry.cell_type == "cylindrical":
            # Exploded view not as useful for cylindrical - use normal detailed
            return self.create_figure(geometry, detail_level="detailed")

        from forge.engine.geometry.layer_stack import LayerStackGeometry

        traces: list[go.Mesh3d] = []
        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        wall = ext.wall_thickness_mm or 0.5
        x_size = (ext.length_mm or 100.0) - 2 * wall
        y_size = (ext.width_mm or 100.0) - 2 * wall

        # Sample layers if too many
        layers = stack.layers
        if len(layers) > max_layers:
            step = len(layers) // max_layers
            layers = [layers[i] for i in range(0, len(layers), step)]

        # Calculate exploded Z positions
        exploded_z = 0.0

        for layer in layers:
            color = self.builder._get_layer_color(layer, geometry.chemistry)
            thickness_mm = layer.thickness_um / 1000.0

            # Explode by multiplying gaps
            exploded_thickness = thickness_mm * explosion_factor

            x_half, y_half = x_size / 2, y_size / 2

            from .geometry_builders import create_box_mesh

            traces.append(
                create_box_mesh(
                    x_min=-x_half,
                    x_max=x_half,
                    y_min=-y_half,
                    y_max=y_half,
                    z_min=exploded_z,
                    z_max=exploded_z + thickness_mm,
                    color=color,
                    name=f"{layer.layer_type.value} ({layer.material})",
                )
            )

            exploded_z += exploded_thickness

        fig = go.Figure(data=traces)

        fig.update_layout(
            title=dict(
                text=f"{geometry.archetype_name} - Exploded View",
                x=0.5,
                xanchor="center",
            ),
            showlegend=True,
            scene=dict(
                xaxis=dict(title="X (mm)"),
                yaxis=dict(title="Y (mm)"),
                zaxis=dict(title="Z (mm) - Exploded"),
                aspectmode="data",
                camera=dict(eye={"x": 1.5, "y": 1.5, "z": 1.5}),
            ),
        )

        return fig

