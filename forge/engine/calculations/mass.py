"""Mass calculation formulas for FORGE engine.

This module implements all mass calculation formulas from Section 5.1 of the spec:
- Cathode mass (coating + collector)
- Anode mass (coating + collector)
- Separator mass
- Electrolyte mass
- Pouch housing mass
- Prismatic housing mass
- Tab mass
"""

from dataclasses import dataclass

from forge.engine.models.materials import PackagingLayer


# Default material densities [g/cm³]
DENSITY_ALUMINUM = 2.70
DENSITY_COPPER = 8.96


@dataclass
class ElectrodeMassResult:
    """Result of electrode mass calculation.

    Attributes:
        coating_g: Coating (active material) mass [g]
        collector_g: Current collector foil mass [g]
        total_g: Total electrode mass [g]
    """

    coating_g: float
    collector_g: float

    @property
    def total_g(self) -> float:
        """Total electrode mass [g]."""
        return self.coating_g + self.collector_g


@dataclass
class ElectrolyteMassResult:
    """Result of electrolyte mass calculation.

    Attributes:
        calc_volume_ml: Calculated pore volume [ml]
        used_volume_ml: Used volume (with excess factor) [ml]
        mass_g: Electrolyte mass [g]
    """

    calc_volume_ml: float
    used_volume_ml: float
    mass_g: float


def calculate_cathode_mass(
    cathode_area_cm2: float,
    cathode_sheets: int,
    loading_mgcm2: float,
    collector_thk_um: float,
    al_density_gcm3: float = DENSITY_ALUMINUM,
    flag_area_cm2: float = 0.0,
) -> ElectrodeMassResult:
    """Calculate cathode coating and collector masses.

    Args:
        cathode_area_cm2: Cathode sheet area [cm²]
        cathode_sheets: Number of cathode sheets
        loading_mgcm2: Cathode coating loading [mg/cm²]
        collector_thk_um: Aluminum collector foil thickness [µm]
        al_density_gcm3: Aluminum density [g/cm³]
        flag_area_cm2: Flag (tab extension) area [cm²], default 0 for backward compat

    Returns:
        ElectrodeMassResult with coating and collector masses

    Formula:
        coating_mass = area × sheets × loading × 2 (double-sided) / 1000 [mg→g]
        collector_mass = (area + flag_area) × sheets × thickness × density / 10000
    """
    # Coating mass (double-sided coating) - only on electrode area, not flag
    coating_mass_g = cathode_area_cm2 * cathode_sheets * loading_mgcm2 * 2 / 1000

    # Collector (aluminum foil) mass - includes flag area per C# formula
    # thickness [µm] × density [g/cm³] / 10000 → [g/cm²]
    total_collector_area_cm2 = cathode_area_cm2 + flag_area_cm2
    collector_mass_g = (
        total_collector_area_cm2 * cathode_sheets * collector_thk_um * al_density_gcm3 / 10000
    )

    return ElectrodeMassResult(coating_g=coating_mass_g, collector_g=collector_mass_g)


def calculate_anode_mass(
    anode_area_cm2: float,
    anode_sheets: int,
    loading_mgcm2: float,
    collector_thk_um: float,
    cu_density_gcm3: float = DENSITY_COPPER,
    flag_area_cm2: float = 0.0,
) -> ElectrodeMassResult:
    """Calculate anode coating and collector masses.

    Args:
        anode_area_cm2: Anode sheet area [cm²]
        anode_sheets: Number of anode sheets
        loading_mgcm2: Anode coating loading [mg/cm²]
        collector_thk_um: Copper collector foil thickness [µm]
        cu_density_gcm3: Copper density [g/cm³]
        flag_area_cm2: Flag (tab extension) area [cm²], default 0 for backward compat

    Returns:
        ElectrodeMassResult with coating and collector masses

    Formula:
        coating_mass = area × sheets × loading × 2 (double-sided) / 1000 [mg→g]
        collector_mass = (area + flag_area) × sheets × thickness × density / 10000
    """
    # Coating mass (double-sided coating) - only on electrode area, not flag
    coating_mass_g = anode_area_cm2 * anode_sheets * loading_mgcm2 * 2 / 1000

    # Collector (copper foil) mass - includes flag area per C# formula
    total_collector_area_cm2 = anode_area_cm2 + flag_area_cm2
    collector_mass_g = (
        total_collector_area_cm2 * anode_sheets * collector_thk_um * cu_density_gcm3 / 10000
    )

    return ElectrodeMassResult(coating_g=coating_mass_g, collector_g=collector_mass_g)


def calculate_separator_mass(
    separator_area_cm2: float, separator_sheets: int, areal_weight_mgcm2: float
) -> float:
    """Calculate separator mass from areal weight.

    Args:
        separator_area_cm2: Separator sheet area [cm²]
        separator_sheets: Number of separator sheets
        areal_weight_mgcm2: Separator areal weight [mg/cm²]

    Returns:
        Separator mass [g]

    Formula:
        mass = area × sheets × areal_weight / 1000 [mg→g]
    """
    return separator_area_cm2 * separator_sheets * areal_weight_mgcm2 / 1000


def calculate_electrolyte_mass(
    pores_anode_ml: float,
    pores_cathode_ml: float,
    pores_separator_ml: float,
    density_gcm3: float,
    excess_factor: float = 1.10,
    user_override_ml: float | None = None,
) -> ElectrolyteMassResult:
    """Calculate electrolyte mass from pore volumes.

    Args:
        pores_anode_ml: Anode pore volume [ml]
        pores_cathode_ml: Cathode pore volume [ml]
        pores_separator_ml: Separator pore volume [ml]
        density_gcm3: Electrolyte density [g/cm³]
        excess_factor: Electrolyte excess factor (default 1.10 = 10% excess)
        user_override_ml: Optional user-specified volume [ml]

    Returns:
        ElectrolyteMassResult with volumes and mass
    """
    calc_volume_ml = pores_anode_ml + pores_cathode_ml + pores_separator_ml

    if user_override_ml is not None and user_override_ml > 0:
        used_volume_ml = user_override_ml
    else:
        used_volume_ml = calc_volume_ml * excess_factor

    mass_g = used_volume_ml * density_gcm3

    return ElectrolyteMassResult(
        calc_volume_ml=calc_volume_ml, used_volume_ml=used_volume_ml, mass_g=mass_g
    )


def calculate_pouch_housing_mass(
    cell_height_mm: float, cell_width_mm: float, case_composition: list[PackagingLayer]
) -> float:
    """Calculate pouch foil mass from composition layers.

    Args:
        cell_height_mm: Cell external height [mm]
        cell_width_mm: Cell external width [mm]
        case_composition: List of packaging layers (e.g., PET/Al/PP)

    Returns:
        Pouch housing mass [g]

    Formula:
        cell_area = height × width / 100 [mm²→cm²]
        both_sides = cell_area × 2
        areal_weight = sum(layer.thickness × layer.eff_density / 10) [mg/cm²]
        mass = both_sides × areal_weight / 1000 [mg→g]
    """
    # Cell area (mm² → cm²)
    cell_area_cm2 = cell_height_mm * cell_width_mm / 100

    # Both sides of pouch
    both_sides_cm2 = cell_area_cm2 * 2

    # Sum areal weight from all layers [mg/cm²]
    areal_weight_mgcm2 = sum(
        layer.thickness_um * layer.effective_density_gcm3 / 10 for layer in case_composition
    )

    # Mass (mg/cm² × cm² → g)
    return both_sides_cm2 * areal_weight_mgcm2 / 1000


def calculate_prismatic_housing_mass(
    cell_height_mm: float,
    cell_width_mm: float,
    cell_thickness_mm: float,
    wall_top_mm: float,
    wall_bottom_mm: float,
    wall_side_xy_mm: float,
    wall_side_zy_mm: float,
    al_density_gcm3: float = DENSITY_ALUMINUM,
    header_mass_g: float = 120.0,
) -> float:
    """Calculate prismatic aluminum case mass.

    Args:
        cell_height_mm: External cell height [mm]
        cell_width_mm: External cell width [mm]
        cell_thickness_mm: External cell thickness [mm]
        wall_top_mm: Top lid thickness [mm]
        wall_bottom_mm: Bottom lid thickness [mm]
        wall_side_xy_mm: Side wall thickness in XY plane [mm]
        wall_side_zy_mm: Side wall thickness in ZY plane [mm]
        al_density_gcm3: Aluminum density [g/cm³]
        header_mass_g: Header/terminal assembly mass [g]

    Returns:
        Total housing mass (case walls + header) [g]
    """
    # Convert to cm for volume calculation
    h_cm = cell_height_mm / 10
    w_cm = cell_width_mm / 10
    t_cm = cell_thickness_mm / 10

    t_top_cm = wall_top_mm / 10
    t_bot_cm = wall_bottom_mm / 10
    t_xy_cm = wall_side_xy_mm / 10
    t_zy_cm = wall_side_zy_mm / 10

    # Top/Bottom plates (averaged thickness)
    mass_top_bot = 2 * w_cm * t_cm * ((t_top_cm + t_bot_cm) / 2) * al_density_gcm3

    # Front/Back plates (XY walls)
    mass_front_back = 2 * w_cm * h_cm * t_xy_cm * al_density_gcm3

    # Left/Right plates (ZY walls)
    mass_left_right = 2 * t_cm * h_cm * t_zy_cm * al_density_gcm3

    case_walls_g = mass_top_bot + mass_front_back + mass_left_right

    return case_walls_g + header_mass_g


def calculate_tab_mass(
    height_mm: float, width_mm: float, thickness_mm: float, density_gcm3: float
) -> float:
    """Calculate single tab mass.

    Args:
        height_mm: Tab height [mm]
        width_mm: Tab width [mm]
        thickness_mm: Tab thickness [mm]
        density_gcm3: Tab material density [g/cm³]

    Returns:
        Tab mass [g]

    Formula:
        volume = height × width × thickness / 1000 [mm³→cm³]
        mass = volume × density [g]
    """
    volume_cm3 = height_mm * width_mm * thickness_mm / 1000
    return volume_cm3 * density_gcm3
