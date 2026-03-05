"""Geometry validation module."""

from .models import (
    Severity,
    ValidationCategory,
    ValidationReport,
    ValidationResult,
)
from .thresholds import (
    DEFAULT_THRESHOLDS,
    ValidationThresholds,
)
from .validator import (
    GeometryValidator,
    validate_geometry,
)


__all__ = [
    # Models
    "Severity",
    "ValidationCategory",
    "ValidationResult",
    "ValidationReport",
    # Thresholds
    "ValidationThresholds",
    "DEFAULT_THRESHOLDS",
    # Validator
    "GeometryValidator",
    "validate_geometry",
]
