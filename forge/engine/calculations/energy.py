"""Energy calculation formulas for FORGE engine.

This module implements energy-related calculations from Sections 5.2-5.3 of the spec:
- Energy density (gravimetric and volumetric)
- Areal characteristics (capacity and energy per area)
- Cell capacity from electrode properties
- ECU (Electrochemical Unit) metrics
"""

from dataclasses import dataclass


@dataclass
class EnergyDensityResult:
    """Result of energy density calculation.

    Attributes:
        cell_energy_wh: Cell energy [Wh]
        gravimetric_whkg: Gravimetric energy density [Wh/kg]
        volumetric_cell_whl: Volumetric energy density based on cell volume [Wh/L]
        volumetric_stack_whl: Volumetric energy density based on stack volume [Wh/L]
    """

    cell_energy_wh: float
    gravimetric_whkg: float
    volumetric_cell_whl: float
    volumetric_stack_whl: float


@dataclass
class ArealCharacteristicsResult:
    """Result of areal characteristics calculation.

    Attributes:
        total_cathode_area_cm2: Total cathode area [cm²]
        areal_capacity_mahcm2: Areal capacity [mAh/cm²]
        areal_energy_mwhcm2: Areal energy [mWh/cm²]
    """

    total_cathode_area_cm2: float
    areal_capacity_mahcm2: float
    areal_energy_mwhcm2: float


@dataclass
class ECUMetricsResult:
    """Result of Electrochemical Unit (ECU) calculation.

    The ECU represents the active repeating unit of a cell - just the electrode
    coatings, half of each collector, and separator. It excludes housing, tabs,
    excess electrolyte, etc. ECU metrics show the theoretical efficiency of the
    electrode stack design.

    Attributes:
        ecu_thickness_um: ECU thickness (one repeating unit) [um]
        ecu_volume_cm3: Total ECU volume [cm³]
        ecu_energy_density_wh_l: ECU volumetric energy density [Wh/L]
    """

    ecu_thickness_um: float
    ecu_volume_cm3: float
    ecu_energy_density_wh_l: float


def calculate_energy_density(
    capacity_ah: float,
    nominal_voltage_v: float,
    cell_mass_g: float,
    cell_volume_cm3: float,
    stack_volume_cm3: float,
) -> EnergyDensityResult:
    """Calculate all energy density metrics.

    Args:
        capacity_ah: Cell capacity [Ah]
        nominal_voltage_v: Nominal voltage [V]
        cell_mass_g: Total cell mass [g]
        cell_volume_cm3: External cell volume [cm³]
        stack_volume_cm3: Internal stack volume [cm³]

    Returns:
        EnergyDensityResult with all energy density metrics

    Formulas:
        energy = capacity × voltage [Wh]
        gravimetric = energy / mass × 1000 [Wh/kg]
        volumetric = energy / volume × 1000 [Wh/L]
    """
    cell_energy_wh = capacity_ah * nominal_voltage_v

    # Gravimetric: Wh / g × 1000 → Wh/kg
    gravimetric_whkg = cell_energy_wh / cell_mass_g * 1000 if cell_mass_g > 0 else 0.0

    # Volumetric: Wh / cm³ × 1000 → Wh/L (since 1 L = 1000 cm³)
    volumetric_cell_whl = cell_energy_wh / cell_volume_cm3 * 1000 if cell_volume_cm3 > 0 else 0.0
    volumetric_stack_whl = cell_energy_wh / stack_volume_cm3 * 1000 if stack_volume_cm3 > 0 else 0.0

    return EnergyDensityResult(
        cell_energy_wh=cell_energy_wh,
        gravimetric_whkg=gravimetric_whkg,
        volumetric_cell_whl=volumetric_cell_whl,
        volumetric_stack_whl=volumetric_stack_whl,
    )


def calculate_areal_characteristics(
    capacity_ah: float, nominal_voltage_v: float, cathode_area_cm2: float, cathode_sheets: int
) -> ArealCharacteristicsResult:
    """Calculate areal capacity and energy.

    Args:
        capacity_ah: Cell capacity [Ah]
        nominal_voltage_v: Nominal voltage [V]
        cathode_area_cm2: Single cathode sheet area [cm²]
        cathode_sheets: Number of cathode sheets

    Returns:
        ArealCharacteristicsResult with areal metrics

    Formulas:
        total_area = area × sheets [cm²]
        areal_capacity = capacity × 1000 / total_area [mAh/cm²]
        areal_energy = areal_capacity × voltage [mWh/cm²]
    """
    total_cathode_area_cm2 = cathode_area_cm2 * cathode_sheets

    if total_cathode_area_cm2 > 0:
        # Ah × 1000 / cm² → mAh/cm²
        areal_capacity_mahcm2 = capacity_ah * 1000 / total_cathode_area_cm2
        areal_energy_mwhcm2 = areal_capacity_mahcm2 * nominal_voltage_v
    else:
        areal_capacity_mahcm2 = 0.0
        areal_energy_mwhcm2 = 0.0

    return ArealCharacteristicsResult(
        total_cathode_area_cm2=total_cathode_area_cm2,
        areal_capacity_mahcm2=areal_capacity_mahcm2,
        areal_energy_mwhcm2=areal_energy_mwhcm2,
    )


def calculate_cell_capacity(
    cathode_area_cm2: float, cathode_sheets: int, loading_mgcm2: float, spec_capacity_mahg: float
) -> float:
    """Calculate cell capacity from electrode properties.

    This calculates the theoretical capacity based on cathode active material.

    Args:
        cathode_area_cm2: Single cathode sheet area [cm²]
        cathode_sheets: Number of cathode sheets
        loading_mgcm2: Cathode loading (single side) [mg/cm²]
        spec_capacity_mahg: Specific capacity of cathode material [mAh/g]

    Returns:
        Cell capacity [Ah]

    Formula:
        total_area = area × sheets [cm²]
        active_mass = total_area × loading × 2 (double-sided) [mg]
        capacity = active_mass × spec_capacity / 1000000 [mAh→Ah]
    """
    total_cathode_area_cm2 = cathode_area_cm2 * cathode_sheets

    # Active material mass (double-sided coating)
    active_mass_mg = total_cathode_area_cm2 * loading_mgcm2 * 2

    # Capacity: mg × mAh/g = µAh, / 1000000 → Ah
    capacity_ah = active_mass_mg * spec_capacity_mahg / 1_000_000

    return capacity_ah


def calculate_np_ratio(
    cathode_area_cm2: float,
    cathode_sheets: int,
    cathode_loading_mgcm2: float,
    cathode_spec_capacity_mahg: float,
    anode_area_cm2: float,
    anode_sheets: int,
    anode_loading_mgcm2: float,
    anode_spec_capacity_mahg: float,
) -> float:
    """Calculate the N/P ratio (anode to cathode capacity ratio).

    The N/P ratio is an important design parameter. Typically > 1.0 to prevent
    lithium plating during charging.

    Args:
        cathode_area_cm2: Single cathode sheet area [cm²]
        cathode_sheets: Number of cathode sheets
        cathode_loading_mgcm2: Cathode loading (single side) [mg/cm²]
        cathode_spec_capacity_mahg: Cathode specific capacity [mAh/g]
        anode_area_cm2: Single anode sheet area [cm²]
        anode_sheets: Number of anode sheets
        anode_loading_mgcm2: Anode loading (single side) [mg/cm²]
        anode_spec_capacity_mahg: Anode specific capacity [mAh/g]

    Returns:
        N/P ratio (dimensionless)
    """
    # Total capacities (in mAh)
    cathode_capacity = (
        cathode_area_cm2
        * cathode_sheets
        * cathode_loading_mgcm2
        * 2
        * cathode_spec_capacity_mahg
        / 1000
    )
    anode_capacity = (
        anode_area_cm2 * anode_sheets * anode_loading_mgcm2 * 2 * anode_spec_capacity_mahg / 1000
    )

    if cathode_capacity > 0:
        return anode_capacity / cathode_capacity
    return 0.0


def calculate_ecu_metrics(
    cathode_coating_100pct_um: float,
    anode_coating_100pct_um: float,
    cathode_collector_um: float,
    anode_collector_um: float,
    separator_um: float,
    cathode_area_cm2: float,
    cathode_sheets_cell: int,
    energy_wh: float,
) -> ECUMetricsResult:
    """Calculate Electrochemical Unit (ECU) metrics.

    The ECU represents the active repeating unit of a cell - coatings, half of
    each collector, and separator. This metric shows theoretical electrode
    stack efficiency excluding packaging overhead.

    Args:
        cathode_coating_100pct_um: Cathode coating thickness at 100% SoC [um]
        anode_coating_100pct_um: Anode coating thickness at 100% SoC [um]
        cathode_collector_um: Cathode collector thickness [um]
        anode_collector_um: Anode collector thickness [um]
        separator_um: Separator thickness [um]
        cathode_area_cm2: Single cathode sheet area [cm²]
        cathode_sheets_cell: Total cathode sheets in cell
        energy_wh: Cell energy [Wh]

    Returns:
        ECUMetricsResult with ECU thickness, volume, and energy density

    Formulas (from C#):
        ECU_Thickness = CathodeCoating100 + AnodeCoating100
                       + (CathodeCollector + AnodeCollector) / 2.0
                       + SeparatorThk
        ECU_Volume = (ECU_Thickness / 10000) × CathodeArea × CathodeSheets
        ECU_EnergyDensity = Energy / ECU_Volume × 1000 [Wh/L]
    """
    # ECU thickness = cathode coating + anode coating + avg collector + separator
    ecu_thickness_um = (
        cathode_coating_100pct_um
        + anode_coating_100pct_um
        + (cathode_collector_um + anode_collector_um) / 2.0
        + separator_um
    )

    # ECU volume = thickness × area × sheet count
    # thickness [um] / 10000 → [cm], × area [cm²] × sheets → [cm³]
    ecu_volume_cm3 = (ecu_thickness_um / 10000.0) * cathode_area_cm2 * cathode_sheets_cell

    # ECU volumetric energy density [Wh/L]
    # Wh / cm³ × 1000 → Wh/L (since 1 L = 1000 cm³)
    ecu_energy_density_wh_l = (energy_wh / ecu_volume_cm3 * 1000) if ecu_volume_cm3 > 0 else 0.0

    return ECUMetricsResult(
        ecu_thickness_um=ecu_thickness_um,
        ecu_volume_cm3=ecu_volume_cm3,
        ecu_energy_density_wh_l=ecu_energy_density_wh_l,
    )
