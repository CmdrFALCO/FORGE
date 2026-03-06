"""Abstract interfaces for dataset creation and loading."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from forge.ml.common.types import CellSpec, GeometricRepresentation, SimulationResult


class DatasetBuilder(ABC):
    """Orchestrates batch generation, simulation, and dataset assembly."""

    @abstractmethod
    def build(
        self,
        cell_specs: list[CellSpec],
        simulation_results: list[list[SimulationResult]],
        representations: list[GeometricRepresentation],
        output_path: Path,
    ) -> dict[str, Any]:
        """Assemble a complete dataset from pre-computed components."""
        raise NotImplementedError


class DatasetLoader(ABC):
    """Loads a previously built dataset for ML training."""

    @abstractmethod
    def load(
        self,
        dataset_path: Path,
    ) -> dict[str, Any]:
        """Load a dataset from disk."""
        raise NotImplementedError
