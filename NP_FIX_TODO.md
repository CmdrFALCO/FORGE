# N/P Constraint Fix — Test Debt (RESOLVED)

After `check_np_ratio` was changed to validate the COMPUTED N/P ratio
(from loadings x specific capacities) instead of trusting a declared scalar,
13 tests failed because their fixtures had inconsistent loadings. All three
groups are now resolved:

- **(a) Fixture-loading fixes** — done in `0c8fae5` (balanced fixture
  variants: `valid_cell_balanced`, `VALID_CYLINDRICAL_CELL_BALANCED`, etc.).
- **(b) N/P constraint tests rewritten to computed-value semantics** — done.
  `test_np_ratio_above_maximum`, `test_np_ratio_at_boundary_min`,
  `test_np_ratio_at_boundary_max` in
  `tests/engine/validation/test_constraint_validation.py` now set anode
  `loading_mg_cm2` so the computed N/P lands at the target value (boundary
  tests sit just inside 1.05/1.25 with a float-safe margin).
- **(c) Coincidentally-passing negative tests rewritten** — done.
  `test_np_ratio_below_minimum` and `test_error_feedback_helpful` (same file)
  and `test_invalid_np_ratio_fails` (`tests/axiom/test_cylindrical_support.py`)
  now set explicit loadings that compute out-of-range, instead of relying on
  the inconsistent base-fixture loadings. Declared `np_ratio` is set to match
  the computed value in each test so the tests exercise exactly one thing.

## Still open (unrelated to N/P)

`tests/ml/simulation/test_pybamm_runner.py::TestTemperatureMonotonic::test_thick_electrode_hotter` —
pre-existing PyBaMM thermal monotonicity failure. Does not run on CI (CI
installs only the `dev` extra, not `ml`). Needs separate investigation.
