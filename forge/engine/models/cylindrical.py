"""Cylindrical cell data models for FORGE engine.

This module defines dataclasses for cylindrical battery cells including:
- TabType: Enum for traditional vs tabless designs
- CanMaterial: Enum for can materials (steel, aluminum)
- CylindricalGeometry: External cell dimensions and can properties
- WindingConfig: Jelly roll winding configuration
- HeaderComponents: Detailed header/cap assembly components
- JellyRollResult: Calculated jelly roll properties
- CylindricalCellInput: Complete input specification for cylindrical cell calculations
"""

import math
from dataclasses import dataclass
from enum import Enum

from .materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)

# Material densities [g/cm³]
DENSITY_STEEL = 7.85
DENSITY_ALUMINUM = 2.70
DENSITY_NICKEL_PLATED_STEEL = 7.85
DENSITY_COPPER = 8.96


class TabType(Enum):
    """Tab configuration type for cylindrical cells."""

    TRADITIONAL = "traditional"  # Tabs welded to foil
    TABLESS = "tabless"  # Foil edge direct-welded (4680 style)


class CanMaterial(Enum):
    """Can material options for cylindrical cells."""

    STEEL = "steel"
    ALUMINUM = "aluminum"
    NICKEL_PLATED_STEEL = "nickel_plated_steel"


def get_can_material_density(material: CanMaterial) -> float:
    """Get density for a can material.

    Args:
        material: Can material enum value

    Returns:
        Density in g/cm³
    """
    densities = {
        CanMaterial.STEEL: DENSITY_STEEL,
        CanMaterial.ALUMINUM: DENSITY_ALUMINUM,
        CanMaterial.NICKEL_PLATED_STEEL: DENSITY_NICKEL_PLATED_STEEL,
    }
    return densities[material]


@dataclass
class CylindricalGeometry:
    """Cylindrical cell external dimensions.

    Defines the external can dimensions and wall thicknesses.

    Attributes:
        diameter_mm: External can diameter (e.g., 21 for 21700, 46 for 4680)
        length_mm: External can length (e.g., 70 for 21700, 80 for 4680)
        can_wall_thickness_mm: Can body wall thickness (typically 0.2-0.4mm)
        can_bottom_thickness_mm: Can bottom plate thickness
        header_height_mm: Top assembly/header height
    """

    diameter_mm: float
    length_mm: float
    can_wall_thickness_mm: float
    can_bottom_thickness_mm: float
    header_height_mm: float

    @property
    def can_inner_diameter_mm(self) -> float:
        """Internal can diameter [mm]."""
        return self.diameter_mm - 2 * self.can_wall_thickness_mm

    @property
    def can_inner_length_mm(self) -> float:
        """Internal can length available for jelly roll [mm]."""
        return self.length_mm - self.can_bottom_thickness_mm - self.header_height_mm

    @property
    def can_volume_cm3(self) -> float:
        """External can volume [cm³]."""
        r = self.diameter_mm / 2 / 10  # mm to cm
        h = self.length_mm / 10  # mm to cm
        return math.pi * r**2 * h

    @property
    def can_inner_volume_cm3(self) -> float:
        """Internal can volume [cm³]."""
        r = self.can_inner_diameter_mm / 2 / 10  # mm to cm
        h = self.can_inner_length_mm / 10  # mm to cm
        return math.pi * r**2 * h


@dataclass
class WindingConfig:
    """Jelly roll winding configuration.

    Defines the winding parameters including mandrel size, clearances,
    tension/compression factors, and tab configuration.

    Attributes:
        mandrel_diameter_mm: Inner core/mandrel diameter (typically 2-5mm)
        winding_clearance_mm: Gap between jelly roll outer diameter and can wall
        winding_tension_factor: Compression factor (1.0 = no compression, 0.95 = 5% compressed)
        tab_type: Traditional tabs or tabless (4680-style)

        # For traditional tabs
        anode_tab_width_mm: Anode tab width (traditional only)
        anode_tab_thickness_mm: Anode tab thickness (traditional only)
        cathode_tab_width_mm: Cathode tab width (traditional only)
        cathode_tab_thickness_mm: Cathode tab thickness (traditional only)

        # For tabless - foil extension beyond coating
        anode_foil_extension_mm: Anode foil extension for tabless design (typically 2-5mm)
        cathode_foil_extension_mm: Cathode foil extension for tabless design (typically 2-5mm)
    """

    mandrel_diameter_mm: float
    winding_clearance_mm: float
    winding_tension_factor: float
    tab_type: TabType

    # Traditional tab dimensions
    anode_tab_width_mm: float | None = None
    anode_tab_thickness_mm: float | None = None
    cathode_tab_width_mm: float | None = None
    cathode_tab_thickness_mm: float | None = None

    # Tabless foil extension dimensions
    anode_foil_extension_mm: float | None = None
    cathode_foil_extension_mm: float | None = None

    def __post_init__(self):
        """Validate configuration based on tab type."""
        if self.tab_type == TabType.TRADITIONAL:
            if self.anode_tab_width_mm is None or self.anode_tab_thickness_mm is None:
                pass  # Allow None for now, validation will be done in calculator
            if self.cathode_tab_width_mm is None or self.cathode_tab_thickness_mm is None:
                pass  # Allow None for now
        elif self.tab_type == TabType.TABLESS:
            if self.anode_foil_extension_mm is None:
                self.anode_foil_extension_mm = 3.0  # Default 3mm
            if self.cathode_foil_extension_mm is None:
                self.cathode_foil_extension_mm = 3.0  # Default 3mm


@dataclass
class HeaderComponents:
    """Detailed header/cap assembly components.

    Models the various safety and structural components in the cell header.

    Attributes:
        ptc_diameter_mm: PTC (Positive Temperature Coefficient) device diameter
        ptc_thickness_mm: PTC thickness
        ptc_mass_g: PTC mass (often easier to specify directly)
        cid_diameter_mm: CID (Current Interrupt Device) diameter
        cid_thickness_mm: CID thickness
        cid_mass_g: CID mass
        vent_diameter_mm: Safety vent disc diameter
        vent_thickness_mm: Vent disc thickness
        vent_mass_g: Vent disc mass
        cap_diameter_mm: Top cap diameter
        cap_thickness_mm: Top cap thickness
        cap_material: Cap material (typically same as can)
        gasket_mass_g: Gasket/seal mass
        insulator_ring_mass_g: Top insulator ring mass
    """

    ptc_diameter_mm: float
    ptc_thickness_mm: float
    ptc_mass_g: float
    cid_diameter_mm: float
    cid_thickness_mm: float
    cid_mass_g: float
    vent_diameter_mm: float
    vent_thickness_mm: float
    vent_mass_g: float
    cap_diameter_mm: float
    cap_thickness_mm: float
    cap_material: CanMaterial
    gasket_mass_g: float
    insulator_ring_mass_g: float

    @property
    def cap_mass_g(self) -> float:
        """Calculate cap mass from geometry and material [g]."""
        r = self.cap_diameter_mm / 2 / 10  # mm to cm
        h = self.cap_thickness_mm / 10  # mm to cm
        volume = math.pi * r**2 * h
        density = get_can_material_density(self.cap_material)
        return volume * density

    @property
    def total_header_mass_g(self) -> float:
        """Total header assembly mass [g]."""
        return (
            self.ptc_mass_g
            + self.cid_mass_g
            + self.vent_mass_g
            + self.cap_mass_g
            + self.gasket_mass_g
            + self.insulator_ring_mass_g
        )


@dataclass
class SimplifiedHeader:
    """Simplified header specification using total mass.

    For cases where detailed component breakdown is not available.

    Attributes:
        total_mass_g: Total header assembly mass
        cap_material: Cap material
    """

    total_mass_g: float
    cap_material: CanMaterial = CanMaterial.STEEL


@dataclass
class JellyRollResult:
    """Calculated jelly roll properties.

    Contains the results of jelly roll geometry calculations.

    Attributes:
        num_winds: Number of complete winds/turns
        electrode_length_m: Total length of wound electrode [m]
        anode_area_cm2: Total anode active area (both sides) [cm²]
        cathode_area_cm2: Total cathode active area (both sides) [cm²]
        separator_area_cm2: Total separator area [cm²]
        separator_length_m: Total separator length [m]
        jelly_roll_outer_diameter_mm: Actual outer diameter of wound roll [mm]
        jelly_roll_height_mm: Height of jelly roll (electrode width) [mm]
        compression_ratio: Actual vs theoretical thickness ratio
        electrode_width_mm: Width of electrode strip [mm]
        layer_thickness_um: Thickness of one complete layer [µm]
    """

    num_winds: float
    electrode_length_m: float
    anode_area_cm2: float
    cathode_area_cm2: float
    separator_area_cm2: float
    separator_length_m: float
    jelly_roll_outer_diameter_mm: float
    jelly_roll_height_mm: float
    compression_ratio: float
    electrode_width_mm: float
    layer_thickness_um: float

    @property
    def anode_area_single_side_cm2(self) -> float:
        """Single-side anode area [cm²]."""
        return self.anode_area_cm2 / 2

    @property
    def cathode_area_single_side_cm2(self) -> float:
        """Single-side cathode area [cm²]."""
        return self.cathode_area_cm2 / 2


@dataclass
class CylindricalCellInput:
    """Complete input specification for a cylindrical cell calculation.

    Attributes:
        cell_name: Design name for identification
        geometry: External can geometry
        winding: Winding configuration
        header: Header components (detailed or simplified)
        can_material: Can body material
        cathode: Cathode material properties
        anode: Anode material properties
        separator: Separator material properties
        electrolyte: Electrolyte properties
        capacity_ah: Cell capacity [Ah] (optional - calculated if not provided)
        nominal_voltage_v: Nominal cell voltage [V]
        electrolyte_excess_factor: Electrolyte excess factor
        electrolyte_volume_override_ml: Optional manual electrolyte volume [ml]
        cathode_porosity_pct: Cathode coating porosity [%] (for electrolyte calc)
        anode_porosity_pct: Anode coating porosity [%] (for electrolyte calc)
        bottom_insulator_mass_g: Bottom insulator disc mass [g]
        top_insulator_mass_g: Top insulator disc mass [g]
    """

    cell_name: str
    geometry: CylindricalGeometry
    winding: WindingConfig
    can_material: CanMaterial
    cathode: CathodeMaterial
    anode: AnodeMaterial
    separator: SeparatorMaterial
    electrolyte: ElectrolyteModel

    # Header - either detailed or simplified
    header: HeaderComponents | None = None
    header_simplified: SimplifiedHeader | None = None

    # Electrical specs
    capacity_ah: float | None = None
    nominal_voltage_v: float = 3.6

    # Electrolyte
    electrolyte_excess_factor: float = 1.0
    electrolyte_volume_override_ml: float | None = None

    # Porosity for electrolyte calculation
    cathode_porosity_pct: float = 25.0
    anode_porosity_pct: float = 35.0

    # Additional components
    bottom_insulator_mass_g: float = 0.1
    top_insulator_mass_g: float = 0.1

    def __post_init__(self):
        """Validate that header is specified."""
        if self.header is None and self.header_simplified is None:
            # Create a default simplified header
            self.header_simplified = SimplifiedHeader(
                total_mass_g=2.0,  # Typical for 21700
                cap_material=self.can_material,
            )

    @property
    def header_mass_g(self) -> float:
        """Get total header mass from either detailed or simplified spec."""
        if self.header is not None:
            return self.header.total_header_mass_g
        elif self.header_simplified is not None:
            return self.header_simplified.total_mass_g
        return 0.0

    @property
    def is_tabless(self) -> bool:
        """Check if cell uses tabless design."""
        return self.winding.tab_type == TabType.TABLESS


# Factory functions for common cell formats


def create_21700_geometry(
    can_wall_thickness_mm: float = 0.25,
    can_bottom_thickness_mm: float = 0.4,
    header_height_mm: float = 3.5,
) -> CylindricalGeometry:
    """Create standard 21700 geometry.

    Args:
        can_wall_thickness_mm: Can wall thickness (default 0.25mm)
        can_bottom_thickness_mm: Can bottom thickness (default 0.4mm)
        header_height_mm: Header assembly height (default 3.5mm)

    Returns:
        CylindricalGeometry for 21700 format
    """
    return CylindricalGeometry(
        diameter_mm=21.0,
        length_mm=70.0,
        can_wall_thickness_mm=can_wall_thickness_mm,
        can_bottom_thickness_mm=can_bottom_thickness_mm,
        header_height_mm=header_height_mm,
    )


def create_4680_geometry(
    can_wall_thickness_mm: float = 0.35,
    can_bottom_thickness_mm: float = 0.5,
    header_height_mm: float = 4.0,
) -> CylindricalGeometry:
    """Create standard 4680 geometry.

    Args:
        can_wall_thickness_mm: Can wall thickness (default 0.35mm)
        can_bottom_thickness_mm: Can bottom thickness (default 0.5mm)
        header_height_mm: Header assembly height (default 4.0mm)

    Returns:
        CylindricalGeometry for 4680 format
    """
    return CylindricalGeometry(
        diameter_mm=46.0,
        length_mm=80.0,
        can_wall_thickness_mm=can_wall_thickness_mm,
        can_bottom_thickness_mm=can_bottom_thickness_mm,
        header_height_mm=header_height_mm,
    )


def create_18650_geometry(
    can_wall_thickness_mm: float = 0.20,
    can_bottom_thickness_mm: float = 0.35,
    header_height_mm: float = 3.0,
) -> CylindricalGeometry:
    """Create standard 18650 geometry.

    Args:
        can_wall_thickness_mm: Can wall thickness (default 0.20mm)
        can_bottom_thickness_mm: Can bottom thickness (default 0.35mm)
        header_height_mm: Header assembly height (default 3.0mm)

    Returns:
        CylindricalGeometry for 18650 format
    """
    return CylindricalGeometry(
        diameter_mm=18.0,
        length_mm=65.0,
        can_wall_thickness_mm=can_wall_thickness_mm,
        can_bottom_thickness_mm=can_bottom_thickness_mm,
        header_height_mm=header_height_mm,
    )
