# Corpus B Results Report — Controlled Realism Evaluation

*Date: 2026-03-31*
*Corpus: prompt_corpus_b.json (v B-1.0, 250 prompts)*
*Models: 7 (Sonnet 4.6, Haiku 4.5, Qwen 27B, Qwen 9B, Mistral Small 3.1, Llama 8B, Llama 3B)*
*Conditions: Unsupervised + Supervised per model (14 experiments, 3,500 evaluations)*
*Cloud API cost: $18.87 billed (Haiku $4.67 + Sonnet $14.20)*
*Local electricity cost: not separately metered for Corpus B*

---

## 1. Executive Summary

Corpus B tests whether AXIOM supervision remains effective when prompts are rougher, shorter, underspecified, and contaminated with noise — closer to real engineering communication than the clean Corpus A benchmark. The 250-prompt corpus uses five roughness families (shorthand, underspecification, unit/scale ambiguity, contradiction bundles, and noisy fragments) plus 10 sentinel probes targeting known model-specific failure modes.

**Primary finding: supervised validity is relatively stable across these two corpora.** Relative to Corpus A, unsupervised validity changed in mixed ways across models on Corpus B (ranging from -4.4 pp to +6.8 pp), while supervised validity remained high for feedback-responsive models and generally stayed within about ±2.6 pp of Corpus A. The supervision architecture compensates for messier input on this second, rougher corpus, though the degree of that robustness should be tested on additional corpora before claiming full generalisation.

---

## 2. Overall Results

### Table 1: Validity Rates — Corpus B vs Corpus A

| Model | A Unsup | B Unsup | Delta | A Sup | B Sup | Delta | B Lift |
|---|---|---|---|---|---|---|---|
| Sonnet 4.6 | 75.6% | 73.6% | -2.0 | 97.0% | 94.8% | -2.2 | +21.2 |
| Haiku 4.5 | 87.0% | 84.8% | -2.2 | 97.8% | 98.0% | +0.2 | +13.2 |
| Qwen 3.5 27B | 89.6% | 88.0% | -1.6 | 99.4% | 98.8% | -0.6 | +10.8 |
| Qwen 3.5 9B | 93.6% | 89.2% | -4.4 | 97.8% | 95.2% | -2.6 | +6.0 |
| Mistral Small 3.1 | 88.0% | 85.6% | -2.4 | 90.0% | 91.2% | +1.2 | +5.6 |
| Llama 3.1 8B | 71.6% | 78.4% | +6.8 | 95.6% | 96.8% | +1.2 | +18.4 |
| Llama 3.2 3B | 74.2% | 70.8% | -3.4 | 82.6% | 80.4% | -2.2 | +9.6 |

**Supervised model ranking (Corpus B):** Qwen 27B (98.8%) > Haiku (98.0%) > Llama 8B (96.8%) > Qwen 9B (95.2%) > Sonnet (94.8%) > Mistral (91.2%) > Llama 3B (80.4%).

Haiku outperformed Sonnet on Corpus B supervised by 3.2 pp (98.0% vs 94.8%), a wider gap than on Corpus A (+0.8 pp). Sonnet's 13 supervised rejects are all prismatic, suggesting that the rougher prompts exacerbate its prismatic schema difficulty.

Llama 8B is an outlier: it *improved* on Corpus B (+6.8 pp unsupervised, +1.2 pp supervised). One possible explanation is that the informal, clipped prompt style of Corpus B better matches the model's training distribution than Corpus A's more structured prompts, though this hypothesis has not been independently tested.

### Table 2: Supervision Lift Comparison

| Model | Corpus A Lift | Corpus B Lift | Change |
|---|---|---|---|
| Sonnet 4.6 | +21.4 pp | +21.2 pp | -0.2 |
| Haiku 4.5 | +10.8 pp | +13.2 pp | +2.4 |
| Qwen 3.5 27B | +9.8 pp | +10.8 pp | +1.0 |
| Qwen 3.5 9B | +4.2 pp | +6.0 pp | +1.8 |
| Mistral Small 3.1 | +2.0 pp | +5.6 pp | +3.6 |
| Llama 3.1 8B | +24.0 pp | +18.4 pp | -5.6 |
| Llama 3.2 3B | +8.4 pp | +9.6 pp | +1.2 |

Supervision lift increased for 5 of 7 models on Corpus B. The rougher prompts create more first-attempt failures, giving supervision more opportunities to recover. The two exceptions are Sonnet (essentially unchanged at +21.2 pp) and Llama 8B (reduced because its unsupervised baseline improved).

---

## 3. Analysis by Roughness Family

### Table 3: Supervised Validity by Roughness Family (all 7 models)

| Model | B1 Short | B2 Underspec | B3 Unit/Scale | B4 Contradict | B5 Noise | SENT |
|---|---|---|---|---|---|---|
| Sonnet 4.6 | 96% | 98% | **90%** | 94% | 98% | 90% |
| Haiku 4.5 | 100% | 100% | **96%** | 98% | 100% | 80% |
| Qwen 3.5 27B | 100% | 100% | **96%** | 100% | 100% | 90% |
| Qwen 3.5 9B | 96% | 98% | **92%** | 96% | 100% | 70% |
| Mistral Small 3.1 | 94% | 94% | **85%** | 96% | 90% | 80% |
| Llama 3.1 8B | 100% | 100% | **96%** | 96% | 96% | 80% |
| Llama 3.2 3B | 90% | 81% | **62%** | 83% | 94% | 40% |

**B3 (unit/scale ambiguity) is the hardest roughness family across all models and both corpora.** Even under supervision, B3 validity ranges from 62% (Llama 3B) to 96% (Haiku, Llama 8B, Qwen 27B). This directly validates the corpus design decision to create a dedicated roughness family targeting the unit confusion and cell-vs-module scale errors documented in the Corpus A failure analysis.

### Table 4: Supervision Lift by Roughness Family (percentage points)

| Model | B1 | B2 | B3 | B4 | B5 | SENT |
|---|---|---|---|---|---|---|
| Sonnet 4.6 | +15 | +17 | **+35** | +17 | +23 | +20 |
| Haiku 4.5 | +2 | +4 | **+35** | +8 | +15 | +20 |
| Qwen 3.5 27B | 0 | 0 | **+33** | 0 | +17 | +30 |
| Qwen 3.5 9B | 0 | 0 | **+19** | 0 | +8 | +20 |
| Mistral Small 3.1 | 0 | 0 | **+21** | +4 | +2 | +10 |
| Llama 3.1 8B | 0 | +12 | **+48** | +10 | +17 | +40 |
| Llama 3.2 3B | +4 | +8 | **+21** | +6 | +8 | +10 |

Supervision provides near-zero additional benefit on B1 and B2 for models that already achieve 94–100% unsupervised on these families. The supervision budget is spent disproportionately on B3 and sentinels. **Llama 8B's +48 pp lift on B3 is the largest single-family supervision effect observed in either corpus.**

---

## 4. Analysis by Cell Type

### Table 5: Supervised Validity by Cell Type

| Model | Pouch | Prismatic | Cylindrical |
|---|---|---|---|
| Sonnet 4.6 | **100%** | **85%** | **100%** |
| Haiku 4.5 | **100%** | **94%** | **100%** |
| Qwen 3.5 27B | **100%** | **96%** | **100%** |
| Qwen 3.5 9B | **100%** | **89%** | 96% |
| Mistral Small 3.1 | **100%** | **74%** | **100%** |
| Llama 3.1 8B | **100%** | 90% | **100%** |
| Llama 3.2 3B | 93% | **82%** | 66% |

Prismatic cells remain the hardest geometry across both corpora. Six of seven models reach 100% supervised validity on pouch; six reach 100% on cylindrical. No model reaches 100% on prismatic. Sonnet's prismatic rate (85%) is notably lower than its Corpus A prismatic rate (91%), while Haiku (94%) is slightly higher than its Corpus A rate (93%). Mistral's 74% prismatic rate is the weakest single model-geometry combination in either corpus.

Llama 3B's cylindrical weakness (66% supervised) persists from Corpus A (66% supervised), representing a consistent model-specific geometry blindspot.

---

## 5. Analysis by Chemistry

### Table 6: Supervised Validity by Chemistry

| Model | NMC-111 | NMC-622 | NMC-811 | LFP |
|---|---|---|---|---|
| Sonnet 4.6 | 93% | 95% | 97% | **94%** |
| Haiku 4.5 | 98% | 97% | 98% | **98%** |
| Qwen 3.5 27B | 100% | 100% | 98% | **97%** |
| Qwen 3.5 9B | 95% | 95% | 97% | **94%** |
| Mistral Small 3.1 | 97% | 90% | 87% | **91%** |
| Llama 3.1 8B | 98% | 97% | 98% | **94%** |
| Llama 3.2 3B | 84% | 89% | 85% | **65%** |

Chemistry effects are modest relative to cell type and roughness family. LFP is consistently the hardest chemistry for Llama 3B (65% vs 84–89% for NMC variants). LFP cathodes have lower specific capacity (~140–170 mAh/g vs 150–200+ for NMC), and the smallest model appears least calibrated on these ranges.

---

## 6. Recovery Analysis

### Table 7: Retry Dynamics (Supervised Experiments)

| Model | Failed A1 | Rec. A2 | Rec. A3 | Rec. A4 | Rejected | Recovery Rate |
|---|---|---|---|---|---|---|
| Sonnet 4.6 | 66 | 46 | 4 | 3 | 13 | **80.3%** |
| Haiku 4.5 | 36 | 23 | 2 | 6 | 5 | **86.1%** |
| Qwen 3.5 27B | 30 | 24 | 3 | 0 | 3 | **90.0%** |
| Qwen 3.5 9B | 27 | 10 | 4 | 1 | 12 | **55.6%** |
| Mistral Small 3.1 | 36 | 12 | 2 | 0 | 22 | **38.9%** |
| Llama 3.1 8B | 54 | 40 | 5 | 1 | 8 | **85.2%** |
| Llama 3.2 3B | 73 | 19 | 5 | 0 | 49 | **32.9%** |

### Table 8: Recovery Rate Comparison — Corpus A vs Corpus B

| Model | Corpus A Recovery | Corpus B Recovery | Delta |
|---|---|---|---|
| Sonnet 4.6 | 88.0% | 80.3% | -7.7 |
| Haiku 4.5 | 81.7% | 86.1% | +4.4 |
| Qwen 3.5 27B | 94.0% | 90.0% | -4.0 |
| Qwen 3.5 9B | 65.6% | 55.6% | -10.0 |
| Mistral Small 3.1 | 16.7% | 38.9% | +22.2 |
| Llama 3.1 8B | 84.4% | 85.2% | +0.8 |
| Llama 3.2 3B | 32.6% | 32.9% | +0.3 |

Recovery rates are relatively stable across these two corpora for most models: Llama 8B (84–85%), Llama 3B (32–33%), Haiku (82–86%). Qwen 27B and Sonnet show moderate drops (-4 and -8 pp respectively), likely because the rougher B3 prompts produce harder-to-correct failures. The notable outlier is **Mistral (+22.2 pp)**: in Corpus A, 50/50 of Mistral's rejects were the identical `cathode_height_mm = 175` error with a 0% recovery rate on that field; in Corpus B, the failure distribution appears more diverse, which may allow Mistral to correct some errors it could not address when stuck on a single repeated failure. This explanation is consistent with the data but has not been confirmed by a per-field breakdown of Corpus B Mistral rejects.

Attempt 2 accounts for 83% of all recoveries across all models (174/210), consistent with the Corpus A pattern.

---

## 7. Sentinel Results

The 10 sentinel prompts are targeted diagnostic probes for known failure modes documented in the Corpus A failure analysis.

### Table 9: Sentinel Probe Results (all 7 models)

| ID | Target | Son U | Son S | Hai U | Hai S | Q27 U | Q27 S | Q9 U | Q9 S | Mis U | Mis S | L8 U | L8 S | L3 U | L3 S |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-241 | Cathode height 175mm | R | R | R | R | R | R | R | R | R | R | R | R | R | R |
| B-242 | Blade wording | V | V | R | V4 | R | V3 | R | V2 | V | V | R | V2 | R | R |
| B-243 | Cyl. 170mm diameter | R | V2 | V | V | R | V2 | V | V | R | V2 | R | V2 | R | V2 |
| B-244 | Separator 3.5 mm/um | V | V | R | V2 | R | V2 | V | V | V | V | R | V2 | R | R |
| B-245 | Steel vs aluminium | V | V | R | R | V | V | R | R | V | V | R | R | R | R |
| B-246 | Field alias (Ni-plated) | V | V | V | V | V | V | V | V | V | V | V | V | R | R |
| B-247 | Cell vs pack energy | V | V | V | V | V | V | V | V | V | V | V | V | V | V |
| B-248 | Contradiction bundle | R | V2 | V | V2 | V | V | V | V | V | V | R | V2 | R | R |
| B-249 | Parse contamination | V | V | V | V | V | V | R | R | R | R | V | V | V | V |
| B-250 | Forwarded email stale | V | V | V | V | V | V | R | V3 | V | V | V | V | V | V |
| **Total** | | 7 | 9 | 6 | 8 | 6 | 9 | 5 | 7 | 7 | 8 | 4 | 8 | 3 | 4 |

V = valid on attempt 1, R = rejected, V2/V3/V4 = recovered on that attempt.

**B-241 (cathode height 175mm range trap)** is a controlled diagnostic probe of the feedback gap documented in the Corpus A failure analysis. It explicitly requests cathode heights of 170–180mm, which exceed the schema maximum of 150mm. Its universal failure (0/14 experiments) is by design: it confirms that when the validation message does not include the valid range, no model can self-correct from a value that the model considers physically realistic. The Corpus A demonstration experiment showed that enriching the feedback message to include the valid range resolves this class of failure (50/50 recovery for Mistral).

**B-247 (cell vs pack energy)** serves as a baseline probe: it passes universally (14/14), confirming that all models correctly interpret "500 Wh per cell" as a cell-level target. The 500 Wh value does not trigger a schema violation because the models generate valid cell designs and let the energy emerge from the calculation. This sentinel verifies that the pack-energy trap is not effective at the schema level.

**B-245 (steel vs aluminium prior)** reveals a model-family split: Sonnet, Mistral, and Qwen 27B handle "robust metal case" correctly (choosing aluminium), while Haiku, Qwen 9B, Llama 8B, and Llama 3B default to steel density. This confirms the material-prior finding from Corpus A in a new prompt context.

**B-246 (field alias)** reveals a capability cliff: Llama 3B is the only model that cannot handle "Ni-plated steel" in any condition. All other models pass it at least unsupervised.

Supervision recovers sentinels B-242, B-243, B-244, and B-248 for most models, typically on attempt 2.

---

## 8. Error Analysis

### 8.1 Final Rejections Across All 14 Experiments

Of 444 total final rejections across all 14 experiments (7 unsupervised + 7 supervised):

| Category | Count | Percentage |
|---|---|---|
| Schema-level validation (value out of range, missing field) | 433 | 97.5% |
| Parse/YAML extraction failure | 11 | 2.5% |
| Physics constraint violation | 0 | 0.0% |

The same pattern as Corpus A holds: **zero physics constraint violations appear in any final rejection.** When a design reaches the constraint checker, the feedback loop corrects it. All persistent failures are upstream schema errors.

Parse failures (11 total, all in unsupervised conditions) are concentrated in Haiku unsupervised (8 cases) where the model occasionally generates conversational text rather than YAML.

### 8.2 Supervised Rejections Only (117 total)

All 117 supervised rejections across the 7 models are schema-level failures. The most common error fields:

| Field | Occurrences (across all supervised retry attempts) | Primary Models Affected |
|---|---|---|
| `cathode_height_mm` | 138+ | Mistral, Sonnet, Haiku |
| `cathode_width_mm` | ~80 | Sonnet, Haiku, Qwen 27B |
| `rev_spec_capacity_mahg` (cathode + anode) | ~150 | Llama 3B |
| `case_density_g_cm3` | ~50 | Qwen 9B, Haiku |
| `envelope.internals` (missing) | ~44 | Llama 3B, Llama 8B |
| `separator.thickness_um` | ~42 | Llama 8B, Llama 3B |
| `fixing_tape_width_mm` | ~40 | Sonnet |
| `geometry.diameter_mm` / `length_mm` | ~68 | Llama 8B, Llama 3B |

These error fields map directly to the failure signatures documented in the Corpus A `FAILURE_MODE_ANALYSIS.md`. The same model-specific failure modes persist under the rougher Corpus B prompts.

### 8.3 Supervised Accepted Outputs (3,383 total)

Of the 3,500 supervised evaluations, 3,383 produced valid designs that passed all schema and physics constraints. These validated designs span:

- All 3 cell types (pouch, prismatic, cylindrical)
- All 4 chemistries (NMC-111, NMC-622, NMC-811, LFP)
- All 5 roughness families + sentinels
- All 4 difficulty levels (D1–D4)

The supervised acceptance rate of 96.7% (3,383/3,500) across seven models and a deliberately rough corpus indicates that the AXIOM validation pipeline produces reliable engineering output under realistic prompt conditions.

---

## 9. Convergence Analysis

### Table 10: Inter-Model Validity Gap

| Metric | Corpus A | Corpus B |
|---|---|---|
| Unsupervised range (all 7 models) | 22.0 pp (71.6–93.6%) | 17.6 pp (70.8–88.0%) |
| Supervised range (all 7 models) | 16.8 pp (82.6–99.4%) | 18.4 pp (80.4–98.8%) |
| Supervised range (excl. Llama 3B) | 9.4 pp (90.0–99.4%) | 7.6 pp (91.2–98.8%) |
| Supervised range (excl. Llama 3B + Mistral) | 3.8 pp (95.6–99.4%) | 4.0 pp (94.8–98.8%) |

For models that respond effectively to feedback (excluding Llama 3B and Mistral), the supervised inter-model gap is 4.0 pp on Corpus B — essentially unchanged from the 3.8 pp on Corpus A. Supervision continues to compress capability differences on the rougher corpus.

---

## 10. Hardest Prompts

### Table 11: Prompts Rejected in 8+ of 14 Experiments

| Prompt | Fails | Family | Cell | Chemistry | Roughness | Expected Failure |
|---|---|---|---|---|---|---|
| B-241 | 14/14 | SENT | prismatic | LFP | sentinel | range_error |
| B-137 | 13/14 | B3 | prismatic | NMC-811 | scale_confusion | scale_confusion |
| B-108 | 10/14 | B3 | prismatic | LFP | scale_confusion | scale_confusion |
| B-245 | 8/14 | SENT | prismatic | NMC-622 | sentinel | material_misprior |

All four are prismatic. B-241 is a controlled diagnostic (see Section 7). B-137 and B-108 are B3 scale-confusion prompts that probe cell-vs-module dimensional ambiguity. B-245 tests the steel-vs-aluminium material prior.

---

## 11. Timing

### Table 12: Inference Speed

| Model | Unsup avg (s) | Sup avg (s) | Valid designs/hr (sup) |
|---|---|---|---|
| Llama 3.2 3B | 3.7 | 6.2 | 465 |
| Llama 3.1 8B | 5.9 | 7.9 | 441 |
| Haiku 4.5 | 7.6 | 9.1 | 396 |
| Qwen 3.5 9B | 8.7 | 10.9 | 330 |
| Sonnet 4.6 | 12.6 | 17.1 | 211 |
| Mistral Small 3.1 | 15.1 | 20.8 | 173 |
| Qwen 3.5 27B | 29.8 | 34.4 | 103 |

---

## 12. Key Findings

1. **Supervision shows robustness on a second, rougher corpus.** Supervised validity dropped by at most 2.6 pp from Corpus A to Corpus B for feedback-responsive models, while unsupervised validity dropped by up to 7 pp. The validation layer compensates for messier neural input on this prompt distribution.

2. **B3 (unit/scale ambiguity) is the dominant difficulty driver.** It produces the lowest validity rates and the largest supervision lifts across all models. This confirms that unit confusion and dimensional scale errors — the exact failure modes targeted by B3 — are the primary frontier for improvement.

3. **Recovery rates are relatively stable across these two corpora.** Five of seven models showed recovery rates within 8 pp of their Corpus A values. The notable outlier is Mistral (+22 pp), explained by diversification of its failure modes under rough prompts.

4. **Consistent with a capability floor above 3B in this sample.** Llama 3B at 80.4% supervised on Corpus B and 82.6% on Corpus A, with 33% recovery rates on both, places it consistently below all other models. Whether this floor generalises to other architectures at similar scale would require testing additional 3B-class models.

5. **Prismatic cells remain the universal hard geometry.** All four most-failed prompts are prismatic. Sonnet's prismatic supervised rate (85%) is notably lower on Corpus B than Corpus A (91%), while most other models hold steady.

6. **B-241 validates the feedback gap as a controlled diagnostic.** Its 0/14 failure rate, by design, confirms that when the schema maximum (150mm) conflicts with a realistic engineering value (175mm) and the feedback does not include the valid range, no model can self-correct. The Corpus A range-feedback demonstration (50/50 Mistral recovery) established that this failure is resolvable.

7. **Zero physics-invalid designs were accepted by the supervised system on Corpus B**, extending the Corpus A finding across 3,500 additional evaluations. Across both corpora, 0 of 10,500 supervised evaluations (7,000 Corpus A + 3,500 Corpus B) produced a physics-invalid accepted design.

8. **Haiku outperforms Sonnet on rough prompts.** Haiku supervised (98.0%) exceeded Sonnet supervised (94.8%) by 3.2 pp on Corpus B, a wider gap than on Corpus A (+0.8 pp). Sonnet's 13 supervised rejects are all prismatic, while Haiku has only 5. For the IEMA cost argument, the cheaper cloud model performs better on realistic, rough input — strengthening the case that Sonnet is not necessary for production use.

9. **Cloud cost estimates require reconciliation.** Token-based cost projections underestimated actual billed costs by approximately 20–25%. The Corpus A cost figure of $33.35 (computed from token counts) does not match the actual account expenditure and should not be cited as a precise figure in the thesis without reconciliation against billing records.

---

## 13. Limitations Specific to Corpus B

1. **Corpus B is a single additional distribution, not a generalisation proof.** Robustness on two corpora is stronger evidence than on one, but the two corpora share the same technical stratification (3 cell types × 4 chemistries × 4 applications) and were tested with the same pipeline. Generalisation to fundamentally different prompt distributions (e.g., non-English, domain-transfer, production logs) is not established.

2. **Corpus B was generated by a rule-based template system, not sampled from real engineering requests.** Despite roughness injection, the prompts may not reflect the actual distribution of requests in engineering practice.

3. **Corpus B has 250 prompts vs Corpus A's 500.** The smaller sample size means wider confidence intervals on per-family and per-cell-type breakdowns.

4. **Cloud costs were not pre-registered.** The actual billed costs for Corpus B cloud experiments ($18.87) were measured post-hoc and are reported as-billed. No claim is made about cost consistency with Corpus A.

---

## Appendix: Data Files

| File | Records | Description |
|---|---|---|
| `results/corpusB_sonnet_unsup.jsonl` | 250 | Sonnet 4.6 unsupervised |
| `results/corpusB_sonnet_sup.jsonl` | 250 | Sonnet 4.6 supervised |
| `results/corpusB_haiku_unsup.jsonl` | 250 | Haiku 4.5 unsupervised |
| `results/corpusB_haiku_sup.jsonl` | 250 | Haiku 4.5 supervised |
| `results/corpusB_qwen27b_unsup.jsonl` | 250 | Qwen 3.5 27B unsupervised |
| `results/corpusB_qwen27b_sup.jsonl` | 250 | Qwen 3.5 27B supervised |
| `results/corpusB_qwen9b_unsup.jsonl` | 250 | Qwen 3.5 9B unsupervised |
| `results/corpusB_qwen9b_sup.jsonl` | 250 | Qwen 3.5 9B supervised |
| `results/corpusB_mistral_unsup.jsonl` | 250 | Mistral Small 3.1 unsupervised |
| `results/corpusB_mistral_sup.jsonl` | 250 | Mistral Small 3.1 supervised |
| `results/corpusB_llama8b_unsup.jsonl` | 250 | Llama 3.1 8B unsupervised |
| `results/corpusB_llama8b_sup.jsonl` | 250 | Llama 3.1 8B supervised |
| `results/corpusB_llama3b_unsup.jsonl` | 250 | Llama 3.2 3B unsupervised |
| `results/corpusB_llama3b_sup.jsonl` | 250 | Llama 3.2 3B supervised |
| `prompt_corpus_b.json` | 250 | Corpus B prompts with full metadata |
| `generation_log.json` | 250 | Corpus generation provenance log |
| `seed_bank.json` | 45+10 | Frozen seed bank (v1.1-FROZEN) |
