"""Tests for the GeometryTranslator — verifies physics correctness."""

from __future__ import annotations

import math

import pytest

from forge.ml.simulation.geometry_translator import (
    NP_RATIO,
    R_CONTACT_BASELINE,
    GeometryTranslator,
)

# Mid-range parameter set used as baseline for most tests
MID_PARAMS: dict[str, float] = {
    "electrode_thickness": 100.0,
    "porosity": 0.30,
    "separator_thickness": 20.0,
    "n_tabs": 3,
    "tab_width": 15.0,
    "can_inner_diameter": 45.0,
    "can_wall_thickness": 0.5,
    "cell_height": 80.0,
}


@pytest.fixture
def translator() -> GeometryTranslator:
    return GeometryTranslator()


class TestDirectMappings:
    """Electrode/separator parameters converted to SI correctly."""

    def test_positive_electrode_thickness(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        expected = 100.0e-6  # 100 µm → m
        assert ov["Positive electrode thickness [m]"] == pytest.approx(expected)

    def test_separator_thickness(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        expected = 20.0e-6
        assert ov["Separator thickness [m]"] == pytest.approx(expected)

    def test_porosity(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        assert ov["Positive electrode porosity"] == pytest.approx(0.30)
        assert ov["Negative electrode porosity"] == pytest.approx(0.30)


class TestNPRatio:
    """Negative electrode is 1.1× positive electrode thickness."""

    def test_np_ratio(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        pos = ov["Positive electrode thickness [m]"]
        neg = ov["Negative electrode thickness [m]"]
        assert neg == pytest.approx(pos * NP_RATIO)


class TestContactResistance:
    """More/wider tabs → lower resistance, scaling linearly with total tab area."""

    def test_baseline_single_tab(self, translator: GeometryTranslator) -> None:
        p = {**MID_PARAMS, "n_tabs": 1, "tab_width": 10.0}
        ov = translator.translate(p)
        assert ov["Contact resistance [Ohm]"] == pytest.approx(R_CONTACT_BASELINE)

    def test_double_tabs_halves_resistance(self, translator: GeometryTranslator) -> None:
        p = {**MID_PARAMS, "n_tabs": 2, "tab_width": 10.0}
        ov = translator.translate(p)
        assert ov["Contact resistance [Ohm]"] == pytest.approx(R_CONTACT_BASELINE / 2)

    def test_double_width_halves_resistance(self, translator: GeometryTranslator) -> None:
        p = {**MID_PARAMS, "n_tabs": 1, "tab_width": 20.0}
        ov = translator.translate(p)
        assert ov["Contact resistance [Ohm]"] == pytest.approx(R_CONTACT_BASELINE / 2)

    def test_six_tabs_thirty_mm(self, translator: GeometryTranslator) -> None:
        p = {**MID_PARAMS, "n_tabs": 6, "tab_width": 30.0}
        ov = translator.translate(p)
        assert ov["Contact resistance [Ohm]"] == pytest.approx(R_CONTACT_BASELINE / 18)


class TestWindingIntegration:
    """Translator correctly calls L1 winding functions with plausible results."""

    def test_electrode_height(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        # 80mm cell - 5mm header - 3mm bottom = 72mm
        assert ov["Electrode height [m]"] == pytest.approx(0.072)

    def test_num_winds_reasonable(self, translator: GeometryTranslator) -> None:
        """4680-class cell should have ~20-60 winds."""
        ov = translator.translate(MID_PARAMS)
        # Electrode width (PyBaMM) = electrode length from winding [m]
        electrode_length_m = ov["Electrode width [m]"]
        # For 4680 cell: length should be order of metres (1-5m typically)
        assert 0.5 < electrode_length_m < 10.0

    def test_electrode_area_reasonable(self, translator: GeometryTranslator) -> None:
        """Electrode area for 4680 should be thousands of cm²."""
        ov = translator.translate(MID_PARAMS)
        length_m = ov["Electrode width [m]"]
        height_m = ov["Electrode height [m]"]
        # Double-sided area in cm²
        area_cm2 = length_m * height_m * 2 * 1e4
        assert 500 < area_cm2 < 20_000

    def test_single_parallel(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        assert ov["Number of electrodes connected in parallel to make a cell"] == 1


class TestThermalParameters:
    """Cell volume and surface area computed correctly for known dimensions."""

    def test_cell_volume(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        # r_outer = (45/2 + 0.5) mm = 23.0 mm = 0.023 m
        # h = 80 mm = 0.08 m
        r = 0.023
        h = 0.08
        expected = math.pi * r**2 * h
        assert ov["Cell volume [m3]"] == pytest.approx(expected, rel=1e-6)

    def test_heat_transfer_coefficient(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        assert ov["Total heat transfer coefficient [W.m-2.K-1]"] == 5.0

    def test_ambient_temperature(self, translator: GeometryTranslator) -> None:
        ov = translator.translate(MID_PARAMS)
        assert ov["Ambient temperature [K]"] == pytest.approx(298.15)


class TestDerivedFeatures:
    """ML derived features computed correctly."""

    def test_surface_to_volume(self, translator: GeometryTranslator) -> None:
        derived = translator.compute_derived_features(MID_PARAMS)
        expected = 2.0 / (45.0 / 2.0) + 2.0 / 80.0
        assert derived["surface_to_volume"] == pytest.approx(expected)

    def test_tab_conductance(self, translator: GeometryTranslator) -> None:
        derived = translator.compute_derived_features(MID_PARAMS)
        assert derived["tab_conductance_proxy"] == pytest.approx(3 * 15.0)

    def test_diffusion_path(self, translator: GeometryTranslator) -> None:
        derived = translator.compute_derived_features(MID_PARAMS)
        assert derived["diffusion_path_proxy"] == pytest.approx(100.0 / 0.30)


class TestDesignSpace:
    """get_design_space() returns all 8 parameters with correct ranges."""

    def test_all_params_present(self) -> None:
        ds = GeometryTranslator.get_design_space()
        assert len(ds) == 8
        for key in MID_PARAMS:
            assert key in ds

    def test_ranges_match(self) -> None:
        ds = GeometryTranslator.get_design_space()
        assert ds["electrode_thickness"] == (50.0, 150.0)
        assert ds["porosity"] == (0.20, 0.50)
        assert ds["n_tabs"] == (1.0, 6.0)
