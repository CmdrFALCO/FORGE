"""
LLM backend implementations for cell design generation.

Supports both cloud (Claude) and local (Ollama) inference.
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
        backend_type: "claude", "ollama", or "mock"
        **kwargs: Backend-specific configuration

    Returns:
        Configured LLM backend
    """
    if backend_type == "claude":
        return ClaudeBackend(**kwargs)
    elif backend_type == "ollama":
        return OllamaBackend(**kwargs)
    elif backend_type == "mock":
        return MockBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

