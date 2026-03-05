"""AXIOM supervision pipeline route."""

from __future__ import annotations

import dataclasses
import logging
import threading
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from forge.api.deps import build_backend
from forge.api.schemas.models import (
    AttemptRecord,
    PipelineData,
    PipelineRequest,
    PipelineResponse,
)
from forge.axiom.supervisor import driver as supervisor_driver
from forge.axiom.supervisor.result import GenerationResult

logger = logging.getLogger(__name__)
router = APIRouter()

_retry_lock = threading.Lock()


def _to_jsonable(value: Any) -> Any:
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


def _build_attempt_records(result: GenerationResult) -> list[AttemptRecord]:
    records: list[AttemptRecord] = []

    for attempt_idx, reason in enumerate(result.retry_reasons, start=1):
        records.append(AttemptRecord(attempt=attempt_idx, valid=False, errors=[reason]))

    if result.success:
        records.append(AttemptRecord(attempt=result.attempts, valid=True, errors=[]))
        return records

    if result.attempts > len(records):
        for attempt_idx in range(len(records) + 1, result.attempts + 1):
            error = result.last_error if result.last_error else "Design generation failed."
            records.append(AttemptRecord(attempt=attempt_idx, valid=False, errors=[error]))

    return records


def _extract_pipeline_result(result: GenerationResult) -> dict[str, Any] | None:
    if result.calculation_result is not None:
        return _to_jsonable(result.calculation_result)
    if result.cell_input is not None:
        return _to_jsonable(result.cell_input)
    return None


def _is_infrastructure_failure(result: GenerationResult) -> bool:
    if not result.last_error:
        return False
    return result.last_error.lower().startswith("generation error:")


@contextmanager
def _override_max_retries(max_retries: int):
    with _retry_lock:
        original = supervisor_driver.MAX_RETRIES
        supervisor_driver.MAX_RETRIES = max_retries
        try:
            yield
        finally:
            supervisor_driver.MAX_RETRIES = original


@router.post("/pipeline", response_model=PipelineResponse)
def run_pipeline(payload: PipelineRequest) -> PipelineResponse:
    """Run the full AXIOM loop: generate -> validate -> retry -> calculate."""
    backend = build_backend(payload.backend, model=payload.model)

    try:
        with _override_max_retries(payload.max_retries):
            generation_result = supervisor_driver.generate_cell_design(
                request=payload.prompt,
                backend=backend,
                calculate=True,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Pipeline endpoint infrastructure failure.")
        raise HTTPException(status_code=502, detail=f"Pipeline infrastructure error: {exc}") from exc

    if not generation_result.success and _is_infrastructure_failure(generation_result):
        raise HTTPException(status_code=502, detail=generation_result.last_error)

    attempts = _build_attempt_records(generation_result)
    data = PipelineData(
        result=_extract_pipeline_result(generation_result),
        attempts=attempts,
        final_valid=generation_result.success,
        total_attempts=generation_result.attempts,
    )
    return PipelineResponse(data=data)
