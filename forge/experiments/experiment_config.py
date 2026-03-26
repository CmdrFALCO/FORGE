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
    "exp3a": ExperimentDefinition(
        experiment_id="exp3a",
        name="Baseline (Local)",
        description="Unsupervised LLM, single attempt, Qwen 2.5 Coder 32B via Ollama",
        backend_config=QWEN_25_32B,
        supervised=False,
        max_retries=1,
        output_filename="exp3a_baseline_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3a_gpu.csv",
    ),
    "exp3b": ExperimentDefinition(
        experiment_id="exp3b",
        name="Supervised (Local)",
        description="Full AXIOM pipeline with retries, Qwen 2.5 Coder 32B via Ollama",
        backend_config=QWEN_25_32B,
        supervised=True,
        max_retries=4,
        output_filename="exp3b_supervised_local.jsonl",
        gpu_monitor=True,
        gpu_log_filename="exp3b_gpu.csv",
    ),
}
