"""
AXIOM Phase 4 Experiment Runner.

Executes the four AXIOM evaluation experiments by directly invoking the
supervisor driver (no HTTP).  Each completed prompt is written as a single
JSON line to enable crash-safe resume.

Usage:
    # Single experiment
    python -m forge.experiments.run_experiments \\
        --experiment exp1 --corpus forge/experiments/prompt_corpus_v1.json

    # All experiments sequentially
    python -m forge.experiments.run_experiments \\
        --experiment all --corpus forge/experiments/prompt_corpus_v1.json

    # Dry-run pilot (no file I/O, limited prompts)
    python -m forge.experiments.run_experiments \\
        --experiment exp1 --corpus forge/experiments/prompt_corpus_v1.json \\
        --dry-run --limit 3
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import subprocess
import sys
import time
import traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge.axiom.backends.backends import ClaudeBackend, LLMBackend, OllamaBackend
from forge.axiom.supervisor import driver as supervisor_driver
from forge.axiom.supervisor.result import GenerationResult
from forge.experiments.experiment_config import (
    EXPERIMENTS,
    BackendConfig,
    ExperimentDefinition,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RESULTS_DIR = Path(__file__).resolve().parent / "results"
_GPU_LOGS_DIR = _RESULTS_DIR / "gpu_logs"


def _utcnow_iso() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses, Paths, enums, etc. to JSON-safe types."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    # numpy / other numeric types -> Python float/int
    if hasattr(value, "item"):
        return value.item()  # type: ignore[union-attr]
    return value


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------

def _build_backend(cfg: BackendConfig) -> LLMBackend:
    """Instantiate an LLM backend from an experiment config."""
    if cfg.backend_type == "claude":
        return ClaudeBackend(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    if cfg.backend_type == "ollama":
        return OllamaBackend(
            host=cfg.host,
            model=cfg.model,
            temperature=cfg.temperature,
            num_ctx=cfg.num_ctx,
        )
    raise ValueError(f"Unknown backend type: {cfg.backend_type}")


# ---------------------------------------------------------------------------
# Resume: read already-completed prompt IDs from existing JSONL
# ---------------------------------------------------------------------------

def _load_completed_ids(jsonl_path: Path) -> set[str]:
    """Return the set of prompt_ids already recorded in *jsonl_path*."""
    completed: set[str] = set()
    if not jsonl_path.exists():
        return completed
    with open(jsonl_path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                pid = record.get("prompt_id")
                if pid:
                    completed.add(pid)
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping malformed JSON on line %d of %s", line_no, jsonl_path
                )
    return completed


# ---------------------------------------------------------------------------
# GPU monitor subprocess management
# ---------------------------------------------------------------------------

def _start_gpu_monitor(
    csv_path: Path, gpu_index: int = 0, interval: float = 5.0
) -> subprocess.Popen[str]:
    """Launch the GPU monitor as a background subprocess."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "forge.experiments.gpu_monitor",
            "--output",
            str(csv_path),
            "--interval",
            str(interval),
            "--gpu",
            str(gpu_index),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("GPU monitor started (PID %d) -> %s", proc.pid, csv_path)
    return proc


def _stop_gpu_monitor(proc: subprocess.Popen[str]) -> None:
    """Gracefully terminate the GPU monitor subprocess."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    logger.info("GPU monitor stopped (PID %d)", proc.pid)


# ---------------------------------------------------------------------------
# Single-prompt execution
# ---------------------------------------------------------------------------

def _run_single_prompt(
    prompt_entry: dict[str, Any],
    experiment: ExperimentDefinition,
    backend: LLMBackend,
) -> dict[str, Any]:
    """Execute a single prompt through the AXIOM pipeline and return a result record.

    This is the core inner loop.  It:
      1. Sets MAX_RETRIES on the driver module.
      2. Calls generate_cell_design().
      3. Extracts timing, token usage, constraint results, and design validity.
      4. Returns a fully-populated record dict ready for JSONL serialisation.
    """
    prompt_id: str = prompt_entry["prompt_id"]
    prompt_text: str = prompt_entry["prompt_text"]
    cell_type: str = prompt_entry.get("cell_type", "prismatic")

    timestamp_start = _utcnow_iso()
    wall_t0 = time.perf_counter()

    # Set MAX_RETRIES before calling the driver
    supervisor_driver.MAX_RETRIES = experiment.max_retries

    result: GenerationResult | None = None
    error_info: dict[str, Any] | None = None

    try:
        result = supervisor_driver.generate_cell_design(
            request=prompt_text,
            backend=backend,
            calculate=True,
            cell_type=cell_type,
        )
    except Exception as exc:
        error_info = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }

    wall_elapsed_s = time.perf_counter() - wall_t0
    timestamp_end = _utcnow_iso()

    # -- Build attempt records --
    attempts_out: list[dict[str, Any]] = []
    total_tokens_in = 0
    total_tokens_out = 0

    if result is not None:
        acr = result.attempt_constraint_results  # list[list[ConstraintResult]]

        # Attempts that triggered retries (failed attempts)
        for attempt_idx, reason in enumerate(result.retry_reasons):
            cr_list = acr[attempt_idx] if attempt_idx < len(acr) else []
            cr_dicts = [_to_jsonable(cr) for cr in cr_list]

            passed = sum(1 for cr in cr_list if cr.passed)
            total = len(cr_list)
            failed = total - passed

            attempts_out.append({
                "attempt_number": attempt_idx + 1,
                "design_valid": False,
                "constraints_total": total,
                "constraints_passed": passed,
                "constraints_failed": failed,
                "constraint_results": cr_dicts,
                "feedback_sent": reason,
                "tokens_in": None,
                "tokens_out": None,
                "inference_time_ms": None,
                "simulation_time_ms": None,
                "raw_llm_output": None,
            })

        # Final attempt (successful or last failed without retry reason)
        if result.success:
            cr_list = acr[-1] if acr else []
            cr_dicts = [_to_jsonable(cr) for cr in cr_list]
            passed = sum(1 for cr in cr_list if cr.passed)
            total = len(cr_list)
            failed = total - passed

            attempts_out.append({
                "attempt_number": result.attempts,
                "design_valid": True,
                "constraints_total": total,
                "constraints_passed": passed,
                "constraints_failed": failed,
                "constraint_results": cr_dicts,
                "feedback_sent": None,
                "tokens_in": None,
                "tokens_out": None,
                "inference_time_ms": None,
                "simulation_time_ms": None,
                "raw_llm_output": result.yaml_content,
            })
        elif result.attempts > len(result.retry_reasons):
            # Last attempt failed without a retry reason entry
            attempts_out.append({
                "attempt_number": result.attempts,
                "design_valid": False,
                "constraints_total": 0,
                "constraints_passed": 0,
                "constraints_failed": 0,
                "constraint_results": [],
                "feedback_sent": None,
                "tokens_in": None,
                "tokens_out": None,
                "inference_time_ms": None,
                "simulation_time_ms": None,
                "raw_llm_output": result.yaml_content,
            })

        # Token usage from last_usage (limitation: only the LAST LLM call)
        usage = backend.last_usage
        total_tokens_in = usage.tokens_in
        total_tokens_out = usage.tokens_out
        # Attach token counts to the last attempt record
        if attempts_out:
            attempts_out[-1]["tokens_in"] = usage.tokens_in
            attempts_out[-1]["tokens_out"] = usage.tokens_out

    # -- Prompt metadata --
    prompt_metadata = {
        "cell_type": prompt_entry.get("cell_type"),
        "chemistry": prompt_entry.get("chemistry"),
        "application": prompt_entry.get("application"),
        "difficulty": prompt_entry.get("difficulty"),
        "prompt_style": prompt_entry.get("prompt_style"),
    }

    # -- Summary --
    final_valid: bool | None = None
    total_attempts = 0
    recovered = False
    recovery_attempt: int | None = None

    if result is not None:
        final_valid = result.success
        total_attempts = result.attempts
        if result.success and result.attempts > 1:
            recovered = True
            recovery_attempt = result.attempts

    total_wall_time_ms = round(wall_elapsed_s * 1000, 1)

    summary = {
        "final_valid": final_valid,
        "total_attempts": total_attempts,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_inference_time_ms": None,
        "total_simulation_time_ms": None,
        "total_wall_time_ms": total_wall_time_ms,
        "recovered": recovered,
        "recovery_attempt": recovery_attempt,
    }

    # -- Assemble record --
    backend_label = (
        "claude_sonnet_4"
        if experiment.backend_config.backend_type == "claude"
        else "qwen_25_32b"
    )

    record: dict[str, Any] = {
        "prompt_id": prompt_id,
        "experiment_id": experiment.experiment_id,
        "backend": backend_label,
        "backend_model": experiment.backend_config.model,
        "supervised": experiment.supervised,
        "max_retries": experiment.max_retries - 1,  # user-facing: 0 or 3
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "prompt_metadata": prompt_metadata,
        "attempts": attempts_out,
        "summary": summary,
        "errors": error_info,
    }

    return record


# ---------------------------------------------------------------------------
# Progress / ETA helpers
# ---------------------------------------------------------------------------

def _format_duration(seconds: float) -> str:
    """Format seconds as 'Xh Ym' or 'Xm Ys'."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.0f}m {seconds % 60:.0f}s"
    hours = int(minutes // 60)
    remaining_min = int(minutes % 60)
    return f"{hours}h {remaining_min:02d}m"


def _status_line(
    exp_id: str,
    record: dict[str, Any],
    prompt_entry: dict[str, Any],
) -> str:
    """Format a single-line progress summary for one completed prompt."""
    pid = record["prompt_id"]
    ct = prompt_entry.get("cell_type", "?")
    chem = prompt_entry.get("chemistry", "?")
    app = prompt_entry.get("application", "?")[:4]
    diff = prompt_entry.get("difficulty", "?")[:5]
    style = prompt_entry.get("prompt_style", "?")[:7]

    meta = f"{ct}/{chem}/{app}/{diff}/{style}"

    wall_s = record["summary"]["total_wall_time_ms"] / 1000

    if record["errors"] is not None:
        err_type = record["errors"].get("error_type", "unknown")
        return f"[{exp_id}] {pid} | {meta:<42s} | ERROR  {err_type} | {wall_s:.1f}s"

    attempts = record["summary"]["total_attempts"]
    max_att = record["max_retries"] + 1  # display total possible

    if record["summary"]["final_valid"]:
        # Count constraints from last attempt
        last_attempt = record["attempts"][-1] if record["attempts"] else {}
        c_total = last_attempt.get("constraints_total", 0)
        c_passed = last_attempt.get("constraints_passed", 0)
        tag = "VALID "
        recovery = " (recovered)" if record["summary"]["recovered"] else ""
        return (
            f"[{exp_id}] {pid} | {meta:<42s} | {tag} "
            f"attempt {attempts}/{max_att} | {wall_s:.1f}s | "
            f"{c_passed}/{c_total} constraints{recovery}"
        )

    last_attempt = record["attempts"][-1] if record["attempts"] else {}
    c_total = last_attempt.get("constraints_total", 0)
    c_passed = last_attempt.get("constraints_passed", 0)
    return (
        f"[{exp_id}] {pid} | {meta:<42s} | REJECT "
        f"attempt {attempts}/{max_att} | {wall_s:.1f}s | "
        f"{c_passed}/{c_total} constraints"
    )


def _progress_line(
    exp_id: str,
    done: int,
    total: int,
    valid: int,
    rejected: int,
    errors: int,
    recent_wall_times: deque[float],
) -> str:
    """Periodic aggregate progress line with ETA."""
    pct = done / total * 100 if total else 0
    remaining = total - done

    if recent_wall_times:
        avg_s = sum(recent_wall_times) / len(recent_wall_times)
        eta_s = avg_s * remaining
        eta_str = _format_duration(eta_s)
    else:
        eta_str = "N/A"

    return (
        f"[{exp_id}] Progress: {done}/{total} ({pct:.1f}%) | "
        f"Valid: {valid} | Rejected: {rejected} | Errors: {errors} | "
        f"ETA: {eta_str}"
    )


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

def run_experiment(
    experiment: ExperimentDefinition,
    corpus: list[dict[str, Any]],
    output_dir: Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    gpu_index: int = 0,
) -> None:
    """Execute a single experiment over the full prompt corpus.

    Handles resume, GPU monitoring, progress reporting, and JSONL output.
    """
    exp_id = experiment.experiment_id

    # -- Resolve output paths --
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / experiment.output_filename

    # -- Resume detection --
    completed_ids = _load_completed_ids(jsonl_path) if not dry_run else set()
    total_prompts = len(corpus) if limit is None else min(limit, len(corpus))
    prompts_to_run = corpus[:total_prompts]

    skip_count = sum(1 for p in prompts_to_run if p["prompt_id"] in completed_ids)

    # -- Header --
    print(f"[{exp_id}] Starting {experiment.name}")
    print(
        f"[{exp_id}]   Backend: {experiment.backend_config.model} | "
        f"supervised={experiment.supervised} | MAX_RETRIES={experiment.max_retries}"
    )
    print(f"[{exp_id}]   Corpus: {total_prompts} prompts")
    if dry_run:
        print(f"[{exp_id}]   Mode: DRY RUN (no files written)")
    else:
        print(f"[{exp_id}]   Output: {jsonl_path}")
    if skip_count:
        first_remaining = next(
            (p["prompt_id"] for p in prompts_to_run if p["prompt_id"] not in completed_ids),
            "N/A",
        )
        print(
            f"[{exp_id}]   Resuming from {first_remaining} "
            f"({skip_count}/{total_prompts} already completed)"
        )
    else:
        print(f"[{exp_id}]   Starting from {prompts_to_run[0]['prompt_id']}")

    # -- Build backend --
    if dry_run:
        backend: LLMBackend | None = None
    else:
        backend = _build_backend(experiment.backend_config)

    # -- GPU monitor --
    gpu_proc: subprocess.Popen[str] | None = None
    if experiment.gpu_monitor and not dry_run and experiment.gpu_log_filename:
        gpu_log_dir = output_dir / "gpu_logs"
        gpu_log_dir.mkdir(parents=True, exist_ok=True)
        gpu_csv = gpu_log_dir / experiment.gpu_log_filename
        gpu_proc = _start_gpu_monitor(gpu_csv, gpu_index=gpu_index)

    # -- Counters --
    done = skip_count
    valid_count = 0
    rejected_count = 0
    error_count = 0
    recent_wall_times: deque[float] = deque(maxlen=10)

    try:
        for prompt_entry in prompts_to_run:
            pid = prompt_entry["prompt_id"]

            # Skip already completed
            if pid in completed_ids:
                continue

            # -- Dry-run shortcut --
            if dry_run:
                record = _build_dry_run_record(prompt_entry, experiment)
                print(_status_line(exp_id, record, prompt_entry))
                done += 1
                if done % 10 == 0 or done == total_prompts:
                    print(
                        _progress_line(
                            exp_id, done, total_prompts,
                            valid_count, rejected_count, error_count,
                            recent_wall_times,
                        )
                    )
                continue

            # -- Execute --
            assert backend is not None
            record = _run_single_prompt(prompt_entry, experiment, backend)

            # -- Write JSONL --
            with open(jsonl_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")

            # -- Update counters --
            done += 1
            wall_s = record["summary"]["total_wall_time_ms"] / 1000
            recent_wall_times.append(wall_s)

            if record["errors"] is not None:
                error_count += 1
            elif record["summary"]["final_valid"]:
                valid_count += 1
            else:
                rejected_count += 1

            # -- Print status --
            print(_status_line(exp_id, record, prompt_entry))
            if done % 10 == 0 or done == total_prompts:
                print(
                    _progress_line(
                        exp_id, done, total_prompts,
                        valid_count, rejected_count, error_count,
                        recent_wall_times,
                    )
                )

    except KeyboardInterrupt:
        print(f"\n[{exp_id}] Interrupted at {done}/{total_prompts}. Progress saved.")
    finally:
        if gpu_proc is not None:
            _stop_gpu_monitor(gpu_proc)

    # -- Summary footer --
    _print_summary(exp_id, done, total_prompts, valid_count, rejected_count,
                   error_count, jsonl_path, dry_run)


# ---------------------------------------------------------------------------
# Dry-run record builder
# ---------------------------------------------------------------------------

def _build_dry_run_record(
    prompt_entry: dict[str, Any],
    experiment: ExperimentDefinition,
) -> dict[str, Any]:
    """Return a lightweight placeholder record for dry-run mode."""
    backend_label = (
        "claude_sonnet_4"
        if experiment.backend_config.backend_type == "claude"
        else "qwen_25_32b"
    )
    now = _utcnow_iso()
    return {
        "prompt_id": prompt_entry["prompt_id"],
        "experiment_id": experiment.experiment_id,
        "backend": backend_label,
        "backend_model": experiment.backend_config.model,
        "supervised": experiment.supervised,
        "max_retries": experiment.max_retries - 1,
        "timestamp_start": now,
        "timestamp_end": now,
        "prompt_metadata": {
            "cell_type": prompt_entry.get("cell_type"),
            "chemistry": prompt_entry.get("chemistry"),
            "application": prompt_entry.get("application"),
            "difficulty": prompt_entry.get("difficulty"),
            "prompt_style": prompt_entry.get("prompt_style"),
        },
        "attempts": [
            {
                "attempt_number": 1,
                "design_valid": None,
                "constraints_total": 0,
                "constraints_passed": 0,
                "constraints_failed": 0,
                "constraint_results": [],
                "feedback_sent": None,
                "tokens_in": 0,
                "tokens_out": 0,
                "inference_time_ms": 0,
                "simulation_time_ms": 0,
                "raw_llm_output": "[DRY RUN]",
            }
        ],
        "summary": {
            "final_valid": None,
            "total_attempts": 1,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_inference_time_ms": 0,
            "total_simulation_time_ms": 0,
            "total_wall_time_ms": 0,
            "recovered": False,
            "recovery_attempt": None,
        },
        "errors": None,
    }


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def _print_summary(
    exp_id: str,
    done: int,
    total: int,
    valid: int,
    rejected: int,
    errors: int,
    jsonl_path: Path,
    dry_run: bool,
) -> None:
    sep = "=" * 50
    print(f"[{exp_id}] {sep}")
    print(f"[{exp_id}] EXPERIMENT {'DRY RUN ' if dry_run else ''}COMPLETE")
    print(f"[{exp_id}] Total prompts: {done}/{total}")

    if done > 0:
        vp = valid / done * 100
        rp = rejected / done * 100
        ep = errors / done * 100
        print(f"[{exp_id}] Valid designs: {valid} ({vp:.1f}%)")
        print(f"[{exp_id}] Rejected (max retries): {rejected} ({rp:.1f}%)")
        print(f"[{exp_id}] Errors: {errors} ({ep:.1f}%)")

    if not dry_run:
        print(f"[{exp_id}] Output: {jsonl_path}")
    print(f"[{exp_id}] {sep}")


# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------

def _load_corpus(corpus_path: Path) -> list[dict[str, Any]]:
    """Load and validate the prompt corpus JSON."""
    with open(corpus_path, encoding="utf-8") as fh:
        data = json.load(fh)

    prompts = data.get("prompts")
    if not prompts or not isinstance(prompts, list):
        raise SystemExit(f"Invalid corpus: 'prompts' key missing or empty in {corpus_path}")

    # Minimal validation
    for p in prompts[:3]:
        for key in ("prompt_id", "prompt_text", "cell_type"):
            if key not in p:
                raise SystemExit(f"Corpus entry missing required key '{key}': {p}")

    total = data.get("total_prompts", len(prompts))
    if len(prompts) != total:
        logger.warning(
            "Corpus header says %d prompts but found %d", total, len(prompts)
        )

    return prompts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AXIOM Phase 4 Experiment Runner",
    )
    parser.add_argument(
        "--experiment",
        required=True,
        choices=["exp1", "exp2", "exp3a", "exp3b", "all"],
        help="Which experiment to run (or 'all' for sequential execution).",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to prompt_corpus_v1.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Output directory (default: {_RESULTS_DIR}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing files or calling LLMs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N prompts (for piloting).",
    )
    parser.add_argument(
        "--gpu-index",
        type=int,
        default=0,
        help="GPU index for nvidia-smi monitoring (default: 0).",
    )
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    args = _build_parser().parse_args()

    output_dir = args.output_dir if args.output_dir else _RESULTS_DIR
    output_dir = Path(output_dir)
    corpus = _load_corpus(args.corpus)

    if args.experiment == "all":
        experiment_ids = ["exp1", "exp2", "exp3a", "exp3b"]
    else:
        experiment_ids = [args.experiment]

    for eid in experiment_ids:
        exp_def = EXPERIMENTS[eid]
        run_experiment(
            experiment=exp_def,
            corpus=corpus,
            output_dir=output_dir,
            dry_run=args.dry_run,
            limit=args.limit,
            gpu_index=args.gpu_index,
        )
        print()  # blank line between experiments


if __name__ == "__main__":
    main()
