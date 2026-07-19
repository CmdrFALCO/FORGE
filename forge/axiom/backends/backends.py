"""
LLM backend implementations for cell design generation.

Supports cloud (Claude and OpenAI) and local (Ollama) inference.
The supervision mechanism is LLM-agnostic.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False


@dataclass
class LLMUsage:
    """Token usage and metadata from an LLM call.

    Populated after each generate() call. Access via backend.last_usage.
    """

    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    raw_response: Any = None  # Full API response for downstream extraction


class LLMBackend(Protocol):
    """Protocol for LLM backends."""

    last_usage: LLMUsage

    def generate(self, messages: list[dict[str, str]]) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Design a cell..."}]

        Returns:
            The LLM's response text
        """
        ...


@dataclass
class ClaudeBackend:
    """
    Anthropic Claude API backend.

    Uses claude-sonnet-4-20250514 for good balance of quality and cost.
    """

    api_key: str | None = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 1.0
    last_usage: LLMUsage = field(default_factory=LLMUsage)

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key is None:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Generate response using Claude API."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package required for ClaudeBackend. Install with: pip install forge[llm]"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        # Extract system message if present
        system_content = None
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                chat_messages.append(msg)

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_content or "",
            messages=chat_messages,
        )

        self.last_usage = LLMUsage(
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=response.model,
            raw_response=response,
        )

        return response.content[0].text


@dataclass
class OpenAIBackend:
    """OpenAI Responses API backend."""

    api_key: str | None = None
    model: str = "gpt-5.6"
    max_output_tokens: int = 4096
    timeout: float = 120.0
    transport_max_retries: int = 2
    last_usage: LLMUsage = field(default_factory=LLMUsage)

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key is None:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Generate a response using the synchronous OpenAI Responses API."""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package required for OpenAIBackend. Install with: pip install forge[llm]"
            )

        instructions = []
        input_messages = []
        allowed_roles = {"system", "user", "assistant"}

        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValueError(f"Message at index {index} must be a dictionary")
            if "role" not in message:
                raise ValueError(f"Message at index {index} is missing required 'role'")
            if "content" not in message:
                raise ValueError(f"Message at index {index} is missing required 'content'")

            role = message["role"]
            content = message["content"]
            if role not in allowed_roles:
                raise ValueError(
                    f"Message at index {index} has unsupported role {role!r}; "
                    "expected system, user, or assistant"
                )
            if not isinstance(content, str):
                raise ValueError(f"Message at index {index} content must be a string")

            if role == "system":
                instructions.append(content)
            else:
                input_messages.append({"role": role, "content": content})

        request = {
            "model": self.model,
            "input": input_messages,
            "max_output_tokens": self.max_output_tokens,
        }
        if instructions:
            request["instructions"] = "\n\n".join(instructions)

        try:
            client = openai.OpenAI(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.transport_max_retries,
            )
            response = client.responses.create(**request)
        except Exception as exc:
            raise RuntimeError("OpenAI API error: request failed") from exc

        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise RuntimeError("OpenAI API returned missing or empty output text")

        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "input_tokens", 0) if usage is not None else 0
        tokens_out = getattr(usage, "output_tokens", 0) if usage is not None else 0
        response_model = getattr(response, "model", None)

        self.last_usage = LLMUsage(
            tokens_in=tokens_in or 0,
            tokens_out=tokens_out or 0,
            model=response_model if isinstance(response_model, str) and response_model else self.model,
            raw_response=response,
        )

        return output_text


@dataclass
class OllamaBackend:
    """
    Local Ollama backend for sovereign AI operation.

    Default model: qwen2.5-coder:14b (good at structured output)
    """

    host: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:14b"
    temperature: float = 1.0
    num_ctx: int = 8192
    num_predict: int = 2000  # Hard cap on output tokens to prevent runaway generation
    think: bool = False  # Disable reasoning/thinking mode (e.g. Qwen 3.5)
    append_yaml_suffix: bool = True  # Append YAML-only suffix to system prompt
    last_usage: LLMUsage = field(default_factory=LLMUsage)

    def __post_init__(self):
        if self.host is None:
            self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Generate response using Ollama API."""
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests package required for OllamaBackend. Install with: pip install forge[llm]"
            )

        # Ollama uses different message format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "think": self.think,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }

        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=600,  # Local inference can be slow, especially large models
        )
        response.raise_for_status()

        data = response.json()

        # Ollama reports token counts in response metadata
        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)

        self.last_usage = LLMUsage(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=data.get("model", self.model),
            raw_response=data,
        )

        return data["message"]["content"]


class MockBackend:
    """
    Mock backend for testing.

    Returns predefined responses in sequence.
    """

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
        self.received_messages: list[list[dict]] = []
        self.last_usage = LLMUsage()

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.received_messages.append(messages)

        if self.call_count >= len(self.responses):
            raise RuntimeError(f"MockBackend exhausted after {self.call_count} calls")

        response = self.responses[self.call_count]
        self.call_count += 1
        self.last_usage = LLMUsage(
            tokens_in=sum(len(m["content"]) // 4 for m in messages),
            tokens_out=len(response) // 4,
            model="mock",
        )
        return response


def get_backend(backend_type: str, **kwargs) -> LLMBackend:
    """
    Factory function to create LLM backends.

    Args:
        backend_type: "claude", "openai", "ollama", or "mock"
        **kwargs: Backend-specific configuration

    Returns:
        Configured LLM backend
    """
    if backend_type == "claude":
        return ClaudeBackend(**kwargs)
    elif backend_type == "openai":
        return OpenAIBackend(**kwargs)
    elif backend_type == "ollama":
        return OllamaBackend(**kwargs)
    elif backend_type == "mock":
        return MockBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

