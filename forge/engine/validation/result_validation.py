"""Validation utilities for FORGE engine.

This module provides validation functions to compare calculated results
against reference data from specification and commercial cell databases.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge.engine.models.results import CellReport

# =============================================================================
# Reference Data Directory
# =============================================================================

REFERENCE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "reference"
"""Default directory for reference cell JSON files."""


# =============================================================================
# Legacy Reference Data (for backward compatibility)
# =============================================================================

V1_POUCH_REFERENCE: dict[str, float] = {
    "capacity_ah": 9.348,
    "nominal_voltage_v": 3.65,
    "total_mass_g": 320.0,
    "cathode_mass_g": 150.0,
    "anode_mass_g": 85.0,
    "separator_mass_g": 6.0,
    "electrolyte_mass_g": 58.0,
    "housing_mass_g": 17.3,
    "gravimetric_ed_whkg": 107.0,
    "volumetric_ed_cell_whl": 250.0,
}
"""Reference values for V1 Pouch cell design."""

V1_POUCH_TOLERANCES: dict[str, float] = {
    "capacity_ah": 0.0,  # Exact match expected
    "nominal_voltage_v": 0.0,  # Exact match expected
    "total_mass_g": 5.0,  # ±5%
    "cathode_mass_g": 2.0,  # ±2%
    "anode_mass_g": 2.0,  # ±2%
    "separator_mass_g": 2.0,  # ±2%
    "electrolyte_mass_g": 5.0,  # ±5%
    "housing_mass_g": 5.0,  # ±5%
    "gravimetric_ed_whkg": 2.0,  # ±2%
    "volumetric_ed_cell_whl": 2.0,  # ±2%
}
"""Tolerance percentages for V1 Pouch reference values."""

V1_PRISMATIC_REFERENCE: dict[str, float] = {
    "capacity_ah": 156.3,
    "nominal_voltage_v": 3.65,
    "cell_height_mm": 113.0,
    "cell_width_mm": 163.0,
    "cell_thickness_soc0_mm": 41.0,
}
"""Reference values for V1 Prismatic cell design."""


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ValidationResult:
    """Result of a single value validation.

    Attributes:
        parameter: Parameter name
        expected: Expected (reference) value
        actual: Calculated value
        delta: Absolute difference
        delta_pct: Relative difference [%]
        tolerance_pct: Allowed tolerance [%]
        passed: Whether the validation passed
    """

    parameter: str
    expected: float
    actual: float
    delta: float
    delta_pct: float
    tolerance_pct: float
    passed: bool


@dataclass
class ValidationReport:
    """Complete validation report.

    Attributes:
        results: List of individual validation results
        all_passed: Whether all validations passed
        pass_count: Number of passed validations
        fail_count: Number of failed validations
        reference_id: ID of the reference cell used
        reference_name: Name of the reference cell
    """

    results: list
    all_passed: bool
    pass_count: int
    fail_count: int
    reference_id: str = ""
    reference_name: str = ""


@dataclass
class ReferenceCell:
    """Reference cell data loaded from JSON.

    Attributes:
        id: Unique identifier
        name: Display name
        cell_type: Cell type (Pouch, Prismatic, etc.)
        source: Data source
        confidence: Confidence level (high, medium, low)
        targets: Validation target values
        tolerances: Per-parameter tolerance values
        default_tolerance: Default tolerance if not specified per-parameter
        raw_data: Complete raw JSON data
    """

    id: str
    name: str
    cell_type: str
    source: str
    confidence: str
    targets: dict[str, float]
    tolerances: dict[str, float]
    default_tolerance: float
    raw_data: dict[str, Any]


# =============================================================================
# Reference Cell Loading Functions
# =============================================================================


def list_reference_cells(
    reference_dir: Path | None = None, cell_type: str | None = None
) -> list[str]:
    """List available reference cell IDs.

    Args:
        reference_dir: Directory containing reference JSON files.
                       Defaults to data/reference in the package.
        cell_type: Optional filter by cell type ("Pouch", "Prismatic", etc.)
                   Case-insensitive matching.

    Returns:
        List of reference cell IDs (JSON filenames without extension)
    """
    if reference_dir is None:
        reference_dir = REFERENCE_DIR

    if not reference_dir.exists():
        return []

    all_cells = sorted([f.stem for f in reference_dir.glob("*.json") if f.is_file()])

    # Filter by cell_type if specified
    if cell_type is not None:
        filtered = []
        cell_type_lower = cell_type.lower()
        for cell_id in all_cells:
            try:
                ref = load_reference_cell(cell_id, reference_dir)
                if ref.cell_type.lower() == cell_type_lower:
                    filtered.append(cell_id)
            except (FileNotFoundError, ValueError):
                # Skip cells that can't be loaded
                pass
        return filtered

    return all_cells


def load_reference_cell(cell_id: str, reference_dir: Path | None = None) -> ReferenceCell:
    """Load a reference cell from JSON file.

    Args:
        cell_id: Reference cell ID (filename without .json extension)
        reference_dir: Directory containing reference JSON files.
                       Defaults to data/reference in the package.

    Returns:
        ReferenceCell object with loaded data

    Raises:
        FileNotFoundError: If reference file not found
        ValueError: If JSON is invalid or missing required fields
    """
    if reference_dir is None:
        reference_dir = REFERENCE_DIR

    file_path = reference_dir / f"{cell_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Reference cell not found: {cell_id}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    if "metadata" not in data:
        raise ValueError(f"Missing 'metadata' section in {cell_id}.json")
    if "validation" not in data:
        raise ValueError(f"Missing 'validation' section in {cell_id}.json")

    metadata = data["metadata"]
    validation = data["validation"]

    # Extract targets and tolerances
    targets = validation.get("targets", {})
    tolerances = validation.get("tolerances", {})
    default_tolerance = validation.get("tolerance_pct", 5.0)

    return ReferenceCell(
        id=metadata.get("id", cell_id),
        name=metadata.get("name", cell_id),
        cell_type=metadata.get("cell_type", "Unknown"),
        source=metadata.get("source", "Unknown"),
        confidence=metadata.get("confidence", "unknown"),
        targets=targets,
        tolerances=tolerances,
        default_tolerance=default_tolerance,
        raw_data=data,
    )


def get_reference_info(cell_id: str, reference_dir: Path | None = None) -> dict[str, Any]:
    """Get summary information about a reference cell.

    Args:
        cell_id: Reference cell ID
        reference_dir: Directory containing reference JSON files

    Returns:
        Dictionary with summary information
    """
    ref = load_reference_cell(cell_id, reference_dir)
    specs = ref.raw_data.get("cell_specs", {})

    return {
        "id": ref.id,
        "name": ref.name,
        "cell_type": ref.cell_type,
        "source": ref.source,
        "confidence": ref.confidence,
        "chemistry": specs.get("chemistry", "Unknown"),
        "capacity_ah": specs.get("capacity_ah"),
        "nominal_voltage_v": specs.get("nominal_voltage_v"),
        "energy_wh": specs.get("energy_wh"),
        "gravimetric_ed_whkg": specs.get("gravimetric_ed_whkg"),
        "validation_tolerance_pct": ref.default_tolerance,
    }


# =============================================================================
# Validation Functions
# =============================================================================


def validate_value(
    parameter: str, expected: float, actual: float, tolerance_pct: float = 5.0
) -> ValidationResult:
    """Validate a single calculated value against reference.

    Args:
        parameter: Parameter name
        expected: Expected (reference) value
        actual: Calculated value
        tolerance_pct: Allowed tolerance [%]

    Returns:
        ValidationResult with comparison details
    """
    delta = abs(actual - expected)
    delta_pct = (delta / expected * 100) if expected != 0 else 0.0
    passed = delta_pct <= tolerance_pct

    return ValidationResult(
        parameter=parameter,
        expected=expected,
        actual=actual,
        delta=delta,
        delta_pct=delta_pct,
        tolerance_pct=tolerance_pct,
        passed=passed,
    )


def validate_against_reference(
    calculated: CellReport,
    reference: dict[str, float],
    tolerances: dict[str, float] | None = None,
    default_tolerance_pct: float = 5.0,
) -> ValidationReport:
    """Compare calculated values against reference data.

    Args:
        calculated: Calculated cell report
        reference: Dictionary of expected values
        tolerances: Optional dictionary of parameter-specific tolerances [%]
        default_tolerance_pct: Default tolerance if not specified [%]

    Returns:
        ValidationReport with all comparison results
    """
    if tolerances is None:
        tolerances = {}

    results = []

    for param, expected in reference.items():
        # Get actual value from report
        if hasattr(calculated, param):
            actual = getattr(calculated, param)
        else:
            # Skip parameters not in report
            continue

        # Get tolerance for this parameter
        tolerance = tolerances.get(param, default_tolerance_pct)

        # Validate
        result = validate_value(param, expected, actual, tolerance)
        results.append(result)

    # Summary
    pass_count = sum(1 for r in results if r.passed)
    fail_count = len(results) - pass_count
    all_passed = fail_count == 0

    return ValidationReport(
        results=results,
        all_passed=all_passed,
        pass_count=pass_count,
        fail_count=fail_count,
    )


def validate_cell(
    calculated: CellReport, reference_id: str, reference_dir: Path | None = None
) -> ValidationReport:
    """Validate calculated results against a reference cell.

    This is the main validation function that loads a reference cell
    by ID and validates the calculated report against it.

    Args:
        calculated: Calculated cell report
        reference_id: Reference cell ID (e.g., "v1_pouch", "a123_amp20")
        reference_dir: Optional directory for reference files

    Returns:
        ValidationReport with all comparison results

    Raises:
        FileNotFoundError: If reference cell not found
    """
    ref = load_reference_cell(reference_id, reference_dir)

    results = []

    for param, expected in ref.targets.items():
        # Get actual value from report
        if hasattr(calculated, param):
            actual = getattr(calculated, param)
        else:
            # Skip parameters not in report
            continue

        # Get tolerance for this parameter
        tolerance = ref.tolerances.get(param, ref.default_tolerance)

        # Validate
        result = validate_value(param, expected, actual, tolerance)
        results.append(result)

    # Summary
    pass_count = sum(1 for r in results if r.passed)
    fail_count = len(results) - pass_count
    all_passed = fail_count == 0

    return ValidationReport(
        results=results,
        all_passed=all_passed,
        pass_count=pass_count,
        fail_count=fail_count,
        reference_id=ref.id,
        reference_name=ref.name,
    )


# =============================================================================
# Formatting Functions
# =============================================================================


def format_validation_report(report: ValidationReport) -> str:
    """Format validation report as text.

    Args:
        report: Validation report to format

    Returns:
        Formatted text report
    """
    lines = [
        "=" * 80,
        "                        VALIDATION REPORT",
    ]

    if report.reference_name:
        lines.append(f"                  Reference: {report.reference_name}")

    lines.extend(
        [
            "=" * 80,
            "",
            f"  Summary: {report.pass_count} passed, {report.fail_count} failed",
            f"  Status:  {'PASSED' if report.all_passed else 'FAILED'}",
            "",
            "-" * 80,
            f"  {'Parameter':<30} {'Expected':>12} {'Actual':>12} {'Delta %':>10} {'Status':>8}",
            "-" * 80,
        ]
    )

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(
            f"  {r.parameter:<30} {r.expected:>12.3f} {r.actual:>12.3f} "
            f"{r.delta_pct:>9.2f}% {status:>8}"
        )

    lines.append("=" * 80)

    return "\n".join(lines)


def format_reference_list(reference_dir: Path | None = None) -> str:
    """Format a list of available reference cells.

    Args:
        reference_dir: Directory containing reference JSON files

    Returns:
        Formatted text list
    """
    cell_ids = list_reference_cells(reference_dir)

    if not cell_ids:
        return "No reference cells found."

    lines = [
        "Available Reference Cells:",
        "-" * 60,
    ]

    for cell_id in cell_ids:
        try:
            info = get_reference_info(cell_id, reference_dir)
            lines.append(f"  {cell_id:<20} {info['name']:<25} ({info['confidence']} confidence)")
        except (FileNotFoundError, ValueError) as e:
            lines.append(f"  {cell_id:<20} (error loading: {e})")

    return "\n".join(lines)


# =============================================================================
# Quick Validation Functions
# =============================================================================


def quick_validate_pouch(calculated: CellReport) -> bool:
    """Quick validation against V1 Pouch reference.

    Args:
        calculated: Calculated cell report

    Returns:
        True if all validations pass, False otherwise
    """
    report = validate_against_reference(
        calculated,
        V1_POUCH_REFERENCE,
        V1_POUCH_TOLERANCES,
    )
    return report.all_passed
