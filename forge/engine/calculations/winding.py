"""Jelly roll winding calculations for cylindrical cells.

This module provides calculations for wound jelly roll geometry including:
- Layer thickness calculation
- Number of winds (Archimedean spiral)
- Electrode length calculation
- Electrode area calculation
- Winding compression model
"""

import math
from dataclasses import dataclass

from forge.engine.models.cylindrical import (
    CylindricalGeometry,
    JellyRollResult,
    TabType,
    WindingConfig,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    SeparatorMaterial,
)


@dataclass
class LayerThickness:
    """Breakdown of layer thicknesses in the jelly roll.

    All thicknesses in micrometers (µm).

    Attributes:
        cathode_collector_um: Cathode current collector thickness
        cathode_coating_single_um: Single-side cathode coating thickness
        anode_collector_um: Anode current collector thickness
        anode_coating_single_um: Single-side anode coating thickness
        separator_um: Separator thickness
    """

    cathode_collector_um: float
    cathode_coating_single_um: float
    anode_collector_um: float
    anode_coating_single_um: float
    separator_um: float

    @property
    def cathode_total_um(self) -> float:
        """Total cathode thickness (collector + 2× coating) [µm]."""
        return self.cathode_collector_um + 2 * self.cathode_coating_single_um

    @property
    def anode_total_um(self) -> float:
        """Total anode thickness (collector + 2× coating) [µm]."""
        return self.anode_collector_um + 2 * self.anode_coating_single_um

    @property
    def single_layer_um(self) -> float:
        """Single wound layer thickness [µm].

        One layer consists of:
        - Cathode (collector + 2× coating)
        - Separator
        - Anode (collector + 2× coating)
        - Separator

        Note: In a wound cell, each turn contains one cathode, one anode,
        and two separators (one on each side of the electrodes).
        """
        return self.cathode_total_um + self.anode_total_um + 2 * self.separator_um

    @property
    def single_layer_mm(self) -> float:
        """Single wound layer thickness [mm]."""
        return self.single_layer_um / 1000.0


def calculate_layer_thickness(
    cathode: CathodeMaterial,
    anode: AnodeMaterial,
    separator: SeparatorMaterial,
) -> LayerThickness:
    """Calculate layer thicknesses from material properties.

    Args:
        cathode: Cathode material properties
        anode: Anode material properties
        separator: Separator material properties

    Returns:
        LayerThickness with all component thicknesses
    """
    return LayerThickness(
        cathode_collector_um=cathode.collector_thickness_um,
        cathode_coating_single_um=cathode.coating_thickness_0pct_um,
        anode_collector_um=anode.collector_thickness_um,
        anode_coating_single_um=anode.coating_thickness_0pct_um,
        separator_um=separator.thickness_um,
    )


def calculate_compressed_thickness(
    theoretical_thickness_um: float,
    wind_number: int,
    total_winds: int,
    max_compression_pct: float = 5.0,
) -> float:
    """Calculate compressed layer thickness at a specific wind.

    Inner winds experience more compression than outer winds due to
    winding tension. This implements a linear compression model.

    Args:
        theoretical_thickness_um: Uncompressed layer thickness [µm]
        wind_number: Current wind number (0-indexed, 0 = innermost)
        total_winds: Total number of winds
        max_compression_pct: Maximum compression at innermost wind [%]

    Returns:
        Compressed thickness [µm]
    """
    if total_winds <= 1:
        return theoretical_thickness_um

    # Linear gradient: innermost wind has max compression, outermost has none
    compression_at_wind = max_compression_pct * (1 - wind_number / (total_winds - 1))
    return theoretical_thickness_um * (1 - compression_at_wind / 100)


def calculate_number_of_winds(
    inner_radius_mm: float,
    outer_radius_mm: float,
    layer_thickness_mm: float,
    tension_factor: float = 1.0,
) -> float:
    """Calculate number of winds in an Archimedean spiral.

    For a spiral with inner radius r_i and outer radius r_o:
    - Each wind adds layer_thickness to radius
    - n_winds = (r_o - r_i) / effective_layer_thickness

    Args:
        inner_radius_mm: Mandrel radius [mm]
        outer_radius_mm: Maximum outer radius (can inner radius - clearance) [mm]
        layer_thickness_mm: Uncompressed layer thickness [mm]
        tension_factor: Compression factor (1.0 = no compression, 0.95 = 5% compressed)

    Returns:
        Number of winds (can be fractional)
    """
    if layer_thickness_mm <= 0:
        return 0.0

    effective_thickness = layer_thickness_mm * tension_factor
    available_radial_space = outer_radius_mm - inner_radius_mm

    if available_radial_space <= 0 or effective_thickness <= 0:
        return 0.0

    return available_radial_space / effective_thickness


def calculate_electrode_length_analytical(
    num_winds: float, inner_radius_mm: float, layer_thickness_mm: float, tension_factor: float = 1.0
) -> float:
    """Calculate total electrode length using analytical formula.

    For an Archimedean spiral, the total length is:
    L = π × n × (2×r_i + (n-1)×t)

    where:
    - n = number of winds
    - r_i = inner radius
    - t = layer thickness

    Args:
        num_winds: Number of complete winds
        inner_radius_mm: Mandrel radius [mm]
        layer_thickness_mm: Layer thickness [mm]
        tension_factor: Compression factor

    Returns:
        Total electrode length [mm]
    """
    if num_winds <= 0:
        return 0.0

    effective_thickness = layer_thickness_mm * tension_factor

    # Analytical formula for spiral length
    length_mm = math.pi * num_winds * (2 * inner_radius_mm + (num_winds - 1) * effective_thickness)

    return length_mm


def calculate_electrode_length_iterative(
    num_winds: int, inner_radius_mm: float, layer_thickness_mm: float, tension_factor: float = 1.0
) -> float:
    """Calculate total electrode length by summing circumferences.

    More accurate for cells with significant compression gradients.

    Args:
        num_winds: Number of complete winds (integer)
        inner_radius_mm: Mandrel radius [mm]
        layer_thickness_mm: Layer thickness [mm]
        tension_factor: Average compression factor

    Returns:
        Total electrode length [mm]
    """
    if num_winds <= 0:
        return 0.0

    effective_thickness = layer_thickness_mm * tension_factor
    total_length = 0.0

    for i in range(int(num_winds)):
        radius = inner_radius_mm + i * effective_thickness
        circumference = 2 * math.pi * radius
        total_length += circumference

    # Add partial wind if num_winds is not integer
    fractional_wind = num_winds - int(num_winds)
    if fractional_wind > 0:
        radius = inner_radius_mm + int(num_winds) * effective_thickness
        circumference = 2 * math.pi * radius
        total_length += circumference * fractional_wind

    return total_length


def calculate_electrode_width(
    can_inner_length_mm: float,
    header_clearance_mm: float,
    bottom_clearance_mm: float,
    tab_type: TabType,
    anode_foil_extension_mm: float = 0.0,
    cathode_foil_extension_mm: float = 0.0,
) -> tuple[float, float, float]:
    """Calculate electrode widths considering clearances and tab design.

    Args:
        can_inner_length_mm: Internal can length [mm]
        header_clearance_mm: Clearance at header end [mm]
        bottom_clearance_mm: Clearance at bottom end [mm]
        tab_type: Traditional or tabless design
        anode_foil_extension_mm: Anode foil extension for tabless [mm]
        cathode_foil_extension_mm: Cathode foil extension for tabless [mm]

    Returns:
        Tuple of (separator_width_mm, cathode_active_width_mm, anode_active_width_mm)
    """
    # Total available width
    total_width = can_inner_length_mm - header_clearance_mm - bottom_clearance_mm

    if tab_type == TabType.TABLESS:
        # For tabless design:
        # - Separator covers full width
        # - Anode foil extends beyond coating at bottom (for can welding)
        # - Cathode foil extends beyond coating at top (for cap welding)
        separator_width = total_width
        cathode_active_width = total_width - cathode_foil_extension_mm
        anode_active_width = total_width - anode_foil_extension_mm
    else:
        # For traditional design:
        # - All components have same width
        # - Tabs are separate components
        separator_width = total_width
        cathode_active_width = total_width
        anode_active_width = total_width

    return separator_width, cathode_active_width, anode_active_width


def calculate_jelly_roll(
    geometry: CylindricalGeometry,
    winding: WindingConfig,
    cathode: CathodeMaterial,
    anode: AnodeMaterial,
    separator: SeparatorMaterial,
    header_clearance_mm: float = 1.0,
    bottom_clearance_mm: float = 0.5,
) -> JellyRollResult:
    """Calculate complete jelly roll properties.

    This is the main calculation function that combines all individual
    calculations to produce the full jelly roll specification.

    Args:
        geometry: Cylindrical cell geometry
        winding: Winding configuration
        cathode: Cathode material
        anode: Anode material
        separator: Separator material
        header_clearance_mm: Clearance between jelly roll and header [mm]
        bottom_clearance_mm: Clearance between jelly roll and can bottom [mm]

    Returns:
        JellyRollResult with all calculated properties
    """
    # 1. Calculate layer thickness
    layer_thk = calculate_layer_thickness(cathode, anode, separator)

    # 2. Calculate available space
    inner_radius = winding.mandrel_diameter_mm / 2
    max_outer_radius = (geometry.can_inner_diameter_mm / 2) - winding.winding_clearance_mm

    # 3. Calculate number of winds
    num_winds = calculate_number_of_winds(
        inner_radius_mm=inner_radius,
        outer_radius_mm=max_outer_radius,
        layer_thickness_mm=layer_thk.single_layer_mm,
        tension_factor=winding.winding_tension_factor,
    )

    # 4. Calculate electrode length
    electrode_length_mm = calculate_electrode_length_analytical(
        num_winds=num_winds,
        inner_radius_mm=inner_radius,
        layer_thickness_mm=layer_thk.single_layer_mm,
        tension_factor=winding.winding_tension_factor,
    )
    electrode_length_m = electrode_length_mm / 1000.0

    # 5. Calculate electrode widths
    separator_width, cathode_width, anode_width = calculate_electrode_width(
        can_inner_length_mm=geometry.can_inner_length_mm,
        header_clearance_mm=header_clearance_mm,
        bottom_clearance_mm=bottom_clearance_mm,
        tab_type=winding.tab_type,
        anode_foil_extension_mm=winding.anode_foil_extension_mm or 0.0,
        cathode_foil_extension_mm=winding.cathode_foil_extension_mm or 0.0,
    )

    # 6. Calculate electrode areas (both sides coated)
    # Area = length × width × 2 (both sides)
    cathode_area_cm2 = (electrode_length_mm * cathode_width / 100) * 2
    anode_area_cm2 = (electrode_length_mm * anode_width / 100) * 2
    separator_area_cm2 = (electrode_length_mm * separator_width / 100) * 2  # Two separators

    # 7. Calculate actual outer diameter
    effective_thickness = layer_thk.single_layer_mm * winding.winding_tension_factor
    actual_outer_diameter = winding.mandrel_diameter_mm + 2 * num_winds * effective_thickness

    # 8. Calculate compression ratio
    theoretical_radial_growth = num_winds * layer_thk.single_layer_mm
    actual_radial_growth = num_winds * effective_thickness
    compression_ratio = (
        actual_radial_growth / theoretical_radial_growth if theoretical_radial_growth > 0 else 1.0
    )

    return JellyRollResult(
        num_winds=num_winds,
        electrode_length_m=electrode_length_m,
        anode_area_cm2=anode_area_cm2,
        cathode_area_cm2=cathode_area_cm2,
        separator_area_cm2=separator_area_cm2,
        separator_length_m=electrode_length_m,  # Separator has same length as electrodes
        jelly_roll_outer_diameter_mm=actual_outer_diameter,
        jelly_roll_height_mm=separator_width,
        compression_ratio=compression_ratio,
        electrode_width_mm=cathode_width,  # Use cathode width as reference
        layer_thickness_um=layer_thk.single_layer_um,
    )


def calculate_jelly_roll_pore_volume(
    jelly_roll: JellyRollResult,
    cathode: CathodeMaterial,
    anode: AnodeMaterial,
    separator: SeparatorMaterial,
    cathode_porosity_pct: float,
    anode_porosity_pct: float,
) -> tuple[float, float, float]:
    """Calculate pore volumes in jelly roll for electrolyte calculation.

    Args:
        jelly_roll: Calculated jelly roll result
        cathode: Cathode material
        anode: Anode material
        separator: Separator material
        cathode_porosity_pct: Cathode coating porosity [%]
        anode_porosity_pct: Anode coating porosity [%]

    Returns:
        Tuple of (cathode_pores_ml, anode_pores_ml, separator_pores_ml)
    """
    # Cathode pore volume
    # Single-side area × coating thickness × porosity × 2 sides
    cathode_coating_vol_cm3 = (
        jelly_roll.cathode_area_single_side_cm2
        * cathode.coating_thickness_0pct_um
        / 10000  # µm to cm
        * 2  # Both sides already in single_side_area, but we need both sides
    )
    cathode_pores_ml = cathode_coating_vol_cm3 * cathode_porosity_pct / 100

    # Anode pore volume
    anode_coating_vol_cm3 = (
        jelly_roll.anode_area_single_side_cm2 * anode.coating_thickness_0pct_um / 10000 * 2
    )
    anode_pores_ml = anode_coating_vol_cm3 * anode_porosity_pct / 100

    # Separator pore volume
    # Separator area already includes both separators
    separator_vol_cm3 = (
        jelly_roll.separator_area_cm2
        / 2  # Single separator area
        * separator.thickness_um
        / 10000
    )
    separator_pores_ml = separator_vol_cm3 * separator.porosity_pct / 100

    return cathode_pores_ml, anode_pores_ml, separator_pores_ml


def estimate_jelly_roll_volume(jelly_roll: JellyRollResult, mandrel_diameter_mm: float) -> float:
    """Estimate total jelly roll volume.

    Args:
        jelly_roll: Calculated jelly roll result
        mandrel_diameter_mm: Mandrel/core diameter [mm]

    Returns:
        Jelly roll volume [cm³]
    """
    # Annular cylinder volume
    r_outer = jelly_roll.jelly_roll_outer_diameter_mm / 2 / 10  # mm to cm
    r_inner = mandrel_diameter_mm / 2 / 10  # mm to cm
    height = jelly_roll.jelly_roll_height_mm / 10  # mm to cm

    volume = math.pi * height * (r_outer**2 - r_inner**2)
    return volume
