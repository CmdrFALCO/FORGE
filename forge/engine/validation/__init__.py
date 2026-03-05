"""Validation module for FORGE engine and AXIOM pipelines.

This package exposes:
- Two-level input validation for generated cell definitions (schema + physics)
- Reference-based result validation utilities for calculated cell reports
"""

from . import result_validation
from .constraint_validator import (
    get_constraint_descriptions,
    validate_physics,
)
from .pipeline import (
    create_validation_context,
    get_validation_report,
    validate_cell_definition,
    validate_json_string,
    validate_yaml_file,
)
from .result_validation import (
    REFERENCE_DIR,
    ReferenceCell,
    V1_POUCH_REFERENCE,
    V1_POUCH_TOLERANCES,
    V1_PRISMATIC_REFERENCE,
    ValidationReport,
    format_reference_list,
    format_validation_report,
    get_reference_info,
    list_reference_cells,
    load_reference_cell,
    quick_validate_pouch,
    validate_against_reference,
    validate_cell,
    validate_value,
)
from .schema_validator import (
    ValidationError,
    ValidationResult,
    validate_required_fields,
    validate_structure,
)


__all__ = [
    # Main validation functions
    "validate_cell_definition",
    "validate_yaml_file",
    "validate_json_string",
    "validate_structure",
    "validate_physics",
    # Result types (schema/physics)
    "ValidationResult",
    "ValidationError",
    # Utilities
    "get_validation_report",
    "get_constraint_descriptions",
    "create_validation_context",
    "validate_required_fields",
    # Reference validation module + selected API
    "result_validation",
    "REFERENCE_DIR",
    "ReferenceCell",
    "ValidationReport",
    "V1_POUCH_REFERENCE",
    "V1_POUCH_TOLERANCES",
    "V1_PRISMATIC_REFERENCE",
    "list_reference_cells",
    "load_reference_cell",
    "get_reference_info",
    "validate_value",
    "validate_against_reference",
    "validate_cell",
    "format_validation_report",
    "format_reference_list",
    "quick_validate_pouch",
]

__version__ = "1.0.0"
__description__ = "FORGE engine validation module (schema, physics, and reference validation)"
