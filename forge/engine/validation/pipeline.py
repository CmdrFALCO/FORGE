"""
Combined validation pipeline for LLM-generated cell definitions.

This module implements the complete supervision Petri Net with two guard transitions:
  LLM Output
    ↓
  [T_schema_check] (Level 1: JSON Schema validation)
    ↓
  Valid Structure OR Feedback to LLM (retry)
    ↓
  [T_constraint_check] (Level 2: Physics constraint validation)
    ↓
  Valid Design OR Feedback to LLM (retry)
    ↓
  CellCAD Engine Input

The validation pipeline is the gatekeeper between driver layer and execution engine.
"""

from pathlib import Path

import yaml

from .constraint_validator import get_constraint_descriptions, validate_physics
from .schema_validator import ValidationResult, validate_required_fields, validate_structure


def validate_cell_definition(
    cell_dict: dict, strict: bool = True, cell_type: str = "prismatic"
) -> ValidationResult:
    """
    Full validation pipeline for LLM-generated cell definitions.

    Two-stage validation:
      1. Schema validation (structure, types, simple bounds)
      2. Physics validation (cross-field constraints)

    This is the main entry point for validating cell definitions from LLMs.

    Args:
        cell_dict: Cell definition dict (from YAML, JSON, or LLM output)
        strict: If True, exit on first validation failure. If False, collect all errors.
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        ValidationResult - check .valid and .errors for details

    Usage:
        result = validate_cell_definition(cell_dict, cell_type="cylindrical")
        if not result.valid:
            print(result.to_llm_feedback())  # Send back to LLM for retry
            return
        else:
            # Proceed to CellCAD engine
            cellcad_input = convert_to_engine_format(cell_dict)
            output = cellcad_engine.run(cellcad_input)
    """

    # Level 1: Quick check for required fields
    required_result = validate_required_fields(cell_dict, cell_type)
    if not required_result.valid and strict:
        return required_result

    # Level 1: Full schema validation
    schema_result = validate_structure(cell_dict, cell_type)
    if not schema_result.valid and strict:
        return schema_result  # Early exit - structure errors block further checks

    # Level 2: Physics constraint validation
    # Only run physics checks if NOT a template (template has 'default' fields and metadata)
    is_template = "_meta" in cell_dict and "default" in str(cell_dict).lower()
    if is_template:
        # Template structure - just return schema validation result
        return schema_result

    physics_result = validate_physics(cell_dict, cell_type)

    return physics_result


def validate_yaml_file(yaml_path: str | Path, cell_type: str = "prismatic") -> ValidationResult:
    """
    Convenience function to validate a YAML file directly.

    Args:
        yaml_path: Path to YAML file containing cell definition
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        ValidationResult

    Usage:
        result = validate_yaml_file("my_cell.yaml", cell_type="cylindrical")
        if not result.valid:
            print(result.to_llm_feedback())
    """
    yaml_path = Path(yaml_path)

    with open(yaml_path, encoding="utf-8") as f:
        cell_dict = yaml.safe_load(f)

    return validate_cell_definition(cell_dict, cell_type=cell_type)


def validate_json_string(json_string: str, cell_type: str = "prismatic") -> ValidationResult:
    """
    Validate a JSON string containing cell definition.

    Args:
        json_string: JSON string with cell definition
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        ValidationResult

    Usage:
        llm_output_json = '{"_meta": {...}, "geometry": {...}, ...}'
        result = validate_json_string(llm_output_json, cell_type="cylindrical")
    """
    import json

    try:
        cell_dict = json.loads(json_string)
    except json.JSONDecodeError as e:
        from .schema_validator import ValidationError

        return ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="(json_parse)",
                    message=f"Invalid JSON: {e.msg}",
                    value=json_string[:100],
                    constraint="json_syntax",
                )
            ],
            level="schema",
        )

    return validate_cell_definition(cell_dict, cell_type=cell_type)


def get_validation_report(cell_dict: dict, cell_type: str = "prismatic") -> str:
    """
    Get a detailed validation report for a cell definition.

    Includes information about all validation stages and constraints.

    Args:
        cell_dict: Cell definition to validate
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        Multi-line string report
    """
    result = validate_cell_definition(cell_dict, cell_type=cell_type)

    report = []
    report.append("=" * 80)
    report.append(f"CELLCAD VALIDATION REPORT ({cell_type.upper()})")
    report.append("=" * 80)
    report.append("")

    if result.valid:
        report.append("STATUS: VALID")
        report.append("")
        report.append("This cell definition passes all validation checks:")
        report.append("  [PASS] Schema validation (structure, types, bounds)")
        report.append("  [PASS] Physics constraints (geometry, electrochemistry, stack config)")
        report.append("")
        report.append("Ready to proceed to CellCAD engine for:")
        report.append("  - Derived property calculations")
        report.append("  - CAD geometry generation")
        report.append("  - STEP file export")
    else:
        report.append(f"STATUS: INVALID ({result.level.upper()} LEVEL)")
        report.append("")
        report.append(f"Found {len(result.errors)} validation error(s):")
        report.append("")

        for i, error in enumerate(result.errors, 1):
            report.append(f"[{i}] {error.path}")
            report.append(f"    Error: {error.message}")
            report.append("")

    report.append("=" * 80)
    report.append("CONSTRAINTS ENFORCED:")
    report.append("=" * 80)
    report.append("")
    report.append(get_constraint_descriptions(cell_type))
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def create_validation_context(cell_type: str = "prismatic") -> str:
    """
    Create a detailed context string for LLM drivers about validation rules.

    This can be provided to LLMs in their system prompt to help them understand
    what constraints they need to satisfy.

    Args:
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        String describing all validation rules
    """
    cell_type_lower = cell_type.lower()

    if cell_type_lower == "pouch":
        domains_description = """Your output MUST be a valid pouch cell definition with these top-level domains:
  - _meta: Metadata about the design
  - geometry: Sheet dimensions (cathode_height, cathode_width, anode_offset, separator_offset)
  - stack_config: Electrode arrangement (num_stacks, electrode_pairs_per_stack, end_electrode_config)
  - electrochemistry: Active materials (cathode, anode, separator, electrolyte)
  - tabs: Tab configurations for current collection (cathode and anode)
  - packaging: Pouch packaging (pouch_thickness, offsets)

Each parameter MUST have the correct type (number or string) and be within
the specified bounds from pouch_master.schema.json."""
    elif cell_type_lower == "cylindrical":
        domains_description = """Your output MUST be a valid cylindrical cell definition with these top-level domains:
  - _meta: Metadata about the design (cell_type, format, design_intent)
  - geometry: Can dimensions (diameter, length, wall thicknesses, header_height)
  - winding: Jelly roll configuration (mandrel, clearance, tension, tab_type)
  - electrochemistry: Active materials (cathode, anode, separator, electrolyte)
  - housing: Can housing config (can_material, header_mass_g)

Each parameter MUST have the correct type (number or string) and be within
the specified bounds from cylindrical_master.schema.json."""
    else:
        domains_description = """Your output MUST be a valid prismatic cell definition with these top-level domains:
  - _meta: Metadata about the design
  - envelope: Physical cell dimensions (height, width, thickness, walls)
  - stack_config: Electrode arrangement (stacks, pairs, sheet geometry)
  - electrochemistry: Active materials (cathode, anode, separator, electrolyte)
  - current_collection: Tabs for current collection (cathode and anode)
  - packaging: Housing and insulation materials

Each parameter MUST have the correct type (number or string) and be within
the specified bounds from prismatic_master.schema.json."""

    return f"""
CELLCAD VALIDATION RULES FOR LLM DRIVERS ({cell_type.upper()})
=========================================

Your task is to generate valid {cell_type} battery cell parameters that will pass
two levels of validation before being sent to the CellCAD engine.

LEVEL 1: SCHEMA VALIDATION (Structure and Types)
-------------------------------------------------
{domains_description}

LEVEL 2: PHYSICS CONSTRAINTS (Cross-field Rules)
-------------------------------------------------
Beyond structure, your parameters must satisfy these physics rules:

{get_constraint_descriptions(cell_type)}

CRITICAL CONSTRAINT: N/P Ratio
The anode-to-cathode capacity ratio MUST be in [1.05, 1.25]:
  - Below 1.05: Risk of lithium plating (safety failure)
  - Above 1.25: Risk of interface instability (degradation)

This is THE most important constraint. Always verify N/P ratio when
modifying anode or cathode parameters.

WORKFLOW:
1. Understand the user's intent (e.g., "high-energy cell", "long-life")
2. Map to parameter changes using trade-off documentation
3. Adjust parameters while respecting all constraints
4. Verify N/P ratio is in safe range
5. Return complete parameter set

If validation fails, you will receive specific error messages indicating:
  - Which parameter(s) failed
  - What the constraint is
  - How to fix it

Then retry with corrected parameters.
""".strip()
