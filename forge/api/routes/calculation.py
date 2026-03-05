"""Calculation routes wrapping FORGE engine calculators."""

from __future__ import annotations

import dataclasses
import logging
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from forge.api.schemas.models import CalculationData, CalculationResponse, CellSpecRequest
from forge.engine.calculators.cylindrical_calculator import CylindricalCalculator
from forge.engine.calculators.pouch_calculator import CellCalculator
from forge.engine.calculators.prismatic_calculator import PrismaticCalculator
from forge.engine.conversion.exceptions import MappingError, MissingFieldError
from forge.engine.conversion.template_to_input import (
    from_cylindrical_template_format,
    from_pouch_template_format,
    from_template_format,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_jsonable(value: Any) -> Any:
    """Convert calculation outputs into JSON-serializable primitives."""
    if dataclasses.is_dataclass(value):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    return value


def _calculate_pouch(spec: dict[str, Any]) -> dict[str, Any]:
    cell_input = from_pouch_template_format(spec)
    report = CellCalculator().calculate_pouch_cell(cell_input)
    return _to_jsonable(report)


def _calculate_prismatic(spec: dict[str, Any]) -> dict[str, Any]:
    cell_input = from_template_format(spec)
    report = PrismaticCalculator(cell_input).calculate()
    return _to_jsonable(report)


def _calculate_cylindrical(spec: dict[str, Any]) -> dict[str, Any]:
    cell_input = from_cylindrical_template_format(spec)
    report = CylindricalCalculator(cell_input).calculate()
    return _to_jsonable(report)


@router.post("/calculate", response_model=CalculationResponse)
def calculate_spec(payload: CellSpecRequest) -> CalculationResponse:
    """Run calculator dispatch for a validated cell specification."""
    try:
        if payload.cell_type == "pouch":
            report = _calculate_pouch(payload.spec)
        elif payload.cell_type == "prismatic":
            report = _calculate_prismatic(payload.spec)
        else:
            report = _calculate_cylindrical(payload.spec)

        return CalculationResponse(
            data=CalculationData(report=report, cell_type=payload.cell_type)
        )
    except (MappingError, MissingFieldError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Calculation input error: {exc}") from exc
    except Exception as exc:
        logger.exception("Calculation endpoint failed.")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {exc}") from exc
