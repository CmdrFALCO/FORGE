"""Tests for API backend construction and dependency mapping."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import forge.api.deps as deps
from forge.axiom.backends.backends import OpenAIBackend


def test_build_backend_selects_openai_with_normalization_and_model_override(monkeypatch):
    monkeypatch.setattr(deps, "OPENAI_AVAILABLE", True)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    backend = deps.build_backend(" OpenAI ", model="custom-openai-model")

    assert isinstance(backend, OpenAIBackend)
    assert backend.api_key == "test-openai-key"
    assert backend.model == "custom-openai-model"


def test_build_backend_openai_uses_default_model(monkeypatch):
    monkeypatch.setattr(deps, "OPENAI_AVAILABLE", True)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    backend = deps.build_backend("openai")

    assert isinstance(backend, OpenAIBackend)
    assert backend.model == "gpt-5.6"


def test_build_backend_openai_missing_sdk_maps_to_503(monkeypatch):
    monkeypatch.setattr(deps, "OPENAI_AVAILABLE", False)

    with pytest.raises(HTTPException) as exc_info:
        deps.build_backend("openai")

    assert exc_info.value.status_code == 503
    assert "pip install forge[llm]" in str(exc_info.value.detail)


def test_build_backend_openai_missing_key_maps_to_503(monkeypatch):
    monkeypatch.setattr(deps, "OPENAI_AVAILABLE", True)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        deps.build_backend("openai")

    assert exc_info.value.status_code == 503
    assert "OPENAI_API_KEY" in str(exc_info.value.detail)


def test_build_backend_openai_initialization_error_is_sanitized(monkeypatch):
    monkeypatch.setattr(deps, "OPENAI_AVAILABLE", True)
    constructor = MagicMock(side_effect=RuntimeError("sensitive initialization detail"))
    monkeypatch.setattr(deps, "OpenAIBackend", constructor)

    with pytest.raises(HTTPException) as exc_info:
        deps.build_backend("openai", model="custom-openai-model")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Failed to initialize OpenAI backend."
    assert "sensitive initialization detail" not in str(exc_info.value.detail)
    constructor.assert_called_once_with(model="custom-openai-model")


@pytest.mark.parametrize(
    ("backend_name", "availability_flag", "constructor_name"),
    [
        ("ollama", "REQUESTS_AVAILABLE", "OllamaBackend"),
        ("claude", "ANTHROPIC_AVAILABLE", "ClaudeBackend"),
        ("anthropic", "ANTHROPIC_AVAILABLE", "ClaudeBackend"),
    ],
)
def test_existing_backend_factory_branches_remain_unchanged(
    monkeypatch,
    backend_name,
    availability_flag,
    constructor_name,
):
    sentinel_backend = object()
    constructor = MagicMock(return_value=sentinel_backend)
    monkeypatch.setattr(deps, availability_flag, True)
    monkeypatch.setattr(deps, constructor_name, constructor)

    backend = deps.build_backend(backend_name, model="existing-model")

    assert backend is sentinel_backend
    constructor.assert_called_once_with(model="existing-model")


def test_unsupported_backend_lists_openai():
    with pytest.raises(HTTPException) as exc_info:
        deps.build_backend("gpt")

    assert exc_info.value.status_code == 400
    assert "openai" in str(exc_info.value.detail)
