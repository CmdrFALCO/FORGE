"""Convert DetailedGeometry to Plotly mesh data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go

from .colors import DEFAULT_COLORS, ColorScheme


if TYPE_CHECKING:
    from forge.engine.geometry.detailed_geometry import DetailedGeometry
    from forge.engine.geometry.layer_stack import Layer, LayerStackGeometry, WindingGeometry
    from forge.engine.geometry.tabs import Busbar, TabGeometry, TabStrip, TerminalPost


def create_box_mesh(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
    color: str,
    name: str,
    opacity: float | None = None,
) -> go.Mesh3d:
    """Create a 3D box mesh for Plotly.

    Args:
        x_min, x_max: X bounds (mm)
        y_min, y_max: Y bounds (mm)
        z_min, z_max: Z bounds (mm)
        color: RGBA color string
        name: Display name for legend/hover
        opacity: Override opacity (0-1), extracted from color if None

    Returns:
        Plotly Mesh3d trace
    """
    # 8 vertices of a box
    vertices = np.array(
        [
            [x_min, y_min, z_min],  # 0: bottom-left-front
            [x_max, y_min, z_min],  # 1: bottom-right-front
            [x_max, y_max, z_min],  # 2: bottom-right-back
            [x_min, y_max, z_min],  # 3: bottom-left-back
            [x_min, y_min, z_max],  # 4: top-left-front
            [x_max, y_min, z_max],  # 5: top-right-front
            [x_max, y_max, z_max],  # 6: top-right-back
            [x_min, y_max, z_max],  # 7: top-left-back
        ]
    )

    # 12 triangles (2 per face, 6 faces)
    # Each triangle defined by indices i, j, k
    i = [0, 0, 4, 4, 0, 1, 2, 3, 0, 1, 5, 4]
    j = [1, 3, 5, 7, 4, 5, 6, 7, 3, 2, 6, 7]
    k = [2, 2, 6, 6, 1, 2, 3, 0, 4, 6, 2, 3]

    # Extract opacity from color if not specified
    if opacity is None:
        opacity = _extract_opacity_from_color(color)

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i,
        j=j,
        k=k,
        color=color,
        opacity=opacity,
        name=name,
        hoverinfo="name",
        flatshading=True,
        showlegend=True,
    )


def create_cylinder_mesh(
    r_inner: float,
    r_outer: float,
    z_min: float,
    z_max: float,
    color: str,
    name: str,
    n_theta: int = 32,
    opacity: float | None = None,
) -> go.Mesh3d:
    """Create a hollow cylinder (annulus) mesh for Plotly.

    For solid cylinders, set r_inner=0.

    Args:
        r_inner: Inner radius (mm), 0 for solid cylinder
        r_outer: Outer radius (mm)
        z_min, z_max: Z bounds (mm)
        color: RGBA color string
        name: Display name
        n_theta: Number of angular segments (smoothness)
        opacity: Override opacity

    Returns:
        Plotly Mesh3d trace
    """
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)

    if r_inner <= 0:
        # Solid cylinder
        return _create_solid_cylinder_mesh(r_outer, z_min, z_max, theta, color, name, opacity)
    else:
        # Hollow cylinder (annulus)
        return _create_hollow_cylinder_mesh(r_inner, r_outer, z_min, z_max, theta, color, name, opacity)


def _create_solid_cylinder_mesh(
    radius: float,
    z_min: float,
    z_max: float,
    theta: np.ndarray,
    color: str,
    name: str,
    opacity: float | None,
) -> go.Mesh3d:
    """Create a solid cylinder mesh."""
    n = len(theta)

    # Vertices: center bottom, bottom ring, center top, top ring
    vertices = []

    # Bottom center
    vertices.append([0, 0, z_min])

    # Bottom ring
    for t in theta:
        vertices.append([radius * np.cos(t), radius * np.sin(t), z_min])

    # Top center
    vertices.append([0, 0, z_max])

    # Top ring
    for t in theta:
        vertices.append([radius * np.cos(t), radius * np.sin(t), z_max])

    vertices = np.array(vertices)

    # Indices
    i_list, j_list, k_list = [], [], []

    # Bottom face (fan from center)
    for idx in range(n):
        next_idx = (idx + 1) % n
        i_list.append(0)  # center bottom
        j_list.append(1 + next_idx)
        k_list.append(1 + idx)

    # Top face (fan from center)
    top_center = n + 1
    for idx in range(n):
        next_idx = (idx + 1) % n
        i_list.append(top_center)
        j_list.append(top_center + 1 + idx)
        k_list.append(top_center + 1 + next_idx)

    # Side faces (two triangles per quad)
    for idx in range(n):
        next_idx = (idx + 1) % n
        bottom_curr = 1 + idx
        bottom_next = 1 + next_idx
        top_curr = top_center + 1 + idx
        top_next = top_center + 1 + next_idx

        # Triangle 1
        i_list.append(bottom_curr)
        j_list.append(bottom_next)
        k_list.append(top_curr)

        # Triangle 2
        i_list.append(bottom_next)
        j_list.append(top_next)
        k_list.append(top_curr)

    if opacity is None:
        opacity = _extract_opacity_from_color(color)

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i_list,
        j=j_list,
        k=k_list,
        color=color,
        opacity=opacity,
        name=name,
        hoverinfo="name",
        flatshading=True,
        showlegend=True,
    )


def _create_hollow_cylinder_mesh(
    r_inner: float,
    r_outer: float,
    z_min: float,
    z_max: float,
    theta: np.ndarray,
    color: str,
    name: str,
    opacity: float | None,
) -> go.Mesh3d:
    """Create a hollow cylinder (annulus) mesh."""
    n = len(theta)

    # Vertices: outer bottom, outer top, inner bottom, inner top
    vertices = []

    # Outer bottom ring
    for t in theta:
        vertices.append([r_outer * np.cos(t), r_outer * np.sin(t), z_min])

    # Outer top ring
    for t in theta:
        vertices.append([r_outer * np.cos(t), r_outer * np.sin(t), z_max])

    # Inner bottom ring
    for t in theta:
        vertices.append([r_inner * np.cos(t), r_inner * np.sin(t), z_min])

    # Inner top ring
    for t in theta:
        vertices.append([r_inner * np.cos(t), r_inner * np.sin(t), z_max])

    vertices = np.array(vertices)

    # Indices
    i_list, j_list, k_list = [], [], []

    # Offset indices for each ring
    outer_bottom = 0
    outer_top = n
    inner_bottom = 2 * n
    inner_top = 3 * n

    # Outer surface
    for idx in range(n):
        next_idx = (idx + 1) % n
        ob_curr = outer_bottom + idx
        ob_next = outer_bottom + next_idx
        ot_curr = outer_top + idx
        ot_next = outer_top + next_idx

        i_list.append(ob_curr)
        j_list.append(ob_next)
        k_list.append(ot_curr)

        i_list.append(ob_next)
        j_list.append(ot_next)
        k_list.append(ot_curr)

    # Inner surface (reversed winding for correct normals)
    for idx in range(n):
        next_idx = (idx + 1) % n
        ib_curr = inner_bottom + idx
        ib_next = inner_bottom + next_idx
        it_curr = inner_top + idx
        it_next = inner_top + next_idx

        i_list.append(ib_curr)
        j_list.append(it_curr)
        k_list.append(ib_next)

        i_list.append(ib_next)
        j_list.append(it_curr)
        k_list.append(it_next)

    # Top annular face
    for idx in range(n):
        next_idx = (idx + 1) % n
        ot_curr = outer_top + idx
        ot_next = outer_top + next_idx
        it_curr = inner_top + idx
        it_next = inner_top + next_idx

        i_list.append(ot_curr)
        j_list.append(ot_next)
        k_list.append(it_curr)

        i_list.append(ot_next)
        j_list.append(it_next)
        k_list.append(it_curr)

    # Bottom annular face
    for idx in range(n):
        next_idx = (idx + 1) % n
        ob_curr = outer_bottom + idx
        ob_next = outer_bottom + next_idx
        ib_curr = inner_bottom + idx
        ib_next = inner_bottom + next_idx

        i_list.append(ob_curr)
        j_list.append(ib_curr)
        k_list.append(ob_next)

        i_list.append(ob_next)
        j_list.append(ib_curr)
        k_list.append(ib_next)

    if opacity is None:
        opacity = _extract_opacity_from_color(color)

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i_list,
        j=j_list,
        k=k_list,
        color=color,
        opacity=opacity,
        name=name,
        hoverinfo="name",
        flatshading=True,
        showlegend=True,
    )


def _extract_opacity_from_color(color: str) -> float:
    """Extract opacity from RGBA color string.

    Args:
        color: Color string like "rgba(r, g, b, a)" or "rgb(r, g, b)"

    Returns:
        Opacity value (0-1), defaults to 1.0 if not found
    """
    if color.startswith("rgba"):
        try:
            # Extract the alpha value from "rgba(r, g, b, a)"
            parts = color.replace("rgba(", "").replace(")", "").split(",")
            if len(parts) >= 4:
                return float(parts[3].strip())
        except (ValueError, IndexError):
            pass
    return 1.0


class GeometryBuilder:
    """Build Plotly meshes from DetailedGeometry.

    This class converts the computed layer geometry from Phase 1 into
    Plotly Mesh3d traces for 3D visualization.

    Attributes:
        colors: ColorScheme to use for material colors
    """

    def __init__(self, colors: ColorScheme | None = None) -> None:
        """Initialize builder with color scheme.

        Args:
            colors: ColorScheme to use, defaults to DEFAULT_COLORS
        """
        self.colors = colors or DEFAULT_COLORS

    def build_simplified(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Build simplified view (electrode pairs as grouped blocks).

        For stacked cells: Groups electrode pairs into ~5-10 blocks
        For cylindrical: Shows concentric regions (core, inner winds, outer winds)

        Args:
            geometry: DetailedGeometry from Phase 1

        Returns:
            List of Plotly Mesh3d traces
        """
        traces: list[go.Mesh3d] = []

        if geometry.cell_type in ("pouch", "prismatic"):
            traces.extend(self._build_stacked_simplified(geometry))
        elif geometry.cell_type == "cylindrical":
            traces.extend(self._build_wound_simplified(geometry))

        # Add casing (semi-transparent)
        traces.extend(self._build_casing(geometry, simplified=True))

        return traces

    def build_detailed(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Build detailed view (individual layers).

        Shows every layer with correct material colors.

        Args:
            geometry: DetailedGeometry from Phase 1

        Returns:
            List of Plotly Mesh3d traces
        """
        traces: list[go.Mesh3d] = []

        if geometry.cell_type in ("pouch", "prismatic"):
            traces.extend(self._build_stacked_detailed(geometry))
        elif geometry.cell_type == "cylindrical":
            traces.extend(self._build_wound_detailed(geometry))

        # Add casing
        traces.extend(self._build_casing(geometry, simplified=False))

        return traces

    def _build_stacked_simplified(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Simplified stacked cell: grouped electrode pairs."""
        traces: list[go.Mesh3d] = []
        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        # Cell internal dimensions
        wall = ext.wall_thickness_mm or 0.5
        x_size = (ext.length_mm or 100.0) - 2 * wall
        y_size = (ext.width_mm or 100.0) - 2 * wall

        # Group layers into electrode pairs for simplified view
        # Show ~5-10 blocks regardless of actual layer count
        num_pairs = stack.num_electrode_pairs
        target_blocks = 8
        group_size = max(1, num_pairs // target_blocks)

        # Estimate thickness per electrode pair
        pair_thickness_um = self._estimate_pair_thickness(geometry)

        z = 0.0
        block_colors = [
            self.colors.electrode_pair,
            "rgba(90, 90, 110, 0.7)",  # Slightly different shade for alternating
        ]

        for block_idx, pair_start in enumerate(range(0, num_pairs, group_size)):
            pair_end = min(pair_start + group_size, num_pairs)
            actual_pairs = pair_end - pair_start

            # Calculate thickness for this group
            group_thickness_mm = (pair_thickness_um * actual_pairs) / 1000.0

            # Alternate colors for visibility
            color = block_colors[block_idx % len(block_colors)]

            traces.append(
                create_box_mesh(
                    x_min=-x_size / 2,
                    x_max=x_size / 2,
                    y_min=-y_size / 2,
                    y_max=y_size / 2,
                    z_min=z,
                    z_max=z + group_thickness_mm,
                    color=color,
                    name=f"Electrode pairs {pair_start + 1}-{pair_end}",
                )
            )

            z += group_thickness_mm

        return traces

    def _build_stacked_detailed(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Detailed stacked cell: individual layers."""
        traces: list[go.Mesh3d] = []
        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        wall = ext.wall_thickness_mm or 0.5
        x_size = (ext.length_mm or 100.0) - 2 * wall
        y_size = (ext.width_mm or 100.0) - 2 * wall

        # Coating zones for accurate X/Y sizing
        zones = geometry.coating_zones

        # Track layer counts for naming
        layer_counts: dict[str, int] = {}

        for layer in stack.layers:
            # Determine color based on layer type
            color = self._get_layer_color(layer, geometry.chemistry)

            # Convert um to mm
            z_min = layer.z_bottom_um / 1000.0
            z_max = (layer.z_bottom_um + layer.thickness_um) / 1000.0

            # Adjust X/Y based on layer type (anode has overhang over cathode)
            x_half, y_half = x_size / 2, y_size / 2

            if zones:
                # Use actual coating zone dimensions if available
                if "anode" in layer.layer_type.value:
                    x_half = zones.anode_coated.width_mm / 2 if zones.anode_coated else x_half
                    y_half = zones.anode_coated.height_mm / 2 if zones.anode_coated else y_half
                elif "cathode" in layer.layer_type.value:
                    x_half = zones.cathode_coated.width_mm / 2 if zones.cathode_coated else x_half
                    y_half = zones.cathode_coated.height_mm / 2 if zones.cathode_coated else y_half
                elif "separator" in layer.layer_type.value:
                    x_half = zones.separator_sheet.width_mm / 2 if zones.separator_sheet else x_half + 2.0
                    y_half = zones.separator_sheet.height_mm / 2 if zones.separator_sheet else y_half + 2.0
            else:
                # Default overhangs
                if "anode" in layer.layer_type.value:
                    x_half += 0.5
                    y_half += 0.5
                elif "separator" in layer.layer_type.value:
                    x_half += 1.0
                    y_half += 1.0

            # Count layers for unique names
            layer_type_str = layer.layer_type.value
            layer_counts[layer_type_str] = layer_counts.get(layer_type_str, 0) + 1
            layer_num = layer_counts[layer_type_str]

            traces.append(
                create_box_mesh(
                    x_min=-x_half,
                    x_max=x_half,
                    y_min=-y_half,
                    y_max=y_half,
                    z_min=z_min,
                    z_max=z_max,
                    color=color,
                    name=f"{layer.layer_type.value} #{layer_num} ({layer.material})",
                )
            )

        return traces

    def _build_wound_simplified(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Simplified cylindrical cell: colored layer bands."""
        traces: list[go.Mesh3d] = []
        winding: WindingGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        height = ext.height_mm or 65.0

        r_mandrel = winding.mandrel_diameter_mm / 2
        r_outer = winding.outer_diameter_mm / 2
        total_thickness = r_outer - r_mandrel

        # Core void (if hollow)
        if r_mandrel > 0.5:
            traces.append(
                create_cylinder_mesh(
                    r_inner=0,
                    r_outer=r_mandrel,
                    z_min=0,
                    z_max=height,
                    color="rgba(40, 40, 50, 0.5)",
                    name="Core void",
                    opacity=0.5,
                )
            )

        # Layer pattern and fractions (simplified to 5 main layer types)
        layer_configs = [
            ("Anode collector", self.colors.anode_collector, 0.08),
            ("Anode coating", self.colors.anode_coating, 0.25),
            ("Separator", self.colors.separator, 0.10),
            ("Cathode coating", self.colors.get_cathode_color(geometry.chemistry), 0.32),
            ("Cathode collector", self.colors.cathode_collector, 0.10),
            ("Anode coating", self.colors.anode_coating, 0.15),
        ]

        current_r = r_mandrel
        for name, color, frac in layer_configs:
            band_thickness = total_thickness * frac
            next_r = current_r + band_thickness

            traces.append(
                create_cylinder_mesh(
                    r_inner=current_r,
                    r_outer=next_r,
                    z_min=0,
                    z_max=height,
                    color=color,
                    name=name,
                )
            )
            current_r = next_r

        return traces

    def _build_wound_detailed(
        self,
        geometry: DetailedGeometry,
    ) -> list[go.Mesh3d]:
        """Detailed cylindrical cell: colored layer bands with finer resolution."""
        traces: list[go.Mesh3d] = []
        winding: WindingGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        height = ext.height_mm or 65.0

        r_mandrel = winding.mandrel_diameter_mm / 2
        r_outer = winding.outer_diameter_mm / 2
        total_thickness = r_outer - r_mandrel

        # Core void if present
        if r_mandrel > 0.5:
            traces.append(
                create_cylinder_mesh(
                    r_inner=0,
                    r_outer=r_mandrel,
                    z_min=0,
                    z_max=height,
                    color="rgba(40, 40, 50, 0.5)",
                    name="Core void",
                    opacity=0.5,
                )
            )

        # Layer pattern and fractions (full jellyroll layer sequence)
        # Represents: anode_cc | anode | sep | cathode | cathode_cc | cathode | sep | anode
        layer_configs = [
            ("Anode collector", self.colors.anode_collector, 0.03),
            ("Anode coating", self.colors.anode_coating, 0.22),
            ("Separator", self.colors.separator, 0.05),
            ("Cathode coating", self.colors.get_cathode_color(geometry.chemistry), 0.22),
            ("Cathode collector", self.colors.cathode_collector, 0.06),
            ("Cathode coating", self.colors.get_cathode_color(geometry.chemistry), 0.22),
            ("Separator", self.colors.separator, 0.05),
            ("Anode coating", self.colors.anode_coating, 0.15),
        ]

        current_r = r_mandrel
        for name, color, frac in layer_configs:
            band_thickness = total_thickness * frac
            next_r = current_r + band_thickness

            traces.append(
                create_cylinder_mesh(
                    r_inner=current_r,
                    r_outer=next_r,
                    z_min=0,
                    z_max=height,
                    color=color,
                    name=name,
                )
            )
            current_r = next_r

        return traces

    def _build_casing(
        self,
        geometry: DetailedGeometry,
        simplified: bool,
    ) -> list[go.Mesh3d]:
        """Build transparent casing around cell."""
        traces: list[go.Mesh3d] = []
        ext = geometry.external_geometry

        if geometry.cell_type in ("pouch", "prismatic"):
            # Box casing
            wall = ext.wall_thickness_mm or 0.5

            # Determine cell height (thickness for pouch, height for prismatic)
            cell_height = ext.thickness_mm if geometry.cell_type == "pouch" else ext.height_mm
            cell_height = cell_height or 20.0

            # Use different colors and opacity for pouch vs prismatic
            if geometry.cell_type == "pouch":
                casing_color = self.colors.pouch_film
                opacity = 0.2
            else:
                casing_color = self.colors.can_wall
                opacity = 0.25

            # Outer casing (transparent)
            traces.append(
                create_box_mesh(
                    x_min=-(ext.length_mm or 100.0) / 2,
                    x_max=(ext.length_mm or 100.0) / 2,
                    y_min=-(ext.width_mm or 100.0) / 2,
                    y_max=(ext.width_mm or 100.0) / 2,
                    z_min=-wall,
                    z_max=cell_height + wall,
                    color=casing_color,
                    name="Casing",
                    opacity=opacity,
                )
            )

        elif geometry.cell_type == "cylindrical":
            # Cylindrical can
            wall = ext.wall_thickness_mm or 0.5
            r_outer = (ext.diameter_mm or 46.0) / 2
            height = ext.height_mm or 65.0

            traces.append(
                create_cylinder_mesh(
                    r_inner=r_outer - wall,
                    r_outer=r_outer,
                    z_min=0,
                    z_max=height,
                    color=self.colors.can_wall,
                    name="Can wall",
                    opacity=0.3,
                )
            )

        return traces

    def _get_layer_color(self, layer: Layer, chemistry: str) -> str:
        """Get color for layer based on type and chemistry."""
        return self.colors.get_layer_color(layer.layer_type.value, chemistry)

    def _estimate_pair_thickness(self, geometry: DetailedGeometry) -> float:
        """Estimate thickness of one electrode pair in um.

        Args:
            geometry: DetailedGeometry with layer stack

        Returns:
            Estimated thickness per electrode pair in micrometers
        """
        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        if hasattr(stack, "layers") and stack.layers and stack.num_electrode_pairs > 0:
            return stack.total_thickness_um / stack.num_electrode_pairs
        return 300.0  # Default fallback


# Tab visualization colors by material
TAB_MATERIAL_COLORS: dict[str, str] = {
    "aluminum": "rgba(192, 192, 192, 0.9)",  # Silver
    "copper": "rgba(184, 115, 51, 0.9)",  # Copper
    "ni_cu": "rgba(180, 180, 180, 0.9)",  # Nickel-plated
    "nickel": "rgba(160, 160, 170, 0.9)",  # Nickel
}


def create_tab_meshes(
    tab_geometry: TabGeometry,
    colors: ColorScheme | None = None,
) -> list[go.Mesh3d]:
    """Create Plotly meshes for tab geometry.

    Args:
        tab_geometry: TabGeometry with tab positions
        colors: Color scheme for materials (unused, kept for interface consistency)

    Returns:
        List of Plotly Mesh3d traces
    """
    meshes: list[go.Mesh3d] = []

    # Create meshes for positive tabs
    for i, tab in enumerate(tab_geometry.positive_tabs):
        color = TAB_MATERIAL_COLORS.get(tab.material.value, "rgba(192, 192, 192, 0.9)")
        mesh = _create_tab_strip_mesh(tab, color, f"Pos_Tab_{i + 1}")
        meshes.append(mesh)

    # Create meshes for negative tabs
    for i, tab in enumerate(tab_geometry.negative_tabs):
        color = TAB_MATERIAL_COLORS.get(tab.material.value, "rgba(184, 115, 51, 0.9)")
        mesh = _create_tab_strip_mesh(tab, color, f"Neg_Tab_{i + 1}")
        meshes.append(mesh)

    # Create busbar meshes if present
    if tab_geometry.positive_busbar:
        mesh = _create_busbar_mesh(
            tab_geometry.positive_busbar, "rgba(192, 192, 192, 0.8)"
        )
        meshes.append(mesh)

    if tab_geometry.negative_busbar:
        mesh = _create_busbar_mesh(
            tab_geometry.negative_busbar, "rgba(184, 115, 51, 0.8)"
        )
        meshes.append(mesh)

    # Create terminal meshes
    if tab_geometry.positive_terminal:
        mesh = _create_terminal_mesh(
            tab_geometry.positive_terminal, "rgba(192, 192, 192, 1.0)"
        )
        meshes.append(mesh)

    if tab_geometry.negative_terminal:
        mesh = _create_terminal_mesh(
            tab_geometry.negative_terminal, "rgba(160, 160, 170, 1.0)"
        )
        meshes.append(mesh)

    return meshes


def _create_tab_strip_mesh(tab: TabStrip, color: str, name: str) -> go.Mesh3d:
    """Create mesh for single tab strip.

    Args:
        tab: TabStrip with position and dimensions
        color: RGBA color string
        name: Display name for the mesh

    Returns:
        Plotly Mesh3d trace
    """
    p = tab.attachment_point

    # Determine tab orientation based on exit direction
    if tab.exit_direction in ("x+", "x-"):
        # Tab extends in X direction
        sign = 1 if tab.exit_direction == "x+" else -1
        x_vals = [p.x, p.x + sign * tab.strip_length_mm]
        half_w = tab.strip_width_mm / 2
        half_t = tab.strip_thickness_mm / 2

        vertices = [
            (x_vals[0], p.y - half_w, p.z - half_t),
            (x_vals[0], p.y + half_w, p.z - half_t),
            (x_vals[0], p.y + half_w, p.z + half_t),
            (x_vals[0], p.y - half_w, p.z + half_t),
            (x_vals[1], p.y - half_w, p.z - half_t),
            (x_vals[1], p.y + half_w, p.z - half_t),
            (x_vals[1], p.y + half_w, p.z + half_t),
            (x_vals[1], p.y - half_w, p.z + half_t),
        ]
    elif tab.exit_direction in ("z+", "z-"):
        # Tab extends in Z direction
        sign = 1 if tab.exit_direction == "z+" else -1
        z_vals = [p.z, p.z + sign * tab.strip_length_mm]
        half_w = tab.strip_width_mm / 2
        half_t = tab.strip_thickness_mm / 2

        vertices = [
            (p.x - half_w, p.y - half_t, z_vals[0]),
            (p.x + half_w, p.y - half_t, z_vals[0]),
            (p.x + half_w, p.y + half_t, z_vals[0]),
            (p.x - half_w, p.y + half_t, z_vals[0]),
            (p.x - half_w, p.y - half_t, z_vals[1]),
            (p.x + half_w, p.y - half_t, z_vals[1]),
            (p.x + half_w, p.y + half_t, z_vals[1]),
            (p.x - half_w, p.y + half_t, z_vals[1]),
        ]
    else:
        # Default: Y direction
        sign = 1 if tab.exit_direction == "y+" else -1
        y_vals = [p.y, p.y + sign * tab.strip_length_mm]
        half_w = tab.strip_width_mm / 2
        half_t = tab.strip_thickness_mm / 2

        vertices = [
            (p.x - half_w, y_vals[0], p.z - half_t),
            (p.x + half_w, y_vals[0], p.z - half_t),
            (p.x + half_w, y_vals[0], p.z + half_t),
            (p.x - half_w, y_vals[0], p.z + half_t),
            (p.x - half_w, y_vals[1], p.z - half_t),
            (p.x + half_w, y_vals[1], p.z - half_t),
            (p.x + half_w, y_vals[1], p.z + half_t),
            (p.x - half_w, y_vals[1], p.z + half_t),
        ]

    x, y, z = zip(*vertices)

    # Box faces (12 triangles for 6 faces)
    i = [0, 0, 4, 4, 0, 1, 2, 3, 0, 1, 5, 4]
    j = [1, 2, 5, 6, 4, 5, 6, 7, 3, 2, 6, 7]
    k = [2, 3, 6, 7, 1, 2, 3, 0, 4, 6, 2, 3]

    return go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        color=color,
        name=name,
        showlegend=True,
        hoverinfo="name",
        flatshading=True,
    )


def _create_busbar_mesh(busbar: Busbar, color: str) -> go.Mesh3d:
    """Create mesh for busbar.

    Args:
        busbar: Busbar with position and dimensions
        color: RGBA color string

    Returns:
        Plotly Mesh3d trace
    """
    s = busbar.start_point
    e = busbar.end_point

    half_w = busbar.width_mm / 2
    half_t = busbar.thickness_mm / 2

    # Create box from start to end
    vertices = [
        (s.x, s.y - half_w, s.z - half_t),
        (s.x, s.y + half_w, s.z - half_t),
        (s.x, s.y + half_w, s.z + half_t),
        (s.x, s.y - half_w, s.z + half_t),
        (e.x, e.y - half_w, e.z - half_t),
        (e.x, e.y + half_w, e.z - half_t),
        (e.x, e.y + half_w, e.z + half_t),
        (e.x, e.y - half_w, e.z + half_t),
    ]

    x, y, z = zip(*vertices)
    i = [0, 0, 4, 4, 0, 1, 2, 3, 0, 1, 5, 4]
    j = [1, 2, 5, 6, 4, 5, 6, 7, 3, 2, 6, 7]
    k = [2, 3, 6, 7, 1, 2, 3, 0, 4, 6, 2, 3]

    return go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        color=color,
        name=f"Busbar ({busbar.polarity.value})",
        showlegend=True,
        hoverinfo="name",
        flatshading=True,
    )


def _create_terminal_mesh(terminal: TerminalPost, color: str) -> go.Mesh3d:
    """Create mesh for terminal post.

    Args:
        terminal: TerminalPost with position and dimensions
        color: RGBA color string

    Returns:
        Plotly Mesh3d trace
    """
    p = terminal.position

    if terminal.diameter_mm:
        # Cylindrical terminal
        r = terminal.diameter_mm / 2
        h = terminal.height_mm
        n_segments = 16

        angles = np.linspace(0, 2 * np.pi, n_segments, endpoint=False)

        # Bottom circle vertices
        x_bottom = [p.x + r * np.cos(a) for a in angles]
        y_bottom = [p.y + r * np.sin(a) for a in angles]
        z_bottom = [p.z] * n_segments

        # Top circle vertices
        x_top = [p.x + r * np.cos(a) for a in angles]
        y_top = [p.y + r * np.sin(a) for a in angles]
        z_top = [p.z + h] * n_segments

        # Center points for top and bottom caps
        x_list = list(x_bottom) + list(x_top) + [p.x, p.x]
        y_list = list(y_bottom) + list(y_top) + [p.y, p.y]
        z_list = list(z_bottom) + list(z_top) + [p.z, p.z + h]

        # Create triangular faces
        i_list: list[int] = []
        j_list: list[int] = []
        k_list: list[int] = []

        bottom_center = 2 * n_segments
        top_center = 2 * n_segments + 1

        # Bottom cap
        for idx in range(n_segments):
            next_idx = (idx + 1) % n_segments
            i_list.append(bottom_center)
            j_list.append(next_idx)
            k_list.append(idx)

        # Top cap
        for idx in range(n_segments):
            next_idx = (idx + 1) % n_segments
            i_list.append(top_center)
            j_list.append(n_segments + idx)
            k_list.append(n_segments + next_idx)

        # Side faces
        for idx in range(n_segments):
            next_idx = (idx + 1) % n_segments
            # Triangle 1
            i_list.append(idx)
            j_list.append(next_idx)
            k_list.append(n_segments + idx)
            # Triangle 2
            i_list.append(next_idx)
            j_list.append(n_segments + next_idx)
            k_list.append(n_segments + idx)

        return go.Mesh3d(
            x=x_list,
            y=y_list,
            z=z_list,
            i=i_list,
            j=j_list,
            k=k_list,
            color=color,
            name=f"Terminal ({terminal.polarity.value})",
            showlegend=True,
            hoverinfo="name",
            flatshading=True,
        )
    else:
        # Rectangular terminal
        half_w = (terminal.width_mm or 10) / 2
        half_l = (terminal.length_mm or 10) / 2
        h = terminal.height_mm

        vertices = [
            (p.x - half_l, p.y - half_w, p.z),
            (p.x + half_l, p.y - half_w, p.z),
            (p.x + half_l, p.y + half_w, p.z),
            (p.x - half_l, p.y + half_w, p.z),
            (p.x - half_l, p.y - half_w, p.z + h),
            (p.x + half_l, p.y - half_w, p.z + h),
            (p.x + half_l, p.y + half_w, p.z + h),
            (p.x - half_l, p.y + half_w, p.z + h),
        ]

        x, y, z = zip(*vertices)
        i = [0, 0, 4, 4, 0, 1, 2, 3, 0, 1, 5, 4]
        j = [1, 2, 5, 6, 4, 5, 6, 7, 3, 2, 6, 7]
        k = [2, 3, 6, 7, 1, 2, 3, 0, 4, 6, 2, 3]

        return go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color=color,
            name=f"Terminal ({terminal.polarity.value})",
            showlegend=True,
            hoverinfo="name",
            flatshading=True,
        )

