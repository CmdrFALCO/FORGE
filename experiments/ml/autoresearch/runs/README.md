# Autoresearch Run Archive

Each subdirectory contains frozen artifacts from a completed autoresearch run.

| Run | Dataset | Samples | Experiments | Best Score | Improvement |
|-----|---------|---------|-------------|------------|-------------|
| run-001-synthetic | Synthetic proxy formulas | 2000 | 200 (36 accepted) | 0.1517 | 57.5% |
| run-002-pybamm-500 | PyBaMM DFN (Chen2020) | 496 | 37 (6 accepted) | 0.4676 | 28.4% |

## Structure per run

- `results.tsv` — Full experiment log (experiment_id, metrics, accepted/rejected)
- `surrogate.py` — Best (final accepted) surrogate architecture
- `checkpoint.pt` — Saved model weights (if available)
- `run_config.json` — Run metadata, key findings, dataset info

## Adding a new run

1. Complete the autoresearch loop on a feature branch
2. Create a new directory: `run-NNN-description/`
3. Copy `results.tsv`, `surrogate.py`, `checkpoint.pt` from the branch
4. Create `run_config.json` with metadata
5. The dashboard dropdown will pick it up automatically
