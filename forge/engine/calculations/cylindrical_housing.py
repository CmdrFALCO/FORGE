"""Cylindrical housing calculations for FORGE engine.

This module provides calculations for cylindrical cell housing components:
- Can body mass (cylinder shell)
- Can bottom mass (disc)
- Header component masses
- Total housing mass breakdown
- Tab mass calculations (traditional vs tabless)
"""

import math
from dataclasses import dataclass

from forge.engine.models.cylindrical import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    CanMaterial,
    CylindricalGeometry,
    HeaderComponents,
    SimplifiedHeader,
    TabType,
    WindingConfig,
    get_can_material_density,
)


@dataclass
class CylindricalHousingResult:
    """Result of cylindrical housing mass calculation.

    Attributes:
        can_body_g: Cylindrical can body (shell) mass [g]
        can_bottom_g: Can bottom disc mass [g]
        header_total_g: Total header/cap assembly mass [g]
        bottom_insulator_g: Bottom insulator disc mass [g]
        top_insulator_g: Top insulator disc mass [g]
        tabs_g: Tab mass (0 for tabless) [g]
    """

    can_body_g: float
    can_bottom_g: float
    header_total_g: float
    bottom_insulator_g: float
    top_insulator_g: float
    tabs_g: float

    @property
    def total_housing_g(self) -> float:
        """Total housing mass [g]."""
        return (
            self.can_body_g
            + self.can_bottom_g
            + self.header_total_g
            + self.bottom_insulator_g
            + self.top_insulator_g
            + self.tabs_g
        )

    @property
    def can_total_g(self) -> float:
        """Total can mass (body + bottom) [g]."""
        return self.can_body_g + self.can_bottom_g


def calculate_can_body_mass(
    outer_diameter_mm: float, body_length_mm: float, wall_thickness_mm: float, material: CanMaterial
) -> float:
    """Calculate mass of cylindrical can body (shell only).

    The can body is modeled as a hollow cylinder (tube).

    Args:
        outer_diameter_mm: External can diameter [mm]
        body_length_mm: Can body length (excluding bottom) [mm]
        wall_thickness_mm: Wall thickness [mm]
        material: Can material

    Returns:
        Can body mass [g]
    """
    # Convert to cm
    r_outer = outer_diameter_mm / 2 / 10
    r_inner = (outer_diameter_mm - 2 * wall_thickness_mm) / 2 / 10
    h = body_length_mm / 10

    # Volume of hollow cylinder
    volume = math.pi * h * (r_outer**2 - r_inner**2)

    density = get_can_material_density(material)
    return volume * density


def calculate_can_bottom_mass(
    diameter_mm: float, thickness_mm: float, material: CanMaterial
) -> float:
    """Calculate mass of can bottom disc.

    Args:
        diameter_mm: Bottom disc diameter [mm]
        thickness_mm: Bottom disc thickness [mm]
        material: Can material

    Returns:
        Can bottom mass [g]
    """
    # Convert to cm
    r = diameter_mm / 2 / 10
    h = thickness_mm / 10

    # Volume of disc
    volume = math.pi * r**2 * h

    density = get_can_material_density(material)
    return volume * density


def calculate_traditional_tab_mass(
    tab_width_mm: float,
    tab_thickness_mm: float,
    electrode_width_mm: float,
    num_tabs: int,
    material_density_gcm3: float,
) -> float:
    """Calculate mass of traditional welded tabs.

    Args:
        tab_width_mm: Tab width [mm]
        tab_thickness_mm: Tab thickness [mm]
        electrode_width_mm: Electrode width (tab length equals this) [mm]
        num_tabs: Number of tabs
        material_density_gcm3: Tab material density [g/cm³]

    Returns:
        Total tab mass [g]
    """
    # Tab volume = width × thickness × length (approx electrode width)
    volume_cm3 = (tab_width_mm * tab_thickness_mm * electrode_width_mm) / 1000  # mm³ to cm³
    return volume_cm3 * material_density_gcm3 * num_tabs


def calculate_tabless_foil_extension_mass(
    foil_extension_mm: float,
    electrode_length_m: float,
    collector_thickness_um: float,
    material_density_gcm3: float,
) -> float:
    """Calculate additional foil mass for tabless design.

    In tabless designs, the current collector foil extends beyond the
    active coating area. This calculates the mass of that extension.

    Args:
        foil_extension_mm: Foil extension beyond coating [mm]
        electrode_length_m: Total electrode length [m]
        collector_thickness_um: Collector foil thickness [µm]
        material_density_gcm3: Collector material density [g/cm³]

    Returns:
        Foil extension mass [g]
    """
    # Volume = extension_width × electrode_length × thickness
    length_cm = electrode_length_m * 100  # m to cm
    width_cm = foil_extension_mm / 10  # mm to cm
    thickness_cm = collector_thickness_um / 10000  # µm to cm

    volume_cm3 = length_cm * width_cm * thickness_cm
    return volume_cm3 * material_density_gcm3


def calculate_tab_or_foil_mass(
    winding: WindingConfig,
    electrode_length_m: float,
    electrode_width_mm: float,
    anode_collector_thickness_um: float,
    cathode_collector_thickness_um: float,
) -> float:
    """Calculate tab mass based on tab type.

    For traditional cells, calculates welded tab mass.
    For tabless cells, calculates additional foil extension mass.

    Args:
        winding: Winding configuration with tab type and dimensions
        electrode_length_m: Total electrode length [m]
        electrode_width_mm: Electrode width [mm]
        anode_collector_thickness_um: Anode collector thickness [µm]
        cathode_collector_thickness_um: Cathode collector thickness [µm]

    Returns:
        Total tab or foil extension mass [g]
    """
    if winding.tab_type == TabType.TRADITIONAL:
        # Traditional welded tabs
        anode_tab_mass = 0.0
        cathode_tab_mass = 0.0

        if winding.anode_tab_width_mm and winding.anode_tab_thickness_mm:
            anode_tab_mass = calculate_traditional_tab_mass(
                tab_width_mm=winding.anode_tab_width_mm,
                tab_thickness_mm=winding.anode_tab_thickness_mm,
                electrode_width_mm=electrode_width_mm,
                num_tabs=1,
                material_density_gcm3=DENSITY_COPPER,  # Anode tab typically copper
            )

        if winding.cathode_tab_width_mm and winding.cathode_tab_thickness_mm:
            cathode_tab_mass = calculate_traditional_tab_mass(
                tab_width_mm=winding.cathode_tab_width_mm,
                tab_thickness_mm=winding.cathode_tab_thickness_mm,
                electrode_width_mm=electrode_width_mm,
                num_tabs=1,
                material_density_gcm3=DENSITY_ALUMINUM,  # Cathode tab typically aluminum
            )

        return anode_tab_mass + cathode_tab_mass

    else:
        # Tabless design - foil extensions
        anode_foil_mass = 0.0
        cathode_foil_mass = 0.0

        if winding.anode_foil_extension_mm:
            anode_foil_mass = calculate_tabless_foil_extension_mass(
                foil_extension_mm=winding.anode_foil_extension_mm,
                electrode_length_m=electrode_length_m,
                collector_thickness_um=anode_collector_thickness_um,
                material_density_gcm3=DENSITY_COPPER,
            )

        if winding.cathode_foil_extension_mm:
            cathode_foil_mass = calculate_tabless_foil_extension_mass(
                foil_extension_mm=winding.cathode_foil_extension_mm,
                electrode_length_m=electrode_length_m,
                collector_thickness_um=cathode_collector_thickness_um,
                material_density_gcm3=DENSITY_ALUMINUM,
            )

        return anode_foil_mass + cathode_foil_mass


def calculate_cylindrical_housing_mass(
    geometry: CylindricalGeometry,
    can_material: CanMaterial,
    header: HeaderComponents | None = None,
    header_simplified: SimplifiedHeader | None = None,
    bottom_insulator_mass_g: float = 0.1,
    top_insulator_mass_g: float = 0.1,
    tabs_mass_g: float = 0.0,
) -> CylindricalHousingResult:
    """Calculate all housing component masses for a cylindrical cell.

    Args:
        geometry: Cylindrical cell geometry
        can_material: Can material
        header: Detailed header components (optional)
        header_simplified: Simplified header spec (optional)
        bottom_insulator_mass_g: Bottom insulator disc mass [g]
        top_insulator_mass_g: Top insulator disc mass [g]
        tabs_mass_g: Pre-calculated tab mass [g]

    Returns:
        CylindricalHousingResult with detailed mass breakdown
    """
    # Can body - cylindrical shell
    # Body length = total length - bottom thickness
    body_length = geometry.length_mm - geometry.can_bottom_thickness_mm

    can_body_mass = calculate_can_body_mass(
        outer_diameter_mm=geometry.diameter_mm,
        body_length_mm=body_length,
        wall_thickness_mm=geometry.can_wall_thickness_mm,
        material=can_material,
    )

    # Can bottom - disc
    can_bottom_mass = calculate_can_bottom_mass(
        diameter_mm=geometry.diameter_mm,
        thickness_mm=geometry.can_bottom_thickness_mm,
        material=can_material,
    )

    # Header mass
    if header is not None:
        header_mass = header.total_header_mass_g
    elif header_simplified is not None:
        header_mass = header_simplified.total_mass_g
    else:
        header_mass = 0.0

    return CylindricalHousingResult(
        can_body_g=can_body_mass,
        can_bottom_g=can_bottom_mass,
        header_total_g=header_mass,
        bottom_insulator_g=bottom_insulator_mass_g,
        top_insulator_g=top_insulator_mass_g,
        tabs_g=tabs_mass_g,
    )


# Typical header mass estimates for common formats


def estimate_21700_header_mass(can_material: CanMaterial = CanMaterial.STEEL) -> float:
    """Estimate typical header mass for 21700 cell.

    Based on typical component masses from literature:
    - PTC: ~0.3g
    - CID: ~0.2g
    - Vent: ~0.2g
    - Cap: ~1.0g
    - Gasket: ~0.15g
    - Insulator: ~0.1g

    Args:
        can_material: Can material (affects cap density)

    Returns:
        Estimated header mass [g]
    """
    base_mass = 1.95  # For steel cap
    if can_material == CanMaterial.ALUMINUM:
        # Aluminum cap is lighter
        base_mass -= 0.7  # Approximate cap mass difference
    return base_mass


def estimate_4680_header_mass(can_material: CanMaterial = CanMaterial.STEEL) -> float:
    """Estimate typical header mass for 4680 cell.

    Scaled from 21700 based on diameter ratio.
    4680 has more complex header due to tabless design.

    Args:
        can_material: Can material (affects cap density)

    Returns:
        Estimated header mass [g]
    """
    # Diameter ratio squared (area ratio) × complexity factor
    diameter_ratio = 46.0 / 21.0
    area_ratio = diameter_ratio**2

    base_21700 = estimate_21700_header_mass(can_material)
    complexity_factor = 1.2  # Tabless design adds complexity

    return base_21700 * area_ratio * complexity_factor


def estimate_18650_header_mass(can_material: CanMaterial = CanMaterial.STEEL) -> float:
    """Estimate typical header mass for 18650 cell.

    Args:
        can_material: Can material

    Returns:
        Estimated header mass [g]
    """
    # Scaled from 21700 by diameter ratio
    diameter_ratio = 18.0 / 21.0
    area_ratio = diameter_ratio**2

    return estimate_21700_header_mass(can_material) * area_ratio


def create_typical_21700_header() -> HeaderComponents:
    """Create typical header components for 21700 cell.

    Returns:
        HeaderComponents with typical 21700 values
    """
    return HeaderComponents(
        ptc_diameter_mm=8.0,
        ptc_thickness_mm=0.8,
        ptc_mass_g=0.3,
        cid_diameter_mm=10.0,
        cid_thickness_mm=0.5,
        cid_mass_g=0.2,
        vent_diameter_mm=6.0,
        vent_thickness_mm=0.3,
        vent_mass_g=0.2,
        cap_diameter_mm=21.0,
        cap_thickness_mm=0.5,
        cap_material=CanMaterial.STEEL,
        gasket_mass_g=0.15,
        insulator_ring_mass_g=0.1,
    )


def create_typical_4680_header() -> HeaderComponents:
    """Create typical header components for 4680 cell.

    Note: 4680 tabless design has different header configuration.
    Values are estimates based on public teardown information.

    Returns:
        HeaderComponents with typical 4680 values
    """
    return HeaderComponents(
        ptc_diameter_mm=20.0,
        ptc_thickness_mm=1.0,
        ptc_mass_g=1.5,
        cid_diameter_mm=25.0,
        cid_thickness_mm=0.8,
        cid_mass_g=1.0,
        vent_diameter_mm=15.0,
        vent_thickness_mm=0.5,
        vent_mass_g=0.8,
        cap_diameter_mm=46.0,
        cap_thickness_mm=0.6,
        cap_material=CanMaterial.STEEL,
        gasket_mass_g=0.8,
        insulator_ring_mass_g=0.5,
    )
