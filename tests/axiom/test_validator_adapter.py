"""Tests for the AXIOM-facing production validation adapter."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from forge.axiom import validator as validator_module
from forge.axiom.validator import FormalValidator
from forge.engine.validation import ValidationResult, validate_cell_definition

TRACE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "demos"
    / "axiom"
    / "openai_build_week_cy5"
    / "trace.json"
)


@pytest.fixture(scope="module")
def canonical_cells() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the canonical invalid and corrected cylindrical definitions."""
    trace = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    invalid = trace["attempts"][0]["validation"]["parsed_yaml"]
    valid = trace["attempts"][1]["validation"]["parsed_yaml"]
    return invalid, valid


def _semantic_result(result: ValidationResult) -> dict[str, Any]:
    """Project deterministic evidence while excluding check runtime telemetry."""
    return {
        "valid": result.valid,
        "level": result.level,
        "errors": [
            (error.path, error.message, error.value, error.constraint)
            for error in result.errors
        ],
        "constraints": [
            (
                constraint.constraint_id,
                constraint.name,
                constraint.passed,
                constraint.actual_value,
                constraint.threshold,
                constraint.message,
            )
            for constraint in result.constraint_results
        ],
        "feedback": result.to_llm_feedback(),
    }


def test_validate_delegates_to_production_pipeline() -> None:
    cell_definition: dict[str, Any] = {"example": True}
    expected = ValidationResult(valid=True, errors=[])
    production_validate = Mock(return_value=expected)

    original = validator_module.validation_pipeline.validate_cell_definition
    validator_module.validation_pipeline.validate_cell_definition = production_validate
    try:
        result = FormalValidator().validate(
            cell_definition,
            cell_type="cylindrical",
            strict=False,
        )
    finally:
        validator_module.validation_pipeline.validate_cell_definition = original

    assert result is expected
    production_validate.assert_called_once_with(
        cell_definition,
        strict=False,
        cell_type="cylindrical",
    )


def test_validate_returns_production_result_for_valid_cell(
    canonical_cells: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, valid_cell = canonical_cells

    adapter_result = FormalValidator().validate(valid_cell, cell_type="cylindrical")
    direct_result = validate_cell_definition(valid_cell, cell_type="cylindrical")

    assert isinstance(adapter_result, ValidationResult)
    assert adapter_result.valid
    assert _semantic_result(adapter_result) == _semantic_result(direct_result)


def test_invalid_result_preserves_constraint_evidence_and_feedback(
    canonical_cells: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    invalid_cell, _ = canonical_cells

    adapter_result = FormalValidator().validate(invalid_cell, cell_type="cylindrical")
    direct_result = validate_cell_definition(invalid_cell, cell_type="cylindrical")
    failed_ids = [
        constraint.constraint_id
        for constraint in adapter_result.constraint_results
        if not constraint.passed
    ]

    assert not adapter_result.valid
    assert failed_ids == ["CY5"]
    assert adapter_result.errors
    assert adapter_result.to_llm_feedback() == direct_result.to_llm_feedback()
    assert _semantic_result(adapter_result) == _semantic_result(direct_result)


def test_validate_does_not_modify_input(
    canonical_cells: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, valid_cell = canonical_cells
    cell_definition = deepcopy(valid_cell)
    original = deepcopy(cell_definition)

    FormalValidator().validate(cell_definition, cell_type="cylindrical")

    assert cell_definition == original


def test_unsupported_cell_type_matches_production_pipeline(
    canonical_cells: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, valid_cell = canonical_cells

    adapter_result = FormalValidator().validate(valid_cell, cell_type="unsupported")
    direct_result = validate_cell_definition(valid_cell, cell_type="unsupported")

    assert _semantic_result(adapter_result) == _semantic_result(direct_result)
