# FORGE Experiments - Thesis Evaluation Infrastructure

## Overview

This directory contains experiment scripts, configurations, and analysis tools
for the FORGE Master's thesis. It is intentionally outside the `forge/` Python
package - the package is the portfolio tool; experiments are research on the tool.

## Structure

### AXIOM Experiments (`axiom/`)

Evaluation of the neuro-symbolic supervision architecture.

- `prompts/` - Test prompts for cell generation (for example, 50 design requests)
- `runners/` - Experiment execution scripts (supervised vs. unsupervised comparison)
- `analysis/` - Statistical analysis (success rates, retry counts, error types)

### ML Experiments (`ml/`)

Surrogate modeling and geometric representation learning experiments.

- `sensitivity/` - PyBOP Sobol screening runs and parameter importance analysis
- `dataset_generation/` - Batch PyBaMM simulation scripts and output management
- `training/` - Model training runs, hyperparameter configs, checkpoints
- `analysis/` - ML result analysis (accuracy, representation comparison, ablations)

### Shared

- `data/` - Generated datasets, simulation outputs, ML training results
- `notebooks/` - Jupyter notebooks for interactive analysis and visualization

## Relationship to Package

```
forge/              <- The tool (portfolio)
experiments/        <- Research on the tool (thesis)
```

The experiments directory imports from `forge.*` but is never imported by it.
