"""Offline unit tests for the OpenAI Responses API backend."""

from types import SimpleNamespace

import pytest

import forge.axiom as axiom
import forge.axiom.backends as backend_exports
import forge.axiom.backends.backends as backend_module
from forge.axiom.backends.backends import (
    ClaudeBackend,
    MockBackend,
    OllamaBackend,
    OpenAIBackend,
    get_backend,
)


def make_response(
    output_text="generated design",
    *,
    input_tokens=17,
    output_tokens=23,
    model="gpt-5.6-2026-07-19",
    include_usage=True,
):
    usage = (
        SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
        if include_usage
        else None
    )
    return SimpleNamespace(output_text=output_text, usage=usage, model=model)


@pytest.fixture
def fake_openai(monkeypatch):
    state = SimpleNamespace(
        response=make_response(),
        error=None,
        clients=[],
        requests=[],
    )

    class FakeResponses:
        def create(self, **kwargs):
            state.requests.append(kwargs)
            if state.error is not None:
                raise state.error
            return state.response

    class FakeOpenAIClient:
        def __init__(self, *, api_key, timeout, max_retries):
            state.clients.append(
                {
                    "api_key": api_key,
                    "timeout": timeout,
                    "max_retries": max_retries,
                }
            )
            self.responses = FakeResponses()

    monkeypatch.setattr(backend_module, "openai", SimpleNamespace(OpenAI=FakeOpenAIClient))
    monkeypatch.setattr(backend_module, "OPENAI_AVAILABLE", True)
    return state


def test_explicit_api_key_overrides_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    backend = OpenAIBackend(api_key="explicit-key")

    assert backend.api_key == "explicit-key"


def test_environment_api_key_is_used(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    backend = OpenAIBackend()

    assert backend.api_key == "environment-key"


def test_missing_api_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIBackend()


def test_missing_sdk_raises_import_error(monkeypatch):
    monkeypatch.setattr(backend_module, "OPENAI_AVAILABLE", False)

    backend = OpenAIBackend(api_key="test-key")

    with pytest.raises(ImportError, match=r"pip install forge\[llm\]"):
        backend.generate([{"role": "user", "content": "Design a cell"}])


def test_model_defaults_and_constructor_override():
    assert OpenAIBackend(api_key="test-key").model == "gpt-5.6"
    assert OpenAIBackend(api_key="test-key", model="custom-model").model == "custom-model"


def test_generate_maps_messages_request_response_and_usage(fake_openai):
    backend = OpenAIBackend(
        api_key="test-key",
        model="configured-model",
        max_output_tokens=2048,
        timeout=45.0,
        transport_max_retries=0,
    )
    messages = [
        {"role": "system", "content": "First instruction"},
        {"role": "user", "content": "Initial request"},
        {"role": "assistant", "content": "Earlier answer"},
        {"role": "system", "content": "Second instruction"},
        {"role": "user", "content": "Correction"},
    ]

    result = backend.generate(messages)

    assert result == "generated design"
    assert fake_openai.clients == [
        {"api_key": "test-key", "timeout": 45.0, "max_retries": 0}
    ]
    assert fake_openai.requests == [
        {
            "model": "configured-model",
            "input": [
                {"role": "user", "content": "Initial request"},
                {"role": "assistant", "content": "Earlier answer"},
                {"role": "user", "content": "Correction"},
            ],
            "max_output_tokens": 2048,
            "instructions": "First instruction\n\nSecond instruction",
        }
    ]
    assert backend.last_usage.tokens_in == 17
    assert backend.last_usage.tokens_out == 23
    assert backend.last_usage.model == "gpt-5.6-2026-07-19"
    assert backend.last_usage.raw_response is fake_openai.response


def test_generate_omits_instructions_without_system_message(fake_openai):
    backend = OpenAIBackend(api_key="test-key")

    backend.generate([{"role": "user", "content": "Design a cell"}])

    assert "instructions" not in fake_openai.requests[0]
    assert fake_openai.clients[0]["max_retries"] == 2


def test_absent_usage_uses_zeroes_and_missing_model_uses_configured_model(fake_openai):
    fake_openai.response = make_response(include_usage=False, model=None)
    backend = OpenAIBackend(api_key="test-key", model="configured-model")

    backend.generate([{"role": "user", "content": "Design a cell"}])

    assert backend.last_usage.tokens_in == 0
    assert backend.last_usage.tokens_out == 0
    assert backend.last_usage.model == "configured-model"
    assert backend.last_usage.raw_response is fake_openai.response


@pytest.mark.parametrize("output_text", [None, 42, "   \n"])
def test_invalid_output_text_raises_infrastructure_error(fake_openai, output_text):
    fake_openai.response = make_response(output_text=output_text)
    backend = OpenAIBackend(api_key="test-key")

    with pytest.raises(RuntimeError, match="OpenAI API"):
        backend.generate([{"role": "user", "content": "Design a cell"}])


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ({"content": "hello"}, "missing required 'role'"),
        ({"role": "user"}, "missing required 'content'"),
        ({"role": "tool", "content": "hello"}, "unsupported role"),
        ({"role": "user", "content": 123}, "content must be a string"),
        ("not-a-dictionary", "must be a dictionary"),
    ],
)
def test_malformed_messages_raise_local_validation_errors(fake_openai, message, error):
    backend = OpenAIBackend(api_key="test-key")

    with pytest.raises(ValueError, match=error):
        backend.generate([message])

    assert fake_openai.requests == []


def test_sdk_request_exception_is_wrapped(fake_openai):
    fake_openai.error = ConnectionError("sensitive transport detail")
    backend = OpenAIBackend(api_key="test-key")

    with pytest.raises(RuntimeError, match=r"^OpenAI API error: request failed$") as exc_info:
        backend.generate([{"role": "user", "content": "Design a cell"}])

    assert isinstance(exc_info.value.__cause__, ConnectionError)
    assert "sensitive transport detail" not in str(exc_info.value)


def test_core_factory_returns_openai_backend():
    backend = get_backend("openai", api_key="test-key", model="custom-model")

    assert isinstance(backend, OpenAIBackend)
    assert backend.model == "custom-model"


def test_package_exports_are_importable():
    assert backend_exports.OpenAIBackend is OpenAIBackend
    assert isinstance(backend_exports.OPENAI_AVAILABLE, bool)
    assert axiom.OpenAIBackend is OpenAIBackend
    assert isinstance(axiom.OPENAI_AVAILABLE, bool)


def test_existing_factory_branches_remain_unchanged():
    assert isinstance(get_backend("claude", api_key="test-key"), ClaudeBackend)
    assert isinstance(get_backend("ollama"), OllamaBackend)
    assert isinstance(get_backend("mock", responses=[]), MockBackend)

    with pytest.raises(ValueError, match="Unknown backend type: unknown"):
        get_backend("unknown")
