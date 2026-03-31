# AXIOM Supervised Failure Mode Analysis

*Generated: 2026-03-30*
*Scope: All 7 supervised experiments, focused on persistent rejects (failures surviving 4 retry attempts)*

---

## Executive Summary

**Every persistent supervised failure across all 7 models is a schema-level error (Category A or B). Zero physics constraint violations (Category C) survive to final rejection.** The AXIOM supervision loop is 100% effective at correcting engineering errors — what it cannot fix are YAML formatting issues, field name misspellings, and out-of-range values where the model has a strong but incorrect prior.

| Model | Supervised Rejects | Cat A (Schema) | Cat B (Dimensions) | Cat C (Physics) | Cat D (Other) |
|---|---|---|---|---|---|
| **Mistral Small 3.1** | **50** | 0 | **50** | 0 | 0 |
| **Llama 3.2 3B** | **87** | **77** | **10** | 0 | 0 |
| **Llama 3.1 8B** | **22** | **12** | **10** | 0 | 0 |
| Sonnet 4.6 | 15 | **15** | 0 | 0 | 0 |
| Haiku 4.5 | 11 | **11** | 0 | 0 | 0 |
| Qwen 3.5 9B | 11 | **11** | 0 | 0 | 0 |
| Qwen 3.5 27B | 3 | **3** | 0 | 0 | 0 |

*Note: `raw_llm_output` is null for all rejected records across all experiments. Failure details are reconstructed from `feedback_sent` validation error messages and parsed design fields.*

---

## 1. Mistral Small 3.1 Supervised — 50 Rejects (10.0%)

### Diagnosis: Single field, single failure mode

**100% Category B (impossible dimensions).** Every reject is prismatic with `cathode_height_mm` outside the schema range [50, 150]. Mistral outputs 168–178 mm (modal: 175 mm). No other cell type is affected.

### Why 175 mm?

175 mm is a realistic cathode height for large-format prismatic cells (BYD Blade-class). Mistral has a strong, correct-in-the-real-world prior that happens to violate this schema's upper bound of 150 mm.

### Why supervision doesn't help (17% recovery rate)

The feedback message says `"175.0 is not valid under any of the given schemas"` but **does not reveal the valid range**. Mistral responds by making ±1–3 mm adjustments:

| Attempt | Typical sequence | Distance from valid max (150) |
|---|---|---|
| 1 | 168 mm | 18 mm over |
| 2 | 175 mm | 25 mm over |
| 3 | 174 mm | 24 mm over |
| 4 | 173 mm | 23 mm over |

Six dominant retry sequences account for 40/50 rejects — the model is highly deterministic. Of 150 consecutive attempt pairs, 59% move *further* from the valid range.

The 10/60 recoveries from unsupervised failures were on *different* fields (case_density, length_mm, cell_thickness_mm) where the gap between Mistral's output and the valid range was smaller. The cathode_height gap (24 mm) is never bridged.

### Breakdown

- **Cell type**: 50/164 prismatic (30.5%), 0/166 cylindrical, 0/170 pouch
- **Chemistry**: NMC-811 36.6%, LFP 30.0%, NMC-111 27.9%, NMC-622 27.5% — roughly uniform
- **Difficulty**: uniform (27–33%)
- **Prompt style**: detailed 35.9%, terse 30.6%, natural_language 25.0%

### Example prompts

- **P-002** (prismatic/NMC-111/standard/detailed): cathode_height attempts [168, 175, 174, 173]
- **P-010** (prismatic/NMC-111/edge_case/natural_language): cathode_height attempts [174, 175, 176, 177]
- **P-324** (prismatic/NMC-622/contradictory/terse): also fails cathode_width_mm (95–99 vs min 100) — the only prompt with a second failing field

---

## 2. Llama 3.2 3B Supervised — 87 Rejects (17.4%)

### Diagnosis: Multiple overlapping schema errors, retries make things worse

77 Category A (schema-level), 10 Category B (dimensions). The dominant pattern is `rev_spec_capacity_mahg` errors — either misspelling the field name or producing out-of-range values.

### Sub-category breakdown

| Sub-category | Count | Description |
|---|---|---|
| **A1: `rev_spec_capacity_mahg` misspelled** | **39** (45%) | Renamed to `rev_spec_capacity_ahg`, `_ah`, `_mwh`, `capacity_ahg` |
| **A2: `rev_spec_capacity_mahg` value OOR** | **19** (22%) | Cathode: 240–310 (valid: 140–220). Anode: 140–280 (valid: 300–500) |
| **A3: Prismatic `internals` missing** | **8** (9%) | `envelope.internals` subsection omitted |
| **A4: Mixed missing fields** | **5** (6%) | Missing `separator`, `electrolyte`, `insulation` sections |
| **B1: Dimension/packaging OOR** | **10** (11%) | Pouch offset, prismatic height/width, cylindrical length |
| **A5: Other** | **6** (7%) | `can_material` strings, separator thickness OOR |

### The retry-degradation pathology

Retries make Llama 3B *worse*, not better:

| Attempt | Avg errors per prompt |
|---|---|
| 1 | 1.5 |
| 2 | 2.3 |
| 3 | 2.9 |
| 4 | 3.3 |

The dominant failure transition: the model receives feedback that `rev_spec_capacity_mahg = 250.0` is out of range. Instead of adjusting the value, it **renames the field** to `rev_spec_capacity_ahg`, introducing *two* new errors (missing required field + unexpected field) while eliminating zero. This OOR→misspelling transition accounts for 38/87 retry degradations. Only 4 prompts ever recover from a misspelling back to correct field name.

### Breakdown

- **Cell type**: cylindrical 34.3%, prismatic 11.0%, pouch 7.1% — cylindrical concentrates 57/87 rejects
- **Chemistry**: **LFP 30.6%**, NMC-811 14.5%, NMC-111 14.2%, NMC-622 10.4%
- **Prompt style**: **natural_language 30.2%**, detailed 12.5%, terse 4.3% — the sharpest predictor
- **Difficulty**: uniform (15.5–20.8%)

### Hotspot: cylindrical + natural_language + LFP = 81% failure rate

| Combination | Reject Rate |
|---|---|
| cylindrical / LFP / natural_language | **81.2%** (13/16) |
| cylindrical / NMC-811 / natural_language | **68.8%** (11/16) |
| cylindrical / NMC-111 / natural_language | **56.2%** (9/16) |
| cylindrical / LFP / detailed | **43.8%** (7/16) |

The model's weakest domain knowledge is cylindrical cell electrochemistry parameters, especially for LFP cathodes (lower specific capacity ~160–170 mAh/g vs NMC ~170–200 mAh/g). Natural language prompts compound this by providing less structural guidance.

### Anode/cathode confusion

The anode `rev_spec_capacity_mahg` errors (values 140–280 vs valid 300–500) overlap with typical *cathode* ranges (140–220). The model appears to not distinguish between the two electrodes' capacity ranges, outputting cathode-appropriate values for anode fields.

### Example prompts

- **P-005** (cylindrical/NMC-111/underspecified/natural_language): Attempt 1 has OOR value 250.0; attempts 2–4 the model "fixes" by renaming to `rev_spec_capacity_ahg`, introducing 2 new errors
- **P-026** (cylindrical/NMC-111/contradictory/terse): Cathode values across 4 attempts: 250→280→300→310 — moving *away* from the valid range
- **P-081** (prismatic/NMC-622/edge_case/natural_language): Missing `envelope.internals` on all 4 attempts — never learns to add this section from feedback

---

## 3. Llama 3.1 8B Supervised — 22 Rejects (4.4%)

### Diagnosis: Three distinct failure modes, each model-specific

| Sub-category | Count | Description |
|---|---|---|
| **B1: Cylindrical geometry OOR** | **10** (45%) | diameter 170–220 mm (valid: 10–60), length 280–800 mm (valid: 30–100) |
| **A1: Separator thickness OOR** | **7** (32%) | 3–5 µm values (valid: 9–25); all contradictory difficulty |
| **A2: Structural collapse** | **2** (9%) | Entire subsections missing or wrongly nested |
| **B2: Prismatic dimensions OOR** | **2** (9%) | cathode_height or cell_thickness out of range |
| **A3: case_density wrong value** | **1** (5%) | 7.85 g/cm³ (steel) where schema expects 2.6–2.8 (aluminum) |

### B1: Cylindrical geometry — the "module confusion"

The model outputs cell dimensions 3–10× too large, consistent with EV battery *module* dimensions rather than individual cell dimensions. The diagnostic clue: P-485 outputs `diameter_mm: 18650` on attempt 4 — the model confuses the format name (18650) with a dimension value.

Retry behavior is non-convergent. The model fluctuates within the out-of-range band:

| Prompt | diameter_mm attempts | length_mm attempts |
|---|---|---|
| P-042 | 170 → 160 → 186 → 180 | 350 → 300 → — → — |
| P-088 | 220 → 216 → 186 → 216 | 300 → 276 → 276 → — |
| P-211 | 220 → 216 → 186 → 186 | 800 → 720 → 650 → — |

Application correlation: grid_storage prompts (requesting 100–290 Ah) account for most failures. Mean requested capacity for failures: 134 Ah vs 41 Ah for passes. The model doesn't know that cylindrical cells physically max out at ~26 Ah (4680 form factor).

### A1: Separator thickness — unit confusion

All 7 prompts are contradictory difficulty. Values of 3–5 suggest the model is thinking in mm (3.5 mm ≈ 35 µm) but writing to a `_um` field. When told the value is invalid, it sometimes multiplies by 10 (3.8→38, 4.2→42), overshooting the 25 µm maximum.

| Prompt | thickness_um attempts | Note |
|---|---|---|
| P-071 | 3.5 → 3.5 → 3.5 → 3.5 | Perfectly stuck |
| P-151 | 4.2 → 4.2 → 4 → **42** | Over-corrects to 42 (>25 max) |
| P-278 | 3.8 → 3.8 → 38 → 38 | Over-corrects to 38 (>25 max) |

### Example prompts

- **P-042** (cylindrical/NMC-111/standard): Grid storage prompt requesting high capacity. Diameter oscillates 160–186 mm across 4 attempts, never approaching the 60 mm maximum.
- **P-071** (prismatic/NMC-622/contradictory): Separator thickness locked at 3.5 µm on all 4 attempts. Zero adaptation to feedback.
- **P-314** (prismatic/NMC-622/contradictory): Structural collapse — required subsections nested under wrong parent keys, 10–13 missing field errors per attempt.

---

## 4. Sonnet 4.6 Supervised — 15 Rejects (3.0%)

### Diagnosis: Prismatic cathode sheet geometry, single-field persistence

**100% prismatic.** All 15 rejects fail on `cathode_width_mm` and/or `cathode_height_mm`:

| Error Field | Count | Schema Range | Sonnet Values |
|---|---|---|---|
| `cathode_width_mm` | 11 | [100, 350] | 9 too small (50–95), 2 too large (375–380) |
| `cathode_height_mm` | 6 | [50, 150] | All too large (155–185) |

The model hovers just below the 100 mm minimum for width, producing values like 85, 90, 93 across 4 retries without ever crossing the boundary.

### Example prompt

- **P-329** (prismatic/NMC-622/standard/detailed): cathode_width_mm attempts: 58→93→90→50. Regresses from 93 back to 50 on the final attempt.

---

## 5. Haiku 4.5 Supervised — 11 Rejects (2.2%)

### Diagnosis: Same prismatic pattern as Sonnet

6 rejects on `cathode_height_mm` (155–185 mm, above 150 max), 5 on `cathode_width_mm` (88–360 mm, outside [100, 350]). One novel error: P-272 outputs `case_density_g_cm3 = "Steel"` (string where number expected).

---

## 6. Qwen 3.5 9B Supervised — 11 Rejects (2.2%)

### Diagnosis: case_density material confusion

**9/11 are `case_density_g_cm3 = 7.85`** — the model defaults to steel density (7.85 g/cm³) where the schema expects aluminum density (2.6–2.8 g/cm³). All 11 are prismatic. This is a chemistry knowledge error: prismatic battery cells use aluminum cases, but the model associates prismatic enclosures with steel.

The remaining 2 have dimension or envelope thickness errors.

---

## 7. Qwen 3.5 27B Supervised — 3 Rejects (0.6%)

### Diagnosis: Same cathode_width_mm as Sonnet

All 3 are `cathode_width_mm = 85.0` (below 100 mm minimum). Same retry pattern: model fixes all other errors but cannot cross the 100 mm boundary for this field.

---

## Cross-Model Error Field Heatmap

| Error Field | Mistral (50) | Llama 3B (87) | Llama 8B (22) | Sonnet (15) | Haiku (11) | Qwen 9B (11) | Qwen 27B (3) |
|---|---|---|---|---|---|---|---|
| `cathode_height_mm` | **50** | — | 1 | 6 | 6 | — | — |
| `rev_spec_capacity_mahg` | — | **58** | — | — | — | — | — |
| `geometry.diameter_mm` | — | — | **10** | — | — | — | — |
| `geometry.length_mm` | — | — | 5 | — | — | — | — |
| `cathode_width_mm` | 1 | — | — | **11** | 5 | 1 | **3** |
| `separator.thickness_um` | — | 3 | **7** | — | — | — | — |
| `case_density_g_cm3` | — | — | 1 | — | 1 | **9** | — |
| `can_material` (enum) | — | 1 | 6* | — | — | — | — |
| `envelope.internals` missing | — | **8** | — | — | — | — | — |
| dimension/packaging OOR | — | 10 | 2 | — | — | 2 | — |
| structural collapse | — | 5 | 2 | — | — | — | — |

*Llama 8B `can_material` errors are concurrent with cylindrical geometry errors and ARE recoverable on retry — they are not the primary cause of rejection.

---

## Key Cross-Cutting Findings

### 1. The feedback gap is the root cause

The validation error format `"175.0 is not valid under any of the given schemas"` does not include the valid range. Every stubborn failure involves a model that has a strong prior for a value 10–50% outside the valid range and makes small adjustments that never bridge the gap. **Including the valid range in the error message** (e.g., `"cathode_height_mm must be between 50 and 150, got 175"`) would likely resolve the majority of persistent failures across all models.

### 2. Each model has a signature failure

| Model | Signature Error | Root Cause |
|---|---|---|
| Mistral Small 3.1 | `cathode_height_mm = 175` | Strong prior for BYD Blade-class dimensions |
| Llama 3.2 3B | `rev_spec_capacity_mahg` misspelling | Tokenization artifact + anode/cathode confusion |
| Llama 3.1 8B | cylindrical diameter 170+ mm | Cell vs module dimension confusion |
| Sonnet 4.6 | `cathode_width_mm = 85` | Persistently below 100 mm minimum |
| Haiku 4.5 | `cathode_height_mm = 165` | Same as Mistral but milder |
| Qwen 3.5 9B | `case_density = 7.85` | Steel vs aluminum material confusion |
| Qwen 3.5 27B | `cathode_width_mm = 85` | Same as Sonnet |

### 3. Retries help large models, hurt small ones

| Model | Avg errors attempt 1 → attempt 4 | Trajectory |
|---|---|---|
| Qwen 27B | converges | Fixes all but 1 field |
| Sonnet | converges | Fixes all but 1 field |
| Llama 8B | flat | Oscillates in same range |
| Mistral | flat | ±1 mm adjustments, no convergence |
| Llama 3B | **diverges (1.5 → 3.3)** | Renames fields, introduces new errors |

Below ~8B parameters, the model lacks the capacity to correctly interpret structured feedback and apply targeted fixes. Llama 3B's dominant failure transition — receiving "value out of range" feedback and responding by *renaming the field* — demonstrates that the model does not understand the correction semantics.

### 4. Prismatic is the universal hard geometry

Prismatic cells account for the majority of failures in 5/7 models (all except Llama 8B, whose weakness is cylindrical, and Llama 3B, whose cylindrical failure rate exceeds prismatic). The `cathode_width_mm` and `cathode_height_mm` fields in the prismatic sheet geometry are the two most commonly failing fields across the cloud and larger local models.

### 5. No Category C failures exist

Not a single physics constraint violation survived 4 supervised retries in any model. When a design is parseable and reaches the constraint checker, the feedback loop always corrects it. The remaining 199 total supervised rejects (across all 7 models) are all parsing or schema-level errors that prevent constraint checking from ever running.

---

## Potential Mitigations (Not Yet Implemented)

| Fix | Scope | Expected Impact |
|---|---|---|
| **Include valid range in validation errors** | All models | Likely resolves Mistral (50), Sonnet (15), Haiku (6), Qwen 27B (3), partial Llama 8B and 3B |
| **Accept `nickel_plated steel` as alias** | Llama 8B | Eliminates concurrent errors, simplifies 6 of 22 rejects |
| **List valid enum values in system prompt** | All local models | Prevents enum and field-name errors proactively |
| **Add standard form factor hints for cylindrical** | Llama 8B, Llama 3B | "18650: ø18×65mm, 21700: ø21×70mm, 4680: ø46×80mm" |
| **Expand `cathode_height_mm` max to 200 mm** | Schema change | If 175 mm is a valid real-world dimension, fixes Mistral entirely |
| **Add electrode-specific capacity range hints** | Llama 3B | "cathode: 140–220 mAh/g, anode (graphite): 300–500 mAh/g" |
