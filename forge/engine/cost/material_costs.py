"""
Material cost database for CellCAD cost estimation.

This module provides realistic 2024/2025 market prices for battery materials
organized by category. Prices are in $/kg unless otherwise noted.

Data sources:
- Benchmark Mineral Intelligence
- BloombergNEF
- Industry reports and supplier quotes

Note: Prices are approximate and vary by region, volume, and supplier.
These defaults represent typical market conditions and should be updated
periodically to reflect current market prices.
"""

from dataclasses import dataclass
from enum import Enum


class CostRegion(Enum):
    """Geographic regions for cost adjustments."""

    GLOBAL = "global"
    CHINA = "china"
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"
    ASIA_PACIFIC = "asia_pacific"


@dataclass
class MaterialCost:
    """Cost information for a material."""

    price_per_kg: float
    unit: str = "$/kg"
    source: str = "market_estimate"
    year: int = 2024
    notes: str = ""


# =============================================================================
# CATHODE ACTIVE MATERIALS ($/kg)
# =============================================================================
# Prices vary significantly based on nickel content and supply chain

CATHODE_COSTS: dict[str, MaterialCost] = {
    # NMC variants - price scales with nickel content
    "NMC111": MaterialCost(
        price_per_kg=22.0, notes="Balanced Ni:Mn:Co ratio, lower energy but stable"
    ),
    "NMC523": MaterialCost(price_per_kg=24.0, notes="Mid-nickel variant, good balance"),
    "NMC622": MaterialCost(price_per_kg=26.0, notes="Higher nickel, improved energy density"),
    "NMC811": MaterialCost(price_per_kg=28.0, notes="High nickel, highest energy density NMC"),
    "NMC955": MaterialCost(price_per_kg=30.0, notes="Ultra-high nickel, cutting edge"),
    # LFP - Iron phosphate (cheaper, no cobalt/nickel)
    "LFP": MaterialCost(price_per_kg=12.0, notes="Lithium iron phosphate, lower cost, safer"),
    "LFMP": MaterialCost(price_per_kg=14.0, notes="Manganese-doped LFP, slightly higher voltage"),
    # NCA - Nickel Cobalt Aluminum (Tesla/Panasonic)
    "NCA": MaterialCost(price_per_kg=29.0, notes="High energy density, used in Tesla cells"),
    # LCO - Lithium Cobalt Oxide (consumer electronics)
    "LCO": MaterialCost(price_per_kg=35.0, notes="High cost due to cobalt, used in phones/laptops"),
    # LMFP - Lithium Manganese Iron Phosphate
    "LMFP": MaterialCost(price_per_kg=15.0, notes="Higher voltage LFP variant"),
    # Sodium-ion cathodes (emerging)
    "Prussian_Blue": MaterialCost(price_per_kg=8.0, notes="Sodium-ion cathode, very low cost"),
    "Na_Layered_Oxide": MaterialCost(price_per_kg=10.0, notes="Sodium-ion layered oxide cathode"),
}


# =============================================================================
# ANODE ACTIVE MATERIALS ($/kg)
# =============================================================================

ANODE_COSTS: dict[str, MaterialCost] = {
    # Graphite variants
    "Graphite_Natural": MaterialCost(
        price_per_kg=8.0, notes="Natural graphite, lower cost, lower performance"
    ),
    "Graphite_Synthetic": MaterialCost(
        price_per_kg=12.0, notes="Synthetic graphite, higher purity and performance"
    ),
    "Graphite": MaterialCost(
        price_per_kg=10.0, notes="Generic graphite (blended natural/synthetic)"
    ),
    # Silicon-enhanced anodes
    "Silicon_Graphite_5": MaterialCost(
        price_per_kg=15.0, notes="5% silicon in graphite, modest capacity boost"
    ),
    "Silicon_Graphite_10": MaterialCost(
        price_per_kg=20.0, notes="10% silicon, higher capacity but more expansion"
    ),
    "Silicon_Graphite_20": MaterialCost(
        price_per_kg=30.0, notes="20% silicon, significant capacity boost"
    ),
    "Silicon_Oxide": MaterialCost(
        price_per_kg=35.0, notes="SiOx anode, high capacity with better cycling than pure Si"
    ),
    "Pure_Silicon": MaterialCost(
        price_per_kg=50.0, notes="Pure silicon anode, highest capacity, cycling challenges"
    ),
    # LTO - Lithium Titanate
    "LTO": MaterialCost(price_per_kg=18.0, notes="Fast charging, long life, lower energy density"),
    # Hard carbon (for sodium-ion)
    "Hard_Carbon": MaterialCost(price_per_kg=14.0, notes="Sodium-ion anode material"),
}


# =============================================================================
# CURRENT COLLECTORS ($/kg)
# =============================================================================

COLLECTOR_COSTS: dict[str, MaterialCost] = {
    # Aluminum foil (cathode current collector)
    "Aluminum_Foil": MaterialCost(price_per_kg=4.0, notes="Standard cathode current collector"),
    "Aluminum_Foil_Carbon_Coated": MaterialCost(
        price_per_kg=6.0, notes="Carbon-coated for better adhesion"
    ),
    # Copper foil (anode current collector)
    "Copper_Foil": MaterialCost(price_per_kg=12.0, notes="Standard anode current collector"),
    "Copper_Foil_ED": MaterialCost(price_per_kg=14.0, notes="Electrodeposited copper, thinner"),
}


# =============================================================================
# SEPARATORS ($/m² converted to $/kg equivalent)
# =============================================================================
# Separator costs are typically per m², converted to $/kg for consistency

SEPARATOR_COSTS: dict[str, MaterialCost] = {
    "PE_Monolayer": MaterialCost(price_per_kg=25.0, notes="Polyethylene monolayer, basic"),
    "PP_Monolayer": MaterialCost(price_per_kg=25.0, notes="Polypropylene monolayer"),
    "Ceramic_Coated": MaterialCost(
        price_per_kg=35.0, notes="Ceramic-coated for better thermal stability"
    ),
    "Trilayer_PP_PE_PP": MaterialCost(
        price_per_kg=30.0, notes="PP/PE/PP trilayer, shutdown feature"
    ),
    "Wet_Process": MaterialCost(price_per_kg=28.0, notes="Wet-process separator, thinner"),
    "Dry_Process": MaterialCost(price_per_kg=22.0, notes="Dry-process separator, lower cost"),
}


# =============================================================================
# ELECTROLYTE ($/kg)
# =============================================================================

ELECTROLYTE_COSTS: dict[str, MaterialCost] = {
    # Liquid electrolytes
    "LiPF6_Carbonate": MaterialCost(
        price_per_kg=15.0, notes="Standard LiPF6 in carbonate solvents"
    ),
    "LiPF6_EC_DMC": MaterialCost(price_per_kg=15.0, notes="LiPF6 in EC/DMC blend"),
    "LiPF6_High_Voltage": MaterialCost(
        price_per_kg=20.0, notes="High-voltage stable electrolyte with additives"
    ),
    # Advanced electrolytes
    "LiFSI_Based": MaterialCost(
        price_per_kg=35.0, notes="LiFSI salt, better stability, higher cost"
    ),
    "Fluorinated": MaterialCost(price_per_kg=40.0, notes="Fluorinated solvents for high voltage"),
    # Solid electrolytes (emerging)
    "Sulfide_Solid": MaterialCost(price_per_kg=100.0, notes="Sulfide-based solid electrolyte"),
    "Oxide_Solid": MaterialCost(
        price_per_kg=120.0, notes="Oxide-based solid electrolyte (LLZO, etc.)"
    ),
    "Polymer_Solid": MaterialCost(price_per_kg=50.0, notes="Polymer solid electrolyte"),
}


# =============================================================================
# HOUSING MATERIALS ($/kg)
# =============================================================================

HOUSING_COSTS: dict[str, MaterialCost] = {
    # Pouch materials
    "Aluminum_Laminate": MaterialCost(
        price_per_kg=8.0, notes="Aluminum-polymer laminate for pouch cells"
    ),
    "Pouch_Film": MaterialCost(price_per_kg=8.0, notes="Standard pouch film"),
    # Prismatic can materials
    "Aluminum_Can": MaterialCost(price_per_kg=5.0, notes="Aluminum can for prismatic cells"),
    "Steel_Can": MaterialCost(price_per_kg=3.0, notes="Steel can for cylindrical cells"),
    "Nickel_Plated_Steel": MaterialCost(
        price_per_kg=4.0, notes="Nickel-plated steel for cylindrical cells"
    ),
    # Prismatic housing
    "Prismatic_Case": MaterialCost(price_per_kg=5.0, notes="Aluminum prismatic case with lid"),
}


# =============================================================================
# TAB/TERMINAL MATERIALS ($/kg)
# =============================================================================

TAB_COSTS: dict[str, MaterialCost] = {
    "Aluminum_Tab": MaterialCost(price_per_kg=6.0, notes="Aluminum tab for cathode"),
    "Nickel_Tab": MaterialCost(price_per_kg=20.0, notes="Nickel tab for anode"),
    "Copper_Tab": MaterialCost(price_per_kg=15.0, notes="Copper tab for anode (high current)"),
    "Nickel_Plated_Copper": MaterialCost(price_per_kg=18.0, notes="Nickel-plated copper tab"),
    "Tab_Sealant": MaterialCost(price_per_kg=10.0, notes="Tab sealant tape/film"),
}


# =============================================================================
# OTHER MATERIALS ($/kg)
# =============================================================================

OTHER_COSTS: dict[str, MaterialCost] = {
    # Binders
    "PVDF": MaterialCost(price_per_kg=25.0, notes="Polyvinylidene fluoride binder"),
    "SBR": MaterialCost(price_per_kg=8.0, notes="Styrene-butadiene rubber binder"),
    "CMC": MaterialCost(price_per_kg=5.0, notes="Carboxymethyl cellulose"),
    "PAA": MaterialCost(price_per_kg=15.0, notes="Polyacrylic acid binder (for silicon)"),
    # Conductive additives
    "Carbon_Black": MaterialCost(price_per_kg=10.0, notes="Conductive carbon black"),
    "CNT": MaterialCost(price_per_kg=100.0, notes="Carbon nanotubes"),
    "Graphene": MaterialCost(price_per_kg=150.0, notes="Graphene conductive additive"),
    # Solvents
    "NMP": MaterialCost(price_per_kg=3.0, notes="N-methyl-2-pyrrolidone (cathode slurry)"),
    "Water": MaterialCost(price_per_kg=0.01, notes="Deionized water (anode slurry)"),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_cathode_cost(material: str, region: CostRegion = CostRegion.GLOBAL) -> float:
    """
    Get cathode material cost in $/kg.

    Args:
        material: Material name (e.g., "NMC811", "LFP")
        region: Cost region for regional adjustments

    Returns:
        Cost in $/kg
    """
    # Normalize material name for lookup
    material_key = material.upper().replace("-", "").replace(" ", "_")

    # Direct lookup
    if material_key in CATHODE_COSTS:
        return CATHODE_COSTS[material_key].price_per_kg

    # Try case-insensitive match
    for key, cost in CATHODE_COSTS.items():
        if key.upper() == material_key:
            return cost.price_per_kg

    # Default fallback for unknown materials
    return 25.0  # Reasonable mid-range estimate


def get_anode_cost(material: str, region: CostRegion = CostRegion.GLOBAL) -> float:
    """
    Get anode material cost in $/kg.

    Args:
        material: Material name (e.g., "Graphite", "Silicon_Graphite_10")
        region: Cost region for regional adjustments

    Returns:
        Cost in $/kg
    """
    # Normalize material name for lookup
    material_key = material.replace("-", "_").replace(" ", "_")

    # Direct lookup
    if material_key in ANODE_COSTS:
        return ANODE_COSTS[material_key].price_per_kg

    # Try case variations
    for key, cost in ANODE_COSTS.items():
        if key.lower() == material_key.lower():
            return cost.price_per_kg

    # Check for graphite substring
    if "graphite" in material_key.lower():
        return ANODE_COSTS["Graphite"].price_per_kg

    # Default fallback
    return 10.0  # Reasonable graphite-like estimate


def get_separator_cost(separator_type: str = "Ceramic_Coated") -> float:
    """
    Get separator cost in $/kg.

    Args:
        separator_type: Type of separator

    Returns:
        Cost in $/kg
    """
    if separator_type in SEPARATOR_COSTS:
        return SEPARATOR_COSTS[separator_type].price_per_kg
    return 30.0  # Default ceramic-coated estimate


def get_electrolyte_cost(electrolyte_type: str = "LiPF6_Carbonate") -> float:
    """
    Get electrolyte cost in $/kg.

    Args:
        electrolyte_type: Type of electrolyte

    Returns:
        Cost in $/kg
    """
    if electrolyte_type in ELECTROLYTE_COSTS:
        return ELECTROLYTE_COSTS[electrolyte_type].price_per_kg
    return 15.0  # Default LiPF6 estimate


def get_housing_cost(housing_type: str, cell_type: str = "prismatic") -> float:
    """
    Get housing material cost in $/kg.

    Args:
        housing_type: Type of housing material
        cell_type: Cell type (prismatic, pouch, cylindrical)

    Returns:
        Cost in $/kg
    """
    if housing_type in HOUSING_COSTS:
        return HOUSING_COSTS[housing_type].price_per_kg

    # Default by cell type
    defaults = {
        "prismatic": 5.0,
        "pouch": 8.0,
        "cylindrical": 3.5,
    }
    return defaults.get(cell_type.lower(), 5.0)


def get_tab_cost(tab_material: str) -> float:
    """
    Get tab material cost in $/kg.

    Args:
        tab_material: Tab material type

    Returns:
        Cost in $/kg
    """
    if tab_material in TAB_COSTS:
        return TAB_COSTS[tab_material].price_per_kg

    # Infer from material name
    material_lower = tab_material.lower()
    if "aluminum" in material_lower or "al" in material_lower:
        return TAB_COSTS["Aluminum_Tab"].price_per_kg
    if "nickel" in material_lower or "ni" in material_lower:
        return TAB_COSTS["Nickel_Tab"].price_per_kg
    if "copper" in material_lower or "cu" in material_lower:
        return TAB_COSTS["Copper_Tab"].price_per_kg

    return 15.0  # Default estimate


def get_material_cost_summary() -> dict[str, dict[str, float]]:
    """
    Get a summary of all material costs organized by category.

    Returns:
        Dictionary with category names as keys and material:price dicts as values
    """
    return {
        "cathode": {k: v.price_per_kg for k, v in CATHODE_COSTS.items()},
        "anode": {k: v.price_per_kg for k, v in ANODE_COSTS.items()},
        "collector": {k: v.price_per_kg for k, v in COLLECTOR_COSTS.items()},
        "separator": {k: v.price_per_kg for k, v in SEPARATOR_COSTS.items()},
        "electrolyte": {k: v.price_per_kg for k, v in ELECTROLYTE_COSTS.items()},
        "housing": {k: v.price_per_kg for k, v in HOUSING_COSTS.items()},
        "tab": {k: v.price_per_kg for k, v in TAB_COSTS.items()},
        "other": {k: v.price_per_kg for k, v in OTHER_COSTS.items()},
    }
