"""Autoresearch -- autonomous ML surrogate experimentation engine.

Run experiments in a loop: modify surrogate, train, evaluate, accept/reject, log.
Agent-agnostic: works with any training script that outputs the expected metric format.

Usage:
    python -m forge.ml.autoresearch --surrogate path/to/surrogate.py --dataset path/to/data/

See Also:
    experiments/ml/autoresearch/ for the concrete battery cell surrogate setup.
"""

from forge.ml.autoresearch.config import RunConfig
from forge.ml.autoresearch.metrics import (
    check_guardrails,
    compute_score,
    normalize_rmse,
    parse_output,
    should_accept,
)
from forge.ml.autoresearch.results import ResultsLog, RunResult
from forge.ml.autoresearch.runner import run_loop, run_once

__all__ = [
    "RunConfig",
    "RunResult",
    "ResultsLog",
    "run_once",
    "run_loop",
    "parse_output",
    "normalize_rmse",
    "compute_score",
    "check_guardrails",
    "should_accept",
]
