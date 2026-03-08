"""Tests for autoresearch constants."""

from forge.ml.autoresearch.constants import (
    MAX_ERROR_RATE,
    MAX_ERROR_TEMP,
    NUM_EPOCHS,
    NUM_PARAMS,
    PRIMARY_SCORE,
    REQUIRED_KEYS,
    RMSE_RATE,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
    TOTAL_SECONDS,
    TRAINING_SECONDS,
)


def test_required_keys_are_non_empty_strings() -> None:
    for key in REQUIRED_KEYS:
        assert isinstance(key, str)
        assert key


def test_expected_metric_keys_in_required() -> None:
    assert RMSE_RATE in REQUIRED_KEYS
    assert RMSE_TEMP in REQUIRED_KEYS
    assert RMSE_RATE_NORM in REQUIRED_KEYS
    assert RMSE_TEMP_NORM in REQUIRED_KEYS
    assert MAX_ERROR_RATE in REQUIRED_KEYS
    assert MAX_ERROR_TEMP in REQUIRED_KEYS
    assert TRAINING_SECONDS in REQUIRED_KEYS
    assert TOTAL_SECONDS in REQUIRED_KEYS
    assert NUM_PARAMS in REQUIRED_KEYS
    assert NUM_EPOCHS in REQUIRED_KEYS


def test_primary_score_not_required() -> None:
    assert PRIMARY_SCORE not in REQUIRED_KEYS


def test_required_keys_is_frozenset() -> None:
    assert isinstance(REQUIRED_KEYS, frozenset)

