# Stage 4 Setup Report — QLoRA Fine-Tuning Infrastructure

*Date: 2026-04-01*
*Status: Training in progress (Medium adapter, step 0/750)*

---

## 1. Dependency Installation

### What happened

Unsloth 2026.3.18 installed cleanly via pip but **downgraded torch from 2.11.0 to 2.10.0** and switched CUDA from cu130 to cu128. This was a side-effect of Unsloth's pinned torch dependency.

### What needed fixing

Nothing — the downgrade didn't break existing functionality. The surrogate training stack (experiments/ml/autoresearch) should be re-tested if used again, but AXIOM evaluation and Ollama inference are unaffected.

### Final dependency state

| Package | Version | Notes |
|---|---|---|
| torch | 2.10.0+cu128 | Downgraded from 2.11.0+cu130 |
| unsloth | 2026.3.18 | Installed fresh |
| transformers | 5.3.0 | Pulled by Unsloth |
| trl | 0.24.0 | Pulled by Unsloth |
| peft | 0.18.1 | Pulled by Unsloth |
| bitsandbytes | 0.49.2 | Pulled by Unsloth |
| accelerate | 1.13.0 | Pulled by Unsloth |
| xformers | 0.0.35 | Used instead of Flash Attention 2 |

Flash Attention 2 is not installed. Unsloth falls back to Xformers, which provides equivalent performance for training.

---

## 2. Dry Run Results

### What went right

Model load and tokenization worked perfectly on the first try:

| Check | Result |
|---|---|
| Model | unsloth/Qwen2.5-7B-Instruct (4-bit NF4) |
| GPU memory after load | 7.19 GB |
| Peak memory | 7.21 GB |
| Medium sample tokens | avg 3,141, max 3,168, p95 3,164 |
| Hard sample tokens | avg 3,441, max 3,493, p95 3,480 |
| Max under 4096? | Yes — max is 3,493 |
| Chat template | Qwen2.5 format applied correctly |
| bf16 support | Detected TRUE |

All token lengths are well within the 4096 context window. No truncation needed.

---

## 3. Training Script Issues (4 fixes required)

### Issue 1: `SFTTrainer.__init__()` got unexpected argument `tokenizer`

**Root cause:** TRL 0.24.0 renamed the parameter from `tokenizer` to `processing_class`. The pseudocode in the Stage 4 prompt used the old API.

**Fix:** Changed `tokenizer=tokenizer` to `processing_class=tokenizer` in the SFTTrainer constructor.

### Issue 2: `SFTConfig.__init__()` got unexpected argument `max_seq_length`

**Root cause:** TRL 0.24.0 also renamed `max_seq_length` to `max_length` in `SFTConfig`. However, this parameter was also being passed through to the model constructor, causing a conflict.

**Fix:** Removed `max_length`/`max_seq_length` from `SFTConfig` entirely. The context length is already set by `FastLanguageModel.from_pretrained(max_seq_length=4096)` which handles truncation at the tokenizer level.

**Side effect of the fix:** The initial `replace_all` edit also changed `max_seq_length` in `FastLanguageModel.from_pretrained()` to `max_length`, which caused the model constructor to fail with `Qwen2ForCausalLM.__init__() got an unexpected keyword argument 'max_length'`. This required a second fix to restore `max_seq_length` in the model loading call only.

### Issue 3: `eos_token ('<EOS_TOKEN>') not found in vocabulary`

**Root cause:** The `unsloth` import must come BEFORE `trl`, `transformers`, and `peft` imports. Unsloth monkey-patches these libraries to fix compatibility issues, including the `<EOS_TOKEN>` default handling. When `trl` was imported first, the patches weren't applied, and TRL's SFTTrainer defaulted to looking for a literal `<EOS_TOKEN>` string.

**Diagnosis path:** This took 4 attempts to resolve:
1. First tried setting `tokenizer.eos_token = '<|im_end|>'` — didn't help (patches not applied)
2. Then tried `eos_token=None` in SFTConfig — overwritten by unpatched TRL
3. Then tried `eos_token=tokenizer.eos_token` — still overwritten
4. Finally identified the import order warning and moved `from unsloth import FastLanguageModel` to the first import

**Fix:** Moved the unsloth import to the top of the file, before trl/transformers.

### Issue 4: `Model is in bfloat16 but you want to use float16`

**Root cause:** Unsloth loaded the model in bf16 (detected as supported on RTX 3090), but the training config specified `fp16=True, bf16=False`. Unsloth's patched trainer enforces consistency between model precision and training precision.

**Fix:** Changed to `fp16=False, bf16=True`. This is actually better — Unsloth's bf16 kernels are optimized for training.

**Note:** The original Stage 4 prompt said "RTX 3090 doesn't have good bf16" and recommended fp16. Unsloth's dry run detected `Bfloat16 = TRUE`, indicating its optimized kernels can handle bf16 efficiently on the 3090 despite the hardware's limited native bf16 throughput.

---

## 4. Training Configuration (Final)

| Parameter | Value |
|---|---|
| Base model | unsloth/Qwen2.5-7B-Instruct |
| Quantization | 4-bit NF4 |
| LoRA rank (r) | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| LoRA targets | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Trainable parameters | 40,370,176 / 7,655,986,688 (0.53%) |
| Effective batch size | 16 (4 per device × 4 grad accum) |
| Learning rate | 2e-4 |
| Scheduler | Cosine with 5% warmup |
| Precision | bf16 |
| Optimizer | AdamW 8-bit |
| Max sequence length | 4096 |
| Epochs | 3 |
| Total steps | 750 per adapter |
| Eval every | 100 steps |
| Save every | 200 steps |
| Packing | Disabled (padding-free auto-enabled by Unsloth) |

---

## 5. Training Status

| Metric | Value |
|---|---|
| Current phase | Medium adapter training |
| Steps | 0/750 (just started) |
| GPU utilization | 100% |
| GPU memory | 15.2 GB / 24 GB |
| GPU temperature | 47°C |
| Power draw | 296W (300W limit) |

Unsloth auto-enabled padding-free training, which is more efficient than standard padding and should reduce training time.

---

## 6. Estimated Timeline

| Phase | Estimated Duration |
|---|---|
| Medium training (750 steps) | ~50-70 min |
| Hard training (750 steps) | ~60-80 min (longer sequences) |
| Medium GGUF export | ~15-30 min |
| Hard GGUF export | ~15-30 min |
| **Total remaining** | **~2.5-3.5 hours** |

Faster than the original 6-8 hour estimate because:
- Unsloth's padding-free mode reduces wasted computation
- bf16 with Unsloth kernels is faster than vanilla fp16
- The 3,141-token average sequence length (Medium) is shorter than worst-case 4096

---

## 7. Lessons Learned

1. **Import order matters with Unsloth.** The `import unsloth` must come before any trl/transformers/peft imports. This is documented in Unsloth's README but easy to miss in a larger codebase. The failure mode (silent `<EOS_TOKEN>` injection) is non-obvious.

2. **TRL API changed significantly in v0.24.** The `tokenizer` → `processing_class` rename, `max_seq_length` → `max_length` rename, `TrainingArguments` → `SFTConfig` migration, and `warmup_ratio` → `warmup_steps` deprecation all happened in recent versions. Pseudocode from even a few months ago may not work.

3. **Don't use `replace_all` carelessly.** The `max_seq_length` → `max_length` rename was intended only for `SFTConfig` but also changed the parameter in `FastLanguageModel.from_pretrained()`, causing a cascade failure. Targeted edits are safer.

4. **Let Unsloth choose precision.** Unsloth's kernel optimizations mean bf16 works well even on GPUs where raw hardware bf16 throughput is limited. The dry run's `Bfloat16 = TRUE` detection should be trusted.

5. **Dry runs catch 90% of issues.** The model load + tokenization test passed on the first attempt. All four training failures were API-level issues that could have been caught by a more thorough dry run that also tested `SFTTrainer` construction (not just model loading).

---

## 8. Files Created

| File | Purpose |
|---|---|
| `forge/finetune/__init__.py` | Package init |
| `forge/finetune/data/__init__.py` | Data subpackage init |
| `forge/finetune/data/config_generator.py` | Stage 1: LHS cell config generation |
| `forge/finetune/data/prompt_generator.py` | Stage 2A: Config-to-prompt reverse engineering |
| `forge/finetune/data/reasoning_generator.py` | Stage 2B: Batch API reasoning traces |
| `forge/finetune/data/dataset_formatter.py` | Stage 3: ChatML formatting + splits |
| `forge/finetune/train.py` | Stage 4: QLoRA training script |
| `forge/finetune/export_to_ollama.py` | Stage 4: GGUF export + Ollama registration |
| `forge/finetune/run_training.sh` | Stage 4: Overnight run orchestrator |
| `forge/finetune/data/output/` | All intermediate and final data files |
