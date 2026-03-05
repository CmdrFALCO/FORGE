"""Tests for energy calculation formulas."""

import pytest

from forge.engine.calculations.energy import (
    calculate_areal_characteristics,
    calculate_cell_capacity,
    calculate_ecu_metrics,
    calculate_energy_density,
    calculate_np_ratio,
)


class TestEnergyDensity:
    """Tests for energy density calculations."""

    def test_basic_calculation(self):
        """Test basic energy density calculation."""
        result = calculate_energy_density(
            capacity_ah=10.0,
            nominal_voltage_v=3.65,
            cell_mass_g=300.0,
            cell_volume_cm3=150.0,
            stack_volume_cm3=120.0,
        )

        # Energy: 10 × 3.65 = 36.5 Wh
        assert result.cell_energy_wh == pytest.approx(36.5, rel=1e-6)

        # Gravimetric: 36.5 / 300 × 1000 = 121.67 Wh/kg
        assert result.gravimetric_whkg == pytest.approx(121.667, rel=1e-3)

        # Volumetric (cell): 36.5 / 150 × 1000 = 243.33 Wh/L
        assert result.volumetric_cell_whl == pytest.approx(243.333, rel=1e-3)

        # Volumetric (stack): 36.5 / 120 × 1000 = 304.17 Wh/L
        assert result.volumetric_stack_whl == pytest.approx(304.167, rel=1e-3)

    def test_zero_mass_protection(self):
        """Test that zero mass doesn't cause division error."""
        result = calculate_energy_density(
            capacity_ah=10.0,
            nominal_voltage_v=3.65,
            cell_mass_g=0.0,
            cell_volume_cm3=150.0,
            stack_volume_cm3=120.0,
        )
        assert result.gravimetric_whkg == 0.0

    def test_zero_volume_protection(self):
        """Test that zero volume doesn't cause division error."""
        result = calculate_energy_density(
            capacity_ah=10.0,
            nominal_voltage_v=3.65,
            cell_mass_g=300.0,
            cell_volume_cm3=0.0,
            stack_volume_cm3=0.0,
        )
        assert result.volumetric_cell_whl == 0.0
        assert result.volumetric_stack_whl == 0.0


class TestArealCharacteristics:
    """Tests for areal capacity and energy calculations."""

    def test_basic_calculation(self):
        """Test basic areal characteristics calculation."""
        result = calculate_areal_characteristics(
            capacity_ah=10.0,
            nominal_voltage_v=3.65,
            cathode_area_cm2=100.0,
            cathode_sheets=20,
        )

        # Total area: 100 × 20 = 2000 cm²
        assert result.total_cathode_area_cm2 == pytest.approx(2000.0, rel=1e-6)

        # Areal capacity: 10 × 1000 / 2000 = 5.0 mAh/cm²
        assert result.areal_capacity_mahcm2 == pytest.approx(5.0, rel=1e-6)

        # Areal energy: 5.0 × 3.65 = 18.25 mWh/cm²
        assert result.areal_energy_mwhcm2 == pytest.approx(18.25, rel=1e-6)

    def test_zero_area_protection(self):
        """Test that zero area doesn't cause division error."""
        result = calculate_areal_characteristics(
            capacity_ah=10.0,
            nominal_voltage_v=3.65,
            cathode_area_cm2=0.0,
            cathode_sheets=20,
        )
        assert result.areal_capacity_mahcm2 == 0.0
        assert result.areal_energy_mwhcm2 == 0.0


class TestCellCapacity:
    """Tests for cell capacity calculation."""

    def test_basic_calculation(self):
        """Test capacity calculation from electrode properties."""
        capacity = calculate_cell_capacity(
            cathode_area_cm2=100.0,  # 100 cm²
            cathode_sheets=20,
            loading_mgcm2=20.0,  # 20 mg/cm²
            spec_capacity_mahg=170.0,  # 170 mAh/g
        )

        # Total area: 100 × 20 = 2000 cm²
        # Active mass: 2000 × 20 × 2 = 80000 mg = 80 g
        # Capacity: 80 × 170 / 1000 = 13.6 Ah
        assert capacity == pytest.approx(13.6, rel=1e-6)

    def test_typical_nmc_cell(self):
        """Test with typical NMC pouch cell values."""
        # Typical values for ~10 Ah pouch cell
        capacity = calculate_cell_capacity(
            cathode_area_cm2=180.0,  # ~10cm × 18cm
            cathode_sheets=15,
            loading_mgcm2=18.0,  # 18 mg/cm² loading
            spec_capacity_mahg=170.0,  # NMC532 capacity
        )

        # Should be approximately 16-17 Ah
        assert 16.0 < capacity < 18.0


class TestNPRatio:
    """Tests for N/P ratio calculation."""

    def test_balanced_cell(self):
        """Test N/P ratio for balanced design."""
        np_ratio = calculate_np_ratio(
            cathode_area_cm2=100.0,
            cathode_sheets=10,
            cathode_loading_mgcm2=20.0,
            cathode_spec_capacity_mahg=170.0,
            anode_area_cm2=105.0,  # Slightly larger anode
            anode_sheets=11,
            anode_loading_mgcm2=12.0,
            anode_spec_capacity_mahg=360.0,
        )

        # Cathode capacity: 100 × 10 × 20 × 2 × 170 / 1000 = 6800 mAh
        # Anode capacity: 105 × 11 × 12 × 2 × 360 / 1000 = 9979.2 mAh
        # N/P ratio: 9979.2 / 6800 ≈ 1.47

        assert np_ratio == pytest.approx(1.467, rel=1e-2)

    def test_typical_np_ratio(self):
        """Test that typical designs have N/P > 1."""
        # Typical cell should have N/P ratio between 1.1 and 1.3
        np_ratio = calculate_np_ratio(
            cathode_area_cm2=100.0,
            cathode_sheets=10,
            cathode_loading_mgcm2=18.0,
            cathode_spec_capacity_mahg=170.0,
            anode_area_cm2=104.0,  # 2mm overhang each side
            anode_sheets=11,
            anode_loading_mgcm2=10.0,
            anode_spec_capacity_mahg=360.0,
        )

        # N/P should be > 1 for safe operation (prevents Li plating)
        assert np_ratio > 1.0
        assert np_ratio < 2.0

    def test_zero_cathode_protection(self):
        """Test that zero cathode capacity returns 0."""
        np_ratio = calculate_np_ratio(
            cathode_area_cm2=0.0,
            cathode_sheets=10,
            cathode_loading_mgcm2=18.0,
            cathode_spec_capacity_mahg=170.0,
            anode_area_cm2=100.0,
            anode_sheets=11,
            anode_loading_mgcm2=10.0,
            anode_spec_capacity_mahg=360.0,
        )
        assert np_ratio == 0.0


class TestECUMetrics:
    """Tests for Electrochemical Unit (ECU) metrics calculation.

    ECU represents the active repeating unit: coatings + half collectors + separator.
    """

    def test_ecu_thickness(self):
        """ECU thickness = cathode + anode coating + avg collector + separator."""
        result = calculate_ecu_metrics(
            cathode_coating_100pct_um=70.0,
            anode_coating_100pct_um=80.0,
            cathode_collector_um=15.0,
            anode_collector_um=10.0,
            separator_um=16.0,
            cathode_area_cm2=100.0,
            cathode_sheets_cell=20,
            energy_wh=50.0,
        )

        # ECU thickness = 70 + 80 + (15+10)/2 + 16 = 178.5 um
        expected_thickness = 70.0 + 80.0 + (15.0 + 10.0) / 2.0 + 16.0
        assert result.ecu_thickness_um == pytest.approx(expected_thickness, rel=0.01)
        assert result.ecu_thickness_um == pytest.approx(178.5, rel=0.01)

    def test_ecu_volume(self):
        """ECU volume = thickness x area x sheets."""
        result = calculate_ecu_metrics(
            cathode_coating_100pct_um=70.0,
            anode_coating_100pct_um=80.0,
            cathode_collector_um=15.0,
            anode_collector_um=10.0,
            separator_um=16.0,
            cathode_area_cm2=100.0,
            cathode_sheets_cell=20,
            energy_wh=50.0,
        )

        # ECU thickness = 178.5 um
        # ECU volume = (178.5/10000) x 100 x 20 = 35.7 cm3
        expected_volume = (178.5 / 10000.0) * 100.0 * 20
        assert result.ecu_volume_cm3 == pytest.approx(expected_volume, rel=0.01)
        assert result.ecu_volume_cm3 == pytest.approx(35.7, rel=0.01)

    def test_ecu_energy_density(self):
        """ECU energy density = energy / volume x 1000."""
        result = calculate_ecu_metrics(
            cathode_coating_100pct_um=70.0,
            anode_coating_100pct_um=80.0,
            cathode_collector_um=15.0,
            anode_collector_um=10.0,
            separator_um=16.0,
            cathode_area_cm2=100.0,
            cathode_sheets_cell=20,
            energy_wh=50.0,
        )

        # ECU energy density = 50 Wh / 35.7 cm3 x 1000 = 1401 Wh/L
        expected_ed = (50.0 / 35.7) * 1000
        assert result.ecu_energy_density_wh_l == pytest.approx(expected_ed, rel=0.01)
        assert result.ecu_energy_density_wh_l == pytest.approx(1401.0, rel=0.01)

    def test_ecu_energy_density_higher_than_cell(self):
        """ECU energy density should be higher than cell volumetric energy density.

        This is because ECU excludes packaging overhead (housing, tabs, etc.).
        """
        # Use realistic values from V1 Prismatic
        cathode_coating = 57.08  # um at 100% SoC
        anode_coating = 92.31  # um at 100% SoC
        cathode_collector = 12.0
        anode_collector = 6.0
        separator = 13.0
        cathode_area = 186.18  # cm2
        cathode_sheets = 88
        energy = 440.467  # Wh

        ecu_result = calculate_ecu_metrics(
            cathode_coating_100pct_um=cathode_coating,
            anode_coating_100pct_um=anode_coating,
            cathode_collector_um=cathode_collector,
            anode_collector_um=anode_collector,
            separator_um=separator,
            cathode_area_cm2=cathode_area,
            cathode_sheets_cell=cathode_sheets,
            energy_wh=energy,
        )

        # V1 Prismatic cell volumetric ED is ~629 Wh/L
        cell_volumetric_ed = 629.29  # Wh/L

        # ECU ED should be significantly higher (excludes housing overhead)
        assert ecu_result.ecu_energy_density_wh_l > cell_volumetric_ed
        # Typically ECU ED is 30-50% higher than cell ED
        assert ecu_result.ecu_energy_density_wh_l > cell_volumetric_ed * 1.2

    def test_zero_volume_protection(self):
        """Test that zero volume doesn't cause division error."""
        result = calculate_ecu_metrics(
            cathode_coating_100pct_um=0.0,
            anode_coating_100pct_um=0.0,
            cathode_collector_um=0.0,
            anode_collector_um=0.0,
            separator_um=0.0,
            cathode_area_cm2=100.0,
            cathode_sheets_cell=20,
            energy_wh=50.0,
        )

        # Volume is 0, energy density should be 0 (not crash)
        assert result.ecu_volume_cm3 == 0.0
        assert result.ecu_energy_density_wh_l == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
