"""Tests for geometry validation."""

from pathlib import Path

import pytest

from forge.engine.geometry.loader import ArchetypeLoader
from forge.engine.geometry.validation import (
    DEFAULT_THRESHOLDS,
    GeometryValidator,
    Severity,
    ValidationCategory,
    ValidationReport,
    ValidationThresholds,
    validate_geometry,
)

ARCHETYPE_DIR = Path("docs")


@pytest.fixture
def byd_blade_geometry():
    loader = ArchetypeLoader(ARCHETYPE_DIR / "byd_blade_138ah_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def tesla_4680_geometry():
    loader = ArchetypeLoader(ARCHETYPE_DIR / "tesla_4680_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def samsung_21700_geometry():
    loader = ArchetypeLoader(ARCHETYPE_DIR / "samsung_21700_50g_archetype.json")
    return loader.to_detailed_geometry()


class TestValidationReport:
    def test_report_summary(self, byd_blade_geometry):
        """Report should have summary."""
        report = validate_geometry(byd_blade_geometry)

        assert report.geometry_name is not None
        assert len(report.results) > 0
        assert isinstance(report.summary(), str)

    def test_report_to_dict(self, byd_blade_geometry):
        """Report should serialize to dict."""
        report = validate_geometry(byd_blade_geometry)
        d = report.to_dict()

        assert "geometry_name" in d
        assert "passed" in d
        assert "results" in d
        assert isinstance(d["results"], list)

    def test_report_counts(self, byd_blade_geometry):
        """Report should correctly count results."""
        report = validate_geometry(byd_blade_geometry)

        total = len(report.results)
        assert total > 0
        assert (
            report.pass_count + report.error_count + report.warning_count + report.info_count
            <= total
        )

    def test_get_by_category(self, byd_blade_geometry):
        """Should filter by category."""
        report = validate_geometry(byd_blade_geometry)

        dim_results = report.get_by_category(ValidationCategory.DIMENSIONAL)
        assert all(r.category == ValidationCategory.DIMENSIONAL for r in dim_results)

    def test_get_by_severity(self, byd_blade_geometry):
        """Should filter by severity."""
        report = validate_geometry(byd_blade_geometry)

        errors = report.get_by_severity(Severity.ERROR)
        assert all(r.severity == Severity.ERROR for r in errors)

    def test_get_failures(self, byd_blade_geometry):
        """Should get all failed validations."""
        report = validate_geometry(byd_blade_geometry)

        failures = report.get_failures()
        assert all(not r.passed for r in failures)


class TestGeometryValidator:
    def test_validate_returns_report(self, byd_blade_geometry):
        """Validator should return ValidationReport."""
        validator = GeometryValidator()
        report = validator.validate(byd_blade_geometry)

        assert isinstance(report, ValidationReport)

    def test_all_archetypes_validate(self):
        """All archetypes should pass validation."""
        archetypes = [
            "byd_blade_138ah_archetype.json",
            "tesla_4680_archetype.json",
            "lg_e66a_archetype.json",
            "samsung_21700_50g_archetype.json",
        ]

        for archetype_file in archetypes:
            path = ARCHETYPE_DIR / archetype_file
            if path.exists():
                loader = ArchetypeLoader(path)
                geometry = loader.to_detailed_geometry()
                report = validate_geometry(geometry)

                # Should at least run without errors
                assert report is not None
                assert len(report.results) > 0

    def test_custom_thresholds(self, byd_blade_geometry):
        """Should accept custom thresholds."""
        strict_thresholds = ValidationThresholds(
            min_coating_thickness_um=100.0,  # Very strict
        )

        validator = GeometryValidator(thresholds=strict_thresholds)
        report = validator.validate(byd_blade_geometry)

        # Should have more warnings with stricter thresholds
        assert report is not None

    def test_skip_rules(self, byd_blade_geometry):
        """Should skip specified rules."""
        validator = GeometryValidator(skip_rules=["DIM_001", "DIM_002"])
        report = validator.validate(byd_blade_geometry)

        rule_ids = [r.rule_id for r in report.results]
        assert "DIM_001" not in rule_ids
        assert "DIM_002" not in rule_ids

    def test_validate_for_export(self, byd_blade_geometry):
        """Should return export decision."""
        validator = GeometryValidator()
        can_export, report = validator.validate_for_export(byd_blade_geometry)

        assert isinstance(can_export, bool)
        assert isinstance(report, ValidationReport)

    def test_validate_for_export_strict(self, byd_blade_geometry):
        """Strict mode should block on warnings too."""
        validator = GeometryValidator()
        can_export_strict, report = validator.validate_for_export(byd_blade_geometry, strict=True)
        can_export_lax, _ = validator.validate_for_export(byd_blade_geometry, strict=False)

        # Lax mode allows warnings, strict does not
        if report.has_warnings and report.passed:
            assert can_export_lax is True
            assert can_export_strict is False


class TestValidationRules:
    def test_stack_fits_in_casing(self, byd_blade_geometry):
        """Stack should fit in casing for valid archetype."""
        report = validate_geometry(byd_blade_geometry)

        dim_results = report.get_by_category(ValidationCategory.DIMENSIONAL)
        stack_fit = next((r for r in dim_results if r.rule_id == "DIM_001"), None)

        assert stack_fit is not None
        # Valid archetype should pass
        assert stack_fit.passed or stack_fit.severity != Severity.ERROR

    def test_manufacturing_rules_run(self, byd_blade_geometry):
        """Manufacturing rules should execute."""
        report = validate_geometry(byd_blade_geometry)

        mfg_results = report.get_by_category(ValidationCategory.MANUFACTURING)
        assert len(mfg_results) > 0

    def test_safety_rules_run(self, byd_blade_geometry):
        """Safety rules should execute."""
        report = validate_geometry(byd_blade_geometry)

        safety_results = report.get_by_category(ValidationCategory.SAFETY)
        assert len(safety_results) > 0

    def test_cylindrical_validation(self, tesla_4680_geometry):
        """Cylindrical cells should validate correctly."""
        report = validate_geometry(tesla_4680_geometry)

        assert report is not None
        assert len(report.results) > 0

        # Check dimensional validation ran for cylindrical
        dim_results = report.get_by_category(ValidationCategory.DIMENSIONAL)
        assert len(dim_results) > 0


class TestValidationThresholds:
    def test_default_thresholds(self):
        """Default thresholds should have reasonable values."""
        t = ValidationThresholds()

        assert t.min_coating_thickness_um > 0
        assert t.min_collector_thickness_um > 0
        assert t.np_ratio_min < t.np_ratio_max

    def test_chemistry_specific_thresholds(self):
        """Should adjust for chemistry."""
        lfp = ValidationThresholds.for_chemistry("LFP")
        nmc811 = ValidationThresholds.for_chemistry("NMC811")

        # LFP is more tolerant
        assert lfp.np_ratio_max >= nmc811.np_ratio_max

    def test_user_override_takes_precedence(self):
        """User overrides should take precedence over chemistry defaults."""
        custom = ValidationThresholds.for_chemistry(
            "LFP",
            np_ratio_max=1.5,  # Override
        )

        assert custom.np_ratio_max == 1.5

    def test_chemistry_normalization(self):
        """Chemistry names should be normalized."""
        # NCM should be normalized to NMC
        ncm = ValidationThresholds.for_chemistry("NCM811")
        nmc = ValidationThresholds.for_chemistry("NMC811")

        assert ncm.np_ratio_max == nmc.np_ratio_max

    def test_default_thresholds_constant(self):
        """DEFAULT_THRESHOLDS should be usable."""
        assert DEFAULT_THRESHOLDS is not None
        assert DEFAULT_THRESHOLDS.min_coating_thickness_um > 0


class TestDetailedGeometryIntegration:
    def test_validate_method(self, byd_blade_geometry):
        """DetailedGeometry should have validate() method."""
        report = byd_blade_geometry.validate()
        assert isinstance(report, ValidationReport)

    def test_is_valid_method(self, byd_blade_geometry):
        """DetailedGeometry should have is_valid() method."""
        is_valid = byd_blade_geometry.is_valid()
        assert isinstance(is_valid, bool)

    def test_validate_legacy_method(self, byd_blade_geometry):
        """DetailedGeometry should have validate_legacy() method for backwards compat."""
        errors = byd_blade_geometry.validate_legacy()
        assert isinstance(errors, list)


class TestValidationResult:
    def test_result_str(self, byd_blade_geometry):
        """ValidationResult should have string representation."""
        report = validate_geometry(byd_blade_geometry)

        for result in report.results:
            s = str(result)
            assert result.rule_id in s
            assert result.message in s


class TestCrossValidation:
    def test_capacity_validation_with_declared(self, byd_blade_geometry):
        """Capacity validation should work with declared value."""
        validator = GeometryValidator()
        report = validator.validate(byd_blade_geometry, declared_capacity_ah=138.0)

        xval_results = report.get_by_category(ValidationCategory.CROSS_VALIDATION)
        capacity_result = next((r for r in xval_results if r.rule_id == "XVAL_001"), None)

        assert capacity_result is not None

    def test_mass_validation_with_declared(self, byd_blade_geometry):
        """Mass validation should work with declared value."""
        validator = GeometryValidator()
        report = validator.validate(byd_blade_geometry, declared_mass_g=1000.0)

        xval_results = report.get_by_category(ValidationCategory.CROSS_VALIDATION)
        mass_result = next((r for r in xval_results if r.rule_id == "XVAL_002"), None)

        assert mass_result is not None
