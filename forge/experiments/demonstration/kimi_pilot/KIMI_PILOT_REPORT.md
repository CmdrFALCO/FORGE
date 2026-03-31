# Kimi-VL-A3B-Thinking Pilot Report

*Date: 2026-03-30*
*Model: richardyoung/kimi-vl-a3b-thinking:Q4_K_M*
*Architecture: 16B total parameters, MoE (384 experts, 8 active), ~2.8B active per token*
*Corpus: 50-prompt stratified subset (17 cylindrical, 17 pouch, 16 prismatic)*

---

## 1. Headline Results

| Condition | Valid | Rate | Llama 3.2 3B (full run) |
|---|---|---|---|
| Unsupervised | 21/50 | 42.0% | 74.2% |
| Supervised | 35/50 | 70.0% | 82.6% |
| Supervision lift | +14 | +28.0 pp | +8.4 pp |
| Recovery rate | 14/29 | 48.3% | 32.6% |

Kimi-VL-A3B-Thinking performs significantly worse than Llama 3.2 3B on unsupervised generation (-32 pp) but responds substantially better to supervision (+28 pp lift vs +8.4 pp, 48% recovery vs 33%).

---

## 2. Failure Mode Categorisation

### 2.1 Unsupervised (29 rejects)

| Category | Count | % | Description |
|---|---|---|---|
| A — Parse failure | 8 | 28% | YAML could not be extracted (truncation, prose mixed in) |
| B — Schema error | 17 | 59% | YAML parsed but missing fields or out-of-range values |
| C — Physics violation | 4 | 14% | Design parsed and checked but failed constraints |

### 2.2 Supervised (15 rejects)

| Category | Count | Description |
|---|---|---|
| A — Parse failure | 3 | Token budget exhausted on all 4 attempts |
| B — Schema error | 11 | Missing sections not recoverable via feedback |
| C — Physics violation | 1 | Cathode-cavity fit not corrected |

### 2.3 Recovery by Category

| Original Category | Recovered | Stuck | Recovery Rate |
|---|---|---|---|
| Parse failure (8) | 3 | 5 | 38% |
| Schema error (17) | 9 | 8 | 53% |
| Physics violation (4) | 2 | 2 | 50% |

---

## 3. The Thinking Tax

The dominant factor explaining Kimi-VL's poor unsupervised performance is the output token budget consumed by chain-of-thought reasoning.

**Ollama strips `<think>` tokens from the delivered response, but they still count against `num_predict`.** With `num_predict=4000`:

| Metric | Value |
|---|---|
| Average tokens_out (valid designs) | ~1,966 |
| Average YAML content (valid designs) | ~340 tokens |
| Estimated thinking overhead | **~80%** of output budget |
| Effective YAML budget | ~400–1,000 tokens |
| Parse failures from token exhaustion | 7/8 (88% of parse failures) |

The model spends ~3,000+ tokens on invisible reasoning, leaving insufficient budget for a complete YAML specification. This directly causes 7 of 8 parse failures and likely contributes to the 17 schema errors (incomplete YAML due to truncation of later sections).

**Evidence**: Rejects average 2,743 tokens_out vs 1,966 for passes — the model "thinks harder" on prompts it ultimately fails, consuming even more budget.

---

## 4. Failure Signatures

### 4.1 Comparison with Llama 3.2 3B

| Dimension | Kimi-VL-A3B-Thinking | Llama 3.2 3B |
|---|---|---|
| Dominant failure | Missing entire sections | Field renaming under feedback |
| Retry behaviour | **Stubborn** (same error x4) | **Chaotic** (new errors each attempt) |
| Error trajectory | Flat or worsening | Diverging (1.5→3.3 errors) |
| Field renaming? | No | Yes (dominant pathology) |
| Parse failures? | Yes (28% of rejects) | Rare |
| Thinking overhead? | ~80% of output budget | N/A |

Kimi-VL and Llama 3B fail in qualitatively different ways. Kimi-VL's thinking mode causes it to reason from scratch on each retry rather than incrementally editing, which prevents the Llama 3B "chaotic mutation" failure but also prevents incremental correction. The result is a "stubborn" model that repeats the same error across all 4 attempts.

### 4.2 Cell Type Breakdown

| Cell Type | Unsup Reject Rate | Llama 3B (full run) |
|---|---|---|
| Cylindrical (17) | 29% | 58% |
| Pouch (17) | 65% | 92% |
| Prismatic (16) | **81%** | 71% |

Kimi-VL is better than Llama 3B on cylindrical (+29 pp) but worse on prismatic (-10 pp). The prismatic weakness is driven by a blind spot for `envelope.internals` (6 cases, 4 irrecoverable).

### 4.3 Supervised Retry Patterns

| Pattern | Count | Description |
|---|---|---|
| Stuck (same error x4) | 7/15 | Ignores feedback completely |
| Partial fix | 4/15 | Reduces but doesn't eliminate errors |
| Worsening | 2/15 | Error count escalates under feedback |
| Category shift | 2/15 | Oscillates between parse and schema failures |

---

## 5. Key Findings

1. **The capability floor holds at ~3B active parameters, regardless of architecture.** Doubling the output token budget (4K→8K) improved unsupervised validity by only +4 pp (42%→46%), confirming that the poor performance is a capability limitation, not a budget problem. At 2.8B active parameters, neither MoE routing, chain-of-thought reasoning, nor additional output room compensates for insufficient model capacity.

2. **Thinking mode helps feedback incorporation but hurts first-attempt generation.** Kimi-VL's recovery rate (48%) exceeds Llama 3B's (33%), and its supervision lift (+28 pp) is the third-largest of any model tested (behind Llama 8B's +24 pp and Sonnet's +21.4 pp on the full corpus). However, its unsupervised validity (42–46%) is far below Llama 3B (74.2%). The thinking mode creates a net negative for unsupervised generation (prose contamination, token waste) but a net positive for supervised correction (better reasoning about feedback).

3. **Different failure signature from Llama 3B.** No field-renaming pathology. Kimi-VL is "stubborn" (repeats identical errors across 4 attempts) rather than "chaotic" (mutates errors on each attempt). The thinking model reasons from scratch on each retry rather than incrementally editing, which prevents cascading mutations but also prevents incremental correction.

4. **Prismatic blind spot.** The model has not learned the `envelope.internals` schema section. This affects 6/16 prismatic prompts (81% prismatic reject rate) and is not recoverable via feedback.

5. **Vision encoder is pure overhead.** No evidence that the VL architecture helps or hinders text-only YAML generation. The MoonViT parameters (~200M) contribute nothing to this task.

6. **`think: false` is not suppressible for this model.** The `◁think▷` markers are baked into the model weights via fine-tuning. Neither the Ollama API flag, system prompt overrides, nor custom Modelfiles can disable them. This is a practical limitation for deploying thinking models in structured output pipelines.

---

## 6. Rerun: Budget Ablation

### Proposed Rerun: Budget Ablation

Two confounded factors were hypothesised:
- **Factor A**: Thinking overhead consuming output budget (testable by increasing `num_predict`)
- **Factor B**: Thinking mode generating prose instead of YAML (testable by disabling thinking)

**Run 3 (`think: false`) was not feasible.** Testing revealed that the `◁think▷` markers are baked into the model weights via fine-tuning, not a toggleable Ollama flag. Neither the `think: false` API parameter, system prompt overrides, nor custom Modelfiles suppressed the thinking behaviour. Only assistant message prefilling (injecting closed thinking tags) worked, but this required modifications to the experiment runner's message management that would compromise comparability.

**Run 2 (`num_predict=8000`) was executed** to isolate Factor A.

### Run 2 Results

| Condition | Run 1 (4K tokens) | Run 2 (8K tokens) | Delta |
|---|---|---|---|
| Unsupervised | 21/50 (42.0%) | 23/50 (46.0%) | **+4.0 pp** |
| Supervised | 35/50 (70.0%) | 35/50 (70.0%) | **+0.0 pp** |
| Recovery rate | 14/29 (48.3%) | 12/27 (44.4%) | -3.9 pp |

Prediction was 55–65% unsupervised. Actual: 46%. Doubling the token budget added only 2 valid designs unsupervised and zero supervised. The 7 parse failures from token truncation were replaced by 7 new schema errors — the model now completes the YAML but still produces invalid content.

### Interpretation

**The problem is capability, not budget.** The thinking overhead (Factor A) accounts for at most +4 pp of the deficit. The remaining ~28 pp gap versus Llama 3.2 3B (74.2%) reflects a genuine capability limitation at 2.8B active parameters. Even with unlimited output budget, this model cannot reliably produce valid battery cell YAML.

This result strengthens the capability floor finding from the main experiments: the threshold for effective structured generation lies in the 3–8B parameter range, and neither MoE architecture nor chain-of-thought reasoning lowers it meaningfully.

---

## 7. Summary: All Kimi Pilot Runs

| Run | num_predict | Unsup | Sup | Lift | Recovery |
|---|---|---|---|---|---|
| Run 1 (baseline) | 4,000 | 42.0% (21/50) | 70.0% (35/50) | +28.0 pp | 48.3% |
| Run 2 (doubled budget) | 8,000 | 46.0% (23/50) | 70.0% (35/50) | +24.0 pp | 44.4% |
| **Llama 3.2 3B (full run, comparison)** | 2,000 | **74.2%** | **82.6%** | +8.4 pp | 32.6% |

**Verdict: do not promote to full 500-prompt run.** Kimi-VL-A3B-Thinking at 2.8B active parameters is well below the capability floor for this task. Its interesting property — higher feedback-responsiveness than Llama 3B — is offset by dramatically worse first-attempt generation. The pilot confirms the thesis finding that the ~3B parameter range is insufficient for structured engineering output, regardless of architecture (dense vs MoE), training approach (standard vs reasoning-tuned), or modality (text-only vs vision-language).

### Thesis relevance

This pilot adds a 5th model family (Moonshot AI) and a new architecture variant (MoE + thinking) to the capability floor evidence. The finding that thinking mode improves recovery rate (+48% vs +33%) but worsens generation (42% vs 74%) at small scale provides a nuance to the feedback-responsiveness discussion in Section 5.5: reasoning capability and generation capability can be independently variable even within a single model, depending on the mode of operation.
