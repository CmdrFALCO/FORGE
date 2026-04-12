# Fix Prismatic Template Conversion — Complete Task

## Working Directory
```
~/Projects/CmdrFALCO/FORGE/
```

## Problem

The prismatic cell prompt builder was fixed to generate schema-compliant YAML (correct field names like `cell_height_mm`, `material_name`, `porosity_pct`). The LLM now generates correct output. But the **conversion function** (`forge/engine/conversion/template_to_input.py`) uses OLD shorthand field names (`name` instead of `material_name`, `density_gcm3` instead of `density_g_cm3`, flat envelope instead of nested `envelope.external.*`).

The conversion was partially fixed but still fails on `coating_density_gcm3` — and likely has more mismatches.

## Root Cause

Two different naming conventions exist in the codebase:
1. **Schema format** (what the LLM generates): `material_name`, `density_g_cm3`, `rev_spec_capacity_mahg`, `coating_thickness_0pct_um`, `porosity_pct`, nested `envelope.external.*` / `envelope.walls.*`
2. **Legacy format** (what the conversion expects): `name`, `density_gcm3`, `specific_capacity_mah_g`, `coating_thickness_um`, `porosity`, flat `envelope.cell_height_mm`

The conversion must accept BOTH formats for backward compatibility.

## What's Already Fixed

1. **`_map_geometry()`** — flattens `envelope.external.*` and `envelope.walls.*` into a flat dict before reading
2. **`from_template_format()`** — reads `stack_config.architecture.num_stacks` with fallback to `stack_config.stacks`, packaging nested paths with fallbacks
3. **`_map_cathode/anode/separator/electrolyte()`** — `material_name` with fallback to `name` (using `or` pattern)
4. **Electrolyte** — `density_g_cm3` with fallback to `density_gcm3`

## What Still Needs Fixing

The pattern is always the same: try schema field name first, fall back to legacy field name.

### Systematic approach

1. Read the schema format from a real LLM output. Use this command:
```bash
.venv311/bin/python -c "
import json, yaml
results = [json.loads(line) for line in open('forge/experiments/results/exp1_prismatic_fix.jsonl')]
raw = results[0]['attempts'][0]['raw_llm_output']
print(raw)
"
```

2. Read the conversion function completely:
```
forge/engine/conversion/template_to_input.py
```

3. For every `_require_nested(dict, "field")` call in the prismatic conversion path (`_map_geometry`, `_map_sheet_geometry`, `_map_cathode`, `_map_anode`, `_map_separator`, `_map_electrolyte`, `from_template_format`), check if the LLM output uses a different field name. If so, add the fallback pattern:
```python
# Before (breaks on schema format):
value = _require_nested(cathode, "coating_density_gcm3")

# After (accepts both):
value = (_get_nested(cathode, "coating_density_g_cm3", None)
         or _require_nested(cathode, "coating_density_gcm3"))
```

4. **IMPORTANT: Do NOT change the function signatures or return types.** Only add field name fallbacks inside the existing mapping functions.

5. **IMPORTANT: Do NOT break existing tests.** Run `pytest tests/engine/conversion/ -q` after every change. All 76 tests must pass.

### Known remaining mismatches (non-exhaustive)

| Conversion expects | Schema/LLM uses | Location |
|-------------------|-----------------|----------|
| `coating_density_gcm3` | Not in LLM output — needs default from material_defaults | `_map_cathode`, `_map_anode` |
| `density_gcm3` | `density_g_cm3` | `_map_separator` |
| `porosity` | `porosity_pct` (and value is percentage not decimal) | cathode, anode, separator |
| `specific_capacity_mah_g` | `rev_spec_capacity_mahg` | cathode, anode |
| `coating_thickness_um` | `coating_thickness_0pct_um` | cathode, anode |
| `collector_material` | May be missing — use default | cathode, anode |

### The porosity conversion issue

The schema uses `porosity_pct` (e.g., 30 for 30%). The internal model uses `porosity` as a fraction (0.30). If the conversion reads `porosity_pct`, it needs to divide by 100. Check what the `PrismaticCellInput` model expects and convert accordingly.

## Verification

After fixing all mismatches:

```bash
# 1. Existing tests still pass
.venv311/bin/python -m pytest tests/engine/conversion/ -q --tb=short

# 2. Direct conversion test on saved LLM output
.venv311/bin/python -c "
import json, yaml
results = [json.loads(line) for line in open('forge/experiments/results/exp1_prismatic_fix.jsonl')]
raw = results[0]['attempts'][0]['raw_llm_output']
template = yaml.safe_load(raw)
from forge.engine.conversion.template_to_input import from_template_format
result = from_template_format(template)
print('SUCCESS:', result.cell_name)
print('  Height:', result.case_geometry.cell_height_mm)
print('  Cathode:', result.cathode.name)
"

# 3. Full test suite
.venv311/bin/python -m pytest tests/ -q --tb=short -x

# 4. Ruff
ruff check forge/engine/conversion/template_to_input.py
```

## After Conversion Works — Run Pilot

```bash
rm -f forge/experiments/results/exp1_prismatic_fix.jsonl
export ANTHROPIC_API_KEY="$(grep ANTHROPIC_API_KEY ~/.bashrc | tail -1 | cut -d'"' -f2)"
.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp1_pfix \
    --corpus forge/experiments/prompt_corpus_v1.json \
    --cell-type prismatic \
    --limit 20
```

If at least 10/20 prismatic prompts produce valid designs, the fix is working. Then:

1. Commit the prompt builder + conversion fixes
2. Run full prismatic experiments (all 164 prompts × 4 experiment configs)

## Do NOT

- Change the JSON schema files (`forge/data/templates/*.schema.json`)
- Change the LLM prompt to match the old field names (the schema names ARE the correct names)
- Change any model dataclasses (`PrismaticCellInput`, `PrismaticGeometry`, etc.)
- Skip running tests after changes
- Commit without verifying conversion works on real LLM output
