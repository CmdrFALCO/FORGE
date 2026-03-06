"""Cost estimation module for FORGE engine.

Provides:
- Cost data and lookup helpers (material_costs)
- Cell cost calculation and reporting functions (cost)
"""

from .cost import (
    CellCostReport,
    ComponentCost,
    calculate_cell_cost,
    calculate_cost_per_kwh,
    enrich_report_with_cost,
    format_cost_report,
)
from .material_costs import (
    ANODE_COSTS,
    CATHODE_COSTS,
    COLLECTOR_COSTS,
    ELECTROLYTE_COSTS,
    HOUSING_COSTS,
    OTHER_COSTS,
    SEPARATOR_COSTS,
    TAB_COSTS,
    CostRegion,
    MaterialCost,
    get_anode_cost,
    get_cathode_cost,
    get_electrolyte_cost,
    get_housing_cost,
    get_material_cost_summary,
    get_separator_cost,
    get_tab_cost,
)

__all__ = [
    # cost.py
    "ComponentCost",
    "CellCostReport",
    "calculate_cell_cost",
    "calculate_cost_per_kwh",
    "enrich_report_with_cost",
    "format_cost_report",
    # material_costs.py
    "CostRegion",
    "MaterialCost",
    "CATHODE_COSTS",
    "ANODE_COSTS",
    "COLLECTOR_COSTS",
    "SEPARATOR_COSTS",
    "ELECTROLYTE_COSTS",
    "HOUSING_COSTS",
    "TAB_COSTS",
    "OTHER_COSTS",
    "get_cathode_cost",
    "get_anode_cost",
    "get_separator_cost",
    "get_electrolyte_cost",
    "get_housing_cost",
    "get_tab_cost",
    "get_material_cost_summary",
]
