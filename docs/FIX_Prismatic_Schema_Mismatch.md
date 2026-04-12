# Prismatic Schema Mismatch — Complete Fix List

## Root Cause
The prismatic system prompt in `forge/axiom/generator/prompt_builder.py` uses shorthand field names that don't match `forge/data/templates/prismatic_master.schema.json`. 100% of prismatic designs fail schema validation.

## All Mismatches (fix all in one pass)

### Envelope External (3 mismatches)
| Prompt says | Schema requires |
|-------------|----------------|
| `height_mm` | `cell_height_mm` |
| `width_mm` | `cell_width_mm` |
| `thickness_mm` | `cell_thickness_mm` |

### Envelope Walls (4 mismatches)
| Prompt says | Schema requires |
|-------------|----------------|
| `top_mm` | `wall_top_mm` |
| `bottom_mm` | `wall_bottom_mm` |
| `front_back_mm` | `wall_front_back_mm` |
| `sides_mm` | `wall_sides_mm` |

### Envelope Internals (3 missing)
Schema requires `envelope.internals` with:
- `insulation_coating_um`
- `external_corner_radius_mm`
- `internal_corner_radius_mm`

Prompt has NO mention of internals.

### Electrochemistry Cathode/Anode (6 mismatches per electrode = 12)
| Prompt says | Schema requires |
|-------------|----------------|
| `specific_capacity_mah_g` | `rev_spec_capacity_mahg` |
| `coating_thickness_um` (single) | `coating_thickness_0pct_um` + `coating_thickness_100pct_um` |
| `porosity` (decimal 0.20-0.40) | `porosity_pct` (percentage 20-40) |

### Separator (1 mismatch)
| Prompt says | Schema requires |
|-------------|----------------|
| `porosity` (decimal) | `porosity_pct` (percentage) |

### Electrolyte (1 missing)
Schema requires `salt_concentration_m` — prompt mentions it in parameter schema but example omits it.

### Packaging (1 mismatch)
| Prompt says | Schema requires |
|-------------|----------------|
| `header_mass_g` | `lid_thickness_mm` |

Also missing: `case_material` in the example.

## Files to Fix
1. `forge/axiom/generator/prompt_builder.py` — PRISMATIC_PARAMETER_SCHEMA text AND PRISMATIC_EXAMPLE_CELL YAML
2. Both must use exact schema field names

## Why Pouch Works
Pouch prompt and schema are aligned on field names. The pouch prompt was written to match the schema; the prismatic prompt was written with shorthand names that diverged.
