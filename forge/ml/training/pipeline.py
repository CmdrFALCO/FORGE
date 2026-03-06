"""Abstract interface for ML training pipeline orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from forge.ml.common.types import TrainingConfig, TrainingMetrics


class TrainingPipeline(ABC):
    """Orchestrates the full ML training workflow."""

    @abstractmethod
    def run(
        self,
        config: TrainingConfig,
        dataset_path: Path,
        output_dir: Path,
    ) -> TrainingMetrics:
        """Execute a complete training run."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        model_path: Path,
        dataset_path: Path,
    ) -> TrainingMetrics:
        """Evaluate a saved model on a dataset."""
        raise NotImplementedError
