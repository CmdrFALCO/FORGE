"""PyBaMM DFN simulation runner for battery cell design evaluation.

Implements the :class:`SimulationRunner` interface using PyBaMM's Doyle–Fuller–Newman
model to compute rate capability and thermal behaviour from geometric cell parameters.
"""

from __future__ import annotations

import logging
import time

from forge.ml.common.types import (
    CellSpec,
    RateCapabilityResult,
    SimulationConfig,
    SimulationResult,
)
from forge.ml.simulation.geometry_translator import GeometryTranslator
from forge.ml.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class PyBaMMRunner(SimulationRunner):
    """Run PyBaMM DFN simulations and extract electrochemical/thermal targets."""

    def __init__(self, base_parameter_set: str = "Chen2020") -> None:
        self._base_parameter_set = base_parameter_set
        self._translator = GeometryTranslator()

    # ---- SimulationRunner interface --------------------------------------

    def simulate(
        self,
        cell_spec: CellSpec,
        config: SimulationConfig,
    ) -> list[SimulationResult]:
        """Run discharge simulations at each C-rate in *config*.

        For each C-rate the DFN model is solved. An additional thermal
        simulation (lumped) is run at 2 C charge for max-temperature
        extraction. Results that fail to solve are returned with
        ``success=False``.
        """
        import pybamm

        overrides = self._translator.translate(cell_spec.parameters)
        results: list[SimulationResult] = []

        for c_rate in config.c_rates:
            t0 = time.monotonic()
            try:
                model = pybamm.lithium_ion.DFN()
                param = pybamm.ParameterValues(self._base_parameter_set)
                param.update(overrides)

                experiment = pybamm.Experiment(
                    [f"Discharge at {c_rate}C until 2.5V"]
                )
                sim = pybamm.Simulation(
                    model, parameter_values=param, experiment=experiment
                )
                sol = sim.solve()
                capacity = float(sol["Discharge capacity [A.h]"].entries[-1])

                results.append(
                    SimulationResult(
                        cell_spec=cell_spec,
                        c_rate=c_rate,
                        capacity_ah=capacity,
                        success=True,
                        solver_time_seconds=time.monotonic() - t0,
                    )
                )
            except Exception as exc:
                logger.warning(
                    "Simulation failed at %.1fC for %s: %s",
                    c_rate,
                    cell_spec.parameters,
                    exc,
                )
                results.append(
                    SimulationResult(
                        cell_spec=cell_spec,
                        c_rate=c_rate,
                        success=False,
                        error_message=str(exc),
                        solver_time_seconds=time.monotonic() - t0,
                    )
                )

        # ---- thermal simulation (2C discharge, lumped thermal) ------------
        t0 = time.monotonic()
        try:
            thermal_model = pybamm.lithium_ion.DFN(
                options={"thermal": "lumped"}
            )
            param_thermal = pybamm.ParameterValues(self._base_parameter_set)
            param_thermal.update(overrides)
            param_thermal.update(
                {
                    "Total heat transfer coefficient [W.m-2.K-1]": 5.0,
                    "Ambient temperature [K]": 298.15,
                    "Initial temperature [K]": 298.15,
                }
            )
            # Use fast discharge (starts at 100% SOC) instead of charge
            # to avoid infeasible charge-from-full-SOC.
            experiment_thermal = pybamm.Experiment(
                ["Discharge at 2C until 2.5V"]
            )
            sim_thermal = pybamm.Simulation(
                thermal_model,
                parameter_values=param_thermal,
                experiment=experiment_thermal,
            )
            sol_thermal = sim_thermal.solve()
            t_max_k = float(sol_thermal["Cell temperature [K]"].entries.max())
            t_max_c = t_max_k - 273.15

            # Attach thermal result to a synthetic 0-C-rate entry
            results.append(
                SimulationResult(
                    cell_spec=cell_spec,
                    c_rate=0.0,  # sentinel: thermal charge experiment
                    max_temperature_celsius=t_max_c,
                    success=True,
                    solver_time_seconds=time.monotonic() - t0,
                )
            )
        except Exception as exc:
            logger.warning(
                "Thermal simulation failed for %s: %s",
                cell_spec.parameters,
                exc,
            )
            results.append(
                SimulationResult(
                    cell_spec=cell_spec,
                    c_rate=0.0,
                    success=False,
                    error_message=str(exc),
                    solver_time_seconds=time.monotonic() - t0,
                )
            )

        return results

    def compute_rate_capability(
        self,
        results: list[SimulationResult],
        reference_c_rate: float = 0.2,
        test_c_rate: float = 2.0,
    ) -> RateCapabilityResult:
        """Compute rate capability as ``Q_test / Q_reference``."""
        ref_cap = 0.0
        test_cap = 0.0
        cell_spec = results[0].cell_spec

        for r in results:
            if not r.success:
                continue
            if abs(r.c_rate - reference_c_rate) < 0.01:
                ref_cap = r.capacity_ah
            elif abs(r.c_rate - test_c_rate) < 0.01:
                test_cap = r.capacity_ah

        ratio = test_cap / max(ref_cap, 1e-10)

        return RateCapabilityResult(
            cell_spec=cell_spec,
            reference_c_rate=reference_c_rate,
            test_c_rate=test_c_rate,
            capacity_ratio=ratio,
            reference_capacity_ah=ref_cap,
            test_capacity_ah=test_cap,
        )
