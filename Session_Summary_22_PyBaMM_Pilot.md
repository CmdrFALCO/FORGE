# Session Summary 22 — PyBaMM Pilot

## 1. Context

This session implemented the PyBaMM pilot: real physics-based dataset generation replacing synthetic proxy formulas. Three prompts (P1, P2, P3) were planned and executed sequentially, culminating in a 500-sample DFN simulation dataset with Sobol sensitivity screening.

The session also included the Surrogate Playground (interactive dashboard with live ensemble inference) and 5 ML dashboard enhancements (prediction plots, Pareto front, hyperparameter landscape, uncertainty calibration, model comparison).

## 2. What Was Done

### Surrogate Playground + Dashboard Enhancements

- `forge/ml/surrogate_inference.py` — SurrogatePredictor with predict(), predict_batch(), sensitivity(), feature_ranges
- `forge/gui/pages/5_ML_Autoresearch.py` — Tab 3 interactive playground (sliders, metrics, sensitivity chart) + Tabs 1-2 enhancements (pred vs actual, Pareto front, hyperparameter landscape, uncertainty calibration, GBR comparison)
- `Dockerfile` — CPU-only torch for inference in Docker
- Checkpoint saved from experiment 184 (30-member ensemble, score 0.151660)

### P1 — Translation Layer + PyBaMM Runner

- `forge/ml/simulation/geometry_translator.py` — GeometryTranslator with translate(), compute_derived_features(), get_design_space(). Reuses L1 `calculate_number_of_winds` and `calculate_electrode_length_analytical` directly (no CylindricalCalculator coupling).
- `forge/ml/simulation/pybamm_runner.py` — PyBaMMRunner(SimulationRunner) with 3 experiments per sample: 0.2C discharge, 3C discharge, 2C discharge with lumped thermal.
- Tests: 20 fast + 4 slow

### P2 — Batch Generator + Sobol Screening

- `forge/ml/batch/lhs_generator.py` — LHSGenerator(BatchGenerator) with LHS via scipy.stats.qmc, integer rounding for n_tabs.
- `forge/ml/sensitivity/sobol_screener.py` — SobolScreener(SensitivityScreener) using SALib Saltelli sampling, calc_second_order=False (N×(D+2) evaluations).
- New dependency: SALib>=1.4 added to pyproject.toml ml group.
- Tests: 12 fast LHS + 5 fast Sobol + 2 slow

### P3 — Dataset Builder + Pilot Orchestration

- `forge/ml/dataset/npz_builder.py` — NpzDatasetBuilder + NpzDatasetLoader. Same .npz + metadata.json format as synthetic.
- `experiments/ml/autoresearch/prepare_pybamm.py` — Full pilot script with optional Sobol screening, LHS sampling, PyBaMM simulation, dataset assembly.
- Tests: 12 fast (mock data)

### Bugs Fixed During Smoke Test

1. **Nominal capacity scaling** — GeometryTranslator now computes `"Nominal cell capacity [A.h]"` from electrode area/thickness/porosity ratio vs Chen2020 baseline. Without this, C-rate definitions were wrong for 4680-scale cells (0.2C was effectively 0.026C, causing 10-hour discharge timeouts).
2. **Thermal experiment** — Changed from 2C CC-CV charge (infeasible at 100% SOC) to "Discharge at 2C until 2.5V" with lumped thermal model.
3. **Min samples threshold** — Parameterized to `min(50, n_samples)` for smoke tests with <50 samples.

## 3. Sobol Screening Results

N=64 base samples, 640 evaluations per target (1,280 total). Duration: 3h 19m.

### Rate Capability

| Parameter | S1 | ST | Significant? |
|-----------|------|------|-------------|
| electrode_thickness | 0.508 | 0.684 | Yes |
| porosity | 0.134 | 0.422 | Yes |
| separator_thickness | -0.047 | 0.074 | Yes |
| can_inner_diameter | 0.015 | 0.051 | Yes |
| n_tabs | 0.000 | 0.000 | No |
| tab_width | 0.000 | 0.000 | No |
| can_wall_thickness | 0.000 | 0.000 | No |
| cell_height | -0.001 | 0.000 | No |

**Dominant drivers:** electrode_thickness (ST=0.68) and porosity (ST=0.42) together explain most variance. Strong interaction effects (ST >> S1 for porosity). Separator thickness and can_inner_diameter have minor effects.

**Dead parameters for rate:** n_tabs, tab_width, can_wall_thickness, cell_height all have ST ≈ 0. This is expected — in the 1D DFN model, tab geometry only affects contact resistance, and the rate capability is dominated by electrode diffusion physics (thickness/porosity).

### Max Temperature

| Parameter | S1 | ST | Significant? |
|-----------|------|------|-------------|
| porosity | 0.194 | 0.747 | Yes |
| electrode_thickness | 0.194 | 0.539 | Yes |
| separator_thickness | -0.062 | 0.054 | Yes |
| cell_height | 0.017 | 0.040 | Yes |
| can_wall_thickness | -0.019 | 0.021 | Yes |
| can_inner_diameter | -0.019 | 0.018 | Yes |
| n_tabs | 0.000 | 0.000 | No |
| tab_width | 0.000 | 0.000 | No |

**Dominant drivers:** porosity (ST=0.75) and electrode_thickness (ST=0.54) with very strong interaction effects. Temperature is sensitive to more parameters than rate capability — cell_height, can_wall_thickness, and can_inner_diameter all contribute through thermal mass and surface area.

**Dead parameters for temp:** n_tabs and tab_width have ST=0. Same reasoning — 1D DFN lumped thermal doesn't resolve current distribution from tabs.

### Parameters Below ST < 0.01 (Both Targets)

- **n_tabs** (ST=0.000 for both) — contact resistance proxy has no effect in 1D DFN
- **tab_width** (ST=0.000 for both) — same as n_tabs
- **cell_height** (ST=0.000 for rate) — only affects temperature target

### Sobol Failure Rate

- Rate capability screening: 0/640 evaluations failed
- Max temperature screening: 5/640 evaluations failed (0.8%), NaN imputation triggered once

## 4. Dataset Summary

| Metric | Value |
|--------|-------|
| Source | pybamm_dfn (Chen2020) |
| Attempted | 500 |
| Succeeded | 496 |
| Failed | 4 (0.8% failure rate) |
| Train | 347 |
| Val | 74 |
| Test | 75 |
| Features | 11 (8 geometric + 3 derived) |
| Targets | 2 (rate_capability_proxy, max_temp_proxy) |
| Duration | 47 min (500 samples) |

### Target Distributions

| Target | Min | Mean | Max | Std |
|--------|------|------|------|------|
| rate_capability | 0.0000 | 0.3272 | 0.9394 | 0.3557 |
| max_temp (°C) | 28.79 | 53.33 | 82.71 | 15.88 |

Compared to synthetic dataset: rate capability has a wider range (0–0.94 vs ~0.3–1.0 synthetic) and lower mean (0.33 vs 0.69). Temperature range is similar but centered lower (53°C vs 70°C). The DFN model produces more extreme rate-limiting behavior at high electrode thickness + low porosity.

## 5. Smoke Test Verification

- 20/20 simulations succeeded (0% failure rate)
- Rate capability: 0.136 (physically plausible for 100μm NMC532 at 3C)
- Max temperature: 71.4°C (physically plausible for 2C discharge)
- `surrogate.py` training: loss decreases monotonically (1592 → 0.0001), no NaN
- Target name alignment confirmed (`target_stds["rate_capability_proxy"]` resolves correctly)
- `surrogate.py` on main branch works unchanged on PyBaMM data

## 6. Test Progression

| After Phase | Passed | Skipped | Failed | New Tests |
|-------------|--------|---------|--------|-----------|
| P1 (translator + runner) | 1424 | 24 | 2* | +24 |
| P2 (batch + sobol) | 1441 | 24 | 2* | +17 |
| P3 (builder + pilot) | 1453 | 24 | 2* | +12 |

*2 pre-existing AXIOM live API test failures (missing ANTHROPIC_API_KEY).

Total new tests this session: **53** (49 fast + 4 slow PyBaMM + 2 slow Sobol)

## 7. Commits This Session

| Hash | Message |
|------|---------|
| `3344304` | feat(gui): add Surrogate Playground with live ensemble inference |
| `5b1bddc` | feat(gui): add prediction plots, model comparison, Pareto front, and calibration to ML dashboard |
| `af26182` | feat(ml): add geometry translator and PyBaMM simulation runner (P1) |
| `51208f2` | feat(ml): add LHS batch generator and Sobol sensitivity screener (P2) |
| `684a399` | feat(ml): add NpzDatasetBuilder and PyBaMM pilot orchestration script (P3) |
| `68fc909` | fix(ml): scale nominal capacity for 4680 geometry, use discharge for thermal experiment |

Also on `autoresearch/run-001`:
| `3a9f539` | feat(surrogate): add --save-checkpoint to export ensemble for inference |
| `c8be258` | feat(ml): add SurrogatePredictor inference module for ensemble checkpoint |

## 8. Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `forge/ml/surrogate_inference.py` | SurrogatePredictor for live ensemble inference |
| `forge/ml/simulation/geometry_translator.py` | L1→L3 bridge: geometric params → PyBaMM overrides |
| `forge/ml/simulation/pybamm_runner.py` | PyBaMM DFN simulation runner |
| `forge/ml/batch/lhs_generator.py` | Latin Hypercube Sampling batch generator |
| `forge/ml/sensitivity/sobol_screener.py` | Sobol sensitivity analysis via SALib |
| `forge/ml/dataset/npz_builder.py` | Dataset builder/loader (.npz + metadata.json) |
| `experiments/ml/autoresearch/prepare_pybamm.py` | Pilot orchestration script |
| `experiments/ml/autoresearch/checkpoint.pt` | Ensemble checkpoint (not committed, volume-mounted) |
| `tests/ml/simulation/test_geometry_translator.py` | 20 translator tests |
| `tests/ml/simulation/test_pybamm_runner.py` | 4 slow PyBaMM tests |
| `tests/ml/batch/test_lhs_generator.py` | 12 LHS generator tests |
| `tests/ml/sensitivity/test_sobol_screener.py` | 7 Sobol screener tests |
| `tests/ml/dataset/test_npz_builder.py` | 12 dataset builder tests |

### Modified Files

| File | Change |
|------|--------|
| `forge/gui/pages/5_ML_Autoresearch.py` | Tab 3 playground + 5 enhancements |
| `forge/ml/simulation/__init__.py` | Export GeometryTranslator, PyBaMMRunner |
| `forge/ml/batch/__init__.py` | Export LHSGenerator |
| `forge/ml/sensitivity/__init__.py` | Export SobolScreener |
| `forge/ml/dataset/__init__.py` | Export NpzDatasetBuilder, NpzDatasetLoader |
| `Dockerfile` | CPU-only torch for inference |
| `.gitignore` | Exclude checkpoint.pt |
| `experiments/ml/autoresearch/.gitignore` | Exclude dataset_pybamm/, sobol_report.json |
| `pyproject.toml` | SALib>=1.4 in ml deps |
| `experiments/ml/autoresearch/surrogate.py` | --save-checkpoint flag (on autoresearch/run-001) |

## 9. Architecture Decisions

- **Direct L1 function calls (not CylindricalCalculator):** Less coupling. Translator imports only `calculate_number_of_winds` and `calculate_electrode_length_analytical` from `winding.py`.
- **Tab geometry → contact resistance proxy:** 1D DFN limitation. Not spatially resolved but physically defensible. Sobol confirmed n_tabs/tab_width have ST=0 — the 1D model can't differentiate tab configurations.
- **N/P ratio = 1.1:** Anode 10% thicker than cathode. Standard safety margin.
- **Equal porosity for cathode and anode:** Simplification, acknowledged in thesis.
- **Nominal capacity scaling:** Computed from electrode area × active thickness × solid fraction ratio vs Chen2020 baseline. Critical for correct C-rate definitions at 4680 scale.
- **2C discharge (not charge) for thermal target:** Avoids infeasible charge-from-full-SOC experiment. Produces representative thermal behavior under high current.
- **DFN for both Sobol screening and dataset generation:** Consistent, no model-transfer uncertainty.
- **Chen2020 base parameter set with geometric overrides:** Standard approach per Jackowska et al. (2025).
- **SALib for Sobol analysis:** calc_second_order=False reduces evaluations from N×(2D+2) to N×(D+2).
- **Target names kept as `_proxy`:** For backward compatibility with existing surrogate.py. The naming is a code artifact — the thesis should clarify these are DFN simulation outputs, not proxy formulas.

## 10. Next Steps

- **Review Sobol report** — n_tabs and tab_width are dead (ST=0 for both targets). Consider zeroing them out or dropping from the feature set before autoresearch on real data. This aligns with Run 001's finding that can_inner_diameter was low-importance.
- **Run autoresearch on real data:** `python surrogate.py --dataset dataset_pybamm --seed 42 --budget-seconds 300`
- **Feature set adjustment:** The Sobol results suggest a reduced feature set may be optimal. electrode_thickness and porosity are the dominant drivers for both targets.
- **prepare_synthetic_v2.py** — Not yet created. Would regenerate synthetic data with matched schema for direct comparison. Lower priority since the PyBaMM dataset is now available.
- **Deployment workstreams (W1-W5)** — Docker rebuild with new dashboard features, push to production
- **JOSS submission preparation**

## 11. Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Session Summary 22 | This document | PyBaMM pilot complete |
| Sobol Report | experiments/ml/autoresearch/sobol_report.json | Sensitivity analysis results |
| PyBaMM Dataset | experiments/ml/autoresearch/dataset_pybamm/ | 496-sample DFN dataset |
| Smoke Test Log | /tmp/pybamm_pilot.log | Full pilot execution log |
| P1 Plan | docs/P1_Translation_Layer_and_PyBaMM_Runner.md | Translation layer spec |
| P2 Plan | docs/P2_Batch_Generator_and_Sobol_Screening.md | Batch generator spec |
| P3 Plan | docs/P3_Dataset_Builder_and_Pilot_Orchestration.md | Dataset builder spec |
