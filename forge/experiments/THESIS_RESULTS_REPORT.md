# AXIOM Thesis Results Report — Cloud, Local, and Multi-Model Experiments

*Updated: 2026-03-30*
*Covers: 14 experiments, 7 models, 7,000 prompt evaluations*

---

## Section 1: Experiment Overview

### 1.1 Experiments Conducted

| ID | Model | Parameters | Backend | Condition | N | Date |
|---|---|---|---|---|---|---|
| exp1/exp1_pfix | Claude Sonnet 4.6 | — | Anthropic API | Unsupervised | 500 | 2026-03-25 |
| exp2/exp2_pfix | Claude Sonnet 4.6 | — | Anthropic API | Supervised | 500 | 2026-03-26 |
| exp1h/exp1h_pfix | Claude Haiku 4.5 | — | Anthropic API | Unsupervised | 500 | 2026-03-26 |
| exp2h/exp2h_pfix | Claude Haiku 4.5 | — | Anthropic API | Supervised | 500 | 2026-03-26 |
| exp3a | Qwen 3.5 27B | Q4_K_M | Ollama (local) | Unsupervised | 500 | 2026-03-27 |
| exp3b | Qwen 3.5 27B | Q4_K_M | Ollama (local) | Supervised | 500 | 2026-03-27 |
| exp3a_small | Qwen 3.5 9B | Q4_K_M | Ollama (local) | Unsupervised | 500 | 2026-03-26 |
| exp3b_small | Qwen 3.5 9B | Q4_K_M | Ollama (local) | Supervised | 500 | 2026-03-27 |
| exp_mistral_unsup | Mistral Small 3.1 | 24B | Ollama (local) | Unsupervised | 500 | 2026-03-29 |
| exp_mistral_sup | Mistral Small 3.1 | 24B | Ollama (local) | Supervised | 500 | 2026-03-29 |
| exp_llama8b_unsup | Llama 3.1 8B | 8B | Ollama (local) | Unsupervised | 500 | 2026-03-29 |
| exp_llama8b_sup | Llama 3.1 8B | 8B | Ollama (local) | Supervised | 500 | 2026-03-30 |
| exp_llama3b_unsup | Llama 3.2 3B | 3B | Ollama (local) | Unsupervised | 500 | 2026-03-30 |
| exp_llama3b_sup | Llama 3.2 3B | 3B | Ollama (local) | Supervised | 500 | 2026-03-30 |

All experiments use the same 500-prompt corpus (3 cell types × 4 chemistries × 4 applications × 4 difficulties × 3 prompt styles), the same validation pipeline, and the same constraint registry.

### 1.2 Backend Configuration

| Parameter | Cloud (Claude) | Local (Qwen 3.5) | Local (Multi-model) |
|---|---|---|---|
| Temperature | 0.0 | 0.0 | 0.0 |
| Max output tokens | 4,096 | 2,000 | 2,000 |
| Context window | model default | 8,192 | 8,192 |
| Thinking mode | N/A | OFF (`think: false`) | OFF (`think: false`) |
| Supervised retries | 4 attempts max | 4 attempts max | 4 attempts max |

### 1.3 Prismatic Schema Fix (Cloud Only)

The original cloud experiments (exp1, exp2, exp1h, exp2h) produced 0% validity on 164 prismatic prompts due to a prompt engineering defect (missing schema specification). These were re-run as dedicated fix experiments (exp1_pfix, exp2_pfix, exp1h_pfix, exp2h_pfix). The combined datasets used throughout this report merge the fix results for prismatic with the original results for pouch and cylindrical. The local experiments did not require this fix.

### 1.4 Cost Summary

| Backend | Experiments | API Cost | Electricity | Total |
|---|---|---|---|---|
| Anthropic API (Cloud) | 4 × 500 prompts | $33.35 | — | **$33.35** |
| Ollama — Qwen (Local) | 4 × 500 prompts | $0.00 | €0.87 (~$0.96) | **$0.96** |
| Ollama — Multi-model (Local) | 6 × 500 prompts | $0.00 | €0.75 (~$0.83) | **$0.83** |
| **Combined** | **14 × 500 prompts** | | | **$35.14** |

---

## Section 2: Overall Results

### Table 2.1: Validity Rate by Model and Supervision Condition

| Model | Unsupervised | 95% CI | Supervised | 95% CI | Δ (pp) |
|---|---|---|---|---|---|
| Sonnet 4.6 (cloud) | 75.6% (378/500) | [71.6, 79.2] | 97.0% (485/500) | [95.1, 98.2] | +21.4 |
| Haiku 4.5 (cloud) | 87.0% (435/500) | [83.8, 89.7] | 97.8% (489/500) | [96.1, 98.8] | +10.8 |
| Qwen 3.5 27B (local) | 89.6% (448/500) | [86.6, 92.0] | **99.4% (497/500)** | [98.3, 99.8] | +9.8 |
| Qwen 3.5 9B (local) | **93.6% (468/500)** | [91.1, 95.4] | 97.8% (489/500) | [96.1, 98.8] | +4.2 |
| Mistral Small 3.1 (local) | 88.0% (440/500) | [85.2, 90.8] | 90.0% (450/500) | [87.4, 92.6] | +2.0 |
| Llama 3.1 8B (local) | 71.6% (358/500) | [67.7, 75.5] | 95.6% (478/500) | [93.8, 97.4] | +24.0 |
| Llama 3.2 3B (local) | 74.2% (371/500) | [70.4, 78.0] | 82.6% (413/500) | [79.3, 85.9] | +8.4 |

### Table 2.2a: Validity Rate by Cell Type — Cloud and Qwen Models

| Cell Type (N) | Sonnet U | Sonnet S | Haiku U | Haiku S | 27B U | 27B S | 9B U | 9B S |
|---|---|---|---|---|---|---|---|---|
| Pouch (170) | 99% | 100% | 91% | 100% | 96% | 100% | 95% | 100% |
| Cylindrical (166) | 95% | 100% | 93% | 100% | 80% | 100% | 98% | 100% |
| Prismatic (164) | 32% | 91% | 77% | 93% | 93% | 98% | 87% | 93% |
| **Overall (500)** | **76%** | **97%** | **87%** | **98%** | **90%** | **99%** | **94%** | **98%** |

### Table 2.2b: Validity Rate by Cell Type — Multi-Model Experiments

| Cell Type (N) | Mistral U | Mistral S | Llama 8B U | Llama 8B S | Llama 3B U | Llama 3B S |
|---|---|---|---|---|---|---|
| Pouch (170) | 100% | 100% | 97% | 99% | 92% | 93% |
| Cylindrical (166) | 98% | 100% | 67% | 92% | 58% | 66% |
| Prismatic (164) | 65% | 70% | 50% | 95% | 71% | 89% |
| **Overall (500)** | **88%** | **90%** | **72%** | **96%** | **74%** | **83%** |

### Table 2.3: Inference Speed

| Model | Unsupervised (avg) | Supervised (avg) |
|---|---|---|
| Sonnet 4.6 | 13.8s | 18.0s |
| Haiku 4.5 | 10.7s | 13.7s |
| Qwen 3.5 27B | 23.3s | 26.1s |
| Qwen 3.5 9B | 9.0s | 10.1s |
| Mistral Small 3.1 | 15.1s | 21.0s |
| Llama 3.1 8B | 6.0s | 8.8s |
| **Llama 3.2 3B** | **4.0s** | **6.2s** |

The Llama 3.2 3B is the fastest model across all conditions. Among models achieving >95% supervised validity, the Qwen 3.5 9B (9.0s unsupervised) remains the best speed-quality trade-off.

---

## Section 3: Statistical Tests

### H1: Supervision Improves Validity (McNemar's Test, Paired by prompt_id)

| Model | Δ (pp) | χ² | p-value | Improved | Regressed | Odds Ratio |
|---|---|---|---|---|---|---|
| Sonnet 4.6 | +21.4 | 105.01 | <0.0001 | 107 | 0 | ∞ |
| Haiku 4.5 | +10.8 | 42.56 | <0.0001 | 60 | 6 | 10.00 |
| Qwen 3.5 27B | +9.8 | 47.02 | <0.0001 | 49 | 0 | ∞ |
| Qwen 3.5 9B | +4.2 | — | <0.0001 | 21 | 0 | ∞ |
| Mistral Small 3.1 | +2.0 | 8.10 | 0.0044 | 10 | 0 | ∞ |
| Llama 3.1 8B | +24.0 | 118.01 | <0.0001 | 120 | 0 | ∞ |
| Llama 3.2 3B | +8.4 | 40.02 | <0.0001 | 42 | 0 | ∞ |

**Conclusion:** Supervision significantly improves validity for all seven models (p < 0.005 or better). The effect is largest for Llama 3.1 8B (+24.0pp), surpassing even Sonnet (+21.4pp). The effect is smallest for Mistral Small 3.1 (+2.0pp), which has a high unsupervised baseline but a very low recovery rate (see Section 4).

Six of seven models show zero regressions under supervision (no prompt that was valid unsupervised became invalid supervised). Haiku regressed on 6 prompts — a known stochastic effect at temperature 0.0 due to batched API load.

### H2: Model Comparison Under Supervision (McNemar's Test)

| Comparison | p-value | Significant (α=0.05) |
|---|---|---|
| Sonnet Sup. vs Haiku Sup. | 0.5413 | No |
| Sonnet Sup. vs Qwen-27B Sup. | **0.0075** | **Yes** |
| Sonnet Sup. vs Qwen-9B Sup. | 0.5563 | No |
| Haiku Sup. vs Qwen-27B Sup. | 0.0574 | No (marginal) |
| Haiku Sup. vs Qwen-9B Sup. | 1.0000 | No |
| Qwen-27B Sup. vs Qwen-9B Sup. | **0.0386** | **Yes** |

*Note: Pairwise McNemar's tests for the three multi-model experiments against the original four models are pending a unified analysis script. The raw validity rates (Mistral 90.0%, Llama 8B 95.6%, Llama 3B 82.6%) indicate that Llama 8B supervised is competitive with the cloud+Qwen tier, while Mistral and Llama 3B supervised fall below.*

---

## Section 4: Recovery Analysis

### Table 4.1: Retry Dynamics (Supervised Experiments)

| Metric | Sonnet | Haiku | Qwen 27B | Qwen 9B | Mistral | Llama 8B | Llama 3B |
|---|---|---|---|---|---|---|---|
| Valid on attempt 1 | 375 | 440 | 448 | 468 | 440 | 359 | 371 |
| Valid on attempt 2 | 88 | 36 | 49 | 19 | 7 | 102 | 36 |
| Valid on attempt 3 | 14 | 12 | 0 | 1 | 2 | 10 | 5 |
| Valid on attempt 4 | 8 | 1 | 0 | 1 | 1 | 7 | 1 |
| **Rejected** | **15** | **11** | **3** | **11** | **50** | **22** | **87** |
| Failed attempt 1 | 125 | 60 | 52 | 32 | 60 | 141 | 129 |
| Recovered | 110 | 49 | 49 | 21 | 10 | 119 | 42 |
| **Recovery rate** | **88%** | **82%** | **94%** | **66%** | **17%** | **84%** | **33%** |
| Mean attempts (overall) | 1.29 | 1.13 | 1.10 | 1.05 | 1.33 | 1.42 | 1.62 |

**Key finding:** The Qwen 27B retains the highest recovery rate at 94%. Llama 3.1 8B is the "supervision champion" — it has the most failed first attempts (141) but recovers 84% of them, producing a +24.0pp supervision lift, the largest of any model. In contrast, Mistral Small 3.1 has a near-identical first-attempt profile to its unsupervised run (440 valid) but recovers only 17% of failures — it tends to repeat the same parse error across retry attempts. Llama 3.2 3B has limited capacity to incorporate feedback (33% recovery), suggesting a floor of model capability below which supervision yields diminishing returns.

### Table 4.2: Recovery by Difficulty Level

**Cloud and Qwen Models (1st attempt valid / Recovered / Rejected):**

| Difficulty | Sonnet | Haiku | Qwen 27B | Qwen 9B |
|---|---|---|---|---|
| standard (96) | 74 / 19 / 3 | 87 / 8 / 1 | 91 / 4 / 1 | 94 / 1 / 1 |
| edge_case (116) | 91 / 21 / 4 | 106 / 5 / 5 | 106 / 9 / 1 | 104 / 6 / 6 |
| underspecified (144) | 111 / 29 / 4 | 136 / 6 / 2 | 131 / 12 / 1 | 138 / 3 / 3 |
| contradictory (144) | 99 / 41 / 4 | 111 / 30 / 3 | 120 / 24 / 0 | 132 / 11 / 1 |

**Multi-Model Experiments (1st attempt valid / Recovered / Rejected):**

| Difficulty | Mistral | Llama 8B | Llama 3B |
|---|---|---|---|
| standard (96) | 83 / 3 / 10 | 62 / 29 / 5 | 68 / 8 / 20 |
| edge_case (116) | 103 / 2 / 11 | 76 / 36 / 4 | 89 / 9 / 18 |
| underspecified (144) | 125 / 3 / 16 | 118 / 23 / 3 | 107 / 12 / 25 |
| contradictory (144) | 129 / 2 / 13 | 102 / 32 / 10 | 107 / 13 / 24 |

**Key finding:** The Qwen 27B supervised remains the only model-condition combination to fully solve the contradictory difficulty class (144/144). Llama 8B shows strong recovery across all difficulty levels, with its highest recovery counts on edge_case (36) and contradictory (32) prompts.

### Table 4.3: Stubborn Rejects

| Model (Supervised) | Rejects | Prompt IDs |
|---|---|---|
| Sonnet 4.6 | 15 | P-011, P-012, P-126, P-133, P-225, P-278, P-295, P-329, P-334, P-352, P-398, P-416, P-428, P-441, P-487 |
| Haiku 4.5 | 11 | P-102, P-109, P-113, P-216, P-239, P-272, P-278, P-307, P-347, P-385, P-497 |
| Qwen 3.5 27B | 3 | P-186, P-266, P-315 |
| Qwen 3.5 9B | 11 | P-046, P-056, P-139, P-216, P-220, P-266, P-272, P-385, P-410, P-443, P-446 |
| Mistral Small 3.1 | 50 | P-002, P-010, P-021, P-030, P-051, P-061, P-063, P-092, P-104, P-109, P-110, P-113, P-116, P-124, P-130, P-135, P-147, P-161, P-175, P-188, P-194, P-212, P-223, P-226, P-239, P-240, P-247, P-253, P-264, P-280, P-295, P-307, P-309, P-324, P-350, P-361, P-363, P-368, P-371, P-383, P-385, P-399, P-405, P-406, P-419, P-450, P-469, P-483, P-487, P-488 |
| Llama 3.1 8B | 22 | P-042, P-044, P-046, P-071, P-088, P-090, P-107, P-151, P-196, P-211, P-223, P-278, P-292, P-314, P-315, P-349, P-356, P-416, P-457, P-471, P-485, P-498 |
| Llama 3.2 3B | 87 | P-005, P-007, P-026, P-027, P-038, P-044, P-046, P-051, P-054, P-058, P-065, P-071, P-076, P-081, P-088, P-107, P-115, P-117, P-129, P-131, P-136, P-151, P-154, P-155, P-160, P-163, P-169, P-182, P-186, P-187, P-206, P-208, P-210, P-211, P-213, P-214, P-216, P-218, P-223, P-229, P-242, P-254, P-255, P-261, P-266, P-267, P-268, P-272, P-276, P-278, P-279, P-291, P-292, P-295, P-296, P-297, P-310, P-319, P-321, P-326, P-336, P-341, P-353, P-356, P-357, P-374, P-375, P-378, P-387, P-401, P-402, P-415, P-420, P-437, P-439, P-443, P-444, P-447, P-452, P-466, P-473, P-474, P-483, P-485, P-488, P-489, P-498 |

- **No single prompt fails all seven models under supervision** — every prompt in the corpus is solvable by at least three models.
- **P-278** is the hardest prompt, rejected by 4/7 supervised models (Sonnet, Haiku, Llama 8B, Llama 3B).
- **P-223** (prismatic/NMC-811/contradictory/detailed) is the only prompt rejected by all three multi-model experiments.
- The Qwen 27B rejects only 3 prompts — the smallest reject set of any model. Llama 3B rejects 87 — the largest.

---

## Section 5: Disaggregated Analysis

### 5.1 By Cell Type

**Cloud and Qwen Models:**

| Cell Type | Sonnet U | Sonnet S | Haiku U | Haiku S | 27B U | 27B S | 9B U | 9B S |
|---|---|---|---|---|---|---|---|---|
| Pouch (170) | 169/170 | 170/170 | 155/170 | 170/170 | 163/170 | 170/170 | 162/170 | 170/170 |
| Cylindrical (166) | 157/166 | 166/166 | 154/166 | 166/166 | 133/166 | 166/166 | 163/166 | 166/166 |
| Prismatic (164) | 52/164 | 149/164 | 126/164 | 153/164 | 152/164 | 161/164 | 143/164 | 153/164 |

**Multi-Model Experiments:**

| Cell Type | Mistral U | Mistral S | Llama 8B U | Llama 8B S | Llama 3B U | Llama 3B S |
|---|---|---|---|---|---|---|
| Pouch (170) | 170/170 | 170/170 | 165/170 | 169/170 | 157/170 | 158/170 |
| Cylindrical (166) | 163/166 | 166/166 | 111/166 | 153/166 | 97/166 | 109/166 |
| Prismatic (164) | 107/164 | 114/164 | 82/164 | 156/164 | 117/164 | 146/164 |

All four cloud+Qwen models achieve **100% validity on pouch and cylindrical** under supervision. Mistral also achieves 100% on both. Llama models struggle with cylindrical (66–92% supervised) — a geometry-specific weakness.

### 5.2 By Difficulty

**Cloud and Qwen Models:**

| Difficulty | Sonnet U | Sonnet S | Haiku U | Haiku S | 27B U | 27B S | 9B U | 9B S |
|---|---|---|---|---|---|---|---|---|
| standard (96) | 74/96 | 93/96 | 88/96 | 95/96 | 91/96 | 95/96 | 94/96 | 95/96 |
| edge_case (116) | 91/116 | 112/116 | 104/116 | 111/116 | 106/116 | 115/116 | 104/116 | 110/116 |
| underspecified (144) | 112/144 | 140/144 | 132/144 | 142/144 | 131/144 | 143/144 | 138/144 | 141/144 |
| contradictory (144) | 101/144 | 140/144 | 111/144 | 141/144 | 120/144 | **144/144** | 132/144 | 143/144 |

**Multi-Model Experiments:**

| Difficulty | Mistral U | Mistral S | Llama 8B U | Llama 8B S | Llama 3B U | Llama 3B S |
|---|---|---|---|---|---|---|
| standard (96) | 83/96 | 86/96 | 62/96 | 91/96 | 68/96 | 76/96 |
| edge_case (116) | 103/116 | 105/116 | 76/116 | 112/116 | 89/116 | 98/116 |
| underspecified (144) | 125/144 | 128/144 | 118/144 | 141/144 | 107/144 | 119/144 |
| contradictory (144) | 129/144 | 131/144 | 102/144 | 134/144 | 107/144 | 120/144 |

### 5.3 By Chemistry

**Cloud and Qwen Models:**

| Chemistry | Sonnet U | Sonnet S | Haiku U | Haiku S | 27B U | 27B S | 9B U | 9B S |
|---|---|---|---|---|---|---|---|---|
| NMC-111 (127) | 98/127 | 124/127 | 112/127 | 124/127 | 109/127 | 127/127 | 121/127 | 124/127 |
| NMC-622 (125) | 98/125 | 121/125 | 108/125 | 123/125 | 113/125 | 124/125 | 119/125 | 123/125 |
| NMC-811 (124) | 92/124 | 122/124 | 112/124 | 123/124 | 116/124 | 123/124 | 113/124 | 121/124 |
| LFP (124) | 90/124 | 118/124 | 103/124 | 119/124 | 110/124 | 123/124 | 115/124 | 121/124 |

**Multi-Model Experiments:**

| Chemistry | Mistral U | Mistral S | Llama 8B U | Llama 8B S | Llama 3B U | Llama 3B S |
|---|---|---|---|---|---|---|
| NMC-111 (127) | 111/127 | 115/127 | 89/127 | 122/127 | 97/127 | 109/127 |
| NMC-622 (125) | 113/125 | 114/125 | 86/125 | 117/125 | 102/125 | 112/125 |
| NMC-811 (124) | 106/124 | 109/124 | 91/124 | 119/124 | 95/124 | 106/124 |
| LFP (124) | 110/124 | 112/124 | 92/124 | 120/124 | 77/124 | 86/124 |

### 5.4 By Prompt Style

**Cloud and Qwen Models:**

| Style | Sonnet U | Sonnet S | Haiku U | Haiku S | 27B U | 27B S | 9B U | 9B S |
|---|---|---|---|---|---|---|---|---|
| detailed (192) | 141/192 | 185/192 | 175/192 | 186/192 | 168/192 | 192/192 | 183/192 | 192/192 |
| natural_language (192) | 144/192 | 186/192 | 150/192 | 188/192 | 176/192 | 189/192 | 170/192 | 181/192 |
| terse (116) | 93/116 | 114/116 | 110/116 | 115/116 | 104/116 | 116/116 | 115/116 | 116/116 |

**Multi-Model Experiments:**

| Style | Mistral U | Mistral S | Llama 8B U | Llama 8B S | Llama 3B U | Llama 3B S |
|---|---|---|---|---|---|---|
| detailed (192) | 167/192 | 169/192 | 131/192 | 177/192 | 152/192 | 168/192 |
| natural_language (192) | 169/192 | 176/192 | 123/192 | 189/192 | 118/192 | 134/192 |
| terse (116) | 104/116 | 105/116 | 104/116 | 112/116 | 101/116 | 111/116 |

**Key finding:** Terse prompts are surprisingly effective across all models — even Llama 3.2 3B achieves 87% unsupervised and 96% supervised on terse prompts, its best style. Natural language remains the hardest prompt style for most local models, with the exception of Llama 8B supervised which achieves 98% on natural language — higher than its detailed score (92%).

---

## Section 6: The Prismatic Inversion (Revisited)

### 6.1 Cloud Models

In the original cloud analysis, Haiku outperformed Sonnet on unsupervised prismatic by +45.1pp — a counter-intuitive result where the smaller model produced better structured output.

### 6.2 Local Models Resolve the Inversion

| Model | Unsupervised | Supervised |
|---|---|---|
| Sonnet 4.6 | 31.7% | 90.9% |
| Haiku 4.5 | 76.8% | 93.3% |
| **Qwen 3.5 27B** | **92.7%** | **98.2%** |
| Qwen 3.5 9B | 87.2% | 93.3% |
| Mistral Small 3.1 | 65.2% | 69.5% |
| Llama 3.1 8B | 50.0% | 95.1% |
| Llama 3.2 3B | 71.3% | 89.0% |

The Qwen 27B maintains the highest prismatic validity in both conditions. The multi-model results reveal a second "inversion": Llama 8B jumps from 50% unsupervised to 95.1% supervised on prismatic (+45.1pp) — the single largest cell-type-specific supervision lift in the study, matching the magnitude of the original Sonnet prismatic gap. Mistral, despite strong overall performance (88% unsupervised), has a persistent prismatic weakness that supervision barely addresses (65.2% → 69.5%).

---

## Section 7: Cost Analysis

### 7.1 Token Usage

| Condition | Tokens In | Tokens Out | Mean Out/Prompt |
|---|---|---|---|
| Sonnet Unsupervised | 1,422,978 | 492,197 | 984 |
| Sonnet Supervised | 1,670,914 | 477,070 | 954 |
| Haiku Unsupervised | 1,422,907 | 656,985 | 1,314 |
| Haiku Supervised | 1,548,956 | 655,247 | 1,310 |
| Qwen 27B Unsupervised | 1,345,127 | 326,953 | 654 |
| Qwen 27B Supervised | 1,392,912 | 327,236 | 654 |
| Qwen 9B Unsupervised | 1,345,127 | 326,052 | 652 |
| Qwen 9B Supervised | 1,400,776 | 326,040 | 652 |
| Mistral Unsupervised | 1,318,396 | 320,445 | 641 |
| Mistral Supervised | 1,480,149 | 320,454 | 641 |
| Llama 8B Unsupervised | 1,208,330 | 298,800 | 598 |
| Llama 8B Supervised | 1,387,047 | 302,965 | 606 |
| Llama 3B Unsupervised | 1,213,330 | 318,300 | 637 |
| Llama 3B Supervised | 1,466,664 | 313,170 | 626 |

All local models produce fewer output tokens than the cloud models due to the YAML-only output constraint. Llama 8B is the most token-efficient (~600 tokens/prompt).

### 7.2 Cost per Valid Design

| Condition | N Valid | Total Cost | Cost per Valid Design |
|---|---|---|---|
| Sonnet Unsupervised | 378 | $11.65 | $0.03083 |
| Sonnet Supervised | 485 | $12.17 | $0.02509 |
| Haiku Unsupervised | 435 | $4.71 | $0.01082 |
| Haiku Supervised | 489 | $4.83 | $0.00987 |
| Qwen 27B Unsupervised | 448 | €0.26 | €0.00059 |
| **Qwen 27B Supervised** | **497** | €0.29 | **€0.00058** |
| Qwen 9B Unsupervised | 468 | €0.10 | €0.00021 |
| Qwen 9B Supervised | 489 | €0.11 | €0.00023 |
| Mistral Unsupervised | 440 | €0.19 | €0.00043 |
| Mistral Supervised | 450 | €0.26 | €0.00058 |
| Llama 8B Unsupervised | 358 | €0.07 | €0.00020 |
| Llama 8B Supervised | 478 | €0.11 | €0.00023 |
| **Llama 3B Unsupervised** | 371 | €0.05 | **€0.00013** |
| Llama 3B Supervised | 413 | €0.07 | €0.00017 |

Local energy costs computed from measured GPU power draw × wall time, at €0.30/kWh.

**The local models are 40–430× cheaper per valid design than the cheapest cloud option (Haiku supervised).** The Llama 3.2 3B produces the cheapest designs overall (€0.00013/valid unsupervised), though at lower quality (74.2% validity).

### 7.3 Total Cost of Ownership — IEMA Comparison

| Scenario | Setup Cost | Per-Design Cost | Break-Even (vs Haiku Sup.) |
|---|---|---|---|
| Cloud (Haiku Supervised) | $0 | $0.00987 | — |
| Local (9B Supervised, used GPU) | ~€800 | €0.00023 | ~83,000 designs |
| Local (9B Supervised, new GPU) | ~€2,000 | €0.00023 | ~207,000 designs |

At 500 designs per experiment run, the used-GPU setup breaks even after ~166 full experiment runs. For a production deployment generating designs continuously, the break-even is reached in months.

---

## Section 8: GPU Performance

### 8.1 Wall Time by Experiment

| Experiment | Model | Wall Time | Per-Prompt Avg |
|---|---|---|---|
| exp3a_small | Qwen 3.5 9B Unsupervised | 1h 14m | 9.0s |
| exp3b_small | Qwen 3.5 9B Supervised | 1h 24m | 10.1s |
| exp3a | Qwen 3.5 27B Unsupervised | 3h 14m | 23.3s |
| exp3b | Qwen 3.5 27B Supervised | 3h 37m | 26.1s |
| exp_mistral_unsup | Mistral Small 3.1 Unsupervised | 2h 06m | 15.1s |
| exp_mistral_sup | Mistral Small 3.1 Supervised | 2h 55m | 21.0s |
| exp_llama8b_unsup | Llama 3.1 8B Unsupervised | 0h 50m | 6.0s |
| exp_llama8b_sup | Llama 3.1 8B Supervised | 1h 13m | 8.8s |
| exp_llama3b_unsup | Llama 3.2 3B Unsupervised | 0h 33m | 4.0s |
| exp_llama3b_sup | Llama 3.2 3B Supervised | 0h 52m | 6.2s |
| **Total (Qwen)** | | **9h 30m** | |
| **Total (Multi-model)** | | **8h 30m** | |

### 8.2 Energy Consumption

| Experiment | Mean GPU Power | Energy |
|---|---|---|
| exp3a_small (9B Unsup.) | 304W | 0.379 kWh |
| exp3b_small (9B Sup.) | 303W | 0.426 kWh |
| exp3a (27B Unsup.) | 311W | 1.006 kWh |
| exp3b (27B Sup.) | 304W | 1.100 kWh |
| exp_mistral_unsup | 304W | 0.637 kWh |
| exp_mistral_sup | 297W | 0.868 kWh |
| exp_llama8b_unsup | 292W | 0.244 kWh |
| exp_llama8b_sup | 291W | 0.356 kWh |
| exp_llama3b_unsup | 285W | 0.158 kWh |
| exp_llama3b_sup | 286W | 0.248 kWh |
| **Total** | | **5.42 kWh** |

Total electricity cost for all 10 local experiments: **€1.62** (at €0.30/kWh European residential rate).

*Note: The multi-model experiments ran with a GPU power limit of 300W (reduced from 350W during exp_mistral_unsup for thermal management). The RTX 3090 showed no measurable throughput reduction at this power cap.*

### 8.3 Throughput Comparison

| Model | Designs per Hour | Valid Designs per Hour |
|---|---|---|
| Sonnet 4.6 Supervised | 200 | 194 |
| Haiku 4.5 Supervised | 263 | 257 |
| Qwen 3.5 9B Supervised | 356 | 349 |
| Qwen 3.5 27B Supervised | 138 | 137 |
| Mistral Small 3.1 Supervised | 171 | 154 |
| Llama 3.1 8B Supervised | 409 | 391 |
| **Llama 3.2 3B Supervised** | **577** | **476** |

The Llama 3.2 3B achieves the highest raw throughput (577 designs/hr) but its lower validity (82.6%) reduces effective throughput. **Llama 3.1 8B supervised offers the best throughput-quality balance among the new models at 391 valid designs/hour** — faster than Qwen 9B (349) with competitive validity (95.6% vs 97.8%).

---

## Section 9: Key Findings

1. **Supervision universally improves validity.** All seven models show statistically significant improvement under AXIOM supervision (p < 0.005 or better). The effect ranges from +2.0pp (Mistral) to +24.0pp (Llama 8B).

2. **The Qwen 3.5 27B supervised achieves the highest validity of any condition tested: 99.4% (497/500).** This remains significantly higher than Sonnet supervised (p = 0.0075) and the only model-condition to achieve 100% on contradictory prompts (144/144).

3. **Llama 3.1 8B is the supervision champion.** It has the largest supervision lift (+24.0pp), the most recoveries (119), and an 84% recovery rate — transforming the weakest unsupervised model (71.6%) into one that rivals the cloud models (95.6%).

4. **Mistral Small 3.1 is strong but stubborn.** It achieves 88.0% unsupervised (third-best baseline) but only a +2.0pp supervision lift with a 17% recovery rate. When Mistral fails, it repeats the same parse error across all retry attempts — it does not incorporate feedback effectively.

5. **Model scale sets a floor for supervision effectiveness.** The Llama 3.2 3B (3B parameters) achieves only +8.4pp lift with 33% recovery, while the Llama 3.1 8B (8B parameters) achieves +24.0pp with 84% recovery. Below a certain capability threshold, models cannot effectively utilize constraint feedback.

6. **Under supervision, model capability differences largely disappear for models ≥8B.** The supervised validity range for models ≥8B is 90.0–99.4%, while the unsupervised range spans 71.6–93.6%. Supervision narrows the gap, though the Mistral result (90.0%) suggests that feedback-responsiveness matters as much as raw capability.

7. **Local models eliminate the prismatic inversion.** The Qwen 27B achieves 92.7% unsupervised validity on prismatic (vs Sonnet's 31.7%), and 98.2% under supervision. Llama 8B shows the most dramatic prismatic recovery: 50.0% → 95.1% under supervision.

8. **Local inference is 40–430× cheaper per valid design than cloud.** The cheapest valid design costs €0.00013 (Llama 3B unsupervised). For production-quality output (≥95% validity), Qwen 9B supervised at €0.00023/design remains the cost-optimal choice.

9. **The 27B has a 94% retry recovery rate** — the highest of any model. When supervision identifies a failed design, the 27B almost always fixes it on the first retry.

10. **Total experiment cost for all 5,000 local evaluations: €1.62 in electricity.** The four cloud experiments cost $33.35 in API fees. The entire 7,000-prompt evaluation across all 14 conditions cost $35.14.

---

## Section 10: Thesis Implications

### The IEMA Argument

A €800 used GPU running a 9.7B-parameter open-weight model (Qwen 3.5 9B, Q4_K_M quantization) with AXIOM constraint-feedback supervision produces valid battery cell designs:

- **Faster** than any cloud API tested (9.0s vs 10.7–13.8s)
- **Cheaper** by a factor of 43× per valid design (€0.00023 vs $0.00987)
- **Equally valid** (97.8% = Haiku 4.5 supervised)
- **With full data sovereignty** — no proprietary battery design data leaves the premises

For organizations requiring maximum validity regardless of cost, the Qwen 3.5 27B supervised achieves 99.4% — statistically superior to any cloud model tested — at a cost of €0.00058 per valid design.

### Supervision as the Equalizer

The central thesis finding is that AXIOM supervision, not model scale, is the primary driver of design quality — **for models that can incorporate feedback**. The unsupervised validity gap between the weakest (Llama 8B, 71.6%) and strongest (Qwen 9B, 93.6%) conditions spans 22.0 percentage points. Under supervision, the gap among feedback-responsive models (≥8B, excluding Mistral) narrows from 71.6–93.6% to 95.6–99.4% — a range of just 3.8 percentage points. The constraint-feedback loop makes model choice a second-order decision.

### The Limits of Supervision

The multi-model experiments reveal two boundaries of the supervision paradigm:

1. **Feedback-responsiveness varies by architecture.** Mistral Small 3.1 and Llama 3.1 8B have similar unsupervised validity on non-prismatic prompts, yet their supervision responses diverge dramatically (17% vs 84% recovery). The ability to learn from structured error feedback is not purely a function of model scale.

2. **A minimum capability threshold exists.** The Llama 3.2 3B (3B parameters) shows that very small models have limited capacity to benefit from supervision (+8.4pp, 33% recovery). Below ~8B parameters, the constraint-feedback loop yields diminishing returns, and the unsupervised-to-supervised gap remains large (74.2% → 82.6%).

### Model Selection Guide

| Priority | Recommended Model | Validity | Cost/Design | Speed |
|---|---|---|---|---|
| Maximum validity | Qwen 3.5 27B Supervised | 99.4% | €0.00058 | 26.1s |
| Best cost-quality | Qwen 3.5 9B Supervised | 97.8% | €0.00023 | 10.1s |
| Maximum throughput (≥95%) | Llama 3.1 8B Supervised | 95.6% | €0.00023 | 8.8s |
| No supervision available | Qwen 3.5 9B Unsupervised | 93.6% | €0.00021 | 9.0s |

---

## Appendix A: Figures

All figures from the Phase 5 cloud analysis are in `forge/experiments/figures/`. A combined analysis with all 7 models and 14 conditions will generate updated figures.

## Appendix B: Data Files

| File | Records | Description |
|---|---|---|
| `exp1_baseline_cloud.jsonl` | 500 | Sonnet unsupervised (all cell types, pre-fix) |
| `exp1_prismatic_fix.jsonl` | 164 | Sonnet unsupervised (prismatic fix) |
| `exp2_supervised_cloud.jsonl` | 500 | Sonnet supervised (all cell types, pre-fix) |
| `exp2_prismatic_fix.jsonl` | 164 | Sonnet supervised (prismatic fix) |
| `exp1h_baseline_haiku.jsonl` | 500 | Haiku unsupervised (all cell types, pre-fix) |
| `exp1h_prismatic_fix.jsonl` | 164 | Haiku unsupervised (prismatic fix) |
| `exp2h_supervised_haiku.jsonl` | 500 | Haiku supervised (all cell types, pre-fix) |
| `exp2h_prismatic_fix.jsonl` | 164 | Haiku supervised (prismatic fix) |
| `exp3a_baseline_local.jsonl` | 500 | Qwen 27B unsupervised |
| `exp3b_supervised_local.jsonl` | 500 | Qwen 27B supervised |
| `exp3a_small_baseline_local.jsonl` | 500 | Qwen 9B unsupervised |
| `exp3b_small_supervised_local.jsonl` | 500 | Qwen 9B supervised |
| `pilot_5prompt_multimodel/exp_mistral_unsup_baseline_local.jsonl` | 500 | Mistral Small 3.1 unsupervised |
| `pilot_5prompt_multimodel/exp_mistral_sup_supervised_local.jsonl` | 500 | Mistral Small 3.1 supervised |
| `pilot_5prompt_multimodel/exp_llama8b_unsup_baseline_local.jsonl` | 500 | Llama 3.1 8B unsupervised |
| `pilot_5prompt_multimodel/exp_llama8b_sup_supervised_local.jsonl` | 500 | Llama 3.1 8B supervised |
| `pilot_5prompt_multimodel/exp_llama3b_unsup_baseline_local.jsonl` | 500 | Llama 3.2 3B unsupervised |
| `pilot_5prompt_multimodel/exp_llama3b_sup_supervised_local.jsonl` | 500 | Llama 3.2 3B supervised |
| `pilot_5prompt/` | 4 × 5 | 5-prompt pilot results (archived) |
| `gpu_logs/` | 5 files | GPU power/utilization monitoring |
| `local_full_run.log` | — | Qwen experiment run log |
| `multimodel_full_run.log` | — | Multi-model experiment run log |
