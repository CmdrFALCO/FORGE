"""Sobol sensitivity screener using SALib for variance-based global sensitivity."""

from __future__ import annotations

import logging

import numpy as np
from SALib.analyze import sobol as salib_sobol
from SALib.sample import saltelli

from forge.ml.common.types import (
    CellSpec,
    CellType,
    DesignSpace,
    SimulationConfig,
    SobolIndex,
    SobolResult,
)
from forge.ml.sensitivity.screener import SensitivityScreener
from forge.ml.simulation.geometry_translator import GeometryTranslator
from forge.ml.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class SobolScreener(SensitivityScreener):
    """Sobol sensitivity analysis using Saltelli sampling and SALib."""

    def __init__(
        self,
        runner: SimulationRunner,
        translator: GeometryTranslator,
    ) -> None:
        self._runner = runner
        self._translator = translator

    # ---- SensitivityScreener interface -----------------------------------

    def screen(
        self,
        design_space: DesignSpace,
        target_property: str,
        n_samples: int = 1024,
        seed: int = 42,
    ) -> SobolResult:
        """Run Sobol analysis for *target_property* (``rate_capability`` or ``max_temp``).

        Uses ``calc_second_order=False`` so the evaluation count is
        ``N * (D + 2)`` instead of ``N * (2D + 2)``.
        """
        params = design_space.parameters
        problem = {
            "num_vars": len(params),
            "names": [p.name for p in params],
            "bounds": [[p.min_value, p.max_value] for p in params],
        }

        # Saltelli sample matrix — shape (N*(D+2), D)
        param_values = saltelli.sample(
            problem, n_samples, calc_second_order=False
        )
        n_evals = len(param_values)
        logger.info(
            "Sobol screening: %d evaluations for %d samples, %d params",
            n_evals,
            n_samples,
            len(params),
        )

        config = SimulationConfig(
            c_rates=[0.2, 3.0],
            parameter_set="Chen2020",
        )

        y = np.full(n_evals, np.nan)
        n_failed = 0

        for i, row in enumerate(param_values):
            sample_params = {
                p.name: float(row[j]) for j, p in enumerate(params)
            }
            # Round integer params
            if "n_tabs" in sample_params:
                sample_params["n_tabs"] = float(round(sample_params["n_tabs"]))

            cell_spec = CellSpec(
                cell_type=CellType.CYLINDRICAL,
                parameters=sample_params,
                metadata={},
            )

            results = self._runner.simulate(cell_spec, config)

            if target_property == "rate_capability":
                rc = self._runner.compute_rate_capability(
                    results, reference_c_rate=0.2, test_c_rate=3.0,
                )
                y[i] = rc.capacity_ratio
            elif target_property == "max_temp":
                thermal = [
                    r for r in results if r.c_rate == 0.0 and r.success
                ]
                if thermal:
                    y[i] = thermal[0].max_temperature_celsius
            else:
                raise ValueError(f"Unknown target: {target_property}")

            if np.isnan(y[i]):
                n_failed += 1

            if (i + 1) % 50 == 0:
                logger.info("Evaluated %d / %d (failed: %d)", i + 1, n_evals, n_failed)

        # Impute NaN with mean (documented limitation)
        nan_mask = np.isnan(y)
        if nan_mask.any():
            logger.warning(
                "%d / %d evaluations failed (%.1f%%), imputing with mean",
                nan_mask.sum(),
                n_evals,
                100 * nan_mask.sum() / n_evals,
            )
            y[nan_mask] = np.nanmean(y) if not np.all(nan_mask) else 0.0

        si = salib_sobol.analyze(problem, y, calc_second_order=False)

        indices = []
        for j, p in enumerate(params):
            indices.append(
                SobolIndex(
                    parameter_name=p.name,
                    target_name=target_property,
                    first_order=float(si["S1"][j]),
                    total_order=float(si["ST"][j]),
                    confidence_interval=float(si["ST_conf"][j]),
                )
            )

        return SobolResult(
            target_name=target_property,
            indices=indices,
            n_samples=n_samples,
            converged=n_failed / n_evals < 0.10,
        )

    def rank_parameters(
        self,
        result: SobolResult,
        threshold: float = 0.05,
    ) -> list[str]:
        """Return parameter names sorted by ST descending, above *threshold*."""
        significant = [
            (idx.parameter_name, idx.total_order)
            for idx in result.indices
            if idx.total_order >= threshold
        ]
        significant.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in significant]

    # ---- reporting -------------------------------------------------------

    def print_report(self, result: SobolResult, threshold: float = 0.01) -> str:
        """Return a formatted text report of the Sobol analysis."""
        lines = [
            f"Sobol Sensitivity Analysis — target: {result.target_name} "
            f"(N={result.n_samples})",
            "=" * 60,
            f"{'Parameter':<25s} {'S1':>8s} {'ST':>8s} {'ST_conf':>8s}",
        ]
        above, below = [], []
        for idx in sorted(result.indices, key=lambda x: x.total_order, reverse=True):
            row = (
                f"{idx.parameter_name:<25s} "
                f"{idx.first_order:>8.3f} "
                f"{idx.total_order:>8.3f} "
                f"{idx.confidence_interval:>8.3f}"
            )
            if idx.total_order >= threshold:
                above.append(row)
            else:
                below.append(idx)

        lines.extend(above)
        lines.append("-" * 60)
        if below:
            lines.append(f"Parameters below threshold (ST < {threshold}):")
            for idx in below:
                lines.append(f"  {idx.parameter_name} (ST={idx.total_order:.3f})")
        else:
            lines.append("All parameters above threshold.")
        return "\n".join(lines)
