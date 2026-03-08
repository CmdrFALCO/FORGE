"""Tests for autoresearch runner orchestration."""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from forge.ml.autoresearch.config import RunConfig
from forge.ml.autoresearch.constants import (
    MAX_ERROR_RATE,
    MAX_ERROR_TEMP,
    NUM_EPOCHS,
    NUM_PARAMS,
    RMSE_RATE,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
    TOTAL_SECONDS,
    TRAINING_SECONDS,
)
from forge.ml.autoresearch.metrics import compute_score
from forge.ml.autoresearch.results import RunResult
from forge.ml.autoresearch.runner import run_loop, run_once


def _build_valid_stdout(**overrides: float) -> str:
    values: dict[str, float] = {
        RMSE_RATE: 0.4,
        RMSE_TEMP: 0.3,
        RMSE_RATE_NORM: 0.2,
        RMSE_TEMP_NORM: 0.3,
        MAX_ERROR_RATE: 1.0,
        MAX_ERROR_TEMP: 2.0,
        TRAINING_SECONDS: 10.0,
        TOTAL_SECONDS: 12.0,
        NUM_PARAMS: 1000.0,
        NUM_EPOCHS: 50.0,
    }
    values.update(overrides)
    lines = ["---"] + [f"{key}: {value}" for key, value in values.items()]
    return "\n".join(lines)


def _build_config(tmp_path: Path) -> RunConfig:
    return RunConfig(
        surrogate_script=tmp_path / "surrogate.py",
        dataset_path=tmp_path / "dataset",
        results_path=tmp_path / "results.tsv",
        repo_dir=tmp_path,
        budget_seconds=30,
    )


def _mock_completed(stdout: str, returncode: int = 0, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_baseline(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(_build_valid_stdout())
    config = _build_config(tmp_path)

    result = run_once(config=config, experiment_id=1, best_result=None)

    assert result.accepted is True
    assert result.reason == "baseline"
    assert result.primary_score == pytest.approx(compute_score(result.metrics))


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_improvement(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(
        _build_valid_stdout(**{RMSE_RATE_NORM: 0.2, RMSE_TEMP_NORM: 0.3})
    )
    config = _build_config(tmp_path)
    best = RunResult(
        experiment_id=0,
        metrics={TOTAL_SECONDS: 20.0},
        primary_score=0.8,
        accepted=True,
        reason="seed",
        timestamp="2026-03-08T00:00:00+00:00",
    )

    result = run_once(config=config, experiment_id=1, best_result=best)
    assert result.accepted is True


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_no_improvement(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(
        _build_valid_stdout(**{RMSE_RATE_NORM: 0.2, RMSE_TEMP_NORM: 0.3})
    )
    config = _build_config(tmp_path)
    best = RunResult(
        experiment_id=0,
        metrics={TOTAL_SECONDS: 20.0},
        primary_score=0.3,
        accepted=True,
        reason="seed",
        timestamp="2026-03-08T00:00:00+00:00",
    )

    result = run_once(config=config, experiment_id=1, best_result=best)
    assert result.accepted is False


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_timeout(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=1)
    config = _build_config(tmp_path)

    result = run_once(config=config, experiment_id=1)
    assert result.accepted is False
    assert "timeout" in result.reason


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_crash(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(
        _build_valid_stdout(),
        returncode=1,
        stderr="boom",
    )
    config = _build_config(tmp_path)

    result = run_once(config=config, experiment_id=1)
    assert result.accepted is False
    assert "crash" in result.reason


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_parse_error(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed("garbage")
    config = _build_config(tmp_path)

    result = run_once(config=config, experiment_id=1)
    assert result.accepted is False
    assert "parse_error" in result.reason


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_guardrail_rejection(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(_build_valid_stdout(**{RMSE_TEMP: 10.0}))
    config = RunConfig(
        surrogate_script=tmp_path / "surrogate.py",
        dataset_path=tmp_path / "dataset",
        results_path=tmp_path / "results.tsv",
        repo_dir=tmp_path,
        temp_guardrail=5.0,
    )
    result = run_once(config=config, experiment_id=1)
    assert result.accepted is False
    assert "guardrail" in result.reason


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_once_cwd(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(_build_valid_stdout())
    config = _build_config(tmp_path)

    run_once(config=config, experiment_id=1)

    assert mock_subprocess.run.call_count == 1
    assert mock_subprocess.run.call_args.kwargs["cwd"] == config.repo_dir


@patch("forge.ml.autoresearch.runner.subprocess")
def test_run_loop_basic(mock_subprocess: SimpleNamespace, tmp_path: Path) -> None:
    mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
    mock_subprocess.run.return_value = _mock_completed(_build_valid_stdout())
    config = _build_config(tmp_path)
    results = run_loop(config=config, iterations=3)
    assert len(results) == 3

