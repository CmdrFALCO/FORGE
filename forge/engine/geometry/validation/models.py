"""Validation result models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Validation result severity levels."""

    ERROR = "error"  # Must fix before export
    WARNING = "warning"  # Should review, but can proceed
    INFO = "info"  # Informational note


class ValidationCategory(str, Enum):
    """Categories of validation rules."""

    DIMENSIONAL = "dimensional"
    SAFETY = "safety"
    MANUFACTURING = "manufacturing"
    CROSS_VALIDATION = "cross_validation"


@dataclass
class ValidationResult:
    """Single validation check result."""

    rule_id: str  # Unique identifier, e.g., "DIM_001"
    rule_name: str  # Human-readable name
    category: ValidationCategory
    severity: Severity
    passed: bool
    message: str  # Description of result
    details: dict[str, Any] = field(default_factory=dict)  # Additional data

    def __str__(self) -> str:
        status = "PASS" if self.passed else f"{self.severity.value.upper()}"
        return f"[{self.rule_id}] {status}: {self.message}"


@dataclass
class ValidationReport:
    """Complete validation report for a geometry."""

    geometry_name: str
    cell_type: str
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if no errors (warnings/info OK)."""
        return not any(r.severity == Severity.ERROR and not r.passed for r in self.results)

    @property
    def has_warnings(self) -> bool:
        """True if any warnings present."""
        return any(r.severity == Severity.WARNING and not r.passed for r in self.results)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.ERROR and not r.passed)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.WARNING and not r.passed)

    @property
    def info_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.INFO and not r.passed)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    def get_by_category(self, category: ValidationCategory) -> list[ValidationResult]:
        """Get results filtered by category."""
        return [r for r in self.results if r.category == category]

    def get_by_severity(self, severity: Severity) -> list[ValidationResult]:
        """Get results filtered by severity."""
        return [r for r in self.results if r.severity == severity]

    def get_failures(self) -> list[ValidationResult]:
        """Get all failed validations."""
        return [r for r in self.results if not r.passed]

    def get_errors(self) -> list[ValidationResult]:
        """Get failed error-level validations."""
        return [r for r in self.results if r.severity == Severity.ERROR and not r.passed]

    def summary(self) -> str:
        """Generate summary string."""
        total = len(self.results)
        passed = self.pass_count
        status = "PASSED" if self.passed else "FAILED"

        return (
            f"{status} - {passed}/{total} checks passed "
            f"(Errors: {self.error_count}, Warnings: {self.warning_count}, "
            f"Info: {self.info_count})"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "geometry_name": self.geometry_name,
            "cell_type": self.cell_type,
            "passed": self.passed,
            "summary": {
                "total": len(self.results),
                "passed": self.pass_count,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
            },
            "results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category.value,
                    "severity": r.severity.value,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }
