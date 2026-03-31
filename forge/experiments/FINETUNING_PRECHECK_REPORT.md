# Fine-Tuning Experiment Pre-Check Report

*Date: 2026-03-31*
*Scope: Read-only analysis of FORGE codebase reuse potential for QLoRA fine-tuning on Qwen 2.5 7B*

---

## Stage 1: Cell Configuration Generation

**Existing infrastructure — strong.**

| Component | Path | Reuse |
|---|---|---|
| Prismatic calculator | `forge/engine/calculators/prismatic_calculator.py` | As-is |
| Pouch calculator | `forge/engine/calculators/pouch_calculator.py` | As-is |
| Cylindrical calculator | `forge/engine/calculators/cylindrical_calculator.py` | As-is |
| Input dataclasses | `forge/engine/models/prismatic.py`, `pouch.py`, `cylindrical.py` | As-is |
| JSON Schemas (3) | `forge/data/templates/*_master.schema.json` | As-is — defines valid output format |
| Constraint validator (29 checks) | `forge/engine/validation/constraint_validator.py` | As-is |
| Validation pipeline | `forge/engine/validation/pipeline.py` | As-is |
| LHS batch sampler | `forge/ml/batch/lhs_generator.py` | Adapt — currently samples for PyBaMM features, needs to sample full cell configs |
| 27 reference cells | `data/reference/*.json` | As-is — seed configs + validation benchmarks |
| BOM/cost output | `forge/engine/models/results.py`, `forge/engine/cost/` | As-is — enriches training data |
| Conversion layer | `forge/engine/conversion/template_to_input.py` | As-is — maps YAML to typed input |

### Schema Ranges (Key Fields)

**Prismatic:** cell_height_mm [50–200], cell_width_mm [100–400], cell_thickness_mm [10–80], wall_top_mm [0.5–5.0], wall_sides_mm [0.5–1.5]

**Pouch:** cathode_height_mm [30–500], cathode_width_mm [30–400], anode_offset_mm [0.5–5.0], separator_offset_mm [0.5–5.0]

**Cylindrical:** diameter_mm [10–60], length_mm [30–100], can_wall_thickness_mm [0.15–0.6], can_bottom_thickness_mm [0.2–1.0]

### All 29 Constraints

**Common (C1–C7):** N/P ratio [1.05–1.25], cathode loading [5–30 mg/cm²], anode loading [5–20 mg/cm²], separator porosity [30–55%], electrolyte salt [0.8–1.5 M], cathode material valid, anode material valid.

**Prismatic (PR1–PR7):** Internal height/width/thickness positive, cathode fits cavity, stacks [1–4], electrode pairs positive, end electrode config valid.

**Pouch (PO1–PO7):** Anode/separator offset positive, separator covers anode, stacks [1–4], electrode pairs positive, end electrode config valid, packaging offsets.

**Cylindrical (CY1–CY8):** Mandrel diameter, winding clearance, tension factor, tab type valid, can material valid, jelly roll fits can, header height, format consistency.

### Gap

No existing script that does "sample random parameters → validate against schema + constraints → keep valid ones → output as YAML." The LHS sampler generates parameter vectors for PyBaMM simulation, not full cell YAML configs. Need a new glue script that:

1. Samples from schema-valid ranges (already defined in JSON schemas)
2. Runs each sample through `validate_cell_definition()`
3. Keeps only designs that pass all 29 constraints
4. Outputs as YAML (the format LLMs must produce)

The pieces exist. The glue script doesn't.

---

## Stage 2: Prompt Generation & Variation

**Existing infrastructure — strong.**

| Component | Path | Reuse |
|---|---|---|
| Corpus A (500 prompts) | `forge/experiments/prompt_corpus_v1.json` | As-is for evaluation |
| Corpus B (250 prompts) | `forge/experiments/corpus_b/prompt_corpus_b.json` | As-is for evaluation |
| Corpus A generator | `forge/experiments/generate_corpus.py` | Adapt — reuse templates for training prompt generation |
| Corpus B generator + seed bank | `forge/experiments/corpus_b/generate_corpus_b.py` | Adapt — roughness transforms for training data augmentation |
| Corpus config (profiles, templates) | `forge/experiments/corpus_config.py` | As-is — chemistry/application profiles |
| System prompt builder | `forge/axiom/generator/prompt_builder.py` | As-is — `build_system_prompt()` provides the system message for training pairs |
| Retry prompt builder | `forge/axiom/generator/prompt_builder.py` | As-is — `build_retry_prompt()` provides correction examples for Hard dataset |
| AXIOM Designer GUI | `forge/gui/pages/4_AXIOM_Designer.py` | Reference only |

### Prompt Generation Details

**Corpus A generator** (`generate_corpus.py`, 21 functions):
- Cross-product stratification: 3 cell types × 4 chemistries × 4 applications × 4 difficulties × 3 prompt styles
- Parameter generation per difficulty: standard (middle 60%), edge case (85–99th percentile), underspecified (2–4 fields omitted), contradictory (physical conflicts injected)
- Three prompt styles: terse, detailed, natural_language
- Trimmed from 576 to 500 prompts

**Corpus B generator** (`generate_corpus_b.py`, 17 functions):
- Seed bank approach: 45 hand-written seeds, 5 roughness families, 3 surface styles
- Controlled transformations: clause reorder, connector drop, typo injection (12% budget), broken fragment injection
- 240 core prompts + 10 sentinels = 250

**System prompt** (`build_system_prompt()`):
- Role definition + parameter schema + validation rules + design trade-offs + valid example cell
- Cell-type-specific: prismatic, pouch, cylindrical variants
- Few-shot examples: 100Ah LFP prismatic, 10Ah NMC811 pouch, standard cylindrical formats

### Gap

Need a pairing script that matches generated configs (Stage 1) with synthetic prompts to create (prompt, config) training pairs. For the Hard dataset, also need reasoning traces between prompt and config — the Claude Batch API step. No existing reasoning-trace generator.

---

## Stage 3: Dataset Formatting

**Existing infrastructure — partial.**

| Component | Path | Reuse |
|---|---|---|
| NPZ dataset builder | `forge/ml/dataset/npz_builder.py` | Pattern only — NPZ format not suitable for LLM fine-tuning |
| Train/val/test split logic | `forge/ml/dataset/npz_builder.py` (70/15/15) | Reuse split logic |
| JSON schemas | `forge/data/templates/*.schema.json` | Defines target output structure |
| YAML parser | `forge/axiom/generator/parser.py` | As-is — validates that output is extractable YAML |

### Existing Dataset Pipeline

The autoresearch ML pipeline uses NPZ format:
- `NpzDatasetBuilder` in `forge/ml/dataset/npz_builder.py`
- 11 input features → 2 regression targets
- 70/15/15 train/val/test split with configurable seed
- SHA-256 hash verification in metadata.json
- Used by `experiments/ml/autoresearch/prepare.py` with LHS sampling (2000 samples)

### Gap — Biggest Build

No ChatML, ShareGPT, or Alpaca formatters exist anywhere in the codebase. Need to build:

- Converter from (system_prompt, user_prompt, assistant_yaml) → ChatML conversation format
- For Hard dataset: (system_prompt, user_prompt, assistant_reasoning + yaml) → ChatML with reasoning trace
- Proper train/val split with stratification by cell type and chemistry
- Decontamination check against Corpus A and B evaluation prompts (critical — training data must not contain evaluation prompts)

---

## Stage 4: Training Infrastructure

**Existing infrastructure — minimal for LLM fine-tuning.**

| Component | Path | Reuse |
|---|---|---|
| PyTorch surrogate training | `experiments/ml/autoresearch/surrogate.py` | Pattern only — MLP, not LLM |
| Optuna hyperparameter search | `experiments/ml/autoresearch/optuna_search.py` | Could adapt for fine-tuning HP search |
| Autoresearch runner | `forge/ml/autoresearch/runner.py` | Pattern — subprocess orchestration |
| GPU monitor | `forge/experiments/gpu_monitor.py` | As-is |
| OllamaBackend | `forge/axiom/backends/backends.py` | As-is — serves fine-tuned model after training |

### Existing PyTorch Usage

Found in 7 files, all for MLP surrogate training:
- `experiments/ml/autoresearch/surrogate.py`: 2-layer MLP (64 hidden, ReLU), Adam optimizer, time-budgeted training, ensemble support
- `forge/ml/surrogate_inference.py`: Loads checkpoints, ensemble averaging, CPU inference
- `experiments/ml/autoresearch/optuna_search.py`: Optuna-based hyperparameter search

### Dependencies in `pyproject.toml`

**Installed:** torch>=2.0, scipy>=1.11, numpy>=1.24, optuna>=3.0, pybamm>=24.1

**NOT installed:** transformers, peft, bitsandbytes, accelerate, trl, unsloth. None appear in pyproject.toml or any import statement. The entire QLoRA fine-tuning stack needs to be added.

### Ollama Integration Path for Fine-Tuned Models

After training, the QLoRA adapter can be merged and converted to GGUF, then loaded into Ollama via a Modelfile. The existing `OllamaBackend` and `ExperimentDefinition` pattern handles the rest:

1. Merge adapter → base model
2. Convert to GGUF (llama.cpp quantize)
3. `ollama create qwen25-7b-medium -f Modelfile`
4. Add `BackendConfig(model="qwen25-7b-medium", ...)` to experiment config
5. Entire evaluation pipeline works unchanged

### GPU Setup

- GPU monitor exists (`forge/experiments/gpu_monitor.py`) — polls nvidia-smi every 5s, logs CSV
- No explicit CUDA device management or multi-GPU code
- PyTorch models train on single GPU; Ollama handles GPU internally
- RTX 3090 (24GB) sufficient for QLoRA on 7B model at 4-bit

---

## Stage 5: Evaluation Harness

**Existing infrastructure — very strong. Most reusable stage.**

| Component | Path | Reuse |
|---|---|---|
| Validation pipeline | `forge/engine/validation/pipeline.py` | As-is |
| CPN supervision loop | `forge/axiom/supervisor/driver.py` | As-is |
| Experiment runner | `forge/experiments/run_experiments.py` | As-is — JSONL output, resume, per-attempt metrics |
| Experiment config | `forge/experiments/experiment_config.py` | Add 4 new entries |
| Statistical tests | `forge/experiments/analysis/statistical_tests.py` | As-is — McNemar, Wilson CI |
| Visualization (10 figure types) | `forge/experiments/analysis/visualizations.py` | As-is |
| Report generator | `forge/experiments/analysis/analyze_all.py` | Adapt — add fine-tuned model columns |
| Corpus A + B | Both corpus JSON files | As-is — evaluation prompts |
| GPU monitor | `forge/experiments/gpu_monitor.py` | As-is |

### Per-Prompt Metrics Already Captured

**Summary level:** final_valid, total_attempts, total_tokens_in/out, total_wall_time_ms, recovered (bool)

**Per-attempt:** attempt_number, design_valid, constraints_total/passed/failed, constraint_results (list of ConstraintResult), feedback_sent, tokens_in/out, raw_llm_output

### Adding a Fine-Tuned Model to Evaluation

Requires only:

1. Merge QLoRA adapter → base model → GGUF → `ollama create`
2. Add `BackendConfig` in `experiment_config.py` with new model name
3. Add 4 `ExperimentDefinition` entries (Medium unsup, Medium sup, Hard unsup, Hard sup)
4. Run `python -m forge.experiments.run_experiments --experiment <id>`
5. Results flow into existing JSONL → analysis → report pipeline

### Analysis Infrastructure

- `forge/experiments/analysis/statistical_tests.py`: Wilson CI, McNemar (paired proportions), chi-square, Wilcoxon
- `forge/experiments/analysis/visualizations.py`: 10 publication-ready figure types (validity bars, cell type heatmaps, cost scatter, retry sankey, constraint co-occurrence)
- `forge/experiments/analysis/analyze_all.py`: Loads JSONL, converts to DataFrame, generates report + figures

---

## Summary Table

| Stage | Reuse % | Main Gaps | Est. Build (hours) |
|---|---|---|---|
| **1. Config Generation** | ~70% | Glue script: sample → validate → output YAML | 4–6 |
| **2. Prompt Generation** | ~80% | Pairing script + Claude Batch reasoning traces | 6–10 |
| **3. Dataset Formatting** | ~20% | ChatML converter, decontamination, stratified splits | 8–12 |
| **4. Training Infra** | ~10% | Entire QLoRA stack (unsloth/peft/transformers + training script) | 12–16 |
| **5. Evaluation Harness** | **~95%** | 4 new experiment config entries + model conversion | 2–3 |
| **Total** | | | **32–47 hours** |

---

## Key Architectural Insight

The evaluation harness is essentially free — the entire AXIOM pipeline, statistical testing, and reporting infrastructure works as-is for any model Ollama can serve. The biggest build is the training infrastructure (Stage 4), which starts from near-zero. Stages 1–2 are mostly assembly of existing pieces. Stage 3 is moderate — the format conversion is straightforward but needs care to avoid data leakage between training and evaluation corpora.

The critical path is: **Stage 1 (config gen) → Stage 2 (prompt pairing) → Stage 3 (formatting) → Stage 4 (training) → Stage 5 (eval)**. Stages 1–3 can be built and validated before any fine-tuning dependencies are installed.
