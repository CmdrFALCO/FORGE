"""FORGE engine calculations package.

Pure math modules for battery cell calculations:
- energy: Energy density, areal characteristics, cell capacity, ECU metrics
- mass: Electrode, separator, electrolyte, housing, and tab mass calculations
- stack: Sheet counts, stack thickness at different states, pore volumes
- winding: Jelly roll winding geometry for cylindrical cells
- cylindrical_housing: Cylindrical cell housing component masses
"""

from .cylindrical_housing import (
    CylindricalHousingResult,
    calculate_can_body_mass,
    calculate_can_bottom_mass,
    calculate_cylindrical_housing_mass,
    calculate_tab_or_foil_mass,
    calculate_tabless_foil_extension_mass,
    calculate_traditional_tab_mass,
    create_typical_21700_header,
    create_typical_4680_header,
    estimate_18650_header_mass,
    estimate_21700_header_mass,
    estimate_4680_header_mass,
)
from .energy import (
    ArealCharacteristicsResult,
    ECUMetricsResult,
    EnergyDensityResult,
    calculate_areal_characteristics,
    calculate_cell_capacity,
    calculate_ecu_metrics,
    calculate_energy_density,
    calculate_np_ratio,
)
from .mass import (
    ElectrodeMassResult,
    ElectrolyteMassResult,
    calculate_anode_mass,
    calculate_cathode_mass,
    calculate_electrolyte_mass,
    calculate_pouch_housing_mass,
    calculate_prismatic_housing_mass,
    calculate_separator_mass,
    calculate_tab_mass,
)
from .stack import (
    calculate_pore_volumes,
    calculate_sheet_counts,
    calculate_stack_thickness,
)
from .winding import (
    LayerThickness,
    calculate_compressed_thickness,
    calculate_electrode_length_analytical,
    calculate_electrode_length_iterative,
    calculate_electrode_width,
    calculate_jelly_roll,
    calculate_jelly_roll_pore_volume,
    calculate_layer_thickness,
    calculate_number_of_winds,
    estimate_jelly_roll_volume,
)

__all__ = [
    # Energy
    "ArealCharacteristicsResult",
    "ECUMetricsResult",
    "EnergyDensityResult",
    "calculate_areal_characteristics",
    "calculate_cell_capacity",
    "calculate_ecu_metrics",
    "calculate_energy_density",
    "calculate_np_ratio",
    # Mass
    "ElectrodeMassResult",
    "ElectrolyteMassResult",
    "calculate_anode_mass",
    "calculate_cathode_mass",
    "calculate_electrolyte_mass",
    "calculate_pouch_housing_mass",
    "calculate_prismatic_housing_mass",
    "calculate_separator_mass",
    "calculate_tab_mass",
    # Stack
    "calculate_pore_volumes",
    "calculate_sheet_counts",
    "calculate_stack_thickness",
    # Winding
    "LayerThickness",
    "calculate_compressed_thickness",
    "calculate_electrode_length_analytical",
    "calculate_electrode_length_iterative",
    "calculate_electrode_width",
    "calculate_jelly_roll",
    "calculate_jelly_roll_pore_volume",
    "calculate_layer_thickness",
    "calculate_number_of_winds",
    "estimate_jelly_roll_volume",
    # Cylindrical Housing
    "CylindricalHousingResult",
    "calculate_can_body_mass",
    "calculate_can_bottom_mass",
    "calculate_cylindrical_housing_mass",
    "calculate_tab_or_foil_mass",
    "calculate_tabless_foil_extension_mass",
    "calculate_traditional_tab_mass",
    "create_typical_21700_header",
    "create_typical_4680_header",
    "estimate_18650_header_mass",
    "estimate_21700_header_mass",
    "estimate_4680_header_mass",
]
