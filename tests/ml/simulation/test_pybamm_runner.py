"""Tests for the PyBaMMRunner — requires PyBaMM installed.

ALL tests are marked ``@pytest.mark.slow``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pybamm")

from forge.ml.common.types import CellSpec, CellType, SimulationConfig  # noqa: E402
from forge.ml.simulation.pybamm_runner import PyBaMMRunner  # noqa: E402

pytestmark = pytest.mark.slow

# Mid-range parameters expected to produce a viable cell
MID_PARAMS: dict[str, float] = {
    "electrode_thickness": 100.0,
    "porosity": 0.35,
    "separator_thickness": 25.0,
    "n_tabs": 3,
    "tab_width": 15.0,
    "can_inner_diameter": 45.0,
    "can_wall_thickness": 0.5,
    "cell_height": 80.0,
}


def _make_spec(params: dict[str, float]) -> CellSpec:
    return CellSpec(
        cell_type=CellType.CYLINDRICAL,
        parameters=params,
        metadata={},
    )


def _make_config(
    c_rates: list[float] | None = None,
) -> SimulationConfig:
    return SimulationConfig(
        c_rates=c_rates or [0.2, 3.0],
        parameter_set="Chen2020",
    )


@pytest.fixture
def runner() -> PyBaMMRunner:
    return PyBaMMRunner(base_parameter_set="Chen2020")


class TestSingleSimulation:
    """Run one simulation with mid-range parameters."""

    def test_success_and_plausible(self, runner: PyBaMMRunner) -> None:
        spec = _make_spec(MID_PARAMS)
        cfg = _make_config(c_rates=[0.2, 3.0])
        results = runner.simulate(spec, cfg)

        # Should have discharge results + 1 thermal result
        assert len(results) >= 2

        # Check discharge results
        discharge_results = [r for r in results if r.c_rate > 0]
        for r in discharge_results:
            assert r.success, f"Failed at {r.c_rate}C: {r.error_message}"
            assert r.capacity_ah > 0

        # Check rate capability
        rc = runner.compute_rate_capability(results, reference_c_rate=0.2, test_c_rate=3.0)
        assert 0.0 < rc.capacity_ratio <= 1.0

        # Check thermal result
        thermal = [r for r in results if r.c_rate == 0.0]
        if thermal and thermal[0].success:
            assert 25.0 < thermal[0].max_temperature_celsius < 80.0


class TestExtremeParams:
    """Extreme parameters should fail gracefully, not crash."""

    def test_graceful_failure(self, runner: PyBaMMRunner) -> None:
        extreme = {
            "electrode_thickness": 150.0,
            "porosity": 0.20,
            "separator_thickness": 10.0,
            "n_tabs": 1,
            "tab_width": 5.0,
            "can_inner_diameter": 44.0,
            "can_wall_thickness": 0.2,
            "cell_height": 65.0,
        }
        spec = _make_spec(extreme)
        cfg = _make_config(c_rates=[0.2, 3.0])
        results = runner.simulate(spec, cfg)

        # Should not raise — results returned with success=True or False
        for r in results:
            if not r.success:
                assert r.error_message  # failure reason is populated


class TestRateCapabilityMonotonic:
    """More tabs → better rate capability (lower resistance)."""

    def test_more_tabs_better_rate(self, runner: PyBaMMRunner) -> None:
        params_few = {**MID_PARAMS, "n_tabs": 1, "tab_width": 5.0}
        params_many = {**MID_PARAMS, "n_tabs": 6, "tab_width": 30.0}

        cfg = _make_config(c_rates=[0.2, 3.0])

        res_few = runner.simulate(_make_spec(params_few), cfg)
        res_many = runner.simulate(_make_spec(params_many), cfg)

        rc_few = runner.compute_rate_capability(res_few, 0.2, 3.0)
        rc_many = runner.compute_rate_capability(res_many, 0.2, 3.0)

        if rc_few.capacity_ratio > 0 and rc_many.capacity_ratio > 0:
            assert rc_many.capacity_ratio >= rc_few.capacity_ratio


class TestTemperatureMonotonic:
    """Thicker electrode → higher max temperature."""

    def test_thick_electrode_hotter(self, runner: PyBaMMRunner) -> None:
        params_thin = {**MID_PARAMS, "electrode_thickness": 60.0}
        params_thick = {**MID_PARAMS, "electrode_thickness": 140.0}

        cfg = _make_config(c_rates=[0.2])

        res_thin = runner.simulate(_make_spec(params_thin), cfg)
        res_thick = runner.simulate(_make_spec(params_thick), cfg)

        thermal_thin = [r for r in res_thin if r.c_rate == 0.0 and r.success]
        thermal_thick = [r for r in res_thick if r.c_rate == 0.0 and r.success]

        if thermal_thin and thermal_thick:
            assert thermal_thick[0].max_temperature_celsius >= thermal_thin[0].max_temperature_celsius
