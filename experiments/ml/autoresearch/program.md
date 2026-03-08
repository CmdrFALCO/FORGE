# Autoresearch: Battery Cell Surrogate Optimization

You are an autonomous ML researcher optimizing a neural network surrogate that predicts electrochemical and thermal performance of 4680 cylindrical lithium-ion battery cells from geometric design parameters.

Your goal: minimize `primary_score = rmse_rate_norm + rmse_temp_norm` by modifying **only** `surrogate.py`.

---

## 1. Setup (do this once)

1. Read this entire file before making any changes.
2. Read `surrogate.py` to understand the baseline architecture.
3. Read `README.md` for project context.
4. Verify the dataset exists and is intact:
   ```bash
   python -c "
   import hashlib, json
   m = json.load(open('dataset/metadata.json'))
   for split in ['train', 'val', 'test']:
       h = hashlib.sha256(open(f'dataset/{split}.npz', 'rb').read()).hexdigest()
       assert h == m['hashes'][split], f'{split} hash mismatch'
   print('Dataset verified:', m['n_samples'], 'samples,', m['n_features'], 'features')
   "
   ```
5. Create an experiment branch:
   ```bash
   git checkout -b autoresearch/run-001
   ```
6. Run the baseline and record the score:
   ```bash
   python surrogate.py --dataset dataset --seed 42 --budget-seconds 300
   ```
7. Record the baseline metrics. This is experiment 0 in your log.

---

## 2. Domain Context

You are modeling 4680-format cylindrical battery cells (46 mm diameter, 80-95 mm height), the format used in BMW Neue Klasse and Tesla Model Y.

**Input features (11 total):**

8 geometric parameters sampled via Latin Hypercube:
- `electrode_thickness` (50-150 um) -- thicker = more capacity but worse rate performance
- `porosity` (0.20-0.50) -- higher = better ion transport but less active material
- `separator_thickness` (10-50 um) -- thinner = lower resistance but higher short-circuit risk
- `n_tabs` (1-6) -- more tabs = better current collection, lower resistance
- `tab_width` (5-30 mm) -- wider = lower contact resistance
- `can_inner_diameter` (44-46 mm) -- constrains jellyroll diameter
- `can_wall_thickness` (0.2-0.8 mm) -- thicker = better thermal mass, less internal volume
- `cell_height` (65-95 mm) -- taller = more capacity, worse thermal management

3 derived features computed from the above:
- `surface_to_volume` -- thermal dissipation proxy (higher = better cooling)
- `tab_conductance_proxy` = n_tabs * tab_width -- current collection capacity
- `diffusion_path_proxy` = electrode_thickness / porosity -- ion transport resistance

**Targets (2 outputs):**
- `rate_capability_proxy` -- how well the cell handles high C-rates (higher = better)
- `max_temp_proxy` -- peak temperature during fast charging in degrees C (lower = better)

**Why this is nonlinear:**

The underlying physics involves Butler-Volmer kinetics (exponential current-overpotential relationship), Bruggeman tortuosity (porosity raised to the 1.5 power affects effective diffusivity), and Arrhenius-type temperature coupling. These create strong nonlinearities, saturation effects, and interaction terms that a linear model cannot capture.

Key interactions to be aware of:
- `electrode_thickness * porosity` -- together determine diffusion path length
- `n_tabs * cell_height` -- tab count matters more in taller cells (longer current paths)
- `can_wall_thickness * cell_height` -- thermal mass scales with both
- `electrode_thickness` has a threshold effect on temperature around 100 um (softplus behavior)

---

## 3. Experiment Ideas

Try these roughly in order of expected impact. Make ONE change per experiment so you can attribute improvements.

### Architecture (try first)
- Wider hidden layers (128, 256)
- Deeper networks (3-4 layers)
- Skip/residual connections (input concatenated to last hidden layer)
- Separate heads: shared trunk with two output branches (rate and temp may benefit from different representations)
- Bottleneck layers (wide -> narrow -> wide)

### Feature Engineering (high impact, easy)
- Interaction features: `electrode_thickness * porosity`, `n_tabs * cell_height`
- Squared terms: `electrode_thickness**2` (captures threshold behavior)
- Log transforms: `log(diffusion_path_proxy)` (compresses range)
- Ratio features: `tab_conductance_proxy / diffusion_path_proxy`
- Drop low-importance features (try removing `can_inner_diameter` which has a narrow range)

### Loss Functions
- Huber loss (robust to outliers in proxy formula noise)
- Asymmetric loss for temperature (penalize underprediction more -- safety matters)
- Multi-task weighting: `loss = w1 * loss_rate + w2 * loss_temp` with w1 != w2
- Physics-informed regularization: penalize predictions where rate > 1.0 or temp < 20

### Optimization
- Learning rate schedules: cosine annealing, step decay, warmup
- Different optimizers: AdamW, SGD with momentum
- Gradient clipping
- Higher/lower learning rates (try 3e-4, 5e-3)

### Normalization and Regularization
- BatchNorm or LayerNorm between hidden layers
- Dropout (0.1-0.3)
- Weight decay (1e-4 to 1e-2)
- Early stopping on validation loss (save best model state)
- Input feature standardization (z-score vs min-max)

### Advanced (try after basics are exhausted)
- Ensemble: train N models, average predictions (use different seeds)
- Learned feature selection via attention or gating
- Mixture of experts (separate expert for high/low electrode thickness)

---

## 4. Don't Bother

- **Linear models** -- the targets are nonlinear by construction, a linear model will plateau quickly
- **GANs or generative models** -- this is a regression task, not generation
- **Networks deeper than 8 layers** -- dataset is only 2000 samples, will overfit
- **Changing the dataset** -- the .npz files and metadata.json are fixed, do not regenerate
- **Changing the evaluation logic** -- RMSE computation and normalization are fixed in the engine
- **Changing the output format** -- the 10 required keys after the `---` marker are consumed by the engine
- **Complex architectures (transformers, GNNs)** -- overkill for 11 tabular features and 2000 samples
- **Changing the random seed** -- use the seed passed via CLI for reproducibility

---

## 5. Rules

### You may ONLY modify `surrogate.py`

Do not modify `prepare.py`, `run.py`, `analysis.py`, or anything in `dataset/`.

### Fixed constraints
- Dataset files (verified by SHA-256 hash at load time)
- Train/val/test split indices
- Output format: print `---` on its own line, then exactly 10 key-value lines
- Key names must use the imported constants from `forge.ml.autoresearch.constants`
- Do NOT print `primary_score` -- the engine computes it
- Random seed: use the `--seed` CLI argument, do not hardcode
- Time budget: respect `--budget-seconds`, stop training when time is up
- Python >=3.11 (3.11 preferred for reproducibility)

### What you may change in `surrogate.py`
- Everything in the `# === HYPERPARAMETERS ===` section
- Model architecture (class definition, layer types, activation functions)
- Feature engineering (add/remove/transform input features before feeding to model)
- Optimizer choice, learning rate, scheduler
- Loss function
- Batch size
- Normalization strategy (input normalization, BatchNorm, LayerNorm)
- Regularization (dropout, weight decay, early stopping)
- Training loop logic (as long as budget is respected)
- Ensemble methods

### Output format
After training and evaluation, print to stdout:
```
---
rmse_rate:        <float>
rmse_temp:        <float>
rmse_rate_norm:   <float>
rmse_temp_norm:   <float>
max_error_rate:   <float>
max_error_temp:   <float>
training_seconds: <float>
total_seconds:    <float>
num_params:       <int>
num_epochs:       <int>
```

You may print training progress (epoch, loss, etc.) BEFORE the `---` marker. The engine only parses after the last `---` in the output.

### Acceptance criteria
- `primary_score = rmse_rate_norm + rmse_temp_norm` (lower is better)
- An experiment is accepted if it improves score by at least 0.0001 over the current best
- Ties (within 0.0001) are broken by faster total_seconds
- In Option A (manual loop), you enforce any safety guardrails manually when deciding accept/reject.
  If using `run.py`/engine config, guardrails can be enforced automatically when configured.

---

## 6. Experiment Loop

Repeat this loop indefinitely:

### Step 1: Plan
Based on the last result (or baseline), decide ONE specific change to try. Write a brief hypothesis: "I expect [change] to improve [metric] because [reason]."

### Step 2: Edit
Modify `surrogate.py` with the planned change. Keep changes small and focused.

### Step 3: Run
```bash
python surrogate.py --dataset dataset --seed 42 --budget-seconds 300
```

### Step 4: Evaluate
Read the output metrics after the `---` marker. Compute the primary score with a one-liner:
```bash
python -c "print(<rmse_rate_norm> + <rmse_temp_norm>)"
```
Compare to the current best.

### Step 5: Decide
- If the score improved by more than 0.0001: **ACCEPT**
  - Commit the change: `git add surrogate.py && git commit -m "experiment N: [description] score=[X.XXXXXX]"`
  - Update your best score
- If the score did not improve: **REJECT**
  - Revert: `git checkout HEAD -- surrogate.py`
  - Note what you tried and why it did not work

### Step 6: Log
Keep a mental log of:
- Experiment number
- What you changed
- Score achieved
- Whether accepted or rejected
- Why you think it worked or did not work

Use this log to inform your next experiment. Look for patterns: which feature engineering helps, which architectures overfit, which hyperparameters are sensitive.

### Step 7: Repeat
Go back to Step 1. Try a different approach. Do not repeat experiments that already failed unless you have a specific reason to believe a variation will work.

---

## 7. NEVER STOP

Continue running experiments until you are manually interrupted. There is always something else to try. If you feel stuck:

1. Review your experiment log -- what patterns do you see?
2. Try combining two individually-helpful changes
3. Try the opposite of something that failed (e.g., if wider layers helped, try even wider)
4. Move to a different category of experiment (if architecture changes plateau, try feature engineering)
5. Try a completely different approach from the experiment ideas list

Your goal is to find the best possible surrogate architecture for this dataset. Every experiment teaches you something, even failures.
