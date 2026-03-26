# Run 004 — Optuna Hyperparameter Comparison

## Context

Runs 001-003 used an LLM agent (Claude Sonnet) for autonomous surrogate optimization. The thesis needs a controlled comparison against a standard automated hyperparameter optimizer to answer: "What does the LLM contribute beyond what Optuna can do?"

The hypothesis: the LLM's advantage is feature engineering and dead feature removal — things Optuna can't do. On the data-scarce 500-sample dataset, this matters. On the data-rich 3000-sample dataset, it doesn't.

**Two runs:**
- **Run 004a:** Optuna on `dataset_pybamm` (496 samples, 347 train) — compare against Run 002
- **Run 004b:** Optuna on `dataset_pybamm_3k` (3000 samples, ~2100 train) — compare against Run 003

## Pre-Check — READ THESE FILES FIRST

1. **`experiments/ml/autoresearch/runs/run-002-pybamm-500/surrogate.py`** — The LLM's best architecture on 500 samples. Understand what the LLM discovered: Huber loss, AdamW, GELU, dead feature zeroing, Bruggeman feature, electrode-porosity interaction.

2. **`experiments/ml/autoresearch/runs/run-003-pybamm-3k/surrogate.py`** — The LLM's best on 3000 samples. Much simpler: GELU, HIDDEN=96, dead feature zeroing.

3. **`forge/ml/autoresearch/metrics.py`** — How `primary_score` is computed (rmse_rate_norm + rmse_temp_norm). Optuna must use the exact same metric as its objective.

4. **`experiments/ml/autoresearch/dataset_pybamm/metadata.json`** — Feature names, target names, target stds (needed for RMSE normalization).

5. **`experiments/ml/autoresearch/dataset_pybamm_3k/metadata.json`** — Same, for the 3k dataset.

## What to Build

### File 1: `experiments/ml/autoresearch/optuna_search.py`

**Purpose:** Self-contained Optuna hyperparameter search script. Trains an MLP surrogate with Optuna-selected hyperparameters and reports results in the same format as the autoresearch loop.

**Design principle:** Optuna controls ONLY what a traditional hyperparameter optimizer controls. It does NOT do feature engineering, feature selection, or architecture invention. It uses the 11 raw input features as-is. This is the fair comparison — Optuna tunes numbers, the LLM invents ideas.

**Optuna search space:**

```python
def objective(trial):
    # Architecture
    hidden_size = trial.suggest_int("hidden_size", 32, 256, step=32)
    num_layers = trial.suggest_int("num_layers", 1, 4)
    activation = trial.suggest_categorical("activation", ["relu", "gelu", "tanh", "silu"])
    
    # Training
    learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True)
    batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128])
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True)
    optimizer_name = trial.suggest_categorical("optimizer", ["adam", "adamw"])
    loss_fn = trial.suggest_categorical("loss", ["mse", "huber"])
    
    # Regularization
    use_batchnorm = trial.suggest_categorical("batchnorm", [True, False])
    use_skip = trial.suggest_categorical("skip_connection", [True, False])
    dropout = trial.suggest_float("dropout", 0.0, 0.3, step=0.05)
    
    # Ensemble
    ensemble_size = trial.suggest_int("ensemble_size", 1, 10)
```

**What Optuna does NOT control (fixed for fair comparison):**
- Input features: always the 11 raw features (8 geometric + 3 derived). NO feature engineering, NO log transforms, NO Bruggeman, NO interaction terms, NO dead feature zeroing
- Random seed: 42 (same as LLM runs)
- Time budget per trial: 300 seconds (same as LLM experiments)
- Dataset: fixed per run (passed via CLI)
- Output metric: primary_score = rmse_rate_norm + rmse_temp_norm (computed identically to autoresearch engine)

**Training loop inside the objective:**

The training loop should be essentially the same as the baseline surrogate.py but with parameterized hyperparameters. For each trial:

1. Load dataset (.npz + metadata.json), verify hashes
2. Normalize inputs (zero mean, unit variance from training set)
3. Build MLP with trial's hyperparameters
4. Train for as many epochs as fit within 300s budget
5. Evaluate on validation set
6. Compute primary_score = rmse_rate_norm + rmse_temp_norm
7. Return primary_score (Optuna minimizes)

**Important:** Each ensemble member trains independently with a different seed (same pattern as the LLM's surrogate.py). The time budget covers ALL ensemble members.

**CLI interface:**

```python
parser = argparse.ArgumentParser(description="Optuna hyperparameter search for surrogate model")
parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory")
parser.add_argument("--n-trials", type=int, default=200, help="Number of Optuna trials")
parser.add_argument("--budget-seconds", type=int, default=300, help="Time budget per trial")
parser.add_argument("--seed", type=int, default=42, help="Random seed")
parser.add_argument("--output", type=str, default="optuna_results", help="Output directory")
parser.add_argument("--study-name", type=str, default="surrogate_hpo", help="Optuna study name")
```

**Output format:**

After all trials complete, save:

1. **`results.tsv`** — One row per trial, same columns as autoresearch results.tsv:
   - experiment_id, rmse_rate, rmse_temp, rmse_rate_norm, rmse_temp_norm, max_error_rate, max_error_temp, training_seconds, total_seconds, num_params, num_epochs
   - Add column: `primary_score` (Optuna computes this directly, unlike the LLM loop where the engine computes it)
   - Add column: `accepted` (1 if score < previous best, 0 otherwise — retrospective, for chart compatibility)

2. **`best_params.json`** — Best trial's hyperparameters

3. **`optuna_study.db`** — SQLite study database (Optuna's native format, enables later analysis)

4. **`run_config.json`** — Same format as LLM runs, with additional fields:
   ```json
   {
     "optimizer_type": "optuna_tpe",
     "search_space": { ... },
     "fixed_features": "11 raw (no engineering, no selection)",
     "comparison_note": "Fair comparison — Optuna tunes numbers, LLM invents ideas"
   }
   ```

**Progress logging:**

```python
# After each trial
logger.info(
    f"Trial {trial.number}/{n_trials} | "
    f"score={trial.value:.4f} | best={study.best_value:.4f} | "
    f"params: h={trial.params['hidden_size']}, lr={trial.params['learning_rate']:.1e}, "
    f"act={trial.params['activation']}, ens={trial.params['ensemble_size']}"
)
```

**Pruning:** Use Optuna's MedianPruner to kill unpromising trials early. Report intermediate values (validation loss at each epoch) so Optuna can prune trials that are clearly losing:

```python
# Inside training loop
if epoch % 50 == 0:
    trial.report(val_loss, epoch)
    if trial.should_prune():
        raise optuna.TrialPruned()
```

This makes Optuna faster than the LLM (which always runs to budget). That's fair — Optuna's efficiency at evaluating hyperparameters is part of its advantage.

### File 2: Dependencies

Add to `pyproject.toml` under `ml` optional dependencies:
```toml
ml = [
    "torch>=2.0",
    "scipy>=1.11",
    "matplotlib>=3.7",
    "pybop>=24.3",
    "SALib>=1.4",
    "optuna>=3.0",
]
```

## Execution Plan

### Run 004a — Optuna on 500 samples

```bash
cd experiments/ml/autoresearch
python optuna_search.py --dataset dataset_pybamm --n-trials 200 --budget-seconds 300 --output optuna_results_500 --study-name run-004a-500
```

**Expected runtime:** Faster than LLM runs because Optuna prunes bad trials early. Estimate: 6-10 hours for 200 trials.

After completion, archive:
```bash
mkdir -p runs/run-004a-optuna-500
cp optuna_results_500/results.tsv runs/run-004a-optuna-500/
cp optuna_results_500/best_params.json runs/run-004a-optuna-500/
cp optuna_results_500/run_config.json runs/run-004a-optuna-500/
```

Create `run_config.json` with actual results. Set `display_name` to `"Run 004a — Optuna (500 samples)"`.

### Run 004b — Optuna on 3000 samples

```bash
python optuna_search.py --dataset dataset_pybamm_3k --n-trials 200 --budget-seconds 300 --output optuna_results_3k --study-name run-004b-3k
```

After completion, archive into `runs/run-004b-optuna-3k/`.

Set `display_name` to `"Run 004b — Optuna (3000 samples)"`.

### Run Both Sequentially

```bash
# Run both back-to-back (~12-20 hours total)
python optuna_search.py --dataset dataset_pybamm --n-trials 200 --budget-seconds 300 --output optuna_results_500 --study-name run-004a-500 && \
python optuna_search.py --dataset dataset_pybamm_3k --n-trials 200 --budget-seconds 300 --output optuna_results_3k --study-name run-004b-3k
```

## Expected Results

**Run 004a vs Run 002 (500 samples):**
- Run 002 (LLM): 0.6528 → 0.4676 (28.4% improvement)
- Run 004a (Optuna): 0.6528 → likely ~0.50-0.55 (better hyperparams but no feature engineering)
- LLM wins because it discovered Bruggeman features and dead feature zeroing that compensate for data scarcity

**Run 004b vs Run 003 (3000 samples):**
- Run 003 (LLM): 0.2958 → 0.2871 (2.95% improvement)
- Run 004b (Optuna): 0.2958 → likely ~0.28-0.29 (similar — both barely beat baseline)
- Near-tie because data quantity dominates and neither method finds much to improve

**The thesis figure:** Two-panel plot showing LLM vs Optuna optimization curves, one panel per dataset size. The gap narrows with more data.

## Verification

```bash
# Import check
python -c "import optuna; print(optuna.__version__)"

# Quick smoke test (5 trials, 30s budget)
python optuna_search.py --dataset dataset_pybamm --n-trials 5 --budget-seconds 30 --output optuna_smoke_test

# Verify output format
ls optuna_smoke_test/
cat optuna_smoke_test/best_params.json | python -m json.tool
head -3 optuna_smoke_test/results.tsv

# Clean up smoke test
rm -rf optuna_smoke_test

# Full regression
pytest --tb=short -q

# Ruff
ruff check experiments/ml/autoresearch/optuna_search.py
```

## Important Notes

- **Fair comparison requires identical features.** The whole point is that Optuna gets 11 raw features while the LLM can invent new ones. If Optuna also got the Bruggeman feature, it wouldn't be a fair comparison.
- **Optuna's TPE sampler is the default and correct choice.** Don't use random or grid search — TPE is what a competent practitioner would use.
- **Pruning makes Optuna faster per-trial.** This is fair — speed is part of Optuna's value proposition. The comparison is on total budget (200 trials × 300s max each), not wall-clock time.
- **The results.tsv format must be compatible with the dashboard.** The Optimization Journey chart reads results.tsv — if the columns match, the dashboard works for Optuna runs too.
- **Optuna's SQLite study can be analyzed later** with `optuna.visualization` for the thesis (parameter importance plots, optimization history, parallel coordinate plots).
