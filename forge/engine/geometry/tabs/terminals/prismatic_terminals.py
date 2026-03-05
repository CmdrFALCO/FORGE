"""Terminal assembly calculator for prismatic cells.

Prismatic cells typically have:
- Bolt-style terminals on top face
- Insulating gaskets around terminals
- Seal rings for environmental protection
- Terminal spacing optimized for busbar connection
"""

from typing import TYPE_CHECKING

from ..models import Point3D, TabMaterial, TabPolarity
from .models import (
    InsulatorMaterial,
    InsulatorRing,
    SealGasket,
    TerminalAssembly,
    TerminalPost,
    TerminalType,
)

if TYPE_CHECKING:
    from ...detailed_geometry import DetailedGeometry


class PrismaticTerminalCalculator:
    """Calculate terminal assemblies for prismatic cells.

    Prismatic cells have bolt-style terminals on the top face, with
    insulating rings to prevent shorting to the casing.

    Attributes:
        terminal_diameter_mm: Terminal post diameter
        terminal_height_mm: Terminal height above casing
        terminal_spacing_ratio: Terminal spacing as fraction of cell length
        include_insulators: Whether to include insulator rings
        include_gaskets: Whether to include seal gaskets
    """

    def __init__(
        self,
        terminal_diameter_mm: float = 12.0,
        terminal_height_mm: float = 10.0,
        terminal_spacing_ratio: float = 0.6,  # Fraction of cell length
        include_insulators: bool = True,
        include_gaskets: bool = True,
    ) -> None:
        """Initialize calculator.

        Args:
            terminal_diameter_mm: Terminal post diameter
            terminal_height_mm: Terminal height above casing
            terminal_spacing_ratio: Terminal spacing as fraction of cell length
            include_insulators: Whether to include insulator rings
            include_gaskets: Whether to include seal gaskets
        """
        self.terminal_diameter_mm = terminal_diameter_mm
        self.terminal_height_mm = terminal_height_mm
        self.terminal_spacing_ratio = terminal_spacing_ratio
        self.include_insulators = include_insulators
        self.include_gaskets = include_gaskets

    def calculate(self, geometry: "DetailedGeometry") -> TerminalAssembly:
        """Calculate terminal assembly for prismatic cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TerminalAssembly with prismatic-style terminals
        """
        ext = geometry.external_geometry

        length = ext.length_mm or 150.0
        width = ext.width_mm or 100.0
        height = ext.thickness_mm or ext.height_mm or 25.0

        half_height = height / 2

        # Terminal positions
        terminal_spacing = length * self.terminal_spacing_ratio
        pos_x = terminal_spacing / 2
        neg_x = -terminal_spacing / 2

        assembly = TerminalAssembly(cell_type="prismatic")

        # Positive terminal (bolt-style)
        pos_insulator = None
        pos_gasket = None

        if self.include_insulators:
            pos_insulator = InsulatorRing(
                position=Point3D(pos_x, 0, half_height),
                outer_diameter_mm=self.terminal_diameter_mm + 8,
                inner_diameter_mm=self.terminal_diameter_mm + 1,
                thickness_mm=2.0,
                material=InsulatorMaterial.PLASTIC,
            )

        if self.include_gaskets:
            pos_gasket = SealGasket(
                position=Point3D(pos_x, 0, half_height - 0.5),
                outer_diameter_mm=self.terminal_diameter_mm + 6,
                inner_diameter_mm=self.terminal_diameter_mm + 0.5,
                thickness_mm=1.0,
                material=InsulatorMaterial.RUBBER,
            )

        assembly.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(pos_x, 0, half_height),
            diameter_mm=self.terminal_diameter_mm,
            height_mm=self.terminal_height_mm,
            thread_diameter_mm=self.terminal_diameter_mm * 0.8,
            thread_pitch_mm=1.5,
            material=TabMaterial.ALUMINUM,
            insulator=pos_insulator,
            gasket=pos_gasket,
        )

        # Negative terminal
        neg_insulator = None
        neg_gasket = None

        if self.include_insulators:
            neg_insulator = InsulatorRing(
                position=Point3D(neg_x, 0, half_height),
                outer_diameter_mm=self.terminal_diameter_mm + 8,
                inner_diameter_mm=self.terminal_diameter_mm + 1,
                thickness_mm=2.0,
                material=InsulatorMaterial.PLASTIC,
            )

        if self.include_gaskets:
            neg_gasket = SealGasket(
                position=Point3D(neg_x, 0, half_height - 0.5),
                outer_diameter_mm=self.terminal_diameter_mm + 6,
                inner_diameter_mm=self.terminal_diameter_mm + 0.5,
                thickness_mm=1.0,
                material=InsulatorMaterial.RUBBER,
            )

        assembly.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(neg_x, 0, half_height),
            diameter_mm=self.terminal_diameter_mm,
            height_mm=self.terminal_height_mm,
            thread_diameter_mm=self.terminal_diameter_mm * 0.8,
            thread_pitch_mm=1.5,
            material=TabMaterial.NICKEL_PLATED_COPPER,
            insulator=neg_insulator,
            gasket=neg_gasket,
        )

        assembly.notes.append(f"Terminal spacing: {terminal_spacing:.1f} mm")
        assembly.notes.append("Bolt-style terminals for busbar connection")

        return assembly
