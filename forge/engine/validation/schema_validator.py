"""
Level 1 Validation: Structure, types, and simple bounds.
Uses JSON Schema to validate LLM-generated cell definitions.

This module implements the first guard transition in the supervision Petri Net:
  LLM Output → [T_schema_check] → Valid Structure (or Feedback)
"""

import json
from dataclasses import dataclass
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
class ValidationResult:
    """Result of validation with errors if any."""

    valid: bool
    errors: list[ValidationError]
    level: str = "schema"  # "schema" or "physics"

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

    errors = []
    for domain in required_domains:
        if domain not in cell_dict:
            errors.append(
                ValidationError(
                    path=domain,
                    message=f"Required domain '{domain}' is missing",
                    value=None,
                    constraint="required_field",
                )
            )

    return ValidationResult(valid=len(errors) == 0, errors=errors, level="schema")
