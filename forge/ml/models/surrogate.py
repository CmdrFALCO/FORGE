"""Abstract interface for ML surrogate models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class SurrogateModel(ABC):
    """Base class for ML surrogate models predicting cell properties."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
        raise NotImplementedError

    @abstractmethod
    def train(
        self,
        X: Any,
        y: Any,
        validation_data: tuple[Any, Any] | None = None,
    ) -> dict[str, float]:
        """Train the model on feature matrix X and target matrix y."""
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        X: Any,
    ) -> Any:
        """Predict target properties from feature matrix X."""
        raise NotImplementedError

    @abstractmethod
    def save(self, path: Path) -> None:
        """Save a trained model to disk."""
        raise NotImplementedError

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load a trained model from disk."""
        raise NotImplementedError
