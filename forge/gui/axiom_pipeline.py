"""Tracked AXIOM pipeline execution for the Streamlit GUI."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from forge.axiom.backends import LLMBackend, get_backend
from forge.axiom.generator.parser import extract_yaml_block
from forge.axiom.generator.prompt_builder import build_retry_prompt, build_system_prompt
from forge.engine.calculators.cylindrical_calculator import CylindricalCalculator
from forge.engine.calculators.pouch_calculator import CellCalculator
from forge.engine.calculators.prismatic_calculator import PrismaticCalculator
from forge.engine.conversion import (
    MappingError,
    from_cylindrical_template_format,
    from_pouch_template_format,
    from_template_format,
)
from forge.engine.models.results import CellReport
from forge.engine.validation.constraint_validator import (
    COMMON_CONSTRAINTS,
    CYLINDRICAL_CONSTRAINTS,
    POUCH_CONSTRAINTS,
    PRISMATIC_CONSTRAINTS,
    validate_physics,
)
from forge.engine.validation.schema_validator import (
    ValidationError,
    ValidationResult,
    validate_required_fields,
    validate_structure,
)

FLOW_STEPS = (
    "Build Prompt",
    "LLM Generate",
    "Parse YAML",
    "Schema Validate",
    "Physics Validate",
    "Convert",
    "Calculate",
)
RETRY_STEP = "Retry Feedback"
DEMO_DIR = Path(__file__).resolve().parents[2] / "data" / "demos" / "axiom"


class StepStatus(str, Enum):
    """Status of an AXIOM pipeline step."""

    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """Single observed pipeline step."""

    name: str
    status: StepStatus = StepStatus.PENDING
    detail: str = ""
    raw_data: Any = None
    duration_ms: float = 0.0
    started_at: float = 0.0
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize the step for JSON storage."""
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "raw_data": _serialize_value(self.raw_data),
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "attempt": self.attempt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineStep":
        """Deserialize a step from JSON data."""
        return cls(
            name=data["name"],
            status=StepStatus(data.get("status", StepStatus.PENDING.value)),
            detail=data.get("detail", ""),
            raw_data=data.get("raw_data"),
            duration_ms=float(data.get("duration_ms", 0.0)),
            started_at=float(data.get("started_at", 0.0)),
            attempt=int(data.get("attempt", 1)),
        )


@dataclass
class PipelineRun:
    """Tracked AXIOM pipeline execution."""

    prompt: str
    backend_name: str
    cell_type: str = "prismatic"
    steps: list[PipelineStep] = field(default_factory=list)
    attempt: int = 1
    max_attempts: int = 3
    success: bool = False
    total_duration_ms: float = 0.0
    yaml_content: str | None = None
    calculation_summary: dict[str, Any] | None = None
    last_error: str | None = None
    retry_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the run for recorded demos."""
        return {
            "prompt": self.prompt,
            "backend_name": self.backend_name,
            "cell_type": self.cell_type,
            "steps": [step.to_dict() for step in self.steps],
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "yaml_content": self.yaml_content,
            "calculation_summary": _serialize_value(self.calculation_summary),
            "last_error": self.last_error,
            "retry_reasons": list(self.retry_reasons),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineRun":
        """Deserialize a run from JSON data."""
        return cls(
            prompt=data["prompt"],
            backend_name=data["backend_name"],
            cell_type=data.get("cell_type", "prismatic"),
            steps=[PipelineStep.from_dict(step) for step in data.get("steps", [])],
            attempt=int(data.get("attempt", 1)),
            max_attempts=int(data.get("max_attempts", 3)),
            success=bool(data.get("success", False)),
            total_duration_ms=float(data.get("total_duration_ms", 0.0)),
            yaml_content=data.get("yaml_content"),
            calculation_summary=data.get("calculation_summary"),
            last_error=data.get("last_error"),
            retry_reasons=list(data.get("retry_reasons", [])),
        )

    @property
    def latest_retry_feedback(self) -> PipelineStep | None:
        """Return the latest retry feedback step if present."""
        retry_steps = [step for step in self.steps if step.name == RETRY_STEP]
        return retry_steps[-1] if retry_steps else None


def save_pipeline_run(run: PipelineRun, path: str | Path) -> None:
    """Persist a pipeline run as JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")


def load_pipeline_run(path: str | Path) -> PipelineRun:
    """Load a recorded pipeline run from disk."""
    return PipelineRun.from_dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def load_demo_run(filename: str) -> PipelineRun:
    """Load a demo run from the standard demo directory."""
    return load_pipeline_run(DEMO_DIR / filename)


def run_pipeline_with_tracking(
    prompt: str,
    backend: str | LLMBackend = "ollama",
    api_key: str | None = None,
    max_attempts: int = 3,
    on_step_update: Callable[[PipelineRun], None] | None = None,
    cell_type: str = "prismatic",
    calculate: bool = True,
    **backend_kwargs: Any,
) -> PipelineRun:
    """Run the AXIOM pipeline step by step and emit tracked updates."""
    started = perf_counter()
    normalized_cell_type = _normalize_cell_type(cell_type)
    run = PipelineRun(
        prompt=prompt,
        backend_name=_backend_name(backend),
        cell_type=normalized_cell_type,
        max_attempts=max_attempts,
    )

    def emit() -> None:
        run.total_duration_ms = (perf_counter() - started) * 1000
        if on_step_update is not None:
            on_step_update(run)

    system_step = _start_step(run, "Build Prompt", 1, "Preparing AXIOM system prompt")
    try:
        system_prompt = build_system_prompt(include_example=True, cell_type=normalized_cell_type)
        _finish_step(
            system_step,
            StepStatus.PASSED,
            detail=f"System prompt ready ({len(system_prompt):,} chars)",
            raw_data={
                "cell_type": normalized_cell_type,
                "include_example": True,
                "prompt_chars": len(system_prompt),
            },
        )
    except Exception as exc:  # pragma: no cover - defensive
        run.last_error = f"Prompt construction failed: {exc}"
        _finish_step(system_step, StepStatus.FAILED, detail=run.last_error, raw_data=str(exc))
        emit()
        return run
    emit()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    llm = None
    for attempt in range(1, max_attempts + 1):
        run.attempt = attempt
        if llm is None:
            try:
                llm = _resolve_backend(backend, api_key=api_key, **backend_kwargs)
            except Exception as exc:
                llm_step = _start_step(run, "LLM Generate", attempt, "Initializing backend")
                run.last_error = f"Backend initialization failed: {exc}"
                _finish_step(
                    llm_step,
                    StepStatus.FAILED,
                    detail=run.last_error,
                    raw_data={"error": str(exc), "backend": run.backend_name},
                )
                emit()
                return run

        response_step = _start_step(run, "LLM Generate", attempt, f"Querying {run.backend_name}")
        emit()
        try:
            response = llm.generate(messages)
        except Exception as exc:
            run.last_error = f"Generation failed: {exc}"
            _finish_step(
                response_step,
                StepStatus.FAILED,
                detail=run.last_error,
                raw_data={"error": str(exc), "backend": run.backend_name},
            )
            emit()
            return run

        _finish_step(
            response_step,
            StepStatus.PASSED,
            detail=f"Received {len(response):,} characters",
            raw_data=response,
        )
        emit()

        parse_step = _start_step(run, "Parse YAML", attempt, "Extracting YAML block")
        emit()
        parse_result = extract_yaml_block(response)
        if not parse_result.success:
            run.last_error = f"Parse error: {parse_result.error}"
            _finish_step(
                parse_step,
                StepStatus.FAILED,
                detail=run.last_error,
                raw_data={"error": parse_result.error, "response_excerpt": response[:500]},
            )
            emit()

            retry_prompt = (
                f"Your response could not be parsed: {parse_result.error}\n\n"
                "Please provide a valid YAML cell definition in a ```yaml code block."
            )
            _append_retry_feedback(
                run=run,
                attempt=attempt,
                reason=run.last_error,
                retry_prompt=retry_prompt,
            )
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": retry_prompt})
            emit()
            continue

        run.yaml_content = parse_result.raw_yaml
        _finish_step(
            parse_step,
            StepStatus.PASSED,
            detail=f"YAML extracted ({len(parse_result.raw_yaml.splitlines())} lines)",
            raw_data={"parsed": parse_result.yaml_content, "raw_yaml": parse_result.raw_yaml},
        )
        emit()

        schema_step = _start_step(run, "Schema Validate", attempt, "Checking required fields")
        emit()
        schema_result = _run_schema_validation(parse_result.yaml_content, normalized_cell_type)
        if not schema_result.valid:
            feedback = schema_result.to_llm_feedback()
            run.last_error = f"Schema validation failed: {schema_result.errors[0].message}"
            _finish_step(
                schema_step,
                StepStatus.FAILED,
                detail=_summarize_validation_result(schema_result),
                raw_data=_validation_result_payload(schema_result),
            )
            emit()

            retry_prompt = build_retry_prompt(prompt, feedback, cell_type=normalized_cell_type)
            _append_retry_feedback(
                run=run,
                attempt=attempt,
                reason=feedback,
                retry_prompt=retry_prompt,
            )
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": retry_prompt})
            emit()
            continue

        _finish_step(
            schema_step,
            StepStatus.PASSED,
            detail="Structure valid and required domains present",
            raw_data=_validation_result_payload(schema_result),
        )
        emit()

        physics_step = _start_step(run, "Physics Validate", attempt, "Checking physical constraints")
        emit()
        if _is_template_payload(parse_result.yaml_content):
            _finish_step(
                physics_step,
                StepStatus.SKIPPED,
                detail="Template payload detected, physics guard skipped",
                raw_data={"skipped": True},
            )
            physics_result = ValidationResult(valid=True, errors=[], level="physics")
        else:
            physics_result = validate_physics(parse_result.yaml_content, cell_type=normalized_cell_type)

        if not physics_result.valid:
            feedback = physics_result.to_llm_feedback()
            run.last_error = f"Physics validation failed: {physics_result.errors[0].message}"
            _finish_step(
                physics_step,
                StepStatus.FAILED,
                detail=_summarize_validation_result(physics_result),
                raw_data=_validation_result_payload(physics_result),
            )
            emit()

            retry_prompt = build_retry_prompt(prompt, feedback, cell_type=normalized_cell_type)
            _append_retry_feedback(
                run=run,
                attempt=attempt,
                reason=feedback,
                retry_prompt=retry_prompt,
            )
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": retry_prompt})
            emit()
            continue

        if physics_step.status == StepStatus.ACTIVE:
            _finish_step(
                physics_step,
                StepStatus.PASSED,
                detail=f"{_constraint_count(normalized_cell_type)} constraints passed",
                raw_data=_validation_result_payload(physics_result),
            )
            emit()

        convert_step = _start_step(run, "Convert", attempt, "Mapping YAML into engine dataclass")
        emit()
        try:
            cell_input = _convert_definition(parse_result.yaml_content, normalized_cell_type)
        except (MappingError, Exception) as exc:
            run.last_error = f"Conversion failed: {exc}"
            _finish_step(
                convert_step,
                StepStatus.FAILED,
                detail=run.last_error,
                raw_data={"error": str(exc), "cell_type": normalized_cell_type},
            )
            emit()
            return run

        _finish_step(
            convert_step,
            StepStatus.PASSED,
            detail=f"Created {type(cell_input).__name__}",
            raw_data={"cell_input_type": type(cell_input).__name__},
        )
        emit()

        calculate_step = _start_step(run, "Calculate", attempt, "Running FORGE calculator")
        emit()
        try:
            report = _calculate_cell(cell_input, normalized_cell_type) if calculate else None
        except Exception as exc:
            run.last_error = f"Calculation failed: {exc}"
            _finish_step(
                calculate_step,
                StepStatus.FAILED,
                detail=run.last_error,
                raw_data={"error": str(exc)},
            )
            emit()
            return run

        summary = _report_summary(report) if report is not None else None
        run.calculation_summary = summary
        _finish_step(
            calculate_step,
            StepStatus.PASSED,
            detail=_format_report_detail(report) if report is not None else "Calculation skipped",
            raw_data=summary,
        )
        run.success = True
        emit()
        break

    run.total_duration_ms = (perf_counter() - started) * 1000
    return run


def _normalize_cell_type(cell_type: str) -> str:
    cell_type_lower = cell_type.lower()
    if cell_type_lower not in {"prismatic", "pouch", "cylindrical"}:
        return "prismatic"
    return cell_type_lower


def _backend_name(backend: str | LLMBackend) -> str:
    return backend if isinstance(backend, str) else backend.__class__.__name__


def _resolve_backend(
    backend: str | LLMBackend,
    api_key: str | None = None,
    **backend_kwargs: Any,
) -> LLMBackend:
    if not isinstance(backend, str):
        return backend
    config = dict(backend_kwargs)
    if backend == "claude" and api_key:
        config["api_key"] = api_key
    return get_backend(backend, **config)


def _start_step(run: PipelineRun, name: str, attempt: int, detail: str) -> PipelineStep:
    step = PipelineStep(
        name=name,
        status=StepStatus.ACTIVE,
        detail=detail,
        started_at=perf_counter(),
        attempt=attempt,
    )
    run.steps.append(step)
    return step


def _finish_step(
    step: PipelineStep,
    status: StepStatus,
    detail: str,
    raw_data: Any = None,
) -> None:
    step.status = status
    step.detail = detail
    step.raw_data = raw_data
    step.duration_ms = max((perf_counter() - step.started_at) * 1000, 0.0)


def _append_retry_feedback(
    run: PipelineRun,
    attempt: int,
    reason: str,
    retry_prompt: str,
) -> None:
    run.retry_reasons.append(reason)
    step = _start_step(run, RETRY_STEP, attempt, "Preparing feedback for retry")
    _finish_step(
        step,
        StepStatus.PASSED,
        detail=reason.splitlines()[0][:180],
        raw_data={"feedback": reason, "retry_prompt": retry_prompt},
    )


def _run_schema_validation(cell_dict: dict[str, Any], cell_type: str) -> ValidationResult:
    required_result = validate_required_fields(cell_dict, cell_type)
    if not required_result.valid:
        return required_result
    return validate_structure(cell_dict, cell_type)


def _is_template_payload(cell_dict: dict[str, Any]) -> bool:
    return "_meta" in cell_dict and "default" in str(cell_dict).lower()


def _constraint_count(cell_type: str) -> int:
    if cell_type == "pouch":
        return len(COMMON_CONSTRAINTS) + len(POUCH_CONSTRAINTS)
    if cell_type == "cylindrical":
        return len(COMMON_CONSTRAINTS) + len(CYLINDRICAL_CONSTRAINTS)
    return len(COMMON_CONSTRAINTS) + len(PRISMATIC_CONSTRAINTS)


def _convert_definition(cell_dict: dict[str, Any], cell_type: str) -> Any:
    if cell_type == "pouch":
        return from_pouch_template_format(cell_dict)
    if cell_type == "cylindrical":
        return from_cylindrical_template_format(cell_dict)
    return from_template_format(cell_dict)


def _calculate_cell(cell_input: Any, cell_type: str) -> CellReport:
    if cell_type == "pouch":
        return CellCalculator(cell_input).calculate()
    if cell_type == "cylindrical":
        return CylindricalCalculator(cell_input).calculate()
    return PrismaticCalculator(cell_input).calculate()


def _report_summary(report: CellReport) -> dict[str, Any]:
    return {
        "cell_name": report.cell_name,
        "cell_type": report.cell_type,
        "capacity_ah": report.capacity_ah,
        "energy_wh": report.energy_wh,
        "total_mass_g": report.total_mass_g,
        "gravimetric_ed_whkg": report.gravimetric_ed_whkg,
        "volumetric_ed_cell_whl": report.volumetric_ed_cell_whl,
        "volumetric_ed_stack_whl": report.volumetric_ed_stack_whl,
        "cell_height_mm": report.cell_height_mm,
        "cell_width_mm": report.cell_width_mm,
        "cell_thickness_soc100_mm": report.cell_thickness_soc100_mm,
        "nominal_voltage_v": report.nominal_voltage_v,
    }


def _format_report_detail(report: CellReport) -> str:
    return (
        f"{report.capacity_ah:.1f} Ah | {report.energy_wh:.0f} Wh | "
        f"{report.gravimetric_ed_whkg:.1f} Wh/kg"
    )


def _summarize_validation_result(result: ValidationResult) -> str:
    if result.valid:
        return "Validation passed"
    first = result.errors[0]
    return f"{first.path}: {first.message}"


def _validation_result_payload(result: ValidationResult) -> dict[str, Any]:
    return {
        "level": result.level,
        "valid": result.valid,
        "errors": [_validation_error_payload(error) for error in result.errors],
    }


def _validation_error_payload(error: ValidationError) -> dict[str, Any]:
    return {
        "path": error.path,
        "message": error.message,
        "value": _serialize_value(error.value),
        "constraint": error.constraint,
    }


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _serialize_value(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)
