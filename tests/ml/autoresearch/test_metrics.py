"""Tests for metric parsing, scoring, guardrails, and acceptance logic."""

from pathlib import Path

import pytest

from forge.ml.autoresearch.config import RunConfig
from forge.ml.autoresearch.constants import (
    MAX_ERROR_RATE,
    MAX_ERROR_TEMP,
    NUM_EPOCHS,
    NUM_PARAMS,
    PRIMARY_SCORE,
    RMSE_RATE,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
    TOTAL_SECONDS,
    TRAINING_SECONDS,
)
from forge.ml.autoresearch.metrics import (
    check_guardrails,
    compute_score,
    normalize_rmse,
    parse_output,
    should_accept,
)


def _build_valid_output(**overrides: float) -> str:
    values: dict[str, float] = {
        RMSE_RATE: 0.4,
        RMSE_TEMP: 0.3,
        RMSE_RATE_NORM: 0.25,
        RMSE_TEMP_NORM: 0.15,
        MAX_ERROR_RATE: 1.2,
        MAX_ERROR_TEMP: 2.5,
        TRAINING_SECONDS: 10.0,
        TOTAL_SECONDS: 12.0,
        NUM_PARAMS: 1000.0,
        NUM_EPOCHS: 50.0,
    }
    values.update(overrides)
    lines = ["---"] + [f"{key}: {value}" for key, value in values.items()]
    return "\n".join(lines)


def _build_config(tmp_path: Path, **overrides: float | None) -> RunConfig:
    values: dict[str, object] = {
        "surrogate_script": tmp_path / "surrogate.py",
        "dataset_path": tmp_path / "dataset",
        "results_path": tmp_path / "results.tsv",
        "repo_dir": tmp_path,
    }
    values.update(overrides)
    return RunConfig(**values)


def test_parse_output_valid() -> None:
    parsed = parse_output(_build_valid_output())
    assert parsed[RMSE_RATE] == pytest.approx(0.4)
    assert parsed[RMSE_TEMP] == pytest.approx(0.3)


def test_parse_output_missing_key() -> None:
    output = _build_valid_output()
    output = output.replace(f"{RMSE_RATE}: 0.4", "")
    with pytest.raises(ValueError, match=RMSE_RATE):
        parse_output(output)


def test_parse_output_no_marker() -> None:
    with pytest.raises(ValueError, match="No metrics marker"):
        parse_output("rmse_rate: 0.1")


def test_parse_output_last_marker() -> None:
    output = (
        "---\n"
        "random: 1\n"
        "---\n"
        f"{RMSE_RATE}: 0.4\n"
        f"{RMSE_TEMP}: 0.3\n"
        f"{RMSE_RATE_NORM}: 0.25\n"
        f"{RMSE_TEMP_NORM}: 0.15\n"
        f"{MAX_ERROR_RATE}: 1.2\n"
        f"{MAX_ERROR_TEMP}: 2.5\n"
        f"{TRAINING_SECONDS}: 10.0\n"
        f"{TOTAL_SECONDS}: 12.0\n"
        f"{NUM_PARAMS}: 1000\n"
        f"{NUM_EPOCHS}: 50\n"
    )
    parsed = parse_output(output)
    assert parsed[RMSE_RATE] == pytest.approx(0.4)


def test_parse_output_scientific_notation() -> None:
    output = _build_valid_output(
        **{
            RMSE_RATE: 1.23e-4,
            RMSE_TEMP: 5.67e2,
        }
    )
    parsed = parse_output(output)
    assert parsed[RMSE_RATE] == pytest.approx(1.23e-4)
    assert parsed[RMSE_TEMP] == pytest.approx(5.67e2)


def test_parse_output_ignores_unknown_keys() -> None:
    output = _build_valid_output() + "\ncustom_metric: 99.0"
    parsed = parse_output(output)
    assert parsed["custom_metric"] == pytest.approx(99.0)


def test_parse_output_primary_score_ignored() -> None:
    output = _build_valid_output() + f"\n{PRIMARY_SCORE}: 999.0"
    parsed = parse_output(output)
    assert parsed[PRIMARY_SCORE] == pytest.approx(999.0)
    assert compute_score(parsed) != pytest.approx(parsed[PRIMARY_SCORE])


def test_normalize_rmse() -> None:
    assert normalize_rmse(0.5, 2.0) == pytest.approx(0.25)


def test_normalize_rmse_zero_std() -> None:
    with pytest.raises(ValueError, match="target_std must be > 0"):
        normalize_rmse(0.5, 0.0)


def test_normalize_rmse_negative_std() -> None:
    with pytest.raises(ValueError, match="target_std must be > 0"):
        normalize_rmse(0.5, -1.0)


def test_compute_score() -> None:
    parsed = parse_output(_build_valid_output())
    assert compute_score(parsed) == pytest.approx(0.40)


def test_check_guardrails_pass(tmp_path: Path) -> None:
    parsed = parse_output(_build_valid_output())
    config = _build_config(tmp_path)
    assert check_guardrails(parsed, config) == (True, "")


def test_check_guardrails_temp_fail(tmp_path: Path) -> None:
    parsed = parse_output(_build_valid_output(**{RMSE_TEMP: 6.0}))
    config = _build_config(tmp_path, temp_guardrail=5.0)
    ok, reason = check_guardrails(parsed, config)
    assert ok is False
    assert "rmse_temp guardrail exceeded" in reason


def test_check_guardrails_max_error_fail(tmp_path: Path) -> None:
    parsed = parse_output(_build_valid_output(**{MAX_ERROR_TEMP: 12.0}))
    config = _build_config(tmp_path, max_error_temp_guardrail=10.0)
    ok, reason = check_guardrails(parsed, config)
    assert ok is False
    assert "max_error_temp guardrail exceeded" in reason


def test_should_accept_clear_improvement() -> None:
    accepted, _ = should_accept(0.5, 0.7, 10.0, 11.0, min_delta=1e-4, epsilon=1e-4)
    assert accepted is True


def test_should_accept_no_improvement() -> None:
    accepted, reason = should_accept(0.7, 0.5, 10.0, 11.0, min_delta=1e-4, epsilon=1e-4)
    assert accepted is False
    assert reason == "no improvement"


def test_should_accept_tie_break_faster() -> None:
    accepted, reason = should_accept(
        0.500001,
        0.5,
        candidate_time=9.0,
        best_time=10.0,
        min_delta=1e-4,
        epsilon=1e-4,
    )
    assert accepted is True
    assert reason == "tie-break: faster"


def test_should_accept_tie_break_slower() -> None:
    accepted, reason = should_accept(
        0.500001,
        0.5,
        candidate_time=10.5,
        best_time=10.0,
        min_delta=1e-4,
        epsilon=1e-4,
    )
    assert accepted is False
    assert reason == "slower tie"

