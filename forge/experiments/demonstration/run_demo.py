#!/usr/bin/env python3
"""
Demo: Range-enriched validation feedback for Mistral Small 3.1.

Tests the hypothesis that including valid ranges in schema error messages
(e.g., "cathode_height_mm must be between 50 and 150, got 175" instead of
"175.0 is not valid under any of the given schemas") allows Mistral to
correct its 50 persistent prismatic failures from exp_mistral_sup.

Single change only. Supervised mode, 4 attempts max. Writes to:
  forge/experiments/demonstration/demo_mistral_range_feedback.jsonl

Usage (from FORGE root):
    .venv/bin/python3 forge/experiments/demonstration/run_demo.py
"""

from __future__ import annotations

import json
import logging
from collections import deque
from pathlib import Path

# ---------------------------------------------------------------------------
# Monkey-patch validate_structure BEFORE any pipeline imports pick it up.
# This is the ONLY change: enrich error messages with valid ranges.
# ---------------------------------------------------------------------------
import jsonschema

from forge.engine.validation import schema_validator

_original_validate_structure = schema_validator.validate_structure


def _enrich_error_message(error: jsonschema.ValidationError) -> str:
    """Extract valid range from jsonschema error and produce a clear message."""
    field_name = error.absolute_path[-1] if error.absolute_path else "value"

    # oneOf failure — extract numeric schema's min/max
    if error.validator == "oneOf" and isinstance(error.validator_value, list):
        for sub_schema in error.validator_value:
            if sub_schema.get("type") == "number":
                lo = sub_schema.get("minimum")
                hi = sub_schema.get("maximum")
                if lo is not None and hi is not None:
                    return f"{field_name} must be between {lo} and {hi}, got {error.instance}"
                if lo is not None:
                    return f"{field_name} must be at least {lo}, got {error.instance}"
                if hi is not None:
                    return f"{field_name} must be at most {hi}, got {error.instance}"
            if sub_schema.get("type") == "string" and "enum" in sub_schema:
                return (
                    f"{field_name} must be one of {sub_schema['enum']}, "
                    f"got {error.instance!r}"
                )

    # Direct minimum / maximum
    if error.validator == "minimum":
        return f"{field_name} must be at least {error.validator_value}, got {error.instance}"
    if error.validator == "maximum":
        return f"{field_name} must be at most {error.validator_value}, got {error.instance}"

    # Enum
    if error.validator == "enum":
        return f"{field_name} must be one of {error.validator_value}, got {error.instance!r}"

    # Type mismatch
    if error.validator == "type":
        return (
            f"{field_name} must be of type {error.validator_value}, "
            f"got {type(error.instance).__name__}: {error.instance!r}"
        )

    # Fallback: original jsonschema message
    return error.message


def _validate_structure_with_ranges(
    cell_dict: dict, cell_type: str = "prismatic"
) -> schema_validator.ValidationResult:
    """Drop-in replacement for validate_structure with range-enriched errors."""
    schema = schema_validator.load_schema(cell_type)
    validator = jsonschema.Draft7Validator(schema)

    errors: list[schema_validator.ValidationError] = []
    for error in validator.iter_errors(cell_dict):
        path_parts = [str(p) for p in error.absolute_path]
        path = ".".join(path_parts) if path_parts else "(root)"

        if error.validator == "required" and error.validator_value:
            missing = (
                list(set(error.validator_value) - set(error.instance.keys()))
                if isinstance(error.instance, dict)
                else []
            )
            if missing:
                path = f"{path}.{missing[0]}" if path != "(root)" else missing[0]

        errors.append(
            schema_validator.ValidationError(
                path=path,
                message=_enrich_error_message(error),
                value=error.instance,
                constraint=error.validator,
            )
        )

    return schema_validator.ValidationResult(
        valid=len(errors) == 0, errors=errors, level="schema"
    )


# Patch both modules so every call path sees the enriched version.
schema_validator.validate_structure = _validate_structure_with_ranges

from forge.engine.validation import pipeline as _pipeline  # noqa: E402

_pipeline.validate_structure = _validate_structure_with_ranges

# ---------------------------------------------------------------------------
# Now import the rest (after patching).
# ---------------------------------------------------------------------------

from forge.experiments.experiment_config import (  # noqa: E402
    MISTRAL_SMALL_31,
    ExperimentDefinition,
)
from forge.experiments.run_experiments import (  # noqa: E402
    _build_backend,
    _load_completed_ids,
    _progress_line,
    _run_single_prompt,
    _status_line,
)

# ---------------------------------------------------------------------------
# Demo configuration
# ---------------------------------------------------------------------------

DEMO_EXPERIMENT = ExperimentDefinition(
    experiment_id="demo_mistral_range_fb",
    name="Demo: Mistral + range feedback (supervised)",
    description=(
        "Re-runs the 50 known Mistral supervised rejects with "
        "range-enriched validation error messages."
    ),
    backend_config=MISTRAL_SMALL_31,
    supervised=True,
    max_retries=4,
    output_filename="demo_mistral_range_feedback.jsonl",
    gpu_monitor=False,
)

# The 50 prompt IDs that Mistral supervised rejected in exp_mistral_sup.
MISTRAL_REJECT_IDS: set[str] = {
    "P-002", "P-010", "P-021", "P-030", "P-051", "P-061", "P-063",
    "P-092", "P-104", "P-109", "P-110", "P-113", "P-116", "P-124",
    "P-130", "P-135", "P-147", "P-161", "P-175", "P-188", "P-194",
    "P-212", "P-223", "P-226", "P-239", "P-240", "P-247", "P-253",
    "P-264", "P-280", "P-295", "P-307", "P-309", "P-324", "P-350",
    "P-361", "P-363", "P-368", "P-371", "P-383", "P-385", "P-399",
    "P-405", "P-406", "P-419", "P-450", "P-469", "P-483", "P-487",
    "P-488",
}

CORPUS_PATH = Path(__file__).resolve().parent.parent / "prompt_corpus_v1.json"
OUTPUT_DIR = Path(__file__).resolve().parent


def _load_corpus(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["prompts"]


def _prewarm_mistral() -> None:
    """Pre-warm Mistral in Ollama so the first prompt isn't cold."""
    import urllib.request

    print("[demo] Pre-warming mistral-small3.1 ...", flush=True)
    body = json.dumps({
        "model": "mistral-small3.1",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.0, "num_ctx": 8192, "num_predict": 5},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            print(f"[demo] Model loaded: {result.get('model', '?')}", flush=True)
    except Exception as e:
        print(f"[demo] Pre-warm warning: {e}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    # Load & filter corpus to the 50 rejects
    corpus = _load_corpus(CORPUS_PATH)
    demo_corpus = [p for p in corpus if p["prompt_id"] in MISTRAL_REJECT_IDS]

    if len(demo_corpus) != len(MISTRAL_REJECT_IDS):
        found = {p["prompt_id"] for p in demo_corpus}
        missing = MISTRAL_REJECT_IDS - found
        print(f"[demo] WARNING: {len(missing)} prompt IDs not found in corpus: {missing}")

    total = len(demo_corpus)
    print(f"[demo] Loaded {total} prompts (the known Mistral rejects)")

    # Output path
    jsonl_path = OUTPUT_DIR / DEMO_EXPERIMENT.output_filename
    completed_ids = _load_completed_ids(jsonl_path)
    skip = sum(1 for p in demo_corpus if p["prompt_id"] in completed_ids)
    if skip:
        print(f"[demo] Resuming: {skip}/{total} already completed")

    # Pre-warm & build backend
    _prewarm_mistral()
    backend = _build_backend(DEMO_EXPERIMENT.backend_config)

    # Run
    exp_id = DEMO_EXPERIMENT.experiment_id
    done = skip
    valid_count = 0
    rejected_count = 0
    error_count = 0
    recent: deque[float] = deque(maxlen=10)

    print(f"\n[{exp_id}] Starting — {total} prompts, supervised, max_retries=4")
    print(f"[{exp_id}] Change: range-enriched validation feedback")
    print(f"[{exp_id}] Output: {jsonl_path}\n", flush=True)

    try:
        for prompt_entry in demo_corpus:
            pid = prompt_entry["prompt_id"]
            if pid in completed_ids:
                continue

            record = _run_single_prompt(prompt_entry, DEMO_EXPERIMENT, backend)

            with open(jsonl_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")

            done += 1
            wall_s = record["summary"]["total_wall_time_ms"] / 1000
            recent.append(wall_s)

            if record["errors"] is not None:
                error_count += 1
            elif record["summary"]["final_valid"]:
                valid_count += 1
            else:
                rejected_count += 1

            print(_status_line(exp_id, record, prompt_entry), flush=True)
            if done % 10 == 0 or done == total:
                print(
                    _progress_line(
                        exp_id, done, total,
                        valid_count, rejected_count, error_count, recent,
                    ),
                    flush=True,
                )

    except KeyboardInterrupt:
        print(f"\n[{exp_id}] Interrupted at {done}/{total}. Progress saved.")

    # Summary
    print(f"\n{'='*60}")
    print(f"[{exp_id}] DONE: {done}/{total}")
    print(f"  Valid:    {valid_count}/{done} ({valid_count/done*100:.1f}%)" if done else "")
    print(f"  Rejected: {rejected_count}/{done}")
    print(f"  Errors:   {error_count}/{done}")
    print(f"  Output:   {jsonl_path}")

    if done:
        # Compare with baseline (50/50 rejected without range feedback)
        baseline_rejected = 50
        improvement = baseline_rejected - rejected_count
        print(f"\n  Baseline (no ranges): 0/{baseline_rejected} valid (0.0%)")
        print(f"  Demo (with ranges):   {valid_count}/{done} valid ({valid_count/done*100:.1f}%)")
        print(f"  Improvement:          +{improvement} designs recovered")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
