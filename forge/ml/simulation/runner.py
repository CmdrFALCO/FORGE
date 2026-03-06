"""Abstract interface for electrochemical simulation runners."""

from __future__ import annotations

from abc import ABC, abstractmethod

from forge.ml.common.types import (
    CellSpec,
    RateCapabilityResult,
    SimulationConfig,
    SimulationResult,
)


class SimulationRunner(ABC):
    """Runs electrochemical simulations on cell specifications."""

    @abstractmethod
    def simulate(
        self,
        cell_spec: CellSpec,
        config: SimulationConfig,
    ) -> list[SimulationResult]:
        """Run simulation for all C-rates defined in config."""
        raise NotImplementedError

    @abstractmethod
    def compute_rate_capability(
        self,
        results: list[SimulationResult],
        reference_c_rate: float = 0.2,
        test_c_rate: float = 2.0,
    ) -> RateCapabilityResult:
        """Compute rate capability metric from simulation results."""
        raise NotImplementedError
