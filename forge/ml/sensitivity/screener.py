"""Abstract interface for Sobol sensitivity screening."""

from __future__ import annotations

from abc import ABC, abstractmethod

from forge.ml.common.types import DesignSpace, SobolResult


class SensitivityScreener(ABC):
    """Performs Sobol sensitivity analysis on the design space."""

    @abstractmethod
    def screen(
        self,
        design_space: DesignSpace,
        target_property: str,
        n_samples: int = 1024,
        seed: int = 42,
    ) -> SobolResult:
        """Run Sobol sensitivity analysis for a single target property."""
        raise NotImplementedError

    @abstractmethod
    def rank_parameters(
        self,
        result: SobolResult,
        threshold: float = 0.05,
    ) -> list[str]:
        """Rank parameters by total-order Sobol index and filter by threshold."""
        raise NotImplementedError
