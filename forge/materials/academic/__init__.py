"""Custom PyBaMM-compatible parameter sets for academic-validated cells.

This module provides parameter sets derived from peer-reviewed publications
with complete electrode-level characterization data.

Available Parameter Sets:
- Gunter2022: LG E78 Pouch (NCM652015/Graphite) - DOI: 10.1149/1945-7111/ac4e11
- Stock2023: CATL 161Ah LFP Prismatic - DOI: 10.1016/j.electacta.2023.143341
- Heenan2020: LG MJ1 18650 (NMC811/Graphite+Si) - DOI: 10.1149/1945-7111/ab728d
"""

from .gunter2022_lge78 import get_parameter_values as get_gunter2022
from .heenan2020_lgmj1 import get_parameter_values as get_heenan2020
from .stock2023_catl161 import get_parameter_values as get_stock2023

# Registry of custom parameter sets
CUSTOM_PARAMETER_SETS = {
    "Gunter2022": get_gunter2022,
    "Stock2023": get_stock2023,
    "Heenan2020": get_heenan2020,
}

# Chemistry mapping for custom sets
CUSTOM_CHEMISTRY_MAP = {
    "Gunter2022": ("NCM652015", "Graphite"),
    "Stock2023": ("LFP", "Graphite"),
    "Heenan2020": ("NMC811", "Graphite_Si"),
}

# Cathode specific capacities for custom sets [mAh/g]
CUSTOM_CATHODE_CAPACITIES = {
    "NCM652015": 180.0,  # Ni65 Co20 Mn15
    "LFP": 150.0,  # LiFePO4
    "NMC811": 190.0,  # High nickel
}


def get_custom_parameters(set_name: str) -> dict:
    """Load custom parameter set by name.

    Args:
        set_name: Name of the parameter set (e.g., "Gunter2022")

    Returns:
        Dictionary of parameters compatible with PyBaMM ParameterValues

    Raises:
        ValueError: If set_name is not found
    """
    if set_name not in CUSTOM_PARAMETER_SETS:
        available = ", ".join(CUSTOM_PARAMETER_SETS.keys())
        raise ValueError(f"Unknown parameter set '{set_name}'. Available: {available}")

    return CUSTOM_PARAMETER_SETS[set_name]()


def list_custom_parameter_sets() -> list[str]:
    """List available custom parameter sets.

    Returns:
        List of parameter set names
    """
    return list(CUSTOM_PARAMETER_SETS.keys())


__all__ = [
    "get_custom_parameters",
    "list_custom_parameter_sets",
    "CUSTOM_PARAMETER_SETS",
    "CUSTOM_CHEMISTRY_MAP",
    "CUSTOM_CATHODE_CAPACITIES",
]
