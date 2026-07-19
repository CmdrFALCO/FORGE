"""Integrity-checked projection of the OpenAI Build Week AXIOM replay."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge.gui.axiom_pipeline import (
    DEMO_DIR,
    RETRY_STEP,
    PipelineRun,
    PipelineStep,
    StepStatus,
)

VERIFIED_REPLAY_DIR = DEMO_DIR / "openai_build_week_cy5"
REPLAY_FILES = ("trace.json", "manifest.json", "BUNDLE_SHA256.txt")


class VerifiedReplayError(ValueError):
    """Raised when a verified replay bundle is incomplete or inconsistent."""


@dataclass(frozen=True)
class VerifiedReplay:
    """Validated replay data and its projection into the GUI pipeline model."""

    directory: Path
    trace: dict[str, Any]
    manifest: dict[str, Any]
    bundle_sha256: str
    pipeline_run: PipelineRun

    @property
    def attempts(self) -> list[dict[str, Any]]:
        """Return the captured attempts in their authenticated order."""
        return self.trace["attempts"]

    @property
    def retry_feedback(self) -> str:
        """Return the exact validator feedback sent before the correction."""
        return self.pipeline_run.retry_reasons[0]


def load_verified_replay(directory: str | Path = VERIFIED_REPLAY_DIR) -> VerifiedReplay:
    """Load, validate, and project the canonical Build Week replay bundle."""
    root = Path(directory)
    missing = [name for name in REPLAY_FILES if not (root / name).is_file()]
    if missing:
        raise VerifiedReplayError(f"Incomplete replay bundle; missing: {', '.join(missing)}")

    trace_text = (root / "trace.json").read_text(encoding="utf-8-sig")
    manifest_text = (root / "manifest.json").read_text(encoding="utf-8-sig")
    bundle_sha256 = (root / "BUNDLE_SHA256.txt").read_text(encoding="utf-8-sig").strip()

    try:
        trace = json.loads(trace_text)
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        raise VerifiedReplayError("Replay bundle contains invalid JSON.") from exc
    if not isinstance(trace, dict) or not isinstance(manifest, dict):
        raise VerifiedReplayError("Replay trace and manifest must be JSON objects.")

    _verify_outer_integrity(trace_text, manifest_text, bundle_sha256, manifest)
    _verify_manifest(trace, manifest)
    _verify_trace(trace)

    return VerifiedReplay(
        directory=root,
        trace=trace,
        manifest=manifest,
        bundle_sha256=bundle_sha256,
        pipeline_run=_project_pipeline_run(trace, manifest),
    )


def build_audit_archive(replay: VerifiedReplay) -> bytes:
    """Return a deterministic ZIP containing the complete verified bundle."""
    current = load_verified_replay(replay.directory)
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in REPLAY_FILES:
            content = (current.directory / name).read_text(encoding="utf-8-sig")
            info = zipfile.ZipInfo(name, date_time=(2026, 7, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content.encode("utf-8"))
    return archive_buffer.getvalue()


def _verify_outer_integrity(
    trace_text: str,
    manifest_text: str,
    bundle_sha256: str,
    manifest: dict[str, Any],
) -> None:
    expected_trace_sha = manifest.get("trace_sha256")
    if expected_trace_sha != _sha256_text(trace_text):
        raise VerifiedReplayError("Trace hash does not match the manifest.")
    if bundle_sha256 != _sha256_text(trace_text + manifest_text):
        raise VerifiedReplayError("Bundle hash does not match the trace and manifest.")


def _verify_manifest(trace: dict[str, Any], manifest: dict[str, Any]) -> None:
    attempts = _attempts(trace)
    candidate = _mapping(trace.get("candidate"), "candidate")
    first_messages = _messages(attempts[0], 1)
    system_prompt = next(
        (
            message["content"]
            for message in first_messages
            if message.get("role") == "system"
        ),
        None,
    )
    if not isinstance(system_prompt, str):
        raise VerifiedReplayError("First attempt is missing its system prompt.")

    expected = {
        "schema_version": trace.get("schema_version"),
        "run_id": trace.get("run_id"),
        "git": trace.get("git"),
        "prompt_id": candidate.get("id"),
        "prompt_sha256": _sha256_text(_string(candidate.get("prompt"), "candidate prompt")),
        "system_prompt_sha256": _sha256_text(system_prompt),
        "requested_model": candidate.get("requested_model"),
        "returned_models": sorted(
            {
                _mapping(attempt.get("usage"), "attempt usage").get("model")
                for attempt in attempts
                if _mapping(attempt.get("usage"), "attempt usage").get("model")
            }
        ),
        "attempt_count": len(attempts),
        "latest_classification": trace.get("latest_classification"),
        "latest_failed_constraint_ids": trace.get("latest_failed_constraint_ids"),
        "tokens_in": sum(
            int(_mapping(attempt.get("usage"), "attempt usage").get("tokens_in", 0))
            for attempt in attempts
        ),
        "tokens_out": sum(
            int(_mapping(attempt.get("usage"), "attempt usage").get("tokens_out", 0))
            for attempt in attempts
        ),
        "redaction_check": "passed",
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise VerifiedReplayError(
            f"Manifest does not describe the replay trace: {', '.join(mismatches)}"
        )


def _verify_trace(trace: dict[str, Any]) -> None:
    attempts = _attempts(trace)
    candidate = _mapping(trace.get("candidate"), "candidate")
    promotion = _mapping(trace.get("promotion"), "promotion")
    derived = _mapping(trace.get("derived_calculation"), "derived calculation")

    if trace.get("schema_version") != 1:
        raise VerifiedReplayError("Unsupported replay schema version.")
    if trace.get("source") != "live_gpt56":
        raise VerifiedReplayError("Replay is not marked as an authentic GPT-5.6 capture.")
    if candidate.get("id") != "P4" or candidate.get("cell_type") != "cylindrical":
        raise VerifiedReplayError("Replay is not the reviewed P4 cylindrical scenario.")
    if candidate.get("target_constraints") != ["CY5"]:
        raise VerifiedReplayError("Replay does not target the reviewed CY5 constraint.")
    if len(attempts) != 2 or [attempt.get("attempt") for attempt in attempts] != [1, 2]:
        raise VerifiedReplayError("Replay must contain exactly two ordered attempts.")
    if promotion.get("mode") != "verified_replay":
        raise VerifiedReplayError("Trace has not been promoted as a verified replay.")
    if promotion.get("source_run_id") != trace.get("run_id"):
        raise VerifiedReplayError("Promotion source run does not match the trace run.")
    if trace.get("latest_classification") != "accepted":
        raise VerifiedReplayError("Replay does not end in an accepted design.")
    if trace.get("latest_failed_constraint_ids") != []:
        raise VerifiedReplayError("Accepted replay still reports failed constraints.")
    if _contains_key(trace, "response_id"):
        raise VerifiedReplayError("Replay contains a response identifier.")

    for number, attempt in enumerate(attempts, start=1):
        messages = _messages(attempt, number)
        output_text = _string(attempt.get("output_text"), f"attempt {number} output")
        if attempt.get("source") != "live_gpt56":
            raise VerifiedReplayError(f"Attempt {number} is not marked as a live capture.")
        if attempt.get("message_sha256") != _sha256_text(_canonical_json(messages)):
            raise VerifiedReplayError(f"Attempt {number} message hash does not match.")
        if attempt.get("output_sha256") != _sha256_text(output_text):
            raise VerifiedReplayError(f"Attempt {number} output hash does not match.")
        usage = _mapping(attempt.get("usage"), f"attempt {number} usage")
        returned_model = usage.get("model")
        requested_model = candidate.get("requested_model")
        if not isinstance(returned_model, str) or not returned_model.startswith(
            f"{requested_model}"
        ):
            raise VerifiedReplayError(f"Attempt {number} returned unexpected model telemetry.")
        if int(usage.get("tokens_in", 0)) <= 0 or int(usage.get("tokens_out", 0)) <= 0:
            raise VerifiedReplayError(f"Attempt {number} is missing token telemetry.")

    first_validation = _mapping(attempts[0].get("validation"), "attempt 1 validation")
    second_validation = _mapping(attempts[1].get("validation"), "attempt 2 validation")
    if first_validation.get("classification") != "engineering":
        raise VerifiedReplayError("Attempt 1 is not an engineering rejection.")
    if first_validation.get("failed_constraint_ids") != ["CY5"]:
        raise VerifiedReplayError("Attempt 1 does not isolate the CY5 failure.")
    if second_validation.get("classification") != "accepted":
        raise VerifiedReplayError("Attempt 2 is not accepted.")
    if second_validation.get("failed_constraint_ids") != []:
        raise VerifiedReplayError("Attempt 2 still contains failed constraints.")
    if any(
        _mapping(attempt.get("validation"), "attempt validation").get("parse_error")
        or _mapping(attempt.get("validation"), "attempt validation").get("schema_errors")
        for attempt in attempts
    ):
        raise VerifiedReplayError("Replay attempts must be schema-valid engineering evidence.")

    feedback = _retry_feedback(attempts)
    second_messages = _messages(attempts[1], 2)
    if len(second_messages) != 4:
        raise VerifiedReplayError("Corrected attempt does not contain the complete retry history.")
    if second_messages[:2] != _messages(attempts[0], 1):
        raise VerifiedReplayError("Corrected attempt does not preserve the original request.")
    if second_messages[2] != {
        "role": "assistant",
        "content": attempts[0]["output_text"],
    }:
        raise VerifiedReplayError("Corrected attempt does not preserve the rejected output.")
    if second_messages[3].get("role") != "user" or feedback not in second_messages[3].get(
        "content", ""
    ):
        raise VerifiedReplayError("Corrected attempt does not contain the exact CY5 feedback.")

    required_metrics = {
        "capacity_ah",
        "energy_wh",
        "total_mass_g",
        "gravimetric_ed_whkg",
        "volumetric_ed_cell_whl",
    }
    if derived.get("source") != "deterministic_recalculation" or derived.get("attempt") != 2:
        raise VerifiedReplayError("Derived result is not tied to deterministic attempt 2 output.")
    if any(not isinstance(derived.get(key), (int, float)) for key in required_metrics):
        raise VerifiedReplayError("Derived result is missing required numeric metrics.")


def _project_pipeline_run(trace: dict[str, Any], manifest: dict[str, Any]) -> PipelineRun:
    attempts = _attempts(trace)
    candidate = _mapping(trace["candidate"], "candidate")
    derived = _mapping(trace["derived_calculation"], "derived calculation")
    feedback = _retry_feedback(attempts)
    steps = [
        PipelineStep(
            name="Build Prompt",
            status=StepStatus.PASSED,
            detail="Authenticated P4 prompt and AXIOM system prompt",
            raw_data={
                "prompt_sha256": manifest["prompt_sha256"],
                "system_prompt_sha256": manifest["system_prompt_sha256"],
            },
            attempt=1,
        )
    ]

    for index, attempt in enumerate(attempts):
        number = int(attempt["attempt"])
        validation = _mapping(attempt["validation"], f"attempt {number} validation")
        parsed_yaml = _mapping(validation.get("parsed_yaml"), f"attempt {number} parsed YAML")
        failed_ids = validation.get("failed_constraint_ids", [])
        constraints = validation.get("constraint_results", [])
        steps.extend(
            [
                PipelineStep(
                    name="LLM Generate",
                    status=StepStatus.PASSED,
                    detail=f"Authenticated {attempt['usage']['model']} output",
                    raw_data={
                        "output_text": attempt["output_text"],
                        "output_sha256": attempt["output_sha256"],
                        "usage": attempt["usage"],
                    },
                    attempt=number,
                ),
                PipelineStep(
                    name="Parse YAML",
                    status=StepStatus.PASSED,
                    detail=f"Captured YAML parsed ({len(validation['raw_yaml'].splitlines())} lines)",
                    raw_data={"parsed": parsed_yaml, "raw_yaml": validation["raw_yaml"]},
                    attempt=number,
                ),
                PipelineStep(
                    name="Schema Validate",
                    status=StepStatus.PASSED,
                    detail="Structure valid and required domains present",
                    raw_data={"level": "schema", "valid": True, "errors": []},
                    attempt=number,
                ),
                PipelineStep(
                    name="Physics Validate",
                    status=StepStatus.FAILED if failed_ids else StepStatus.PASSED,
                    detail=_physics_detail(constraints, failed_ids),
                    raw_data={
                        "level": "physics",
                        "valid": not failed_ids,
                        "constraint_results": constraints,
                        "failed_constraint_ids": failed_ids,
                    },
                    attempt=number,
                ),
            ]
        )
        if index == 0:
            steps.append(
                PipelineStep(
                    name=RETRY_STEP,
                    status=StepStatus.PASSED,
                    detail="CY5 feedback returned for correction",
                    raw_data={
                        "feedback": feedback,
                        "retry_prompt": _messages(attempts[1], 2)[-1]["content"],
                    },
                    attempt=number,
                )
            )

    steps.extend(
        [
            PipelineStep(
                name="Convert",
                status=StepStatus.PASSED,
                detail="Accepted cylindrical definition captured",
                raw_data={"cell_input_type": "CylindricalCellInput"},
                attempt=2,
            ),
            PipelineStep(
                name="Calculate",
                status=StepStatus.PASSED,
                detail=(
                    f"{derived['capacity_ah']:.3f} Ah | {derived['energy_wh']:.3f} Wh | "
                    f"{derived['gravimetric_ed_whkg']:.1f} Wh/kg"
                ),
                raw_data=dict(derived),
                attempt=2,
            ),
        ]
    )

    return PipelineRun(
        prompt=_string(candidate["prompt"], "candidate prompt"),
        backend_name=f"OpenAI {candidate['requested_model']} | Verified Replay",
        cell_type="cylindrical",
        steps=steps,
        attempt=2,
        max_attempts=2,
        success=True,
        total_duration_ms=0.0,
        yaml_content=attempts[-1]["validation"]["raw_yaml"],
        calculation_summary={key: value for key, value in derived.items() if key != "source"},
        last_error=None,
        retry_reasons=[feedback],
    )


def _physics_detail(constraints: Any, failed_ids: Any) -> str:
    if not isinstance(constraints, list):
        raise VerifiedReplayError("Constraint results must be a list.")
    if not failed_ids:
        return f"{len(constraints)} captured constraints passed"
    failure = next(
        (
            item
            for item in constraints
            if isinstance(item, dict) and item.get("constraint_id") == failed_ids[0]
        ),
        None,
    )
    if not isinstance(failure, dict):
        raise VerifiedReplayError("Failed constraint has no captured result.")
    return f"{failure['constraint_id']}: {failure['message']}"


def _retry_feedback(attempts: list[dict[str, Any]]) -> str:
    first_supervisor = _mapping(attempts[0].get("supervisor"), "attempt 1 supervisor")
    final_supervisor = _mapping(attempts[-1].get("supervisor"), "final supervisor")
    first_reasons = first_supervisor.get("retry_reasons")
    final_reasons = final_supervisor.get("retry_reasons")
    if (
        not isinstance(first_reasons, list)
        or len(first_reasons) != 1
        or not isinstance(first_reasons[0], str)
        or final_reasons != first_reasons
    ):
        raise VerifiedReplayError("Replay does not preserve one consistent retry reason.")
    return first_reasons[0]


def _attempts(trace: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = trace.get("attempts")
    if not isinstance(attempts, list) or not attempts or not all(
        isinstance(attempt, dict) for attempt in attempts
    ):
        raise VerifiedReplayError("Replay must contain captured attempt objects.")
    return attempts


def _messages(attempt: dict[str, Any], number: int) -> list[dict[str, str]]:
    messages = attempt.get("messages")
    if not isinstance(messages, list) or not all(
        isinstance(message, dict)
        and isinstance(message.get("role"), str)
        and isinstance(message.get("content"), str)
        for message in messages
    ):
        raise VerifiedReplayError(f"Attempt {number} contains invalid messages.")
    return messages


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerifiedReplayError(f"Replay {label} must be an object.")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise VerifiedReplayError(f"Replay {label} must be a non-empty string.")
    return value


def _contains_key(value: Any, forbidden: str) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() == forbidden or _contains_key(child, forbidden)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_key(child, forbidden) for child in value)
    return False


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
