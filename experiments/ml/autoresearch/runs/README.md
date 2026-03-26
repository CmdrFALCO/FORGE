# Autoresearch Run Archive

Each subdirectory contains frozen artifacts from a completed autoresearch run.

| Run | Optimizer | Dataset | Samples | Trials | Best Score | Improvement |
|-----|-----------|---------|---------|--------|------------|-------------|
| run-001-synthetic | LLM (Sonnet) | Synthetic proxy formulas | 2000 | 200 (36 accepted) | 0.1517 | 57.5% |
| run-002-pybamm-500 | LLM (Sonnet) | PyBaMM DFN (Chen2020) | 496 | 37 (6 accepted) | 0.4676 | 28.4% |
| run-003-pybamm-3k | LLM (Sonnet) | PyBaMM DFN (Chen2020) | 3000 | 16 (3 accepted) | 0.2871 | 2.95% |
| run-004a-optuna-500 | Optuna TPE | PyBaMM DFN (Chen2020) | 496 | 200 (112 completed) | 0.4634 | 29.0% |
| run-004b-optuna-3k | Optuna TPE | PyBaMM DFN (Chen2020) | 3000 | 200 (112 completed) | 0.3053 | -3.2% |

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
