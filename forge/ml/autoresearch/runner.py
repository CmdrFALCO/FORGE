"""Run orchestration for autoresearch experiments."""

import argparse
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .config import RunConfig
from .constants import TOTAL_SECONDS
from .metrics import check_guardrails, compute_score, parse_output, should_accept
from .results import ResultsLog, RunResult


def _now_iso() -> str:
    """Return UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _build_command(config: RunConfig) -> list[str]:
    """Build surrogate subprocess command."""
    return [
        config.python_executable,
        str(config.surrogate_script),
        "--dataset",
        str(config.dataset_path),
        "--seed",
        str(config.seed),
        "--budget-seconds",
        str(config.budget_seconds),
    ]


def _rejected_result(experiment_id: int, reason: str) -> RunResult:
    """Build a rejected result with empty metrics."""
    return RunResult(
        experiment_id=experiment_id,
        metrics={},
        primary_score=float("inf"),
        accepted=False,
        reason=reason,
        timestamp=_now_iso(),
        git_hash="",
    )


def run_once(
    config: RunConfig,
    experiment_id: int,
    best_result: RunResult | None = None,
) -> RunResult:
    """Run one surrogate process, parse metrics, and decide accept/reject."""
    command = _build_command(config)
    try:
        completed = subprocess.run(
            command,
            cwd=config.repo_dir,
            timeout=config.budget_seconds + 30,
            capture_output=True,
            text=True,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _rejected_result(experiment_id, "timeout")

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        return _rejected_result(experiment_id, f"crash: {stderr[:200]}")

    try:
        parsed_metrics = parse_output(completed.stdout or "")
    except ValueError as exc:
        return _rejected_result(experiment_id, f"parse_error: {exc}")

    guardrails_ok, guardrail_reason = check_guardrails(parsed_metrics, config)
    if not guardrails_ok:
        return RunResult(
            experiment_id=experiment_id,
            metrics=parsed_metrics,
            primary_score=compute_score(parsed_metrics),
            accepted=False,
            reason=guardrail_reason,
            timestamp=_now_iso(),
            git_hash="",
        )

    primary_score = compute_score(parsed_metrics)
    result = RunResult(
        experiment_id=experiment_id,
        metrics=parsed_metrics,
        primary_score=primary_score,
        accepted=False,
        reason="",
        timestamp=_now_iso(),
        git_hash="",
    )

    if best_result is None:
        return replace(result, accepted=True, reason="baseline")

    best_time = best_result.metrics.get(TOTAL_SECONDS, float("inf"))
    candidate_time = parsed_metrics[TOTAL_SECONDS]
    accepted, reason = should_accept(
        candidate_score=primary_score,
        best_score=best_result.primary_score,
        candidate_time=candidate_time,
        best_time=best_time,
        min_delta=config.min_delta,
        epsilon=config.epsilon,
    )
    return replace(result, accepted=accepted, reason=reason)


def run_loop(config: RunConfig, iterations: int) -> list[RunResult]:
    """Run multiple experiments and append each result to TSV log."""
    results_log = ResultsLog(config.results_path)
    existing = results_log.load()
    best_result = results_log.get_best()

    start_id = 1
    if existing:
        start_id = max(item.experiment_id for item in existing) + 1

    loop_results: list[RunResult] = []
    for offset in range(iterations):
        experiment_id = start_id + offset
        result = run_once(config=config, experiment_id=experiment_id, best_result=best_result)
        results_log.append(result)
        loop_results.append(result)

        if result.accepted:
            best_result = result

        score_text = f"{result.primary_score:.6f}" if result.primary_score != float("inf") else "inf"
        status = "ACCEPT" if result.accepted else "REJECT"
        print(f"[{experiment_id}] score={score_text} {status} ({result.reason})")

    return loop_results


def _entrypoint(args: list[str] | None = None) -> None:
    """CLI entrypoint for autoresearch runner."""
    parser = argparse.ArgumentParser(description="FORGE autoresearch experiment runner")
    parser.add_argument("--surrogate", required=True, help="Path to surrogate.py")
    parser.add_argument("--dataset", required=True, help="Path to dataset directory")
    parser.add_argument("--results", default="results.tsv", help="Path to results TSV file")
    parser.add_argument("--repo-dir", default=".", help="Repository root directory")
    parser.add_argument("--budget-seconds", type=int, default=300, help="Time budget per experiment")
    parser.add_argument("--iterations", type=int, default=100, help="Number of experiments")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--min-delta", type=float, default=1e-4, help="Minimum score improvement")
    parser.add_argument("--epsilon", type=float, default=1e-4, help="Tie-break threshold")
    parser.add_argument("--temp-guardrail", type=float, default=None, help="Max allowed rmse_temp")
    parser.add_argument(
        "--max-error-temp-guardrail",
        type=float,
        default=None,
        help="Max allowed max_error_temp",
    )
    parser.add_argument("--dry-run", action="store_true", help="Disable write side-effects")
    parser.add_argument("--python", default="python", help="Python executable for surrogate subprocess")

    ns = parser.parse_args(args=args)
    config = RunConfig(
        surrogate_script=Path(ns.surrogate),
        dataset_path=Path(ns.dataset),
        results_path=Path(ns.results),
        repo_dir=Path(ns.repo_dir),
        budget_seconds=ns.budget_seconds,
        min_delta=ns.min_delta,
        epsilon=ns.epsilon,
        temp_guardrail=ns.temp_guardrail,
        max_error_temp_guardrail=ns.max_error_temp_guardrail,
        seed=ns.seed,
        dry_run=ns.dry_run,
        python_executable=ns.python,
    )
    results = run_loop(config=config, iterations=ns.iterations)
    accepted_count = sum(1 for item in results if item.accepted)
    print(f"Completed {len(results)} experiments, accepted {accepted_count}.")


if __name__ == "__main__":
    _entrypoint()

