"""Tests for TSV result persistence."""

from pathlib import Path

import pytest

from forge.ml.autoresearch.constants import PRIMARY_SCORE, REQUIRED_KEYS
from forge.ml.autoresearch.results import ResultsLog, RunResult


def _make_result(experiment_id: int, primary_score: float, accepted: bool) -> RunResult:
    metrics = {key: 1.0 + index for index, key in enumerate(sorted(REQUIRED_KEYS))}
    return RunResult(
        experiment_id=experiment_id,
        metrics=metrics,
        primary_score=primary_score,
        accepted=accepted,
        reason="reason",
        timestamp="2026-03-08T00:00:00+00:00",
        git_hash="abc123",
    )


def test_results_log_write_read_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "results.tsv"
    log = ResultsLog(path)
    expected = _make_result(experiment_id=1, primary_score=0.5, accepted=True)

    log.append(expected)
    loaded = log.load()

    assert len(loaded) == 1
    actual = loaded[0]
    assert actual.experiment_id == expected.experiment_id
    assert actual.primary_score == pytest.approx(expected.primary_score)
    assert actual.accepted is True
    assert actual.reason == expected.reason
    assert actual.timestamp == expected.timestamp
    assert actual.git_hash == expected.git_hash
    for key, value in expected.metrics.items():
        assert actual.metrics[key] == pytest.approx(value)


def test_results_log_creates_header(tmp_path: Path) -> None:
    path = tmp_path / "results.tsv"
    log = ResultsLog(path)
    log.append(_make_result(1, 0.5, True))

    raw = path.read_text(encoding="utf-8")
    header = raw.splitlines()[0].split("\t")
    assert "experiment_id" in header
    assert PRIMARY_SCORE in header


def test_results_log_append_multiple(tmp_path: Path) -> None:
    path = tmp_path / "results.tsv"
    log = ResultsLog(path)
    log.append(_make_result(1, 0.5, True))
    log.append(_make_result(2, 0.4, False))
    log.append(_make_result(3, 0.3, True))
    assert len(log.load()) == 3


def test_results_log_get_best(tmp_path: Path) -> None:
    path = tmp_path / "results.tsv"
    log = ResultsLog(path)
    log.append(_make_result(1, 0.5, True))
    log.append(_make_result(2, 0.3, True))
    log.append(_make_result(3, 0.7, True))
    best = log.get_best()
    assert best is not None
    assert best.primary_score == pytest.approx(0.3)


def test_results_log_get_best_empty(tmp_path: Path) -> None:
    log = ResultsLog(tmp_path / "results.tsv")
    assert log.get_best() is None


def test_results_log_get_leaderboard(tmp_path: Path) -> None:
    log = ResultsLog(tmp_path / "results.tsv")
    for idx, score in enumerate([0.9, 0.5, 0.1, 0.7, 0.3], start=1):
        log.append(_make_result(idx, score, True))
    leaderboard = log.get_leaderboard(top_n=3)
    assert [row.primary_score for row in leaderboard] == pytest.approx([0.1, 0.3, 0.5])


def test_results_log_only_accepted_in_best(tmp_path: Path) -> None:
    log = ResultsLog(tmp_path / "results.tsv")
    log.append(_make_result(1, 0.3, False))
    log.append(_make_result(2, 0.5, True))
    best = log.get_best()
    assert best is not None
    assert best.primary_score == pytest.approx(0.5)

