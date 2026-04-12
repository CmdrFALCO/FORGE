# Fine-Tuning Diagnostic Report — QLoRA on Qwen 2.5 7B

*Date: 2026-04-03*
*Status: Both adapters trained and exported. Both fail at inference.*

---

## 1. Timeline

| Attempt | Training Config | Result |
|---|---|---|
| **V1** | SFTTrainer, loss on all tokens | Model regurgitates user prompts. 0/5 valid. |
| **V2** | Added `completion_only_loss=True` | TRL flag not applied by Unsloth patches. Same masking as V1. |
| **V3** | Unsloth `train_on_responses_only()` | Masking verified correct (83% masked). Model produces YAML blocks but wrong schema. 0/5 valid. |

**Base Qwen 2.5 7B (unfinetuned): 4/5 valid** on the same 5 prompts.

---

## 2. What Each Version Produced

### V1 — All-token loss (broken)
```
This is for electric delivery truck project. Safety is the top priority.
Weight should be minimized...
```
Model predicted user-style text. Learned to continue conversations, not to produce assistant responses.

### V3 — Assistant-only loss (correct masking, wrong output)

**Without system prompt (raw Ollama test):**
```yaml
voltage:
  nominal: 3.67
training_info:
  num_epochs: 81
  batch_size: 512
  loss:
    total: 1.43
configuration:
  num_layers: 19
```
Produces YAML (format learned) but ML config schema (wrong content). The base model's pretraining prior for "YAML" is neural network configs, and the LoRA adapter wasn't strong enough to override this.

**With AXIOM system prompt (full pipeline):**
```
Parse error: YAML parse error: mapping values are not allowed here
  Training config: Training config training confi...
```
Even with the 2,500-token system prompt specifying the exact battery cell schema, the model generates "Training config:" text. The adapter has overwritten the base model's instruction-following capability.

---

## 3. Root Cause Analysis

### The masking fix was necessary but not sufficient

V1's failure (predicting user prompts) was caused by training on all tokens. V3's masking fix (83% masked, loss only on assistant YAML) was verified correct at the data level. The model DID learn to produce YAML blocks instead of prose — that's progress.

### The LoRA adapter degraded instruction-following

The fundamental problem: **LoRA r=16 with 4,000 examples overwrote the base model's general instruction-following capability without successfully replacing it with battery-specific generation.**

Evidence:
- The base Qwen 2.5 7B scores 4/5 on the same prompts — it can follow the AXIOM system prompt and produce valid battery cell YAML.
- The fine-tuned model cannot follow the same system prompt. It ignores the schema specification and defaults to its pretraining prior for YAML (ML configs).
- The adapter changed the model's output format (prose → YAML) but corrupted its ability to attend to the system prompt's content.

This is a known failure mode: **catastrophic forgetting in parameter-efficient fine-tuning.** The LoRA adapter modifies the attention projections (q/k/v/o) and MLP layers just enough to shift the output distribution, but not enough to encode the domain-specific schema. The result is a model that "knows" it should output YAML but doesn't "know" which YAML.

### Why 4,000 examples wasn't enough

The training data contains 4,000 (system_prompt, user_prompt, assistant_YAML) conversations. Each assistant response is ~500 tokens of battery cell YAML. But:

1. **The system prompt varies by cell type** (3 variants × ~2,500 tokens each). The model needs to learn the mapping from each system prompt variant to the corresponding YAML schema.

2. **The YAML schema has ~50 distinct field names** across 6 hierarchical sections. Each field name appears in only ~30% of training examples (cell-type-dependent).

3. **LoRA r=16 provides only 40M trainable parameters** — 0.53% of the 7.6B total. This is a very thin adapter layer to encode both the YAML structure AND the field-level content for 3 cell types.

4. **The base model has a strong pretraining prior** for what "YAML" looks like — primarily software config files. Overriding this prior requires either more training data, higher LoRA rank, or both.

---

## 4. Training Metrics (V3)

### Medium Adapter
| Metric | Value |
|---|---|
| Final train loss | 0.334 |
| Final val loss | 0.329 |
| Best val loss | 0.329 (step 700) |
| Training time | 700 min |
| Peak VRAM | 21.4 GB |

### Hard Adapter
| Metric | Value |
|---|---|
| Final train loss | 0.397 |
| Final val loss | 0.379 |
| Best val loss | 0.379 (step 700) |
| Training time | 763 min |
| Peak VRAM | 22.5 GB |

### Loss Trajectory (Medium)

| Eval Point | Epoch | Eval Loss |
|---|---|---|
| 1 | 0.4 | 0.3335 |
| 2 | 0.8 | 0.3316 |
| 3 | 1.2 | 0.3307 |
| 4 | 1.6 | 0.3306 |
| 5 | 2.0 | 0.3298 |
| 6 | 2.4 | 0.3295 |
| 7 | 2.8 | 0.3293 |

Val loss decreased monotonically but plateaued at ~0.329. This plateau represents the model learning YAML structure but not the specific battery schema — the loss floor is the base model's pretraining prior resisting the LoRA override.

---

## 5. What Worked

1. **Masking verification (Check #3)** correctly identified that V1/V2 were training on all tokens. The `train_on_responses_only()` function with `instruction_part='<|im_start|>user\n'` and `response_part='<|im_start|>assistant\n'` produced correct masking: 83% masked, 17% active on assistant tokens only.

2. **The GGUF export pipeline** (manual via llama.cpp) works reliably. The V3 models produce coherent output through Ollama — the problem is what they produce, not how they're served.

3. **The evaluation pipeline** (Stage 5 config, suffix flag, experiment definitions) is ready and functional. When a working adapter exists, evaluation can run immediately.

---

## 6. Options Forward

### Option A: Higher LoRA rank (r=64 or r=128)

More trainable parameters means more capacity to encode the battery schema. At r=64, the adapter has ~160M parameters (4x current). This significantly increases VRAM during training — may require reducing batch size.

**Estimated VRAM at r=64:** ~23-24 GB (tight on RTX 3090)
**Estimated training time:** ~same per step, slightly more due to larger adapter

### Option B: Full fine-tuning (not LoRA)

Use Unsloth's full fine-tuning mode at 4-bit. All parameters are trainable (with quantized base). This gives the model maximum capacity to learn the schema but risks more catastrophic forgetting on non-battery tasks (irrelevant for our use case — we only need battery cell generation).

**Estimated VRAM:** ~22-23 GB (Unsloth optimized)
**Risk:** May lose the base model's general YAML fluency entirely

### Option C: More training data

Generate 20,000-50,000 examples instead of 5,000. More repetition of the schema fields gives the LoRA adapter more gradient signal. This doesn't require code changes to the training script — just rerun Stage 1 with `--target 20000`.

**Estimated generation time:** ~30 min (Stage 1 is fast)
**Estimated training time:** ~4x longer (60+ hours)

### Option D: Prompt-tuning approach

Instead of fine-tuning the model weights, embed the battery schema as a learned soft prompt prefix. This preserves the base model's instruction-following capability entirely while adding domain-specific context.

**Pros:** No catastrophic forgetting
**Cons:** Requires different training infrastructure (not SFTTrainer)

### Option E: Different base model

Qwen 2.5 7B Instruct may have a particularly strong pretraining prior for ML config YAML. A different model (e.g., Llama 3.1 8B, Mistral 7B) might have a weaker YAML prior and be easier to fine-tune toward battery schemas.

### Option F: Abandon fine-tuning for this thesis scope

The existing AXIOM results (Corpus A + B, 7 models, 10,500 evaluations) already tell a strong thesis story. The fine-tuning experiment, including its failure, is itself a finding: **domain-specific fine-tuning on structured output is harder than loss curves suggest, and completion-only masking is necessary but not sufficient.**

This finding can be written up as a "limitations and future work" section rather than a positive result. The thesis contribution remains the AXIOM supervision architecture, not the fine-tuning.

---

## 7. Recommendation

**Option C + A combined**: Generate 20,000 examples (4x current), train with LoRA r=64 (4x capacity), 3 epochs. This addresses both the data volume and adapter capacity issues simultaneously. Estimated time: ~24-36 hours generation + training.

If that fails, **Option F** is the pragmatic path. The fine-tuning failure is a genuine finding about the difficulty of teaching small models domain-specific structured output — it strengthens, not weakens, the thesis argument that AXIOM supervision on general-purpose models is a more practical approach than fine-tuning.

---

## 8. Lessons Learned

1. **Low training loss does not mean the model learned the right thing.** V1's 0.07 val loss was meaningless — the model got credit for predicting system prompts. V3's 0.33 was honest but still didn't produce valid output.

2. **Completion-only masking is necessary but not sufficient.** Without it, the model learns to predict everything. With it, the model learns the right output format but may not learn the right content.

3. **LoRA at small ranks can degrade instruction-following.** The adapter changed the model's output distribution (prose → YAML) but corrupted its ability to attend to system prompt content. This is catastrophic forgetting at the attention level.

4. **Always smoke-test before full evaluation.** The 5-prompt smoke test caught both V1 and V3 failures in minutes, saving hours of wasted inference.

5. **The base model is surprisingly good without fine-tuning.** Qwen 2.5 7B scored 4/5 on the same prompts where both fine-tuned variants scored 0/5. The AXIOM system prompt + few-shot example is more effective than 4,000 fine-tuning examples at LoRA r=16.

6. **Verify masking at the data level, not just the config level.** TRL's `completion_only_loss=True` was silently overridden by Unsloth's patches. Only the manual label inspection (Check #3) caught this.
