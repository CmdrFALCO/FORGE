"""Pydantic request/response schemas for FORGE API endpoints."""

from typing import Any, Literal

from pydantic import BaseModel, Field

CellType = Literal["pouch", "prismatic", "cylindrical"]


class ErrorDetail(BaseModel):
    """Structured error payload for API responses."""

    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: Literal[False] = False
    error: ErrorDetail


class HealthData(BaseModel):
    """Payload for health endpoints."""

    status: str
    version: str
    backends_available: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Success envelope for health endpoints."""

    success: Literal[True] = True
    data: HealthData


class ReferenceCellMeta(BaseModel):
    """Reference cell metadata exposed through the API."""

    id: str
    name: str
    cell_type: CellType
    chemistry: str
    tier: str
    source: str
    data: dict[str, Any] | None = None


class ReferenceCellsData(BaseModel):
    """Payload for reference-cell listing endpoint."""

    cells: list[ReferenceCellMeta] = Field(default_factory=list)
    count: int


class ReferenceCellsResponse(BaseModel):
    """Success envelope for reference-cell listing endpoint."""

    success: Literal[True] = True
    data: ReferenceCellsData


class CellSpecRequest(BaseModel):
    """Unified request schema for engine-driven validation/calculation routes."""

    cell_type: CellType
    spec: dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cell_type": "prismatic",
                    "spec": {
                        "_meta": {"cell_type": "prismatic"},
                        "envelope": {"cell_height_mm": 88.8},
                    },
                }
            ]
        }
    }


class ValidationData(BaseModel):
    """Payload for validation results."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    feedback_message: str | None = None


class ValidationResponse(BaseModel):
    """Success envelope for validation endpoint."""

    success: Literal[True] = True
    data: ValidationData


class CalculationData(BaseModel):
    """Payload for calculation results."""

    report: dict[str, Any]
    cell_type: CellType


class CalculationResponse(BaseModel):
    """Success envelope for calculation endpoint."""

    success: Literal[True] = True
    data: CalculationData


class GenerateRequest(BaseModel):
    """Request schema for LLM generation endpoint (implemented in G1-B)."""

    prompt: str
    backend: str = "ollama"
    system_prompt: str | None = None
    model: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Design a 50Ah prismatic NMC cell",
                    "backend": "ollama",
                    "model": "qwen2.5-coder:14b",
                }
            ]
        }
    }


class GenerateData(BaseModel):
    """Payload for LLM generation endpoint (implemented in G1-B)."""

    raw_yaml: str
    model: str
    tokens_used: int | None = None


class GenerateResponse(BaseModel):
    """Success envelope for generation endpoint (implemented in G1-B)."""

    success: Literal[True] = True
    data: GenerateData


class ParseRequest(BaseModel):
    """Request schema for parser endpoint (implemented in G1-B)."""

    raw_yaml: str

    model_config = {
        "json_schema_extra": {"examples": [{"raw_yaml": "geometry:\n  diameter_mm: 21.0"}]}
    }


class ParseData(BaseModel):
    """Payload for parser endpoint (implemented in G1-B)."""

    parsed_spec: dict[str, Any]
    parse_errors: list[str] = Field(default_factory=list)


class ParseResponse(BaseModel):
    """Success envelope for parser endpoint (implemented in G1-B)."""

    success: Literal[True] = True
    data: ParseData


class PipelineRequest(BaseModel):
    """Request schema for full AXIOM pipeline endpoint (implemented in G1-B)."""

    prompt: str
    backend: str = "ollama"
    max_retries: int = Field(default=3, ge=1)
    model: str | None = None
    supervised: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Design a high-energy 21700 cell",
                    "backend": "ollama",
                    "max_retries": 3,
                }
            ]
        }
    }


class ConstraintResultSchema(BaseModel):
    """Per-constraint pass/fail result for experiment logging."""

    constraint_id: str
    name: str
    passed: bool
    actual_value: Any = None
    threshold: Any = None
    message: str = ""
    check_time_ms: float = 0.0


class AttemptRecord(BaseModel):
    """Per-attempt record for pipeline endpoint (implemented in G1-B)."""

    attempt: int
    valid: bool
    errors: list[str] = Field(default_factory=list)
    constraint_results: list[ConstraintResultSchema] = Field(default_factory=list)


class PipelineData(BaseModel):
    """Payload for full AXIOM pipeline endpoint (implemented in G1-B)."""

    result: dict[str, Any] | None
    attempts: list[AttemptRecord] = Field(default_factory=list)
    final_valid: bool
    total_attempts: int


class PipelineResponse(BaseModel):
    """Success envelope for pipeline endpoint (implemented in G1-B)."""

    success: Literal[True] = True
    data: PipelineData
