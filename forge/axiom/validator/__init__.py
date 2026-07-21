"""AXIOM-facing adapter for the production FORGE validation pipeline.

Deterministic validation is implemented in :mod:`forge.engine.validation`.
AXIOM delegates to that production pipeline so engineering rules and evidence
remain authoritative in one place rather than being duplicated here.
"""

from typing import Any

from forge.engine.validation import ValidationResult
from forge.engine.validation import pipeline as validation_pipeline

__all__ = ["FormalValidator", "ValidationResult"]


class FormalValidator:
    """Expose production cell-definition validation at the AXIOM boundary."""

    def validate(
        self,
        cell_definition: dict[str, Any],
        cell_type: str = "prismatic",
        *,
        strict: bool = True,
    ) -> ValidationResult:
        """Validate a cell definition with the production FORGE pipeline.

        The returned object is the production ``ValidationResult``; constraint
        evidence and feedback are not translated or wrapped.
        """
        return validation_pipeline.validate_cell_definition(
            cell_definition,
            strict=strict,
            cell_type=cell_type,
        )
