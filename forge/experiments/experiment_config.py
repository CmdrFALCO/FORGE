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
}
