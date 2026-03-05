"""Header assembly calculator for cylindrical cells.

Cylindrical cell header (top to bottom):
1. Positive cap (button top) - external positive terminal
2. Vent disc - pressure relief
3. CID (Current Interrupt Device) - safety disconnect
4. Top insulator ring - isolates cap from can
5. Gasket - seals header to can

Bottom:
- Can bottom serves as negative terminal
"""

from typing import TYPE_CHECKING

from ..models import Point3D, TabMaterial, TabPolarity
from .models import (
    CurrentInterruptDevice,
    HeaderAssembly,
    InsulatorMaterial,
    InsulatorRing,
    PositiveCap,
    SealGasket,
    TerminalAssembly,
    TerminalPost,
    TerminalType,
    VentDisc,
)

if TYPE_CHECKING:
    from ...detailed_geometry import DetailedGeometry


class CylindricalHeaderCalculator:
    """Calculate header assembly for cylindrical cells.

    Cylindrical cells have a complex header assembly at the top including
    the positive cap, vent disc, CID (safety device), and sealing components.
    The can bottom serves as the negative terminal.

    Attributes:
        include_vent: Whether to include vent disc
        include_cid: Whether to include CID
        include_insulator: Whether to include insulator ring
        button_style: True for button top, False for flat-top
    """

    def __init__(
        self,
        include_vent: bool = True,
        include_cid: bool = True,
        include_insulator: bool = True,
        button_style: bool = True,  # False for flat-top
    ) -> None:
        """Initialize calculator.

        Args:
            include_vent: Whether to include vent disc
            include_cid: Whether to include CID
            include_insulator: Whether to include insulator ring
            button_style: True for button top, False for flat-top
        """
        self.include_vent = include_vent
        self.include_cid = include_cid
        self.include_insulator = include_insulator
        self.button_style = button_style

    def calculate(self, geometry: "DetailedGeometry") -> TerminalAssembly:
        """Calculate header assembly for cylindrical cell.

        Args:
            geometry: DetailedGeometry with cell dimensions

        Returns:
            TerminalAssembly with cylindrical header
        """
        ext = geometry.external_geometry

        diameter = ext.diameter_mm or 46.0
        height = ext.height_mm or 80.0
        wall = ext.wall_thickness_mm or 0.5

        radius = diameter / 2
        inner_radius = radius - wall
        half_height = height / 2

        # Header dimensions (typical proportions)
        header_height = diameter * 0.12  # ~5.5mm for 4680
        cap_height = header_height * 0.4
        vent_thickness = 0.3
        cid_thickness = 0.5
        insulator_thickness = 1.5
        gasket_thickness = 1.0

        assembly = TerminalAssembly(cell_type="cylindrical")

        # Build header assembly
        header = HeaderAssembly(
            cell_diameter_mm=diameter,
            cell_height_mm=height,
            total_height_mm=header_height,
        )

        # Z positions (from top down)
        z_top = half_height
        z_cap_bottom = z_top - cap_height
        z_vent = z_cap_bottom - vent_thickness
        z_cid = z_vent - cid_thickness
        z_insulator = z_cid - insulator_thickness

        # Positive cap
        button_diameter = diameter * 0.3 if self.button_style else None
        button_height = cap_height * 0.5 if self.button_style else None

        header.positive_cap = PositiveCap(
            position=Point3D(0, 0, z_top - cap_height / 2),
            outer_diameter_mm=inner_radius * 2 - 1,  # Slight gap to can
            inner_diameter_mm=inner_radius * 1.4,  # Contact area
            height_mm=cap_height,
            material=TabMaterial.NICKEL,
            button_diameter_mm=button_diameter,
            button_height_mm=button_height,
        )

        # Vent disc
        if self.include_vent:
            header.vent_disc = VentDisc(
                position=Point3D(0, 0, z_vent),
                diameter_mm=inner_radius * 1.6,
                thickness_mm=vent_thickness,
                burst_pressure_mpa=1.5,  # Typical value
            )

        # CID
        if self.include_cid:
            header.cid = CurrentInterruptDevice(
                position=Point3D(0, 0, z_cid),
                diameter_mm=inner_radius * 1.4,
                thickness_mm=cid_thickness,
                trigger_pressure_mpa=1.0,
            )

        # Top insulator
        if self.include_insulator:
            header.top_insulator = InsulatorRing(
                position=Point3D(0, 0, z_insulator),
                outer_diameter_mm=inner_radius * 2,
                inner_diameter_mm=inner_radius * 0.6,
                thickness_mm=insulator_thickness,
                material=InsulatorMaterial.PLASTIC,
            )

        # Gasket (seals header to can)
        header.gasket = SealGasket(
            position=Point3D(0, 0, z_top - header_height + gasket_thickness / 2),
            outer_diameter_mm=diameter,
            inner_diameter_mm=inner_radius * 2 - 2,
            thickness_mm=gasket_thickness,
            material=InsulatorMaterial.RUBBER,
        )

        assembly.header_assembly = header

        # Positive terminal (cap serves as terminal)
        assembly.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BUTTON,
            position=Point3D(0, 0, z_top),
            diameter_mm=button_diameter or (inner_radius * 2 - 2),
            height_mm=button_height or cap_height,
            material=TabMaterial.NICKEL,
        )

        # Negative terminal (can bottom)
        assembly.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            terminal_type=TerminalType.CAN_BOTTOM,
            position=Point3D(0, 0, -half_height),
            diameter_mm=diameter,
            height_mm=wall,
            material=TabMaterial.NICKEL,
        )

        assembly.can_bottom_thickness_mm = wall

        assembly.notes.append(f"Header height: {header_height:.1f} mm")
        assembly.notes.append(
            "Button-top positive terminal"
            if self.button_style
            else "Flat-top positive terminal"
        )
        if self.include_cid:
            assembly.notes.append("Includes CID safety device")

        return assembly
