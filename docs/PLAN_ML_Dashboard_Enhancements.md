# ML Dashboard Enhancements — Implementation Plan

## Working Directory

```
~/Projects/CmdrFALCO/FORGE/
```

## Branch

All work on `main`. No branch switching needed.

---

## Overview

Five enhancements to the ML Autoresearch dashboard, all visualization-only (no new training). The model checkpoint and test set already exist. Estimated total: ~1.5h.

| # | Enhancement | Where | Effort |
|---|------------|-------|--------|
| 1 | Prediction vs Actual plots | Tab 2 (Best Model) | ~15 min |
| 2 | Model comparison (XGBoost) | Tab 1 or new section | ~30 min |
| 3 | Hyperparameter landscape | Tab 1 (Optimization Journey) | ~20 min |
| 4 | Pareto front | Tab 1 (Optimization Journey) | ~15 min |
| 5 | Uncertainty calibration | Tab 2 (Best Model) | ~15 min |

---

## Pre-Read — Do First

1. **The inference module** (already exists):
   ```
   forge/ml/surrogate_inference.py
   ```
   Key API:
   - `SurrogatePredictor(checkpoint_path)` — loads ensemble
   - `.predict(inputs)` → `{"rate": (mean, std), "temp": (mean, std)}`
   - `.sensitivity(base_inputs, feature, n_points)` → sweep arrays

2. **The dashboard page** (modify this file):
   ```
   forge/gui/pages/5_ML_Autoresearch.py
   ```

3. **The dataset** (for pred vs actual, uncertainty calibration):
   ```
   experiments/ml/autoresearch/dataset/test.npz   — 300 test samples
   experiments/ml/autoresearch/dataset/metadata.json
   ```

4. **The results TSV** (for Pareto front, hyperparameter landscape):
   ```
   experiments/ml/autoresearch/results.tsv
   ```
   Columns: `experiment_id`, `primary_score`, `rmse_rate_norm`, `rmse_temp_norm`, `num_params`, `training_seconds`, `reason`, etc.

5. **The surrogate script** (for understanding the model):
   ```
   experiments/ml/autoresearch/surrogate.py
   ```

---

## Enhancement 1 — Prediction vs Actual Plots

### What

Two scatter plots (one per target) showing predicted vs actual values on the test set. A diagonal line shows perfect prediction. Points should cluster around the line.

### Where

Add to **Tab 2 (Best Model)**, below the architecture descriptor.

### Implementation

1. **Add a method to `SurrogatePredictor`** to predict on a batch (the full test set):
   ```python
   def predict_batch(self, X_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
       """Predict on a batch of raw feature vectors.

       Args:
           X_raw: shape (n_samples, 11) — raw features before engineering

       Returns:
           (means, stds) — each shape (n_samples, 2)
       """
   ```
   This method should:
   - Zero out column 5 (can_inner_diameter)
   - Apply `_add_features()`
   - Normalize with x_mean/x_std
   - Run through all ensemble members
   - Denormalize with y_mean/y_std
   - Return mean and std across ensemble

2. **In the dashboard**, load the test set and run batch prediction:
   ```python
   test_data = np.load(TEST_PATH)
   X_test, y_test = test_data["X"], test_data["y"]
   means, stds = predictor.predict_batch(X_test)
   ```

3. **Create two Plotly scatter plots** side by side:
   - Left: Rate Capability (predicted vs actual)
   - Right: Max Temperature (predicted vs actual)
   - Add diagonal reference line (`y = x`)
   - Color points by prediction error or ensemble uncertainty
   - Use `plotly_dark` template, transparent background
   - Hover: show actual value, predicted value, error, uncertainty

4. **Add R² and RMSE metrics** above the plots as `st.metric()`.

### Data paths

```python
TEST_PATH = _repo_root() / "experiments" / "ml" / "autoresearch" / "dataset" / "test.npz"
```

The test.npz contains arrays named `X` and `y`:
- `X`: shape (300, 11) — raw features
- `y`: shape (300, 2) — targets [rate_capability_proxy, max_temp_proxy]

### Target names and units

From `metadata.json`:
- Target 0: `rate_capability_proxy` (dimensionless, ~0.3-1.0 range)
- Target 1: `max_temp_proxy` (°C, ~60-85 range)

---

## Enhancement 2 — Model Comparison (XGBoost vs MLP Ensemble)

### What

Train a simple XGBoost/sklearn model on the same dataset, evaluate on the test set, and show a comparison table: MLP ensemble vs tree model.

### Where

Add to **Tab 2 (Best Model)** as a "Model Comparison" section, or as a new sub-section in Tab 1.

### Implementation

1. **Add XGBoost or sklearn GradientBoosting to the dashboard page** (not a separate module). This is a demo comparison, not production code.

2. **Guard the import:**
   ```python
   try:
       from sklearn.ensemble import GradientBoostingRegressor
       SKLEARN_AVAILABLE = True
   except ImportError:
       SKLEARN_AVAILABLE = False
   ```

3. **Train two GBR models** (one per target) on the training set, evaluate on test:
   ```python
   @st.cache_resource
   def _train_gbr():
       train = np.load(TRAIN_PATH)
       test = np.load(TEST_PATH)
       # ... train GBR, return predictions
   ```

4. **Comparison table** showing:
   | Metric | MLP Ensemble (30) | Gradient Boosting |
   |--------|-------------------|-------------------|
   | RMSE (rate) | 0.0139 | ? |
   | RMSE (temp) | 0.511 | ? |
   | R² (rate) | ? | ? |
   | R² (temp) | ? | ? |
   | Parameters | 12,142 | N/A |
   | Inference (ms) | 4.2 | <1 |

5. **If sklearn is not available**, show `st.info("Install scikit-learn for model comparison")` and skip.

### Dependency

`scikit-learn` is NOT in `pyproject.toml` currently. Two options:
- **Option A**: Add `scikit-learn` to `[gui]` deps and Dockerfile. Simple.
- **Option B**: Use `sklearn` only when available, graceful fallback. No dep change.

**Recommend Option B** — keep it optional. The comparison is a bonus, not essential. If sklearn is not available in Docker, the section just doesn't show. On the local `.venv311` it should be available (came with torch/pybamm).

### Data paths

```python
TRAIN_PATH = _repo_root() / "experiments" / "ml" / "autoresearch" / "dataset" / "train.npz"
TEST_PATH = _repo_root() / "experiments" / "ml" / "autoresearch" / "dataset" / "test.npz"
```

---

## Enhancement 3 — Hyperparameter Landscape

### What

Visualize which hyperparameters were tried and how they affected performance. Parse the `reason` column in `results.tsv` to extract hyperparameter changes, then show a scatter/heatmap.

### Where

Add to **Tab 1 (Optimization Journey)**, below the leaderboard.

### Implementation

1. **Parse the `reason` column** for hyperparameter info. The `reason` field contains descriptions like:
   - `"GELU activation"`
   - `"hidden_size=96"`
   - `"ensemble of 5 models"`
   - `"LR=5e-3 ensemble=8"`
   - `"BatchNorm in skip net"`
   - `"add log_cond feature"`
   - `"target normalization"`
   - `"CUDA + ensemble=30"`

2. **Categorize experiments** into groups:
   - Architecture changes (GELU, BatchNorm, skip connection)
   - Feature engineering (log transforms, interactions, Bruggeman)
   - Hyperparameter tuning (hidden_size, LR, batch_size, ensemble_size)
   - Infrastructure (CUDA, target normalization)

3. **Create a grouped bar chart or timeline** showing:
   - X: experiment_id
   - Y: primary_score
   - Color: category (architecture / features / hyperparams / infra)
   - This replaces or augments the existing optimization journey chart

4. **Alternative: bubble chart** with:
   - X: experiment_id
   - Y: primary_score
   - Size: num_params
   - Color: category

### Data

All data comes from `results.tsv` which is already loaded as `df` in the dashboard.

### Categorization logic

Simple keyword matching on the `reason` column:
```python
def _categorize(reason: str) -> str:
    reason_lower = reason.lower()
    if any(k in reason_lower for k in ["log_", "feature", "bruggeman", "remove", "drop", "add "]):
        return "Feature Engineering"
    if any(k in reason_lower for k in ["ensemble", "hidden", "lr=", "batch", "learning"]):
        return "Hyperparameter Tuning"
    if any(k in reason_lower for k in ["gelu", "batchnorm", "skip", "activation"]):
        return "Architecture"
    if any(k in reason_lower for k in ["cuda", "target norm", "adamw"]):
        return "Training Strategy"
    return "Other"
```

---

## Enhancement 4 — Pareto Front

### What

Plot `rmse_rate_norm` vs `rmse_temp_norm` for all experiments. Highlight the Pareto-optimal experiments (those where no other experiment is better in both metrics). This shows the tradeoff between rate prediction and temperature prediction.

### Where

Add to **Tab 1 (Optimization Journey)**, as a second chart below the optimization curve.

### Implementation

1. **Extract the two RMSE columns** from the DataFrame:
   ```python
   rate_norm = df["rmse_rate_norm"]
   temp_norm = df["rmse_temp_norm"]
   ```

2. **Compute Pareto front:**
   ```python
   def _pareto_front(points: np.ndarray) -> np.ndarray:
       """Return mask of Pareto-optimal points (lower is better for both)."""
       is_pareto = np.ones(len(points), dtype=bool)
       for i, p in enumerate(points):
           if is_pareto[i]:
               is_pareto[is_pareto] = np.any(points[is_pareto] < p, axis=1) | np.all(points[is_pareto] == p, axis=1)
               is_pareto[i] = True
       return is_pareto
   ```

3. **Create Plotly scatter:**
   - All experiments as grey dots
   - Pareto-optimal experiments as green dots, connected by a line (the Pareto front)
   - Hover: experiment_id, reason, both RMSE values
   - Axis labels: "RMSE Rate (normalized)" and "RMSE Temp (normalized)"
   - Lower-left corner = better

4. **Handle missing data:** Some rows may have NaN for rmse columns (from fast reconstruction). Filter those out.

### Note

The `rmse_rate_norm` and `rmse_temp_norm` columns exist in results.tsv from the full reconstruction. They represent the re-run metrics with 90s budget, so they won't exactly match the commit message scores for ensemble experiments. That's fine — the relative positions should be correct.

---

## Enhancement 5 — Uncertainty Calibration

### What

Check if the ensemble's predicted uncertainty (std across 30 models) correlates with actual prediction error. If the model says "I'm uncertain about this point," does it actually predict it poorly? This is a trust/reliability visual that ties into FORGE's AXIOM trust narrative.

### Where

Add to **Tab 2 (Best Model)**, below the Prediction vs Actual plots.

### Implementation

1. **Run batch prediction on test set** (same as Enhancement 1 — reuse the cached result):
   ```python
   means, stds = predictor.predict_batch(X_test)
   ```

2. **Compute actual errors:**
   ```python
   errors = np.abs(means - y_test)  # shape (300, 2)
   ```

3. **Create two scatter plots** (one per target):
   - X: predicted uncertainty (ensemble std)
   - Y: actual absolute error
   - Add diagonal reference line
   - If points cluster near the diagonal, the model is well-calibrated
   - If points are above the line, the model is overconfident (underestimates uncertainty)
   - If points are below, the model is conservative (overestimates uncertainty)

4. **Add calibration metric:**
   - Compute Spearman correlation between predicted std and actual error
   - Display as `st.metric("Uncertainty Calibration (ρ)", f"{spearman_r:.3f}")`
   - A value near 1.0 means the uncertainty is well-calibrated

5. **Use `scipy.stats.spearmanr`** if available (it should be — comes with numpy/scipy). Guard with try/except if not.

### Interpretation text

Add a brief explanation below the chart:
```python
st.caption(
    "Points near the diagonal indicate well-calibrated uncertainty. "
    "The ensemble's disagreement (std across 30 models) should correlate "
    "with actual prediction error — higher uncertainty where the model struggles."
)
```

---

## File Changes Summary

| File | Action |
|------|--------|
| `forge/ml/surrogate_inference.py` | Add `predict_batch()` method |
| `forge/gui/pages/5_ML_Autoresearch.py` | Add all 5 enhancements to existing tabs |

Only 2 files modified. No new files, no new dependencies (sklearn is optional with graceful fallback).

---

## Styling

All new charts must match the existing dark theme:
- Template: `plotly_dark`
- Background: `paper_bgcolor='rgba(0,0,0,0)'`, `plot_bgcolor='rgba(0,0,0,0)'`
- Green accent: `#4ade80`
- Red accent: `#f87171`
- Blue accent: `#60a5fa` (for uncertainty/calibration)
- Height: 400-420px per chart
- Use `st.plotly_chart(fig, use_container_width=True)` for all charts

---

## Testing

After implementing all 5 enhancements:

1. **Lint:**
   ```bash
   ruff check forge/ml/surrogate_inference.py forge/gui/pages/5_ML_Autoresearch.py
   ```

2. **Local test:**
   ```bash
   .venv311/bin/streamlit run forge/gui/app.py
   ```
   Check all 3 tabs — verify no errors, all charts render, data looks reasonable.

3. **Docker test:**
   ```bash
   docker compose restart streamlit
   ```
   Check `/app/ML_Autoresearch` through the browser.

---

## Commit

Single commit on `main`:
```
feat(gui): add prediction plots, model comparison, Pareto front, and calibration to ML dashboard
```

No Claude references in commit message. Run `ruff check .` before committing.

---

## Do NOT

- Modify `forge/ml/autoresearch/` (the engine code)
- Modify `experiments/ml/autoresearch/surrogate.py`
- Add new required dependencies to `pyproject.toml` (sklearn is optional)
- Train new models outside of the dashboard's cached functions
- Add `st.set_page_config()` to the page file
- Commit `checkpoint.pt` or `results.tsv` to git
- Skip the local test before Docker restart

---

## Sequence

Execute in this order (dependencies between enhancements):

1. **Add `predict_batch()` to `surrogate_inference.py`** — needed by Enhancements 1, 2, and 5
2. **Enhancement 1 (Pred vs Actual)** — validates that batch prediction works
3. **Enhancement 5 (Uncertainty Calibration)** — reuses same batch prediction data
4. **Enhancement 4 (Pareto Front)** — pure DataFrame visualization, no inference needed
5. **Enhancement 3 (Hyperparameter Landscape)** — pure DataFrame visualization
6. **Enhancement 2 (Model Comparison)** — independent, can be last since it's optional

This order minimizes rework — batch prediction is built first, then reused.
