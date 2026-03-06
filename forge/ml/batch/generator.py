"""Abstract interface for batch cell geometry generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from forge.ml.common.types import CellSpec, DesignSpace, SamplingStrategy


class BatchGenerator(ABC):
    """Generates batches of cell specifications from a parametric design space."""

    @abstractmethod
    def generate(
        self,
        design_space: DesignSpace,
        n_samples: int,
        strategy: SamplingStrategy = SamplingStrategy.LATIN_HYPERCUBE,
        seed: int = 42,
    ) -> list[CellSpec]:
        """Generate a batch of cell specifications by sampling the design space."""
        raise NotImplementedError
