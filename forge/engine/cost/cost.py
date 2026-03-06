"""
Cost calculation module for CellCAD.

This module calculates material costs for battery cells using the
material cost database and cell reports. It provides:
- Per-component cost breakdown
- Total cell cost in USD
- Cost per kWh metric

Works with all cell types: pouch, prismatic, and cylindrical.
"""

from dataclasses import dataclass, field

from forge.engine.models.results import CellReport

from .material_costs import (
    COLLECTOR_COSTS,
    get_anode_cost,
    get_cathode_cost,
    get_electrolyte_cost,
    get_housing_cost,
    get_separator_cost,
    get_tab_cost,
)


@dataclass
class ComponentCost:
    """Cost breakdown for a single component."""

    component: str
    material: str
    mass_g: float
    cost_per_kg: float
    cost_usd: float

    @property
    def cost_per_g(self) -> float:
        """Cost per gram."""
        return self.cost_per_kg / 1000.0


@dataclass
class CellCostReport:
    """Complete cost breakdown for a cell.

    Attributes:
        cell_name: Name of the cell design
        cell_type: Type of cell (pouch, prismatic, cylindrical)
        component_costs: List of individual component costs
        total_cost_usd: Total material cost in USD
        energy_wh: Cell energy in Wh
        cost_per_kwh: Cost per kWh ($/kWh)
    """

    cell_name: str
    cell_type: str
    component_costs: list[ComponentCost] = field(default_factory=list)
    total_cost_usd: float = 0.0
    energy_wh: float = 0.0

    @property
    def cost_per_kwh(self) -> float:
        """Cost per kWh in $/kWh."""
        if self.energy_wh <= 0:
            return 0.0
        return (self.total_cost_usd / self.energy_wh) * 1000.0

    def get_component_breakdown(self) -> dict[str, float]:
        """Get cost breakdown by component type."""
        breakdown: dict[str, float] = {}
        for cost in self.component_costs:
            if cost.component in breakdown:
                breakdown[cost.component] += cost.cost_usd
            else:
                breakdown[cost.component] = cost.cost_usd
        return breakdown

    def get_percentage_breakdown(self) -> dict[str, float]:
        """Get cost breakdown as percentages."""
        breakdown = self.get_component_breakdown()
        if self.total_cost_usd <= 0:
            return dict.fromkeys(breakdown, 0.0)
        return {k: (v / self.total_cost_usd) * 100.0 for k, v in breakdown.items()}


def calculate_cell_cost(
    cell_report: CellReport,
    cathode_material: str = "NMC811",
    anode_material: str = "Graphite",
    separator_type: str = "Ceramic_Coated",
    electrolyte_type: str = "LiPF6_Carbonate",
    housing_type: str | None = None,
    cathode_tab_material: str = "Aluminum_Tab",
    anode_tab_material: str = "Nickel_Tab",
) -> CellCostReport:
    """
    Calculate complete material cost for a cell.

    Uses mass data from CellReport and prices from the material cost database
    to compute per-component and total costs.

    Args:
        cell_report: CellReport with mass data for each component
        cathode_material: Cathode active material (e.g., "NMC811", "LFP")
        anode_material: Anode active material (e.g., "Graphite", "Silicon_Graphite_10")
        separator_type: Separator type (e.g., "Ceramic_Coated", "PE_Monolayer")
        electrolyte_type: Electrolyte type (e.g., "LiPF6_Carbonate")
        housing_type: Housing material (auto-detected from cell_type if None)
        cathode_tab_material: Cathode tab material
        anode_tab_material: Anode tab material

    Returns:
        CellCostReport with complete cost breakdown
    """
    report = CellCostReport(
        cell_name=cell_report.cell_name,
        cell_type=cell_report.cell_type,
        energy_wh=cell_report.energy_wh,
    )

    # Auto-detect housing type based on cell type
    if housing_type is None:
        cell_type_lower = cell_report.cell_type.lower()
        if cell_type_lower == "pouch":
            housing_type = "Aluminum_Laminate"
        elif cell_type_lower == "cylindrical":
            housing_type = "Steel_Can"
        else:
            housing_type = "Prismatic_Case"

    # Calculate cathode coating cost
    cathode_cost_per_kg = get_cathode_cost(cathode_material)
    cathode_coating_cost = (cell_report.cathode_coating_mass_g / 1000.0) * cathode_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Cathode Active Material",
            material=cathode_material,
            mass_g=cell_report.cathode_coating_mass_g,
            cost_per_kg=cathode_cost_per_kg,
            cost_usd=cathode_coating_cost,
        )
    )

    # Calculate cathode collector cost (aluminum foil)
    al_collector_cost_per_kg = COLLECTOR_COSTS["Aluminum_Foil"].price_per_kg
    cathode_collector_cost = (
        cell_report.cathode_collector_mass_g / 1000.0
    ) * al_collector_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Cathode Current Collector",
            material="Aluminum_Foil",
            mass_g=cell_report.cathode_collector_mass_g,
            cost_per_kg=al_collector_cost_per_kg,
            cost_usd=cathode_collector_cost,
        )
    )

    # Calculate anode coating cost
    anode_cost_per_kg = get_anode_cost(anode_material)
    anode_coating_cost = (cell_report.anode_coating_mass_g / 1000.0) * anode_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Anode Active Material",
            material=anode_material,
            mass_g=cell_report.anode_coating_mass_g,
            cost_per_kg=anode_cost_per_kg,
            cost_usd=anode_coating_cost,
        )
    )

    # Calculate anode collector cost (copper foil)
    cu_collector_cost_per_kg = COLLECTOR_COSTS["Copper_Foil"].price_per_kg
    anode_collector_cost = (cell_report.anode_collector_mass_g / 1000.0) * cu_collector_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Anode Current Collector",
            material="Copper_Foil",
            mass_g=cell_report.anode_collector_mass_g,
            cost_per_kg=cu_collector_cost_per_kg,
            cost_usd=anode_collector_cost,
        )
    )

    # Calculate separator cost
    separator_cost_per_kg = get_separator_cost(separator_type)
    separator_cost = (cell_report.separator_mass_g / 1000.0) * separator_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Separator",
            material=separator_type,
            mass_g=cell_report.separator_mass_g,
            cost_per_kg=separator_cost_per_kg,
            cost_usd=separator_cost,
        )
    )

    # Calculate electrolyte cost
    electrolyte_cost_per_kg = get_electrolyte_cost(electrolyte_type)
    electrolyte_cost = (cell_report.electrolyte_mass_g / 1000.0) * electrolyte_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Electrolyte",
            material=electrolyte_type,
            mass_g=cell_report.electrolyte_mass_g,
            cost_per_kg=electrolyte_cost_per_kg,
            cost_usd=electrolyte_cost,
        )
    )

    # Calculate housing cost
    housing_cost_per_kg = get_housing_cost(housing_type, cell_report.cell_type)
    housing_cost = (cell_report.housing_mass_g / 1000.0) * housing_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Housing",
            material=housing_type,
            mass_g=cell_report.housing_mass_g,
            cost_per_kg=housing_cost_per_kg,
            cost_usd=housing_cost,
        )
    )

    # Calculate tab costs (split equally between cathode and anode tabs)
    # Assume 50/50 mass split between cathode and anode tabs
    tab_mass_each = cell_report.tabs_mass_g / 2.0

    cathode_tab_cost_per_kg = get_tab_cost(cathode_tab_material)
    cathode_tab_cost = (tab_mass_each / 1000.0) * cathode_tab_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Cathode Tab",
            material=cathode_tab_material,
            mass_g=tab_mass_each,
            cost_per_kg=cathode_tab_cost_per_kg,
            cost_usd=cathode_tab_cost,
        )
    )

    anode_tab_cost_per_kg = get_tab_cost(anode_tab_material)
    anode_tab_cost = (tab_mass_each / 1000.0) * anode_tab_cost_per_kg
    report.component_costs.append(
        ComponentCost(
            component="Anode Tab",
            material=anode_tab_material,
            mass_g=tab_mass_each,
            cost_per_kg=anode_tab_cost_per_kg,
            cost_usd=anode_tab_cost,
        )
    )

    # Calculate total
    report.total_cost_usd = sum(c.cost_usd for c in report.component_costs)

    return report


def calculate_cost_per_kwh(
    cell_report: CellReport,
    cathode_material: str = "NMC811",
    anode_material: str = "Graphite",
) -> float:
    """
    Quick calculation of cost per kWh for a cell.

    Convenience function for getting just the $/kWh metric.

    Args:
        cell_report: CellReport with mass and energy data
        cathode_material: Cathode active material
        anode_material: Anode active material

    Returns:
        Cost per kWh in $/kWh
    """
    cost_report = calculate_cell_cost(
        cell_report,
        cathode_material=cathode_material,
        anode_material=anode_material,
    )
    return cost_report.cost_per_kwh


def enrich_report_with_cost(
    report: CellReport,
    cathode_material: str = "NMC811",
    anode_material: str = "Graphite",
    separator_type: str = "Ceramic_Coated",
    electrolyte_type: str = "LiPF6_Carbonate",
) -> CellReport:
    """
    Add cost fields to an existing CellReport.

    This is a convenience function that calculates cost and updates
    the report's cost fields in-place.

    Args:
        report: CellReport to enrich with cost data
        cathode_material: Cathode active material (e.g., "NMC811", "LFP")
        anode_material: Anode active material (e.g., "Graphite")
        separator_type: Separator type
        electrolyte_type: Electrolyte type

    Returns:
        The same CellReport with cost fields populated
    """
    cost_report = calculate_cell_cost(
        report,
        cathode_material=cathode_material,
        anode_material=anode_material,
        separator_type=separator_type,
        electrolyte_type=electrolyte_type,
    )

    report.total_cost_usd = cost_report.total_cost_usd
    report.cost_per_kwh = cost_report.cost_per_kwh
    report.cathode_material = cathode_material
    report.anode_material = anode_material

    return report


def format_cost_report(cost_report: CellCostReport) -> str:
    """
    Format a cost report as a human-readable string.

    Args:
        cost_report: CellCostReport to format

    Returns:
        Multi-line string with formatted cost breakdown
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"CELLCAD COST REPORT: {cost_report.cell_name}")
    lines.append(f"Cell Type: {cost_report.cell_type}")
    lines.append("=" * 70)
    lines.append("")

    # Component breakdown table
    lines.append("COMPONENT COST BREAKDOWN:")
    lines.append("-" * 70)
    lines.append(f"{'Component':<30} {'Material':<20} {'Mass (g)':<10} {'Cost ($)':<10}")
    lines.append("-" * 70)

    for cost in cost_report.component_costs:
        lines.append(
            f"{cost.component:<30} {cost.material:<20} {cost.mass_g:>8.2f} {cost.cost_usd:>9.4f}"
        )

    lines.append("-" * 70)
    total_mass = sum(c.mass_g for c in cost_report.component_costs)
    lines.append(f"{'TOTAL':<30} {'':<20} {total_mass:>8.2f} {cost_report.total_cost_usd:>9.4f}")
    lines.append("")

    # Summary metrics
    lines.append("COST METRICS:")
    lines.append("-" * 70)
    lines.append(f"Total Material Cost:     ${cost_report.total_cost_usd:.4f}")
    lines.append(f"Cell Energy:             {cost_report.energy_wh:.2f} Wh")
    lines.append(f"Cost per kWh:            ${cost_report.cost_per_kwh:.2f}/kWh")
    lines.append("")

    # Percentage breakdown
    lines.append("COST DISTRIBUTION (%):")
    lines.append("-" * 70)
    pct_breakdown = cost_report.get_percentage_breakdown()
    for component, pct in sorted(pct_breakdown.items(), key=lambda x: -x[1]):
        bar_length = int(pct / 2)
        bar = "#" * bar_length
        lines.append(f"{component:<30} {pct:>5.1f}% {bar}")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)

