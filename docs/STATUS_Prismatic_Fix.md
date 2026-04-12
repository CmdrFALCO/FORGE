# Prismatic Fix — Current Status

**Last updated:** 2026-03-26 ~13:00 CET

## What's Done

### Prompt Builder Fixes (all in `forge/axiom/generator/prompt_builder.py`)
- Fixed all envelope field names: `height_mm` → `cell_height_mm`, `width_mm` → `cell_width_mm`, etc.
- Fixed all wall field names: `top_mm` → `wall_top_mm`, etc.
- Added missing `envelope.internals` section (insulation_coating_um, corner radii)
- Fixed `specific_capacity_mah_g` → `rev_spec_capacity_mahg`
- Fixed `coating_thickness_um` → `coating_thickness_0pct_um` + `coating_thickness_100pct_um`
- Fixed `porosity` (decimal) → `porosity_pct` (percentage)
- Added `salt_concentration_m` to electrolyte
- Fixed `header_mass_g` → `lid_thickness_mm` + `case_material` in packaging
- Added `current_collection` section (tabs with cathode/anode)
- Added `fixing_tape_width_mm` to insulation
- Updated PRISMATIC_EXAMPLE_CELL to use all correct schema field names
- Updated output format checklist to include `current_collection`

### Schema Validator Fix (`forge/engine/validation/schema_validator.py`)
- Added structural skeleton hints for `current_collection` and `packaging` in retry feedback

### Experiment Runner Fix (`forge/experiments/run_experiments.py`)
- Added `--cell-type` filter argument
- Dynamic experiment choices from EXPERIMENTS dict

### Experiment Config (`forge/experiments/experiment_config.py`)
- Added 4 prismatic fix experiments: exp1_pfix, exp2_pfix, exp1h_pfix, exp2h_pfix
- Added CLAUDE_HAIKU backend config

## What's NOT Done — Remaining Issue

### Last Error: `fixing_tape_width_mm` type validation
The LLM generates `fixing_tape_width_mm: 8.0` but the schema rejects it with "not valid under any of the given schemas." This is likely a schema type issue (integer vs float, or a oneOf pattern that doesn't accept the float).

**To investigate:**
```bash
.venv311/bin/python -c "
import json
schema = json.loads(open('forge/data/templates/prismatic_master.schema.json').read())
ftw = schema['properties']['packaging']['properties']['insulation']['properties']['fixing_tape_width_mm']
print(json.dumps(ftw, indent=2))
"
```

This should show what type/format the schema expects. Fix the schema or the prompt example accordingly.

**Progress: went from 28 schema errors → 1 schema error.** Once this last field is fixed, prismatic should start passing schema validation and reaching physics constraints.

## Uncommitted Changes

All changes are local, NOT committed or pushed:
- `forge/axiom/generator/prompt_builder.py` — major prismatic prompt overhaul
- `forge/engine/validation/schema_validator.py` — structural feedback hints
- `forge/experiments/run_experiments.py` — --cell-type filter
- `forge/experiments/experiment_config.py` — prismatic fix experiment definitions

## Experiments Completed (results saved)

| Experiment | File | Status |
|-----------|------|--------|
| exp1 (Sonnet unsupervised) | exp1_baseline_cloud.jsonl | Done, 326/500 valid |
| exp2 (Sonnet supervised) | exp2_supervised_cloud.jsonl | Done, 336/500 valid |
| exp1h (Haiku unsupervised) | exp1h_baseline_haiku.jsonl | Done, 309/500 valid |
| exp2h (Haiku supervised) | exp2h_supervised_haiku.jsonl | Done, 336/500 valid |
| exp1_pfix pilot | exp1_prismatic_fix.jsonl | 20 prompts, 0 valid (1 remaining schema error) |

## Next Steps After Restart

1. Investigate and fix `fixing_tape_width_mm` schema type issue
2. Delete pilot results: `rm forge/experiments/results/exp1_prismatic_fix.jsonl`
3. Re-run 20-prompt pilot
4. If pilot passes, commit all changes and run full prismatic experiments (164 prompts × 4 experiments)
5. Update ANALYSIS_Exp1_Exp2_Results.md with combined numbers
