"""Metric parsing, scoring, and acceptance utilities."""

import re

from .config import RunConfig
from .constants import (
    MAX_ERROR_TEMP,
    REQUIRED_KEYS,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
)

_METRIC_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")


def parse_output(stdout: str) -> dict[str, float]:
    """Parse metrics from the last marker block in surrogate stdout.

    The parser looks for the last line equal to `---`, then parses `key: value`
    pairs after that marker. Unknown keys are accepted and included in the
    returned dictionary. Required keys are validated.
    """
    lines = stdout.splitlines()
    marker_indices = [idx for idx, line in enumerate(lines) if line.strip() == "---"]
    if not marker_indices:
        raise ValueError("No metrics marker '---' found in output")

    start = marker_indices[-1] + 1
    parsed: dict[str, float] = {}
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            continue
        match = _METRIC_LINE_RE.match(stripped)
        if match is None:
            continue
        key, raw_value = match.groups()
        try:
            parsed[key] = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"Could not parse float for key '{key}': {raw_value}") from exc

    missing = sorted(REQUIRED_KEYS - set(parsed.keys()))
    if missing:
        raise ValueError(f"Missing required keys: {', '.join(missing)}")

    return parsed


def normalize_rmse(rmse: float, target_std: float) -> float:
    """Normalize RMSE by target standard deviation."""
    if target_std <= 0:
        raise ValueError("target_std must be > 0")
    return rmse / target_std


def compute_score(metrics: dict[str, float]) -> float:
    """Compute composite score from normalized per-target RMSE values."""
    return metrics[RMSE_RATE_NORM] + metrics[RMSE_TEMP_NORM]


def check_guardrails(metrics: dict[str, float], config: RunConfig) -> tuple[bool, str]:
    """Check configured guardrails against parsed metrics."""
    if config.temp_guardrail is not None and metrics[RMSE_TEMP] > config.temp_guardrail:
        return False, f"rmse_temp guardrail exceeded ({metrics[RMSE_TEMP]:.6f} > {config.temp_guardrail:.6f})"

    if (
        config.max_error_temp_guardrail is not None
        and metrics[MAX_ERROR_TEMP] > config.max_error_temp_guardrail
    ):
        return (
            False,
            "max_error_temp guardrail exceeded "
            f"({metrics[MAX_ERROR_TEMP]:.6f} > {config.max_error_temp_guardrail:.6f})",
        )

    return True, ""


def should_accept(
    candidate_score: float,
    best_score: float,
    candidate_time: float,
    best_time: float,
    min_delta: float,
    epsilon: float,
) -> tuple[bool, str]:
    """Apply the acceptance rule with tie-break on runtime."""
    delta = candidate_score - best_score
    if delta < -min_delta:
        return True, f"improved by {abs(delta):.6f}"
    if abs(delta) <= epsilon:
        if candidate_time < best_time:
            return True, "tie-break: faster"
        return False, "slower tie"
    return False, "no improvement"

