"""AXIOM generation routes: raw LLM generation and YAML parsing."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from forge.api.deps import build_backend
from forge.api.schemas.models import (
    GenerateData,
    GenerateRequest,
    GenerateResponse,
    ParseData,
    ParseRequest,
    ParseResponse,
)
from forge.axiom.generator.parser import extract_yaml_block

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
def generate_text(payload: GenerateRequest) -> GenerateResponse:
    """Call an LLM backend and return raw model output."""
    backend = build_backend(payload.backend, model=payload.model)
    messages = [{"role": "user", "content": payload.prompt}]
    if payload.system_prompt:
        messages.insert(0, {"role": "system", "content": payload.system_prompt})

    try:
        raw_yaml = backend.generate(messages)
        model_name = payload.model or str(getattr(backend, "model", payload.backend))
        return GenerateResponse(
            data=GenerateData(raw_yaml=raw_yaml, model=model_name, tokens_used=None)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Generate endpoint failed.")
        raise HTTPException(status_code=502, detail=f"Upstream LLM error: {exc}") from exc


@router.post("/parse", response_model=ParseResponse)
def parse_generated_yaml(payload: ParseRequest) -> ParseResponse:
    """Extract and parse YAML from raw LLM output."""
    try:
        parse_result = extract_yaml_block(payload.raw_yaml)
    except Exception as exc:
        logger.exception("Parse endpoint failed unexpectedly.")
        raise HTTPException(status_code=500, detail=f"Parser failure: {exc}") from exc

    if parse_result.success and isinstance(parse_result.yaml_content, dict):
        return ParseResponse(
            data=ParseData(parsed_spec=parse_result.yaml_content, parse_errors=[])
        )

    errors = [parse_result.error] if parse_result.error else ["Unable to parse YAML response."]
    return ParseResponse(data=ParseData(parsed_spec={}, parse_errors=errors))

