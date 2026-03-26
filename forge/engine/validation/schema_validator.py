"""
Level 1 Validation: Structure, types, and simple bounds.
Uses JSON Schema to validate LLM-generated cell definitions.

This module implements the first guard transition in the supervision Petri Net:
  LLM Output → [T_schema_check] → Valid Structure (or Feedback)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema


@dataclass
class ValidationError:
    """Single validation error with context for LLM feedback."""

    path: str  # JSON path to error, e.g., "envelope.external.height_mm"
    message: str  # Human-readable error message
    value: Any  # The invalid value (if applicable)
    constraint: str  # What constraint was violated


@dataclass
class ConstraintResult:
    """Result of a single constraint check (pass or fail).

    Used for per-constraint logging in thesis experiments.
    Every constraint emits one of these, regardless of pass/fail.
    """

    constraint_id: str      # "C1", "PR3", "CY7", etc.
    name: str               # "np_ratio", "internal_height", etc.
    passed: bool
    actual_value: Any       # the value that was checked (None if field missing)
    threshold: Any          # the bound/range/expected value
    message: str            # human-readable; empty string if passed
    check_time_ms: float    # milliseconds for this check


@dataclass
class ValidationResult:
    """Result of validation with errors if any."""

    valid: bool
    errors: list[ValidationError]
    level: str = "schema"  # "schema" or "physics"
    constraint_results: list[ConstraintResult] = field(default_factory=list)

    def to_llm_feedback(self) -> str:
        """Format errors as feedback string for LLM to retry."""
        if self.valid:
            return "Validation passed."

        lines = ["[VALIDATION FAILED - SCHEMA LEVEL]"]
        lines.append(f"Found {len(self.errors)} error(s). Please fix and retry:")
        lines.append("")

        for err in self.errors:
            lines.append(f"  [{err.path}]")
            lines.append(f"    Error: {err.message}")
            if err.value is not None and not isinstance(err.value, dict):
                lines.append(f"    Got: {err.value}")
            lines.append("")

        return "\n".join(lines)


def load_schema(cell_type: str = "prismatic") -> dict:
    """Load the schema from JSON file based on cell type.

    Args:
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        JSON Schema dictionary
    """
    cell_type_lower = cell_type.lower()
    if cell_type_lower == "pouch":
        schema_file = "pouch_master.schema.json"
    elif cell_type_lower == "cylindrical":
        schema_file = "cylindrical_master.schema.json"
    else:
        schema_file = "prismatic_master.schema.json"

    schema_path = Path(__file__).parent.parent.parent / "data" / "templates" / schema_file
    with open(schema_path) as f:
        return json.load(f)


def validate_structure(cell_dict: dict, cell_type: str = "prismatic") -> ValidationResult:
    """
    Validate cell definition against JSON Schema (structure and types).

    This is Level 1 validation: checks that the cell definition has the correct
    structure and types. Does not check physics constraints (Level 2).

    Args:
        cell_dict: Cell definition dictionary (from YAML, JSON, or LLM output)
        cell_type: Type of cell - "prismatic" or "pouch" (default: "prismatic")

    Returns:
        ValidationResult with any schema errors

    Example:
        result = validate_structure(cell_dict, cell_type="pouch")
        if not result.valid:
            print(result.to_llm_feedback())
    """
    schema = load_schema(cell_type)
    validator = jsonschema.Draft7Validator(schema)

    errors = []
    for error in validator.iter_errors(cell_dict):
        # Format the path nicely
        path_parts = [str(p) for p in error.absolute_path]
        path = ".".join(path_parts) if path_parts else "(root)"

        # Include constraint type and validator details in path when helpful
        if error.validator == "required" and error.validator_value:
            # Extract which required property is missing
            missing = (
                list(set(error.validator_value) - set(error.instance.keys()))
                if isinstance(error.instance, dict)
                else []
            )
            if missing:
                path = f"{path}.{missing[0]}" if path != "(root)" else missing[0]

        errors.append(
            ValidationError(
                path=path, message=error.message, value=error.instance, constraint=error.validator
            )
        )

    return ValidationResult(valid=len(errors) == 0, errors=errors, level="schema")


def validate_required_fields(cell_dict: dict, cell_type: str = "prismatic") -> ValidationResult:
    """
    Quick validation that all required core fields exist.

    This is a lighter check than full schema validation.

    Args:
        cell_dict: Cell definition dictionary
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        ValidationResult
    """
    cell_type_lower = cell_type.lower()
    if cell_type_lower == "pouch":
        required_domains = ["geometry", "stack_config", "electrochemistry", "tabs", "packaging"]
    elif cell_type_lower == "cylindrical":
        required_domains = ["geometry", "winding", "electrochemistry", "housing"]
    else:
        required_domains = [
            "envelope",
            "stack_config",
            "electrochemistry",
            "current_collection",
            "packaging",
        ]

    # Structural hints for missing domains — helps LLM fix on retry
    _DOMAIN_SKELETONS: dict[str, str] = {
        "current_collection": (
            "Add a current_collection section with this structure:\n"
            "current_collection:\n"
            "  tabs:\n"
            "    cathode:\n"
            "      material: \"Aluminum\"\n"
            "      height_mm: <20-80>\n"
            "      width_mm: <30-100>\n"
            "      thickness_mm: <0.1-0.5>\n"
            "    anode:\n"
            "      material: \"Nickel-plated copper\"\n"
            "      height_mm: <20-80>\n"
            "      width_mm: <30-100>\n"
            "      thickness_mm: <0.1-0.4>"
        ),
        "packaging": (
            "Add a packaging section with this structure:\n"
            "packaging:\n"
            "  housing:\n"
            "    case_material: \"Aluminum\"\n"
            "    case_density_g_cm3: 2.70\n"
            "    lid_thickness_mm: <1.0-3.0>\n"
            "  insulation:\n"
            "    shell_thickness_um: <80-200>\n"
            "    shell_count: <1-3>\n"
            "    fixing_tape_count: <2-6>"
        ),
    }

    errors = []
    for domain in required_domains:
        if domain not in cell_dict:
            skeleton = _DOMAIN_SKELETONS.get(domain, "")
            hint = f". {skeleton}" if skeleton else ""
            errors.append(
                ValidationError(
                    path=domain,
                    message=f"Required domain '{domain}' is missing{hint}",
                    value=None,
                    constraint="required_field",
                )
            )

    return ValidationResult(valid=len(errors) == 0, errors=errors, level="schema")
