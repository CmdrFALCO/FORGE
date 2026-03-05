"""Tests for result validation functionality.

This module tests result validation (comparing calculated values against reference targets).
This is DIFFERENT from parameter validation in tests/validation/ (Phase 1.5 LLM parameter validation).

Result validation: cellcad.result_validation module
Parameter validation: cellcad.validation package
"""

import pytest

from forge.engine.models.results import CellReport
from forge.engine.validation.result_validation import (
    V1_POUCH_REFERENCE,
    V1_POUCH_TOLERANCES,
    format_validation_report,
    validate_against_reference,
    validate_value,
)


@pytest.fixture
def sample_report():
    """Create a sample cell report for testing."""
    return CellReport(
        cell_name="Test Cell",
        cell_type="Pouch",
        cell_height_mm=200.0,
        cell_width_mm=100.0,
        cell_thickness_dry_mm=6.0,
        cell_thickness_soc0_mm=6.12,
        cell_thickness_soc100_mm=6.3,
        volume_cell_cm3=122.4,
        volume_stack_cm3=100.0,
        cathode_sheets=15,
        anode_sheets=16,
        separator_sheets=32,
        cathode_coating_mass_g=100.0,
        cathode_collector_mass_g=10.0,
        anode_coating_mass_g=60.0,
        anode_collector_mass_g=25.0,
        separator_mass_g=6.0,
        electrolyte_mass_g=50.0,
        housing_mass_g=15.0,
        tabs_mass_g=3.0,
        capacity_ah=10.0,
        nominal_voltage_v=3.65,
        gravimetric_ed_whkg=120.0,
        volumetric_ed_cell_whl=300.0,
        volumetric_ed_stack_whl=365.0,
        areal_capacity_mahcm2=5.0,
        areal_energy_mwhcm2=18.25,
    )


class TestValidateValue:
    """Tests for single value validation."""

    def test_exact_match(self):
        """Test exact match passes."""
        result = validate_value("test_param", 100.0, 100.0, tolerance_pct=5.0)
        assert result.passed
        assert result.delta == 0.0
        assert result.delta_pct == 0.0

    def test_within_tolerance(self):
        """Test value within tolerance passes."""
        result = validate_value("test_param", 100.0, 103.0, tolerance_pct=5.0)
        assert result.passed
        assert result.delta_pct == pytest.approx(3.0, rel=1e-6)

    def test_outside_tolerance(self):
        """Test value outside tolerance fails."""
        result = validate_value("test_param", 100.0, 110.0, tolerance_pct=5.0)
        assert not result.passed
        assert result.delta_pct == pytest.approx(10.0, rel=1e-6)

    def test_negative_delta(self):
        """Test negative delta (actual < expected)."""
        result = validate_value("test_param", 100.0, 95.0, tolerance_pct=5.0)
        assert result.passed
        assert result.delta == 5.0

    def test_zero_expected(self):
        """Test handling of zero expected value."""
        result = validate_value("test_param", 0.0, 0.0, tolerance_pct=5.0)
        assert result.passed
        assert result.delta_pct == 0.0


class TestValidateAgainstReference:
    """Tests for reference validation."""

    def test_all_pass(self, sample_report):
        """Test validation when all values pass."""
        reference = {
            "capacity_ah": 10.0,
            "nominal_voltage_v": 3.65,
        }
        tolerances = {
            "capacity_ah": 1.0,
            "nominal_voltage_v": 1.0,
        }

        report = validate_against_reference(sample_report, reference, tolerances)

        assert report.all_passed
        assert report.pass_count == 2
        assert report.fail_count == 0

    def test_some_fail(self, sample_report):
        """Test validation when some values fail."""
        reference = {
            "capacity_ah": 10.0,  # Will pass
            "gravimetric_ed_whkg": 100.0,  # Will fail (actual=120)
        }
        tolerances = {
            "capacity_ah": 1.0,
            "gravimetric_ed_whkg": 5.0,  # 5% tolerance
        }

        report = validate_against_reference(sample_report, reference, tolerances)

        assert not report.all_passed
        assert report.pass_count == 1
        assert report.fail_count == 1

    def test_missing_attributes_skipped(self, sample_report):
        """Test that missing attributes are skipped."""
        reference = {
            "capacity_ah": 10.0,
            "nonexistent_param": 100.0,
        }

        report = validate_against_reference(sample_report, reference)

        # Only capacity_ah should be validated
        assert len(report.results) == 1
        assert report.results[0].parameter == "capacity_ah"

    def test_default_tolerance(self, sample_report):
        """Test using default tolerance."""
        reference = {
            "capacity_ah": 10.0,
        }

        # With 5% default tolerance
        report = validate_against_reference(sample_report, reference, default_tolerance_pct=5.0)

        assert report.results[0].tolerance_pct == 5.0


class TestFormatValidationReport:
    """Tests for validation report formatting."""

    def test_format_passed(self, sample_report):
        """Test formatting passed validation."""
        reference = {"capacity_ah": 10.0}
        validation = validate_against_reference(sample_report, reference)

        text = format_validation_report(validation)

        assert "VALIDATION REPORT" in text
        assert "PASSED" in text
        assert "capacity_ah" in text

    def test_format_failed(self, sample_report):
        """Test formatting failed validation."""
        reference = {"capacity_ah": 5.0}  # Will fail (actual=10)
        validation = validate_against_reference(sample_report, reference)

        text = format_validation_report(validation)

        assert "FAILED" in text
        assert "FAIL" in text

    def test_format_shows_values(self, sample_report):
        """Test that formatted report shows values."""
        reference = {"capacity_ah": 10.0}
        validation = validate_against_reference(sample_report, reference)

        text = format_validation_report(validation)

        assert "10.000" in text  # Expected and actual values


class TestV1References:
    """Tests for V1 reference data."""

    def test_v1_pouch_reference_keys(self):
        """Test that V1 Pouch reference has expected keys."""
        expected_keys = [
            "capacity_ah",
            "nominal_voltage_v",
            "total_mass_g",
            "cathode_mass_g",
            "anode_mass_g",
            "separator_mass_g",
            "electrolyte_mass_g",
            "housing_mass_g",
            "gravimetric_ed_whkg",
            "volumetric_ed_cell_whl",
        ]

        for key in expected_keys:
            assert key in V1_POUCH_REFERENCE

    def test_v1_pouch_tolerances_match_reference(self):
        """Test that tolerances exist for all reference values."""
        for key in V1_POUCH_REFERENCE:
            assert key in V1_POUCH_TOLERANCES

    def test_v1_pouch_values_reasonable(self):
        """Test that V1 Pouch values are reasonable."""
        assert V1_POUCH_REFERENCE["capacity_ah"] > 0
        assert V1_POUCH_REFERENCE["nominal_voltage_v"] > 0
        assert V1_POUCH_REFERENCE["total_mass_g"] > 0
        assert V1_POUCH_REFERENCE["gravimetric_ed_whkg"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

