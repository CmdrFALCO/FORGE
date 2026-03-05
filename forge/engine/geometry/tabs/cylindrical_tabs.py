"""Tab geometry calculator for cylindrical cells.

Cylindrical cells have two main configurations:
1. Traditional (tabbed): Single tab per electrode wound into jellyroll
2. Tabless (Tesla 4680 style): Continuous foil connection with laser-welded contacts
"""

import math
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


class CylindricalTabCalculator:
    """Calculate tab geometry for cylindrical cells.

    Cylindrical cells have two main configurations:

    1. Traditional (tabbed):
       - Single tab per electrode wound into jellyroll
       - Tabs route to header (+) and can bottom (-)

    2. Tabless (Tesla 4680 style):
       - Continuous foil connection, no discrete tabs
       - Foil extends to both ends
       - Laser-welded to current collectors
       - Represented as annular contact regions
    """

    def __init__(
        self,
        configuration: str = "tabless",
        custom_dimensions: dict[str, float] | None = None,
    ) -> None:
        """Initialize calculator.

        Args:
            configuration: "traditional" or "tabless"
            custom_dimensions: Override default tab dimensions
        """
        self.configuration = configuration

        self.dimensions = DEFAULT_TAB_DIMENSIONS["cylindrical"].copy()
        if custom_dimensions:
            self.dimensions.update(custom_dimensions)

    def calculate(self, geometry: "DetailedGeometry") -> TabGeometry:
        """Calculate tab geometry for cylindrical cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TabGeometry with calculated tab positions
        """
        ext = geometry.external_geometry

        # Cell dimensions
        diameter = ext.diameter_mm or 46.0
        height = ext.height_mm or 80.0
        wall = ext.wall_thickness_mm or 0.5

        radius = diameter / 2
        inner_radius = radius - wall
        half_height = height / 2

        tab_geom = TabGeometry(
            cell_type="cylindrical",
            configuration=self.configuration,
        )

        if self.configuration == "tabless":
            tab_geom = self._calculate_tabless(
                tab_geom, radius, inner_radius, height, half_height
            )
        else:
            tab_geom = self._calculate_traditional(
                tab_geom, radius, inner_radius, height, half_height
            )

        return tab_geom

    def _calculate_tabless(
        self,
        tab_geom: TabGeometry,
        radius: float,
        inner_radius: float,
        height: float,
        half_height: float,
    ) -> TabGeometry:
        """Calculate tabless (4680-style) geometry.

        In tabless design:
        - Cathode foil extends to top, welded to positive cap
        - Anode foil extends to bottom, welded to can
        - No discrete tabs, but we represent the contact regions

        Args:
            tab_geom: TabGeometry to populate
            radius: Outer cell radius
            inner_radius: Inner radius (after wall)
            height: Cell height
            half_height: Half of cell height

        Returns:
            Updated TabGeometry
        """
        # Estimate jellyroll dimensions from geometry
        mandrel_radius = 2.5  # Typical mandrel
        jellyroll_radius = inner_radius - 1.0  # Gap to can wall

        # Positive contact (top) - annular ring
        # Represented as multiple "virtual tabs" around circumference
        num_contact_points = 8
        for i in range(num_contact_points):
            angle = 2 * math.pi * i / num_contact_points
            x = (jellyroll_radius * 0.7) * math.cos(angle)
            y = (jellyroll_radius * 0.7) * math.sin(angle)

            tab = TabStrip(
                polarity=TabPolarity.POSITIVE,
                material=TabMaterial.ALUMINUM,
                attachment_point=Point3D(x, y, half_height - 3),
                attachment_width_mm=5.0,
                attachment_height_mm=2.0,
                strip_width_mm=3.0,
                strip_thickness_mm=0.015,  # Foil thickness
                strip_length_mm=3.0,
                exit_direction="z+",
                connects_to="terminal",
            )
            tab_geom.positive_tabs.append(tab)

        # Negative contact (bottom) - annular ring
        for i in range(num_contact_points):
            angle = 2 * math.pi * i / num_contact_points
            x = (jellyroll_radius * 0.7) * math.cos(angle)
            y = (jellyroll_radius * 0.7) * math.sin(angle)

            tab = TabStrip(
                polarity=TabPolarity.NEGATIVE,
                material=TabMaterial.COPPER,
                attachment_point=Point3D(x, y, -half_height + 3),
                attachment_width_mm=5.0,
                attachment_height_mm=2.0,
                strip_width_mm=3.0,
                strip_thickness_mm=0.010,  # Cu foil thickness
                strip_length_mm=3.0,
                exit_direction="z-",
                connects_to="can",
            )
            tab_geom.negative_tabs.append(tab)

        # Terminal posts
        tab_geom.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            position=Point3D(0, 0, half_height),
            diameter_mm=radius * 0.6,
            height_mm=2.0,
            material=TabMaterial.ALUMINUM,
        )

        tab_geom.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            position=Point3D(0, 0, -half_height),
            diameter_mm=radius * 2,  # Can bottom
            height_mm=0.8,
            material=TabMaterial.NICKEL,
        )

        tab_geom.notes.append("Tabless design: continuous foil contact")
        tab_geom.notes.append("Virtual tabs represent laser-weld contact regions")

        return tab_geom

    def _calculate_traditional(
        self,
        tab_geom: TabGeometry,
        radius: float,
        inner_radius: float,
        height: float,
        half_height: float,
    ) -> TabGeometry:
        """Calculate traditional tabbed geometry.

        Args:
            tab_geom: TabGeometry to populate
            radius: Outer cell radius
            inner_radius: Inner radius (after wall)
            height: Cell height
            half_height: Half of cell height

        Returns:
            Updated TabGeometry
        """
        # Single positive tab wound in jellyroll
        tab_geom.positive_tabs.append(
            TabStrip(
                polarity=TabPolarity.POSITIVE,
                material=TabMaterial.ALUMINUM,
                attachment_point=Point3D(0, inner_radius * 0.5, 0),
                attachment_width_mm=self.dimensions["strip_width"],
                attachment_height_mm=height * 0.8,
                strip_width_mm=self.dimensions["strip_width"],
                strip_thickness_mm=self.dimensions["strip_thickness"],
                strip_length_mm=self.dimensions["strip_length"],
                exit_direction="z+",
                connects_to="terminal",
            )
        )

        # Single negative tab wound in jellyroll
        tab_geom.negative_tabs.append(
            TabStrip(
                polarity=TabPolarity.NEGATIVE,
                material=TabMaterial.NICKEL_PLATED_COPPER,
                attachment_point=Point3D(0, -inner_radius * 0.5, 0),
                attachment_width_mm=self.dimensions["strip_width"],
                attachment_height_mm=height * 0.8,
                strip_width_mm=self.dimensions["strip_width"],
                strip_thickness_mm=self.dimensions["strip_thickness"],
                strip_length_mm=self.dimensions["strip_length"],
                exit_direction="z-",
                connects_to="can",
            )
        )

        # Terminals
        tab_geom.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            position=Point3D(0, 0, half_height),
            diameter_mm=5.0,
            height_mm=2.0,
        )

        tab_geom.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            position=Point3D(0, 0, -half_height),
            diameter_mm=radius * 2,
            height_mm=0.8,
        )

        return tab_geom
