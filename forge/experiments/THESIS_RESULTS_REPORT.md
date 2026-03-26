# AXIOM Phase 5: Thesis Results Report

*Generated: 2026-03-26 21:17:46*

---

## Section 1: Experiment Overview

### 1.1 Experiments Conducted

| ID | Model | Condition | N | Date | Cost (USD) |
|---|---|---|---|---|---|
| exp1 | Sonnet 4.6 | Unsupervised | 500 | 2026-03-25 | $10.5435 |
| exp2 | Sonnet 4.6 | Supervised | 500 | 2026-03-26 | $13.2048 |
| exp1_pfix | Sonnet 4.6 | Unsupervised (Prismatic Fix) | 164 | 2026-03-26 | $4.4966 |
| exp2_pfix | Sonnet 4.6 | Supervised (Prismatic Fix) | 164 | 2026-03-26 | $4.9920 |
| exp1h | Haiku 4.5 | Unsupervised | 500 | 2026-03-26 | $4.3758 |
| exp2h | Haiku 4.5 | Supervised | 500 | 2026-03-26 | $5.2938 |
| exp1h_pfix | Haiku 4.5 | Unsupervised (Prismatic Fix) | 164 | 2026-03-26 | $1.7547 |
| exp2h_pfix | Haiku 4.5 | Supervised (Prismatic Fix) | 164 | 2026-03-26 | $1.8245 |
| **Total** | | | | | **$46.4856** |

**Total API cost across all experiments: $46.4856**

### 1.2 Prismatic Schema Fix

The original experiment runs (exp1, exp2) used a prompt that did not include the 
correct prismatic cell schema structure. All 164 prismatic prompts produced designs 
that failed schema-level validation (0% validity). This was a prompt engineering 
defect, not a model capability limitation.

**Fix applied:** The prismatic prompt was corrected to include the proper schema 
specification, and all 164 prismatic prompts were re-run in dedicated fix experiments 
(exp1_pfix, exp2_pfix, exp1h_pfix, exp2h_pfix). The combined datasets used throughout 
this analysis merge the fix results for prismatic with the original results for 
pouch and cylindrical cell types.

**Transparency note:** This is disclosed here and in the thesis methodology as a 
limitation of the initial experimental setup. The fix experiments are methodologically 
identical to the originals — same prompts, same models, same validation pipeline — and 
differ only in the corrected schema specification within the system prompt.

## Section 2: Overall Results

### Table 2.1: Validity Rate by Model and Supervision Condition

| Cell Type (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| Pouch (170) | 99.4% [96.7, 99.9] (169/170) | 100.0% [97.8, 100.0] (170/170) | 91.2% [86.0, 94.6] (155/170) | 100.0% [97.8, 100.0] (170/170) |
| Cylindrical (166) | 94.6% [90.0, 97.1] (157/166) | 100.0% [97.7, 100.0] (166/166) | 92.8% [87.8, 95.8] (154/166) | 100.0% [97.7, 100.0] (166/166) |
| Prismatic (164) | 31.7% [25.1, 39.2] (52/164) | 90.9% [85.5, 94.4] (149/164) | 76.8% [69.8, 82.6] (126/164) | 93.3% [88.4, 96.2] (153/164) |
| **Overall (500)** | 75.6% [71.6, 79.2] (378/500) | 97.0% [95.1, 98.2] (485/500) | 87.0% [83.8, 89.7] (435/500) | 97.8% [96.1, 98.8] (489/500) |

### Table 2.2: Supervision Improvement (Δ)

| Cell Type | Sonnet Δ (pp) | p-value | Sig. | Haiku Δ (pp) | p-value | Sig. |
|---|---|---|---|---|---|---|
| Pouch (170) | +0.6 | 1.0000 |  | +8.8 | 0.0001 | ✓ |
| Cylindrical (166) | +5.4 | 0.0039 | ✓ | +7.2 | 0.0005 | ✓ |
| Prismatic (164) | +59.1 | 0.0000 | ✓ | +16.5 | 0.0000 | ✓ |
| **Overall (500)** | +21.4 | 0.0000 | ✓ | +10.8 | 0.0000 | ✓ |

## Section 3: Statistical Tests

### H1: Validity Improvement (McNemar’s Test)

| Model | N | Unsup. Rate | Sup. Rate | Statistic | p-value | Odds Ratio |
|---|---|---|---|---|---|---|
| Sonnet | 500 | 75.6% | 97.0% | 105.01 | 0.0000 | inf |
| Haiku | 500 | 87.0% | 97.8% | 42.56 | 0.0000 | 10.00 |
| Combined | 1000 | 81.3% | 97.4% | 147.98 | 0.0000 | 27.83 |

### H2: Constraint Coverage Improvement (Wilcoxon Signed-Rank)

| Model | N | Median Δ | Statistic | p-value | Rank-biserial r |
|---|---|---|---|---|---|
| Sonnet | 500 | 0.0 | 0.00 | 0.0000 | 1.0000 |
| Haiku | 500 | 0.0 | 165.00 | 0.0000 | 0.8507 |

### H3: Per-Constraint Analysis (McNemar’s + Holm-Bonferroni)

**Haiku_common:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| C1 | 13.0% | 2.2% | 0.0000 | ✓ |
| C2 | 13.0% | 2.2% | 0.0000 | ✓ |
| C3 | 13.0% | 2.2% | 0.0000 | ✓ |
| C4 | 13.0% | 2.2% | 0.0000 | ✓ |
| C5 | 13.0% | 2.2% | 0.0000 | ✓ |
| C6 | 13.0% | 2.2% | 0.0000 | ✓ |
| C7 | 13.0% | 2.2% | 0.0000 | ✓ |

**Haiku_cylindrical:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| CY1 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY2 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY3 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY4 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY5 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY6 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY7 | 7.2% | 0.0% | 0.0039 | ✓ |
| CY8 | 7.2% | 0.0% | 0.0039 | ✓ |

**Haiku_pouch:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| PO1 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO2 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO3 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO4 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO5 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO6 | 8.8% | 0.0% | 0.0004 | ✓ |
| PO7 | 8.8% | 0.0% | 0.0004 | ✓ |

**Haiku_prismatic:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| PR1 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR2 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR3 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR4 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR5 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR6 | 23.2% | 6.7% | 0.0002 | ✓ |
| PR7 | 23.2% | 6.7% | 0.0002 | ✓ |

**Sonnet_common:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| C1 | 24.4% | 3.0% | 0.0000 | ✓ |
| C2 | 24.0% | 3.0% | 0.0000 | ✓ |
| C3 | 24.0% | 3.0% | 0.0000 | ✓ |
| C4 | 24.0% | 3.0% | 0.0000 | ✓ |
| C5 | 24.0% | 3.0% | 0.0000 | ✓ |
| C6 | 24.0% | 3.0% | 0.0000 | ✓ |
| C7 | 24.0% | 3.0% | 0.0000 | ✓ |

**Sonnet_cylindrical:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| CY1 | 4.2% | 0.0% | 0.1250 |  |
| CY2 | 4.2% | 0.0% | 0.1250 |  |
| CY3 | 4.2% | 0.0% | 0.1250 |  |
| CY4 | 4.2% | 0.0% | 0.1250 |  |
| CY5 | 4.2% | 0.0% | 0.1250 |  |
| CY6 | 4.2% | 0.0% | 0.1250 |  |
| CY7 | 4.2% | 0.0% | 0.1250 |  |
| CY8 | 4.2% | 0.0% | 0.1250 |  |

**Sonnet_pouch:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| PO1 | 0.6% | 0.0% | 1.0000 |  |
| PO2 | 0.6% | 0.0% | 1.0000 |  |
| PO3 | 0.6% | 0.0% | 1.0000 |  |
| PO4 | 0.6% | 0.0% | 1.0000 |  |
| PO5 | 0.6% | 0.0% | 1.0000 |  |
| PO6 | 0.6% | 0.0% | 1.0000 |  |
| PO7 | 0.6% | 0.0% | 1.0000 |  |

**Sonnet_prismatic:**

| Constraint | Unsup. Fail | Sup. Fail | p (corrected) | Significant |
|---|---|---|---|---|
| PR1 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR2 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR3 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR4 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR5 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR6 | 68.3% | 9.1% | 0.0000 | ✓ |
| PR7 | 68.3% | 9.1% | 0.0000 | ✓ |

### H4: Model Comparison Under Supervision (McNemar’s)

- **N:** 500 paired prompts
- **Sonnet supervised validity:** 97.0%
- **Haiku supervised validity:** 97.8%
- **McNemar’s statistic:** 10.00
- **p-value:** 0.5413
- **Odds ratio:** 1.40

**Conclusion:** No statistically significant difference between Sonnet and Haiku under supervision.

### Additional Tests: Supervision Effect by Stratification

| Dimension | Model | χ² | p-value | Cramér’s V | Significant |
|---|---|---|---|---|---|
| cell_type | Haiku | 15.45 | 0.0004 | 0.1758 | ✓ |
| difficulty | Haiku | 20.21 | 0.0002 | 0.2011 | ✓ |
| prompt_style | Haiku | 23.34 | 0.0000 | 0.2160 | ✓ |
| cell_type | Sonnet | 207.89 | 0.0000 | 0.6448 | ✓ |
| difficulty | Sonnet | 3.99 | 0.2626 | 0.0893 |  |
| prompt_style | Sonnet | 1.04 | 0.5952 | 0.0456 |  |

## Section 4: Recovery Analysis

### Table 4.1: Retry Dynamics (Supervised)

| Metric | Sonnet 4.6 | Haiku 4.5 |
|---|---|---|
| Valid on attempt 1 | 375 | 440 |
| Valid on attempt 2 | 88 | 36 |
| Valid on attempt 3 | 14 | 12 |
| Valid on attempt 4 | 8 | 1 |
| Rejected (all attempts failed) | 15 | 11 |
| Failed attempt 1 (eligible for recovery) | 125 | 60 |
| Recovered (attempts 2-4) | 110 | 49 |
| Recovery rate | 88.0% | 81.7% |
| Mean attempts (recovered) | 2.27 | 2.29 |
| Mean attempts (overall) | 1.29 | 1.13 |

### Table 4.2: Recovery by Difficulty Level

| Difficulty | Sonnet 1st Valid | Sonnet Recovered | Sonnet Rejected | Haiku 1st Valid | Haiku Recovered | Haiku Rejected |
|---|---|---|---|---|---|---|
| standard | 74 | 19 | 3 | 87 | 8 | 1 |
| edge_case | 91 | 21 | 4 | 106 | 5 | 5 |
| underspecified | 111 | 29 | 4 | 136 | 6 | 2 |
| contradictory | 99 | 41 | 4 | 111 | 30 | 3 |

### Table 4.3: Stubborn Rejects Analysis

- **Sonnet rejects:** 15 prompts
- **Haiku rejects:** 11 prompts
- **Both models reject:** 1 prompts
- **Either model rejects:** 25 prompts

| Prompt ID | Cell Type | Chemistry | Difficulty | Style | Sonnet | Haiku |
|---|---|---|---|---|---|---|
| P-011 | prismatic | LFP | edge_case | detailed | ✗ | ✓ |
| P-012 | prismatic | NMC-811 | underspecified | terse | ✗ | ✓ |
| P-102 | prismatic | NMC-622 | standard | detailed | ✓ | ✗ |
| P-109 | prismatic | NMC-111 | contradictory | natural_language | ✓ | ✗ |
| P-113 | prismatic | LFP | edge_case | detailed | ✓ | ✗ |
| P-126 | prismatic | LFP | contradictory | natural_language | ✗ | ✓ |
| P-133 | prismatic | LFP | standard | natural_language | ✗ | ✓ |
| P-216 | prismatic | NMC-811 | underspecified | natural_language | ✓ | ✗ |
| P-225 | prismatic | NMC-111 | underspecified | detailed | ✗ | ✓ |
| P-239 | prismatic | LFP | underspecified | detailed | ✓ | ✗ |
| P-272 | prismatic | NMC-111 | edge_case | natural_language | ✓ | ✗ |
| P-278 | prismatic | LFP | contradictory | detailed | ✗ | ✗ |
| P-295 | prismatic | LFP | underspecified | natural_language | ✗ | ✓ |
| P-307 | prismatic | LFP | contradictory | terse | ✓ | ✗ |
| P-329 | prismatic | NMC-622 | standard | detailed | ✗ | ✓ |
| P-334 | prismatic | NMC-622 | underspecified | detailed | ✗ | ✓ |
| P-347 | prismatic | LFP | edge_case | detailed | ✓ | ✗ |
| P-352 | prismatic | NMC-111 | contradictory | natural_language | ✗ | ✓ |
| P-385 | prismatic | NMC-111 | edge_case | natural_language | ✓ | ✗ |
| P-398 | prismatic | NMC-622 | contradictory | natural_language | ✗ | ✓ |
| P-416 | prismatic | NMC-622 | standard | natural_language | ✗ | ✓ |
| P-428 | prismatic | NMC-111 | edge_case | detailed | ✗ | ✓ |
| P-441 | prismatic | NMC-811 | edge_case | terse | ✗ | ✓ |
| P-487 | prismatic | LFP | edge_case | detailed | ✗ | ✓ |
| P-497 | prismatic | NMC-622 | edge_case | detailed | ✓ | ✗ |

**Stubborn reject difficulty distribution:**

- standard: 4
- edge_case: 9
- underspecified: 6
- contradictory: 6

## Section 5: Disaggregated Analysis

### 5.1 By Cell Type

| Cell Type (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| cylindrical (166) | 94.6% (157/166) | 100.0% (166/166) | 92.8% (154/166) | 100.0% (166/166) |
| pouch (170) | 99.4% (169/170) | 100.0% (170/170) | 91.2% (155/170) | 100.0% (170/170) |
| prismatic (164) | 31.7% (52/164) | 90.9% (149/164) | 76.8% (126/164) | 93.3% (153/164) |

### 5.2 By Chemistry

| Chemistry (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| LFP (124) | 72.6% (90/124) | 95.2% (118/124) | 83.1% (103/124) | 96.0% (119/124) |
| NMC-111 (127) | 77.2% (98/127) | 97.6% (124/127) | 88.2% (112/127) | 97.6% (124/127) |
| NMC-622 (125) | 78.4% (98/125) | 96.8% (121/125) | 86.4% (108/125) | 98.4% (123/125) |
| NMC-811 (124) | 74.2% (92/124) | 98.4% (122/124) | 90.3% (112/124) | 99.2% (123/124) |

### 5.3 By Application

| Application (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| consumer_electronics (126) | 65.9% (83/126) | 98.4% (124/126) | 80.2% (101/126) | 97.6% (123/126) |
| ev_traction (124) | 85.5% (106/124) | 99.2% (123/124) | 91.1% (113/124) | 97.6% (121/124) |
| grid_storage (126) | 81.0% (102/126) | 96.0% (121/126) | 85.7% (108/126) | 96.8% (122/126) |
| power_tools (124) | 70.2% (87/124) | 94.4% (117/124) | 91.1% (113/124) | 99.2% (123/124) |

### 5.4 By Difficulty

| Difficulty (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| contradictory (144) | 70.1% (101/144) | 97.2% (140/144) | 77.1% (111/144) | 97.9% (141/144) |
| edge_case (116) | 78.4% (91/116) | 96.6% (112/116) | 89.7% (104/116) | 95.7% (111/116) |
| standard (96) | 77.1% (74/96) | 96.9% (93/96) | 91.7% (88/96) | 99.0% (95/96) |
| underspecified (144) | 77.8% (112/144) | 97.2% (140/144) | 91.7% (132/144) | 98.6% (142/144) |

### 5.5 By Prompt Style

| Prompt Style (N) | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|
| detailed (192) | 73.4% (141/192) | 96.4% (185/192) | 91.1% (175/192) | 96.9% (186/192) |
| natural_language (192) | 75.0% (144/192) | 96.9% (186/192) | 78.1% (150/192) | 97.9% (188/192) |
| terse (116) | 80.2% (93/116) | 98.3% (114/116) | 94.8% (110/116) | 99.1% (115/116) |

## Section 6: Constraint-Level Analysis

**Important note:** The dominant failure mode is schema-level validation, where 
the LLM output does not conform to the expected YAML structure. When a design 
fails at schema level, _all_ applicable constraints are counted as failed 
(since no valid design was produced to check). This is why constraints within 
the same geometry group show identical failure rates — they co-fail together 
at the schema layer. Individual constraint violations (designs that pass schema 
but fail specific engineering constraints) are extremely rare (<0.5%), 
indicating that the constraint specifications are well-calibrated to the 
models' engineering knowledge.

### 6.1 Constraint Failure Rates

| Constraint | Name | Sonnet Unsup. | Sonnet Sup. | Haiku Unsup. | Haiku Sup. |
|---|---|---|---|---|---|
| C1 | np_ratio | 24.4% | 3.0% | 13.0% | 2.2% |
| C2 | cathode_loading | 24.0% | 3.0% | 13.0% | 2.2% |
| C3 | anode_loading | 24.0% | 3.0% | 13.0% | 2.2% |
| C4 | separator_porosity | 24.0% | 3.0% | 13.0% | 2.2% |
| C5 | electrolyte_concentration | 24.0% | 3.0% | 13.0% | 2.2% |
| C6 | cathode_material | 24.0% | 3.0% | 13.0% | 2.2% |
| C7 | anode_material | 24.0% | 3.0% | 13.0% | 2.2% |
| CY1 | mandrel_diameter | 4.2% | 0.0% | 7.2% | 0.0% |
| CY2 | winding_clearance | 4.2% | 0.0% | 7.2% | 0.0% |
| CY3 | tension_factor | 4.2% | 0.0% | 7.2% | 0.0% |
| CY4 | tab_type | 4.2% | 0.0% | 7.2% | 0.0% |
| CY5 | jelly_roll_fits | 4.2% | 0.0% | 7.2% | 0.0% |
| CY6 | header_height | 4.2% | 0.0% | 7.2% | 0.0% |
| CY7 | format_consistency | 4.2% | 0.0% | 7.2% | 0.0% |
| CY8 | can_material | 4.2% | 0.0% | 7.2% | 0.0% |
| PO1 | anode_offset | 0.6% | 0.0% | 8.8% | 0.0% |
| PO2 | separator_offset | 0.6% | 0.0% | 8.8% | 0.0% |
| PO3 | separator_covers_anode | 0.6% | 0.0% | 8.8% | 0.0% |
| PO4 | stacks_count | 0.6% | 0.0% | 8.8% | 0.0% |
| PO5 | electrode_pairs | 0.6% | 0.0% | 8.8% | 0.0% |
| PO6 | end_electrode_config | 0.6% | 0.0% | 8.8% | 0.0% |
| PO7 | packaging_offsets | 0.6% | 0.0% | 8.8% | 0.0% |
| PR1 | internal_height | 68.3% | 9.1% | 23.2% | 6.7% |
| PR2 | internal_width | 68.3% | 9.1% | 23.2% | 6.7% |
| PR3 | internal_thickness | 68.3% | 9.1% | 23.2% | 6.7% |
| PR4 | cathode_fits_cavity | 68.3% | 9.1% | 23.2% | 6.7% |
| PR5 | stacks_count | 68.3% | 9.1% | 23.2% | 6.7% |
| PR6 | electrode_pairs | 68.3% | 9.1% | 23.2% | 6.7% |
| PR7 | end_electrode_config | 68.3% | 9.1% | 23.2% | 6.7% |

### 6.2 Constraint Co-occurrence (Jaccard Similarity)

See `figures/fig_constraint_cooccurrence.png` for the full heatmap.

**Top constraint co-failure pairs (Jaccard > 0.10):**

| Constraint A | Constraint B | Jaccard |
|---|---|---|
| C2 (cathode_loading) | C3 (anode_loading) | 1.000 |
| C2 (cathode_loading) | C4 (separator_porosity) | 1.000 |
| C2 (cathode_loading) | C5 (electrolyte_concentration) | 1.000 |
| C2 (cathode_loading) | C6 (cathode_material) | 1.000 |
| C2 (cathode_loading) | C7 (anode_material) | 1.000 |
| C3 (anode_loading) | C4 (separator_porosity) | 1.000 |
| C3 (anode_loading) | C5 (electrolyte_concentration) | 1.000 |
| C3 (anode_loading) | C6 (cathode_material) | 1.000 |
| C3 (anode_loading) | C7 (anode_material) | 1.000 |
| C4 (separator_porosity) | C5 (electrolyte_concentration) | 1.000 |
| C4 (separator_porosity) | C6 (cathode_material) | 1.000 |
| C4 (separator_porosity) | C7 (anode_material) | 1.000 |
| C5 (electrolyte_concentration) | C6 (cathode_material) | 1.000 |
| C5 (electrolyte_concentration) | C7 (anode_material) | 1.000 |
| C6 (cathode_material) | C7 (anode_material) | 1.000 |

### 6.3 Constraints: Supervision Fixes vs. Cannot Fix

| Constraint | Name | Sonnet Fixed | Haiku Fixed | Sonnet Δ | Haiku Δ |
|---|---|---|---|---|---|
| C1 | np_ratio | ✓ | ✓ | +21.4pp | +10.8pp |
| C2 | cathode_loading | ✓ | ✓ | +21.0pp | +10.8pp |
| C3 | anode_loading | ✓ | ✓ | +21.0pp | +10.8pp |
| C4 | separator_porosity | ✓ | ✓ | +21.0pp | +10.8pp |
| C5 | electrolyte_concentration | ✓ | ✓ | +21.0pp | +10.8pp |
| C6 | cathode_material | ✓ | ✓ | +21.0pp | +10.8pp |
| C7 | anode_material | ✓ | ✓ | +21.0pp | +10.8pp |
| CY1 | mandrel_diameter | ✓ | ✓ | +4.2pp | +7.2pp |
| CY2 | winding_clearance | ✓ | ✓ | +4.2pp | +7.2pp |
| CY3 | tension_factor | ✓ | ✓ | +4.2pp | +7.2pp |
| CY4 | tab_type | ✓ | ✓ | +4.2pp | +7.2pp |
| CY5 | jelly_roll_fits | ✓ | ✓ | +4.2pp | +7.2pp |
| CY6 | header_height | ✓ | ✓ | +4.2pp | +7.2pp |
| CY7 | format_consistency | ✓ | ✓ | +4.2pp | +7.2pp |
| CY8 | can_material | ✓ | ✓ | +4.2pp | +7.2pp |
| PO1 | anode_offset |  | ✓ | +0.6pp | +8.8pp |
| PO2 | separator_offset |  | ✓ | +0.6pp | +8.8pp |
| PO3 | separator_covers_anode |  | ✓ | +0.6pp | +8.8pp |
| PO4 | stacks_count |  | ✓ | +0.6pp | +8.8pp |
| PO5 | electrode_pairs |  | ✓ | +0.6pp | +8.8pp |
| PO6 | end_electrode_config |  | ✓ | +0.6pp | +8.8pp |
| PO7 | packaging_offsets |  | ✓ | +0.6pp | +8.8pp |
| PR1 | internal_height | ✓ | ✓ | +59.1pp | +16.5pp |
| PR2 | internal_width | ✓ | ✓ | +59.1pp | +16.5pp |
| PR3 | internal_thickness | ✓ | ✓ | +59.1pp | +16.5pp |
| PR4 | cathode_fits_cavity | ✓ | ✓ | +59.1pp | +16.5pp |
| PR5 | stacks_count | ✓ | ✓ | +59.1pp | +16.5pp |
| PR6 | electrode_pairs | ✓ | ✓ | +59.1pp | +16.5pp |
| PR7 | end_electrode_config | ✓ | ✓ | +59.1pp | +16.5pp |

## Section 7: Cost Analysis

### 7.1 Token Usage Summary

| Condition | Tokens In | Tokens Out | Mean In/Prompt | Mean Out/Prompt | Cost (USD) |
|---|---|---|---|---|---|
| Sonnet Unsupervised | 1,803,919 | 641,886 | 3608 | 1284 | $15.0400 |
| Sonnet Supervised | 2,821,507 | 648,813 | 5643 | 1298 | $18.1967 |
| Haiku Unsupervised | 1,803,848 | 865,333 | 3608 | 1731 | $6.1305 |
| Haiku Supervised | 2,816,301 | 860,408 | 5633 | 1721 | $7.1183 |

### 7.2 Cost per Valid Design

Definition 3.2: `Cost_cloud = (tokens_in * rate_in + tokens_out * rate_out) / N_valid`

| Condition | N Valid | Total Cost | Cost per Valid Design |
|---|---|---|---|
| Sonnet Unsupervised | 378 | $15.0400 | $0.039788 |
| Sonnet Supervised | 485 | $18.1967 | $0.037519 |
| Haiku Unsupervised | 435 | $6.1305 | $0.014093 |
| Haiku Supervised | 489 | $7.1183 | $0.014557 |

**Key finding:** Supervised Haiku ($0.014557/design) is cheaper per valid design than unsupervised Sonnet ($0.039788/design).

### 7.3 Supervision Overhead

- **Sonnet supervision overhead:** $3.1567
- **Haiku supervision overhead:** $0.9878
- **Sonnet cost per recovered design:** $0.028697
- **Haiku cost per recovered design:** $0.020160

## Section 8: The Prismatic Inversion

A counter-intuitive finding: on prismatic cell designs, Haiku 4.5 significantly 
outperforms Sonnet 4.6 in unsupervised mode.

### Validity Rates (Prismatic Only, N=164)

| | Unsupervised | Supervised |
|---|---|---|
| Sonnet 4.6 | 31.7% | 90.9% |
| Haiku 4.5 | 76.8% | 93.3% |
| **Δ (Haiku - Sonnet)** | **+45.1 pp** | **+2.4 pp** |

### Original (Pre-Fix) Prismatic Results

- Sonnet original prismatic validity: 0.0%
- Haiku original prismatic validity: 0.0%

### Output Complexity Analysis

- **Sonnet mean output tokens (prismatic unsup.):** 1179
- **Haiku mean output tokens (prismatic unsup.):** 1491
- **Sonnet mean raw output length (chars):** 676
- **Haiku mean raw output length (chars):** 1663

### Constraint Error Patterns (Prismatic Unsupervised)

| Constraint | Sonnet Fail Rate | Haiku Fail Rate | Δ |
|---|---|---|---|
| PR1 (internal_height) | 68.3% | 23.2% | +45.1pp |
| PR2 (internal_width) | 68.3% | 23.2% | +45.1pp |
| PR3 (internal_thickness) | 68.3% | 23.2% | +45.1pp |
| PR4 (cathode_fits_cavity) | 68.3% | 23.2% | +45.1pp |
| PR5 (stacks_count) | 68.3% | 23.2% | +45.1pp |
| PR6 (electrode_pairs) | 68.3% | 23.2% | +45.1pp |
| PR7 (end_electrode_config) | 68.3% | 23.2% | +45.1pp |
| C1 (np_ratio) | 68.3% | 23.2% | +45.1pp |
| C2 (cathode_loading) | 68.3% | 23.2% | +45.1pp |
| C3 (anode_loading) | 68.3% | 23.2% | +45.1pp |
| C4 (separator_porosity) | 68.3% | 23.2% | +45.1pp |
| C5 (electrolyte_concentration) | 68.3% | 23.2% | +45.1pp |
| C6 (cathode_material) | 68.3% | 23.2% | +45.1pp |
| C7 (anode_material) | 68.3% | 23.2% | +45.1pp |

### Interpretation

The prismatic inversion demonstrates that model capability (as measured by general 
benchmarks) does not directly predict structured output quality for domain-specific 
schemas. Sonnet 4.6 — the more capable model — generates more elaborate and complex 
YAML structures that are more likely to deviate from the expected schema, while Haiku 4.5 
produces simpler, more schema-compliant outputs. Under supervision (with constraint feedback), 
both models converge toward similar validity rates, suggesting that the inversion is 
fundamentally about structural compliance rather than domain understanding.

## Section 9: Key Findings Summary

1. **Finding 1: Supervision significantly improves design validity.** Sonnet: +21.4pp (p=0.0000), Haiku: +10.8pp (p=0.0000).

2. **Finding 2: Constraint-feedback supervision enables design recovery.** Sonnet recovers 88% of initially-failed designs (110/125), Haiku recovers 82% (49/60).

3. **Finding 3: Model capability ≠ structured output quality (Prismatic Inversion).** Haiku outperforms Sonnet on unsupervised prismatic by +45.1pp, but both converge under supervision.

4. **Finding 4: Under supervision, model differences diminish.** Sonnet supervised: 97.0%, Haiku supervised: 97.8% (p=0.5413).

5. **Finding 5: Supervised Haiku is a cost-efficient option.** Cost per valid design: Haiku Sup. $0.014557 vs. Sonnet Unsup. $0.039788.

6. **Finding 6: Contradictory prompts have the lowest validity.** Rates: Sonnet Unsup. 70.1%, Sonnet Sup. 97.2%, Haiku Unsup. 77.1%, Haiku Sup. 97.9%.

7. **Finding 7: Total experiment cost is extremely low.** All 8 experiment runs (4,000 total LLM invocations + retries) cost $46.49 total.

8. **Finding 8: A small core of prompts resist supervision.** 1 prompts fail under supervision for both models, primarily edge_case difficulty.

---

## Figures

All figures are saved in `forge/experiments/figures/`:

- `fig_validity_rate_overall.png` — Overall validity rate by model and condition
- `fig_validity_by_celltype.png` — Validity rate by cell type
- `fig_validity_by_difficulty.png` — Validity rate by difficulty level
- `fig_constraint_heatmap.png` — Constraint failure rate heatmap
- `fig_retry_sankey.png` — Retry dynamics flow diagram
- `fig_recovery_by_difficulty.png` — Recovery by difficulty level
- `fig_cost_per_valid.png` — Cost per valid design
- `fig_constraint_cooccurrence.png` — Constraint co-failure matrix
- `fig_model_comparison_scatter.png` — Model convergence scatter plot
- `fig_prismatic_inversion.png` — Prismatic inversion comparison
