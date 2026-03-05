"""Geometry data models for FORGE engine.

This module defines dataclasses for cell geometry including:
- SheetGeometry: Base sheet dimensions with symmetric offsets (Pouch)
- PrismaticSheetGeometry: Sheet dimensions with directional offsets (Prismatic)
- PouchPackaging: Pouch cell packaging dimensions
- PrismaticGeometry: Prismatic cell case dimensions
"""

from dataclasses import dataclass


@dataclass
class SheetGeometry:
    """Sheet geometry with symmetric offsets (for Pouch cells).

    Defines cathode dimensions and symmetric offsets for anode and separator.
    All derived dimensions are calculated as properties.

    Attributes:
        cathode_height_mm: Cathode sheet height [mm]
        cathode_width_mm: Cathode sheet width [mm]
        anode_offset_y_mm: Anode overhang in Y direction (per side) [mm]
        anode_offset_x_mm: Anode overhang in X direction (per side) [mm]
        separator_offset_y_mm: Separator overhang beyond anode in Y (per side) [mm]
        separator_offset_x_mm: Separator overhang beyond anode in X (per side) [mm]
        cathode_flag_width_mm: Cathode flag (tab extension) width [mm]
        cathode_flag_height_mm: Cathode flag (tab extension) height [mm]
        anode_flag_width_mm: Anode flag (tab extension) width [mm]
        anode_flag_height_mm: Anode flag (tab extension) height [mm]
    """

    cathode_height_mm: float
    cathode_width_mm: float
    anode_offset_y_mm: float
    anode_offset_x_mm: float
    separator_offset_y_mm: float
    separator_offset_x_mm: float
    # Flag (tab extension) dimensions - optional, default 0 for backward compatibility
    cathode_flag_width_mm: float = 0.0
    cathode_flag_height_mm: float = 0.0
    anode_flag_width_mm: float = 0.0
    anode_flag_height_mm: float = 0.0

    @property
    def cathode_area_cm2(self) -> float:
        """Cathode sheet area [cm²]."""
        return self.cathode_height_mm * self.cathode_width_mm / 100

    @property
    def cathode_flag_area_cm2(self) -> float:
        """Cathode flag (tab extension) area [cm²]."""
        return self.cathode_flag_width_mm * self.cathode_flag_height_mm / 100

    @property
    def anode_flag_area_cm2(self) -> float:
        """Anode flag (tab extension) area [cm²]."""
        return self.anode_flag_width_mm * self.anode_flag_height_mm / 100

    @property
    def anode_height_mm(self) -> float:
        """Anode sheet height [mm]."""
        return self.cathode_height_mm + 2 * self.anode_offset_y_mm

    @property
    def anode_width_mm(self) -> float:
        """Anode sheet width [mm]."""
        return self.cathode_width_mm + 2 * self.anode_offset_x_mm

    @property
    def anode_area_cm2(self) -> float:
        """Anode sheet area [cm²]."""
        return self.anode_height_mm * self.anode_width_mm / 100

    @property
    def separator_height_mm(self) -> float:
        """Separator sheet height [mm]."""
        return self.anode_height_mm + 2 * self.separator_offset_y_mm

    @property
    def separator_width_mm(self) -> float:
        """Separator sheet width [mm]."""
        return self.anode_width_mm + 2 * self.separator_offset_x_mm

    @property
    def separator_area_cm2(self) -> float:
        """Separator sheet area [cm²]."""
        return self.separator_height_mm * self.separator_width_mm / 100


@dataclass
class PrismaticSheetGeometry:
    """Sheet geometry with directional offsets (for Prismatic cells).

    Unlike SheetGeometry, this allows different offsets on each side.

    Attributes:
        cathode_height_mm: Cathode sheet height [mm]
        cathode_width_mm: Cathode sheet width [mm]
        anode_offset_top_mm: Anode overhang at top [mm]
        anode_offset_bottom_mm: Anode overhang at bottom [mm]
        anode_offset_left_mm: Anode overhang at left [mm]
        anode_offset_right_mm: Anode overhang at right [mm]
        separator_offset_top_mm: Separator overhang beyond anode at top [mm]
        separator_offset_bottom_mm: Separator overhang beyond anode at bottom [mm]
        separator_offset_left_mm: Separator overhang beyond anode at left [mm]
        separator_offset_right_mm: Separator overhang beyond anode at right [mm]
    """

    cathode_height_mm: float
    cathode_width_mm: float
    anode_offset_top_mm: float
    anode_offset_bottom_mm: float
    anode_offset_left_mm: float
    anode_offset_right_mm: float
    separator_offset_top_mm: float
    separator_offset_bottom_mm: float
    separator_offset_left_mm: float
    separator_offset_right_mm: float

    @property
    def cathode_area_cm2(self) -> float:
        """Cathode sheet area [cm²]."""
        return self.cathode_height_mm * self.cathode_width_mm / 100

    @property
    def anode_height_mm(self) -> float:
        """Anode sheet height [mm]."""
        return self.cathode_height_mm + self.anode_offset_top_mm + self.anode_offset_bottom_mm

    @property
    def anode_width_mm(self) -> float:
        """Anode sheet width [mm]."""
        return self.cathode_width_mm + self.anode_offset_left_mm + self.anode_offset_right_mm

    @property
    def anode_area_cm2(self) -> float:
        """Anode sheet area [cm²]."""
        return self.anode_height_mm * self.anode_width_mm / 100

    @property
    def separator_height_mm(self) -> float:
        """Separator sheet height [mm]."""
        return self.anode_height_mm + self.separator_offset_top_mm + self.separator_offset_bottom_mm

    @property
    def separator_width_mm(self) -> float:
        """Separator sheet width [mm]."""
        return self.anode_width_mm + self.separator_offset_left_mm + self.separator_offset_right_mm

    @property
    def separator_area_cm2(self) -> float:
        """Separator sheet area [cm²]."""
        return self.separator_height_mm * self.separator_width_mm / 100


@dataclass
class PouchPackaging:
    """Pouch cell packaging dimensions.

    Defines the pouch foil overhang beyond the separator on each side.

    Attributes:
        pouch_offset_top_mm: Pouch foil overhang at top [mm]
        pouch_offset_bottom_mm: Pouch foil overhang at bottom [mm]
        pouch_offset_left_mm: Pouch foil overhang at left [mm]
        pouch_offset_right_mm: Pouch foil overhang at right [mm]
    """

    pouch_offset_top_mm: float
    pouch_offset_bottom_mm: float
    pouch_offset_left_mm: float
    pouch_offset_right_mm: float

    def calculate_cell_dimensions(
        self, separator_height_mm: float, separator_width_mm: float
    ) -> tuple[float, float]:
        """Calculate cell outer dimensions from separator size.

        Args:
            separator_height_mm: Separator sheet height [mm]
            separator_width_mm: Separator sheet width [mm]

        Returns:
            Tuple of (cell_height_mm, cell_width_mm)
        """
        cell_height_mm = (
            separator_height_mm + self.pouch_offset_top_mm + self.pouch_offset_bottom_mm
        )
        cell_width_mm = separator_width_mm + self.pouch_offset_left_mm + self.pouch_offset_right_mm
        return cell_height_mm, cell_width_mm


@dataclass
class PrismaticGeometry:
    """Prismatic cell case geometry.

    Defines external dimensions and wall thicknesses for a prismatic cell.

    Attributes:
        cell_height_y_mm: External cell height [mm]
        cell_width_x_mm: External cell width [mm]
        cell_thickness_z_mm: External cell thickness (excl. coating) [mm]
        wall_top_xz_mm: Top lid thickness [mm]
        wall_bottom_xz_mm: Bottom lid thickness [mm]
        wall_side_xy_mm: Side wall thickness in XY plane [mm]
        wall_side_zy_mm: Side wall thickness in ZY plane [mm]
        insulation_foil_thickness_um: External insulation coating [µm]
    """

    cell_height_y_mm: float
    cell_width_x_mm: float
    cell_thickness_z_mm: float
    wall_top_xz_mm: float
    wall_bottom_xz_mm: float
    wall_side_xy_mm: float
    wall_side_zy_mm: float
    insulation_foil_thickness_um: float = 0.0

    @property
    def internal_height_mm(self) -> float:
        """Internal cavity height [mm]."""
        return self.cell_height_y_mm - self.wall_top_xz_mm - self.wall_bottom_xz_mm

    @property
    def internal_width_mm(self) -> float:
        """Internal cavity width [mm]."""
        return self.cell_width_x_mm - 2 * self.wall_side_xy_mm

    @property
    def internal_thickness_mm(self) -> float:
        """Internal cavity thickness [mm]."""
        return self.cell_thickness_z_mm - 2 * self.wall_side_zy_mm

    @property
    def cell_volume_cm3(self) -> float:
        """External cell volume [cm³]."""
        return self.cell_height_y_mm * self.cell_width_x_mm * self.cell_thickness_z_mm / 1000

    @property
    def internal_volume_cm3(self) -> float:
        """Internal cavity volume [cm³]."""
        return self.internal_height_mm * self.internal_width_mm * self.internal_thickness_mm / 1000

    def calculate_gap_thickness(self, stack_thickness_mm: float) -> float:
        """Calculate gap between stack and internal wall.

        Args:
            stack_thickness_mm: Total stack thickness [mm]

        Returns:
            Gap thickness [mm]
        """
        return self.internal_thickness_mm - stack_thickness_mm
