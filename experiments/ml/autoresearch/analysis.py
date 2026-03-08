import argparse
import sys
from pathlib import Path

import numpy as np

# Ensure forge package is importable when running from experiments/ directory.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

try:
    import matplotlib.pyplot as plt
except ImportError:
    print('matplotlib required: pip install -e ".[ml]"', file=sys.stderr)
    raise SystemExit(1)

from forge.ml.autoresearch import ResultsLog  # noqa: E402
from forge.ml.autoresearch.constants import RMSE_RATE_NORM, RMSE_TEMP_NORM  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze autoresearch results")
    parser.add_argument(
        "--results",
        default=str(Path(__file__).resolve().parent / "results.tsv"),
        help="Path to results.tsv",
    )
    return parser


def _print_leaderboard(rows: list) -> None:
    accepted = [row for row in rows if row.accepted]
    accepted.sort(key=lambda item: item.primary_score)
    print("Top 10 accepted experiments:")
    if not accepted:
        print("  (none)")
        return
    for row in accepted[:10]:
        print(
            f"  id={row.experiment_id:4d} "
            f"score={row.primary_score:.6f} "
            f"reason={row.reason} "
            f"timestamp={row.timestamp}"
        )


def main() -> int:
    args = _build_parser().parse_args()
    results_path = Path(args.results).resolve()
    log = ResultsLog(results_path)
    rows = log.load()

    if not rows:
        print(f"No results found at {results_path}")
        return 0

    _print_leaderboard(rows)

    rows_sorted = sorted(rows, key=lambda item: item.experiment_id)
    exp_ids = np.array([item.experiment_id for item in rows_sorted], dtype=np.int64)
    scores = np.array([item.primary_score for item in rows_sorted], dtype=np.float64)
    accepted_mask = np.array([item.accepted for item in rows_sorted], dtype=bool)
    safe_scores = np.where(np.isfinite(scores), scores, np.nan)
    running_best = np.minimum.accumulate(np.where(np.isnan(safe_scores), np.inf, safe_scores))

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)

    axes[0].scatter(exp_ids[~accepted_mask], safe_scores[~accepted_mask], c="red", label="Rejected", alpha=0.6)
    axes[0].scatter(exp_ids[accepted_mask], safe_scores[accepted_mask], c="green", label="Accepted", alpha=0.8)
    axes[0].plot(exp_ids, running_best, c="blue", label="Best so far", linewidth=1.5)
    axes[0].set_title("Primary Score vs Experiment")
    axes[0].set_xlabel("Experiment ID")
    axes[0].set_ylabel("Primary Score")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    accepted_ids = [item.experiment_id for item in rows_sorted if item.accepted]
    rate_norm = [item.metrics.get(RMSE_RATE_NORM, np.nan) for item in rows_sorted if item.accepted]
    temp_norm = [item.metrics.get(RMSE_TEMP_NORM, np.nan) for item in rows_sorted if item.accepted]
    axes[1].plot(accepted_ids, rate_norm, marker="o", label="rmse_rate_norm")
    axes[1].plot(accepted_ids, temp_norm, marker="o", label="rmse_temp_norm")
    axes[1].set_title("Accepted Experiments: Normalized RMSE")
    axes[1].set_xlabel("Experiment ID")
    axes[1].set_ylabel("Normalized RMSE")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    output_path = results_path.parent / "results_plot.png"
    fig.savefig(output_path, dpi=150)
    print(f"Saved plot: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

