# Surrogate Playground — Implementation Plan

## Working Directory

```
~/Projects/CmdrFALCO/FORGE/
```

---

## Key Decision: Torch in Docker

The Docker image only installs `forge[gui]` which excludes torch. For the PoC, install **CPU-only torch** (~170MB) in the Dockerfile. Real-time inference through the actual ensemble is far more impressive than static interpolation.

---

## Critical Instructions

### Which surrogate.py to use

The best model is from **experiment 184** on branch `autoresearch/run-001` (commit `c19c661`). This version has:
- `HIDDEN_SIZE = 80`
- `BATCH_SIZE = 32`
- `ENSEMBLE_SIZE = 30`
- `LEARNING_RATE = 5e-3`
- `WEIGHT_DECAY = 1e-4`
- `ACTIVATION = gelu`

Do NOT use the current HEAD of `autoresearch/run-001` — that's the convergence commit (experiment 200) which just records the stop, not a code change. Checkout `c19c661` to get the right surrogate.

### Training budget

Use `--budget-seconds 300` (5 minutes). This is the final checkpoint — it should be the best quality we can get. Do NOT use 90s.

### Dataset

The dataset already exists at `experiments/ml/autoresearch/dataset/`. Do NOT run `prepare.py`. Contents:
- `train.npz`, `val.npz`, `test.npz`
- `metadata.json` — contains feature names, physical ranges, normalization stats

### Checkpoint path

Save to: `experiments/ml/autoresearch/checkpoint.pt`

This path is already volume-mounted into the Docker container via:
```yaml
- ./experiments/ml/autoresearch:/app/experiments/ml/autoresearch:ro
```

### Do NOT commit checkpoint.pt to git

It's a binary blob (~1.5MB). Add `experiments/ml/autoresearch/checkpoint.pt` to `.gitignore`. It lives on the host filesystem and reaches Docker via the volume mount (same pattern as `results.tsv`).

### Branch workflow

1. Steps 1-2: work on `autoresearch/run-001`
2. Switch to `main` for Steps 3-4
3. Copy `forge/ml/surrogate_inference.py` to `main` — don't cherry-pick

### Lint before committing

CI failed last time on ruff lint. Run `ruff check .` before every commit. Fix any issues.

### No Claude references in commit messages

Do not include "Co-Authored-By: Claude" or any mention of Claude/AI in commit messages.

---

## Pre-Read — Do First

Before writing any code, read these files to understand the full picture:

1. **The surrogate script** (the model you're saving):
   ```
   experiments/ml/autoresearch/surrogate.py
   ```
   Pay special attention to `_add_features()` — this is the feature engineering that must be reproduced exactly in the inference module.

2. **The dataset metadata** (feature names, ranges):
   ```
   experiments/ml/autoresearch/dataset/metadata.json
   ```

3. **The current dashboard page** (Tab 3 placeholder you're replacing):
   ```
   forge/gui/pages/5_ML_Autoresearch.py
   ```

4. **The Dockerfile** (to understand the current build):
   ```
   Dockerfile
   ```

5. **docker-compose.yml** (to verify volume mounts):
   ```
   docker-compose.yml
   ```

---

## Step 1 — Checkpoint Saving (`surrogate.py`)

Add `--save-checkpoint <path>` optional CLI argument to `_build_parser()`.

After training completes, if `--save-checkpoint` is provided, save a dict containing:
- `ensemble_state_dicts`: list of all best_state dicts (one per ensemble member)
- `hyperparameters`: dict with hidden_size, ensemble_size, input_dim, activation, num_layers
- `normalization`: dict with x_mean, x_std (input normalization) AND y_mean, y_std (target denormalization)
- `feature_config`: dict describing the feature engineering (zeroed columns, engineered features)
- `metadata`: the full metadata.json contents (feature names, physical ranges)

**Implementation details:**
- Create `all_best_states: list[dict] = []` before the ensemble training loop
- After each member's `model.load_state_dict(best_state)`, append `best_state` to `all_best_states`
- After metrics printing, if `args.save_checkpoint` is set, build the checkpoint dict and `torch.save()`
- This does NOT change behavior when `--save-checkpoint` is not passed (autoresearch engine is unaffected)

**IMPORTANT:** Targets ARE normalized in the training code:
```python
y_mean = y_train.mean(axis=0, keepdims=True)
y_std = y_train.std(axis=0, keepdims=True)
y_train_n = (y_train - y_mean) / y_std
```
The checkpoint must also save `y_mean` and `y_std`. The inference module must denormalize after the forward pass: `pred = pred_normalized * y_std + y_mean`. Without this, predictions will be in normalized space — completely wrong values.

### Train and produce checkpoint

After modifying surrogate.py, run:
```bash
cd ~/Projects/CmdrFALCO/FORGE
.venv311/bin/python experiments/ml/autoresearch/surrogate.py \
    --dataset experiments/ml/autoresearch/dataset \
    --seed 42 \
    --budget-seconds 300 \
    --save-checkpoint experiments/ml/autoresearch/checkpoint.pt
```

Verify the checkpoint was saved:
```bash
ls -lh experiments/ml/autoresearch/checkpoint.pt
```

---

## Step 2 — Inference Module (`forge/ml/surrogate_inference.py`)

**New file** in the `forge` package (NOT in `forge/ml/autoresearch/` — that's the engine code we don't modify).

### Class: `SurrogatePredictor`

```python
class SurrogatePredictor:
    def __init__(self, checkpoint_path: str | Path):
        """Load checkpoint, reconstruct ensemble on CPU."""
        ...

    def predict(self, inputs: dict[str, float]) -> dict[str, tuple[float, float]]:
        """Predict from physical inputs.

        Args:
            inputs: e.g. {"electrode_thickness": 120.0, "porosity": 0.35, ...}

        Returns:
            {"rate": (mean, std), "temp": (mean, std)}
        """
        ...

    def sensitivity(self, base_inputs: dict[str, float], feature: str, n_points: int = 50) -> dict:
        """Sweep one feature to measure output sensitivity."""
        ...

    @property
    def feature_ranges(self) -> dict[str, tuple[float, float]]:
        """Physical ranges for each input feature (for slider bounds)."""
        ...
```

### Internal flow of `predict()`:
1. Build raw feature vector (11 values) from the input dict using `metadata["feature_names"]` ordering
2. Zero out `can_inner_diameter` (column index from checkpoint config) — matching training
3. Apply `_add_features()` — **must reproduce the exact same feature engineering as surrogate.py**
4. Normalize: `(x - x_mean) / x_std`
5. Run through all ensemble members in `eval()` mode
6. Collect predictions, compute mean and std across ensemble members
7. Denormalize outputs: `pred = pred_normalized * y_std + y_mean`
8. Return predictions in physical units

### Critical: Feature engineering must match exactly

The `_add_features()` function in `surrogate.py` computes engineered features. The inference module must do the exact same transformations in the exact same order. Read `surrogate.py` carefully and reproduce it. Any mismatch means wrong predictions.

### Testing the inference module

```bash
.venv311/bin/python -c "
from forge.ml.surrogate_inference import SurrogatePredictor
p = SurrogatePredictor('experiments/ml/autoresearch/checkpoint.pt')
print('Features:', list(p.feature_ranges.keys()))
result = p.predict({k: (v[0]+v[1])/2 for k, v in p.feature_ranges.items()})
print('Predictions:', result)
"
```

---

## Step 3 — Playground UI (Tab 3 of dashboard)

**File:** `forge/gui/pages/5_ML_Autoresearch.py`

Replace the placeholder in `with tab_playground:` (currently lines ~243-248).

### Layout

```
[Left Column: Sliders]              [Right Column: Predictions]
electrode_thickness  [====|====]    Rate Capability: 0.72 ± 0.03
porosity            [==|======]     Max Temperature: 68.4 ± 1.2°C
separator_thickness [====|====]
n_tabs              [==|======]     [Sensitivity Chart]
...                                 (horizontal bar: which input matters most)
```

### Implementation

1. **Import guard:** At module level, try importing `SurrogatePredictor`. Set a flag if torch is unavailable.
2. **Checkpoint check:** In `tab_playground`, check if checkpoint exists AND torch is available. Show graceful fallback message if either is missing.
3. **Load predictor:** Use `@st.cache_resource` to load once:
   ```python
   @st.cache_resource
   def _load_predictor():
       return SurrogatePredictor(CHECKPOINT_PATH)
   ```
4. **Sliders:** Two columns. Left column has sliders for each input feature. Use `predictor.feature_ranges` for min/max/default values. Skip `can_inner_diameter` (it's zeroed). Default slider values: midpoint of each range.
5. **Predictions:** Right column shows `st.metric()` for each output. Use ensemble std as the delta field (±uncertainty).
6. **Sensitivity chart:** For each feature, perturb by ±1% of range and measure output change. Display as horizontal Plotly bar chart. Use the same dark theme settings as Tab 1.

### Styling
- Dark theme: `plotly_dark` template, transparent background
- Green accent `#4ade80` for positive sensitivity, red `#f87171` for negative
- No custom CSS unless necessary

---

## Step 4 — Docker Integration

### Dockerfile

After the main `pip install -e ".[gui]"` line, add CPU-only torch:
```dockerfile
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
```

This installs ~170MB CPU-only torch. Do NOT install the full CUDA version.

### docker-compose.yml

No changes needed. The existing volume mount covers the checkpoint:
```yaml
- ./experiments/ml/autoresearch:/app/experiments/ml/autoresearch:ro
```

### Rebuild and verify

```bash
docker compose up -d --build streamlit
docker compose exec streamlit python -c "
from forge.ml.surrogate_inference import SurrogatePredictor
p = SurrogatePredictor('experiments/ml/autoresearch/checkpoint.pt')
print('Loaded OK, features:', len(p.feature_ranges))
"
```

Then check `/app/ML_Autoresearch` → Surrogate Playground tab in the browser.

---

## Testing — Full Loop Before Docker

Before touching Docker, verify locally with the `.venv311` environment:

```bash
cd ~/Projects/CmdrFALCO/FORGE
.venv311/bin/streamlit run forge/gui/app.py &
sleep 5
# Open http://localhost:8501/app/ML_Autoresearch and check Tab 3
```

Verify:
- Sliders appear with correct physical ranges
- Moving a slider updates predictions in real-time
- Sensitivity chart renders
- No errors in the terminal

---

## File Changes Summary

| File | Action | Branch |
|------|--------|--------|
| `experiments/ml/autoresearch/surrogate.py` | Add `--save-checkpoint`, accumulate state_dicts | `autoresearch/run-001` |
| `forge/ml/surrogate_inference.py` | **New** — SurrogatePredictor class | `main` |
| `forge/gui/pages/5_ML_Autoresearch.py` | Replace Tab 3 placeholder with interactive UI | `main` |
| `Dockerfile` | Add CPU-only torch pip install | `main` |
| `.gitignore` | Add `experiments/ml/autoresearch/checkpoint.pt` | `main` |

---

## Architecture Notes

- Best model: experiment 184, ensemble of 30 MLPs (2-layer, HIDDEN_SIZE=80, BatchNorm, skip connections)
- 22 input features: 11 raw + 11 engineered (interactions, log transforms, Bruggeman physics)
- 2 output targets: discharge rate proxy, max temperature proxy
- ~12K parameters per model, ~360K total ensemble
- Inference: <5ms for full ensemble on CPU
- Ensemble std provides free uncertainty estimates

## Risk: BatchNorm on single samples

The model uses `BatchNorm1d`. Single-sample inference works fine in `eval()` mode (uses running stats, not batch stats). The inference module must call `model.eval()` — this is standard.

---

## Do NOT

- Modify `forge/ml/autoresearch/` (the engine code)
- Commit `checkpoint.pt` or `results.tsv` to git
- Install full CUDA torch in Docker
- Use fake/demo data in the playground
- Add `st.set_page_config()` to the page file
- Skip the local test before Docker rebuild
