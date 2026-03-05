"""JSON export functionality for FORGE.

This module provides functions to export cell reports and BOMs to JSON format.
"""

import json
from datetime import datetime
from pathlib import Path

from forge.engine.models.results import BillOfMaterials, CellReport


def export_json(
    report: CellReport,
    bom: BillOfMaterials | None = None,
    output_path: str | Path = None,
) -> str | None:
    """Export cell report and optional BOM to JSON format.

    Args:
        report: Cell report to export
        bom: Optional Bill of Materials to include
        output_path: Path for output file. If None, returns JSON string.

    Returns:
        JSON string if output_path is None, otherwise None
    """
    # Build report data manually to include computed properties
    report_data = {
        "cell_name": report.cell_name,
        "cell_type": report.cell_type,
        "dimensions": {
            "cell_height_mm": report.cell_height_mm,
            "cell_width_mm": report.cell_width_mm,
            "cell_thickness_dry_mm": report.cell_thickness_dry_mm,
            "cell_thickness_soc0_mm": report.cell_thickness_soc0_mm,
            "cell_thickness_soc100_mm": report.cell_thickness_soc100_mm,
        },
        "volumes": {
            "volume_cell_cm3": report.volume_cell_cm3,
            "volume_stack_cm3": report.volume_stack_cm3,
            "efficiency_stack_pct": report.efficiency_stack_pct,
        },
        "sheet_counts": {
            "cathode_sheets": report.cathode_sheets,
            "anode_sheets": report.anode_sheets,
            "separator_sheets": report.separator_sheets,
            "all_electrode_sheets": report.all_electrode_sheets,
        },
        "electrical": {
            "capacity_ah": report.capacity_ah,
            "nominal_voltage_v": report.nominal_voltage_v,
            "energy_wh": report.energy_wh,
        },
        "energy_density": {
            "gravimetric_whkg": report.gravimetric_ed_whkg,
            "volumetric_cell_whl": report.volumetric_ed_cell_whl,
            "volumetric_stack_whl": report.volumetric_ed_stack_whl,
        },
        "areal_characteristics": {
            "areal_capacity_mahcm2": report.areal_capacity_mahcm2,
            "areal_energy_mwhcm2": report.areal_energy_mwhcm2,
        },
        "mass_breakdown": {
            "cathode_coating_g": report.cathode_coating_mass_g,
            "cathode_collector_g": report.cathode_collector_mass_g,
            "cathode_total_g": report.cathode_mass_g,
            "anode_coating_g": report.anode_coating_mass_g,
            "anode_collector_g": report.anode_collector_mass_g,
            "anode_total_g": report.anode_mass_g,
            "separator_g": report.separator_mass_g,
            "electrolyte_g": report.electrolyte_mass_g,
            "housing_g": report.housing_mass_g,
            "tabs_g": report.tabs_mass_g,
            "total_g": report.total_mass_g,
        },
        "swelling": {
            "formation_swelling_pct": report.formation_swelling_pct,
            "soc_breathing_pct": report.soc_breathing_pct,
        },
    }

    # Build BOM data if provided
    bom_data = None
    if bom is not None:
        bom_data = {
            "cell_name": bom.cell_name,
            "cell_type": bom.cell_type,
            "items": [
                {
                    "type": item.type,
                    "name": item.name,
                    "mass_g": item.mass_g,
                    "volume_ml": item.volume_ml,
                    "cost_eur": item.cost_eur,
                    "mass_pct": item.mass_pct,
                    "volume_pct": item.volume_pct,
                    "cost_pct": item.cost_pct,
                }
                for item in bom.items
            ],
            "totals": {
                "total_mass_g": bom.total_mass_g,
                "total_volume_ml": bom.total_volume_ml,
                "total_cost_eur": bom.total_cost_eur,
            },
        }

    # Build complete output
    data = {
        "report": report_data,
        "bom": bom_data,
        "metadata": {
            "generated": datetime.now().isoformat(),
            "version": "1.0",
            "tool": "FORGE",
        },
    }

    json_str = json.dumps(data, indent=2)

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return None
    else:
        return json_str


def export_report_json(
    report: CellReport,
    output_path: str | Path = None,
) -> str | None:
    """Export cell report to JSON format (without BOM).

    Args:
        report: Cell report to export
        output_path: Path for output file. If None, returns JSON string.

    Returns:
        JSON string if output_path is None, otherwise None
    """
    return export_json(report, bom=None, output_path=output_path)


def export_bom_json(
    bom: BillOfMaterials,
    output_path: str | Path = None,
) -> str | None:
    """Export Bill of Materials to JSON format (without report).

    Args:
        bom: Bill of Materials to export
        output_path: Path for output file. If None, returns JSON string.

    Returns:
        JSON string if output_path is None, otherwise None
    """
    bom_data = {
        "cell_name": bom.cell_name,
        "cell_type": bom.cell_type,
        "items": [
            {
                "type": item.type,
                "name": item.name,
                "mass_g": item.mass_g,
                "volume_ml": item.volume_ml,
                "cost_eur": item.cost_eur,
                "mass_pct": item.mass_pct,
                "volume_pct": item.volume_pct,
                "cost_pct": item.cost_pct,
            }
            for item in bom.items
        ],
        "totals": {
            "total_mass_g": bom.total_mass_g,
            "total_volume_ml": bom.total_volume_ml,
            "total_cost_eur": bom.total_cost_eur,
        },
        "metadata": {
            "generated": datetime.now().isoformat(),
            "version": "1.0",
            "tool": "FORGE",
        },
    }

    json_str = json.dumps(bom_data, indent=2)

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return None
    else:
        return json_str


def load_report_json(input_path: str | Path) -> dict:
    """Load cell report data from JSON file.

    Args:
        input_path: Path to JSON file

    Returns:
        Dictionary containing report data
    """
    input_path = Path(input_path)
    with open(input_path, encoding="utf-8") as f:
        return json.load(f)


