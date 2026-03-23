"""Reconstruct results.tsv from git commit history.

Two modes:
  --fast    Extract primary_score from commit messages only (instant, no metrics)
  --full    Re-run each surrogate at each commit to get full metrics (~90s each)

Usage:
    python reconstruct_results.py --fast
    python reconstruct_results.py --full --budget 90
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Ensure forge is importable
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from forge.ml.autoresearch.metrics import parse_output  # noqa: E402
from forge.ml.autoresearch.results import ResultsLog, RunResult  # noqa: E402


def _git_log_experiments() -> list[dict]:
    """Parse experiment commits from git log."""
    result = subprocess.run(
        ["git", "log", "main..autoresearch/run-001", "--reverse",
         "--format=%H\t%aI\t%s"],
        capture_output=True, text=True, cwd=_repo_root,
    )
    if result.returncode != 0:
        print(f"git log failed: {result.stderr}", file=sys.stderr)
        return []

    experiments = []
    pattern = re.compile(r"experiment\s+(\d+):\s+(.+?)\s+score=([\d.]+)")
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        git_hash, timestamp, subject = parts
        m = pattern.search(subject)
        if not m:
            continue
        experiments.append({
            "experiment_id": int(m.group(1)),
            "description": m.group(2),
            "primary_score": float(m.group(3)),
            "git_hash": git_hash,
            "timestamp": timestamp,
        })
    return experiments


def _checkout_surrogate(git_hash: str) -> str:
    """Get surrogate.py content at a specific commit."""
    result = subprocess.run(
        ["git", "show", f"{git_hash}:experiments/ml/autoresearch/surrogate.py"],
        capture_output=True, text=True, cwd=_repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get surrogate.py at {git_hash[:8]}: {result.stderr}")
    return result.stdout


def _run_surrogate(surrogate_code: str, dataset_path: Path, budget: int, seed: int) -> dict[str, float]:
    """Run a surrogate script and parse its output metrics."""
    # Fix the repo root path so it works from a temp file location
    surrogate_code = surrogate_code.replace(
        "_repo_root = Path(__file__).resolve().parents[3]",
        f"_repo_root = Path({str(_repo_root)!r})",
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(surrogate_code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path,
             "--dataset", str(dataset_path),
             "--seed", str(seed),
             "--budget-seconds", str(budget)],
            capture_output=True, text=True, timeout=budget + 60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Surrogate failed: {result.stderr[-500:]}")
        return parse_output(result.stdout)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _run_fast(experiments: list[dict], results_path: Path) -> None:
    """Fast mode: primary_score from commit messages only."""
    log = ResultsLog(results_path)
    for exp in experiments:
        run = RunResult(
            experiment_id=exp["experiment_id"],
            metrics={},
            primary_score=exp["primary_score"],
            accepted=True,
            reason=exp["description"],
            timestamp=exp["timestamp"],
            git_hash=exp["git_hash"][:8],
        )
        log.append(run)
        print(f"  Exp {exp['experiment_id']:>3d}: {exp['primary_score']:.6f}  {exp['description']}")


def _run_full(experiments: list[dict], results_path: Path, budget: int, seed: int) -> None:
    """Full mode: re-run each surrogate to get all metrics."""
    dataset_path = Path(__file__).resolve().parent / "dataset"
    if not (dataset_path / "train.npz").exists():
        print("Dataset not found. Run `python prepare.py` first.", file=sys.stderr)
        sys.exit(1)

    log = ResultsLog(results_path)
    total = len(experiments)
    for i, exp in enumerate(experiments, 1):
        print(f"  [{i}/{total}] Experiment {exp['experiment_id']}: {exp['description']}...", end=" ", flush=True)
        try:
            surrogate_code = _checkout_surrogate(exp["git_hash"])
            metrics = _run_surrogate(surrogate_code, dataset_path, budget, seed)
        except Exception as e:
            print(f"FAILED: {e}")
            metrics = {}

        # Always use the commit message score (from the original full-budget run)
        # The re-run metrics are for detail columns only
        primary_score = exp["primary_score"]

        run = RunResult(
            experiment_id=exp["experiment_id"],
            metrics=metrics,
            primary_score=primary_score,
            accepted=True,
            reason=exp["description"],
            timestamp=exp["timestamp"],
            git_hash=exp["git_hash"][:8],
        )
        log.append(run)
        expected = exp["primary_score"]
        print(f"score={primary_score:.6f} (expected {expected:.6f})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct results.tsv from git history")
    parser.add_argument("--fast", action="store_true", help="Fast mode: scores from commit messages only")
    parser.add_argument("--full", action="store_true", help="Full mode: re-run surrogates for all metrics")
    parser.add_argument("--budget", type=int, default=90, help="Per-experiment budget in seconds (full mode)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for surrogate runs")
    args = parser.parse_args()

    if not args.fast and not args.full:
        args.fast = True  # default to fast

    experiments = _git_log_experiments()
    if not experiments:
        print("No experiment commits found.")
        return 1

    print(f"Found {len(experiments)} experiment commits to reconstruct.")

    results_path = Path(__file__).resolve().parent / "results.tsv"
    if results_path.exists():
        results_path.unlink()
        print(f"Removed existing {results_path.name}")

    if args.fast:
        _run_fast(experiments, results_path)
    else:
        _run_full(experiments, results_path, args.budget, args.seed)

    print(f"\nDone. Wrote {len(experiments)} rows to {results_path}")
    best = min(experiments, key=lambda e: e["primary_score"])
    print(f"Best: experiment {best['experiment_id']}, score={best['primary_score']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
