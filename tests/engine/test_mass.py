"""Tests for mass calculation formulas."""

import pytest

from forge.engine.calculations.mass import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    calculate_anode_mass,
    calculate_cathode_mass,
    calculate_electrolyte_mass,
    calculate_pouch_housing_mass,
    calculate_separator_mass,
    calculate_tab_mass,
)
from forge.engine.models.materials import PackagingLayer


class TestCathodeMass:
    """Tests for cathode mass calculation."""

    def test_basic_calculation(self):
        """Test basic cathode mass calculation."""
        result = calculate_cathode_mass(
            cathode_area_cm2=100.0,  # 100 cm²
            cathode_sheets=10,
            loading_mgcm2=20.0,  # 20 mg/cm²
            collector_thk_um=15.0,  # 15 µm Al foil
        )

        # Coating: 100 × 10 × 20 × 2 / 1000 = 40 g
        assert result.coating_g == pytest.approx(40.0, rel=1e-6)

        # Collector: 100 × 10 × 15 × 2.70 / 10000 = 4.05 g
        assert result.collector_g == pytest.approx(4.05, rel=1e-6)

        # Total: 40 + 4.05 = 44.05 g
        assert result.total_g == pytest.approx(44.05, rel=1e-6)

    def test_zero_sheets(self):
        """Test with zero sheets."""
        result = calculate_cathode_mass(
            cathode_area_cm2=100.0,
            cathode_sheets=0,
            loading_mgcm2=20.0,
            collector_thk_um=15.0,
        )
        assert result.coating_g == 0.0
        assert result.collector_g == 0.0
        assert result.total_g == 0.0

    def test_custom_density(self):
        """Test with custom aluminum density."""
        result = calculate_cathode_mass(
            cathode_area_cm2=100.0,
            cathode_sheets=1,
            loading_mgcm2=10.0,
            collector_thk_um=10.0,
            al_density_gcm3=3.0,  # Custom density
        )

        # Collector: 100 × 1 × 10 × 3.0 / 10000 = 0.3 g
        assert result.collector_g == pytest.approx(0.3, rel=1e-6)


class TestAnodeMass:
    """Tests for anode mass calculation."""

    def test_basic_calculation(self):
        """Test basic anode mass calculation."""
        result = calculate_anode_mass(
            anode_area_cm2=110.0,  # 110 cm² (larger than cathode)
            anode_sheets=11,
            loading_mgcm2=12.0,  # 12 mg/cm²
            collector_thk_um=10.0,  # 10 µm Cu foil
        )

        # Coating: 110 × 11 × 12 × 2 / 1000 = 29.04 g
        assert result.coating_g == pytest.approx(29.04, rel=1e-6)

        # Collector: 110 × 11 × 10 × 8.96 / 10000 = 10.8416 g
        assert result.collector_g == pytest.approx(10.8416, rel=1e-6)

    def test_copper_density_used(self):
        """Test that copper density is used by default."""
        result = calculate_anode_mass(
            anode_area_cm2=100.0,
            anode_sheets=1,
            loading_mgcm2=10.0,
            collector_thk_um=10.0,
        )

        # Collector: 100 × 1 × 10 × 8.96 / 10000 = 0.896 g
        assert result.collector_g == pytest.approx(0.896, rel=1e-6)


class TestSeparatorMass:
    """Tests for separator mass calculation."""

    def test_basic_calculation(self):
        """Test basic separator mass calculation."""
        mass = calculate_separator_mass(
            separator_area_cm2=120.0,
            separator_sheets=22,
            areal_weight_mgcm2=1.5,  # 1.5 mg/cm²
        )

        # Mass: 120 × 22 × 1.5 / 1000 = 3.96 g
        assert mass == pytest.approx(3.96, rel=1e-6)


class TestElectrolyteMass:
    """Tests for electrolyte mass calculation."""

    def test_basic_calculation(self):
        """Test basic electrolyte calculation with default excess."""
        result = calculate_electrolyte_mass(
            pores_anode_ml=10.0,
            pores_cathode_ml=8.0,
            pores_separator_ml=2.0,
            density_gcm3=1.25,
        )

        # Calc volume: 10 + 8 + 2 = 20 ml
        assert result.calc_volume_ml == pytest.approx(20.0, rel=1e-6)

        # Used volume: 20 × 1.10 = 22 ml
        assert result.used_volume_ml == pytest.approx(22.0, rel=1e-6)

        # Mass: 22 × 1.25 = 27.5 g
        assert result.mass_g == pytest.approx(27.5, rel=1e-6)

    def test_custom_excess_factor(self):
        """Test with custom excess factor."""
        result = calculate_electrolyte_mass(
            pores_anode_ml=10.0,
            pores_cathode_ml=10.0,
            pores_separator_ml=0.0,
            density_gcm3=1.0,
            excess_factor=1.20,  # 20% excess
        )

        # Used volume: 20 × 1.20 = 24 ml
        assert result.used_volume_ml == pytest.approx(24.0, rel=1e-6)

    def test_user_override(self):
        """Test with user-specified volume override."""
        result = calculate_electrolyte_mass(
            pores_anode_ml=10.0,
            pores_cathode_ml=10.0,
            pores_separator_ml=10.0,
            density_gcm3=1.0,
            excess_factor=1.10,
            user_override_ml=50.0,
        )

        # Calc volume unchanged
        assert result.calc_volume_ml == pytest.approx(30.0, rel=1e-6)

        # Used volume = override
        assert result.used_volume_ml == pytest.approx(50.0, rel=1e-6)

        # Mass: 50 × 1.0 = 50 g
        assert result.mass_g == pytest.approx(50.0, rel=1e-6)


class TestPouchHousingMass:
    """Tests for pouch housing mass calculation."""

    def test_basic_calculation(self):
        """Test pouch foil mass calculation."""
        # Simple single-layer foil
        layers = [
            PackagingLayer(
                name="Aluminum",
                version="1.0",
                thickness_um=40.0,
                porosity_pct=0.0,
                density_gcm3=2.70,
            )
        ]

        mass = calculate_pouch_housing_mass(
            cell_height_mm=100.0,
            cell_width_mm=100.0,
            case_composition=layers,
        )

        # Cell area: 100 × 100 / 100 = 100 cm²
        # Both sides: 100 × 2 = 200 cm²
        # Areal weight: 40 × 2.70 / 10 = 10.8 mg/cm²
        # Mass: 200 × 10.8 / 1000 = 2.16 g
        assert mass == pytest.approx(2.16, rel=1e-6)

    def test_multilayer_pouch(self):
        """Test multi-layer pouch foil."""
        layers = [
            PackagingLayer("PET", "1.0", 12.0, 0.0, 1.38),
            PackagingLayer("Al", "1.0", 40.0, 0.0, 2.70),
            PackagingLayer("PP", "1.0", 80.0, 0.0, 0.95),
        ]

        mass = calculate_pouch_housing_mass(
            cell_height_mm=200.0,
            cell_width_mm=100.0,
            case_composition=layers,
        )

        # Cell area: 200 × 100 / 100 = 200 cm²
        # Both sides: 400 cm²
        # Areal weights:
        #   PET: 12 × 1.38 / 10 = 1.656 mg/cm²
        #   Al:  40 × 2.70 / 10 = 10.8 mg/cm²
        #   PP:  80 × 0.95 / 10 = 7.6 mg/cm²
        # Total: 20.056 mg/cm²
        # Mass: 400 × 20.056 / 1000 = 8.0224 g
        assert mass == pytest.approx(8.0224, rel=1e-4)


class TestTabMass:
    """Tests for tab mass calculation."""

    def test_copper_tab(self):
        """Test copper tab mass calculation."""
        mass = calculate_tab_mass(
            height_mm=30.0,
            width_mm=50.0,
            thickness_mm=0.2,
            density_gcm3=DENSITY_COPPER,
        )

        # Volume: 30 × 50 × 0.2 / 1000 = 0.3 cm³
        # Mass: 0.3 × 8.96 = 2.688 g
        assert mass == pytest.approx(2.688, rel=1e-6)

    def test_aluminum_tab(self):
        """Test aluminum tab mass calculation."""
        mass = calculate_tab_mass(
            height_mm=30.0,
            width_mm=50.0,
            thickness_mm=0.3,
            density_gcm3=DENSITY_ALUMINUM,
        )

        # Volume: 30 × 50 × 0.3 / 1000 = 0.45 cm³
        # Mass: 0.45 × 2.70 = 1.215 g
        assert mass == pytest.approx(1.215, rel=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
