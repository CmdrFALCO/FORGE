"""Tests for RunConfig validation and defaults."""

from pathlib import Path

import pytest

from forge.ml.autoresearch.config import RunConfig


def _build_minimal_config(tmp_path: Path, **overrides: object) -> RunConfig:
    values: dict[str, object] = {
        "surrogate_script": tmp_path / "surrogate.py",
        "dataset_path": tmp_path / "dataset",
        "results_path": tmp_path / "results.tsv",
        "repo_dir": tmp_path,
    }
    values.update(overrides)
    return RunConfig(**values)


def test_config_defaults(tmp_path: Path) -> None:
    config = _build_minimal_config(tmp_path)
    assert config.budget_seconds == 300
    assert config.min_delta == pytest.approx(1e-4)
    assert config.epsilon == pytest.approx(1e-4)
    assert config.seed == 42
    assert config.dry_run is False
    assert config.temp_guardrail is None
    assert config.max_error_temp_guardrail is None


@pytest.mark.parametrize("budget", [0, -1])
def test_config_rejects_non_positive_budget(tmp_path: Path, budget: int) -> None:
    with pytest.raises(ValueError, match="budget_seconds must be > 0"):
        _build_minimal_config(tmp_path, budget_seconds=budget)


def test_config_rejects_negative_min_delta(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="min_delta must be >= 0"):
        _build_minimal_config(tmp_path, min_delta=-0.1)


def test_config_rejects_negative_epsilon(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="epsilon must be >= 0"):
        _build_minimal_config(tmp_path, epsilon=-0.1)


def test_valid_config_all_fields(tmp_path: Path) -> None:
    config = _build_minimal_config(
        tmp_path,
        budget_seconds=123,
        min_delta=0.01,
        epsilon=0.02,
        temp_guardrail=1.0,
        max_error_temp_guardrail=2.0,
        seed=99,
        dry_run=True,
        python_executable="python3",
    )
    assert config.budget_seconds == 123
    assert config.min_delta == pytest.approx(0.01)
    assert config.epsilon == pytest.approx(0.02)
    assert config.temp_guardrail == pytest.approx(1.0)
    assert config.max_error_temp_guardrail == pytest.approx(2.0)
    assert config.seed == 99
    assert config.dry_run is True
    assert config.python_executable == "python3"

