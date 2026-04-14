"""
Backend configurations and experiment definitions for AXIOM evaluation.

Each experiment specifies which LLM backend to use, whether AXIOM supervision
is enabled, and what MAX_RETRIES value to apply to the supervisor driver.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackendConfig:
    """Configuration for instantiating an LLM backend."""

    backend_type: str          # "claude" or "ollama"
    model: str                 # model identifier
    temperature: float = 0.0   # deterministic for reproducibility
    max_tokens: int = 4096     # Claude-specific
    num_ctx: int = 8192        # Ollama-specific
    num_predict: int = 2000    # Ollama-specific: hard cap on output tokens
    host: str = "http://localhost:11434"  # Ollama-specific
    append_yaml_suffix: bool = True  # Append YAML-only suffix for Ollama models


@dataclass(frozen=True)
class ExperimentDefinition:
    """Complete definition of one experiment run."""

    experiment_id: str
    name: str
    description: str
    backend_config: BackendConfig
    supervised: bool
    max_retries: int           # maps to supervisor_driver.MAX_RETRIES
    output_filename: str
    gpu_monitor: bool = False  # auto-start GPU logging
    gpu_log_filename: str | None = None


# ---------------------------------------------------------------------------
# Backend configurations
# ---------------------------------------------------------------------------

CLAUDE_SONNET_4 = BackendConfig(
    backend_type="claude",
    model="claude-sonnet-4-20250514",
    temperature=0.0,
    max_tokens=4096,
)

CLAUDE_HAIKU = BackendConfig(
    backend_type="claude",
    model="claude-haiku-4-5-20251001",
    temperature=0.0,
    max_tokens=4096,
)

QWEN_25_32B = BackendConfig(
    backend_type="ollama",
    model="qwen2.5-coder:32b",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

QWEN_35_27B = BackendConfig(
    backend_type="ollama",
    model="qwen3.5:27b",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

QWEN_35_9B = BackendConfig(
    backend_type="ollama",
    model="qwen3.5:9b",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

MISTRAL_SMALL_31 = BackendConfig(
    backend_type="ollama",
    model="mistral-small3.1",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

LLAMA_31_8B = BackendConfig(
    backend_type="ollama",
    model="llama3.1:8b",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

LLAMA_32_3B = BackendConfig(
    backend_type="ollama",
    model="llama3.2:3b",
    temperature=0.0,
    num_ctx=8192,
    host="http://localhost:11434",
)

# ── Fine-Tuning Evaluation Models ──

QWEN_25_7B_BASE = BackendConfig(
    backend_type="ollama",
    model="qwen2.5:7b",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,
)

QWEN_25_7B_MEDIUM = BackendConfig(
    backend_type="ollama",
    model="qwen25-7b-forge-medium",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,  # Trained WITH suffix
)

QWEN_25_7B_HARD = BackendConfig(
    backend_type="ollama",
    model="qwen25-7b-forge-hard",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=False,  # Trained WITHOUT suffix (reasoning before YAML)
)

GEMMA4_E4B_FORGE_MEDIUM = BackendConfig(
    backend_type="ollama",
    model="gemma4-e4b-forge-medium",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,  # Trained WITH suffix (Medium recipe)
)

# ── Gemma 4 Evaluation Models ──

GEMMA4_E2B = BackendConfig(
    backend_type="ollama",
    model="gemma4:e2b",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,
)

GEMMA4_E4B = BackendConfig(
    backend_type="ollama",
    model="gemma4:e4b",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,
)

GEMMA4_26B = BackendConfig(
    backend_type="ollama",
    model="gemma4:26b",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,
)

GEMMA4_31B = BackendConfig(
    backend_type="ollama",
    model="gemma4:31b",
    temperature=0.0,
    num_ctx=4096,
    num_predict=2000,
    host="http://localhost:11434",
    append_yaml_suffix=True,
)

# ---------------------------------------------------------------------------
# Experiment definitions
# ---------------------------------------------------------------------------

EXPERIMENTS: dict[str, ExperimentDefinition] = {
    "exp1": ExperimentDefinition(
        experiment_id="exp1",
        name="Baseline (Cloud)",
        description="Unsupervised LLM, single attempt, Claude Sonnet 4",
        backend_config=CLAUDE_SONNET_4,
        supervised=False,
        max_retries=1,  # 1 = single attempt, no retry
        output_filename="exp1_baseline_cloud.jsonl",
    ),
    "exp2": ExperimentDefinition(
        experiment_id="exp2",
        name="Supervised (Cloud)",
        description="Full AXIOM pipeline with retries, Claude Sonnet 4",
        backend_config=CLAUDE_SONNET_4,
        supervised=True,
        max_retries=4,  # 1 initial + 3 retries = 4 total
        output_filename="exp2_supervised_cloud.jsonl",
    ),
    "exp1h": ExperimentDefinition(
        experiment_id="exp1h",
        name="Baseline (Cloud, Haiku)",
        description="Unsupervised LLM, single attempt, Claude Haiku 4.5",
        backend_config=CLAUDE_HAIKU,
        supervised=False,
        max_retries=1,
        output_filename="exp1h_baseline_haiku.jsonl",
    ),
    "exp2h": ExperimentDefinition(
        experiment_id="exp2h",
        name="Supervised (Cloud, Haiku)",
        description="Full AXIOM pipeline with retries, Claude Haiku 4.5",
        backend_config=CLAUDE_HAIKU,
        supervised=True,
        max_retries=4,
        output_filename="exp2h_supervised_haiku.jsonl",
    ),
    # Prismatic fix re-runs (same prompts, fixed system prompt + schema feedback)
    "exp1_pfix": ExperimentDefinition(
        experiment_id="exp1_pfix",
        name="Baseline Prismatic Fix (Sonnet)",
        description="Unsupervised Sonnet 4, prismatic prompts only, with current_collection fix",
        backend_config=CLAUDE_SONNET_4,
        supervised=False,
        max_retries=1,
        output_filename="exp1_prismatic_fix.jsonl",
    ),
    "exp2_pfix": ExperimentDefinition(
        experiment_id="exp2_pfix",
        name="Supervised Prismatic Fix (Sonnet)",
        description="Full AXIOM pipeline, prismatic prompts only, with current_collection fix",
        backend_config=CLAUDE_SONNET_4,
        supervised=True,
        max_retries=4,
        output_filename="exp2_prismatic_fix.jsonl",
    ),
    "exp1h_pfix": ExperimentDefinition(
        experiment_id="exp1h_pfix",
        name="Baseline Prismatic Fix (Haiku)",
        description="Unsupervised Haiku 4.5, prismatic prompts only, with current_collection fix",
        backend_config=CLAUDE_HAIKU,
        supervised=False,
        max_retries=1,
        output_filename="exp1h_prismatic_fix.jsonl",
    ),
    "exp2h_pfix": ExperimentDefinition(
        experiment_id="exp2h_pfix",
        name="Supervised Prismatic Fix (Haiku)",
        description="Full AXIOM pipeline, prismatic prompts only, with current_collection fix",
        backend_config=CLAUDE_HAIKU,
        supervised=True,
        max_retries=4,
        output_filename="exp2h_prismatic_fix.jsonl",
    ),
    "exp3a": ExperimentDefinition(
        experiment_id="exp3a",
        name="Baseline (Local, Qwen 3.5 27B)",
        description="Unsupervised LLM, single attempt, Qwen 3.5 27B via Ollama",
        backend_config=QWEN_35_27B,
        supervised=False,
        max_retries=1,
        output_filename="exp3a_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3a_gpu.csv",
    ),
    "exp3b": ExperimentDefinition(
        experiment_id="exp3b",
        name="Supervised (Local, Qwen 3.5 27B)",
        description="Full AXIOM pipeline with retries, Qwen 3.5 27B via Ollama",
        backend_config=QWEN_35_27B,
        supervised=True,
        max_retries=4,
        output_filename="exp3b_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3b_gpu.csv",
    ),
    "exp3a_small": ExperimentDefinition(
        experiment_id="exp3a_small",
        name="Baseline (Local, Qwen 3.5 9B)",
        description="Unsupervised LLM, single attempt, Qwen 3.5 9B via Ollama",
        backend_config=QWEN_35_9B,
        supervised=False,
        max_retries=1,
        output_filename="exp3a_small_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3a_small_gpu.csv",
    ),
    "exp3b_small": ExperimentDefinition(
        experiment_id="exp3b_small",
        name="Supervised (Local, Qwen 3.5 9B)",
        description="Full AXIOM pipeline with retries, Qwen 3.5 9B via Ollama",
        backend_config=QWEN_35_9B,
        supervised=True,
        max_retries=4,
        output_filename="exp3b_small_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3b_small_gpu.csv",
    ),
    # ── Mistral Small 3.1 ──
    "exp_mistral_unsup": ExperimentDefinition(
        experiment_id="exp_mistral_unsup",
        name="Baseline (Local, Mistral Small 3.1)",
        description="Unsupervised LLM, single attempt, Mistral Small 3.1 via Ollama",
        backend_config=MISTRAL_SMALL_31,
        supervised=False,
        max_retries=1,
        output_filename="exp_mistral_unsup_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_mistral_unsup_gpu.csv",
    ),
    "exp_mistral_sup": ExperimentDefinition(
        experiment_id="exp_mistral_sup",
        name="Supervised (Local, Mistral Small 3.1)",
        description="Full AXIOM pipeline with retries, Mistral Small 3.1 via Ollama",
        backend_config=MISTRAL_SMALL_31,
        supervised=True,
        max_retries=4,
        output_filename="exp_mistral_sup_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_mistral_sup_gpu.csv",
    ),
    # ── Llama 3.1 8B ──
    "exp_llama8b_unsup": ExperimentDefinition(
        experiment_id="exp_llama8b_unsup",
        name="Baseline (Local, Llama 3.1 8B)",
        description="Unsupervised LLM, single attempt, Llama 3.1 8B via Ollama",
        backend_config=LLAMA_31_8B,
        supervised=False,
        max_retries=1,
        output_filename="exp_llama8b_unsup_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_llama8b_unsup_gpu.csv",
    ),
    "exp_llama8b_sup": ExperimentDefinition(
        experiment_id="exp_llama8b_sup",
        name="Supervised (Local, Llama 3.1 8B)",
        description="Full AXIOM pipeline with retries, Llama 3.1 8B via Ollama",
        backend_config=LLAMA_31_8B,
        supervised=True,
        max_retries=4,
        output_filename="exp_llama8b_sup_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_llama8b_sup_gpu.csv",
    ),
    # ── Llama 3.2 3B ──
    "exp_llama3b_unsup": ExperimentDefinition(
        experiment_id="exp_llama3b_unsup",
        name="Baseline (Local, Llama 3.2 3B)",
        description="Unsupervised LLM, single attempt, Llama 3.2 3B via Ollama",
        backend_config=LLAMA_32_3B,
        supervised=False,
        max_retries=1,
        output_filename="exp_llama3b_unsup_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_llama3b_unsup_gpu.csv",
    ),
    "exp_llama3b_sup": ExperimentDefinition(
        experiment_id="exp_llama3b_sup",
        name="Supervised (Local, Llama 3.2 3B)",
        description="Full AXIOM pipeline with retries, Llama 3.2 3B via Ollama",
        backend_config=LLAMA_32_3B,
        supervised=True,
        max_retries=4,
        output_filename="exp_llama3b_sup_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp_llama3b_sup_gpu.csv",
    ),
    # ── Fine-Tuning Evaluation: Qwen 2.5 7B base + Medium + Hard ──
    "ft_base_unsup": ExperimentDefinition(
        experiment_id="ft_base_unsup",
        name="Baseline (Qwen 2.5 7B, unsupervised)",
        description="Qwen 2.5 7B base model, single attempt, no fine-tuning",
        backend_config=QWEN_25_7B_BASE,
        supervised=False,
        max_retries=1,
        output_filename="ft_base_unsup.jsonl",
    ),
    "ft_base_sup": ExperimentDefinition(
        experiment_id="ft_base_sup",
        name="Baseline (Qwen 2.5 7B, supervised)",
        description="Qwen 2.5 7B base model, full AXIOM pipeline with retries",
        backend_config=QWEN_25_7B_BASE,
        supervised=True,
        max_retries=4,
        output_filename="ft_base_sup.jsonl",
    ),
    "ft_medium_unsup": ExperimentDefinition(
        experiment_id="ft_medium_unsup",
        name="Medium Fine-Tuned (unsupervised)",
        description="QLoRA Medium adapter on Qwen 2.5 7B, single attempt",
        backend_config=QWEN_25_7B_MEDIUM,
        supervised=False,
        max_retries=1,
        output_filename="ft_medium_unsup.jsonl",
    ),
    "ft_medium_sup": ExperimentDefinition(
        experiment_id="ft_medium_sup",
        name="Medium Fine-Tuned (supervised)",
        description="QLoRA Medium adapter on Qwen 2.5 7B, full AXIOM pipeline",
        backend_config=QWEN_25_7B_MEDIUM,
        supervised=True,
        max_retries=4,
        output_filename="ft_medium_sup.jsonl",
    ),
    "ft_hard_unsup": ExperimentDefinition(
        experiment_id="ft_hard_unsup",
        name="Hard Fine-Tuned (unsupervised)",
        description="QLoRA Hard adapter (reasoning+YAML) on Qwen 2.5 7B, single attempt",
        backend_config=QWEN_25_7B_HARD,
        supervised=False,
        max_retries=1,
        output_filename="ft_hard_unsup.jsonl",
    ),
    "ft_hard_sup": ExperimentDefinition(
        experiment_id="ft_hard_sup",
        name="Hard Fine-Tuned (supervised)",
        description="QLoRA Hard adapter (reasoning+YAML) on Qwen 2.5 7B, full AXIOM pipeline",
        backend_config=QWEN_25_7B_HARD,
        supervised=True,
        max_retries=4,
        output_filename="ft_hard_sup.jsonl",
    ),
    # ── Gemma 4 Evaluation: E2B / E4B / 26B / 31B on Corpus A ──
    "gemma4_e2b_unsup_a": ExperimentDefinition(
        experiment_id="gemma4_e2b_unsup_a",
        name="Gemma 4 E2B (unsupervised, Corpus A)",
        description="Gemma 4 E2B via Ollama, single attempt, Corpus A",
        backend_config=GEMMA4_E2B,
        supervised=False,
        max_retries=1,
        output_filename="gemma4_e2b_unsup_a.jsonl",
    ),
    "gemma4_e2b_sup_a": ExperimentDefinition(
        experiment_id="gemma4_e2b_sup_a",
        name="Gemma 4 E2B (supervised, Corpus A)",
        description="Gemma 4 E2B via Ollama, full AXIOM pipeline with retries, Corpus A",
        backend_config=GEMMA4_E2B,
        supervised=True,
        max_retries=4,
        output_filename="gemma4_e2b_sup_a.jsonl",
    ),
    "gemma4_e4b_unsup_a": ExperimentDefinition(
        experiment_id="gemma4_e4b_unsup_a",
        name="Gemma 4 E4B (unsupervised, Corpus A)",
        description="Gemma 4 E4B via Ollama, single attempt, Corpus A",
        backend_config=GEMMA4_E4B,
        supervised=False,
        max_retries=1,
        output_filename="gemma4_e4b_unsup_a.jsonl",
    ),
    "gemma4_e4b_sup_a": ExperimentDefinition(
        experiment_id="gemma4_e4b_sup_a",
        name="Gemma 4 E4B (supervised, Corpus A)",
        description="Gemma 4 E4B via Ollama, full AXIOM pipeline with retries, Corpus A",
        backend_config=GEMMA4_E4B,
        supervised=True,
        max_retries=4,
        output_filename="gemma4_e4b_sup_a.jsonl",
    ),
    "gemma4_26b_unsup_a": ExperimentDefinition(
        experiment_id="gemma4_26b_unsup_a",
        name="Gemma 4 26B (unsupervised, Corpus A)",
        description="Gemma 4 26B via Ollama, single attempt, Corpus A",
        backend_config=GEMMA4_26B,
        supervised=False,
        max_retries=1,
        output_filename="gemma4_26b_unsup_a.jsonl",
    ),
    "gemma4_26b_sup_a": ExperimentDefinition(
        experiment_id="gemma4_26b_sup_a",
        name="Gemma 4 26B (supervised, Corpus A)",
        description="Gemma 4 26B via Ollama, full AXIOM pipeline with retries, Corpus A",
        backend_config=GEMMA4_26B,
        supervised=True,
        max_retries=4,
        output_filename="gemma4_26b_sup_a.jsonl",
    ),
    "gemma4_31b_unsup_a": ExperimentDefinition(
        experiment_id="gemma4_31b_unsup_a",
        name="Gemma 4 31B (unsupervised, Corpus A)",
        description="Gemma 4 31B via Ollama, single attempt, Corpus A",
        backend_config=GEMMA4_31B,
        supervised=False,
        max_retries=1,
        output_filename="gemma4_31b_unsup_a.jsonl",
    ),
    "gemma4_31b_sup_a": ExperimentDefinition(
        experiment_id="gemma4_31b_sup_a",
        name="Gemma 4 31B (supervised, Corpus A)",
        description="Gemma 4 31B via Ollama, full AXIOM pipeline with retries, Corpus A",
        backend_config=GEMMA4_31B,
        supervised=True,
        max_retries=4,
        output_filename="gemma4_31b_sup_a.jsonl",
    ),
    # ── Gemma 4 E4B Fine-Tuned (Medium) — defensive 500-prompt eval ──
    "gemma4_e4b_ft_medium_unsup_a": ExperimentDefinition(
        experiment_id="gemma4_e4b_ft_medium_unsup_a",
        name="Gemma 4 E4B Medium FT (unsupervised, Corpus A)",
        description="QLoRA Medium adapter on Gemma 4 E4B, single attempt, Corpus A",
        backend_config=GEMMA4_E4B_FORGE_MEDIUM,
        supervised=False,
        max_retries=1,
        output_filename="gemma4_e4b_ft_medium_unsup_a.jsonl",
    ),
}
