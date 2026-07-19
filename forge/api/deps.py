"""Shared API dependencies for AXIOM-backed routes."""

from __future__ import annotations

from fastapi import HTTPException

from forge.axiom.backends.backends import (
    ANTHROPIC_AVAILABLE,
    OPENAI_AVAILABLE,
    REQUESTS_AVAILABLE,
    ClaudeBackend,
    LLMBackend,
    OllamaBackend,
    OpenAIBackend,
)

SUPPORTED_BACKENDS = ("ollama", "claude", "anthropic", "openai")


def _normalize_backend_name(backend: str) -> str:
    value = backend.strip().lower()
    if value == "anthropic":
        return "claude"
    return value


def build_backend(backend: str, model: str | None = None) -> LLMBackend:
    """Instantiate an AXIOM backend with dependency checks."""
    backend_name = _normalize_backend_name(backend)

    if backend_name == "ollama":
        if not REQUESTS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Ollama backend requires 'requests'. Install with: "
                    "pip install requests"
                ),
            )
        kwargs: dict[str, str] = {}
        if model:
            kwargs["model"] = model
        try:
            return OllamaBackend(**kwargs)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize Ollama backend: {exc}",
            ) from exc

    if backend_name == "claude":
        if not ANTHROPIC_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Claude backend requires 'anthropic'. Install with: "
                    "pip install anthropic"
                ),
            )
        kwargs: dict[str, str] = {}
        if model:
            kwargs["model"] = model
        try:
            return ClaudeBackend(**kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize Claude backend: {exc}",
            ) from exc

    if backend_name == "openai":
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail=(
                    "OpenAI backend requires 'openai'. Install with: "
                    "pip install forge[llm]"
                ),
            )
        kwargs: dict[str, str] = {}
        if model:
            kwargs["model"] = model
        try:
            return OpenAIBackend(**kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize OpenAI backend.",
            ) from exc

    raise HTTPException(
        status_code=400,
        detail=(
            f"Unsupported backend '{backend}'. "
            f"Supported backends: {', '.join(SUPPORTED_BACKENDS)}"
        ),
    )


__all__ = ["build_backend"]
