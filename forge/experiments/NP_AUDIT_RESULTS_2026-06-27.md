# N/P Consistency Audit — Accepted Supervised Designs

**Date:** 2026-06-27  
**Mode:** Offline, read-only. No result files modified, nothing regenerated, no LLM calls.  
**Method:** Reuses the real `check_np_ratio` + `_get_nested` from `forge/engine/validation/constraint_validator.py`. PASS/FAIL gating comes from the validator itself; the computed value is cross-checked against `ValidationError.value` on every failure (asserted equal to 1e-6 — audit cannot drift from the validator).  
**Formula (identical to validator):** `N/P = (anode_loading_mg_cm2 × anode_rev_spec_capacity_mahg) / (cathode_loading_mg_cm2 × cathode_rev_spec_capacity_mahg)` — no active-material fraction, no porosity correction.  
**Valid band:** [1.05, 1.25].

---

## 1. Coverage

- Accepted supervised designs found (`final_valid == True`): **8252**
- Successfully parsed + N/P computed: **8252**
- Parse failures (raw_llm_output unparseable / not a dict): **0**
- Can't-compute (parsed but ≥1 of the four fields missing): **0**

## 2. Distribution of computed N/P

- min = **0.605**
- median = **1.135**
- max = **2.925**

| bucket | count | % of audited |
|---|---:|---:|
| <0.95 | 972 | 11.8% |
| 0.95-1.00 | 695 | 8.4% |
| 1.00-1.05 | 904 | 11.0% |
| 1.05-1.25 [VALID] | 3811 | 46.2% |
| 1.25-1.40 | 1279 | 15.5% |
| >1.40 | 591 | 7.2% |

## 3. Headline counts

| category | count | % |
|---|---:|---:|
| IN [1.05, 1.25] — consistent (would pass corrected validator) | 3811 | 46.2% |
| OUTSIDE [1.05, 1.25] — inconsistent (would now be rejected) | 4441 | 53.8% |

### ⚠ PHYSICALLY UNSAFE — computed N/P < 1.00 (lithium-plating risk): **1667**  (20.2%)

## 4. By cell type

| cell type | audited | in-valid | outside | % outside | unsafe (<1.00) |
|---|---:|---:|---:|---:|---:|
| pouch | 2934 | 1429 | 1505 | 51.3% | 487 |
| cylindrical | 2776 | 1254 | 1522 | 54.8% | 416 |
| prismatic | 2542 | 1128 | 1414 | 55.6% | 764 |

## 5. By corpus

| corpus | audited | in-valid | outside | % outside | unsafe (<1.00) |
|---|---:|---:|---:|---:|---:|
| A | 6614 | 3119 | 3495 | 52.8% | 1288 |
| B | 1638 | 692 | 946 | 57.8% | 379 |

## 6. Extremes (spot-check)

Lowest computed N/P:

| prompt_id | corpus | file | cell_type | computed N/P |
|---|---|---|---|---:|
| P-010 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| P-212 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| P-247 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| P-349 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| P-380 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| P-419 | A | ft_base_sup.jsonl | prismatic | 0.605 |
| B-145 | B | corpusB_llama3b_sup.jsonl | cylindrical | 0.606 |
| P-045 | A | ft_base_sup.jsonl | prismatic | 0.625 |

Highest computed N/P:

| prompt_id | corpus | file | cell_type | computed N/P |
|---|---|---|---|---:|
| B-140 | B | corpusB_qwen27b_sup.jsonl | pouch | 2.925 |
| P-475 | A | ft_base_sup.jsonl | pouch | 2.914 |
| P-047 | A | ft_base_sup.jsonl | pouch | 2.107 |
| P-490 | A | ft_base_sup.jsonl | pouch | 2.074 |
| B-204 | B | corpusB_llama8b_sup.jsonl | cylindrical | 2.036 |
| B-190 | B | corpusB_llama8b_sup.jsonl | cylindrical | 2.036 |
| P-085 | A | ft_base_sup.jsonl | cylindrical | 2.010 |
| P-189 | A | exp_llama8b_sup_supervised_local.jsonl | cylindrical | 2.000 |

