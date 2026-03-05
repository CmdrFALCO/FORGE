"""Validation routes wrapping the FORGE engine validation pipeline."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from forge.api.schemas.models import CellSpecRequest, ValidationData, ValidationResponse
from forge.engine.validation.pipeline import validate_cell_definition

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
def validate_spec(payload: CellSpecRequest) -> ValidationResponse:
    """Run schema + physics validation for an incoming cell specification."""
    try:
        result = validate_cell_definition(payload.spec, cell_type=payload.cell_type)
        errors = [f"{err.path}: {err.message}" for err in result.errors]
        feedback = result.to_llm_feedback() if not result.valid else None

        return ValidationResponse(
            data=ValidationData(valid=result.valid, errors=errors, feedback_message=feedback)
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Malformed validation request: {exc}") from exc
    except Exception as exc:
        logger.exception("Validation endpoint failed.")
        raise HTTPException(status_code=500, detail=f"Validation failed: {exc}") from exc
