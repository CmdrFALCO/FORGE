"""Tests for the LHS batch generator."""

from __future__ import annotations

import pytest

from forge.ml.batch.lhs_generator import LHSGenerator
from forge.ml.common.types import CellType, DesignSpace, ParameterRange
from forge.ml.simulation.geometry_translator import GeometryTranslator


def _make_design_space() -> DesignSpace:
    return DesignSpace(
        parameters=[
            ParameterRange("electrode_thickness", 50.0, 150.0, "um"),
            ParameterRange("porosity", 0.20, 0.50, ""),
            ParameterRange("separator_thickness", 10.0, 50.0, "um"),
            ParameterRange("n_tabs", 1.0, 6.0, "count"),
            ParameterRange("tab_width", 5.0, 30.0, "mm"),
            ParameterRange("can_inner_diameter", 44.0, 46.0, "mm"),
            ParameterRange("can_wall_thickness", 0.2, 0.8, "mm"),
            ParameterRange("cell_height", 65.0, 95.0, "mm"),
        ],
        cell_type=CellType.CYLINDRICAL,
    )


@pytest.fixture
def gen() -> LHSGenerator:
    return LHSGenerator()


@pytest.fixture
def ds() -> DesignSpace:
    return _make_design_space()


class TestBasicGeneration:
    def test_correct_count(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 50)
        assert len(specs) == 50

    def test_cell_type(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 10)
        for s in specs:
            assert s.cell_type == CellType.CYLINDRICAL

    def test_all_params_present(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 10)
        expected_keys = {p.name for p in ds.parameters}
        for s in specs:
            assert set(s.parameters.keys()) == expected_keys


class TestParameterRanges:
    def test_within_bounds(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 200)
        for s in specs:
            for p in ds.parameters:
                val = s.parameters[p.name]
                # Integer params may be rounded to boundary
                if p.name == "n_tabs":
                    assert p.min_value <= val <= p.max_value
                else:
                    assert p.min_value <= val <= p.max_value, (
                        f"{p.name}: {val} outside [{p.min_value}, {p.max_value}]"
                    )


class TestIntegerRounding:
    def test_n_tabs_integer(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 100)
        for s in specs:
            val = s.parameters["n_tabs"]
            assert val == int(val), f"n_tabs={val} is not integer"
            assert 1 <= val <= 6


class TestReproducibility:
    def test_same_seed_same_result(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        a = gen.generate(ds, 20, seed=42)
        b = gen.generate(ds, 20, seed=42)
        for sa, sb in zip(a, b):
            assert sa.parameters == sb.parameters

    def test_different_seeds_differ(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        a = gen.generate(ds, 20, seed=42)
        b = gen.generate(ds, 20, seed=99)
        # At least one sample must differ
        any_diff = any(
            sa.parameters != sb.parameters for sa, sb in zip(a, b)
        )
        assert any_diff


class TestCoverage:
    def test_lhs_covers_range(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        specs = gen.generate(ds, 500)
        for p in ds.parameters:
            if p.name == "n_tabs":
                continue  # integer, skip coverage check
            vals = [s.parameters[p.name] for s in specs]
            rng = p.max_value - p.min_value
            assert min(vals) < p.min_value + 0.2 * rng
            assert max(vals) > p.max_value - 0.2 * rng


class TestValidation:
    def test_zero_samples(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        with pytest.raises(ValueError, match="n_samples"):
            gen.generate(ds, 0)

    def test_empty_design_space(self, gen: LHSGenerator) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            gen.generate(DesignSpace(), 10)

    def test_bad_range(self, gen: LHSGenerator) -> None:
        bad_ds = DesignSpace(
            parameters=[ParameterRange("x", 10.0, 5.0)],
        )
        with pytest.raises(ValueError, match="min_value"):
            gen.generate(bad_ds, 10)


class TestGenerateWithDerived:
    def test_derived_features_added(self, gen: LHSGenerator, ds: DesignSpace) -> None:
        translator = GeometryTranslator()
        specs = gen.generate_with_derived(ds, 10, translator)
        for s in specs:
            assert "surface_to_volume" in s.parameters
            assert "tab_conductance_proxy" in s.parameters
            assert "diffusion_path_proxy" in s.parameters
            # Original params still there
            assert "electrode_thickness" in s.parameters
