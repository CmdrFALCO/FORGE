"""Bounded GPT-5.6 failure discovery with local replay and trace quarantine.

Each live command permits exactly one delegated OpenAI generation. Earlier
attempts are replayed locally through the unchanged AXIOM supervisor so retry
feedback and message history are rebuilt by production code.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from forge.axiom.backends.backends import LLMUsage, OpenAIBackend  # noqa: E402
from forge.axiom.generator.parser import extract_yaml_block  # noqa: E402
from forge.axiom.supervisor import driver as supervisor_driver  # noqa: E402
from forge.engine.calculators.cylindrical_calculator import CylindricalCalculator  # noqa: E402
from forge.engine.calculators.pouch_calculator import CellCalculator  # noqa: E402
from forge.engine.calculators.prismatic_calculator import PrismaticCalculator  # noqa: E402
from forge.engine.conversion import (  # noqa: E402
    from_cylindrical_template_format,
    from_pouch_template_format,
    from_template_format,
)
from forge.engine.validation.constraint_validator import validate_physics  # noqa: E402
from forge.engine.validation.schema_validator import (  # noqa: E402
    ValidationError,
    validate_required_fields,
    validate_structure,
)

PROMPTS_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "axiom"
    / "prompts"
    / "openai_build_week_candidates.json"
)
STAGING_ROOT = PROJECT_ROOT / "experiments" / "axiom" / "runs" / "_staging"
VERIFIED_REPLAY_ROOT = PROJECT_ROOT / "data" / "demos" / "axiom"
EXPECTED_BRANCH = "build-week/openai"
LIVE_CONFIRMATION = "SEND_FORGE_PROMPT_TO_OPENAI"
MAX_DISCOVERY_CALLS = 5
MAX_CORRECTION_CALLS = 1
MAX_TOTAL_CALLS = 6
TRACE_SCHEMA_VERSION = 1
SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
FORBIDDEN_KEY_PARTS = {
    "api_key",
    "authorization",
    "headers",
    "raw_response",
    "client_state",
    "organization_id",
    "project_id",
}


class DiscoveryError(RuntimeError):
    """Base error for a refused or invalid discovery operation."""


class TraceIntegrityError(DiscoveryError):
    """Raised when replay input differs from the original captured input."""


class BudgetError(DiscoveryError):
    """Raised when a request would exceed the approved discovery budget."""


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically for hashing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    """Return a lowercase SHA-256 digest for text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def load_candidates(path: Path = PROMPTS_PATH) -> dict[str, dict[str, Any]]:
    """Load and validate the reviewed candidate prompt registry."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1:
        raise DiscoveryError("Unsupported candidate prompt schema version.")
    requested_model = payload.get("requested_model")
    if not isinstance(requested_model, str) or not requested_model:
        raise DiscoveryError("Candidate registry is missing requested_model.")

    candidates: dict[str, dict[str, Any]] = {}
    for item in payload.get("candidates", []):
        candidate_id = item.get("id")
        if not isinstance(candidate_id, str) or candidate_id in candidates:
            raise DiscoveryError("Candidate IDs must be unique non-empty strings.")
        if item.get("cell_type") not in {"prismatic", "cylindrical", "pouch"}:
            raise DiscoveryError(f"Candidate {candidate_id} has an unsupported cell type.")
        if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
            raise DiscoveryError(f"Candidate {candidate_id} has an empty prompt.")
        candidates[candidate_id] = {**item, "requested_model": requested_model}
    if not candidates:
        raise DiscoveryError("Candidate registry contains no prompts.")
    return candidates


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git_state() -> dict[str, Any]:
    """Resolve the repository identity required for a live run."""
    return {
        "branch": _run_git("branch", "--show-current"),
        "head": _run_git("rev-parse", "HEAD"),
        "clean": not bool(_run_git("status", "--short")),
    }


def require_live_preflight(expected_head: str | None = None) -> dict[str, Any]:
    """Reject live execution outside the reviewed clean checkpoint."""
    state = git_state()
    if state["branch"] != EXPECTED_BRANCH:
        raise DiscoveryError(f"Live discovery requires branch {EXPECTED_BRANCH}.")
    if not state["clean"]:
        raise DiscoveryError("Live discovery requires a clean working tree.")
    if expected_head is not None and state["head"] != expected_head:
        raise TraceIntegrityError("Current Git HEAD differs from the trace checkpoint.")
    if not os.environ.get("OPENAI_API_KEY"):
        raise DiscoveryError("OPENAI_API_KEY is not available in the process environment.")
    return state


def _scalar_or_none(value: Any) -> str | int | float | bool | None:
    return value if isinstance(value, (str, int, float, bool)) or value is None else None


def _validation_error_payload(error: ValidationError) -> dict[str, Any]:
    return {
        "path": error.path,
        "message": error.message,
        "value": _scalar_or_none(error.value),
        "constraint": error.constraint,
    }


def classify_output(output_text: str, cell_type: str) -> dict[str, Any]:
    """Classify one visible model output without invoking a model."""
    parse_result = extract_yaml_block(output_text)
    if not parse_result.success:
        return {
            "classification": "parse",
            "parse_error": parse_result.error,
            "raw_yaml": parse_result.raw_yaml,
            "parsed_yaml": None,
            "schema_errors": [],
            "constraint_results": [],
            "failed_constraint_ids": [],
        }

    assert parse_result.yaml_content is not None
    required_result = validate_required_fields(parse_result.yaml_content, cell_type)
    schema_result = (
        required_result
        if not required_result.valid
        else validate_structure(parse_result.yaml_content, cell_type)
    )
    if not schema_result.valid:
        return {
            "classification": "schema",
            "parse_error": None,
            "raw_yaml": parse_result.raw_yaml,
            "parsed_yaml": parse_result.yaml_content,
            "schema_errors": [_validation_error_payload(error) for error in schema_result.errors],
            "constraint_results": [],
            "failed_constraint_ids": [],
        }

    physics_result = validate_physics(parse_result.yaml_content, cell_type)
    constraint_results = [dataclasses.asdict(result) for result in physics_result.constraint_results]
    failed_ids = [
        result.constraint_id for result in physics_result.constraint_results if not result.passed
    ]
    return {
        "classification": "accepted" if physics_result.valid else "engineering",
        "parse_error": None,
        "raw_yaml": parse_result.raw_yaml,
        "parsed_yaml": parse_result.yaml_content,
        "schema_errors": [],
        "constraint_results": constraint_results,
        "failed_constraint_ids": failed_ids,
    }


def _usage_payload(backend: Any) -> dict[str, Any]:
    usage = getattr(backend, "last_usage", None)
    raw_response = getattr(usage, "raw_response", None)
    response_id = getattr(raw_response, "id", None)
    payload = {
        "tokens_in": int(getattr(usage, "tokens_in", 0) or 0),
        "tokens_out": int(getattr(usage, "tokens_out", 0) or 0),
        "model": str(getattr(usage, "model", "") or ""),
        "response_id": response_id if isinstance(response_id, str) else None,
    }
    if usage is not None and hasattr(usage, "raw_response"):
        usage.raw_response = None
    return payload


class ReplayThenLiveBackend:
    """Replay prior outputs, then permit exactly one delegated generation."""

    def __init__(
        self,
        live_backend: Any,
        replay_attempts: list[dict[str, Any]],
        before_live_call: Callable[[], Any] | None = None,
    ) -> None:
        self.live_backend = live_backend
        self.replay_attempts = replay_attempts
        self.before_live_call = before_live_call
        self.call_index = 0
        self.live_calls = 0
        self.reservation: Any = None
        self.live_record: dict[str, Any] | None = None
        self.fatal_error: DiscoveryError | None = None
        self.last_usage = LLMUsage()

    def generate(self, messages: list[dict[str, str]]) -> str:
        message_payload = [dict(message) for message in messages]
        message_hash = sha256_text(canonical_json(message_payload))

        if self.call_index < len(self.replay_attempts):
            prior = self.replay_attempts[self.call_index]
            if prior.get("message_sha256") != message_hash:
                self.fatal_error = TraceIntegrityError(
                    f"Replay message hash mismatch at attempt {self.call_index + 1}."
                )
                raise self.fatal_error
            output_text = prior.get("output_text")
            if not isinstance(output_text, str):
                self.fatal_error = TraceIntegrityError(
                    "Replay attempt is missing visible output text."
                )
                raise self.fatal_error
            if prior.get("output_sha256") != sha256_text(output_text):
                self.fatal_error = TraceIntegrityError(
                    f"Replay output hash mismatch at attempt {self.call_index + 1}."
                )
                raise self.fatal_error
            self.call_index += 1
            return output_text

        if self.live_calls >= 1:
            raise BudgetError("One runner invocation may delegate only one live generation.")
        if self.before_live_call is not None:
            self.reservation = self.before_live_call()

        output_text = self.live_backend.generate(message_payload)
        usage = _usage_payload(self.live_backend)
        self.last_usage = LLMUsage(
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
            model=usage["model"],
            raw_response=None,
        )
        self.live_record = {
            "attempt": self.call_index + 1,
            "captured_utc": utc_now(),
            "source": "live_gpt56",
            "messages": message_payload,
            "message_sha256": message_hash,
            "output_text": output_text,
            "output_sha256": sha256_text(output_text),
            "usage": usage,
        }
        self.live_calls += 1
        self.call_index += 1
        return output_text


@contextmanager
def _attempt_limit(max_attempts: int):
    original = supervisor_driver.MAX_RETRIES
    supervisor_driver.MAX_RETRIES = max_attempts
    try:
        yield
    finally:
        supervisor_driver.MAX_RETRIES = original


def execute_one_attempt(
    trace: dict[str, Any],
    live_backend: Any,
    before_live_call: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Replay a trace and append exactly one newly delegated attempt."""
    attempts = trace.setdefault("attempts", [])
    candidate = trace["candidate"]
    wrapper = ReplayThenLiveBackend(live_backend, attempts, before_live_call)
    previous_logging_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with _attempt_limit(len(attempts) + 1):
            result = supervisor_driver.generate_cell_design(
                request=candidate["prompt"],
                backend=wrapper,
                calculate=True,
                cell_type=candidate["cell_type"],
            )
    finally:
        logging.disable(previous_logging_disable)

    if wrapper.fatal_error is not None:
        raise wrapper.fatal_error
    if wrapper.live_calls != 1 or wrapper.live_record is None:
        raise TraceIntegrityError("Supervisor completed without exactly one new live generation.")

    record = wrapper.live_record
    validation = classify_output(record["output_text"], candidate["cell_type"])
    if validation["classification"] == "accepted" and (
        not result.success or result.calculation_result is None
    ):
        validation["classification"] = "conversion_calculation"
    record["validation"] = validation
    record["supervisor"] = {
        "success": result.success,
        "attempts": result.attempts,
        "last_error": result.last_error,
        "retry_reasons": list(result.retry_reasons),
    }
    attempts.append(record)
    trace["updated_utc"] = utc_now()
    trace["latest_classification"] = validation["classification"]
    trace["latest_failed_constraint_ids"] = validation["failed_constraint_ids"]
    return trace


def _read_ledger() -> dict[str, Any]:
    path = STAGING_ROOT / "discovery_ledger.json"
    if not path.exists():
        return {"schema_version": 1, "entries": []}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def reserve_call(kind: str, run_id: str, prompt_id: str, attempt: int) -> int:
    """Reserve one request before network execution, counting failures conservatively."""
    if kind not in {"discovery", "correction"}:
        raise ValueError(f"Unknown call kind: {kind}")
    ledger = _read_ledger()
    entries = ledger.setdefault("entries", [])
    if len(entries) >= MAX_TOTAL_CALLS:
        raise BudgetError(f"The {MAX_TOTAL_CALLS}-request discovery budget is exhausted.")
    kind_limit = MAX_DISCOVERY_CALLS if kind == "discovery" else MAX_CORRECTION_CALLS
    if sum(entry.get("kind") == kind for entry in entries) >= kind_limit:
        raise BudgetError(f"The {kind} request budget is exhausted.")
    if kind == "discovery" and any(entry.get("kind") == "correction" for entry in entries):
        raise BudgetError("Discovery is closed after a correction request begins.")
    if kind == "discovery" and any(
        entry.get("kind") == "discovery" and entry.get("prompt_id") == prompt_id
        for entry in entries
    ):
        raise BudgetError(f"Candidate {prompt_id} already consumed its discovery request.")

    reservation = {
        "index": len(entries) + 1,
        "reserved_utc": utc_now(),
        "kind": kind,
        "run_id": run_id,
        "prompt_id": prompt_id,
        "attempt": attempt,
        "status": "reserved",
    }
    entries.append(reservation)
    _atomic_write_json(STAGING_ROOT / "discovery_ledger.json", ledger)
    return reservation["index"]


def mark_reservation(index: int | None, status: str) -> None:
    if index is None:
        return
    ledger = _read_ledger()
    for entry in ledger.get("entries", []):
        if entry.get("index") == index:
            entry["status"] = status
            entry["finished_utc"] = utc_now()
            _atomic_write_json(STAGING_ROOT / "discovery_ledger.json", ledger)
            return
    raise TraceIntegrityError("Request reservation is missing from the local ledger.")


def _assert_redacted(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise TraceIntegrityError(f"Forbidden trace field at {path}.{key}.")
            _assert_redacted(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _assert_redacted(child, f"{path}[{index}]")
        return
    if isinstance(value, str):
        if SECRET_PATTERN.search(value) or "authorization: bearer " in value.lower():
            raise TraceIntegrityError(f"Secret-like value detected at {path}.")


def _manifest_for(trace: dict[str, Any], trace_sha256: str) -> dict[str, Any]:
    attempts = trace.get("attempts", [])
    first_messages = attempts[0].get("messages", []) if attempts else []
    system_prompt = next(
        (
            message.get("content", "")
            for message in first_messages
            if message.get("role") == "system"
        ),
        "",
    )
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "run_id": trace["run_id"],
        "created_utc": trace["created_utc"],
        "updated_utc": trace.get("updated_utc"),
        "git": trace["git"],
        "prompt_id": trace["candidate"]["id"],
        "prompt_sha256": sha256_text(trace["candidate"]["prompt"]),
        "system_prompt_sha256": sha256_text(system_prompt) if system_prompt else None,
        "requested_model": trace["candidate"]["requested_model"],
        "returned_models": sorted(
            {
                attempt.get("usage", {}).get("model")
                for attempt in attempts
                if attempt.get("usage", {}).get("model")
            }
        ),
        "attempt_count": len(attempts),
        "latest_classification": trace.get("latest_classification"),
        "latest_failed_constraint_ids": trace.get("latest_failed_constraint_ids", []),
        "tokens_in": sum(attempt.get("usage", {}).get("tokens_in", 0) for attempt in attempts),
        "tokens_out": sum(attempt.get("usage", {}).get("tokens_out", 0) for attempt in attempts),
        "trace_sha256": trace_sha256,
        "redaction_check": "passed",
    }


def write_bundle(run_dir: Path, trace: dict[str, Any]) -> None:
    """Write an allowlisted trace, manifest, and bundle digest atomically."""
    _assert_redacted(trace)
    trace_text = json.dumps(trace, indent=2, ensure_ascii=False) + "\n"
    trace_sha256 = sha256_text(trace_text)
    manifest = _manifest_for(trace, trace_sha256)
    _assert_redacted(manifest)
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    bundle_sha256 = sha256_text(trace_text + manifest_text)
    _atomic_write_text(run_dir / "trace.json", trace_text)
    _atomic_write_text(run_dir / "manifest.json", manifest_text)
    _atomic_write_text(run_dir / "BUNDLE_SHA256.txt", bundle_sha256 + "\n")


def _load_bundle(run_dir: Path, expected_run_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    trace_path = run_dir / "trace.json"
    manifest_path = run_dir / "manifest.json"
    bundle_path = run_dir / "BUNDLE_SHA256.txt"
    if not all(path.is_file() for path in (trace_path, manifest_path, bundle_path)):
        raise DiscoveryError(f"Incomplete trace bundle: {run_dir}")

    trace_text = trace_path.read_text(encoding="utf-8-sig")
    manifest_text = manifest_path.read_text(encoding="utf-8-sig")
    recorded_bundle_sha256 = bundle_path.read_text(encoding="utf-8-sig").strip()
    trace = json.loads(trace_text)
    manifest = json.loads(manifest_text)
    _assert_redacted(trace)
    _assert_redacted(manifest)
    if manifest.get("trace_sha256") != sha256_text(trace_text):
        raise TraceIntegrityError("Trace hash does not match its manifest.")
    if recorded_bundle_sha256 != sha256_text(trace_text + manifest_text):
        raise TraceIntegrityError("Bundle hash does not match its contents.")
    if manifest.get("run_id") != expected_run_id or trace.get("run_id") != expected_run_id:
        raise TraceIntegrityError("Trace run identifier does not match its bundle.")
    return trace, manifest


def load_trace(run_id: str) -> tuple[Path, dict[str, Any]]:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise DiscoveryError("Invalid staged run identifier.")
    run_dir = STAGING_ROOT / run_id
    if not run_dir.is_dir():
        raise DiscoveryError(f"Unknown staged run: {run_id}")
    trace, _ = _load_bundle(run_dir, run_id)
    return run_dir, trace


def _derive_calculation(trace: dict[str, Any]) -> dict[str, Any]:
    attempts = trace.get("attempts", [])
    if not attempts:
        raise DiscoveryError("Verified replay requires at least one captured attempt.")
    parsed = attempts[-1].get("validation", {}).get("parsed_yaml")
    if not isinstance(parsed, dict):
        raise DiscoveryError("Final attempt is missing parsed output for calculation.")

    cell_type = trace["candidate"]["cell_type"]
    if cell_type == "cylindrical":
        report = CylindricalCalculator(from_cylindrical_template_format(parsed)).calculate()
    elif cell_type == "pouch":
        report = CellCalculator(from_pouch_template_format(parsed)).calculate()
    else:
        report = PrismaticCalculator(from_template_format(parsed)).calculate()
    return {
        "source": "deterministic_recalculation",
        "attempt": len(attempts),
        "capacity_ah": report.capacity_ah,
        "energy_wh": report.energy_wh,
        "total_mass_g": report.total_mass_g,
        "gravimetric_ed_whkg": report.gravimetric_ed_whkg,
        "volumetric_ed_cell_whl": report.volumetric_ed_cell_whl,
    }


def promote_trace(run_id: str, replay_id: str) -> tuple[Path, dict[str, Any]]:
    """Create a sanitized, integrity-checked verified-replay bundle."""
    if not replay_id or Path(replay_id).name != replay_id or replay_id in {".", ".."}:
        raise DiscoveryError("Invalid verified-replay identifier.")
    source_dir, source_trace = load_trace(run_id)
    _, source_manifest = _load_bundle(source_dir, run_id)
    attempts = source_trace.get("attempts", [])
    if (
        source_trace.get("source") != "live_gpt56"
        or source_trace.get("git", {}).get("clean") is not True
        or len(attempts) < 2
        or attempts[0].get("validation", {}).get("classification") != "engineering"
        or attempts[-1].get("validation", {}).get("classification") != "accepted"
        or source_trace.get("latest_classification") != "accepted"
        or any(attempt.get("source") != "live_gpt56" for attempt in attempts)
    ):
        raise DiscoveryError(
            "Verified replay requires a clean authentic engineering failure followed by acceptance."
        )

    destination = VERIFIED_REPLAY_ROOT / replay_id
    if destination.exists():
        raise DiscoveryError(f"Verified-replay destination already exists: {destination}")

    promoted = deepcopy(source_trace)
    removed_identifiers = 0
    for attempt in promoted["attempts"]:
        usage = attempt.get("usage", {})
        if usage.pop("response_id", None) is not None:
            removed_identifiers += 1
    promoted["promotion"] = {
        "mode": "verified_replay",
        "source_run_id": run_id,
        "source_trace_sha256": source_manifest["trace_sha256"],
        "source_bundle_sha256": (source_dir / "BUNDLE_SHA256.txt")
        .read_text(encoding="utf-8-sig")
        .strip(),
        "originating_commit": source_trace["git"]["head"],
        "removed_response_identifiers": removed_identifiers,
    }
    promoted["derived_calculation"] = _derive_calculation(promoted)
    write_bundle(destination, promoted)
    verified_trace, _ = _load_bundle(destination, run_id)
    return destination, verified_trace


def _new_trace(candidate: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    run_id = f"{timestamp}_{candidate['id'].lower()}_gpt56"
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "run_id": run_id,
        "created_utc": utc_now(),
        "updated_utc": None,
        "source": "live_gpt56",
        "mode": "failure_discovery",
        "git": state,
        "settings": {
            "openai_sdk_version": importlib.metadata.version("openai"),
            "max_output_tokens": 4096,
            "timeout_seconds": 120.0,
            "transport_max_retries": 0,
        },
        "candidate": candidate,
        "attempts": [],
        "latest_classification": None,
        "latest_failed_constraint_ids": [],
    }


def _validate_telemetry(trace: dict[str, Any]) -> None:
    attempt = trace["attempts"][-1]
    usage = attempt["usage"]
    requested_model = trace["candidate"]["requested_model"]
    actual_model = usage.get("model", "")
    if not actual_model or not (
        actual_model == requested_model or actual_model.startswith(f"{requested_model}-")
    ):
        trace["latest_classification"] = "telemetry"
        raise DiscoveryError("Returned model telemetry is missing or unexpected.")
    if usage.get("tokens_in", 0) <= 0 or usage.get("tokens_out", 0) <= 0:
        trace["latest_classification"] = "telemetry"
        raise DiscoveryError("Token telemetry is missing from the live response.")


def _print_summary(trace: dict[str, Any]) -> None:
    latest = trace["attempts"][-1] if trace.get("attempts") else {}
    usage = latest.get("usage", {})
    summary = {
        "run_id": trace["run_id"],
        "prompt_id": trace["candidate"]["id"],
        "attempt": len(trace.get("attempts", [])),
        "classification": trace.get("latest_classification"),
        "failed_constraint_ids": trace.get("latest_failed_constraint_ids", []),
        "returned_model": usage.get("model"),
        "tokens_in": usage.get("tokens_in"),
        "tokens_out": usage.get("tokens_out"),
        "staged_bundle": str(STAGING_ROOT / trace["run_id"]),
    }
    print(json.dumps(summary, indent=2))


def _public_error(exc: Exception) -> str:
    if isinstance(exc, DiscoveryError):
        return str(exc)
    return "Discovery command failed."


def _execute_live(trace: dict[str, Any], kind: str) -> dict[str, Any]:
    candidate = trace["candidate"]
    next_attempt = len(trace.get("attempts", [])) + 1
    reservation: int | None = None

    def reserve() -> int:
        nonlocal reservation
        reservation = reserve_call(
            kind,
            trace["run_id"],
            candidate["id"],
            next_attempt,
        )
        return reservation

    backend = OpenAIBackend(
        model=candidate["requested_model"],
        max_output_tokens=trace["settings"]["max_output_tokens"],
        timeout=trace["settings"]["timeout_seconds"],
        transport_max_retries=trace["settings"]["transport_max_retries"],
    )
    try:
        execute_one_attempt(trace, backend, reserve)
        mark_reservation(reservation, "completed")
        _validate_telemetry(trace)
    except Exception:
        mark_reservation(reservation, "failed")
        raise
    return trace


def command_list(_: argparse.Namespace) -> int:
    for candidate in load_candidates().values():
        print(
            f"{candidate['id']}: {candidate['cell_type']} -> "
            f"{','.join(candidate['target_constraints'])}"
        )
    return 0


def command_start(args: argparse.Namespace) -> int:
    candidates = load_candidates()
    if args.prompt_id not in candidates:
        raise DiscoveryError(f"Unknown candidate prompt: {args.prompt_id}")
    state = require_live_preflight()
    trace = _new_trace(candidates[args.prompt_id], state)
    run_dir = STAGING_ROOT / trace["run_id"]
    if run_dir.exists():
        raise DiscoveryError(f"Staging directory already exists: {run_dir}")
    write_bundle(run_dir, trace)
    try:
        _execute_live(trace, "discovery")
    except Exception as exc:
        trace["updated_utc"] = utc_now()
        trace["latest_classification"] = trace.get("latest_classification") or "infrastructure"
        trace["last_error"] = _public_error(exc)
        write_bundle(run_dir, trace)
        raise
    write_bundle(run_dir, trace)
    _print_summary(trace)
    return 0


def command_continue(args: argparse.Namespace) -> int:
    run_dir, trace = load_trace(args.run_id)
    require_live_preflight(expected_head=trace["git"]["head"])
    if trace.get("latest_classification") != "engineering":
        raise DiscoveryError("Only an engineering failure may receive a correction call.")
    if len(trace.get("attempts", [])) >= 3:
        raise BudgetError("The trace already contains the maximum three attempts.")
    try:
        _execute_live(trace, "correction")
    except Exception as exc:
        trace["updated_utc"] = utc_now()
        trace["latest_classification"] = trace.get("latest_classification") or "infrastructure"
        trace["last_error"] = _public_error(exc)
        write_bundle(run_dir, trace)
        raise
    write_bundle(run_dir, trace)
    _print_summary(trace)
    return 0


def command_summarize(args: argparse.Namespace) -> int:
    _, trace = load_trace(args.run_id)
    _print_summary(trace)
    return 0


def command_promote(args: argparse.Namespace) -> int:
    destination, trace = promote_trace(args.run_id, args.replay_id)
    print(
        json.dumps(
            {
                "run_id": trace["run_id"],
                "replay_id": args.replay_id,
                "mode": trace["promotion"]["mode"],
                "attempt_count": len(trace["attempts"]),
                "destination": str(destination),
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List reviewed prompts without network access.")
    list_parser.set_defaults(handler=command_list)

    start_parser = subparsers.add_parser("start", help="Make one first-attempt live request.")
    start_parser.add_argument("--prompt-id", required=True)
    start_parser.add_argument("--confirm-live", choices=[LIVE_CONFIRMATION], required=True)
    start_parser.set_defaults(handler=command_start)

    continue_parser = subparsers.add_parser(
        "continue", help="Replay prior attempts and make one correction request."
    )
    continue_parser.add_argument("--run-id", required=True)
    continue_parser.add_argument("--confirm-live", choices=[LIVE_CONFIRMATION], required=True)
    continue_parser.set_defaults(handler=command_continue)

    summary_parser = subparsers.add_parser("summarize", help="Print an allowlisted local summary.")
    summary_parser.add_argument("--run-id", required=True)
    summary_parser.set_defaults(handler=command_summarize)

    promote_parser = subparsers.add_parser(
        "promote", help="Create a sanitized verified-replay bundle without network access."
    )
    promote_parser.add_argument("--run-id", required=True)
    promote_parser.add_argument("--replay-id", required=True)
    promote_parser.set_defaults(handler=command_promote)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except DiscoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("ERROR: Discovery command failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
