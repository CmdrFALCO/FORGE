"""Tests for the SobolScreener.

Fast tests (rank_parameters, print_report) use manually constructed data.
Slow tests (actual PyBaMM simulations) are marked ``@pytest.mark.slow``.
"""

from __future__ import annotations

import pytest

from forge.ml.common.types import SobolIndex, SobolResult
from forge.ml.sensitivity.sobol_screener import SobolScreener

# ---------------------------------------------------------------------------
# Manually constructed fixture for fast tests
# ---------------------------------------------------------------------------

def _make_result() -> SobolResult:
    return SobolResult(
        target_name="rate_capability",
        indices=[
            SobolIndex("electrode_thickness", "rate_capability", 0.412, 0.485, 0.028),
            SobolIndex("porosity", "rate_capability", 0.298, 0.341, 0.022),
            SobolIndex("n_tabs", "rate_capability", 0.103, 0.158, 0.017),
            SobolIndex("tab_width", "rate_capability", 0.045, 0.072, 0.012),
            SobolIndex("separator_thickness", "rate_capability", 0.031, 0.048, 0.010),
            SobolIndex("can_wall_thickness", "rate_capability", 0.008, 0.015, 0.008),
            SobolIndex("cell_height", "rate_capability", 0.015, 0.022, 0.009),
            SobolIndex("can_inner_diameter", "rate_capability", 0.001, 0.003, 0.005),
        ],
        n_samples=64,
        converged=True,
    )


class TestRankParameters:
    """Fast — no simulation needed."""

    def test_sorted_by_st_descending(self) -> None:
        screener = SobolScreener.__new__(SobolScreener)  # skip __init__
        result = _make_result()
        ranked = screener.rank_parameters(result, threshold=0.01)
        assert ranked[0] == "electrode_thickness"
        assert ranked[1] == "porosity"
        # Verify monotonic ST
        sts = {idx.parameter_name: idx.total_order for idx in result.indices}
        for i in range(len(ranked) - 1):
            assert sts[ranked[i]] >= sts[ranked[i + 1]]

    def test_threshold_excludes(self) -> None:
        screener = SobolScreener.__new__(SobolScreener)
        result = _make_result()
        ranked = screener.rank_parameters(result, threshold=0.05)
        assert "can_inner_diameter" not in ranked
        assert "can_wall_thickness" not in ranked
        assert "electrode_thickness" in ranked

    def test_high_threshold_empty(self) -> None:
        screener = SobolScreener.__new__(SobolScreener)
        result = _make_result()
        ranked = screener.rank_parameters(result, threshold=1.0)
        assert ranked == []


class TestPrintReport:
    """Fast — no simulation needed."""

    def test_report_contains_all_params(self) -> None:
        screener = SobolScreener.__new__(SobolScreener)
        result = _make_result()
        report = screener.print_report(result)
        for idx in result.indices:
            assert idx.parameter_name in report

    def test_report_format(self) -> None:
        screener = SobolScreener.__new__(SobolScreener)
        result = _make_result()
        report = screener.print_report(result, threshold=0.01)
        assert "Sobol Sensitivity Analysis" in report
        assert "rate_capability" in report
        assert "below threshold" in report.lower() or "above threshold" in report.lower()


# ---------------------------------------------------------------------------
# Slow tests — require PyBaMM
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestScreenRateCapability:
    def test_pipeline(self) -> None:
        from forge.ml.common.types import CellType, DesignSpace, ParameterRange
        from forge.ml.simulation.geometry_translator import GeometryTranslator
        from forge.ml.simulation.pybamm_runner import PyBaMMRunner

        ds = DesignSpace(
            parameters=[
                ParameterRange("electrode_thickness", 50.0, 150.0),
                ParameterRange("porosity", 0.20, 0.50),
                ParameterRange("separator_thickness", 10.0, 50.0),
                ParameterRange("n_tabs", 1.0, 6.0),
                ParameterRange("tab_width", 5.0, 30.0),
                ParameterRange("can_inner_diameter", 44.0, 46.0),
                ParameterRange("can_wall_thickness", 0.2, 0.8),
                ParameterRange("cell_height", 65.0, 95.0),
            ],
            cell_type=CellType.CYLINDRICAL,
        )
        runner = PyBaMMRunner()
        translator = GeometryTranslator()
        screener = SobolScreener(runner, translator)
        result = screener.screen(ds, "rate_capability", n_samples=16)

        assert result.target_name == "rate_capability"
        assert len(result.indices) == 8
        for idx in result.indices:
            assert -0.5 <= idx.first_order <= 1.5
            assert idx.total_order >= 0


@pytest.mark.slow
class TestScreenMaxTemp:
    def test_pipeline(self) -> None:
        from forge.ml.common.types import CellType, DesignSpace, ParameterRange
        from forge.ml.simulation.geometry_translator import GeometryTranslator
        from forge.ml.simulation.pybamm_runner import PyBaMMRunner

        ds = DesignSpace(
            parameters=[
                ParameterRange("electrode_thickness", 50.0, 150.0),
                ParameterRange("porosity", 0.20, 0.50),
                ParameterRange("separator_thickness", 10.0, 50.0),
                ParameterRange("n_tabs", 1.0, 6.0),
                ParameterRange("tab_width", 5.0, 30.0),
                ParameterRange("can_inner_diameter", 44.0, 46.0),
                ParameterRange("can_wall_thickness", 0.2, 0.8),
                ParameterRange("cell_height", 65.0, 95.0),
            ],
            cell_type=CellType.CYLINDRICAL,
        )
        runner = PyBaMMRunner()
        translator = GeometryTranslator()
        screener = SobolScreener(runner, translator)
        result = screener.screen(ds, "max_temp", n_samples=16)

        assert result.target_name == "max_temp"
        assert len(result.indices) == 8
