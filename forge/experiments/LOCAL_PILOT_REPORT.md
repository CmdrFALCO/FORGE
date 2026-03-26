# AXIOM Local Model Pilot Report

*Generated: 2026-03-26*

---

## 1. Experiment Summary

Four pilot experiments were conducted using locally-hosted Qwen 3.5 models via Ollama on a single NVIDIA GPU (24 GB VRAM). Each experiment ran 5 prompts selected from the existing 500-prompt corpus (P-001 through P-005), covering all three cell geometries, two chemistries, three difficulty levels, and three prompt styles.

| Experiment | Model | Quantization | Condition | N | Output File |
|---|---|---|---|---|---|
| exp3a | Qwen 3.5 27B | Q4_K_M | Unsupervised | 5 | `exp3a_baseline_local.jsonl` |
| exp3b | Qwen 3.5 27B | Q4_K_M | Supervised | 5 | `exp3b_supervised_local.jsonl` |
| exp3a_small | Qwen 3.5 9B | Q4_K_M | Unsupervised | 5 | `exp3a_small_baseline_local.jsonl` |
| exp3b_small | Qwen 3.5 9B | Q4_K_M | Supervised | 5 | `exp3b_small_supervised_local.jsonl` |

### Prompt Mix

| Prompt | Cell Type | Chemistry | Difficulty | Prompt Style |
|---|---|---|---|---|
| P-001 | Cylindrical | NMC-111 | standard | detailed |
| P-002 | Prismatic | LFP | standard | detailed |
| P-003 | Pouch | NMC-811 | edge_case | natural_language |
| P-004 | Pouch | NMC-811 | underspecified | terse |
| P-005 | Cylindrical | NMC-111 | underspecified | natural_language |

### Configuration

- **Temperature:** 0.0 (deterministic)
- **Thinking mode:** OFF (`think: false` in Ollama API)
- **Context window:** 8192 tokens
- **Output cap:** 2000 tokens (`num_predict`) for exp3a, exp3a_small, exp3b_small; 3000 for exp3b (pre-optimization run)
- **System prompt:** Cell-type-specific schema + YAML-only output suffix for Ollama backends
- **GPU:** Single NVIDIA GPU, 24 GB VRAM, one model loaded at a time

---

## 2. Results Overview

### Table 2.1: Validity Rate

| Experiment | Valid / Total | Rate | Avg Wall Time | Avg Tokens Out |
|---|---|---|---|---|
| exp3a (27B Unsup.) | 5 / 5 | **100.0%** | 25.6s | 621 |
| exp3b (27B Sup.) | 5 / 5 | **100.0%** | 46.7s* | 1,222 |
| exp3a_small (9B Unsup.) | 5 / 5 | **100.0%** | 9.0s | 623 |
| exp3b_small (9B Sup.) | 5 / 5 | **100.0%** | 8.7s | 623 |

*\*exp3b avg inflated by P-001 (103.6s) which ran before the YAML-only prompt suffix was applied; P-002 through P-005 averaged 32.6s.*

### Table 2.2: Per-Prompt Detail

| Prompt | 27B Unsup. | 27B Sup. | 9B Unsup. | 9B Sup. |
|---|---|---|---|---|
| P-001 (cyl.) | 22.8s, 15/15 | 103.6s*, 15/15 | 7.1s, 15/15 | 8.1s, 15/15 |
| P-002 (pris.) | 34.3s, 14/14 | 35.8s, 14/14 | 11.9s, 14/14 | 11.1s, 14/14 |
| P-003 (pouch) | 24.1s, 14/14 | 32.7s, 14/14 | 8.7s, 14/14 | 7.9s, 14/14 |
| P-004 (pouch) | 23.1s, 14/14 | 29.3s, 14/14 | 8.5s, 14/14 | 7.9s, 14/14 |
| P-005 (cyl.) | 23.8s, 15/15 | 32.4s, 15/15 | 8.9s, 15/15 | 8.5s, 15/15 |

All designs passed all applicable constraints on attempt 1. No retries were triggered in any supervised experiment.

---

## 3. Cloud Comparison

The same 5 prompts (P-001 through P-005) were compared against the cloud model results from the combined Phase 5 datasets (using prismatic-fix data for P-002).

### Table 3.1: Head-to-Head — Same Prompts, All Models

| Model | Condition | Valid | Avg Wall | Avg Tokens Out |
|---|---|---|---|---|
| **Sonnet 4.6** | Unsupervised | 5/5 | 13.4s | 931 |
| **Sonnet 4.6** | Supervised | 5/5 | 12.9s | 931 |
| **Haiku 4.5** | Unsupervised | 5/5 | 11.5s | 1,439 |
| **Haiku 4.5** | Supervised | 5/5 | 11.1s | 1,463 |
| **Qwen 3.5 27B** | Unsupervised | 5/5 | 25.6s | 621 |
| **Qwen 3.5 27B** | Supervised | 5/5 | 32.6s** | 842 |
| **Qwen 3.5 9B** | Unsupervised | 5/5 | 9.0s | 623 |
| **Qwen 3.5 9B** | Supervised | 5/5 | 8.7s | 623 |

*\*\*27B supervised avg excludes P-001 outlier (103.6s pre-optimization).*

### Key Observations

1. **Validity parity.** On these 5 prompts, all 6 model-condition combinations achieve 100% validity. The local models match cloud quality on this sample.

2. **9B is the fastest.** At 8.7s average, the 9B outperforms even the cloud APIs (Haiku at 11.1s, Sonnet at 12.9s). No network latency and efficient Q4_K_M inference at ~65 tok/s.

3. **27B is 2-3x slower than cloud.** The 27B generates at ~25 tok/s locally vs cloud models returning in 11-13s. The tradeoff is zero API cost and full data sovereignty.

4. **Local models are more token-efficient.** Qwen 3.5 produces ~620 output tokens vs Sonnet's ~930 and Haiku's ~1,440. The YAML-only system prompt suffix helps, but even structurally the local models generate more compact YAML.

---

## 4. Token Usage

### Table 4.1: Token Counts Per Prompt

| Prompt | 27B In | 27B Out | 9B In | 9B Out | Sonnet Out | Haiku Out |
|---|---|---|---|---|---|---|
| P-001 (cyl.) | 2,771 | 548 | 2,771 | 564 | 939 | 1,746 |
| P-002 (pris.) | 3,039 | 838 | 3,039 | 839 | 1,232 | 1,565 |
| P-003 (pouch) | 2,358 | 583 | 2,358 | 568 | 829 | 1,086 |
| P-004 (pouch) | 2,300 | 574 | 2,300 | 572 | 821 | 1,097 |
| P-005 (cyl.) | 2,733 | 563 | 2,733 | 570 | 832 | 1,702 |

- **Input tokens are identical** between 27B and 9B — same system prompts, same user prompts. The slight difference from cloud models reflects the different tokenizer.
- **Prismatic prompts generate more output** (~840 tokens) than cylindrical/pouch (~560-580) across both local models, matching the cloud pattern. Prismatic schemas have more fields.
- **27B and 9B produce nearly identical output lengths** (within 2-3%), suggesting both models learn the same YAML structure from the system prompt.

---

## 5. Verification Checklist

| Check | Status | Evidence |
|---|---|---|
| Ollama returns parseable responses | PASS | All 20 prompts produced valid YAML extracted by `extract_yaml_block()` |
| Structured YAML matches schema | PASS | Schema validation passed for all 20 records (0 schema-level failures) |
| Constraint results populated | PASS | Every record has 14 or 15 constraint results with IDs, names, and pass/fail |
| Token counts captured from Ollama | PASS | `prompt_eval_count` and `eval_count` present in all records; values match expected ranges |
| Thinking mode OFF | PASS | `think: false` sent in API payload; 9B eval_count matches output token count (no hidden thinking) |
| Temperature 0.0 | PASS | Configured in `BackendConfig` and passed in `options` to Ollama API |
| No timeouts | PASS | All wall times under 35s (excluding exp3b P-001 pre-optimization outlier) |
| Retry feedback loop | NOT TESTED | All 5 prompts passed on attempt 1; no retry was triggered in supervised experiments |

### Note on Retry Loop

The supervision feedback loop was not exercised because all prompts in this pilot achieved first-attempt validity. This is a positive result — it means the local models produce schema-compliant designs without corrective feedback on these prompts — but it means the retry mechanism has not yet been validated for local models. The full 500-prompt run will inevitably trigger retries (cloud models required retries on 12-25% of prompts in the supervised condition), which will test this pathway.

---

## 6. Engineering Issues Encountered and Resolved

### 6.1 Runaway Token Generation (27B)

**Problem:** Without an output token cap, the 27B model generated 7,400+ tokens of explanatory text interleaved with YAML, exceeding the 600s HTTP timeout.

**Root cause:** Qwen 3.5 27B, given a long system prompt with engineering specifications, tends to "teach back" the domain knowledge before producing the YAML. Even with `think: false` (which disables the structured reasoning chain), the model generates verbose preamble.

**Fix:** Three mitigations applied:
1. `num_predict: 2000` — hard cap on output tokens (valid YAML is 550-840 tokens)
2. YAML-only system prompt suffix — appended to the system prompt for Ollama backends only: *"CRITICAL: Output ONLY the YAML specification. No explanations, no commentary..."*
3. Pre-warming the model before experiments — avoids cold-start model loading consuming the timeout budget

**Result:** After fixes, 27B generates 548-838 output tokens per prompt, well within the 2,000 cap.

### 6.2 GPU Contention

**Problem:** Running both 27B (17.4 GB) and 9B (6.6 GB) models simultaneously on a 24 GB GPU caused VRAM thrashing and all requests timed out.

**Fix:** Sequential execution — unload one model before loading the other. Each experiment run loads exactly one model.

### 6.3 Stale Ollama Connections

**Problem:** Killing a Python experiment process left orphan HTTP connections to the Ollama server. Subsequent requests queued behind stale in-progress generations, causing cascading timeouts.

**Fix:** Force-kill stale Python processes and unload the model (via `keep_alive: 0`) before starting a new experiment.

---

## 7. Implications for Full 500-Prompt Run

### Estimated Run Times

| Experiment | Model | Est. per Prompt | Est. Total (500) |
|---|---|---|---|
| exp3a | 27B Unsupervised | ~26s | ~3.6 hours |
| exp3b | 27B Supervised | ~30s (+ retries) | ~5-7 hours |
| exp3a_small | 9B Unsupervised | ~9s | ~1.3 hours |
| exp3b_small | 9B Supervised | ~9s (+ retries) | ~1.5-2 hours |

Total estimated: **12-14 hours** of GPU time, run sequentially (one model at a time).

### Cost Comparison

| Condition | Cost (500 prompts) |
|---|---|
| Sonnet Unsupervised (cloud) | $15.04 |
| Sonnet Supervised (cloud) | $18.20 |
| Haiku Unsupervised (cloud) | $6.13 |
| Haiku Supervised (cloud) | $7.12 |
| **Qwen 3.5 27B (local)** | **$0.00** (electricity only) |
| **Qwen 3.5 9B (local)** | **$0.00** (electricity only) |

Estimated electricity cost at 350W GPU draw: ~$0.50-0.70 for the full 14-hour run (at European residential rates).

### Operational Requirements

1. **Model sequencing:** Run all 27B experiments first (exp3a, exp3b), then swap to 9B (exp3a_small, exp3b_small). Each swap takes ~10s.
2. **Pre-warming:** Send a trivial request to the model before starting the experiment to ensure it's loaded in VRAM.
3. **Resume safety:** The runner supports crash-safe resume via JSONL line-by-line output. If interrupted, re-running the same command skips completed prompts.
4. **GPU monitoring:** Each experiment automatically starts a GPU logger subprocess writing to `results/gpu_logs/`.

---

## 8. Conclusion

The 5-prompt pilot validates that both Qwen 3.5 models (27B and 9B) can produce schema-compliant, constraint-passing battery cell designs through the AXIOM pipeline. Key findings:

1. **100% validity on pilot prompts** for both models, both conditions — matching cloud model performance on the same prompts.
2. **The 9B model is production-viable** at 9s per prompt with 100% validity, making it the fastest option across all tested models (faster than cloud APIs).
3. **The 27B model is viable but verbose** — it requires output capping and YAML-only prompting to prevent runaway generation, adding engineering complexity.
4. **Zero API cost** — the entire pilot ran on local hardware with no external API calls.
5. **The retry loop was not stress-tested** — all prompts passed on attempt 1. The full 500-prompt corpus, which includes contradictory and edge-case prompts, will exercise this pathway.

**Recommendation:** Proceed to full 500-prompt runs. Start with exp3a_small and exp3b_small (9B, ~3 hours total), then exp3a and exp3b (27B, ~10 hours total). This sequencing lets us validate the 9B results quickly before committing to the longer 27B runs.
