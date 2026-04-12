# AXIOM Phase 1: Instrumentation Refactoring — Execution Plan

## Working Directory

```
~/Projects/CmdrFALCO/FORGE/
```

## Branch

`main` — all changes go here. No conflict with Opus CLI (running Optuna on `autoresearch/run-004`).

---

## Constraint Registry — ID Mapping

Derived from `forge/engine/validation/constraint_validator.py` lines 883-934.

### Common Constraints (C1-C7) — All Cell Types

| ID | Name | Function | Rule | Path |
|----|------|----------|------|------|
| C1 | np_ratio | `check_np_ratio` | 1.05 ≤ N/P ≤ 1.25 | `electrochemistry.anode.np_ratio` |
| C2 | cathode_loading | `check_cathode_loading_reasonable` | 5.0 ≤ loading ≤ 30.0 mg/cm² | `electrochemistry.cathode.loading_mg_cm2` |
| C3 | anode_loading | `check_anode_loading_reasonable` | 5.0 ≤ loading ≤ 20.0 mg/cm² | `electrochemistry.anode.loading_mg_cm2` |
| C4 | separator_porosity | `check_separator_porosity_valid` | 30.0 ≤ porosity ≤ 55.0 % | `electrochemistry.separator.porosity_pct` |
| C5 | electrolyte_concentration | `check_electrolyte_salt_concentration` | 0.8 ≤ conc ≤ 1.5 M | `electrochemistry.electrolyte.salt_concentration_m` |
| C6 | cathode_material | `check_cathode_material_valid` | non-empty string | `electrochemistry.cathode.material_name` |
| C7 | anode_material | `check_anode_material_valid` | non-empty string | `electrochemistry.anode.material_name` |

### Prismatic Constraints (PR1-PR7)

| ID | Name | Function | Rule |
|----|------|----------|------|
| PR1 | internal_height | `check_internal_height_positive` | height - wall_top - wall_bottom > 0 |
| PR2 | internal_width | `check_internal_width_positive` | width - 2*wall_side > 0 |
| PR3 | internal_thickness | `check_internal_thickness_positive` | thickness - 2*wall_front_back > 0 |
| PR4 | cathode_fits_cavity | `check_cathode_fits_in_cavity` | cathode_height < internal_cavity_height |
| PR5 | stacks_count | `check_stacks_positive` | 1 ≤ num_stacks ≤ 4 |
| PR6 | electrode_pairs | `check_electrode_pairs_positive` | 10 ≤ pairs ≤ 100 |
| PR7 | end_electrode_config | `check_end_electrode_config_valid` | one of [BothNegative, BothPositive, PositiveNegative] |

### Pouch Constraints (PO1-PO7)

| ID | Name | Function | Rule |
|----|------|----------|------|
| PO1 | anode_offset | `check_pouch_anode_offset_positive` | 0.5 ≤ offset ≤ 5.0 mm |
| PO2 | separator_offset | `check_pouch_separator_offset_positive` | 0.5 ≤ offset ≤ 5.0 mm |
| PO3 | separator_covers_anode | `check_pouch_separator_larger_than_anode` | sep_offset ≥ anode_offset |
| PO4 | stacks_count | `check_pouch_stacks_positive` | 1 ≤ num_stacks ≤ 4 |
| PO5 | electrode_pairs | `check_pouch_electrode_pairs_positive` | 5 ≤ pairs ≤ 100 |
| PO6 | end_electrode_config | `check_pouch_end_electrode_config_valid` | valid option |
| PO7 | packaging_offsets | `check_pouch_packaging_offsets` | packaging offsets positive |

### Cylindrical Constraints (CY1-CY7)

| ID | Name | Function | Rule |
|----|------|----------|------|
| CY1 | mandrel_diameter | `check_cylindrical_mandrel_diameter` | valid mandrel size |
| CY2 | winding_clearance | `check_cylindrical_winding_clearance` | clearance > 0 |
| CY3 | tension_factor | `check_cylindrical_tension_factor` | valid tension |
| CY4 | tab_type | `check_cylindrical_tab_type_valid` | valid tab type |
| CY5 | jelly_roll_fits | `check_cylindrical_jelly_roll_fits` | roll fits in can |
| CY6 | header_height | `check_cylindrical_header_height` | header fits |
| CY7 | format_consistency | `check_cylindrical_format_consistency` | dimensions match format |

---

## Files to Modify (in order)

### 1. `forge/engine/validation/constraint_validator.py`

**Add at top (after imports):**

```python
import time
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ConstraintResult:
    constraint_id: str      # "C1", "PR3", "CY7", etc.
    name: str               # "np_ratio", "internal_height", etc.
    passed: bool
    actual_value: Any       # the value that was checked (None if field missing)
    threshold: Any          # the bound/range/expected value
    message: str            # human-readable; empty string if passed
    check_time_ms: float    # milliseconds for this check
```

**Add the CONSTRAINT_REGISTRY:**

```python
# Registry: maps constraint ID → (human_name, function, threshold_description)
# Used for full report card generation and thesis tables

_COMMON_REGISTRY: list[tuple[str, str, ConstraintFunc]] = [
    ("C1", "np_ratio", check_np_ratio),
    ("C2", "cathode_loading", check_cathode_loading_reasonable),
    ("C3", "anode_loading", check_anode_loading_reasonable),
    ("C4", "separator_porosity", check_separator_porosity_valid),
    ("C5", "electrolyte_concentration", check_electrolyte_salt_concentration),
    ("C6", "cathode_material", check_cathode_material_valid),
    ("C7", "anode_material", check_anode_material_valid),
]

_PRISMATIC_REGISTRY: list[tuple[str, str, ConstraintFunc]] = [
    ("PR1", "internal_height", check_internal_height_positive),
    ("PR2", "internal_width", check_internal_width_positive),
    ("PR3", "internal_thickness", check_internal_thickness_positive),
    ("PR4", "cathode_fits_cavity", check_cathode_fits_in_cavity),
    ("PR5", "stacks_count", check_stacks_positive),
    ("PR6", "electrode_pairs", check_electrode_pairs_positive),
    ("PR7", "end_electrode_config", check_end_electrode_config_valid),
]

_POUCH_REGISTRY: list[tuple[str, str, ConstraintFunc]] = [
    ("PO1", "anode_offset", check_pouch_anode_offset_positive),
    ("PO2", "separator_offset", check_pouch_separator_offset_positive),
    ("PO3", "separator_covers_anode", check_pouch_separator_larger_than_anode),
    ("PO4", "stacks_count", check_pouch_stacks_positive),
    ("PO5", "electrode_pairs", check_pouch_electrode_pairs_positive),
    ("PO6", "end_electrode_config", check_pouch_end_electrode_config_valid),
    ("PO7", "packaging_offsets", check_pouch_packaging_offsets),
]

_CYLINDRICAL_REGISTRY: list[tuple[str, str, ConstraintFunc]] = [
    ("CY1", "mandrel_diameter", check_cylindrical_mandrel_diameter),
    ("CY2", "winding_clearance", check_cylindrical_winding_clearance),
    ("CY3", "tension_factor", check_cylindrical_tension_factor),
    ("CY4", "tab_type", check_cylindrical_tab_type_valid),
    ("CY5", "jelly_roll_fits", check_cylindrical_jelly_roll_fits),
    ("CY6", "header_height", check_cylindrical_header_height),
    ("CY7", "format_consistency", check_cylindrical_format_consistency),
]
```

**Modify `validate_physics()`:**

Current signature returns `ValidationResult`. New version additionally populates `constraint_results`:

```python
def validate_physics(cell_dict: dict, cell_type: str = "prismatic") -> ValidationResult:
    errors = []
    constraint_results: list[ConstraintResult] = []

    # Select registry based on cell type
    cell_type_lower = cell_type.lower()
    if cell_type_lower == "pouch":
        registry = _COMMON_REGISTRY + _POUCH_REGISTRY
    elif cell_type_lower == "cylindrical":
        registry = _COMMON_REGISTRY + _CYLINDRICAL_REGISTRY
    else:
        registry = _COMMON_REGISTRY + _PRISMATIC_REGISTRY

    for constraint_id, name, check_fn in registry:
        t0 = time.perf_counter_ns()
        error = check_fn(cell_dict)
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000

        if error is not None:
            errors.append(error)
            constraint_results.append(ConstraintResult(
                constraint_id=constraint_id,
                name=name,
                passed=False,
                actual_value=error.value,
                threshold=error.constraint,
                message=error.message,
                check_time_ms=elapsed_ms,
            ))
        else:
            constraint_results.append(ConstraintResult(
                constraint_id=constraint_id,
                name=name,
                passed=True,
                actual_value=None,  # could extract, but adds complexity
                threshold="",
                message="",
                check_time_ms=elapsed_ms,
            ))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        level="physics",
        constraint_results=constraint_results,
    )
```

**Important:** The old `COMMON_CONSTRAINTS`, `PRISMATIC_CONSTRAINTS`, etc. lists must remain for backward compatibility. The registry is an addition, not a replacement. But `validate_physics()` now uses the registry instead of the plain lists.

### 2. `forge/engine/validation/schema_validator.py`

**Extend `ValidationResult`:**

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError]
    level: str = "schema"
    constraint_results: list = field(default_factory=list)  # list[ConstraintResult]
```

Note: Can't type-hint `list[ConstraintResult]` here without a circular import (ConstraintResult is in constraint_validator.py which imports from schema_validator.py). Use plain `list` with a comment, or move ConstraintResult to schema_validator.py.

**Better approach:** Define `ConstraintResult` in `schema_validator.py` (alongside `ValidationError` and `ValidationResult`) to avoid circular imports. Then import it in `constraint_validator.py`.

### 3. `forge/axiom/supervisor/result.py`

**Add field to `GenerationResult`:**

```python
from forge.engine.validation.schema_validator import ConstraintResult  # new import

@dataclass
class GenerationResult:
    ...existing fields...
    # Per-attempt constraint results for experiment logging
    attempt_constraint_results: list[list[ConstraintResult]] = field(default_factory=list)
```

Each inner list is one attempt's full constraint report card.

### 4. `forge/axiom/supervisor/driver.py`

**In the retry loop (around line 141-147):**

```python
validation_result = validate_cell_definition(yaml_content, cell_type=cell_type_lower)

# Capture per-constraint results for this attempt
if validation_result.constraint_results:
    attempt_constraint_results.append(validation_result.constraint_results)

if not validation_result.valid:
    feedback = validation_result.to_llm_feedback()
    ...existing retry logic...
```

Initialize `attempt_constraint_results = []` at the top of the function (near `retry_reasons = []`).

Thread it through to the `GenerationResult` constructor calls (lines ~178, ~206, ~226).

### 5. `forge/api/schemas/models.py`

**Add new Pydantic models:**

```python
class ConstraintResultSchema(BaseModel):
    constraint_id: str
    name: str
    passed: bool
    actual_value: Any = None
    threshold: Any = None
    message: str = ""
    check_time_ms: float = 0.0

class AttemptRecord(BaseModel):
    attempt: int
    valid: bool
    errors: list[str] = []
    constraint_results: list[ConstraintResultSchema] = []  # NEW
```

### 6. `forge/api/routes/pipeline.py`

**Modify `_build_attempt_records()`** to include constraint results from `GenerationResult.attempt_constraint_results`.

**Add `supervised` parameter:**

```python
@router.post("/pipeline", response_model=PipelineResponse)
def run_pipeline(payload: PipelineRequest, supervised: bool = True) -> PipelineResponse:
```

When `supervised=False`:
- Set `max_retries = 0` (or 1 — single attempt)
- Still run validation (measurement only)
- No feedback sent to LLM
- Response includes full constraint report card

**Add structured logging after each attempt:**

```python
logger.info(
    "constraint_check",
    extra={
        "attempt": attempt_number,
        "supervised": supervised,
        "design_valid": result.valid,
        "constraints_passed": sum(1 for c in constraint_results if c.passed),
        "constraints_failed": [c.constraint_id for c in constraint_results if not c.passed],
    },
)
```

### 7. Pipeline route `_build_attempt_records()` update

Map `GenerationResult.attempt_constraint_results[i]` to `AttemptRecord.constraint_results` using the Pydantic schema.

---

## Circular Import Risk

`ConstraintResult` is defined in `constraint_validator.py` which imports `ValidationError` and `ValidationResult` from `schema_validator.py`. If we add `constraint_results: list[ConstraintResult]` to `ValidationResult`, we have a circular import.

**Solution:** Define `ConstraintResult` in `schema_validator.py` alongside the other dataclasses. It has no dependencies on constraint_validator.py — it's a pure data container.

---

## Test Impact

- Existing tests should pass unchanged (constraint_results defaults to empty list)
- `validate_physics()` still returns `ValidationResult` with `.valid` and `.errors`
- New field `constraint_results` is additional, not replacing anything
- The `supervised=False` mode is new behavior — needs a new test or manual verification

---

## Verification

```bash
# Run full test suite
pytest --tb=short -q

# Lint
ruff check forge/engine/validation/ forge/axiom/supervisor/ forge/api/

# Manual API test (supervised=True, existing behavior)
curl -X POST http://localhost:8000/api/v1/pipeline \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a 100Ah NMC811 prismatic cell", "backend": "ollama"}'

# Manual API test (supervised=False, single attempt)
curl -X POST "http://localhost:8000/api/v1/pipeline?supervised=false" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a 100Ah NMC811 prismatic cell", "backend": "ollama"}'
```

---

## Do NOT

- Change the LLM prompt templates
- Change the CPN supervision logic
- Change the PyBaMM simulation configuration
- Break backward compatibility (existing callers that don't read constraint_results must still work)
- Modify tests for the Optuna run or autoresearch engine
