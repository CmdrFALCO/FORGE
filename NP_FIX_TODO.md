# N/P Constraint Fix — Remaining Test Failures

After `check_np_ratio` was changed to validate the COMPUTED N/P ratio
(from loadings x specific capacities) instead of trusting a declared scalar,
13 tests fail because their fixtures have inconsistent loadings.

## (a) Fixture-loading fixes needed

These tests use "valid cell" fixtures whose anode loadings imply a computed
N/P outside [1.05, 1.25]. Fix: adjust anode `loading_mg_cm2` so computed N/P
matches the declared value (same pattern as the pouch fixture fix already in
the unstaged `tests/axiom/test_pouch_support.py`).

- `tests/api/test_validation.py::test_validate_prismatic_valid` — prismatic fixture
- `tests/api/test_validation.py::test_validate_cylindrical_valid` — cylindrical fixture
- `tests/axiom/test_cylindrical_support.py::test_valid_cylindrical_passes_physics` — VALID_CYLINDRICAL_CELL (computed 1.009)
- `tests/axiom/test_cylindrical_support.py::test_full_validation_passes` — same fixture
- `tests/axiom/test_cylindrical_support.py::test_4680_full_validation_passes` — VALID_4680_CELL (computed 1.032)
- `tests/engine/validation/test_constraint_validation.py::test_valid_cell_passes` — prismatic fixture (computed 0.997)
- `tests/engine/validation/test_validation_pipeline.py::test_minimal_valid_passes_pipeline` — same prismatic fixture
- `tests/engine/validation/test_validation_pipeline.py::test_valid_json_string` — same fixture as JSON
- `tests/gui/test_axiom_pipeline.py::test_run_pipeline_with_tracking_mock_backend_success` — mock YAML (computed 1.001)
- `tests/gui/test_axiom_pipeline.py::test_run_pipeline_with_tracking_retry_success` — same mock YAML

## (b) N/P constraint tests that must be REWRITTEN

These tests were designed for the OLD behavior (checking a declared scalar).
They set `np_ratio` to boundary/out-of-range values and assert pass/fail.
With the new computed-value check, they need to be rewritten to manipulate
LOADINGS to produce computed N/P values at the boundaries and beyond.

- `tests/engine/validation/test_constraint_validation.py::test_np_ratio_above_maximum` — sets declared N/P=1.30, expects fail on "1.25"; now needs loadings that compute to >1.25
- `tests/engine/validation/test_constraint_validation.py::test_np_ratio_at_boundary_min` — sets declared N/P=1.05, expects pass; now needs loadings that compute to exactly 1.05
- `tests/engine/validation/test_constraint_validation.py::test_np_ratio_at_boundary_max` — sets declared N/P=1.25, expects pass; now needs loadings that compute to exactly 1.25

## (c) Negative N/P tests passing by fixture coincidence

These tests currently PASS only because their shared "valid cell" fixtures
have loadings that compute OUTSIDE [1.05, 1.25]. They encode the OLD
declared-scalar semantics (they set a bad declared `np_ratio` and expect a
failure that is actually being produced by the inconsistent loadings, not the
declared value). They are NOT touched by the group (a) fixture work — the
group (a) plan splits the fixtures so these keep their original loadings and
keep passing. They need the same rewrite to computed-value behavior as group
(b). (See Group-A plan §4 note: `Reports/2026-06-27_NP_Group-A_Fixture_Fix_Plan.md`.)

- `tests/engine/validation/test_constraint_validation.py::test_np_ratio_below_minimum` — sets declared N/P=1.00, expects fail; passes only because fixture computes 0.997
- `tests/engine/validation/test_constraint_validation.py::test_error_feedback_helpful` — sets declared N/P=0.95, expects N/P feedback; same coincidence
- `tests/axiom/test_cylindrical_support.py::test_invalid_np_ratio_fails` — sets declared N/P=0.9, expects fail; passes only because VALID_CYLINDRICAL_CELL computes 1.009

## Not related

`tests/ml/simulation/test_pybamm_runner.py::test_thick_electrode_hotter` —
pre-existing PyBaMM thermal monotonicity failure, unrelated to N/P change.
Do not touch.
