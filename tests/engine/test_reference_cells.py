"""Tests for reference cell loading and validation.

This module tests the result validation system for reference cells:
- Loading reference cell JSON files
- Validation against reference cells
- PyBaMM parameter extraction (if available)

Note: This is different from parameter validation in tests/validation/ (Phase 1.5 LLM parameter validation).

Result validation: cellcad.result_validation module
Parameter validation: cellcad.validation package
"""

import importlib.util
import json
from pathlib import Path

import pytest

from forge.engine.validation.result_validation import (
    ReferenceCell,
    format_reference_list,
    get_reference_info,
    list_reference_cells,
    load_reference_cell,
)

# =============================================================================
# Test Reference Cell Loading
# =============================================================================


class TestListReferenceCells:
    """Tests for list_reference_cells function."""

    def test_list_reference_cells_returns_list(self):
        """Should return a list of reference cell IDs."""
        cells = list_reference_cells()
        assert isinstance(cells, list)

    def test_list_reference_cells_contains_v1_pouch(self):
        """Should include the v1_pouch reference."""
        cells = list_reference_cells()
        assert "v1_pouch" in cells

    def test_list_reference_cells_contains_expected_cells(self):
        """Should include all expected reference cells."""
        cells = list_reference_cells()
        expected = ["v1_pouch", "a123_amp20", "kokam_ecker2015", "lg_e66a"]
        for cell_id in expected:
            assert cell_id in cells, f"Missing reference cell: {cell_id}"

    def test_list_reference_cells_sorted(self):
        """Should return sorted list."""
        cells = list_reference_cells()
        assert cells == sorted(cells)

    def test_list_reference_cells_empty_dir(self, tmp_path):
        """Should return empty list for empty directory."""
        cells = list_reference_cells(tmp_path)
        assert cells == []


class TestLoadReferenceCell:
    """Tests for load_reference_cell function."""

    def test_load_v1_pouch(self):
        """Should load v1_pouch reference successfully."""
        ref = load_reference_cell("v1_pouch")
        assert isinstance(ref, ReferenceCell)
        assert ref.id == "v1_pouch"
        assert ref.name == "V1 Pouch Cell"
        assert ref.cell_type == "Pouch"

    def test_load_a123_amp20(self):
        """Should load a123_amp20 reference successfully."""
        ref = load_reference_cell("a123_amp20")
        assert ref.id == "a123_amp20"
        assert ref.name == "A123 AMP20 LFP Power Cell"
        assert ref.confidence == "medium"

    def test_load_kokam_ecker2015(self):
        """Should load kokam_ecker2015 reference successfully."""
        ref = load_reference_cell("kokam_ecker2015")
        assert ref.id == "kokam_ecker2015"
        assert "Ecker2015" in ref.raw_data.get("pybamm_reference", {}).get("parameter_set", "")

    def test_load_lg_e66a(self):
        """Should load lg_e66a reference successfully."""
        ref = load_reference_cell("lg_e66a")
        assert ref.id == "lg_e66a"
        assert ref.default_tolerance == 15.0  # Higher tolerance for estimated values

    def test_load_nonexistent_raises_error(self):
        """Should raise FileNotFoundError for unknown cell."""
        with pytest.raises(FileNotFoundError):
            load_reference_cell("nonexistent_cell")

    def test_reference_has_targets(self):
        """Should have validation targets."""
        ref = load_reference_cell("v1_pouch")
        assert "capacity_ah" in ref.targets
        assert "total_mass_g" in ref.targets

    def test_reference_has_tolerances(self):
        """Should have tolerance values."""
        ref = load_reference_cell("v1_pouch")
        assert isinstance(ref.tolerances, dict)
        assert ref.default_tolerance > 0


class TestGetReferenceInfo:
    """Tests for get_reference_info function."""

    def test_get_info_v1_pouch(self):
        """Should return info dictionary for v1_pouch."""
        info = get_reference_info("v1_pouch")
        assert info["id"] == "v1_pouch"
        assert info["chemistry"] == "NCM65/Graphite"
        assert info["capacity_ah"] == 81.41
        assert info["nominal_voltage_v"] == 3.663

    def test_get_info_a123(self):
        """Should return info dictionary for a123_amp20."""
        info = get_reference_info("a123_amp20")
        assert info["chemistry"] == "LFP/Graphite"
        assert info["capacity_ah"] == 19.6
        assert info["nominal_voltage_v"] == 3.3

    def test_get_info_lg_e66a(self):
        """Should return info dictionary for lg_e66a."""
        info = get_reference_info("lg_e66a")
        assert info["chemistry"] == "NMC712/Graphite"
        assert info["capacity_ah"] == 64.6
        assert info["gravimetric_ed_whkg"] == 259.0


# =============================================================================
# Test Reference Cell JSON Structure
# =============================================================================


class TestReferenceJSONStructure:
    """Tests for reference cell JSON file structure."""

    @pytest.fixture
    def all_reference_ids(self):
        """Get all reference cell IDs."""
        return list_reference_cells()

    def test_all_references_have_metadata(self, all_reference_ids):
        """All reference cells should have metadata section."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            assert "metadata" in ref.raw_data
            assert "id" in ref.raw_data["metadata"]
            assert "name" in ref.raw_data["metadata"]

    def test_all_references_have_cell_specs(self, all_reference_ids):
        """All reference cells should have cell_specs section."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            specs = ref.raw_data.get("cell_specs", {})
            assert "capacity_ah" in specs
            assert "nominal_voltage_v" in specs

    def test_all_references_have_geometry(self, all_reference_ids):
        """All reference cells should have geometry section."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            metadata = ref.raw_data.get("metadata", {})
            cell_type = metadata.get("cell_type", "Pouch").lower()

            if cell_type == "cylindrical":
                # Cylindrical cells use "geometry" key
                geometry = ref.raw_data.get("geometry", {})
                assert "diameter_mm" in geometry
                assert "length_mm" in geometry
            else:
                # Pouch/Prismatic use "geometry_inputs" key
                geometry = ref.raw_data.get("geometry_inputs", {})
                assert "cathode_height_mm" in geometry
                assert "cathode_width_mm" in geometry

    def test_all_references_have_materials(self, all_reference_ids):
        """All reference cells should have materials section."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            materials = ref.raw_data.get("materials", {})
            assert "cathode" in materials
            assert "anode" in materials
            assert "separator" in materials

    def test_all_references_have_validation(self, all_reference_ids):
        """All reference cells should have validation section."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            validation = ref.raw_data.get("validation", {})
            assert "tolerance_pct" in validation
            assert "targets" in validation

    def test_all_references_have_confidence_levels(self, all_reference_ids):
        """All reference cells should have confidence levels."""
        for cell_id in all_reference_ids:
            ref = load_reference_cell(cell_id)
            assert ref.confidence in ["high", "medium", "low"]


# =============================================================================
# Test Validation Functions
# =============================================================================


class TestValidation:
    """Tests for validation functions."""

    def test_format_reference_list(self):
        """Should format reference list."""
        output = format_reference_list()
        assert "v1_pouch" in output
        assert "Available Reference Cells" in output

    def test_format_reference_list_empty_dir(self, tmp_path):
        """Should handle empty directory."""
        output = format_reference_list(tmp_path)
        assert "No reference cells found" in output


# =============================================================================
# Test Reference Cell Values
# =============================================================================


class TestReferenceValues:
    """Tests for specific reference cell values."""

    def test_v1_pouch_values(self):
        """V1 Pouch should have correct reference values (updated 2025-12-27)."""
        ref = load_reference_cell("v1_pouch")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 81.41
        assert specs["nominal_voltage_v"] == 3.663
        assert specs["mass_g"] == 1136.82
        assert specs["gravimetric_ed_whkg"] == 262.3

    def test_a123_amp20_values(self):
        """A123 AMP20 should have correct reference values."""
        ref = load_reference_cell("a123_amp20")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 19.6
        assert specs["nominal_voltage_v"] == 3.3
        assert specs["energy_wh"] == 65.0
        assert specs["mass_g"] == 496.0
        assert specs["gravimetric_ed_whkg"] == 131.0

    def test_kokam_ecker2015_values(self):
        """Kokam Ecker2015 should have correct reference values."""
        ref = load_reference_cell("kokam_ecker2015")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 5.0
        assert specs["nominal_voltage_v"] == 3.7
        assert specs["gravimetric_ed_whkg"] == 137.0

    def test_lg_e66a_values(self):
        """LG E66A should have correct reference values."""
        ref = load_reference_cell("lg_e66a")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 64.6
        assert specs["nominal_voltage_v"] == 3.657
        assert specs["energy_wh"] == 237.7
        assert specs["gravimetric_ed_whkg"] == 259.0


# =============================================================================
# Test Tolerance Values
# =============================================================================


class TestTolerances:
    """Tests for tolerance values."""

    def test_v1_pouch_has_tight_tolerance(self):
        """V1 Pouch should have 6% tolerance (updated 2025-12-27)."""
        ref = load_reference_cell("v1_pouch")
        assert ref.default_tolerance == 6.0

    def test_kokam_has_medium_tolerance(self):
        """Kokam Ecker2015 should have 10% tolerance (updated 2025-12-27)."""
        ref = load_reference_cell("kokam_ecker2015")
        assert ref.default_tolerance == 10.0

    def test_a123_has_moderate_tolerance(self):
        """A123 AMP20 should have moderate tolerance (10%)."""
        ref = load_reference_cell("a123_amp20")
        assert ref.default_tolerance == 10.0

    def test_lg_e66a_has_high_tolerance(self):
        """LG E66A should have high tolerance (15%) due to estimations."""
        ref = load_reference_cell("lg_e66a")
        assert ref.default_tolerance == 15.0


# =============================================================================
# Test PyBaMM Extraction (Optional)
# =============================================================================


class TestPyBaMMExtraction:
    """Tests for PyBaMM parameter extraction."""

    def test_kokam_references_pybamm(self):
        """Kokam reference should reference PyBaMM Ecker2015."""
        ref = load_reference_cell("kokam_ecker2015")
        pybamm_ref = ref.raw_data.get("pybamm_reference", {})
        assert pybamm_ref.get("parameter_set") == "Ecker2015"

    @pytest.mark.skipif(
        not importlib.util.find_spec("pybamm"),
        reason="PyBaMM not installed",
    )
    def test_extract_pybamm_params_script(self):
        """Test PyBaMM extraction script can be imported."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        # Skip gracefully in CI if the standalone script is not importable.
        extract_pybamm_params = pytest.importorskip("extract_pybamm_params")
        extract_parameters = extract_pybamm_params.extract_parameters

        params = extract_parameters("Ecker2015")

        assert "cathode" in params
        assert "anode" in params
        assert "separator" in params


# =============================================================================
# Test CLI Integration
# =============================================================================


class TestCLIIntegration:
    """Tests for CLI integration with reference cells."""

    def test_cli_list_references(self):
        """CLI should be able to list references."""
        from forge.cli.main import cli

        # This should not raise an error
        result = cli(["validate", "--list-references"])
        assert result == 0

    def test_cli_info_reference(self):
        """CLI should show reference info."""
        from forge.cli.main import cli

        result = cli(["info", "--reference", "v1_pouch"])
        assert result == 0

    def test_cli_template_from_reference(self, tmp_path):
        """CLI should generate template from reference."""
        from forge.cli.main import cli

        output_path = tmp_path / "test_template.json"
        result = cli(["template", "--from-reference", "v1_pouch", "-o", str(output_path)])
        assert result == 0
        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path) as f:
            config = json.load(f)
        assert "cell_name" in config
        assert "cathode" in config


# =============================================================================
# Test Prismatic Reference Cells
# =============================================================================


class TestPrismaticReferenceCells:
    """Test prismatic reference cell loading and validation."""

    def test_load_v1_prismatic(self):
        """V1 Prismatic loads correctly."""
        ref = load_reference_cell("v1_prismatic")
        assert ref.name == "V1 Prismatic"
        assert ref.cell_type == "Prismatic"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 120.866
        assert specs.get("nominal_voltage_v") == 3.644

    def test_load_samsung_sdi_94ah(self):
        """Samsung SDI 94Ah loads correctly."""
        ref = load_reference_cell("samsung_sdi_94ah")
        assert ref.name == "Samsung SDI 94Ah"
        assert ref.cell_type == "Prismatic"
        assert ref.confidence == "medium"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 94.0
        assert specs.get("nominal_voltage_v") == 3.7

    def test_load_catl_100ah(self):
        """CATL 100Ah loads correctly."""
        ref = load_reference_cell("catl_100ah_lfp")
        assert ref.name == "CATL 100Ah LFP"
        assert ref.cell_type == "Prismatic"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 100.0
        assert specs.get("nominal_voltage_v") == 3.2
        assert "LiFePO4" in specs.get("chemistry", "")

    def test_load_catl_150ah(self):
        """CATL 150Ah loads correctly."""
        ref = load_reference_cell("catl_150ah_lfp")
        assert ref.name == "CATL 150Ah LFP"
        assert ref.cell_type == "Prismatic"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 150.0
        assert specs.get("nominal_voltage_v") == 3.2

    def test_v1_prismatic_has_tight_tolerance(self):
        """V1 Prismatic should have tight tolerance (5%)."""
        ref = load_reference_cell("v1_prismatic")
        assert ref.default_tolerance == 5.0

    def test_samsung_sdi_has_moderate_tolerance(self):
        """Samsung SDI should have moderate tolerance (10%)."""
        ref = load_reference_cell("samsung_sdi_94ah")
        assert ref.default_tolerance == 10.0

    def test_catl_cells_have_relaxed_tolerance(self):
        """CATL cells should have relaxed tolerance (12%)."""
        for cell_id in ["catl_100ah_lfp", "catl_150ah_lfp"]:
            ref = load_reference_cell(cell_id)
            assert ref.default_tolerance == 12.0

    def test_list_prismatic_cells(self):
        """list_reference_cells(cell_type='prismatic') returns 7 cells."""
        prismatic_cells = list_reference_cells(cell_type="prismatic")
        assert len(prismatic_cells) == 7
        assert "v1_prismatic" in prismatic_cells
        assert "samsung_sdi_94ah" in prismatic_cells
        assert "catl_100ah_lfp" in prismatic_cells
        assert "catl_150ah_lfp" in prismatic_cells
        assert "eve_lf280k_prismatic" in prismatic_cells
        assert "byd_blade_138ah" in prismatic_cells
        assert "catl_161ah_lfp" in prismatic_cells

    def test_list_all_cells(self):
        """list_reference_cells() returns all cells (6 pouch + 7 prismatic + 12 cylindrical)."""
        all_cells = list_reference_cells()
        assert len(all_cells) == 25  # 6 pouch + 7 prismatic + 12 cylindrical

        # Check all types present
        pouch_cells = list_reference_cells(cell_type="pouch")
        prismatic_cells = list_reference_cells(cell_type="prismatic")
        cylindrical_cells = list_reference_cells(cell_type="cylindrical")
        assert len(pouch_cells) == 6
        assert len(prismatic_cells) == 7
        assert len(cylindrical_cells) == 12

    def test_prismatic_cells_have_case_geometry(self):
        """All prismatic cells should have case_geometry section."""
        for cell_id in list_reference_cells(cell_type="prismatic"):
            ref = load_reference_cell(cell_id)
            case_geo = ref.raw_data.get("case_geometry", {})
            assert "cell_height_mm" in case_geo
            assert "cell_width_mm" in case_geo
            assert "cell_thickness_mm" in case_geo
            assert "wall_top_mm" in case_geo

    def test_prismatic_cells_have_housing(self):
        """All prismatic cells should have housing section."""
        for cell_id in list_reference_cells(cell_type="prismatic"):
            ref = load_reference_cell(cell_id)
            housing = ref.raw_data.get("housing", {})
            assert "case_material" in housing
            assert "header_mass_g" in housing

    def test_prismatic_cells_have_validation_targets(self):
        """All prismatic cells should have validation targets."""
        for cell_id in list_reference_cells(cell_type="prismatic"):
            ref = load_reference_cell(cell_id)
            targets = ref.targets
            assert "capacity_ah" in targets
            assert "total_mass_g" in targets
            assert "gravimetric_ed_whkg" in targets


# =============================================================================
# Test Prismatic Reference Values
# =============================================================================


class TestPrismaticReferenceValues:
    """Tests for specific prismatic reference cell values."""

    def test_v1_prismatic_values(self):
        """V1 Prismatic should have correct reference values."""
        ref = load_reference_cell("v1_prismatic")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 120.866
        assert specs["nominal_voltage_v"] == 3.644
        assert specs["mass_g"] == 1686.64
        assert specs["gravimetric_ed_whkg"] == 261.151

    def test_samsung_sdi_94ah_values(self):
        """Samsung SDI 94Ah should have correct reference values."""
        ref = load_reference_cell("samsung_sdi_94ah")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 94.0
        assert specs["nominal_voltage_v"] == 3.7
        assert specs["mass_g"] == 2000.0
        assert specs["gravimetric_ed_whkg"] == 174.0

    def test_catl_100ah_lfp_values(self):
        """CATL 100Ah LFP should have correct reference values."""
        ref = load_reference_cell("catl_100ah_lfp")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 100.0
        assert specs["nominal_voltage_v"] == 3.2
        assert specs["mass_g"] == 2270.0
        assert specs["gravimetric_ed_whkg"] == 141.0

    def test_catl_150ah_lfp_values(self):
        """CATL 150Ah LFP should have correct reference values."""
        ref = load_reference_cell("catl_150ah_lfp")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 150.0
        assert specs["nominal_voltage_v"] == 3.2
        assert specs["mass_g"] == 2950.0
        assert specs["gravimetric_ed_whkg"] == 163.0


# =============================================================================
# Test Prismatic Cell Geometry
# =============================================================================


class TestPrismaticGeometry:
    """Tests for prismatic cell geometry."""

    def test_v1_prismatic_dimensions(self):
        """V1 Prismatic should have correct dimensions."""
        ref = load_reference_cell("v1_prismatic")
        case_geo = ref.raw_data["case_geometry"]

        assert case_geo["cell_height_mm"] == 88.8
        assert case_geo["cell_width_mm"] == 264.6
        assert case_geo["cell_thickness_mm"] == 29.6

    def test_samsung_sdi_94ah_dimensions(self):
        """Samsung SDI 94Ah should have correct dimensions."""
        ref = load_reference_cell("samsung_sdi_94ah")
        case_geo = ref.raw_data["case_geometry"]

        assert case_geo["cell_height_mm"] == 173.0
        assert case_geo["cell_width_mm"] == 125.0
        assert case_geo["cell_thickness_mm"] == 45.0

    def test_catl_100ah_dimensions(self):
        """CATL 100Ah should have correct dimensions."""
        ref = load_reference_cell("catl_100ah_lfp")
        case_geo = ref.raw_data["case_geometry"]

        assert case_geo["cell_height_mm"] == 172.2
        assert case_geo["cell_width_mm"] == 200.33
        assert case_geo["cell_thickness_mm"] == 33.22

    def test_catl_150ah_dimensions(self):
        """CATL 150Ah should have correct dimensions."""
        ref = load_reference_cell("catl_150ah_lfp")
        case_geo = ref.raw_data["case_geometry"]

        assert case_geo["cell_height_mm"] == 207.2
        assert case_geo["cell_width_mm"] == 200.33
        assert case_geo["cell_thickness_mm"] == 33.4


# =============================================================================
# Test New Cylindrical Reference Cells (Phase 3 additions)
# =============================================================================


class TestNewCylindricalReferenceCells:
    """Tests for new cylindrical reference cells added in Phase 3."""

    def test_load_molicel_p42a(self):
        """Molicel P42A 21700 loads correctly."""
        ref = load_reference_cell("molicel_p42a_21700")
        assert ref.name == "Molicel P42A 21700"
        assert ref.cell_type == "Cylindrical"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 4.2
        assert specs.get("nominal_voltage_v") == 3.6
        assert specs.get("mass_g") == 70.0

    def test_load_samsung_50e(self):
        """Samsung 50E 21700 loads correctly."""
        ref = load_reference_cell("samsung_50e_21700")
        assert ref.name == "Samsung 50E 21700"
        assert ref.cell_type == "Cylindrical"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 5.0
        assert specs.get("nominal_voltage_v") == 3.63
        assert specs.get("mass_g") == 68.7

    def test_load_panasonic_2170_nca(self):
        """Panasonic 2170 NCA (Tesla) loads correctly."""
        ref = load_reference_cell("panasonic_2170_nca")
        assert ref.name == "Panasonic 2170 NCA (Tesla)"
        assert ref.cell_type == "Cylindrical"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 4.8
        assert specs.get("nominal_voltage_v") == 3.6
        assert specs.get("mass_g") == 69.0
        assert "NCA" in specs.get("chemistry", "")

    def test_molicel_p42a_values(self):
        """Molicel P42A should have correct reference values."""
        ref = load_reference_cell("molicel_p42a_21700")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 4.2
        assert specs["energy_wh"] == 15.12
        assert specs["gravimetric_ed_whkg"] == 216.0
        assert specs["volumetric_ed_whl"] == 615.0

    def test_samsung_50e_values(self):
        """Samsung 50E should have correct reference values."""
        ref = load_reference_cell("samsung_50e_21700")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 5.0
        assert specs["energy_wh"] == 18.15
        assert specs["gravimetric_ed_whkg"] == 264.0
        assert specs["volumetric_ed_whl"] == 510.0

    def test_panasonic_2170_nca_values(self):
        """Panasonic 2170 NCA should have correct reference values."""
        ref = load_reference_cell("panasonic_2170_nca")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 4.8
        assert specs["energy_wh"] == 17.3
        assert specs["gravimetric_ed_whkg"] == 251.0
        assert specs["volumetric_ed_whl"] == 708.0

    def test_new_cylindrical_cells_have_geometry(self):
        """New cylindrical cells should have proper geometry section."""
        for cell_id in ["molicel_p42a_21700", "samsung_50e_21700", "panasonic_2170_nca"]:
            ref = load_reference_cell(cell_id)
            geometry = ref.raw_data.get("geometry", {})
            assert "diameter_mm" in geometry
            assert "length_mm" in geometry
            assert "can_wall_thickness_mm" in geometry
            assert "header_height_mm" in geometry

    def test_new_cylindrical_cells_have_winding(self):
        """New cylindrical cells should have winding configuration."""
        for cell_id in ["molicel_p42a_21700", "samsung_50e_21700", "panasonic_2170_nca"]:
            ref = load_reference_cell(cell_id)
            winding = ref.raw_data.get("winding", {})
            assert "mandrel_diameter_mm" in winding
            assert "winding_tension_factor" in winding
            assert "tab_type" in winding

    def test_molicel_p42a_is_multi_tab(self):
        """Molicel P42A should be multi-tab design for high power."""
        ref = load_reference_cell("molicel_p42a_21700")
        winding = ref.raw_data.get("winding", {})
        assert winding.get("tab_type") == "multi_tab"


# =============================================================================
# Test New Prismatic Reference Cells (Phase 3 additions)
# =============================================================================


class TestNewPrismaticReferenceCells:
    """Tests for new prismatic reference cells added in Phase 3."""

    def test_load_eve_lf280k(self):
        """EVE LF280K loads correctly."""
        ref = load_reference_cell("eve_lf280k_prismatic")
        assert ref.name == "EVE LF280K"
        assert ref.cell_type == "Prismatic"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 280.0
        assert specs.get("nominal_voltage_v") == 3.2
        assert specs.get("mass_g") == 5490.0

    def test_load_byd_blade_138ah(self):
        """BYD Blade 138Ah loads correctly."""
        ref = load_reference_cell("byd_blade_138ah")
        assert ref.name == "BYD Blade 138Ah"
        assert ref.cell_type == "Prismatic"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 138.0
        assert specs.get("nominal_voltage_v") == 3.2
        assert specs.get("mass_g") == 2630.0

    def test_eve_lf280k_values(self):
        """EVE LF280K should have correct reference values."""
        ref = load_reference_cell("eve_lf280k_prismatic")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 280.0
        assert specs["energy_wh"] == 896.0
        assert specs["gravimetric_ed_whkg"] == 163.2
        assert specs["volumetric_ed_whl"] == 346.0

    def test_byd_blade_values(self):
        """BYD Blade should have correct reference values."""
        ref = load_reference_cell("byd_blade_138ah")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 138.0
        assert specs["energy_wh"] == 441.6
        assert specs["gravimetric_ed_whkg"] == 168.0
        assert specs["volumetric_ed_whl"] == 424.0

    def test_eve_lf280k_dimensions(self):
        """EVE LF280K should have correct dimensions."""
        ref = load_reference_cell("eve_lf280k_prismatic")
        specs = ref.raw_data["cell_specs"]
        dims = specs.get("dimensions_mm", {})

        assert dims["height"] == 207.0
        assert dims["width"] == 173.7
        assert dims["thickness"] == 72.0

    def test_byd_blade_unique_dimensions(self):
        """BYD Blade should have unique long thin dimensions."""
        ref = load_reference_cell("byd_blade_138ah")
        specs = ref.raw_data["cell_specs"]
        dims = specs.get("dimensions_mm", {})

        # Blade cells are very long and thin
        assert dims["width"] == 960.0  # Very long
        assert dims["thickness"] == 12.0  # Very thin
        assert dims["height"] == 90.0

    def test_byd_blade_z_fold_stacking(self):
        """BYD Blade should use z-fold stacking method."""
        ref = load_reference_cell("byd_blade_138ah")
        stack = ref.raw_data.get("stack_config", {})
        assert stack.get("stacking_method") == "z_fold"

    def test_new_prismatic_cells_are_lfp(self):
        """New prismatic cells should be LFP chemistry."""
        for cell_id in ["eve_lf280k_prismatic", "byd_blade_138ah"]:
            ref = load_reference_cell(cell_id)
            specs = ref.raw_data.get("cell_specs", {})
            chemistry = specs.get("chemistry", "")
            assert "LiFePO4" in chemistry or "LFP" in chemistry


# =============================================================================
# Test New Pouch Reference Cell (Phase 3 additions)
# =============================================================================


class TestNewPouchReferenceCells:
    """Tests for new pouch reference cells added in Phase 3."""

    def test_load_sk_e556(self):
        """SK On E556 loads correctly."""
        ref = load_reference_cell("sk_e556_pouch")
        assert ref.name == "SK On E556 (E-GMP)"
        assert ref.cell_type == "Pouch"
        assert ref.confidence == "medium"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 55.6
        assert specs.get("nominal_voltage_v") == 3.65
        assert specs.get("mass_g") == 740.0

    def test_sk_e556_values(self):
        """SK On E556 should have correct reference values."""
        ref = load_reference_cell("sk_e556_pouch")
        specs = ref.raw_data["cell_specs"]

        assert specs["capacity_ah"] == 55.6
        assert specs["energy_wh"] == 203.0
        assert specs["gravimetric_ed_whkg"] == 274.3
        assert specs["volumetric_ed_whl"] == 577.0

    def test_sk_e556_dimensions(self):
        """SK On E556 should have correct dimensions."""
        ref = load_reference_cell("sk_e556_pouch")
        specs = ref.raw_data["cell_specs"]
        dims = specs.get("dimensions_mm", {})

        assert dims["height"] == 355.0
        assert dims["width"] == 100.0
        assert dims["thickness"] == 9.9

    def test_sk_e556_has_pouch_structure(self):
        """SK On E556 should have proper pouch cell structure."""
        ref = load_reference_cell("sk_e556_pouch")
        materials = ref.raw_data.get("materials", {})

        # Should have case composition for pouch laminate
        assert "case_composition" in materials
        assert len(materials["case_composition"]) >= 3  # PET, Al, PP

        # Should have tab configurations
        assert "cathode_tab" in materials
        assert "anode_tab" in materials


# =============================================================================
# Test Updated Reference Cell Counts
# =============================================================================


class TestUpdatedReferenceCellCounts:
    """Tests for updated reference cell counts after Phase 4 Unified Reference additions."""

    def test_total_reference_cells(self):
        """Should have 25 total reference cells after Unified Reference additions."""
        all_cells = list_reference_cells()
        # Phase 3: 18 cells
        # Phase 4 added: 1 pouch (LG E78) + 1 prismatic (CATL 161Ah) + 5 cylindrical (MJ1, P45B, M58T, 40T, 30Q)
        # New total: 25
        assert len(all_cells) == 25

    def test_pouch_cell_count(self):
        """Should have 6 pouch cells."""
        pouch_cells = list_reference_cells(cell_type="pouch")
        assert len(pouch_cells) == 6
        assert "sk_e556_pouch" in pouch_cells
        assert "lg_e78_pouch" in pouch_cells

    def test_prismatic_cell_count(self):
        """Should have 7 prismatic cells."""
        prismatic_cells = list_reference_cells(cell_type="prismatic")
        assert len(prismatic_cells) == 7
        assert "eve_lf280k_prismatic" in prismatic_cells
        assert "byd_blade_138ah" in prismatic_cells
        assert "catl_161ah_lfp" in prismatic_cells

    def test_cylindrical_cell_count(self):
        """Should have 12 cylindrical cells."""
        cylindrical_cells = list_reference_cells(cell_type="cylindrical")
        assert len(cylindrical_cells) == 12
        assert "molicel_p42a_21700" in cylindrical_cells
        assert "samsung_50e_21700" in cylindrical_cells
        assert "panasonic_2170_nca" in cylindrical_cells
        assert "lg_mj1_18650" in cylindrical_cells
        assert "molicel_p45b_21700" in cylindrical_cells
        assert "lg_m58t_21700" in cylindrical_cells
        assert "samsung_40t_21700" in cylindrical_cells
        assert "samsung_30q_18650" in cylindrical_cells

    def test_all_new_cells_in_list(self):
        """All cells from Unified Reference should be in the list."""
        all_cells = list_reference_cells()
        unified_cells = [
            # Phase 3 cells
            "molicel_p42a_21700",
            "samsung_50e_21700",
            "panasonic_2170_nca",
            "eve_lf280k_prismatic",
            "byd_blade_138ah",
            "sk_e556_pouch",
            # Phase 4 Unified Reference cells
            "lg_e78_pouch",
            "catl_161ah_lfp",
            "lg_mj1_18650",
            "molicel_p45b_21700",
            "lg_m58t_21700",
            "samsung_40t_21700",
            "samsung_30q_18650",
        ]
        for cell_id in unified_cells:
            assert cell_id in all_cells, f"Missing cell: {cell_id}"


# =============================================================================
# Test Tier 1 Reference Cells (Best Datasets from Unified Reference)
# =============================================================================


class TestTier1ReferenceCells:
    """Tests for Tier 1 cells with best academic teardown data."""

    def test_load_lg_e78_pouch(self):
        """LG E78 pouch (GÃ¼nter 2022 JES) loads correctly."""
        ref = load_reference_cell("lg_e78_pouch")
        assert ref.name == "LG E78 (VW ID.3)"
        assert ref.cell_type == "Pouch"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 78.0
        assert specs.get("nominal_voltage_v") == 3.68
        assert specs.get("mass_g") == 1080.0

    def test_lg_e78_has_doi(self):
        """LG E78 should have DOI reference."""
        ref = load_reference_cell("lg_e78_pouch")
        assert "10.1149/1945-7111/ac4e11" in ref.raw_data.get("metadata", {}).get("doi", "")

    def test_lg_e78_electrode_parameters(self):
        """LG E78 should have detailed electrode parameters from teardown."""
        ref = load_reference_cell("lg_e78_pouch")
        materials = ref.raw_data.get("materials", {})

        cathode = materials.get("cathode", {})
        assert cathode.get("coating_thickness_0pct_um") == 87.3
        assert cathode.get("loading_mgcm2") == 27.9
        assert cathode.get("collector_thickness_um") == 14.0
        assert cathode.get("areal_capacity_mahcm2") == 5.02

        anode = materials.get("anode", {})
        assert anode.get("coating_thickness_0pct_um") == 115.3
        assert anode.get("loading_mgcm2") == 18.1
        assert anode.get("collector_thickness_um") == 12.0
        assert anode.get("np_ratio") == 1.04

        separator = materials.get("separator", {})
        assert separator.get("thickness_um") == 17.6

    def test_load_catl_161ah_lfp(self):
        """CATL 161.5Ah LFP (Stock 2023 TUM) loads correctly."""
        ref = load_reference_cell("catl_161ah_lfp")
        assert ref.name == "CATL 161.5Ah LFP (Tesla Model 3 SR)"
        assert ref.cell_type == "Prismatic"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 161.5
        assert specs.get("nominal_voltage_v") == 3.2

    def test_catl_161ah_has_doi(self):
        """CATL 161Ah should have DOI reference."""
        ref = load_reference_cell("catl_161ah_lfp")
        assert "10.1016/j.electacta.2023.143341" in ref.raw_data.get("metadata", {}).get("doi", "")

    def test_catl_161ah_thick_lfp_cathode(self):
        """CATL 161Ah should have thick LFP cathode (~200um)."""
        ref = load_reference_cell("catl_161ah_lfp")
        materials = ref.raw_data.get("materials", {})

        cathode = materials.get("cathode", {})
        assert cathode.get("coating_thickness_0pct_um") == 200.0  # Much thicker than NCM

        anode = materials.get("anode", {})
        assert anode.get("collector_thickness_um") == 5.0  # Aggressive lightweighting

    def test_catl_161ah_butterfly_design(self):
        """CATL 161Ah should have butterfly jelly-roll design."""
        ref = load_reference_cell("catl_161ah_lfp")
        stack = ref.raw_data.get("stack_config", {})
        assert stack.get("design_type") == "butterfly_jellyroll"
        assert stack.get("number_of_stacks") == 2

    def test_load_lg_mj1_18650(self):
        """LG MJ1 18650 (Heenan 2020 X-ray) loads correctly."""
        ref = load_reference_cell("lg_mj1_18650")
        assert ref.name == "LG INR18650-MJ1"
        assert ref.cell_type == "Cylindrical"
        assert ref.confidence == "high"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 3.5
        assert specs.get("nominal_voltage_v") == 3.635

    def test_lg_mj1_has_open_data(self):
        """LG MJ1 should have open-source X-ray data reference."""
        ref = load_reference_cell("lg_mj1_18650")
        open_data = ref.raw_data.get("open_data", {})
        assert open_data.get("repository") == "rdr.ucl.ac.uk"
        assert open_data.get("data_type") == "X-ray_tomography"


# =============================================================================
# Test Tier 2 Reference Cells (Well-Documented Cells)
# =============================================================================


class TestTier2ReferenceCells:
    """Tests for Tier 2 well-documented reference cells."""

    def test_load_molicel_p45b(self):
        """Molicel P45B 21700 loads correctly."""
        ref = load_reference_cell("molicel_p45b_21700")
        assert ref.name == "Molicel P45B 21700"
        assert ref.cell_type == "Cylindrical"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 4.5
        assert specs.get("gravimetric_ed_whkg") == 242.0

    def test_p45b_higher_energy_than_p42a(self):
        """P45B should have higher energy than P42A while maintaining power."""
        p45b = load_reference_cell("molicel_p45b_21700")
        p42a = load_reference_cell("molicel_p42a_21700")

        p45b_specs = p45b.raw_data.get("cell_specs", {})
        p42a_specs = p42a.raw_data.get("cell_specs", {})

        assert p45b_specs.get("capacity_ah") > p42a_specs.get("capacity_ah")
        assert p45b_specs.get("gravimetric_ed_whkg") > p42a_specs.get("gravimetric_ed_whkg")

    def test_load_lg_m58t(self):
        """LG M58T 21700 loads correctly."""
        ref = load_reference_cell("lg_m58t_21700")
        assert ref.name == "LG INR21700-M58T"
        assert ref.cell_type == "Cylindrical"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 5.8
        assert specs.get("gravimetric_ed_whkg") == 285.0
        assert "NMCA" in specs.get("chemistry", "")

    def test_m58t_highest_capacity_21700(self):
        """M58T should be highest capacity 21700."""
        m58t = load_reference_cell("lg_m58t_21700")
        m50 = load_reference_cell("lg_m50_21700")
        e50 = load_reference_cell("samsung_50e_21700")

        m58t_cap = m58t.raw_data.get("cell_specs", {}).get("capacity_ah")
        m50_cap = m50.raw_data.get("cell_specs", {}).get("capacity_ah")
        e50_cap = e50.raw_data.get("cell_specs", {}).get("capacity_ah")

        assert m58t_cap > m50_cap
        assert m58t_cap > e50_cap

    def test_load_samsung_40t(self):
        """Samsung 40T 21700 loads correctly."""
        ref = load_reference_cell("samsung_40t_21700")
        assert ref.name == "Samsung INR21700-40T"
        assert ref.cell_type == "Cylindrical"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 4.0
        assert specs.get("gravimetric_ed_whkg") == 214.0

    def test_40t_is_power_cell(self):
        """Samsung 40T should be multi-tab power cell."""
        ref = load_reference_cell("samsung_40t_21700")
        winding = ref.raw_data.get("winding", {})
        assert winding.get("tab_type") == "multi_tab"

    def test_load_samsung_30q(self):
        """Samsung 30Q 18650 loads correctly."""
        ref = load_reference_cell("samsung_30q_18650")
        assert ref.name == "Samsung INR18650-30Q"
        assert ref.cell_type == "Cylindrical"

        specs = ref.raw_data.get("cell_specs", {})
        assert specs.get("capacity_ah") == 3.0
        assert specs.get("gravimetric_ed_whkg") == 225.0

        dims = specs.get("dimensions_mm", {})
        assert dims.get("diameter") == 18.4
        assert dims.get("length") == 65.0

    def test_30q_15a_discharge(self):
        """Samsung 30Q should support 15A discharge."""
        ref = load_reference_cell("samsung_30q_18650")
        perf = ref.raw_data.get("performance", {})
        assert perf.get("max_continuous_discharge_a") == 15.0

