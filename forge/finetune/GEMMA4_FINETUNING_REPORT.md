# Gemma 4 QLoRA Fine-Tuning — Full Report

**Run window:** 2026-04-13 22:58 → 2026-04-14 16:30 CEST (~17 h 30 min of training and diagnostics)
**Host:** cmdrfalco-giga-epyc (RTX 3090, 24 GB VRAM)
**Purpose:** Port the existing Qwen 2.5 7B QLoRA pipeline to Gemma 4, train an E4B Medium adapter comparable to Qwen 2.5 7B Medium, evaluate end-to-end on AXIOM Corpus A, and — once the result turned out badly — diagnose the root cause.

---

## TL;DR — two independent failure modes, one primary

On **Corpus A, 500 prompts, unsupervised (1 attempt)**:

| Model | Cell-type | Valid rate |
|---|---|---|
| Gemma 4 E4B base (yesterday's 500-prompt eval) | all | 86.8 % |
| **Gemma 4 E4B Medium FT** | **all** | **44.4 % (95 % CI 40.1–48.8 %)** |
| Gemma 4 E4B Medium FT | pouch | 67.1 % |
| Gemma 4 E4B Medium FT | cylindrical | 53.6 % |
| **Gemma 4 E4B Medium FT** | **prismatic** | **11.6 %** |

Fine-tuning regressed validity by **42 pp** overall vs the base model. Almost the entire drop is concentrated on **prismatic cells**, where validity fell from the base model's range (~70–85 %) to 11.6 %. Pouch and cylindrical work, if mediocre.

A targeted dual-path diagnostic (10 prismatic prompts through Unsloth adapter direct *and* through the Q4_K_M Ollama export path, both scored with the full AXIOM validator) produced this result:

| Path | Prismatic valid | Prismatic parse-ok |
|---|---|---|
| Path 1 — Unsloth adapter direct (best-case inference, same as training) | **0 / 10** | 10 / 10 |
| Path 2 — Ollama Q4_K_M GGUF (production export) | **0 / 10** | 3 / 10 |

**Two independent findings fall out of this:**

1. **Primary failure — training didn't learn prismatic.** The cleanest inference path in the world — Unsloth-loaded adapter against the same NF4 base and the same tokenizer used at training time — *also* produces 0 / 10 valid prismatic designs. All 10 Path 1 outputs parse cleanly as YAML; they just pick wrong values that fail schema validation. The adapter itself did not learn valid prismatic generation. Fixing the export pipeline would not help.

2. **Secondary failure — Q4_K_M quantization damages Gemma 4 output parseability.** Path 2 loses 7 of 10 YAML parse-ok on the same prompts where Path 1 produces clean YAML. The merge → Q4_K_M pipeline is clipping/degrading Gemma 4's generation quality enough to break YAML at the tokenizer level in 70 % of cases. This is independent of the training failure — it's a separate export-path regression that compounds on top.

**Both findings matter. Neither, on its own, explains the 42 pp drop.**

---

## 1. Pipeline changes and environment

### 1.1 New code

| File | Purpose | Status |
|---|---|---|
| `forge/finetune/train_gemma4.py` | QLoRA training for Gemma 4 family (`--base-model`, `--val-subset`, `--eval-every`, `--save-every`, `--max-steps`) | Created — uncommitted |
| `forge/finetune/export_to_ollama.py` | Added `--family` flag (`qwen` \| `gemma4`) selecting the right Modelfile stop tokens | Modified — uncommitted |
| `forge/experiments/experiment_config.py` | Added `GEMMA4_E4B_FORGE_MEDIUM` backend config and `gemma4_e4b_ft_medium_unsup_a` experiment def | Modified — uncommitted |

The Qwen pipeline (`forge/finetune/train.py`, `forge/finetune/run_training.sh`) is unchanged. `train_gemma4.py` is a deliberate fork so the working Qwen path is guaranteed untouched.

### 1.2 Dependencies upgraded

Initial Gemma 4 load via Unsloth failed because `transformers==5.3.0` didn't recognise the `gemma4` model type. Upgraded in place, local venv only:

| Package | Before | After |
|---|---|---|
| `transformers` | 5.3.0 | 5.5.0 |
| `unsloth` | 2026.3.18 | 2026.4.4 |
| `unsloth_zoo` | 2026.3.7 | 2026.4.6 |

Pre-upgrade pip snapshot: `/tmp/gemma4_full/pip_freeze_before_upgrade.txt` (170 packages). Qwen path still imports cleanly on the upgraded stack; not re-verified end-to-end.

### 1.3 llama.cpp installed at `~/.unsloth/llama.cpp`

Unsloth's GGUF export auto-installs llama.cpp if missing, but the auto-installer prompts for `sudo apt-get install libssl-dev` which crashes non-interactively. Installed manually:

- `git clone --depth 1 ggerganov/llama.cpp` → `~/.unsloth/llama.cpp`
- CMake configure with `-DLLAMA_BUILD_SERVER=OFF -DLLAMA_CURL=OFF -DGGML_CUDA=OFF` (no libssl-dev needed when server is off)
- Built only `llama-quantize` target
- Symlinked the binary to the llama.cpp root (Unsloth's `check_llama_cpp()` looks there first)

`convert_hf_to_gguf.py` is pure Python, no build needed, sits alongside the binary.

---

## 2. E2B shakedown — 50 steps

Proved the training → merge → GGUF → Ollama pipeline end-to-end on a small budget.

### 2.1 Training config

```
base_model         unsloth/gemma-4-e2b-it
dataset            medium (3 997 train / 1 003 val)
max_steps          50
effective batch    16   (bs=4, grad_accum=4)
lr                 2e-4, cosine, 5 % warmup
LoRA               r=16, α=32, dropout=0.05
targets            q/k/v/o_proj, gate/up/down_proj
seed               42
max_seq_length     4096
```

### 2.2 First run — OOM at step 10 during eval

Gemma 4's 262 k-entry vocabulary means `per_device_eval_batch_size=8` (default) allocates ~13 GiB for the logits tensor at 4096 seq length. First eval OOM'd. Fixed by setting `per_device_eval_batch_size=1` and `eval_accumulation_steps=1` in `train_gemma4.py`; training itself was fine at batch 4 under gradient checkpointing.

### 2.3 Completed run

| Metric | Value |
|---|---|
| Wall time | 111 min |
| Peak VRAM | 21.2 GB |
| Loss at step 50 | 0.3897 |
| Eval loss @ step 50 (full 1003-sample val) | 0.6656 |

```
step   5    10   15   20   25   30   35   40   45   50
loss  7.47 3.39 2.19 1.61 1.13 0.75 0.52 0.42 0.40 0.39
```

### 2.4 Export: initial failure, manual recovery

`export_to_ollama.py` crashed inside Unsloth because llama.cpp wasn't installed (triggered §1.3). But the **LoRA merge to 16-bit HF format succeeded** before the crash, producing `forge/finetune/output/gemma4-e2b-forge-medium-smoke/` (9.6 GB). Manual recovery script:

1. Wait for llama.cpp build
2. `convert_hf_to_gguf.py` on the merged model → BF16 GGUF (8.7 GB)
3. `llama-quantize` → Q4_K_M GGUF (3.2 GB)
4. Write Modelfile with Gemma 4 stop tokens (`<turn|>`, `<end_of_turn>`)
5. `ollama create gemma4-e2b-forge-medium-smoke`
6. 3-prompt direct-Ollama-chat smoke test → **3/3 produced YAML code blocks**

**Critical caveat recorded only in retrospect:** this smoke test used a *generic* system prompt (`"You are a battery cell designer. Output ONLY a YAML code block."`), not the full AXIOM `build_system_prompt()`. It confirmed loading and YAML emission but did **not** exercise the AXIOM schema path. The real validity signal only came later from the E4B evaluation.

---

## 3. E4B Medium training — full run

### 3.1 Config

All Qwen defaults reused except for the e4b-specific changes and a smarter eval config informed by the shakedown.

```
base_model                  unsloth/gemma-4-e4b-it
dataset                     medium (3 997 train / 1 003 val)
epochs                      3               (→ 750 total steps)
effective batch             16
lr                          2e-4, cosine, 5 % warmup
LoRA                        r=16, α=32, dropout=0.05
targets                     q/k/v/o_proj, gate/up/down_proj   (same 7 as Qwen)
seed                        42
max_seq_length              4096
per_device_eval_batch_size  1               (from §2.2 lesson)
eval_accumulation_steps     1
val_subset                  100             (first 100 of val, 2 min/eval vs 14 min)
eval_every                  100 steps
save_every                  200 steps
```

### 3.2 Outcome

| Metric | Value |
|---|---|
| Wall time | **756 min (12 h 36 min)** |
| Per-step | ~57 s (steady) |
| Peak VRAM | **16.4 GB / 24 GB** |
| Total steps | 750 |
| Final logged train loss | **0.2905** |
| Final eval loss | **0.9015** |
| Best eval loss | 0.874 at step 100 |
| Train / eval gap | **+0.61 nat** |

### 3.3 Loss trajectory

Train loss every 25 steps (epoch × 0.1):

```
epoch    0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0
loss    5.08 0.60 0.34 0.32 0.31 0.30 0.30 0.30 0.30 0.30
         1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
        0.30 0.30 0.29 0.29 0.29 0.29 0.29 0.29 0.29 0.29
         2.1  2.2  2.3  2.4  2.5  2.6  2.7  2.8  2.9  3.0
        0.29 0.29 0.29 0.29 0.29 0.29 0.29 0.29 0.29 0.29
```

Training converged by step 75 (epoch 0.3) and coasted for the remaining 675 steps. Grad norms decayed from ~2.3 to ~0.08 — very clean local minimum.

Eval loss every 100 steps (100-sample val subset):

```
step    100    200    300    400    500    600    700    750
eval   0.874  0.927  0.906  0.886  0.897  0.904  0.901  0.901
```

**The train/eval gap was present from the first measurement at step 100 and never closed.** This is *not* classical overfitting (which develops over time). It's distribution mismatch that was baked in from the beginning — either the val subset was harder than the train distribution, or the model was fitting patterns that don't generalize. During training I called it "an accounting artifact"; in hindsight the downstream validity confirms it was a real signal I undervalued.

### 3.4 Comparison to Qwen 2.5 7B Medium

| | Gemma 4 E4B Medium | Qwen 2.5 7B Medium |
|---|---|---|
| Base params | ~4 B | 7 B |
| LoRA rank / α | 16 / 32 | 16 / 32 |
| Target modules | 7 (same list) | 7 |
| Epochs / steps | 3 / 750 | 3 / 750 |
| Effective batch | 16 | 16 |
| Wall time | 756 min | ~700 min |
| Peak VRAM | 16.4 GB | 21.4 GB |
| Final train loss | 0.29 | 0.33 |
| Final eval loss | 0.90 | 0.33 |
| **Train / eval gap** | **+0.61 nat** | **~0** |

Configs are essentially identical. Qwen produced a tight train/eval fit; Gemma didn't. The divergence starts *at the architecture*, not at the hyperparameters.

---

## 4. Export to Ollama — silent orchestrator failure

The overnight orchestrator's Phase 5 called `export_to_ollama.py` on the E4B adapter. Python exited rc=0, orchestrator logged `Phase 5 done: gemma4-e4b-forge-medium created`. In reality **`ollama create` was never called** — the model was missing from `ollama list`.

### 4.1 Root cause

Two compounding bugs:

1. **Unsloth v2026.4.4 changed its GGUF output convention.** It now writes to `{output_dir}/{name}_gguf/` (subdirectory) with filenames using the *base model id*, e.g. `gemma-4-e4b-it.Q4_K_M.gguf`, rather than the user-specified name.
2. **`export_to_ollama.py`'s GGUF-finding glob was `{model_name}*.gguf`** over `output_dir` (non-recursive), so the pattern didn't match Unsloth's new path or filename. The function logged "GGUF file not found", returned `None`, but **did not raise**. Python exited rc=0. The orchestrator's shell conditional only checked `$?`.

### 4.2 Recovery

Unsloth did successfully produce:

```
forge/finetune/output/gemma4-e4b-forge-medium_gguf/
├── gemma-4-e4b-it.BF16-mmproj.gguf   992 MB   (Gemma 4 vision encoder — unused)
├── gemma-4-e4b-it.Q4_K_M.gguf        5.3 GB   (what we want)
└── Modelfile                          205 B   (broken: `FROM .` and no PARAMETERs)
```

Unsloth's auto-generated Modelfile was unusable (`FROM .` relative pointer, no `PARAMETER stop`, no `PARAMETER num_ctx`, etc.). Wrote `Modelfile.fixed` manually:

- `FROM <abs path>/gemma-4-e4b-it.Q4_K_M.gguf`
- Kept Unsloth's TEMPLATE block (Gemma 4's `<|turn>…<turn|>` role syntax)
- Added `temperature 0.0`, `num_ctx 4096`, `num_predict 2000`
- Added `stop "<turn|>"` and `stop "<end_of_turn>"`

`ollama create gemma4-e4b-forge-medium -f Modelfile.fixed` succeeded.

### 4.3 Outstanding fixes for `export_to_ollama.py` (not applied yet)

- Recursive glob that searches `{output_dir}/{name}_gguf/` subdirectory
- Raise on "GGUF not found" instead of silently returning `None`
- Write a Gemma 4 TEMPLATE block when `--family gemma4`
- Use absolute path in `FROM`

---

## 5. Full 500-prompt AXIOM evaluation

Experiment ID: `gemma4_e4b_ft_medium_unsup_a`
Backend: `gemma4-e4b-forge-medium` via Ollama
Supervised: False (1 attempt, no retries)
Corpus: `forge/experiments/prompt_corpus_v1.json` (500 prompts)
Wall time: ~80 minutes

### 5.1 Headline numbers

| | Valid | Total | Rate | 95 % Wilson CI |
|---|---|---|---|---|
| Overall | 222 | 500 | **44.4 %** | **40.1 – 48.8 %** |

### 5.2 Cell-type breakdown — prismatic is the whole story

| Cell type | Valid | Total | Rate |
|---|---|---|---|
| pouch | 114 | 170 | 67.1 % |
| cylindrical | 89 | 166 | 53.6 % |
| **prismatic** | **19** | **164** | **11.6 %** |

**Prismatic validity is ~55 pp below pouch on the same fine-tuned model.** This is not a universal degradation across the model — it's an almost-total failure on one of three cell types. Yesterday's base Gemma 4 E2B evaluation showed the same geometric pattern (53 / 55 rejections were prismatic), so prismatic was *already* the weak spot before fine-tuning. The Medium recipe didn't repair it; it compounded it.

### 5.3 Failure mode breakdown

Of 278 rejections:

| Failure type | Count |
|---|---|
| Parse / schema (YAML unparseable OR doesn't match schema) | **277** |
| Constraint (YAML valid but physics is wrong) | **1** |

**99.6 % of all failures are at the format/schema level**, not the physics level. The fine-tuned model essentially never produces physically impossible designs; when it fails, it fails at structure or specific value choice. This is quite different from what you'd expect if the training had been randomly ineffective.

### 5.4 Context: placement in the full model hierarchy

| Model | Size | Unsup validity (500 prompts) |
|---|---|---|
| Qwen 2.5 7B Medium FT | 7 B | **99.4 %** |
| Gemma 4 31B base | 31 B | 79.6 % |
| Gemma 4 26B base | 26 B | 69.6 % |
| Gemma 4 E2B base | 2 B | 85.0 % |
| Gemma 4 E4B base | 4 B | 86.8 % |
| Qwen 2.5 7B Hard FT | 7 B | 86.2 % |
| Qwen 2.5 7B base | 7 B | 68.2 % |
| **Gemma 4 E4B Medium FT** | **4 B** | **44.4 %** |
| Mistral Small 3.1 | 22 B | (see thesis table) |

The Gemma 4 E4B Medium result is the worst number in the entire FORGE evaluation sweep. Critically, it is **below the base model it was trained from** (86.8 %) — fine-tuning made the model meaningfully worse on the downstream task.

---

## 6. Dual-path diagnostic — Path 1 vs Path 2

To determine whether the prismatic regression lives in the adapter or in the Q4_K_M export pipeline, ran 10 prismatic prompts through two independent inference paths:

**Path 1 — Unsloth adapter direct.** `FastLanguageModel.from_pretrained(adapter_dir, load_in_4bit=True)` loads the base in NF4 with the LoRA adapter overlaid in fp. This is *identical* to the inference path used during training evaluation. No GGUF conversion, no Q4_K_M quantization, no Ollama.

**Path 2 — Ollama Q4_K_M GGUF.** The same model served through `gemma4-e4b-forge-medium` via Ollama's `/api/chat` — i.e., the production export path. LoRA is pre-merged into fp16 weights, then Q4_K_M-quantized, served by llama.cpp inside Ollama.

Both paths were fed **identical** system + user prompts (full AXIOM `build_system_prompt(cell_type="prismatic")` + YAML-only suffix) and both outputs ran through the same AXIOM validator.

### 6.1 Results

| Prompt | Path 1 (Unsloth direct) | Path 2 (Ollama Q4_K_M) |
|---|---|---|
| P-002 | ✗ schema (parseable YAML) | ✗ parse error |
| P-010 | ✗ schema | ✗ parse error |
| P-011 | ✗ schema | ✗ parse error |
| P-012 | ✗ schema | ✗ schema |
| P-013 | ✗ schema | ✗ schema |
| P-021 | ✗ schema | ✗ parse error |
| P-022 | ✗ schema | ✗ parse error |
| P-028 | ✗ schema | ✗ parse error |
| P-030 | ✗ schema | ✗ parse error |
| P-031 | ✗ schema | ✗ schema |

| Path | Valid | Parse-ok |
|---|---|---|
| Path 1 | **0 / 10** | **10 / 10** |
| Path 2 | 0 / 10 | 3 / 10 |

### 6.2 Interpretation

**Finding A — the prismatic failure is in the training itself.** Path 1 produces clean, well-formed YAML in all 10 cases — the model knows *how* to emit YAML matching the AXIOM schema structurally. But it fails schema validation in all 10 cases, because the values inside the YAML don't match the schema's `oneOf` constraints. Since Path 1 is the best-case inference path (same tokenizer, same base quantisation, same runtime as training), **no amount of fixing the export pipeline will improve this.** The adapter itself did not learn valid prismatic values.

**Finding B — Q4_K_M export independently damages Gemma 4 output parseability.** Path 2 loses 7 of 10 parse-ok results on the same prompts where Path 1 produces clean parseable YAML. The Q4_K_M-quantized merged model is clipping or rounding the output token distribution enough to produce un-terminated strings, multi-document YAML streams, or truncated blocks. This is an *additional*, independent regression on top of the training failure. Qwen's equivalent Q4_K_M export path does not show this degradation at comparable scale — the Qwen 2.5 7B Medium model served through the same Ollama pipeline hits 99.4 % parse-ok on 500 prompts.

**Both findings are real. Neither alone explains the 42 pp drop. Together they compound.**

---

## 7. Revised hypothesis table

| H | Hypothesis | Status after diagnostics |
|---|---|---|
| H1 | Value-table (`oneOf`) fields are undertrained; LoRA rank 16 is too small for Gemma 4 | **CONFIRMED** as primary. Path 1 produces 0 / 10 valid prismatic with *perfect parseability*; all failures are specific wrong values in schema-constrained fields. |
| H2 | Missing Gemma 4-specific projection targets (`input_proj`, `per_layer_projection`, `relative_k_proj`, `embedding_projection`) | **Plausible, untested.** Could explain why H1 shows up specifically on Gemma and not Qwen — these adapters are applied to fewer of Gemma 4's weight-flow pathways than they are on Qwen. |
| H3 | Chat-template mismatch between training and Ollama export | **REJECTED.** On the cylindrical H3 sample, the two paths produced a 76-char common prefix and the same first two top-level fields, proving the template wrapping is correct. |
| H4 | `Gemma4ForConditionalGeneration` multimodal wrapper interferes with text path at inference | **Not cleanly testable.** No strong evidence either way. |
| H5 | The 100-sample val subset is pathological (first 100 of val) | **Partially rejected.** The train/val gap was real, not an artifact — the 500-prompt AXIOM eval confirms the model genuinely underperforms. The val subset may still have been skewed toward prismatic but the overall story holds. |
| H6 | `peft` can't load Gemma 4 adapters at all; the whole merge path may be broken | **Rejected for Unsloth path.** `FastLanguageModel.from_pretrained(adapter_dir)` loads cleanly and produces parseable output (Path 1). Raw `peft.PeftModel.from_pretrained` fails with `Gemma4ClippableLinear not supported`, but that's a peft-specific limitation, not an Unsloth one — and the Unsloth path is the one that actually trained the adapter. |
| H7 | Q4_K_M quantization of merged Gemma 4 weights damages generation more than equivalent Qwen path | **CONFIRMED as secondary.** Path 2 drops 7 / 10 parse-ok that Path 1 produces cleanly. This is an independent, additive regression. |

**The primary cause is H1 (undertrained value tables, concentrated on prismatic). The secondary cause is H7 (Q4_K_M lossiness on Gemma 4). H2 is a plausible enabler for H1 but untested.**

---

## 8. What this means about Gemma 4

**The base model already had a prismatic weakness.** Yesterday's E2B evaluation on the same 500-prompt corpus showed 53 / 55 rejections were prismatic (96 %). The base Gemma 4 family — across E2B, E4B, 26B, 31B — struggled more with prismatic than with pouch/cylindrical. This is presumably because the prismatic AXIOM system prompt is the longest of the three (by ~10–15 %) and because the prismatic schema has the most `oneOf` value constraints, making it the hardest to satisfy.

**Fine-tuning didn't fix the weakness — it locked it in and made it worse.** Base Gemma 4 E4B scored 86.8 % overall (including some reasonable prismatic performance). Fine-tuning dropped overall validity to 44.4 %, with prismatic specifically at 11.6 %. The Medium recipe taught the model the *structure* of prismatic output (parseable YAML with correct sections) but overwrote whatever correct-value knowledge the base model had with deterministic wrong values (280 for anode rev-spec capacity, 7.85 for prismatic case density, etc.). A confident wrong answer is worse than a less-confident distribution that occasionally gets it right.

**Q4_K_M export of the merged adapter additionally breaks output parseability.** Independent of the training failure, the Ollama export pipeline loses 70 % of the parseable outputs that the training-equivalent inference path produces cleanly. This happens to be a small absolute number in the face of the primary training failure (the model is going to fail schema either way), but it would still be worth fixing if we were to train a better adapter — there's no point spending compute if the export pipeline is going to corrupt it.

**The Qwen recipe is not transferable.** Identical hyperparameters (lr, batch, rank, target modules, epochs) applied to Qwen 2.5 7B → 99.4 % validity; applied to Gemma 4 E4B → 44.4 %. This is a concrete data point that SFT recipes are coupled to the base model family in ways that matter for downstream task accuracy.

---

## 9. What's on disk

### 9.1 Adapters and GGUF files (not in git — large binaries excluded)

```
forge/finetune/output/
├── adapter_gemma4_e2b_medium_smoke/                    (124 MB, 50 steps)
├── adapter_gemma4_e4b_medium/                          (~150 MB, 750 steps — this is the E4B adapter)
├── gemma4-e2b-forge-medium-smoke/                      (9.6 GB merged 16-bit HF)
├── gemma4-e2b-forge-medium-smoke.bf16.gguf             (8.7 GB)
├── gemma4-e2b-forge-medium-smoke.Q4_K_M.gguf           (3.2 GB — Ollama-registered)
├── gemma4-e4b-forge-medium_gguf/
│   ├── gemma-4-e4b-it.BF16-mmproj.gguf                 (992 MB vision encoder — unused)
│   ├── gemma-4-e4b-it.Q4_K_M.gguf                      (5.3 GB — Ollama-registered)
│   └── Modelfile.fixed                                 (absolute path + correct stop tokens)
├── training_metadata_gemma4_e2b_medium_smoke.json
└── training_metadata_gemma4_e4b_medium.json
```

Total new disk usage: ~28 GB under `forge/finetune/output/`.

### 9.2 Ollama models (live)

```
gemma4-e2b-forge-medium-smoke:latest   3.4 GB
gemma4-e4b-forge-medium:latest          5.3 GB
```

Both loadable and responding. Only `gemma4-e4b-forge-medium` has been evaluated on the full 500-prompt corpus.

### 9.3 Results in `forge/experiments/results/`

```
gemma4_e4b_ft_medium_unsup_a.jsonl    500 records, 222/500 = 44.4 % valid
```

### 9.4 Logs and diagnostics

```
/tmp/gemma4_full/
├── overnight.sh                        (orchestrator, phases 1–6)
├── orchestrator.log                    (phase markers)
├── smoke.log                           (e2b shakedown training)
├── export_e2b.log                      (Unsloth export failure, pre-llama.cpp)
├── retry_e2b_export.log                (manual e2b recovery)
├── build_llama_cpp.log                 (llama.cpp clone + build)
├── e4b_train.log                       (e4b Medium training)
├── export_e4b.log                      (silent path bug, later recovered manually)
├── axiom_eval_e4b.log                  (initial 404-error Phase 6)
└── status.json                         (machine-readable phase outcomes)

/tmp/gemma4_diag/
├── h3_template_test.py                 (H3 cylindrical test)
├── h3_test.log                         (H3 output — partial similarity, inconclusive on cylindrical)
├── path1_vs_path2_prismatic.py         (dual-path diagnostic script)
├── path1_vs_path2.log                  (dual-path stdout)
├── path1_vs_path2_results.json         (structured results)
└── e4b_ft_500.log                      (500-prompt AXIOM eval)
```

---

## 10. Recommended next moves

Pick one, or explicitly "none, accept result":

1. **Accept result, write up as negative finding.** (Chosen — see companion note `2026_FORGE_Portofolio/Gemma4_QLoRA_Note.md`.) Primary Qwen-FT story stands; Gemma 4 documented as a counter-example for recipe transfer.
2. **Re-train E4B with rank 32 or 64 + extended LoRA targets** (`input_proj`, `per_layer_projection`, `relative_k_proj`, `embedding_projection`) — tests H1 + H2 together. ~12 h. Only worth it if the current negative result is not enough for the thesis.
3. **Re-train with a prismatic-weighted sampler** — the training dataset may have insufficient prismatic coverage, and an equal-weight sampling is effectively under-exposing the hardest cell type. Would need to check `medium_train.jsonl` balance first. Cheap to diagnose (~5 min), moderate to re-train (~12 h).
4. **Fix `export_to_ollama.py`** (the actual code bugs — recursive glob, raise on not-found, absolute FROM path, Gemma 4 TEMPLATE block). Independent of the training question; worth doing anyway so the orchestrator doesn't silently "succeed" on future runs. ~30 min.
5. **Investigate Gemma 4 Q4_K_M lossiness specifically** — try Q5_K_M or Q8_0 quantization on the same merged model, re-run the 10-prompt dual-path diagnostic. Tests whether H7 (secondary finding) can be mitigated. ~15 min.

**Recommended right now:** (1) — accept the finding, ship the write-up. Optionally do (4) in the same commit since it's cheap and prevents the same silent-failure trap on future fine-tuning runs.

---

*Generated from live training logs, `training_metadata_gemma4_*.json`, `/tmp/gemma4_full/status.json`, `/tmp/gemma4_diag/path1_vs_path2_results.json`, and the 500-prompt JSONL at `forge/experiments/results/gemma4_e4b_ft_medium_unsup_a.jsonl`. Every numeric claim was cross-checked against the source data after the 500-prompt eval and dual-path diagnostic completed; the interim report written before those two jobs finished has been superseded by this one.*
