# L2-B Autoresearch Experiment Setup

This directory contains the concrete battery-cell surrogate experiment setup used by FORGE autoresearch.
The reusable engine lives in `forge/ml/autoresearch/`. The scripts here are experiment artifacts.

## Prerequisites

From the repository root:

```bash
pip install -e ".[ml]"
```

This installs `torch`, `scipy`, `matplotlib`, and makes the `forge` package importable.

## Quick Start

From `experiments/ml/autoresearch/`:

1. Generate synthetic dataset:

```bash
python prepare.py
```

2. Run a smoke test loop:

```bash
python run.py --budget-seconds 60 --iterations 5
```

3. Plot results:

```bash
python analysis.py
```

## Output Key Contract

`surrogate.py` prints one metrics block beginning with `---` and exactly these 10 keys:

- `rmse_rate`: RMSE for rate capability target (raw units)
- `rmse_temp`: RMSE for max temperature target (raw units)
- `rmse_rate_norm`: normalized rate RMSE (divide by train-set std)
- `rmse_temp_norm`: normalized temp RMSE (divide by train-set std)
- `max_error_rate`: max absolute error for rate target
- `max_error_temp`: max absolute error for temp target
- `training_seconds`: training loop duration in seconds
- `total_seconds`: total runtime duration in seconds
- `num_params`: model parameter count
- `num_epochs`: completed training epochs

`primary_score` is intentionally not printed. It is computed by the L2-A engine from normalized RMSE values.

## Notes

- `surrogate.py` is the only file intended for autonomous modification during search.
- Generated files (`dataset/*.npz`, `dataset/metadata.json`, `results.tsv`, `results_plot.png`) are ignored by git.
- See `forge/ml/autoresearch/` for engine internals and API.

