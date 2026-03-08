"""Launch autoresearch experiments on the local surrogate + dataset.

Usage:
    python run.py --budget-seconds 60 --iterations 5
    python run.py --budget-seconds 300 --iterations 100
"""

import argparse
import sys
from pathlib import Path

# Ensure forge package is importable when running from experiments/ directory.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from forge.ml.autoresearch import ResultsLog, RunConfig, run_loop  # noqa: E402


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local L2-B autoresearch loop")
    parser.add_argument("--budget-seconds", type=int, default=300)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--python", default=sys.executable, help="Python executable for subprocess")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    base_dir = Path(__file__).resolve().parent
    surrogate_path = base_dir / "surrogate.py"
    dataset_path = base_dir / "dataset"
    results_path = base_dir / "results.tsv"
    repo_dir = _find_repo_root(base_dir)

    config = RunConfig(
        surrogate_script=surrogate_path,
        dataset_path=dataset_path,
        results_path=results_path,
        repo_dir=repo_dir,
        budget_seconds=args.budget_seconds,
        min_delta=1e-4,
        epsilon=1e-4,
        seed=args.seed,
        dry_run=args.dry_run,
        python_executable=args.python,
    )

    results = run_loop(config=config, iterations=args.iterations)
    accepted_count = sum(1 for item in results if item.accepted)
    best = ResultsLog(results_path).get_best()
    best_text = "N/A" if best is None else f"{best.primary_score:.6f}"
    print(f"Finished {len(results)} experiments, accepted {accepted_count}, best score {best_text}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

