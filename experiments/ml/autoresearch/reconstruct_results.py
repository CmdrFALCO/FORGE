"""Reconstruct results.tsv from git history by re-running surrogate.py at each commit.

The autoresearch experiments on autoresearch/run-001 were run manually
(not via run.py), so no results.tsv was written. This script iterates
through each experiment commit, checks out surrogate.py at that revision,
runs it against the dataset, parses the output, and writes results.tsv
using the same schema as ResultsLog.

Usage:
    cd experiments/ml/autoresearch
    python reconstruct_results.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from forge.ml.autoresearch.metrics import compute_score, parse_output  # noqa: E402
from forge.ml.autoresearch.results import ResultsLog, RunResult  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
RESULTS_PATH = BASE_DIR / "results.tsv"
SURROGATE_TMP = BASE_DIR / "_surrogate_tmp.py"

# Parse experiment number and score from commit subject line
_SUBJECT_RE = re.compile(r"experiment\s+(\d+):\s+.+\s+score=([\d.]+)")


def get_experiment_commits() -> list[tuple[str, str, str]]:
    """Get (hash, subject, timestamp) for each experiment commit."""
    result = subprocess.run(
        ["git", "log", "main..autoresearch/run-001", "--reverse",
         "--format=%H\t%s\t%aI"],
        capture_output=True, text=True, cwd=_repo_root,
    )
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append((parts[0], parts[1], parts[2]))
    return commits


def checkout_surrogate_at(commit_hash: str) -> str:
    """Extract surrogate.py content at a specific commit."""
    result = subprocess.run(
        ["git", "show", f"{commit_hash}:experiments/ml/autoresearch/surrogate.py"],
        capture_output=True, text=True, cwd=_repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get surrogate.py at {commit_hash[:8]}: {result.stderr}")
    return result.stdout


def run_surrogate(surrogate_code: str, budget: int = 90) -> str:
    """Write surrogate to temp file and run it, return stdout."""
    SURROGATE_TMP.write_text(surrogate_code)
    try:
        result = subprocess.run(
            [sys.executable, str(SURROGATE_TMP),
             "--dataset", str(DATASET_DIR),
             "--budget-seconds", str(budget),
             "--seed", "42"],
            capture_output=True, text=True, timeout=300,
            cwd=BASE_DIR,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Surrogate failed: {result.stderr[-500:]}")
        return result.stdout
    finally:
        SURROGATE_TMP.unlink(missing_ok=True)


def main() -> int:
    if not DATASET_DIR.exists():
        print("Dataset not found. Run prepare.py first.", file=sys.stderr)
        return 1

    commits = get_experiment_commits()
    print(f"Found {len(commits)} experiment commits to reconstruct.")

    if RESULTS_PATH.exists():
        RESULTS_PATH.unlink()
        print("Removed existing results.tsv")

    log = ResultsLog(RESULTS_PATH)
    total_start = time.time()

    for i, (commit_hash, subject, timestamp) in enumerate(commits):
        match = _SUBJECT_RE.match(subject)
        if not match:
            print(f"  [{i+1}/{len(commits)}] SKIP: {subject[:60]}")
            continue

        exp_id = int(match.group(1))
        expected_score = float(match.group(2))
        reason = subject.split(":", 1)[1].strip() if ":" in subject else subject

        print(f"  [{i+1}/{len(commits)}] Experiment {exp_id}: {reason[:50]}...", end=" ", flush=True)

        try:
            code = checkout_surrogate_at(commit_hash)
            stdout = run_surrogate(code)
            metrics = parse_output(stdout)
            score = compute_score(metrics)
            print(f"score={score:.6f} (expected {expected_score:.6f})")
        except Exception as e:
            # Fall back to commit message score with no detailed metrics
            print(f"FAILED ({e}), using commit score")
            metrics = {}
            score = expected_score

        result = RunResult(
            experiment_id=exp_id,
            metrics=metrics,
            primary_score=score,
            accepted=True,  # all commits on branch are accepted (rejected were reverted)
            reason=reason,
            timestamp=timestamp,
            git_hash=commit_hash[:8],
        )
        log.append(result)

    elapsed = time.time() - total_start
    print(f"\nDone. Wrote {len(commits)} rows to {RESULTS_PATH} in {elapsed:.0f}s")

    # Summary
    best = log.get_best()
    if best:
        print(f"Best: experiment {best.experiment_id}, score={best.primary_score:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
