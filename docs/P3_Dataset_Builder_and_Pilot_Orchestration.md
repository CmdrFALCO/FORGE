# P3 — Dataset Builder + Pilot Orchestration

## Context

This is prompt 3 of 3 for the FORGE PyBaMM pilot. P1 built the translation layer and PyBaMM runner. P2 built the batch generator and Sobol screener. P3 builds the dataset assembly infrastructure and the pilot orchestration script that ties everything together.

**Dependencies:** P1 and P2 must be complete and verified before executing P3.

**End goal:** After P3, running `python prepare_pybamm.py` in the experiments directory generates a real physics-based dataset in the exact same format as the existing synthetic dataset, ready for the autoresearch loop.

## Pre-Check — READ THESE FILES FIRST

1. **`forge/ml/dataset/builder.py`** — `DatasetBuilder` and `DatasetLoader` ABCs. Read the interface contracts: `build(specs, results, representations, output_path)` and `load(dataset_path)`.

2. **`forge/ml/common/types.py`** — All ML dataclasses. Specifically `CellSpec`, `SimulationResult`, `SimulationConfig`, `DesignSpace`, `ParameterRange`.

3. **`experiments/ml/autoresearch/prepare.py`** — **THE CRITICAL REFERENCE.** This is the existing synthetic dataset generator. The output format of P3 must match EXACTLY:
   - `.npz` files: `train.npz`, `val.npz`, `test.npz` each containing arrays `X` (features) and `Y` (targets)
   - `metadata.json` with:
     - `feature_names`: list of column names for X
     - `target_names`: list of column names for Y
     - `target_stds`: dict of target name → standard deviation (for RMSE normalization)
     - `hashes`: dict of split name → SHA-256 hash of the .npz file
     - `n_samples`: dict of split name → sample count
     - `ranges`: dict of feature name → [min, max]
     - `split_ratio`: [0.7, 0.15, 0.15]
   - Read the exact key names, array shapes, and hash computation logic.

4. **`experiments/ml/autoresearch/surrogate.py`** — Read how it loads the dataset. This is what must work unchanged with the new data. Specifically check:
   - How it reads `X` and `Y` from `.npz`
   - How it uses `metadata.json` for normalization
   - Which feature columns it expects by index or name

5. **`forge/ml/simulation/geometry_translator.py`** (from P1) — Read `compute_derived_features()` and `get_design_space()`.

6. **`forge/ml/simulation/pybamm_runner.py`** (from P1) — Read `simulate()` return type and how targets are stored in `SimulationResult`.

7. **`forge/ml/batch/lhs_generator.py`** (from P2) — Read `generate()` and `generate_with_derived()`.

8. **`forge/ml/sensitivity/sobol_screener.py`** (from P2) — Read `screen()` and `rank_parameters()`.

## What to Build

### File 1: `forge/ml/dataset/npz_builder.py`

**Purpose:** Implement `DatasetBuilder` and `DatasetLoader` ABCs. Assembles simulation results into train/val/test `.npz` splits with `metadata.json`.

**Class: `NpzDatasetBuilder(DatasetBuilder)`**

**Method: `build(self, specs: list[CellSpec], results: list[SimulationResult], representations: list | None = None, output_path: Path | str = "dataset") -> Path`**

Implementation:

1. **Filter to successful simulations only:**
   ```python
   successful = [(spec, result) for spec, result in zip(specs, results) if result.success]
   failed_count = len(specs) - len(successful)
   if failed_count > 0:
       logger.warning(f"Dropped {failed_count}/{len(specs)} failed simulations")
   ```

2. **Assemble feature matrix X:**
   
   The feature columns must match the synthetic prepare.py exactly. Read prepare.py to determine the exact column order. The expected columns are the 8 geometric parameters + 3 derived features = 11 features total:
   ```
   electrode_thickness, porosity, separator_thickness, n_tabs, tab_width,
   can_inner_diameter, can_wall_thickness, cell_height,
   surface_to_volume, tab_conductance_proxy, diffusion_path_proxy
   ```
   
   Extract these from each `CellSpec.parameters` dict in the correct order.

3. **Assemble target matrix Y:**
   
   Two columns: `rate_capability` and `max_temp`, extracted from each `SimulationResult`.
   
   **CRITICAL:** Read how the existing `prepare.py` names these targets. Use the EXACT same names in `metadata.json` → `target_names`. If prepare.py uses `rate_capability_proxy` and `max_temp_proxy`, we may need to decide whether to keep the `_proxy` suffix or drop it. Since this is real physics data (not proxy), dropping it makes sense — but `surrogate.py` must still work. **Read surrogate.py carefully to see if it references target names by string or by index.**

4. **Shuffle and split:**
   ```python
   rng = np.random.default_rng(seed=42)
   indices = rng.permutation(len(successful))
   
   n_total = len(successful)
   n_train = int(n_total * 0.7)
   n_val = int(n_total * 0.15)
   # n_test = remaining
   
   train_idx = indices[:n_train]
   val_idx = indices[n_train:n_train + n_val]
   test_idx = indices[n_train + n_val:]
   ```

5. **Save .npz files:**
   ```python
   output = Path(output_path)
   output.mkdir(parents=True, exist_ok=True)
   
   np.savez(output / "train.npz", X=X[train_idx], Y=Y[train_idx])
   np.savez(output / "val.npz", X=X[val_idx], Y=Y[val_idx])
   np.savez(output / "test.npz", X=X[test_idx], Y=Y[test_idx])
   ```

6. **Compute SHA-256 hashes** (same method as prepare.py):
   ```python
   import hashlib
   
   def _hash_file(path: Path) -> str:
       h = hashlib.sha256()
       h.update(path.read_bytes())
       return h.hexdigest()
   ```

7. **Compute metadata:**
   ```python
   metadata = {
       "feature_names": [...],  # 11 feature names in order
       "target_names": [...],   # 2 target names
       "target_stds": {
           target_names[0]: float(Y[:, 0].std()),
           target_names[1]: float(Y[:, 1].std()),
       },
       "hashes": {
           "train": _hash_file(output / "train.npz"),
           "val": _hash_file(output / "val.npz"),
           "test": _hash_file(output / "test.npz"),
       },
       "n_samples": {
           "train": int(len(train_idx)),
           "val": int(len(val_idx)),
           "test": int(len(test_idx)),
           "total": n_total,
           "failed": failed_count,
           "attempted": len(specs),
       },
       "ranges": {
           name: [float(X[:, i].min()), float(X[:, i].max())]
           for i, name in enumerate(feature_names)
       },
       "split_ratio": [0.7, 0.15, 0.15],
       "source": "pybamm_dfn",  # distinguishes from "synthetic"
       "parameter_set": "Chen2020",
       "seed": 42,
   }
   
   with open(output / "metadata.json", "w") as f:
       json.dump(metadata, f, indent=2)
   ```

8. **Return output path.**

**Class: `NpzDatasetLoader(DatasetLoader)`**

**Method: `load(self, dataset_path: Path | str) -> dict`**

```python
path = Path(dataset_path)
metadata = json.loads((path / "metadata.json").read_text())

# Verify hashes
for split in ["train", "val", "test"]:
    npz_path = path / f"{split}.npz"
    actual_hash = _hash_file(npz_path)
    expected_hash = metadata["hashes"][split]
    if actual_hash != expected_hash:
        raise ValueError(f"Hash mismatch for {split}: {actual_hash} != {expected_hash}")

# Load arrays
data = {}
for split in ["train", "val", "test"]:
    npz = np.load(path / f"{split}.npz")
    data[split] = {"X": npz["X"], "Y": npz["Y"]}

data["metadata"] = metadata
return data
```

### File 2: `forge/ml/dataset/__init__.py`

Update exports:
```python
from forge.ml.dataset.npz_builder import NpzDatasetBuilder, NpzDatasetLoader
```

### File 3: `tests/ml/dataset/__init__.py`

Create package init.

### File 4: `tests/ml/dataset/test_npz_builder.py`

These tests use **mock data** — no PyBaMM needed. Create fake `CellSpec` and `SimulationResult` objects directly.

1. **test_build_basic** — Create 100 fake specs + results (all successful). Build dataset. Verify:
   - `train.npz`, `val.npz`, `test.npz` exist
   - `metadata.json` exists and is valid JSON
   - Train/val/test sizes sum to 100
   - Split ratio is approximately 70/15/15

2. **test_build_with_failures** — Create 100 specs: 90 successful, 10 failed (`success=False`). Build dataset. Verify:
   - Only 90 samples in the output (failures dropped)
   - `metadata["n_samples"]["failed"] == 10`
   - `metadata["n_samples"]["attempted"] == 100`

3. **test_feature_columns** — Build from fake data. Verify:
   - `metadata["feature_names"]` has exactly 11 entries
   - First 8 are geometric parameters
   - Last 3 are derived features
   - `X` array shape is `(n_samples, 11)`

4. **test_target_columns** — Verify:
   - `metadata["target_names"]` has exactly 2 entries
   - `Y` array shape is `(n_samples, 2)`
   - `target_stds` has 2 entries, both > 0

5. **test_hash_integrity** — Build dataset, then load with `NpzDatasetLoader`. Verify no hash errors. Then corrupt one file (flip a byte) and verify `ValueError` raised.

6. **test_reproducibility** — Build twice with same data and seed. Hashes and splits must be identical.

7. **test_loader_round_trip** — Build, then load. Verify `X` and `Y` arrays match (within floating point tolerance).

### File 5: `experiments/ml/autoresearch/prepare_pybamm.py`

**Purpose:** The pilot orchestration script. This is the "run this and get a real dataset" entry point.

**This is an experiment script, NOT a library module.** It lives in `experiments/`, not `forge/`. It orchestrates the library components.

**Structure:**

```python
#!/usr/bin/env python3
"""
FORGE PyBaMM Pilot — Physics-Based Dataset Generation

Generates a dataset of battery cell designs with electrochemical/thermal
performance targets from PyBaMM DFN simulations.

Pipeline:
  1. (Optional) Sobol sensitivity screening
  2. Latin Hypercube Sampling of geometric design space
  3. PyBaMM DFN simulation for each sample
  4. Dataset assembly (train/val/test .npz + metadata.json)

Usage:
  # Full pilot (500 samples, ~30-40 min on GPU rig)
  python prepare_pybamm.py --n-samples 500

  # Quick smoke test (20 samples, ~2 min)
  python prepare_pybamm.py --n-samples 20

  # With Sobol screening first (adds ~45 min for N=64)
  python prepare_pybamm.py --n-samples 500 --sobol --sobol-n 64

  # Custom output directory
  python prepare_pybamm.py --n-samples 500 --output dataset_pybamm
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path if needed
# (same pattern as existing prepare.py)

from forge.ml.batch import LHSGenerator
from forge.ml.dataset import NpzDatasetBuilder
from forge.ml.simulation import GeometryTranslator, PyBaMMRunner
# Conditional import for Sobol (only if --sobol flag)
```

**Argument parser:**

```python
parser = argparse.ArgumentParser(description="FORGE PyBaMM Pilot Dataset Generation")
parser.add_argument("--n-samples", type=int, default=500, help="Number of cell designs to simulate")
parser.add_argument("--seed", type=int, default=42, help="Random seed for LHS sampling")
parser.add_argument("--output", type=str, default="dataset_pybamm", help="Output directory for dataset")
parser.add_argument("--sobol", action="store_true", help="Run Sobol screening before dataset generation")
parser.add_argument("--sobol-n", type=int, default=64, help="Sobol base sample size (evaluations = N × (D+2))")
parser.add_argument("--sobol-output", type=str, default="sobol_report.json", help="Sobol results output file")
parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING"])
```

**Main pipeline:**

```python
def main():
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    translator = GeometryTranslator()
    runner = PyBaMMRunner(base_parameter_set="Chen2020")
    generator = LHSGenerator()
    builder = NpzDatasetBuilder()

    design_space = translator.get_design_space()
    # Convert to DesignSpace if get_design_space() returns a dict
    # (adapt based on actual return type from P1)

    # ── Phase 1: Sobol Screening (optional) ──────────────────────
    if args.sobol:
        from forge.ml.sensitivity import SobolScreener

        logger.info(f"Running Sobol screening with N={args.sobol_n}...")
        screener = SobolScreener(runner=runner, translator=translator)

        t0 = time.time()
        sobol_rate = screener.screen(design_space, target="rate_capability", n_samples=args.sobol_n)
        sobol_temp = screener.screen(design_space, target="max_temp", n_samples=args.sobol_n)
        t_sobol = time.time() - t0

        logger.info(f"Sobol screening complete in {t_sobol:.0f}s")
        logger.info("\n" + screener.print_report(sobol_rate))
        logger.info("\n" + screener.print_report(sobol_temp))

        # Save Sobol results
        important_rate = screener.rank_parameters(sobol_rate, threshold=0.01)
        important_temp = screener.rank_parameters(sobol_temp, threshold=0.01)
        
        sobol_output = {
            "rate_capability": {
                "indices": [{"parameter": idx.parameter, "S1": idx.S1, "ST": idx.ST} for idx in sobol_rate.indices],
                "important_parameters": important_rate,
            },
            "max_temp": {
                "indices": [{"parameter": idx.parameter, "S1": idx.S1, "ST": idx.ST} for idx in sobol_temp.indices],
                "important_parameters": important_temp,
            },
            "n_samples": args.sobol_n,
            "duration_seconds": t_sobol,
        }
        sobol_path = Path(args.sobol_output)
        sobol_path.write_text(json.dumps(sobol_output, indent=2))
        logger.info(f"Sobol results saved to {sobol_path}")

    # ── Phase 2: LHS Sampling ────────────────────────────────────
    logger.info(f"Generating {args.n_samples} cell designs via LHS (seed={args.seed})...")
    specs = generator.generate_with_derived(design_space, args.n_samples, translator, seed=args.seed)
    logger.info(f"Generated {len(specs)} cell designs")

    # ── Phase 3: PyBaMM Simulations ──────────────────────────────
    logger.info(f"Running PyBaMM DFN simulations...")
    
    config = SimulationConfig(...)  # Construct with standard settings
    # (adapt based on actual SimulationConfig fields from types.py)
    
    results = []
    n_success = 0
    n_fail = 0
    t_start = time.time()

    for i, spec in enumerate(specs):
        t_sim = time.time()
        result = runner.simulate(spec, config)
        dt = time.time() - t_sim

        if result.success:
            n_success += 1
            status = "OK"
        else:
            n_fail += 1
            status = f"FAIL: {result.error_message}"

        results.append(result)

        # Progress logging every 10 samples or on failure
        if (i + 1) % 10 == 0 or not result.success:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            eta = (args.n_samples - i - 1) / rate if rate > 0 else 0
            logger.info(
                f"[{i+1}/{args.n_samples}] {status} | "
                f"{dt:.1f}s | {n_success} ok, {n_fail} fail | "
                f"ETA: {eta:.0f}s"
            )

    t_total = time.time() - t_start
    logger.info(f"Simulations complete: {n_success} ok, {n_fail} fail in {t_total:.0f}s")
    
    fail_rate = n_fail / args.n_samples
    if fail_rate > 0.2:
        logger.warning(f"High failure rate: {fail_rate:.1%}. Dataset quality may be compromised.")
    if n_success < 50:
        logger.error(f"Only {n_success} successful simulations. Need at least 50 for a viable dataset.")
        sys.exit(1)

    # ── Phase 4: Dataset Assembly ────────────────────────────────
    logger.info(f"Assembling dataset in '{args.output}'...")
    output_path = builder.build(
        specs=specs,
        results=results,
        representations=None,
        output_path=args.output,
    )
    
    # Load back and verify
    from forge.ml.dataset import NpzDatasetLoader
    loader = NpzDatasetLoader()
    data = loader.load(output_path)
    
    meta = data["metadata"]
    logger.info(f"Dataset assembled:")
    logger.info(f"  Source: {meta.get('source', 'unknown')}")
    logger.info(f"  Samples: {meta['n_samples']['total']} (attempted: {meta['n_samples']['attempted']}, failed: {meta['n_samples']['failed']})")
    logger.info(f"  Train: {meta['n_samples']['train']}, Val: {meta['n_samples']['val']}, Test: {meta['n_samples']['test']}")
    logger.info(f"  Features: {len(meta['feature_names'])} — {meta['feature_names']}")
    logger.info(f"  Targets: {meta['target_names']}")
    logger.info(f"  Target stds: {meta['target_stds']}")
    logger.info(f"  Hashes verified: OK")

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("FORGE PyBaMM Pilot — Complete")
    print("=" * 60)
    print(f"Samples:    {n_success} / {args.n_samples} ({n_fail} failures)")
    print(f"Duration:   {t_total:.0f}s ({t_total/60:.1f} min)")
    print(f"Rate:       {args.n_samples/t_total:.1f} samples/s")
    print(f"Output:     {output_path}/")
    print(f"  train.npz:     {meta['n_samples']['train']} samples")
    print(f"  val.npz:       {meta['n_samples']['val']} samples")
    print(f"  test.npz:      {meta['n_samples']['test']} samples")
    print(f"  metadata.json: hashes verified")
    print("=" * 60)
    print(f"\nTo use with autoresearch:")
    print(f"  python surrogate.py --dataset {args.output} --seed 42 --budget-seconds 300")
    print()


if __name__ == "__main__":
    main()
```

### File 6: `experiments/ml/autoresearch/prepare_synthetic_v2.py`

**Purpose:** Regenerate the synthetic dataset with the EXACT same feature schema as `prepare_pybamm.py`. This ensures `surrogate.py` works identically with either dataset source.

**Approach:** This is a modified copy of the existing `prepare.py`. The changes:

1. **Read the existing `prepare.py` first.** Understand every formula, every column name, every output format detail.

2. **Ensure the feature column names and order match exactly** what `NpzDatasetBuilder` produces:
   ```
   electrode_thickness, porosity, separator_thickness, n_tabs, tab_width,
   can_inner_diameter, can_wall_thickness, cell_height,
   surface_to_volume, tab_conductance_proxy, diffusion_path_proxy
   ```

3. **Ensure the target column names match** what the PyBaMM runner produces. If the original `prepare.py` uses `rate_capability_proxy` and `max_temp_proxy`, rename to match the PyBaMM output names. Or if we keep `_proxy` for synthetic and drop it for real data, surrogate.py must handle both — **check this carefully**.

4. **Use the same metadata.json schema** as `NpzDatasetBuilder`, including `"source": "synthetic_v2"`.

5. **Keep the same proxy formulas** from the original `prepare.py` — they're the synthetic approximation. Don't change the physics, just align the schema.

6. **Keep the 3 sanity assertions** from the original prepare.py.

**CRITICAL DECISION — target naming:**

Read `surrogate.py` to determine if it loads targets by name (string lookup) or by column index. If by index (Y[:, 0] and Y[:, 1]), then naming doesn't matter as long as the order is consistent. If by name, the names must match between synthetic and PyBaMM datasets.

The safest approach: use the SAME target names for both datasets. If the original prepare.py uses `rate_capability_proxy`, rename it to `rate_capability` in the v2 version. The `_proxy` suffix was appropriate when we only had formulas; now that we have both synthetic and real data, consistent naming is better.

**Do NOT delete or modify the original `prepare.py`.** It's a historical artifact. Create `prepare_synthetic_v2.py` alongside it.

### File 7: Update `experiments/ml/autoresearch/.gitignore`

Add entries for the new output paths:
```
dataset_pybamm/
sobol_report.json
```

## Constraints

- **Python 3.11**
- **No new dependencies.** Everything needed is already in the `ml` group (numpy, scipy, torch, SALib, pybamm).
- **Output format must be byte-for-byte compatible with surrogate.py.** The whole point is that `surrogate.py` works unchanged on either synthetic or PyBaMM data.
- **`npz_builder.py` must NOT import PyBaMM.** It operates on CellSpec/SimulationResult objects — pure data. Domain-agnostic.
- **`prepare_pybamm.py` IS allowed to import everything** — it's an experiment script, not library code.
- **Follow existing code style:** ruff-clean, mypy-compatible, docstrings.
- **Do not modify any existing files** except:
  - `forge/ml/dataset/__init__.py` (add exports)
  - `experiments/ml/autoresearch/.gitignore` (add new paths)

## Verification

```bash
# Import checks
python -c "from forge.ml.dataset import NpzDatasetBuilder, NpzDatasetLoader"

# Dataset builder tests (fast, mock data)
pytest tests/ml/dataset/test_npz_builder.py -v

# Full regression
pytest --tb=short -q

# Ruff
ruff check forge/ml/dataset/ tests/ml/dataset/ experiments/ml/autoresearch/prepare_pybamm.py

# ── End-to-end smoke test (needs PyBaMM, ~2 min) ──
cd experiments/ml/autoresearch
python prepare_pybamm.py --n-samples 20 --output dataset_smoke_test

# Verify the smoke test dataset works with surrogate.py
python surrogate.py --dataset dataset_smoke_test --seed 42 --budget-seconds 30

# ── Synthetic v2 regeneration ──
python prepare_synthetic_v2.py
python surrogate.py --dataset dataset --seed 42 --budget-seconds 30
# (should work identically to the original prepare.py output)

# ── Hash verification ──
python -c "
from forge.ml.dataset import NpzDatasetLoader
loader = NpzDatasetLoader()
data = loader.load('dataset_smoke_test')
print('Loaded OK, hashes verified')
print(f'Train: {data[\"metadata\"][\"n_samples\"][\"train\"]} samples')
print(f'Features: {data[\"metadata\"][\"feature_names\"]}')
print(f'Targets: {data[\"metadata\"][\"target_names\"]}')
"
```

## Important Notes

- **The smoke test (20 samples) is the first thing to run.** If it fails, debug before attempting the full 500-sample pilot. Common failure modes: PyBaMM not installed, parameter name typos, solver divergence on edge cases.
- **The full pilot (500 samples) should take 30-40 minutes.** Run it and walk away. Check the log for failure rate — if >10%, investigate which parameter combinations fail and consider narrowing the design space.
- **`prepare_synthetic_v2.py` exists alongside the original `prepare.py`.** The original is untouched history. The v2 version has aligned naming. Both output to the `dataset/` directory by default (the original) or a specified directory.
- **After P3 is verified**, the autoresearch loop can run on real data:
  ```bash
  cd experiments/ml/autoresearch
  python prepare_pybamm.py --n-samples 500 --sobol --sobol-n 64
  # Then point the agent at program.md with --dataset dataset_pybamm
  ```
- **The Sobol report is a thesis artifact.** Save `sobol_report.json` — it goes directly into the methodology chapter. The parameter ranking table, with confidence intervals, demonstrates formal experimental design.
- **Target naming alignment is critical.** The prompt emphasizes this multiple times because a mismatch here causes `surrogate.py` to silently produce wrong results (training on shuffled target columns). The verification step of running `surrogate.py` on the new dataset catches this.
