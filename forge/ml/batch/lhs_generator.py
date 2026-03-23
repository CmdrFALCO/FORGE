"""Latin Hypercube Sampling batch generator for parametric design spaces."""

from __future__ import annotations

import numpy as np
from scipy.stats.qmc import LatinHypercube

from forge.ml.batch.generator import BatchGenerator
from forge.ml.common.types import CellSpec, DesignSpace, SamplingStrategy

# Parameters that must be rounded to integers
_INTEGER_PARAMS = frozenset({"n_tabs"})


class LHSGenerator(BatchGenerator):
    """Generate batches of cell specifications using Latin Hypercube Sampling."""

    def generate(
        self,
        design_space: DesignSpace,
        n_samples: int,
        strategy: SamplingStrategy = SamplingStrategy.LATIN_HYPERCUBE,
        seed: int = 42,
    ) -> list[CellSpec]:
        """Sample the design space using LHS.

        Args:
            design_space: Parameter ranges to sample from.
            n_samples: Number of samples to generate.
            strategy: Sampling strategy (only LHS is supported).
            seed: Random seed for reproducibility.

        Returns:
            List of *n_samples* :class:`CellSpec` instances.

        Raises:
            ValueError: If inputs are invalid.
        """
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")
        if not design_space.parameters:
            raise ValueError("design_space.parameters must be non-empty")
        for p in design_space.parameters:
            if p.min_value >= p.max_value:
                raise ValueError(
                    f"Parameter '{p.name}': min_value ({p.min_value}) "
                    f"must be < max_value ({p.max_value})"
                )

        n_params = len(design_space.parameters)
        sampler = LatinHypercube(d=n_params, seed=seed)
        raw = sampler.random(n=n_samples)  # shape (n_samples, n_params), values in [0, 1]

        lows = np.array([p.min_value for p in design_space.parameters])
        highs = np.array([p.max_value for p in design_space.parameters])
        scaled = lows + raw * (highs - lows)

        specs: list[CellSpec] = []
        for row in scaled:
            params: dict[str, float] = {}
            for j, p in enumerate(design_space.parameters):
                val = float(row[j])
                if p.name in _INTEGER_PARAMS:
                    val = float(round(val))
                params[p.name] = val
            specs.append(
                CellSpec(
                    cell_type=design_space.cell_type,
                    parameters=params,
                    metadata={},
                )
            )
        return specs

    def generate_with_derived(
        self,
        design_space: DesignSpace,
        n_samples: int,
        translator: "GeometryTranslator",  # noqa: F821 — avoid circular import
        seed: int = 42,
    ) -> list[CellSpec]:
        """Generate samples and enrich with derived ML features.

        Calls :meth:`generate` then appends ``surface_to_volume``,
        ``tab_conductance_proxy``, and ``diffusion_path_proxy`` to each
        spec's parameter dict via the translator.
        """
        specs = self.generate(design_space, n_samples, seed=seed)
        for spec in specs:
            derived = translator.compute_derived_features(spec.parameters)
            spec.parameters.update(derived)
        return specs
