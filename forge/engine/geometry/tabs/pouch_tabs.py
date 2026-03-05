"""Tab geometry calculator for pouch cells.

Pouch cells typically have tab strips extending from opposite edges of the
electrode stack, with tabs exiting through heat-sealed edges.
"""

from typing import TYPE_CHECKING

from .models import (
    DEFAULT_TAB_DIMENSIONS,
    Point3D,
    TabGeometry,
    TabMaterial,
    TabPolarity,
    TabStrip,
    TerminalPost,
)


if TYPE_CHECKING:
    from ..detailed_geometry import DetailedGeometry


class PouchTabCalculator:
    """Calculate tab geometry for pouch cells.

    Pouch cells typically have:
    - Tab strips extending from opposite edges of the electrode stack
    - Multiple tabs per polarity (2-4 typical) for current distribution
    - Tabs exit through heat-sealed edges
    - No internal busbars (tabs go directly to external connection)

    Common configurations:
    - "standard": Tabs on opposite short edges (positive one side, negative other)
    - "same_side": All tabs on same edge (less common)
    - "staggered": Tabs at corners for better current distribution
    """

    def __init__(
        self,
        tabs_per_polarity: int = 2,
        configuration: str = "standard",
        custom_dimensions: dict[str, float] | None = None,
    ) -> None:
        """Initialize calculator.

        Args:
            tabs_per_polarity: Number of tab strips per polarity (1-4)
            configuration: Tab arrangement ("standard", "same_side", "staggered")
            custom_dimensions: Override default tab dimensions
        """
        self.tabs_per_polarity = max(1, min(4, tabs_per_polarity))
        self.configuration = configuration

        # Merge custom dimensions with defaults
        self.dimensions = DEFAULT_TAB_DIMENSIONS["pouch"].copy()
        if custom_dimensions:
            self.dimensions.update(custom_dimensions)

    def calculate(self, geometry: "DetailedGeometry") -> TabGeometry:
        """Calculate tab geometry for pouch cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TabGeometry with calculated tab positions
        """
        ext = geometry.external_geometry

        # Cell dimensions (centered at origin)
        length = ext.length_mm or 200.0
        width = ext.width_mm or 150.0
        thickness = ext.thickness_mm or ext.height_mm or 10.0

        # Stack dimensions
        stack_thickness = geometry.total_stack_thickness_mm()

        # Half dimensions for centering
        half_length = length / 2
        half_width = width / 2

        # Create tab geometry
        tab_geom = TabGeometry(
            cell_type="pouch",
            configuration=self.configuration,
        )

        # Calculate tab positions based on configuration
        if self.configuration == "standard":
            # Positive tabs on +X edge, negative on -X edge
            tab_geom.positive_tabs = self._create_edge_tabs(
                polarity=TabPolarity.POSITIVE,
                edge_x=half_length,
                edge_sign=1,
                width=width,
                stack_thickness=stack_thickness,
            )
            tab_geom.negative_tabs = self._create_edge_tabs(
                polarity=TabPolarity.NEGATIVE,
                edge_x=-half_length,
                edge_sign=-1,
                width=width,
                stack_thickness=stack_thickness,
            )

        elif self.configuration == "same_side":
            # Both polarities on +X edge, offset in Y
            tab_geom.positive_tabs = self._create_edge_tabs(
                polarity=TabPolarity.POSITIVE,
                edge_x=half_length,
                edge_sign=1,
                width=width,
                stack_thickness=stack_thickness,
                y_offset=width * 0.25,
            )
            tab_geom.negative_tabs = self._create_edge_tabs(
                polarity=TabPolarity.NEGATIVE,
                edge_x=half_length,
                edge_sign=1,
                width=width,
                stack_thickness=stack_thickness,
                y_offset=-width * 0.25,
            )

        elif self.configuration == "staggered":
            # Tabs at corners
            tab_geom.positive_tabs = self._create_corner_tabs(
                polarity=TabPolarity.POSITIVE,
                length=length,
                width=width,
                stack_thickness=stack_thickness,
                corners=[(1, 1), (1, -1)],  # +X corners
            )
            tab_geom.negative_tabs = self._create_corner_tabs(
                polarity=TabPolarity.NEGATIVE,
                length=length,
                width=width,
                stack_thickness=stack_thickness,
                corners=[(-1, 1), (-1, -1)],  # -X corners
            )

        # Add terminal posts (simplified - at tab exit points)
        if tab_geom.positive_tabs:
            first_pos = tab_geom.positive_tabs[0]
            sign = 1 if first_pos.exit_direction == "x+" else -1
            tab_geom.positive_terminal = TerminalPost(
                polarity=TabPolarity.POSITIVE,
                position=Point3D(
                    first_pos.attachment_point.x + first_pos.strip_length_mm * sign,
                    first_pos.attachment_point.y,
                    first_pos.attachment_point.z + thickness / 2,
                ),
                width_mm=self.dimensions["strip_width"] * 1.5,
                length_mm=self.dimensions["strip_width"],
                height_mm=3.0,
                material=TabMaterial.ALUMINUM,
            )

        if tab_geom.negative_tabs:
            first_neg = tab_geom.negative_tabs[0]
            sign = -1 if first_neg.exit_direction == "x-" else 1
            tab_geom.negative_terminal = TerminalPost(
                polarity=TabPolarity.NEGATIVE,
                position=Point3D(
                    first_neg.attachment_point.x + first_neg.strip_length_mm * sign,
                    first_neg.attachment_point.y,
                    first_neg.attachment_point.z + thickness / 2,
                ),
                width_mm=self.dimensions["strip_width"] * 1.5,
                length_mm=self.dimensions["strip_width"],
                height_mm=3.0,
                material=TabMaterial.NICKEL_PLATED_COPPER,
            )

        return tab_geom

    def _create_edge_tabs(
        self,
        polarity: TabPolarity,
        edge_x: float,
        edge_sign: int,
        width: float,
        stack_thickness: float,
        y_offset: float = 0.0,
    ) -> list[TabStrip]:
        """Create tabs along one edge.

        Args:
            polarity: Tab polarity
            edge_x: X position of the edge
            edge_sign: Direction sign (1 for +X, -1 for -X)
            width: Cell width (Y dimension)
            stack_thickness: Electrode stack thickness
            y_offset: Y offset for positioning (for same_side config)

        Returns:
            List of TabStrip objects
        """
        tabs = []

        # Material based on polarity
        material = (
            TabMaterial.ALUMINUM
            if polarity == TabPolarity.POSITIVE
            else TabMaterial.NICKEL_PLATED_COPPER
        )

        # Distribute tabs along width
        if self.tabs_per_polarity == 1:
            y_positions = [y_offset]
        else:
            spacing = (width * 0.6) / (self.tabs_per_polarity - 1)
            start_y = -spacing * (self.tabs_per_polarity - 1) / 2 + y_offset
            y_positions = [start_y + i * spacing for i in range(self.tabs_per_polarity)]

        for y_pos in y_positions:
            tab = TabStrip(
                polarity=polarity,
                material=material,
                attachment_point=Point3D(edge_x, y_pos, 0),
                attachment_width_mm=self.dimensions["attachment_width"],
                attachment_height_mm=stack_thickness,
                strip_width_mm=self.dimensions["strip_width"],
                strip_thickness_mm=self.dimensions["strip_thickness"],
                strip_length_mm=self.dimensions["strip_length"],
                exit_direction="x+" if edge_sign > 0 else "x-",
                connects_to="terminal",
            )
            tabs.append(tab)

        return tabs

    def _create_corner_tabs(
        self,
        polarity: TabPolarity,
        length: float,
        width: float,
        stack_thickness: float,
        corners: list[tuple[int, int]],
    ) -> list[TabStrip]:
        """Create tabs at specified corners.

        Args:
            polarity: Tab polarity
            length: Cell length (X dimension)
            width: Cell width (Y dimension)
            stack_thickness: Electrode stack thickness
            corners: List of (x_sign, y_sign) tuples for corner positions

        Returns:
            List of TabStrip objects
        """
        tabs = []
        material = (
            TabMaterial.ALUMINUM
            if polarity == TabPolarity.POSITIVE
            else TabMaterial.NICKEL_PLATED_COPPER
        )

        half_length = length / 2
        half_width = width / 2

        for x_sign, y_sign in corners:
            # Position near corner but not exactly at it
            x_pos = x_sign * (half_length - self.dimensions["strip_width"])
            y_pos = y_sign * (half_width - self.dimensions["strip_width"] * 1.5)

            tab = TabStrip(
                polarity=polarity,
                material=material,
                attachment_point=Point3D(x_pos, y_pos, 0),
                attachment_width_mm=self.dimensions["attachment_width"] * 0.75,
                attachment_height_mm=stack_thickness,
                strip_width_mm=self.dimensions["strip_width"],
                strip_thickness_mm=self.dimensions["strip_thickness"],
                strip_length_mm=self.dimensions["strip_length"],
                exit_direction="x+" if x_sign > 0 else "x-",
                connects_to="terminal",
            )
            tabs.append(tab)

        return tabs
