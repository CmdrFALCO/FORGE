"""Tab geometry calculator for prismatic cells.

Prismatic cells typically have multiple tab strips from the electrode stack,
internal busbars for current collection, and terminal posts on top.
"""

from typing import TYPE_CHECKING

from .models import (
    DEFAULT_TAB_DIMENSIONS,
    Busbar,
    Point3D,
    TabGeometry,
    TabMaterial,
    TabPolarity,
    TabStrip,
    TerminalPost,
)


if TYPE_CHECKING:
    from ..detailed_geometry import DetailedGeometry


class PrismaticTabCalculator:
    """Calculate tab geometry for prismatic cells.

    Prismatic cells typically have:
    - Multiple tab strips from electrode stack
    - Internal busbars to collect current from tabs
    - Terminal posts on top of cell
    - More complex routing due to rigid aluminum casing

    Common configurations:
    - "top_terminal": Terminals on top face (most common)
    - "side_terminal": Terminals on side face
    """

    def __init__(
        self,
        tabs_per_polarity: int = 4,
        configuration: str = "top_terminal",
        custom_dimensions: dict[str, float] | None = None,
    ) -> None:
        """Initialize calculator.

        Args:
            tabs_per_polarity: Number of tab strips per polarity
            configuration: Terminal arrangement
            custom_dimensions: Override default tab dimensions
        """
        self.tabs_per_polarity = max(2, min(8, tabs_per_polarity))
        self.configuration = configuration

        self.dimensions = DEFAULT_TAB_DIMENSIONS["prismatic"].copy()
        if custom_dimensions:
            self.dimensions.update(custom_dimensions)

    def calculate(self, geometry: "DetailedGeometry") -> TabGeometry:
        """Calculate tab geometry for prismatic cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TabGeometry with calculated tab positions
        """
        ext = geometry.external_geometry

        # Cell dimensions
        length = ext.length_mm or 150.0
        width = ext.width_mm or 100.0
        height = ext.thickness_mm or ext.height_mm or 25.0
        wall = ext.wall_thickness_mm or 1.0

        # Internal dimensions
        internal_length = length - 2 * wall
        internal_width = width - 2 * wall

        # Stack dimensions
        stack_thickness = geometry.total_stack_thickness_mm()

        # Half dimensions
        half_length = length / 2
        half_height = height / 2

        tab_geom = TabGeometry(
            cell_type="prismatic",
            configuration=self.configuration,
        )

        # Create tabs along length (distributed along electrode width)
        # Positive tabs on one half, negative on other
        tab_geom.positive_tabs = self._create_distributed_tabs(
            polarity=TabPolarity.POSITIVE,
            length=internal_length,
            width=internal_width,
            stack_thickness=stack_thickness,
            z_center=0,
            x_region=(0, internal_length / 2 - 10),  # First half of cell
        )

        tab_geom.negative_tabs = self._create_distributed_tabs(
            polarity=TabPolarity.NEGATIVE,
            length=internal_length,
            width=internal_width,
            stack_thickness=stack_thickness,
            z_center=0,
            x_region=(-internal_length / 2 + 10, 0),  # Second half of cell
        )

        # Create busbars to collect from tabs
        tab_geom.positive_busbar = self._create_busbar(
            polarity=TabPolarity.POSITIVE,
            tabs=tab_geom.positive_tabs,
            cell_height=height,
            cell_width=width,
        )

        tab_geom.negative_busbar = self._create_busbar(
            polarity=TabPolarity.NEGATIVE,
            tabs=tab_geom.negative_tabs,
            cell_height=height,
            cell_width=width,
        )

        # Create terminal posts on top
        terminal_spacing = length * 0.6
        tab_geom.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            position=Point3D(terminal_spacing / 2, 0, half_height),
            diameter_mm=15.0,
            height_mm=8.0,
            material=TabMaterial.ALUMINUM,
        )

        tab_geom.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            position=Point3D(-terminal_spacing / 2, 0, half_height),
            diameter_mm=15.0,
            height_mm=8.0,
            material=TabMaterial.NICKEL_PLATED_COPPER,
        )

        return tab_geom

    def _create_distributed_tabs(
        self,
        polarity: TabPolarity,
        length: float,
        width: float,
        stack_thickness: float,
        z_center: float,
        x_region: tuple[float, float],
    ) -> list[TabStrip]:
        """Create tabs distributed along electrode.

        Args:
            polarity: Tab polarity
            length: Internal cell length
            width: Internal cell width
            stack_thickness: Electrode stack thickness
            z_center: Z center position
            x_region: (x_start, x_end) region for tab distribution

        Returns:
            List of TabStrip objects
        """
        tabs = []
        material = (
            TabMaterial.ALUMINUM
            if polarity == TabPolarity.POSITIVE
            else TabMaterial.NICKEL_PLATED_COPPER
        )

        # Distribute tabs within x_region
        x_start, x_end = x_region
        x_span = x_end - x_start

        if self.tabs_per_polarity == 1:
            x_positions = [(x_start + x_end) / 2]
        else:
            spacing = x_span / (self.tabs_per_polarity + 1)
            x_positions = [
                x_start + spacing * (i + 1) for i in range(self.tabs_per_polarity)
            ]

        for x_pos in x_positions:
            tab = TabStrip(
                polarity=polarity,
                material=material,
                attachment_point=Point3D(x_pos, 0, z_center),
                attachment_width_mm=self.dimensions["attachment_width"],
                attachment_height_mm=stack_thickness,
                strip_width_mm=self.dimensions["strip_width"],
                strip_thickness_mm=self.dimensions["strip_thickness"],
                strip_length_mm=self.dimensions["strip_length"],
                exit_direction="z+",
                connects_to="busbar",
            )
            tabs.append(tab)

        return tabs

    def _create_busbar(
        self,
        polarity: TabPolarity,
        tabs: list[TabStrip],
        cell_height: float,
        cell_width: float,
    ) -> Busbar | None:
        """Create busbar connecting tabs to terminal.

        Args:
            polarity: Busbar polarity
            tabs: List of tabs to connect
            cell_height: Total cell height
            cell_width: Total cell width

        Returns:
            Busbar object or None if no tabs
        """
        if not tabs:
            return None

        material = (
            TabMaterial.ALUMINUM
            if polarity == TabPolarity.POSITIVE
            else TabMaterial.NICKEL_PLATED_COPPER
        )

        # Busbar runs along top of cell, connecting all tabs
        x_positions = [t.attachment_point.x for t in tabs]
        x_min, x_max = min(x_positions), max(x_positions)

        z_top = cell_height / 2 - 5  # Below terminal

        busbar = Busbar(
            polarity=polarity,
            material=material,
            start_point=Point3D(x_min - 5, 0, z_top),
            end_point=Point3D(x_max + 5, 0, z_top),
            width_mm=self.dimensions["busbar_width"],
            thickness_mm=self.dimensions["busbar_thickness"],
            tab_connection_points=[Point3D(t.attachment_point.x, 0, z_top) for t in tabs],
        )

        return busbar
