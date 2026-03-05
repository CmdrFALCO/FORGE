"""Main CLI entry point for FORGE.

This module provides the command-line interface for FORGE operations.
"""

import argparse
import json
import sys
from pathlib import Path

from forge.engine.calculators.pouch_calculator import CellCalculator, PouchCellInput, generate_report_text
from forge.engine.models.materials import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    DENSITY_PET,
    DENSITY_PP,
    NMC_NOMINAL_VOLTAGE,
)
# Legacy default from CellCAD constants.py
TYPICAL_SEPARATOR_UM = 16.0

from forge.export import export_json, export_report_csv
from forge.engine.models.geometry import PouchPackaging, SheetGeometry
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)
from forge.engine.models.stack import EndElectrodesMode, StackConfiguration
from forge.engine.validation.result_validation import (
    V1_POUCH_REFERENCE,
    V1_POUCH_TOLERANCES,
    format_reference_list,
    format_validation_report,
    get_reference_info,
    list_reference_cells,
    load_reference_cell,
    validate_against_reference,
    validate_cell,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="forge",
        description="FORGE - Battery Cell Design Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  forge calculate --config cell_design.json
  forge calculate --config cell_design.json --output report.csv
  forge validate --config cell_design.json --reference v1_pouch
  forge validate --list-references
  forge info --pybamm Chen2020
  forge info --reference v1_pouch
  forge template --output cell_design.json
        """,
    )

    parser.add_argument("--version", action="version", version="FORGE 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Calculate command
    calc_parser = subparsers.add_parser(
        "calculate", help="Calculate cell properties from configuration"
    )
    calc_parser.add_argument(
        "--config", "-c", type=str, required=True, help="Path to cell configuration JSON file"
    )
    calc_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (format determined by extension: .json, .csv)",
    )
    calc_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    calc_parser.add_argument(
        "--bom", action="store_true", help="Include Bill of Materials in output"
    )

    # Validate command
    val_parser = subparsers.add_parser(
        "validate", help="Validate calculated results against reference data"
    )
    val_parser.add_argument("--config", "-c", type=str, help="Path to cell configuration JSON file")
    val_parser.add_argument(
        "--reference",
        "-r",
        type=str,
        default="v1_pouch",
        help="Reference cell ID (default: v1_pouch). Use --list-references to see available.",
    )
    val_parser.add_argument(
        "--tolerance", "-t", type=float, help="Override default tolerance percentage"
    )
    val_parser.add_argument(
        "--list-references", action="store_true", help="List all available reference cells"
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about available materials, parameter sets, and references"
    )
    info_parser.add_argument("--pybamm", type=str, help="Show info for a PyBaMM parameter set")
    info_parser.add_argument("--excel", type=str, help="Show info for an Excel material database")
    info_parser.add_argument("--reference", type=str, help="Show info for a reference cell")
    info_parser.add_argument(
        "--list-pybamm", action="store_true", help="List available PyBaMM parameter sets"
    )
    info_parser.add_argument(
        "--list-references", action="store_true", help="List available reference cells"
    )

    # Template command
    template_parser = subparsers.add_parser(
        "template", help="Generate template configuration files"
    )
    template_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="cell_config.json",
        help="Output path for template (default: cell_config.json)",
    )
    template_parser.add_argument(
        "--type",
        "-t",
        choices=["pouch", "prismatic", "excel"],
        default="pouch",
        help="Template type (default: pouch)",
    )
    template_parser.add_argument(
        "--from-reference", type=str, help="Generate template from a reference cell"
    )

    return parser


def load_config(config_path: str) -> dict:
    """Load cell configuration from JSON file.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        Configuration dictionary
    """
    with open(config_path) as f:
        return json.load(f)


def config_to_pouch_input(config: dict) -> PouchCellInput:
    """Convert configuration dictionary to PouchCellInput.

    Args:
        config: Configuration dictionary

    Returns:
        PouchCellInput instance
    """
    # Create materials
    cathode = CathodeMaterial(**config["cathode"])
    anode = AnodeMaterial(**config["anode"])
    separator = SeparatorMaterial(**config["separator"])
    electrolyte = ElectrolyteModel(**config["electrolyte"])

    # Create geometry
    geometry = SheetGeometry(**config["geometry"])
    packaging = PouchPackaging(**config["packaging"])

    # Create stack configuration
    stack_cfg = config["stack_config"].copy()
    stack_cfg["end_electrodes"] = EndElectrodesMode(stack_cfg["end_electrodes"])
    stack_config = StackConfiguration(**stack_cfg)

    # Create case composition
    case_composition = [PackagingLayer(**layer) for layer in config["case_composition"]]

    # Create tabs
    anode_tab = TabConfig(**config["anode_tab"])
    cathode_tab = TabConfig(**config["cathode_tab"])

    return PouchCellInput(
        cell_name=config["cell_name"],
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        geometry=geometry,
        packaging=packaging,
        stack_config=stack_config,
        case_composition=case_composition,
        anode_tab=anode_tab,
        cathode_tab=cathode_tab,
        nominal_voltage_v=config.get("nominal_voltage_v", NMC_NOMINAL_VOLTAGE),
        capacity_ah=config.get("capacity_ah"),
        electrolyte_excess_factor=config.get("electrolyte_excess_factor", 1.10),
        electrolyte_volume_override_ml=config.get("electrolyte_volume_override_ml"),
        cathode_porosity_pct=config.get("cathode_porosity_pct", 30.0),
        anode_porosity_pct=config.get("anode_porosity_pct", 30.0),
    )


def reference_to_config(reference_id: str) -> dict:
    """Convert a reference cell to a configuration dictionary.

    Args:
        reference_id: Reference cell ID

    Returns:
        Configuration dictionary compatible with config_to_pouch_input
    """
    ref = load_reference_cell(reference_id)
    data = ref.raw_data

    materials = data.get("materials", {})
    geometry = data.get("geometry_inputs", {})
    stack = data.get("stack_config", {})
    specs = data.get("cell_specs", {})

    # Build cathode
    cat = materials.get("cathode", {})
    cathode_config = {
        "id": f"{reference_id}_cathode",
        "name": cat.get("name", "Cathode"),
        "chemistry": cat.get("chemistry", "NMC"),
        "rev_spec_capacity_mahg": cat.get("rev_spec_capacity_mahg", 165.0),
        "max_spec_capacity_mahg": cat.get("max_spec_capacity_mahg", 180.0),
        "areal_weight_mgcm2": cat.get("loading_mgcm2", 18.0),
        "collector_thickness_um": cat.get("collector_thickness_um", 15.0),
        "coating_density_gcm3": cat.get("coating_density_gcm3", 3.5),
        "coating_thickness_0pct_um": cat.get("coating_thickness_0pct_um", 70.0),
        "coating_thickness_100pct_um": cat.get("coating_thickness_100pct_um", 71.4),
    }

    # Build anode
    an = materials.get("anode", {})
    anode_config = {
        "id": f"{reference_id}_anode",
        "name": an.get("name", "Anode"),
        "chemistry": an.get("chemistry", "Graphite"),
        "rev_spec_capacity_mahg": an.get("rev_spec_capacity_mahg", 360.0),
        "max_spec_capacity_mahg": an.get("max_spec_capacity_mahg", 372.0),
        "areal_weight_mgcm2": an.get("loading_mgcm2", 10.0),
        "collector_thickness_um": an.get("collector_thickness_um", 10.0),
        "coating_density_gcm3": an.get("coating_density_gcm3", 1.6),
        "coating_thickness_0pct_um": an.get("coating_thickness_0pct_um", 80.0),
        "coating_thickness_100pct_um": an.get("coating_thickness_100pct_um", 84.0),
    }

    # Build separator
    sep = materials.get("separator", {})
    separator_config = {
        "id": f"{reference_id}_separator",
        "name": sep.get("name", "Separator"),
        "thickness_um": sep.get("thickness_um", TYPICAL_SEPARATOR_UM),
        "porosity_pct": sep.get("porosity_pct", 40.0),
        "density_gcm3": sep.get("density_gcm3", DENSITY_PP),
        "areal_weight_mgcm2": sep.get("areal_weight_mgcm2", 1.0),
    }

    # Build electrolyte
    elec = materials.get("electrolyte", {})
    electrolyte_config = {
        "id": f"{reference_id}_electrolyte",
        "name": elec.get("name", "Electrolyte"),
        "density_gcm3": elec.get("density_gcm3", 1.25),
    }

    # Build geometry
    geometry_config = {
        "cathode_height_mm": geometry.get("cathode_height_mm", 180.0),
        "cathode_width_mm": geometry.get("cathode_width_mm", 100.0),
        "anode_offset_y_mm": geometry.get("anode_offset_y_mm", 2.0),
        "anode_offset_x_mm": geometry.get("anode_offset_x_mm", 2.0),
        "separator_offset_y_mm": geometry.get("separator_offset_y_mm", 1.0),
        "separator_offset_x_mm": geometry.get("separator_offset_x_mm", 1.0),
    }

    # Build packaging
    packaging_config = {
        "pouch_offset_top_mm": geometry.get("pouch_offset_top_mm", 10.0),
        "pouch_offset_bottom_mm": geometry.get("pouch_offset_bottom_mm", 5.0),
        "pouch_offset_left_mm": geometry.get("pouch_offset_left_mm", 5.0),
        "pouch_offset_right_mm": geometry.get("pouch_offset_right_mm", 5.0),
    }

    # Build stack config
    end_electrodes_map = {
        "BothNegative": "BothNegative",
        "BothPositive": "BothPositive",
        "PositiveNegative": "PositiveNegative",
    }
    stack_config = {
        "number_of_stacks": stack.get("number_of_stacks", 1),
        "electrode_pairs_per_stack": stack.get("electrode_pairs", 15),
        "end_electrodes": end_electrodes_map.get(
            stack.get("end_electrodes", "BothNegative"), "BothNegative"
        ),
        "separator_overwraps_per_stack": stack.get("separator_overwraps", 1),
        "additional_overwraps_per_stack": stack.get("additional_overwraps", 0),
        "insulation_shell_count": stack.get("insulation_shell_count", 1),
        "fixing_tapes_per_stack": stack.get("fixing_tapes_per_stack", 2),
    }

    # Build case composition
    case_layers = materials.get("case_composition", [])
    if not case_layers:
        case_layers = [
            {
                "name": "PET",
                "version": "1.0",
                "thickness_um": 12.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PET,
            },
            {
                "name": "Aluminum",
                "version": "1.0",
                "thickness_um": 40.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_ALUMINUM,
            },
            {
                "name": "PP",
                "version": "1.0",
                "thickness_um": 80.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PP,
            },
        ]
    else:
        case_layers = [
            {
                "name": layer.get("name", "Layer"),
                "version": "1.0",
                "thickness_um": layer.get("thickness_um", 10.0),
                "porosity_pct": layer.get("porosity_pct", 0.0),
                "density_gcm3": layer.get("density_gcm3", 1.0),
            }
            for layer in case_layers
        ]

    # Build tabs
    cat_tab = materials.get("cathode_tab", {})
    cathode_tab_config = {
        "material": cat_tab.get("material", "Aluminum"),
        "height_mm": cat_tab.get("height_mm", 30.0),
        "width_mm": cat_tab.get("width_mm", 40.0),
        "thickness_mm": cat_tab.get("thickness_mm", 0.3),
        "density_gcm3": cat_tab.get("density_gcm3", DENSITY_ALUMINUM),
    }

    an_tab = materials.get("anode_tab", {})
    anode_tab_config = {
        "material": an_tab.get("material", "Copper"),
        "height_mm": an_tab.get("height_mm", 30.0),
        "width_mm": an_tab.get("width_mm", 40.0),
        "thickness_mm": an_tab.get("thickness_mm", 0.2),
        "density_gcm3": an_tab.get("density_gcm3", DENSITY_COPPER),
    }

    result = {
        "cell_name": ref.name,
        "cathode": cathode_config,
        "anode": anode_config,
        "separator": separator_config,
        "electrolyte": electrolyte_config,
        "geometry": geometry_config,
        "packaging": packaging_config,
        "stack_config": stack_config,
        "case_composition": case_layers,
        "anode_tab": anode_tab_config,
        "cathode_tab": cathode_tab_config,
        "nominal_voltage_v": specs.get("nominal_voltage_v", NMC_NOMINAL_VOLTAGE),
        "capacity_ah": specs.get("capacity_ah"),
        "electrolyte_excess_factor": elec.get("excess_factor", 1.10),
        "cathode_porosity_pct": 30.0,
        "anode_porosity_pct": 35.0,
    }

    # Add electrolyte volume override if specified
    if elec.get("volume_override_ml"):
        result["electrolyte_volume_override_ml"] = elec.get("volume_override_ml")

    return result


def generate_pouch_template() -> dict:
    """Generate a template configuration for a pouch cell.

    Returns:
        Template configuration dictionary
    """
    return {
        "cell_name": "Example Pouch Cell",
        "cathode": {
            "id": "NMC532_V1",
            "name": "NMC532",
            "chemistry": "NMC532",
            "rev_spec_capacity_mahg": 165.0,
            "max_spec_capacity_mahg": 180.0,
            "areal_weight_mgcm2": 18.5,
            "collector_thickness_um": 15.0,
            "coating_density_gcm3": 3.5,
            "coating_thickness_0pct_um": 70.0,
            "coating_thickness_100pct_um": 71.4,
        },
        "anode": {
            "id": "Graphite_V1",
            "name": "Graphite",
            "chemistry": "Graphite",
            "rev_spec_capacity_mahg": 360.0,
            "max_spec_capacity_mahg": 372.0,
            "areal_weight_mgcm2": 10.5,
            "collector_thickness_um": 10.0,
            "coating_density_gcm3": 1.6,
            "coating_thickness_0pct_um": 85.0,
            "coating_thickness_100pct_um": 89.25,
        },
        "separator": {
            "id": "Separator_V1",
            "name": "PE/PP Trilayer",
            "thickness_um": TYPICAL_SEPARATOR_UM,
            "porosity_pct": 40.0,
            "density_gcm3": DENSITY_PP,
            "areal_weight_mgcm2": 1.14,
        },
        "electrolyte": {"id": "LiPF6_EC_DMC", "name": "LiPF6 in EC:DMC", "density_gcm3": 1.25},
        "geometry": {
            "cathode_height_mm": 180.0,
            "cathode_width_mm": 100.0,
            "anode_offset_y_mm": 2.0,
            "anode_offset_x_mm": 2.0,
            "separator_offset_y_mm": 1.0,
            "separator_offset_x_mm": 1.0,
        },
        "packaging": {
            "pouch_offset_top_mm": 10.0,
            "pouch_offset_bottom_mm": 5.0,
            "pouch_offset_left_mm": 5.0,
            "pouch_offset_right_mm": 5.0,
        },
        "stack_config": {
            "number_of_stacks": 1,
            "electrode_pairs_per_stack": 15,
            "end_electrodes": "BothNegative",
            "separator_overwraps_per_stack": 1,
            "additional_overwraps_per_stack": 0,
            "insulation_shell_count": 1,
            "fixing_tapes_per_stack": 2,
        },
        "case_composition": [
            {
                "name": "PET",
                "version": "1.0",
                "thickness_um": 12.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PET,
            },
            {
                "name": "Aluminum",
                "version": "1.0",
                "thickness_um": 40.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_ALUMINUM,
            },
            {
                "name": "PP",
                "version": "1.0",
                "thickness_um": 80.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PP,
            },
        ],
        "anode_tab": {
            "material": "Copper",
            "height_mm": 30.0,
            "width_mm": 40.0,
            "thickness_mm": 0.2,
            "density_gcm3": 8.96,
        },
        "cathode_tab": {
            "material": "Aluminum",
            "height_mm": 30.0,
            "width_mm": 40.0,
            "thickness_mm": 0.3,
            "density_gcm3": 2.70,
        },
        "nominal_voltage_v": 3.65,
        "capacity_ah": None,
        "electrolyte_excess_factor": 1.10,
        "cathode_porosity_pct": 30.0,
        "anode_porosity_pct": 35.0,
    }


def cmd_calculate(args: argparse.Namespace) -> int:
    """Execute the calculate command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        return 1

    # Convert to input
    try:
        cell_input = config_to_pouch_input(config)
    except (KeyError, TypeError) as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1

    # Calculate
    calculator = CellCalculator()
    report = calculator.calculate_pouch_cell(cell_input)

    # Determine output format
    output_format = args.format
    if args.output:
        ext = Path(args.output).suffix.lower()
        if ext == ".json":
            output_format = "json"
        elif ext == ".csv":
            output_format = "csv"

    # Generate output
    if output_format == "json":
        bom = None
        if args.bom:
            # Calculate electrolyte volume for BOM
            from forge.engine.calculations.stack import calculate_pore_volumes

            cathode_pores, anode_pores, separator_pores = calculate_pore_volumes(
                cathode_area_cm2=cell_input.geometry.cathode_area_cm2,
                cathode_sheets=cell_input.stack_config.total_cathode_sheets,
                cathode_coating_thk_um=cell_input.cathode.coating_thickness_0pct_um,
                cathode_porosity_pct=cell_input.cathode_porosity_pct,
                anode_area_cm2=cell_input.geometry.anode_area_cm2,
                anode_sheets=cell_input.stack_config.total_anode_sheets,
                anode_coating_thk_um=cell_input.anode.coating_thickness_0pct_um,
                anode_porosity_pct=cell_input.anode_porosity_pct,
                separator_area_cm2=cell_input.geometry.separator_area_cm2,
                separator_sheets=cell_input.stack_config.total_separator_sheets,
                separator_thk_um=cell_input.separator.thickness_um,
                separator_porosity_pct=cell_input.separator.porosity_pct,
            )
            electrolyte_volume = (
                cathode_pores + anode_pores + separator_pores
            ) * cell_input.electrolyte_excess_factor

            bom = calculator.generate_bom(
                report=report,
                cathode=cell_input.cathode,
                anode=cell_input.anode,
                separator=cell_input.separator,
                electrolyte=cell_input.electrolyte,
                anode_tab=cell_input.anode_tab,
                cathode_tab=cell_input.cathode_tab,
                electrolyte_volume_ml=electrolyte_volume,
            )

        if args.output:
            export_json(report, bom, args.output)
            print(f"Report saved to: {args.output}")
        else:
            print(export_json(report, bom))

    elif output_format == "csv":
        if args.output:
            export_report_csv(report, args.output)
            print(f"Report saved to: {args.output}")
        else:
            print("Error: CSV output requires --output file path", file=sys.stderr)
            return 1

    else:  # text
        print(generate_report_text(report))

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute the validate command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for validation failure)
    """
    # List references if requested
    if args.list_references:
        print(format_reference_list())
        return 0

    # Require config for validation
    if not args.config:
        print("Error: --config is required for validation", file=sys.stderr)
        print("Use --list-references to see available reference cells", file=sys.stderr)
        return 1

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        return 1

    # Convert to input and calculate
    try:
        cell_input = config_to_pouch_input(config)
    except (KeyError, TypeError) as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1

    calculator = CellCalculator()
    report = calculator.calculate_pouch_cell(cell_input)

    # Try to use new reference cell system first
    try:
        # Check if reference exists as a JSON file
        available_refs = list_reference_cells()
        if args.reference in available_refs:
            validation = validate_cell(report, args.reference)
            print(format_validation_report(validation))
            return 0 if validation.all_passed else 1
    except FileNotFoundError:
        pass

    # Fall back to legacy validation
    if args.reference.lower() == "v1_pouch":
        reference = V1_POUCH_REFERENCE
        tolerances = V1_POUCH_TOLERANCES
    else:
        # Try to load from file
        try:
            with open(args.reference) as f:
                reference = json.load(f)
            tolerances = {}
        except FileNotFoundError:
            print(f"Error: Reference not found: {args.reference}", file=sys.stderr)
            print("Use --list-references to see available reference cells", file=sys.stderr)
            return 1

    # Validate
    default_tol = args.tolerance if args.tolerance else 5.0
    validation = validate_against_reference(
        report, reference, tolerances, default_tolerance_pct=default_tol
    )

    print(format_validation_report(validation))

    return 0 if validation.all_passed else 1


def cmd_info(args: argparse.Namespace) -> int:
    """Execute the info command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.list_references:
        print(format_reference_list())
        return 0

    if args.reference:
        try:
            info = get_reference_info(args.reference)
            print(f"Reference Cell: {info['name']}")
            print("=" * 50)
            print(f"ID: {info['id']}")
            print(f"Type: {info['cell_type']}")
            print(f"Chemistry: {info['chemistry']}")
            print(f"Source: {info['source']}")
            print(f"Confidence: {info['confidence']}")
            print(f"Capacity: {info['capacity_ah']} Ah")
            print(f"Nominal Voltage: {info['nominal_voltage_v']} V")
            print(f"Energy: {info['energy_wh']} Wh")
            print(f"Gravimetric ED: {info['gravimetric_ed_whkg']} Wh/kg")
            print(f"Validation Tolerance: {info['validation_tolerance_pct']}%")
        except FileNotFoundError:
            print(f"Error: Reference cell not found: {args.reference}", file=sys.stderr)
            return 1
        return 0

    if args.list_pybamm:
        from forge.materials.repositories import AVAILABLE_PARAMETER_SETS, check_pybamm_available

        print("Available PyBaMM Parameter Sets:")
        print("-" * 40)

        if not check_pybamm_available():
            print("(PyBaMM is not installed)")
            print("\nInstall with: pip install pybamm")
        else:
            for name in AVAILABLE_PARAMETER_SETS:
                print(f"  {name}")

        return 0

    if args.pybamm:
        from forge.materials.repositories import PyBaMMRepository, check_pybamm_available

        if not check_pybamm_available():
            print("Error: PyBaMM is not installed", file=sys.stderr)
            return 1

        try:
            repo = PyBaMMRepository(args.pybamm)
            summary = repo.get_parameter_summary()

            print(f"PyBaMM Parameter Set: {args.pybamm}")
            print("=" * 50)
            print(f"Cathode Chemistry: {summary['cathode_chemistry']}")
            print(f"Anode Chemistry: {summary['anode_chemistry']}")
            print(f"Cathode Thickness: {summary['cathode_thickness_um']:.1f} Âµm")
            print(f"Anode Thickness: {summary['anode_thickness_um']:.1f} Âµm")
            print(f"Separator Thickness: {summary['separator_thickness_um']:.1f} Âµm")
            print(f"Cathode Porosity: {summary['cathode_porosity']:.2f}")
            print(f"Anode Porosity: {summary['anode_porosity']:.2f}")
            print(f"Separator Porosity: {summary['separator_porosity']:.2f}")

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        return 0

    if args.excel:
        from forge.materials.repositories import ExcelRepository, check_pandas_available

        if not check_pandas_available():
            print("Error: pandas is not installed", file=sys.stderr)
            return 1

        try:
            repo = ExcelRepository(args.excel)

            print(f"Excel Material Database: {args.excel}")
            print("=" * 50)
            print(f"Cathodes: {', '.join(repo.list_cathodes()) or 'None'}")
            print(f"Anodes: {', '.join(repo.list_anodes()) or 'None'}")
            print(f"Separators: {', '.join(repo.list_separators()) or 'None'}")
            print(f"Electrolytes: {', '.join(repo.list_electrolytes()) or 'None'}")
            print(f"Packaging Presets: {', '.join(repo.list_packaging_presets()) or 'None'}")

        except FileNotFoundError:
            print(f"Error: Excel file not found: {args.excel}", file=sys.stderr)
            return 1

        return 0

    print(
        "Use --list-pybamm, --list-references, --pybamm <name>, --reference <id>, or --excel <path>"
    )
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    """Execute the template command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.from_reference:
        try:
            template = reference_to_config(args.from_reference)
        except FileNotFoundError:
            print(f"Error: Reference cell not found: {args.from_reference}", file=sys.stderr)
            return 1
    elif args.type == "excel":
        from forge.materials.repositories import check_pandas_available, create_template_excel

        if not check_pandas_available():
            print("Error: pandas is not installed", file=sys.stderr)
            return 1

        output = args.output
        if not output.endswith(".xlsx"):
            output = output.rsplit(".", 1)[0] + ".xlsx"

        create_template_excel(output)
        print(f"Excel template created: {output}")
        return 0
    else:
        template = generate_pouch_template()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(template, f, indent=2)
        print(f"Template created: {args.output}")
    else:
        print(json.dumps(template, indent=2))

    return 0


def cli(args: list | None = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command is None:
        parser.print_help()
        return 0

    if parsed_args.command == "calculate":
        return cmd_calculate(parsed_args)
    elif parsed_args.command == "validate":
        return cmd_validate(parsed_args)
    elif parsed_args.command == "info":
        return cmd_info(parsed_args)
    elif parsed_args.command == "template":
        return cmd_template(parsed_args)
    else:
        parser.print_help()
        return 0


def main():
    """Main entry point for the CLI."""
    sys.exit(cli())


if __name__ == "__main__":
    main()





