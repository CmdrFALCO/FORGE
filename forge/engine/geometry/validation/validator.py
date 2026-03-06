"""Main geometry validator class."""

from typing import TYPE_CHECKING

from . import rules
from .models import ValidationReport
from .thresholds import DEFAULT_THRESHOLDS, ValidationThresholds

if TYPE_CHECKING:
    from ..detailed_geometry import DetailedGeometry


class GeometryValidator:
    """Comprehensive geometry validator for DetailedGeometry.

    Runs all validation rules and produces a ValidationReport.

    Usage:
        validator = GeometryValidator()
        report = validator.validate(geometry)

        if not report.passed:
            print("Validation failed!")
            for error in report.get_errors():
                print(f"  {error}")
    """

    def __init__(
        self,
        thresholds: ValidationThresholds | None = None,
        skip_rules: list[str] | None = None,
    ):
        """Initialize validator.

        Args:
            thresholds: Custom thresholds (uses defaults if None)
            skip_rules: List of rule_ids to skip (e.g., ["DIM_002", "MFG_004"])
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.skip_rules = set(skip_rules or [])

    def validate(
        self,
        geometry: "DetailedGeometry",
        declared_capacity_ah: float | None = None,
        declared_mass_g: float | None = None,
    ) -> ValidationReport:
        """Run all validation rules on geometry.

        Args:
            geometry: DetailedGeometry to validate
            declared_capacity_ah: Optional declared capacity for cross-validation
            declared_mass_g: Optional declared mass for cross-validation

        Returns:
            ValidationReport with all results
        """
        report = ValidationReport(
            geometry_name=geometry.archetype_name,
            cell_type=geometry.cell_type,
        )

        # Run dimensional rules
        report.results.append(rules.validate_stack_fits_in_casing(geometry, self.thresholds))
        report.results.append(rules.validate_layer_thickness_consistency(geometry, self.thresholds))

        # Run safety rules
        report.results.append(rules.validate_anode_overhang(geometry, self.thresholds))
        report.results.append(rules.validate_separator_overhang(geometry, self.thresholds))
        report.results.append(rules.validate_np_ratio(geometry, self.thresholds))

        # Run manufacturing rules
        report.results.append(rules.validate_min_coating_thickness(geometry, self.thresholds))
        report.results.append(rules.validate_min_collector_thickness(geometry, self.thresholds))
        report.results.append(rules.validate_min_separator_thickness(geometry, self.thresholds))
        report.results.append(rules.validate_max_layer_count(geometry, self.thresholds))

        # Run cross-validation rules
        report.results.append(
            rules.validate_capacity_consistency(geometry, declared_capacity_ah, self.thresholds)
        )
        report.results.append(
            rules.validate_mass_consistency(geometry, declared_mass_g, self.thresholds)
        )

        # Filter out skipped rules
        if self.skip_rules:
            report.results = [r for r in report.results if r.rule_id not in self.skip_rules]

        return report

    def validate_for_export(
        self,
        geometry: "DetailedGeometry",
        strict: bool = True,
    ) -> tuple[bool, ValidationReport]:
        """Validate geometry before CAD export.

        Args:
            geometry: DetailedGeometry to validate
            strict: If True, warnings also block export

        Returns:
            Tuple of (can_export, report)
        """
        report = self.validate(geometry)

        if strict:
            can_export = report.passed and not report.has_warnings
        else:
            can_export = report.passed

        return can_export, report


def validate_geometry(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds | None = None,
) -> ValidationReport:
    """Convenience function to validate geometry.

    Args:
        geometry: DetailedGeometry to validate
        thresholds: Optional custom thresholds

    Returns:
        ValidationReport
    """
    validator = GeometryValidator(thresholds=thresholds)
    return validator.validate(geometry)
