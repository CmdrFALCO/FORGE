"""Prismatic cell data models for FORGE engine.

This module defines dataclasses for prismatic battery cells including:
- PrismaticGeometry: External cell dimensions and wall thicknesses
- PrismaticCellInput: Complete input specification for prismatic cell calculations
"""

from dataclasses import dataclass, field

from .materials import (
    DENSITY_ALUMINUM,
    DENSITY_PP,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)

# =============================================================================
# CAD Geometry Features for 3D Model Generation
# =============================================================================


@dataclass
class TerminalGeometry:
    """Geometry for positive and negative terminals on cell lid."""

    # Positive terminal
    positive_diameter_mm: float = 16.0  # M8 bolt standard
    positive_height_mm: float = 10.0  # Above lid surface
    positive_x_mm: float | None = None  # From left edge, None = auto 30%
    positive_y_mm: float | None = None  # From front edge, None = auto center

    # Negative terminal
    negative_diameter_mm: float = 16.0
    negative_height_mm: float = 10.0
    negative_x_mm: float | None = None  # From left edge, None = auto 70%
    negative_y_mm: float | None = None  # From front edge, None = auto center

    def get_positions(self, cell_width_mm: float, cell_thickness_mm: float) -> dict:
        """Calculate actual positions, using defaults if not specified.

        Args:
            cell_width_mm: Cell width (X dimension)
            cell_thickness_mm: Cell thickness (Z dimension)

        Returns:
            Dictionary with calculated positions for each terminal
        """
        return {
            "positive_x_mm": self.positive_x_mm
            if self.positive_x_mm is not None
            else cell_width_mm * 0.3,
            "positive_y_mm": self.positive_y_mm
            if self.positive_y_mm is not None
            else cell_thickness_mm / 2,
            "negative_x_mm": self.negative_x_mm
            if self.negative_x_mm is not None
            else cell_width_mm * 0.7,
            "negative_y_mm": self.negative_y_mm
            if self.negative_y_mm is not None
            else cell_thickness_mm / 2,
        }


@dataclass
class VentGeometry:
    """Geometry for safety vent on cell lid."""

    diameter_mm: float = 5.0  # Typical burst disc
    x_mm: float | None = None  # From left edge, None = auto center
    y_mm: float | None = None  # From front edge, None = auto center

    def get_position(self, cell_width_mm: float, cell_thickness_mm: float) -> dict:
        """Calculate actual position, using defaults if not specified.

        Args:
            cell_width_mm: Cell width (X dimension)
            cell_thickness_mm: Cell thickness (Z dimension)

        Returns:
            Dictionary with calculated vent position
        """
        return {
            "x_mm": self.x_mm if self.x_mm is not None else cell_width_mm / 2,
            "y_mm": self.y_mm if self.y_mm is not None else cell_thickness_mm / 2,
        }


@dataclass
class PrismaticCADFeatures:
    """Additional geometry features needed for 3D CAD model generation.

    All dimensions in millimeters. Provides optional CAD-specific details
    that augment the basic PrismaticGeometry for complete 3D model generation.
    All fields have industry-standard defaults.
    """

    # Corner radii
    external_corner_radius_mm: float = 3.0  # External case corners
    internal_corner_radius_mm: float = 1.5  # Internal cavity corners
    lid_corner_radius_mm: float = 2.0  # Lid edge radius

    # Terminal geometry
    terminals: TerminalGeometry = field(default_factory=TerminalGeometry)

    # Vent geometry
    vent: VentGeometry = field(default_factory=VentGeometry)

    # Additional features
    lid_thickness_mm: float = 2.0  # Usually same as wall_top
    weld_seam_width_mm: float = 1.5  # Laser weld width (cosmetic)


@dataclass
class PrismaticGeometry:
    """External cell dimensions and wall thicknesses for prismatic cells.

    All dimensions in millimeters unless otherwise noted.

    Attributes:
        cell_height_mm: External cell height (Z direction for V1: 88.8mm)
        cell_width_mm: External cell width (Y direction for V1: 264.6mm)
        cell_thickness_mm: External cell thickness (X direction for V1: 29.6mm)
        wall_top_mm: Top lid thickness (2.0mm for V1)
        wall_bottom_mm: Bottom wall thickness (1.0mm for V1)
        wall_front_back_mm: Front/back wall thickness in YZ plane (0.5mm for V1)
        wall_sides_mm: Side wall thickness in XZ plane (0.7mm for V1)
        insulation_coating_um: External insulation coating thickness [µm]
    """

    cell_height_mm: float
    cell_width_mm: float
    cell_thickness_mm: float
    wall_top_mm: float
    wall_bottom_mm: float
    wall_front_back_mm: float
    wall_sides_mm: float
    insulation_coating_um: float = 85.0

    @property
    def internal_height_mm(self) -> float:
        """Internal height available for stacks [mm]."""
        return self.cell_height_mm - self.wall_top_mm - self.wall_bottom_mm

    @property
    def internal_width_mm(self) -> float:
        """Internal width available for stacks [mm]."""
        return self.cell_width_mm - 2 * self.wall_sides_mm

    @property
    def internal_thickness_mm(self) -> float:
        """Internal thickness available for stacks [mm]."""
        return self.cell_thickness_mm - 2 * self.wall_front_back_mm

    @property
    def cell_volume_cm3(self) -> float:
        """External cell volume [cm³]."""
        return (self.cell_height_mm * self.cell_width_mm * self.cell_thickness_mm) / 1000.0

    @property
    def cell_volume_with_coating_cm3(self) -> float:
        """Cell volume including external insulation coating [cm³]."""
        coating_mm = self.insulation_coating_um / 1000.0
        return (
            (self.cell_height_mm + 2 * coating_mm)
            * (self.cell_width_mm + 2 * coating_mm)
            * (self.cell_thickness_mm + 2 * coating_mm)
        ) / 1000.0


@dataclass
class PrismaticSheetGeometry:
    """Sheet geometry with directional offsets for prismatic cells.

    This class handles the asymmetric offset calculations where anode
    extends beyond cathode in specific directions (top, bottom, left, right).

    Attributes:
        cathode_height_mm: Cathode sheet height [mm]
        cathode_width_mm: Cathode sheet width [mm]
        anode_offset_top_mm: Anode extends beyond cathode at top [mm]
        anode_offset_bottom_mm: Anode extends beyond cathode at bottom [mm]
        anode_offset_left_mm: Anode extends beyond cathode at left [mm]
        anode_offset_right_mm: Anode extends beyond cathode at right [mm]
        separator_offset_top_mm: Separator extends beyond anode at top [mm]
        separator_offset_bottom_mm: Separator extends beyond anode at bottom [mm]
        separator_offset_left_mm: Separator extends beyond anode at left [mm]
        separator_offset_right_mm: Separator extends beyond anode at right [mm]
    """

    cathode_height_mm: float
    cathode_width_mm: float
    anode_offset_top_mm: float = 2.0
    anode_offset_bottom_mm: float = 2.0
    anode_offset_left_mm: float = 2.0
    anode_offset_right_mm: float = 2.0
    separator_offset_top_mm: float = 2.0
    separator_offset_bottom_mm: float = 2.0
    separator_offset_left_mm: float = 2.0
    separator_offset_right_mm: float = 2.0

    @property
    def cathode_area_cm2(self) -> float:
        """Cathode sheet area [cm²]."""
        return self.cathode_height_mm * self.cathode_width_mm / 100.0

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
        return self.anode_height_mm * self.anode_width_mm / 100.0

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
        return self.separator_height_mm * self.separator_width_mm / 100.0


@dataclass
class PrismaticCellInput:
    """Complete input specification for a prismatic cell calculation.

    Attributes:
        cell_name: Design name for identification
        case_geometry: External case dimensions and wall thicknesses
        sheet_geometry: Sheet dimensions with directional offsets
        number_of_stacks: Number of electrode stacks (typically 2)
        electrode_pairs_per_stack: Electrode pairs per stack
        end_electrodes: End electrode configuration ("BothNegative", etc.)
        cathode: Cathode material properties
        anode: Anode material properties
        separator: Separator material properties
        electrolyte: Electrolyte properties
        case_material_density_gcm3: Case material density (aluminum)
        header_mass_g: Header assembly mass (lid + terminals + insulations)
        insulation_shell_thickness_um: Insulation shell thickness around stacks
        insulation_shell_count: Number of insulation shells
        insulation_shell_density_gcm3: Insulation shell material density
        electrolyte_excess_factor: Electrolyte excess factor
        electrolyte_volume_override_ml: Optional manual electrolyte volume
        cathode_porosity_pct: Cathode coating porosity at 0% SoC
        anode_porosity_pct: Anode coating porosity at 0% SoC
        nominal_voltage_v: Nominal cell voltage
        capacity_ah: Cell capacity (optional - calculated if not provided)
        fixing_tape_count: Number of fixing tapes
        fixing_tape_thickness_um: Fixing tape thickness
        fixing_tape_width_mm: Fixing tape width
        fixing_tape_length_mm: Fixing tape length
        fixing_tape_density_gcm3: Fixing tape material density
    """

    # Cell identification
    cell_name: str = "Prismatic Cell"

    # Case geometry
    case_geometry: PrismaticGeometry = None

    # Sheet geometry with directional offsets
    sheet_geometry: PrismaticSheetGeometry = None

    # Stack configuration
    number_of_stacks: int = 2
    electrode_pairs_per_stack: int = 22
    end_electrodes: str = "BothNegative"

    # Materials
    cathode: CathodeMaterial = None
    anode: AnodeMaterial = None
    separator: SeparatorMaterial = None
    electrolyte: ElectrolyteModel = None

    # Case properties
    case_material_density_gcm3: float = DENSITY_ALUMINUM
    header_mass_g: float = 88.76  # Lid + terminals + insulations

    # Insulation shell (around stacks, inside case)
    insulation_shell_thickness_um: float = 120.0
    insulation_shell_count: int = 2
    insulation_shell_density_gcm3: float = DENSITY_PP

    # Electrolyte
    electrolyte_excess_factor: float = 1.0
    electrolyte_volume_override_ml: float | None = None

    # Porosity for electrolyte calculation
    cathode_porosity_pct: float = 25.36  # V1 value at 0% SoC
    anode_porosity_pct: float = 38.01  # V1 value at 0% SoC

    # Electrical
    nominal_voltage_v: float = 3.644
    capacity_ah: float | None = None

    # Fixing tape
    fixing_tape_count: int = 4
    fixing_tape_thickness_um: float = 30.0
    fixing_tape_width_mm: float = 30.0
    fixing_tape_length_mm: float = 200.0
    fixing_tape_density_gcm3: float = 1.42

    # Separator overwraps (C# default is 1)
    separator_overwraps_per_stack: int = 1

    # Insulation coating on external case
    insulation_coating_density_gcm3: float = DENSITY_PP

    # CAD geometry features (optional, with defaults)
    cad_features: PrismaticCADFeatures = field(default_factory=PrismaticCADFeatures)

    @property
    def total_electrode_pairs(self) -> int:
        """Total electrode pairs in cell."""
        return self.electrode_pairs_per_stack * self.number_of_stacks

    @property
    def cathode_sheets_per_stack(self) -> int:
        """Cathode sheets per stack based on end configuration."""
        if self.end_electrodes == "BothNegative":
            return self.electrode_pairs_per_stack
        elif self.end_electrodes == "BothPositive":
            return self.electrode_pairs_per_stack + 1
        else:  # PositiveNegative
            return self.electrode_pairs_per_stack

    @property
    def anode_sheets_per_stack(self) -> int:
        """Anode sheets per stack based on end configuration."""
        if self.end_electrodes == "BothNegative":
            return self.electrode_pairs_per_stack + 1
        elif self.end_electrodes == "BothPositive":
            return self.electrode_pairs_per_stack
        else:  # PositiveNegative
            return self.electrode_pairs_per_stack

    @property
    def separator_sheets_per_stack(self) -> int:
        """Separator sheets per stack.

        Uses C# formula: Cathode + Anode + (2 * SeparatorOverwraps) - 1
        """
        return (
            self.cathode_sheets_per_stack
            + self.anode_sheets_per_stack
            + (2 * self.separator_overwraps_per_stack)
            - 1
        )

    @property
    def total_cathode_sheets(self) -> int:
        """Total cathode sheets in cell."""
        return self.cathode_sheets_per_stack * self.number_of_stacks

    @property
    def total_anode_sheets(self) -> int:
        """Total anode sheets in cell."""
        return self.anode_sheets_per_stack * self.number_of_stacks

    @property
    def total_separator_sheets(self) -> int:
        """Total separator sheets in cell."""
        return self.separator_sheets_per_stack * self.number_of_stacks


# =============================================================================
# CAD Export Dataclass
# =============================================================================


@dataclass
class PrismaticCADExport:
    """
    Complete geometry data package for 3D CAD generation.

    All dimensions in mm. Coordinate system:
    - Origin at bottom-left-front corner of cell
    - X = width (left to right)
    - Y = height (bottom to top)
    - Z = thickness (front to back)
    """

    # Cell envelope
    cell_height_mm: float  # Y dimension (vertical)
    cell_width_mm: float  # X dimension (left-right)
    cell_thickness_mm: float  # Z dimension (front-back)

    # Case geometry
    external_corner_radius_mm: float
    internal_corner_radius_mm: float

    # Wall thicknesses
    wall_top_mm: float
    wall_bottom_mm: float
    wall_front_mm: float  # YZ plane
    wall_back_mm: float  # YZ plane
    wall_left_mm: float  # XZ plane
    wall_right_mm: float  # XZ plane

    # Internal cavity (derived)
    cavity_height_mm: float
    cavity_width_mm: float
    cavity_thickness_mm: float

    # Lid geometry
    lid_thickness_mm: float
    lid_corner_radius_mm: float

    # Positive terminal (absolute positions)
    positive_terminal_x_mm: float
    positive_terminal_y_mm: float  # On lid, so Y = cell_height
    positive_terminal_z_mm: float
    positive_terminal_diameter_mm: float
    positive_terminal_height_mm: float

    # Negative terminal (absolute positions)
    negative_terminal_x_mm: float
    negative_terminal_y_mm: float
    negative_terminal_z_mm: float
    negative_terminal_diameter_mm: float
    negative_terminal_height_mm: float

    # Vent (absolute position)
    vent_x_mm: float
    vent_y_mm: float  # On lid, so Y = cell_height
    vent_z_mm: float
    vent_diameter_mm: float

    # Stack geometry (for internal modeling)
    stack_height_mm: float
    stack_width_mm: float
    stack_thickness_dry_mm: float
    stack_thickness_soc0_mm: float
    stack_thickness_soc100_mm: float
    stack_count: int

    # Gap analysis
    gap_to_wall_dry_mm: float
    gap_to_wall_soc100_mm: float
