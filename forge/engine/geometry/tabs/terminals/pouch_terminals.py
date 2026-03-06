"""Terminal assembly calculator for pouch cells.

Pouch cells have simpler terminals compared to prismatic or cylindrical:
- Tab extensions serve as terminals (sealed through pouch edge)
- Sealant around tab exit points
- No bolt-style posts (tabs connect directly)
"""

from typing import TYPE_CHECKING

from ..models import Point3D, TabMaterial, TabPolarity
from .models import (
    InsulatorMaterial,
    SealGasket,
    TerminalAssembly,
    TerminalPost,
    TerminalType,
)

if TYPE_CHECKING:
    from ...detailed_geometry import DetailedGeometry


class PouchTerminalCalculator:
    """Calculate terminal assemblies for pouch cells.

    Pouch cells have simple tab extensions that exit through the sealed
    pouch edge. The tabs themselves serve as external terminals.

    Attributes:
        tab_exit_width_mm: Width of tab exit zone
        tab_exit_thickness_mm: Thickness of tab strip
        include_seal_zones: Whether to include seal zones in output
    """

    def __init__(
        self,
        tab_exit_width_mm: float = 40.0,
        tab_exit_thickness_mm: float = 0.4,
        include_seal_zones: bool = True,
    ) -> None:
        """Initialize calculator.

        Args:
            tab_exit_width_mm: Width of tab exit zone
            tab_exit_thickness_mm: Thickness of tab strip
            include_seal_zones: Whether to include seal gaskets
        """
        self.tab_exit_width_mm = tab_exit_width_mm
        self.tab_exit_thickness_mm = tab_exit_thickness_mm
        self.include_seal_zones = include_seal_zones

    def calculate(self, geometry: "DetailedGeometry") -> TerminalAssembly:
        """Calculate terminal assembly for pouch cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TerminalAssembly with pouch-style terminals
        """
        ext = geometry.external_geometry

        length = ext.length_mm or 200.0
        thickness = ext.thickness_mm or ext.height_mm or 10.0

        half_length = length / 2
        thickness / 2

        assembly = TerminalAssembly(cell_type="pouch")

        # Positive terminal (tab exit zone on +X edge)
        pos_gasket = None
        if self.include_seal_zones:
            pos_gasket = SealGasket(
                position=Point3D(half_length, 0, 0),
                width_mm=self.tab_exit_width_mm + 10,
                length_mm=thickness + 4,
                thickness_mm=2.0,
                material=InsulatorMaterial.PFA,
            )

        assembly.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.POST,
            position=Point3D(half_length + 15, 0, 0),
            width_mm=self.tab_exit_width_mm,
            length_mm=self.tab_exit_thickness_mm,
            height_mm=20.0,  # Tab extension length
            material=TabMaterial.ALUMINUM,
            gasket=pos_gasket,
        )

        # Negative terminal (tab exit zone on -X edge)
        neg_gasket = None
        if self.include_seal_zones:
            neg_gasket = SealGasket(
                position=Point3D(-half_length, 0, 0),
                width_mm=self.tab_exit_width_mm + 10,
                length_mm=thickness + 4,
                thickness_mm=2.0,
                material=InsulatorMaterial.PFA,
            )

        assembly.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            terminal_type=TerminalType.POST,
            position=Point3D(-half_length - 15, 0, 0),
            width_mm=self.tab_exit_width_mm,
            length_mm=self.tab_exit_thickness_mm,
            height_mm=20.0,
            material=TabMaterial.NICKEL_PLATED_COPPER,
            gasket=neg_gasket,
        )

        assembly.notes.append("Pouch tabs serve as external terminals")
        assembly.notes.append("Tabs sealed through heat-sealed pouch edge")

        return assembly
