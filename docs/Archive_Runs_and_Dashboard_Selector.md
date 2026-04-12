# Archive Autoresearch Runs + Dashboard Run Selector

## Context

FORGE's autoresearch system has completed two runs:
- **Run 001** (synthetic data, 200 experiments, 57.5% improvement) — on branch `autoresearch/run-001`
- **Run 002** (PyBaMM DFN 500 samples, 37 experiments, 28.4% improvement) — on branch `autoresearch/run-002-pybamm`

A third run is planned (PyBaMM DFN 2000 samples). The runs need to be archived into a persistent directory structure and the ML dashboard needs a dropdown to switch between them.

**Work on the `main` branch.** The run artifacts need to be collected from their respective branches and committed to main.

## Pre-Check — READ THESE FILES FIRST

1. **`forge/gui/pages/5_ML_Autoresearch.py`** — Current ML dashboard page. Read the complete file to understand:
   - How it loads `results.tsv`
   - How Tab 1 (Optimization Journey) renders the score trajectory, leaderboard, and stats
   - How Tab 2 (Best Model) renders metrics and plots
   - How Tab 3 (Surrogate Playground) works with the checkpoint
   - What path(s) are currently hardcoded

2. **`experiments/ml/autoresearch/`** — Current workspace layout. Check what artifacts exist on the current branch.

3. **Check both run branches for artifacts:**
   ```bash
   # Run 001
   git show autoresearch/run-001:experiments/ml/autoresearch/results.tsv | head -5
   git show autoresearch/run-001:experiments/ml/autoresearch/surrogate.py | head -30

   # Run 002
   git show autoresearch/run-002-pybamm:experiments/ml/autoresearch/results.tsv | head -5
   git show autoresearch/run-002-pybamm:experiments/ml/autoresearch/surrogate.py | head -30
   ```
   
   Identify what artifacts exist on each branch: `results.tsv`, `surrogate.py` (best version), `checkpoint.pt`, any `memory/` files.

## What to Build

### Part 1: Create Run Archive Structure

Create the directory structure and populate it with frozen artifacts from each run.

```
experiments/ml/autoresearch/runs/
├── run-001-synthetic/
│   ├── results.tsv              ← from autoresearch/run-001 branch
│   ├── surrogate.py             ← best (final accepted) version from that branch
│   ├── checkpoint.pt            ← if it exists on disk or branch (30-member ensemble)
│   └── run_config.json          ← see below
├── run-002-pybamm-500/
│   ├── results.tsv              ← from autoresearch/run-002-pybamm branch
│   ├── surrogate.py             ← best (final accepted) version from that branch
│   ├── checkpoint.pt            ← if available
│   └── run_config.json          ← see below
└── README.md                    ← documents the structure
```

**Extract artifacts from branches using `git show`:**
```bash
# Run 001
git show autoresearch/run-001:experiments/ml/autoresearch/results.tsv > experiments/ml/autoresearch/runs/run-001-synthetic/results.tsv
git show autoresearch/run-001:experiments/ml/autoresearch/surrogate.py > experiments/ml/autoresearch/runs/run-001-synthetic/surrogate.py

# Run 002
git show autoresearch/run-002-pybamm:experiments/ml/autoresearch/results.tsv > experiments/ml/autoresearch/runs/run-002-pybamm-500/results.tsv
git show autoresearch/run-002-pybamm:experiments/ml/autoresearch/surrogate.py > experiments/ml/autoresearch/runs/run-002-pybamm-500/surrogate.py
```

For `checkpoint.pt` — check if it exists on disk at `experiments/ml/autoresearch/checkpoint.pt`. If so, copy it to the appropriate run directory. If it only exists for Run 001, only archive it there.

**Create `run_config.json` for each run:**

Run 001:
```json
{
  "run_id": "run-001-synthetic",
  "display_name": "Run 001 — Synthetic (2000 samples)",
  "dataset": "synthetic proxy formulas",
  "dataset_samples": 2000,
  "training_samples": 1400,
  "model_type": "DFN proxy (analytical formulas)",
  "parameter_set": "N/A (synthetic)",
  "cell_format": "4680 cylindrical",
  "experiments_attempted": 200,
  "experiments_accepted": 36,
  "baseline_score": 0.3351,
  "best_score": 0.1517,
  "improvement_pct": 57.5,
  "best_experiment": 184,
  "branch": "autoresearch/run-001",
  "date": "2026-03-20",
  "duration_hours": 18,
  "key_findings": [
    "Physics-informed features (Bruggeman tortuosity) discovered autonomously",
    "BatchNorm + skip connections accepted",
    "30-member ensemble as final architecture",
    "57.5% improvement from baseline"
  ]
}
```

Run 002:
```json
{
  "run_id": "run-002-pybamm-500",
  "display_name": "Run 002 — PyBaMM DFN (500 samples)",
  "dataset": "PyBaMM DFN simulations (Chen2020)",
  "dataset_samples": 496,
  "training_samples": 347,
  "model_type": "PyBaMM DFN with lumped thermal",
  "parameter_set": "Chen2020 (NMC532/Graphite)",
  "cell_format": "4680 cylindrical",
  "experiments_attempted": 37,
  "experiments_accepted": 6,
  "baseline_score": 0.6528,
  "best_score": 0.4676,
  "improvement_pct": 28.4,
  "best_experiment": 26,
  "branch": "autoresearch/run-002-pybamm",
  "date": "2026-03-24",
  "duration_hours": 2.5,
  "key_findings": [
    "Bruggeman feature (et/por^1.5) transfers from synthetic to real data",
    "n_tabs and tab_width independently confirmed as dead features (ST=0 in Sobol)",
    "Rate-temp tradeoff severe — DFN physics harder than synthetic",
    "Converged at exp 37 — data-limited, not architecture-limited",
    "Huber loss + AdamW accepted, BatchNorm/skip/ensemble all rejected (overfitting on 347 samples)"
  ]
}
```

**Create `experiments/ml/autoresearch/runs/README.md`:**
```markdown
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
```

### Part 2: Update Dashboard with Run Selector

Modify `forge/gui/pages/5_ML_Autoresearch.py` to add a run selector dropdown.

**Key changes:**

1. **Discover available runs** by scanning `experiments/ml/autoresearch/runs/` for subdirectories that contain `run_config.json`:
   ```python
   import json
   from pathlib import Path

   RUNS_DIR = Path("experiments/ml/autoresearch/runs")

   def discover_runs() -> list[dict]:
       """Scan runs/ directory for completed autoresearch runs."""
       runs = []
       if not RUNS_DIR.exists():
           return runs
       for run_dir in sorted(RUNS_DIR.iterdir()):
           config_path = run_dir / "run_config.json"
           if config_path.exists():
               config = json.loads(config_path.read_text())
               config["_path"] = str(run_dir)
               runs.append(config)
       return runs
   ```

2. **Add a selectbox at the top of the page** (above the tabs):
   ```python
   runs = discover_runs()
   if not runs:
       st.info("No autoresearch runs found. Run the autoresearch loop to generate results.")
       st.stop()

   run_names = [r["display_name"] for r in runs]
   selected_idx = st.selectbox("Select Run", range(len(run_names)), format_func=lambda i: run_names[i])
   selected_run = runs[selected_idx]
   run_path = Path(selected_run["_path"])
   ```

3. **Show a run summary card** below the selector:
   ```python
   col1, col2, col3, col4 = st.columns(4)
   col1.metric("Dataset", selected_run["dataset_samples"])
   col2.metric("Experiments", f"{selected_run['experiments_accepted']}/{selected_run['experiments_attempted']}")
   col3.metric("Best Score", f"{selected_run['best_score']:.4f}")
   col4.metric("Improvement", f"{selected_run['improvement_pct']:.1f}%")
   ```

4. **Update all data loading** to use `run_path` instead of the hardcoded path:
   - `results.tsv` → `run_path / "results.tsv"`
   - `checkpoint.pt` → `run_path / "checkpoint.pt"`
   - Any other path references

5. **Tab 1 (Optimization Journey)** — works as before, just reads from `run_path / "results.tsv"`. No changes to chart logic.

6. **Tab 2 (Best Model)** — works as before. The metrics come from `results.tsv` (the best experiment row) and `run_config.json` (for metadata like dataset, parameter set).

7. **Tab 3 (Surrogate Playground)** — loads checkpoint from `run_path / "checkpoint.pt"`. If the checkpoint doesn't exist for the selected run, show info banner: "No saved checkpoint for this run."

8. **Add key findings** from `run_config.json` as an expandable section:
   ```python
   with st.expander("Key Findings"):
       for finding in selected_run.get("key_findings", []):
           st.markdown(f"- {finding}")
   ```

### Part 3: Update .gitignore

Add to `experiments/ml/autoresearch/.gitignore`:
```
# Run artifacts are explicitly committed (not generated)
# But checkpoint.pt files are large — track with git-lfs or exclude
runs/*/checkpoint.pt
```

**Note on checkpoint.pt:** These are ~1.2MB each. For a Git repo, that's fine to commit directly (not large enough to need git-lfs). But if you prefer to keep them out of Git, exclude them and note they must be generated locally. **Decision: commit checkpoint.pt files if they're under 5MB. Exclude if larger.**

Check the size:
```bash
ls -lh experiments/ml/autoresearch/checkpoint.pt 2>/dev/null
```

If under 5MB, track it. If over, gitignore it and add a note in README.md about regeneration.

## Constraints

- **Work on `main` branch.** The run artifacts are extracted from feature branches via `git show`.
- **Do NOT modify anything on the feature branches.** They are historical records.
- **Do NOT delete or modify existing experiment files** in `experiments/ml/autoresearch/` (prepare.py, surrogate.py, etc.). The runs/ directory is additive.
- **The dashboard must still work if runs/ is empty** — show the info banner.
- **Follow existing Streamlit code style** from the current Page 5 implementation.
- **Ruff-clean, mypy-compatible.**

## Verification

```bash
# Verify run archive structure
ls -la experiments/ml/autoresearch/runs/run-001-synthetic/
ls -la experiments/ml/autoresearch/runs/run-002-pybamm-500/
cat experiments/ml/autoresearch/runs/run-001-synthetic/run_config.json | python -m json.tool
cat experiments/ml/autoresearch/runs/run-002-pybamm-500/run_config.json | python -m json.tool

# Verify results.tsv extracted correctly
head -3 experiments/ml/autoresearch/runs/run-001-synthetic/results.tsv
head -3 experiments/ml/autoresearch/runs/run-002-pybamm-500/results.tsv

# Verify dashboard runs
streamlit run forge/gui/app.py
# → Navigate to ML Autoresearch page
# → Verify dropdown shows both runs
# → Switch between runs, verify charts update
# → Check Tab 3 playground loads correct checkpoint (or shows info banner)

# Full regression
pytest --tb=short -q

# Ruff
ruff check forge/gui/pages/5_ML_Autoresearch.py
```
