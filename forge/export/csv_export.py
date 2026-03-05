"""CSV export functionality for CellCAD.

This module provides functions to export BOM and cell reports to CSV format
using European conventions (semicolon delimiter, comma decimal separator).
"""

from datetime import datetime
from pathlib import Path

from forge.engine.cost.material_costs import (
    COLLECTOR_COSTS,
    get_anode_cost,
    get_cathode_cost,
    get_electrolyte_cost,
    get_housing_cost,
    get_separator_cost,
    get_tab_cost,
)
from forge.engine.models.results import BillOfMaterials, CellReport


def _format_number(value: float, decimals: int = 2) -> str:
    """Format number with comma as decimal separator.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string with comma decimal separator
    """
    return f"{value:.{decimals}f}".replace(".", ",")


def export_bom_csv(
    bom: BillOfMaterials, output_path: str | Path, include_header: bool = True
) -> None:
    """Export Bill of Materials to CSV format.

    Uses European CSV conventions:
    - Semicolon (;) as field delimiter
    - Comma (,) as decimal separator

    Args:
        bom: Bill of Materials to export
        output_path: Path for the output CSV file
        include_header: Whether to include metadata header (default True)
    """
    lines = []

    if include_header:
        lines.extend(
            [
                "CellCAD Bill of Materials (BOM)",
                f"Export Date;{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Design Name;{bom.cell_name}",
                f"Cell Type;{bom.cell_type}",
                "",
            ]
        )

    # Column headers
    lines.append("Type;Name;Mass [%];Volume [%];Cost [%];Mass [g];Volume [ml];Cost [EUR]")

    # BOM items
    for item in bom.items:
        lines.append(
            f"{item.type};{item.name};"
            f"{_format_number(item.mass_pct)};{_format_number(item.volume_pct)};"
            f"{_format_number(item.cost_pct)};"
            f"{_format_number(item.mass_g, 3)};{_format_number(item.volume_ml, 3)};"
            f"{_format_number(item.cost_eur, 3)}"
        )

    # Totals row
    lines.append(
        f"TOTAL;;100,00;100,00;100,00;"
        f"{_format_number(bom.total_mass_g, 3)};"
        f"{_format_number(bom.total_volume_ml, 3)};"
        f"{_format_number(bom.total_cost_eur, 3)}"
    )

    # Write file
    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_report_csv(
    report: CellReport, output_path: str | Path, include_header: bool = True
) -> None:
    """Export cell report to CSV format.

    Exports key cell parameters in a Parameter;Value format.

    Args:
        report: Cell report to export
        output_path: Path for the output CSV file
        include_header: Whether to include metadata header (default True)
    """
    lines = []

    if include_header:
        lines.extend(
            [
                "CellCAD Cell Report",
                f"Export Date;{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Design Name;{report.cell_name}",
                f"Cell Type;{report.cell_type}",
                "",
            ]
        )

    lines.append("Parameter;Value;Unit")

    # Dimensions
    lines.extend(
        [
            "",
            "DIMENSIONS;;",
            f"Cell Height;{_format_number(report.cell_height_mm)};mm",
            f"Cell Width;{_format_number(report.cell_width_mm)};mm",
            f"Cell Thickness (Dry);{_format_number(report.cell_thickness_dry_mm)};mm",
            f"Cell Thickness (SoC0);{_format_number(report.cell_thickness_soc0_mm)};mm",
            f"Cell Thickness (SoC100);{_format_number(report.cell_thickness_soc100_mm)};mm",
        ]
    )

    # Volumes
    lines.extend(
        [
            "",
            "VOLUMES;;",
            f"Cell Volume;{_format_number(report.volume_cell_cm3)};cmÂ³",
            f"Stack Volume;{_format_number(report.volume_stack_cm3)};cmÂ³",
            f"Stack Efficiency;{_format_number(report.efficiency_stack_pct)};%",
        ]
    )

    # Sheet counts
    lines.extend(
        [
            "",
            "SHEET COUNTS;;",
            f"Cathode Sheets;{report.cathode_sheets};",
            f"Anode Sheets;{report.anode_sheets};",
            f"Separator Sheets;{report.separator_sheets};",
        ]
    )

    # Electrical
    lines.extend(
        [
            "",
            "ELECTRICAL;;",
            f"Capacity;{_format_number(report.capacity_ah, 3)};Ah",
            f"Nominal Voltage;{_format_number(report.nominal_voltage_v)};V",
            f"Energy;{_format_number(report.energy_wh)};Wh",
        ]
    )

    # Energy density
    lines.extend(
        [
            "",
            "ENERGY DENSITY;;",
            f"Gravimetric;{_format_number(report.gravimetric_ed_whkg, 1)};Wh/kg",
            f"Volumetric (Cell);{_format_number(report.volumetric_ed_cell_whl, 1)};Wh/L",
            f"Volumetric (Stack);{_format_number(report.volumetric_ed_stack_whl, 1)};Wh/L",
        ]
    )

    # Areal characteristics
    lines.extend(
        [
            "",
            "AREAL CHARACTERISTICS;;",
            f"Areal Capacity;{_format_number(report.areal_capacity_mahcm2)};mAh/cmÂ²",
            f"Areal Energy;{_format_number(report.areal_energy_mwhcm2)};mWh/cmÂ²",
        ]
    )

    # Mass breakdown
    lines.extend(
        [
            "",
            "MASS BREAKDOWN;;",
            f"Cathode (Coating);{_format_number(report.cathode_coating_mass_g)};g",
            f"Cathode (Collector);{_format_number(report.cathode_collector_mass_g)};g",
            f"Cathode (Total);{_format_number(report.cathode_mass_g)};g",
            f"Anode (Coating);{_format_number(report.anode_coating_mass_g)};g",
            f"Anode (Collector);{_format_number(report.anode_collector_mass_g)};g",
            f"Anode (Total);{_format_number(report.anode_mass_g)};g",
            f"Separator;{_format_number(report.separator_mass_g)};g",
            f"Electrolyte;{_format_number(report.electrolyte_mass_g)};g",
            f"Housing;{_format_number(report.housing_mass_g)};g",
            f"Tabs;{_format_number(report.tabs_mass_g)};g",
            f"Total Mass;{_format_number(report.total_mass_g)};g",
        ]
    )

    # Swelling
    lines.extend(
        [
            "",
            "SWELLING;;",
            f"Formation Swelling;{_format_number(report.formation_swelling_pct, 1)};%",
            f"SoC Breathing;{_format_number(report.soc_breathing_pct, 1)};%",
        ]
    )

    # Cost (if available)
    if report.total_cost_usd > 0:
        lines.extend(
            [
                "",
                "COST ANALYSIS;;",
                f"Cathode Material;{report.cathode_material};",
                f"Anode Material;{report.anode_material};",
                f"Total Material Cost;{_format_number(report.total_cost_usd, 4)};USD",
                f"Cost per kWh;{_format_number(report.cost_per_kwh)};$/kWh",
            ]
        )

    # Write file
    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_bom_with_real_costs(
    report: CellReport,
    cathode_material: str = "NMC811",
    anode_material: str = "Graphite",
    separator_type: str = "Ceramic_Coated",
    electrolyte_type: str = "LiPF6_Carbonate",
    housing_type: str | None = None,
) -> BillOfMaterials:
    """
    Generate a Bill of Materials using real material costs.

    Uses the material cost database to calculate accurate component costs
    based on current market prices.

    Args:
        report: CellReport with mass data
        cathode_material: Cathode active material name
        anode_material: Anode active material name
        separator_type: Separator type
        electrolyte_type: Electrolyte type
        housing_type: Housing material (auto-detected if None)

    Returns:
        BillOfMaterials with real cost estimates
    """
    bom = BillOfMaterials(
        cell_name=report.cell_name,
        cell_type=report.cell_type,
    )

    # Auto-detect housing type
    if housing_type is None:
        cell_type_lower = report.cell_type.lower()
        if cell_type_lower == "pouch":
            housing_type = "Aluminum_Laminate"
        elif cell_type_lower == "cylindrical":
            housing_type = "Steel_Can"
        else:
            housing_type = "Prismatic_Case"

    # Cathode active material
    cathode_cost_per_kg = get_cathode_cost(cathode_material)
    cathode_coating_cost = (report.cathode_coating_mass_g / 1000.0) * cathode_cost_per_kg
    # Estimate volume from mass using typical NMC density (~4.7 g/cmÂ³)
    cathode_coating_vol = report.cathode_coating_mass_g / 4.7
    bom.add_item(
        type="Cathode Actives",
        name=cathode_material,
        mass_g=report.cathode_coating_mass_g,
        volume_ml=cathode_coating_vol,
        cost_eur=cathode_coating_cost,
    )

    # Cathode collector (aluminum)
    al_cost_per_kg = COLLECTOR_COSTS["Aluminum_Foil"].price_per_kg
    cathode_collector_cost = (report.cathode_collector_mass_g / 1000.0) * al_cost_per_kg
    cathode_collector_vol = report.cathode_collector_mass_g / 2.7  # Al density
    bom.add_item(
        type="Cathode Collector",
        name="Aluminum Foil",
        mass_g=report.cathode_collector_mass_g,
        volume_ml=cathode_collector_vol,
        cost_eur=cathode_collector_cost,
    )

    # Anode active material
    anode_cost_per_kg = get_anode_cost(anode_material)
    anode_coating_cost = (report.anode_coating_mass_g / 1000.0) * anode_cost_per_kg
    # Estimate volume using typical graphite density (~2.2 g/cmÂ³)
    anode_coating_vol = report.anode_coating_mass_g / 2.2
    bom.add_item(
        type="Anode Actives",
        name=anode_material,
        mass_g=report.anode_coating_mass_g,
        volume_ml=anode_coating_vol,
        cost_eur=anode_coating_cost,
    )

    # Anode collector (copper)
    cu_cost_per_kg = COLLECTOR_COSTS["Copper_Foil"].price_per_kg
    anode_collector_cost = (report.anode_collector_mass_g / 1000.0) * cu_cost_per_kg
    anode_collector_vol = report.anode_collector_mass_g / 8.96  # Cu density
    bom.add_item(
        type="Anode Collector",
        name="Copper Foil",
        mass_g=report.anode_collector_mass_g,
        volume_ml=anode_collector_vol,
        cost_eur=anode_collector_cost,
    )

    # Separator
    separator_cost_per_kg = get_separator_cost(separator_type)
    separator_cost = (report.separator_mass_g / 1000.0) * separator_cost_per_kg
    separator_vol = report.separator_mass_g / 0.9  # Typical separator density
    bom.add_item(
        type="Separator",
        name=separator_type,
        mass_g=report.separator_mass_g,
        volume_ml=separator_vol,
        cost_eur=separator_cost,
    )

    # Electrolyte
    electrolyte_cost_per_kg = get_electrolyte_cost(electrolyte_type)
    electrolyte_cost = (report.electrolyte_mass_g / 1000.0) * electrolyte_cost_per_kg
    electrolyte_vol = report.electrolyte_mass_g / 1.2  # Typical electrolyte density
    bom.add_item(
        type="Electrolyte",
        name=electrolyte_type,
        mass_g=report.electrolyte_mass_g,
        volume_ml=electrolyte_vol,
        cost_eur=electrolyte_cost,
    )

    # Housing
    housing_cost_per_kg = get_housing_cost(housing_type, report.cell_type)
    housing_cost = (report.housing_mass_g / 1000.0) * housing_cost_per_kg
    housing_density = 2.7 if "aluminum" in housing_type.lower() else 1.5
    housing_vol = report.housing_mass_g / housing_density
    bom.add_item(
        type="Housing",
        name=housing_type,
        mass_g=report.housing_mass_g,
        volume_ml=housing_vol,
        cost_eur=housing_cost,
    )

    # Tabs (if present)
    if report.tabs_mass_g > 0:
        # Split equally between cathode (Al) and anode (Ni) tabs
        tab_mass_each = report.tabs_mass_g / 2.0

        cathode_tab_cost_per_kg = get_tab_cost("Aluminum_Tab")
        cathode_tab_cost = (tab_mass_each / 1000.0) * cathode_tab_cost_per_kg
        bom.add_item(
            type="Cathode Tab",
            name="Aluminum_Tab",
            mass_g=tab_mass_each,
            volume_ml=tab_mass_each / 2.7,
            cost_eur=cathode_tab_cost,
        )

        anode_tab_cost_per_kg = get_tab_cost("Nickel_Tab")
        anode_tab_cost = (tab_mass_each / 1000.0) * anode_tab_cost_per_kg
        bom.add_item(
            type="Anode Tab",
            name="Nickel_Tab",
            mass_g=tab_mass_each,
            volume_ml=tab_mass_each / 8.9,
            cost_eur=anode_tab_cost,
        )

    # Calculate percentages
    bom.calculate_percentages()

    return bom

