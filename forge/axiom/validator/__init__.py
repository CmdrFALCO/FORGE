"""
AXIOM Validator - Multi-stage formal validation orchestration.

Orchestrates the validation pipeline for LLM-generated cell configurations.
Currently, validation logic lives in supervisor/driver.py calling
forge.engine.validation.pipeline.validate_cell_definition() directly.
This module will extract and extend that orchestration with:
- Multi-stage validation (schema -> physics -> cross-field)
- Validation result aggregation
- Configurable validation profiles
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationStageResult:
    """Result from a single validation stage."""

    stage_name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Aggregated result from all validation stages."""

    stages: list[ValidationStageResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(s.passed for s in self.stages)

    @property
    def all_errors(self) -> list[str]:
        return [e for s in self.stages for e in s.errors]


class FormalValidator:
    """
    Multi-stage formal validator for LLM-generated cell configurations.

    Will orchestrate validation stages in sequence, collecting results
    and producing a ValidationReport for the supervisor's retry logic.
    """

    def validate(self, cell_definition: dict[str, Any], cell_type: str) -> ValidationReport:
        """Run all validation stages on a cell definition.

        Args:
            cell_definition: Raw parsed cell parameters from LLM output.
            cell_type: One of 'pouch', 'prismatic', 'cylindrical'.

        Returns:
            ValidationReport with per-stage results.
        """
        raise NotImplementedError(
            "FormalValidator.validate() - planned for post-migration extraction from supervisor/driver.py"
        )
