# P2 — Batch Generator + Sobol Screening

## Context

This is prompt 2 of 3 for the FORGE PyBaMM pilot. P1 built the translation layer (`GeometryTranslator`) and PyBaMM runner (`PyBaMMRunner`). P2 builds the sampling infrastructure and sensitivity analysis that feeds into dataset generation (P3).

**Dependency:** P1 must be complete and verified before executing P2. The batch generator produces `CellSpec` objects that the `PyBaMMRunner` from P1 consumes. The Sobol screener uses both the batch generator and the runner.

## Pre-Check — READ THESE FILES FIRST

1. **`forge/ml/batch/generator.py`** — `BatchGenerator` ABC. Read the interface contract: `generate(design_space, n_samples, strategy, seed)` method signature, return type, docstring.

2. **`forge/ml/sensitivity/screener.py`** — `SensitivityScreener` ABC. Read the interface: `screen(design_space, target, n_samples)` and `rank_parameters(result, threshold)` method signatures.

3. **`forge/ml/common/types.py`** — All ML dataclasses. Specifically understand:
   - `ParameterRange(name, low, high, is_integer)`
   - `DesignSpace(parameters: list[ParameterRange])`
   - `CellSpec(parameters: dict[str, float], cell_type: CellType)`
   - `SobolIndex(parameter, S1, ST, S1_conf, ST_conf)`
   - `SobolResult(indices: list[SobolIndex], n_samples, target_name)`
   - `SamplingStrategy` enum

4. **`forge/ml/simulation/geometry_translator.py`** (from P1) — Read `get_design_space()` to understand the parameter ranges and `compute_derived_features()` for the 3 derived features.

5. **`forge/ml/simulation/pybamm_runner.py`** (from P1) — Read how `simulate()` works, what it returns, how errors are handled.

6. **`experiments/ml/autoresearch/prepare.py`** — Read the existing synthetic LHS sampling implementation. The batch generator generalizes this pattern into a reusable class.

## What to Build

### File 1: `forge/ml/batch/lhs_generator.py`

**Purpose:** Implement `BatchGenerator` ABC using Latin Hypercube Sampling via `scipy.stats.qmc`.

**Class: `LHSGenerator(BatchGenerator)`**

**Method: `generate(self, design_space: DesignSpace, n_samples: int, strategy: SamplingStrategy = SamplingStrategy.LATIN_HYPERCUBE, seed: int = 42) -> list[CellSpec]`**

Implementation:

1. Extract parameter bounds from `design_space.parameters` into arrays for `scipy.stats.qmc.LatinHypercube`.
2. Generate `n_samples` in [0, 1] hypercube using `LatinHypercube(d=n_params, seed=seed).random(n=n_samples)`.
3. Scale each dimension to its `[low, high]` range: `scaled = low + sample * (high - low)`.
4. For integer parameters (`is_integer=True`), round to nearest integer: `np.round(scaled).astype(int)`. Specifically, `n_tabs` must be an integer in [1, 6].
5. Construct `CellSpec` objects with `cell_type=CellType.CYLINDRICAL` and the parameter dict.
6. Return the list.

**Validation:**
- `n_samples` must be > 0
- `design_space.parameters` must be non-empty
- All `low < high` in parameter ranges
- Raise `ValueError` with descriptive messages on violations

**Method: `generate_with_derived(self, design_space: DesignSpace, n_samples: int, translator: 'GeometryTranslator', seed: int = 42) -> list[CellSpec]`**

Convenience method that:
1. Calls `self.generate(...)` to get base samples
2. For each `CellSpec`, calls `translator.compute_derived_features(spec.parameters)` to add the 3 derived features
3. Returns the enriched list

This is a helper — the base `generate()` must work standalone without the translator.

### File 2: `forge/ml/sensitivity/sobol_screener.py`

**Purpose:** Implement `SensitivityScreener` ABC using Sobol sensitivity analysis. Uses `scipy.stats.qmc.Sobol` for quasi-random sampling and computes first-order (S1) and total-effect (ST) Sobol indices.

**Class: `SobolScreener(SensitivityScreener)`**

**Constructor: `__init__(self, runner: SimulationRunner, translator: GeometryTranslator)`**

Stores references to the simulation runner and geometry translator. The screener needs both because:
- The translator converts geometric params → PyBaMM overrides
- The runner executes the actual simulations
- Sobol analysis needs to evaluate the full pipeline for each sample point

**Method: `screen(self, design_space: DesignSpace, target: str, n_samples: int = 128) -> SobolResult`**

`target` is either `"rate_capability"` or `"max_temp"`.

Implementation strategy — **Saltelli sampling + finite-difference Sobol estimation:**

Sobol analysis requires `N × (2D + 2)` model evaluations where N = `n_samples` and D = number of parameters. For 8 parameters and N=128, that's 128 × 18 = 2,304 evaluations. At ~3-5s per DFN simulation, that's ~2-3 hours.

**This is too expensive for DFN.** Revised approach — use a **simpler Sobol estimation** that requires fewer evaluations:

**Option: Direct variance-based estimation with N × (D + 2) evaluations.**

Actually, the standard Saltelli scheme needs `N * (2*D + 2)` samples. For N=64, D=8: 64 * 18 = 1,152 simulations × ~4s = ~75 minutes. That's acceptable on the RTX 3060 rig.

Use `SALib` (Sensitivity Analysis Library) if available, otherwise implement manually with `scipy.stats.qmc.Sobol`.

**Recommended approach — use SALib:**

```python
from SALib.sample import saltelli
from SALib.analyze import sobol

problem = {
    'num_vars': len(design_space.parameters),
    'names': [p.name for p in design_space.parameters],
    'bounds': [[p.low, p.high] for p in design_space.parameters],
}

# Generate Saltelli samples
param_values = saltelli.sample(problem, n_samples, calc_second_order=False)
# With calc_second_order=False: N * (D + 2) = 64 * 10 = 640 evaluations
# At ~4s each: ~43 minutes. Acceptable.

# Evaluate model for each sample
Y = np.zeros(len(param_values))
for i, params in enumerate(param_values):
    cell_spec = self._make_cell_spec(params, design_space)
    config = SimulationConfig(...)  # standard config
    result = self.runner.simulate(cell_spec, config)
    if result.success:
        Y[i] = getattr(result, target)  # or extract from result dict
    else:
        Y[i] = np.nan  # handle failed simulations

# Handle NaN — SALib can't handle NaN. Options:
# 1. Replace NaN with column mean (simple, introduces bias)
# 2. Drop and resample (expensive)
# 3. Replace with worst-case value (conservative)
# Use option 1 for pilot, document the limitation.
nan_mask = np.isnan(Y)
if nan_mask.any():
    Y[nan_mask] = np.nanmean(Y)
    # Log how many NaN replacements occurred

# Compute Sobol indices
Si = sobol.analyze(problem, Y, calc_second_order=False)
```

**If SALib is not installed, fall back to a manual implementation:**

A simpler variance-based approach using two independent LHS sample matrices (A, B) and recombined matrices. This is more code but avoids the SALib dependency. However, SALib is well-maintained, pip-installable, and commonly used. **Prefer SALib.**

**Add `SALib` to `pyproject.toml` under the `ml` optional dependencies:**
```toml
ml = [
    "torch>=2.0",
    "scipy>=1.11",
    "matplotlib>=3.7",
    "pybop>=24.3",
    "SALib>=1.4",
]
```

**Construct `SobolResult`:**
```python
indices = []
for j, param in enumerate(design_space.parameters):
    indices.append(SobolIndex(
        parameter=param.name,
        S1=float(Si['S1'][j]),
        ST=float(Si['ST'][j]),
        S1_conf=float(Si['S1_conf'][j]),
        ST_conf=float(Si['ST_conf'][j]),
    ))
return SobolResult(
    indices=indices,
    n_samples=n_samples,
    target_name=target,
)
```

**Method: `rank_parameters(self, result: SobolResult, threshold: float = 0.01) -> list[str]`**

Returns parameter names sorted by total-effect index (ST) descending, excluding any with ST < threshold. These are the "important" parameters.

```python
significant = [(idx.parameter, idx.ST) for idx in result.indices if idx.ST >= threshold]
significant.sort(key=lambda x: x[1], reverse=True)
return [name for name, _ in significant]
```

**Method: `print_report(self, result: SobolResult) -> str`**

Returns a formatted text report:
```
Sobol Sensitivity Analysis — target: rate_capability (N=64)
============================================================
Parameter                S1        ST        S1_conf   ST_conf
electrode_thickness      0.412     0.485     0.031     0.028
porosity                 0.298     0.341     0.025     0.022
n_tabs                   0.103     0.158     0.019     0.017
...
------------------------------------------------------------
Parameters below threshold (ST < 0.01):
  can_inner_diameter (ST=0.003)
```

### File 3: `forge/ml/batch/__init__.py`

Update exports:
```python
from forge.ml.batch.lhs_generator import LHSGenerator
```

### File 4: `forge/ml/sensitivity/__init__.py`

Update exports:
```python
from forge.ml.sensitivity.sobol_screener import SobolScreener
```

### File 5: `tests/ml/batch/__init__.py`

Create package init.

### File 6: `tests/ml/batch/test_lhs_generator.py`

1. **test_basic_generation** — Generate 50 samples from the standard design space. Verify:
   - Returns exactly 50 `CellSpec` objects
   - All `cell_type == CellType.CYLINDRICAL`
   - Each spec has all 8 parameter keys

2. **test_parameter_ranges** — Generate 200 samples. For each parameter, verify all values fall within `[low, high]`.

3. **test_integer_rounding** — Generate 100 samples. Verify `n_tabs` is always an integer in [1, 6] with no fractional values.

4. **test_reproducibility** — Generate with seed=42 twice. Results must be identical.

5. **test_different_seeds** — Generate with seed=42 and seed=99. Results must differ.

6. **test_coverage** — Generate 500 samples. For each continuous parameter, verify the samples cover at least 80% of the range (i.e., min(samples) < low + 0.2 × range AND max(samples) > high - 0.2 × range). LHS should give excellent coverage.

7. **test_validation_errors** — Verify `ValueError` raised for n_samples=0, empty design space, and low >= high.

8. **test_generate_with_derived** — Generate 10 samples with derived features. Verify each spec has the 3 additional keys: `surface_to_volume`, `tab_conductance_proxy`, `diffusion_path_proxy`.

### File 7: `tests/ml/sensitivity/__init__.py`

Create package init.

### File 8: `tests/ml/sensitivity/test_sobol_screener.py`

**Mark ALL tests with `@pytest.mark.slow`** — they run actual PyBaMM simulations.

1. **test_screen_rate_capability** — Run Sobol screening with `n_samples=16` (minimal, just to verify the pipeline works end-to-end — 16 × 10 = 160 evaluations, ~10 minutes). Verify:
   - Returns a `SobolResult`
   - `result.target_name == "rate_capability"`
   - All 8 parameters have indices
   - All S1 values are in [-0.5, 1.5] (can be slightly negative/above 1 due to estimation noise with small N)
   - All ST values are >= 0

2. **test_screen_max_temp** — Same as above but for `"max_temp"` target.

3. **test_rank_parameters** — Given a manually constructed `SobolResult` (no simulation needed, just create the dataclass directly), verify:
   - Parameters are sorted by ST descending
   - Parameters below threshold are excluded
   - Empty list returned if all below threshold

4. **test_print_report** — Given a manually constructed `SobolResult`, verify the report string contains all parameter names, is properly formatted, and lists below-threshold parameters.

**Note on test_rank_parameters and test_print_report:** These do NOT need `@pytest.mark.slow` since they use manually constructed data. Only tests 1 and 2 need the slow marker.

## Constraints

- **Python 3.11**
- **New dependency: `SALib>=1.4`** — add to `pyproject.toml` `ml` group.
- **`lhs_generator.py` must NOT import PyBaMM.** It only depends on scipy and numpy.
- **`sobol_screener.py` imports the runner and translator** but does not import PyBaMM directly — it calls them through the ABC interface.
- **Follow existing code style:** ruff-clean, mypy-compatible, docstrings on public methods.
- **Do not modify any existing files** except:
  - `forge/ml/batch/__init__.py` (add exports)
  - `forge/ml/sensitivity/__init__.py` (add exports)
  - `pyproject.toml` (add SALib to ml deps)

## Verification

```bash
# Import checks
python -c "from forge.ml.batch import LHSGenerator"
python -c "from forge.ml.sensitivity import SobolScreener"

# Batch generator tests (fast, no PyBaMM needed)
pytest tests/ml/batch/test_lhs_generator.py -v

# Sobol screener — fast tests only (rank_parameters, print_report)
pytest tests/ml/sensitivity/test_sobol_screener.py -v -m "not slow"

# Sobol screener — full with PyBaMM (slow, ~10-20 min)
pytest tests/ml/sensitivity/test_sobol_screener.py -v -m slow

# Full regression
pytest --tb=short -q

# Ruff
ruff check forge/ml/batch/ forge/ml/sensitivity/ tests/ml/batch/ tests/ml/sensitivity/

# Dependency check
python -c "import SALib; print(SALib.__version__)"
```

## Important Notes

- The Sobol screening is Phase 1 of the pilot. Its output tells us which of the 8 parameters actually affect the targets. If `can_inner_diameter` (44-46mm range) shows ST < 0.01, we can zero it out in the ML feature set — matching what Run 001 synthetic data did. This is methodological rigor.
- SALib's `calc_second_order=False` reduces the required evaluations from `N*(2D+2)` to `N*(D+2)`. For 8 parameters and N=64: 640 evaluations instead of 1,152. First-order and total-effect indices are sufficient — interaction effects are captured by the difference `ST - S1`.
- The screener's NaN handling (mean imputation for failed simulations) is a known simplification. If more than ~10% of simulations fail, the Sobol estimates become unreliable. The `print_report` should include the failure count.
- `n_samples=16` in the slow tests is deliberately minimal. Real Sobol screening should use N=64 or N=128 for reliable estimates. The test just verifies the pipeline works.
- The LHS generator is general-purpose — it works for any `DesignSpace`, not just battery cells. This is intentional: FORGE's sampling infrastructure should be domain-agnostic.
